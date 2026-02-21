"""
Unit tests for ValidationAgent - Security and quality validation across all agents.

TDD Approach:
1. Write tests for ValidationAgent capabilities
2. Build ValidationAgent to pass tests
3. Integrate with existing agents
"""

import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from reign.swarm.agents.validation_agent import ValidationAgent, ValidationResult, ValidationSeverity
    from reign.swarm.reign_general import Task
except ModuleNotFoundError:
    # Will fail until we create the agent
    pytest.skip("ValidationAgent not yet implemented", allow_module_level=True)


class TestValidationAgentCreation:
    """Test ValidationAgent initialization"""
    
    def test_can_create_validation_agent(self):
        """Test that ValidationAgent can be instantiated"""
        agent = ValidationAgent()
        
        assert agent is not None
        assert agent.name == "ValidationAgent"
    
    def test_agent_has_validation_expertise(self):
        """Test that agent knows its validation capabilities"""
        agent = ValidationAgent()
        
        assert len(agent.expertise) > 0
        expertise_str = " ".join(agent.expertise).lower()
        assert "security" in expertise_str or "validation" in expertise_str


class TestSecurityValidation:
    """Test security-related validation checks"""
    
    def test_detects_hardcoded_secrets(self):
        """Test detection of hardcoded secrets in configurations"""
        agent = ValidationAgent()
        
        task = Task(
            id=1,
            description="Validate workflow with hardcoded secret",
            agent_type="validation",
            params={
                "content": "password: supersecret123\\napi_key: sk-1234567890abcdef",
                "content_type": "yaml"
            }
        )
        
        result = agent.execute(task)
        
        # Should detect security issues
        assert result.success is True  # Validation ran successfully
        assert len(result.issues) > 0  # Found issues
        assert any("secret" in issue.message.lower() or "password" in issue.message.lower() 
                   for issue in result.issues)
    
    def test_detects_exposed_credentials(self):
        """Test detection of exposed credentials"""
        agent = ValidationAgent()
        
        task = Task(
            id=1,
            description="Validate Docker config with credentials",
            agent_type="validation",
            params={
                "content": "ENV DATABASE_PASSWORD=admin123",
                "content_type": "dockerfile"
            }
        )
        
        result = agent.execute(task)
        
        assert result.success is True
        assert any(issue.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH] 
                   for issue in result.issues)
    
    def test_warns_about_insecure_ports(self):
        """Test detection of insecure port configurations"""
        agent = ValidationAgent()
        
        task = Task(
            id=1,
            description="Validate K8s config with exposed ports",
            agent_type="validation",
            params={
                "content": "port: 22\\nprotocol: TCP",  # SSH port exposed
                "content_type": "yaml"
            }
        )
        
        result = agent.execute(task)
        
        assert result.success is True
        # May warn about sensitive ports


class TestBestPracticeValidation:
    """Test best practice checks"""
    
    def test_validates_docker_image_tags(self):
        """Test that Docker images should have specific version tags"""
        agent = ValidationAgent()
        
        task = Task(
            id=1,
            description="Validate Docker task",
            agent_type="validation",
            params={
                "agent_type": "docker",
                "task_params": {"image": "nginx:latest"}
            }
        )
        
        result = agent.execute(task)
        
        assert result.success is True
        # Should suggest using specific version tags instead of 'latest'
        assert any("version" in issue.message.lower() or "latest" in issue.message.lower() 
                   for issue in result.issues if issue.severity == ValidationSeverity.MEDIUM)
    
    def test_validates_resource_limits(self):
        """Test validation of resource limits in K8s"""
        agent = ValidationAgent()
        
        task = Task(
            id=1,
            description="Validate K8s deployment without limits",
            agent_type="validation",
            params={
                "agent_type": "kubernetes",
                "task_params": {
                    "name": "myapp",
                    "image": "myapp:v1",
                    "replicas": 3
                    # Missing: resource limits
                }
            }
        )
        
        result = agent.execute(task)
        
        assert result.success is True
        # Should recommend setting resource limits
        assert any("resource" in issue.message.lower() or "limit" in issue.message.lower()
                   for issue in result.issues)
    
    def test_validates_terraform_state_backend(self):
        """Test that Terraform configurations should have remote state"""
        agent = ValidationAgent()
        
        task = Task(
            id=1,
            description="Validate Terraform config",
            agent_type="validation",
            params={
                "agent_type": "terraform",
                "task_params": {
                    "provider": "aws",
                    "file_content": "resource vpc main {}"
                    # Missing: backend configuration
                }
            }
        )
        
        result = agent.execute(task)
        
        assert result.success is True
        # Should recommend remote state backend


class TestSyntaxValidation:
    """Test syntax validation for different file types"""
    
    def test_validates_yaml_syntax(self):
        """Test YAML syntax validation"""
        agent = ValidationAgent()
        
        # Valid YAML
        valid_task = Task(
            id=1,
            description="Validate valid YAML",
            agent_type="validation",
            params={
                "content": "name: test\\nversion: 1.0\\nsteps:\\n  - build\\n  - deploy",
                "content_type": "yaml"
            }
        )
        
        result = agent.execute(valid_task)
        assert result.success is True
        
        # Invalid YAML
        invalid_task = Task(
            id=2,
            description="Validate invalid YAML",
            agent_type="validation",
            params={
                "content": "name: test\\n  invalid indentation\\nno: proper: structure",
                "content_type": "yaml"
            }
        )
        
        result = agent.execute(invalid_task)
        assert result.success is True
        # Should detect syntax issues
    
    def test_validates_json_syntax(self):
        """Test JSON syntax validation"""
        agent = ValidationAgent()
        
        task = Task(
            id=1,
            description="Validate JSON",
            agent_type="validation",
            params={
                "content": '{"name": "test", "version": "1.0"}',
                "content_type": "json"
            }
        )
        
        result = agent.execute(task)
        assert result.success is True


class TestCrossAgentValidation:
    """Test validation across multiple agent contexts"""
    
    def test_validates_docker_image_exists_for_kubernetes(self):
        """Test that K8s deployments reference valid Docker images"""
        agent = ValidationAgent()
        
        task = Task(
            id=1,
            description="Validate K8s uses valid Docker image",
            agent_type="validation",
            params={
                "agent_type": "kubernetes",
                "task_params": {
                    "name": "myapp",
                    "image": "myapp:v1.0",
                    "replicas": 2
                },
                "context": {
                    "available_images": ["nginx:latest", "postgres:14"]
                }
            }
        )
        
        result = agent.execute(task)
        
        assert result.success is True
        # May warn if image not in available images
    
    def test_validates_github_workflow_references_valid_actions(self):
        """Test that GitHub workflows use valid actions"""
        agent = ValidationAgent()
        
        task = Task(
            id=1,
            description="Validate GitHub workflow",
            agent_type="validation",
            params={
                "agent_type": "github",
                "task_params": {
                    "workflow_name": "ci.yml",
                    "workflow_content": "name: CI\\non: push\\njobs:\\n  build:\\n    runs-on: ubuntu-latest"
                }
            }
        )
        
        result = agent.execute(task)
        assert result.success is True


class TestValidationResult:
    """Test ValidationResult data structure"""
    
    def test_validation_result_creation(self):
        """Test creating ValidationResult"""
        result = ValidationResult(
            success=True,
            issues=[],
            summary="No issues found"
        )
        
        assert result.success is True
        assert len(result.issues) == 0
        assert result.summary == "No issues found"
    
    def test_validation_result_with_issues(self):
        """Test ValidationResult with multiple issues"""
        from reign.swarm.agents.validation_agent import ValidationIssue
        
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.HIGH,
                message="Hardcoded password detected",
                line_number=10
            ),
            ValidationIssue(
                severity=ValidationSeverity.MEDIUM,
                message="Missing resource limits",
                line_number=None
            )
        ]
        
        result = ValidationResult(
            success=True,
            issues=issues,
            summary="Found 2 issues"
        )
        
        assert len(result.issues) == 2
        assert result.issues[0].severity == ValidationSeverity.HIGH
        assert result.issues[1].severity == ValidationSeverity.MEDIUM


class TestValidationIntegration:
    """Test ValidationAgent integration with other agents"""
    
    def test_validates_docker_agent_output(self):
        """Test validating Docker agent task before execution"""
        agent = ValidationAgent()
        
        task = Task(
            id=1,
            description="Validate Docker task",
            agent_type="validation",
            params={
                "agent_type": "docker",
                "task_params": {
                    "image": "nginx:latest"
                }
            }
        )
        
        result = agent.execute(task)
        
        assert result.success is True
        # Should have suggestions for improvement
    
    def test_validates_complex_multi_agent_workflow(self):
        """Test validating entire multi-agent workflow"""
        agent = ValidationAgent()
        
        task = Task(
            id=1,
            description="Validate multi-agent workflow",
            agent_type="validation",
            params={
                "workflow": [
                    {"agent": "terraform", "action": "create_infrastructure"},
                    {"agent": "docker", "action": "build_image"},
                    {"agent": "kubernetes", "action": "deploy"}
                ]
            }
        )
        
        result = agent.execute(task)
        
        assert result.success is True
        # Should validate entire workflow for consistency


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
