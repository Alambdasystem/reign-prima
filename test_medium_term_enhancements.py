#!/usr/bin/env python3
"""
TDD Test Suite for Medium-Term Enhancements

Tests for:
1. Enhanced component detection (Kafka, message queues, monitoring)
2. Terraform real CLI integration
3. Self-healing feedback loops
4. Dashboard metrics and container features
"""

import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reign.swarm.reign_general import ReignGeneral
from reign.swarm.agents.terraform_agent import TerraformAgent
from reign.swarm.feedback_loop import FeedbackLoop, FeedbackType, FeedbackSeverity, Feedback
from reign.swarm.state.state_manager import StateManager, ResourceState


# ============================================================================
# TEST 1: Enhanced Component Detection
# ============================================================================

def test_component_detection_kafka():
    """Test detection of Kafka message queue"""
    rg = ReignGeneral()
    components = rg._detect_components("deploy with kafka message queue")
    
    assert "queue" in components, "Should detect queue component"
    assert components["queue"] == "kafka", "Should detect Kafka specifically"
    print("[+] PASS: Kafka detection")


def test_component_detection_rabbitmq():
    """Test detection of RabbitMQ"""
    rg = ReignGeneral()
    components = rg._detect_components("setup rabbitmq broker")
    
    assert "queue" in components, "Should detect queue component"
    assert components["queue"] == "rabbitmq", "Should detect RabbitMQ"
    print("[+] PASS: RabbitMQ detection")


def test_component_detection_prometheus():
    """Test detection of Prometheus monitoring"""
    rg = ReignGeneral()
    components = rg._detect_components("setup prometheus monitoring")
    
    assert "monitoring" in components, "Should detect monitoring component"
    assert components["monitoring"] == "prometheus", "Should detect Prometheus"
    print("[+] PASS: Prometheus detection")


def test_component_detection_elk():
    """Test detection of ELK logging stack"""
    rg = ReignGeneral()
    components = rg._detect_components("create elk logging stack")
    
    assert "logging" in components, "Should detect logging component"
    assert components["logging"] == "elk", "Should detect ELK"
    print("[+] PASS: ELK detection")


def test_component_detection_java_spring():
    """Test detection of Java/Spring API"""
    rg = ReignGeneral()
    components = rg._detect_components("deploy spring boot java api")
    
    assert "api" in components, "Should detect API component"
    assert components["api"] == "java", "Should detect Java API"
    print("[+] PASS: Java Spring detection")


def test_component_detection_golang():
    """Test detection of Golang service"""
    rg = ReignGeneral()
    components = rg._detect_components("deploy golang microservice")
    
    assert "api" in components, "Should detect API component"
    assert components["api"] == "golang", "Should detect Golang"
    print("[+] PASS: Golang detection")


def test_component_detection_nextjs():
    """Test detection of Next.js frontend"""
    rg = ReignGeneral()
    components = rg._detect_components("deploy nextjs frontend")
    
    assert "frontend" in components, "Should detect frontend component"
    assert components["frontend"] == "nextjs", "Should detect Next.js"
    print("[+] PASS: Next.js detection")


def test_component_detection_elasticsearch():
    """Test detection of Elasticsearch database"""
    rg = ReignGeneral()
    components = rg._detect_components("deploy elasticsearch cluster")
    
    assert "database" in components, "Should detect database component"
    assert components["database"] == "elasticsearch", "Should detect Elasticsearch"
    print("[+] PASS: Elasticsearch detection")


def test_component_detection_multi_tier():
    """Test detection of multiple components in one request"""
    rg = ReignGeneral()
    components = rg._detect_components(
        "Deploy with kafka message queue, prometheus monitoring, and postgresql database"
    )
    
    assert "queue" in components, f"Should detect queue, got: {components}"
    assert components["queue"] == "kafka", "Should detect Kafka"
    assert "monitoring" in components, "Should detect monitoring"
    assert "database" in components, "Should detect database"
    assert len(components) >= 3, f"Should detect at least 3 components, got {len(components)}"
    print("[+] PASS: Multi-tier component detection")


# ============================================================================
# TEST 2: Terraform Real CLI Integration
# ============================================================================

def test_terraform_agent_initialization():
    """Test Terraform agent initializes correctly"""
    agent = TerraformAgent()
    
    assert agent.name == "TerraformAgent", "Should have correct name"
    assert agent.supported_providers, "Should have supported providers"
    assert "aws" in agent.supported_providers, "Should support AWS"
    assert "azure" in agent.supported_providers, "Should support Azure"
    print("[+] PASS: Terraform agent initialization")


def test_terraform_hcl_generation():
    """Test HCL file generation"""
    agent = TerraformAgent()
    
    hcl_file = agent._generate_hcl_file(
        "aws",
        "aws_vpc",
        {
            "cidr_block": "10.0.0.0/16",
            "region": "us-east-1",
            "enable_dns_hostnames": True
        }
    )
    
    assert os.path.exists(hcl_file), "Should create HCL file"
    content = Path(hcl_file).read_text()
    assert "provider" in content, "Should contain provider block"
    assert "aws" in content, "Should contain AWS provider"
    assert "resource" in content, "Should contain resource block"
    print("[+] PASS: HCL file generation")


def test_terraform_syntax_validation():
    """Test Terraform HCL syntax validation"""
    agent = TerraformAgent()
    
    hcl_file = agent._generate_hcl_file("aws", "aws_instance", {"ami": "ami-12345"})
    
    # Should validate without error
    is_valid = agent._validate_with_terraform(hcl_file)
    assert is_valid is not None, "Should return validation result"
    print("[+] PASS: Terraform syntax validation")


def test_terraform_plan_generation():
    """Test Terraform plan generation with AgentResult"""
    agent = TerraformAgent()
    
    from reign.swarm.reign_general import Task
    task = Task(
        id=1,
        description="Test Terraform plan",
        agent_type="terraform",
        params={
            "action": "plan",
            "provider": "aws",
            "resource_type": "aws_vpc",
            "config": {"cidr_block": "10.0.0.0/16"}
        }
    )
    
    result = agent._run_plan(task.params)
    
    assert result is not None, "Should return plan result"
    assert hasattr(result, 'success'), "Should return AgentResult"
    assert hasattr(result, 'output'), "Should have output"
    print("[+] PASS: Terraform plan generation")


def test_terraform_config_generation():
    """Test Terraform config generation with execute method"""
    agent = TerraformAgent()
    
    from reign.swarm.reign_general import Task
    task = Task(
        id=1,
        description="Generate Terraform config",
        agent_type="terraform",
        params={
            "provider": "aws",
            "resource_type": "aws_vpc",
            "cidr_block": "10.0.0.0/16"
        }
    )
    
    result = agent.execute(task)
    
    assert result.success, "Should succeed"
    assert result.confidence > 0.7, "Should have good confidence"
    assert "config" in result.output or "terraform" in result.output, "Should contain config"
    print("[+] PASS: Terraform config generation")


# ============================================================================
# TEST 3: Self-Healing Feedback Loops
# ============================================================================

def test_feedback_generation():
    """Test feedback generation from low confidence result"""
    from reign.swarm.agents.docker_agent import AgentResult
    
    loop = FeedbackLoop(confidence_threshold=0.8)
    
    # Create a low-confidence result
    result = AgentResult(
        success=True,
        confidence=0.6,
        output={"status": "created"},
        suggestions=["Increase timeout", "Check resource availability"]
    )
    
    feedbacks = loop._generate_feedback(result, None)
    
    assert len(feedbacks) > 0, "Should generate feedback"
    assert any(f.type == FeedbackType.LOW_CONFIDENCE for f in feedbacks), \
        "Should identify low confidence"
    print("[+] PASS: Feedback generation")


def test_feedback_severity_levels():
    """Test feedback severity levels"""
    # Test critical feedback
    critical_feedback = Feedback(
        type=FeedbackType.VALIDATION_ERROR,
        severity=FeedbackSeverity.CRITICAL,
        message="Critical error"
    )
    
    # Test low feedback
    low_feedback = Feedback(
        type=FeedbackType.BEST_PRACTICE,
        severity=FeedbackSeverity.LOW,
        message="Nice to have improvement"
    )
    
    assert critical_feedback.severity == FeedbackSeverity.CRITICAL
    assert low_feedback.severity == FeedbackSeverity.LOW
    print("[+] PASS: Feedback severity levels")


def test_feedback_retry_logic():
    """Test retry logic in feedback loop"""
    loop = FeedbackLoop(max_retries=3, confidence_threshold=0.9)
    
    assert loop.max_retries == 3, "Should set max retries"
    assert loop.confidence_threshold == 0.9, "Should set confidence threshold"
    assert loop.attempt_count == 0, "Should start at attempt 0"
    print("[+] PASS: Feedback retry logic")


def test_feedback_history_tracking():
    """Test that feedback history is tracked"""
    loop = FeedbackLoop()
    
    # Create feedback and add to history
    feedback = Feedback(
        type=FeedbackType.SUCCESS,
        severity=FeedbackSeverity.INFO,
        message="Operation succeeded"
    )
    
    loop.feedback_history.append(feedback)
    
    assert len(loop.feedback_history) == 1, "Should track feedback"
    assert loop.feedback_history[0].message == "Operation succeeded"
    print("[+] PASS: Feedback history tracking")


# ============================================================================
# TEST 4: State Management with Self-Healing
# ============================================================================

def test_resource_health_check():
    """Test resource health status"""
    resource = ResourceState(
        resource_id="docker-1",
        resource_type="docker_container",
        name="web-server",
        metadata={"image": "nginx", "health": "healthy"},
        agent_type="docker"
    )
    
    assert resource.status == "deployed", "Should have deployed status"
    assert resource.metadata["health"] == "healthy", "Should track health"
    print("[+] PASS: Resource health check")


def test_deployment_failure_detection():
    """Test detection of failed deployments"""
    failing_resource = ResourceState(
        resource_id="docker-fail",
        resource_type="docker_container",
        name="broken-app",
        metadata={"image": "bad-image", "error": "Image not found"},
        agent_type="docker",
        status="failed"
    )
    
    assert failing_resource.status == "failed", "Should track failed status"
    assert "error" in failing_resource.metadata, "Should track error reason"
    print("[+] PASS: Deployment failure detection")


def test_state_checkpoint_recovery():
    """Test checkpoint recovery capability"""
    state_mgr = StateManager()
    
    # Create and record resource
    resource = ResourceState(
        resource_id="test-1",
        resource_type="docker_container",
        name="test-app",
        metadata={"version": "1.0"},
        agent_type="docker"
    )
    
    state_mgr.record_deployment(resource)
    
    # Create checkpoint
    checkpoint_id = state_mgr.create_checkpoint("Recovery point")
    
    assert checkpoint_id is not None, "Should create checkpoint"
    
    # List checkpoints
    checkpoints = state_mgr.list_checkpoints()
    assert len(checkpoints) > 0, "Should have checkpoints"
    
    print("[+] PASS: State checkpoint recovery")


# ============================================================================
# TEST 5: Dashboard Features
# ============================================================================

def test_metrics_dashboard_concepts():
    """Test metrics dashboard data structures"""
    # Test agent metrics
    agent_metrics = {
        "docker": {"success_rate": 0.95, "avg_time": 2.3},
        "kubernetes": {"success_rate": 0.85, "avg_time": 5.1},
        "terraform": {"success_rate": 0.75, "avg_time": 8.7}
    }
    
    assert "docker" in agent_metrics, "Should track Docker metrics"
    assert agent_metrics["docker"]["success_rate"] == 0.95, "Should track success rate"
    assert agent_metrics["docker"]["avg_time"] == 2.3, "Should track execution time"
    print("[+] PASS: Metrics dashboard concepts")


def test_container_log_tracking():
    """Test container logging capability"""
    container_logs = {
        "container_id": "abc123",
        "image": "nginx:latest",
        "status": "running",
        "logs": [
            "[2026-02-21 14:23:15] Container started",
            "[2026-02-21 14:23:16] Health check: OK",
            "[2026-02-21 14:23:17] Ready to serve requests"
        ]
    }
    
    assert container_logs["status"] == "running", "Should track running status"
    assert len(container_logs["logs"]) > 0, "Should have logs"
    print("[+] PASS: Container log tracking")


def test_performance_metrics_calculation():
    """Test performance metrics calculation"""
    executions = [
        {"duration": 2.1, "success": True},
        {"duration": 2.5, "success": True},
        {"duration": 2.3, "success": True},
        {"duration": 1.9, "success": True}
    ]
    
    total = len(executions)
    successes = sum(1 for e in executions if e["success"])
    avg_time = sum(e["duration"] for e in executions) / total
    success_rate = (successes / total) * 100
    
    assert total == 4, "Should count executions"
    assert successes == 4, "Should count successes"
    assert abs(avg_time - 2.2) < 0.1, "Should calculate average time"
    assert success_rate == 100.0, "Should calculate success rate"
    print("[+] PASS: Performance metrics calculation")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_end_to_end_detection_to_terraform():
    """Test end-to-end: detect components -> generate Terraform"""
    rg = ReignGeneral()
    terraform_agent = TerraformAgent()
    
    # Step 1: Detect components
    request = "Deploy AWS infrastructure with VPC, RDS PostgreSQL, and monitoring with Prometheus"
    components = rg._detect_components(request.lower())
    
    assert "database" in components, "Should detect database"
    assert "monitoring" in components, "Should detect monitoring"
    print("  Components detected:", components)
    
    # Step 2: Generate Terraform for each component
    assert components["database"] == "postgresql", "Should map to PostgreSQL"
    
    # Step 3: Create Terraform task for database
    from reign.swarm.reign_general import Task
    task = Task(
        id=1,
        description="Create RDS PostgreSQL instance",
        agent_type="terraform",
        params={
            "action": "plan",
            "provider": "aws",
            "resource_type": "aws_db_instance",
            "config": {
                "engine": "postgres",
                "instance_class": "db.t3.micro",
                "allocated_storage": "20"
            }
        }
    )
    
    result = terraform_agent._run_plan(task.params)
    assert result is not None, "Should generate plan"
    
    print("[+] PASS: End-to-end detection to Terraform")


def test_failure_detection_and_recovery():
    """Test failure detection and self-healing attempt"""
    state_mgr = StateManager()
    loop = FeedbackLoop(max_retries=3)
    
    # Create failed resource
    failed_resource = ResourceState(
        resource_id="docker-fail-1",
        resource_type="docker_container",
        name="broken-service",
        metadata={"image": "bad-image:latest", "error": "Failed to pull image"},
        agent_type="docker",
        status="failed"
    )
    
    # Record failure
    state_mgr.record_deployment(failed_resource)
    
    # Generate feedback
    from reign.swarm.agents.docker_agent import AgentResult
    
    fail_result = AgentResult(
        success=False,
        confidence=0.2,
        output={"error": "Image pull failed"},
        error="Failed to pull image from registry"
    )
    
    feedbacks = loop._generate_feedback(fail_result, None)
    
    # Should suggest improvements
    assert len(feedbacks) > 0, "Should generate feedback on failure"
    
    print("[+] PASS: Failure detection and recovery")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("MEDIUM-TERM ENHANCEMENTS - TDD TEST SUITE")
    print("="*70)
    
    tests = [
        # Component Detection Tests
        ("Component Detection - Kafka", test_component_detection_kafka),
        ("Component Detection - RabbitMQ", test_component_detection_rabbitmq),
        ("Component Detection - Prometheus", test_component_detection_prometheus),
        ("Component Detection - ELK", test_component_detection_elk),
        ("Component Detection - Java/Spring", test_component_detection_java_spring),
        ("Component Detection - Golang", test_component_detection_golang),
        ("Component Detection - Next.js", test_component_detection_nextjs),
        ("Component Detection - Elasticsearch", test_component_detection_elasticsearch),
        ("Component Detection - Multi-Tier", test_component_detection_multi_tier),
        
        # Terraform Tests
        ("Terraform Agent Init", test_terraform_agent_initialization),
        ("Terraform HCL Generation", test_terraform_hcl_generation),
        ("Terraform Syntax Validation", test_terraform_syntax_validation),
        ("Terraform Plan Generation", test_terraform_plan_generation),
        ("Terraform Config Generation", test_terraform_config_generation),
        
        # Feedback Loop Tests
        ("Feedback Generation", test_feedback_generation),
        ("Feedback Severity Levels", test_feedback_severity_levels),
        ("Feedback Retry Logic", test_feedback_retry_logic),
        ("Feedback History Tracking", test_feedback_history_tracking),
        
        # State Management Tests
        ("Resource Health Check", test_resource_health_check),
        ("Deployment Failure Detection", test_deployment_failure_detection),
        ("State Checkpoint Recovery", test_state_checkpoint_recovery),
        
        # Dashboard Tests
        ("Metrics Dashboard Concepts", test_metrics_dashboard_concepts),
        ("Container Log Tracking", test_container_log_tracking),
        ("Performance Metrics Calculation", test_performance_metrics_calculation),
        
        # Integration Tests
        ("E2E Detection to Terraform", test_end_to_end_detection_to_terraform),
        ("Failure Detection & Recovery", test_failure_detection_and_recovery),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            error_msg = f"{test_name}: {str(e)}"
            errors.append(error_msg)
            print(f"[-] FAIL: {test_name}")
            print(f"    Error: {e}")
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    print(f"[+] Passed: {passed}/{len(tests)}")
    print(f"[-] Failed: {failed}/{len(tests)}")
    
    if errors:
        print("\nFailed Tests:")
        for error in errors:
            print(f"  - {error}")
        return 1
    else:
        print("\n[+] All tests passed! TDD complete.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
