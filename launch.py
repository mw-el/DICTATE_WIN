#!/usr/bin/env python3
"""
GUI launcher for Dictate that avoids opening a console window.
Sets required environment variables, then runs dictate.py.
"""

import os
import sys
import runpy


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


def main():
    _set_env()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    runpy.run_path(os.path.join(script_dir, "dictate.py"), run_name="__main__")


if __name__ == "__main__":
    main()
