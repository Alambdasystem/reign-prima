"""
Generate sample data for the REIGN dashboard.
Populates databases with test executions and deployments.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
import uuid
import json

# Database paths
home = Path.home()
memory_db = home / ".reign" / "memory" / "agent_memory.db"
state_db = home / ".reign" / "state" / "state_manager.db"

# Ensure directories exist
memory_db.parent.mkdir(parents=True, exist_ok=True)
state_db.parent.mkdir(parents=True, exist_ok=True)

# Agent types and tasks
agents = ["DockerAgent", "K8sAgent", "TerraformAgent", "ReignGeneral"]
tasks = [
    "deploy_container",
    "create_deployment",
    "apply_terraform",
    "scale_pods",
    "build_image",
    "create_service",
    "setup_network",
    "configure_storage"
]

resource_types = ["docker_container", "k8s_deployment", "k8s_service", "terraform_resource"]
resource_names = [
    "web-api", "database", "redis-cache", "nginx-proxy",
    "worker-queue", "monitoring", "logging", "backup-service"
]

def populate_memory():
    """Add sample execution data to AgentMemory."""
    conn = sqlite3.connect(memory_db)
    cursor = conn.cursor()
    
    # Create table if not exists
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
    
    # Generate 100 sample executions
    base_time = datetime.now() - timedelta(hours=24)
    
    for i in range(100):
        agent = random.choice(agents)
        task = random.choice(tasks)
        success = random.random() > 0.15  # 85% success rate
        execution_time = random.uniform(0.5, 3.5)
        timestamp = base_time + timedelta(minutes=random.randint(0, 1440))
        
        error = None if success else random.choice([
            "Connection timeout",
            "Resource already exists",
            "Permission denied",
            "Invalid configuration"
        ])
        
        cursor.execute("""
            INSERT INTO memories (
                task_id, description, agent_type, parameters, success,
                confidence, execution_time, output, error, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            i,
            task,
            agent,
            json.dumps({"task": task, "target": f"resource-{i}"}),
            1 if success else 0,
            random.uniform(0.7, 1.0) if success else random.uniform(0.3, 0.7),
            execution_time,
            json.dumps({"status": "success" if success else "failed"}),
            error,
            timestamp.isoformat()
        ))
    
    conn.commit()
    conn.close()
    print(f"✓ Added 100 memory records to {memory_db}")

def populate_state():
    """Add sample deployment data to StateManager."""
    conn = sqlite3.connect(state_db)
    cursor = conn.cursor()
    
    # Create tables if not exists
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
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checkpoints (
            checkpoint_id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            resource_count INTEGER,
            state_snapshot TEXT NOT NULL
        )
    """)
    
    # Generate 25 sample deployments
    base_time = datetime.now() - timedelta(hours=48)
    
    for i in range(25):
        resource_type = random.choice(resource_types)
        name = random.choice(resource_names) + f"-{i}"
        agent = random.choice(agents[:3])  # Docker, K8s, Terraform
        status = random.choice(["deployed", "deployed", "deployed", "pending", "failed"])
        timestamp = base_time + timedelta(hours=random.randint(0, 48))
        
        cursor.execute("""
            INSERT INTO resources (
                resource_id, resource_type, name, metadata, agent_type,
                depends_on, status, deployed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            resource_type,
            name,
            json.dumps({"region": "us-west-2", "env": "production"}),
            agent,
            json.dumps([]) if i == 0 else json.dumps([f"resource-{i-1}"]),
            status,
            timestamp.isoformat()
        ))
    
    # Add a checkpoint
    cursor.execute("""
        INSERT INTO checkpoints (
            checkpoint_id, description, resource_count, state_snapshot
        ) VALUES (?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        "Pre-deployment checkpoint",
        15,
        json.dumps([{"id": f"res-{i}", "type": "container"} for i in range(15)])
    ))
    
    conn.commit()
    conn.close()
    print(f"✓ Added 25 deployment records to {state_db}")

if __name__ == "__main__":
    print("Generating sample dashboard data...")
    print("=" * 50)
    populate_memory()
    populate_state()
    print("\nSample data generated successfully!")
    print("\nRun the dashboard to see the data:")
    print("  python reign_dashboard.py")
