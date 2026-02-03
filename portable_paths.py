#!/usr/bin/env python3
"""
Small helper for locating resources in both:
- source checkout (python launch.py / python dictate.py)
- PyInstaller-frozen portable builds (Dictate.exe)
"""

from __future__ import annotations

import os
import sys


def app_dir() -> str:
    """
    Returns the directory that should be treated as the app root for locating
    side-by-side resources (assets/, icon_pngs/, models/, paste_rules.json).
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def path(*parts: str) -> str:
    return os.path.join(app_dir(), *parts)

