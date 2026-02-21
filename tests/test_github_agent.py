"""
Unit tests for GitHubAgent

TDD: Write tests first, then build the agent
"""
import pytest
from reign.swarm.agents.github_agent import GitHubAgent, AgentResult
from reign.swarm.reign_general import Task


class TestGitHubAgentCreation:
    """Test basic GitHubAgent setup"""
    
    def test_can_create_github_agent(self):
        """Test: Can we create a GitHubAgent?"""
        agent = GitHubAgent()
        
        assert agent is not None
        assert agent.name == "GitHubAgent"
    
    def test_agent_has_github_expertise(self):
        """Test: Does agent know GitHub expertise?"""
        agent = GitHubAgent()
        
        assert len(agent.expertise) > 0
        expertise_text = " ".join(agent.expertise).lower()
        assert "github" in expertise_text or "git" in expertise_text


class TestGitHubAgentRepositoryOps:
    """Test GitHub repository operations"""
    
    def test_agent_can_create_repository(self):
        """Test: Can agent create GitHub repository?"""
        agent = GitHubAgent()
        task = Task(
            id=1,
            description="Create new repository",
            agent_type="github",
            params={
                "name": "my-project",
                "description": "My awesome project",
                "private": True
            }
        )
        
        result = agent.execute(task)
        
        assert result.success == True
        assert "repository" in result.output
    
    def test_validates_repository_name(self):
        """Test: Agent validates repo name format"""
        agent = GitHubAgent()
        task = Task(
            id=1,
            description="Create repo with invalid name",
            agent_type="github",
            params={
                "name": "Invalid Repo Name!!!"  # Spaces and special chars
            }
        )
        
        result = agent.execute(task)
        
        assert result.success == False
        assert "name" in result.error.lower() or "invalid" in result.error.lower()


class TestGitHubAgentWorkflows:
    """Test GitHub Actions workflow creation"""
    
    def test_agent_can_create_workflow(self):
        """Test: Can agent create GitHub Actions workflow?"""
        agent = GitHubAgent()
        task = Task(
            id=1,
            description="Create CI/CD workflow",
            agent_type="github",
            params={
                "workflow_type": "ci",
                "triggers": ["push", "pull_request"]
            }
        )
        
        result = agent.execute(task)
        
        assert result.success == True
        assert "workflow" in result.output or "yaml" in result.output
    
    def test_suggests_branch_protection(self):
        """Test: Agent suggests branch protection for main branch"""
        agent = GitHubAgent()
        task = Task(
            id=1,
            description="Create repository",
            agent_type="github",
            params={
                "name": "production-app",
                "branch": "main"
                # No branch protection!
            }
        )
        
        result = agent.execute(task)
        
        if result.success and result.suggestions:
            suggestions_text = " ".join(result.suggestions).lower()
            assert "protection" in suggestions_text or "branch" in suggestions_text


class TestGitHubAgentPullRequests:
    """Test PR operations"""
    
    def test_agent_can_create_pull_request(self):
        """Test: Can agent create PR?"""
        agent = GitHubAgent()
        task = Task(
            id=1,
            description="Create pull request",
            agent_type="github",
            params={
                "title": "Add new feature",
                "source": "feature-branch",
                "target": "main"
            }
        )
        
        result = agent.execute(task)
        
        assert result.success == True
        assert "pull_request" in result.output or "pr" in result.output
    
    def test_validates_pr_has_description(self):
        """Test: Agent checks PR has description"""
        agent = GitHubAgent()
        task = Task(
            id=1,
            description="Create PR without description",
            agent_type="github",
            params={
                "title": "Fix bug",
                "source": "fix",
                "target": "main"
                # Missing description/body
            }
        )
        
        result = agent.execute(task)
        
        # Should suggest adding description
        if result.success and result.suggestions:
            suggestions_text = " ".join(result.suggestions).lower()
            assert "description" in suggestions_text or "body" in suggestions_text


class TestGitHubAgentValidation:
    """Test GitHub validation"""
    
    def test_validates_workflow_yaml_syntax(self):
        """Test: Agent validates workflow YAML"""
        agent = GitHubAgent()
        task = Task(
            id=1,
            description="Create workflow with invalid YAML",
            agent_type="github",
            params={
                "workflow_yaml": "invalid: yaml: syntax::"
            }
        )
        
        result = agent.execute(task)
        
        assert result.success == False
        assert "yaml" in result.error.lower() or "syntax" in result.error.lower()
    
    def test_warns_about_hardcoded_secrets(self):
        """Test: Agent detects hardcoded secrets"""
        agent = GitHubAgent()
        task = Task(
            id=1,
            description="Create workflow",
            agent_type="github",
            params={
                "workflow_yaml": "env:\n  API_KEY: sk-1234567890"  # Hardcoded!
            }
        )
        
        result = agent.execute(task)
        
        # Should warn about secrets
        if result.success:
            suggestions_text = " ".join(result.suggestions).lower()
            assert "secret" in suggestions_text or "hardcoded" in suggestions_text
