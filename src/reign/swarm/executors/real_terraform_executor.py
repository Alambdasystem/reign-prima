"""
Real Terraform executor using python-terraform wrapper.

This executor performs actual Terraform operations by calling terraform CLI
through the python-terraform library.
"""

import subprocess
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
from python_terraform import Terraform, IsFlagged

logger = logging.getLogger(__name__)


class RealTerraformExecutor:
    """Real Terraform executor using python-terraform wrapper"""
    
    def __init__(self):
        """
        Initialize Terraform executor.
        
        Raises:
            EnvironmentError: If terraform CLI is not found
        """
        self._verify_terraform()
    
    def _verify_terraform(self) -> bool:
        """
        Verify terraform is installed and accessible.
        
        Returns:
            bool: True if terraform is available
        
        Raises:
            EnvironmentError: If terraform is not found
        """
        try:
            result = subprocess.run(
                ["terraform", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info(f"terraform found: {result.stdout.strip()}")
                return True
            else:
                raise EnvironmentError("terraform command failed")
        
        except FileNotFoundError:
            raise EnvironmentError(
                "terraform not found. Please install terraform: "
                "https://www.terraform.io/downloads"
            )
        except subprocess.TimeoutExpired:
            raise EnvironmentError("terraform command timed out")
    
    def init(
        self,
        working_dir: str,
        backend_config: Optional[Dict[str, str]] = None,
        upgrade: bool = False
    ) -> Dict[str, Any]:
        """
        Initialize a Terraform working directory.
        
        Args:
            working_dir: Path to terraform configuration
            backend_config: Optional backend configuration
            upgrade: Whether to upgrade providers
        
        Returns:
            Dict with operation result
        """
        try:
            tf = Terraform(working_dir=working_dir)
            
            kwargs = {}
            if backend_config:
                kwargs['backend_config'] = backend_config
            if upgrade:
                kwargs['upgrade'] = IsFlagged
            
            return_code, stdout, stderr = tf.init(**kwargs)
            
            success = return_code == 0
            
            if success:
                logger.info(f"Successfully initialized Terraform in {working_dir}")
            else:
                logger.error(f"Terraform init failed: {stderr}")
            
            return {
                "success": success,
                "returncode": return_code,
                "stdout": stdout,
                "stderr": stderr
            }
        
        except Exception as e:
            logger.error(f"Terraform init error: {e}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def plan(
        self,
        working_dir: str,
        var_file: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
        out: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Terraform execution plan.
        
        Args:
            working_dir: Path to terraform configuration
            var_file: Path to variables file
            variables: Dictionary of variables
            out: Path to save plan file
        
        Returns:
            Dict with operation result
        """
        try:
            tf = Terraform(working_dir=working_dir)
            
            kwargs = {}
            if var_file:
                kwargs['var_file'] = var_file
            if variables:
                kwargs['var'] = variables
            if out:
                kwargs['out'] = out
            
            return_code, stdout, stderr = tf.plan(**kwargs)
            
            success = return_code == 0
            
            if success:
                logger.info(f"Terraform plan successful in {working_dir}")
            else:
                logger.error(f"Terraform plan failed: {stderr}")
            
            return {
                "success": success,
                "returncode": return_code,
                "stdout": stdout,
                "stderr": stderr
            }
        
        except Exception as e:
            logger.error(f"Terraform plan error: {e}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def apply(
        self,
        working_dir: str,
        var_file: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
        auto_approve: bool = True
    ) -> Dict[str, Any]:
        """
        Apply Terraform configuration.
        
        Args:
            working_dir: Path to terraform configuration
            var_file: Path to variables file
            variables: Dictionary of variables
            auto_approve: Whether to auto-approve (default: True for automation)
        
        Returns:
            Dict with operation result
        """
        try:
            tf = Terraform(working_dir=working_dir)
            
            kwargs = {}
            if var_file:
                kwargs['var_file'] = var_file
            if variables:
                kwargs['var'] = variables
            if auto_approve:
                kwargs['auto_approve'] = IsFlagged
            
            return_code, stdout, stderr = tf.apply(**kwargs)
            
            success = return_code == 0
            
            if success:
                logger.info(f"Terraform apply successful in {working_dir}")
            else:
                logger.error(f"Terraform apply failed: {stderr}")
            
            return {
                "success": success,
                "returncode": return_code,
                "stdout": stdout,
                "stderr": stderr
            }
        
        except Exception as e:
            logger.error(f"Terraform apply error: {e}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def destroy(
        self,
        working_dir: str,
        var_file: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
        auto_approve: bool = True
    ) -> Dict[str, Any]:
        """
        Destroy Terraform-managed infrastructure.
        
        Args:
            working_dir: Path to terraform configuration
            var_file: Path to variables file
            variables: Dictionary of variables
            auto_approve: Whether to auto-approve (default: True for automation)
        
        Returns:
            Dict with operation result
        """
        try:
            tf = Terraform(working_dir=working_dir)
            
            kwargs = {}
            if var_file:
                kwargs['var_file'] = var_file
            if variables:
                kwargs['var'] = variables
            if auto_approve:
                kwargs['force'] = IsFlagged
            
            return_code, stdout, stderr = tf.destroy(**kwargs)
            
            success = return_code == 0
            
            if success:
                logger.info(f"Terraform destroy successful in {working_dir}")
            else:
                logger.error(f"Terraform destroy failed: {stderr}")
            
            return {
                "success": success,
                "returncode": return_code,
                "stdout": stdout,
                "stderr": stderr
            }
        
        except Exception as e:
            logger.error(f"Terraform destroy error: {e}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def validate(self, working_dir: str) -> Dict[str, Any]:
        """
        Validate Terraform configuration.
        
        Args:
            working_dir: Path to terraform configuration
        
        Returns:
            Dict with operation result
        """
        try:
            tf = Terraform(working_dir=working_dir)
            
            return_code, stdout, stderr = tf.validate()
            
            success = return_code == 0
            
            if success:
                logger.info(f"Terraform configuration valid in {working_dir}")
            else:
                logger.error(f"Terraform validation failed: {stderr}")
            
            return {
                "success": success,
                "returncode": return_code,
                "stdout": stdout,
                "stderr": stderr
            }
        
        except Exception as e:
            logger.error(f"Terraform validate error: {e}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def fmt(
        self,
        working_dir: str,
        check: bool = False,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Format Terraform configuration files.
        
        Args:
            working_dir: Path to terraform configuration
            check: Check if files are formatted without writing
            recursive: Process subdirectories
        
        Returns:
            Dict with operation result
        """
        try:
            tf = Terraform(working_dir=working_dir)
            
            kwargs = {}
            if check:
                kwargs['check'] = IsFlagged
            if recursive:
                kwargs['recursive'] = IsFlagged
            
            return_code, stdout, stderr = tf.fmt(**kwargs)
            
            success = return_code == 0
            
            return {
                "success": success,
                "returncode": return_code,
                "stdout": stdout,
                "stderr": stderr
            }
        
        except Exception as e:
            logger.error(f"Terraform fmt error: {e}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def output(
        self,
        working_dir: str,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get Terraform output values.
        
        Args:
            working_dir: Path to terraform configuration
            name: Specific output name (optional)
        
        Returns:
            Dict with output values or error
        """
        try:
            tf = Terraform(working_dir=working_dir)
            
            if name:
                result = tf.output(name)
            else:
                result = tf.output()
            
            return {
                "success": True,
                "output": result
            }
        
        except Exception as e:
            logger.error(f"Terraform output error: {e}")
            return {
                "success": False,
                "output": None,
                "error": str(e)
            }
