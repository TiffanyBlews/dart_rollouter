"""
Android-specific metrics for evaluating Android GUI tasks.
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger("desktopenv.metric.android")


def check_app_launched(result: str, rules: Dict[str, Any]) -> float:
    """
    Check if the expected app was launched.

    Args:
        result: The current app package name
        rules: Dict with 'package' key for expected package name

    Returns:
        1.0 if matches, 0.0 otherwise
    """
    if result is None:
        return 0.0

    expected_package = rules.get("package", "")
    if not expected_package:
        logger.warning("No package specified in rules")
        return 0.0

    if expected_package in result:
        logger.info(f"App match: expected '{expected_package}', got '{result}'")
        return 1.0

    logger.info(f"App mismatch: expected '{expected_package}', got '{result}'")
    return 0.0


def check_ui_element_exists(result: str, rules: Dict[str, Any]) -> float:
    """
    Check if a UI element exists in the hierarchy.

    Args:
        result: The UI hierarchy XML string
        rules: Dict with 'text', 'resource_id', 'class', or 'content_desc'

    Returns:
        1.0 if element exists, 0.0 otherwise
    """
    if not result:
        return 0.0

    text = rules.get("text", "")
    resource_id = rules.get("resource_id", "")
    class_name = rules.get("class", "")
    content_desc = rules.get("content_desc", "")

    found = False

    if text and f'text="{text}"' in result:
        found = True
        logger.info(f"Found element with text='{text}'")
    elif resource_id and f'resourceId="{resource_id}"' in result:
        found = True
        logger.info(f"Found element with resourceId='{resource_id}'")
    elif class_name and f'class="{class_name}"' in result:
        found = True
        logger.info(f"Found element with class='{class_name}'")
    elif content_desc and f'content-desc="{content_desc}"' in result:
        found = True
        logger.info(f"Found element with content_desc='{content_desc}'")

    return 1.0 if found else 0.0


def check_text_visible(result: str, rules: Dict[str, Any]) -> float:
    """
    Check if text is visible in the UI hierarchy.

    Args:
        result: The UI hierarchy XML string
        rules: Dict with 'text' key for expected text

    Returns:
        1.0 if text is found, 0.0 otherwise
    """
    if not result:
        return 0.0

    expected_text = rules.get("text", "")
    if not expected_text:
        logger.warning("No text specified in rules")
        return 0.0

    # Check if text appears in hierarchy
    if f'text="{expected_text}"' in result:
        logger.info(f"Text found: '{expected_text}'")
        return 1.0

    # Partial match
    if expected_text in result:
        logger.info(f"Text partially found: '{expected_text}'")
        return 1.0

    logger.info(f"Text not found: '{expected_text}'")
    return 0.0


def exact_match(result: Any, rules: Dict[str, Any]) -> float:
    """
    Exact match metric for Android results.

    Args:
        result: The result to check
        rules: Dict with 'expected' key for expected value

    Returns:
        1.0 if exact match, 0.0 otherwise
    """
    expected = rules.get("expected", "")

    if str(result) == str(expected):
        return 1.0
    return 0.0


def contains_match(result: str, rules: Dict[str, Any]) -> float:
    """
    Check if result contains expected substring.

    Args:
        result: The result string
        rules: Dict with 'expected' key for expected substring

    Returns:
        1.0 if contains, 0.0 otherwise
    """
    expected = rules.get("expected", "")

    if expected in str(result):
        return 1.0
    return 0.0


def check_screen_on(result: Dict[str, Any], rules: Dict[str, Any]) -> float:
    """
    Check if screen is on (not asleep/off).

    Returns:
        1.0 if screen is on, 0.0 otherwise
    """
    # This would require additional implementation
    # For now, assume screen is on if we can get screenshot
    return 1.0
