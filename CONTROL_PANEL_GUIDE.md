# 🎮 REIGN Dashboard - Control Panel Guide

## 🚀 Interactive Features Added!

Your dashboard now has full agent control capabilities. You can deploy, monitor, and manage your infrastructure directly from the UI.

## 📋 New Control Panel Tab

The dashboard now includes a **Control Panel** tab with four main sections:

### 1. 🐳 Docker Agent Controls

**Deploy Container:**
- **Image**: Docker image to deploy (e.g., `nginx:latest`, `redis:alpine`)
- **Name**: Container name (e.g., `my-web-server`)
- **Port**: Port mapping (e.g., `8080:80`, `6379:6379`)
- **Button**: "Deploy Container" - Triggers deployment
- **Button**: "List Containers" - Shows running containers

**Example Usage:**
```
Image: nginx:latest
Name: my-nginx
Port: 8080:80
→ Click "Deploy Container"
→ Watch Activity Log for results
```

### 2. ☸️ Kubernetes Agent Controls

**Deploy K8s Deployment:**
- **Deployment**: Deployment name (e.g., `my-deployment`)
- **Image**: Container image (e.g., `nginx:latest`)
- **Replicas**: Number of pods (e.g., `3`)
- **Button**: "Create Deployment" - Deploys to K8s
- **Button**: "List Deployments" - Shows current deployments

**Example Usage:**
```
Deployment: web-api
Image: myapp:v1.0
Replicas: 3
→ Click "Create Deployment"
→ Deployment tracked in State Manager
```

### 3. 💾 State Management Controls

**Checkpoint Management:**
- **Checkpoint**: Name for the checkpoint (e.g., `pre-update-backup`)
- **Button**: "Create Checkpoint" - Saves current state
- **Button**: "List Checkpoints" - Shows all checkpoints
- **Button**: "Rollback" - Opens rollback dialog

**Rollback Process:**
1. Click "Rollback" button
2. Modal window shows available checkpoints
3. Select checkpoint to restore
4. Confirms and executes rollback
5. Watch Activity Log for progress

### 4. 🎯 ReignGeneral Orchestration

**Task Execution:**
- **Task Description**: Multi-line natural language task
- **Button**: "Execute Task" - Runs through ReignGeneral

**Example Tasks:**
```
Deploy a web application with 3 replicas

Create a Redis cache with persistent storage

Scale the web-api deployment to 5 replicas

Deploy nginx reverse proxy on port 8080
```

## 🔄 How It Works

### Execution Flow
1. **User Input** → Fill form fields with deployment parameters
2. **Button Click** → Triggers callback function
3. **Background Thread** → Executes agent task asynchronously
4. **Activity Log** → Shows real-time progress and results
5. **State Tracking** → Records deployment in StateManager
6. **Memory Learning** → Stores execution in AgentMemory
7. **UI Refresh** → Tables update automatically (2s refresh)

### Agent Integration
```
Dashboard → DockerAgent → Docker Executor → Real Docker API
         → K8sAgent    → K8s Executor   → Real kubectl
         → StateManager → SQLite DB
         → AgentMemory  → SQLite DB
```

## 📊 Live Monitoring

All actions appear in multiple places:

1. **Activity Log Tab**: Real-time execution logs with timestamps
2. **Recent Tasks Tab**: Shows completed tasks
3. **Deployments Tab**: Lists all deployed resources
4. **Overview Tab**: Updates success rates and statistics

## 🔧 Configuration

### Customize Agent Behavior

Edit callback functions in `dashboard_app.py`:

```python
def _deploy_docker_container(self):
    image = dpg.get_value("docker_image")
    name = dpg.get_value("docker_name")
    
    # Add custom logic here
    task = Task(
        description=f"Deploy {name}",
        parameters={
            "action": "run",
            "image": image,
            # Add more parameters
        }
    )
```

### Add Custom Controls

```python
# In _create_control_tab():
with dpg.collapsing_header(label="Custom Section"):
    dpg.add_input_text(tag="my_input")
    dpg.add_button(label="Execute", callback=self._my_callback)

def _my_callback(self):
    value = dpg.get_value("my_input")
    # Your logic here
```

## 🎯 Example Workflows

### Workflow 1: Deploy Web Stack
1. **Deploy Docker Container**
   - Image: `postgres:15`
   - Name: `my-database`
   - Port: `5432:5432`

2. **Create Checkpoint**
   - Name: `pre-app-deploy`

3. **Deploy K8s Deployment**
   - Name: `web-api`
   - Image: `myapp:latest`
   - Replicas: `3`

4. **Monitor** in Recent Tasks tab

### Workflow 2: Safe Deployment with Rollback
1. **Create Checkpoint** → "stable-state"
2. **Deploy New Version** → via ReignGeneral
3. **Test** → Check logs and metrics
4. **If Failed** → Click "Rollback" → Select "stable-state"
5. **If Success** → Create new checkpoint

### Workflow 3: Scale Application
1. **List Deployments** → Find deployment name
2. **ReignGeneral Task**:
   ```
   Scale web-api deployment to 5 replicas
   ```
3. **Monitor** → Watch Activity Log
4. **Verify** → Check Deployments tab

## 🛡️ Safety Features

### Built-in Protection:
- **Background Threads**: UI never freezes during operations
- **Error Handling**: All exceptions caught and logged
- **State Tracking**: Every deployment recorded
- **Checkpoints**: Easy rollback to known-good state
- **Memory Learning**: Failed attempts logged with solutions

### Error Messages:
```
[ERROR] Docker agent not available
[ERROR] Deployment failed: Connection timeout
[WARNING] No checkpoints available for rollback
```

## 📝 Activity Log Format

```
[HH:MM:SS] [LEVEL] Message

Examples:
[10:15:23] [INFO] Deploying Docker container: my-nginx (nginx:latest)
[10:15:25] [INFO] ✓ Container deployed: my-nginx
[10:16:10] [INFO] Creating checkpoint: pre-update
[10:16:11] [INFO] ✓ Checkpoint created: a7f3b29c
[10:17:05] [ERROR] ✗ Deployment failed: Image not found
```

## 🔄 Refresh Behavior

- **Manual Actions**: Executed immediately
- **UI Updates**: Every 2 seconds
- **Database Queries**: Every 2 seconds
- **Log Updates**: Real-time (as events occur)

## 🎨 UI Elements

### Input Types:
- `dpg.add_input_text()` - Text fields
- `dpg.add_input_int()` - Number fields
- `dpg.add_button()` - Action buttons
- `dpg.add_text()` - Labels and headers

### Color Coding:
- **Cyan** (100, 200, 255): Headers and titles
- **Green** (0, 255, 0): Success indicators
- **Red** (255, 0, 0): Error indicators
- **Gray** (200, 200, 200): Input labels

## 🚨 Troubleshooting

### "REIGN agents not available"
- Check imports in `dashboard_app.py`
- Verify REIGN components installed
- Restart dashboard after installing dependencies

### Actions don't execute
- Check Activity Log for error messages
- Verify agent executors are configured
- Check Docker/K8s connectivity

### UI not updating
- Check refresh_interval setting
- Verify background thread is running
- Check for database lock errors

## 🎓 Next Steps

### Advanced Features to Add:
1. **Resource Monitoring**: CPU, memory, network graphs
2. **Bulk Operations**: Deploy multiple resources at once
3. **Templates**: Save and reuse deployment configs
4. **Scheduling**: Schedule deployments for later
5. **Notifications**: Alert on failures or completion
6. **Export/Import**: Save/load configurations
7. **Multi-cluster**: Switch between K8s clusters
8. **Terraform**: Add Terraform agent controls

### Customization Ideas:
- Add custom deployment templates
- Create deployment workflows
- Add resource health checks
- Implement auto-scaling rules
- Add cost estimation
- Create deployment pipelines

---

**You now have full control of your infrastructure from the dashboard!** 🎉
