"""
Integration tests for AgentMemory with ReignGeneral and agents.

Tests memory-enhanced agent behavior:
- Learning from past executions
- Confidence boosting from history
- Failure avoidance based on patterns
- Performance optimization
"""

import pytest
import tempfile
from pathlib import Path

from reign.swarm.memory.agent_memory import AgentMemory
from reign.swarm.reign_general import ReignGeneral, Task
from reign.swarm.agents.docker_agent import DockerAgent, AgentResult


class TestMemoryWithAgents:
    """Test AgentMemory integration with individual agents."""
    
    def test_docker_agent_with_memory(self):
        """Test Docker agent can use memory for learning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            agent = DockerAgent()
            
            # Store successful Docker operation
            task = Task(
                id=1,
                description="Pull nginx image",
                agent_type="docker",
                params={"image": "nginx:latest"}
            )
            result = AgentResult(
                success=True,
                confidence=0.9,
                output={"image": "nginx:latest", "status": "pulled"}
            )
            memory.remember_success(task, result)
            
            # Check agent can retrieve similar tasks
            similar_task = Task(
                id=2,
                description="Pull nginx alpine",
                agent_type="docker",
                params={"image": "nginx:alpine"}
            )
            
            memories = memory.get_similar_tasks(similar_task)
            assert len(memories) > 0
            assert "nginx" in memories[0]["description"]
    
    def test_memory_improves_confidence_over_time(self):
        """Test that memory of successes improves confidence suggestions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            # Simulate multiple successful executions of same pattern
            for i in range(5):
                task = Task(
                    id=i,
                    description="Deploy with 4GB memory",
                    agent_type="kubernetes",
                    params={"memory": "4Gi", "replicas": 3}
                )
                result = AgentResult(
                    success=True,
                    confidence=0.85 + i*0.02,  # Increasing confidence
                    output={"status": "deployed"}
                )
                memory.remember_success(task, result)
            
            # Check suggestions for new similar task
            new_task = Task(
                id=10,
                description="Deploy app",
                agent_type="kubernetes",
                params={"memory": "4Gi"}
            )
            
            suggestions = memory.suggest_improvements(new_task)
            assert suggestions["confidence"] == 1.0  # 100% success rate
            assert suggestions["total_similar_tasks"] == 5
    
    def test_memory_warns_about_past_failures(self):
        """Test memory provides warnings about common failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            # Store multiple failures with same error
            common_error = "Port 80 already in use"
            solution = "Use different port or stop conflicting container"
            
            for i in range(3):
                task = Task(
                    id=i,
                    description="Start web server on port 80",
                    agent_type="docker",
                    params={"port": 80}
                )
                memory.remember_failure(task, common_error, solution)
            
            # Check suggestions warn about this error
            new_task = Task(
                id=10,
                description="Start nginx on port 80",
                agent_type="docker",
                params={"port": 80}
            )
            
            suggestions = memory.suggest_improvements(new_task)
            assert len(suggestions["suggestions"]) > 0
            
            # Should have failure warning
            failure_warnings = [s for s in suggestions["suggestions"] if s["type"] == "failure_warning"]
            assert len(failure_warnings) > 0
            assert common_error in failure_warnings[0]["description"]
            assert failure_warnings[0]["solution"] == solution


class TestMemoryWithReignGeneral:
    """Test AgentMemory integration with ReignGeneral orchestrator."""
    
    def test_reign_general_can_use_memory(self):
        """Test ReignGeneral can leverage memory for task decomposition."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            general = ReignGeneral()
            
            # Store successful task decomposition pattern
            task = Task(
                id=1,
                description="Deploy nginx to kubernetes",
                agent_type="kubernetes",
                params={"image": "nginx", "replicas": 3}
            )
            result = AgentResult(
                success=True,
                confidence=0.95,
                output={"deployment": "created", "service": "created"}
            )
            memory.remember_success(task, result)
            
            # New similar request should find historical pattern
            similar_task = Task(
                id=2,
                description="Deploy apache to kubernetes",
                agent_type="kubernetes",
                params={"image": "apache"}
            )
            
            memories = memory.get_similar_tasks(similar_task)
            assert len(memories) > 0
    
    def test_memory_tracks_task_decomposition_patterns(self):
        """Test memory can track how tasks were decomposed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            # Store multi-step task pattern
            context = {
                "steps": [
                    {"step": 1, "action": "build_image"},
                    {"step": 2, "action": "push_image"},
                    {"step": 3, "action": "deploy_k8s"}
                ]
            }
            
            task = Task(
                id=1,
                description="Deploy containerized app",
                agent_type="docker",
                params={"dockerfile": "Dockerfile"}
            )
            result = AgentResult(
                success=True,
                confidence=0.9,
                output={"deployed": True}
            )
            memory.remember_success(task, result, context=context)
            
            # Retrieve and verify context is preserved
            memories = memory.get_similar_tasks(task)
            assert len(memories) > 0
            assert memories[0]["context"] is not None
            assert memories[0]["context"]["steps"][0]["action"] == "build_image"


class TestMemoryPerformanceOptimization:
    """Test memory-based performance optimization."""
    
    def test_tracks_execution_time_patterns(self):
        """Test memory tracks execution times for optimization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            # Store tasks with varying execution times
            for i, exec_time in enumerate([10.0, 8.0, 6.0, 5.0, 4.0]):
                task = Task(
                    id=i,
                    description="Build Docker image",
                    agent_type="docker",
                    params={"cache": True}
                )
                result = AgentResult(
                    success=True,
                    confidence=0.9,
                    output={"image": "built"},
                    execution_time=exec_time
                )
                memory.remember_success(task, result)
            
            # Get statistics
            test_task = Task(
                id=10,
                description="Build Docker image",
                agent_type="docker",
                params={"cache": True}
            )
            
            stats = memory.get_pattern_statistics(test_task)
            assert stats["average_execution_time"] < 10.0
            assert stats["average_execution_time"] == 6.6  # (10+8+6+5+4)/5
    
    def test_suggests_faster_parameters(self):
        """Test memory suggests parameters that led to faster execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            # Slow execution without cache
            slow_task = Task(
                id=1,
                description="Build image",
                agent_type="docker",
                params={"cache": False}
            )
            memory.remember_success(
                slow_task,
                AgentResult(success=True, confidence=0.7, output={}, execution_time=15.0)
            )
            
            # Fast execution with cache
            fast_task = Task(
                id=2,
                description="Build image",
                agent_type="docker",
                params={"cache": True}
            )
            memory.remember_success(
                fast_task,
                AgentResult(success=True, confidence=0.95, output={}, execution_time=3.0)
            )
            
            # Get suggestions
            new_task = Task(
                id=3,
                description="Build image",
                agent_type="docker",
                params={}
            )
            
            suggestions = memory.suggest_improvements(new_task)
            assert len(suggestions["suggestions"]) > 0
            
            # Should suggest using cache (high confidence, fast execution)
            param_opts = [s for s in suggestions["suggestions"] if s["type"] == "parameter_optimization"]
            assert len(param_opts) > 0
            assert param_opts[0]["confidence"] == 0.95


class TestMemoryErrorRecovery:
    """Test memory-based error recovery strategies."""
    
    def test_remembers_error_solutions(self):
        """Test memory stores and retrieves error solutions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            # Store error with solution (2 times to be considered "common")
            error = "Error: Provider not initialized"
            solution = "Run 'terraform init' first"
            
            for i in range(2):  # Store twice for common error
                task = Task(
                    id=i,
                    description="Apply terraform config",
                    agent_type="terraform",
                    params={"config": "main.tf"}
                )
                memory.remember_failure(task, error, solution)
            
            # Retrieve for similar task
            similar_task = Task(
                id=10,
                description="Apply terraform",
                agent_type="terraform",
                params={"config": "app.tf"}
            )
            
            suggestions = memory.suggest_improvements(similar_task)
            failure_warnings = [s for s in suggestions["suggestions"] if s["type"] == "failure_warning"]
            
            assert len(failure_warnings) > 0
            assert solution in str(failure_warnings[0])
    
    def test_calculates_failure_rates_by_pattern(self):
        """Test memory calculates failure rates for risk assessment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            # Risky pattern: 60% failure rate
            for i in range(10):
                task = Task(
                    id=i,
                    description="Deploy without health check",
                    agent_type="kubernetes",
                    params={"health_check": False}
                )
                if i < 6:  # 6 failures
                    memory.remember_failure(task, "Pod crashed", "Add health checks")
                else:  # 4 successes
                    memory.remember_success(
                        task,
                        AgentResult(success=True, confidence=0.6, output={})
                    )
            
            # Check statistics
            test_task = Task(
                id=20,
                description="Deploy app",
                agent_type="kubernetes",
                params={"health_check": False}
            )
            
            stats = memory.get_pattern_statistics(test_task)
            assert stats["success_rate"] == 0.4  # 4/10
            assert stats["failed_executions"] == 6
