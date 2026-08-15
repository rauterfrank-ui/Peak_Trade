"""Wiring-proof tests for current-SHA no-order Package-N orchestrator.

Does not set COMPLETE_CURRENT_SYSTEM_E2E_PROVEN=true.
"""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import (
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.live_eval.live_session_eval import compute_metrics
from src.ops.canonical_current_sha_no_order_package_n_e2e_v1.constants_v1 import (
    COMPLETE_CURRENT_SYSTEM_E2E_PROVEN,
    CONTRACT_ID,
    EVIDENCE_DIRNAME,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORBIDDEN_GENERATE_SCRIPTS,
    I65_RUN_TYPE,
    OUT_OPS_PREFIX,
)
from src.ops.canonical_current_sha_no_order_package_n_e2e_v1.i61_fill_mapper_v1 import (
    map_cap71_fills_to_i61_fills_v1,
)
from src.ops.canonical_current_sha_no_order_package_n_e2e_v1.orchestrator_v1 import (
    CanonicalCurrentShaNoOrderPackageNE2EError,
    combined_evidence_digest_v1,
    evidence_root_for_run_v1,
    require_current_run_i17_v1,
    require_i56_artifacts_nonempty_v1,
    require_i61_metrics_nonempty_v1,
    require_identical_package_n_v1,
    require_matching_shas_v1,
    require_source_experiment_id_v1,
    run_canonical_current_sha_no_order_package_n_e2e_v1,
    validate_isolated_run_root_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATOR_PATH = (
    REPO_ROOT
    / "src"
    / "ops"
    / "canonical_current_sha_no_order_package_n_e2e_v1"
    / "orchestrator_v1.py"
)


def test_complete_current_system_e2e_proven_remains_false() -> None:
    assert COMPLETE_CURRENT_SYSTEM_E2E_PROVEN is False
    assert CONTRACT_ID == "canonical_current_sha_no_order_package_n_e2e_v1"


def test_orchestrator_does_not_import_destructive_generators() -> None:
    source = ORCHESTRATOR_PATH.read_text(encoding="utf-8")
    for rel in FORBIDDEN_GENERATE_SCRIPTS:
        assert rel not in source
        assert Path(rel).name.replace(".py", "") not in source


def test_tmp_runtime_root_rejected() -> None:
    repo = Path("/tmp") / f"peak_trade_e2e_r2_{uuid.uuid4().hex[:8]}"
    run_root = repo / OUT_OPS_PREFIX / EVIDENCE_DIRNAME / "run1"
    try:
        with pytest.raises(
            CanonicalCurrentShaNoOrderPackageNE2EError, match="tmp runtime root forbidden"
        ):
            validate_isolated_run_root_v1(repo, run_root)
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def test_docs_evidence_target_rejected() -> None:
    run_root = REPO_ROOT / "docs" / "evidence" / "forbidden_e2e_root"
    with pytest.raises(
        CanonicalCurrentShaNoOrderPackageNE2EError, match="docs/evidence write forbidden"
    ):
        validate_isolated_run_root_v1(REPO_ROOT, run_root)


def test_root_outside_out_ops_rejected() -> None:
    run_root = REPO_ROOT / "out" / "other" / "run1"
    with pytest.raises(
        CanonicalCurrentShaNoOrderPackageNE2EError, match="run root must be under out/ops/"
    ):
        validate_isolated_run_root_v1(REPO_ROOT, run_root)


def test_preexisting_evidence_root_rejected() -> None:
    run_id = f"preexist_{uuid.uuid4().hex[:12]}"
    run_root = evidence_root_for_run_v1(REPO_ROOT, run_id)
    run_root.mkdir(parents=True, exist_ok=False)
    try:
        with pytest.raises(
            CanonicalCurrentShaNoOrderPackageNE2EError, match="pre-existing evidence root"
        ):
            validate_isolated_run_root_v1(REPO_ROOT, run_root)
    finally:
        shutil.rmtree(run_root, ignore_errors=True)


def test_fixture_i17_rejected() -> None:
    with pytest.raises(CanonicalCurrentShaNoOrderPackageNE2EError, match="fixture I17 rejected"):
        require_current_run_i17_v1(
            {
                "fixture_non_authoritative": True,
                "expected_repository_sha": EXPECTED_ORIGIN_MAIN_SHA,
                "evidence_root": "tests/fixtures/ops/paper_shadow_observation_operator_go_session_preregistration_v1",
            }
        )


def test_empty_i56_capsule_rejected() -> None:
    with pytest.raises(
        CanonicalCurrentShaNoOrderPackageNE2EError, match="empty I56 capsule rejected"
    ):
        require_i56_artifacts_nonempty_v1({"artifacts": []})


def test_empty_i61_fills_rejected() -> None:
    metrics = compute_metrics([])
    with pytest.raises(
        CanonicalCurrentShaNoOrderPackageNE2EError, match="empty I61 fills rejected"
    ):
        require_i61_metrics_nonempty_v1(metrics)


def test_repository_sha_mismatch_rejected() -> None:
    with pytest.raises(CanonicalCurrentShaNoOrderPackageNE2EError, match="repository SHA mismatch"):
        require_matching_shas_v1("aaa", "bbb", "bbb")


def test_cap71_cap72_sha_mismatch_rejected() -> None:
    with pytest.raises(CanonicalCurrentShaNoOrderPackageNE2EError, match="Cap7.1/7.2 SHA mismatch"):
        require_matching_shas_v1(EXPECTED_ORIGIN_MAIN_SHA, EXPECTED_ORIGIN_MAIN_SHA, "deadbeef")


def test_divergent_package_n_rejected() -> None:
    with pytest.raises(
        CanonicalCurrentShaNoOrderPackageNE2EError, match="divergent Package-N across owners"
    ):
        require_identical_package_n_v1(
            {"I16": "a" * 64, "I17": "b" * 64},
            "a" * 64,
        )


def test_source_experiment_id_mismatch_rejected() -> None:
    with pytest.raises(
        CanonicalCurrentShaNoOrderPackageNE2EError, match="source_experiment_id mismatch"
    ):
        require_source_experiment_id_v1(
            {
                "experiment_identity_id": "a" * 64,
                "provenance": {"source_experiment_id": "b" * 64},
            },
            "c" * 64,
        )


def test_tampered_manifest_rejected() -> None:
    run_id = f"tamper_{uuid.uuid4().hex[:12]}"
    run_root = evidence_root_for_run_v1(REPO_ROOT, run_id)
    run_root.mkdir(parents=True, exist_ok=False)
    try:
        payload_path = run_root / "note.json"
        payload_path.write_text("{}\n", encoding="utf-8")
        write_manifest_sha256(run_root)
        ok, _msg = verify_manifest_sha256(run_root)
        assert ok is True
        payload_path.write_text('{"tampered": true}\n', encoding="utf-8")
        ok, _msg = verify_manifest_sha256(run_root)
        assert ok is False
    finally:
        shutil.rmtree(run_root, ignore_errors=True)


def test_i61_mapper_maps_buy_sell_and_skips_flat() -> None:
    fills = map_cap71_fills_to_i61_fills_v1(
        [
            {
                "side": "BUY",
                "quantity": "1.5",
                "fill_price": "3500.1",
                "instrument_id": "ETH-USD_UM_XPERP-310404",
                "event_ts_unix": 1_700_000_000,
            },
            {"side": "FLAT", "quantity": "1", "fill_price": "3500"},
            {
                "side": "SELL",
                "quantity": "1.5",
                "fill_price": "3510.0",
                "instrument_id": "ETH-USD_UM_XPERP-310404",
                "event_ts_unix": 1_700_000_010,
            },
        ]
    )
    assert [item.side for item in fills] == ["buy", "sell"]
    metrics = compute_metrics(fills)
    require_i61_metrics_nonempty_v1(metrics)


def test_combined_evidence_digest_is_sha256_of_concatenated_digests() -> None:
    digest = combined_evidence_digest_v1("aa", "bb")
    assert len(digest) == 64
    assert digest != "aa"
    assert digest != "bb"


def test_positive_isolated_wiring_proof() -> None:
    run_id = f"wiring_{uuid.uuid4().hex[:12]}"
    run_root = evidence_root_for_run_v1(REPO_ROOT, run_id)
    try:
        result = run_canonical_current_sha_no_order_package_n_e2e_v1(
            repo_root=REPO_ROOT,
            run_id=run_id,
            repository_sha=EXPECTED_ORIGIN_MAIN_SHA,
        )
        assert result.ok is True
        assert result.complete_current_system_e2e_proven is False
        assert result.to_dict()["COMPLETE_CURRENT_SYSTEM_E2E_PROVEN"] is False
        assert result.package_n_same_across_all_owners is True
        assert len(result.package_n_sha256) == 64
        assert set(result.owner_identities) == {"I16", "I17", "I52", "I56", "I61", "I65"}
        assert set(result.owner_identities.values()) == {result.package_n_sha256}
        assert result.source_experiment_id == result.combined_evidence_digest
        assert result.source_experiment_id != result.package_n_sha256
        assert result.manifest_verify_ok is True
        assert I65_RUN_TYPE == "offline_no_order_lifecycle"
        summary = json.loads((run_root / "owners" / "i65_summary.json").read_text(encoding="utf-8"))
        assert summary["run_type"] == I65_RUN_TYPE
        i17 = json.loads(
            (run_root / "owners" / "i17_preregistration.json").read_text(encoding="utf-8")
        )
        assert i17["fixture_non_authoritative"] is False
        assert "confirm_token" not in i17
        i56 = json.loads((run_root / "owners" / "i56_capsule.json").read_text(encoding="utf-8"))
        assert i56["artifacts"]
        metadata = json.loads((run_root / "RUN_METADATA.json").read_text(encoding="utf-8"))
        assert metadata["COMPLETE_CURRENT_SYSTEM_E2E_PROVEN"] is False
        ok, _msg = verify_manifest_sha256(run_root)
        assert ok is True
        (run_root / "RUN_METADATA.json").write_text('{"tampered": true}\n', encoding="utf-8")
        ok, _msg = verify_manifest_sha256(run_root)
        assert ok is False
    finally:
        shutil.rmtree(run_root, ignore_errors=True)
