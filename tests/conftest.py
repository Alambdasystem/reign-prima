"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_request():
    """Sample user request for testing"""
    return "Deploy a PostgreSQL database"


@pytest.fixture
def complex_request():
    """Complex multi-step request"""
    return "Deploy full-stack app with React frontend, Node.js API, and PostgreSQL database"


@pytest.fixture(autouse=True)
def reset_state():
    """Reset any global state between tests"""
    yield
    # Cleanup after each test
