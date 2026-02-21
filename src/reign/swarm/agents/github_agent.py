"""
GitHubAgent - Specialized agent for GitHub operations

This agent:
1. Creates and manages repositories
2. Generates GitHub Actions workflows
3. Manages pull requests
4. Provides Git/GitHub best practices
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import yaml


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


class GitHubAgent:
    """
    Specialized agent for GitHub operations
    
    Expertise:
    - Repository management
    - GitHub Actions workflows
    - Pull requests
    - Branch protection
    - CI/CD automation
    """
    
    def __init__(self):
        """Initialize GitHub agent"""
        self.name = "GitHubAgent"
        self.expertise = [
            "GitHub repositories",
            "GitHub Actions",
            "Pull requests",
            "Branch protection",
            "CI/CD workflows",
            "Repository secrets"
        ]
        self.confidence_threshold = 0.7
    
    def execute(self, task) -> AgentResult:
        """Execute a GitHub task"""
        params = task.params
        
        # Determine operation type
        if "name" in params and "workflow" not in task.description.lower():
            return self._create_repository(params)
        elif "workflow" in task.description.lower() or "workflow_type" in params:
            return self._create_workflow(params)
        elif "pull_request" in task.description.lower() or "title" in params:
            return self._create_pull_request(params)
        else:
            return self._create_repository(params)
    
    def _create_repository(self, params: Dict[str, Any]) -> AgentResult:
        """Create GitHub repository"""
        name = params.get("name", "")
        
        # Validate repository name
        if not self._validate_repo_name(name):
            return AgentResult(
                success=False,
                confidence=0.0,
                output={},
                error=f"Invalid repository name: '{name}'. Must be lowercase, alphanumeric, hyphens only",
                self_validated=True
            )
        
        # Calculate confidence
        confidence = self._calculate_confidence(params)
        
        # Generate suggestions
        suggestions = self._generate_repo_suggestions(params)
        
        output = {
            "repository": name,
            "private": params.get("private", False),
            "description": params.get("description", "")
        }
        
        return AgentResult(
            success=True,
            confidence=confidence,
            output=output,
            suggestions=suggestions,
            self_validated=True
        )
    
    def _create_workflow(self, params: Dict[str, Any]) -> AgentResult:
        """Create GitHub Actions workflow"""
        workflow_type = params.get("workflow_type", "ci")
        workflow_yaml = params.get("workflow_yaml", "")
        
        # If YAML provided, validate it
        if workflow_yaml:
            try:
                yaml.safe_load(workflow_yaml)
            except yaml.YAMLError as e:
                return AgentResult(
                    success=False,
                    confidence=0.0,
                    output={},
                    error=f"Invalid YAML syntax: {str(e)}",
                    self_validated=True
                )
            
            # Check for hardcoded secrets
            if self._has_hardcoded_secrets(workflow_yaml):
                suggestions = ["Use GitHub Secrets instead of hardcoding sensitive values"]
            else:
                suggestions = []
        else:
            suggestions = []
        
        # Generate workflow
        output = {
            "workflow": workflow_type,
            "yaml": workflow_yaml or self._generate_workflow_template(workflow_type)
        }
        
        confidence = 0.85 if not workflow_yaml else 0.9
        
        return AgentResult(
            success=True,
            confidence=confidence,
            output=output,
            suggestions=suggestions,
            self_validated=True
        )
    
    def _create_pull_request(self, params: Dict[str, Any]) -> AgentResult:
        """Create pull request"""
        title = params.get("title", "")
        source = params.get("source", "")
        target = params.get("target", "main")
        body = params.get("body", params.get("description", ""))
        
        confidence = 0.85
        suggestions = []
        
        # Check if PR has description
        if not body or len(body) < 10:
            suggestions.append("Add a detailed description explaining the changes")
            confidence -= 0.1
        
        output = {
            "pull_request": title,
            "source": source,
            "target": target,
            "body": body
        }
        
        return AgentResult(
            success=True,
            confidence=confidence,
            output=output,
            suggestions=suggestions,
            self_validated=True
        )
    
    def _validate_repo_name(self, name: str) -> bool:
        """Validate GitHub repository name"""
        if not name:
            return False
        
        # GitHub repo names: alphanumeric, hyphens, underscores
        # No spaces or special characters
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, name))
    
    def _has_hardcoded_secrets(self, yaml_content: str) -> bool:
        """Detect hardcoded secrets in YAML"""
        # Look for common secret patterns
        secret_patterns = [
            r'API_KEY:\s*["\']?sk-\w+',
            r'PASSWORD:\s*["\'].+["\']',
            r'TOKEN:\s*["\']?\w{20,}',
        ]
        
        for pattern in secret_patterns:
            if re.search(pattern, yaml_content, re.IGNORECASE):
                return True
        
        return False
    
    def _calculate_confidence(self, params: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        confidence = 0.8
        
        # Boost: Has description
        if params.get("description"):
            confidence += 0.05
        
        # Boost: Branch protection mentioned
        if params.get("branch_protection"):
            confidence += 0.1
        
        # Reduce: Production repo without protection
        if "production" in params.get("name", "").lower() and not params.get("branch_protection"):
            confidence -= 0.1
        
        return min(confidence, 1.0)
    
    def _generate_repo_suggestions(self, params: Dict[str, Any]) -> List[str]:
        """Generate repository best practice suggestions"""
        suggestions = []
        
        # Branch protection
        if not params.get("branch_protection"):
            suggestions.append("Enable branch protection rules for main/master branch")
        
        # README
        if not params.get("readme"):
            suggestions.append("Add a comprehensive README.md file")
        
        # License
        if not params.get("license"):
            suggestions.append("Consider adding an open source license")
        
        # .gitignore
        if not params.get("gitignore"):
            suggestions.append("Add .gitignore file for your project type")
        
        return suggestions
    
    def _generate_workflow_template(self, workflow_type: str) -> str:
        """Generate basic workflow template"""
        if workflow_type == "ci":
            return """name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: echo "Add your test commands here"
"""
        return "# Workflow template"
