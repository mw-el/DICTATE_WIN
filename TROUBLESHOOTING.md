# Dictate - Troubleshooting (Windows Only)

## Common Issues

### Audio capture latency / first words cut off (Windows)

Dictate uses the low-latency WASAPI capture path via `sounddevice`.
If you still notice delay or missing first words:

1. Update the environment (so sounddevice/soundfile are installed).
2. Check the default Windows input device (Sound Settings).
3. Restart Dictate.

Note: Recordings are saved as `.wav` files.

### Conda Terms of Service error (CondaToSNonInteractiveError)

If installation fails with a message about accepting Terms of Service for the default channels, run:

```powershell
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/msys2
```

Then re-run:

```powershell
.\install.ps1
```

### 1) "faster_whisper module not found"
- Ensure you launched via `start_dictate.ps1` or activated the conda environment.

### 2) No audio device detected
- Verify the default Windows input device in Sound Settings.
- Reinstall the environment to restore `sounddevice`/`soundfile`.

### 3) GPU not available
- Run `nvidia-smi` to confirm the driver (NVIDIA only).
- If GPU fails, switch to CPU mode in the tray menu.
- AMD/ROCm GPUs are not supported by the Windows CUDA pipeline used here.

### 4) Auto-paste not working
- Some apps block simulated input. Try another paste key rule in `paste_rules.json`.

## Logs

Crash logs are stored in:

```
~/Music/dictate/logs/
```
