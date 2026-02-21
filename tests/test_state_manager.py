"""
Tests for StateManager - Infrastructure state tracking and rollback.

StateManager enables:
- Track deployed infrastructure state
- Store resource metadata and relationships
- Dependency graph management
- Rollback to previous states
- Checkpoint/restore capabilities
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from reign.swarm.state.state_manager import StateManager, ResourceState, Checkpoint


class TestStateManagerBasics:
    """Test basic StateManager functionality."""
    
    def test_can_create_state_manager(self):
        """Test StateManager instantiation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(storage_path=tmpdir)
            assert manager is not None
            assert manager.storage_path == tmpdir
    
    def test_can_create_with_default_path(self):
        """Test StateManager with default storage."""
        manager = StateManager()
        assert manager is not None
        assert Path(manager.storage_path).exists()
    
    def test_records_resource_deployment(self):
        """Test recording deployed resource."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(storage_path=tmpdir)
            
            resource = ResourceState(
                resource_id="container-123",
                resource_type="docker_container",
                name="nginx",
                metadata={"image": "nginx:latest", "port": 80},
                agent_type="docker"
            )
            
            manager.record_deployment(resource)
            
            # Verify recorded
            state = manager.get_resource_state("container-123")
            assert state is not None
            assert state["name"] == "nginx"
            assert state["resource_type"] == "docker_container"
    
    def test_records_resource_dependencies(self):
        """Test recording resource dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(storage_path=tmpdir)
            
            # Deploy container
            container = ResourceState(
                resource_id="container-1",
                resource_type="docker_container",
                name="app",
                metadata={"image": "app:1.0"},
                agent_type="docker"
            )
            manager.record_deployment(container)
            
            # Deploy service that depends on container
            service = ResourceState(
                resource_id="service-1",
                resource_type="k8s_service",
                name="app-service",
                metadata={"port": 80},
                agent_type="kubernetes",
                depends_on=["container-1"]
            )
            manager.record_deployment(service)
            
            # Verify dependency tracked
            deps = manager.get_dependent_resources("container-1")
            assert len(deps) == 1
            assert deps[0]["resource_id"] == "service-1"


class TestStateManagerCheckpoints:
    """Test checkpoint and restore functionality."""
    
    def test_can_create_checkpoint(self):
        """Test creating state checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(storage_path=tmpdir)
            
            # Deploy some resources
            for i in range(3):
                resource = ResourceState(
                    resource_id=f"res-{i}",
                    resource_type="docker_container",
                    name=f"container-{i}",
                    metadata={},
                    agent_type="docker"
                )
                manager.record_deployment(resource)
            
            # Create checkpoint
            checkpoint_id = manager.create_checkpoint("Before update")
            assert checkpoint_id is not None
            
            # Verify checkpoint exists
            checkpoints = manager.list_checkpoints()
            assert len(checkpoints) > 0
            assert checkpoint_id in [c["checkpoint_id"] for c in checkpoints]
    
    def test_can_restore_checkpoint(self):
        """Test restoring to previous checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(storage_path=tmpdir)
            
            # Deploy initial resources
            res1 = ResourceState(
                resource_id="res-1",
                resource_type="docker_container",
                name="nginx",
                metadata={},
                agent_type="docker"
            )
            manager.record_deployment(res1)
            
            # Create checkpoint
            checkpoint_id = manager.create_checkpoint("Initial state")
            
            # Deploy more resources
            res2 = ResourceState(
                resource_id="res-2",
                resource_type="docker_container",
                name="postgres",
                metadata={},
                agent_type="docker"
            )
            manager.record_deployment(res2)
            
            # Restore checkpoint
            restored = manager.restore_checkpoint(checkpoint_id)
            assert restored is True
            
            # Verify state matches checkpoint
            all_resources = manager.get_all_resources()
            assert len(all_resources) == 1
            assert all_resources[0]["resource_id"] == "res-1"
    
    def test_checkpoint_includes_metadata(self):
        """Test checkpoint stores description and timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(storage_path=tmpdir)
            
            description = "Before risky deployment"
            checkpoint_id = manager.create_checkpoint(description)
            
            checkpoints = manager.list_checkpoints()
            checkpoint = next(c for c in checkpoints if c["checkpoint_id"] == checkpoint_id)
            
            assert checkpoint["description"] == description
            assert "timestamp" in checkpoint
            assert "resource_count" in checkpoint


class TestStateManagerRollback:
    """Test rollback functionality."""
    
    def test_can_rollback_to_checkpoint(self):
        """Test rolling back to specific checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(storage_path=tmpdir)
            
            # Initial state
            res1 = ResourceState(
                resource_id="res-1",
                resource_type="docker_container",
                name="app-v1",
                metadata={"version": "1.0"},
                agent_type="docker"
            )
            manager.record_deployment(res1)
            checkpoint1 = manager.create_checkpoint("Version 1.0")
            
            # Update state
            res2 = ResourceState(
                resource_id="res-2",
                resource_type="docker_container",
                name="app-v2",
                metadata={"version": "2.0"},
                agent_type="docker"
            )
            manager.record_deployment(res2)
            
            # Rollback
            rollback_plan = manager.get_rollback_plan(checkpoint1)
            assert rollback_plan is not None
            assert len(rollback_plan["resources_to_remove"]) == 1
            
            success = manager.rollback_to_checkpoint(checkpoint1)
            assert success is True
    
    def test_rollback_respects_dependencies(self):
        """Test rollback removes resources in correct order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(storage_path=tmpdir)
            
            checkpoint1 = manager.create_checkpoint("Empty state")
            
            # Deploy container
            container = ResourceState(
                resource_id="container-1",
                resource_type="docker_container",
                name="app",
                metadata={},
                agent_type="docker"
            )
            manager.record_deployment(container)
            
            # Deploy dependent service
            service = ResourceState(
                resource_id="service-1",
                resource_type="k8s_service",
                name="app-svc",
                metadata={},
                agent_type="kubernetes",
                depends_on=["container-1"]
            )
            manager.record_deployment(service)
            
            # Get rollback plan
            plan = manager.get_rollback_plan(checkpoint1)
            
            # Service should be removed before container
            remove_ids = plan["resources_to_remove"]
            service_idx = remove_ids.index("service-1")
            container_idx = remove_ids.index("container-1")
            assert service_idx < container_idx  # Service removed first
    
    def test_partial_rollback(self):
        """Test rolling back specific resources."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(storage_path=tmpdir)
            
            # Deploy multiple resources
            for i in range(5):
                res = ResourceState(
                    resource_id=f"res-{i}",
                    resource_type="docker_container",
                    name=f"container-{i}",
                    metadata={},
                    agent_type="docker"
                )
                manager.record_deployment(res)
            
            # Rollback only specific resources
            resources_to_rollback = ["res-2", "res-3"]
            success = manager.rollback_resources(resources_to_rollback)
            
            assert success is True
            
            # Verify only those resources removed
            all_resources = manager.get_all_resources()
            resource_ids = [r["resource_id"] for r in all_resources]
            assert "res-2" not in resource_ids
            assert "res-3" not in resource_ids
            assert "res-0" in resource_ids  # Others remain


class TestStateManagerQueries:
    """Test state querying functionality."""
    
    def test_get_resources_by_type(self):
        """Test filtering resources by type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(storage_path=tmpdir)
            
            # Deploy mixed resources
            docker_res = ResourceState(
                resource_id="docker-1",
                resource_type="docker_container",
                name="nginx",
                metadata={},
                agent_type="docker"
            )
            k8s_res = ResourceState(
                resource_id="k8s-1",
                resource_type="k8s_deployment",
                name="app",
                metadata={},
                agent_type="kubernetes"
            )
            
            manager.record_deployment(docker_res)
            manager.record_deployment(k8s_res)
            
            # Query by type
            docker_resources = manager.get_resources_by_type("docker_container")
            assert len(docker_resources) == 1
            assert docker_resources[0]["resource_id"] == "docker-1"
    
    def test_get_resources_by_agent(self):
        """Test filtering resources by agent type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(storage_path=tmpdir)
            
            # Deploy resources from different agents
            for i in range(3):
                res = ResourceState(
                    resource_id=f"docker-{i}",
                    resource_type="docker_container",
                    name=f"container-{i}",
                    metadata={},
                    agent_type="docker"
                )
                manager.record_deployment(res)
            
            res = ResourceState(
                resource_id="k8s-1",
                resource_type="k8s_deployment",
                name="app",
                metadata={},
                agent_type="kubernetes"
            )
            manager.record_deployment(res)
            
            # Query by agent
            docker_resources = manager.get_resources_by_agent("docker")
            assert len(docker_resources) == 3
    
    def test_get_deployment_timeline(self):
        """Test retrieving deployment timeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(storage_path=tmpdir)
            
            # Deploy resources over time
            for i in range(3):
                res = ResourceState(
                    resource_id=f"res-{i}",
                    resource_type="docker_container",
                    name=f"app-{i}",
                    metadata={},
                    agent_type="docker"
                )
                manager.record_deployment(res)
            
            # Get timeline
            timeline = manager.get_deployment_timeline()
            assert len(timeline) == 3
            
            # Should be ordered by timestamp
            timestamps = [t["timestamp"] for t in timeline]
            assert timestamps == sorted(timestamps)


class TestStateManagerPersistence:
    """Test state persistence across sessions."""
    
    def test_state_persists_across_instances(self):
        """Test state survives manager restart."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create manager and deploy resource
            manager1 = StateManager(storage_path=tmpdir)
            res = ResourceState(
                resource_id="res-1",
                resource_type="docker_container",
                name="nginx",
                metadata={},
                agent_type="docker"
            )
            manager1.record_deployment(res)
            
            # Create new manager instance
            manager2 = StateManager(storage_path=tmpdir)
            state = manager2.get_resource_state("res-1")
            
            assert state is not None
            assert state["name"] == "nginx"
    
    def test_checkpoints_persist(self):
        """Test checkpoints survive manager restart."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create checkpoint
            manager1 = StateManager(storage_path=tmpdir)
            checkpoint_id = manager1.create_checkpoint("Test checkpoint")
            
            # New instance should see checkpoint
            manager2 = StateManager(storage_path=tmpdir)
            checkpoints = manager2.list_checkpoints()
            
            assert len(checkpoints) > 0
            assert checkpoint_id in [c["checkpoint_id"] for c in checkpoints]
