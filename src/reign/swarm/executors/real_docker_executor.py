"""
Real Docker executor using docker-py SDK.

This executor connects to the Docker daemon and performs actual
container operations instead of simulating them.
"""

import docker
from docker.errors import DockerException, ImageNotFound, NotFound, APIError
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class RealDockerExecutor:
    """Real Docker executor using docker-py SDK"""
    
    def __init__(self):
        """Initialize Docker client connection"""
        try:
            self.client = docker.from_env()
            # Verify connection
            self.client.ping()
            logger.info("Successfully connected to Docker daemon")
        except DockerException as e:
            logger.error(f"Cannot connect to Docker daemon: {e}")
            raise ConnectionError(
                f"Cannot connect to Docker daemon. Is Docker Desktop running? Error: {e}"
            )
    
    def ping(self) -> bool:
        """
        Ping Docker daemon to verify connection.
        
        Returns:
            bool: True if Docker daemon is accessible
        """
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Docker ping failed: {e}")
            return False
    
    def pull_image(self, repository: str, tag: str = "latest") -> Optional[str]:
        """
        Pull a Docker image from registry.
        
        Args:
            repository: Image repository name (e.g., "nginx")
            tag: Image tag (default: "latest")
        
        Returns:
            str: Image name if successful, None otherwise
        """
        try:
            image_name = f"{repository}:{tag}"
            logger.info(f"Pulling image: {image_name}")
            
            image = self.client.images.pull(repository, tag=tag)
            
            logger.info(f"Successfully pulled: {image_name}")
            return image_name
        except ImageNotFound as e:
            logger.error(f"Image not found: {repository}:{tag} - {e}")
            return None
        except APIError as e:
            logger.error(f"Docker API error while pulling {repository}:{tag} - {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error pulling {repository}:{tag} - {e}")
            return None
    
    def create_container(
        self,
        image: str,
        name: Optional[str] = None,
        command: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Create a Docker container.
        
        Args:
            image: Docker image to use
            name: Container name (optional)
            command: Command to run in container (optional)
            **kwargs: Additional container options (ports, volumes, environment, etc.)
        
        Returns:
            str: Container ID/name if successful, error message otherwise
        """
        try:
            logger.info(f"Creating container from image: {image}")
            
            container = self.client.containers.create(
                image=image,
                name=name,
                command=command,
                **kwargs
            )
            
            logger.info(f"Successfully created container: {container.short_id}")
            return container.name if name else container.short_id
        
        except ImageNotFound as e:
            error_msg = f"Image not found: {image}"
            logger.error(f"{error_msg} - {e}")
            return error_msg
        
        except APIError as e:
            error_msg = f"Docker API error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        
        except Exception as e:
            error_msg = f"Error creating container: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def list_containers(self, all: bool = False) -> List[Dict[str, Any]]:
        """
        List Docker containers.
        
        Args:
            all: If True, show all containers (default: running only)
        
        Returns:
            List of container dictionaries with id, name, status
        """
        try:
            containers = self.client.containers.list(all=all)
            
            result = []
            for container in containers:
                result.append({
                    "id": container.short_id,
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else "unknown"
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return []
    
    def remove_container(self, container_name: str, force: bool = False) -> bool:
        """
        Remove a Docker container.
        
        Args:
            container_name: Container name or ID
            force: If True, force removal even if running
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            container = self.client.containers.get(container_name)
            container.remove(force=force)
            
            logger.info(f"Successfully removed container: {container_name}")
            return True
        
        except NotFound:
            logger.warning(f"Container not found: {container_name}")
            return False
        
        except APIError as e:
            logger.error(f"Docker API error removing {container_name}: {e}")
            return False
        
        except Exception as e:
            logger.error(f"Error removing container {container_name}: {e}")
            return False
    
    def inspect_container(self, container_name: str) -> Optional[Dict[str, Any]]:
        """
        Inspect a Docker container.
        
        Args:
            container_name: Container name or ID
        
        Returns:
            Dict with container details, or None if not found
        """
        try:
            container = self.client.containers.get(container_name)
            
            # Return simplified inspection data
            return {
                "id": container.short_id,
                "name": container.name,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "created": container.attrs.get("Created"),
                "state": container.attrs.get("State"),
                "config": {
                    "hostname": container.attrs.get("Config", {}).get("Hostname"),
                    "cmd": container.attrs.get("Config", {}).get("Cmd"),
                    "env": container.attrs.get("Config", {}).get("Env"),
                }
            }
        
        except NotFound:
            logger.error(f"Container not found: {container_name}")
            return None
        
        except Exception as e:
            logger.error(f"Error inspecting container {container_name}: {e}")
            return None
    
    def start_container(self, container_name: str) -> bool:
        """
        Start a Docker container.
        
        Args:
            container_name: Container name or ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            container = self.client.containers.get(container_name)
            container.start()
            
            logger.info(f"Successfully started container: {container_name}")
            return True
        
        except NotFound:
            logger.error(f"Container not found: {container_name}")
            return False
        
        except APIError as e:
            logger.error(f"Docker API error starting {container_name}: {e}")
            return False
        
        except Exception as e:
            logger.error(f"Error starting container {container_name}: {e}")
            return False
    
    def stop_container(self, container_name: str, timeout: int = 10) -> bool:
        """
        Stop a Docker container.
        
        Args:
            container_name: Container name or ID
            timeout: Seconds to wait before killing
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=timeout)
            
            logger.info(f"Successfully stopped container: {container_name}")
            return True
        
        except NotFound:
            logger.error(f"Container not found: {container_name}")
            return False
        
        except APIError as e:
            logger.error(f"Docker API error stopping {container_name}: {e}")
            return False
        
        except Exception as e:
            logger.error(f"Error stopping container {container_name}: {e}")
            return False
    
    def get_logs(self, container_name: str, tail: int = 100) -> Optional[str]:
        """
        Get container logs.
        
        Args:
            container_name: Container name or ID
            tail: Number of lines from end to retrieve
        
        Returns:
            str: Container logs, or None if error
        """
        try:
            container = self.client.containers.get(container_name)
            logs = container.logs(tail=tail).decode('utf-8')
            
            return logs
        
        except NotFound:
            logger.error(f"Container not found: {container_name}")
            return None
        
        except Exception as e:
            logger.error(f"Error getting logs for {container_name}: {e}")
            return None
