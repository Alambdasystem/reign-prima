# REIGN Desktop Dashboard

A real-time monitoring dashboard for the REIGN infrastructure orchestration system.

## Features

### 📊 Overview Tab
- **Execution Statistics**: Total executions and success rate
- **Infrastructure Status**: Deployment count and active agents
- **Agent Performance Table**: Per-agent metrics including:
  - Total executions
  - Success rate
  - Average execution time

### 📝 Recent Tasks Tab
- Live feed of the last 10 task executions
- Shows agent name, task type, success/failure status, and execution time
- Color-coded status indicators (✓ green = success, ✗ red = failure)

### 🚀 Deployments Tab
- All infrastructure deployments tracked by StateManager
- Shows resource ID, type, name, status, and who deployed it
- Automatically updates as new resources are deployed

### 📋 Activity Log Tab
- Real-time activity log with timestamps
- Dashboard events and errors
- Maintains last 100 log entries

## Installation

The dashboard requires Dear PyGui, which is already installed:

```powershell
pip install dearpygui
```

## Usage

### Quick Start

```powershell
python reign_dashboard.py
```

### Programmatic Usage

```python
from src.reign.dashboard import ReignDashboard

# Use default database paths
dashboard = ReignDashboard()
dashboard.run()

# Or specify custom paths
dashboard = ReignDashboard(
    memory_db_path="path/to/agent_memory.db",
    state_db_path="path/to/state_manager.db"
)
dashboard.run()
```

## Database Locations

The dashboard reads from:
- **AgentMemory**: `~/.reign/memory/agent_memory.db`
- **StateManager**: `~/.reign/state/state_manager.db`

## Refresh Rate

Data refreshes every 2 seconds by default. The dashboard runs a background thread that:
1. Fetches latest data from SQLite databases
2. Updates all UI components
3. Maintains responsiveness

## Technical Details

### Architecture
- **UI Framework**: Dear PyGui (immediate mode GUI)
- **Data Storage**: SQLite databases
- **Threading**: Background refresh thread for non-blocking updates
- **Cross-platform**: Works on Windows, macOS, Linux

### Performance
- Lightweight memory footprint
- Efficient SQLite queries with indexes
- Real-time updates without freezing UI
- Handles thousands of executions smoothly

## Screenshots

```
┌─────────────────────────────────────────────────┐
│ REIGN Dashboard                           ✕ □ — │
├─────────────────────────────────────────────────┤
│ REIGN - Infrastructure Orchestration Monitor   │
├─────────────────────────────────────────────────┤
│ [Overview] [Recent Tasks] [Deployments] [Log]  │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌──────────────┐    ┌──────────────┐          │
│ │Execution Stats│    │Infrastructure│          │
│ │Total: 127    │    │Deployments: 5│          │
│ │Success: 94.5%│    │Active: 3     │          │
│ └──────────────┘    └──────────────┘          │
│                                                 │
│ Agent Performance                               │
│ ┌────────────────────────────────────────────┐ │
│ │Agent        │Executions│Success│Avg Time  │ │
│ ├────────────────────────────────────────────┤ │
│ │DockerAgent  │45        │97.8%  │1.23s     │ │
│ │K8sAgent     │38        │92.1%  │2.14s     │ │
│ │ReignGeneral │44        │93.2%  │0.87s     │ │
│ └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## Extending the Dashboard

### Adding New Tabs

```python
def _create_custom_tab(self):
    with dpg.tab(label="Custom"):
        dpg.add_text("Custom Content")
        # Add your widgets here
```

### Custom Metrics

```python
def _fetch_custom_metrics(self):
    conn = sqlite3.connect(self.memory_db)
    cursor = conn.cursor()
    # Your custom queries
    cursor.execute("SELECT ...")
    results = cursor.fetchall()
    conn.close()
    return results
```

## Troubleshooting

### Dashboard doesn't show data
- Ensure agents have executed tasks (run some tests or real operations)
- Check database paths are correct
- Verify databases exist and are readable

### UI is slow/frozen
- Increase `refresh_interval` in `__init__` (default: 2.0 seconds)
- Check for very large databases (>1M rows)

### Import errors
```powershell
pip install dearpygui
```

## Integration with REIGN

The dashboard automatically reads from:
1. **AgentMemory**: All agent executions, patterns, statistics
2. **StateManager**: Infrastructure deployments, checkpoints

No configuration needed - just run agents and the dashboard shows results!

## Next Steps

- Add charts/graphs for execution trends
- Add manual agent triggering from dashboard
- Add checkpoint creation/rollback buttons
- Export reports to PDF/CSV
- Add alerting for failures
- Dark/light theme toggle
