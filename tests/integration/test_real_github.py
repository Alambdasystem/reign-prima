"""
Integration tests for real GitHub API operations.

These tests interact with actual GitHub API via PyGithub.
Requires GITHUB_TOKEN environment variable for authentication.
"""

import pytest
import os
from pathlib import Path
import sys

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from reign.swarm.executors.real_github_executor import RealGitHubExecutor
except ModuleNotFoundError:
    pytest.skip("RealGitHubExecutor not yet implemented", allow_module_level=True)


def check_github_token():
    """Check if GitHub token is available"""
    return os.getenv("GITHUB_TOKEN") is not None


# Skip all tests if no GitHub token
pytestmark = pytest.mark.skipif(
    not check_github_token(),
    reason="GITHUB_TOKEN environment variable not set"
)


class TestRealGitHubExecutor:
    """Test real GitHub executor with PyGithub"""
    
    def test_can_create_executor(self):
        """Test that RealGitHubExecutor can be instantiated"""
        token = os.getenv("GITHUB_TOKEN")
        executor = RealGitHubExecutor(token=token)
        
        assert executor is not None
    
    def test_can_authenticate(self):
        """Test GitHub authentication"""
        token = os.getenv("GITHUB_TOKEN")
        executor = RealGitHubExecutor(token=token)
        
        result = executor.get_authenticated_user()
        
        assert result is not None
        assert "login" in result or "user" in str(result).lower()
    
    def test_can_list_repositories(self):
        """Test listing user repositories"""
        token = os.getenv("GITHUB_TOKEN")
        executor = RealGitHubExecutor(token=token)
        
        result = executor.list_repositories()
        
        assert result is not None
        assert isinstance(result, list)
    
    def test_can_get_repository_info(self):
        """Test getting repository information"""
        token = os.getenv("GITHUB_TOKEN")
        executor = RealGitHubExecutor(token=token)
        
        # Get user's repos first
        repos = executor.list_repositories()
        
        if repos and len(repos) > 0:
            repo_name = repos[0]["name"]
            user = executor.get_authenticated_user()
            full_name = f"{user['login']}/{repo_name}"
            
            result = executor.get_repository(full_name)
            
            assert result is not None
            assert "name" in result
    
    def test_handles_invalid_token(self):
        """Test handling of invalid GitHub token"""
        executor = RealGitHubExecutor(token="invalid_token_12345")
        
        result = executor.get_authenticated_user()
        
        # Should return error or None
        assert result is None or "error" in str(result).lower()


class TestGitHubExecutorValidation:
    """Test GitHub executor validation"""
    
    def test_requires_token(self):
        """Test that token is required"""
        with pytest.raises((ValueError, TypeError)):
            RealGitHubExecutor(token=None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
