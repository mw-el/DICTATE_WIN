$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$shortcutPath = Join-Path $startMenuDir "Dictate.lnk"
$iconPath = Join-Path $scriptDir "dictate.ico"
$startScript = Join-Path $scriptDir "start_dictate.ps1"

if (-not (Test-Path $startScript)) {
    throw "start_dictate.ps1 not found in $scriptDir"
}

# Create shortcut using WScript.Shell COM object
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
$shortcut.Arguments = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$startScript`""
$shortcut.WorkingDirectory = $scriptDir
if (Test-Path $iconPath) {
    $shortcut.IconLocation = "$iconPath,0"
}
$shortcut.Save()

Write-Host "Shortcut created: $shortcutPath"

# Set AppUserModelID for correct taskbar grouping
# This requires pywin32 from the conda environment
$minicondaDir = Join-Path $env:USERPROFILE "miniconda3"
$anacondaDir = Join-Path $env:USERPROFILE "anaconda3"

$condaBase = $minicondaDir
if (-not (Test-Path (Join-Path $minicondaDir "Scripts\conda.exe"))) {
    if (Test-Path (Join-Path $anacondaDir "Scripts\conda.exe")) {
        $condaBase = $anacondaDir
    }
}

$envRoot = Join-Path $condaBase "envs\fasterwhisper"
$pythonExe = Join-Path $envRoot "python.exe"

if (Test-Path $pythonExe) {
    $env:DICTATE_SHORTCUT = $shortcutPath
    $env:DICTATE_APPID = "Dictate"
    $env:KMP_DUPLICATE_LIB_OK = "TRUE"

    $pyLines = @(
        "import os",
        "from win32com.propsys import propsys",
        "lnk = os.path.abspath(os.environ['DICTATE_SHORTCUT'])",
        "appid = os.environ['DICTATE_APPID']",
        "import time",
        "time.sleep(0.2)",
        "gps_readwrite = 2",
        "ps = propsys.SHGetPropertyStoreFromParsingName(lnk, None, gps_readwrite, propsys.IID_IPropertyStore)",
        "key = propsys.PSGetPropertyKeyFromName('System.AppUserModel.ID')",
        "ps.SetValue(key, propsys.PROPVARIANTType(appid))",
        "ps.Commit()",
        "print('AppUserModelID set to:', appid)"
    )
    $py = $pyLines -join "`n"
    $py | & $pythonExe -
} else {
    Write-Host "Note: python.exe not found in conda env. AppUserModelID not set (run install.ps1 first)."
}
