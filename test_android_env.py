#!/usr/bin/env python3
"""
Test script for Android environment in DART-GUI.

Usage:
    # Start a docker-android container first:
    docker run -d --name android-test -p 5554:5554 -p 4723:4723 -p 6080:6080 budtmo/docker-android:emulator_11.0

    # Run this test:
    python3 test_android_env.py
"""

import sys
import time
sys.path.insert(0, '.')

from desktop_env.desktop_env import DesktopEnv
from desktop_env.controllers.android_adb import AndroidADBController


def test_android_controller():
    """Test AndroidADBController directly."""
    print("\n=== Testing AndroidADBController ===")

    controller = AndroidADBController(
        adb_port=5554,
        device_id="emulator-5554"
    )

    # Test screenshot
    print("Getting screenshot...")
    screenshot = controller.get_screenshot()
    if screenshot:
        print(f"  Screenshot OK: {len(screenshot)} bytes")
    else:
        print("  ERROR: Failed to get screenshot")
        return False

    # Test UI hierarchy
    print("Getting UI hierarchy...")
    hierarchy = controller.get_ui_hierarchy()
    if hierarchy:
        print(f"  UI hierarchy OK: {len(hierarchy)} chars")
    else:
        print("  WARNING: Failed to get UI hierarchy")

    # Test platform info
    print("Getting platform info...")
    info = controller.get_platform_info()
    print(f"  Platform info: {info}")

    # Test tap action
    print("Testing TAP action...")
    if controller.tap(540, 960):
        print("  TAP OK")
    else:
        print("  WARNING: TAP may have failed")

    return True


def test_android_desktop_env():
    """Test DesktopEnv with Android configuration."""
    print("\n=== Testing DesktopEnv (Android) ===")

    try:
        env = DesktopEnv(
            provider_name="android_docker",
            action_space="android",
            os_type="Android",
            headless=False,
        )
        print("DesktopEnv created successfully!")
        print(f"  Provider: {env.provider}")
        print(f"  Controller type: {type(env.controller).__name__}")
        print(f"  OS type: {env.os_type}")

        # Test reset without task (just to check observation)
        print("\nGetting initial observation...")
        obs = env._get_obs()
        print(f"  Observation keys: {obs.keys()}")
        if 'screenshot' in obs:
            print(f"  Screenshot: {len(obs['screenshot'])} bytes")
        if 'accessibility_tree' in obs:
            at = obs['accessibility_tree']
            if at:
                print(f"  accessibility_tree: {len(at)} chars")
            else:
                print("  accessibility_tree: None")

        # Close env
        env.close()
        print("\nDesktopEnv test passed!")
        return True

    except Exception as e:
        print(f"DesktopEnv test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("Android Environment Test for DART-GUI")
    print("=" * 60)

    # Check if docker container is running
    import subprocess
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=android", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    container_name = result.stdout.strip()

    if not container_name:
        print("\nNo docker-android container running.")
        print("Please start one with:")
        print("  docker run -d --name android-test -p 5554:5554 -p 4723:4723 -p 6080:6080 budtmo/docker-android:emulator_11.0")
        print("\nFalling back to controller-only test...")
        return test_android_controller()
    else:
        print(f"\nUsing docker container: {container_name}")

        # Wait for emulator to be ready
        print("Waiting for emulator to be ready...")
        time.sleep(5)

        return test_android_desktop_env()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
