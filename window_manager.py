#!/usr/bin/env python3
"""
Windows window management and text insertion for Dictate app.

Features:
- Rule-based paste key selection (configured in paste_rules.json)
- Window class/title detection via Win32 APIs
- Clipboard paste using pynput key simulation
"""

import json
import time
import ctypes
from ctypes import wintypes
from pathlib import Path

# Load paste rules from configuration file
PASTE_RULES_PATH = Path(__file__).parent / "paste_rules.json"
_paste_rules_cache = None

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.GetForegroundWindow.restype = wintypes.HWND
_user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
_user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.SetForegroundWindow.argtypes = [wintypes.HWND]
_user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.IsWindow.argtypes = [wintypes.HWND]

SW_RESTORE = 9


def load_paste_rules():
    """
    Load paste rules from paste_rules.json

    Returns:
        dict: Paste rules configuration with 'default_paste_key' and 'app_rules'
    """
    global _paste_rules_cache

    # Return cached rules if already loaded
    if _paste_rules_cache is not None:
        return _paste_rules_cache

    # Default fallback if file doesn't exist
    default_rules = {
        "default_paste_key": "ctrl+v",
        "app_rules": []
    }

    if not PASTE_RULES_PATH.exists():
        print(f"Paste rules file not found: {PASTE_RULES_PATH}")
        print("Using default: ctrl+v for all apps")
        _paste_rules_cache = default_rules
        return _paste_rules_cache

    try:
        with open(PASTE_RULES_PATH, 'r', encoding='utf-8') as f:
            rules = json.load(f)

        # Validate required keys
        if "default_paste_key" not in rules:
            rules["default_paste_key"] = "ctrl+v"
        if "app_rules" not in rules:
            rules["app_rules"] = []

        _paste_rules_cache = rules
        print(f"Loaded {len(rules['app_rules'])} paste rules from {PASTE_RULES_PATH}")
        return _paste_rules_cache

    except json.JSONDecodeError as e:
        print(f"Paste rules file corrupt: {e}")
        print("Using default: ctrl+v for all apps")
        _paste_rules_cache = default_rules
        return _paste_rules_cache
    except Exception as e:
        print(f"Error loading paste rules: {e}")
        print("Using default: ctrl+v for all apps")
        _paste_rules_cache = default_rules
        return _paste_rules_cache


def get_paste_key_for_window(window_id):
    """
    Determine the correct paste key for a window based on paste rules

    Args:
        window_id (int): Window handle

    Returns:
        str: Paste key to use (e.g., 'ctrl+v', 'ctrl+shift+v')
    """
    rules = load_paste_rules()
    default_key = rules.get("default_paste_key", "ctrl+v")

    if not window_id:
        return default_key

    # Get window class and title for matching
    window_class = get_window_class(window_id).lower()
    window_title = get_window_title(window_id).lower()

    # Check each rule in order
    for rule in rules.get("app_rules", []):
        # Check window_class match
        rule_classes = [cls.lower() for cls in rule.get("window_class", [])]
        if rule_classes and window_class not in rule_classes:
            continue  # Window class doesn't match, skip this rule

        # Check title_contains (all must match)
        title_contains = rule.get("title_contains", [])
        if title_contains:
            if not all(phrase.lower() in window_title for phrase in title_contains):
                continue  # Title requirement not met, skip this rule

        # Check title_not_contains (none must match)
        title_not_contains = rule.get("title_not_contains", [])
        if title_not_contains:
            if any(phrase.lower() in window_title for phrase in title_not_contains):
                continue  # Title exclusion matched, skip this rule

        # Rule matched! Return the paste key
        paste_key = rule.get("paste_key", default_key)
        description = rule.get("description", "")
        print(f"Matched rule: {description}")
        print(f"Window class: {window_class}")
        print(f"Window title: {window_title[:50]}...")
        print(f"Using paste key: {paste_key}")
        return paste_key

    # No rule matched, use default
    print(f"No rule matched for window class '{window_class}'")
    print(f"Using default paste key: {default_key}")
    return default_key


def get_active_window_id():
    """
    Get handle of currently focused window

    Returns:
        int: Window handle or None if failed
    """
    try:
        hwnd = _user32.GetForegroundWindow()
        if hwnd:
            print(f"Active window HWND: {hwnd}")
            return hwnd
        print("No active window detected")
        return None
    except Exception as e:
        print(f"Failed to get active window: {e}")
        return None


def get_window_class(window_id):
    """
    Get the window class for a window handle

    Args:
        window_id (int): Window handle

    Returns:
        str: Window class name (lowercase) or empty string if failed
    """
    if not window_id:
        return ""

    # Check cache first (window class doesn't change during app lifetime)
    cache_key = f"_window_class_cache_{window_id}"
    if hasattr(get_window_class, cache_key):
        return getattr(get_window_class, cache_key)

    try:
        buf = ctypes.create_unicode_buffer(256)
        _user32.GetClassNameW(window_id, buf, len(buf))
        window_class = buf.value.lower()
        setattr(get_window_class, cache_key, window_class)
        print(f"Window class: {window_class} (cached)")
        return window_class
    except Exception as e:
        print(f"Failed to get window class: {e}")
        setattr(get_window_class, cache_key, "")
        return ""


def get_window_title(window_id):
    """
    Get the window title for context detection

    Args:
        window_id (int): Window handle

    Returns:
        str: Window title or empty string if failed
    """
    if not window_id:
        return ""

    try:
        length = _user32.GetWindowTextLengthW(window_id)
        buf = ctypes.create_unicode_buffer(length + 1)
        _user32.GetWindowTextW(window_id, buf, len(buf))
        return buf.value
    except Exception:
        return ""


def focus_window(window_id):
    """
    Focus a specific window by handle

    Args:
        window_id (int): Window handle to focus

    Returns:
        bool: True if command was sent, False if window_id invalid
    """
    if not window_id:
        return False

    try:
        _user32.ShowWindow(window_id, SW_RESTORE)
        result = _user32.SetForegroundWindow(window_id)
        time.sleep(0.05)
        return bool(result)
    except Exception as e:
        print(f"Error activating window: {e}")
        return False


def paste_text_clipboard(text, window_id=None, _window_class_hint=None):
    """
    Paste text using clipboard (fast method)

    Args:
        text (str): Text to paste
        window_id (int, optional): Window handle to focus first
        _window_class_hint (str, optional): Unused on Windows

    Returns:
        bool: True if successful, False otherwise
    """
    if not text:
        print("No text to paste")
        return False

    # Focus target window if specified
    if window_id:
        if not focus_window(window_id):
            print("Could not focus target window")
            return False

    try:
        import pyperclip

        # Copy to clipboard
        pyperclip.copy(text)
        print(f"Copied {len(text)} chars to clipboard")

        # Determine paste key using rule engine
        paste_key = get_paste_key_for_window(window_id)

        _send_hotkey_windows(paste_key)

        print(f"Text pasted via clipboard ({paste_key}): {len(text)} characters")
        return True

    except ImportError:
        print("pyperclip not available")
        return False
    except Exception as e:
        print(f"Error with clipboard paste: {e}")
        return False


def verify_window_exists(window_id):
    """
    Check if window still exists

    Args:
        window_id (int): Window handle to check

    Returns:
        bool: True if window exists, False otherwise
    """
    if not window_id:
        return False

    try:
        return bool(_user32.IsWindow(window_id))
    except Exception:
        return False


def _send_hotkey_windows(paste_key):
    """Send a key combo like ctrl+v or ctrl+shift+v using pynput."""
    from pynput.keyboard import Controller, Key

    key_parts = [part.strip().lower() for part in paste_key.split("+") if part.strip()]
    keys = []
    for part in key_parts:
        if part in ("ctrl", "control"):
            keys.append(Key.ctrl)
        elif part == "shift":
            keys.append(Key.shift)
        elif part == "alt":
            keys.append(Key.alt)
        elif part in ("win", "windows", "cmd", "meta"):
            keys.append(Key.cmd)
        elif part in ("insert", "ins"):
            keys.append(Key.insert)
        else:
            keys.append(part)

    controller = Controller()
    for key in keys:
        controller.press(key)
    for key in reversed(keys):
        controller.release(key)


if __name__ == "__main__":
    # Test window manager
    print("Testing Window Manager...")
    print("Make sure a text editor is open!\n")

    # Get current window
    window_id = get_active_window_id()
    print(f"\nCurrent window: {window_id}")

    # Wait for user to switch to text editor
    print("\nSwitch to a text editor and press Enter...")
    input()

    # Get text editor window
    editor_window = get_active_window_id()
    print(f"Editor window: {editor_window}")

    # Test paste
    test_text = "Hello from Dictate! This is a test of the auto-paste system."
    print(f"\nPasting test text: '{test_text}'")

    time.sleep(1)

    success = paste_text_clipboard(test_text, editor_window)

    if success:
        print("Paste test successful!")
    else:
        print("Paste test failed!")
