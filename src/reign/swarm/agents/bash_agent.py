"""
BashAgent - Shell command and script execution agent.

Executes shell commands, runs bash scripts, manages processes,
and performs file operations with safety validation.
"""

import subprocess
import tempfile
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging
import sys

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result from agent execution"""
    success: bool
    confidence: float
    output: str = ""
    error: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    self_validated: bool = False
    
    def __post_init__(self):
        """Validate confidence range"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")


@dataclass
class Task:
    """Task representation"""
    id: int
    description: str
    agent_type: str
    params: Dict[str, Any] = field(default_factory=dict)


class BashAgent:
    """Agent for executing shell commands and bash scripts"""
    
    def __init__(self):
        """Initialize BashAgent"""
        super().__init__()
        self.expertise = [
            "Shell command execution",
            "Bash script execution",
            "File operations",
            "Process management",
            "System administration",
            "Command-line automation"
        ]
        
        # Dangerous command patterns to validate
        self.dangerous_patterns = [
            r"rm\s+-rf\s+/",  # rm -rf /
            r"rm\s+-rf\s+~",  # rm -rf ~
            r":\(\)\{\s*:\|:&\s*\};:",  # Fork bomb
            r"dd\s+if=.*\s+of=/dev/sd",  # Disk wipe
            r"mkfs\.",  # Format filesystem
            r">\s*/dev/sd",  # Write to disk device
        ]
    
    def execute(self, task: Task) -> AgentResult:
        """
        Execute a bash command or script.
        
        Args:
            task: Task with command or script in params
        
        Returns:
            AgentResult with execution output
        """
        params = task.params
        
        # Validate input
        if "command" not in params and "script" not in params:
            return AgentResult(
                success=False,
                confidence=0.0,
                output="",
                error="Either 'command' or 'script' parameter required",
                suggestions=["Provide 'command' parameter for single command",
                           "Provide 'script' parameter for multi-line script"]
            )
        
        command = params.get("command", "")
        script = params.get("script", "")
        
        # Validate not empty
        if not command and not script:
            return AgentResult(
                success=False,
                confidence=0.0,
                output="",
                error="Command or script cannot be empty"
            )
        
        # Safety validation
        content = command or script
        safety_check = self._validate_safety(content)
        if not safety_check["safe"]:
            return AgentResult(
                success=False,
                confidence=0.0,
                output="",
                error=safety_check["reason"],
                suggestions=["Review command for safety",
                           "Use less destructive alternatives",
                           "Consider running in isolated environment"]
            )
        
        # Execute command or script
        if command:
            result = self._execute_command(command)
        else:
            result = self._execute_script(script)
        
        return result
    
    def _validate_safety(self, content: str) -> Dict[str, Any]:
        """
        Validate command safety.
        
        Args:
            content: Command or script content
        
        Returns:
            Dict with 'safe' boolean and 'reason' string
        """
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return {
                    "safe": False,
                    "reason": f"Dangerous command detected: matches pattern '{pattern}'"
                }
        
        # Check for destructive commands (basic check)
        destructive_commands = [
            "rm -rf /",
            "rm -rf ~",
            "rm -rf *",
            "mkfs.",
            "dd if=",
        ]
        
        for cmd in destructive_commands:
            if cmd in content.lower():
                return {
                    "safe": False,
                    "reason": f"Potentially destructive command: '{cmd}'"
                }
        
        return {"safe": True, "reason": ""}
    
    def _execute_command(self, command: str) -> AgentResult:
        """
        Execute a single shell command.
        
        Args:
            command: Shell command to execute
        
        Returns:
            AgentResult with execution output
        """
        try:
            logger.info(f"Executing command: {command}")
            
            # Determine shell
            if sys.platform == "win32":
                # Use PowerShell on Windows
                full_command = ["powershell", "-Command", command]
            else:
                # Use bash on Unix-like systems
                full_command = ["bash", "-c", command]
            
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nStderr: {result.stderr}"
            
            success = result.returncode == 0
            confidence = 0.9 if success else 0.5
            
            suggestions = []
            if not success:
                suggestions.append(f"Command exited with code {result.returncode}")
                if result.stderr:
                    suggestions.append("Check stderr output for details")
            
            return AgentResult(
                success=success,
                confidence=confidence,
                output=output.strip() if output else "",
                error=result.stderr if not success else "",
                suggestions=suggestions
            )
        
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return AgentResult(
                success=False,
                confidence=0.0,
                output="",
                error="Command execution timed out (30s limit)",
                suggestions=["Reduce command complexity",
                           "Use background execution for long-running commands"]
            )
        
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return AgentResult(
                success=False,
                confidence=0.0,
                output="",
                error=f"Execution failed: {str(e)}",
                suggestions=["Verify command syntax",
                           "Check if required tools are installed"]
            )
    
    def _execute_script(self, script: str) -> AgentResult:
        """
        Execute a bash script.
        
        Args:
            script: Script content
        
        Returns:
            AgentResult with execution output
        """
        try:
            logger.info("Executing bash script")
            
            # Write script to temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.sh' if sys.platform != "win32" else '.ps1',
                delete=False
            ) as f:
                f.write(script)
                script_path = f.name
            
            try:
                # Make script executable on Unix
                if sys.platform != "win32":
                    Path(script_path).chmod(0o755)
                
                # Execute script
                if sys.platform == "win32":
                    full_command = ["powershell", "-File", script_path]
                else:
                    full_command = ["bash", script_path]
                
                result = subprocess.run(
                    full_command,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                output = result.stdout
                if result.stderr:
                    output += f"\nStderr: {result.stderr}"
                
                success = result.returncode == 0
                confidence = 0.9 if success else 0.5
                
                suggestions = []
                if not success:
                    suggestions.append(f"Script exited with code {result.returncode}")
                
                return AgentResult(
                    success=success,
                    confidence=confidence,
                    output=output.strip() if output else "",
                    error=result.stderr if not success else "",
                    suggestions=suggestions
                )
            
            finally:
                # Cleanup temp script
                try:
                    Path(script_path).unlink()
                except:
                    pass
        
        except subprocess.TimeoutExpired:
            logger.error("Script execution timed out")
            return AgentResult(
                success=False,
                confidence=0.0,
                output="",
                error="Script execution timed out (60s limit)",
                suggestions=["Optimize script execution time",
                           "Use background processes for long-running tasks"]
            )
        
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return AgentResult(
                success=False,
                confidence=0.0,
                output="",
                error=f"Script execution failed: {str(e)}"
            )
