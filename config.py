#!/usr/bin/env python3
"""
Configuration management for Dictate app
Handles loading/saving user preferences to ~/.config/dictate/config.json
"""

import os
import json
from pathlib import Path

# Default configuration with sensible defaults
DEFAULT_CONFIG = {
    "hotkey": "right_ctrl",          # Options: right_ctrl, scroll_lock, right_alt, caps_lock
    "language": "DE-CH",             # Default: Swiss German (Options: DE-CH, DE-DE, EN)
    "model": "large-v3-turbo",       # Default: V3 Turbo (Options: base, small, large-v3-turbo)
    "use_gpu": True,                 # Default: GPU enabled (Options: True, False)
    "start_minimized": False,        # Start with window visible
    "auto_paste": True,              # Automatically paste transcribed text
    "beep_on_start": True,           # Beep when recording starts
    "beep_on_stop": True,            # Beep when recording stops
    "show_window_on_startup": True,  # Show window on startup
    "paste_method": "clipboard",     # Options: clipboard
    "window_toggle_hotkey": "ctrl+shift+d",  # Hotkey to show/hide window (future)
    "recording_timeout_seconds": 300,  # 5 minutes safety timeout
    "cpu_quality_preset": "MED"      # Options: HI, MED, LO (CPU-only)
}

CONFIG_PATH = Path.home() / ".config" / "dictate" / "config.json"


def load_config():
    """
    Load configuration from file, create with defaults if missing

    Returns:
        dict: Configuration dictionary with all settings
    """
    if not CONFIG_PATH.exists():
        # First run - create config directory and file with defaults
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        save_config(DEFAULT_CONFIG)
        print(f"✅ Created default config: {CONFIG_PATH}")
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            user_config = json.load(f)

        # Merge with defaults (in case new keys added in updates)
        config = DEFAULT_CONFIG.copy()
        config.update(user_config)

        print(f"✅ Loaded config from: {CONFIG_PATH}")
        return config

    except json.JSONDecodeError as e:
        print(f"⚠️ Config file corrupt, using defaults: {e}")
        return DEFAULT_CONFIG.copy()
    except Exception as e:
        print(f"⚠️ Error loading config, using defaults: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """
    Save configuration to file

    Args:
        config (dict): Configuration dictionary to save
    """
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        print(f"✅ Config saved to: {CONFIG_PATH}")

    except Exception as e:
        print(f"⚠️ Error saving config: {e}")


def get_config_value(config, key, default=None):
    """
    Safely get a config value with fallback

    Args:
        config (dict): Configuration dictionary
        key (str): Configuration key
        default: Default value if key not found

    Returns:
        Value from config or default
    """
    return config.get(key, default if default is not None else DEFAULT_CONFIG.get(key))


if __name__ == "__main__":
    # Test configuration system
    print("Testing configuration system...")

    print("\n1. Loading config:")
    config = load_config()
    print(f"   Hotkey: {config['hotkey']}")
    print(f"   Language: {config['language']}")
    print(f"   Model: {config['model']}")
    print(f"   GPU: {config['use_gpu']}")

    print("\n2. Modifying config:")
    config['language'] = 'EN'
    config['model'] = 'small'
    save_config(config)

    print("\n3. Reloading config:")
    config2 = load_config()
    print(f"   Language: {config2['language']}")
    print(f"   Model: {config2['model']}")

    print("\n✅ Configuration system test complete!")
