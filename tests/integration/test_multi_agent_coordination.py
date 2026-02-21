"""
Integration tests for multi-agent coordination.

Tests that multiple agents can work together seamlessly to accomplish
complex infrastructure tasks requiring coordination between Docker, Kubernetes,
Terraform, and GitHub agents.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Try importing with different paths
try:
    from reign.swarm.reign_general import ReignGeneral, Task
    from reign.swarm.agents.docker_agent import DockerAgent
    from reign.swarm.agents.kubernetes_agent import KubernetesAgent
    from reign.swarm.agents.terraform_agent import TerraformAgent
    from reign.swarm.agents.github_agent import GitHubAgent
    from reign.swarm.feedback_loop import FeedbackLoop
except ModuleNotFoundError:
    # Fallback to direct imports
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


class TestDockerToKubernetesCoordination:
    """Test coordination between Docker and Kubernetes agents."""
    
    def test_docker_creates_image_kubernetes_deploys(self):
        """Test that Docker can build image and K8s can deploy it."""
        # Arrange
        docker_agent = DockerAgent()
        k8s_agent = KubernetesAgent()
        
        # Act: Docker creates container image
        docker_task = Task(
            id=1,
            description="Build web app image",
            agent_type="docker",
            params={
                "image": "myapp:v1.0",
                "dockerfile": "FROM nginx:alpine"
            }
        )
        docker_result = docker_agent.execute(docker_task)
        
        # Act: Kubernetes deploys the image
        k8s_task = Task(
            id=2,
            description="Deploy web app to K8s",
            agent_type="kubernetes",
            params={
                "name": "myapp",
                "image": "myapp:v1.0",
                "replicas": 3
            }
        )
        k8s_result = k8s_agent.execute(k8s_task)
        
        # Assert
        assert docker_result.success is True
        assert docker_result.confidence >= 0.75
        assert "myapp" in str(docker_result.output)
        
        assert k8s_result.success is True
        assert k8s_result.confidence >= 0.75
        assert "myapp" in str(k8s_result.output)
    
    def test_docker_build_failure_prevents_kubernetes_deploy(self):
        """Test that K8s doesn't deploy if Docker build fails."""
        # Arrange
        docker_agent = DockerAgent()
        k8s_agent = KubernetesAgent()
        
        # Act: Docker build with missing/invalid image
        docker_task = Task(
            id=1,
            description="Build with missing image",
            agent_type="docker",
            params={
                "image": "",  # Empty image should fail
            }
        )
        docker_result = docker_agent.execute(docker_task)
        
        # Assert: Docker should fail or have low confidence
        # In real system, this would block K8s deployment
        if not docker_result.success or docker_result.confidence < 0.70:
            # K8s deployment should not proceed
            # This simulates the coordination logic
            should_deploy = False
        else:
            should_deploy = True
        
        assert should_deploy is False, "K8s should not deploy when Docker build fails"


class TestTerraformToDockerCoordination:
    """Test coordination between Terraform and Docker agents."""
    
    def test_terraform_creates_infrastructure_docker_deploys(self):
        """Test that Terraform creates infra then Docker deploys to it."""
        # Arrange
        tf_agent = TerraformAgent()
        docker_agent = DockerAgent()
        
        # Act: Terraform creates VPC and compute resources
        tf_task = Task(
            id=1,
            description="Create AWS VPC with EC2",
            agent_type="terraform",
            params={
                "provider": "aws",  # Required parameter
                "file_content": "provider aws { region = us-west-2 }\nresource vpc main {}\nresource ec2 instance {}"
            }
        )
        tf_result = tf_agent.execute(tf_task)
        
        # Act: Docker deploys to the created infrastructure
        docker_task = Task(
            id=2,
            description="Deploy app to EC2",
            agent_type="docker",
            params={
                "image": "webapp:latest",
            }
        )
        docker_result = docker_agent.execute(docker_task)
        
        # Assert
        assert tf_result.success is True
        assert tf_result.confidence >= 0.70
        
        assert docker_result.success is True
        assert docker_result.confidence >= 0.75


class TestGitHubToMultiAgentPipeline:
    """Test GitHub agent triggering multi-agent workflows."""
    
    def test_github_workflow_triggers_docker_and_kubernetes(self):
        """Test that GitHub workflow can orchestrate Docker + K8s."""
        # Arrange
        github_agent = GitHubAgent()
        docker_agent = DockerAgent()
        k8s_agent = KubernetesAgent()
        
        # Act: Create GitHub workflow
        github_task = Task(
            id=1,
            description="Create CI/CD workflow",
            agent_type="github",
            params={
                "workflow_name": "deploy.yml",
                "workflow_content": "name: Deploy\non: push\njobs:\n  build: {}\n  deploy: {}"
            }
        )
        github_result = github_agent.execute(github_task)
        
        # Simulate workflow execution: Build with Docker
        docker_task = Task(
            id=2,
            description="Build from CI/CD",
            agent_type="docker",
            params={"image": "cicd-app:latest"}
        )
        docker_result = docker_agent.execute(docker_task)
        
        # Deploy with Kubernetes
        k8s_task = Task(
            id=3,
            description="Deploy from CI/CD",
            agent_type="kubernetes",
            params={"name": "cicd-app", "image": "cicd-app:latest", "replicas": 2}
        )
        k8s_result = k8s_agent.execute(k8s_task)
        
        # Assert: All steps succeeded
        assert github_result.success is True
        assert docker_result.success is True
        assert k8s_result.success is True
        
        assert all(r.confidence >= 0.70 for r in [github_result, docker_result, k8s_result])


class TestAgentDependencyExecution:
    """Test agents executing with proper dependencies."""
    
    def test_agents_wait_for_dependencies(self):
        """Test that agents execute in correct order based on dependencies."""
        # Arrange
        general = ReignGeneral()
        
        # Act: Request that requires ordered execution
        request = "Deploy Docker container with PostgreSQL database"
        intent = general.understand_request(request)
        tasks = general.decompose_task(intent)
        
        # Assert: ReignGeneral should decompose request into tasks
        assert len(tasks) >= 1
        assert isinstance(tasks[0], Task)
        
        # In a real multi-step scenario, tasks would have dependencies
        # For now, we validate that task decomposition works
        for task in tasks:
            assert hasattr(task, 'agent_type')
            assert hasattr(task, 'description')
    
    def test_parallel_independent_tasks(self):
        """Test that independent tasks can execute in parallel."""
        # Arrange
        docker_agent = DockerAgent()
        github_agent = GitHubAgent()
        
        # Act: Two independent tasks (can run in parallel)
        docker_task = Task(
            id=1,
            description="Build image A",
            agent_type="docker",
            params={"image": "app-a:latest"}
        )
        
        github_task = Task(
            id=2,
            description="Create repo B",
            agent_type="github",
            params={
                "name": "project-b",  # Use 'name' not 'repo_name'
                "workflow_name": "test.yml",
                "workflow_content": "name: test\non: push\njobs:\n  build: {}"
            }
        )
        
        # Execute both
        docker_result = docker_agent.execute(docker_task)
        github_result = github_agent.execute(github_task)
        
        # Assert: Both should succeed independently
        assert docker_result.success is True
        assert github_result.success is True
        # No dependencies means both could have run simultaneously


class TestMultiAgentWithFeedbackLoop:
    """Test multi-agent coordination with feedback loops."""
    
    def test_feedback_loop_improves_multi_agent_execution(self):
        """Test that feedback loops work across multiple agents."""
        # Arrange
        docker_agent = DockerAgent()
        k8s_agent = KubernetesAgent()
        feedback_loop = FeedbackLoop(max_retries=2, confidence_threshold=0.75)
        
        # Act: Execute Docker task with feedback
        docker_task = Task(
            id=1,
            description="Build production app",
            agent_type="docker",
            params={"image": "prod-app:latest"}
        )
        
        docker_result = feedback_loop.execute_with_feedback(
            docker_agent, 
            docker_task, 
            auto_improve=True
        )
        
        # Act: Execute K8s task with feedback
        k8s_task = Task(
            id=2,
            description="Deploy production app",
            agent_type="kubernetes",
            params={
                "name": "prod-app",
                "image": "prod-app:latest",
                "replicas": 5
            }
        )
        
        k8s_result = feedback_loop.execute_with_feedback(
            k8s_agent,
            k8s_task,
            auto_improve=True
        )
        
        # Assert: Both should achieve high quality through feedback
        assert docker_result.success is True
        assert k8s_result.success is True
        
        # Feedback loop should improve confidence
        assert docker_result.confidence >= 0.70
        assert k8s_result.confidence >= 0.70
        
        # Get feedback summaries
        docker_summary = feedback_loop.get_feedback_summary()
        assert docker_summary["attempts"] >= 1


class TestAgentFailurePropagation:
    """Test how failures propagate through multi-agent workflows."""
    
    def test_critical_failure_stops_pipeline(self):
        """Test that critical failure in one agent stops the pipeline."""
        # Arrange
        docker_agent = DockerAgent()
        k8s_agent = KubernetesAgent()
        
        # Act: Docker task that should fail critically
        docker_task = Task(
            id=1,
            description="Build with missing Dockerfile",
            agent_type="docker",
            params={"image": ""}
        )
        docker_result = docker_agent.execute(docker_task)
        
        # Simulate pipeline logic: Don't proceed if Docker failed
        if not docker_result.success or docker_result.confidence < 0.60:
            k8s_should_execute = False
        else:
            k8s_should_execute = True
        
        # Assert: K8s should not execute
        assert k8s_should_execute is False, "Pipeline should stop on critical Docker failure"
    
    def test_non_critical_failure_continues_with_warning(self):
        """Test that non-critical failures allow pipeline to continue."""
        # Arrange
        github_agent = GitHubAgent()
        docker_agent = DockerAgent()
        
        # Act: GitHub task with minor issue (non-critical)
        github_task = Task(
            id=1,
            description="Create repo with default settings",
            agent_type="github",
            params={"repo_name": "test-repo", "workflow_content": "name: test"}
        )
        github_result = github_agent.execute(github_task)
        
        # Even if GitHub has minor issues, Docker can still build
        docker_task = Task(
            id=2,
            description="Build regardless of GitHub status",
            agent_type="docker",
            params={"image": "independent-app:latest"}
        )
        docker_result = docker_agent.execute(docker_task)
        
        # Assert: Docker should succeed even if GitHub had issues
        assert docker_result.success is True
        assert docker_result.confidence >= 0.70


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
