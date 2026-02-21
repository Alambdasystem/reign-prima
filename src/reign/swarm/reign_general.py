"""
ReignGeneral - The Orchestrator

This is the central "General" that:
1. Understands natural language requests
2. Decomposes tasks into subtasks
3. Spawns specialized agents
4. Coordinates execution with feedback loops
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import re
import json


@dataclass
class Intent:
    """Represents understanding of user's request"""
    action: str  # deploy, create, delete, etc.
    target: str  # docker, kubernetes, terraform, etc.
    description: str
    confidence: float
    params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate confidence is in range [0, 1]"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")


@dataclass
class Task:
    """A single task to be executed by an agent"""
    id: int
    description: str
    agent_type: str  # docker, kubernetes, terraform, etc.
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[int] = field(default_factory=list)
    priority: int = 0


class ReignGeneral:
    """
    The General orchestrator that commands the swarm
    
    This is a minimal implementation to pass tests.
    We'll build it up incrementally using TDD.
    """
    
    def __init__(self, llm_config=None):
        """
        Initialize the General
        
        Args:
            llm_config: Optional LLMConfig for natural language understanding
                       If None, uses keyword matching (fallback mode)
        """
        self.agents = {}
        self.task_counter = 0
        self.llm_config = llm_config
        self.llm_provider = None
        
        # Initialize LLM provider if config provided
        if llm_config:
            try:
                # Import with proper path handling
                try:
                    from reign.swarm.llm_provider import create_llm_provider
                except ImportError:
                    # Fallback for different import contexts
                    import sys
                    from pathlib import Path
                    # Add parent directory to path if not already there
                    parent = Path(__file__).parent
                    if str(parent) not in sys.path:
                        sys.path.insert(0, str(parent))
                    from llm_provider import create_llm_provider
                
                self.llm_provider = create_llm_provider(llm_config)
            except Exception as e:
                print(f"Warning: Failed to initialize LLM provider: {e}")
                print("Falling back to keyword matching")
    
    def understand_request(self, user_request: str) -> Intent:
        """
        Parse natural language request into structured Intent
        
        Uses LLM if configured, otherwise falls back to keyword matching
        """
        # Try LLM first if available
        if self.llm_provider:
            try:
                return self._understand_with_llm(user_request)
            except Exception as e:
                print(f"LLM understanding failed: {e}, falling back to keywords")
        
        # Fallback to keyword matching
        return self._understand_with_keywords(user_request)
    
    def _understand_with_llm(self, user_request: str) -> Intent:
        """
        Use LLM to understand the request
        
        Args:
            user_request: User's natural language request
        
        Returns:
            Intent object parsed from LLM response
        """
        try:
            from reign.swarm.llm_provider import parse_llm_json_response
        except ImportError:
            from llm_provider import parse_llm_json_response
        
        response = self.llm_provider.understand_request(user_request)
        data = parse_llm_json_response(response)
        
        return Intent(
            action=data.get("action", "deploy"),
            target=data.get("target", "unknown"),
            description=data.get("description", user_request),
            confidence=data.get("confidence", 0.8),
            params=data.get("params", {})
        )
    
    def _understand_with_keywords(self, user_request: str) -> Intent:
        """
        Fallback keyword-based understanding
        
        Args:
            user_request: User's natural language request
        
        Returns:
            Intent object from keyword matching
        """
        request_lower = user_request.lower()
        
        # Determine action
        action = "deploy"  # Default
        if "create" in request_lower or "deploy" in request_lower or "set up" in request_lower:
            action = "deploy"
        elif "delete" in request_lower or "remove" in request_lower:
            action = "delete"
        elif "scale" in request_lower:
            action = "scale"
        elif "update" in request_lower:
            action = "update"
        
        # Determine target platform
        target = "docker"  # Default
        if "kubernetes" in request_lower or "k8s" in request_lower or "helm" in request_lower:
            target = "kubernetes"
        elif "terraform" in request_lower or "infrastructure" in request_lower:
            target = "terraform"
        elif "github" in request_lower or "repository" in request_lower or "repo" in request_lower:
            target = "github"
        elif "container" in request_lower or "docker" in request_lower or "image" in request_lower:
            target = "docker"
        
        # Calculate confidence based on how clear the request is
        confidence = self._calculate_confidence(user_request, action, target)
        
        return Intent(
            action=action,
            target=target,
            description=user_request,
            confidence=confidence
        )
    
    def _calculate_confidence(self, request: str, action: str, target: str) -> float:
        """
        Calculate confidence score for intent understanding
        
        Simple heuristic:
        - Specific keywords = higher confidence
        - Vague requests = lower confidence
        """
        confidence = 0.7  # Base confidence
        
        request_lower = request.lower()
        
        # Boost confidence for specific keywords
        specific_keywords = [
            "postgresql", "postgres", "mysql", "mongodb", "redis",
            "nginx", "apache", "node", "react", "vue", "angular",
            "api", "frontend", "backend", "database", "cache"
        ]
        
        for keyword in specific_keywords:
            if keyword in request_lower:
                confidence += 0.05
        
        # Reduce confidence for vague requests
        if len(request.split()) < 3:
            confidence -= 0.1
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def decompose_task(self, user_request) -> List[Task]:
        """
        Break down user request into individual tasks
        
        This is where the General's planning happens.
        Each task will be assigned to a specialized agent.
        
        Args:
            user_request: Either a string or an Intent object
        """
        # Handle both string and Intent inputs
        if isinstance(user_request, Intent):
            request_lower = user_request.description.lower()
        else:
            request_lower = user_request.lower()
        
        tasks = []
        task_id = 1
        
        # Detect components that need to be deployed
        components = self._detect_components(request_lower)
        
        # Create tasks with proper dependencies
        # Database should come first (other services depend on it)
        if "database" in components:
            tasks.append(Task(
                id=task_id,
                description=f"Create {components['database']} database container",
                agent_type="docker",
                params={"component": "database", "image": components["database"]}
            ))
            db_task_id = task_id
            task_id += 1
        else:
            db_task_id = None
        
        # Cache services
        if "cache" in components:
            tasks.append(Task(
                id=task_id,
                description=f"Create {components['cache']} cache container",
                agent_type="docker",
                params={"component": "cache", "image": components["cache"]}
            ))
            task_id += 1
        
        # Backend API (depends on database if it exists)
        if "api" in components or "backend" in components:
            depends = [db_task_id] if db_task_id else []
            api_image = components.get('api', 'nginx')
            tasks.append(Task(
                id=task_id,
                description=f"Create {api_image} API container",
                agent_type="docker",
                params={"component": "api", "image": api_image},
                depends_on=depends
            ))
            api_task_id = task_id
            task_id += 1
        else:
            api_task_id = None
        
        # Frontend (may depend on API)
        if "frontend" in components:
            depends = [api_task_id] if api_task_id else []
            frontend_image = components['frontend']
            tasks.append(Task(
                id=task_id,
                description=f"Create {frontend_image} frontend container",
                agent_type="docker",
                params={"component": "frontend", "image": frontend_image},
                depends_on=depends
            ))
            task_id += 1
        
        # If no specific components found, create a generic task
        if not tasks:
            # Simple single-component deployment - default to nginx web server
            if "postgresql" in request_lower or "postgres" in request_lower:
                tasks.append(Task(
                    id=1,
                    description="Create PostgreSQL database container",
                    agent_type="docker",
                    params={"image": "postgres:latest"}
                ))
            elif "web" in request_lower or "application" in request_lower or "service" in request_lower:
                # Generic web application - use nginx
                tasks.append(Task(
                    id=1,
                    description="Deploy web application server",
                    agent_type="docker",
                    params={"image": "nginx:latest", "action": "run"}
                ))
            else:
                # Ultimate fallback - still provide a default image
                tasks.append(Task(
                    id=1,
                    description="Deploy application",
                    agent_type="docker",
                    params={"image": "nginx:latest", "action": "run"}
                ))

        return tasks
    
    def _detect_components(self, request_lower: str) -> Dict[str, str]:
        """Detect what components are mentioned in the request"""
        components = {}
        
        # Database detection
        if "postgresql" in request_lower or "postgres" in request_lower:
            components["database"] = "postgresql"
        elif "mysql" in request_lower:
            components["database"] = "mysql"
        elif "mongodb" in request_lower or "mongo" in request_lower:
            components["database"] = "mongodb"
        elif "database" in request_lower or "db" in request_lower:
            components["database"] = "postgresql"  # Default
        
        # Cache detection
        if "redis" in request_lower:
            components["cache"] = "redis"
        elif "memcached" in request_lower:
            components["cache"] = "memcached"
        elif "cache" in request_lower:
            components["cache"] = "redis"  # Default
        
        # Backend/API detection
        if "node" in request_lower or "nodejs" in request_lower:
            components["api"] = "nodejs"
        elif "python" in request_lower or "flask" in request_lower or "django" in request_lower:
            components["api"] = "python"
        elif "api" in request_lower or "backend" in request_lower or "server" in request_lower:
            components["api"] = "nginx"  # Default for generic API/backend
        
        # Frontend detection
        if "react" in request_lower:
            components["frontend"] = "react"
        elif "vue" in request_lower:
            components["frontend"] = "vue"
        elif "angular" in request_lower:
            components["frontend"] = "angular"
        elif "frontend" in request_lower or "ui" in request_lower or "web" in request_lower:
            components["frontend"] = "nginx"  # Default for generic frontend
        
        return components
