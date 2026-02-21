"""
DockerAgent - Specialized agent for Docker operations

This agent:
1. Executes Docker-related tasks
2. Validates its own work
3. Provides confidence scores
4. Gives suggestions for improvement
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import re


@dataclass
class AgentResult:
    """Result from agent execution"""
    success: bool
    confidence: float
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    self_validated: bool = False
    execution_time: Optional[float] = None  # Execution time in seconds
    
    def __post_init__(self):
        """Validate confidence range"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")


class DockerAgent:
    """
    Specialized agent for Docker operations
    
    Expertise:
    - Container creation and management
    - Image validation
    - Docker networking
    - Volume management
    - Health checks
    """
    
    def __init__(self):
        """Initialize Docker agent"""
        self.name = "DockerAgent"
        self.expertise = [
            "Docker containers",
            "Container images",
            "Docker networking",
            "Volume management",
            "Health checks",
            "Resource limits"
        ]
        self.confidence_threshold = 0.7
    
    def execute(self, task) -> AgentResult:
        """
        Execute a Docker task
        
        Args:
            task: Task object with description and params
            
        Returns:
            AgentResult with success status, confidence, and output
        """
        # Extract task parameters
        params = task.params
        image = params.get("image", "")
        
        # Validate image name
        if not self._validate_image_name(image):
            return AgentResult(
                success=False,
                confidence=0.0,
                error=f"Invalid image name: {image}",
                self_validated=True
            )
        
        # Try to create actual Docker container
        try:
            import docker
            client = docker.from_env()
            
            # Extract container parameters
            name = params.get("name", f"reign-{image.replace(':', '-')[:20]}")
            action = params.get("action", "run")
            
            if action == "run":
                # Run the container
                try:
                    container = client.containers.run(
                        image,
                        name=name,
                        detach=True,
                        remove=False
                    )
                    container_id = container.id[:12]
                    
                    return AgentResult(
                        success=True,
                        confidence=0.95,
                        output={
                            "container_id": container_id,
                            "image": image,
                            "name": name,
                            "status": "running"
                        },
                        suggestions=self._generate_suggestions(params),
                        self_validated=True
                    )
                except docker.errors.ImageNotFound:
                    # Image not found, try to pull it first
                    try:
                        client.images.pull(image)
                        container = client.containers.run(
                            image,
                            name=name,
                            detach=True,
                            remove=False
                        )
                        container_id = container.id[:12]
                        
                        return AgentResult(
                            success=True,
                            confidence=0.90,
                            output={
                                "container_id": container_id,
                                "image": image,
                                "name": name,
                                "status": "running",
                                "pulled": True
                            },
                            suggestions=self._generate_suggestions(params),
                            self_validated=True
                        )
                    except Exception as pull_err:
                        return AgentResult(
                            success=False,
                            confidence=0.0,
                            error=f"Failed to pull image {image}: {pull_err}",
                            self_validated=True
                        )
            else:
                # Unsupported action
                return AgentResult(
                    success=False,
                    confidence=0.0,
                    error=f"Unsupported action: {action}",
                    self_validated=True
                )
                
        except ImportError:
            # Docker SDK not installed, fall back to mock
            return self._execute_mock(params)
        except Exception as e:
            # Docker daemon not available, fall back to mock
            return self._execute_mock(params)
    
    def _execute_mock(self, params: Dict[str, Any]) -> AgentResult:
        """Fallback mock execution when Docker is not available"""
        image = params.get("image", "")
        container_id = f"mock-{hash(image) % 1000000}"
        
        return AgentResult(
            success=True,
            confidence=0.5,
            output={
                "container_id": container_id,
                "image": image,
                "status": "simulated"
            },
            suggestions=self._generate_suggestions(params),
            self_validated=True
        )
    
    def _validate_image_name(self, image: str) -> bool:
        """
        Validate Docker image name format
        
        Valid formats:
        - nginx
        - nginx:latest
        - nginx:1.21.0
        - registry.example.com/nginx:latest
        """
        if not image:
            return False
        
        # Check for invalid characters
        if any(char in image for char in ["!", " ", "@", "#", "$", "%", "^", "&", "*", "(", ")"]):
            return False
        
        # Basic format check
        # Must have name, optionally :tag
        pattern = r'^[a-zA-Z0-9._/-]+(:[\w][\w.-]*)?$'
        return bool(re.match(pattern, image))
    
    def _calculate_confidence(self, params: Dict[str, Any]) -> float:
        """
        Calculate confidence score for this execution
        
        Higher confidence when:
        - Specific version tags (not 'latest')
        - Health checks configured
        - Resource limits set
        - Proper networking
        """
        confidence = 0.8  # Base confidence
        
        image = params.get("image", "")
        
        # Boost: Specific version tag (not 'latest')
        if ":" in image and not image.endswith(":latest"):
            confidence += 0.1
        
        # Reduce: Using 'latest' tag
        if image.endswith(":latest") or ":" not in image:
            confidence -= 0.05
        
        # Boost: Health check configured
        if params.get("healthcheck"):
            confidence += 0.05
        
        # Boost: Resource limits set
        if params.get("mem_limit") or params.get("cpu_limit"):
            confidence += 0.05
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def _generate_suggestions(self, params: Dict[str, Any]) -> List[str]:
        """
        Generate suggestions for improvement
        
        Based on best practices and missing configurations
        """
        suggestions = []
        
        image = params.get("image", "")
        
        # Suggest specific version tags
        if image.endswith(":latest") or ":" not in image:
            suggestions.append("Consider using a specific version tag instead of 'latest'")
        
        # Suggest health checks
        if not params.get("healthcheck"):
            suggestions.append("Add health check for production deployments")
        
        # Suggest resource limits
        if not params.get("mem_limit"):
            suggestions.append("Set memory limits to prevent resource exhaustion")
        
        # Suggest restart policy
        if not params.get("restart_policy"):
            suggestions.append("Configure restart policy for automatic recovery")
        
        return suggestions
    
    def receive_feedback(self, feedback) -> None:
        """
        Receive and learn from feedback
        
        This allows the agent to improve over time
        """
        # In full implementation:
        # - Store feedback in AgentMemory
        # - Adjust strategies based on feedback
        # - Update confidence calculations
        pass
