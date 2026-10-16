"""Readmodels MANIFEST coherence helper for dashboard presentation materializers."""

from __future__ import annotations

from pathlib import Path

from src.ops.archive_sibling_export_contract_v1.manifest_finalize_v1 import (
    finalize_readmodels_manifest_after_write_v1,
)


def finalize_manifest_for_readmodel_artifact_v1(artifact_path: Path) -> bool:
    """Finalize MANIFEST.sha256 after a successful readmodels/ artifact write."""
    ok, _msg = finalize_readmodels_manifest_after_write_v1(artifact_path.parent)
    return ok
