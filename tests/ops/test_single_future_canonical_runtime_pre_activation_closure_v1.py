"""Capability 4.1 — single-future canonical runtime pre-activation closure tests."""

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
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.authority_inventory_v1 import (
    inventory_pre_activation_authority_surfaces_v1,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.constants_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    CAPABILITY_ID,
    FORBIDDEN_STATUS_VALUES,
    PACKAGE_MARKER,
    PRODUCTIVE_RUNTIME_HOST,
    REQUIRED_GATE_FLAGS,
    RUNTIME_ACTIVATED,
    RUNTIME_ACTIVATION_ALLOWED,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.persistence_v1 import (
    persist_pre_activation_evidence_atomic_v1,
    verify_manifest,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.pre_activation_gate_v1 import (
    PreActivationGateError,
    prove_config_effective_values_v1,
    run_single_future_canonical_runtime_pre_activation_closure_v1,
    validate_authorization_contract_offline_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import SELECTION_FILENAME
from src.ops.single_selected_future_policy_v1.models_v1 import SingleSelectedFutureSelectionV1
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    run_single_selected_future_policy_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.constants_v1 import (
    RUNTIME_BRIDGE_LIVE_ACTIVATED,
)

REPO_SHA = "58af5100ef8c307f4dbe5e95fe4a13102272a1b0"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"


def _perp(inst_id: str, *, base: str) -> dict:
    return {
        "instId": inst_id,
        "instType": "SWAP",
        "state": "live",
        "baseCcy": base,
        "quoteCcy": "USDT",
        "settleCcy": "USDT",
        "ctType": "linear",
        "ctVal": "0.01",
        "ctValCcy": base,
        "tickSz": "0.01",
        "lotSz": "1",
        "minSz": "1",
        "uly": f"{base}-USDT",
        "expTime": "",
    }


@pytest.fixture()
def fixture_roots(tmp_path: Path) -> dict[str, Path]:
    rows = [
        _perp("SOL-USDT-SWAP", base="SOL"),
        _perp("ETH-USDT-SWAP", base="ETH"),
        _perp("ADA-USDT-SWAP", base="ADA"),
    ]
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
            "data": [{"instId": i, "markPx": "100.5"} for i in mark_ids],
        },
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    )
    uni_writer = GovernedUniverseSingleWriterV1(state_root=uni_root, session_id="t41")
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
    rank_writer = ProductiveRankingSingleWriterV1(state_root=rank_root, session_id="t41")
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
        session_id="t41",
    )
    assert sel.get("ok"), sel
    selection = SingleSelectedFutureSelectionV1.from_dict(
        json.loads((sel_root / SELECTION_FILENAME).read_text(encoding="utf-8"))
    )
    marks = {selection.venue_native_id: "100.5"}
    return {
        "universe": uni_root,
        "ranking": rank_root,
        "selection": sel_root,
        "recon": recon_root,
        "accounting": acct_root,
        "marks": marks,  # type: ignore[dict-item]
        "selection_id": selection.selection_id,  # type: ignore[dict-item]
    }


def test_constants_status_and_call_graph() -> None:
    assert CAPABILITY_ID == (
        "CAPABILITY_4_1_SINGLE_FUTURE_CANONICAL_RUNTIME_PRE_ACTIVATION_CLOSURE_V1"
    )
    assert PACKAGE_MARKER.endswith("=true")
    assert CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "READY_FOR_ACTIVATION"
    assert RUNTIME_ACTIVATED is False
    assert RUNTIME_ACTIVATION_ALLOWED is False
    assert CANONICAL_RUNTIME_ENTRYPOINT_STATUS not in FORBIDDEN_STATUS_VALUES
    assert "authorization_contract_validation" in CALL_GRAPH_AFTER
    assert "session_lock" in CALL_GRAPH_AFTER
    assert "typed_volatility_presence" in CALL_GRAPH_AFTER
    assert "canonical_futures_accounting" in CALL_GRAPH_AFTER
    assert CALL_GRAPH_BEFORE != CALL_GRAPH_AFTER
    assert Path(PRODUCTIVE_RUNTIME_HOST).is_file()
    assert len(REQUIRED_GATE_FLAGS) >= 30


def test_no_second_runtime_host() -> None:
    inv = inventory_pre_activation_authority_surfaces_v1()
    assert inv["second_canonical_runtime_host_created"] is False
    assert inv["parallel_readiness_authority_created"] is False
    assert inv["legacy_parallel_authority_absent"] is True
    assert inv["dashboard_authority_effect"] is False


def test_config_effective_values_phase1() -> None:
    eff = prove_config_effective_values_v1()
    assert eff["max_open_positions"] == 1
    assert eff["MULTI_FUTURE_RUNTIME_AUTHORIZED"] is False
    assert eff["enable_live_trading"] is False
    assert eff["live_authorized"] is False
    assert eff["orders_authorized"] is False
    assert eff["paper_execution_authorized"] is False
    assert eff["testnet_authorized"] is False
    assert eff["runtime_bridge_live_activated"] is False
    assert eff["volatility_numeric_max_age_enforcement"] is False
    assert RUNTIME_BRIDGE_LIVE_ACTIVATED is False


def test_authorization_consumption_rejected() -> None:
    with pytest.raises(PreActivationGateError):
        validate_authorization_contract_offline_v1(
            authorization_artifact={"consumed": True},
            allow_consumption=False,
        )
    ok = validate_authorization_contract_offline_v1(
        authorization_artifact={"consumed": False},
        allow_consumption=False,
    )
    assert ok["authorization_consumed"] is False


def test_offline_end_to_end_ready_for_activation(fixture_roots: dict) -> None:
    tmp = Path(fixture_roots["accounting"]).parent
    gate = run_single_future_canonical_runtime_pre_activation_closure_v1(
        selection_state_root=fixture_roots["selection"],
        ranking_state_root=fixture_roots["ranking"],
        universe_state_root=fixture_roots["universe"],
        reconciliation_state_root=fixture_roots["recon"],
        accounting_state_root=fixture_roots["accounting"],
        evidence_root=tmp / "evidence",
        lock_root=tmp / "locks",
        repository_sha=REPO_SHA,
        baseline_sha=REPO_SHA,
        session_id="test-cap41",
        now_unix=OBSERVED_UNIX,
        mark_price_by_native_id=fixture_roots["marks"],
        mid_prices=(100.5, 101.0, 101.5, 102.0),
        authorization_artifact={"consumed": False},
        tmp_root=tmp / "fi",
        run_bridge=True,
    )
    assert gate.ok is True
    assert gate.ready_for_activation is True
    assert gate.runtime_activated is False
    assert gate.status == "READY_FOR_ACTIVATION"
    assert gate.gate_flags.all_true()
    assert gate.offline_end_to_end and gate.offline_end_to_end["ok"]
    assert gate.evidence.restart_recovery["ok"] is True
    assert gate.evidence.exit_risk_safety_independence["ok"] is True
    assert gate.evidence.activation_negative["ok"] is True
    assert gate.evidence.network_order_negative["ok"] is True
    assert all(v.get("ok") for v in gate.evidence.failure_injection_results.values())

    persist_pre_activation_evidence_atomic_v1(
        evidence_root=tmp / "evidence",
        evidence=gate.evidence.to_dict(),
        result=gate.to_dict(),
        gate=gate.gate_flags.to_dict(),
    )
    assert verify_manifest(tmp / "evidence")["ok"] is True


def test_activation_negative_constants() -> None:
    assert RUNTIME_ACTIVATED is False
    assert "ACTIVATED" in FORBIDDEN_STATUS_VALUES
    assert "LIVE" in FORBIDDEN_STATUS_VALUES
    assert CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "READY_FOR_ACTIVATION"
