"""
Android action parsing utilities for DART-GUI.

This module provides utilities to parse model responses and convert them
to Android action format.
"""

import re
import logging

logger = logging.getLogger(__name__)


def parse_android_action(action_str):
    """
    Parse a model action string into an Android action dict.

    Supports formats like:
    - TAP(100, 200)
    - SWIPE(100, 200, 300, 400)
    - TYPE("hello world")
    - PRESS_KEY(HOME)
    - LAUNCH_APP("com.android.chrome")
    - PRESS_HOME()
    - PRESS_BACK()
    - WAIT()
    - DONE()
    - FAIL()
    """
    action_str = action_str.strip()

    # Done/Fail/Wait
    if action_str.upper() in ["DONE", "FAIL", "WAIT"]:
        return action_str.upper()

    # Tap
    match = re.match(r'TAP\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', action_str, re.IGNORECASE)
    if match:
        return {
            "action_type": "TAP",
            "parameters": {
                "x": int(match.group(1)),
                "y": int(match.group(2))
            }
        }

    # Long press
    match = re.match(r'LONG_PRESS\s*\(\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d+)\s*)?\)', action_str, re.IGNORECASE)
    if match:
        params = {"x": int(match.group(1)), "y": int(match.group(2))}
        if match.group(3):
            params["duration"] = int(match.group(3))
        return {"action_type": "LONG_PRESS", "parameters": params}

    # Swipe
    match = re.match(r'SWIPE\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d+)\s*)?\)', action_str, re.IGNORECASE)
    if match:
        params = {
            "start_x": int(match.group(1)),
            "start_y": int(match.group(2)),
            "end_x": int(match.group(3)),
            "end_y": int(match.group(4))
        }
        if match.group(5):
            params["duration"] = int(match.group(5))
        return {"action_type": "SWIPE", "parameters": params}

    # Type
    match = re.match(r'TYPE\s*\(\s*"([^"]*)"\s*\)', action_str, re.IGNORECASE)
    if match:
        return {
            "action_type": "TYPE",
            "parameters": {"text": match.group(1)}
        }
    match = re.match(r"TYPE\s*\(\s*'([^']*)'\s*\)", action_str, re.IGNORECASE)
    if match:
        return {
            "action_type": "TYPE",
            "parameters": {"text": match.group(1)}
        }

    # Press key
    match = re.match(r'PRESS_KEY\s*\(\s*(\w+)\s*\)', action_str, re.IGNORECASE)
    if match:
        return {
            "action_type": "PRESS_KEY",
            "parameters": {"key": match.group(1).upper()}
        }

    # Launch app
    match = re.match(r'LAUNCH_APP\s*\(\s*"([^"]+)"\s*(?:,\s*"([^"]*)"\s*)?\)', action_str, re.IGNORECASE)
    if match:
        params = {"package": match.group(1)}
        if match.group(2):
            params["activity"] = match.group(2)
        return {"action_type": "LAUNCH_APP", "parameters": params}

    # Press home/back
    match = re.match(r'PRESS_HOME\s*\(\s*\)', action_str, re.IGNORECASE)
    if match:
        return {"action_type": "PRESS_HOME", "parameters": {}}

    match = re.match(r'PRESS_BACK\s*\(\s*\)', action_str, re.IGNORECASE)
    if match:
        return {"action_type": "PRESS_BACK", "parameters": {}}

    # Open notification
    match = re.match(r'OPEN_NOTIFICATION\s*\(\s*\)', action_str, re.IGNORECASE)
    if match:
        return {"action_type": "OPEN_NOTIFICATION", "parameters": {}}

    logger.warning(f"Could not parse Android action: {action_str}")
    return None


def parse_response_to_android_action(response, image_size=None):
    """
    Parse model response text and extract Android action.

    Args:
        response: Model output text containing action
        image_size: Tuple of (width, height) - not used for Android but kept for API compatibility

    Returns:
        Android action dict or 'WAIT', 'DONE', 'FAIL' string
    """
    response = response.strip()

    # Extract action from response
    if "Action:" in response:
        action_str = response.split("Action:")[-1].strip()
        # Take first line of action
        action_str = action_str.split("\n")[0].strip()
    else:
        action_str = response.strip()

    # Try to parse
    action = parse_android_action(action_str)
    if action:
        return action

    # Default to WAIT if cannot parse
    return "WAIT"


def convert_pyautogui_to_android(pyautogui_action):
    """
    Convert a pyautogui action string to Android format.
    This is a best-effort conversion for common actions.

    Args:
        pyautogui_action: String like "pyautogui.click(100, 200)" or
                         dict like {"action_type": "TAP", ...}

    Returns:
        Android action dict
    """
    if isinstance(pyautogui_action, dict):
        action_type = pyautogui_action.get("action_type", "").upper()
        if action_type == "TAP":
            return {
                "action_type": "TAP",
                "parameters": {
                    "x": pyautogui_action.get("x", 0),
                    "y": pyautogui_action.get("y", 0)
                }
            }
        elif action_type == "CLICK":
            return {
                "action_type": "TAP",
                "parameters": {
                    "x": pyautogui_action.get("x", 0),
                    "y": pyautogui_action.get("y", 0)
                }
            }
        elif action_type == "TYPE":
            return {
                "action_type": "TYPE",
                "parameters": {"text": pyautogui_action.get("text", "")}
            }
        elif action_type in ["DONE", "FAIL", "WAIT"]:
            return action_type

    if isinstance(pyautogui_action, str):
        # Try to parse pyautogui.click(x, y) format
        match = re.match(r'pyautogui\.click\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', pyautogui_action)
        if match:
            return {
                "action_type": "TAP",
                "parameters": {
                    "x": int(match.group(1)),
                    "y": int(match.group(2))
                }
            }

        # pyautogui.typewrite("text")
        match = re.match(r'pyautogui\.typewrite\s*\(\s*"([^"]*)"\s*\)', pyautogui_action)
        if match:
            return {
                "action_type": "TYPE",
                "parameters": {"text": match.group(1)}
            }

        # pyautogui.press("key")
        match = re.match(r'pyautogui\.press\s*\(\s*"(\w+)"\s*\)', pyautogui_action)
        if match:
            key = match.group(1).upper()
            # Map common keys
            if key == "RETURN":
                key = "ENTER"
            elif key == "ESCAPE":
                key = "BACK"
            return {
                "action_type": "PRESS_KEY",
                "parameters": {"key": key}
            }

    # Default to WAIT
    return "WAIT"
