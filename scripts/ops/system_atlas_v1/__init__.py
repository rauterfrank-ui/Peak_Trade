"""System Atlas v1 package. ATLAS_AUTHORITY=NONE."""

from __future__ import annotations

from scripts.ops.system_atlas_v1.constants_v1 import ATLAS_AUTHORITY, PACKAGE_MARKER
from scripts.ops.system_atlas_v1.generate_v1 import generate_views_v1, write_generated_v1
from scripts.ops.system_atlas_v1.load_v1 import load_atlas_v1
from scripts.ops.system_atlas_v1.validate_v1 import AtlasValidationError, validate_atlas_v1

__all__ = [
    "ATLAS_AUTHORITY",
    "PACKAGE_MARKER",
    "AtlasValidationError",
    "generate_views_v1",
    "load_atlas_v1",
    "validate_atlas_v1",
    "write_generated_v1",
]
