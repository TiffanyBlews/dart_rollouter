"""
Android-specific getters for evaluating Android GUI tasks.
"""

import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger("desktopenv.getter.android")


def get_current_app(env, *args) -> Dict[str, str]:
    """Get the currently focused app package and activity."""
    if hasattr(env.controller, 'get_current_app'):
        return env.controller.get_current_app()
    return {"package": None, "activity": None}


def get_ui_hierarchy(env, *args) -> str:
    """Get the current UI hierarchy XML."""
    if hasattr(env.controller, 'get_ui_hierarchy'):
        hierarchy = env.controller.get_ui_hierarchy()
        logger.debug("UI Hierarchy: %s", hierarchy)
        return hierarchy
    return ""


def get_platform_info(env, *args) -> Dict[str, Any]:
    """Get Android platform information."""
    if hasattr(env.controller, 'get_platform_info'):
        return env.controller.get_platform_info()
    return {"platform": "Android", "error": "get_platform_info not available"}


def get_screen_size(env, *args) -> Dict[str, int]:
    """Get Android screen size."""
    if hasattr(env.controller, 'get_screen_size'):
        return env.controller.get_screen_size()
    return {"width": 1080, "height": 1920}


def check_element_exists(ui_hierarchy: str, config: Dict) -> bool:
    """
    Check if an element exists in the UI hierarchy.

    Args:
        ui_hierarchy: The UI hierarchy XML string
        config: Config dict with 'text', 'resource_id', 'class', or 'content_desc' keys

    Returns:
        True if element exists, False otherwise
    """
    if not ui_hierarchy:
        return False

    text = config.get("text", "")
    resource_id = config.get("resource_id", "")
    class_name = config.get("class", "")
    content_desc = config.get("content_desc", "")

    if text and f'text="{text}"' in ui_hierarchy:
        return True
    if resource_id and f'resourceId="{resource_id}"' in ui_hierarchy:
        return True
    if class_name and f'class="{class_name}"' in ui_hierarchy:
        return True
    if content_desc and f'content-desc="{content_desc}"' in ui_hierarchy:
        return True

    return False


def get_element_text(ui_hierarchy: str, config: Dict) -> Optional[str]:
    """
    Get the text of a specific element from UI hierarchy.

    Args:
        ui_hierarchy: The UI hierarchy XML string
        config: Config dict with 'resource_id' or 'index' to identify element

    Returns:
        Element text if found, None otherwise
    """
    if not ui_hierarchy:
        return None

    resource_id = config.get("resource_id", "")
    index = config.get("index", 0)

    # Simple regex-based extraction
    if resource_id:
        pattern = f'resourceId="{resource_id}"[^>]*text="([^"]*)"'
        match = re.search(pattern, ui_hierarchy)
        if match:
            return match.group(1)

    return None


def parse_app_package(env, *args) -> str:
    """Parse current app package name from environment."""
    app_info = get_current_app(env)
    return app_info.get("package", "")


def parse_app_activity(env, *args) -> str:
    """Parse current app activity name from environment."""
    app_info = get_current_app(env)
    return app_info.get("activity", "")
