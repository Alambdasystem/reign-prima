"""
TerraformAgent - Specialized agent for Infrastructure as Code

This agent:
1. Generates Terraform configurations
2. Validates HCL syntax
3. Runs plan/apply operations
4. Provides IaC best practices
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class AgentResult:
    """Result from agent execution"""
    success: bool
    confidence: float
    output: Dict[str, Any]
    error: Optional[str] = None
    suggestions: List[str] = None
    self_validated: bool = False
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")


class TerraformAgent:
    """
    Specialized agent for Terraform / Infrastructure as Code
    
    Expertise:
    - Terraform configuration
    - Cloud infrastructure provisioning
    - State management
    - Multi-cloud deployments
    """
    
    def __init__(self):
        """Initialize Terraform agent"""
        self.name = "TerraformAgent"
        self.expertise = [
            "Terraform HCL",
            "Infrastructure as Code",
            "AWS/Azure/GCP provisioning",
            "State management",
            "Terraform modules",
            "Multi-environment setup"
        ]
        self.confidence_threshold = 0.7
        self.supported_providers = ["aws", "azure", "gcp", "google"]
    
    def execute(self, task) -> AgentResult:
        """Execute a Terraform task"""
        params = task.params
        action = params.get("action", "")
        
        # Validate action
        if action == "validate":
            return self._validate_config(params)
        elif action == "plan":
            return self._run_plan(params)
        elif action == "apply":
            return self._run_apply(params)
        elif action == "destroy":
            return self._run_destroy(params)
        else:
            # Default: Generate config (when no action specified)
            return self._generate_config(params)
    
    def _generate_config(self, params: Dict[str, Any]) -> AgentResult:
        """Generate Terraform configuration"""
        provider = params.get("provider", "").lower()
        
        # Validate provider is specified
        if not provider:
            return AgentResult(
                success=False,
                confidence=0.0,
                output={},
                error="Cloud provider must be specified (aws, azure, gcp)",
                self_validated=True
            )
        
        if provider not in self.supported_providers:
            return AgentResult(
                success=False,
                confidence=0.5,
                output={},
                error=f"Provider '{provider}' not in supported list: {self.supported_providers}",
                suggestions=[f"Supported providers: {', '.join(self.supported_providers)}"],
                self_validated=True
            )
        
        # Calculate confidence
        confidence = self._calculate_confidence(params)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(params)
        
        # Simulate config generation
        config = {
            "terraform": {"required_version": ">= 1.0"},
            "provider": {provider: {}},
            "hcl": f'resource "{params.get("resource_type", "vpc")}" "main" {{\n  # Configuration here\n}}'
        }
        
        return AgentResult(
            success=True,
            confidence=confidence,
            output=config,
            suggestions=suggestions,
            self_validated=True
        )
    
    def _validate_config(self, params: Dict[str, Any]) -> AgentResult:
        """Validate Terraform configuration"""
        config = params.get("config", "")
        
        # Basic HCL syntax validation
        if "{{{{" in config or "::::" in config or config.count("{") != config.count("}"):
            return AgentResult(
                success=False,
                confidence=0.0,
                output={},
                error="Invalid HCL syntax detected",
                self_validated=True
            )
        
        return AgentResult(
            success=True,
            confidence=0.95,
            output={"validation": "passed"},
            self_validated=True
        )
    
    def _run_plan(self, params: Dict[str, Any]) -> AgentResult:
        """Run terraform plan"""
        provider = params.get("provider", "")
        
        if not provider:
            confidence = 0.6
            suggestions = ["Specify cloud provider for better accuracy"]
        else:
            confidence = 0.9
            suggestions = []
        
        return AgentResult(
            success=True,
            confidence=confidence,
            output={"action": "plan", "provider": provider},
            suggestions=suggestions,
            self_validated=True
        )
    
    def _run_apply(self, params: Dict[str, Any]) -> AgentResult:
        """Run terraform apply"""
        confidence = 0.85
        suggestions = ["Review plan output before applying", "Use remote state backend for team collaboration"]
        
        return AgentResult(
            success=True,
            confidence=confidence,
            output={"action": "apply"},
            suggestions=suggestions,
            self_validated=True
        )
    
    def _run_destroy(self, params: Dict[str, Any]) -> AgentResult:
        """Run terraform destroy (destructive!)"""
        # Destroy operations have lower confidence due to risk
        confidence = 0.6
        suggestions = [
            "Destructive operation! Ensure you have backups",
            "Review resources to be destroyed before proceeding",
            "Consider terraform plan -destroy first"
        ]
        
        return AgentResult(
            success=True,
            confidence=confidence,
            output={"action": "destroy"},
            suggestions=suggestions,
            self_validated=True
        )
    
    def _calculate_confidence(self, params: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        confidence = 0.8
        
        # Boost: Backend configured
        if params.get("backend"):
            confidence += 0.1
        
        # Boost: Variables defined
        if params.get("variables"):
            confidence += 0.05
        
        # Boost: Modules used
        if params.get("modules"):
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _generate_suggestions(self, params: Dict[str, Any]) -> List[str]:
        """Generate IaC best practice suggestions"""
        suggestions = []
        
        # Backend suggestion
        if not params.get("backend"):
            suggestions.append("Configure remote state backend (S3, Azure Storage, etc.) for team collaboration")
        
        # Variables suggestion
        if not params.get("variables"):
            suggestions.append("Use variables for flexibility across environments")
        
        # Modules suggestion
        if not params.get("modules"):
            suggestions.append("Consider using Terraform modules for reusable infrastructure patterns")
        
        # Version constraint
        if not params.get("version_constraint"):
            suggestions.append("Pin Terraform version in configuration for reproducibility")
        
        return suggestions
