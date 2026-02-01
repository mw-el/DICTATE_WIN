# ttkbootstrap Window & Icon Integration (Windows)

**For humans:** Fix for missing app icons and taskbar grouping when using ttkbootstrap on Windows.

**For AI:** Correct pattern for ttkbootstrap window creation with AppUserModelID support.

## PROBLEM

**Using `tb.Window()` → no control over taskbar grouping or icon**

**Cause:** `tb.Window()` doesn't support `className` parameter.

## SOLUTION

**Use `tk.Tk()` + `tb.Style()`:**

```python
import tkinter as tk
import ttkbootstrap as tb
import ctypes

# Set AppUserModelID for taskbar grouping BEFORE creating window
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Dictate")

# CORRECT
app = tk.Tk(className='dictate')
style = tb.Style(theme='sandstone')  # Apply theme

# All ttkbootstrap widgets work normally
button = tb.Button(app, text="Click")
button.pack()

app.mainloop()
```

**WRONG:**
```python
# DON'T DO THIS
app = tb.Window(themename='sandstone')
# No way to set className!
```

## WHY IT MATTERS

**Windows taskbar integration requires:**

1. `SetCurrentProcessExplicitAppUserModelID("Dictate")` — groups windows in taskbar
2. Start Menu shortcut with matching AppUserModelID — set via `create_shortcut.ps1`
3. `.ico` file for taskbar/window icon

## START MENU SHORTCUT

The `create_shortcut.ps1` script creates a shortcut with:

- Target: `powershell.exe` calling `start_dictate.ps1`
- Working directory: script folder
- Icon: `dictate.ico`
- AppUserModelID: "Dictate" (set via pywin32 propsys)

## COMPLETE PATTERN

```python
import tkinter as tk
import ttkbootstrap as tb
import ctypes
import os

# Set AppUserModelID
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Dictate")

# Initialize with className
app = tk.Tk(className='dictate')

# Apply ttkbootstrap theme
style = tb.Style(theme='sandstone')

# Set window icon
icon_ico = os.path.join(os.path.dirname(__file__), "dictate.ico")
if os.path.exists(icon_ico):
    app.iconbitmap(icon_ico)

# Multi-size PNG icons for better rendering
icon_dir = os.path.join(os.path.dirname(__file__), "icon_variants")
icons = []
for size in (16, 24, 32, 48, 64, 128, 256):
    path = os.path.join(icon_dir, f"dictate_icon_{size}x{size}.png")
    if os.path.exists(path):
        icons.append(tk.PhotoImage(file=path))
if icons:
    app.iconphoto(True, *icons)

app.mainloop()
```

## TROUBLESHOOTING

| Issue | Cause | Fix |
|-------|-------|-----|
| Generic taskbar icon | AppUserModelID not set | Call SetCurrentProcessExplicitAppUserModelID |
| Wrong icon | .ico not loaded | Use app.iconbitmap() with .ico file |
| Theme not applied | Forgot tb.Style() | Add style = tb.Style(theme='...') |
| Multiple taskbar entries | AppUserModelID mismatch | Ensure code + shortcut use same ID |
