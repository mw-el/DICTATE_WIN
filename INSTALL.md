# Dictate - Installation Guide (Windows Only)

This Windows-only installer creates a reproducible environment for Dictate using Miniconda.

---

## Quick Install

### Prerequisites

1. **Windows 10/11**
2. **Miniconda** (the installer will install it if missing)
3. **Optional: NVIDIA GPU (CUDA)** for faster transcription

### Installation (PowerShell)

```powershell
# 1. Clone or download the repository
cd C:\path\to\dictate

# 2. Allow scripts for this session and run installer
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

Optional: download models into the repo (for offline moves):

```powershell
.\install.ps1 -DownloadModels
```

Or run directly:

```powershell
.\download_models.ps1
```

Start Menu shortcut (Taskbar pin with correct icon):

```powershell
.\create_shortcut.ps1
```

Force a specific environment:

```powershell
# Force GPU environment (NVIDIA/CUDA only)
.\install.ps1 -ForceGpu

# Force CPU environment
.\install.ps1 -ForceCpu
```

**That's it.** The script handles everything else.

---

## What Gets Installed

### Conda Environment

- Python 3.10.14
- PyTorch 2.5.1 (GPU or CPU; GPU requires NVIDIA/CUDA)
- faster-whisper, ctranslate2, av
- ttkbootstrap, pynput, pyperclip, pystray, pillow

### Directories

- `~/Music/dictate/transcripts/`
- `~/Music/dictate/logs/`
- `./models/` (optional local model cache)
- Start Menu shortcut `Dictate` (created by installer)

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
