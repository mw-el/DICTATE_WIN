#!/usr/bin/env python3
"""
System tray icon for Dictate app
Provides status indication and right-click menu for settings
"""

import pystray
from PIL import Image, ImageDraw
import threading


class TrayIcon:
    """
    System tray icon with status colors and settings menu

    Status colors:
    - Green: Idle/Ready
    - Red: Recording
    - Gray: Transcribing
    """

    def __init__(self, app_window, on_quit_callback, on_language_change_callback,
                 on_model_change_callback, on_gpu_toggle_callback):
        """
        Initialize tray icon

        Args:
            app_window: Tkinter window reference
            on_quit_callback: Function to call when quitting
            on_language_change_callback: Function to call when language changes
            on_model_change_callback: Function to call when model changes
            on_gpu_toggle_callback: Function to call when GPU/CPU toggles
        """
        self.app_window = app_window
        self.on_quit = on_quit_callback
        self.on_language_change = on_language_change_callback
        self.on_model_change = on_model_change_callback
        self.on_gpu_toggle = on_gpu_toggle_callback
        self.icon = None
        self.status = "idle"  # idle, recording, transcribing

        # Current settings (will be synced from config)
        self.current_language = "DE-CH"
        self.current_model = "large-v3-turbo"
        self.use_gpu = True

    def create_icon_image(self, color="green"):
        """
        Load pre-generated PNG icon for the given status color

        Args:
            color (str): Color name (green, red, gray)

        Returns:
            PIL.Image: Icon image
        """
        import os

        # Load pre-generated PNG file
        icon_path = os.path.join(
            os.path.dirname(__file__),
            "assets", "icons", f"dictate_{color}.png"
        )

        try:
            if os.path.exists(icon_path):
                return Image.open(icon_path)
            else:
                print(f"⚠️ Icon not found: {icon_path}, using fallback")
                return self._create_fallback_icon(color)
        except Exception as e:
            print(f"⚠️ Error loading icon: {e}, using fallback")
            return self._create_fallback_icon(color)

    def _create_fallback_icon(self, color):
        """Fallback colored circle if main icon fails"""
        size = 48
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)

        colors = {
            "green": "#00c800",
            "red": "#dc0000",
            "gray": "#808080",
        }

        dc.ellipse(
            [0, 0, size - 1, size - 1],
            fill=colors.get(color, "#00c800")
        )

        return image

    def toggle_window(self, icon=None, item=None):
        """Show/hide main window"""
        print(f"\n{'='*50}")
        print(f"🖱️ TOGGLE WINDOW CLICKED")
        print(f"   icon={icon}, item={item}")
        def _toggle():
            try:
                state = self.app_window.state()
                visible = state != "withdrawn"
                print(f"   Window state: {state} visible={visible}")
                if visible:
                    self.app_window.withdraw()
                    print("   🔕 Window hidden")
                else:
                    if hasattr(self.app_window, "force_window_visible"):
                        self.app_window.force_window_visible()
                    else:
                        self.app_window.deiconify()
                        self.app_window.lift()
                        self.app_window.focus_force()
                    print("   🔔 Window shown")
            except Exception as e:
                print(f"   ⚠️ Error toggling window: {e}")
                import traceback
                traceback.print_exc()
        try:
            self.app_window.after(0, _toggle)
        except Exception:
            _toggle()
        print(f"{'='*50}\n")

    def quit_app(self, icon=None, item=None):
        """Quit application with full cleanup"""
        print(f"\n{'='*50}")
        print("👋 QUIT CLICKED - Quitting from tray menu...")
        print(f"{'='*50}\n")
        self.stop()
        self.on_quit()  # Calls on_closing() which handles all cleanup

    def set_language(self, lang_code):
        """Change language and update menu"""
        print(f"\n🌍 LANGUAGE MENU CLICKED: {lang_code}")
        self.current_language = lang_code
        self.on_language_change(lang_code)
        # Update menu to show checkmark on selected language
        if self.icon:
            self.icon.menu = self.create_menu()
        print(f"✅ Language changed to {lang_code}\n")

    def set_model(self, model_name):
        """Change model and update menu"""
        print(f"🔄 Model changed via tray: {model_name}")
        self.current_model = model_name
        self.on_model_change(model_name)
        # Update menu to show checkmark on selected model
        if self.icon:
            self.icon.menu = self.create_menu()

    def _set_gpu_mode(self, use_gpu):
        """Set GPU mode (True=GPU, False=CPU) and update menu"""
        if self.use_gpu == use_gpu:
            return  # Already in this mode

        self.use_gpu = use_gpu
        print(f"🔄 Processing changed via tray: {'GPU' if self.use_gpu else 'CPU'}")
        self.on_gpu_toggle(self.use_gpu)
        # Update menu to show new GPU/CPU state
        if self.icon:
            self.icon.menu = self.create_menu()

    def create_menu(self):
        """Create tray icon menu with submenus for language, model, and GPU"""

        # Language options in priority order
        languages = [
            ("DE-CH", "German (Swiss)"),
            ("DE-DE", "German (Germany)"),
            ("EN", "English")
        ]

        # Model options with descriptions
        models = [
            ("large-v3-turbo", "Large V3 Turbo (Best Quality)"),
            ("small", "Small (Faster)"),
            ("base", "Base (Fastest)")
        ]

        # Create language menu items with checkmarks
        language_items = []
        for code, name in languages:
            display_name = f"✓ {name}" if code == self.current_language else f"  {name}"
            language_items.append(
                pystray.MenuItem(
                    display_name,
                    lambda _, lang=code: self.set_language(lang)
                )
            )

        # Create model menu items with checkmarks
        model_items = []
        for model_code, model_name in models:
            display_name = f"✓ {model_name}" if model_code == self.current_model else f"  {model_name}"
            model_items.append(
                pystray.MenuItem(
                    display_name,
                    lambda _, m=model_code: self.set_model(m)
                )
            )

        # GPU/CPU toggle with checkmark showing current state
        gpu_items = []

        # GPU Mode item
        gpu_label = "✓ GPU Mode" if self.use_gpu else "  GPU Mode"
        gpu_items.append(pystray.MenuItem(
            gpu_label,
            lambda icon=None, item=None: self._set_gpu_mode(True)
        ))

        # CPU Mode item
        cpu_label = "  CPU Mode" if self.use_gpu else "✓ CPU Mode"
        gpu_items.append(pystray.MenuItem(
            cpu_label,
            lambda icon=None, item=None: self._set_gpu_mode(False)
        ))

        # Build complete menu
        return pystray.Menu(
            pystray.MenuItem("Show/Hide Window", self.toggle_window),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Language", pystray.Menu(*language_items)),
            pystray.MenuItem("Model", pystray.Menu(*model_items)),
            pystray.MenuItem("Processing", pystray.Menu(*gpu_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit_app)
        )

    def start(self):
        """Start tray icon in background thread"""
        print("🔧 Creating tray icon...")

        self.icon = pystray.Icon(
            "dictate",
            self.create_icon_image("green"),
            "Dictate - Ready",
            self.create_menu()
        )

        print(f"🔧 Icon object created: {self.icon}")
        print(f"🔧 Icon name: {self.icon.name}")
        print(f"🔧 Icon title: {self.icon.title}")

        # Optional setup callback for debugging
        def setup(icon):
            print("🔧 Tray icon setup callback triggered")
            print(f"🔧 Icon visible: {icon.visible}")
            icon.visible = True
            print(f"🔧 Icon visibility set to True")

        # Run in background thread - use simple daemon thread
        def run_icon():
            print("🔧 Starting icon.run()...")
            try:
                self.icon.run(setup=setup)
                print("🔧 icon.run() completed normally")
            except Exception as e:
                print(f"❌ Tray icon error: {e}")
                import traceback
                traceback.print_exc()

        # Use NON-daemon thread so tray icon can receive events properly
        # Daemon threads don't process events reliably in pystray
        self.icon_thread = threading.Thread(target=run_icon, daemon=False, name="TrayIconThread")
        self.icon_thread.start()
        print(f"🔧 Icon thread started: daemon={self.icon_thread.daemon}, alive={self.icon_thread.is_alive()}, name={self.icon_thread.name}")
        print(f"⚠️  IMPORTANT: Using non-daemon thread for proper event handling")

        print("✅ Tray icon started")
        print("💡 Left-click tray icon to show/hide window")
        print("💡 Right-click tray icon for settings menu")

    def update_status(self, status):
        """
        Update icon color based on status

        Args:
            status (str): Status name (idle, recording, transcribing)
        """
        self.status = status
        color_map = {
            "idle": "green",      # Green = Ready to record
            "recording": "red",   # Red = Recording in progress
            "transcribing": "gray"  # Gray = Transcribing
        }

        if self.icon:
            self.icon.icon = self.create_icon_image(color_map.get(status, "green"))
            self.icon.title = f"Dictate - {status.capitalize()}"
            print(f"🎨 Tray icon status: {status} → {color_map.get(status, 'green')}")

    def stop(self):
        """Stop tray icon and its thread."""
        try:
            if self.icon:
                self.icon.stop()
        except Exception:
            pass
        try:
            if hasattr(self, "icon_thread") and self.icon_thread:
                self.icon_thread.join(timeout=1.0)
        except Exception:
            pass


if __name__ == "__main__":
    # Test tray icon (requires Tkinter window)
    import tkinter as tk
    import time

    print("Testing Tray Icon...")
    print("Right-click the tray icon to test menu")
    print("Press Ctrl+C to exit\n")

    # Create minimal window
    app = tk.Tk()
    app.title("Tray Icon Test")
    app.geometry("300x200")

    # Callbacks
    def on_quit():
        print("Quit callback triggered")
        app.quit()

    def on_language_change(lang):
        print(f"Language callback: {lang}")

    def on_model_change(model):
        print(f"Model callback: {model}")

    def on_gpu_toggle(use_gpu):
        print(f"GPU callback: {use_gpu}")

    # Create tray icon
    tray = TrayIcon(app, on_quit, on_language_change, on_model_change, on_gpu_toggle)
    tray.start()

    # Test status changes
    def cycle_status():
        time.sleep(2)
        tray.update_status("recording")
        time.sleep(2)
        tray.update_status("transcribing")
        time.sleep(2)
        tray.update_status("idle")

    threading.Thread(target=cycle_status, daemon=True).start()

    # Keep window visible
    app.mainloop()
    print("\n✅ Tray icon test complete!")
