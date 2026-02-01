# Dictate - Troubleshooting (Windows Only)

## Common Issues

### 1) "faster_whisper module not found"
- Ensure you launched via `start_dictate.ps1` or activated the conda environment.

### 2) No audio device detected
- Open `~/.config/dictate/config.json` and set `audio_device` to your DirectShow device name.
- To list devices, run:
  ```powershell
  ffmpeg -hide_banner -list_devices true -f dshow -i dummy
  ```

### 3) GPU not available
- Run `nvidia-smi` to confirm the driver.
- If GPU fails, switch to CPU mode in the tray menu.

### 4) Auto-paste not working
- Some apps block simulated input. Try another paste key rule in `paste_rules.json`.

## Logs

Crash logs are stored in:

```
~/Music/dictate/logs/
```
