"""Contract tests for P7 Shadow repeated-run stability (fixture-only, no live runs)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tests.ops.p7_shadow_one_shot_acceptance_bundle_v0 import (
    assert_p7_shadow_repeated_run_stability_v0,
    normalize_p7_shadow_repeated_run_value_v0,
    stable_repeated_run_artifact_paths_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "p7_shadow_one_shot_acceptance_v0"
ACCEPTANCE_RUNBOOK = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "P7_SHADOW_ONE_SHOT_ACCEPTANCE_CONTRACT_V0.md"
)
GOVERNANCE_RUNBOOK = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "P7_SHADOW_REPEATED_ONE_SHOT_DRY_RUN_GOVERNANCE_V0.md"
)


def _fixture_payloads() -> dict[str, object]:
    return {
        path.relative_to(FIXTURE_DIR).as_posix(): json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(FIXTURE_DIR.rglob("*.json"))
    }


def test_normalizer_removes_expected_timestamp_hash_and_path_volatility() -> None:
    payload = {
        "created_at_utc": "2026-05-05T16:20:00Z",
        "sha256": "abc",
        "path": "/tmp/peak_trade_manual_p7_shadow_repeated_campaign_scope_20260505T162028Z/runs/run_001/x.json",
        "stable": {"symbol": "BTC", "fills": [{"side": "BUY", "qty": 1.0}]},
    }

    normalized = normalize_p7_shadow_repeated_run_value_v0(payload)

    assert "created_at_utc" not in normalized
    assert "sha256" not in normalized
    assert "path" not in normalized
    assert normalized["stable"] == {"fills": [{"qty": 1.0, "side": "BUY"}], "symbol": "BTC"}


def test_stability_contract_accepts_expected_run_local_volatility() -> None:
    run_001 = _fixture_payloads()
    run_002 = copy.deepcopy(run_001)
    run_003 = copy.deepcopy(run_001)

    run_002["shadow_session_summary.json"]["created_at_utc"] = "2026-05-05T16:21:00Z"
    run_003["shadow_session_summary.json"]["created_at_utc"] = "2026-05-05T16:22:00Z"

    for relpath in (
        "p7/evidence_manifest.json",
        "evidence_manifest.json",
        "p7_evidence_manifest.json",
    ):
        if relpath in run_002 and isinstance(run_002[relpath], dict):
            meta = run_002[relpath].setdefault("meta", {})
            assert isinstance(meta, dict)
            meta["created_at_utc"] = "2026-05-05T16:21:05Z"
        if relpath in run_003 and isinstance(run_003[relpath], dict):
            meta = run_003[relpath].setdefault("meta", {})
            assert isinstance(meta, dict)
            meta["created_at_utc"] = "2026-05-05T16:22:05Z"

    assert_p7_shadow_repeated_run_stability_v0(
        {"run_001": run_001, "run_002": run_002, "run_003": run_003}
    )


def test_stability_contract_rejects_business_artifact_drift() -> None:
    run_001 = _fixture_payloads()
    run_002 = copy.deepcopy(run_001)

    fills_list = run_002["p7/fills.json"]
    assert isinstance(fills_list, dict)
    rows = fills_list["fills"]
    assert isinstance(rows, list) and rows
    first = rows[0]
    assert isinstance(first, dict)
    first["side"] = "SELL" if first.get("side") == "BUY" else "BUY"

    with pytest.raises(AssertionError, match="stable artifact drifted"):
        assert_p7_shadow_repeated_run_stability_v0({"run_001": run_001, "run_002": run_002})


def test_stability_contract_names_stable_business_artifacts() -> None:
    stable_paths = stable_repeated_run_artifact_paths_v0()

    assert "shadow_session_summary.json" in stable_paths
    assert "p5a/l3_trade_plan_advisory.json" in stable_paths
    assert "p7/fills.json" in stable_paths
    assert "p7/account.json" in stable_paths


def test_runbooks_document_stable_vs_volatile_repeated_run_boundary() -> None:
    acceptance = ACCEPTANCE_RUNBOOK.read_text(encoding="utf-8")
    governance = GOVERNANCE_RUNBOOK.read_text(encoding="utf-8")

    assert "volatile repeated-run fields" in acceptance
    assert "stable business-critical artifacts" in acceptance
    assert "created_at_utc" in acceptance
    assert "p7&#47;fills.json" in acceptance
    assert "Evidence-Manifest hashes" in governance
    assert "business-critical artifact drift" in governance
