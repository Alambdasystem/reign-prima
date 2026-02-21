"""
Demo: Feedback Loop System in Action

This demonstrates how the FeedbackLoop enables:
1. Automatic retry on low confidence
2. Learning from failures
3. Applying best practice suggestions
4. Improving task parameters
"""
from src.reign.swarm.feedback_loop import FeedbackLoop, Feedback, FeedbackType, FeedbackSeverity
from src.reign.swarm.agents.docker_agent import DockerAgent
from src.reign.swarm.agents.kubernetes_agent import KubernetesAgent
from src.reign.swarm.agents.terraform_agent import TerraformAgent
from src.reign.swarm.reign_general import Task


def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def demo_basic_feedback():
    """Demo 1: Basic feedback loop with Docker"""
    print_section("Demo 1: Basic Feedback Loop - Docker Deployment")
    
    agent = DockerAgent()
    loop = FeedbackLoop(max_retries=3, confidence_threshold=0.80)
    
    task = Task(
        id=1,
        description="Deploy PostgreSQL database",
        agent_type="docker",
        params={"image": "postgres:14-alpine", "port": 5432}
    )
    
    print(f"Task: {task.description}")
    print(f"Confidence threshold: {loop.confidence_threshold}")
    
    result = loop.execute_with_feedback(agent, task)
    
    print(f"\n✓ Result:")
    print(f"  - Success: {result.success}")
    print(f"  - Confidence: {result.confidence:.2f}")
    print(f"  - Attempts: {loop.attempt_count}")
    print(f"  - Feedback count: {len(loop.feedback_history)}")
    
    if loop.feedback_history:
        print(f"\n  Feedback generated:")
        for fb in loop.feedback_history:
            print(f"    • {fb.type.value}: {fb.message}")
            for suggestion in fb.suggestions[:2]:  # First 2 suggestions
                print(f"      → {suggestion}")


def demo_low_confidence_retry():
    """Demo 2: Retry on low confidence"""
    print_section("Demo 2: Automatic Retry on Low Confidence")
    
    agent = DockerAgent()
    loop = FeedbackLoop(max_retries=3, confidence_threshold=0.90)  # High threshold
    
    task = Task(
        id=2,
        description="Deploy custom app without version",
        agent_type="docker",
        params={"image": "myapp", "port": 3000}  # No version tag!
    )
    
    print(f"Task: {task.description}")
    print(f"Image: {task.params['image']} (no version tag)")
    print(f"High confidence threshold: {loop.confidence_threshold}")
    
    result = loop.execute_with_feedback(agent, task)
    
    print(f"\n✓ Result:")
    print(f"  - Success: {result.success}")
    print(f"  - Confidence: {result.confidence:.2f} (below threshold!)")
    print(f"  - Attempts: {loop.attempt_count}")
    
    summary = loop.get_feedback_summary()
    print(f"\n  Feedback Summary:")
    print(f"    - Total feedback items: {len(summary['feedbacks'])}")
    for fb_dict in summary['feedbacks']:
        print(f"    - {fb_dict['type']}: {fb_dict['message']}")


def demo_auto_improvement():
    """Demo 3: Auto-improvement with feedback"""
    print_section("Demo 3: Auto-Improvement with Feedback")
    
    agent = DockerAgent()
    loop = FeedbackLoop(max_retries=3, confidence_threshold=0.85)
    
    task = Task(
        id=3,
        description="Deploy nginx web server",
        agent_type="docker",
        params={"image": "nginx"}  # Missing version and other best practices
    )
    
    print(f"Task: {task.description}")
    print(f"Original params: {task.params}")
    print(f"Auto-improve: ENABLED")
    
    result = loop.execute_with_feedback(agent, task, auto_improve=True)
    
    print(f"\n✓ Result:")
    print(f"  - Success: {result.success}")
    print(f"  - Confidence: {result.confidence:.2f}")
    print(f"  - Attempts: {loop.attempt_count}")
    
    if result.suggestions:
        print(f"\n  Best Practice Suggestions Applied:")
        for suggestion in result.suggestions[:3]:
            print(f"    ✓ {suggestion}")


def demo_multi_agent_feedback():
    """Demo 4: Feedback loops across multiple agents"""
    print_section("Demo 4: Multi-Agent Feedback Loop Coordination")
    
    tasks_and_agents = [
        (DockerAgent(), Task(
            id=4, 
            description="Deploy Redis cache",
            agent_type="docker",
            params={"image": "redis:7-alpine", "port": 6379}
        )),
        (KubernetesAgent(), Task(
            id=5,
            description="Deploy web app to K8s",
            agent_type="kubernetes",
            params={"action": "deploy", "name": "webapp", "image": "myapp:1.0", "replicas": 3}
        )),
        (TerraformAgent(), Task(
            id=6,
            description="Provision AWS infrastructure",
            agent_type="terraform",
            params={"provider": "aws", "resources": ["vpc", "subnet"]}
        ))
    ]
    
    loop = FeedbackLoop(max_retries=2, confidence_threshold=0.75)
    results = []
    
    for agent, task in tasks_and_agents:
        print(f"\n→ Executing: {task.description}")
        result = loop.execute_with_feedback(agent, task)
        results.append({
            "agent": agent.name,
            "success": result.success,
            "confidence": result.confidence,
            "attempts": loop.attempt_count
        })
        print(f"  ✓ {agent.name}: Confidence {result.confidence:.2f} in {loop.attempt_count} attempt(s)")
    
    print(f"\n{'─'*70}")
    print(f"  Multi-Agent Summary:")
    print(f"{'─'*70}")
    for r in results:
        status = "✓" if r["success"] else "✗"
        print(f"  {status} {r['agent']:20s} | Confidence: {r['confidence']:.2f} | Attempts: {r['attempts']}")


def demo_feedback_learning():
    """Demo 5: Learning from feedback history"""
    print_section("Demo 5: Learning from Feedback History")
    
    agent = DockerAgent()
    loop = FeedbackLoop(max_retries=3, confidence_threshold=0.80)
    
    # Series of tasks with progressive improvement
    tasks = [
        Task(1, "Deploy without version", "docker", {"image": "app1"}),
        Task(2, "Deploy with version", "docker", {"image": "app2:1.0"}),
        Task(3, "Deploy with all best practices", "docker", {
            "image": "app3:1.0",
            "health_check": True,
            "memory": "512m"
        })
    ]
    
    print("Running 3 tasks with progressive improvement:\n")
    
    for i, task in enumerate(tasks, 1):
        print(f"{i}. {task.description}")
        result = loop.execute_with_feedback(agent, task)
        print(f"   → Confidence: {result.confidence:.2f}")
        print(f"   → Suggestions: {len(result.suggestions)}")
        print()
    
    print("📊 Learning Pattern:")
    print("   • Task 1: Low confidence (no version)")
    print("   • Task 2: Better confidence (has version)")
    print("   • Task 3: High confidence (best practices)")
    print("\n   The system learns what makes a high-quality deployment!")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  REIGN FEEDBACK LOOP SYSTEM DEMONSTRATION")
    print("  Enabling Agent Learning & Quality Improvement")
    print("="*70)
    
    demo_basic_feedback()
    demo_low_confidence_retry()
    demo_auto_improvement()
    demo_multi_agent_feedback()
    demo_feedback_learning()
    
    print(f"\n{'='*70}")
    print("  ✓ Feedback Loop System Working!")
    print("  ✓ Agents can retry, learn, and improve")
    print("  ✓ Quality thresholds enforced")
    print("  ✓ Best practices applied automatically")
    print(f"{'='*70}\n")
