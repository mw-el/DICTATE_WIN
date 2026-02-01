# Dictate App Architecture (Windows Only)

**For humans:** Code structure and system design overview. Ask AI to explain details if needed.

**For AI:** Use this as reference when modifying code structure or explaining architecture.


## STRUCTURE

```
_AA_DICTATE_WIN/
├── dictate.py                   # Entry point, main app logic
├── config.py                    # Settings management (~/.config/dictate/config.json)
├── hotkey_manager.py            # Global hotkey detection (pynput)
├── window_manager.py            # Window focus + paste (Win32 APIs)
├── tray_icon.py                 # System tray (pystray)
├── paste_rules.json             # Rule-based paste key selection
├── install.ps1                  # Installation + conda env setup
├── create_shortcut.ps1          # Start Menu shortcut creation
├── start_dictate.ps1            # Launcher (sets env vars, runs app)
├── uninstall.ps1                # Remove conda environment
├── download_models.ps1          # Pre-download models for offline use
├── smoke_test.py                # Basic functionality tests
├── environment-win-gpu.yml      # Conda env (GPU/CUDA)
├── environment-win-cpu.yml      # Conda env (CPU)
├── environment.yml              # Alias for environment-win-cpu.yml
├── dictate.ico                  # Application icon
├── settings.json                # User preferences (persistent, gitignored)
├── ~/Music/dictate/
│   ├── transcripts/             # Saved .txt files
│   └── logs/                    # Application + crash logs
├── assets/icons/
│   ├── dictate_green.png        # Idle
│   ├── dictate_red.png          # Recording
│   └── dictate_gray.png         # Transcribing
├── icon_variants/               # Multi-size PNG icons for window
├── models/                      # Optional local model cache (gitignored)
├── scripts/
│   └── compare_models.py        # Model comparison utility
└── docs/                        # Documentation
```


## DATA FLOW

### Transcription Pipeline

```
User → Hotkey → Record → Transcribe → Save → Paste
```

**Details:**
1. **Hotkey Detection** (hotkey_manager.py)
   - Listen: Right Ctrl key (configurable)
   - Trigger: `toggle_recording()`

2. **Audio Recording** (dictate.py)
   - ffmpeg captures microphone via DirectShow
   - Stores as MP3 file
   - Visual feedback via tray icon (red)

3. **Transcription** (dictate.py)
   - faster-whisper processes audio
   - Model: large-v3-turbo/small/base
   - Language: DE-CH/DE-DE/EN

4. **Output** (dictate.py)
   - Save: ~/Music/dictate/transcripts/TIMESTAMP.txt
   - Paste: clipboard + simulated keypress via pynput


## KEY COMPONENTS

### dictate.py
**Purpose:** Main application logic

**Critical sections:**
- `detect_gpu_availability()` — CUDA detection and GPU test
- `initialize_model()` — Model loading with withdrawn-window fix
- `toggle_recording()` — Recording start/stop with withdrawn-window fix
- `transcribe_audio()` — Transcription + auto-paste

**Dependencies:**
- faster-whisper (transcription)
- ffmpeg (audio capture via DirectShow)
- PyAV (audio decoding)
- pynput (hotkey + paste simulation)
- ttkbootstrap (GUI)

### tray_icon.py
**Purpose:** System tray integration (pystray)

**Key functions:**
- `start()` — Initialize tray icon
- `update_status(state)` — Change icon (green/red/gray)
- `create_menu()` — Build context menu

**Menu items:**
- Show/Hide Window
- Language Selection (DE-CH/DE-DE/EN)
- Model Selection (large-v3-turbo/small/base)
- Processing (GPU/CPU)
- Quit

### hotkey_manager.py
**Purpose:** Global hotkey detection via pynput

### config.py
**Purpose:** Settings persistence (~/.config/dictate/config.json)

### window_manager.py
**Purpose:** Win32 window focus + rule-based paste key selection


## DEPENDENCIES

### Critical (exact versions required)

```yaml
Python: 3.10.14
PyAV: 16.0.1              # CRITICAL for audio
PyTorch: 2.5.1
faster-whisper: 1.2.0
ctranslate2: 4.6.0
ttkbootstrap: 1.14.7
pynput: 1.8.1
pyperclip: 1.11.0
pywin32                    # Windows COM/shortcut APIs
```

### System

```
Miniconda/Anaconda         # Environment management
ffmpeg                     # Audio recording (bundled in conda env)
```


## ENVIRONMENT VARIABLES

Set by `start_dictate.ps1`:
```powershell
TTKBOOTSTRAP_FONT_MANAGER=tk   # GUI font rendering
KMP_DUPLICATE_LIB_OK=TRUE      # Avoid duplicate OpenMP errors
PYTHONUTF8=1                    # UTF-8 output
PYTHONIOENCODING=utf-8          # UTF-8 encoding
```


## STATE MANAGEMENT

### App States

```
IDLE         → Green icon, ready to record
RECORDING    → Red icon, capturing audio
TRANSCRIBING → Gray icon, processing audio
```

### GUI States

```
'normal'    → Window visible
'withdrawn' → Window minimized to tray
```

**CRITICAL:** Must check state before `app.update()`:
```python
if app.state() != 'withdrawn':
    app.update()
```


## KNOWN ISSUES

| Issue | Cause | Fix Location |
|-------|-------|--------------|
| Slow hotkey mode | Withdrawn window blocking | dictate.py (withdrawn check) |
| Font rendering | Missing env var | TTKBOOTSTRAP_FONT_MANAGER=tk |
| Blurry UI | No DPI awareness | dictate.py (enable_windows_dpi_awareness) |
