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
$pythonExe = Join-Path $envRoot "pythonw.exe"
if (-not (Test-Path $pythonExe)) {
    throw "pythonw.exe not found. Run install.ps1 first."
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
    & $pythonExe "$scriptDir\\dictate.py"
} finally {
    Pop-Location
}
