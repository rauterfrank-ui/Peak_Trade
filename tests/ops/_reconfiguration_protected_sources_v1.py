"""Frozen protection of the Owner-approved assembled-system source, not a moving ref."""

import hashlib
import json
from pathlib import Path


MANIFEST = Path(__file__).resolve().parents[1] / "fixtures/ops/approved_reconfiguration_core_v1.json"


def assert_approved_reconfiguration_sources_v1(repo_root: Path, paths) -> None:
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["approved_revision"] == "c17ffa3f9"
    approved = manifest["sha256"]
    for name in paths:
        assert name in approved, f"UNREVIEWED_PROTECTED_SOURCE: {name}"
        actual = hashlib.sha256((repo_root / name).read_bytes()).hexdigest()
        assert actual == approved[name], f"PROTECTED_SOURCE_CHANGED_AFTER_APPROVAL: {name}"
