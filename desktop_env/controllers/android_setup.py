"""
Android-specific setup controller.

Handles task setup operations for Android environments like
launching apps, going home, clearing app data, etc.
"""

import logging
import time
from typing import Dict, Any, List

logger = logging.getLogger("desktopenv.setup.android")


class AndroidSetupController:
    """
    Setup controller for Android environments.
    Handles task configuration like launching apps, navigating home, etc.
    """

    def __init__(self, controller):
        """
        Args:
            controller: AndroidADBController instance
        """
        self.controller = controller

    def setup(self, config: List[Dict[str, Any]]) -> bool:
        """
        Execute setup configuration for Android.

        Args:
            config: List of config dicts with 'type' and 'parameters'

        Returns:
            True if all setup steps succeeded
        """
        if not config:
            logger.info("No Android setup config provided")
            return True

        for i, cfg in enumerate(config):
            config_type = cfg.get("type", "")
            parameters = cfg.get("parameters", {})

            setup_function = f"_{config_type}_setup"
            if not hasattr(self, setup_function):
                logger.warning(f"Android setup: unknown config type '{config_type}', skipping")
                continue

            try:
                logger.info(f"Executing Android setup step {i+1}/{len(config)}: {config_type}")
                getattr(self, setup_function)(**parameters)
                logger.info(f"ANDROID SETUP COMPLETED: {config_type}({parameters})")
                # Give the system time to settle after each action
                time.sleep(1)
            except Exception as e:
                logger.error(f"Android setup failed at step {i+1}: {config_type} - {e}")
                return False

        return True

    def _launch_app_setup(self, package: str = None, activity: str = None, **kwargs):
        """Launch an Android app by package name."""
        if not package:
            logger.warning("launch_app_setup: no package specified")
            return

        logger.info(f"Launching app: {package}")
        if activity:
            self.controller.launch_app(package, activity)
        else:
            self.controller.launch_app(package)
        time.sleep(2)  # Wait for app to launch

    def _press_home_setup(self, **kwargs):
        """Press HOME button."""
        logger.info("Pressing HOME button")
        self.controller.press_home()
        time.sleep(1)

    def _press_back_setup(self, **kwargs):
        """Press BACK button."""
        logger.info("Pressing BACK button")
        self.controller.press_back()
        time.sleep(0.5)

    def _open_notification_setup(self, **kwargs):
        """Open notification shade."""
        logger.info("Opening notifications")
        self.controller.open_notification()
        time.sleep(1)

    def _swipe_up_setup(self, **kwargs):
        """Swipe up from bottom to go home."""
        # Assuming 1080x1920 screen, swipe from center bottom to center
        logger.info("Swiping up to go home")
        self.controller.swipe(540, 1500, 540, 500, duration=500)
        time.sleep(1)

    def _swipe_down_setup(self, **kwargs):
        """Swipe down from top."""
        logger.info("Swiping down")
        self.controller.swipe(540, 100, 540, 1000, duration=500)
        time.sleep(1)

    def _clear_app_data_setup(self, package: str = None, **kwargs):
        """
        Clear app data (requires root or special permissions).
        Note: This may not work without root.
        """
        if not package:
            logger.warning("clear_app_data_setup: no package specified")
            return

        logger.info(f"Clearing app data for: {package}")
        # This would require ADB root or shell permissions
        # Most docker-android containers have root access
        import subprocess
        subprocess.run(
            ["adb", "-s", self.controller.device_id, "shell", "pm", "clear", package],
            capture_output=True
        )
        time.sleep(1)

    def _stop_app_setup(self, package: str = None, **kwargs):
        """Force stop an app."""
        if not package:
            logger.warning("stop_app_setup: no package specified")
            return

        logger.info(f"Stopping app: {package}")
        import subprocess
        subprocess.run(
            ["adb", "-s", self.controller.device_id, "shell", "am", "force-stop", package],
            capture_output=True
        )
        time.sleep(1)

    def _open_url_setup(self, url: str = None, **kwargs):
        """Open a URL in the default browser."""
        if not url:
            logger.warning("open_url_setup: no URL specified")
            return

        logger.info(f"Opening URL: {url}")
        import subprocess
        subprocess.run(
            ["adb", "-s", self.controller.device_id, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url],
            capture_output=True
        )
        time.sleep(2)

    def _type_text_setup(self, text: str = None, **kwargs):
        """Type text into the focused input field."""
        if not text:
            logger.warning("type_text_setup: no text specified")
            return

        logger.info(f"Typing text: {text}")
        self.controller.type_text(text)
        time.sleep(0.5)

    def _wait_setup(self, duration: int = 2, **kwargs):
        """Wait for a specified duration."""
        logger.info(f"Waiting for {duration} seconds")
        time.sleep(duration)

    def reset_state(self):
        """
        Reset Android state to a clean home state.
        Used between tasks for RL training to ensure clean slate.
        This is a best-effort reset since Android doesn't support VM snapshots.
        """
        logger.info("Resetting Android state to home...")

        # Press HOME to go back
        self.controller.press_home()
        time.sleep(1)

        # Open notification to dismiss any overlays
        try:
            self.controller.open_notification()
            time.sleep(0.5)
            self.controller.press_back()
        except:
            pass

        # Press HOME again
        self.controller.press_home()
        time.sleep(1)

        # Stop all recent apps (swipe up from bottom, then tap X)
        # Note: This is device-specific and may not work on all Android versions
        try:
            # Go home first
            self.controller.press_home()
            time.sleep(0.5)

            # Try to open recent apps (usually done by swiping up from bottom)
            self.controller.swipe(540, 1800, 540, 600, duration=300)
            time.sleep(1)

            # Tap "Clear all" or similar if available
            # This is heuristic-based
        except Exception as e:
            logger.warning(f"Could not clear recent apps: {e}")

        logger.info("Android state reset complete")


def create_android_setup_controller(controller) -> AndroidSetupController:
    """Factory function to create AndroidSetupController."""
    return AndroidSetupController(controller)
