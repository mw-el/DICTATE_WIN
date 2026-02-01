#!/usr/bin/env python3
"""
Clean Faster Whisper - Large-v3 + Swiss German
-----------------------------------------------
Based on your existing dictate.py, just optimized for:
- Large-v3 model (best quality)
- Swiss German support (DE-CH)
- Proper GPU detection and fallback
- No error handling bloat - just works or fails clean
"""

__version__ = "1.0.0"

import os
import threading
import subprocess
import shutil
import ctypes
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import Text, messagebox
import tkinter as tk
import tkinter.font as tkfont
import pyperclip
import time
from datetime import datetime
import re
import sys
import traceback
import glob  # NEW: for transcript file discovery

# Import hotkey system components
from config import load_config, save_config
from hotkey_manager import HotkeyManager
from window_manager import get_active_window_id, paste_text_clipboard
from tray_icon import TrayIcon

# Try importing faster_whisper and torch
try:
    from faster_whisper import WhisperModel
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False
    print("Warning: faster_whisper module not found. Please make sure you are in the right Conda environment.")

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("Warning: torch module not found.")

# Simple exception handler (keep your existing one)
def global_exception_handler(exc_type, exc_value, exc_traceback):
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"UNHANDLED EXCEPTION: {error_msg}")
    
    crash_dir = os.path.expanduser("~/Music/dictate/logs")
    os.makedirs(crash_dir, exist_ok=True)
    crash_file = os.path.join(crash_dir, f"crash_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
    
    with open(crash_file, 'w', encoding='utf-8') as f:
        f.write(f"CRASH REPORT - {datetime.now()}\n")
        f.write(f"Exception: {str(exc_value)}\n\n")
        f.write(error_msg)
    
    print(f"Application crashed. See log file: {crash_file}")
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = global_exception_handler

# Windows taskbar grouping/icon
def set_windows_app_id(app_id):
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass

def enable_windows_dpi_awareness():
    """Enable DPI awareness to avoid blurry rendering on Windows."""
    try:
        shcore = ctypes.windll.shcore
        PROCESS_PER_MONITOR_DPI_AWARE = 2
        shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
        return True
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
            return True
        except Exception:
            return False

# Environment check - just warn, don't try to activate
if 'CONDA_DEFAULT_ENV' not in os.environ:
    print("⚠️ Warning: CONDA_DEFAULT_ENV not set")
    print("   Make sure you're running with the correct Python interpreter:")
    print("   Example: C:\\Users\\<you>\\miniconda3\\envs\\fasterwhisper\\python.exe")
elif os.environ['CONDA_DEFAULT_ENV'] != 'fasterwhisper':
    print(f"⚠️ Warning: Running in environment '{os.environ['CONDA_DEFAULT_ENV']}', expected 'fasterwhisper'")

# GPU Detection Function
def detect_gpu_availability():
    """Detect if GPU is available and working for faster-whisper"""
    gpu_info = {
        'available': False,
        'error': None,
        'details': []
    }

    if not HAS_TORCH:
        gpu_info['error'] = "PyTorch not available"
        gpu_info['details'].append("- Install PyTorch with CUDA support")
        return gpu_info

    try:
        if not torch.cuda.is_available():
            gpu_info['error'] = "CUDA not available"
            gpu_info['details'].extend([
                "- CUDA drivers may not be installed",
                "- PyTorch may be CPU-only version",
                "- Check: nvidia-smi command"
            ])
            return gpu_info

        device_count = torch.cuda.device_count()
        gpu_info['details'].append(f"- CUDA devices detected: {device_count}")

        if device_count == 0:
            gpu_info['error'] = "No CUDA devices found"
            return gpu_info

        device_name = torch.cuda.get_device_name(0)
        gpu_info['details'].append(f"- Device: {device_name}")

        test_tensor = torch.randn(10, device='cuda')
        del test_tensor
        torch.cuda.empty_cache()

        gpu_info['available'] = True
        gpu_info['details'].append("GPU test successful")
        return gpu_info

    except Exception as e:
        gpu_info['error'] = f"GPU test failed: {str(e)}"
        gpu_info['details'].extend([
            "- Possible causes:",
            "  - CUDA_VISIBLE_DEVICES changed",
            "  - Conda environment issues",
            "  - Driver/library version mismatch",
            "- Try: nvidia-smi",
            "- Try: set CUDA_VISIBLE_DEVICES",
            "- Try: conda list"
        ])
        return gpu_info

def resolve_model_source(model_name):
    """Prefer local models/ directory if present."""
    local_dir = os.path.join(os.path.dirname(__file__), "models", model_name)
    if os.path.isdir(local_dir):
        return local_dir
    return model_name

# Settings - auto-adapt to GPU availability
gpu_info = detect_gpu_availability()

# Auto-configure based on GPU availability
if gpu_info['available']:
    # GPU system: use large-v3-turbo for best quality
    current_model_name = "large-v3-turbo"
    use_gpu = True
else:
    # CPU-only system: default to small model for reasonable performance
    current_model_name = "small"
    use_gpu = False
    print("ℹ️  No GPU detected - defaulting to CPU (default model: small)")

# Load configuration
config = load_config()

# Override defaults with config values (ensure DE-CH is default)
current_language = config.get("language", "DE-CH")
cpu_quality_preset = str(config.get("cpu_quality_preset", "MED")).upper()
if cpu_quality_preset not in ("HI", "MED", "LO"):
    cpu_quality_preset = "MED"
    config["cpu_quality_preset"] = cpu_quality_preset
    save_config(config)

# Make sure config has DE-CH as default if not set
if "language" not in config:
    config["language"] = "DE-CH"
    current_language = "DE-CH"
    save_config(config)
current_model_name = config.get("model", current_model_name)  # Use config or GPU-detected default
use_gpu = config.get("use_gpu", use_gpu)  # Use config or GPU-detected default

# Models available in HuggingFace cache (~/.cache/huggingface/hub/)
# Only efficient models: base (142M), small (464M), large-v3-turbo (1.6G)
available_models = ["base", "small", "large-v3-turbo"]

# Language options with Swiss German
language_options = ["DE-DE", "DE-CH", "EN"]
language_codes = {"DE-DE": "de", "DE-CH": "de", "EN": "en"}

model = None
recording_in_progress = False
audio_file_path = None
ffmpeg_process = None
ffmpeg_log_handle = None
windows_audio_device = None
model_load_lock = threading.Lock()
model_loading = False

# Hotkey system global variables
hotkey_manager = None
tray_icon = None
active_window_id = None  # Store window ID that was active when recording started

# MEMORY FIX: Track active threads for cleanup
_active_threads = {}

# MEMORY FIX: Helper function for thread management
def start_managed_thread(target, args=(), name=None, daemon=True):
    """Start a thread and track it for cleanup"""
    thread = threading.Thread(target=target, args=args, name=name, daemon=daemon)
    thread.start()
    # Track thread for cleanup (optional - mainly for debugging)
    if name:
        _active_threads[name] = thread
    return thread

def cleanup_threads():
    """Clean up finished threads from tracking"""
    finished = [name for name, thread in _active_threads.items() if not thread.is_alive()]
    for name in finished:
        del _active_threads[name]

# Swiss German conversion - simple and fast
def swiss_german_convert(text):
    if current_language == "DE-CH":
        return text.replace('ß', 'ss')
    return text

# Your existing utility functions (unchanged)
def ensure_directory(path):
    os.makedirs(path, exist_ok=True)

def sanitize_filename(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    return text[:50]

def get_output_paths(transcript_text):
    timestamp = datetime.now().strftime("%y-%m-%d_%H-%M")
    first_words = " ".join(transcript_text.strip().split()[:7]) or "untitled"
    filename_base = f"{timestamp}_{sanitize_filename(first_words)}"
    
    output_dir = os.path.expanduser("~/Music/dictate")
    ensure_directory(output_dir)
    
    audio_file_path = os.path.join(output_dir, f"{filename_base}.mp3")
    transcript_file_path = os.path.join(output_dir, f"{filename_base}.txt")
    
    return audio_file_path, transcript_file_path

def _detect_windows_audio_device():
    """Return first DirectShow audio device name or None if not found."""
    try:
        ffmpeg_path = _resolve_ffmpeg_path()
        result = subprocess.run(
            [ffmpeg_path, "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = (result.stderr or "") + (result.stdout or "")
        devices = []
        in_audio = False
        for line in output.splitlines():
            if "DirectShow audio devices" in line:
                in_audio = True
                continue
            if "DirectShow video devices" in line:
                in_audio = False
            if in_audio:
                match = re.search(r"\"(.+?)\"", line)
                if match:
                    devices.append(match.group(1))
        if devices:
            return devices[0]
    except Exception as e:
        print(f"âš ï¸ Audio device detection failed: {e}")
    return None

def _get_windows_audio_device():
    """Resolve Windows audio device from config or auto-detect and persist."""
    global windows_audio_device
    if windows_audio_device:
        return windows_audio_device
    configured = config.get("audio_device", "").strip()
    if configured:
        windows_audio_device = configured
        return windows_audio_device
    detected = _detect_windows_audio_device()
    if detected:
        windows_audio_device = detected
        config["audio_device"] = detected
        save_config(config)
        print(f"âœ… Auto-detected audio device: {detected}")
        return windows_audio_device
    return None

def _build_ffmpeg_command(audio_path):
    ffmpeg_path = _resolve_ffmpeg_path()
    device = _get_windows_audio_device()
    if device:
        input_spec = f"audio={device}"
    else:
        input_spec = "audio=default"
        print("âš ï¸ No DirectShow device found, trying audio=default")
    return [
        ffmpeg_path, "-y",
        "-f", "dshow",
        "-i", input_spec,
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        audio_path
    ]

def start_ffmpeg_recording(audio_path):
    """Start ffmpeg recording and store the process handle."""
    global ffmpeg_process, ffmpeg_log_handle
    cmd = _build_ffmpeg_command(audio_path)
    creationflags = 0
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        creationflags = subprocess.CREATE_NO_WINDOW
    log_dir = os.path.expanduser("~/Music/dictate/logs")
    ensure_directory(log_dir)
    log_path = os.path.join(log_dir, f"ffmpeg_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
    ffmpeg_log_handle = open(log_path, "w", encoding="utf-8", errors="replace")
    ffmpeg_process = subprocess.Popen(
        cmd,
        stdout=ffmpeg_log_handle,
        stderr=ffmpeg_log_handle,
        stdin=subprocess.PIPE,
        creationflags=creationflags
    )
    return log_path

def stop_ffmpeg_recording():
    """Stop ffmpeg recording if running."""
    global ffmpeg_process, ffmpeg_log_handle
    if ffmpeg_process and ffmpeg_process.poll() is None:
        try:
            if ffmpeg_process.stdin:
                try:
                    ffmpeg_process.stdin.write(b"q\n")
                    ffmpeg_process.stdin.flush()
                except Exception:
                    pass
            ffmpeg_process.wait(timeout=3)
        except Exception:
            try:
                ffmpeg_process.terminate()
                ffmpeg_process.wait(timeout=2)
            except Exception:
                try:
                    ffmpeg_process.kill()
                except Exception:
                    pass
    ffmpeg_process = None
    if ffmpeg_log_handle:
        try:
            ffmpeg_log_handle.flush()
            ffmpeg_log_handle.close()
        except Exception:
            pass
        ffmpeg_log_handle = None

def _resolve_ffmpeg_path():
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    env_root = os.path.abspath(os.path.join(os.path.dirname(sys.executable), ".."))
    candidate = os.path.join(env_root, "Library", "bin", "ffmpeg.exe")
    if os.path.exists(candidate):
        return candidate
    return "ffmpeg"

def beep():
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_OK)
    except Exception:
        print("\a", end="", flush=True)

# Display error in transcription area
def display_error_in_text_area(title, error_msg, details=None):
    """Display error information in the main text area where transcriptions normally appear"""
    error_text = f"🚨 {title}\n"
    error_text += "=" * 50 + "\n\n"
    error_text += f"ERROR: {error_msg}\n\n"
    
    if details:
        error_text += "DIAGNOSTIC INFO:\n"
        for detail in details:
            error_text += f"{detail}\n"
        error_text += "\n"
    
    error_text += "TROUBLESHOOTING STEPS:\n"
    error_text += "1. Check GPU status: nvidia-smi\n"
    error_text += "2. Check environment: set CUDA_VISIBLE_DEVICES\n"
    error_text += "3. Check CUDA packages: conda list\n"
    error_text += "4. Restart conda environment:\n"
    error_text += "   conda deactivate && conda activate fasterwhisper\n"
    error_text += "5. If still failing, click GPU button to try CPU mode\n\n"
    error_text += "💡 Since this worked yesterday, likely an environment issue!\n"
    
    # Display in main text area
    app.after(0, lambda: transcript_text.delete("1.0", 'end'))
    app.after(0, lambda: transcript_text.insert("1.0", error_text))

# Model initialization - show errors instead of silent fallback
def initialize_model():
    global model, use_gpu, model_loading

    if model_loading:
        print("ℹ️  Model load already in progress; skipping duplicate request")
        return

    if not model_load_lock.acquire(blocking=False):
        print("ℹ️  Model load lock busy; skipping duplicate request")
        return

    model_loading = True
    
    if not HAS_WHISPER:
        error_msg = "faster_whisper module not found"
        display_error_in_text_area("WHISPER NOT AVAILABLE", error_msg, 
                                 ["Make sure you're in the 'fasterwhisper' conda environment"])
        action_status.config(text="ERROR: faster_whisper not available", anchor="center")
        model_loading = False
        model_load_lock.release()
        return
    
    print(f"=== STARTING MODEL LOAD: {current_model_name} ===")
    model_abbrev = {"base": "BASE", "small": "SML", "large-v3-turbo": "V3T"}
    abbrev = model_abbrev.get(current_model_name, current_model_name.upper()[:4])
    action_status.config(text=f"LOADING {abbrev}...", anchor="center")

    # CRITICAL FIX: Only call app.update() if window is visible (not withdrawn)
    # This prevents multi-second delays during model loading when using hotkey with GUI minimized
    try:
        if app.state() != 'withdrawn':
            app.update()
    except:
        pass  # If app.update() fails, continue anyway
    
    # Free previous model before loading a new one
    if model is not None:
        try:
            del model
            model = None
            print("✅ Previous model freed")
        except Exception:
            pass

    model_source = resolve_model_source(current_model_name)

    # Try GPU if requested
    if use_gpu:
        if not gpu_info['available']:
            # Show GPU error in text area but don't fallback automatically
            display_error_in_text_area("GPU INITIALIZATION FAILED", 
                                     gpu_info['error'], gpu_info['details'])
            action_status.config(text="GPU ERROR - Check text area for details", anchor="center")
            model_loading = False
            model_load_lock.release()
            return
        
        try:
            device = 'cuda'
            compute_type = 'float16'
            print(f"Attempting GPU load: device={device}, compute_type={compute_type}")
            
            model = WhisperModel(model_source, device=device, compute_type=compute_type)
            
            print("✅ GPU MODEL LOADED SUCCESSFULLY")
            model_abbrev = {"base": "BASE", "small": "SML", "large-v3-turbo": "V3T"}
            abbrev = model_abbrev.get(current_model_name, current_model_name.upper()[:4])
            action_status.config(text=f"LOADED: {abbrev} (GPU)", anchor="center")
            # Clear any previous errors
            if "🚨" in transcript_text.get("1.0", "1.10"):
                transcript_text.delete("1.0", 'end')
            model_loading = False
            model_load_lock.release()
            return
            
        except Exception as e:
            # Show detailed GPU error
            error_details = [
                f"Model: {current_model_name}",
                f"Model source: {model_source}",
                f"Device: {device}",
                f"Compute type: {compute_type}",
                f"Full error: {str(e)}",
                "",
                "This suggests faster-whisper couldn't initialize the CUDA model",
                "even though basic CUDA tests passed."
            ]
            display_error_in_text_area("MODEL LOAD FAILED (GPU)", str(e), error_details)
            action_status.config(text="GPU MODEL LOAD FAILED - See text area", anchor="center")
            model_loading = False
            model_load_lock.release()
            return
    
    # CPU mode (only if explicitly requested via button)
    else:
        try:
            device = 'cpu'
            cpu_compute_map = {
                "HI": "float32",
                "MED": "int8_float32",
                "LO": "int8"
            }
            compute_type = cpu_compute_map.get(cpu_quality_preset, "float32")
            print(f"Loading CPU model: device={device}, compute_type={compute_type}")
            
            model = WhisperModel(model_source, device=device, compute_type=compute_type)
            
            print("✅ CPU MODEL LOADED SUCCESSFULLY")
            model_abbrev = {"base": "BASE", "small": "SML", "large-v3-turbo": "V3T"}
            abbrev = model_abbrev.get(current_model_name, current_model_name.upper()[:4])
            action_status.config(text=f"LOADED: {abbrev} (CPU)", anchor="center")
            # Clear any previous errors
            if "🚨" in transcript_text.get("1.0", "1.10"):
                transcript_text.delete("1.0", 'end')
            
        except Exception as e:
            error_details = [
                f"Model: {current_model_name}",
                f"Model source: {model_source}",
                f"Device: {device}",
                f"Compute type: {compute_type}",
                f"Full error: {str(e)}"
            ]
            display_error_in_text_area("MODEL LOAD FAILED (CPU)", str(e), error_details)
            action_status.config(text="CPU MODEL LOAD FAILED", anchor="center")
        finally:
            model_loading = False
            model_load_lock.release()

# Language toggle - now cycles through DE-DE, DE-CH, EN
def toggle_language():
    global current_language
    current_index = language_options.index(current_language) if current_language in language_options else 0
    next_index = (current_index + 1) % len(language_options)
    current_language = language_options[next_index]
    language_button.config(text=current_language)
    update_status_labels()

def cycle_model():
    global current_model_name
    current_index = available_models.index(current_model_name) if current_model_name in available_models else 0
    next_index = (current_index + 1) % len(available_models)
    current_model_name = available_models[next_index]
    # Use abbreviated model names: BASE, SML, V3T
    model_abbrev = {"base": "BASE", "small": "SML", "large-v3-turbo": "V3T"}
    model_button.config(text=model_abbrev.get(current_model_name, current_model_name.upper()[:4]))

    # MEMORY FIX: Use managed thread
    start_managed_thread(target=initialize_model, name="InitializeModel")
    update_status_labels()

def toggle_gpu():
    global use_gpu, current_model_name

    use_gpu = not use_gpu
    
    if use_gpu:
        gpu_button.config(text="GPU", bootstyle="success")
        print("🔄 Switching to GPU mode - will show errors if GPU fails")
    else:
        gpu_button.config(text="CPU", bootstyle="secondary")
        print("🔄 Switching to CPU mode")

    # MEMORY FIX: Use managed thread
    start_managed_thread(target=initialize_model, name="InitializeModel_GPU")
    update_quality_button_state()
    update_status_labels()

def update_status_labels():
    model_abbrev = {"base": "BASE", "small": "SML", "large-v3-turbo": "V3T"}
    abbrev = model_abbrev.get(current_model_name, current_model_name.upper()[:4])
    model_status.config(text=f"{abbrev} - {current_language}")

def update_quality_button_state():
    if use_gpu:
        quality_button.config(state="disabled")
    else:
        quality_button.config(state="normal")
    quality_button.config(text=cpu_quality_preset)

def cycle_quality_preset():
    global cpu_quality_preset
    presets = ["HI", "MED", "LO"]
    current_index = presets.index(cpu_quality_preset) if cpu_quality_preset in presets else 1
    cpu_quality_preset = presets[(current_index + 1) % len(presets)]
    config["cpu_quality_preset"] = cpu_quality_preset
    save_config(config)
    update_quality_button_state()
    if not use_gpu:
        start_managed_thread(target=initialize_model, name="InitializeModel_CPU_Quality")

# Recording
def toggle_recording():
    global recording_in_progress, audio_file_path

    if recording_in_progress:
        stop_ffmpeg_recording()
        recording_in_progress = False
        record_button.config(text="TRANSCRIBING", bootstyle="secondary", state="disabled")
        action_status.config(text="TRANSCRIPTION RUNNING...", anchor="center")

        # CRITICAL FIX: Only call app.update() if window is visible (not withdrawn)
        # When window is withdrawn, app.update() can be EXTREMELY slow (multi-second delays)
        # This was causing the asymmetry: fast when GUI open, slow when minimized to tray
        try:
            if app.state() != 'withdrawn':
                app.update()
        except:
            pass  # If app.update() fails, continue anyway

        time.sleep(1)

        if not audio_file_path or not os.path.exists(audio_file_path):
            action_status.config(text="RECORD ERROR: audio file missing", anchor="center")
            record_button.config(text="RECORD", bootstyle="warning", state="normal")
            return

        try:
            size_bytes = os.path.getsize(audio_file_path)
        except Exception:
            size_bytes = 0

        if size_bytes < 1024:
            action_status.config(text="RECORD ERROR: audio file too small", anchor="center")
            record_button.config(text="RECORD", bootstyle="warning", state="normal")
            return

        # MEMORY FIX: Use managed thread
        start_managed_thread(target=transcribe_audio, args=(audio_file_path,), name="Transcription")
    else:
        if model is None:
            action_status.config(text="MODEL NOT READY - LOADING...", anchor="center")
            start_managed_thread(target=initialize_model, name="InitializeModel")
            return

        audio_file_path, _ = get_output_paths("temp")

        try:
            ffmpeg_log_path = start_ffmpeg_recording(audio_file_path)
        except Exception as e:
            action_status.config(text=f"RECORD ERROR: {e}", anchor="center")
            return

        recording_in_progress = True
        record_button.config(text="STOP", bootstyle="danger", state="normal")
        action_status.config(text="RECORDING...", anchor="center")

# Transcription - just added Swiss German processing
def transcribe_audio(audio_file_path):
    global model, active_window_id

    if model is None:
        initialize_model()

    print(f"Starting transcription of: {audio_file_path}")

    file_size = os.path.getsize(audio_file_path)
    print(f"Audio file size: {file_size} bytes")

    # Get language code for Whisper
    whisper_language = language_codes.get(current_language, "en")

    try:
        # Transcribe with anti-hallucination parameter
        if use_gpu:
            beam_size = 5
        else:
            cpu_beam_map = {
                "HI": 5,
                "MED": 3,
                "LO": 2
            }
            beam_size = cpu_beam_map.get(cpu_quality_preset, 5)
        segments, info = model.transcribe(
            audio_file_path,
            language=whisper_language,
            beam_size=beam_size,
            condition_on_previous_text=False  # Critical: Prevents end-of-transcription hallucinations
        )
        # Convert to list and process, then explicitly free memory
        segment_list = list(segments)

        if not segment_list:
            transcription = "(No speech detected)"
        else:
            transcription = ''.join(segment.text for segment in segment_list).strip()

        # MEMORY FIX: Explicitly free segment list after transcription is complete
        segment_list = None
        del segments
        
        # Apply Swiss German conversion if needed
        transcription = swiss_german_convert(transcription)

        # Add trailing space for continuous dictation (so words don't run together)
        transcription = transcription + " "

        print(f"Transcription completed. Length: {len(transcription)} characters")
        
        # Save transcript
        _, transcript_file_path = get_output_paths(transcription)
        with open(transcript_file_path, "w", encoding="utf-8") as f:
            f.write(transcription)
        
        print(f"Transcript saved to: {transcript_file_path}")

        # Always copy to clipboard (as backup)
        app.after(0, lambda: pyperclip.copy(transcription))

        # AUTO-PASTE if enabled and we have a target window
        if config.get("auto_paste", True) and active_window_id:
            import time
            t_start = time.time()
            print(f"\n{'='*60}")
            print(f"📋 [{time.time():.3f}] AUTO-PASTE START")
            print(f"   Target window: {active_window_id}")
            print(f"   Text length: {len(transcription)} chars")
            print(f"   Paste method: {config.get('paste_method', 'clipboard')}")

            # Run paste in separate thread to avoid blocking GUI
            def do_paste():
                t_paste_start = time.time()
                print(f"🔄 [{time.time():.3f}] do_paste() thread STARTED (in background)")
                print(f"   Thread: {threading.current_thread().name}")
                print(f"   Daemon: {threading.current_thread().daemon}")

                paste_method = config.get("paste_method", "clipboard")
                print(f"📌 [{time.time():.3f}] Calling paste function: {paste_method}")

                paste_success = paste_text_clipboard(transcription, active_window_id)

                t_paste_end = time.time()
                paste_duration = t_paste_end - t_paste_start
                print(f"⏱️  [{time.time():.3f}] Paste function returned: success={paste_success}")
                print(f"   Paste duration: {paste_duration:.2f} seconds")

                if paste_success:
                    # Success - update status
                    print(f"✅ [{time.time():.3f}] Paste succeeded, updating GUI status")
                    app.after(0, lambda: action_status.config(
                        text=f"✅ PASTED: {len(transcription)} chars",
                        anchor="center"
                    ))
                    app.after(0, beep)

                    # Update tray icon to idle AFTER successful paste
                    if tray_icon:
                        app.after(0, lambda: tray_icon.update_status("idle"))
                        print(f"✅ [{time.time():.3f}] Tray icon set to idle (green)")
                else:
                    # FALLBACK: Show window with transcript
                    print(f"⚠️ [{time.time():.3f}] Auto-paste failed, using fallback")
                    app.after(0, lambda: show_window_fallback(transcription))

                    # Update tray icon to idle even if paste failed
                    if tray_icon:
                        app.after(0, lambda: tray_icon.update_status("idle"))

                print(f"🏁 [{time.time():.3f}] do_paste() thread COMPLETED")
                print(f"{'='*60}\n")

            # Start paste in background thread - don't block!
            # MEMORY FIX: Use managed thread tracking
            paste_thread = start_managed_thread(target=do_paste, name="PasteThread")

            t_thread_start = time.time()
            thread_start_duration = t_thread_start - t_start
            print(f"🚀 [{time.time():.3f}] Paste thread STARTED")
            print(f"   Thread start overhead: {thread_start_duration*1000:.2f} ms")
            print(f"   Thread alive: {paste_thread.is_alive()}")
            print(f"   Main thread continuing immediately (non-blocking)")
            print(f"{'='*60}\n")
        else:
            # Auto-paste disabled or no target window: just update GUI as before
            app.after(0, lambda: transcript_text.insert('end', transcription + "\n"))
            beep()
            app.after(0, lambda: action_status.config(text=f"SAVED: {os.path.basename(audio_file_path)}", anchor="center"))

            # Update tray icon to idle immediately (no paste happening)
            if tray_icon:
                app.after(0, lambda: tray_icon.update_status("idle"))

        # Refresh navigation after saving a new transcript (point to latest)
        app.after(0, lambda: refresh_transcript_list(select_latest=True))

        # DON'T update tray icon here - it's updated after paste completes in do_paste()
        # This ensures the icon stays gray until text is actually pasted

        # Clear active window ID for next recording
        active_window_id = None

    except Exception as e:
        print(f"Transcription error: {e}")
        err_msg = str(e)
        app.after(0, lambda msg=err_msg: action_status.config(text=f"TRANSCRIPTION ERROR: {msg}", anchor="center"))
    
    finally:
        app.after(0, lambda: record_button.config(text="RECORD", bootstyle="warning", state="normal"))

def copy_to_clipboard():
    full_text = transcript_text.get("1.0", 'end').strip()
    pyperclip.copy(full_text)
    action_status.config(text="CONTENT COPIED TO CLIPBOARD.", anchor="center")

def clear_window():
    transcript_text.delete("1.0", 'end')

def show_window_fallback(transcription):
    """Show window with transcript when auto-paste fails"""
    # Show the window
    app.deiconify()
    app.lift()
    app.focus_force()

    # Insert transcript into text area
    transcript_text.insert('end', transcription + "\n")

    # Update status
    action_status.config(
        text="⚠️ AUTO-PASTE FAILED - Text in window & clipboard",
        anchor="center"
    )

    print("💡 Fallback: Window shown with transcript")

# ================================
# Hotkey System Callbacks
# ================================

def on_hotkey_press():
    """Called when hotkey pressed - start recording"""
    global active_window_id, recording_in_progress

    print("\n" + "="*50)
    print("🔴 HOTKEY PRESS DETECTED")
    print(f"   Recording in progress: {recording_in_progress}")

    if recording_in_progress:
        print("   ⚠️ Already recording, ignoring")
        return  # Already recording

    # Save currently active window ID
    active_window_id = get_active_window_id()
    if active_window_id:
        print(f"   📍 Saved active window: {active_window_id}")
    else:
        print(f"   ⚠️ Could not save window ID")

    # Update tray icon
    if tray_icon:
        tray_icon.update_status("recording")
        print("   🎨 Tray icon updated to RED")

    # Start recording on the UI thread
    print("   🎤 Queuing toggle_recording() on UI thread...")
    app.after(0, toggle_recording)
    print("="*50 + "\n")

def on_hotkey_release():
    """Called when hotkey released - stop recording and transcribe"""
    global recording_in_progress

    print("\n" + "="*50)
    print("⚪ HOTKEY RELEASE DETECTED")
    print(f"   Recording in progress: {recording_in_progress}")

    if not recording_in_progress:
        print("   ⚠️ Not recording, ignoring")
        print("="*50 + "\n")
        return  # Not recording

    # Update tray icon
    if tray_icon:
        tray_icon.update_status("transcribing")
        print("   🎨 Tray icon updated to YELLOW")

    # Stop recording on the UI thread
    print("   🛑 Queuing toggle_recording() on UI thread...")
    app.after(0, toggle_recording)
    print("="*50 + "\n")

# ================================
# Tray Menu Callbacks
# ================================

def on_language_change_from_tray(lang_code):
    """Called when user changes language from tray menu"""
    global current_language
    current_language = lang_code

    # Update GUI button if window is visible
    language_button.config(text=lang_code)

    # Save to config
    config["language"] = lang_code
    save_config(config)

    print(f"🌍 Language changed to: {lang_code}")

def on_model_change_from_tray(model_name):
    """Called when user changes model from tray menu"""
    global current_model_name

    current_model_name = model_name

    # Update GUI button if window is visible
    model_abbrev = {"base": "BASE", "small": "SML", "large-v3-turbo": "V3T"}
    model_button.config(text=model_abbrev.get(model_name, model_name.upper()[:4]))

    # Save to config
    config["model"] = model_name
    save_config(config)

    # Reload model in background
    start_managed_thread(target=initialize_model, name="InitializeModel")
    print(f"???? Model changed to: {model_name}")

def on_gpu_toggle_from_tray(use_gpu_enabled):
    """Called when user toggles GPU/CPU from tray menu"""
    global use_gpu, current_model_name
    use_gpu = use_gpu_enabled

    # Update GUI button if window is visible
    if use_gpu:
        gpu_button.config(text="GPU", bootstyle="success")
    else:
        gpu_button.config(text="CPU", bootstyle="secondary")
        model_abbrev = {"base": "BASE", "small": "SML", "large-v3-turbo": "V3T"}
        model_button.config(text=model_abbrev.get(current_model_name, current_model_name.upper()[:4]))

    # Save to config
    config["use_gpu"] = use_gpu
    save_config(config)

    # Reload model in background
    start_managed_thread(target=initialize_model, name="InitializeModel")
    update_quality_button_state()
    print(f"???? Switched to: {'GPU' if use_gpu else 'CPU'} mode")

# ================================
# ================================
# NEW: Transcript Navigation (◀ ▶)
# ================================
transcript_dir = os.path.expanduser("~/Music/dictate")
transcript_files = []           # newest first
current_transcript_index = None # 0 == newest

def _find_transcript_files_sorted():
    """Return list of .txt transcripts sorted by mtime (newest first)."""
    ensure_directory(transcript_dir)
    files = glob.glob(os.path.join(transcript_dir, "*.txt"))
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)  # newest first
    return files

def update_nav_buttons():
    """Enable/disable nav buttons based on position."""
    if not transcript_files:
        prev_button.config(state="disabled")
        next_button.config(state="disabled")
        return
    # At newest (index 0): can't go newer (→), disable NEXT
    next_button.config(state=("disabled" if current_transcript_index in (None, 0) else "normal"))
    # At oldest (index == len-1): can't go older (←), disable PREV
    is_at_oldest = (current_transcript_index is not None and current_transcript_index >= len(transcript_files) - 1)
    prev_button.config(state=("disabled" if is_at_oldest else "normal"))

def update_nav_status_label():
    """Show compact status like '3 / 12' and timestamp of current file."""
    if not transcript_files or current_transcript_index is None:
        nav_status_label.config(text="— / —")
        return
    total = len(transcript_files)
    pos = current_transcript_index + 1  # human-friendly
    path = transcript_files[current_transcript_index]
    nav_status_label.config(text=f"{pos} / {total}")

def load_transcript_at_index(idx):
    """Load transcript text into the main text area; idx is 0=newest, growing older."""
    global current_transcript_index
    if not transcript_files:
        return
    if idx < 0 or idx >= len(transcript_files):
        beep()
        return
    current_transcript_index = idx
    path = transcript_files[current_transcript_index]
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        # Replace full content to switch into the text display mode directly
        transcript_text.delete("1.0", "end")
        transcript_text.insert("1.0", content)
        action_status.config(text=f"LOADED: {os.path.basename(path)}", anchor="center")
    except Exception as e:
        action_status.config(text=f"LOAD ERROR: {e}", anchor="center")
    finally:
        update_nav_status_label()
        update_nav_buttons()

def go_older():
    """Left arrow: move one step older in time (index + 1)."""
    if current_transcript_index is None:
        if transcript_files:
            load_transcript_at_index(0)  # start at newest
        return
    load_transcript_at_index(current_transcript_index + 1)

def go_newer():
    """Right arrow: move one step newer (index - 1)."""
    if current_transcript_index is None:
        if transcript_files:
            load_transcript_at_index(0)  # start at newest
        return
    load_transcript_at_index(current_transcript_index - 1)

def refresh_transcript_list(select_latest=False):
    """Rescan directory and optionally select newest as current index (without loading)."""
    global transcript_files, current_transcript_index
    transcript_files = _find_transcript_files_sorted()
    if not transcript_files:
        current_transcript_index = None
        update_nav_status_label()
        update_nav_buttons()
        return
    if select_latest:
        current_transcript_index = 0
    # Do not auto-load here; only set the counters/buttons
    update_nav_status_label()
    update_nav_buttons()

# ================================
# DPI Detection and Scaling Setup
# ================================
def detect_dpi_scaling():
    """
    Detect monitor DPI and calculate appropriate scaling factor

    Returns:
        tuple: (detected_dpi, auto_scale_factor, physical_info)
    """
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

        if hasattr(user32, "GetDpiForSystem"):
            detected_dpi = user32.GetDpiForSystem()
        else:
            LOGPIXELSX = 88
            hdc = user32.GetDC(0)
            detected_dpi = gdi32.GetDeviceCaps(hdc, LOGPIXELSX)
            user32.ReleaseDC(0, hdc)

        auto_scale = detected_dpi / 96.0
        return detected_dpi, auto_scale, {}
    except Exception as e:
        print(f"?????? DPI detection failed: {e}")
        return 96, 1.0, {}

# Detect DPI and set scaling factors
if enable_windows_dpi_awareness():
    print("✅ DPI awareness enabled")
else:
    print("⚠️ Could not enable DPI awareness")

detected_dpi, auto_scale, _ = detect_dpi_scaling()
font_scale = auto_scale
widget_scale = auto_scale
print(f"? DPI detected: {detected_dpi} DPI (scale: {auto_scale:.2f}x)")

set_windows_app_id("Dictate")
app = tk.Tk(className='dictate')
try:
    app.tk.call("tk", "scaling", 1.0)
    print("✅ Tk scaling set to 1.0 (manual DPI scaling)")
except Exception as e:
    print(f"⚠️ Could not set Tk scaling: {e}")

# ================================
# Font Configuration for Windows
# CRITICAL: Configure fonts BEFORE applying theme!
# ================================

# Calculate scaled font sizes based on font_scale (NOT widget_scale!)
# Base sizes (for 96 DPI): 10pt for default, 10pt for text
base_font_size = 10
base_text_font_size = 10

scaled_font_size = int(base_font_size * font_scale)
scaled_text_font_size = int(base_text_font_size * font_scale)

print(f"📝 Font sizes: Default={scaled_font_size}pt, Text={scaled_text_font_size}pt (base={base_font_size}pt, font scale={font_scale:.2f}x)")

# Windows font defaults
SYSTEM_FONT_SANS = "Segoe UI"
SYSTEM_FONT_MONO = "Consolas"

print(f"✅ Using system fonts: {SYSTEM_FONT_SANS} (sans), {SYSTEM_FONT_MONO} (mono)")

# Configure ALL named fonts for consistent appearance
# This is critical for proper rendering across all tkinter/ttk widgets
font_names = [
    "TkDefaultFont",    # Default font for all widgets
    "TkTextFont",       # Font for text widgets
    "TkFixedFont",      # Monospace font
    "TkMenuFont",       # Menu items
    "TkHeadingFont",    # Headings in trees/lists
    "TkCaptionFont",    # Caption/small text
    "TkSmallCaptionFont",  # Smaller captions
    "TkIconFont",       # Icon labels
    "TkTooltipFont"     # Tooltips
]

configured_fonts = []
for font_name in font_names:
    try:
        font = tkfont.nametofont(font_name)
        if "Fixed" in font_name:
            # Use monospace for fixed-width fonts
            font.configure(family=SYSTEM_FONT_MONO, size=scaled_font_size)
        elif "Caption" in font_name:
            # Slightly smaller for captions
            caption_size = max(8, int(scaled_font_size * 0.9))
            font.configure(family=SYSTEM_FONT_SANS, size=caption_size)
        else:
            # Use sans-serif for all other fonts
            font.configure(family=SYSTEM_FONT_SANS, size=scaled_font_size)
        configured_fonts.append(font_name)
    except Exception as e:
        print(f"⚠️  Could not configure {font_name}: {e}")

print(f"✅ Configured {len(configured_fonts)} named fonts BEFORE theme setup")

# NOW apply theme AFTER fonts are configured
style = tb.Style(theme='sandstone')  # Apply ttkbootstrap theme to existing Tk window
print(f"✅ Applied ttkbootstrap 'sandstone' theme")

app.title("Dictate - Large-v3-Turbo + Swiss German")

# Scale window geometry based on widget_scale (NOT font_scale!)
# Original: 200x1080+1720+0
base_width = 200
base_height = 1080
screen_w = app.winfo_screenwidth()
screen_h = app.winfo_screenheight()
base_x = max(0, screen_w - base_width)
base_y = 0
if base_height > screen_h:
    base_height = screen_h

scaled_width = min(int(base_width * widget_scale), screen_w)
scaled_height = min(int(base_height * widget_scale), screen_h)
scaled_x = max(0, screen_w - scaled_width)
scaled_y = max(0, min(base_y, screen_h - scaled_height))

app.geometry(f"{scaled_width}x{scaled_height}+{scaled_x}+{scaled_y}")
print(f"🖼️  Window geometry: {scaled_width}x{scaled_height}+{scaled_x}+{scaled_y} (widget scale: {widget_scale:.2f}x)")

app.attributes('-topmost', True)  # Keep window always on top
print("✅ Window class set to 'dictate' via tk.Tk(className=...)")

def force_window_visible():
    """Ensure the window is visible and positioned on-screen."""
    try:
        app.deiconify()
        app.lift()
        app.focus_force()
        app.update_idletasks()
        w = app.winfo_width() or scaled_width
        h = app.winfo_height() or scaled_height
        sw = app.winfo_screenwidth()
        sh = app.winfo_screenheight()
        w = min(w, sw)
        h = min(h, sh)
        x = max(0, min(app.winfo_x(), sw - w))
        y = max(0, min(app.winfo_y(), sh - h))
        app.geometry(f"{w}x{h}+{x}+{y}")
    except Exception as e:
        print(f"⚠️  Could not force window visible: {e}")

app.force_window_visible = force_window_visible

# Set application icon
icon_dir = os.path.join(os.path.dirname(__file__), "icon_variants")
icon_ico = os.path.join(os.path.dirname(__file__), "dictate.ico")
icons = []
try:
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon_path = os.path.join(icon_dir, f"dictate_icon_{size}x{size}.png")
        if os.path.exists(icon_path):
            icons.append(tk.PhotoImage(file=icon_path))
    if icons:
        app.icons = icons  # keep references
        app.iconphoto(True, *icons)
    if os.path.exists(icon_ico):
        app.iconbitmap(icon_ico)
    if icons or os.path.exists(icon_ico):
        print("✅ Application icon loaded")
    else:
        print("Warning: Icon files not found")
except Exception as e:
    print(f"Warning: Could not load icon: {e}")

# NOTE: Font configuration already done BEFORE theme setup above
# No additional font configuration needed here

def on_closing():
    """Clean up all resources before closing"""
    global model, hotkey_manager, tray_icon

    print("🧹 Cleaning up resources...")

    # Stop hotkey listener
    if hotkey_manager:
        try:
            hotkey_manager.stop()
            print("✅ Hotkey listener stopped")
        except:
            pass

    # Stop tray icon
    if tray_icon:
        try:
            tray_icon.stop()
            print("✅ Tray icon stopped")
        except Exception as e:
            print(f"⚠️ Error stopping tray icon: {e}")

    # Kill any running ffmpeg processes
    stop_ffmpeg_recording()

    # Clean up the Whisper model and free GPU memory
    if model is not None:
        try:
            del model
            model = None
            print("✅ Model freed")
        except:
            pass

    # Clear GPU cache if torch is available
    if HAS_TORCH:
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print("✅ GPU cache cleared")
        except:
            pass

    # Destroy the window
    try:
        app.quit()  # Stop mainloop
        app.destroy()  # Destroy window
        print("✅ App closed cleanly")
    except:
        pass

def on_window_close():
    """Window X button → hide to tray (don't quit)"""
    if config.get("start_minimized", True):
        # If we're using tray mode, hide window instead of quitting
        app.withdraw()
        if tray_icon:
            tray_icon.update_status("idle")
        print("🔕 Window hidden to tray")
    else:
        # If not using tray mode, quit normally
        on_closing()

app.protocol("WM_DELETE_WINDOW", on_window_close)

# Top button frame
top_button_frame = tb.Frame(app, borderwidth=0, relief="flat")
top_button_frame.pack(pady=(10, 5))

record_button = tb.Button(top_button_frame, text="RECORD", bootstyle="warning", width=10,
                        command=toggle_recording)
record_button.pack(side="left", padx=1)

language_button = tb.Button(top_button_frame, text=current_language, bootstyle="info", width=6,
                           command=toggle_language)
language_button.pack(side="left", padx=1)

# Control buttons frame
button_frame = tb.Frame(app, borderwidth=0, relief="flat")
button_frame.pack(pady=5)

wipe_button = tb.Button(button_frame, text="WIPE", bootstyle="danger", width=4, command=clear_window)
wipe_button.pack(side="left", padx=1)

clipboard_button = tb.Button(button_frame, text="CLIP", bootstyle="success", width=4, command=copy_to_clipboard)
clipboard_button.pack(side="left", padx=1)

# Model name abbreviations for compact display
model_abbrev = {"base": "BASE", "small": "SML", "large-v3-turbo": "V3T"}
model_button = tb.Button(button_frame, text=model_abbrev.get(current_model_name, current_model_name.upper()[:4]),
                         bootstyle="secondary", width=4, command=cycle_model)
model_button.pack(side="left", padx=1)

quality_button = tb.Button(button_frame, text=cpu_quality_preset, bootstyle="secondary", width=4,
                          command=cycle_quality_preset)
quality_button.pack(side="left", padx=1)

# Status display (no bootstyle to avoid white background)
action_status = tb.Label(app, text="APP READY", anchor="center")
action_status.pack(pady=5, fill="x")

# Separator (no horizontal padding to avoid white borders)
separator = tb.Separator(app, orient="horizontal")
separator.pack(fill="x", padx=0, pady=(0, 5))

# Text display area
text_frame = tb.Frame(app, borderwidth=0, relief="flat")
text_frame.pack(pady=5, expand=True, fill="both")
# Get app background color for seamless blending
app_bg = app.cget("bg")
# Use DPI-scaled font size for text area
transcript_text = Text(text_frame, wrap="word", font=(SYSTEM_FONT_SANS, scaled_text_font_size), bd=0, relief="flat", bg=app_bg)
transcript_text.pack(expand=True, fill="both")
transcript_text.config(borderwidth=0, highlightthickness=0)

# NEW: Navigation frame (under the text display)
nav_frame = tb.Frame(app, borderwidth=0, relief="flat")
nav_frame.pack(pady=(0, 6), fill="x")

prev_button = tb.Button(nav_frame, text="◀", width=4, bootstyle="secondary", command=go_older)
prev_button.pack(side="left", padx=1)

nav_status_label = tb.Label(nav_frame, text="— / —", anchor="center")
nav_status_label.pack(side="left", expand=True, fill="x")

next_button = tb.Button(nav_frame, text="▶", width=4, bootstyle="secondary", command=go_newer)
next_button.pack(side="right", padx=1)

# Bottom frame
bottom_frame = tb.Frame(app, borderwidth=0, relief="flat")
bottom_frame.pack(side="bottom", fill="x")

# Bottom status with abbreviated model names
model_abbrev_init = {"base": "BASE", "small": "SML", "large-v3-turbo": "V3T"}
abbrev_init = model_abbrev_init.get(current_model_name, current_model_name.upper()[:4])
model_status = tb.Label(bottom_frame, text=f"{abbrev_init} - {current_language}", anchor="center")
model_status.pack(side="left", fill="x", expand=True)

# Set initial GPU button state based on user preference (not detection)
initial_gpu_text = "GPU" if use_gpu else "CPU"
initial_gpu_style = "success" if use_gpu else "secondary"

gpu_button = tb.Button(bottom_frame, text=initial_gpu_text,
                      bootstyle=initial_gpu_style, width=6,
                      command=toggle_gpu)
gpu_button.pack(side="right", padx=1)

update_quality_button_state()

# Crash handler (keep your existing one)
def show_crash_dialog(exc_type, exc_value, exc_traceback):
    error_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    crash_dir = os.path.expanduser("~/Music/dictate/logs")
    os.makedirs(crash_dir, exist_ok=True)
    crash_file = os.path.join(crash_dir, f"crash_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
    
    with open(crash_file, 'w', encoding='utf-8') as f:
        f.write(f"CRASH REPORT - {datetime.now()}\n")
        f.write(f"Exception: {str(exc_value)}\n\n")
        f.write(error_text)
    
    messagebox.showerror("Application Error", 
                       f"An unexpected error occurred:\n{str(exc_value)}\n\n"
                       f"Details have been saved to:\n{crash_file}")
    
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = show_crash_dialog

# Start the Application
print(f"🚀 Starting dictate.py with {current_model_name} + Swiss German...")
print(f"🔧 GPU Mode: {'Enabled' if use_gpu else 'Disabled'}")
gpu_error = gpu_info.get("error") or "Unknown error"
print(f"🎯 GPU Status: {'✅ Available' if gpu_info['available'] else '❌ ' + gpu_error}")
if not gpu_info['available']:
    print("💡 Will show detailed GPU error in text area - you can toggle to CPU if needed")

# Initialize tray icon
tray_icon = TrayIcon(
    app,
    on_closing,
    on_language_change_from_tray,
    on_model_change_from_tray,
    on_gpu_toggle_from_tray
)
tray_icon.current_language = current_language  # Sync initial state
tray_icon.current_model = current_model_name
tray_icon.use_gpu = use_gpu
tray_icon.start()

# Initialize hotkey manager
hotkey_manager = HotkeyManager(config, on_hotkey_press, on_hotkey_release)
hotkey_manager.start()

# Start minimized if configured
if config.get("start_minimized", False):
    app.withdraw()
    print("🔕 Started minimized to tray")
else:
    print("🔔 Started with window visible")
    app.after(200, force_window_visible)

start_managed_thread(target=initialize_model, name="InitializeModel")

# Initial scan of available transcripts for navigation
refresh_transcript_list(select_latest=False)

if __name__ == "__main__":
    app.mainloop()

