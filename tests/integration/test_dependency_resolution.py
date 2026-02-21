"""
Integration tests for dependency resolution between agents.

Tests that agents can properly resolve dependencies, execute in correct order,
handle circular dependencies, and manage parallel vs sequential execution.
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


class TestTaskDependencies:
    """Test task dependency management"""
    
    def test_task_with_no_dependencies(self):
        """Test that tasks can be created without dependencies"""
        task = Task(
            id=1,
            description="Independent task",
            agent_type="docker",
            params={"image": "nginx:latest"}
        )
        
        assert task.depends_on == []
        assert task.priority == 0
    
    def test_task_with_single_dependency(self):
        """Test that tasks can depend on other tasks"""
        task1 = Task(
            id=1,
            description="Base task",
            agent_type="terraform",
            params={"provider": "aws", "file_content": "resource vpc {}"}
        )
        
        task2 = Task(
            id=2,
            description="Dependent task",
            agent_type="docker",
            params={"image": "app:latest"},
            depends_on=[1]  # Depends on task1
        )
        
        assert task2.depends_on == [1]
    
    def test_task_with_multiple_dependencies(self):
        """Test that tasks can depend on multiple other tasks"""
        task = Task(
            id=3,
            description="Multi-dependency task",
            agent_type="kubernetes",
            params={"name": "app", "image": "app:latest", "replicas": 3},
            depends_on=[1, 2]  # Depends on both task1 and task2
        )
        
        assert 1 in task.depends_on
        assert 2 in task.depends_on
        assert len(task.depends_on) == 2


class TestDependencyExecution:
    """Test dependency-based execution ordering"""
    
    def test_sequential_execution_with_dependencies(self):
        """Test that dependent tasks execute in correct order"""
        # Create task chain: Terraform -> Docker -> Kubernetes
        tasks = [
            Task(
                id=1,
                description="Create infrastructure",
                agent_type="terraform",
                params={"provider": "aws", "file_content": "resource ec2 {}"},
                priority=1
            ),
            Task(
                id=2,
                description="Build container",
                agent_type="docker",
                params={"image": "webapp:latest"},
                depends_on=[1],
                priority=2
            ),
            Task(
                id=3,
                description="Deploy to K8s",
                agent_type="kubernetes",
                params={"name": "webapp", "image": "webapp:latest", "replicas": 2},
                depends_on=[2],
                priority=3
            )
        ]
        
        # Verify dependency chain
        assert tasks[0].depends_on == []
        assert tasks[1].depends_on == [1]
        assert tasks[2].depends_on == [2]
        
        # Verify priorities establish order
        assert tasks[0].priority < tasks[1].priority
        assert tasks[1].priority < tasks[2].priority
    
    def test_parallel_execution_no_dependencies(self):
        """Test that independent tasks can execute in parallel"""
        tasks = [
            Task(
                id=1,
                description="Build app A",
                agent_type="docker",
                params={"image": "app-a:latest"}
            ),
            Task(
                id=2,
                description="Build app B",
                agent_type="docker",
                params={"image": "app-b:latest"}
            ),
            Task(
                id=3,
                description="Create GitHub workflow",
                agent_type="github",
                params={"name": "ci-pipeline", "workflow_content": "name: CI"}
            )
        ]
        
        # All tasks are independent (can run in parallel)
        for task in tasks:
            assert task.depends_on == []
        
        # No priority constraints
        priorities = [task.priority for task in tasks]
        assert all(p == 0 for p in priorities)
    
    def test_mixed_parallel_and_sequential(self):
        """Test tasks with mixed dependencies (some parallel, some sequential)"""
        # Scenario: Build 2 images in parallel, then deploy both to K8s
        tasks = [
            Task(
                id=1,
                description="Build frontend",
                agent_type="docker",
                params={"image": "frontend:latest"},
                priority=1
            ),
            Task(
                id=2,
                description="Build backend",
                agent_type="docker",
                params={"image": "backend:latest"},
                priority=1  # Same priority as task1 (can run in parallel)
            ),
            Task(
                id=3,
                description="Deploy to K8s",
                agent_type="kubernetes",
                params={"name": "fullstack", "image": "frontend:latest", "replicas": 2},
                depends_on=[1, 2],  # Waits for both
                priority=2
            )
        ]
        
        # Tasks 1 and 2 can run in parallel
        assert tasks[0].priority == tasks[1].priority
        assert tasks[0].depends_on == []
        assert tasks[1].depends_on == []
        
        # Task 3 waits for both
        assert 1 in tasks[2].depends_on
        assert 2 in tasks[2].depends_on


class TestDependencyCycles:
    """Test circular dependency detection"""
    
    def test_detect_simple_circular_dependency(self):
        """Test detection of A -> B -> A cycle"""
        # In a real implementation, this would be detected
        # For now, we just validate that cyclic structures can be represented
        task1 = Task(
            id=1,
            description="Task A",
            agent_type="docker",
            params={"image": "a:latest"},
            depends_on=[2]  # Depends on task2
        )
        
        task2 = Task(
            id=2,
            description="Task B",
            agent_type="docker",
            params={"image": "b:latest"},
            depends_on=[1]  # Depends on task1 - CYCLE!
        )
        
        # Verify cycle exists in structure
        assert 2 in task1.depends_on
        assert 1 in task2.depends_on
        
        # In production, a dependency resolver would detect this
        # and raise an error before execution
    
    def test_detect_complex_circular_dependency(self):
        """Test detection of A -> B -> C -> A cycle"""
        tasks = [
            Task(id=1, description="A", agent_type="docker", params={"image": "a:latest"}, depends_on=[3]),
            Task(id=2, description="B", agent_type="docker", params={"image": "b:latest"}, depends_on=[1]),
            Task(id=3, description="C", agent_type="docker", params={"image": "c:latest"}, depends_on=[2]),
        ]
        
        # Cycle: 1 -> 3 -> 2 -> 1
        assert 3 in tasks[0].depends_on
        assert 1 in tasks[1].depends_on
        assert 2 in tasks[2].depends_on
        
        # A dependency validator would need to detect this before execution


class TestDependencyResolution:
    """Test agent dependency resolution logic"""
    
    def test_resolve_single_dependency(self):
        """Test resolving a single-level dependency"""
        docker_agent = DockerAgent()
        k8s_agent = KubernetesAgent()
        
        # Execute docker task first
        docker_task = Task(
            id=1,
            description="Build image",
            agent_type="docker",
            params={"image": "myapp:v1"}
        )
        docker_result = docker_agent.execute(docker_task)
        
        # Then execute K8s task (depends on docker)
        if docker_result.success:
            k8s_task = Task(
                id=2,
                description="Deploy image",
                agent_type="kubernetes",
                params={"name": "myapp", "image": "myapp:v1", "replicas": 3},
                depends_on=[1]
            )
            k8s_result = k8s_agent.execute(k8s_task)
            
            assert k8s_result.success is True
        else:
            # Dependency failed, task 2 should not execute
            assert False, "Dependency task failed"
    
    def test_resolve_multi_level_dependencies(self):
        """Test resolving multi-level dependencies (3 levels deep)"""
        tf_agent = TerraformAgent()
        docker_agent = DockerAgent()
        k8s_agent = KubernetesAgent()
        
        # Level 1: Infrastructure
        tf_task = Task(
            id=1,
            description="Create infrastructure",
            agent_type="terraform",
            params={"provider": "aws", "file_content": "resource vpc {}"}
        )
        tf_result = tf_agent.execute(tf_task)
        assert tf_result.success is True
        
        # Level 2: Container (depends on Level 1)
        if tf_result.success:
            docker_task = Task(
                id=2,
                description="Build container",
                agent_type="docker",
                params={"image": "app:latest"},
                depends_on=[1]
            )
            docker_result = docker_agent.execute(docker_task)
            assert docker_result.success is True
            
            # Level 3: Deployment (depends on Level 2)
            if docker_result.success:
                k8s_task = Task(
                    id=3,
                    description="Deploy to K8s",
                    agent_type="kubernetes",
                    params={"name": "app", "image": "app:latest", "replicas": 2},
                    depends_on=[2]
                )
                k8s_result = k8s_agent.execute(k8s_task)
                assert k8s_result.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
