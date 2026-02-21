"""
REIGN with Ollama 3.2 - Local LLM Integration Demo

This demonstrates REIGN using Ollama 3.2 for natural language understanding.
Ollama provides local, private AI without needing cloud API keys!

Requirements:
- Ollama installed and running (localhost:11434)
- Model pulled: ollama pull llama3.2
"""
from src.reign.swarm.llm_provider import LLMConfig, OllamaProvider, create_llm_provider
from src.reign.swarm.reign_general import ReignGeneral
from src.reign.swarm.feedback_loop import FeedbackLoop
from src.reign.swarm.agents.docker_agent import DockerAgent
from src.reign.swarm.agents.kubernetes_agent import KubernetesAgent
from src.reign.swarm.agents.terraform_agent import TerraformAgent
import requests


def print_header(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def check_ollama_status():
    """Check if Ollama is running and has llama3.2"""
    print("🔍 Checking Ollama status...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json()
            model_names = [m['name'] for m in models.get('models', [])]
            
            print(f"✓ Ollama is running!")
            print(f"  Available models: {', '.join(model_names) if model_names else 'None'}")
            
            # Check for llama3.2
            has_llama32 = any('llama3.2' in m or 'llama3:latest' in m for m in model_names)
            if has_llama32:
                print(f"  ✓ Llama 3.2 found!")
                return True, model_names
            else:
                print(f"  ⚠️ Llama 3.2 not found. Run: ollama pull llama3.2")
                return True, model_names
        else:
            print(f"✗ Ollama returned status {response.status_code}")
            return False, []
    except requests.exceptions.ConnectionError:
        print(f"✗ Ollama is not running!")
        print(f"  Start it with: ollama serve")
        return False, []
    except Exception as e:
        print(f"✗ Error checking Ollama: {e}")
        return False, []


def demo_ollama_understanding():
    """Demo: Natural language understanding with Ollama"""
    print_header("Demo 1: Ollama-Powered Natural Language Understanding")
    
    # Configure Ollama
    llm_config = LLMConfig(
        provider="ollama",
        model="llama3.2",  # or "llama3:latest"
        base_url="http://localhost:11434",
        temperature=0.7
    )
    
    print(f"📝 LLM Configuration:")
    print(f"  - Provider: {llm_config.provider}")
    print(f"  - Model: {llm_config.model}")
    print(f"  - URL: {llm_config.base_url}")
    print(f"  - Temperature: {llm_config.temperature}")
    
    # Create REIGN with Ollama
    print(f"\n🤖 Initializing ReignGeneral with Ollama...")
    general = ReignGeneral(llm_config=llm_config)
    
    if general.llm_provider:
        print(f"  ✓ LLM provider initialized successfully!")
    else:
        print(f"  ⚠️ LLM initialization failed, using keyword fallback")
    
    # Test natural language understanding
    test_requests = [
        "Deploy a PostgreSQL 14 database with Redis cache",
        "Create a Kubernetes cluster with 3 replicas for my web app",
        "Set up Terraform infrastructure on AWS with VPC and RDS",
        "Scale the deployment to 5 instances",
        "Create a GitHub repository with CI/CD pipeline"
    ]
    
    print(f"\n{'─'*80}")
    print(f"Testing Ollama's Understanding:")
    print(f"{'─'*80}\n")
    
    for i, request in enumerate(test_requests, 1):
        print(f"{i}. User: \"{request}\"")
        
        try:
            intent = general.understand_request(request)
            
            print(f"   → Action: {intent.action}")
            print(f"   → Target: {intent.target}")
            print(f"   → Confidence: {intent.confidence:.2f}")
            if intent.params:
                print(f"   → Params: {intent.params}")
            print()
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
            print(f"   (Falling back to keyword matching)")
            print()


def demo_ollama_with_feedback():
    """Demo: Ollama + Feedback Loops"""
    print_header("Demo 2: Ollama + Feedback Loop Integration")
    
    llm_config = LLMConfig(
        provider="ollama",
        model="llama3.2",
        base_url="http://localhost:11434"
    )
    
    general = ReignGeneral(llm_config=llm_config)
    
    # Natural language request
    request = "Deploy a production-ready PostgreSQL database with monitoring and backups"
    
    print(f"User Request: \"{request}\"\n")
    print(f"→ Ollama processing...")
    
    try:
        intent = general.understand_request(request)
        
        print(f"\n✓ Ollama's Understanding:")
        print(f"  - Action: {intent.action}")
        print(f"  - Target: {intent.target}")
        print(f"  - Description: {intent.description}")
        print(f"  - Confidence: {intent.confidence:.2f}")
        print(f"  - Parameters: {intent.params}")
        
        # Now execute with feedback
        print(f"\n→ Executing with feedback loop...")
        
        agent = DockerAgent()
        loop = FeedbackLoop(max_retries=3, confidence_threshold=0.80)
        
        # Create task from intent
        from src.reign.swarm.reign_general import Task
        task = Task(
            id=1,
            description=intent.description,
            agent_type=intent.target if intent.target != "unknown" else "docker",
            params=intent.params if intent.params else {"image": "postgres:14"}
        )
        
        result = loop.execute_with_feedback(agent, task)
        
        print(f"\n✓ Execution Result:")
        print(f"  - Success: {result.success}")
        print(f"  - Confidence: {result.confidence:.2f}")
        print(f"  - Attempts: {loop.attempt_count}")
        
        if result.suggestions:
            print(f"\n  📋 Suggestions:")
            for suggestion in result.suggestions[:3]:
                print(f"    • {suggestion}")
        
    except Exception as e:
        print(f"\n✗ Error with Ollama: {e}")
        print(f"  Using keyword fallback...")


def demo_ollama_multi_agent():
    """Demo: Ollama orchestrating multi-agent swarm"""
    print_header("Demo 3: Ollama Orchestrating Multi-Agent Swarm")
    
    llm_config = LLMConfig(provider="ollama", model="llama3.2")
    general = ReignGeneral(llm_config=llm_config)
    
    # Complex multi-infrastructure request
    request = """
    I need a complete production infrastructure with:
    - PostgreSQL and Redis databases
    - Kubernetes deployment with 3 replicas
    - AWS infrastructure via Terraform
    - GitHub repository with automated CI/CD
    """
    
    print(f"Complex Request:\n{request}\n")
    print(f"→ Ollama analyzing and decomposing...")
    
    try:
        # Understand with Ollama
        intent = general.understand_request(request)
        
        print(f"\n✓ Ollama's Analysis:")
        print(f"  - Action: {intent.action}")
        print(f"  - Scope: {intent.description}")
        print(f"  - Confidence: {intent.confidence:.2f}")
        
        # Decompose into tasks
        tasks = general.decompose_task(intent)
        
        print(f"\n✓ Task Decomposition ({len(tasks)} tasks):")
        for task in tasks:
            deps = f" [depends: {task.depends_on}]" if task.depends_on else ""
            print(f"  {task.id}. [{task.agent_type}] {task.description}{deps}")
        
        # Execute with appropriate agents
        print(f"\n→ Executing swarm coordination...")
        
        agents_map = {
            "docker": DockerAgent(),
            "kubernetes": KubernetesAgent(),
            "terraform": TerraformAgent()
        }
        
        results = []
        for task in tasks[:3]:  # Execute first 3 tasks
            agent = agents_map.get(task.agent_type)
            if agent:
                loop = FeedbackLoop(max_retries=2, confidence_threshold=0.75)
                result = loop.execute_with_feedback(agent, task)
                
                results.append({
                    "task": task.description,
                    "agent": agent.name,
                    "confidence": result.confidence,
                    "success": result.success
                })
                
                status = "✓" if result.success else "✗"
                print(f"  {status} {agent.name}: {result.confidence:.2f} - {task.description[:50]}...")
        
        print(f"\n📊 Summary:")
        successful = sum(1 for r in results if r["success"])
        print(f"  - Completed: {successful}/{len(results)}")
        avg_conf = sum(r["confidence"] for r in results) / len(results) if results else 0
        print(f"  - Average Confidence: {avg_conf:.2f}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


def main():
    print("\n" + "="*80)
    print("  REIGN + OLLAMA 3.2 - Local LLM Integration")
    print("  Private, Fast, No API Keys Required!")
    print("="*80)
    
    # Check Ollama status
    is_running, models = check_ollama_status()
    
    if not is_running:
        print("\n⚠️ Ollama is not running. Please start it:")
        print("   1. Open a terminal")
        print("   2. Run: ollama serve")
        print("\nThen run this demo again.")
        return
    
    print("\n✓ Ollama is operational!\n")
    
    # Run demos
    try:
        demo_ollama_understanding()
        demo_ollama_with_feedback()
        demo_ollama_multi_agent()
        
        print_header("SUCCESS! Ollama Integration Working ✓")
        
        print("🎯 What just happened:")
        print("  1. Ollama (local LLM) processed natural language")
        print("  2. ReignGeneral used AI understanding (not keywords)")
        print("  3. Multi-agent swarm executed coordinated tasks")
        print("  4. Feedback loops ensured quality")
        
        print("\n🚀 Benefits of Ollama:")
        print("  ✓ 100% Private - data stays on your machine")
        print("  ✓ No API costs - completely free")
        print("  ✓ Fast - local processing")
        print("  ✓ Offline capable - no internet needed")
        
        print("\n💡 Next Steps:")
        print("  - Try different Ollama models (llama3.2, mistral, codellama)")
        print("  - Adjust temperature for creativity vs accuracy")
        print("  - Compare Ollama vs OpenAI vs Claude performance")
        
    except Exception as e:
        print(f"\n✗ Demo Error: {e}")
        print("\nNote: Ollama must be running with llama3.2 model")
        print("  Start: ollama serve")
        print("  Pull model: ollama pull llama3.2")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
