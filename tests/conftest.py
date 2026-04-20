"""
tests/conftest.py
=================
Shared pytest fixtures and project-wide configuration.
"""

from __future__ import annotations
import sys
import os

# Ensure the project root is on sys.path so 'core.*' imports work
# when pytest is invoked from any directory.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)