"""
Unit tests for KubernetesAgent

TDD: Write tests first, then build the agent
"""
import pytest
from reign.swarm.agents.kubernetes_agent import KubernetesAgent, AgentResult
from reign.swarm.reign_general import Task


class TestKubernetesAgentCreation:
    """Test basic KubernetesAgent setup"""
    
    def test_can_create_kubernetes_agent(self):
        """Test: Can we create a KubernetesAgent?"""
        agent = KubernetesAgent()
        
        assert agent is not None
        assert agent.name == "KubernetesAgent"
    
    def test_agent_has_k8s_expertise(self):
        """Test: Does agent know K8s expertise?"""
        agent = KubernetesAgent()
        
        assert len(agent.expertise) > 0
        expertise_text = " ".join(agent.expertise).lower()
        assert "kubernetes" in expertise_text or "k8s" in expertise_text


class TestKubernetesAgentExecution:
    """Test KubernetesAgent task execution"""
    
    def test_agent_can_create_deployment(self):
        """Test: Can agent create K8s deployment?"""
        agent = KubernetesAgent()
        task = Task(
            id=1,
            description="Create web app deployment",
            agent_type="kubernetes",
            params={
                "name": "web-app",
                "image": "nginx:1.21",
                "replicas": 3
            }
        )
        
        result = agent.execute(task)
        
        assert result.success == True
        assert result.output.get("kind") == "Deployment"
        assert result.output.get("replicas") == 3
    
    def test_validates_replica_count(self):
        """Test: Agent validates replica count is reasonable"""
        agent = KubernetesAgent()
        task = Task(
            id=1,
            description="Create deployment with too many replicas",
            agent_type="kubernetes",
            params={
                "name": "web-app",
                "image": "nginx:latest",
                "replicas": 1000  # Way too many!
            }
        )
        
        result = agent.execute(task)
        
        # Should warn or reduce confidence
        if result.success:
            assert result.confidence < 0.8 or len(result.suggestions) > 0


class TestKubernetesAgentHelm:
    """Test Helm chart operations"""
    
    def test_agent_can_deploy_helm_chart(self):
        """Test: Can agent deploy Helm chart?"""
        agent = KubernetesAgent()
        task = Task(
            id=1,
            description="Deploy PostgreSQL with Helm",
            agent_type="kubernetes",
            params={
                "chart": "bitnami/postgresql",
                "release_name": "my-db",
                "namespace": "default"
            }
        )
        
        result = agent.execute(task)
        
        assert result.success == True
        assert "helm" in result.output.get("method", "").lower()
    
    def test_suggests_namespace_isolation(self):
        """Test: Agent suggests namespace isolation"""
        agent = KubernetesAgent()
        task = Task(
            id=1,
            description="Deploy to default namespace",
            agent_type="kubernetes",
            params={
                "name": "production-app",
                "namespace": "default"  # Bad practice for prod
            }
        )
        
        result = agent.execute(task)
        
        # Should suggest dedicated namespace
        suggestions_text = " ".join(result.suggestions).lower()
        assert "namespace" in suggestions_text or result.confidence < 0.9


class TestKubernetesAgentValidation:
    """Test K8s resource validation"""
    
    def test_validates_yaml_syntax(self):
        """Test: Agent catches invalid YAML?"""
        agent = KubernetesAgent()
        task = Task(
            id=1,
            description="Apply manifest",
            agent_type="kubernetes",
            params={
                "manifest": "invalid: yaml: syntax::"
            }
        )
        
        result = agent.execute(task)
        
        assert result.success == False
        assert "yaml" in result.error.lower() or "syntax" in result.error.lower()
    
    def test_validates_resource_limits(self):
        """Test: Agent checks resource limits are set"""
        agent = KubernetesAgent()
        task = Task(
            id=1,
            description="Create deployment without limits",
            agent_type="kubernetes",
            params={
                "name": "web-app",
                "image": "nginx:latest"
                # Missing resource limits!
            }
        )
        
        result = agent.execute(task)
        
        # Should suggest resource limits
        if result.success and result.suggestions:
            suggestions_text = " ".join(result.suggestions).lower()
            assert "resource" in suggestions_text or "limit" in suggestions_text
