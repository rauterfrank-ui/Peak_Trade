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


def test_paper_g2_runner_rejects_fixture_before_continuation(tmp_path: Path) -> None:
    from scripts.ops.run_post_6939_bounded_paper_primary_to_g2_m8_causal_closure_e2e_v1 import (
        continue_g2_from_primary_root,
    )

    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    with pytest.raises(ValueError, match="PAPER_OBSERVED_PRIMARY_ARCHIVE_REQUIRED"):
        continue_g2_from_primary_root(root, projection_inputs={})


def test_paper_g2_runner_reports_incomplete_continuation(tmp_path: Path, monkeypatch) -> None:
    import json
    import subprocess
    import sys

    from scripts.ops import (
        run_post_6939_bounded_paper_primary_to_g2_m8_causal_closure_e2e_v1 as cli,
    )
    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    metadata_path = root / "RUN_METADATA.json"
    metadata = json.loads(metadata_path.read_bytes())
    metadata.update(
        run_id="paper-wrapper-test",
        strategy_version="paper-wrapper-test.v1",
        repo_head_sha_prefix=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=cli.REPO, text=True
        ).strip()[:16],
    )
    metadata_path.write_text(json.dumps(metadata))
    write_manifest_sha256(root)
    request = vars(
        projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    ).copy()
    request.pop("source_mode")
    request.pop("primary_evidence_root")
    request_path = tmp_path / "request.json"
    from collections.abc import Mapping

    def serialize_mapping(value):
        if isinstance(value, Mapping):
            return dict(value)
        raise TypeError(f"Unexpected projection value: {type(value).__name__}")

    request_path.write_text(json.dumps(request, default=serialize_mapping))
    monkeypatch.setattr(cli, "PACK", tmp_path / "result")
    monkeypatch.setattr(
        sys, "argv", ["paper-g2", str(root), "--projection-request", str(request_path)]
    )
    assert cli.main() == 1
    report = json.loads((cli.PACK / cli.RUN_TS / "ORCHESTRATOR.json").read_bytes())
    assert report["G2_CONTINUATION"]["classification"]["root"] == str(root)
    assert report["G2_CONTINUATION"]["g2_m8"]["m8_reached"] is False


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
