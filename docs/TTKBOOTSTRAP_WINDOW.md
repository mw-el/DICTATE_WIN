# ttkbootstrap Window & Icon Integration

**For humans:** Fix for missing app icons in Linux dock/taskbar when using ttkbootstrap.

**For AI:** Correct pattern for ttkbootstrap window creation with WM_CLASS support.

---

## PROBLEM

**Using `tb.Window()` → generic icon in dock**

**Cause:** `tb.Window()` doesn't support `className` parameter needed for WM_CLASS matching.

---

## SOLUTION

**Use `tk.Tk()` + `tb.Style()`:**

```python
import tkinter as tk
import ttkbootstrap as tb

# CORRECT
app = tk.Tk(className='app-name')  # Sets WM_CLASS
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

---

## WHY IT MATTERS

**Desktop integration requires WM_CLASS match:**

**.desktop file:**
```desktop
StartupWMClass=app-name
```

**Python code:**
```python
app = tk.Tk(className='app-name')  # Must match
```

**Result:** Custom icon appears in dock.

---

## VERIFICATION

**Check WM_CLASS:**
```bash
# Start app, then:
xprop WM_CLASS  # Click on window
# Should show: "app-name", "app-name"
```

**If wrong:** Rebuild with correct className parameter.

---

## COMPLETE PATTERN

```python
import tkinter as tk
import ttkbootstrap as tb

# Initialize with WM_CLASS
app = tk.Tk(className='my-app')

# Apply ttkbootstrap theme
style = tb.Style(theme='sandstone')

# Set window properties
app.title("My Application")
app.geometry("800x600")

# Optional: Set window icon
icon_path = "/path/to/icon.png"
icon = tk.PhotoImage(file=icon_path)
app.iconphoto(True, icon)

# Build UI with ttkbootstrap widgets
frame = tb.Frame(app)
frame.pack(fill='both', expand=True)

button = tb.Button(frame, text="Click", bootstyle="success")
button.pack(pady=20)

label = tb.Label(frame, text="Hello", font=('Segoe UI', 12))
label.pack()

app.mainloop()
```

---

## DESKTOP FILE

```desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=My App
Icon=/path/to/icon.png
Exec=/path/to/python /path/to/app.py
StartupWMClass=my-app
Categories=Utility;
Terminal=false
```

**Critical:** `StartupWMClass` must match `className` parameter exactly.

---

## TROUBLESHOOTING

| Issue | Cause | Fix |
|-------|-------|-----|
| Generic icon | className not set | Use tk.Tk(className='...') |
| WM_CLASS wrong | Using tb.Window() | Switch to tk.Tk() + tb.Style() |
| Theme not applied | Forgot tb.Style() | Add style = tb.Style(theme='...') |
| Icon file missing | Wrong path | Use absolute path, verify exists |

---

## POST-CREATION WM_CLASS FAILS

**Don't try this:**
```python
# DOESN'T WORK
app = tb.Window(themename='sandstone')
app.tk.call('wm', 'class', app._w, "my-app")
# Appears to execute but doesn't set WM_CLASS correctly
```

**Why:** WM_CLASS must be set at window creation time.

---

## ADDITIONAL REQUIREMENTS

**XFT Tk build:**
```bash
conda install -c conda-forge "tk=8.6.13=xft*"
```

**Font manager env var:**
```bash
export TTKBOOTSTRAP_FONT_MANAGER=tk
```

**See also:** DESKTOP_INTEGRATION.md, TKINTER_FONTS.md
