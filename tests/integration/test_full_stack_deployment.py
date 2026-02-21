"""
Integration tests for complete full-stack deployment scenarios.

Tests end-to-end workflows that span multiple agents to deploy
complete applications with infrastructure, containers, orchestration, and CI/CD.
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


class TestBasicDeployment:
    """Test basic single-agent deployments"""
    
    def test_deploy_simple_docker_container(self):
        """Test deploying a simple containerized application"""
        agent = DockerAgent()
        
        task = Task(
            id=1,
            description="Deploy nginx web server",
            agent_type="docker",
            params={
                "image": "nginx:latest"
            }
        )
        
        result = agent.execute(task)
        
        assert result.success is True
        assert result.confidence >= 0.75
        assert "nginx" in str(result.output).lower()
    
    def test_deploy_kubernetes_application(self):
        """Test deploying application to Kubernetes"""
        agent = KubernetesAgent()
        
        task = Task(
            id=1,
            description="Deploy web app to K8s",
            agent_type="kubernetes",
            params={
                "name": "webapp",
                "image": "nginx:latest",
                "replicas": 3
            }
        )
        
        result = agent.execute(task)
        
        assert result.success is True
        assert result.confidence >= 0.75
        assert "deployment" in str(result.output).lower()


class TestMultiTierDeployment:
    """Test multi-tier application deployments"""
    
    def test_deploy_database_and_application(self):
        """Test deploying database followed by application"""
        docker_agent = DockerAgent()
        k8s_agent = KubernetesAgent()
        
        # Step 1: Deploy database container
        db_task = Task(
            id=1,
            description="Deploy PostgreSQL database",
            agent_type="docker",
            params={"image": "postgres:14"}
        )
        db_result = docker_agent.execute(db_task)
        
        assert db_result.success is True
        
        # Step 2: Deploy application that uses the database
        app_task = Task(
            id=2,
            description="Deploy app with database",
            agent_type="kubernetes",
            params={
                "name": "myapp",
                "image": "myapp:latest",
                "replicas": 2
            },
            depends_on=[1]
        )
        app_result = k8s_agent.execute(app_task)
        
        assert app_result.success is True
        assert db_result.confidence >= 0.75
        assert app_result.confidence >= 0.75
    
    def test_deploy_frontend_backend_database_stack(self):
        """Test deploying complete 3-tier application"""
        docker_agent = DockerAgent()
        k8s_agent = KubernetesAgent()
        
        # Tier 1: Database
        db_task = Task(
            id=1,
            description="Deploy database tier",
            agent_type="docker",
            params={"image": "postgres:14"}
        )
        db_result = docker_agent.execute(db_task)
        assert db_result.success is True
        
        # Tier 2: Backend API
        backend_task = Task(
            id=2,
            description="Deploy backend API",
            agent_type="docker",
            params={"image": "api-server:latest"},
            depends_on=[1]
        )
        backend_result = docker_agent.execute(backend_task)
        assert backend_result.success is True
        
        # Tier 3: Frontend
        frontend_task = Task(
            id=3,
            description="Deploy frontend to K8s",
            agent_type="kubernetes",
            params={
                "name": "frontend",
                "image": "frontend:latest",
                "replicas": 3
            },
            depends_on=[2]
        )
        frontend_result = k8s_agent.execute(frontend_task)
        assert frontend_result.success is True


class TestInfrastructureAndApplication:
    """Test infrastructure provisioning followed by application deployment"""
    
    def test_terraform_then_docker_deployment(self):
        """Test provisioning infrastructure then deploying containers"""
        tf_agent = TerraformAgent()
        docker_agent = DockerAgent()
        
        # Step 1: Provision infrastructure
        infra_task = Task(
            id=1,
            description="Provision AWS infrastructure",
            agent_type="terraform",
            params={
                "provider": "aws",
                "file_content": "provider aws {region = us-west-2}\\nresource vpc main {}"
            }
        )
        infra_result = tf_agent.execute(infra_task)
        assert infra_result.success is True
        
        # Step 2: Deploy application to infrastructure
        app_task = Task(
            id=2,
            description="Deploy app to provisioned infrastructure",
            agent_type="docker",
            params={"image": "webapp:latest"},
            depends_on=[1]
        )
        app_result = docker_agent.execute(app_task)
        assert app_result.success is True


class TestCICDPipeline:
    """Test complete CI/CD pipeline setup"""
    
    def test_github_workflow_with_deployment(self):
        """Test creating GitHub workflow that triggers deployment"""
        github_agent = GitHubAgent()
        docker_agent = DockerAgent()
        k8s_agent = KubernetesAgent()
        
        # Step 1: Create CI/CD workflow
        workflow_task = Task(
            id=1,
            description="Create deployment workflow",
            agent_type="github",
            params={
                "name": "myapp-repo",
                "workflow_name": "deploy.yml",
                "workflow_content": "name: Deploy\\non: push\\njobs:\\n  build:\\n    runs-on: ubuntu-latest"
            }
        )
        workflow_result = github_agent.execute(workflow_task)
        assert workflow_result.success is True
        
        # Step 2: Simulate workflow building Docker image
        build_task = Task(
            id=2,
            description="Build Docker image from workflow",
            agent_type="docker",
            params={"image": "myapp:v1.0"},
            depends_on=[1]
        )
        build_result = docker_agent.execute(build_task)
        assert build_result.success is True
        
        # Step 3: Simulate workflow deploying to K8s
        deploy_task = Task(
            id=3,
            description="Deploy from CI/CD pipeline",
            agent_type="kubernetes",
            params={
                "name": "myapp",
                "image": "myapp:v1.0",
                "replicas": 2
            },
            depends_on=[2]
        )
        deploy_result = k8s_agent.execute(deploy_task)
        assert deploy_result.success is True


class TestCompleteStackWithFeedback:
    """Test complete stack deployment with feedback loops for quality"""
    
    def test_production_deployment_with_quality_gates(self):
        """Test production deployment with feedback-driven quality assurance"""
        tf_agent = TerraformAgent()
        docker_agent = DockerAgent()
        k8s_agent = KubernetesAgent()
        feedback_loop = FeedbackLoop(max_retries=2, confidence_threshold=0.80)
        
        # Step 1: Infrastructure with quality feedback
        infra_task = Task(
            id=1,
            description="Provision production infrastructure",
            agent_type="terraform",
            params={
                "provider": "aws",
                "file_content": "provider aws {region = us-east-1}\\nresource vpc prod {}"
            }
        )
        infra_result = feedback_loop.execute_with_feedback(tf_agent, infra_task, auto_improve=True)
        assert infra_result.success is True
        
        # Step 2: Container build with quality feedback
        build_task = Task(
            id=2,
            description="Build production container",
            agent_type="docker",
            params={"image": "prod-app:v1.0"}
        )
        build_result = feedback_loop.execute_with_feedback(docker_agent, build_task, auto_improve=True)
        assert build_result.success is True
        
        # Step 3: K8s deployment with quality feedback
        deploy_task = Task(
            id=3,
            description="Deploy to production K8s",
            agent_type="kubernetes",
            params={
                "name": "prod-app",
                "image": "prod-app:v1.0",
                "replicas": 5
            }
        )
        deploy_result = feedback_loop.execute_with_feedback(k8s_agent, deploy_task, auto_improve=True)
        assert deploy_result.success is True
        
        # Verify high quality standards met
        assert infra_result.confidence >= 0.75
        assert build_result.confidence >= 0.75
        assert deploy_result.confidence >= 0.75


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
