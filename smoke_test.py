#!/usr/bin/env python3
"""
smoke_test.py - Quick Health Check for Dictate (Windows)

Purpose: Verify that Dictate installation is working correctly.
"""

import sys
import os


def test_python_version():
    """Verify Python version is 3.8+"""
    print("Testing Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"  OK: Python {version.major}.{version.minor}.{version.micro}")
        return True
    print(f"  FAIL: Python {version.major}.{version.minor}.{version.micro} - Need 3.8+")
    return False


def test_imports():
    """Test that all required libraries can be imported"""
    print("\nTesting required imports...")

    required_modules = {
        'tkinter': 'Tkinter (GUI framework)',
        'ttkbootstrap': 'ttkbootstrap (Modern theme)',
        'faster_whisper': 'faster-whisper (Transcription engine)',
        'torch': 'PyTorch (Deep learning backend)',
        'pyperclip': 'pyperclip (Clipboard support)',
        'pynput': 'pynput (Global hotkeys)',
        'pystray': 'pystray (System tray)',
        'PIL': 'Pillow (Tray icon images)',
        'win32api': 'pywin32 (Windows APIs)',
    }

    all_passed = True
    for module_name, description in required_modules.items():
        try:
            __import__(module_name)
            print(f"  OK: {description}")
        except ImportError as e:
            print(f"  FAIL: {description} - MISSING")
            print(f"     Error: {e}")
            all_passed = False

    return all_passed


def test_gpu_availability():
    """Test GPU/CUDA availability (informational only)"""
    print("\nTesting GPU availability...")

    try:
        import torch
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown"
            print(f"  OK: GPU available: {device_name}")
            print(f"     Devices: {device_count}")
            return True
        print("  INFO: No GPU detected - will use CPU mode")
        return True
    except Exception as e:
        print(f"  WARN: GPU test failed: {e}")
        print("     App will fall back to CPU mode")
        return True


def test_directories():
    """Test that required directories exist or can be created"""
    print("\nTesting directories...")

    transcript_dir = os.path.expanduser("~/Music/dictate/transcripts")
    log_dir = os.path.expanduser("~/Music/dictate/logs")

    all_passed = True

    for directory in [transcript_dir, log_dir]:
        if os.path.exists(directory):
            print(f"  OK: {directory} exists")
        else:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"  OK: {directory} created")
            except Exception as e:
                print(f"  FAIL: Cannot create {directory}: {e}")
                all_passed = False

    return all_passed


def test_conda_environment():
    """Test that we're in the correct conda environment"""
    print("\nTesting conda environment...")

    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env == 'fasterwhisper':
        print("  OK: Running in 'fasterwhisper' environment")
        return True
    if conda_env:
        print(f"  WARN: Running in '{conda_env}' environment")
        print("     Expected: 'fasterwhisper'")
        print("     Activate with: conda activate fasterwhisper")
        return False

    print("  WARN: Not running in a conda environment")
    print("     Activate with: conda activate fasterwhisper")
    return False


def test_start_script():
    """Test that start_dictate.ps1 exists"""
    print("\nTesting start script...")

    start_script = os.path.join(os.getcwd(), "start_dictate.ps1")
    if os.path.exists(start_script):
        print("  OK: start_dictate.ps1 found")
    else:
        print("  WARN: start_dictate.ps1 not found")
    return True


def test_gui_initialization():
    """Test that GUI can be initialized (without showing it)"""
    print("\nTesting GUI initialization...")

    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Don't show window
        root.destroy()
        print("  OK: GUI can initialize")
        return True
    except Exception as e:
        print(f"  FAIL: GUI initialization failed: {e}")
        return False


def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("Dictate - Smoke Test Suite (Windows)")
    print("Quick verification that installation is working")
    print("=" * 60)
    print()

    tests = [
        ("Python Version", test_python_version),
        ("Required Imports", test_imports),
        ("GPU Availability", test_gpu_availability),
        ("Directories", test_directories),
        ("Conda Environment", test_conda_environment),
        ("Start Script", test_start_script),
        ("GUI Initialization", test_gui_initialization),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\nFAIL: Test '{test_name}' crashed: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)

    if all(results):
        print("OK: ALL SMOKE TESTS PASSED")
        print()
        print("Your Dictate installation looks good.")
        print("You can now run: .\\start_dictate.ps1")
        print()
        return 0

    print(f"WARN: SOME TESTS FAILED ({passed}/{total} passed)")
    print()
    print("Please fix the issues above before running Dictate.")
    print()
    if not results[4]:  # Conda environment test
        print("Most common issue: Wrong conda environment")
        print("Solution: conda activate fasterwhisper")
    print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
