"""
Android action space definition for GUI agent training.
"""

# Android screen resolution (default, actual may vary)
X_MAX = 1080
Y_MAX = 1920

ANDROID_KEYS = [
    "HOME", "BACK", "ENTER", "SEARCH", "MENU",
    "VOLUME_UP", "VOLUME_DOWN", "POWER", "CAMERA",
    "DELETE", "TAB"
]

ANDROID_ACTION_SPACE = [
    {
        "action_type": "TAP",
        "note": "Tap at the specified coordinates",
        "parameters": {
            "x": {
                "type": int,
                "range": [0, X_MAX],
                "optional": False,
                "description": "X coordinate"
            },
            "y": {
                "type": int,
                "range": [0, Y_MAX],
                "optional": False,
                "description": "Y coordinate"
            }
        }
    },
    {
        "action_type": "LONG_PRESS",
        "note": "Long press at the specified coordinates",
        "parameters": {
            "x": {
                "type": int,
                "range": [0, X_MAX],
                "optional": False,
                "description": "X coordinate"
            },
            "y": {
                "type": int,
                "range": [0, Y_MAX],
                "optional": False,
                "description": "Y coordinate"
            },
            "duration": {
                "type": int,
                "range": [500, 3000],
                "optional": True,
                "default": 1000,
                "description": "Press duration in milliseconds"
            }
        }
    },
    {
        "action_type": "SWIPE",
        "note": "Swipe from start to end coordinates",
        "parameters": {
            "start_x": {
                "type": int,
                "range": [0, X_MAX],
                "optional": False,
                "description": "Start X coordinate"
            },
            "start_y": {
                "type": int,
                "range": [0, Y_MAX],
                "optional": False,
                "description": "Start Y coordinate"
            },
            "end_x": {
                "type": int,
                "range": [0, X_MAX],
                "optional": False,
                "description": "End X coordinate"
            },
            "end_y": {
                "type": int,
                "range": [0, Y_MAX],
                "optional": False,
                "description": "End Y coordinate"
            },
            "duration": {
                "type": int,
                "range": [100, 2000],
                "optional": True,
                "default": 500,
                "description": "Swipe duration in milliseconds"
            }
        }
    },
    {
        "action_type": "TYPE",
        "note": "Type text into the currently focused input field",
        "parameters": {
            "text": {
                "type": str,
                "range": None,
                "optional": False,
                "description": "Text to type"
            }
        }
    },
    {
        "action_type": "CLEAR_INPUT",
        "note": "Clear the currently focused input field",
        "parameters": {}
    },
    {
        "action_type": "PRESS_KEY",
        "note": "Press an Android system key",
        "parameters": {
            "key": {
                "type": str,
                "range": ANDROID_KEYS,
                "optional": False,
                "description": "Android key name (HOME, BACK, ENTER, etc.)"
            }
        }
    },
    {
        "action_type": "PRESS_HOME",
        "note": "Press the HOME button",
        "parameters": {}
    },
    {
        "action_type": "PRESS_BACK",
        "note": "Press the BACK button",
        "parameters": {}
    },
    {
        "action_type": "LAUNCH_APP",
        "note": "Launch an app by package name",
        "parameters": {
            "package": {
                "type": str,
                "range": None,
                "optional": False,
                "description": "App package name (e.g., com.android.chrome)"
            },
            "activity": {
                "type": str,
                "range": None,
                "optional": True,
                "description": "Activity name (optional)"
            }
        }
    },
    {
        "action_type": "OPEN_NOTIFICATION",
        "note": "Open the notification shade",
        "parameters": {}
    },
    {
        "action_type": "WAIT",
        "note": "Wait for the screen to settle before next action",
        "parameters": {}
    },
    {
        "action_type": "DONE",
        "note": "Task has been completed successfully",
        "parameters": {}
    },
    {
        "action_type": "FAIL",
        "note": "Task cannot be completed",
        "parameters": {}
    }
]


def get_android_action_space():
    """Return the Android action space definition."""
    return ANDROID_ACTION_SPACE


def format_android_action_prompt():
    """Format the Android action space for use in prompts."""
    prompt = """You are an Android GUI agent. You can perform the following actions:

## Available Actions

### TAP
Tap at a specific coordinate on the screen.
Parameters: x (int, 0-{}), y (int, 0-{})

### LONG_PRESS
Long press at coordinates to trigger context menu or selection.
Parameters: x, y, duration (optional, default 1000ms)

### SWIPE
Swipe from one position to another (for scrolling, swiping through content).
Parameters: start_x, start_y, end_x, end_y, duration (optional)

### TYPE
Type text into the currently focused input field.
Parameters: text (string)

### CLEAR_INPUT
Clear text from the currently focused input field.
Parameters: none

### PRESS_KEY
Press an Android system key.
Parameters: key (HOME, BACK, ENTER, SEARCH, MENU, VOLUME_UP, VOLUME_DOWN, POWER, CAMERA, DELETE, TAB)

### PRESS_HOME
Press the HOME button to go to the home screen.
Parameters: none

### PRESS_BACK
Press the BACK button to go back.
Parameters: none

### LAUNCH_APP
Launch an app by its package name.
Parameters: package (e.g., "com.android.chrome"), activity (optional)

### OPEN_NOTIFICATION
Open the notification shade to see notifications.
Parameters: none

### WAIT
Wait for the screen to settle before next action.
Parameters: none

### DONE
The task has been completed successfully.
Parameters: none

### FAIL
The task cannot be completed.
Parameters: none

## UI Information
You will receive the current screen screenshot and UI hierarchy (XML format).
Use this information to identify interactive elements and their positions.

## Important Notes
- Always provide coordinates for TAP, LONG_PRESS, and SWIPE actions
- Use PRESS_HOME or PRESS_BACK for navigation
- Use TYPE to input text into input fields
- Use SWIPE to scroll or navigate through content
- Before typing, you may need to TAP on the input field to focus it
""".format(X_MAX, Y_MAX)

    return prompt
