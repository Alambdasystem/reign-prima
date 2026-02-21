"""
Integration tests for real Kubernetes operations.

These tests interact with actual Kubernetes cluster via kubectl.
Requires kubectl configured with a valid cluster.
"""

import pytest
import subprocess
import time
from pathlib import Path
import sys

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from reign.swarm.executors.real_kubernetes_executor import RealKubernetesExecutor
except ModuleNotFoundError:
    pytest.skip("RealKubernetesExecutor not yet implemented", allow_module_level=True)


def check_kubectl_available():
    """Check if kubectl is installed"""
    try:
        result = subprocess.run(
            ["kubectl", "version", "--client", "--short"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_cluster_accessible():
    """Check if a Kubernetes cluster is accessible"""
    if not check_kubectl_available():
        return False
    
    try:
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# Skip all tests if kubectl not available
pytestmark = pytest.mark.skipif(
    not check_kubectl_available(),
    reason="kubectl not installed or not in PATH"
)


class TestRealKubernetesExecutor:
    """Test real Kubernetes executor with kubectl"""
    
    def test_can_create_executor(self):
        """Test that RealKubernetesExecutor can be instantiated"""
        executor = RealKubernetesExecutor()
        
        assert executor is not None
    
    @pytest.mark.skipif(
        not check_cluster_accessible(),
        reason="No accessible Kubernetes cluster"
    )
    def test_can_create_deployment(self):
        """Test creating a real deployment"""
        executor = RealKubernetesExecutor()
        
        # Create simple deployment
        result = executor.create_deployment(
            name="reign-test-nginx",
            image="nginx:alpine",
            replicas=1,
            namespace="default",
            port=80
        )
        
        # Should succeed or already exist
        assert result is not None
        assert "success" in result
        
        # Cleanup
        try:
            executor.delete_deployment("reign-test-nginx", namespace="default")
        except:
            pass
    
    @pytest.mark.skipif(
        not check_cluster_accessible(),
        reason="No accessible Kubernetes cluster"
    )
    def test_can_scale_deployment(self):
        """Test scaling a deployment"""
        executor = RealKubernetesExecutor()
        
        # Create deployment first
        executor.create_deployment(
            name="reign-test-scale",
            image="nginx:alpine",
            replicas=1,
            namespace="default"
        )
        
        # Give it time to create
        time.sleep(2)
        
        # Scale to 3
        result = executor.scale_deployment(
            name="reign-test-scale",
            replicas=3,
            namespace="default"
        )
        
        assert result is not None
        
        # Cleanup
        try:
            executor.delete_deployment("reign-test-scale", namespace="default")
        except:
            pass
    
    @pytest.mark.skipif(
        not check_cluster_accessible(),
        reason="No accessible Kubernetes cluster"
    )
    def test_can_get_pods(self):
        """Test getting pods"""
        executor = RealKubernetesExecutor()
        
        pods = executor.get_pods(namespace="default")
        
        assert pods is not None
        assert isinstance(pods, list)
    
    @pytest.mark.skipif(
        not check_cluster_accessible(),
        reason="No accessible Kubernetes cluster"
    )
    def test_can_delete_deployment(self):
        """Test deleting a deployment"""
        executor = RealKubernetesExecutor()
        
        # Create deployment
        executor.create_deployment(
            name="reign-test-delete",
            image="nginx:alpine",
            replicas=1,
            namespace="default"
        )
        
        time.sleep(2)
        
        # Delete it
        result = executor.delete_deployment(
            name="reign-test-delete",
            namespace="default"
        )
        
        assert result is not None
        assert "success" in result or "returncode" in result
    
    def test_handles_invalid_yaml(self):
        """Test handling of invalid YAML"""
        executor = RealKubernetesExecutor()
        
        invalid_yaml = "invalid: yaml: content: [[[["
        
        result = executor.apply_yaml(invalid_yaml, namespace="default")
        
        assert result is not None
        assert result["success"] is False
        assert "stderr" in result


class TestKubernetesExecutorValidation:
    """Test Kubernetes executor validation"""
    
    def test_detects_missing_kubectl(self, monkeypatch):
        """Test detection when kubectl is not installed"""
        # Mock subprocess.run to simulate kubectl not found
        def mock_run(*args, **kwargs):
            raise FileNotFoundError("kubectl not found")
        
        monkeypatch.setattr(subprocess, "run", mock_run)
        
        with pytest.raises(EnvironmentError, match="kubectl not found"):
            RealKubernetesExecutor()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
