"""Shared datatypes for WP2-B-A1 adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class InspectionResultV1:
    ok: bool
    failure_semantic: str | None = None
    errors: list[str] = field(default_factory=list)
    bundle_doc: dict[str, Any] = field(default_factory=dict)
    manifest_doc: dict[str, Any] = field(default_factory=dict)
    output_dir: Path | None = None
