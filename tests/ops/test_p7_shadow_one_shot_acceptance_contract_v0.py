"""Contract tests for the committed P7 Shadow one-shot dry-run artifact bundle v0."""

from __future__ import annotations

import shutil
from pathlib import Path

from tests.ops.p7_shadow_one_shot_acceptance_bundle_v0 import (
    validate_p7_shadow_one_shot_artifact_bundle,
)

FIXTURE_BUNDLE = Path("tests/fixtures/p7_shadow_one_shot_acceptance_v0")


def test_p7_shadow_one_shot_acceptance_fixture_dir_contract_v0() -> None:
    validate_p7_shadow_one_shot_artifact_bundle(FIXTURE_BUNDLE)


def test_p7_shadow_one_shot_acceptance_tmp_path_copy_contract_v0(tmp_path: Path) -> None:
    """A fresh outdir copy must match the same contract (relative layout only)."""
    dst = tmp_path / "out"
    shutil.copytree(FIXTURE_BUNDLE, dst)
    validate_p7_shadow_one_shot_artifact_bundle(dst)
