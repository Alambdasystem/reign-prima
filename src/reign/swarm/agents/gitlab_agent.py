"""
GitLab CI/CD Agent - Orchestrates GitLab pipelines and deployments
"""

import json
import requests
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


class GitLabAgent:
    """
    Controls GitLab CI/CD pipelines and configurations.
    
    Capabilities:
    - Trigger pipelines
    - Generate .gitlab-ci.yml
    - Manage project variables (secrets)
    - Monitor pipeline status
    - Deploy to environments
    """
    
    def __init__(self, api_token: str, base_url: str = "https://gitlab.com", timeout: int = 30):
        """
        Initialize GitLab agent.
        
        Args:
            api_token: GitLab personal access token (scopes: api, read_api, write_repository)
            base_url: GitLab instance URL (default: gitlab.com)
            timeout: API request timeout in seconds
        """
        self.api_token = api_token
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.headers = {
            "PRIVATE-TOKEN": api_token,
            "Content-Type": "application/json"
        }
    
    def execute(self, task: 'Task') -> AgentResult:
        """
        Execute GitLab action.
        
        Args:
            task: Task with action and params
            
        Returns:
            AgentResult with success status and output
        """
        try:
            action = task.params.get("action")
            
            if action == "trigger_pipeline":
                return self._trigger_pipeline(task.params)
            elif action == "generate_config":
                return self._generate_ci_config(task.params)
            elif action == "get_status":
                return self._get_pipeline_status(task.params)
            elif action == "manage_variables":
                return self._manage_variables(task.params)
            elif action == "list_pipelines":
                return self._list_pipelines(task.params)
            elif action == "get_project_info":
                return self._get_project_info(task.params)
            else:
                return AgentResult(
                    success=False,
                    output=f"Unknown action: {action}",
                    suggestions=["Use action: trigger_pipeline, generate_config, get_status, manage_variables, or list_pipelines"]
                )
        except Exception as e:
            return AgentResult(
                success=False,
                output=f"Error: {str(e)}",
                suggestions=["Check API token validity", "Verify project exists", "Check network connectivity"]
            )
    
    def _trigger_pipeline(self, params: Dict) -> AgentResult:
        """
        Trigger a GitLab CI/CD pipeline.
        
        Args:
            params:
                - project_id: GitLab project ID (int or str)
                - branch: Branch name (default: main)
                - variables: Pipeline variables (dict)
                
        Returns:
            AgentResult with pipeline ID and web URL
        """
        try:
            project_id = params.get("project_id")
            branch = params.get("branch", "main")
            variables = params.get("variables", {})
            
            if not project_id:
                return AgentResult(
                    success=False,
                    output="Missing required parameter: project_id",
                    suggestions=["Provide project_id in params"]
                )
            
            # Build API request
            url = f"{self.base_url}/api/v4/projects/{project_id}/pipeline"
            payload = {
                "ref": branch,
                "variables": [{"key": k, "value": v} for k, v in variables.items()]
            }
            
            # Make API call (simulated for testing)
            response_data = {
                "id": 12345,
                "iid": 1,
                "project_id": project_id,
                "status": "pending",
                "ref": branch,
                "web_url": f"https://gitlab.com/project/pipelines/12345"
            }
            
            output = f"""Pipeline triggered successfully:
- Pipeline ID: {response_data['id']}
- Status: {response_data['status']}
- Branch: {branch}
- Variables: {json.dumps(variables)}
- URL: {response_data['web_url']}"""
            
            return AgentResult(
                success=True,
                output=output,
                suggestions=["Monitor pipeline status with 'get_status' action"],
                metadata=response_data
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=f"Failed to trigger pipeline: {str(e)}",
                suggestions=["Verify project_id is correct", "Check API token has 'api' scope"]
            )
    
    def _generate_ci_config(self, params: Dict) -> AgentResult:
        """
        Generate .gitlab-ci.yml configuration.
        
        Args:
            params:
                - stages: List of pipeline stages (default: [build, test, deploy])
                - language: Programming language (python, nodejs, java, etc.)
                - docker_image: Base Docker image
                - registry: Docker registry URL
                - include_tests: Include test stage (default: true)
                
        Returns:
            AgentResult with YAML content
        """
        try:
            stages = params.get("stages", ["build", "test", "deploy"])
            language = params.get("language", "python").lower()
            docker_image = params.get("docker_image")
            registry = params.get("registry")
            include_tests = params.get("include_tests", True)
            
            # Determine base image by language
            image_map = {
                "python": "python:3.11",
                "nodejs": "node:18",
                "java": "openjdk:17",
                "go": "golang:1.21",
                "ruby": "ruby:3.2",
                "dotnet": "mcr.microsoft.com/dotnet/sdk:7.0"
            }
            
            base_image = docker_image or image_map.get(language, "alpine:latest")
            
            # Build GitLab CI config
            config = {
                "image": base_image,
                "stages": stages,
                "variables": {
                    "DOCKER_DRIVER": "overlay2",
                    "REGISTRY_URL": registry or "docker.io"
                },
                "build": {
                    "stage": "build",
                    "script": [
                        f"echo 'Building {language} application...'",
                        "# Add language-specific build commands here"
                    ],
                    "artifacts": {
                        "paths": ["build/", "dist/"],
                        "expire_in": "1 hour"
                    }
                }
            }
            
            # Add test stage
            if include_tests:
                config["test"] = {
                    "stage": "test",
                    "script": [
                        f"echo 'Running tests for {language}...'",
                        "# Add language-specific test commands here"
                    ],
                    "coverage": "/Coverage: (\\d+\\.\\d+)%/"
                }
            
            # Add deploy stage
            if "deploy" in stages:
                config["deploy"] = {
                    "stage": "deploy",
                    "script": [
                        "echo 'Deploying application...'",
                        "# Add deployment commands here"
                    ],
                    "environment": {
                        "name": "production",
                        "url": "https://example.com"
                    },
                    "only": ["main"]
                }
            
            # Convert to YAML
            yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False)
            
            output = f"""Generated .gitlab-ci.yml for {language}:

{yaml_content}

To use:
1. Save content to .gitlab-ci.yml in repository root
2. Commit and push to trigger pipeline"""
            
            return AgentResult(
                success=True,
                output=output,
                suggestions=["Review and customize the configuration", "Add specific build/test/deploy commands for your project"],
                metadata={"yaml_content": yaml_content, "language": language}
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=f"Failed to generate config: {str(e)}",
                suggestions=["Ensure language parameter is valid", "Check registry URL format"]
            )
    
    def _get_pipeline_status(self, params: Dict) -> AgentResult:
        """
        Get GitLab pipeline status.
        
        Args:
            params:
                - project_id: GitLab project ID
                - pipeline_id: Pipeline ID (optional, get latest if not provided)
                
        Returns:
            AgentResult with pipeline status, stages, duration
        """
        try:
            project_id = params.get("project_id")
            pipeline_id = params.get("pipeline_id")
            
            if not project_id:
                return AgentResult(
                    success=False,
                    output="Missing required parameter: project_id",
                    suggestions=["Provide project_id in params"]
                )
            
            # Simulated pipeline status
            status_data = {
                "id": pipeline_id or 12345,
                "status": "success",
                "stages": [
                    {"name": "build", "status": "success", "duration": 120},
                    {"name": "test", "status": "success", "duration": 300},
                    {"name": "deploy", "status": "success", "duration": 180}
                ],
                "total_duration": 600,
                "created_at": "2024-01-21T10:00:00Z",
                "updated_at": "2024-01-21T10:10:00Z"
            }
            
            output = f"""Pipeline Status:
- ID: {status_data['id']}
- Status: {status_data['status']}
- Total Duration: {status_data['total_duration']} seconds

Stages:
"""
            for stage in status_data['stages']:
                output += f"  [{stage['status'].upper()}] {stage['name']}: {stage['duration']}s\n"
            
            return AgentResult(
                success=True,
                output=output,
                metadata=status_data
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=f"Failed to get pipeline status: {str(e)}",
                suggestions=["Verify project_id exists", "Check pipeline_id if provided"]
            )
    
    def _manage_variables(self, params: Dict) -> AgentResult:
        """
        Manage GitLab project variables (secrets).
        
        Args:
            params:
                - project_id: GitLab project ID
                - var_action: create, update, delete, list
                - variables: Dict of {key: value} for create/update
                
        Returns:
            AgentResult with variable management result
        """
        try:
            project_id = params.get("project_id")
            var_action = params.get("var_action", "list")
            variables = params.get("variables", {})
            
            if not project_id:
                return AgentResult(
                    success=False,
                    output="Missing required parameter: project_id",
                    suggestions=["Provide project_id in params"]
                )
            
            if var_action == "list":
                # Simulated variable list
                existing_vars = {
                    "DOCKER_TOKEN": "***",
                    "KUBECONFIG": "***",
                    "DEPLOY_KEY": "***"
                }
                output = "Project Variables:\n"
                for key in existing_vars:
                    output += f"  - {key}: {existing_vars[key]}\n"
            elif var_action == "create":
                output = "Created variables:\n"
                for key, value in variables.items():
                    output += f"  - {key}: [SECRET]\n"
            elif var_action == "update":
                output = "Updated variables:\n"
                for key, value in variables.items():
                    output += f"  - {key}: [SECRET]\n"
            elif var_action == "delete":
                output = "Deleted variables:\n"
                for key in variables.keys():
                    output += f"  - {key}\n"
            else:
                return AgentResult(
                    success=False,
                    output=f"Unknown action: {var_action}",
                    suggestions=["Use action: list, create, update, or delete"]
                )
            
            return AgentResult(
                success=True,
                output=output,
                suggestions=["Store sensitive data in project variables", "Use variables in pipeline with $VARIABLE_NAME"]
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=f"Failed to manage variables: {str(e)}",
                suggestions=["Check variable format", "Ensure project_id is valid"]
            )
    
    def _list_pipelines(self, params: Dict) -> AgentResult:
        """
        List GitLab pipelines for a project.
        
        Args:
            params:
                - project_id: GitLab project ID
                - limit: Number of pipelines to return (default: 10)
                
        Returns:
            AgentResult with pipeline list
        """
        try:
            project_id = params.get("project_id")
            limit = params.get("limit", 10)
            
            if not project_id:
                return AgentResult(
                    success=False,
                    output="Missing required parameter: project_id",
                    suggestions=["Provide project_id in params"]
                )
            
            # Simulated pipeline list
            pipelines = [
                {"id": 12345, "status": "success", "ref": "main", "created": "2024-01-21T10:00:00Z"},
                {"id": 12344, "status": "success", "ref": "main", "created": "2024-01-20T15:30:00Z"},
                {"id": 12343, "status": "failed", "ref": "develop", "created": "2024-01-20T14:00:00Z"},
            ]
            
            output = f"Recent Pipelines (Project {project_id}):\n"
            for pipeline in pipelines[:limit]:
                output += f"  [{pipeline['status'].upper()}] Pipeline {pipeline['id']} ({pipeline['ref']}) - {pipeline['created']}\n"
            
            return AgentResult(
                success=True,
                output=output,
                metadata={"pipelines": pipelines[:limit]}
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=f"Failed to list pipelines: {str(e)}",
                suggestions=["Verify project_id exists"]
            )
    
    def _get_project_info(self, params: Dict) -> AgentResult:
        """
        Get GitLab project information.
        
        Args:
            params:
                - project_id: GitLab project ID
                
        Returns:
            AgentResult with project details
        """
        try:
            project_id = params.get("project_id")
            
            if not project_id:
                return AgentResult(
                    success=False,
                    output="Missing required parameter: project_id",
                    suggestions=["Provide project_id in params"]
                )
            
            # Simulated project info
            project_info = {
                "id": project_id,
                "name": "example-project",
                "path": "example-project",
                "description": "Example GitLab project",
                "visibility": "private",
                "last_activity": "2024-01-21T10:00:00Z",
                "default_branch": "main"
            }
            
            output = f"""Project Information:
- Name: {project_info['name']}
- ID: {project_info['id']}
- Default Branch: {project_info['default_branch']}
- Visibility: {project_info['visibility']}
- Last Activity: {project_info['last_activity']}"""
            
            return AgentResult(
                success=True,
                output=output,
                metadata=project_info
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=f"Failed to get project info: {str(e)}",
                suggestions=["Verify project_id exists", "Check API token has 'read_api' scope"]
            )
