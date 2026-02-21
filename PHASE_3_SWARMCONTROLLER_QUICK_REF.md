# Phase 3: SwarmController Agent Routing - Quick Reference

## Overview
Integrate GitLab and GitHub Actions agents into SwarmController's agent routing system. This enables complete end-to-end workflow execution with mixed agent types.

---

## What Needs to Be Done

### 1. **SwarmController Agent Registration** 
- Add GitLabAgent and GitHubActionsAgent to agent registry
- Initialize agents with API credentials from config
- Add agent type detection for "gitlab" and "github_actions"

### 2. **Task to Agent Mapping**
- Map tasks with agent_type="gitlab" → GitLabAgent
- Map tasks with agent_type="github_actions" → GitHubActionsAgent
- Handle parameter passing from decomposed tasks

### 3. **Execution Flow**
- Execute CI/CD tasks alongside Docker, Kubernetes, Terraform tasks
- Manage task dependencies (ensure proper ordering)
- Collect feedback from CI/CD agents
- Report results back to user

### 4. **Error Handling**
- Handle API failures gracefully
- Support retry logic for transient failures
- Clear error messages for configuration issues

---

## Key Files to Modify

### `src/reign/swarm/swarm_controller.py`

#### Required Changes:

**1. Import CI/CD Agents**
```python
from agents.gitlab_agent import GitLabAgent
from agents.github_actions_agent import GitHubActionsAgent
```

**2. Add Agent Initialization** (in `__init__` or `_initialize_agents()`)
```python
# GitLab Agent
gitlab_config = {
    "api_token": config.get("gitlab_api_token"),
    "base_url": config.get("gitlab_base_url", "https://gitlab.com"),
}
self.gitlab_agent = GitLabAgent(**gitlab_config)

# GitHub Actions Agent
github_config = {
    "api_token": config.get("github_api_token"),
}
self.github_actions_agent = GitHubActionsAgent(**github_config)
```

**3. Update `execute_task()` Method**
```python
def execute_task(self, task):
    agent_type = task.agent_type
    
    if agent_type == "gitlab":
        return self.gitlab_agent.execute(task)
    elif agent_type == "github_actions":
        return self.github_actions_agent.execute(task)
    elif agent_type == "docker":
        return self.docker_agent.execute(task)
    # ... other agent types
```

**4. Update `get_agent()` Method** (if exists)
```python
def get_agent(self, agent_type):
    agents = {
        "gitlab": self.gitlab_agent,
        "github_actions": self.github_actions_agent,
        "docker": self.docker_agent,
        # ... other agents
    }
    return agents.get(agent_type)
```

---

## Testing Strategy

### Test Categories (10+ tests minimum)

#### 1. Agent Registration (2 tests)
- `test_gitlab_agent_initialized` - Verify agent registered
- `test_github_actions_agent_initialized` - Verify agent registered

#### 2. Task Execution (4 tests)
- `test_execute_gitlab_task` - Execute GitLab CI/CD task
- `test_execute_github_actions_task` - Execute GitHub Actions task
- `test_gitlab_task_with_invalid_config` - Error handling
- `test_github_actions_task_with_invalid_config` - Error handling

#### 3. Mixed-Agent Workflows (3 tests)
- `test_github_actions_then_docker` - CI/CD → Docker
- `test_gitlab_then_kubernetes` - CI/CD → Kubernetes
- `test_full_pipeline_github_docker_k8s` - CI/CD → Docker → Kubernetes

#### 4. Dependency Ordering (2 tests)
- `test_cicd_task_executed_before_docker` - Task ordering
- `test_docker_task_executed_before_kubernetes` - Task ordering

#### 5. Feedback Loop Integration (2 tests)
- `test_cicd_feedback_collection` - Gather execution results
- `test_mixed_agent_feedback_aggregation` - Combine all feedback

### Test File Location
- Create: `tests/test_swarm_controller_cicd.py`
- Follow existing test pattern in `tests/test_*.py`

### Expected Results
- All new tests passing
- All existing controller tests still passing
- End-to-end workflows working correctly

---

## Configuration Requirements

### Environment Variables
```
GITLAB_API_TOKEN=your_gitlab_token
GITLAB_BASE_URL=https://gitlab.com  # Optional, defaults to gitlab.com

GITHUB_API_TOKEN=your_github_token
GITHUB_API_URL=https://api.github.com  # Optional, defaults to api.github.com
```

### Config File Format
```yaml
agents:
  gitlab:
    api_token: ${GITLAB_API_TOKEN}
    base_url: ${GITLAB_BASE_URL}
  github_actions:
    api_token: ${GITHUB_API_TOKEN}
    api_url: ${GITHUB_API_URL}
  docker:
    # ... existing docker config
  kubernetes:
    # ... existing kubernetes config
```

---

## Example Workflows After Integration

### Example 1: GitHub Actions → Docker → Kubernetes
```
User Request:
"Deploy Python app to Kubernetes using GitHub Actions"

ReignGeneral Decomposition:
1. Task: Setup GitHub Actions workflow (agent_type=github_actions)
2. Task: Build Docker image (agent_type=docker)
3. Task: Deploy to Kubernetes (agent_type=kubernetes)

SwarmController Execution:
1. GitHub Actions Agent: Triggers workflow
2. Docker Agent: Builds and pushes image
3. Kubernetes Agent: Deploys updated image
4. Feedback Loop: Reports success/failure at each step
```

### Example 2: GitLab CI → Docker → Infrastructure
```
User Request:
"Set up GitLab pipeline with Docker build and Kubernetes deployment"

ReignGeneral Decomposition:
1. Task: Setup GitLab CI pipeline (agent_type=gitlab)
2. Task: Build Docker image (agent_type=docker)
3. Task: Create Kubernetes config (agent_type=kubernetes)

SwarmController Execution:
1. GitLab Agent: Generates .gitlab-ci.yml
2. Docker Agent: Prepares Docker build steps
3. Kubernetes Agent: Prepares deployment manifests
4. Feedback Loop: Reports integrated pipeline ready
```

---

## Implementation Steps (Recommended Order)

### Step 1: Import and Register (30 min)
- [ ] Add imports for GitLabAgent and GitHubActionsAgent
- [ ] Create agent initialization code
- [ ] Verify imports work correctly

### Step 2: Execute Task Method (45 min)
- [ ] Update `execute_task()` to handle new agent types
- [ ] Test with simple GitLab/GitHub task execution
- [ ] Add error handling for missing agents

### Step 3: Create Tests (1 hour)
- [ ] Write 10+ tests for new functionality
- [ ] Test agent registration
- [ ] Test mixed-agent workflows
- [ ] Test dependency ordering

### Step 4: Integration Testing (1 hour)
- [ ] Run full test suite
- [ ] Verify all 66+ tests passing
- [ ] Create end-to-end workflow examples

### Step 5: Documentation (30 min)
- [ ] Update README with CI/CD agent examples
- [ ] Add configuration guide for tokens
- [ ] Create workflow examples

**Total Estimated Time: 4-5 hours**

---

## Verification Checklist

After implementation, verify:
- [ ] GitLabAgent successfully instantiated in SwarmController
- [ ] GitHubActionsAgent successfully instantiated in SwarmController
- [ ] `execute_task()` correctly routes CI/CD tasks to agents
- [ ] All new tests passing (10+ tests)
- [ ] All existing tests still passing (26+22+18)
- [ ] End-to-end workflows execute successfully
- [ ] Feedback properly collected from all agents
- [ ] Error handling works for invalid configs
- [ ] Documentation updated with examples
- [ ] Code follows existing patterns and style

---

## Known Dependencies

### Already Complete
- ✅ ReignGeneral CI/CD component detection
- ✅ GitLabAgent fully implemented and tested
- ✅ GitHubActionsAgent fully implemented and tested
- ✅ ReignGeneral task decomposition for CI/CD
- ✅ FeedbackLoop infrastructure

### Will Use From Existing Code
- `SwarmController` base class and methods
- `Task` class for task representation
- `FeedbackLoop` for result collection
- `DockerAgent`, `KubernetesAgent` for reference patterns

---

## Resources

### Code References
- [GitLabAgent Implementation](src/reign/swarm/agents/gitlab_agent.py)
- [GitHubActionsAgent Implementation](src/reign/swarm/agents/github_actions_agent.py)
- [ReignGeneral CI/CD Integration](REIGN_CICD_INTEGRATION_COMPLETE.md)
- [Existing SwarmController Patterns](src/reign/swarm/swarm_controller.py)

### Test Examples
- [CI/CD Integration Tests](test_reign_cicd_integration.py)
- [CI/CD Agent Tests](test_cicd_agents.py)
- [Medium-Term Enhancement Tests](test_medium_term_enhancements.py)

---

## Success Criteria

✅ **Phase 3 Complete When:**
- All 10+ new SwarmController tests passing
- All 66 existing tests still passing
- Mixed-agent workflows executing correctly
- Feedback properly aggregated from CI/CD agents
- Documentation updated with working examples
- Code committed and pushed to GitHub

**Target**: All criteria met with 0 regressions, 100% backward compatibility

---

## Questions & Troubleshooting

### Q: Where do I get GitLab/GitHub API tokens?
**A**: 
- GitLab: Settings → Personal Access Tokens → Create token (api scope)
- GitHub: Settings → Developer Settings → Personal Access Tokens → New token (repo, workflow scopes)

### Q: How do I run a test workflow?
**A**: See "Example Workflows After Integration" section above

### Q: What if agent initialization fails?
**A**: Check environment variables and config, ensure tokens are valid, see error logs

### Q: How do task dependencies work?
**A**: Already handled by ReignGeneral decompose_task(). SwarmController just executes in order.

---

**Ready to Start Phase 3? Everything is in place and tested. Let's integrate!**
