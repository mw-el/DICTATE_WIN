# Tkinter Font Rendering (Windows)

**For humans:** Font configuration for crisp rendering in tkinter apps on Windows.

**For AI:** Requirements and patterns for professional font rendering in tkinter/ttkbootstrap on Windows.

## ENVIRONMENT VARIABLE

**Set before starting app (done by start_dictate.ps1):**
```powershell
$env:TTKBOOTSTRAP_FONT_MANAGER = "tk"
```

**In conda environment:**
```powershell
conda env config vars set TTKBOOTSTRAP_FONT_MANAGER=tk -n fasterwhisper
```

## CODE CONFIGURATION

**System fonts on Windows:**
```python
SYSTEM_FONT_SANS = "Segoe UI"
SYSTEM_FONT_MONO = "Consolas"
```

**Configure named fonts BEFORE applying theme:**
```python
import tkinter as tk
import tkinter.font as tkfont
import ttkbootstrap as tb

app = tk.Tk(className='dictate')

# Configure all named fonts first
for font_name in ["TkDefaultFont", "TkTextFont", "TkMenuFont", ...]:
    font = tkfont.nametofont(font_name)
    font.configure(family="Segoe UI", size=scaled_font_size)

# THEN apply theme
style = tb.Style(theme='sandstone')
```

## DPI SCALING

**Windows DPI detection:**
```python
def detect_dpi_scaling():
    user32 = ctypes.WinDLL("user32")
    if hasattr(user32, "GetDpiForSystem"):
        detected_dpi = user32.GetDpiForSystem()
    else:
        hdc = user32.GetDC(0)
        detected_dpi = ctypes.WinDLL("gdi32").GetDeviceCaps(hdc, 88)
        user32.ReleaseDC(0, hdc)
    return detected_dpi / 96.0
```

**DPI awareness (call before creating Tk window):**
```python
def enable_windows_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()
```

## COMMON ISSUES

| Issue | Cause | Fix |
|-------|-------|-----|
| Blurry text | No DPI awareness | Call SetProcessDpiAwareness before Tk |
| Inconsistent sizes | No env var | Set TTKBOOTSTRAP_FONT_MANAGER=tk |
| Too small | High DPI | Detect DPI and scale font sizes |
| Wrong font family | Not specified | Set default font explicitly |
