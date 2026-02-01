# Dictate App - Project-Specific Maintenance (Windows)

**For humans:** Additional maintenance checks specific to this voice transcription app. Run alongside generic maintenance checklist.

**For AI:** Execute these Dictate-specific validation tasks during maintenance.

## VALIDATION TASKS

### 1. Audio & Transcription

**Test models:**
```powershell
.\start_dictate.ps1
# Test: large-v3-turbo, small, base
# Languages: DE-CH (Swiss German), DE-DE, EN
# Record 10s sample, verify quality
```

**Check:**
- [ ] Model downloads work
- [ ] Swiss German transcription quality acceptable
- [ ] ffmpeg detects DirectShow microphone
- [ ] No audio buffer underruns

### 2. Desktop Integration

**Test tray icon:**
```powershell
.\start_dictate.ps1
# Verify: Icon appears in system tray
# Test: All menu items work
# Test: Hotkey (right Ctrl) triggers recording
```

**Check:**
- [ ] Tray icon visible in Windows system tray
- [ ] Menu items functional
- [ ] Hotkey detection works
- [ ] Auto-paste works (clipboard + pynput)

### 3. GUI State Management

**Test withdrawn-window bug fix:**
```powershell
# Test A: GUI open
.\start_dictate.ps1
# Click Record, speak, verify <2s delay

# Test B: GUI minimized (hotkey mode)
# Close window (hides to tray)
# Press right Ctrl, speak, release
# Verify <2s delay (not 5-10s!)
```

**Check:**
- [ ] Both modes equally fast
- [ ] No multi-second blocking
- [ ] Fix active: `Select-String "if app.state\(\) != 'withdrawn'" dictate.py` shows 2+ matches

### 4. Dependencies

**Critical packages:**
```powershell
.\start_dictate.ps1
# In the conda environment:
python -c "import av; print('PyAV:', av.__version__)"           # Must be 16.0.1
python -c "import faster_whisper; print('faster-whisper')"      # 1.2.0
python -c "import torch; print('PyTorch:', torch.__version__)"  # 2.5.1
```

**Check:**
- [ ] PyAV==16.0.1 (CRITICAL for audio)
- [ ] faster-whisper==1.2.0
- [ ] PyTorch==2.5.1
- [ ] TTKBOOTSTRAP_FONT_MANAGER=tk (env var set in start_dictate.ps1)

### 5. File System

**Verify directories:**
```powershell
Test-Path "$env:USERPROFILE\Music\dictate\transcripts"
Test-Path "$env:USERPROFILE\Music\dictate\logs"
```

**Check:**
- [ ] ~/Music/dictate/transcripts/ exists
- [ ] ~/Music/dictate/logs/ exists
- [ ] Permissions allow write

### 6. Configuration

**Test config loading:**
- [ ] Config created at ~/.config/dictate/config.json on first run
- [ ] Language selection persists across restarts
- [ ] Model selection persists across restarts

## PROJECT-SPECIFIC FILES

### dictate.py

**Critical sections:**
- `detect_gpu_availability()` — GPU/CUDA detection
- `initialize_model()` — withdrawn-window fix
- `toggle_recording()` — withdrawn-window fix
- Hotkey detection: pynput listener

**Validation:**
```powershell
Select-String "if app.state\(\) != 'withdrawn'" dictate.py
# Should show 2+ locations
```

### tray_icon.py

**Test:** Right-click tray icon, verify all menu items work.

### install.ps1

**Verify matches:**
- Conda environment creation
- Start Menu shortcut creation (calls create_shortcut.ps1)
- Directory creation (~/Music/dictate/)

## RELEASE CHECKLIST

**Before release:**
- [ ] All models tested (large-v3-turbo, small, base)
- [ ] Swiss German quality verified
- [ ] Tray icon works on Windows
- [ ] Hotkey mode fast (withdrawn-window fix verified)
- [ ] PyAV 16.0.1 in environment files
- [ ] install.ps1 creates conda env + Start Menu shortcut
- [ ] smoke_test.py covers imports + GPU + directories
- [ ] README.md shows correct model sizes
- [ ] CHANGELOG.md documents changes

## KNOWN ISSUES

| Issue | System | Fix |
|-------|--------|-----|
| Slow hotkey mode | Windows | Apply withdrawn-window fix |
| Audio glitches | Some USB mics | Set audio_device in config |
| Blurry UI | High-DPI displays | DPI awareness in dictate.py |
