"""Capability 5.1 — deterministic offline single-future runtime evidence tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    persist_universe_bundle_atomic_v1,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.governed_futures_universe_producer_v1.single_writer_v1 import (
    GovernedUniverseSingleWriterV1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    persist_ranking_bundle_atomic_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from src.ops.productive_futures_ranking_producer_v1.single_writer_v1 import (
    ProductiveRankingSingleWriterV1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.authority_inventory_v1 import (
    inventory_offline_evidence_authority_surfaces_v1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.constants_v1 import (
    CALL_GRAPH_AFTER,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    DEFAULT_FIXTURE_RELPATH,
    FORBIDDEN_STATUS_VALUES,
    PACKAGE_MARKER,
    PRODUCTIVE_RUNTIME_HOST,
    REQUIRED_GATE_FLAGS,
    RUNTIME_ACTIVATED,
    RUNTIME_ACTIVATION_ALLOWED,
    VOL_MAX_AGE_ENFORCEMENT_ENABLED,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.evidence_gate_v1 import (
    OfflineEvidenceGateError,
    run_single_future_canonical_runtime_deterministic_offline_evidence_v1,
    validate_authorization_contract_offline_fixture_v1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.fixture_v1 import (
    load_offline_market_data_fixture_v1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.persistence_v1 import (
    persist_offline_evidence_atomic_v1,
    verify_manifest,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.constants_v1 import (
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS as CAP41_STATUS,
    RUNTIME_ACTIVATED as CAP41_RUNTIME_ACTIVATED,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import SELECTION_FILENAME
from src.ops.single_selected_future_policy_v1.models_v1 import SingleSelectedFutureSelectionV1
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    run_single_selected_future_policy_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.constants_v1 import (
    RUNTIME_BRIDGE_LIVE_ACTIVATED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_SHA = "58af5100ef8c307f4dbe5e95fe4a13102272a1b0"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"


@pytest.fixture()
def fixture_roots(tmp_path: Path) -> dict[str, Path]:
    fixture = load_offline_market_data_fixture_v1(REPO_ROOT / DEFAULT_FIXTURE_RELPATH)
    rows = [dict(fixture.instrument_metadata), *[dict(x) for x in fixture.companion_instruments]]
    mark_ids = [r["instId"] for r in rows]
    uni_root = tmp_path / "universe"
    rank_root = tmp_path / "ranking"
    sel_root = tmp_path / "selection"
    recon_root = tmp_path / "recon"
    acct_root = tmp_path / "accounting"
    for p in (uni_root, rank_root, sel_root, recon_root, acct_root):
        p.mkdir()

    uni = produce_governed_futures_universe_v1(
        source_payload={"code": "0", "msg": "", "data": rows},
        mark_price_payload={
            "code": "0",
            "msg": "",
            "data": [
                {"instId": i, "markPx": str(fixture.mark_price_baseline.get(i, "100.5"))}
                for i in mark_ids
            ],
        },
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    )
    uni_writer = GovernedUniverseSingleWriterV1(state_root=uni_root, session_id="t51")
    uni_writer.acquire(now_unix=OBSERVED_UNIX)
    persist_universe_bundle_atomic_v1(
        state_root=uni_root,
        writer=uni_writer,
        snapshot=uni.snapshot,
        evidence={"ok": True},
    )
    uni_writer.release()

    ranking = produce_productive_futures_ranking_v1(
        universe_snapshot=uni.snapshot.to_dict(),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    rank_writer = ProductiveRankingSingleWriterV1(state_root=rank_root, session_id="t51")
    rank_writer.acquire(now_unix=OBSERVED_UNIX)
    persist_ranking_bundle_atomic_v1(
        state_root=rank_root,
        writer=rank_writer,
        snapshot=ranking.snapshot,
        evidence={"ok": True},
    )
    rank_writer.release()

    sel = run_single_selected_future_policy_v1(
        state_root=sel_root,
        ranking_state_root=rank_root,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="t51",
    )
    assert sel.get("ok"), sel
    selection = SingleSelectedFutureSelectionV1.from_dict(
        json.loads((sel_root / SELECTION_FILENAME).read_text(encoding="utf-8"))
    )
    marks = dict(fixture.mark_price_baseline)
    if selection.venue_native_id not in marks:
        marks[selection.venue_native_id] = "100.5"
    return {
        "universe": uni_root,
        "ranking": rank_root,
        "selection": sel_root,
        "recon": recon_root,
        "accounting": acct_root,
        "marks": marks,
        "fixture": fixture,
        "selection_obj": selection,
    }


def test_package_marker_and_status_semantics() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    assert CAPABILITY_ID.endswith("DETERMINISTIC_OFFLINE_EVIDENCE_V1")
    assert CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "READY_FOR_ACTIVATION"
    assert RUNTIME_ACTIVATED is False
    assert RUNTIME_ACTIVATION_ALLOWED is False
    assert CORE_LOGIC_CHANGE is False
    assert VOL_MAX_AGE_ENFORCEMENT_ENABLED is False
    assert CANONICAL_RUNTIME_ENTRYPOINT_STATUS not in FORBIDDEN_STATUS_VALUES
    assert CAP41_STATUS == "READY_FOR_ACTIVATION"
    assert CAP41_RUNTIME_ACTIVATED is False
    assert RUNTIME_BRIDGE_LIVE_ACTIVATED is False
    assert Path(REPO_ROOT / PRODUCTIVE_RUNTIME_HOST).is_file()


def test_fixture_versioned_and_roles() -> None:
    fixture = load_offline_market_data_fixture_v1(REPO_ROOT / DEFAULT_FIXTURE_RELPATH)
    assert fixture.fixture_version.endswith(".v1")
    assert fixture.seed_policy == "EXPLICIT_VERSIONED_NO_RANDOM"
    stats = fixture.observation_stats()
    assert stats["distinct_observation_count"] >= 8
    assert stats["duplicate_observation_count"] >= 1
    assert stats["missing_observation_count"] >= 1
    roles = {o.sequence_role for o in fixture.observations}
    for required in ("long", "short", "flat_hold", "hold", "adverse", "exit"):
        assert required in roles
    assert fixture.replay_mids()


def test_authorization_offline_never_consumes() -> None:
    out = validate_authorization_contract_offline_fixture_v1(
        authorization_artifact={"schema": "offline_structural_only", "consumed": False}
    )
    assert out["authorization_consumed"] is False
    assert out["step"] == "authorization_contract_validation_offline_fixture"
    with pytest.raises(Exception):
        validate_authorization_contract_offline_fixture_v1(
            authorization_artifact={"consumed": True}
        )


def test_authority_inventory_no_parallel_host() -> None:
    inv = inventory_offline_evidence_authority_surfaces_v1()
    assert inv["second_canonical_runtime_host_created"] is False
    assert inv["parallel_runtime_authority_created"] is False
    assert inv["legacy_parallel_authority_absent"] is True
    assert inv["core_logic_changed"] is False
    assert inv["selection_authority_unchanged"] is True


def test_deterministic_offline_evidence_end_to_end(fixture_roots: dict) -> None:
    evidence_root = fixture_roots["accounting"].parent / "evidence"
    lock_root = fixture_roots["accounting"].parent / "locks"
    evidence_root.mkdir()
    lock_root.mkdir()
    gate = run_single_future_canonical_runtime_deterministic_offline_evidence_v1(
        selection_state_root=fixture_roots["selection"],
        ranking_state_root=fixture_roots["ranking"],
        universe_state_root=fixture_roots["universe"],
        reconciliation_state_root=fixture_roots["recon"],
        accounting_state_root=fixture_roots["accounting"],
        evidence_root=evidence_root,
        lock_root=lock_root,
        repository_sha=REPO_SHA,
        baseline_sha=REPO_SHA,
        session_id="test-cap51",
        now_unix=OBSERVED_UNIX,
        mark_price_by_native_id=fixture_roots["marks"],
        authorization_artifact={"schema": "offline_structural_only", "consumed": False},
        fixture_path=REPO_ROOT / DEFAULT_FIXTURE_RELPATH,
        tmp_root=fixture_roots["accounting"].parent / "tmp",
    )
    assert gate.ok
    assert gate.ready_for_activation
    assert gate.runtime_activated is False
    assert gate.status == "READY_FOR_ACTIVATION"
    assert gate.evidence.independent_run["match"] is True
    assert gate.evidence.restart_recovery["RESTART_FINAL_STATE_MATCH"] is True
    assert gate.evidence.restart_recovery["RESTART_EVIDENCE_DIGEST_MATCH"] is True
    assert gate.evidence.verifier_result["ok"] is True
    assert gate.evidence.telemetry["cycle_count"] >= 8
    assert gate.evidence.telemetry["distinct_observation_count"] >= 8
    assert gate.evidence.telemetry["duplicate_observation_count"] >= 1
    assert gate.evidence.telemetry["missing_observation_count"] >= 1
    assert gate.evidence.telemetry["typed_volatility_presence_events"] >= 1
    for strata in gate.evidence.telemetry["numeric_max_age_strata_diagnostic"]:
        assert strata["enforcement_enabled"] is False
        assert strata["mutates_alpha_risk_safety"] is False
    assert set(REQUIRED_GATE_FLAGS).issubset(set(gate.gate_flags.flags))
    assert gate.gate_flags.all_true()
    assert "deterministic_offline_market_data_replay" in CALL_GRAPH_AFTER
    assert "authorization_contract_validation_offline_fixture" in CALL_GRAPH_AFTER

    persist_offline_evidence_atomic_v1(
        evidence_root=evidence_root,
        evidence=gate.evidence.to_dict(),
        result=gate.to_dict(),
        gate=gate.gate_flags.to_dict(),
        telemetry=gate.evidence.telemetry,
        restart=gate.evidence.restart_recovery,
        failure_injection=gate.evidence.failure_injection_results,
    )
    assert verify_manifest(evidence_root)["ok"] is True


def test_activation_negative_status_unchanged(fixture_roots: dict) -> None:
    evidence_root = fixture_roots["accounting"].parent / "evidence2"
    lock_root = fixture_roots["accounting"].parent / "locks2"
    evidence_root.mkdir()
    lock_root.mkdir()
    gate = run_single_future_canonical_runtime_deterministic_offline_evidence_v1(
        selection_state_root=fixture_roots["selection"],
        ranking_state_root=fixture_roots["ranking"],
        universe_state_root=fixture_roots["universe"],
        reconciliation_state_root=fixture_roots["recon"] / "neg",
        accounting_state_root=fixture_roots["accounting"] / "neg",
        evidence_root=evidence_root,
        lock_root=lock_root,
        repository_sha=REPO_SHA,
        baseline_sha=REPO_SHA,
        session_id="test-cap51-neg",
        now_unix=OBSERVED_UNIX,
        mark_price_by_native_id=fixture_roots["marks"],
        fixture_path=REPO_ROOT / DEFAULT_FIXTURE_RELPATH,
        tmp_root=fixture_roots["accounting"].parent / "tmp2",
    )
    assert gate.evidence.activation_negative["RUNTIME_ACTIVATED"] is False
    assert gate.evidence.activation_negative["status_unchanged"] is True
    assert gate.evidence.network_order_negative["NETWORK_ACCESS_OCCURRED"] is False
    assert gate.evidence.network_order_negative["NO_LIVE_ORDER_PATH"] is True
    assert gate.evidence.network_order_negative["NO_TESTNET_ORDER_PATH"] is True


def test_failure_injection_matrix_covered(fixture_roots: dict) -> None:
    evidence_root = fixture_roots["accounting"].parent / "evidence3"
    lock_root = fixture_roots["accounting"].parent / "locks3"
    evidence_root.mkdir()
    lock_root.mkdir()
    gate = run_single_future_canonical_runtime_deterministic_offline_evidence_v1(
        selection_state_root=fixture_roots["selection"],
        ranking_state_root=fixture_roots["ranking"],
        universe_state_root=fixture_roots["universe"],
        reconciliation_state_root=fixture_roots["recon"] / "fi",
        accounting_state_root=fixture_roots["accounting"] / "fi",
        evidence_root=evidence_root,
        lock_root=lock_root,
        repository_sha=REPO_SHA,
        baseline_sha=REPO_SHA,
        session_id="test-cap51-fi",
        now_unix=OBSERVED_UNIX,
        mark_price_by_native_id=fixture_roots["marks"],
        fixture_path=REPO_ROOT / DEFAULT_FIXTURE_RELPATH,
        tmp_root=fixture_roots["accounting"].parent / "tmp3",
    )
    keys = set(gate.evidence.failure_injection_results)
    for required in (
        "STALE_SELECTION",
        "SELECTION_DIGEST_MISMATCH",
        "MISSING_MARK_PRICE",
        "MISSING_TYPED_VOLATILITY",
        "STALE_MARKET_DATA",
        "DUPLICATE_OBSERVATION",
        "MISSING_OBSERVATION",
        "INVALID_CONTRACT_METADATA",
        "CORRUPTED_PORTFOLIO_CHECKPOINT",
        "CORRUPTED_RISK_CHECKPOINT",
        "ACCOUNTING_PERSISTENCE_FAILURE",
        "VERIFIER_MISMATCH",
    ):
        assert required in keys
        assert gate.evidence.failure_injection_results[required]["ok"] is True


def test_entrypoint_script_exists_and_is_offline_only() -> None:
    path = (
        REPO_ROOT
        / "scripts/ops/run_single_future_canonical_runtime_deterministic_offline_evidence_v1.py"
    )
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "no http" in lowered
    assert "no http, websocket" in lowered or "websocket" in lowered and "no " in lowered
    assert "import requests" not in lowered
    assert "import websocket" not in lowered
    assert "sleep(" not in text
