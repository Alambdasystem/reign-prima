"""
REIGN Desktop Dashboard - Main Application

A desktop monitoring dashboard built with Dear PyGui for real-time
infrastructure and agent monitoring.
"""

import dearpygui.dearpygui as dpg
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
import json
from typing import Dict, List, Any, Optional
import threading
import time
import traceback
import sys

# Add src to path for imports - go up 3 levels from dashboard_app.py to reach src/
_src_path = str(Path(__file__).resolve().parent.parent.parent)
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# Import REIGN components with detailed error tracking
REIGN_AVAILABLE = False
import_error = ""
ReignGeneral = None
Task = None
DockerAgent = None
K8sAgent = None
AgentMemory = None
StateManager = None

try:
    from reign.swarm.reign_general import ReignGeneral, Task
    from reign.swarm.agents.docker_agent import DockerAgent
    from reign.swarm.memory.agent_memory import AgentMemory
    from reign.swarm.state.state_manager import StateManager, ResourceState
    
    # K8s is optional - try both names
    try:
        from reign.swarm.agents.kubernetes_agent import KubernetesAgent as K8sAgent
    except ImportError:
        try:
            from reign.swarm.agents.k8s_agent import K8sAgent
        except ImportError:
            K8sAgent = None
    
    REIGN_AVAILABLE = True
except ImportError as e:
    import_error = f"Import failed: {e}\nPython path: {sys.path[:3]}\nSrc path: {_src_path}"


class ReignDashboard:
    """Main dashboard application for REIGN monitoring."""
    
    def __init__(self, memory_db_path: Optional[str] = None, state_db_path: Optional[str] = None):
        """Initialize the dashboard.
        
        Args:
            memory_db_path: Path to AgentMemory database (default: ~/.reign/memory/agent_memory.db)
            state_db_path: Path to StateManager database (default: ~/.reign/state/state_manager.db)
        """
        # Database paths
        home = Path.home()
        self.memory_db = memory_db_path or str(home / ".reign" / "memory" / "agent_memory.db")
        self.state_db = state_db_path or str(home / ".reign" / "state" / "state_manager.db")
        
        # Ensure database directories exist
        Path(self.memory_db).parent.mkdir(parents=True, exist_ok=True)
        Path(self.state_db).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize databases if they don't exist
        self._init_databases()
        
        # UI state
        self.running = False
        self.refresh_interval = 2.0  # seconds
        self.log_messages = []
        self.max_log_messages = 100
        
        # Data cache
        self.agent_stats = {}
        self.memory_stats = {}
        self.deployments = []
        self.recent_tasks = []
        
        # REIGN components
        self.agent_memory = None
        self.state_manager = None
        self.reign_general = None
        self.docker_agent = None
        self.k8s_agent = None
        self.reign_available = REIGN_AVAILABLE
        
        print(f"REIGN_AVAILABLE = {REIGN_AVAILABLE}")
        
        # Initialize REIGN if available
        if self.reign_available:
            try:
                print("Initializing AgentMemory...")
                self.agent_memory = AgentMemory(storage_path=str(Path(self.memory_db).parent))
                print("✓ AgentMemory created")
                
                print("Initializing StateManager...")
                self.state_manager = StateManager(storage_path=str(Path(self.state_db).parent))
                print("✓ StateManager created")
                
                print("Initializing DockerAgent...")
                self.docker_agent = DockerAgent()
                print("✓ DockerAgent created")
                
                # K8s agent is optional
                if K8sAgent:
                    print("Initializing KubernetesAgent...")
                    self.k8s_agent = K8sAgent()
                    print("✓ KubernetesAgent created")
                else:
                    print("KubernetesAgent not available (optional)")
                
                print("Initializing ReignGeneral...")
                self.reign_general = ReignGeneral()  # Just llm_config, no agents/memory/state
                print("✓ ReignGeneral created")
                print("✓✓✓ REIGN agents initialized successfully!")
            except Exception as e:
                print(f"✗ Failed to initialize REIGN agents: {e}")
                import traceback
                traceback.print_exc()
                self.reign_available = False
        else:
            print("REIGN not available (import failed)")
        
    def _init_databases(self):
        """Initialize database connections and tables if needed."""
        # Memory database
        if not Path(self.memory_db).exists():
            conn = sqlite3.connect(self.memory_db)
            conn.execute("""
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
        
        # State database
        if not Path(self.state_db).exists():
            conn = sqlite3.connect(self.state_db)
            conn.execute("""
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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resource_count INTEGER,
                    state_snapshot TEXT NOT NULL
                )
            """)
            conn.commit()
            conn.close()
    
    def _log(self, message: str, level: str = "INFO"):
        """Add a log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.log_messages.append(log_entry)
        
        # Keep only recent messages
        if len(self.log_messages) > self.max_log_messages:
            self.log_messages = self.log_messages[-self.max_log_messages:]
        
        # Update log window if it exists
        if dpg.does_item_exist("log_text"):
            dpg.set_value("log_text", "\n".join(reversed(self.log_messages)))
    
    def _fetch_agent_stats(self) -> Dict[str, Any]:
        """Fetch agent execution statistics from memory database."""
        try:
            conn = sqlite3.connect(self.memory_db)
            cursor = conn.cursor()
            
            # Total executions
            cursor.execute("SELECT COUNT(*) FROM memories")
            total = cursor.fetchone()[0]
            
            # Success rate
            cursor.execute("SELECT COUNT(*) FROM memories WHERE success = 1")
            successes = cursor.fetchone()[0]
            success_rate = (successes / total * 100) if total > 0 else 0
            
            # By agent
            cursor.execute("""
                SELECT agent_type, 
                       COUNT(*) as total,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                       AVG(execution_time) as avg_time
                FROM memories
                GROUP BY agent_type
            """)
            agents = []
            for row in cursor.fetchall():
                agents.append({
                    "name": row[0],
                    "total": row[1],
                    "successes": row[2],
                    "success_rate": (row[2] / row[1] * 100) if row[1] > 0 else 0,
                    "avg_time": row[3] or 0
                })
            
            # Recent failures
            cursor.execute("""
                SELECT agent_type, description, error, timestamp
                FROM memories
                WHERE success = 0
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            recent_failures = [
                {
                    "agent": row[0],
                    "task": row[1],
                    "error": row[2],
                    "time": row[3]
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return {
                "total_executions": total,
                "success_rate": success_rate,
                "agents": agents,
                "recent_failures": recent_failures
            }
        except Exception as e:
            self._log(f"Error fetching agent stats: {e}", "ERROR")
            return {
                "total_executions": 0,
                "success_rate": 0,
                "agents": [],
                "recent_failures": []
            }
    
    def _fetch_memory_stats(self) -> Dict[str, Any]:
        """Fetch memory statistics and patterns."""
        try:
            conn = sqlite3.connect(self.memory_db)
            cursor = conn.cursor()
            
            # Task types distribution
            cursor.execute("""
                SELECT agent_type, COUNT(*) as count
                FROM memories
                GROUP BY agent_type
                ORDER BY count DESC
                LIMIT 10
            """)
            task_distribution = [
                {"type": row[0], "count": row[1]}
                for row in cursor.fetchall()
            ]
            
            # Execution timeline (last 24 hours)
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            cursor.execute("""
                SELECT strftime('%H:00', timestamp) as hour,
                       COUNT(*) as count,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes
                FROM memories
                WHERE timestamp > ?
                GROUP BY hour
                ORDER BY hour
            """, (yesterday,))
            timeline = [
                {"hour": row[0], "total": row[1], "successes": row[2]}
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return {
                "task_distribution": task_distribution,
                "timeline": timeline
            }
        except Exception as e:
            self._log(f"Error fetching memory stats: {e}", "ERROR")
            return {
                "task_distribution": [],
                "timeline": []
            }
    
    def _fetch_deployments(self) -> List[Dict[str, Any]]:
        """Fetch current deployments from state database."""
        try:
            conn = sqlite3.connect(self.state_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT resource_id, resource_type, name, status, deployed_at, agent_type
                FROM resources
                ORDER BY deployed_at DESC
                LIMIT 50
            """)
            
            deployments = [
                {
                    "id": row[0][:8] if row[0] else "N/A",  # Short ID
                    "type": row[1],
                    "name": row[2],
                    "status": row[3],
                    "deployed_at": row[4],
                    "deployed_by": row[5] or "unknown"
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            return deployments
        except Exception as e:
            self._log(f"Error fetching deployments: {e}", "ERROR")
            return []
    
    def _fetch_recent_tasks(self) -> List[Dict[str, Any]]:
        """Fetch recent task executions."""
        try:
            conn = sqlite3.connect(self.memory_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT agent_type, description, success, execution_time, timestamp
                FROM memories
                ORDER BY timestamp DESC
                LIMIT 20
            """)
            
            tasks = [
                {
                    "agent": row[0],
                    "task": row[1],
                    "success": bool(row[2]),
                    "time": f"{row[3]:.2f}s" if row[3] else "N/A",
                    "timestamp": row[4]
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            return tasks
        except Exception as e:
            self._log(f"Error fetching recent tasks: {e}", "ERROR")
            return []
    
    def _update_data(self):
        """Update all dashboard data."""
        self.agent_stats = self._fetch_agent_stats()
        self.memory_stats = self._fetch_memory_stats()
        self.deployments = self._fetch_deployments()
        self.recent_tasks = self._fetch_recent_tasks()
    
    def _refresh_loop(self):
        """Background thread for data refresh."""
        while self.running:
            try:
                self._update_data()
                self._update_ui()
                time.sleep(self.refresh_interval)
            except Exception as e:
                self._log(f"Refresh error: {e}", "ERROR")
    
    def _update_ui(self):
        """Update UI elements with fresh data."""
        # Update overview stats
        if dpg.does_item_exist("total_executions"):
            dpg.set_value("total_executions", f"Total: {self.agent_stats['total_executions']}")
        if dpg.does_item_exist("success_rate"):
            dpg.set_value("success_rate", f"Success: {self.agent_stats['success_rate']:.1f}%")
        if dpg.does_item_exist("deployment_count"):
            dpg.set_value("deployment_count", f"Deployments: {len(self.deployments)}")
        
        # Update agent table
        if dpg.does_item_exist("agent_table"):
            dpg.delete_item("agent_table", children_only=True)
            for agent in self.agent_stats['agents']:
                with dpg.table_row(parent="agent_table"):
                    dpg.add_text(agent['name'])
                    dpg.add_text(str(agent['total']))
                    dpg.add_text(f"{agent['success_rate']:.1f}%")
                    dpg.add_text(f"{agent['avg_time']:.2f}s")
        
        # Update recent tasks table
        if dpg.does_item_exist("tasks_table"):
            dpg.delete_item("tasks_table", children_only=True)
            for task in self.recent_tasks[:10]:
                with dpg.table_row(parent="tasks_table"):
                    dpg.add_text(task['agent'])
                    dpg.add_text(task['task'])
                    status_color = [0, 255, 0] if task['success'] else [255, 0, 0]
                    dpg.add_text("✓" if task['success'] else "✗", color=status_color)
                    dpg.add_text(task['time'])
        
        # Update deployments table
        if dpg.does_item_exist("deploy_table"):
            dpg.delete_item("deploy_table", children_only=True)
            for dep in self.deployments[:15]:
                with dpg.table_row(parent="deploy_table"):
                    dpg.add_text(dep['id'])
                    dpg.add_text(dep['type'])
                    dpg.add_text(dep['name'])
                    dpg.add_text(dep['status'])
                    dpg.add_text(dep['deployed_by'])
    
    def _create_overview_tab(self):
        """Create the overview tab."""
        with dpg.tab(label="Overview"):
            # Stats row
            with dpg.group(horizontal=True):
                with dpg.child_window(width=250, height=100):
                    dpg.add_text("Execution Stats", color=[100, 200, 255])
                    dpg.add_text("Total: 0", tag="total_executions")
                    dpg.add_text("Success: 0%", tag="success_rate")
                
                dpg.add_spacer(width=10)
                
                with dpg.child_window(width=250, height=100):
                    dpg.add_text("Infrastructure", color=[100, 200, 255])
                    dpg.add_text("Deployments: 0", tag="deployment_count")
                    dpg.add_text("Active Agents: 0", tag="active_agents")
            
            dpg.add_spacer(height=10)
            
            # Agent performance table
            dpg.add_text("Agent Performance", color=[100, 200, 255])
            with dpg.table(header_row=True, tag="agent_table",
                          borders_innerH=True, borders_outerH=True,
                          borders_innerV=True, borders_outerV=True,
                          resizable=True):
                dpg.add_table_column(label="Agent")
                dpg.add_table_column(label="Executions")
                dpg.add_table_column(label="Success Rate")
                dpg.add_table_column(label="Avg Time")
    
    def _create_tasks_tab(self):
        """Create the recent tasks tab."""
        with dpg.tab(label="Recent Tasks"):
            dpg.add_text("Last 10 Task Executions", color=[100, 200, 255])
            dpg.add_spacer(height=5)
            
            with dpg.table(header_row=True, tag="tasks_table",
                          borders_innerH=True, borders_outerH=True,
                          borders_innerV=True, borders_outerV=True,
                          resizable=True, scrollY=True, height=500):
                dpg.add_table_column(label="Agent", width_fixed=True, init_width_or_weight=150)
                dpg.add_table_column(label="Task Type", width_fixed=True, init_width_or_weight=200)
                dpg.add_table_column(label="Status", width_fixed=True, init_width_or_weight=60)
                dpg.add_table_column(label="Time", width_fixed=True, init_width_or_weight=80)
    
    def _create_deployments_tab(self):
        """Create the deployments tab."""
        with dpg.tab(label="Deployments"):
            dpg.add_text("Infrastructure Deployments", color=[100, 200, 255])
            dpg.add_spacer(height=5)
            
            with dpg.table(header_row=True, tag="deploy_table",
                          borders_innerH=True, borders_outerH=True,
                          borders_innerV=True, borders_outerV=True,
                          resizable=True, scrollY=True, height=500):
                dpg.add_table_column(label="ID", width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label="Type", width_fixed=True, init_width_or_weight=120)
                dpg.add_table_column(label="Name", width_fixed=True, init_width_or_weight=200)
                dpg.add_table_column(label="Status", width_fixed=True, init_width_or_weight=100)
                dpg.add_table_column(label="Deployed By", width_fixed=True, init_width_or_weight=150)
    
    def _create_control_tab(self):
        """Create the control panel tab."""
        with dpg.tab(label="Control Panel"):
            dpg.add_text(f"REIGN Status: {'Available' if self.reign_available else 'Not Available'}", 
                        color=[0, 255, 0] if self.reign_available else [255, 100, 100])
            
            if not self.reign_available:
                dpg.add_text("Check Activity Log tab for error details", color=[255, 200, 100])
                dpg.add_text(import_error, color=[255, 100, 100], wrap=600)
                return
            
            dpg.add_text("Agent Control Center", color=[100, 200, 255])
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            # Docker Controls
            with dpg.collapsing_header(label="Docker Agent", default_open=True):
                with dpg.group(horizontal=True):
                    dpg.add_text("Image:", color=[200, 200, 200])
                    dpg.add_input_text(tag="docker_image", default_value="nginx:latest", width=200)
                with dpg.group(horizontal=True):
                    dpg.add_text("Name:", color=[200, 200, 200])
                    dpg.add_input_text(tag="docker_name", default_value="my-container", width=200)
                with dpg.group(horizontal=True):
                    dpg.add_text("Port:", color=[200, 200, 200])
                    dpg.add_input_text(tag="docker_port", default_value="8080:80", width=200)
                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Deploy Container", callback=self._deploy_docker_container)
                    dpg.add_button(label="List Containers", callback=self._list_docker_containers)
            
            dpg.add_spacer(height=10)
            
            # Kubernetes Controls (only if available)
            if self.k8s_agent:
                with dpg.collapsing_header(label="Kubernetes Agent", default_open=True):
                    with dpg.group(horizontal=True):
                        dpg.add_text("Deployment:", color=[200, 200, 200])
                        dpg.add_input_text(tag="k8s_name", default_value="my-deployment", width=200)
                    with dpg.group(horizontal=True):
                        dpg.add_text("Image:", color=[200, 200, 200])
                        dpg.add_input_text(tag="k8s_image", default_value="nginx:latest", width=200)
                    with dpg.group(horizontal=True):
                        dpg.add_text("Replicas:", color=[200, 200, 200])
                        dpg.add_input_int(tag="k8s_replicas", default_value=3, width=200)
                    dpg.add_spacer(height=5)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Create Deployment", callback=self._deploy_k8s_deployment)
                        dpg.add_button(label="List Deployments", callback=self._list_k8s_deployments)
            else:
                with dpg.collapsing_header(label="Kubernetes Agent (Not Available)", default_open=False):
                    dpg.add_text("K8s agent not installed", color=[150, 150, 150])
            
            dpg.add_spacer(height=10)
            
            # State Management Controls
            with dpg.collapsing_header(label="State Management", default_open=True):
                with dpg.group(horizontal=True):
                    dpg.add_text("Checkpoint:", color=[200, 200, 200])
                    dpg.add_input_text(tag="checkpoint_name", default_value="backup-checkpoint", width=200)
                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Create Checkpoint", callback=self._create_checkpoint)
                    dpg.add_button(label="List Checkpoints", callback=self._list_checkpoints)
                    dpg.add_button(label="Rollback", callback=self._show_rollback_dialog)
            
            dpg.add_spacer(height=10)
            
            # ReignGeneral Orchestration
            with dpg.collapsing_header(label="ReignGeneral Orchestration", default_open=True):
                dpg.add_text("Task Description:", color=[200, 200, 200])
                dpg.add_input_text(tag="task_description", multiline=True, height=80, width=500,
                                 default_value="Deploy a web application with 3 replicas")
                dpg.add_spacer(height=5)
                dpg.add_button(label="Execute Task", callback=self._execute_reign_task)
    
    def _create_logs_tab(self):
        """Create the logs tab."""
        with dpg.tab(label="Activity Log"):
            dpg.add_text("Real-time Activity", color=[100, 200, 255])
            dpg.add_spacer(height=5)
            
            dpg.add_input_text(
                tag="log_text",
                multiline=True,
                readonly=True,
                width=-1,
                height=500,
                default_value="Dashboard started...\n"
            )
    
    def run(self):
        """Run the dashboard application."""
        try:
            print("Creating DearPyGUI context...")
            dpg.create_context()
            
            print("Creating main window...")
            # Create main window
            with dpg.window(label="REIGN Dashboard", tag="main_window", width=1200, height=700):
                dpg.add_text("REIGN - Infrastructure Orchestration Monitor", color=[100, 200, 255])
                dpg.add_separator()
                dpg.add_spacer(height=5)
                
                print("Creating tabs...")
                # Tab bar
                with dpg.tab_bar():
                    self._create_overview_tab()
                    self._create_tasks_tab()
                    self._create_deployments_tab()
                    self._create_control_tab()
                    self._create_logs_tab()
            
            print("Setting up viewport...")
            # Setup viewport
            dpg.create_viewport(title="REIGN Dashboard", width=1200, height=700)
            dpg.setup_dearpygui()
            dpg.show_viewport()
            dpg.set_primary_window("main_window", True)
            
            print("Starting background refresh thread...")
            # Start background refresh
            self.running = True
            refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
            refresh_thread.start()
            
            self._log("Dashboard initialized")
            self._log(f"Memory DB: {self.memory_db}")
            self._log(f"State DB: {self.state_db}")
            
            print("Loading initial data...")
            # Initial data load
            self._update_data()
            self._update_ui()
            
            print("Dashboard window should be visible!")
            print("Starting main loop...")
            # Main loop
            while dpg.is_dearpygui_running():
                dpg.render_dearpygui_frame()
        except Exception as e:
            print(f"ERROR in dashboard.run(): {e}")
            print(traceback.format_exc())
        finally:
            print("Cleaning up...")
            self.running = False
            try:
                dpg.destroy_context()
            except:
                pass
    
    # ========== Agent Control Callbacks ==========
    
    def _deploy_docker_container(self):
        """Deploy a Docker container."""
        if not self.docker_agent:
            self._log("Docker agent not available", "ERROR")
            return
        
        image = dpg.get_value("docker_image")
        name = dpg.get_value("docker_name")
        port = dpg.get_value("docker_port")
        
        self._log(f"Deploying Docker container: {name} ({image})", "INFO")
        
        def deploy():
            try:
                task = Task(
                    id=hash(f"docker_{name}_{image}") % 1000000,
                    description=f"Deploy Docker container {name}",
                    agent_type="docker",
                    params={
                        "action": "run",
                        "image": image,
                        "name": name,
                        "ports": {port.split(":")[0]: port.split(":")[1]} if ":" in port else {}
                    }
                )
                result = self.docker_agent.execute(task)
                
                if result.success:
                    self._log(f"✓ Container deployed: {name}", "INFO")
                    # Record in state manager
                    if self.state_manager:
                        resource = ResourceState(
                            resource_id=f"docker_{name}",
                            resource_type="docker_container",
                            name=name,
                            metadata={"image": image, "port": port},
                            agent_type="docker"
                        )
                        self.state_manager.record_deployment(resource)
                else:
                    self._log(f"✗ Deployment failed: {result.error}", "ERROR")
            except Exception as e:
                self._log(f"Error deploying container: {e}", "ERROR")
        
        threading.Thread(target=deploy, daemon=True).start()
    
    def _list_docker_containers(self):
        """List Docker containers."""
        if not self.docker_agent:
            self._log("Docker agent not available", "ERROR")
            return
        
        self._log("Listing Docker containers...", "INFO")
        
        def list_containers():
            try:
                task = Task(
                    id=hash("docker_list") % 1000000,
                    description="List Docker containers",
                    agent_type="docker",
                    params={"action": "list"}
                )
                result = self.docker_agent.execute(task)
                
                if result.success:
                    containers = result.output.get("containers", [])
                    self._log(f"Found {len(containers)} containers", "INFO")
                    for container in containers[:5]:  # Show first 5
                        self._log(f"  - {container.get('name', 'N/A')}: {container.get('status', 'N/A')}", "INFO")
                else:
                    self._log(f"Failed to list containers: {result.error}", "ERROR")
            except Exception as e:
                self._log(f"Error listing containers: {e}", "ERROR")
        
        threading.Thread(target=list_containers, daemon=True).start()
    
    def _deploy_k8s_deployment(self):
        """Deploy a Kubernetes deployment."""
        if not self.k8s_agent:
            self._log("K8s agent not available", "ERROR")
            return
        
        name = dpg.get_value("k8s_name")
        image = dpg.get_value("k8s_image")
        replicas = dpg.get_value("k8s_replicas")
        
        self._log(f"Deploying K8s deployment: {name} ({replicas} replicas)", "INFO")
        
        def deploy():
            try:
                task = Task(
                    id=hash(f"k8s_{name}_{image}") % 1000000,
                    description=f"Deploy K8s deployment {name}",
                    agent_type="kubernetes",
                    params={
                        "action": "create_deployment",
                        "name": name,
                        "image": image,
                        "replicas": replicas
                    }
                )
                result = self.k8s_agent.execute(task)
                
                if result.success:
                    self._log(f"✓ Deployment created: {name}", "INFO")
                    # Record in state manager
                    if self.state_manager:
                        resource = ResourceState(
                            resource_id=f"k8s_{name}",
                            resource_type="k8s_deployment",
                            name=name,
                            metadata={"image": image, "replicas": replicas},
                            agent_type="kubernetes"
                        )
                        self.state_manager.record_deployment(resource)
                else:
                    self._log(f"✗ Deployment failed: {result.error}", "ERROR")
            except Exception as e:
                self._log(f"Error creating deployment: {e}", "ERROR")
        
        threading.Thread(target=deploy, daemon=True).start()
    
    def _list_k8s_deployments(self):
        """List Kubernetes deployments."""
        if not self.k8s_agent:
            self._log("K8s agent not available", "ERROR")
            return
        
        self._log("Listing K8s deployments...", "INFO")
        
        def list_deployments():
            try:
                task = Task(
                    id=hash("k8s_list") % 1000000,
                    description="List K8s deployments",
                    agent_type="kubernetes",
                    params={"action": "list_deployments"}
                )
                result = self.k8s_agent.execute(task)
                
                if result.success:
                    deployments = result.output.get("deployments", [])
                    self._log(f"Found {len(deployments)} deployments", "INFO")
                    for dep in deployments[:5]:  # Show first 5
                        self._log(f"  - {dep.get('name', 'N/A')}: {dep.get('replicas', 'N/A')} replicas", "INFO")
                else:
                    self._log(f"Failed to list deployments: {result.error}", "ERROR")
            except Exception as e:
                self._log(f"Error listing deployments: {e}", "ERROR")
        
        threading.Thread(target=list_deployments, daemon=True).start()
    
    def _create_checkpoint(self):
        """Create a state checkpoint."""
        if not self.state_manager:
            self._log("State manager not available", "ERROR")
            return
        
        name = dpg.get_value("checkpoint_name")
        self._log(f"Creating checkpoint: {name}", "INFO")
        
        try:
            checkpoint_id = self.state_manager.create_checkpoint(
                description=name
            )
            self._log(f"✓ Checkpoint created: {checkpoint_id[:8]}", "INFO")
        except Exception as e:
            self._log(f"Error creating checkpoint: {e}", "ERROR")
    
    def _list_checkpoints(self):
        """List available checkpoints."""
        if not self.state_manager:
            self._log("State manager not available", "ERROR")
            return
        
        self._log("Listing checkpoints...", "INFO")
        
        try:
            checkpoints = self.state_manager.list_checkpoints()
            self._log(f"Found {len(checkpoints)} checkpoints", "INFO")
            for cp in checkpoints[:5]:  # Show first 5
                self._log(f"  - {cp.checkpoint_id[:8]}: {cp.description} ({cp.resource_count} resources)", "INFO")
        except Exception as e:
            self._log(f"Error listing checkpoints: {e}", "ERROR")
    
    def _show_rollback_dialog(self):
        """Show rollback confirmation dialog."""
        if not self.state_manager:
            self._log("State manager not available", "ERROR")
            return
        
        try:
            checkpoints = self.state_manager.list_checkpoints()
            if not checkpoints:
                self._log("No checkpoints available for rollback", "WARNING")
                return
            
            # Create rollback window
            with dpg.window(label="Rollback Confirmation", modal=True, tag="rollback_window", 
                          width=400, height=300, pos=[400, 200]):
                dpg.add_text("Select checkpoint to rollback to:")
                dpg.add_spacer(height=10)
                
                # Checkpoint list
                for cp in checkpoints[:10]:
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label=f"Rollback to: {cp.description}",
                            callback=lambda s, a, u: self._execute_rollback(u),
                            user_data=cp.checkpoint_id,
                            width=350
                        )
                
                dpg.add_spacer(height=10)
                dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item("rollback_window"))
        
        except Exception as e:
            self._log(f"Error showing rollback dialog: {e}", "ERROR")
    
    def _execute_rollback(self, checkpoint_id: str):
        """Execute rollback to checkpoint."""
        dpg.delete_item("rollback_window")
        self._log(f"Rolling back to checkpoint {checkpoint_id[:8]}...", "INFO")
        
        def rollback():
            try:
                plan = self.state_manager.get_rollback_plan(checkpoint_id)
                self._log(f"Rollback will remove {len(plan['resources_to_remove'])} resources", "INFO")
                
                # Execute rollback
                removed = self.state_manager.rollback_to_checkpoint(checkpoint_id)
                self._log(f"✓ Rollback complete: {len(removed)} resources removed", "INFO")
            except Exception as e:
                self._log(f"Error during rollback: {e}", "ERROR")
                self._log(traceback.format_exc(), "ERROR")
        
        threading.Thread(target=rollback, daemon=True).start()
    
    def _execute_reign_task(self):
        """Execute a task using ReignGeneral orchestrator."""
        if not self.reign_general:
            self._log("ReignGeneral not available", "ERROR")
            return
        
        description = dpg.get_value("task_description")
        self._log(f"Executing ReignGeneral task: {description}", "INFO")
        
        def execute():
            try:
                # Decompose the task using ReignGeneral
                tasks = self.reign_general.decompose_task(description)
                self._log(f"✓ Decomposed into {len(tasks)} subtask(s)", "INFO")
                
                # Execute each decomposed task with appropriate agent
                for task in tasks:
                    self._log(f"Executing {task.agent_type} task: {task.description}", "INFO")
                    
                    try:
                        # Route to appropriate agent based on agent_type
                        if task.agent_type == "docker" and self.docker_agent:
                            result = self.docker_agent.execute(task)
                        elif task.agent_type == "kubernetes" and self.k8s_agent:
                            result = self.k8s_agent.execute(task)
                        elif task.agent_type == "terraform" and self.terraform_agent:
                            result = self.terraform_agent.execute(task)
                        else:
                            self._log(f"No agent available for type: {task.agent_type}", "WARNING")
                            continue
                        
                        if result.success:
                            self._log(f"✓ Subtask completed: {task.description}", "INFO")
                            # Record in state manager
                            if self.state_manager:
                                resource = ResourceState(
                                    resource_id=f"{task.agent_type}_{task.id}",
                                    resource_type=task.agent_type,
                                    name=task.description,
                                    metadata=task.params,
                                    agent_type=task.agent_type
                                )
                                self.state_manager.record_deployment(resource)
                        else:
                            self._log(f"✗ Subtask failed: {result.error}", "ERROR")
                    except Exception as e:
                        self._log(f"Error executing subtask: {e}", "ERROR")
                
                self._log(f"✓ ReignGeneral task completed", "INFO")
            except Exception as e:
                self._log(f"Error decomposing task: {e}", "ERROR")
                self._log(traceback.format_exc(), "ERROR")
        
        threading.Thread(target=execute, daemon=True).start()


def main():
    """Entry point for the dashboard."""
    dashboard = ReignDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
