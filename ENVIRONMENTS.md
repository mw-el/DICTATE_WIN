# Environment Files Guide (Windows Only)

This project provides Windows-only environment configurations for GPU and CPU setups.

## Available Environment Files

### 1. `environment-win-gpu.yml` (Windows + CUDA)
- For systems with NVIDIA GPU
- Uses PyTorch with CUDA 12.1 support

### 2. `environment-win-cpu.yml` (Windows + CPU)
- For systems without NVIDIA GPU
- CPU-only PyTorch

### 3. `environment.yml` (Windows CPU default)
- Same as `environment-win-cpu.yml`
- Kept for convenience

## Automatic Detection

The `install.ps1` script automatically detects your system configuration:

1. Checks for NVIDIA GPU using `nvidia-smi`
2. Selects `environment-win-gpu.yml` or `environment-win-cpu.yml`

## Manual Installation

```powershell
# GPU systems
conda env create -f environment-win-gpu.yml

# CPU-only systems
conda env create -f environment-win-cpu.yml
```

## Checking Your GPU

```powershell
nvidia-smi
```
