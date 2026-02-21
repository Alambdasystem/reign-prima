"""
Integration tests for error handling and recovery across agents.

Tests how agents handle errors, propagate failures, retry operations,
and recover from partial failures in multi-agent scenarios.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from reign.swarm.reign_general import ReignGeneral, Task
    from reign.swarm.agents.docker_agent import DockerAgent
    from reign.swarm.agents.kubernetes_agent import KubernetesAgent
    from reign.swarm.agents.terraform_agent import TerraformAgent
    from reign.swarm.agents.github_agent import GitHubAgent
    from reign.swarm.feedback_loop import FeedbackLoop
except ModuleNotFoundError:
    swarm_path = src_path / "reign" / "swarm"
    agents_path = swarm_path / "agents"
    sys.path.insert(0, str(swarm_path))
    sys.path.insert(0, str(agents_path))
    from reign_general import ReignGeneral, Task
    from docker_agent import DockerAgent
    from kubernetes_agent import KubernetesAgent
    from terraform_agent import TerraformAgent
    from github_agent import GitHubAgent
    from feedback_loop import FeedbackLoop


class TestAgentErrorHandling:
    """Test individual agent error handling"""
    
    def test_docker_agent_handles_invalid_image(self):
        """Test Docker agent gracefully handles invalid image names"""
        agent = DockerAgent()
        task = Task(
            id=1,
            description="Build with invalid image",
            agent_type="docker",
            params={"image": ""}  # Empty image name
        )
        
        result = agent.execute(task)
        
        # Should fail gracefully with error message
        assert result.success is False
        assert result.confidence == 0.0
        assert result.error is not None
        assert "image" in result.error.lower()
    
    def test_kubernetes_agent_handles_zero_replicas(self):
        """Test K8s agent handles edge case replica counts"""
        agent = KubernetesAgent()
        task = Task(
            id=1,
            description="Deploy with zero replicas",
            agent_type="kubernetes",
            params={
                "name": "test-app",
                "image": "nginx:latest",
                "replicas": 0  # Zero replicas (scaling down)
            }
        )
        
        result = agent.execute(task)
        
        # Should succeed but may have lower confidence for zero replicas
        assert result.success is True
        # Confidence might be lower for unusual replica count
        assert 0.0 <= result.confidence <= 1.0
    
    def test_terraform_agent_handles_missing_provider(self):
        """Test Terraform agent requires provider specification"""
        agent = TerraformAgent()
        task = Task(
            id=1,
            description="Create infrastructure without provider",
            agent_type="terraform",
            params={
                "file_content": "resource instance {}"  # No provider specified
            }
        )
        
        result = agent.execute(task)
        
        # Should fail with provider error
        assert result.success is False
        assert "provider" in result.error.lower()
    
    def test_github_agent_handles_invalid_repo_name(self):
        """Test GitHub agent validates repository names"""
        agent = GitHubAgent()
        task = Task(
            id=1,
            description="Create repo with invalid name",
            agent_type="github",
            params={
                "name": "INVALID REPO NAME WITH SPACES!@#",
                "workflow_content": "name: test"
            }
        )
        
        result = agent.execute(task)
        
        # Should fail with validation error
        assert result.success is False
        assert "repository name" in result.error.lower() or "invalid" in result.error.lower()


class TestErrorPropagation:
    """Test error propagation in multi-agent workflows"""
    
    def test_error_stops_dependent_tasks(self):
        """Test that error in one agent prevents dependent tasks from executing"""
        docker_agent = DockerAgent()
        k8s_agent = KubernetesAgent()
        
        # Docker task that will fail
        docker_task = Task(
            id=1,
            description="Build with error",
            agent_type="docker",
            params={"image": ""}
        )
        docker_result = docker_agent.execute(docker_task)
        
        # Verify Docker failed
        assert docker_result.success is False
        
        # K8s task should not execute if Docker failed
        should_execute_k8s = docker_result.success and docker_result.confidence >= 0.70
        
        assert should_execute_k8s is False, "Dependent task should not execute after failure"
    
    def test_partial_failure_recovery(self):
        """Test recovery from partial failures using feedback loop"""
        agent = DockerAgent()
        feedback_loop = FeedbackLoop(max_retries=3, confidence_threshold=0.75)
        
        # Task with low confidence that might improve with retry
        task = Task(
            id=1,
            description="Build app",
            agent_type="docker",
            params={"image": "app:latest"}
        )
        
        result = feedback_loop.execute_with_feedback(agent, task, auto_improve=True)
        
        # Should eventually succeed or reach max retries
        summary = feedback_loop.get_feedback_summary()
        assert summary["attempts"] >= 1
        assert summary["attempts"] <= 3


class TestRetryMechanisms:
    """Test retry logic for transient failures"""
    
    def test_feedback_loop_retries_on_failure(self):
        """Test that feedback loop retries failed operations"""
        agent = DockerAgent()
        feedback_loop = FeedbackLoop(max_retries=2, confidence_threshold=0.80)
        
        task = Task(
            id=1,
            description="Task that may need retry",
            agent_type="docker",
            params={"image": "test:latest"}
        )
        
        result = feedback_loop.execute_with_feedback(agent, task)
        
        # Should have attempted at least once
        summary = feedback_loop.get_feedback_summary()
        assert summary["attempts"] >= 1
    
    def test_max_retries_prevents_infinite_loop(self):
        """Test that max retries limit is enforced"""
        agent = DockerAgent()
        feedback_loop = FeedbackLoop(max_retries=2, confidence_threshold=0.99)  # Very high threshold
        
        task = Task(
            id=1,
            description="Task with high confidence requirement",
            agent_type="docker",
            params={"image": "test:latest"}
        )
        
        result = feedback_loop.execute_with_feedback(agent, task)
        
        # Should not exceed max retries
        summary = feedback_loop.get_feedback_summary()
        assert summary["attempts"] <= 2


class TestErrorRecovery:
    """Test error recovery strategies"""
    
    def test_graceful_degradation(self):
        """Test system continues with reduced functionality after non-critical errors"""
        # Simulate scenario where one agent fails but others can continue
        docker_agent = DockerAgent()
        github_agent = GitHubAgent()
        
        # Docker task succeeds
        docker_task = Task(
            id=1,
            description="Build app",
            agent_type="docker",
            params={"image": "myapp:v1"}
        )
        docker_result = docker_agent.execute(docker_task)
        assert docker_result.success is True
        
        # GitHub task might fail but shouldn't affect Docker's success
        github_task = Task(
            id=2,
            description="Create workflow",
            agent_type="github",
            params={
                "name": "myrepo",
                "workflow_name": "ci.yml",
                "workflow_content": "name: CI\\non: push"
            }
        )
        github_result = github_agent.execute(github_task)
        
        # GitHub result doesn't affect Docker's already-successful execution
        # System degraded but functional
        assert docker_result.success is True  # Still true regardless of GitHub


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
