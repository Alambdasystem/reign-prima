"""
Real GitHub executor using PyGithub SDK.

This executor performs actual GitHub API operations using the PyGithub library.
"""

from github import Github, GithubException, BadCredentialsException
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class RealGitHubExecutor:
    """Real GitHub executor using PyGithub SDK"""
    
    def __init__(self, token: str):
        """
        Initialize GitHub executor.
        
        Args:
            token: GitHub personal access token
        
        Raises:
            ValueError: If token is None or empty
        """
        if not token:
            raise ValueError("GitHub token is required")
        
        try:
            self.client = Github(token)
            # Verify authentication
            self.client.get_user().login
            logger.info("Successfully authenticated with GitHub")
        except BadCredentialsException as e:
            logger.error("Invalid GitHub credentials")
            self.client = Github(token)  # Still create client but it won't work
        except Exception as e:
            logger.error(f"GitHub initialization error: {e}")
            raise
    
    def get_authenticated_user(self) -> Optional[Dict[str, Any]]:
        """
        Get authenticated user information.
        
        Returns:
            Dict with user info, or None if error
        """
        try:
            user = self.client.get_user()
            
            return {
                "login": user.login,
                "name": user.name,
                "email": user.email,
                "public_repos": user.public_repos,
                "followers": user.followers,
                "following": user.following
            }
        
        except BadCredentialsException:
            logger.error("Invalid GitHub credentials")
            return None
        
        except Exception as e:
            logger.error(f"Error getting authenticated user: {e}")
            return None
    
    def list_repositories(
        self,
        visibility: str = "all",
        sort: str = "updated"
    ) -> List[Dict[str, Any]]:
        """
        List user's repositories.
        
        Args:
            visibility: Repository visibility (all, public, private)
            sort: Sort order (created, updated, pushed, full_name)
        
        Returns:
            List of repository dictionaries
        """
        try:
            user = self.client.get_user()
            repos = user.get_repos(visibility=visibility, sort=sort)
            
            result = []
            for repo in repos:
                result.append({
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "private": repo.private,
                    "url": repo.html_url,
                    "default_branch": repo.default_branch,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Error listing repositories: {e}")
            return []
    
    def get_repository(self, full_name: str) -> Optional[Dict[str, Any]]:
        """
        Get repository information.
        
        Args:
            full_name: Repository full name (owner/repo)
        
        Returns:
            Dict with repository info, or None if not found
        """
        try:
            repo = self.client.get_repo(full_name)
            
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "url": repo.html_url,
                "default_branch": repo.default_branch,
                "language": repo.language,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "open_issues": repo.open_issues_count,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None
            }
        
        except Exception as e:
            logger.error(f"Error getting repository {full_name}: {e}")
            return None
    
    def create_repository(
        self,
        name: str,
        description: Optional[str] = None,
        private: bool = False,
        auto_init: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new repository.
        
        Args:
            name: Repository name
            description: Repository description
            private: Whether repository is private
            auto_init: Initialize with README
        
        Returns:
            Dict with operation result
        """
        try:
            user = self.client.get_user()
            
            repo = user.create_repo(
                name=name,
                description=description,
                private=private,
                auto_init=auto_init
            )
            
            logger.info(f"Successfully created repository: {repo.full_name}")
            
            return {
                "success": True,
                "repository": {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "url": repo.html_url
                }
            }
        
        except GithubException as e:
            logger.error(f"Error creating repository: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        
        except Exception as e:
            logger.error(f"Unexpected error creating repository: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_repository(self, full_name: str) -> Dict[str, Any]:
        """
        Delete a repository.
        
        Args:
            full_name: Repository full name (owner/repo)
        
        Returns:
            Dict with operation result
        """
        try:
            repo = self.client.get_repo(full_name)
            repo.delete()
            
            logger.info(f"Successfully deleted repository: {full_name}")
            
            return {
                "success": True
            }
        
        except Exception as e:
            logger.error(f"Error deleting repository {full_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_issue(
        self,
        repo_full_name: str,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create an issue in a repository.
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            title: Issue title
            body: Issue body/description
            labels: List of label names
        
        Returns:
            Dict with operation result
        """
        try:
            repo = self.client.get_repo(repo_full_name)
            
            issue = repo.create_issue(
                title=title,
                body=body,
                labels=labels or []
            )
            
            logger.info(f"Successfully created issue #{issue.number} in {repo_full_name}")
            
            return {
                "success": True,
                "issue": {
                    "number": issue.number,
                    "title": issue.title,
                    "url": issue.html_url
                }
            }
        
        except Exception as e:
            logger.error(f"Error creating issue: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_pull_request(
        self,
        repo_full_name: str,
        title: str,
        head: str,
        base: str,
        body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a pull request.
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            title: PR title
            head: Head branch
            base: Base branch
            body: PR description
        
        Returns:
            Dict with operation result
        """
        try:
            repo = self.client.get_repo(repo_full_name)
            
            pr = repo.create_pull(
                title=title,
                head=head,
                base=base,
                body=body
            )
            
            logger.info(f"Successfully created PR #{pr.number} in {repo_full_name}")
            
            return {
                "success": True,
                "pull_request": {
                    "number": pr.number,
                    "title": pr.title,
                    "url": pr.html_url
                }
            }
        
        except Exception as e:
            logger.error(f"Error creating pull request: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_workflow_runs(
        self,
        repo_full_name: str,
        branch: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get workflow runs for a repository.
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            branch: Filter by branch
            status: Filter by status (queued, in_progress, completed)
        
        Returns:
            List of workflow run dictionaries
        """
        try:
            repo = self.client.get_repo(repo_full_name)
            
            kwargs = {}
            if branch:
                kwargs['branch'] = branch
            if status:
                kwargs['status'] = status
            
            runs = repo.get_workflow_runs(**kwargs)
            
            result = []
            for run in runs:
                result.append({
                    "id": run.id,
                    "name": run.name,
                    "status": run.status,
                    "conclusion": run.conclusion,
                    "branch": run.head_branch,
                    "url": run.html_url
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting workflow runs: {e}")
            return []
