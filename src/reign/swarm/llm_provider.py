"""
LLM Provider Interface for Reign

Supports multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3)
- Ollama (Local models: Llama2, Mistral, etc.)

This enables natural language understanding for request processing.
Built using Test-Driven Development.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import json
import os


@dataclass
class LLMConfig:
    """
    Configuration for LLM providers
    
    Attributes:
        provider: Name of the provider (openai, claude, ollama)
        model: Model name (gpt-4, claude-3-sonnet, llama2, etc.)
        api_key: API key for cloud providers
        base_url: Base URL for local providers (Ollama)
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens in response
    """
    provider: str
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = "http://localhost:11434"  # Default Ollama URL
    temperature: float = 0.7
    max_tokens: int = 2000


@dataclass
class LLMResponse:
    """
    Response from LLM provider
    
    Attributes:
        content: The response text
        tokens_used: Number of tokens consumed
        model: Model that generated the response
        metadata: Additional provider-specific metadata
    """
    content: str
    tokens_used: int = 0
    model: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers
    
    All providers must implement:
    - understand_request(): Process natural language request
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    def understand_request(self, user_request: str) -> LLMResponse:
        """
        Process a natural language request
        
        Args:
            user_request: The user's natural language request
        
        Returns:
            LLMResponse with parsed intent
        """
        pass


class OpenAIProvider(LLMProvider):
    """
    OpenAI provider (GPT-4, GPT-3.5)
    
    Requires: pip install openai
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=config.api_key or os.getenv("OPENAI_API_KEY"))
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
    
    def understand_request(self, user_request: str) -> LLMResponse:
        """
        Use OpenAI to understand the request
        
        Args:
            user_request: User's natural language request
        
        Returns:
            LLMResponse with structured intent
        """
        system_prompt = """You are Reign, an infrastructure management AI.
Parse user requests into structured JSON with:
- action: (deploy, scale, create, delete, update, monitor)
- target: (database, kubernetes, docker, terraform, github)
- description: Brief description
- confidence: 0.0-1.0
- params: Dictionary of relevant parameters

Example:
User: "Deploy a PostgreSQL 14 database"
Response: {"action": "deploy", "target": "database", "description": "PostgreSQL 14 database", "confidence": 0.95, "params": {"image": "postgres:14"}}
"""
        
        response = self.client.chat.completions.create(
            model=self.config.model or "gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_request}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            tokens_used=response.usage.total_tokens,
            model=response.model
        )


class ClaudeProvider(LLMProvider):
    """
    Anthropic Claude provider
    
    Requires: pip install anthropic
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=config.api_key or os.getenv("ANTHROPIC_API_KEY"))
        except ImportError:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")
    
    def understand_request(self, user_request: str) -> LLMResponse:
        """
        Use Claude to understand the request
        
        Args:
            user_request: User's natural language request
        
        Returns:
            LLMResponse with structured intent
        """
        system_prompt = """You are Reign, an infrastructure management AI.
Parse user requests into structured JSON with:
- action: (deploy, scale, create, delete, update, monitor)
- target: (database, kubernetes, docker, terraform, github)
- description: Brief description
- confidence: 0.0-1.0
- params: Dictionary of relevant parameters

Return only valid JSON, no markdown or explanations."""
        
        response = self.client.messages.create(
            model=self.config.model or "claude-3-sonnet-20240229",
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_request}
            ]
        )
        
        return LLMResponse(
            content=response.content[0].text,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            model=response.model
        )


class OllamaProvider(LLMProvider):
    """
    Ollama provider for local models
    
    Supports: Llama2, Mistral, CodeLlama, etc.
    Requires: Ollama running locally
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url
    
    def understand_request(self, user_request: str) -> LLMResponse:
        """
        Use Ollama local model to understand the request
        
        Args:
            user_request: User's natural language request
        
        Returns:
            LLMResponse with structured intent
        """
        import requests
        
        system_prompt = """You are Reign, an infrastructure management AI.
Parse user requests into structured JSON with:
- action: (deploy, scale, create, delete, update, monitor)
- target: (database, kubernetes, docker, terraform, github)
- description: Brief description
- confidence: 0.0-1.0
- params: Dictionary of relevant parameters

Return only valid JSON."""
        
        payload = {
            "model": self.config.model or "llama2",
            "prompt": f"{system_prompt}\n\nUser request: {user_request}\n\nJSON response:",
            "stream": False,
            "temperature": self.config.temperature
        }
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            return LLMResponse(
                content=data.get("response", ""),
                tokens_used=0,  # Ollama doesn't return token count
                model=data.get("model", self.config.model)
            )
        else:
            raise Exception(f"Ollama request failed: {response.status_code}")


def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """
    Factory function to create the appropriate LLM provider
    
    Args:
        config: LLM configuration
    
    Returns:
        LLMProvider instance
    
    Raises:
        ValueError: If provider is unknown
    """
    providers = {
        "openai": OpenAIProvider,
        "claude": ClaudeProvider,
        "anthropic": ClaudeProvider,  # Alias
        "ollama": OllamaProvider
    }
    
    provider_class = providers.get(config.provider.lower())
    if not provider_class:
        raise ValueError(f"Unknown LLM provider: {config.provider}. "
                        f"Supported: {', '.join(providers.keys())}")
    
    return provider_class(config)


def parse_llm_json_response(response: LLMResponse) -> Dict[str, Any]:
    """
    Parse JSON from LLM response, handling markdown code blocks
    
    Args:
        response: LLMResponse from provider
    
    Returns:
        Parsed JSON dictionary
    """
    content = response.content.strip()
    
    # Remove markdown code blocks if present
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    
    content = content.strip()
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        # Try to extract JSON from text
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        raise ValueError(f"Failed to parse LLM response as JSON: {e}")
