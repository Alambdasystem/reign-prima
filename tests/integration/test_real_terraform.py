"""
Integration tests for real Terraform operations.

These tests interact with actual Terraform CLI via python-terraform.
Requires terraform CLI installed.
"""

import pytest
import subprocess
import tempfile
from pathlib import Path
import sys

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from reign.swarm.executors.real_terraform_executor import RealTerraformExecutor
except ModuleNotFoundError:
    pytest.skip("RealTerraformExecutor not yet implemented", allow_module_level=True)


def check_terraform_available():
    """Check if terraform CLI is installed"""
    try:
        result = subprocess.run(
            ["terraform", "version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# Skip all tests if terraform not available
pytestmark = pytest.mark.skipif(
    not check_terraform_available(),
    reason="terraform CLI not installed or not in PATH"
)


class TestRealTerraformExecutor:
    """Test real Terraform executor with terraform CLI"""
    
    def test_can_create_executor(self):
        """Test that RealTerraformExecutor can be instantiated"""
        executor = RealTerraformExecutor()
        
        assert executor is not None
    
    def test_can_init_terraform(self):
        """Test terraform init in a directory"""
        executor = RealTerraformExecutor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal terraform config
            tf_file = Path(tmpdir) / "main.tf"
            tf_file.write_text("""
terraform {
  required_providers {
    null = {
      source = "hashicorp/null"
    }
  }
}
""")
            
            result = executor.init(tmpdir)
            
            assert result is not None
            assert result.get("success") is True or result.get("returncode") == 0
    
    def test_can_validate_terraform(self):
        """Test terraform validate"""
        executor = RealTerraformExecutor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid terraform config
            tf_file = Path(tmpdir) / "main.tf"
            tf_file.write_text("""
terraform {
  required_providers {
    null = {
      source = "hashicorp/null"
    }
  }
}

resource "null_resource" "test" {
  triggers = {
    timestamp = timestamp()
  }
}
""")
            
            # Init first
            executor.init(tmpdir)
            
            # Then validate
            result = executor.validate(tmpdir)
            
            assert result is not None
            assert result.get("success") is True or "valid" in str(result).lower()
    
    def test_can_plan_terraform(self):
        """Test terraform plan"""
        executor = RealTerraformExecutor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tf_file = Path(tmpdir) / "main.tf"
            tf_file.write_text("""
terraform {
  required_providers {
    null = {
      source = "hashicorp/null"
    }
  }
}

resource "null_resource" "test" {
  triggers = {
    value = "test"
  }
}
""")
            
            executor.init(tmpdir)
            result = executor.plan(tmpdir)
            
            assert result is not None
            assert "success" in result or "returncode" in result
    
    def test_handles_invalid_terraform_config(self):
        """Test handling of invalid terraform configuration"""
        executor = RealTerraformExecutor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tf_file = Path(tmpdir) / "main.tf"
            tf_file.write_text("invalid terraform syntax {{{")
            
            result = executor.validate(tmpdir)
            
            assert result is not None
            # Should indicate failure
            assert result.get("success") is False or result.get("returncode") != 0
    
    def test_can_format_terraform(self):
        """Test terraform fmt"""
        executor = RealTerraformExecutor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tf_file = Path(tmpdir) / "main.tf"
            # Write poorly formatted terraform
            tf_file.write_text("""
resource "null_resource" "test" {
triggers = {
value = "test"
}
}
""")
            
            result = executor.fmt(tmpdir)
            
            assert result is not None


class TestTerraformExecutorValidation:
    """Test Terraform executor validation"""
    
    def test_detects_missing_terraform(self, monkeypatch):
        """Test detection when terraform is not installed"""
        def mock_run(*args, **kwargs):
            raise FileNotFoundError("terraform not found")
        
        monkeypatch.setattr(subprocess, "run", mock_run)
        
        with pytest.raises(EnvironmentError, match="terraform not found"):
            RealTerraformExecutor()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
