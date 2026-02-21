"""
Real Kubernetes executor using kubectl CLI.

This executor performs actual Kubernetes operations by calling kubectl
subprocess commands instead of simulating them.
"""

import subprocess
import json
import yaml
from typing import Dict, Any, Optional, List
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class RealKubernetesExecutor:
    """Real Kubernetes executor using kubectl CLI"""
    
    def __init__(self, kubeconfig: Optional[str] = None):
        """
        Initialize Kubernetes executor.
        
        Args:
            kubeconfig: Path to kubeconfig file (optional, uses default if not provided)
        """
        self.kubeconfig = kubeconfig
        self._verify_kubectl()
    
    def _verify_kubectl(self) -> bool:
        """
        Verify kubectl is installed and accessible.
        
        Returns:
            bool: True if kubectl is available
        
        Raises:
            EnvironmentError: If kubectl is not found
        """
        try:
            result = subprocess.run(
                ["kubectl", "version", "--client", "--short"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info(f"kubectl found: {result.stdout.strip()}")
                return True
            else:
                raise EnvironmentError("kubectl command failed")
        
        except FileNotFoundError:
            raise EnvironmentError(
                "kubectl not found. Please install kubectl: "
                "https://kubernetes.io/docs/tasks/tools/"
            )
        except subprocess.TimeoutExpired:
            raise EnvironmentError("kubectl command timed out")
    
    def _run_kubectl(
        self,
        args: List[str],
        input_data: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Run kubectl command.
        
        Args:
            args: kubectl arguments (without 'kubectl' prefix)
            input_data: Optional input to pass via stdin
            timeout: Command timeout in seconds
        
        Returns:
            Dict with returncode, stdout, stderr
        """
        cmd = ["kubectl"]
        
        if self.kubeconfig:
            cmd.extend(["--kubeconfig", self.kubeconfig])
        
        cmd.extend(args)
        
        logger.info(f"Running kubectl: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                input=input_data,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
        
        except subprocess.TimeoutExpired:
            logger.error(f"kubectl command timed out after {timeout}s")
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "success": False
            }
        except Exception as e:
            logger.error(f"kubectl command failed: {e}")
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False
            }
    
    def apply_yaml(
        self,
        yaml_content: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Apply Kubernetes YAML configuration.
        
        Args:
            yaml_content: YAML configuration to apply
            namespace: Kubernetes namespace
        
        Returns:
            Dict with operation result
        """
        try:
            # Validate YAML first
            yaml.safe_load(yaml_content)
            
            result = self._run_kubectl(
                ["apply", "-f", "-", "-n", namespace],
                input_data=yaml_content
            )
            
            if result["success"]:
                logger.info(f"Successfully applied YAML to namespace {namespace}")
            else:
                logger.error(f"Failed to apply YAML: {result['stderr']}")
            
            return result
        
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML: {e}")
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Invalid YAML: {e}",
                "success": False
            }
    
    def create_deployment(
        self,
        name: str,
        image: str,
        replicas: int = 1,
        namespace: str = "default",
        port: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a Kubernetes deployment.
        
        Args:
            name: Deployment name
            image: Container image
            replicas: Number of replicas
            namespace: Kubernetes namespace
            port: Container port to expose
        
        Returns:
            Dict with operation result
        """
        # Build deployment YAML
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "spec": {
                "replicas": replicas,
                "selector": {
                    "matchLabels": {
                        "app": name
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": name
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": name,
                            "image": image,
                            "ports": [{"containerPort": port}] if port else []
                        }]
                    }
                }
            }
        }
        
        yaml_content = yaml.dump(deployment)
        return self.apply_yaml(yaml_content, namespace)
    
    def scale_deployment(
        self,
        name: str,
        replicas: int,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Scale a deployment.
        
        Args:
            name: Deployment name
            replicas: New replica count
            namespace: Kubernetes namespace
        
        Returns:
            Dict with operation result
        """
        result = self._run_kubectl([
            "scale",
            f"deployment/{name}",
            f"--replicas={replicas}",
            "-n", namespace
        ])
        
        if result["success"]:
            logger.info(f"Successfully scaled {name} to {replicas} replicas")
        
        return result
    
    def delete_deployment(
        self,
        name: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Delete a deployment.
        
        Args:
            name: Deployment name
            namespace: Kubernetes namespace
        
        Returns:
            Dict with operation result
        """
        result = self._run_kubectl([
            "delete",
            f"deployment/{name}",
            "-n", namespace
        ])
        
        if result["success"]:
            logger.info(f"Successfully deleted deployment {name}")
        
        return result
    
    def get_pods(
        self,
        namespace: str = "default",
        label_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pods in namespace.
        
        Args:
            namespace: Kubernetes namespace
            label_selector: Optional label selector (e.g., "app=myapp")
        
        Returns:
            List of pod dictionaries
        """
        args = ["get", "pods", "-n", namespace, "-o", "json"]
        
        if label_selector:
            args.extend(["-l", label_selector])
        
        result = self._run_kubectl(args)
        
        if result["success"]:
            try:
                pod_list = json.loads(result["stdout"])
                return pod_list.get("items", [])
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse pod JSON: {e}")
                return []
        else:
            logger.error(f"Failed to get pods: {result['stderr']}")
            return []
    
    def get_deployment(
        self,
        name: str,
        namespace: str = "default"
    ) -> Optional[Dict[str, Any]]:
        """
        Get deployment details.
        
        Args:
            name: Deployment name
            namespace: Kubernetes namespace
        
        Returns:
            Dict with deployment details, or None if not found
        """
        result = self._run_kubectl([
            "get",
            f"deployment/{name}",
            "-n", namespace,
            "-o", "json"
        ])
        
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse deployment JSON: {e}")
                return None
        else:
            logger.error(f"Failed to get deployment: {result['stderr']}")
            return None
    
    def deploy_helm_chart(
        self,
        release_name: str,
        chart: str,
        namespace: str = "default",
        values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deploy Helm chart.
        
        Args:
            release_name: Helm release name
            chart: Chart name or path
            namespace: Kubernetes namespace
            values: Optional values dictionary
        
        Returns:
            Dict with operation result
        """
        # Check if helm is available
        try:
            subprocess.run(
                ["helm", "version", "--short"],
                capture_output=True,
                timeout=5
            )
        except FileNotFoundError:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "helm not found. Please install Helm.",
                "success": False
            }
        
        cmd = [
            "helm", "install",
            release_name, chart,
            "-n", namespace,
            "--create-namespace"
        ]
        
        # Add values if provided
        if values:
            # Write values to temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.yaml',
                delete=False
            ) as f:
                yaml.dump(values, f)
                values_file = f.name
            
            cmd.extend(["-f", values_file])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
        
        except Exception as e:
            logger.error(f"Helm install failed: {e}")
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False
            }
        finally:
            # Cleanup temp values file
            if values:
                try:
                    Path(values_file).unlink()
                except:
                    pass
