"""
Test suite for GitLab and GitHub Actions agents using TDD methodology
Tests: 22 comprehensive tests covering CI/CD integration
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from reign.swarm.agents.gitlab_agent import GitLabAgent, AgentResult
from reign.swarm.agents.github_actions_agent import GitHubActionsAgent


# Mock Task class for testing
class Task:
    def __init__(self, description: str, agent_type: str, params: dict):
        self.description = description
        self.agent_type = agent_type
        self.params = params


def test_gitlab_agent_trigger_pipeline():
    """Test: GitLab agent triggers pipeline successfully"""
    agent = GitLabAgent(api_token="test-token")
    task = Task(
        description="Trigger deployment pipeline",
        agent_type="gitlab",
        params={
            "action": "trigger_pipeline",
            "project_id": 12345,
            "branch": "main",
            "variables": {"VERSION": "1.2.3", "ENV": "production"}
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True, "Pipeline trigger should succeed"
    assert "Pipeline triggered successfully" in result.output
    assert "12345" in result.output or "success" in result.output
    assert result.metadata is not None
    print("[+] test_gitlab_agent_trigger_pipeline")


def test_gitlab_agent_trigger_pipeline_missing_project():
    """Test: GitLab agent handles missing project_id"""
    agent = GitLabAgent(api_token="test-token")
    task = Task(
        description="Trigger pipeline",
        agent_type="gitlab",
        params={"action": "trigger_pipeline"}
    )
    
    result = agent.execute(task)
    
    assert result.success == False, "Should fail without project_id"
    assert "project_id" in result.output.lower()
    print("[+] test_gitlab_agent_trigger_pipeline_missing_project")


def test_gitlab_agent_generate_python_config():
    """Test: GitLab agent generates Python CI config"""
    agent = GitLabAgent(api_token="test-token")
    task = Task(
        description="Generate CI config",
        agent_type="gitlab",
        params={
            "action": "generate_config",
            "language": "python",
            "stages": ["build", "test", "deploy"],
            "include_tests": True
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True, "Config generation should succeed"
    assert "python" in result.output.lower()
    assert ".gitlab-ci.yml" in result.output
    assert "yaml_content" in result.metadata
    print("[+] test_gitlab_agent_generate_python_config")


def test_gitlab_agent_generate_nodejs_config():
    """Test: GitLab agent generates Node.js CI config"""
    agent = GitLabAgent(api_token="test-token")
    task = Task(
        description="Generate Node.js CI config",
        agent_type="gitlab",
        params={
            "action": "generate_config",
            "language": "nodejs",
            "docker_image": "node:18"
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True
    assert "node" in result.output.lower()
    assert "yaml_content" in result.metadata
    print("[+] test_gitlab_agent_generate_nodejs_config")


def test_gitlab_agent_get_pipeline_status():
    """Test: GitLab agent gets pipeline status"""
    agent = GitLabAgent(api_token="test-token")
    task = Task(
        description="Get pipeline status",
        agent_type="gitlab",
        params={
            "action": "get_status",
            "project_id": 12345,
            "pipeline_id": 999
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True
    assert "status" in result.output.lower()
    assert "stages" in result.output.lower()
    assert result.metadata is not None
    print("[+] test_gitlab_agent_get_pipeline_status")


def test_gitlab_agent_manage_variables_list():
    """Test: GitLab agent lists project variables"""
    agent = GitLabAgent(api_token="test-token")
    task = Task(
        description="List project variables",
        agent_type="gitlab",
        params={
            "action": "manage_variables",
            "project_id": 12345,
            "var_action": "list"
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True
    assert "variables" in result.output.lower()
    print("[+] test_gitlab_agent_manage_variables_list")


def test_gitlab_agent_manage_variables_create():
    """Test: GitLab agent creates project variables"""
    agent = GitLabAgent(api_token="test-token")
    task = Task(
        description="Create variables",
        agent_type="gitlab",
        params={
            "action": "manage_variables",
            "project_id": 12345,
            "var_action": "create",
            "variables": {"DOCKER_TOKEN": "secret123", "API_KEY": "key456"}
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True
    assert "created" in result.output.lower()
    print("[+] test_gitlab_agent_manage_variables_create")


def test_gitlab_agent_list_pipelines():
    """Test: GitLab agent lists recent pipelines"""
    agent = GitLabAgent(api_token="test-token")
    task = Task(
        description="List pipelines",
        agent_type="gitlab",
        params={
            "action": "list_pipelines",
            "project_id": 12345,
            "limit": 5
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True
    assert "pipeline" in result.output.lower()
    assert "pipelines" in result.metadata
    print("[+] test_gitlab_agent_list_pipelines")


def test_gitlab_agent_get_project_info():
    """Test: GitLab agent retrieves project information"""
    agent = GitLabAgent(api_token="test-token")
    task = Task(
        description="Get project info",
        agent_type="gitlab",
        params={
            "action": "get_project_info",
            "project_id": 12345
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True
    assert "project information" in result.output.lower()
    assert result.metadata is not None
    print("[+] test_gitlab_agent_get_project_info")


def test_gitlab_agent_unknown_action():
    """Test: GitLab agent handles unknown action"""
    agent = GitLabAgent(api_token="test-token")
    task = Task(
        description="Unknown action",
        agent_type="gitlab",
        params={"action": "invalid_action"}
    )
    
    result = agent.execute(task)
    
    assert result.success == False
    assert "unknown action" in result.output.lower()
    print("[+] test_gitlab_agent_unknown_action")


# GitHub Actions tests

def test_github_actions_trigger_workflow():
    """Test: GitHub Actions agent triggers workflow"""
    agent = GitHubActionsAgent(token="test-token")
    task = Task(
        description="Trigger workflow",
        agent_type="github_actions",
        params={
            "action": "trigger_workflow",
            "repo": "owner/repo",
            "workflow_file": "deploy.yml",
            "ref": "main",
            "inputs": {"environment": "production"}
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True
    assert "workflow triggered" in result.output.lower()
    assert "owner/repo" in result.output
    assert result.metadata is not None
    print("[+] test_github_actions_trigger_workflow")


def test_github_actions_trigger_workflow_missing_repo():
    """Test: GitHub Actions agent handles missing repo"""
    agent = GitHubActionsAgent(token="test-token")
    task = Task(
        description="Trigger workflow",
        agent_type="github_actions",
        params={"action": "trigger_workflow", "workflow_file": "deploy.yml"}
    )
    
    result = agent.execute(task)
    
    assert result.success == False
    assert "repo" in result.output.lower()
    print("[+] test_github_actions_trigger_workflow_missing_repo")


def test_github_actions_generate_python_workflow():
    """Test: GitHub Actions agent generates Python workflow"""
    agent = GitHubActionsAgent(token="test-token")
    task = Task(
        description="Generate workflow",
        agent_type="github_actions",
        params={
            "action": "generate_workflow",
            "name": "Python CI",
            "language": "python",
            "include_tests": True,
            "include_deploy": True
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True
    assert ".github/workflows" in result.output
    assert "yaml_content" in result.metadata
    assert "python" in result.metadata.get("language", "").lower()
    print("[+] test_github_actions_generate_python_workflow")


def test_github_actions_generate_nodejs_workflow():
    """Test: GitHub Actions agent generates Node.js workflow"""
    agent = GitHubActionsAgent(token="test-token")
    task = Task(
        description="Generate Node.js workflow",
        agent_type="github_actions",
        params={
            "action": "generate_workflow",
            "name": "Node.js CI",
            "language": "nodejs",
            "docker_registry": "docker.io"
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True
    assert "node" in result.output.lower() or "nodejs" in result.output.lower()
    print("[+] test_github_actions_generate_nodejs_workflow")


def test_github_actions_get_workflow_status():
    """Test: GitHub Actions agent gets workflow status"""
    agent = GitHubActionsAgent(token="test-token")
    task = Task(
        description="Get workflow status",
        agent_type="github_actions",
        params={
            "action": "get_status",
            "repo": "owner/repo",
            "run_id": 9876543
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True
    assert "workflow run status" in result.output.lower()
    assert "jobs" in result.output.lower()
    print("[+] test_github_actions_get_workflow_status")


def test_github_actions_manage_secrets_list():
    """Test: GitHub Actions agent lists secrets"""
    agent = GitHubActionsAgent(token="test-token")
    task = Task(
        description="List secrets",
        agent_type="github_actions",
        params={
            "action": "manage_secrets",
            "repo": "owner/repo",
            "secret_action": "list"
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True
    assert "secrets" in result.output.lower()
    print("[+] test_github_actions_manage_secrets_list")


def test_github_actions_manage_secrets_create():
    """Test: GitHub Actions agent creates secrets"""
    agent = GitHubActionsAgent(token="test-token")
    task = Task(
        description="Create secrets",
        agent_type="github_actions",
        params={
            "action": "manage_secrets",
            "repo": "owner/repo",
            "secret_action": "create",
            "secrets": {"DOCKER_USERNAME": "user", "DOCKER_PASSWORD": "pass"}
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True
    assert "created" in result.output.lower()
    print("[+] test_github_actions_manage_secrets_create")


def test_github_actions_list_workflows():
    """Test: GitHub Actions agent lists workflows"""
    agent = GitHubActionsAgent(token="test-token")
    task = Task(
        description="List workflows",
        agent_type="github_actions",
        params={
            "action": "list_workflows",
            "repo": "owner/repo",
            "limit": 5
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True
    assert "workflows" in result.output.lower()
    assert "workflows" in result.metadata
    print("[+] test_github_actions_list_workflows")


def test_github_actions_get_repo_info():
    """Test: GitHub Actions agent retrieves repo info"""
    agent = GitHubActionsAgent(token="test-token")
    task = Task(
        description="Get repo info",
        agent_type="github_actions",
        params={
            "action": "get_repo_info",
            "repo": "owner/repo"
        }
    )
    
    result = agent.execute(task)
    
    assert result.success == True
    assert "repository information" in result.output.lower()
    assert result.metadata is not None
    print("[+] test_github_actions_get_repo_info")


def test_github_actions_unknown_action():
    """Test: GitHub Actions agent handles unknown action"""
    agent = GitHubActionsAgent(token="test-token")
    task = Task(
        description="Unknown action",
        agent_type="github_actions",
        params={"action": "invalid_action"}
    )
    
    result = agent.execute(task)
    
    assert result.success == False
    assert "unknown action" in result.output.lower()
    print("[+] test_github_actions_unknown_action")


# Integration tests

def test_cicd_workflow_github_to_k8s():
    """Test: Full CI/CD workflow from GitHub to Kubernetes"""
    # Generate GitHub Actions workflow
    github_agent = GitHubActionsAgent(token="test-token")
    github_task = Task(
        description="Generate deployment workflow",
        agent_type="github_actions",
        params={
            "action": "generate_workflow",
            "name": "Deploy to Kubernetes",
            "language": "python",
            "docker_registry": "ghcr.io",
            "deploy_target": "kubernetes"
        }
    )
    
    workflow_result = github_agent.execute(github_task)
    
    assert workflow_result.success == True
    assert "yaml_content" in workflow_result.metadata
    assert ".github/workflows" in workflow_result.output
    print("[+] test_cicd_workflow_github_to_k8s")


def test_cicd_workflow_gitlab_to_docker():
    """Test: Full CI/CD workflow from GitLab with Docker"""
    # Generate GitLab CI config
    gitlab_agent = GitLabAgent(api_token="test-token")
    gitlab_task = Task(
        description="Generate Docker build and push pipeline",
        agent_type="gitlab",
        params={
            "action": "generate_config",
            "language": "python",
            "stages": ["build", "test", "deploy"],
            "registry": "docker.io",
            "include_tests": True
        }
    )
    
    config_result = gitlab_agent.execute(gitlab_task)
    
    assert config_result.success == True
    assert ".gitlab-ci.yml" in config_result.output
    assert "yaml_content" in config_result.metadata
    
    # Then trigger pipeline
    trigger_task = Task(
        description="Trigger pipeline",
        agent_type="gitlab",
        params={
            "action": "trigger_pipeline",
            "project_id": 789,
            "branch": "main",
            "variables": {"DOCKER_REGISTRY": "docker.io"}
        }
    )
    
    trigger_result = gitlab_agent.execute(trigger_task)
    
    assert trigger_result.success == True
    assert "pipeline triggered" in trigger_result.output.lower()
    print("[+] test_cicd_workflow_gitlab_to_docker")


if __name__ == "__main__":
    print("\n[*] Running CI/CD Agent Tests (GitLab + GitHub Actions)\n")
    
    tests = [
        test_gitlab_agent_trigger_pipeline,
        test_gitlab_agent_trigger_pipeline_missing_project,
        test_gitlab_agent_generate_python_config,
        test_gitlab_agent_generate_nodejs_config,
        test_gitlab_agent_get_pipeline_status,
        test_gitlab_agent_manage_variables_list,
        test_gitlab_agent_manage_variables_create,
        test_gitlab_agent_list_pipelines,
        test_gitlab_agent_get_project_info,
        test_gitlab_agent_unknown_action,
        test_github_actions_trigger_workflow,
        test_github_actions_trigger_workflow_missing_repo,
        test_github_actions_generate_python_workflow,
        test_github_actions_generate_nodejs_workflow,
        test_github_actions_get_workflow_status,
        test_github_actions_manage_secrets_list,
        test_github_actions_manage_secrets_create,
        test_github_actions_list_workflows,
        test_github_actions_get_repo_info,
        test_github_actions_unknown_action,
        test_cicd_workflow_github_to_k8s,
        test_cicd_workflow_gitlab_to_docker,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"[-] {test.__name__}: {str(e)}")
        except Exception as e:
            failed += 1
            print(f"[-] {test.__name__}: Unexpected error - {str(e)}")
    
    print(f"\n[*] Results: {passed}/{len(tests)} tests passing\n")
    
    if failed == 0:
        print("[+] ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"[-] {failed} tests failed")
        sys.exit(1)
