#!/usr/bin/env python3
"""
GUI launcher for Dictate that avoids opening a console window.
Sets required environment variables, then runs dictate.py.
"""

import os
import sys
import runpy
import argparse

from portable_paths import app_dir


def _set_env():
    env_root = sys.prefix
    os.environ["PATH"] = ";".join(
        [
            env_root,
            os.path.join(env_root, "Scripts"),
            os.path.join(env_root, "Library", "bin"),
            os.environ.get("PATH", ""),
        ]
    )
    os.environ["CONDA_DEFAULT_ENV"] = "fasterwhisper"
    os.environ["CONDA_PREFIX"] = env_root
    os.environ["TTKBOOTSTRAP_FONT_MANAGER"] = "tk"
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--appid", default="Dictate")
    args, _unknown = parser.parse_known_args(argv)

    _set_env()
    os.environ["DICTATE_APPID"] = args.appid
    base_dir = app_dir()
    os.chdir(base_dir)
    if getattr(sys, "frozen", False):
        internal_dir = os.path.join(base_dir, "_internal")
        if hasattr(os, "add_dll_directory"):
            for p in (base_dir, internal_dir):
                try:
                    if p and os.path.isdir(p):
                        os.add_dll_directory(p)
                except Exception:
                    pass
        os.environ["PATH"] = ";".join([internal_dir, base_dir, os.environ.get("PATH", "")])
        for p in (base_dir, internal_dir):
            if p and p not in sys.path and os.path.isdir(p):
                sys.path.insert(0, p)
    if os.environ.get("DICTATE_DRYRUN") == "1":
        if getattr(sys, "frozen", False):
            print("DRYRUN: would run module 'dictate'")
        else:
            print(f"DRYRUN: would run path {os.path.join(base_dir, 'dictate.py')}")
        return
    script_path = os.path.join(base_dir, "dictate.py")
    if not os.path.exists(script_path) and getattr(sys, "frozen", False):
        script_path = os.path.join(base_dir, "_internal", "dictate.py")
    script_dir = os.path.dirname(script_path)
    if script_dir and script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    runpy.run_path(script_path, run_name="__main__")


if __name__ == "__main__":
    main()
