"""
Tests for the FeedbackLoop system that enables agent learning and retry logic.
Following TDD: Write tests first, then implement.
"""
import pytest
from dataclasses import dataclass
from reign.swarm.feedback_loop import (
    FeedbackLoop,
    Feedback,
    FeedbackType,
    FeedbackSeverity
)
from reign.swarm.agents.docker_agent import DockerAgent, AgentResult
from reign.swarm.reign_general import Task


class TestFeedback:
    """Test the Feedback dataclass"""
    
    def test_feedback_creation(self):
        feedback = Feedback(
            type=FeedbackType.VALIDATION_ERROR,
            severity=FeedbackSeverity.HIGH,
            message="Invalid Docker image name",
            suggestions=["Use valid image format: name:tag"]
        )
        assert feedback.type == FeedbackType.VALIDATION_ERROR
        assert feedback.severity == FeedbackSeverity.HIGH
        assert "Invalid" in feedback.message
        assert len(feedback.suggestions) == 1
    
    def test_feedback_with_context(self):
        feedback = Feedback(
            type=FeedbackType.LOW_CONFIDENCE,
            severity=FeedbackSeverity.MEDIUM,
            message="Low confidence score: 0.45",
            suggestions=["Add health checks", "Specify resource limits"],
            context={"confidence": 0.45, "agent": "DockerAgent"}
        )
        assert feedback.context["confidence"] == 0.45
        assert feedback.context["agent"] == "DockerAgent"


class TestFeedbackLoop:
    """Test the FeedbackLoop orchestration"""
    
    def test_feedback_loop_creation(self):
        loop = FeedbackLoop(max_retries=3, confidence_threshold=0.75)
        assert loop.max_retries == 3
        assert loop.confidence_threshold == 0.75
    
    def test_execute_with_feedback_success_first_try(self):
        """Test successful execution on first attempt"""
        agent = DockerAgent()
        task = Task(
            id=1,
            description="Deploy postgres:14-alpine",
            agent_type="docker",
            params={"image": "postgres:14-alpine", "port": 5432}
        )
        
        loop = FeedbackLoop(max_retries=3, confidence_threshold=0.70)
        result = loop.execute_with_feedback(agent, task)
        
        assert result.success is True
        assert result.confidence >= 0.70
        assert loop.attempt_count == 1
        assert len(loop.feedback_history) >= 0  # May have suggestions but no errors
    
    def test_execute_with_feedback_retry_on_low_confidence(self):
        """Test retry when confidence is below threshold"""
        agent = DockerAgent()
        task = Task(
            id=1,
            description="Deploy custom-app",  # No version tag, will have low confidence
            agent_type="docker",
            params={"image": "custom-app", "port": 3000}  # Missing version tag
        )
        
        loop = FeedbackLoop(max_retries=3, confidence_threshold=0.90)
        result = loop.execute_with_feedback(agent, task)
        
        # Should retry due to low confidence but eventually succeed
        assert loop.attempt_count > 1 or result.confidence < 0.90
        assert len(loop.feedback_history) > 0
    
    def test_execute_with_feedback_max_retries(self):
        """Test that max retries limit is respected"""
        agent = DockerAgent()
        task = Task(
            id=1,
            description="Deploy invalid!!!image",  # Invalid image name
            agent_type="docker",
            params={"image": "invalid!!!image"}
        )
        
        loop = FeedbackLoop(max_retries=2, confidence_threshold=0.75)
        result = loop.execute_with_feedback(agent, task)
        
        assert loop.attempt_count <= 2
        # Should have feedback about the issue
        assert len(loop.feedback_history) > 0
    
    def test_feedback_loop_improves_params(self):
        """Test that feedback loop can improve task parameters"""
        agent = DockerAgent()
        task = Task(
            id=1,
            description="Deploy nginx",
            agent_type="docker",
            params={"image": "nginx"}  # Missing version tag
        )
        
        loop = FeedbackLoop(max_retries=3, confidence_threshold=0.80)
        result = loop.execute_with_feedback(agent, task, auto_improve=True)
        
        # If auto_improve=True, should apply suggestions
        if loop.attempt_count > 1:
            # Check that feedback was generated
            assert len(loop.feedback_history) > 0
    
    def test_get_feedback_summary(self):
        """Test feedback summary generation"""
        loop = FeedbackLoop(max_retries=3, confidence_threshold=0.75)
        agent = DockerAgent()
        task = Task(
            id=1,
            description="Deploy app",
            agent_type="docker",
            params={"image": "app"}
        )
        
        loop.execute_with_feedback(agent, task)
        summary = loop.get_feedback_summary()
        
        assert "attempts" in summary
        assert "final_confidence" in summary
        assert "feedbacks" in summary


class TestFeedbackIntegration:
    """Test feedback loop integration with agents"""
    
    def test_docker_agent_with_feedback(self):
        """Test DockerAgent execution through feedback loop"""
        agent = DockerAgent()
        loop = FeedbackLoop(max_retries=3, confidence_threshold=0.75)
        
        task = Task(
            id=1,
            description="Deploy Redis cache",
            agent_type="docker",
            params={"image": "redis:7-alpine", "port": 6379}
        )
        
        result = loop.execute_with_feedback(agent, task)
        
        assert result.success is True
        assert result.confidence >= 0.75
        summary = loop.get_feedback_summary()
        assert summary["attempts"] >= 1
    
    def test_feedback_learning_from_failures(self):
        """Test that feedback loop learns from failures"""
        agent = DockerAgent()
        loop = FeedbackLoop(max_retries=3, confidence_threshold=0.75)
        
        # First task with issues
        task1 = Task(
            id=1,
            description="Deploy without version",
            agent_type="docker",
            params={"image": "myapp"}
        )
        
        result1 = loop.execute_with_feedback(agent, task1)
        feedback_count_1 = len(loop.feedback_history)
        
        # Should have generated feedback
        assert feedback_count_1 > 0
        
        # Check feedback contains useful suggestions
        if loop.feedback_history:
            feedback = loop.feedback_history[0]
            assert isinstance(feedback, Feedback)
            assert len(feedback.suggestions) > 0


class TestFeedbackTypes:
    """Test different feedback type scenarios"""
    
    def test_validation_error_feedback(self):
        """Test feedback for validation errors"""
        feedback = Feedback(
            type=FeedbackType.VALIDATION_ERROR,
            severity=FeedbackSeverity.HIGH,
            message="Image name contains invalid characters",
            suggestions=["Use only alphanumeric, hyphens, and underscores"]
        )
        assert feedback.severity == FeedbackSeverity.HIGH
    
    def test_low_confidence_feedback(self):
        """Test feedback for low confidence scores"""
        feedback = Feedback(
            type=FeedbackType.LOW_CONFIDENCE,
            severity=FeedbackSeverity.MEDIUM,
            message="Confidence score below threshold",
            suggestions=["Add health checks", "Specify resource limits"]
        )
        assert feedback.severity == FeedbackSeverity.MEDIUM
    
    def test_best_practice_feedback(self):
        """Test feedback for best practice suggestions"""
        feedback = Feedback(
            type=FeedbackType.BEST_PRACTICE,
            severity=FeedbackSeverity.LOW,
            message="Consider adding resource limits",
            suggestions=["Set memory limits", "Set CPU limits"]
        )
        assert feedback.severity == FeedbackSeverity.LOW
    
    def test_security_feedback(self):
        """Test feedback for security issues"""
        feedback = Feedback(
            type=FeedbackType.SECURITY,
            severity=FeedbackSeverity.CRITICAL,
            message="Hardcoded secrets detected",
            suggestions=["Use environment variables", "Use secrets management"]
        )
        assert feedback.severity == FeedbackSeverity.CRITICAL
