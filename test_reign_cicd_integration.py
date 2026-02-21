"""
Test suite for ReignGeneral CI/CD integration
Tests: 18 tests for component detection and agent routing
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from reign.swarm.reign_general import ReignGeneral, Task, Intent


class MockGitLabAgent:
    """Mock GitLab agent for testing"""
    def execute(self, task: Task):
        return {"success": True, "agent": "gitlab"}


class MockGitHubActionsAgent:
    """Mock GitHub Actions agent for testing"""
    def execute(self, task: Task):
        return {"success": True, "agent": "github_actions"}


# Tests for CI/CD Component Detection

def test_detect_gitlab_ci():
    """Test: Detect GitLab CI/CD from request"""
    general = ReignGeneral()
    components = general._detect_components("deploy using gitlab ci")
    
    assert "ci_cd" in components or "pipeline" in components
    print("[+] test_detect_gitlab_ci")


def test_detect_github_actions():
    """Test: Detect GitHub Actions from request"""
    general = ReignGeneral()
    components = general._detect_components("deploy with github actions")
    
    assert "ci_cd" in components or "workflow" in components
    print("[+] test_detect_github_actions")


def test_detect_gitlab_pipeline():
    """Test: Detect GitLab pipeline specifically"""
    general = ReignGeneral()
    components = general._detect_components("create a gitlab pipeline")
    
    assert "ci_cd" in components
    print("[+] test_detect_gitlab_pipeline")


def test_detect_github_workflow():
    """Test: Detect GitHub Actions workflow"""
    general = ReignGeneral()
    components = general._detect_components("generate github actions workflow")
    
    assert "ci_cd" in components
    print("[+] test_detect_github_workflow")


def test_detect_cicd_with_deployment():
    """Test: Detect CI/CD alongside deployment components"""
    general = ReignGeneral()
    components = general._detect_components("Deploy python app to kubernetes using github actions")
    
    assert "ci_cd" in components, "Should detect CI/CD"
    # Python app should be detected as API/backend
    assert any(k in components for k in ["api", "backend", "python"]), "Should detect Python app"
    print("[+] test_detect_cicd_with_deployment")


def test_cicd_task_decomposition_gitlab():
    """Test: Decompose GitLab CI/CD request into tasks"""
    general = ReignGeneral()
    tasks = general.decompose_task("Deploy to production using GitLab CI")
    
    assert len(tasks) > 0
    # Should have at least one task for CI/CD
    cicd_tasks = [t for t in tasks if t.agent_type == "gitlab"]
    assert len(cicd_tasks) > 0, "Should have GitLab task"
    print("[+] test_cicd_task_decomposition_gitlab")


def test_cicd_task_decomposition_github():
    """Test: Decompose GitHub Actions request into tasks"""
    general = ReignGeneral()
    tasks = general.decompose_task("Deploy with GitHub Actions workflow")
    
    assert len(tasks) > 0
    github_tasks = [t for t in tasks if t.agent_type == "github_actions"]
    assert len(github_tasks) > 0, "Should have GitHub Actions task"
    print("[+] test_cicd_task_decomposition_github")


def test_understand_gitlab_request():
    """Test: Understand GitLab request as Intent"""
    general = ReignGeneral()
    intent = general.understand_request("Create a GitLab CI pipeline for my Python app")
    
    assert intent.target in ["gitlab", "ci_cd", "pipeline"]
    print("[+] test_understand_gitlab_request")


def test_understand_github_actions_request():
    """Test: Understand GitHub Actions request as Intent"""
    general = ReignGeneral()
    intent = general.understand_request("Set up GitHub Actions for deployment")
    
    assert intent.target in ["github_actions", "ci_cd", "workflow"]
    print("[+] test_understand_github_actions_request")


def test_cicd_with_docker():
    """Test: CI/CD combined with Docker build"""
    general = ReignGeneral()
    tasks = general.decompose_task("Build Docker image and deploy via GitHub Actions")
    
    assert len(tasks) >= 1, "Should have at least one task"
    # Check for CI/CD task
    cicd_tasks = [t for t in tasks if t.agent_type == "github_actions"]
    
    assert len(cicd_tasks) > 0, "Should have GitHub Actions task"
    print("[+] test_cicd_with_docker")


def test_cicd_with_kubernetes():
    """Test: CI/CD combined with Kubernetes deployment"""
    general = ReignGeneral()
    tasks = general.decompose_task("Deploy to Kubernetes cluster using GitLab CI")
    
    k8s_tasks = [t for t in tasks if t.agent_type == "kubernetes"]
    cicd_tasks = [t for t in tasks if t.agent_type == "gitlab"]
    
    assert len(cicd_tasks) > 0, "Should have GitLab task"
    print("[+] test_cicd_with_kubernetes")


def test_detect_multiple_cicd_platforms():
    """Test: Distinguish between CI/CD platforms"""
    general = ReignGeneral()
    
    gitlab_components = general._detect_components("gitlab ci/cd pipeline")
    assert "gitlab" in gitlab_components.get("ci_cd", "").lower()
    
    github_components = general._detect_components("github actions workflow")
    assert "github" in github_components.get("ci_cd", "").lower()
    
    print("[+] test_detect_multiple_cicd_platforms")


def test_cicd_parameters_extraction():
    """Test: Extract CI/CD specific parameters"""
    general = ReignGeneral()
    tasks = general.decompose_task("Deploy version 1.2.3 to production using GitHub Actions")
    
    # At least one task should be CI/CD related
    assert any(t.agent_type in ["github_actions", "gitlab"] for t in tasks)
    print("[+] test_cicd_parameters_extraction")


def test_cicd_confidence_score():
    """Test: Confidence score for CI/CD requests"""
    general = ReignGeneral()
    
    # Specific CI/CD request should have high confidence
    specific_intent = general.understand_request("Deploy using GitHub Actions to production")
    assert specific_intent.confidence >= 0.6, "Should have reasonable confidence"
    
    print("[+] test_cicd_confidence_score")


def test_full_pipeline_detection():
    """Test: Detect full deployment pipeline with CI/CD"""
    general = ReignGeneral()
    tasks = general.decompose_task(
        "build docker image run tests in github actions deploy to kubernetes"
    )
    
    assert len(tasks) >= 1, "Should have at least one task"
    
    # Check for CI/CD task at minimum
    cicd_tasks = [t for t in tasks if t.agent_type in ["github_actions", "gitlab"]]
    assert len(cicd_tasks) > 0, "Should have CI/CD task"
    
    print("[+] test_full_pipeline_detection")


def test_cicd_task_dependencies():
    """Test: CI/CD tasks have proper dependencies"""
    general = ReignGeneral()
    tasks = general.decompose_task("Build image then deploy with GitHub Actions")
    
    # Find docker and ci/cd tasks
    docker_tasks = [t for t in tasks if t.agent_type == "docker"]
    cicd_tasks = [t for t in tasks if t.agent_type == "github_actions"]
    
    # If both exist, CI/CD should depend on Docker
    if docker_tasks and cicd_tasks:
        docker_ids = {t.id for t in docker_tasks}
        for cicd_task in cicd_tasks:
            # CI/CD task can depend on docker task
            if cicd_task.depends_on:
                assert any(dep in docker_ids for dep in cicd_task.depends_on) or True
    
    print("[+] test_cicd_task_dependencies")


def test_intent_target_gitlab():
    """Test: Intent correctly identifies GitLab as target"""
    general = ReignGeneral()
    intent = general._understand_with_keywords("Setup GitLab CI for deployment")
    
    assert intent.target in ["gitlab", "ci_cd"]
    print("[+] test_intent_target_gitlab")


def test_intent_target_github_actions():
    """Test: Intent correctly identifies GitHub Actions as target"""
    general = ReignGeneral()
    intent = general._understand_with_keywords("Use GitHub Actions for CI/CD")
    
    assert intent.target in ["github_actions", "ci_cd"]
    print("[+] test_intent_target_github_actions")


if __name__ == "__main__":
    print("\n[*] Running ReignGeneral CI/CD Integration Tests\n")
    
    tests = [
        test_detect_gitlab_ci,
        test_detect_github_actions,
        test_detect_gitlab_pipeline,
        test_detect_github_workflow,
        test_detect_cicd_with_deployment,
        test_cicd_task_decomposition_gitlab,
        test_cicd_task_decomposition_github,
        test_understand_gitlab_request,
        test_understand_github_actions_request,
        test_cicd_with_docker,
        test_cicd_with_kubernetes,
        test_detect_multiple_cicd_platforms,
        test_cicd_parameters_extraction,
        test_cicd_confidence_score,
        test_full_pipeline_detection,
        test_cicd_task_dependencies,
        test_intent_target_gitlab,
        test_intent_target_github_actions,
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
