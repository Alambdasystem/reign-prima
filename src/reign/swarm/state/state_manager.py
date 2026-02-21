"""
StateManager - Infrastructure state tracking and rollback.

Provides:
- Resource deployment tracking
- Dependency graph management
- Checkpoint/restore capabilities
- Rollback planning and execution
"""

import sqlite3
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict


logger = logging.getLogger(__name__)


@dataclass
class ResourceState:
    """Represents deployed infrastructure resource state."""
    resource_id: str
    resource_type: str  # docker_container, k8s_deployment, terraform_resource, etc.
    name: str
    metadata: Dict[str, Any]
    agent_type: str  # docker, kubernetes, terraform, github
    depends_on: List[str] = field(default_factory=list)
    status: str = "deployed"
    deployed_at: Optional[str] = None
    
    def __post_init__(self):
        if self.deployed_at is None:
            self.deployed_at = datetime.now().isoformat()


@dataclass
class Checkpoint:
    """Represents a state checkpoint for rollback."""
    checkpoint_id: str
    description: str
    timestamp: str
    resource_count: int
    resources: List[Dict[str, Any]] = field(default_factory=list)


class StateManager:
    """
    Manages infrastructure deployment state and rollback.
    
    Features:
    - Tracks all deployed resources with metadata
    - Records resource dependencies
    - Creates checkpoints for rollback
    - Provides rollback planning
    - Persists state in SQLite database
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize StateManager.
        
        Args:
            storage_path: Directory for SQLite database (default: ~/.reign/state)
        """
        if storage_path is None:
            storage_path = str(Path.home() / ".reign" / "state")
        
        self.storage_path = storage_path
        
        # Ensure storage directory exists
        Path(storage_path).mkdir(parents=True, exist_ok=True)
        
        # Database path
        self.db_path = Path(storage_path) / "state_manager.db"
        
        # Initialize database
        self._init_database()
        
        logger.info(f"StateManager initialized with storage at {self.db_path}")
    
    def _init_database(self):
        """Initialize SQLite database schema."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create resources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    resource_id TEXT PRIMARY KEY,
                    resource_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    metadata TEXT,
                    agent_type TEXT NOT NULL,
                    depends_on TEXT,
                    status TEXT DEFAULT 'deployed',
                    deployed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create checkpoints table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resource_count INTEGER,
                    state_snapshot TEXT NOT NULL
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_resource_type ON resources(resource_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_type ON resources(agent_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON resources(status)")
            
            conn.commit()
            logger.debug("Database schema initialized successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            # Handle corrupted database
            try:
                if conn:
                    conn.close()
            except:
                pass
            if self.db_path.exists():
                logger.warning("Removing corrupted database and recreating")
                try:
                    self.db_path.unlink()
                except PermissionError:
                    import time
                    time.sleep(0.1)
                    try:
                        self.db_path.unlink()
                    except PermissionError:
                        self.db_path = Path(self.storage_path) / f"state_manager_{os.getpid()}.db"
                # Retry
                self._init_database()
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def record_deployment(self, resource: ResourceState):
        """
        Record a deployed resource.
        
        Args:
            resource: ResourceState to record
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO resources (
                    resource_id, resource_type, name, metadata,
                    agent_type, depends_on, status, deployed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                resource.resource_id,
                resource.resource_type,
                resource.name,
                json.dumps(resource.metadata),
                resource.agent_type,
                json.dumps(resource.depends_on) if resource.depends_on else None,
                resource.status,
                resource.deployed_at
            ))
            
            conn.commit()
            logger.debug(f"Recorded deployment: {resource.resource_id}")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to record deployment: {e}")
        finally:
            if conn:
                conn.close()
    
    def get_resource_state(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Get state of a specific resource.
        
        Args:
            resource_id: ID of resource to retrieve
            
        Returns:
            Resource state dict or None if not found
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM resources WHERE resource_id = ?
            """, (resource_id,))
            
            row = cursor.fetchone()
            
            if row:
                state = dict(row)
                if state["metadata"]:
                    state["metadata"] = json.loads(state["metadata"])
                if state["depends_on"]:
                    state["depends_on"] = json.loads(state["depends_on"])
                return state
            return None
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get resource state: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_dependent_resources(self, resource_id: str) -> List[Dict[str, Any]]:
        """
        Get all resources that depend on the given resource.
        
        Args:
            resource_id: ID of resource to check dependencies for
            
        Returns:
            List of dependent resources
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM resources")
            rows = cursor.fetchall()
            
            dependents = []
            for row in rows:
                state = dict(row)
                if state["depends_on"]:
                    deps = json.loads(state["depends_on"])
                    if resource_id in deps:
                        if state["metadata"]:
                            state["metadata"] = json.loads(state["metadata"])
                        state["depends_on"] = deps
                        dependents.append(state)
            
            return dependents
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get dependent resources: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_all_resources(self) -> List[Dict[str, Any]]:
        """Get all tracked resources."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM resources WHERE status = 'deployed'")
            rows = cursor.fetchall()
            
            resources = []
            for row in rows:
                state = dict(row)
                if state["metadata"]:
                    state["metadata"] = json.loads(state["metadata"])
                if state["depends_on"]:
                    state["depends_on"] = json.loads(state["depends_on"])
                resources.append(state)
            
            return resources
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get all resources: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def create_checkpoint(self, description: str) -> str:
        """
        Create a state checkpoint for rollback.
        
        Args:
            description: Description of checkpoint
            
        Returns:
            Checkpoint ID
        """
        conn = None
        try:
            checkpoint_id = str(uuid.uuid4())
            resources = self.get_all_resources()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO checkpoints (
                    checkpoint_id, description, resource_count, state_snapshot
                ) VALUES (?, ?, ?, ?)
            """, (
                checkpoint_id,
                description,
                len(resources),
                json.dumps(resources)
            ))
            
            conn.commit()
            logger.info(f"Created checkpoint {checkpoint_id}: {description}")
            
            return checkpoint_id
            
        except sqlite3.Error as e:
            logger.error(f"Failed to create checkpoint: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List all checkpoints."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT checkpoint_id, description, timestamp, resource_count
                FROM checkpoints
                ORDER BY timestamp DESC
            """)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Restore state to a checkpoint.
        
        Args:
            checkpoint_id: ID of checkpoint to restore
            
        Returns:
            True if successful
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get checkpoint
            cursor.execute("""
                SELECT state_snapshot FROM checkpoints WHERE checkpoint_id = ?
            """, (checkpoint_id,))
            
            row = cursor.fetchone()
            if not row:
                logger.error(f"Checkpoint {checkpoint_id} not found")
                return False
            
            snapshot = json.loads(row["state_snapshot"])
            
            # Clear current state and restore snapshot
            cursor.execute("DELETE FROM resources")
            
            for resource in snapshot:
                cursor.execute("""
                    INSERT INTO resources (
                        resource_id, resource_type, name, metadata,
                        agent_type, depends_on, status, deployed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    resource["resource_id"],
                    resource["resource_type"],
                    resource["name"],
                    json.dumps(resource["metadata"]),
                    resource["agent_type"],
                    json.dumps(resource["depends_on"]) if resource.get("depends_on") else None,
                    resource["status"],
                    resource["deployed_at"]
                ))
            
            conn.commit()
            logger.info(f"Restored checkpoint {checkpoint_id}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Failed to restore checkpoint: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_rollback_plan(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Get rollback plan without executing.
        
        Args:
            checkpoint_id: Target checkpoint
            
        Returns:
            Rollback plan with resources to add/remove
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get checkpoint state
            cursor.execute("""
                SELECT state_snapshot FROM checkpoints WHERE checkpoint_id = ?
            """, (checkpoint_id,))
            
            row = cursor.fetchone()
            if not row:
                return {"error": "Checkpoint not found"}
            
            checkpoint_resources = json.loads(row["state_snapshot"])
            checkpoint_ids = {r["resource_id"] for r in checkpoint_resources}
            
            # Get current state
            current_resources = self.get_all_resources()
            current_ids = {r["resource_id"] for r in current_resources}
            
            # Determine differences
            to_remove = current_ids - checkpoint_ids
            to_add = checkpoint_ids - current_ids
            
            # Order removals respecting dependencies (dependents first)
            ordered_removals = self._topological_sort_removals(
                [r for r in current_resources if r["resource_id"] in to_remove]
            )
            
            return {
                "checkpoint_id": checkpoint_id,
                "resources_to_remove": ordered_removals,
                "resources_to_add": list(to_add),
                "unchanged": list(current_ids & checkpoint_ids)
            }
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get rollback plan: {e}")
            return {"error": str(e)}
        finally:
            if conn:
                conn.close()
    
    def _topological_sort_removals(self, resources: List[Dict[str, Any]]) -> List[str]:
        """
        Sort resources for removal (dependents before dependencies).
        
        Args:
            resources: List of resources to sort
            
        Returns:
            Ordered list of resource IDs
        """
        # Build dependency graph
        graph = {r["resource_id"]: r.get("depends_on") or [] for r in resources}
        
        # Reverse graph for removal order (dependents before dependencies)
        reverse_graph = {rid: [] for rid in graph}
        for rid, deps in graph.items():
            for dep in deps:
                if dep in reverse_graph:
                    reverse_graph[dep].append(rid)
        
        # Topological sort using DFS
        visited = set()
        result = []
        
        def visit(node):
            if node in visited:
                return
            visited.add(node)
            for dependent in reverse_graph.get(node, []):
                visit(dependent)
            result.append(node)
        
        for node in reverse_graph:
            visit(node)
        
        return result
    
    def rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Execute rollback to checkpoint.
        
        Args:
            checkpoint_id: Target checkpoint
            
        Returns:
            True if successful
        """
        return self.restore_checkpoint(checkpoint_id)
    
    def rollback_resources(self, resource_ids: List[str]) -> bool:
        """
        Rollback specific resources.
        
        Args:
            resource_ids: List of resource IDs to rollback
            
        Returns:
            True if successful
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for resource_id in resource_ids:
                cursor.execute("""
                    UPDATE resources SET status = 'removed'
                    WHERE resource_id = ?
                """, (resource_id,))
            
            conn.commit()
            logger.info(f"Rolled back {len(resource_ids)} resources")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Failed to rollback resources: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_resources_by_type(self, resource_type: str) -> List[Dict[str, Any]]:
        """Get resources filtered by type."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM resources
                WHERE resource_type = ? AND status = 'deployed'
            """, (resource_type,))
            
            rows = cursor.fetchall()
            
            resources = []
            for row in rows:
                state = dict(row)
                if state["metadata"]:
                    state["metadata"] = json.loads(state["metadata"])
                if state["depends_on"]:
                    state["depends_on"] = json.loads(state["depends_on"])
                resources.append(state)
            
            return resources
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get resources by type: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_resources_by_agent(self, agent_type: str) -> List[Dict[str, Any]]:
        """Get resources filtered by agent type."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM resources
                WHERE agent_type = ? AND status = 'deployed'
            """, (agent_type,))
            
            rows = cursor.fetchall()
            
            resources = []
            for row in rows:
                state = dict(row)
                if state["metadata"]:
                    state["metadata"] = json.loads(state["metadata"])
                if state["depends_on"]:
                    state["depends_on"] = json.loads(state["depends_on"])
                resources.append(state)
            
            return resources
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get resources by agent: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_deployment_timeline(self) -> List[Dict[str, Any]]:
        """Get deployment timeline ordered by time."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT resource_id, name, resource_type, agent_type, deployed_at AS timestamp
                FROM resources
                WHERE status = 'deployed'
                ORDER BY deployed_at ASC
            """)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get deployment timeline: {e}")
            return []
        finally:
            if conn:
                conn.close()
