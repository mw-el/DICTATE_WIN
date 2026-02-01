# Dictate - Installation Guide (Windows Only)

This Windows-only installer creates a reproducible environment for Dictate using Miniconda.

---

## Quick Install

### Prerequisites

1. **Windows 10/11**
2. **Miniconda** (the installer will install it if missing)
3. **Optional: NVIDIA GPU** for faster transcription

### Installation (PowerShell)

```powershell
# 1. Clone or download the repository
cd C:\_AA_DICTATE

# 2. Allow scripts for this session and run installer
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

**That's it.** The script handles everything else.

---

## What Gets Installed

### Conda Environment

- Python 3.10.14
- PyTorch 2.5.1 (GPU or CPU)
- faster-whisper, ctranslate2, av
- ttkbootstrap, pynput, pyperclip, pystray, pillow

### Directories

- `~/Music/dictate/transcripts/`
- `~/Music/dictate/logs/`

---

## Running the App

```powershell
.\start_dictate.ps1
```

---

## Updating

Re-run the installer after pulling updates:

```powershell
.\install.ps1
```

---

## Uninstall

```powershell
.\uninstall.ps1
```

User data in `~/Music/dictate/` is preserved.
