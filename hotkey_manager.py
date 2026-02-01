#!/usr/bin/env python3
"""
Global hotkey detection for Dictate app
Uses pynput to detect key press/release events system-wide
"""

from pynput import keyboard
import threading


class HotkeyManager:
    """
    Manages global hotkey detection for press-and-hold dictation

    Supports multiple hotkeys: Right Ctrl, Scroll Lock, Right Alt, Caps Lock
    """

    def __init__(self, config, on_press_callback, on_release_callback):
        """
        Initialize hotkey manager

        Args:
            config (dict): Configuration dictionary with 'hotkey' key
            on_press_callback (callable): Function to call when hotkey pressed
            on_release_callback (callable): Function to call when hotkey released
        """
        self.config = config
        self.on_press = on_press_callback
        self.on_release = on_release_callback
        self.listener = None
        self.is_pressed = False

        # Map config names to pynput key constants
        self.key_map = {
            "right_ctrl": keyboard.Key.ctrl_r,
            "scroll_lock": keyboard.Key.scroll_lock,
            "right_alt": keyboard.Key.alt_gr,
            "caps_lock": keyboard.Key.caps_lock
        }

        # Get target key from config
        hotkey_name = config.get("hotkey", "right_ctrl")
        self.target_key = self.key_map.get(hotkey_name, keyboard.Key.ctrl_r)

        print(f"🎯 Hotkey configured: {hotkey_name} -> {self.target_key}")

    def start(self):
        """Start listening for global hotkey events"""
        if self.listener:
            print("⚠️ Hotkey listener already running")
            return

        self.listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.listener.start()
        print(f"🎧 Hotkey listener started: {self.config.get('hotkey', 'right_ctrl')}")

    def stop(self):
        """Stop listening for hotkey events"""
        if self.listener:
            self.listener.stop()
            self.listener = None
            self.is_pressed = False
            print("✅ Hotkey listener stopped")

    def _on_key_press(self, key):
        """
        Internal callback when any key is pressed

        Args:
            key: pynput key object
        """
        # Only trigger if target key is pressed and not already pressed
        if key == self.target_key and not self.is_pressed:
            self.is_pressed = True
            print(f"🔴 Hotkey pressed: {key}")

            # Run callback in separate thread to avoid blocking listener
            threading.Thread(target=self.on_press, daemon=True).start()

    def _on_key_release(self, key):
        """
        Internal callback when any key is released

        Args:
            key: pynput key object
        """
        # Only trigger if target key is released and was pressed
        if key == self.target_key and self.is_pressed:
            self.is_pressed = False
            print(f"⚪ Hotkey released: {key}")

            # Run callback in separate thread to avoid blocking listener
            threading.Thread(target=self.on_release, daemon=True).start()


if __name__ == "__main__":
    # Test hotkey manager
    import time

    print("Testing Hotkey Manager...")
    print("Press and hold Right Ctrl to test (Ctrl+C to exit)\n")

    test_config = {"hotkey": "right_ctrl"}

    def on_press():
        print("  → PRESS callback triggered!")

    def on_release():
        print("  → RELEASE callback triggered!")

    manager = HotkeyManager(test_config, on_press, on_release)
    manager.start()

    try:
        # Keep running until interrupted
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\n✅ Test complete!")
        manager.stop()
