from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from .canonical import canonical_json_line


def run_fingerprint(*, input_manifest: Mapping[str, Any], config: Mapping[str, Any]) -> str:
    """
    Stable fingerprint derived ONLY from input manifest + config.

    Important:
    - Do not include absolute paths, hostnames, wall-clock timestamps.
    - Callers should pass sanitized identifiers (e.g. logical dataset names, content hashes).
    """
    payload = {
        "input_manifest": dict(input_manifest),
        "config": dict(config),
    }
    digest = hashlib.sha256(canonical_json_line(payload).encode("utf-8")).hexdigest()
    return digest


@dataclass(frozen=True)
class DeterministicArtifactSink:
    """
    Deterministic sink that writes provided bytes to files.

    Note: the sink does not inject any environment-dependent metadata.
    """

    output_dir: Path

    def write_bytes(self, *, relpath: str, data: bytes) -> Path:
        p = (self.output_dir / relpath).resolve()
        # Ensure we stay within output_dir.
        base = self.output_dir.resolve()
        if base not in p.parents and p != base:
            raise ValueError("Refusing to write outside output_dir")

        p.parent.mkdir(parents=True, exist_ok=True)
        # Stable bytes: write exactly what we are given.
        p.write_bytes(data)
        return p
