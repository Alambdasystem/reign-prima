"""
ValidationAgent - Comprehensive security and quality validation agent.

This agent validates configurations, detects security issues, enforces best practices,
and performs cross-agent validation to ensure quality across the REIGN system.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import re
import yaml
import json


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a single validation issue"""
    severity: ValidationSeverity
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    category: str = "general"


@dataclass
class ValidationResult:
    """Result from validation execution"""
    success: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    summary: str = ""
    confidence: float = 1.0


class ValidationAgent:
    """
    Specialized agent for security and quality validation.
    
    Capabilities:
    - Security validation (secrets, credentials, ports)
    - Best practice enforcement (versioning, resource limits, state management)
    - Syntax validation (YAML, JSON, HCL)
    - Cross-agent validation (workflow consistency)
    """
    
    def __init__(self):
        """Initialize ValidationAgent"""
        self.name = "ValidationAgent"
        self.expertise = [
            "Security validation",
            "Best practices",
            "Syntax validation",
            "Configuration review",
            "Cross-agent validation",
            "Compliance checking"
        ]
        
        # Patterns for security detection
        self.secret_patterns = [
            r'password\s*[:=]\s*["\']?[\w!@#$%^&*()]+',
            r'api[_-]?key\s*[:=]\s*["\']?[\w-]+',
            r'secret\s*[:=]\s*["\']?[\w-]+',
            r'token\s*[:=]\s*["\']?[\w-]+',
            r'DATABASE_PASSWORD\s*=\s*["\']?[\w]+',
        ]
        
        # Sensitive ports
        self.sensitive_ports = [22, 23, 3389, 5432, 3306, 27017]
    
    def execute(self, task) -> ValidationResult:
        """
        Execute validation task
        
        Args:
            task: Task with validation parameters
            
        Returns:
            ValidationResult with issues found
        """
        params = task.params
        issues = []
        
        # Determine validation type
        if "content" in params:
            # Content validation (YAML, JSON, Dockerfile, etc.)
            issues.extend(self._validate_content(
                params["content"],
                params.get("content_type", "text")
            ))
        
        if "agent_type" in params:
            # Agent-specific validation
            issues.extend(self._validate_agent_task(
                params["agent_type"],
                params.get("task_params", {})
            ))
        
        if "workflow" in params:
            # Multi-agent workflow validation
            issues.extend(self._validate_workflow(params["workflow"]))
        
        # Generate summary
        if not issues:
            summary = "No issues found. Configuration looks good!"
        else:
            critical = sum(1 for i in issues if i.severity == ValidationSeverity.CRITICAL)
            high = sum(1 for i in issues if i.severity == ValidationSeverity.HIGH)
            medium = sum(1 for i in issues if i.severity == ValidationSeverity.MEDIUM)
            summary = f"Found {len(issues)} issues: {critical} critical, {high} high, {medium} medium"
        
        return ValidationResult(
            success=True,  # Validation itself succeeded
            issues=issues,
            summary=summary,
            confidence=0.95
        )
    
    def _validate_content(self, content: str, content_type: str) -> List[ValidationIssue]:
        """Validate raw content for security and syntax issues"""
        issues = []
        
        # Security validation
        issues.extend(self._check_secrets(content))
        issues.extend(self._check_ports(content))
        
        # Syntax validation
        if content_type == "yaml":
            issues.extend(self._validate_yaml(content))
        elif content_type == "json":
            issues.extend(self._validate_json(content))
        elif content_type == "dockerfile":
            issues.extend(self._validate_dockerfile(content))
        
        return issues
    
    def _check_secrets(self, content: str) -> List[ValidationIssue]:
        """Check for hardcoded secrets and credentials"""
        issues = []
        
        for pattern in self.secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Find line number
                line_num = content[:match.start()].count('\n') + 1
                
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Hardcoded secret detected: {match.group().split(':')[0]}",
                    line_number=line_num,
                    suggestion="Use environment variables or secret management service",
                    category="security"
                ))
        
        return issues
    
    def _check_ports(self, content: str) -> List[ValidationIssue]:
        """Check for exposed sensitive ports"""
        issues = []
        
        for port in self.sensitive_ports:
            if f"port: {port}" in content or f"port:{port}" in content:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Sensitive port {port} exposed",
                    suggestion=f"Ensure port {port} is properly secured",
                    category="security"
                ))
        
        return issues
    
    def _validate_yaml(self, content: str) -> List[ValidationIssue]:
        """Validate YAML syntax"""
        issues = []
        
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.HIGH,
                message=f"YAML syntax error: {str(e)}",
                category="syntax"
            ))
        
        return issues
    
    def _validate_json(self, content: str) -> List[ValidationIssue]:
        """Validate JSON syntax"""
        issues = []
        
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.HIGH,
                message=f"JSON syntax error: {str(e)}",
                line_number=e.lineno,
                category="syntax"
            ))
        
        return issues
    
    def _validate_dockerfile(self, content: str) -> List[ValidationIssue]:
        """Validate Dockerfile best practices"""
        issues = []
        
        # Check for ENV with secrets
        if re.search(r'ENV\s+.*PASSWORD', content, re.IGNORECASE):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                message="Password set in ENV variable",
                suggestion="Use Docker secrets or build-time arguments",
                category="security"
            ))
        
        return issues
    
    def _validate_agent_task(self, agent_type: str, task_params: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate agent-specific task parameters"""
        issues = []
        
        if agent_type == "docker":
            issues.extend(self._validate_docker_task(task_params))
        elif agent_type == "kubernetes":
            issues.extend(self._validate_kubernetes_task(task_params))
        elif agent_type == "terraform":
            issues.extend(self._validate_terraform_task(task_params))
        elif agent_type == "github":
            issues.extend(self._validate_github_task(task_params))
        
        return issues
    
    def _validate_docker_task(self, params: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate Docker task parameters"""
        issues = []
        
        image = params.get("image", "")
        
        # Check for 'latest' tag
        if ":latest" in image or ":" not in image:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.MEDIUM,
                message="Using 'latest' tag or no tag specified",
                suggestion="Use specific version tags for reproducibility",
                category="best_practice"
            ))
        
        return issues
    
    def _validate_kubernetes_task(self, params: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate Kubernetes task parameters"""
        issues = []
        
        # Check for resource limits
        if "resources" not in params and "limits" not in params:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.MEDIUM,
                message="No resource limits specified",
                suggestion="Set CPU and memory limits to prevent resource exhaustion",
                category="best_practice"
            ))
        
        # Check for namespace
        if "namespace" not in params:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.LOW,
                message="No namespace specified",
                suggestion="Use dedicated namespaces for better resource isolation",
                category="best_practice"
            ))
        
        return issues
    
    def _validate_terraform_task(self, params: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate Terraform task parameters"""
        issues = []
        
        file_content = params.get("file_content", "")
        
        # Check for backend configuration
        if "backend" not in file_content:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.MEDIUM,
                message="No remote backend configured",
                suggestion="Configure remote state backend for team collaboration",
                category="best_practice"
            ))
        
        return issues
    
    def _validate_github_task(self, params: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate GitHub task parameters"""
        issues = []
        
        workflow_content = params.get("workflow_content", "")
        
        # Check for secrets in workflow
        if re.search(r'password|secret|token', workflow_content, re.IGNORECASE):
            # Could be using secrets properly or hardcoding
            if "${{" not in workflow_content:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.HIGH,
                    message="Potential hardcoded secret in workflow",
                    suggestion="Use GitHub Secrets for sensitive data",
                    category="security"
                ))
        
        return issues
    
    def _validate_workflow(self, workflow: List[Dict[str, str]]) -> List[ValidationIssue]:
        """Validate multi-agent workflow for consistency"""
        issues = []
        
        # Check workflow has proper ordering
        agents = [step.get("agent") for step in workflow]
        
        # Terraform should come before Docker/K8s
        if "terraform" in agents:
            tf_index = agents.index("terraform")
            if "docker" in agents:
                docker_index = agents.index("docker")
                if tf_index > docker_index:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.HIGH,
                        message="Infrastructure should be provisioned before deployment",
                        suggestion="Move Terraform step before Docker step",
                        category="workflow"
                    ))
        
        return issues


if __name__ == "__main__":
    # Quick test
    agent = ValidationAgent()
    print(f"✓ {agent.name} created with {len(agent.expertise)} areas of expertise")
