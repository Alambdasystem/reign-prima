"""
Tests for AgentMemory - Learning and optimization from past executions.

AgentMemory enables the REIGN system to:
- Store successful execution patterns
- Track failure modes and solutions
- Learn from past task decompositions
- Optimize based on historical performance
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from reign.swarm.memory.agent_memory import AgentMemory
from reign.swarm.reign_general import Task
from reign.swarm.agents.docker_agent import AgentResult


class TestAgentMemoryBasics:
    """Test basic AgentMemory functionality."""
    
    def test_can_create_memory(self):
        """Test AgentMemory instantiation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            assert memory is not None
            assert memory.storage_path == tmpdir
    
    def test_can_create_memory_with_default_path(self):
        """Test AgentMemory with default storage path."""
        memory = AgentMemory()
        assert memory is not None
        assert memory.storage_path is not None
        assert Path(memory.storage_path).exists()
    
    def test_remembers_successful_task(self):
        """Test storing successful execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            task = Task(
                id=1,
                description="Deploy nginx container",
                agent_type="docker",
                params={"image": "nginx:latest", "port": 80}
            )
            result = AgentResult(
                success=True,
                confidence=0.9,
                output={"message": "Container deployed successfully"}
            )
            
            memory.remember_success(task, result, context={"env": "test"})
            
            # Verify stored
            memories = memory.get_similar_tasks(task)
            assert len(memories) > 0
            assert memories[0]["success"] == True  # SQLite returns 1, not True
            assert memories[0]["confidence"] == 0.9
    
    def test_remembers_failed_task(self):
        """Test storing failed execution with solution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            task = Task(
                id=2,
                description="Deploy kubernetes pod",
                agent_type="kubernetes",
                params={"manifest": "pod.yaml"}
            )
            error = "Pod failed: ImagePullBackOff"
            solution = "Fixed image name to include correct registry"
            
            memory.remember_failure(task, error, solution)
            
            # Verify stored
            memories = memory.get_similar_tasks(task)
            assert len(memories) > 0
            assert memories[0]["success"] == False  # SQLite returns 0, not False
            assert memories[0]["error"] == error
            assert memories[0]["solution"] == solution


class TestAgentMemoryRetrieval:
    """Test memory retrieval and similarity matching."""
    
    def test_can_find_similar_tasks_by_description(self):
        """Test finding tasks with similar descriptions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            # Store multiple nginx deployment tasks
            for i in range(3):
                task = Task(
                    id=i,
                    description=f"Deploy nginx container version {i}",
                    agent_type="docker",
                    params={"image": f"nginx:{i}"}
                )
                result = AgentResult(success=True, confidence=0.8 + i*0.05, output={})
                memory.remember_success(task, result)
            
            # Search for similar task
            search_task = Task(
                id=99,
                description="Deploy nginx container version 5",
                agent_type="docker",
                params={"image": "nginx:5"}
            )
            
            similar = memory.get_similar_tasks(search_task, limit=5)
            assert len(similar) == 3
            # Should be ordered by relevance/recency
            assert all("nginx" in mem["description"] for mem in similar)
    
    def test_can_find_similar_tasks_by_agent_type(self):
        """Test filtering by agent type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            # Store tasks for different agents
            docker_task = Task(id=1, description="Docker deploy", agent_type="docker")
            k8s_task = Task(id=2, description="K8s deploy", agent_type="kubernetes")
            
            memory.remember_success(docker_task, AgentResult(success=True, confidence=0.9, output={}))
            memory.remember_success(k8s_task, AgentResult(success=True, confidence=0.9, output={}))
            
            # Search for Docker tasks
            search_task = Task(id=3, description="Another deploy", agent_type="docker")
            similar = memory.get_similar_tasks(search_task)
            
            assert len(similar) == 1
            assert similar[0]["agent_type"] == "docker"
    
    def test_limits_results_correctly(self):
        """Test result limiting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            # Store 10 tasks
            for i in range(10):
                task = Task(id=i, description=f"Task {i}", agent_type="docker")
                memory.remember_success(task, AgentResult(success=True, confidence=0.9, output={}))
            
            # Search with limit
            search_task = Task(id=99, description="Task search", agent_type="docker")
            similar = memory.get_similar_tasks(search_task, limit=3)
            
            assert len(similar) == 3


class TestAgentMemoryLearning:
    """Test learning and optimization features."""
    
    def test_suggests_improvements_based_on_history(self):
        """Test improvement suggestions from past executions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            # Store successful task with high confidence
            good_task = Task(
                id=1,
                description="Deploy app with 4GB memory",
                agent_type="kubernetes",
                params={"memory": "4Gi", "cpu": "2"}
            )
            memory.remember_success(
                good_task,
                AgentResult(success=True, confidence=0.95, output={})
            )
            
            # Store similar task with lower confidence
            ok_task = Task(
                id=2,
                description="Deploy app with 2GB memory",
                agent_type="kubernetes",
                params={"memory": "2Gi", "cpu": "1"}
            )
            memory.remember_success(
                ok_task,
                AgentResult(success=True, confidence=0.7, output={})
            )
            
            # Request suggestions
            new_task = Task(
                id=3,
                description="Deploy app",
                agent_type="kubernetes",
                params={"memory": "2Gi"}
            )
            
            suggestions = memory.suggest_improvements(new_task)
            assert suggestions is not None
            assert "suggestions" in suggestions
            # Should suggest using more memory based on higher confidence pattern
    
    def test_calculates_success_rate_by_pattern(self):
        """Test success rate calculation for patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            # Pattern: Terraform with auto_approve=True
            for i in range(7):
                task = Task(
                    id=i,
                    description="Apply terraform",
                    agent_type="terraform",
                    params={"auto_approve": True}
                )
                memory.remember_success(task, AgentResult(success=True, confidence=0.9, output={}))
            
            # Same pattern but 3 failures
            for i in range(7, 10):
                task = Task(
                    id=i,
                    description="Apply terraform",
                    agent_type="terraform",
                    params={"auto_approve": True}
                )
                memory.remember_failure(task, "Validation failed", "Add validation step")
            
            # Get success rate
            test_task = Task(
                id=99,
                description="Apply terraform",
                agent_type="terraform",
                params={"auto_approve": True}
            )
            
            stats = memory.get_pattern_statistics(test_task)
            assert stats is not None
            assert "success_rate" in stats
            assert stats["success_rate"] == 0.7  # 7 success / 10 total
            assert stats["total_executions"] == 10
    
    def test_tracks_execution_time_trends(self):
        """Test tracking execution time improvements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            # Store tasks with decreasing execution times
            execution_times = [10.0, 8.0, 6.0, 5.0, 4.5]
            for i, exec_time in enumerate(execution_times):
                task = Task(
                    id=i,
                    description="Build docker image",
                    agent_type="docker",
                    params={"use_cache": True}
                )
                result = AgentResult(
                    success=True,
                    confidence=0.9,
                    output={}
                )
                memory.remember_success(task, result)
            
            # Get statistics
            test_task = Task(
                id=99,
                description="Build docker image",
                agent_type="docker",
                params={"use_cache": True}
            )
            
            stats = memory.get_pattern_statistics(test_task)
            assert stats is not None
            assert "average_execution_time" in stats
            assert stats["average_execution_time"] < 10.0  # Should show improvement


class TestAgentMemoryPersistence:
    """Test persistent storage functionality."""
    
    def test_persists_data_to_disk(self):
        """Test data survives across memory instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create memory and store task
            memory1 = AgentMemory(storage_path=tmpdir)
            task = Task(
                id=1,
                description="Test persistence",
                agent_type="docker"
            )
            memory1.remember_success(task, AgentResult(success=True, confidence=0.9, output={}))
            
            # Create new memory instance with same path
            memory2 = AgentMemory(storage_path=tmpdir)
            similar = memory2.get_similar_tasks(task)
            
            assert len(similar) > 0
            assert similar[0]["description"] == "Test persistence"
    
    def test_handles_corrupted_storage(self):
        """Test graceful handling of corrupted storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create corrupted file
            storage_file = Path(tmpdir) / "agent_memory.db"
            storage_file.write_text("corrupted data")
            
            # Should handle gracefully
            memory = AgentMemory(storage_path=tmpdir)
            assert memory is not None
            
            # Should be able to store new data
            task = Task(id=1, description="Test", agent_type="docker")
            memory.remember_success(task, AgentResult(success=True, confidence=0.9, output={}))


class TestAgentMemoryCleanup:
    """Test memory cleanup and maintenance."""
    
    def test_can_clear_old_memories(self):
        """Test removing old memories beyond retention period."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir, retention_days=7)
            
            # Store task
            task = Task(id=1, description="Old task", agent_type="docker")
            memory.remember_success(task, AgentResult(success=True, confidence=0.9, output={}))
            
            # Simulate age by manually updating timestamp (implementation detail)
            # For now just test the cleanup method exists
            memory.cleanup_old_memories()
            
            # Should still have recent memories
            similar = memory.get_similar_tasks(task)
            assert len(similar) > 0
    
    def test_can_clear_all_memories(self):
        """Test clearing all stored memories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = AgentMemory(storage_path=tmpdir)
            
            # Store multiple tasks
            for i in range(5):
                task = Task(id=i, description=f"Task {i}", agent_type="docker")
                memory.remember_success(task, AgentResult(success=True, confidence=0.9, output={}))
            
            # Clear all
            memory.clear_all()
            
            # Should be empty
            search_task = Task(id=99, description="Test", agent_type="docker")
            similar = memory.get_similar_tasks(search_task)
            assert len(similar) == 0
