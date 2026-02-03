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
    side-by-side resources (models/, outputs, etc.).
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def internal_dir() -> str:
    """
    Returns the PyInstaller internal directory where code/data lives.
    """
    if getattr(sys, "frozen", False):
        return os.path.join(app_dir(), "_internal")
    return app_dir()


def path(*parts: str) -> str:
    """
    Resolve a resource path. In frozen builds, prefer app_dir but fall back
    to _internal if the resource doesn't exist next to the exe.
    """
    p = os.path.join(app_dir(), *parts)
    if getattr(sys, "frozen", False) and not os.path.exists(p):
        alt = os.path.join(internal_dir(), *parts)
        if os.path.exists(alt):
            return alt
    return p
