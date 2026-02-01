$ErrorActionPreference = "Stop"

$minicondaDir = Join-Path $env:USERPROFILE "miniconda3"
$anacondaDir = Join-Path $env:USERPROFILE "anaconda3"
$condaExe = Join-Path $minicondaDir "Scripts\\conda.exe"

if (-not (Test-Path $condaExe)) {
    $altConda = Join-Path $anacondaDir "Scripts\\conda.exe"
    if (Test-Path $altConda) {
        $condaExe = $altConda
    }
}

if (-not (Test-Path $condaExe)) {
    throw "conda.exe not found. Nothing to uninstall."
}

& $condaExe env remove -n fasterwhisper
Write-Host "Removed conda environment 'fasterwhisper'."
Write-Host "User data preserved in $env:USERPROFILE\\Music\\dictate\\"
