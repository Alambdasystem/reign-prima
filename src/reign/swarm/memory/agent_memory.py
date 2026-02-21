"""
AgentMemory - Learning and optimization from past executions.

This module provides persistent memory for the REIGN system, enabling:
- Storage of successful execution patterns
- Tracking of failure modes and solutions
- Learning from past task decompositions
- Optimization based on historical performance
"""

import sqlite3
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from reign.swarm.reign_general import Task
from reign.swarm.agents.docker_agent import AgentResult


logger = logging.getLogger(__name__)


class AgentMemory:
    """
    Persistent memory for agent learning and optimization.
    
    Stores execution history in SQLite database for:
    - Pattern recognition
    - Success/failure tracking
    - Performance optimization
    - Historical trend analysis
    """
    
    def __init__(self, storage_path: Optional[str] = None, retention_days: int = 90):
        """
        Initialize AgentMemory.
        
        Args:
            storage_path: Directory for SQLite database (default: ~/.reign/memory)
            retention_days: Days to retain old memories (default: 90)
        """
        if storage_path is None:
            storage_path = str(Path.home() / ".reign" / "memory")
        
        self.storage_path = storage_path
        self.retention_days = retention_days
        
        # Ensure storage directory exists
        Path(storage_path).mkdir(parents=True, exist_ok=True)
        
        # Database path
        self.db_path = Path(storage_path) / "agent_memory.db"
        
        # Initialize database
        self._init_database()
        
        logger.info(f"AgentMemory initialized with storage at {self.db_path}")
    
    def _init_database(self):
        """Initialize SQLite database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create memories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    description TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    parameters TEXT,
                    success BOOLEAN NOT NULL,
                    confidence REAL,
                    execution_time REAL,
                    output TEXT,
                    error TEXT,
                    solution TEXT,
                    context TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_type 
                ON memories(agent_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_success 
                ON memories(success)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON memories(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_description 
                ON memories(description)
            """)
            
            conn.commit()
            conn.close()
            
            logger.debug("Database schema initialized successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            # If database is corrupted, close connection, remove and recreate
            try:
                if 'conn' in locals():
                    conn.close()
            except:
                pass
            if self.db_path.exists():
                logger.warning("Removing corrupted database and recreating")
                try:
                    self.db_path.unlink()
                except PermissionError:
                    # On Windows, might need a moment for file handles to release
                    import time
                    time.sleep(0.1)
                    try:
                        self.db_path.unlink()
                    except PermissionError:
                        # If still locked, just create with different name
                        logger.warning("Could not delete corrupted file, creating new database")
                        self.db_path = Path(self.storage_path) / f"agent_memory_{os.getpid()}.db"
                # Retry initialization
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id INTEGER,
                        description TEXT NOT NULL,
                        agent_type TEXT NOT NULL,
                        parameters TEXT,
                        success BOOLEAN NOT NULL,
                        confidence REAL,
                        execution_time REAL,
                        output TEXT,
                        error TEXT,
                        solution TEXT,
                        context TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                conn.close()
    
    def remember_success(
        self,
        task: Task,
        result: AgentResult,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Store a successful task execution.
        
        Args:
            task: The task that was executed
            result: The successful result
            context: Additional context (environment, config, etc.)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO memories (
                    task_id, description, agent_type, parameters,
                    success, confidence, execution_time, output, context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.description,
                task.agent_type,
                json.dumps(task.params) if task.params else None,
                True,
                result.confidence,
                result.execution_time,
                json.dumps(result.output) if result.output else None,
                json.dumps(context) if context else None
            ))
            
            conn.commit()
            
            logger.debug(f"Remembered success for task {task.id}: {task.description}")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to remember success: {e}")
        finally:
            if conn:
                conn.close()
    
    def remember_failure(
        self,
        task: Task,
        error: str,
        solution: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Store a failed task execution with solution.
        
        Args:
            task: The task that failed
            error: Error message
            solution: How the error was resolved (if known)
            context: Additional context
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO memories (
                    task_id, description, agent_type, parameters,
                    success, error, solution, context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.description,
                task.agent_type,
                json.dumps(task.params) if task.params else None,
                False,
                error,
                solution,
                json.dumps(context) if context else None
            ))
            
            conn.commit()
            
            logger.debug(f"Remembered failure for task {task.id}: {error}")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to remember failure: {e}")
        finally:
            if conn:
                conn.close()
    
    def get_similar_tasks(
        self,
        task: Task,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find similar tasks in memory.
        
        Args:
            task: Task to find similar memories for
            limit: Maximum number of results
            
        Returns:
            List of similar task memories, ordered by relevance
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get agent type as string
            agent_type = task.agent_type
            
            # Search by agent type and description similarity
            # For now, use simple keyword matching
            # Future: implement semantic similarity
            cursor.execute("""
                SELECT 
                    task_id, description, agent_type, parameters,
                    success, confidence, execution_time, output,
                    error, solution, context, timestamp
                FROM memories
                WHERE agent_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (agent_type, limit))
            
            rows = cursor.fetchall()
            
            # Convert to dict list
            memories = []
            for row in rows:
                memory = dict(row)
                # Parse JSON fields
                if memory["parameters"]:
                    memory["parameters"] = json.loads(memory["parameters"])
                if memory["output"]:
                    memory["output"] = json.loads(memory["output"])
                if memory["context"]:
                    memory["context"] = json.loads(memory["context"])
                memories.append(memory)
            
            logger.debug(f"Found {len(memories)} similar tasks for agent {agent_type}")
            return memories
            
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve similar tasks: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def suggest_improvements(self, task: Task) -> Dict[str, Any]:
        """
        Suggest improvements based on historical patterns.
        
        Args:
            task: Task to get suggestions for
            
        Returns:
            Dictionary with suggestions and confidence scores
        """
        similar_tasks = self.get_similar_tasks(task, limit=20)
        
        if not similar_tasks:
            return {
                "suggestions": [],
                "confidence": 0.0,
                "message": "No historical data available"
            }
        
        # Analyze patterns
        successful_tasks = [t for t in similar_tasks if t["success"]]
        failed_tasks = [t for t in similar_tasks if not t["success"]]
        
        suggestions = []
        
        # Suggest based on high-confidence successes
        if successful_tasks:
            # Find highest confidence task
            best_task = max(successful_tasks, key=lambda t: t.get("confidence", 0.0))
            
            if best_task.get("confidence", 0.0) > 0.8:
                suggestions.append({
                    "type": "parameter_optimization",
                    "description": f"Consider using parameters from high-confidence execution",
                    "parameters": best_task.get("parameters"),
                    "confidence": best_task.get("confidence"),
                    "execution_time": best_task.get("execution_time")
                })
        
        # Warn about common failures
        if failed_tasks:
            # Group failures by error
            error_counts = {}
            for task in failed_tasks:
                error = task.get("error", "Unknown error")
                if error not in error_counts:
                    error_counts[error] = {
                        "count": 0,
                        "solution": task.get("solution")
                    }
                error_counts[error]["count"] += 1
            
            # Add warnings for common errors
            for error, data in error_counts.items():
                if data["count"] >= 2:  # Common error
                    suggestions.append({
                        "type": "failure_warning",
                        "description": f"Common failure: {error}",
                        "occurrences": data["count"],
                        "solution": data["solution"]
                    })
        
        # Calculate overall confidence
        success_rate = len(successful_tasks) / len(similar_tasks) if similar_tasks else 0.0
        
        return {
            "suggestions": suggestions,
            "confidence": success_rate,
            "total_similar_tasks": len(similar_tasks),
            "success_rate": success_rate
        }
    
    def get_pattern_statistics(self, task: Task) -> Dict[str, Any]:
        """
        Get statistical analysis for similar task patterns.
        
        Args:
            task: Task to analyze patterns for
            
        Returns:
            Dictionary with statistics (success rate, avg time, etc.)
        """
        similar_tasks = self.get_similar_tasks(task, limit=50)
        
        if not similar_tasks:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "average_execution_time": 0.0,
                "average_confidence": 0.0
            }
        
        successes = [t for t in similar_tasks if t["success"]]
        failures = [t for t in similar_tasks if not t["success"]]
        
        # Calculate statistics
        total = len(similar_tasks)
        success_count = len(successes)
        success_rate = success_count / total if total > 0 else 0.0
        
        # Average execution time (successful tasks only)
        exec_times = [t["execution_time"] for t in successes if t.get("execution_time")]
        avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0.0
        
        # Average confidence (successful tasks only)
        confidences = [t["confidence"] for t in successes if t.get("confidence")]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "total_executions": total,
            "successful_executions": success_count,
            "failed_executions": len(failures),
            "success_rate": success_rate,
            "average_execution_time": avg_exec_time,
            "average_confidence": avg_confidence
        }
    
    def cleanup_old_memories(self):
        """Remove memories older than retention period."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            cursor.execute("""
                DELETE FROM memories
                WHERE timestamp < ?
            """, (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Cleaned up {deleted_count} old memories (>{self.retention_days} days)")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup old memories: {e}")
        finally:
            if conn:
                conn.close()
    
    def clear_all(self):
        """Clear all stored memories (for testing/reset)."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM memories")
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.warning(f"Cleared all memories ({deleted_count} records)")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to clear memories: {e}")
        finally:
            if conn:
                conn.close()
