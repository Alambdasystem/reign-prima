"""
Integration tests for real Docker SDK operations.

These tests interact with actual Docker daemon and test real container operations.
Mark as integration tests that require Docker Desktop running.
"""

import pytest
import sys
from pathlib import Path
import docker
from docker.errors import DockerException

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from reign.swarm.executors.real_docker_executor import RealDockerExecutor
    from reign.swarm.reign_general import Task
except ModuleNotFoundError:
    pytest.skip("RealDockerExecutor not yet implemented", allow_module_level=True)


def check_docker_available():
    """Check if Docker daemon is accessible"""
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


# Skip all tests if Docker not available
pytestmark = pytest.mark.skipif(
    not check_docker_available(),
    reason="Docker daemon not running or not accessible"
)


class TestRealDockerExecutor:
    """Test real Docker executor with actual Docker daemon"""
    
    def test_can_create_executor(self):
        """Test that RealDockerExecutor can be instantiated"""
        executor = RealDockerExecutor()
        
        assert executor is not None
        assert executor.client is not None
    
    def test_executor_can_ping_docker(self):
        """Test that executor can communicate with Docker daemon"""
        executor = RealDockerExecutor()
        
        result = executor.ping()
        
        assert result is True
    
    def test_executor_can_pull_image(self):
        """Test pulling a real Docker image"""
        executor = RealDockerExecutor()
        
        # Pull a small image for testing
        result = executor.pull_image("alpine:latest")
        
        assert result is not None
        assert "alpine:latest" in result or "alpine" in result
    
    def test_executor_can_create_container(self):
        """Test creating a real container"""
        executor = RealDockerExecutor()
        
        # Ensure image exists
        executor.pull_image("alpine:latest")
        
        # Create container
        container_name = "reign-test-container"
        result = executor.create_container(
            image="alpine:latest",
            name=container_name,
            command="echo 'Hello from REIGN'"
        )
        
        assert result is not None
        assert container_name in result or "reign-test" in result
        
        # Cleanup
        try:
            executor.remove_container(container_name, force=True)
        except:
            pass
    
    def test_executor_can_list_containers(self):
        """Test listing containers"""
        executor = RealDockerExecutor()
        
        containers = executor.list_containers(all=True)
        
        assert containers is not None
        assert isinstance(containers, list)
    
    def test_executor_can_remove_container(self):
        """Test removing a container"""
        executor = RealDockerExecutor()
        
        # Create a test container
        executor.pull_image("alpine:latest")
        container_name = "reign-test-remove"
        executor.create_container(
            image="alpine:latest",
            name=container_name,
            command="echo 'test'"
        )
        
        # Remove it
        result = executor.remove_container(container_name, force=True)
        
        assert result is True
    
    def test_executor_handles_missing_image(self):
        """Test handling of non-existent image"""
        executor = RealDockerExecutor()
        
        result = executor.create_container(
            image="nonexistent-image-12345:latest",
            name="test-missing"
        )
        
        # Should return error info, not crash
        assert result is not None
        assert "error" in str(result).lower() or "not found" in str(result).lower()
    
    def test_executor_can_inspect_container(self):
        """Test inspecting container details"""
        executor = RealDockerExecutor()
        
        # Create test container
        executor.pull_image("alpine:latest")
        container_name = "reign-test-inspect"
        executor.create_container(
            image="alpine:latest",
            name=container_name,
            command="sleep 1"
        )
        
        # Inspect it
        result = executor.inspect_container(container_name)
        
        assert result is not None
        assert isinstance(result, dict)
        
        # Cleanup
        try:
            executor.remove_container(container_name, force=True)
        except:
            pass


class TestRealDockerIntegrationWithAgent:
    """Test integration of real Docker executor with DockerAgent"""
    
    def test_docker_agent_can_use_real_executor(self):
        """Test that DockerAgent can use RealDockerExecutor"""
        from reign.swarm.agents.docker_agent import DockerAgent
        
        agent = DockerAgent()
        executor = RealDockerExecutor()
        
        # Inject real executor into agent
        agent.executor = executor
        
        task = Task(
            id=1,
            description="Pull nginx image",
            agent_type="docker",
            params={"image": "nginx:alpine"}
        )
        
        # This would execute with real Docker
        # For now, just verify executor is injectable
        assert agent.executor is not None
        assert hasattr(agent.executor, 'pull_image')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not slow"])
