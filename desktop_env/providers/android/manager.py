import logging
import os
from typing import Optional, Dict, Any

from desktop_env.providers.base import VMManager

logger = logging.getLogger("desktopenv.providers.android.manager")


class AndroidVMManager(VMManager):
    """
    VMManager for Android emulator running in docker-android container.
    Manages VM registration and port allocation for Android emulators.
    """

    def __init__(self):
        self.vms: Dict[str, Dict[str, Any]] = {}  # path_to_vm -> {region, pid, ports}
        self.checked_and_cleaned = False

    def initialize_registry(self, **kwargs):
        """Initialize the registry (no-op for Android since we use Docker)."""
        logger.info("Initializing Android VM registry")
        self.checked_and_cleaned = True

    def get_vm_path(self, os_type: str = "Android", region: str = None, screen_size: tuple = (1080, 1920)) -> str:
        """
        Returns a dummy path for Android since we use docker containers.
        The actual VM identification is handled by container name/ID.
        """
        return f"android-{os_type.lower()}-{region or 'default'}"

    def add_vm(self, vm_path: str, region: str = None, screen_size: tuple = None, **kwargs):
        """Register a VM path."""
        if vm_path not in self.vms:
            self.vms[vm_path] = {
                "region": region,
                "screen_size": screen_size,
                "pid": None
            }
            logger.info(f"Registered Android VM: {vm_path}")

    def delete_vm(self, vm_path: str, region: str = None, **kwargs):
        """Remove a VM registration."""
        if vm_path in self.vms:
            del self.vms[vm_path]
            logger.info(f"Unregistered Android VM: {vm_path}")

    def occupy_vm(self, vm_path: str, pid: int, region: str = None, **kwargs):
        """Mark a VM as occupied by a process."""
        if vm_path in self.vms:
            self.vms[vm_path]["pid"] = pid
            logger.info(f"Android VM {vm_path} occupied by PID {pid}")

    def release_vm(self, vm_path: str, **kwargs):
        """Release a VM."""
        if vm_path in self.vms:
            if "pid" in self.vms[vm_path]:
                self.vms[vm_path]["pid"] = None
            logger.info(f"Android VM {vm_path} released")

    def has_free_vm(self, region: str = None, **kwargs) -> bool:
        """Check if there are free VMs."""
        for vm_path, vm_info in self.vms.items():
            if vm_info.get("pid") is None:
                return True
        return True  # Android containers can be created dynamically

    def get_random_free_vm(self, region: str = None, **kwargs) -> str:
        """Get a random free VM path."""
        for vm_path, vm_info in self.vms.items():
            if vm_info.get("pid") is None:
                return vm_path
        return self.get_vm_path(os_type="Android", region=region)

    def list_free_vms(self, region: str = None, **kwargs) -> list:
        """List all free VM paths."""
        return [
            vm_path for vm_path, vm_info in self.vms.items()
            if vm_info.get("pid") is None
        ]

    def check_and_clean(self, **kwargs):
        """
        Check the registration list and remove paths of VMs that are not in use.
        For Android, we just verify containers are still running.
        """
        import docker
        try:
            client = docker.from_env()
            for vm_path in list(self.vms.keys()):
                try:
                    container = client.containers.get(vm_path)
                    if container.status != "running":
                        logger.warning(f"Android VM {vm_path} is not running, removing from registry")
                        del self.vms[vm_path]
                except docker.errors.NotFound:
                    logger.warning(f"Android VM {vm_path} not found, removing from registry")
                    if vm_path in self.vms:
                        del self.vms[vm_path]
        except Exception as e:
            logger.error(f"Error checking Android VMs: {e}")
        self.checked_and_cleaned = True

    def get_all_vm_paths(self) -> list:
        """Get all registered VM paths."""
        return list(self.vms.keys())