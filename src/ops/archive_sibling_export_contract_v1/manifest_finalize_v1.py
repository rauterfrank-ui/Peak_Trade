"""MANIFEST.sha256 coherence after readmodels/ writes (verify-before-trust).

Reuses scripts.ops.primary_evidence_retention_v0.write_manifest_sha256 only.
Does not weaken universe loader verify-before-trust semantics.
"""

from __future__ import annotations

from pathlib import Path

MANIFEST_FINALIZE_FAILED = "MANIFEST_FINALIZE_FAILED"
READMODELS_MANIFEST_FILENAME = "MANIFEST.sha256"


def readmodels_dir_from_artifact_path(artifact_path: Path) -> Path:
    """Return readmodels/ directory containing a written artifact."""
    resolved = artifact_path.expanduser().resolve()
    if resolved.parent.name != "readmodels":
        raise ValueError("artifact_path must live under readmodels/")
    return resolved.parent


def finalize_manifest_for_sibling_target_v1(target_path: Path) -> tuple[bool, str]:
    """Finalize MANIFEST after writing one file under readmodels/."""
    try:
        readmodels_dir = readmodels_dir_from_artifact_path(target_path)
    except ValueError as exc:
        return False, str(exc)
    return finalize_readmodels_manifest_after_write_v1(readmodels_dir)


def finalize_readmodels_manifest_after_write_v1(
    readmodels_dir: Path,
) -> tuple[bool, str]:
    """Rewrite MANIFEST.sha256 for all files under readmodels/ and verify."""
    root = readmodels_dir.expanduser().resolve()
    if root.name != "readmodels":
        return False, "readmodels_dir must be named readmodels"
    from scripts.ops.primary_evidence_retention_v0 import (
        verify_manifest_sha256,
        write_manifest_sha256,
    )

    write_manifest_sha256(root)
    return verify_manifest_sha256(root)
