param(
    [switch]$ForceGpu,
    [switch]$ForceCpu,
    [switch]$DownloadModels
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$envName = "fasterwhisper"
$minicondaDir = Join-Path $env:USERPROFILE "miniconda3"
$anacondaDir = Join-Path $env:USERPROFILE "anaconda3"
$condaExe = Join-Path $minicondaDir "Scripts\\conda.exe"

function Write-Info($msg) { Write-Host $msg }

function Ensure-CondaTosAccepted($condaExePath) {
    $channels = @(
        "https://repo.anaconda.com/pkgs/main",
        "https://repo.anaconda.com/pkgs/r",
        "https://repo.anaconda.com/pkgs/msys2"
    )
    foreach ($ch in $channels) {
        try {
            & $condaExePath tos accept --override-channels --channel $ch | Out-Null
        } catch {
            Write-Info "Note: Could not auto-accept conda ToS for $ch (continuing)."
        }
    }
}

if (-not (Test-Path $condaExe)) {
    $altConda = Join-Path $anacondaDir "Scripts\\conda.exe"
    if (Test-Path $altConda) {
        $condaExe = $altConda
    }
}

if (-not (Test-Path $condaExe)) {
    Write-Info "Miniconda not found. Installing..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $installerUrl = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
    $installerPath = Join-Path $env:TEMP "Miniconda3-latest-Windows-x86_64.exe"
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
    Start-Process -FilePath $installerPath -ArgumentList "/S","/D=$minicondaDir" -Wait
    Remove-Item -Force $installerPath
    $condaExe = Join-Path $minicondaDir "Scripts\\conda.exe"
}

if (-not (Test-Path $condaExe)) {
    throw "conda.exe not found after installation."
}

Ensure-CondaTosAccepted $condaExe

$envFileGpu = Join-Path $scriptDir "environment-win-gpu.yml"
$envFileCpu = Join-Path $scriptDir "environment-win-cpu.yml"
$envFile = $envFileCpu

$useGpu = $false
if ($ForceGpu -and $ForceCpu) {
    throw "Use only one of -ForceGpu or -ForceCpu."
}

if ($ForceGpu) {
    $useGpu = $true
    Write-Info "ForceGpu specified. Using GPU environment."
    try {
        & nvidia-smi | Out-Null
    } catch {
        Write-Info "⚠️  nvidia-smi not found. GPU will not work until NVIDIA drivers are installed."
    }
} elseif ($ForceCpu) {
    $useGpu = $false
    Write-Info "ForceCpu specified. Using CPU environment."
} else {
    try {
        & nvidia-smi | Out-Null
        if ($LASTEXITCODE -eq 0) { $useGpu = $true }
    } catch {
        $useGpu = $false
    }
}

if ($useGpu -and (Test-Path $envFileGpu)) {
    $envFile = $envFileGpu
    Write-Info "GPU environment selected. Using environment-win-gpu.yml"
} else {
    Write-Info "GPU not detected (or not available). Using environment-win-cpu.yml"
}

$envList = & $condaExe env list
$envExists = $false
foreach ($line in $envList) {
    if ($line -match "^\s*$envName\s+") { $envExists = $true; break }
}

if ($envExists) {
    Write-Info "Updating conda environment '$envName'..."
    & $condaExe env update -n $envName -f $envFile
} else {
    Write-Info "Creating conda environment '$envName'..."
    & $condaExe env create -f $envFile
}

$musicBase = Join-Path $env:USERPROFILE "Music\\dictate"
New-Item -ItemType Directory -Force -Path (Join-Path $musicBase "transcripts") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $musicBase "logs") | Out-Null

Write-Info ""
Write-Info "Install complete."
Write-Info "Run: .\\start_dictate.ps1"
Write-Info "Audio capture uses WASAPI via sounddevice (low latency)."

if ($DownloadModels) {
    Write-Info ""
    Write-Info "Downloading models to .\\models ..."
    & (Join-Path $scriptDir "download_models.ps1")
}

Write-Info ""
Write-Info "Creating Start Menu shortcut..."
try {
    & (Join-Path $scriptDir "create_shortcut.ps1")
} catch {
    Write-Info "⚠️  Shortcut creation failed. You can run .\\create_shortcut.ps1 manually."
}
