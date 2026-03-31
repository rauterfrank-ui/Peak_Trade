"""
Learning Loop v0: System 1 for autonomous configuration adaptation.

Models: ``ConfigPatch`` / ``PatchStatus``. Snippets: ``emit_learning_snippet`` schreibt
deterministisch nach ``reports/learning_snippets/`` (kompatibel mit
``scripts/run_learning_apply_cycle.py``). **Bridge:** ``normalize_patches`` — reine
Payload-Normalisierung (kein I/O), erste Quelle = generisches Mapping/Listen-Layout.
"""

from .bridge import normalize_patches
from .emitter import DEFAULT_LEARNING_SNIPPETS_DIR, emit_learning_snippet
from .models import ConfigPatch, PatchStatus

__all__ = [
    "DEFAULT_LEARNING_SNIPPETS_DIR",
    "ConfigPatch",
    "PatchStatus",
    "emit_learning_snippet",
    "normalize_patches",
]
