"""Contract tests for the committed P7 Shadow one-shot dry-run artifact bundle v0."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tests.ops.p7_shadow_one_shot_acceptance_bundle_v0 import (
    validate_p7_shadow_one_shot_artifact_bundle,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_BUNDLE = Path("tests/fixtures/p7_shadow_one_shot_acceptance_v0")
HIGH_VOL_FIXTURE_BUNDLE = (
    REPO_ROOT / "tests" / "fixtures" / "p7_shadow_one_shot_acceptance_high_vol_no_trade_v0"
)


def test_p7_shadow_one_shot_acceptance_fixture_dir_contract_v0() -> None:
    validate_p7_shadow_one_shot_artifact_bundle(FIXTURE_BUNDLE)


def test_p7_shadow_one_shot_acceptance_tmp_path_copy_contract_v0(tmp_path: Path) -> None:
    """A fresh outdir copy must match the same contract (relative layout only)."""
    dst = tmp_path / "out"
    shutil.copytree(FIXTURE_BUNDLE, dst)
    validate_p7_shadow_one_shot_artifact_bundle(dst)


def test_shared_validator_accepts_high_vol_no_trade_profile() -> None:
    validate_p7_shadow_one_shot_artifact_bundle(
        HIGH_VOL_FIXTURE_BUNDLE,
        profile_name="high_vol_no_trade",
    )


def test_shared_validator_rejects_empty_fills_for_baseline_profile() -> None:
    with pytest.raises(AssertionError, match="expected at least one fill"):
        validate_p7_shadow_one_shot_artifact_bundle(
            HIGH_VOL_FIXTURE_BUNDLE,
            profile_name="baseline",
        )


def test_shared_validator_rejects_unknown_profile() -> None:
    with pytest.raises(AssertionError, match="unknown P7 Shadow acceptance fixture profile"):
        validate_p7_shadow_one_shot_artifact_bundle(
            FIXTURE_BUNDLE,
            profile_name="missing_profile",
        )
