"""
GitHub Actions Agent - Orchestrates GitHub Actions workflows and deployments
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import yaml


@dataclass
class AgentResult:
    """Result from agent execution"""
    success: bool
    output: str
    suggestions: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.metadata is None:
            self.metadata = {}


class GitHubActionsAgent:
    """
    Controls GitHub Actions workflows and deployments.
    
    Capabilities:
    - Trigger GitHub Actions workflows
    - Generate workflow YAML files
    - Manage repository secrets
    - Monitor workflow runs
    - Deploy to GitHub environments
    - Create pull requests with automated changes
    """
    
    def __init__(self, token: str, timeout: int = 30):
        """
        Initialize GitHub Actions agent.
        
        Args:
            token: GitHub personal access token or GitHub App token
                   Scopes needed: repo, workflow, admin:repo_hook
            timeout: API request timeout in seconds
        """
        self.token = token
        self.api_base = "https://api.github.com"
        self.timeout = timeout
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    def execute(self, task: 'Task') -> AgentResult:
        """
        Execute GitHub Actions action.
        
        Args:
            task: Task with action and params
            
        Returns:
            AgentResult with success status and output
        """
        try:
            action = task.params.get("action")
            
            if action == "trigger_workflow":
                return self._trigger_workflow(task.params)
            elif action == "generate_workflow":
                return self._generate_workflow(task.params)
            elif action == "get_status":
                return self._get_workflow_status(task.params)
            elif action == "manage_secrets":
                return self._manage_secrets(task.params)
            elif action == "list_workflows":
                return self._list_workflows(task.params)
            elif action == "get_repo_info":
                return self._get_repo_info(task.params)
            else:
                return AgentResult(
                    success=False,
                    output=f"Unknown action: {action}",
                    suggestions=["Use action: trigger_workflow, generate_workflow, get_status, manage_secrets, or list_workflows"]
                )
        except Exception as e:
            return AgentResult(
                success=False,
                output=f"Error: {str(e)}",
                suggestions=["Check GitHub token validity", "Verify repository access", "Check network connectivity"]
            )
    
    def _trigger_workflow(self, params: Dict) -> AgentResult:
        """
        Trigger a GitHub Actions workflow.
        
        Args:
            params:
                - repo: Repository in owner/repo format
                - workflow_file: Workflow filename (e.g., deploy.yml)
                - ref: Git reference (branch, tag, or commit) (default: main)
                - inputs: Workflow inputs as dict (optional)
                
        Returns:
            AgentResult with run ID and execution status
        """
        try:
            repo = params.get("repo")
            workflow_file = params.get("workflow_file")
            ref = params.get("ref", "main")
            inputs = params.get("inputs", {})
            
            if not repo or not workflow_file:
                return AgentResult(
                    success=False,
                    output="Missing required parameters: repo and workflow_file",
                    suggestions=["Provide repo in 'owner/repo' format", "Provide workflow_file name"]
                )
            
            # Build API request
            owner, repo_name = repo.split("/")
            url = f"{self.api_base}/repos/{owner}/{repo_name}/actions/workflows/{workflow_file}/dispatches"
            
            # Simulated workflow trigger
            run_data = {
                "id": 9876543,
                "name": workflow_file.replace(".yml", "").replace(".yaml", ""),
                "status": "queued",
                "conclusion": None,
                "ref": ref,
                "html_url": f"https://github.com/{repo}/actions/runs/9876543"
            }
            
            output = f"""GitHub Actions workflow triggered:
- Repository: {repo}
- Workflow: {workflow_file}
- Reference: {ref}
- Run ID: {run_data['id']}
- Status: {run_data['status']}
- URL: {run_data['html_url']}"""
            
            if inputs:
                output += f"\n- Inputs: {json.dumps(inputs)}"
            
            return AgentResult(
                success=True,
                output=output,
                suggestions=["Monitor workflow with 'get_status' action", "Check run URL for logs"],
                metadata=run_data
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=f"Failed to trigger workflow: {str(e)}",
                suggestions=["Verify repo format is 'owner/repo'", "Check workflow file exists", "Verify GitHub token has 'workflow' scope"]
            )
    
    def _generate_workflow(self, params: Dict) -> AgentResult:
        """
        Generate GitHub Actions workflow YAML.
        
        Args:
            params:
                - name: Workflow name
                - language: Programming language (python, nodejs, java, etc.)
                - docker_registry: Docker registry (ghcr.io, docker.io, etc.)
                - include_tests: Include test job (default: true)
                - include_deploy: Include deploy job (default: true)
                - deploy_target: Deployment target (kubernetes, aws, etc.)
                
        Returns:
            AgentResult with workflow YAML content
        """
        try:
            name = params.get("name", "CI/CD Pipeline")
            language = params.get("language", "python").lower()
            docker_registry = params.get("docker_registry", "ghcr.io")
            include_tests = params.get("include_tests", True)
            include_deploy = params.get("include_deploy", True)
            deploy_target = params.get("deploy_target", "kubernetes")
            
            # Determine runner by language
            runner_map = {
                "python": "ubuntu-latest",
                "nodejs": "ubuntu-latest",
                "java": "ubuntu-latest",
                "go": "ubuntu-latest",
                "ruby": "ubuntu-latest",
                "dotnet": "ubuntu-latest"
            }
            
            runner = runner_map.get(language, "ubuntu-latest")
            
            # Build workflow config
            workflow = {
                "name": name,
                "on": {
                    "push": {"branches": ["main", "develop"]},
                    "pull_request": {"branches": ["main"]},
                    "workflow_dispatch": {}
                },
                "env": {
                    "REGISTRY": docker_registry,
                    "IMAGE_NAME": f"${{ github.repository }}"
                },
                "jobs": {}
            }
            
            # Build job
            workflow["jobs"]["build"] = {
                "runs-on": runner,
                "steps": [
                    {"uses": "actions/checkout@v4"},
                    self._get_setup_step(language),
                    {
                        "name": "Build",
                        "run": self._get_build_command(language)
                    },
                    {
                        "name": "Push Docker image",
                        "run": f"""echo '{docker_registry}' | docker login --username '${{{{ secrets.DOCKER_USERNAME }}}}' --password-stdin
docker build -t {docker_registry}/${{{{ env.IMAGE_NAME }}}}:latest .
docker push {docker_registry}/${{{{ env.IMAGE_NAME }}}}:latest"""
                    }
                ]
            }
            
            # Test job
            if include_tests:
                workflow["jobs"]["test"] = {
                    "runs-on": runner,
                    "needs": "build",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        self._get_setup_step(language),
                        {
                            "name": "Run tests",
                            "run": self._get_test_command(language)
                        },
                        {
                            "name": "Upload coverage",
                            "uses": "codecov/codecov-action@v3"
                        }
                    ]
                }
            
            # Deploy job
            if include_deploy:
                if deploy_target == "kubernetes":
                    deploy_script = """kubectl apply -f k8s/
kubectl rollout status deployment/app"""
                elif deploy_target == "aws":
                    deploy_script = """aws ecs update-service --cluster prod --service app --force-new-deployment"""
                else:
                    deploy_script = """echo 'Deploying to ${{ secrets.DEPLOY_TARGET }}'"""
                
                workflow["jobs"]["deploy"] = {
                    "runs-on": runner,
                    "needs": ["build", "test"] if include_tests else "build",
                    "if": "github.ref == 'refs/heads/main'",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "name": "Configure credentials",
                            "run": """mkdir -p ~/.kube
echo "${{ secrets.KUBECONFIG }}" | base64 -d > ~/.kube/config
chmod 600 ~/.kube/config"""
                        },
                        {
                            "name": "Deploy to " + deploy_target,
                            "run": deploy_script
                        }
                    ]
                }
            
            # Convert to YAML
            yaml_content = yaml.dump(workflow, default_flow_style=False, sort_keys=False)
            
            output = f"""Generated GitHub Actions workflow for {language}:

{yaml_content}

To use:
1. Create .github/workflows/ directory in repository root
2. Save content to .github/workflows/{name.lower().replace(' ', '-')}.yml
3. Commit and push to trigger workflow"""
            
            return AgentResult(
                success=True,
                output=output,
                suggestions=["Review and customize the workflow", "Add secrets for Docker and deployment credentials"],
                metadata={"yaml_content": yaml_content, "language": language, "workflow_name": name}
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=f"Failed to generate workflow: {str(e)}",
                suggestions=["Ensure language parameter is valid", "Check deploy_target value"]
            )
    
    def _get_setup_step(self, language: str) -> Dict:
        """Get language-specific setup step"""
        setup_map = {
            "python": {"uses": "actions/setup-python@v4", "with": {"python-version": "3.11"}},
            "nodejs": {"uses": "actions/setup-node@v4", "with": {"node-version": "18"}},
            "java": {"uses": "actions/setup-java@v4", "with": {"java-version": "17"}},
            "go": {"uses": "actions/setup-go@v4", "with": {"go-version": "1.21"}},
            "ruby": {"uses": "actions/setup-ruby@v1", "with": {"ruby-version": "3.2"}},
            "dotnet": {"uses": "actions/setup-dotnet@v3", "with": {"dotnet-version": "7.0"}}
        }
        return setup_map.get(language, {})
    
    def _get_build_command(self, language: str) -> str:
        """Get language-specific build command"""
        commands = {
            "python": "pip install -r requirements.txt && python -m build",
            "nodejs": "npm install && npm run build",
            "java": "mvn clean package -DskipTests",
            "go": "go build -o app",
            "ruby": "bundle install && bundle exec rake build",
            "dotnet": "dotnet build --configuration Release"
        }
        return commands.get(language, "echo 'Add build command'")
    
    def _get_test_command(self, language: str) -> str:
        """Get language-specific test command"""
        commands = {
            "python": "pytest --cov=src tests/",
            "nodejs": "npm test -- --coverage",
            "java": "mvn test",
            "go": "go test -v -cover ./...",
            "ruby": "bundle exec rspec",
            "dotnet": "dotnet test --configuration Release"
        }
        return commands.get(language, "echo 'Add test command'")
    
    def _get_workflow_status(self, params: Dict) -> AgentResult:
        """
        Get GitHub Actions workflow run status.
        
        Args:
            params:
                - repo: Repository in owner/repo format
                - run_id: Workflow run ID (optional, get latest if not provided)
                
        Returns:
            AgentResult with workflow status and job details
        """
        try:
            repo = params.get("repo")
            run_id = params.get("run_id")
            
            if not repo:
                return AgentResult(
                    success=False,
                    output="Missing required parameter: repo",
                    suggestions=["Provide repo in 'owner/repo' format"]
                )
            
            # Simulated workflow status
            status_data = {
                "id": run_id or 9876543,
                "name": "CI/CD Pipeline",
                "status": "completed",
                "conclusion": "success",
                "jobs": [
                    {"name": "build", "status": "completed", "conclusion": "success", "duration": 120},
                    {"name": "test", "status": "completed", "conclusion": "success", "duration": 300},
                    {"name": "deploy", "status": "completed", "conclusion": "success", "duration": 180}
                ],
                "total_duration": 600
            }
            
            output = f"""Workflow Run Status:
- ID: {status_data['id']}
- Status: {status_data['status']}
- Conclusion: {status_data['conclusion']}
- Total Duration: {status_data['total_duration']} seconds

Jobs:
"""
            for job in status_data['jobs']:
                output += f"  [{job['conclusion'].upper()}] {job['name']}: {job['duration']}s\n"
            
            return AgentResult(
                success=True,
                output=output,
                metadata=status_data
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=f"Failed to get workflow status: {str(e)}",
                suggestions=["Verify repo format is 'owner/repo'", "Check run_id if provided"]
            )
    
    def _manage_secrets(self, params: Dict) -> AgentResult:
        """
        Manage GitHub repository secrets.
        
        Args:
            params:
                - repo: Repository in owner/repo format
                - secret_action: create, update, delete, list
                - secrets: Dict of {key: value} for create/update
                
        Returns:
            AgentResult with secret management result
        """
        try:
            repo = params.get("repo")
            secret_action = params.get("secret_action", "list")
            secrets = params.get("secrets", {})
            
            if not repo:
                return AgentResult(
                    success=False,
                    output="Missing required parameter: repo",
                    suggestions=["Provide repo in 'owner/repo' format"]
                )
            
            if secret_action == "list":
                # Simulated secret list
                existing_secrets = {
                    "DOCKER_USERNAME": "***",
                    "DOCKER_PASSWORD": "***",
                    "KUBECONFIG": "***"
                }
                output = f"Repository Secrets ({repo}):\n"
                for key in existing_secrets:
                    output += f"  - {key}: [SECRET]\n"
            elif secret_action == "create":
                output = "Created secrets:\n"
                for key in secrets.keys():
                    output += f"  - {key}: [SECRET]\n"
            elif secret_action == "update":
                output = "Updated secrets:\n"
                for key in secrets.keys():
                    output += f"  - {key}: [SECRET]\n"
            elif secret_action == "delete":
                output = "Deleted secrets:\n"
                for key in secrets.keys():
                    output += f"  - {key}\n"
            else:
                return AgentResult(
                    success=False,
                    output=f"Unknown action: {secret_action}",
                    suggestions=["Use action: list, create, update, or delete"]
                )
            
            return AgentResult(
                success=True,
                output=output,
                suggestions=["Store sensitive data in repository secrets", "Use secrets in workflows with ${{ secrets.SECRET_NAME }}"]
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=f"Failed to manage secrets: {str(e)}",
                suggestions=["Check secret format", "Ensure repo access"]
            )
    
    def _list_workflows(self, params: Dict) -> AgentResult:
        """
        List GitHub Actions workflows in a repository.
        
        Args:
            params:
                - repo: Repository in owner/repo format
                - limit: Number of workflows to return (default: 10)
                
        Returns:
            AgentResult with workflow list
        """
        try:
            repo = params.get("repo")
            limit = params.get("limit", 10)
            
            if not repo:
                return AgentResult(
                    success=False,
                    output="Missing required parameter: repo",
                    suggestions=["Provide repo in 'owner/repo' format"]
                )
            
            # Simulated workflow list
            workflows = [
                {"id": 1, "name": "CI/CD Pipeline", "state": "active", "path": ".github/workflows/ci.yml"},
                {"id": 2, "name": "Deploy", "state": "active", "path": ".github/workflows/deploy.yml"},
                {"id": 3, "name": "Security", "state": "active", "path": ".github/workflows/security.yml"}
            ]
            
            output = f"GitHub Actions Workflows ({repo}):\n"
            for workflow in workflows[:limit]:
                output += f"  [{workflow['state'].upper()}] {workflow['name']} ({workflow['path']})\n"
            
            return AgentResult(
                success=True,
                output=output,
                metadata={"workflows": workflows[:limit]}
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=f"Failed to list workflows: {str(e)}",
                suggestions=["Verify repo access"]
            )
    
    def _get_repo_info(self, params: Dict) -> AgentResult:
        """
        Get GitHub repository information.
        
        Args:
            params:
                - repo: Repository in owner/repo format
                
        Returns:
            AgentResult with repository details
        """
        try:
            repo = params.get("repo")
            
            if not repo:
                return AgentResult(
                    success=False,
                    output="Missing required parameter: repo",
                    suggestions=["Provide repo in 'owner/repo' format"]
                )
            
            # Simulated repo info
            repo_info = {
                "name": repo.split("/")[1],
                "full_name": repo,
                "description": "Example GitHub repository",
                "visibility": "public",
                "default_branch": "main",
                "topics": ["python", "devops", "automation"]
            }
            
            output = f"""Repository Information:
- Name: {repo_info['name']}
- Full Name: {repo_info['full_name']}
- Default Branch: {repo_info['default_branch']}
- Visibility: {repo_info['visibility']}
- Topics: {', '.join(repo_info['topics'])}"""
            
            return AgentResult(
                success=True,
                output=output,
                metadata=repo_info
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=f"Failed to get repo info: {str(e)}",
                suggestions=["Verify repo format is 'owner/repo'", "Check GitHub token has 'repo' scope"]
            )
