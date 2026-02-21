"""
Unit tests for TerraformAgent

TDD: Write tests first, then build the agent
"""
import pytest
from reign.swarm.agents.terraform_agent import TerraformAgent, AgentResult
from reign.swarm.reign_general import Task


class TestTerraformAgentCreation:
    """Test basic TerraformAgent setup"""
    
    def test_can_create_terraform_agent(self):
        """Test: Can we create a TerraformAgent?"""
        agent = TerraformAgent()
        
        assert agent is not None
        assert agent.name == "TerraformAgent"
    
    def test_agent_has_iac_expertise(self):
        """Test: Does agent know IaC expertise?"""
        agent = TerraformAgent()
        
        assert len(agent.expertise) > 0
        expertise_text = " ".join(agent.expertise).lower()
        assert "terraform" in expertise_text or "infrastructure" in expertise_text


class TestTerraformAgentExecution:
    """Test TerraformAgent task execution"""
    
    def test_agent_can_generate_terraform_config(self):
        """Test: Can agent generate Terraform config?"""
        agent = TerraformAgent()
        task = Task(
            id=1,
            description="Create VPC infrastructure",
            agent_type="terraform",
            params={
                "provider": "aws",
                "resource_type": "vpc",
                "cidr": "10.0.0.0/16"
            }
        )
        
        result = agent.execute(task)
        
        assert result.success == True
        assert "hcl" in result.output or "terraform" in result.output
    
    def test_validates_provider_is_specified(self):
        """Test: Agent requires cloud provider"""
        agent = TerraformAgent()
        task = Task(
            id=1,
            description="Create infrastructure",
            agent_type="terraform",
            params={
                "resource_type": "vpc"
                # Missing provider!
            }
        )
        
        result = agent.execute(task)
        
        # Should fail or have low confidence
        if not result.success:
            assert "provider" in result.error.lower()
        else:
            assert result.confidence < 0.8 or len(result.suggestions) > 0


class TestTerraformAgentPlanApply:
    """Test Terraform plan/apply workflow"""
    
    def test_agent_runs_terraform_plan(self):
        """Test: Agent can run terraform plan"""
        agent = TerraformAgent()
        task = Task(
            id=1,
            description="Plan infrastructure changes",
            agent_type="terraform",
            params={
                "action": "plan",
                "provider": "aws"
            }
        )
        
        result = agent.execute(task)
        
        assert result.success == True
        assert "plan" in result.output.get("action", "").lower()
    
    def test_warns_about_destructive_changes(self):
        """Test: Agent warns about destructive operations"""
        agent = TerraformAgent()
        task = Task(
            id=1,
            description="Destroy infrastructure",
            agent_type="terraform",
            params={
                "action": "destroy"
            }
        )
        
        result = agent.execute(task)
        
        # Should have warning or low confidence for destroy
        assert result.confidence < 0.9 or "destroy" in " ".join(result.suggestions).lower()


class TestTerraformAgentValidation:
    """Test Terraform validation"""
    
    def test_validates_hcl_syntax(self):
        """Test: Agent validates HCL syntax"""
        agent = TerraformAgent()
        task = Task(
            id=1,
            description="Validate Terraform config",
            agent_type="terraform",
            params={
                "action": "validate",
                "config": "resource invalid {{{}"  # Bad syntax
            }
        )
        
        result = agent.execute(task)
        
        assert result.success == False
        assert "syntax" in result.error.lower() or "invalid" in result.error.lower()
    
    def test_suggests_state_backend(self):
        """Test: Agent suggests remote state backend"""
        agent = TerraformAgent()
        task = Task(
            id=1,
            description="Create infrastructure without backend",
            agent_type="terraform",
            params={
                "provider": "aws",
                "resource_type": "vpc"
                # Missing backend configuration
            }
        )
        
        result = agent.execute(task)
        
        if result.success and result.suggestions:
            suggestions_text = " ".join(result.suggestions).lower()
            assert "state" in suggestions_text or "backend" in suggestions_text
