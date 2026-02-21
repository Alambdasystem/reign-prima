"""
Unit tests for ReignGeneral orchestrator

Following TDD:
1. Write test first (it fails)
2. Build minimum code to pass
3. Refactor and improve
4. Repeat
"""
import pytest
from reign.swarm.reign_general import ReignGeneral, Intent, Task


class TestReignGeneral:
    """Test the Reign General orchestrator"""
    
    def test_reign_general_can_be_created(self):
        """Test 1: Can we create a ReignGeneral instance?"""
        reign = ReignGeneral()
        
        assert reign is not None
        assert isinstance(reign, ReignGeneral)
    
    def test_understand_simple_docker_request(self, sample_request):
        """Test 2: Can Reign understand a simple Docker request?"""
        reign = ReignGeneral()
        
        intent = reign.understand_request(sample_request)
        
        # Should recognize this is about Docker
        assert intent is not None
        assert intent.action == "deploy"
        assert "docker" in intent.target.lower()
        assert "postgresql" in intent.description.lower()
    
    def test_confidence_score_is_valid(self, sample_request):
        """Test 3: Does confidence score make sense?"""
        reign = ReignGeneral()
        
        intent = reign.understand_request(sample_request)
        
        # Confidence should be between 0 and 1
        assert 0.0 <= intent.confidence <= 1.0
        # Simple request should have high confidence
        assert intent.confidence > 0.7
    
    def test_decompose_simple_task(self, sample_request):
        """Test 4: Can Reign break down a simple task?"""
        reign = ReignGeneral()
        
        tasks = reign.decompose_task(sample_request)
        
        # Should have at least one task
        assert len(tasks) > 0
        # First task should be creating container
        assert any("container" in task.description.lower() for task in tasks)
    
    def test_decompose_complex_task(self, complex_request):
        """Test 5: Can Reign break down complex multi-step task?"""
        reign = ReignGeneral()
        
        tasks = reign.decompose_task(complex_request)
        
        # Should have multiple tasks
        assert len(tasks) >= 3
        # Should include database, API, frontend
        descriptions = " ".join([t.description.lower() for t in tasks])
        assert "database" in descriptions or "postgresql" in descriptions
        assert "api" in descriptions or "node" in descriptions
        assert "frontend" in descriptions or "react" in descriptions
    
    def test_task_dependencies_ordered_correctly(self):
        """Test 6: Are tasks ordered by dependencies?"""
        reign = ReignGeneral()
        
        request = "Deploy API that connects to database"
        tasks = reign.decompose_task(request)
        
        # Database should come before API
        db_index = None
        api_index = None
        
        for i, task in enumerate(tasks):
            if "database" in task.description.lower():
                db_index = i
            if "api" in task.description.lower():
                api_index = i
        
        if db_index is not None and api_index is not None:
            assert db_index < api_index, "Database should be created before API"


class TestIntent:
    """Test the Intent model"""
    
    def test_intent_creation(self):
        """Test: Can we create an Intent?"""
        intent = Intent(
            action="deploy",
            target="docker",
            description="Deploy PostgreSQL",
            confidence=0.9
        )
        
        assert intent.action == "deploy"
        assert intent.target == "docker"
        assert intent.confidence == 0.9
    
    def test_intent_validation(self):
        """Test: Intent validates confidence range"""
        with pytest.raises(ValueError):
            Intent(
                action="deploy",
                target="docker",
                description="test",
                confidence=1.5  # Invalid: > 1.0
            )


class TestTask:
    """Test the Task model"""
    
    def test_task_creation(self):
        """Test: Can we create a Task?"""
        task = Task(
            id=1,
            description="Create PostgreSQL container",
            agent_type="docker",
            params={"image": "postgres:latest"}
        )
        
        assert task.id == 1
        assert task.agent_type == "docker"
        assert "postgres" in task.params["image"]
    
    def test_task_dependencies(self):
        """Test: Can tasks have dependencies?"""
        task1 = Task(id=1, description="Create DB", agent_type="docker")
        task2 = Task(
            id=2,
            description="Create API",
            agent_type="docker",
            depends_on=[1]
        )
        
        assert 1 in task2.depends_on
        assert len(task2.depends_on) == 1
