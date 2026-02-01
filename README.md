# Dictate - Real-time Speech-to-Text Transcription (Windows Only)

A lightweight, GPU-accelerated speech-to-text transcription application optimized for Swiss German and general German language, with automatic fallback to CPU-only systems.

## Features

- GPU-accelerated transcription (NVIDIA/CUDA) with CPU fallback
- Large-v3-turbo model by default (best quality)
- Swiss German support (DE-CH) with DE/EN options
- Compact UI designed for side-monitor placement
- Smart auto-paste using clipboard + hotkeys
- Transcript history with timestamped files

## Installation

### Quick Start (PowerShell)

```powershell
# Clone or download the repository
cd C:\path\to\dictate

# Allow scripts for this session and run installer
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1

# Optional: force environment selection
.\install.ps1 -ForceGpu
.\install.ps1 -ForceCpu

# Optional: download models into the repo (for offline moves)
.\install.ps1 -DownloadModels

# Create Start Menu shortcut (for correct Taskbar icon/grouping)
.\create_shortcut.ps1
```

### Manual Environment Setup

```powershell
conda env create -f environment-win-cpu.yml
conda activate fasterwhisper
python -c "import faster_whisper; import ttkbootstrap; print('Ready!')"
```

## Usage

```powershell
.\start_dictate.ps1
```

Transcripts are saved in `~/Music/dictate/`.
If `./models/` exists, Dictate will load models from there first.

## Troubleshooting

- If audio device detection fails, set `audio_device` in `~/.config/dictate/config.json`.
- If GPU fails, switch to CPU mode from the tray menu.

## License

See `LICENSE`.
