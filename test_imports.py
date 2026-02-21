"""Test script to verify REIGN imports work correctly."""

import sys
from pathlib import Path

print("=" * 60)
print("TESTING REIGN IMPORTS")
print("=" * 60)

# Show current working directory
print(f"\nCurrent directory: {Path.cwd()}")

# Test 1: Add src to path
src_path = Path.cwd() / "src"
print(f"\nAdding to path: {src_path}")
sys.path.insert(0, str(src_path))

print(f"\nPython path (first 3):")
for i, p in enumerate(sys.path[:3]):
    print(f"  {i}: {p}")

# Test 2: Try importing each component
print("\n" + "=" * 60)
print("IMPORTING COMPONENTS")
print("=" * 60)

try:
    print("\n1. Importing ReignGeneral...")
    from reign.swarm.reign_general import ReignGeneral, Task
    print("   ✓ SUCCESS - ReignGeneral imported")
except Exception as e:
    print(f"   ✗ FAILED - {e}")

try:
    print("\n2. Importing DockerAgent...")
    from reign.swarm.agents.docker_agent import DockerAgent
    print("   ✓ SUCCESS - DockerAgent imported")
except Exception as e:
    print(f"   ✗ FAILED - {e}")

try:
    print("\n3. Importing K8sAgent...")
    from reign.swarm.agents.k8s_agent import K8sAgent
    print("   ✓ SUCCESS - K8sAgent imported")
except Exception as e:
    print(f"   ✗ FAILED - {e}")

try:
    print("\n4. Importing AgentMemory...")
    from reign.swarm.memory.agent_memory import AgentMemory
    print("   ✓ SUCCESS - AgentMemory imported")
except Exception as e:
    print(f"   ✗ FAILED - {e}")

try:
    print("\n5. Importing StateManager...")
    from reign.swarm.state.state_manager import StateManager
    print("   ✓ SUCCESS - StateManager imported")
except Exception as e:
    print(f"   ✗ FAILED - {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)

# Test 3: Check if files exist
print("\nChecking file existence:")
files_to_check = [
    "src/reign/__init__.py",
    "src/reign/swarm/__init__.py",
    "src/reign/swarm/reign_general.py",
    "src/reign/swarm/agents/__init__.py",
    "src/reign/swarm/agents/docker_agent.py",
    "src/reign/swarm/agents/k8s_agent.py",
    "src/reign/swarm/memory/__init__.py",
    "src/reign/swarm/memory/agent_memory.py",
    "src/reign/swarm/state/__init__.py",
    "src/reign/swarm/state/state_manager.py",
]

for file_path in files_to_check:
    full_path = Path.cwd() / file_path
    exists = full_path.exists()
    symbol = "✓" if exists else "✗"
    print(f"  {symbol} {file_path}")

print("\n" + "=" * 60)
