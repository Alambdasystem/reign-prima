"""
Tests for BashAgent - shell command and script execution agent.

BashAgent enables executing shell commands, running bash scripts,
managing processes, and performing file operations.
"""

import pytest
import sys
import tempfile
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from reign.swarm.agents.bash_agent import BashAgent, Task, AgentResult
except ModuleNotFoundError:
    pytest.skip("BashAgent not yet implemented", allow_module_level=True)


class TestBashAgentCreation:
    """Test BashAgent instantiation"""
    
    def test_can_create_bash_agent(self):
        """Test that BashAgent can be created"""
        agent = BashAgent()
        
        assert agent is not None
        assert hasattr(agent, 'execute')
    
    def test_agent_has_bash_expertise(self):
        """Test that BashAgent has appropriate expertise"""
        agent = BashAgent()
        
        assert hasattr(agent, 'expertise')
        expertise_str = ' '.join(agent.expertise).lower()
        assert 'shell' in expertise_str or 'bash' in expertise_str or 'command' in expertise_str


class TestBashCommandExecution:
    """Test basic command execution"""
    
    def test_executes_simple_command(self):
        """Test executing a simple shell command"""
        agent = BashAgent()
        
        task = Task(
            id=1,
            description="List current directory",
            agent_type="bash",
            params={"command": "dir" if sys.platform == "win32" else "ls"}
        )
        
        result = agent.execute(task)
        
        assert result.success is True
        assert result.confidence >= 0.7
        assert result.output is not None
    
    def test_executes_echo_command(self):
        """Test executing echo command"""
        agent = BashAgent()
        
        task = Task(
            id=1,
            description="Echo test message",
            agent_type="bash",
            params={"command": "echo 'Hello from REIGN'"}
        )
        
        result = agent.execute(task)
        
        assert result.success is True
        assert "Hello from REIGN" in result.output or "REIGN" in result.output
    
    def test_captures_command_output(self):
        """Test that command output is captured"""
        agent = BashAgent()
        
        task = Task(
            id=1,
            description="Run command with output",
            agent_type="bash",
            params={"command": "echo test123"}
        )
        
        result = agent.execute(task)
        
        assert result.output is not None
        assert "test123" in result.output
    
    def test_handles_command_errors(self):
        """Test handling of failed commands"""
        agent = BashAgent()
        
        # Use a command that will definitely fail
        task = Task(
            id=1,
            description="Run invalid command",
            agent_type="bash",
            params={"command": "nonexistentcommand12345"}
        )
        
        result = agent.execute(task)
        
        # Should handle gracefully (either success=False or error in output)
        assert result is not None
        assert isinstance(result, AgentResult)


class TestBashScriptExecution:
    """Test bash script execution"""
    
    def test_executes_script_from_content(self):
        """Test executing a bash script from content"""
        agent = BashAgent()
        
        script_content = """
echo "Starting script"
echo "Script complete"
"""
        
        task = Task(
            id=1,
            description="Run bash script",
            agent_type="bash",
            params={"script": script_content}
        )
        
        result = agent.execute(task)
        
        assert result.success is True
        assert "Script complete" in result.output or "complete" in result.output
    
    def test_executes_multiline_script(self):
        """Test executing a multi-line script"""
        agent = BashAgent()
        
        if sys.platform == "win32":
            script = "echo Line1\necho Line2\necho Line3"
        else:
            script = "echo 'Line1'\necho 'Line2'\necho 'Line3'"
        
        task = Task(
            id=1,
            description="Run multi-line script",
            agent_type="bash",
            params={"script": script}
        )
        
        result = agent.execute(task)
        
        assert result.success is True
        assert "Line" in result.output


class TestBashFileOperations:
    """Test file operations"""
    
    def test_can_create_file(self):
        """Test creating a file"""
        agent = BashAgent()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            
            task = Task(
                id=1,
                description="Create test file",
                agent_type="bash",
                params={
                    "command": f"echo 'test content' > {test_file}"
                }
            )
            
            result = agent.execute(task)
            
            assert result.success is True
            assert test_file.exists()
    
    def test_can_read_file(self):
        """Test reading a file"""
        agent = BashAgent()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test file content")
            temp_path = f.name
        
        try:
            if sys.platform == "win32":
                command = f"type {temp_path}"
            else:
                command = f"cat {temp_path}"
            
            task = Task(
                id=1,
                description="Read file",
                agent_type="bash",
                params={"command": command}
            )
            
            result = agent.execute(task)
            
            assert result.success is True
            assert "Test file content" in result.output
        finally:
            Path(temp_path).unlink()


class TestBashSafetyValidation:
    """Test dangerous command validation"""
    
    def test_validates_dangerous_rm_command(self):
        """Test validation of dangerous rm commands"""
        agent = BashAgent()
        
        task = Task(
            id=1,
            description="Dangerous rm command",
            agent_type="bash",
            params={"command": "rm -rf /"}
        )
        
        result = agent.execute(task)
        
        # Should either reject or warn about dangerous command
        assert result is not None
        # Either fails validation or includes warning
        assert result.success is False or "warning" in result.output.lower() or len(result.suggestions) > 0
    
    def test_allows_safe_commands(self):
        """Test that safe commands are allowed"""
        agent = BashAgent()
        
        task = Task(
            id=1,
            description="Safe echo command",
            agent_type="bash",
            params={"command": "echo 'safe'"}
        )
        
        result = agent.execute(task)
        
        assert result.success is True


class TestBashAgentValidation:
    """Test input validation"""
    
    def test_requires_command_or_script(self):
        """Test that either command or script is required"""
        agent = BashAgent()
        
        task = Task(
            id=1,
            description="Empty task",
            agent_type="bash",
            params={}
        )
        
        result = agent.execute(task)
        
        # Should fail validation or provide error
        assert result is not None
        assert result.success is False or len(result.suggestions) > 0
    
    def test_validates_command_format(self):
        """Test command format validation"""
        agent = BashAgent()
        
        # Empty command should fail
        task = Task(
            id=1,
            description="Empty command",
            agent_type="bash",
            params={"command": ""}
        )
        
        result = agent.execute(task)
        
        assert result.success is False


class TestBashAgentConfidence:
    """Test confidence scoring"""
    
    def test_confidence_in_valid_range(self):
        """Test that confidence scores are in valid range [0, 1]"""
        agent = BashAgent()
        
        task = Task(
            id=1,
            description="Echo command",
            agent_type="bash",
            params={"command": "echo test"}
        )
        
        result = agent.execute(task)
        
        assert 0.0 <= result.confidence <= 1.0
    
    def test_simple_commands_have_high_confidence(self):
        """Test that simple commands have high confidence"""
        agent = BashAgent()
        
        task = Task(
            id=1,
            description="Simple echo",
            agent_type="bash",
            params={"command": "echo hello"}
        )
        
        result = agent.execute(task)
        
        if result.success:
            assert result.confidence >= 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
