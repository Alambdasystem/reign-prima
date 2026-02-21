"""
Unit tests for DockerAgent

TDD Approach:
1. Write tests for DockerAgent
2. Build minimal agent to pass
3. Add more complex tests
4. Iterate
"""
import pytest
from reign.swarm.agents.docker_agent import DockerAgent, AgentResult
from reign.swarm.reign_general import Task


class TestDockerAgentCreation:
    """Test basic DockerAgent setup"""
    
    def test_can_create_docker_agent(self):
        """Test: Can we create a DockerAgent?"""
        agent = DockerAgent()
        
        assert agent is not None
        assert agent.name == "DockerAgent"
    
    def test_agent_has_expertise(self):
        """Test: Does agent know its expertise?"""
        agent = DockerAgent()
        
        assert len(agent.expertise) > 0
        assert "docker" in " ".join(agent.expertise).lower()


class TestDockerAgentExecution:
    """Test DockerAgent task execution"""
    
    def test_agent_can_execute_simple_task(self):
        """Test: Can agent execute a simple container creation?"""
        agent = DockerAgent()
        task = Task(
            id=1,
            description="Create PostgreSQL container",
            agent_type="docker",
            params={"image": "postgres:latest", "name": "test-db"}
        )
        
        result = agent.execute(task)
        
        assert result is not None
        assert isinstance(result, AgentResult)
        assert result.success is not None  # Should be True or False
    
    def test_successful_execution_has_high_confidence(self):
        """Test: Successful executions should have high confidence"""
        agent = DockerAgent()
        task = Task(
            id=1,
            description="Create nginx container",
            agent_type="docker",
            params={"image": "nginx:latest"}
        )
        
        result = agent.execute(task)
        
        if result.success:
            assert result.confidence > 0.7
    
    def test_agent_validates_image_name(self):
        """Test: Agent should validate image names"""
        agent = DockerAgent()
        task = Task(
            id=1,
            description="Create container with invalid image",
            agent_type="docker",
            params={"image": "invalid!!!image!!!"}
        )
        
        result = agent.execute(task)
        
        # Should fail validation
        assert result.success == False
        assert "invalid" in result.error.lower() or "image" in result.error.lower()


class TestDockerAgentSelfValidation:
    """Test agent's self-validation capabilities"""
    
    def test_agent_performs_self_validation(self):
        """Test: Does agent validate its own work?"""
        agent = DockerAgent()
        task = Task(
            id=1,
            description="Create database container",
            agent_type="docker",
            params={"image": "postgres:latest"}
        )
        
        result = agent.execute(task)
        
        # Result should have validation info
        assert hasattr(result, "self_validated")
    
    def test_agent_detects_missing_health_check(self):
        """Test: Agent should notice missing health checks"""
        agent = DockerAgent()
        task = Task(
            id=1,
            description="Create production container",
            agent_type="docker",
            params={
                "image": "postgres:latest",
                # Missing health check configuration!
            }
        )
        
        result = agent.execute(task)
        
        # Should suggest adding health check
        if result.suggestions:
            suggestions_text = " ".join(result.suggestions).lower()
            assert "health" in suggestions_text or "monitor" in suggestions_text


class TestAgentResult:
    """Test AgentResult data structure"""
    
    def test_agent_result_creation(self):
        """Test: Can we create AgentResult?"""
        result = AgentResult(
            success=True,
            confidence=0.9,
            output={"container_id": "abc123"}
        )
        
        assert result.success == True
        assert result.confidence == 0.9
        assert result.output["container_id"] == "abc123"
    
    def test_failed_result_has_error(self):
        """Test: Failed results should have error message"""
        result = AgentResult(
            success=False,
            confidence=0.0,
            error="Invalid image name"
        )
        
        assert result.success == False
        assert result.error is not None
        assert len(result.error) > 0
    
    def test_result_can_have_suggestions(self):
        """Test: Results can include suggestions"""
        result = AgentResult(
            success=True,
            confidence=0.8,
            output={},
            suggestions=["Add health check", "Use specific version tag"]
        )
        
        assert len(result.suggestions) == 2
        assert "health" in result.suggestions[0].lower()


class TestDockerAgentConfidence:
    """Test confidence scoring"""
    
    def test_confidence_in_valid_range(self):
        """Test: Confidence should be between 0 and 1"""
        agent = DockerAgent()
        task = Task(
            id=1,
            description="Create container",
            agent_type="docker",
            params={"image": "nginx:latest"}
        )
        
        result = agent.execute(task)
        
        assert 0.0 <= result.confidence <= 1.0
    
    def test_specific_version_tag_increases_confidence(self):
        """Test: Specific version tags should increase confidence"""
        agent = DockerAgent()
        
        # Task with 'latest' tag
        task1 = Task(
            id=1,
            description="Create container",
            agent_type="docker",
            params={"image": "nginx:latest"}
        )
        
        # Task with specific version
        task2 = Task(
            id=2,
            description="Create container",
            agent_type="docker",
            params={"image": "nginx:1.21.0"}
        )
        
        result1 = agent.execute(task1)
        result2 = agent.execute(task2)
        
        # Specific version should have higher confidence
        if result1.success and result2.success:
            assert result2.confidence >= result1.confidence
