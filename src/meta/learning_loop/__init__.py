"""
Learning Loop v0: System 1 for autonomous configuration adaptation.

This package provides the foundational models and interfaces for the Learning Loop,
which generates ConfigPatch recommendations based on performance feedback.
"""

from .models import ConfigPatch, PatchStatus

__all__ = [
    "ConfigPatch",
    "PatchStatus",
]
