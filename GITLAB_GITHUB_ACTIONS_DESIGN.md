# CI/CD Integration for REIGN - GitLab & GitHub Actions

## Architecture Overview

### Goal
Enable REIGN to orchestrate CI/CD pipelines on GitLab and GitHub, allowing infrastructure deployments triggered by code changes.

### Integration Points

```
User Request (NLP)
    ↓
ReignGeneral (Task Decomposition)
    ↓
    ├─→ GitHubActionsAgent (GitHub repos)
    ├─→ GitLabAgent (GitLab repos)
    ├─→ DockerAgent (Container execution)
    ├─→ KubernetesAgent (K8s deployment)
    └─→ TerraformAgent (Infrastructure)
```

## 1. GitLab Agent (NEW)

### Capabilities
- ✅ Trigger CI/CD pipelines via API
- ✅ Create/update GitLab CI/CD YAML configs
- ✅ Monitor pipeline execution
- ✅ Manage project variables (secrets, API keys)
- ✅ Deploy to environments (staging, production)
- ✅ Create merge requests for automated changes
- ✅ Manage GitLab runners

### Example Usage

```python
# Trigger a pipeline
task = Task(
    description="Deploy latest to production",
    agent_type="gitlab",
    params={
        "action": "trigger_pipeline",
        "project_id": "123",
        "branch": "main",
        "variables": {
            "DEPLOY_ENV": "production",
            "VERSION": "1.2.3"
        }
    }
)

# Generate CI/CD config
task = Task(
    description="Create Docker build and deploy pipeline",
    agent_type="gitlab",
    params={
        "action": "generate_config",
        "language": "python",
        "stages": ["build", "test", "deploy"],
        "registry": "docker.io"
    }
)
```

## 2. GitHub Actions Agent (NEW)

### Capabilities
- ✅ Trigger workflows via GitHub API
- ✅ Create/update workflow YAML files
- ✅ Manage repository secrets and variables
- ✅ Monitor workflow runs
- ✅ Deploy to GitHub environments
- ✅ Create pull requests with automated changes
- ✅ Manage GitHub organization settings

### Example Usage

```python
# Trigger a workflow
task = Task(
    description="Run deployment workflow",
    agent_type="github_actions",
    params={
        "action": "trigger_workflow",
        "repo": "owner/repo",
        "workflow_file": "deploy.yml",
        "ref": "main",
        "inputs": {
            "environment": "production",
            "version": "1.2.3"
        }
    }
)

# Generate workflow
task = Task(
    description="Create Docker build workflow",
    agent_type="github_actions",
    params={
        "action": "generate_workflow",
        "language": "python",
        "docker_registry": "ghcr.io",
        "include_tests": True
    }
)
```

## 3. Natural Language Examples

### User Requests REIGN Should Handle

```
"Deploy the latest code from main branch to production using GitHub Actions"
→ Detects: github_actions agent, main branch, production environment
→ Actions: Trigger deploy workflow with production variables

"Create a GitLab CI pipeline that builds Docker images and deploys to Kubernetes"
→ Detects: gitlab agent, docker component, kubernetes component
→ Actions: Generate .gitlab-ci.yml, create pipeline variables, configure K8s deployment

"Set up continuous deployment: push to main → build Docker → deploy to staging"
→ Detects: git event trigger, docker, staging environment
→ Actions: Create workflow/pipeline config with automatic triggers

"Monitor the GitHub Actions workflow and notify on failure"
→ Detects: github_actions agent, monitoring requirement
→ Actions: Track workflow status, set up notifications

"Create a merge request to update the deployment config"
→ Detects: git agent, merge request action
→ Actions: Generate config, create MR with changes, request review
```

## 4. Implementation Strategy

### Phase 1: Basic GitLab Agent
1. Authentication (personal access tokens)
2. List projects and pipelines
3. Trigger pipeline execution
4. Get pipeline status
5. Manage variables

### Phase 2: GitHub Actions Agent
1. Authentication (personal access tokens / GitHub App)
2. List workflows and runs
3. Trigger workflow execution
4. Get run status
5. Manage secrets

### Phase 3: Configuration Generation
1. Generate .gitlab-ci.yml
2. Generate .github/workflows/*.yml
3. Multi-stage pipelines
4. Docker build & push
5. Kubernetes deployment steps

### Phase 4: Advanced Features
1. Merge request creation
2. Environment management
3. Artifact handling
4. Cache optimization
5. Cost analysis

## 5. System Design

### GitLab Agent Class Structure

```python
class GitLabAgent:
    def __init__(self, api_token: str, base_url: str = "https://gitlab.com"):
        self.api_token = api_token
        self.base_url = base_url
    
    def execute(self, task: Task) -> AgentResult:
        """Execute GitLab action"""
        action = task.params.get("action")
        
        if action == "trigger_pipeline":
            return self._trigger_pipeline(task.params)
        elif action == "generate_config":
            return self._generate_ci_config(task.params)
        elif action == "get_status":
            return self._get_pipeline_status(task.params)
        elif action == "manage_variables":
            return self._manage_variables(task.params)
    
    def _trigger_pipeline(self, params: Dict) -> AgentResult:
        """Trigger a CI/CD pipeline"""
        project_id = params.get("project_id")
        branch = params.get("branch", "main")
        variables = params.get("variables", {})
        
        # API call to trigger pipeline
        # POST /projects/{id}/pipeline
        # Returns: Pipeline ID, status, web URL
    
    def _generate_ci_config(self, params: Dict) -> AgentResult:
        """Generate .gitlab-ci.yml"""
        stages = params.get("stages", ["build", "test", "deploy"])
        language = params.get("language", "generic")
        
        # Generate YAML config
        # Returns: YAML content ready to save to .gitlab-ci.yml
    
    def _get_pipeline_status(self, params: Dict) -> AgentResult:
        """Get pipeline execution status"""
        # Returns: status, stages, duration, artifacts
    
    def _manage_variables(self, params: Dict) -> AgentResult:
        """Create/update project variables"""
        # Used for secrets, API keys, deployment credentials
```

### GitHub Actions Agent Class Structure

```python
class GitHubActionsAgent:
    def __init__(self, token: str):
        self.token = token
        self.api_base = "https://api.github.com"
    
    def execute(self, task: Task) -> AgentResult:
        """Execute GitHub Actions"""
        action = task.params.get("action")
        
        if action == "trigger_workflow":
            return self._trigger_workflow(task.params)
        elif action == "generate_workflow":
            return self._generate_workflow(task.params)
        elif action == "get_status":
            return self._get_run_status(task.params)
        elif action == "manage_secrets":
            return self._manage_secrets(task.params)
    
    def _trigger_workflow(self, params: Dict) -> AgentResult:
        """Trigger a GitHub Actions workflow"""
        repo = params.get("repo")  # owner/repo
        workflow = params.get("workflow_file")
        ref = params.get("ref", "main")
        inputs = params.get("inputs", {})
        
        # API call: POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches
    
    def _generate_workflow(self, params: Dict) -> AgentResult:
        """Generate GitHub Actions workflow YAML"""
        # Returns: workflow YAML ready for .github/workflows/
    
    def _get_run_status(self, params: Dict) -> AgentResult:
        """Get workflow run status"""
        # Returns: status, steps, duration, conclusion
    
    def _manage_secrets(self, params: Dict) -> AgentResult:
        """Create/update repository secrets"""
        # For environment variables, API keys, credentials
```

## 6. Integration with REIGN

### Enhanced Component Detection

```python
# Add to ReignGeneral._detect_components()

if "github" in request_lower or "github actions" in request_lower:
    components["ci_cd"] = "github_actions"
elif "gitlab" in request_lower or "gitlab ci" in request_lower:
    components["ci_cd"] = "gitlab"

if "workflow" in request_lower or "pipeline" in request_lower or "ci/cd" in request_lower:
    components["ci_cd"] = detected_platform  # github_actions or gitlab
```

### Task Decomposition Example

```
Request: "Deploy to production using GitHub Actions when main branch updates"

Decomposed Tasks:
1. GitHubActionsAgent: Generate workflow YAML
   - Build Docker image
   - Push to registry
   - Deploy to Kubernetes
   - Notify on completion

2. GitHubActionsAgent: Create secrets
   - DOCKER_TOKEN
   - KUBECONFIG
   - DEPLOY_KEY

3. GitHubActionsAgent: Set up environment
   - Production environment
   - Protection rules
   - Required reviewers

4. DockerAgent: Set up registry auth
5. KubernetesAgent: Configure deployment
```

## 7. API Authentication

### GitLab Setup
```bash
# Get personal access token
https://gitlab.com/profile/personal_access_tokens
# Scopes: api, read_api, read_repository, write_repository

# Environment variable
export GITLAB_TOKEN="glpat-xxxxxxx"
```

### GitHub Setup
```bash
# Option 1: Personal access token
https://github.com/settings/tokens
# Scopes: repo, workflow, admin:repo_hook

# Option 2: GitHub App (recommended for production)
# Create at https://github.com/settings/apps

# Environment variable
export GITHUB_TOKEN="ghp_xxxxxxx"
```

## 8. Workflow Examples

### Example 1: Automated Deployment

**User Request:**
```
"Deploy my Node.js app to production whenever I push to main"
```

**REIGN Actions:**
1. Create GitHub Actions workflow that:
   - Triggers on push to main
   - Installs dependencies
   - Runs tests
   - Builds Docker image
   - Pushes to registry
   - Deploys to Kubernetes
2. Set up secrets (DOCKER_TOKEN, KUBECONFIG)
3. Configure GitHub environment (production)
4. Create required status checks

### Example 2: Multi-Stage Pipeline

**User Request:**
```
"Build, test, and deploy to staging and production with approvals"
```

**REIGN Actions (GitLab):**
1. Generate .gitlab-ci.yml with:
   - Build stage
   - Test stage
   - Deploy to staging (automatic)
   - Deploy to production (manual approval)
2. Configure protected branches
3. Set up deployment approvers
4. Enable pipeline artifacts/caching

### Example 3: Infrastructure as Code Deployment

**User Request:**
```
"Automatically deploy infrastructure changes from Terraform to AWS"
```

**REIGN Actions:**
1. Generate GitHub Actions workflow:
   - Detect Terraform changes
   - Run terraform plan
   - Comment plan on PR
   - On merge to main: terraform apply
2. Set up AWS credentials
3. Configure state file storage (S3)
4. Add cost estimation

## 9. Security Considerations

### Secrets Management
- Never log credentials
- Use platform-native secret storage
- Rotate tokens regularly
- Use environment-specific credentials

### Access Control
- Limit token scope (only needed permissions)
- Use protected branches
- Require approvals for production
- Audit log pipeline executions

### Network Security
- Only HTTPS API calls
- Validate webhook signatures (for events)
- IP allowlisting (if available)

## 10. Next Steps

### Immediate Implementation (Phase 1)
- [ ] Create GitLabAgent class
- [ ] Create GitHubActionsAgent class
- [ ] Basic API authentication
- [ ] Trigger pipeline/workflow
- [ ] Get status

### Short-term (Phase 2)
- [ ] Generate CI/CD configs
- [ ] Manage secrets/variables
- [ ] Monitor executions
- [ ] Error handling and retry logic

### Medium-term (Phase 3)
- [ ] Merge request creation
- [ ] Environment management
- [ ] Integration tests
- [ ] TDD test suite

---

**Status:** Design Complete - Ready for Implementation  
**Complexity:** Medium  
**Impact:** High (enables full CI/CD automation)  
**Dependencies:** External (GitLab/GitHub APIs)
