"""
Feedback Loop System for Agent Learning and Quality Improvement

This module implements the feedback loop mechanism that allows agents to:
- Retry failed operations with improved parameters
- Learn from low confidence scores
- Apply best practice suggestions
- Improve over time through feedback

Built using Test-Driven Development.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import copy


class FeedbackType(Enum):
    """Types of feedback that can be generated"""
    VALIDATION_ERROR = "validation_error"
    LOW_CONFIDENCE = "low_confidence"
    BEST_PRACTICE = "best_practice"
    SECURITY = "security"
    PERFORMANCE = "performance"
    SUCCESS = "success"


class FeedbackSeverity(Enum):
    """Severity levels for feedback"""
    CRITICAL = "critical"  # Must fix
    HIGH = "high"          # Should fix
    MEDIUM = "medium"      # Consider fixing
    LOW = "low"            # Nice to have
    INFO = "info"          # Informational


@dataclass
class Feedback:
    """
    Represents feedback from an agent execution
    
    Attributes:
        type: The type of feedback
        severity: How critical the feedback is
        message: Human-readable description
        suggestions: List of actionable improvements
        context: Additional context data
    """
    type: FeedbackType
    severity: FeedbackSeverity
    message: str
    suggestions: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


class FeedbackLoop:
    """
    Orchestrates agent execution with feedback-driven improvement
    
    The FeedbackLoop:
    1. Executes an agent task
    2. Evaluates the result (confidence, validation, security)
    3. Generates feedback if issues found
    4. Retries with improved parameters if needed
    5. Learns from patterns over time
    
    Attributes:
        max_retries: Maximum retry attempts
        confidence_threshold: Minimum acceptable confidence score
        attempt_count: Current attempt number
        feedback_history: All feedback generated during execution
    """
    
    def __init__(self, max_retries: int = 3, confidence_threshold: float = 0.75):
        self.max_retries = max_retries
        self.confidence_threshold = confidence_threshold
        self.attempt_count = 0
        self.feedback_history: List[Feedback] = []
        self.last_result = None
    
    def execute_with_feedback(self, agent: Any, task: Any, auto_improve: bool = False) -> Any:
        """
        Execute a task through an agent with feedback-driven retry logic
        
        Args:
            agent: The agent to execute the task
            task: The task to execute
            auto_improve: Whether to automatically apply feedback suggestions
        
        Returns:
            AgentResult from the final execution attempt
        """
        self.attempt_count = 0
        self.feedback_history = []
        current_task = copy.deepcopy(task)
        
        while self.attempt_count < self.max_retries:
            self.attempt_count += 1
            
            # Execute the task
            result = agent.execute(current_task)
            self.last_result = result
            
            # Generate feedback based on result
            feedbacks = self._generate_feedback(result, current_task)
            self.feedback_history.extend(feedbacks)
            
            # Check if result is acceptable
            if self._is_acceptable(result, feedbacks):
                return result
            
            # If not last attempt, try to improve
            if self.attempt_count < self.max_retries and auto_improve:
                current_task = self._improve_task(current_task, feedbacks)
        
        # Return last result even if not perfect
        return self.last_result
    
    def _generate_feedback(self, result: Any, task: Any) -> List[Feedback]:
        """
        Generate feedback based on execution result
        
        Args:
            result: The agent execution result
            task: The task that was executed
        
        Returns:
            List of Feedback objects
        """
        feedbacks = []
        
        # Check confidence score
        if hasattr(result, 'confidence') and result.confidence < self.confidence_threshold:
            feedbacks.append(Feedback(
                type=FeedbackType.LOW_CONFIDENCE,
                severity=FeedbackSeverity.MEDIUM,
                message=f"Confidence score {result.confidence:.2f} below threshold {self.confidence_threshold}",
                suggestions=result.suggestions if hasattr(result, 'suggestions') else [],
                context={"confidence": result.confidence, "threshold": self.confidence_threshold}
            ))
        
        # Check validation status
        if hasattr(result, 'self_validated') and not result.self_validated:
            feedbacks.append(Feedback(
                type=FeedbackType.VALIDATION_ERROR,
                severity=FeedbackSeverity.HIGH,
                message="Agent self-validation failed",
                suggestions=result.suggestions if hasattr(result, 'suggestions') else [],
                context={"validated": False}
            ))
        
        # Check for error
        if hasattr(result, 'error') and result.error:
            feedbacks.append(Feedback(
                type=FeedbackType.VALIDATION_ERROR,
                severity=FeedbackSeverity.HIGH,
                message=f"Execution error: {result.error}",
                suggestions=result.suggestions if hasattr(result, 'suggestions') else [],
                context={"error": result.error}
            ))
        
        # Add best practice feedback from suggestions
        if hasattr(result, 'suggestions') and result.suggestions and result.success:
            feedbacks.append(Feedback(
                type=FeedbackType.BEST_PRACTICE,
                severity=FeedbackSeverity.LOW,
                message="Best practice suggestions available",
                suggestions=result.suggestions,
                context={"suggestion_count": len(result.suggestions)}
            ))
        
        return feedbacks
    
    def _is_acceptable(self, result: Any, feedbacks: List[Feedback]) -> bool:
        """
        Determine if the result is acceptable or needs retry
        
        Args:
            result: The agent execution result
            feedbacks: List of generated feedback
        
        Returns:
            True if result is acceptable, False if retry needed
        """
        # Must be successful
        if not result.success:
            return False
        
        # Check for critical issues
        for feedback in feedbacks:
            if feedback.severity == FeedbackSeverity.CRITICAL:
                return False
        
        # Check confidence threshold
        if hasattr(result, 'confidence'):
            if result.confidence < self.confidence_threshold:
                return False
        
        # Check validation
        if hasattr(result, 'self_validated'):
            if not result.self_validated:
                return False
        
        return True
    
    def _improve_task(self, task: Any, feedbacks: List[Feedback]) -> Any:
        """
        Attempt to improve task parameters based on feedback
        
        Args:
            task: The original task
            feedbacks: List of feedback to apply
        
        Returns:
            Improved task (or original if can't improve)
        """
        improved_task = copy.deepcopy(task)
        
        # Apply suggestions from feedback
        for feedback in feedbacks:
            if feedback.type == FeedbackType.LOW_CONFIDENCE:
                # Try to improve confidence by adding recommended params
                for suggestion in feedback.suggestions:
                    if "version tag" in suggestion.lower():
                        # Add version tag if missing
                        if "image" in improved_task.params:
                            image = improved_task.params["image"]
                            if ":" not in image:
                                improved_task.params["image"] = f"{image}:latest"
                    
                    if "health check" in suggestion.lower():
                        # Add health check
                        improved_task.params["health_check"] = True
                    
                    if "resource limit" in suggestion.lower():
                        # Add resource limits
                        improved_task.params["memory"] = "512m"
                        improved_task.params["cpu"] = "1"
        
        return improved_task
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the feedback loop execution
        
        Returns:
            Dictionary with summary information
        """
        return {
            "attempts": self.attempt_count,
            "max_retries": self.max_retries,
            "final_confidence": self.last_result.confidence if self.last_result and hasattr(self.last_result, 'confidence') else None,
            "final_success": self.last_result.success if self.last_result else False,
            "feedbacks": [
                {
                    "type": fb.type.value,
                    "severity": fb.severity.value,
                    "message": fb.message,
                    "suggestions": fb.suggestions
                }
                for fb in self.feedback_history
            ]
        }
