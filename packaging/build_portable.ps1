param(
    [switch]$IncludeModels,
    [switch]$SplitModels,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$specPath = Join-Path $PSScriptRoot "dictate_portable.spec"
$distRoot = Join-Path $repoRoot "dist"
$workRoot = Join-Path $repoRoot "build"
$releaseRoot = Join-Path $repoRoot "release"
$versionFile = Join-Path $repoRoot "VERSION"

if (-not (Test-Path $specPath)) { throw "Spec not found: $specPath" }

# Native command helper: avoid PowerShell treating stderr as terminating errors.
function Invoke-Native {
    param(
        [Parameter(Mandatory=$true)][string]$Exe,
        [Parameter(Mandatory=$true)][string[]]$Args,
        [switch]$Quiet
    )
    $tmpOut = New-TemporaryFile
    $tmpErr = New-TemporaryFile
    try {
        $p = Start-Process -FilePath $Exe -ArgumentList $Args -NoNewWindow -Wait -PassThru `
            -RedirectStandardOutput $tmpOut.FullName -RedirectStandardError $tmpErr.FullName

        if (-not $Quiet) {
            if (Test-Path $tmpOut.FullName) {
                Get-Content $tmpOut.FullName | ForEach-Object { Write-Host $_ }
            }
            if (Test-Path $tmpErr.FullName) {
                Get-Content $tmpErr.FullName | ForEach-Object { Write-Host $_ }
            }
        }

        return $p.ExitCode
    } finally {
        try { Remove-Item -Force $tmpOut.FullName -ErrorAction SilentlyContinue } catch {}
        try { Remove-Item -Force $tmpErr.FullName -ErrorAction SilentlyContinue } catch {}
    }
}

function New-ZipFromDir {
    param(
        [Parameter(Mandatory=$true)][string]$SourceDir,
        [Parameter(Mandatory=$true)][string]$ZipPath,
        [string]$Compression = "store"  # store|deflate
    )

    if (-not (Test-Path $SourceDir)) { throw "Zip source not found: $SourceDir" }
    $zipParent = Split-Path -Parent $ZipPath
    if ($zipParent -and -not (Test-Path $zipParent)) { New-Item -ItemType Directory -Force -Path $zipParent | Out-Null }
    if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }

    $tmpPy = New-TemporaryFile
    try {
        $py = @"
import os, sys, zipfile
src = sys.argv[1]
dst = sys.argv[2]
mode = sys.argv[3].lower()
compression = zipfile.ZIP_STORED if mode == "store" else zipfile.ZIP_DEFLATED
with zipfile.ZipFile(dst, "w", compression=compression, allowZip64=True) as z:
    for root, _dirs, files in os.walk(src):
        for fn in files:
            p = os.path.join(root, fn)
            arc = os.path.relpath(p, src)
            z.write(p, arc)
print("OK zip:", dst)
"@
        Set-Content -Path $tmpPy.FullName -Value $py -Encoding utf8
        $code = Invoke-Native -Exe $pythonExe -Args @($tmpPy.FullName, $SourceDir, $ZipPath, $Compression)
        if ($code -ne 0) { throw "zip creation failed (exit=$code): $ZipPath" }
    } finally {
        try { Remove-Item -Force $tmpPy.FullName -ErrorAction SilentlyContinue } catch {}
    }
}

function Remove-DirSafe {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [int]$Retries = 3
    )
    if (-not (Test-Path $Path)) { return }
    for ($i = 1; $i -le $Retries; $i++) {
        try {
            cmd /c "attrib -R -S -H /S /D `"$Path`"" | Out-Null
        } catch {}
        try {
            Remove-Item -Recurse -Force $Path -ErrorAction Stop
            return
        } catch {
            if ($i -eq $Retries) { throw }
            Start-Sleep -Seconds 2
        }
    }
}

# Ensure known runtime env vars are present during analysis/build (prevents OpenMP duplicate crash)
$env:KMP_DUPLICATE_LIB_OK = "TRUE"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$version = "dev"
if (Test-Path $versionFile) {
    $v = (Get-Content $versionFile -TotalCount 1).Trim()
    if ($v) { $version = $v }
}

if ($Clean) {
    if (Test-Path $distRoot) { Remove-DirSafe $distRoot }
    if (Test-Path $workRoot) { Remove-DirSafe $workRoot }
}

# Find the repo's conda env python (same logic as start_dictate.ps1 / install.ps1)
$minicondaDir = Join-Path $env:USERPROFILE "miniconda3"
$anacondaDir = Join-Path $env:USERPROFILE "anaconda3"

$condaBase = $minicondaDir
if (-not (Test-Path (Join-Path $minicondaDir "envs\\fasterwhisper\\python.exe"))) {
    if (Test-Path (Join-Path $anacondaDir "envs\\fasterwhisper\\python.exe")) {
        $condaBase = $anacondaDir
    }
}

$envRoot = Join-Path $condaBase "envs\\fasterwhisper"
$pythonExe = Join-Path $envRoot "python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Build python not found: $pythonExe (run install.ps1 first, or create the env)"
}

# Ensure pyinstaller exists in that env (install if missing)
$code = Invoke-Native -Exe $pythonExe -Args @("-m","pip","show","pyinstaller") -Quiet
if ($code -ne 0) {
    Write-Host "Installing PyInstaller into build env..."
    $code = Invoke-Native -Exe $pythonExe -Args @("-m","pip","install","--upgrade","pip")
    if ($code -ne 0) { throw "pip upgrade failed (exit=$code)" }
    $code = Invoke-Native -Exe $pythonExe -Args @("-m","pip","install","pyinstaller")
    if ($code -ne 0) { throw "pyinstaller install failed (exit=$code)" }
}

New-Item -ItemType Directory -Force -Path $releaseRoot | Out-Null

Write-Host "Building portable app (version=$version) ..."
$old = Get-Location
Set-Location $repoRoot
try {
    # Ensure previous build output is fully removed to avoid PyInstaller access errors
    $distDictate = Join-Path $distRoot "Dictate"
    if (Test-Path $distDictate) { Remove-DirSafe $distDictate }

    $code = Invoke-Native -Exe $pythonExe -Args @("-m","PyInstaller","--noconfirm","--clean","--distpath",$distRoot,"--workpath",$workRoot,$specPath)
} finally {
    Set-Location $old
}
if ($code -ne 0) { throw "PyInstaller build failed (exit=$code)" }

$appDir = Join-Path $distRoot "Dictate"
if (-not (Test-Path $appDir)) { throw "Build output not found: $appDir" }

# Safety: ensure archive/ never ends up in the shipped folder
$accidentalArchive = Join-Path $appDir "archive"
if (Test-Path $accidentalArchive) {
    Write-Host "Removing accidental archive folder from build output: $accidentalArchive"
    Remove-Item -Recurse -Force $accidentalArchive
}

$modelsDir = Join-Path $repoRoot "models"
if ($SplitModels) {
    if (Test-Path $modelsDir) {
        $modelsZip = Join-Path $releaseRoot ("DictateModels_{0}.zip" -f $version)
        if (Test-Path $modelsZip) { Remove-Item -Force $modelsZip }
        Write-Host "Creating models zip: $modelsZip"
        New-ZipFromDir -SourceDir $modelsDir -ZipPath $modelsZip -Compression store
    } else {
        Write-Host "Models directory not found, skipping models zip: $modelsDir"
    }

    $zipNoModels = Join-Path $releaseRoot ("DictatePortable_{0}_win64_nomodels.zip" -f $version)
    if (Test-Path $zipNoModels) { Remove-Item -Force $zipNoModels }
    Write-Host "Creating portable zip (no models): $zipNoModels"
    New-ZipFromDir -SourceDir $appDir -ZipPath $zipNoModels -Compression deflate
    Write-Host "OK"
    exit 0
}

if ($IncludeModels) {
    if (-not (Test-Path $modelsDir)) {
        throw "IncludeModels set, but models directory not found: $modelsDir (run .\\download_models.ps1 first)"
    }
    $targetModels = Join-Path $appDir "models"
    if (Test-Path $targetModels) { Remove-Item -Recurse -Force $targetModels }
    Write-Host "Copying models -> $targetModels (this can take a while) ..."
    Copy-Item -Recurse -Force $modelsDir $targetModels
}

$zip = Join-Path $releaseRoot ("DictatePortable_{0}_win64.zip" -f $version)
if (Test-Path $zip) { Remove-Item -Force $zip }
Write-Host "Creating portable zip: $zip"
New-ZipFromDir -SourceDir $appDir -ZipPath $zip -Compression store

Write-Host "OK"
