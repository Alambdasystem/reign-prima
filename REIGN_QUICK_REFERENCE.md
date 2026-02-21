# REIGN - Quick Reference Guide

## What is Reign?

**Reign** is an AI-powered agentic general that automates infrastructure management through natural language commands. She understands your intent and orchestrates:

- **Docker & Containers** - Create, manage, and deploy containerized applications
- **Kubernetes & Helm** - Deploy and manage K8s clusters and Helm releases
- **Infrastructure as Code** - Generate and manage Terraform configurations
- **CI/CD Pipelines** - Create GitHub Actions workflows automatically
- **GitHub Integration** - Manage repositories, branches, PRs, and releases
- **Bash Commands** - Execute system commands safely and securely

---

## Core Capabilities

### 1. Create Infrastructure
```
"Reign, create a production microservices stack with:
- React frontend
- Node.js API
- PostgreSQL database
- Redis cache
- Helm deployment to Kubernetes"

Result: Full K8s infrastructure with CI/CD pipeline
```

### 2. Deploy & Scale
```
"Deploy the API service with 5 replicas and monitor health"

Result: Helm upgrade with scaling and health checks
```

### 3. Generate Code
```
"Create a GitHub Actions workflow that:
- Tests on PR
- Builds Docker images
- Deploys to staging on merge"

Result: Complete workflow .yml file in .github/workflows/
```

### 4. Manage Infrastructure
```
"Show me the health of all running services and resource usage"

Result: Comprehensive status report with recommendations
```

### 5. Create Repositories
```
"Create a new GitHub repository for a microservices project
with proper structure, README, and CI/CD setup"

Result: GitHub repo with all infrastructure files
```

---

## Architecture Overview

```
┌────────────────────────────────────────┐
│    Natural Language Request (You)      │
└─────────────────┬──────────────────────┘
                  │
┌─────────────────▼──────────────────────┐
│  Intent Recognition & Understanding    │ ← Claude/GPT-4
│  (What do you want to do?)             │
└─────────────────┬──────────────────────┘
                  │
┌─────────────────▼──────────────────────┐
│  Planning & Orchestration              │
│  (How to do it safely & efficiently)   │
└─────────────────┬──────────────────────┘
                  │
┌─────────────────▼──────────────────────┐
│  Safety & Validation                   │
│  (Permission checks, limits, approvals)│
└─────────────────┬──────────────────────┘
                  │
    ┌─────────────┼─────────────┬──────────────┬──────────────┐
    │             │             │              │              │
    ▼             ▼             ▼              ▼              ▼
┌────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│Docker/ │  │Kubernetes│  │Terraform │  │GitHub &  │  │ Bash     │
│Compose │  │& Helm    │  │(IaC)     │  │CI/CD     │  │ Execute  │
└────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘
    │             │             │              │              │
    └─────────────┼─────────────┴──────────────┴──────────────┘
                  │
┌─────────────────▼──────────────────────┐
│  Execution & Monitoring                │
│  (Run operations, track progress)      │
└─────────────────┬──────────────────────┘
                  │
┌─────────────────▼──────────────────────┐
│  Response & Reporting                  │
│  (Show results, next steps, status)    │
└────────────────────────────────────────┘
```

---

## Implementation Phases

| Phase | Duration | Focus | Status |
|-------|----------|-------|--------|
| 0 | Week 1 | Preparation & Setup | Planned |
| 1 | Week 2-3 | Core Agent Foundation | Planned |
| 2 | Week 4-5 | Docker Integration | Planned |
| 3 | Week 5-6 | Bash Execution | Planned |
| 4 | Week 7-8 | Kubernetes & Helm | Planned |
| 5 | Week 9-10 | Terraform & IaC | Planned |
| 6 | Week 11-12 | CI/CD Pipelines | Planned |
| 7 | Week 13-14 | GitHub Integration | Planned |
| 8 | Week 15-16 | Orchestration | Planned |
| 9 | Week 17-18 | UI & API | Planned |
| 10 | Week 19-20 | Testing & Validation | Planned |
| 11 | Week 21-22 | Production Deploy | Planned |
| 12 | Week 23-24 | Monitoring & Optimize | Planned |

**Total Timeline: 24 weeks (6 months)**

---

## Key Design Principles

### 1. **Safety First**
- Command validation and whitelisting
- Confirmation gates for destructive operations
- Comprehensive audit logging
- Resource limits enforcement
- Permission-based access control

### 2. **Clear Intent Understanding**
- Multi-step request decomposition
- Dependency resolution
- Clarification prompts for ambiguity
- Context preservation across conversations

### 3. **Reliable Execution**
- Error handling and recovery
- Automatic rollback on failure
- Health checks between steps
- Detailed operation logging
- Status reporting and monitoring

### 4. **Cross-Tool Orchestration**
- Seamless Docker ↔ K8s ↔ IaC ↔ CI/CD ↔ GitHub coordination
- Shared state management
- Unified error handling
- Consistent authentication across tools

### 5. **User-Centric**
- Natural language interface
- Real-time execution feedback
- Clear, actionable error messages
- Infrastructure templates for common patterns
- Progressive disclosure of complexity

---

## Real-World Scenarios

### Scenario 1: Launch New Service
```
You:    "Create a new microservice for user authentication 
         with full infrastructure and CI/CD"

Reign:  1. Create GitHub repo
        2. Generate Dockerfile and tests
        3. Create Terraform for deployment
        4. Create Helm charts
        5. Set up GitHub Actions CI/CD
        6. Deploy to staging
        7. Provide docs and endpoints
```

### Scenario 2: Scale for Traffic Spike
```
You:    "We're expecting 10x traffic tomorrow. 
         Scale up the API servers and databases."

Reign:  1. Analyze current resource usage
        2. Calculate needed resources
        3. Update Helm values
        4. Scale deployments
        5. Configure auto-scaling rules
        6. Run load tests
        7. Alert on metrics
```

### Scenario 3: Production Rollback
```
You:    "The new deploy broke things. 
         Rollback to the previous version."

Reign:  1. Check current release status
        2. Identify previous good version
        3. Rollback Helm release
        4. Verify health checks
        5. Run smoke tests
        6. Report rollback completion
```

### Scenario 4: Local Development Environment
```
You:    "Set up a complete dev environment that matches production"

Reign:  1. Generate docker-compose.yml
        2. Create .env files
        3. Set up volumes for data persistence
        4. Configure networking
        5. Start services
        6. Run database migrations
        7. Provide connection strings
```

---

## Technology Stack

### Required
```
Python 3.9+
- FastAPI (REST API)
- asyncio (async operations)
- Docker SDK (container management)
- Kubernetes SDK (K8s management)
- PyGithub (GitHub API)
- SQLAlchemy (database ORM)

CLIs:
- docker desktop
- kubectl
- helm
- terraform
- git
- github cli
```

### LLM Provider
```
Recommended: Claude 3 (Anthropic)
- Best reasoning for planning
- Excellent at code generation
- Cost-effective token usage
- Strong safety features

Alternative: GPT-4 (OpenAI)
- Versatile model
- Wide ecosystem
- High token costs
```

### Infrastructure
```
Local Development:
- Docker Desktop (with K8s)
- Terraform with local state

Production:
- Kubernetes cluster (EKS/AKS/GKE)
- PostgreSQL for state
- Redis for caching
- Prometheus + Grafana for monitoring
```

---

## Safety & Security

### Command Validation
```
Blocked Commands:
❌ rm -rf /
❌ sudo commands without approval
❌ System partition modifications
❌ Direct credential exposure
✓ All destructive operations require confirmation
✓ All commands logged for audit
```

### Credential Management
```
✓ GitHub tokens encrypted at rest
✓ Cloud credentials via environment variables
✓ Secrets stored in encrypted database
✓ No credentials in logs or responses
✓ Automatic credential rotation support
```

### Access Control
```
Levels:
- Read-only: View resources, logs, status
- Write: Create, update, start/stop services
- Admin: Delete, rollback, modify settings
- Dangerous: System-level commands

RBAC:
- User roles and permissions
- Resource-based access control
- API key scoping
- Audit trail per operation
```

---

## Common Commands

### Infrastructure
```
"Create a PostgreSQL database with 100GB storage"
"Deploy the API to 3 replicas with load balancing"
"Scale the worker pool to 10 nodes"
"Destroy all staging infrastructure"
"Show me CPU and memory usage for all services"
```

### CI/CD
```
"Create a GitHub Actions workflow for testing"
"Add a deployment step that deploys to production"
"Set up branch protection rules"
"Create a release with auto-generated notes"
```

### Debugging
```
"Show me the logs for the API container"
"Why is the database slow?"
"Which service is using the most CPU?"
"Check the health of all microservices"
```

### Git
```
"Create a new feature branch for user-auth"
"Create a pull request from feature/auth to main"
"Merge and deploy the PR"
"Tag this release as v1.2.3"
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Intent Accuracy | >95% |
| Safety | Zero unintended destructive actions |
| Response Time | <5 seconds for simple requests |
| Reliability | 99.9% uptime |
| Code Generation Quality | Functional on first try >90% |
| User Satisfaction | >4.5/5 |

---

## What Makes Reign Special?

1. **Unified Interface** - One tool for all infrastructure needs
2. **Natural Language** - No learning curve, just describe what you want
3. **Safe by Default** - Validation and approval gates built-in
4. **Cross-Tool Orchestration** - Docker → K8s → IaC → CI/CD all together
5. **Production-Ready** - Enterprise security and compliance
6. **Extensible** - Easy to add new tools and capabilities
7. **Learning System** - Improves over time from usage patterns

---

## Getting Started Checklist

- [ ] Clone the repository
- [ ] Set up Python 3.9+ environment
- [ ] Install dependencies (pip install -r requirements.txt)
- [ ] Configure LLM provider (Claude or GPT-4 API key)
- [ ] Set up Docker Desktop
- [ ] Configure kubectl for K8s access
- [ ] Generate GitHub API token
- [ ] Set up Terraform credentials (AWS/Azure/GCP)
- [ ] Run tests (pytest)
- [ ] Start the API (fastapi run main.py)
- [ ] Open the web UI (localhost:8000)

---

## Support & Resources

**Documentation**: [REIGN_AGENTIC_GENERAL_DESIGN.md](REIGN_AGENTIC_GENERAL_DESIGN.md)
**Roadmap**: [REIGN_IMPLEMENTATION_ROADMAP.md](REIGN_IMPLEMENTATION_ROADMAP.md)
**GitHub**: https://github.com/yourorg/reign
**Issues**: https://github.com/yourorg/reign/issues
**Discussions**: https://github.com/yourorg/reign/discussions

---

**Reign v1.0 - Making Infrastructure Automation Human-Friendly** 🚀

