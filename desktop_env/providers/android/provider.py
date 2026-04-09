import logging
import time
import docker
import requests
import random
from typing import Optional, Dict

from desktop_env.providers.base import Provider

logger = logging.getLogger("desktopenv.providers.android.provider")

# Default ports for docker-android
DEFAULT_ADB_PORT = 5554
DEFAULT_APPIUM_PORT = 4723
DEFAULT_VNC_PORT = 6080

# Port range for concurrent containers
MIN_PORT = 5554
MAX_PORT = 5999


class AndroidProvider(Provider):
    """
    Provider for Android emulator via docker-android container.
    Manages docker container lifecycle and provides connection info.
    Supports concurrent containers with dynamic port allocation.
    """

    DOCKER_IMAGE = "budtmo/docker-android:emulator_11.0"

    # Class-level tracking for port allocation
    _used_ports: Dict[int, str] = {}  # port -> container_name
    _port_lock = False  # Simple lock for port allocation

    def __init__(self, region: str = None, instance_id: int = None):
        self.client = docker.from_env()
        self.container = None
        self.adb_port = None
        self.appium_port = None
        self.vnc_port = None
        self.container_name = None
        self.emulator_device = "Samsung Galaxy S10"
        self.os_type = "Android"
        self.instance_id = instance_id or random.randint(1000, 9999)

    def _allocate_ports(self) -> tuple:
        """Allocate unique ports for this container instance."""
        # Try to find available ports
        for base_port in range(MIN_PORT, MAX_PORT, 10):
            adb_port = base_port
            appium_port = base_port + 1
            vnc_port = base_port + 2

            # Check if ports are available
            ports_to_check = [adb_port, appium_port, vnc_port]
            available = True
            for p in ports_to_check:
                if p in AndroidProvider._used_ports:
                    available = False
                    break

            if available:
                AndroidProvider._used_ports[adb_port] = self.container_name
                AndroidProvider._used_ports[appium_port] = self.container_name
                AndroidProvider._used_ports[vnc_port] = self.container_name
                return adb_port, appium_port, vnc_port

        raise RuntimeError("No available ports for Android container")

    def _release_ports(self):
        """Release allocated ports."""
        if self.adb_port and self.adb_port in AndroidProvider._used_ports:
            del AndroidProvider._used_ports[self.adb_port]
        if self.appium_port and self.appium_port in AndroidProvider._used_ports:
            del AndroidProvider._used_ports[self.appium_port]
        if self.vnc_port and self.vnc_port in AndroidProvider._used_ports:
            del AndroidProvider._used_ports[self.vnc_port]

    def start_emulator(self, path_to_vm: str, headless: bool = False, os_type: str = "Android"):
        """
        Start docker-android container with Android emulator.

        Args:
            path_to_vm: VM identifier (container name or path)
            headless: Whether to run in headless mode
            os_type: Operating system type (Android)
        """
        # Generate unique container name if not provided
        if path_to_vm and not path_to_vm.startswith("android-"):
            container_name = f"android-{path_to_vm}-{self.instance_id}"
        else:
            container_name = path_to_vm or f"android-{int(time.time())}-{self.instance_id}"

        self.container_name = container_name

        # Check if container already exists and is running
        try:
            existing = self.client.containers.get(container_name)
            if existing.status == "running":
                logger.info(f"Container {container_name} is already running")
                self.container = existing
                self._update_port_info()
                return
            elif existing.status == "exited":
                logger.info(f"Restarting existing container {container_name}")
                existing.start()
                self.container = existing
                time.sleep(10)  # Wait longer for container to be ready
                self._update_port_info()
                return
        except docker.errors.NotFound:
            pass

        # Allocate ports
        self.adb_port, self.appium_port, self.vnc_port = self._allocate_ports()
        logger.info(f"Allocated ports - ADB: {self.adb_port}, Appium: {self.appium_port}, VNC: {self.vnc_port}")

        # Parse environment variables from path_to_vm if provided
        env_vars = {
            "EMULATOR_DEVICE": self.emulator_device,
            "WEB_VNC": "true",
            "APPIUM": "true",
        }

        # Build port bindings with allocated ports
        ports = {
            f"{self.vnc_port}/tcp": ("0.0.0.0", self.vnc_port),
            f"{self.appium_port}/tcp": ("0.0.0.0", self.appium_port),
            f"{self.adb_port}/tcp": ("0.0.0.0", self.adb_port),
            f"{self.adb_port + 1}/tcp": ("0.0.0.0", self.adb_port + 1),
        }

        try:
            logger.info(f"Starting new docker-android container: {container_name}")
            self.container = self.client.containers.run(
                self.DOCKER_IMAGE,
                detach=True,
                name=container_name,
                ports=ports,
                environment=env_vars,
                devices=["/dev/kvm:/dev/kvm"],
                privileged=True,
            )
            logger.info(f"Container started: {self.container.short_id}")

            # Wait for container to be ready
            time.sleep(20)  # Give emulator time to boot

            # Verify container is running
            self.container.reload()
            if self.container.status != "running":
                raise RuntimeError(f"Container failed to start, status: {self.container.status}")

            self._update_port_info()
            logger.info("Android emulator started successfully")

        except docker.errors.DockerException as e:
            logger.error(f"Failed to start docker-android container: {e}")
            raise

    def _update_port_info(self):
        """Update port information from container's actual port bindings."""
        if self.container is None:
            return

        self.container.reload()
        ports = self.container.ports

        # Update ports from container bindings using instance ports
        if self.adb_port and ports.get(f"{self.adb_port}/tcp"):
            pass  # Already set from allocation
        if self.appium_port and ports.get(f"{self.appium_port}/tcp"):
            pass  # Already set from allocation
        if self.vnc_port and ports.get(f"{self.vnc_port}/tcp"):
            pass  # Already set from allocation

        logger.info(f"Ports - ADB: {self.adb_port}, Appium: {self.appium_port}, VNC: {self.vnc_port}")

    def get_ip_address(self, path_to_vm: str = None) -> str:
        """
        Returns connection info as colon-separated string.
        Format: localhost:adb_port:appium_port:vnc_port
        """
        if self.container is None:
            raise RuntimeError("Container not started")

        # Get container IP for internal communication if needed
        self.container.reload()
        container_ip = self.container.attrs.get("NetworkSettings", {}).get("IPAddress", "localhost")

        return f"{container_ip}:{self.adb_port}:{self.appium_port}:{self.vnc_port}"

    def get_host_ip_address(self, path_to_vm: str = None) -> str:
        """Returns connection info for host machine access."""
        return f"localhost:{self.adb_port}:{self.appium_port}:{self.vnc_port}"

    def save_state(self, path_to_vm: str, snapshot_name: str):
        """
        Android emulator does not support snapshots via this interface.
        State saving would require AVD snapshot support which is limited.
        """
        raise NotImplementedError("Android snapshots not supported via this interface")

    def revert_to_snapshot(self, path_to_vm: str, snapshot_name: str):
        """
        Revert to snapshot by stopping and restarting the emulator.
        Note: This does not restore a saved state, just restarts the emulator.
        """
        logger.warning("Android revert_to_snapshot - restarting emulator (no snapshot restore)")
        if self.container:
            self.container.stop()
            time.sleep(2)
            self.container.start()
            time.sleep(20)  # Wait for emulator to boot

    def stop_emulator(self, path_to_vm: str = None):
        """Stop and remove the docker container."""
        if self.container:
            try:
                logger.info(f"Stopping Android emulator container: {self.container.name}")
                self.container.stop(timeout=10)
                self.container.remove()
                logger.info("Container stopped and removed")
            except docker.errors.NotFound:
                logger.warning("Container already removed")
            except Exception as e:
                logger.error(f"Error stopping container: {e}")
            finally:
                self.container = None

        # Release allocated ports
        self._release_ports()

    def is_emulator_ready(self, timeout: int = 60) -> bool:
        """Check if the emulator is booted and responsive via ADB."""
        if self.container is None:
            return False

        try:
            # Check container is running
            self.container.reload()
            if self.container.status != "running":
                return False

            # Check ADB connection with correct device
            import subprocess
            device_id = f"emulator-{self.adb_port}" if self.adb_port == 5554 else f"localhost:{self.adb_port}"
            result = subprocess.run(
                ["docker", "exec", self.container.name,
                 "/opt/android/platform-tools/adb", "-s", device_id, "shell", "getprop", "ro.build.version.release"],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                return True

            return False
        except Exception as e:
            logger.error(f"Error checking emulator readiness: {e}")
            return False

    def wait_for_emulator_ready(self, timeout: int = 120) -> bool:
        """Wait for emulator to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_emulator_ready():
                return True
            logger.info("Waiting for emulator to be ready...")
            time.sleep(5)
        return False