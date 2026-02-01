param(
    [string[]]$Models = @("base", "small", "large-v3-turbo")
)

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
if (-not (Test-Path $pythonExe)) {
    throw "python.exe not found in env. Run install.ps1 first."
}

$modelsDir = Join-Path $scriptDir "models"
New-Item -ItemType Directory -Force -Path $modelsDir | Out-Null

$env:DICTATE_MODEL_LIST = ($Models -join ",")
$env:DICTATE_MODELS_DIR = $modelsDir
$env:KMP_DUPLICATE_LIB_OK = "TRUE"

$pyLines = @(
    "import os",
    "from faster_whisper.utils import download_model",
    "",
    "models = [m.strip() for m in os.environ.get('DICTATE_MODEL_LIST', 'base,small,large-v3-turbo').split(',') if m.strip()]",
    "models_dir = os.environ.get('DICTATE_MODELS_DIR')",
    "if not models_dir:",
    "    raise SystemExit('DICTATE_MODELS_DIR not set')",
    "",
    "for name in models:",
    "    if name == 'large-v3-turbo':",
    "        repo_id = 'mobiuslabsgmbh/faster-whisper-large-v3-turbo'",
    "    else:",
    "        repo_id = name",
    "    out_dir = os.path.join(models_dir, name)",
    "    os.makedirs(out_dir, exist_ok=True)",
    "    print(f'Downloading {repo_id} -> {out_dir}')",
    "    download_model(repo_id, output_dir=out_dir)",
    "    print(f'OK: {name}')"
)

$py = $pyLines -join "`n"
$py | & $pythonExe -
