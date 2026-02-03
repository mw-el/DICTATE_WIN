param(
    [string]$ModelsZip = "",
    [string]$TargetDir = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

if (-not $ModelsZip) {
    $releaseDir = Join-Path $repoRoot "release"
    $latest = Get-ChildItem -Path $releaseDir -Filter "DictateModels_*.zip" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($latest) {
        $ModelsZip = $latest.FullName
    } else {
        throw "ModelsZip not specified and no DictateModels_*.zip found in: $releaseDir"
    }
}

if (-not (Test-Path $ModelsZip)) {
    throw "Models zip not found: $ModelsZip"
}

if (-not $TargetDir) {
    # Default: extract next to Dictate.exe if run from an extracted portable folder,
    # otherwise extract into the repo root (dev convenience).
    $TargetDir = Join-Path $repoRoot "models"
}

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
Write-Host "Extracting models -> $TargetDir"
Expand-Archive -Path $ModelsZip -DestinationPath $TargetDir -Force
Write-Host "OK"
