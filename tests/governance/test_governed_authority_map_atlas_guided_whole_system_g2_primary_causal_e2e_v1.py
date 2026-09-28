"""Tests for post-6938 Authority-Map-/Atlas-guided whole-system G2 primary E2E owner."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.governance.governed_authority_map_atlas_guided_whole_system_g2_primary_causal_e2e_v1 import (
    PrimaryArchiveClassificationV1,
    WORKPACKAGE_ID,
    adjudicate_lifecycle_primary_producers_v1,
    classify_primary_archive_root_v1,
    prove_post_6938_case_b_preserved_v1,
    run_reference_fixture_g2_m8_control_v1,
    select_legitimate_observed_primary_archive_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    RuntimePrimarySourceModeV1,
)
from tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures import (
    build_mode_bundle,
    cleanup_durable_archive_roots,
    projection_request,
)

pytest_plugins = [
    "tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures"
]

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _cleanup_archives():
    yield
    cleanup_durable_archive_roots()


def test_workpackage_id_stable() -> None:
    assert WORKPACKAGE_ID == (
        "AUTHORITY_MAP_ATLAS_GUIDED_WHOLE_SYSTEM_CAUSAL_E2E_FROM_POST_6938_MAIN"
    )


def test_case_b_preserved_on_main() -> None:
    assert prove_post_6938_case_b_preserved_v1(repo_root=REPO) is True


def test_fixture_archive_classified_not_observed_runtime(tmp_path: Path) -> None:
    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    report = classify_primary_archive_root_v1(root, repo_root=REPO)
    assert report.validate_ok is True
    assert report.classification is PrimaryArchiveClassificationV1.FIXTURE_OR_SYNTHETIC
    assert select_legitimate_observed_primary_archive_v1((report,)) is None


def test_fixture_control_g2_m8_reaches_m8(tmp_path: Path) -> None:
    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    req = projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    evidence = run_reference_fixture_g2_m8_control_v1(req)
    assert evidence.g2_ingress_admitted is True
    assert evidence.m8_reached is True


def test_lifecycle_adjudication_reports_no_observed_archive_by_default() -> None:
    paper, shadow, testnet = adjudicate_lifecycle_primary_producers_v1(
        repo_root=REPO,
        observed_runtime_archive_found=False,
    )
    assert paper.lifecycle == "PAPER"
    assert paper.durable_primary_archive_produced.value == "false"
    assert shadow.durable_primary_archive_produced.value == "false"
    assert testnet.durable_primary_archive_produced.value == "false"
