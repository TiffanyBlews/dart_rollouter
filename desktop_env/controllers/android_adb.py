"""
Android controller using ADB directly (no Appium required).

This provides a fallback controller for Android emulators when Appium
is not properly configured. It uses ADB commands for interaction.
"""

import base64
import logging
import subprocess
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("desktopenv.androidcontroller.adb")

ANDROID_KEYCODES = {
    "HOME": "KEYCODE_HOME",
    "BACK": "KEYCODE_BACK",
    "ENTER": "KEYCODE_ENTER",
    "SEARCH": "KEYCODE_SEARCH",
    "MENU": "KEYCODE_MENU",
    "VOLUME_UP": "KEYCODE_VOLUME_UP",
    "VOLUME_DOWN": "KEYCODE_VOLUME_DOWN",
    "POWER": "KEYCODE_POWER",
    "CAMERA": "KEYCODE_CAMERA",
    "DELETE": "KEYCODE_DEL",
    "TAB": "KEYCODE_TAB",
}


class AndroidADBController:
    """
    Controller for Android emulator using ADB commands directly.
    This is a fallback when Appium is not available.
    """

    def __init__(
        self,
        vm_ip: str = "localhost",
        adb_port: int = 5554,
        device_id: str = None,
        retry_times: int = 3,
        retry_interval: int = 5,
        docker_container: str = None,
    ):
        """
        Initialize Android controller with ADB.

        Args:
            vm_ip: IP address of the docker host (not used directly)
            adb_port: ADB port of the emulator
            device_id: Specific device ID to use (overrides adb_port)
            retry_times: Number of retries for failed operations
            retry_interval: Interval between retries
            docker_container: Name of docker container for docker-android (if ADB is inside docker)
        """
        self.adb_port = adb_port
        self.device_id = device_id or f"emulator-{adb_port}"
        self.retry_times = retry_times
        self.retry_interval = retry_interval
        self._adb_path = None
        self.docker_container = docker_container

    @property
    def adb_path(self) -> str:
        """Get ADB executable path."""
        if self._adb_path:
            return self._adb_path

        # Try common locations
        paths = [
            "/opt/platform-tools/adb",
            "/usr/bin/adb",
            "/usr/local/bin/adb",
            "adb",  # Rely on PATH
        ]
        for p in paths:
            try:
                subprocess.run([p, "version"], capture_output=True, timeout=5)
                self._adb_path = p
                return p
            except (subprocess.SubprocessError, FileNotFoundError):
                continue

        self._adb_path = "adb"  # Fallback to PATH
        return self._adb_path

    def _run_adb(self, *args, timeout: int = 30, binary: bool = False) -> subprocess.CompletedProcess:
        """Run an ADB command either locally or inside docker container."""
        if self.docker_container:
            # Run ADB inside the docker container
            cmd = ["docker", "exec", self.docker_container,
                   "/opt/android/platform-tools/adb", "-s", self.device_id] + list(args)
        else:
            cmd = [self.adb_path, "-s", self.device_id] + list(args)

        if binary:
            return subprocess.run(cmd, capture_output=True, timeout=timeout)
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def get_screenshot(self) -> Optional[bytes]:
        """Take screenshot using ADB."""
        for _ in range(self.retry_times):
            try:
                result = self._run_adb("exec-out", "screencap", "-p", binary=True)
                if result.returncode == 0 and result.stdout:
                    return result.stdout  # Binary data already
                logger.error(f"Failed to take screenshot: {result.stderr}")
            except Exception as e:
                logger.error(f"Error taking screenshot: {e}")
            time.sleep(self.retry_interval)
        return None

    def get_ui_hierarchy(self) -> Optional[str]:
        """
        Get UI hierarchy using uiautomator dump.
        Note: Requires UIautomator2 to be available on the device.
        """
        for _ in range(self.retry_times):
            try:
                # Use uiautomator to dump the UI hierarchy
                result = self._run_adb("shell", "uiautomator", "dump", "/sdcard/ui_dump.xml")
                if result.returncode != 0:
                    # Try alternative method
                    result = self._run_adb("shell", "dump", "window", "hierarchy")
                    if result.returncode == 0:
                        return result.stdout

                # Read the dump file
                result = self._run_adb("shell", "cat", "/sdcard/ui_dump.xml")
                if result.returncode == 0:
                    # Clean up
                    self._run_adb("shell", "rm", "/sdcard/ui_dump.xml")
                    return result.stdout
            except Exception as e:
                logger.error(f"Error getting UI hierarchy: {e}")
            time.sleep(self.retry_interval)
        return None

    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information via ADB."""
        try:
            result = self._run_adb("shell", "getprop", "ro.build.version.release")
            version = result.stdout.strip() if result.returncode == 0 else "Unknown"

            result = self._run_adb("shell", "getprop", "ro.product.model")
            model = result.stdout.strip() if result.returncode == 0 else "Unknown"

            result = self._run_adb("shell", "getprop", "ro.product.device")
            device = result.stdout.strip() if result.returncode == 0 else "Unknown"

            return {
                "platform": "Android",
                "platform_version": version,
                "device_name": f"{model} ({device})",
            }
        except Exception as e:
            logger.error(f"Error getting platform info: {e}")
            return {"platform": "Android", "error": str(e)}

    def get_screen_size(self) -> Dict[str, int]:
        """Get screen size using WM size."""
        try:
            result = self._run_adb("shell", "wm", "size")
            if result.returncode == 0:
                # Parse output like "Physical size: 1080x1920"
                output = result.stdout.strip()
                if "x" in output:
                    parts = output.split("x")[-1].split()
                    if len(parts) >= 2:
                        width = int(parts[0])
                        height = int(parts[1])
                        return {"width": width, "height": height}
        except Exception as e:
            logger.error(f"Error getting screen size: {e}")
        return {"width": 1080, "height": 1920}  # Default fallback

    # Action methods
    def tap(self, x: int, y: int) -> bool:
        """Tap at coordinates."""
        try:
            result = self._run_adb("shell", "input", "tap", str(x), str(y))
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error tapping: {e}")
            return False

    def long_press(self, x: int, y: int, duration: int = 1000) -> bool:
        """Long press at coordinates."""
        try:
            # Use swipe with same start/end point for long press
            result = self._run_adb(
                "shell", "input", "swipe",
                str(x), str(y), str(x), str(y), str(duration)
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error long pressing: {e}")
            return False

    def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: int = 500
    ) -> bool:
        """Swipe from start to end."""
        try:
            result = self._run_adb(
                "shell", "input", "swipe",
                str(start_x), str(start_y), str(end_x), str(end_y), str(duration)
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error swiping: {e}")
            return False

    def type_text(self, text: str) -> bool:
        """Type text."""
        try:
            # Escape special characters
            text = text.replace(" ", "%s")
            result = self._run_adb("shell", "input", "text", text)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return False

    def press_key(self, key: str) -> bool:
        """Press an Android key."""
        try:
            keycode = ANDROID_KEYCODES.get(key.upper())
            if not keycode:
                logger.error(f"Unknown key: {key}")
                return False
            result = self._run_adb("shell", "input", "keyevent", keycode)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error pressing key: {e}")
            return False

    def launch_app(self, package: str, activity: str = None) -> bool:
        """Launch an app by package name."""
        try:
            if activity:
                result = self._run_adb(
                    "shell", "am", "start", "-n", f"{package}/{activity}"
                )
            else:
                # Try to start the main activity
                result = self._run_adb(
                    "shell", "monkey", "-p", package, "-c",
                    "android.intent.category.LAUNCHER", "1"
                )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error launching app: {e}")
            return False

    def press_home(self) -> bool:
        """Press HOME button."""
        return self.press_key("HOME")

    def press_back(self) -> bool:
        """Press BACK button."""
        return self.press_key("BACK")

    def open_notification(self) -> bool:
        """Open notification shade."""
        try:
            result = self._run_adb("shell", "cmd", "statusbar", "expand-notifications")
            return result.returncode == 0
        except Exception:
            # Fallback method
            try:
                result = self._run_adb("shell", "input", "swipe", "540", "100", "540", "1800")
                return result.returncode == 0
            except Exception as e:
                logger.error(f"Error opening notifications: {e}")
                return False

    def get_current_app(self) -> Dict[str, str]:
        """Get the currently focused app package and activity."""
        try:
            result = self._run_adb("shell", "dumpsys", "activity", "activities")
            if result.returncode == 0:
                # Parse the output to find the current activity
                for line in result.stdout.split("\n"):
                    if "mResumedActivity" in line or "mFocusedActivity" in line:
                        # Extract package/activity
                        parts = line.split()[-1].split("/")
                        if len(parts) >= 2:
                            return {"package": parts[0], "activity": parts[1]}
        except Exception as e:
            logger.error(f"Error getting current app: {e}")
        return {"package": None, "activity": None}

    def execute_action(self, action: Any) -> None:
        """Execute an action dict."""
        if action in ['WAIT', 'FAIL', 'DONE']:
            return

        if isinstance(action, str):
            if action == 'WAIT':
                time.sleep(2)
            return

        action_type = action.get("action_type") if isinstance(action, dict) else None
        parameters = action.get("parameters", {}) if isinstance(action, dict) else {}

        if action_type is None:
            return

        if action_type == "TAP":
            self.tap(parameters.get("x", 0), parameters.get("y", 0))
        elif action_type == "LONG_PRESS":
            self.long_press(
                parameters.get("x", 0),
                parameters.get("y", 0),
                parameters.get("duration", 1000)
            )
        elif action_type == "SWIPE":
            self.swipe(
                parameters.get("start_x", 0),
                parameters.get("start_y", 0),
                parameters.get("end_x", 0),
                parameters.get("end_y", 0),
                parameters.get("duration", 500)
            )
        elif action_type == "TYPE":
            self.type_text(parameters.get("text", ""))
        elif action_type == "PRESS_KEY":
            self.press_key(parameters.get("key", ""))
        elif action_type == "LAUNCH_APP":
            self.launch_app(
                parameters.get("package", ""),
                parameters.get("activity")
            )
        elif action_type == "OPEN_NOTIFICATION":
            self.open_notification()
        elif action_type == "PRESS_HOME":
            self.press_home()
        elif action_type == "PRESS_BACK":
            self.press_back()
        elif action_type in ["WAIT", "DONE", "FAIL"]:
            pass  # No-op
        else:
            logger.warning(f"Unknown action type: {action_type}")

    def close(self):
        """Cleanup - nothing to do for ADB controller."""
        pass