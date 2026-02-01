$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$minicondaDir = Join-Path $env:USERPROFILE "miniconda3"
$anacondaDir = Join-Path $env:USERPROFILE "anaconda3"

$condaBase = $minicondaDir
if (-not (Test-Path (Join-Path $minicondaDir "Scripts\\conda.exe"))) {
    if (Test-Path (Join-Path $anacondaDir "Scripts\\conda.exe")) {
        $condaBase = $anacondaDir
    }
}

$envRoot = Join-Path $condaBase "envs\\fasterwhisper"
$pythonExe = Join-Path $envRoot "python.exe"
$pythonwExe = Join-Path $envRoot "pythonw.exe"
if (-not (Test-Path $pythonExe)) { throw "python.exe not found. Run install.ps1 first." }
if (-not (Test-Path $pythonwExe)) { throw "pythonw.exe not found. Run install.ps1 first." }

$startMenuDir = Join-Path $env:APPDATA "Microsoft\\Windows\\Start Menu\\Programs"
$shortcutPath = Join-Path $startMenuDir "Dictate.lnk"
$iconPath = Join-Path $scriptDir "dictate.ico"
$dictatePy = Join-Path $scriptDir "dictate.py"

$env:DICTATE_SHORTCUT = $shortcutPath
$env:DICTATE_TARGET = $pythonwExe
$env:DICTATE_ARGS = ('"' + $dictatePy + '"')
$env:DICTATE_WORKDIR = $scriptDir
$env:DICTATE_ICON = $iconPath
$env:DICTATE_APPID = "Dictate"
$env:KMP_DUPLICATE_LIB_OK = "TRUE"

$pyLines = @(
    "import os",
    "from win32com.client import Dispatch",
    "from win32com.propsys import propsys",
    "lnk = os.environ['DICTATE_SHORTCUT']",
    "lnk = os.path.abspath(lnk)",
    "target = os.environ['DICTATE_TARGET']",
    "args = os.environ['DICTATE_ARGS']",
    "workdir = os.environ['DICTATE_WORKDIR']",
    "icon = os.environ['DICTATE_ICON']",
    "appid = os.environ['DICTATE_APPID']",
    "shell = Dispatch('WScript.Shell')",
    "shortcut = shell.CreateShortcut(lnk)",
    "shortcut.TargetPath = target",
    "shortcut.Arguments = args",
    "shortcut.WorkingDirectory = workdir",
    "if os.path.exists(icon):",
    "    shortcut.IconLocation = icon",
    "shortcut.Save()",
    "shortcut = None",
    "import time",
    "time.sleep(0.2)",
    "gps_readwrite = 2",
    "ps = propsys.SHGetPropertyStoreFromParsingName(lnk, None, gps_readwrite, propsys.IID_IPropertyStore)",
    "key = propsys.PSGetPropertyKeyFromName('System.AppUserModel.ID')",
    "ps.SetValue(key, propsys.PROPVARIANTType(appid))",
    "ps.Commit()",
    "print('Shortcut updated:', lnk)",
    "print('AppUserModelID set to:', appid)"
)
$py = $pyLines -join "`n"
$py | & $pythonExe -
