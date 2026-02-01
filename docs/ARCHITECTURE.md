# Dictate App Architecture

**For humans:** Code structure and system design overview. Ask AI to explain details if needed.

**For AI:** Use this as reference when modifying code structure or explaining architecture.


## STRUCTURE

```
_AA_DICTATE/
├── dictate.py                   # Entry point, main app logic
├── config.py                    # Settings management
├── hotkey_manager.py            # Hotkey detection (pynput)
├── window_manager.py            # Window focus (xdotool)
├── tray_icon_appindicator.py    # System tray (AppIndicator3) [PRIMARY]
├── tray_icon.py                 # System tray (fallback)
├── install.sh                   # Installation + validation
├── start_dictate.sh             # Launcher
├── environment-cuda12.yml       # Conda env (GPU)
├── environment-cpu.yml          # Conda env (CPU)
├── settings.json                # User preferences (persistent)
├── ~/Music/dictate/
│   ├── transcripts/             # Saved .txt files
│   └── logs/                    # Application logs
└── assets/icons/
    ├── dictate_green.png        # Idle
    ├── dictate_red.png          # Recording
    └── dictate_gray.png         # Transcribing
```


## DATA FLOW

### Transcription Pipeline

```
User → Hotkey → Record → Transcribe → Save → Paste
```

**Details:**
1. **Hotkey Detection** (hotkey_manager.py)
   - Listen: Right Ctrl key
   - Trigger: `toggle_recording()`

2. **Audio Recording** (dictate.py)
   - PyAudio captures microphone
   - Store in memory buffer
   - Visual feedback via tray icon

3. **Transcription** (dictate.py)
   - faster-whisper processes audio
   - Model: large-v3-turbo/small/base
   - Language: DE-CH/DE-DE/EN

4. **Output** (dictate.py)
   - Save: ~/Music/dictate/transcripts/TIMESTAMP.txt
   - Paste: xdotool (if enabled)


## KEY COMPONENTS

### dictate.py
**Purpose:** Main application logic

**Critical sections:**
```python
# Line ~130: Model initialization
def initialize_model(model_size):
    # CRITICAL: Withdrawn-window fix
    if app.state() != 'withdrawn':
        app.update()

# Line ~250: Recording toggle
def toggle_recording():
    # CRITICAL: Withdrawn-window fix
    if app.state() != 'withdrawn':
        app.update()

# Line ~350: Transcription
def transcribe_audio(audio_data):
    # Uses faster-whisper
    # Returns text
```

**Dependencies:**
- PyAudio (audio capture)
- faster-whisper (transcription)
- PyAV (audio decoding)
- pynput (hotkey)
- ttkbootstrap (GUI)

### tray_icon_appindicator.py
**Purpose:** System tray integration (Gnome/Unity)

**Key functions:**
```python
create_tray_icon()      # Initialize tray
update_icon(state)      # Change icon (green/red/gray)
create_menu()           # Build context menu
```

**Menu items:**
- Toggle Recording
- Model Selection (large/small/base)
- Language Selection (DE-CH/DE-DE/EN)
- Settings
- Quit

### hotkey_manager.py
**Purpose:** Global hotkey detection

**Implementation:**
- Uses pynput.keyboard
- Listens for Right Ctrl
- Calls dictate.toggle_recording()

### config.py
**Purpose:** Settings persistence

**Storage:** settings.json

**Settings:**
```python
{
    "model": "large-v3-turbo",
    "language": "de",
    "auto_paste": true,
    "save_transcripts": true
}
```


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
```

### System (apt packages)

```
python3-gi                # Python GObject
gir1.2-ayatanaappindicator3-0.1  # Tray icon
xdotool                   # Auto-paste
```


## ENVIRONMENT VARIABLES

```bash
TTKBOOTSTRAP_FONT_MANAGER=tk   # GUI font rendering
```


## STATE MANAGEMENT

### App States

```python
IDLE        → Green icon, ready to record
RECORDING   → Red icon, capturing audio
TRANSCRIBING→ Gray icon, processing audio
```

### GUI States

```python
'normal'    → Window visible
'withdrawn' → Window minimized to tray
```

**CRITICAL:** Must check state before `app.update()`:
```python
if app.state() != 'withdrawn':
    app.update()
```


## ERROR HANDLING

### PyAV Missing
```python
try:
    import av
except ImportError:
    # install.sh should catch this
    exit("PyAV required")
```

### Model Load Failure
```python
try:
    model = WhisperModel(size)
except Exception:
    # Fallback to smaller model
    model = WhisperModel("small")
```

### Audio Device Missing
```python
try:
    stream = audio.open()
except Exception:
    # Show error dialog
    # Disable recording
```


## CONFIGURATION

### User Settings (settings.json)
- Model selection
- Language preference
- Auto-paste enabled/disabled
- Save transcripts enabled/disabled

### System Settings (environment variables)
- TTKBOOTSTRAP_FONT_MANAGER
- Conda environment activation

### Install Settings (install.sh)
- Bill of Materials validation
- Dependency versions


## EXTENSION POINTS

### Adding New Language
1. Update config.py language options
2. Add menu item in tray_icon_appindicator.py
3. Test transcription quality

### Adding New Model
1. Update config.py model options
2. Add menu item in tray_icon_appindicator.py
3. Test performance

### Custom Hotkey
1. Modify hotkey_manager.py listener
2. Update settings.json schema
3. Add GUI preference


## TESTING

### Manual Tests
```bash
# Test 1: GUI mode
python dictate.py
# Record via button

# Test 2: Hotkey mode
# Minimize to tray
# Press Right Ctrl

# Test 3: Model switching
# Change model via tray menu
# Record again
```

### Smoke Tests
```python
test_pyav_installed()
test_model_loads()
test_audio_device()
test_withdrawn_fix()
```


## DEPLOYMENT

### Fresh Install
```bash
git clone REPO
cd _AA_DICTATE
./install.sh
```

### Update
```bash
git pull origin main
./install.sh  # Validates and updates only what changed
```


## KNOWN ISSUES

| Issue | Cause | Fix Location |
|-------|-------|--------------|
| Slow hotkey mode | Withdrawn window blocking | dictate.py:257, 384 |
| No tray icon | Wayland | Use XWayland |
| PyAV missing | Not in environment | install.sh checks |
| Font rendering | Missing env var | TTKBOOTSTRAP_FONT_MANAGER=tk |


