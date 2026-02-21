# REIGN AI - Testing Strategy
## Using Tests to Build the Swarm Right

---

## 🎯 Philosophy: Test-Driven Development (TDD) for AI Agents

**Build → Test → Validate → Iterate**

The swarm system is complex, so we use **layered testing** to ensure each component works perfectly before integrating:

```
Unit Tests → Agent Tests → Integration Tests → Swarm Tests → End-to-End Tests
```

---

## 📊 Testing Pyramid

```
                    ▲
                   ╱ ╲
                  ╱E2E╲              ← Few, Slow, Comprehensive
                 ╱─────╲
                ╱Swarm  ╲            ← Medium, Validates coordination
               ╱ Tests   ╲
              ╱───────────╲
             ╱Integration  ╲         ← More, Test agent interactions
            ╱    Tests      ╲
           ╱─────────────────╲
          ╱   Agent Tests     ╲     ← Many, Fast, Test agent logic
         ╱─────────────────────╲
        ╱     Unit Tests        ╲   ← Most, Fastest, Test functions
       ╱───────────────────────────╲
```

---

## 1️⃣ Unit Tests - Foundation Layer

### **Test Individual Functions**

```python
# tests/test_reign_general.py
import pytest
from reign.swarm import ReignGeneral

class TestReignGeneral:
    """Unit tests for Reign General orchestrator"""
    
    @pytest.fixture
    def reign(self):
        """Setup Reign instance for testing"""
        return ReignGeneral(llm_provider="mock")
    
    def test_understand_request_docker_deployment(self, reign):
        """Test: Can Reign understand Docker deployment requests?"""
        request = "Deploy a PostgreSQL database"
        
        intent = reign.understand_request(request)
        
        assert intent.action == "deploy"
        assert intent.target == "docker"
        assert "postgresql" in intent.resources.lower()
        assert intent.confidence > 0.8
    
    def test_decompose_complex_task(self, reign):
        """Test: Can Reign break down complex tasks?"""
        request = "Deploy full-stack app with DB and cache"
        
        subtasks = reign.decompose_task(request)
        
        assert len(subtasks) >= 3  # Should have multiple steps
        assert any("database" in task.description.lower() for task in subtasks)
        assert any("cache" in task.description.lower() for task in subtasks)
    
    def test_dependency_resolution(self, reign):
        """Test: Does Reign correctly order tasks by dependencies?"""
        tasks = [
            {"id": 1, "name": "Deploy API", "depends_on": [2]},
            {"id": 2, "name": "Deploy DB", "depends_on": []},
            {"id": 3, "name": "Deploy Frontend", "depends_on": [1]}
        ]
        
        ordered = reign.resolve_dependencies(tasks)
        
        # DB should come first, API second, Frontend last
        assert ordered[0]["id"] == 2
        assert ordered[1]["id"] == 1
        assert ordered[2]["id"] == 3
    
    def test_safety_validation_blocks_dangerous_commands(self, reign):
        """Test: Does safety validator block dangerous operations?"""
        dangerous_task = {
            "action": "delete",
            "target": "all_containers",
            "force": True
        }
        
        is_safe = reign.safety_validator.check(dangerous_task)
        
        assert is_safe == False
    
    def test_confidence_score_calculation(self, reign):
        """Test: Confidence scores calculated correctly?"""
        result = {
            "self_validation": True,
            "peer_validation": True,
            "quality_score": 0.95
        }
        
        confidence = reign.calculate_confidence(result)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.8  # High quality should give high confidence
```

---

## 2️⃣ Agent Tests - Specialized Agent Validation

### **Test Each Agent's Capabilities**

```python
# tests/agents/test_docker_agent.py
import pytest
from reign.swarm.agents import DockerAgent
from reign.swarm.models import Task, AgentResult

class TestDockerAgent:
    """Test Docker Agent specialized capabilities"""
    
    @pytest.fixture
    def docker_agent(self):
        """Setup Docker Agent with mock Docker client"""
        return DockerAgent(docker_client=MockDockerClient())
    
    def test_agent_can_create_container(self, docker_agent):
        """Test: Can agent create Docker container?"""
        task = Task(
            action="create_container",
            params={
                "image": "postgres:latest",
                "name": "test-db",
                "env": {"POSTGRES_PASSWORD": "test123"}
            }
        )
        
        result = docker_agent.execute(task)
        
        assert result.success == True
        assert result.confidence > 0.7
        assert "container_id" in result.output
    
    def test_agent_self_validation_detects_missing_health_check(self, docker_agent):
        """Test: Agent catches missing health checks?"""
        task = Task(
            action="create_container",
            params={
                "image": "postgres:latest",
                "name": "test-db"
                # Missing health check!
            }
        )
        
        result = docker_agent.execute(task)
        
        assert result.needs_retry == True
        assert "health" in result.feedback.message.lower()
    
    def test_agent_learns_from_feedback(self, docker_agent):
        """Test: Agent improves after feedback?"""
        task = Task(action="deploy_container", params={"image": "nginx"})
        
        # First attempt - should fail
        result1 = docker_agent.execute(task)
        
        # Give feedback
        feedback = Feedback(
            type=Feedback.Type.SECURITY_ISSUE,
            message="Run as non-root user",
            suggestion="Add 'user: 1000' to config"
        )
        docker_agent.receive_feedback(feedback)
        
        # Second attempt - should succeed
        result2 = docker_agent.execute(task)
        
        assert result2.confidence > result1.confidence
        assert "user" in result2.output
    
    def test_agent_confidence_threshold(self, docker_agent):
        """Test: Agent only returns confident results?"""
        task = Task(action="complex_deployment", params={})
        
        result = docker_agent.execute(task)
        
        if result.needs_retry:
            assert result.confidence < docker_agent.confidence_threshold
        else:
            assert result.confidence >= docker_agent.confidence_threshold
```

```python
# tests/agents/test_kubernetes_agent.py
import pytest
from reign.swarm.agents import KubernetesAgent

class TestKubernetesAgent:
    """Test Kubernetes Agent"""
    
    def test_agent_creates_deployment(self, k8s_agent):
        """Test: K8s agent can create deployment?"""
        task = Task(
            action="create_deployment",
            params={
                "name": "web-app",
                "image": "nginx:latest",
                "replicas": 3
            }
        )
        
        result = k8s_agent.execute(task)
        
        assert result.success == True
        assert result.output["kind"] == "Deployment"
        assert result.output["spec"]["replicas"] == 3
    
    def test_agent_validates_yaml_syntax(self, k8s_agent):
        """Test: Agent catches invalid YAML?"""
        task = Task(
            action="apply_manifest",
            params={
                "manifest": "invalid: yaml: syntax::"
            }
        )
        
        result = k8s_agent.execute(task)
        
        assert result.success == False
        assert "syntax" in result.error.lower()
```

---

## 3️⃣ Integration Tests - Agent Coordination

### **Test Multiple Agents Working Together**

```python
# tests/integration/test_swarm_coordination.py
import pytest
from reign.swarm import ReignGeneral

class TestSwarmCoordination:
    """Test multiple agents coordinating"""
    
    @pytest.fixture
    def reign_with_agents(self):
        """Setup Reign with multiple agents"""
        reign = ReignGeneral()
        reign.register_agent(DockerAgent())
        reign.register_agent(GitHubAgent())
        reign.register_agent(ValidationAgent())
        return reign
    
    def test_docker_and_github_coordination(self, reign_with_agents):
        """Test: Docker and GitHub agents coordinate?"""
        request = "Create GitHub repo and deploy Docker container"
        
        result = reign_with_agents.process_request(request)
        
        # Both agents should execute
        assert result.agents_used == ["GitHubAgent", "DockerAgent"]
        assert result.success == True
        assert "repository" in result.outputs
        assert "container" in result.outputs
    
    def test_feedback_loop_between_agents(self, reign_with_agents):
        """Test: Agents give feedback to each other?"""
        # Docker agent creates container
        # Validation agent reviews it
        # Docker agent fixes issues based on feedback
        
        task = Task(action="deploy_secure_container", params={})
        
        result = reign_with_agents.execute_with_feedback(task)
        
        assert result.feedback_loops > 0
        assert result.final_confidence > result.initial_confidence
    
    def test_parallel_execution(self, reign_with_agents):
        """Test: Independent tasks run in parallel?"""
        request = "Deploy 3 independent services"
        
        import time
        start = time.time()
        result = reign_with_agents.process_request(request)
        duration = time.time() - start
        
        # Should be faster than sequential
        assert result.parallel_executed == True
        assert duration < 10  # Adjust based on expected time
```

---

## 4️⃣ Feedback Loop Tests - Iterative Improvement

### **Test the Retry & Refinement System**

```python
# tests/feedback/test_feedback_loops.py
import pytest
from reign.swarm.feedback import FeedbackLoop

class TestFeedbackLoops:
    """Test feedback and retry mechanisms"""
    
    def test_feedback_loop_retries_until_success(self):
        """Test: System retries with feedback until success?"""
        task = Task(action="deploy_with_issues", params={})
        agent = DockerAgent()
        validator = ValidationAgent()
        
        loop = FeedbackLoop(max_retries=3)
        
        result = loop.execute_with_feedback(agent, task, validator)
        
        assert result.success == True
        assert result.attempts <= 3
        assert len(result.feedback_history) > 0
    
    def test_feedback_loop_gives_up_after_max_retries(self):
        """Test: System stops after max retries?"""
        task = Task(action="impossible_task", params={})
        agent = FailingAgent()
        validator = ValidationAgent()
        
        loop = FeedbackLoop(max_retries=3)
        
        result = loop.execute_with_feedback(agent, task, validator)
        
        assert result.success == False
        assert result.attempts == 3
        assert result.failure_reason == "max_retries_exceeded"
    
    def test_feedback_quality_improves_over_iterations(self):
        """Test: Each iteration produces better results?"""
        task = Task(action="optimize_deployment", params={})
        agent = DockerAgent()
        validator = ValidationAgent()
        
        loop = FeedbackLoop(max_retries=5)
        
        result = loop.execute_with_feedback(agent, task, validator)
        
        # Confidence should increase with iterations
        confidences = result.confidence_per_attempt
        for i in range(1, len(confidences)):
            assert confidences[i] >= confidences[i-1]
```

---

## 5️⃣ End-to-End Tests - Full Scenarios

### **Test Complete User Workflows**

```python
# tests/e2e/test_full_stack_deployment.py
import pytest
from reign.swarm import ReignGeneral

class TestFullStackDeployment:
    """End-to-end test: Deploy complete application"""
    
    @pytest.mark.slow
    @pytest.mark.e2e
    def test_deploy_complete_application(self):
        """Test: Deploy React + Node + PostgreSQL + Redis"""
        reign = ReignGeneral()
        
        request = """
        Deploy a full-stack application with:
        - React frontend on port 3000
        - Node.js API on port 5000
        - PostgreSQL database on port 5432
        - Redis cache on port 6379
        All services should be networked together.
        """
        
        result = reign.process_request(request)
        
        # Verify all components deployed
        assert result.success == True
        assert len(result.containers) == 4
        assert "frontend" in result.containers
        assert "api" in result.containers
        assert "database" in result.containers
        assert "cache" in result.containers
        
        # Verify networking
        assert result.network_created == True
        assert all(c.network == result.network_name for c in result.containers)
        
        # Verify health checks
        assert all(c.healthy for c in result.containers)
    
    @pytest.mark.slow
    @pytest.mark.e2e
    def test_deploy_with_github_actions_cicd(self):
        """Test: Full GitOps workflow"""
        reign = ReignGeneral()
        
        request = """
        Create a GitHub repository, set up CI/CD pipeline
        that builds and deploys Docker containers on push.
        """
        
        result = reign.process_request(request)
        
        assert result.repository_created == True
        assert result.workflow_created == True
        assert result.workflow_tested == True
```

---

## 🔄 Test-Driven Development Workflow

### **How to Build the Swarm Using Tests**

```python
# Step 1: Write the test FIRST (it will fail)
def test_docker_agent_creates_container():
    agent = DockerAgent()
    task = Task(action="create", params={"image": "nginx"})
    
    result = agent.execute(task)
    
    assert result.success == True  # FAILS - agent doesn't exist yet!

# Step 2: Build minimum code to pass the test
class DockerAgent:
    def execute(self, task):
        # Simplest implementation
        return AgentResult(success=True)

# Step 3: Test passes! Add more tests for edge cases
def test_docker_agent_validates_image():
    agent = DockerAgent()
    task = Task(action="create", params={"image": "invalid!!!"})
    
    result = agent.execute(task)
    
    assert result.success == False  # FAILS again!

# Step 4: Improve implementation
class DockerAgent:
    def execute(self, task):
        if not self.validate_image(task.params["image"]):
            return AgentResult(success=False, error="Invalid image")
        return AgentResult(success=True)
    
    def validate_image(self, image):
        # Add validation logic
        return ":" in image and not any(c in image for c in "!@#$")

# Repeat: Test → Code → Test → Code → Test...
```

---

## 🧪 Mock Objects for Testing

### **Don't Need Real Docker/K8s for Tests**

```python
# tests/mocks/mock_docker_client.py
class MockDockerClient:
    """Fake Docker client for testing"""
    
    def __init__(self):
        self.containers = {}
        self.images = {}
    
    def create_container(self, image, name, **kwargs):
        """Fake container creation"""
        container_id = f"mock-{len(self.containers)}"
        self.containers[container_id] = {
            "image": image,
            "name": name,
            "status": "running"
        }
        return MockContainer(container_id)
    
    def list_containers(self):
        return list(self.containers.values())

class MockContainer:
    def __init__(self, id):
        self.id = id
    
    def start(self):
        return True
    
    def stop(self):
        return True
```

---

## 📈 Test Coverage Goals

```python
# Run with: pytest --cov=reign --cov-report=html

Target Coverage:
├── reign.swarm.general          → 95%+  (Core orchestration)
├── reign.swarm.agents.*         → 90%+  (Agent logic)
├── reign.swarm.feedback         → 95%+  (Critical path)
├── reign.swarm.validation       → 100%  (Security critical!)
├── reign.swarm.safety           → 100%  (Safety critical!)
└── Overall                      → 85%+
```

---

## 🚀 Continuous Integration Setup

### **Automate Testing with GitHub Actions**

```yaml
# .github/workflows/test.yml
name: Test Swarm System

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run Unit Tests
        run: pytest tests/unit -v --cov
      
      - name: Run Agent Tests
        run: pytest tests/agents -v
      
      - name: Run Integration Tests
        run: pytest tests/integration -v
      
      - name: Run E2E Tests (if not PR)
        if: github.event_name == 'push'
        run: pytest tests/e2e -v --slow
      
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
```

---

## 🎯 Testing Best Practices

### **1. Test Isolation**
```python
# Each test is independent
@pytest.fixture(autouse=True)
def reset_agent_memory():
    """Clear agent memory between tests"""
    AgentMemory.clear_all()
    yield
    AgentMemory.clear_all()
```

### **2. Descriptive Test Names**
```python
# Good
def test_docker_agent_retries_failed_deployment_with_feedback():
    pass

# Bad
def test_deploy():
    pass
```

### **3. Test One Thing at a Time**
```python
# Good - Single assertion
def test_confidence_above_threshold():
    result = agent.execute(task)
    assert result.confidence > 0.8

# Bad - Multiple unrelated assertions
def test_everything():
    assert agent.name == "Docker"
    assert result.confidence > 0.8
    assert container.running == True
```

### **4. Use Parameterized Tests**
```python
@pytest.mark.parametrize("image,expected", [
    ("nginx:latest", True),
    ("postgres:14", True),
    ("invalid-image", False),
    ("", False),
])
def test_image_validation(image, expected):
    assert agent.validate_image(image) == expected
```

---

## 📊 Test Metrics Dashboard

```python
# tests/conftest.py
import pytest

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Custom test report"""
    stats = terminalreporter.stats
    
    print("\n" + "="*70)
    print("🧪 REIGN SWARM TEST SUMMARY")
    print("="*70)
    print(f"✅ Passed:  {len(stats.get('passed', []))}")
    print(f"❌ Failed:  {len(stats.get('failed', []))}")
    print(f"⏭️  Skipped: {len(stats.get('skipped', []))}")
    print(f"⏱️  Duration: {terminalreporter._sessionstarttime:.2f}s")
    print("="*70)
```

---

## 🎬 Ready to Start Testing!

### **Implementation Order:**

1. **Week 1:** Unit tests for ReignGeneral
2. **Week 2:** Agent tests (DockerAgent first)
3. **Week 3:** Feedback loop tests
4. **Week 4:** Integration tests
5. **Week 5:** E2E tests
6. **Week 6:** CI/CD setup

### **Run Tests:**
```bash
# All tests
pytest

# Only unit tests (fast)
pytest tests/unit -v

# With coverage
pytest --cov=reign --cov-report=html

# Specific agent
pytest tests/agents/test_docker_agent.py -v

# Watch mode (re-run on file changes)
pytest-watch
```

**Tests ensure the swarm works perfectly before deployment! 🚀**
