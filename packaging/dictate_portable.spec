# -*- mode: python ; coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path

import sys
from glob import glob

from PyInstaller.utils.hooks import collect_all
from PyInstaller.building.datastruct import Tree

block_cipher = None

ROOT = Path.cwd()
ENTRY = ROOT / "launch.py"

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
    "torch",
    "torchaudio",
    "faster_whisper",
    "ctranslate2",
    "av",
    "sounddevice",
    "soundfile",
    "ttkbootstrap",
    "tkinter_unblur",
    "pyperclip",
    "pynput",
    "pystray",
    "PIL",
    "pywin32_system32",
    "win32com",
    "pythoncom",
]:
    _try_merge(_pkg)

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
