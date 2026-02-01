# Tkinter Font Rendering on Linux

**For humans:** Fixes for pixelated fonts in tkinter apps. Ask AI for details.

**For AI:** Requirements and fixes for professional font rendering in tkinter/ttkbootstrap.


## CRITICAL REQUIREMENT

**Install XFT-enabled Tk:**
```bash
conda install -c conda-forge "tk=8.6.13=xft*" -y
```

**Verify:**
```bash
conda list tk | grep "^tk"
# GOOD: tk  8.6.13  xft_*
# BAD:  tk  8.6.13  noxft_*
```

**Why:** Without XFT, fonts are pixelated regardless of configuration.


## ENVIRONMENT VARIABLE

**Set before starting app:**
```bash
export TTKBOOTSTRAP_FONT_MANAGER=tk
```

**In conda environment:**
```bash
conda env config vars set TTKBOOTSTRAP_FONT_MANAGER=tk -n myenv
conda deactivate && conda activate myenv
```

**Verify:**
```bash
conda env config vars list -n myenv | grep TTKBOOTSTRAP
# Should show: TTKBOOTSTRAP_FONT_MANAGER = tk
```


## CODE CONFIGURATION

**Default font:**
```python
import tkinter as tk
import ttkbootstrap as tb

app = tk.Tk()
style = tb.Style(theme='sandstone')

# Set default font
default_font = ('Segoe UI', 10)
app.option_add('*Font', default_font)
```

**Specific widgets:**
```python
label = tk.Label(app, text="Text", font=('Segoe UI', 12))
button = tk.Button(app, text="Button", font=('Segoe UI', 10, 'bold'))
```

**System font detection:**
```python
import tkinter.font as tkfont

# Get system default
system_font = tkfont.nametofont("TkDefaultFont")
print(f"System font: {system_font.actual()}")

# Use system font
app.option_add('*Font', system_font)
```


## DPI SCALING

**Auto-detect:**
```python
def get_dpi_scale():
    root = tk.Tk()
    root.withdraw()
    dpi = root.winfo_fpixels('1i')
    root.destroy()
    return dpi / 96.0  # 96 DPI is baseline

scale = get_dpi_scale()
base_font_size = 10
scaled_size = int(base_font_size * scale)
```

**Manual override:**
```python
app.tk.call('tk', 'scaling', 2.0)  # 2x scaling
```


## COMMON ISSUES

| Issue | Cause | Fix |
|-------|-------|-----|
| Pixelated fonts | No XFT build | Install tk=8.6.13=xft* |
| Inconsistent sizes | No env var | Set TTKBOOTSTRAP_FONT_MANAGER=tk |
| Too small | High DPI | Detect DPI and scale fonts |
| Wrong font family | Not specified | Set default font explicitly |
| Blurry text | Wrong DPI scaling | Use integer font sizes |


## VALIDATION

**Check XFT:**
```bash
conda list tk | grep xft
# Should have "xft" in build string
```

**Check env var:**
```bash
echo $TTKBOOTSTRAP_FONT_MANAGER
# Should print: tk
```

**Visual test:**
```python
import tkinter as tk
import ttkbootstrap as tb

app = tk.Tk()
style = tb.Style(theme='sandstone')

label = tk.Label(app, text="The quick brown fox", font=('Segoe UI', 14))
label.pack(padx=20, pady=20)

app.mainloop()
# Text should be crisp and clear
```


## RECOMMENDED SETTINGS

**For production apps:**
```bash
# In environment.yml
variables:
  TTKBOOTSTRAP_FONT_MANAGER: tk

# Or in install.sh
conda env config vars set TTKBOOTSTRAP_FONT_MANAGER=tk -n myenv
```

```python
# In app code
import tkinter as tk
import ttkbootstrap as tb

app = tk.Tk()
style = tb.Style(theme='sandstone')

# Set default font
app.option_add('*Font', ('Segoe UI', 10))

# Or detect DPI
dpi_scale = get_dpi_scale()
font_size = int(10 * dpi_scale)
app.option_add('*Font', ('Segoe UI', font_size))
```


