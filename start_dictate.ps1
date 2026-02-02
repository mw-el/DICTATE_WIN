$ErrorActionPreference = "Stop"

function Move-ConsoleOffscreen {
    try {
        Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
    [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr hWnd, int X, int Y, int nWidth, int nHeight, bool bRepaint);
}
"@
        $h = [Win32]::GetConsoleWindow()
        if ($h -ne [IntPtr]::Zero) {
            [Win32]::MoveWindow($h, 10000, 10000, 200, 200, $false) | Out-Null
        }
    } catch {
        # ignore
    }
}

Move-ConsoleOffscreen

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
$pythonExe = Join-Path $envRoot "pythonw.exe"
if (-not (Test-Path $pythonExe)) {
    throw "pythonw.exe not found. Run install.ps1 first."
}
$launchPy = Join-Path $scriptDir "launch.py"
if (-not (Test-Path $launchPy)) {
    throw "launch.py not found. Run install.ps1 first."
}

$env:PATH = "$envRoot;$envRoot\\Scripts;$envRoot\\Library\\bin;$env:PATH"
$env:CONDA_DEFAULT_ENV = "fasterwhisper"
$env:CONDA_PREFIX = $envRoot
$env:TTKBOOTSTRAP_FONT_MANAGER = "tk"
$env:KMP_DUPLICATE_LIB_OK = "TRUE"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

Push-Location $scriptDir
try {
    & $pythonExe $launchPy
} finally {
    Pop-Location
}
