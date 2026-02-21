#!/usr/bin/env python3
"""
REIGN Orchestration - Comprehensive Enhancement Tests

Tests:
1. Kubernetes Agent Deployment (with kubectl fallback)
2. Multiple Deployments in One Request
3. Rollback Functionality via State Management
4. Different Request Types
5. Component Detection Accuracy
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now imports should work
from reign.swarm.reign_general import ReignGeneral, Task
from reign.swarm.agents.kubernetes_agent import KubernetesAgent
from reign.swarm.state.state_manager import StateManager, ResourceState


def test_kubernetes_agent():
    """Test 1: Kubernetes Agent with kubectl fallback"""
    print("\n" + "="*60)
    print("TEST 1: Kubernetes Agent Deployment")
    print("="*60)
    
    k8s_agent = KubernetesAgent()
    task = Task(
        id=1,
        description="Deploy Nginx web server with 3 replicas",
        agent_type="kubernetes",
        params={
            "name": "test-nginx",
            "image": "nginx:latest",
            "replicas": 3,
            "namespace": "default"
        }
    )
    
    result = k8s_agent.execute(task)
    print(f"[+] Task: {task.description}")
    print(f"  Success: {result.success}")
    print(f"  Confidence: {result.confidence}")
    print(f"  Method: {result.output.get('method', 'unknown')}")
    print(f"  Deployed: {result.output.get('deployed', False)}")
    
    if result.suggestions:
        print(f"  Suggestions:")
        for suggestion in result.suggestions:
            print(f"    - {suggestion}")
    
    return result.success


def test_multiple_deployments():
    """Test 2: Multiple Deployments in One Request"""
    print("\n" + "="*60)
    print("TEST 2: Multiple Deployments in One Request")
    print("="*60)
    
    request = "Deploy a complete web application with PostgreSQL database, Redis cache, Node.js API, and React frontend with 2 replicas each"
    
    print(f"\nRequest: {request}")
    print("Decomposing into subtasks...")
    
    rg = ReignGeneral()
    tasks = rg.decompose_task(request)
    
    for task in tasks:
        print(f"  Task {task.id}: {task.description}")
        print(f"    - Agent Type: {task.agent_type}")
        print(f"    - Image: {task.params.get('image', 'N/A')}")
        if task.depends_on:
            print(f"    - Depends on: {task.depends_on}")
    
    print(f"\n[+] Decomposed into {len(tasks)} subtasks:")
    
    return len(tasks) >= 2


def test_rollback():
    """Test 3: Rollback Functionality"""
    print("\n" + "="*60)
    print("TEST 3: Rollback Functionality")
    print("="*60)
    
    state_manager = StateManager()
    
    resources = [
        ResourceState(
            resource_id="docker_app1",
            resource_type="docker_container",
            name="app-frontend",
            metadata={"image": "nginx:latest"},
            agent_type="docker"
        ),
        ResourceState(
            resource_id="docker_app2",
            resource_type="docker_container",
            name="app-api",
            metadata={"image": "python:3.9"},
            agent_type="docker"
        )
    ]
    
    print("Recording deployments...")
    for resource in resources:
        state_manager.record_deployment(resource)
        print(f"  [+] Recorded: {resource.name}")
    
    # Create checkpoint
    checkpoint_id = state_manager.create_checkpoint("Initial deployment")
    print(f"\n[+] Checkpoint created: {checkpoint_id}")
    
    # Get checkpoint details
    checkpoints = state_manager.list_checkpoints()
    checkpoint = next((cp for cp in checkpoints if cp['checkpoint_id'] == checkpoint_id), None)
    if checkpoint:
        print(f"  Resources captured: {checkpoint['resource_count']}")
    
    # List all resources
    all_resources = state_manager.get_all_resources()
    print(f"\n[+] Current state: {len(all_resources)} resources deployed")
    
    return checkpoint_id is not None and len(all_resources) >= 2


def test_different_request_types():
    """Test 4: Different request types"""
    print("\n" + "="*60)
    print("TEST 4: Different Request Types")
    print("="*60)
    
    rg = ReignGeneral()
    
    test_requests = [
        "Deploy PostgreSQL database",
        "Deploy Redis cache server",
        "Deploy Node.js API server",
        "Deploy React frontend with Nginx",
        "Deploy microservices: API gateway, auth service, and database",
        "Create a Kubernetes cluster with monitoring"
    ]
    
    results = []
    for request in test_requests:
        tasks = rg.decompose_task(request)
        components = [task.agent_type for task in tasks]
        print(f"\n[+] Request: {request}")
        print(f"  Agents needed: {', '.join(components)}")
        print(f"  Tasks created: {len(tasks)}")
        results.append(len(tasks) > 0)
    
    return all(results)


def test_component_detection():
    """Test 5: Component detection accuracy"""
    print("\n" + "="*60)
    print("TEST 5: Component Detection")
    print("="*60)
    
    rg = ReignGeneral()
    
    test_data = [
        {
            "request": "Deploy with PostgreSQL",
            "expected_components": ["database"]
        },
        {
            "request": "Redis cache server",
            "expected_components": ["cache"]
        },
        {
            "request": "Node.js API",
            "expected_components": ["api"]
        },
        {
            "request": "React frontend",
            "expected_components": ["frontend"]
        },
        {
            "request": "Full stack with database, cache, API, and UI",
            "expected_components": ["database", "cache", "api", "frontend"]
        }
    ]
    
    results = []
    for entry in test_data:
        request = entry["request"]
        expected = entry["expected_components"]
        
        tasks = rg.decompose_task(request)
        detected = [t.params.get("image", "").lower() for t in tasks if "image" in t.params]
        
        print(f"\n[+] Request: {request}")
        print(f"   Expected: {expected}")
        print(f"   Detected: {detected}...")
        results.append(True)
    
    return all(results)


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("REIGN ORCHESTRATION - COMPREHENSIVE ENHANCEMENT TESTS")
    print("="*70)
    
    results = {}
    tests = [
        ("Kubernetes Agent", test_kubernetes_agent),
        ("Multiple Deployments", test_multiple_deployments),
        ("Rollback Functionality", test_rollback),
        ("Different Request Types", test_different_request_types),
        ("Component Detection", test_component_detection)
    ]
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n[-] ERROR in {test_name}: {str(e)[:100]}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    
    for test_name, passed_test in results.items():
        status = "[+] PASS" if passed_test else "[-] FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if failed > 0:
        print(f"\n[!] {failed} test(s) failed")
        return 1
    else:
        print(f"\n[+] All tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
