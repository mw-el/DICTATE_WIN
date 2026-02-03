# -*- mode: python ; coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path

import os
import sys
from glob import glob

from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs, conda_support
from PyInstaller.building.datastruct import Tree

block_cipher = None

ROOT = Path.cwd()
ENTRY = ROOT / "launch.py"
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

datas = []
binaries = []
hiddenimports = []

def _merge(pkg: str) -> None:
    d, b, h = collect_all(pkg)
    datas.extend(d)
    binaries.extend(b)
    hiddenimports.extend(h)

def _try_merge(pkg: str) -> None:
    try:
        _merge(pkg)
    except Exception as e:
        print(f"[spec] warning: collect_all failed for {pkg}: {e}")

# Core deps (large, but most robust for a “runs everywhere” portable build)
for _pkg in [
    "numpy",
    "torch",
    "torchaudio",
    "faster_whisper",
    "ctranslate2",
    "av",
    "sounddevice",
    "soundfile",
    "ttkbootstrap",
    "pyperclip",
    "pynput",
    "pystray",
    "PIL",
    "pywin32_system32",
    "win32com",
    "pythoncom",
    "tkinter_unblur",
]:
    _try_merge(_pkg)

# Local modules imported by dictate.py (launch.py is the entry point)
hiddenimports += [
    "config",
    "hotkey_manager",
    "window_manager",
    "tray_icon",
    "portable_paths",
    "faster_whisper",
    "ctranslate2",
    "torch",
    "torchaudio",
    "sounddevice",
    "soundfile",
]

# Extra runtime DLLs that PyInstaller sometimes fails to resolve automatically (CUDA + audio backends).
_env = Path(sys.prefix)

# CUDA runtime DLLs from conda env's bin/
_cuda_bin = _env / "bin"
for _name in [
    "cudart64_12.dll",
    "cublas64_12.dll",
    "cublasLt64_12.dll",
    "cufft64_11.dll",
    "cufftw64_11.dll",
    "cusolver64_11.dll",
    "cusolverMg64_11.dll",
    "cusparse64_12.dll",
    "nvJitLink_120_0.dll",
    "nvrtc64_120_0.dll",
    "nvrtc-builtins64_121.dll",
]:
    _p = _cuda_bin / _name
    if _p.exists():
        binaries.append((str(_p), "."))

# sounddevice ships PortAudio DLLs in _sounddevice_data
for _p in glob(str(_env / "lib" / "site-packages" / "_sounddevice_data" / "portaudio-binaries" / "*.dll")):
    binaries.append((_p, "."))

# soundfile ships libsndfile in _soundfile_data
_snd = _env / "lib" / "site-packages" / "_soundfile_data" / "libsndfile_64bit.dll"
if _snd.exists():
    binaries.append((str(_snd), "."))

# Include all conda env DLLs (ensures numpy/BLAS deps are present)
for _p in glob(str(_env / "Library" / "bin" / "*.dll")):
    binaries.append((_p, "."))
for _p in glob(str(_env / "bin" / "*.dll")):
    binaries.append((_p, "."))
for _p in glob(str(_env / "Library" / "mingw-w64" / "bin" / "*.dll")):
    binaries.append((_p, "."))

# Conda DLLs for numpy (from Library/bin)
for _numpy_dist in ["numpy", "numpy-base"]:
    try:
        binaries += collect_dynamic_libs(_numpy_dist)
    except Exception as e:
        print(f"[spec] warning: collect_dynamic_libs failed for {_numpy_dist}: {e}")

for _dist in ["numpy", "numpy-base", "mkl", "mkl-service", "mkl_fft", "mkl_random"]:
    try:
        binaries += conda_support.collect_dynamic_libs(_dist)
    except Exception as e:
        print(f"[spec] warning: conda_support.collect_dynamic_libs failed for {_dist}: {e}")

# Numpy/Fortran runtime DLLs often needed for _multiarray_umath
for _pattern in [
    "libgfortran*.dll",
    "libgcc_s*.dll",
    "libstdc++*.dll",
    "libquadmath*.dll",
]:
    for _p in glob(str(_env / "Library" / "bin" / _pattern)):
        binaries.append((_p, "."))

# Force-package faster_whisper and ctranslate2 if collect_all fails
_site = _env / "lib" / "site-packages"
for _pkg_dir in ["faster_whisper", "ctranslate2"]:
    _p = _site / _pkg_dir
    if _p.exists():
        datas.append((str(_p), _pkg_dir))

# App assets (side-by-side; code uses portable_paths.app_dir())
datas += [
    (str(ROOT / "paste_rules.json"), "."),
    (str(ROOT / "dictate.ico"), "."),
    (str(ROOT / "dictate.py"), "."),
]

a = Analysis(
    [str(ENTRY)],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Dictate",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(ROOT / "dictate.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    Tree(str(ROOT / "assets"), prefix="assets"),
    Tree(str(ROOT / "icon_pngs"), prefix="icon_pngs"),
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Dictate",
)
