param(
    [string]$ArchiveTag = "",
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $ArchiveTag) {
    $ArchiveTag = (Get-Date).ToString("yyyy-MM-dd")
}

$archiveBase = Join-Path $repoRoot ("archive\\_cleanup_{0}" -f $ArchiveTag)
New-Item -ItemType Directory -Force -Path $archiveBase | Out-Null

function Ensure-ParentDir($path) {
    $parent = Split-Path -Parent $path
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
}

function Move-Relative($relativePath) {
    $src = Join-Path $repoRoot $relativePath
    if (-not (Test-Path $src)) { return }

    $dst = Join-Path $archiveBase $relativePath
    Ensure-ParentDir $dst
    if ($WhatIf) {
        Write-Host "WHATIF move: $relativePath -> archive\\_cleanup_$ArchiveTag\\$relativePath"
        return
    }

    Move-Item -Force $src $dst
    Add-Content -Path (Join-Path $archiveBase "MOVED.txt") -Value $relativePath -Encoding utf8
}

function Move-Dir($relativeDir) {
    $src = Join-Path $repoRoot $relativeDir
    if (-not (Test-Path $src)) { return }

    $dst = Join-Path $archiveBase $relativeDir
    Ensure-ParentDir $dst
    if ($WhatIf) {
        Write-Host "WHATIF move dir: $relativeDir -> archive\\_cleanup_$ArchiveTag\\$relativeDir"
        return
    }

    Move-Item -Force $src $dst
    Add-Content -Path (Join-Path $archiveBase "MOVED.txt") -Value ("{0}\\" -f $relativeDir) -Encoding utf8
}

# Directories that are not needed for runtime/portable builds
Move-Dir "docs"
Move-Dir "scripts"
Move-Dir "icon_variants"

# Obvious non-runtime design/working files
Move-Relative "_transcribe.psd"
Move-Relative "dictate.psd"
Move-Relative "dictate.svg"
Move-Relative "dictate.png"
Move-Relative "tk"

# Icon/tooling helpers (kept as history, not needed for running the app)
Move-Relative "ICON_REBUILD_GUIDE.md"
Move-Relative "create_all_icons.py"
Move-Relative "create_icon_pngs.py"
Move-Relative "generate_ico.py"
Move-Relative "check_ico.py"
Move-Relative "make_icon.py"
Move-Relative "make_icon_robust.py"
Move-Relative "rebuild_dictate_icon.py"
Move-Relative "verify_ico.ps1"
Move-Relative "generate_icons_now.ps1"
Move-Relative "fix_icon_now.ps1"
Move-Relative "make_pngs.ps1"
Move-Relative "restart_with_new_icon.ps1"

# Outdated / install-legacy logs and smoke tests
Move-Relative "install_issues.log"
Move-Relative "smoke_test.py"

# Remove accidental build placeholder file if present
$nulPath = Join-Path $repoRoot "nul"
if (Test-Path $nulPath) {
    if ($WhatIf) {
        Write-Host "WHATIF delete: nul"
    } else {
        Remove-Item -Force $nulPath
        Add-Content -Path (Join-Path $archiveBase "MOVED.txt") -Value "nul (deleted)" -Encoding utf8
    }
}

Write-Host "OK: archived under $archiveBase"

