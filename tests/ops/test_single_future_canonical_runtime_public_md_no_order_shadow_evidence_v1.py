"""Capability 5.2 — public-MD no-order shadow single-future runtime evidence tests."""

from __future__ import annotations

import json
import uuid
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
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.fixture_v1 import (
    load_offline_market_data_fixture_v1,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.authority_inventory_v1 import (
    inventory_public_md_shadow_authority_surfaces_v1,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.authorization_consumption_v1 import (
    AuthorizationConsumptionError,
    consume_public_md_shadow_authorization_v1,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.constants_v1 import (
    AUTHORIZATION_SCHEMA,
    CALL_GRAPH_AFTER,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    DEFAULT_CAPTURE_TEMPLATE_RELPATH,
    DEFAULT_CYCLE_COUNT,
    FORBIDDEN_STATUS_VALUES,
    PACKAGE_MARKER,
    PRODUCTIVE_RUNTIME_HOST,
    PUBLIC_MARKET_DATA_ONLY,
    PUBLIC_MD_NO_ORDER_SHADOW,
    REQUIRED_GATE_FLAGS,
    RUNTIME_ACTIVATED,
    RUNTIME_ACTIVATION_ALLOWED,
    VOL_MAX_AGE_ENFORCEMENT_ENABLED,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.evidence_gate_v1 import (
    run_single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.persistence_v1 import (
    persist_public_md_shadow_evidence_atomic_v1,
    verify_manifest,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.public_md_capture_v1 import (
    build_mock_mark_price_fetcher_v1,
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
REPO_SHA = "a7a1a5a5466eb619a7284247f794ee34035f6407"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"


def _auth_artifact(*, auth_id: str | None = None) -> dict:
    return {
        "schema": AUTHORIZATION_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "authorization_id": auth_id or f"cap52_test_{uuid.uuid4().hex[:12]}",
        "network_scope": "PUBLIC_MARKET_DATA_ONLY",
        "public_market_data_only": True,
        "orders_authorized": False,
        "live_authorized": False,
        "testnet_authorized": False,
        "paper_order_execution_authorized": False,
        "authorization_consumption_allowed": True,
        "multi_future_runtime_authorized": False,
        "vol_max_age_enforcement_enabled": False,
        "runtime_activated": False,
        "one_time_use": True,
        "repository_sha": REPO_SHA,
    }


@pytest.fixture()
def fixture_roots(tmp_path: Path) -> dict:
    fixture = load_offline_market_data_fixture_v1(REPO_ROOT / DEFAULT_CAPTURE_TEMPLATE_RELPATH)
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
    uni_writer = GovernedUniverseSingleWriterV1(state_root=uni_root, session_id="t52")
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
    rank_writer = ProductiveRankingSingleWriterV1(state_root=rank_root, session_id="t52")
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
        session_id="t52",
    )
    assert sel.get("ok"), sel
    selection = SingleSelectedFutureSelectionV1.from_dict(
        json.loads((sel_root / SELECTION_FILENAME).read_text(encoding="utf-8"))
    )
    marks = dict(fixture.mark_price_baseline)
    if selection.venue_native_id not in marks:
        marks[selection.venue_native_id] = "100.5"
    mock_marks = [str(float(marks[selection.venue_native_id]) + i * 0.01) for i in range(12)]
    return {
        "universe": uni_root,
        "ranking": rank_root,
        "selection": sel_root,
        "recon": recon_root,
        "accounting": acct_root,
        "marks": marks,
        "fixture": fixture,
        "selection_obj": selection,
        "mock_fetcher": build_mock_mark_price_fetcher_v1(
            venue_native_id=selection.venue_native_id,
            marks=mock_marks,
        ),
    }


def test_package_marker_and_status_semantics() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    assert CAPABILITY_ID.endswith("PUBLIC_MD_NO_ORDER_SHADOW_EVIDENCE_V1")
    assert CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "READY_FOR_ACTIVATION"
    assert RUNTIME_ACTIVATED is False
    assert RUNTIME_ACTIVATION_ALLOWED is False
    assert CORE_LOGIC_CHANGE is False
    assert VOL_MAX_AGE_ENFORCEMENT_ENABLED is False
    assert PUBLIC_MARKET_DATA_ONLY is True
    assert PUBLIC_MD_NO_ORDER_SHADOW is True
    assert CANONICAL_RUNTIME_ENTRYPOINT_STATUS not in FORBIDDEN_STATUS_VALUES
    assert CAP41_STATUS == "READY_FOR_ACTIVATION"
    assert CAP41_RUNTIME_ACTIVATED is False
    assert RUNTIME_BRIDGE_LIVE_ACTIVATED is False
    assert Path(REPO_ROOT / PRODUCTIVE_RUNTIME_HOST).is_file()


def test_authorization_consumes_once(tmp_path: Path) -> None:
    artifact = _auth_artifact()
    first = consume_public_md_shadow_authorization_v1(
        authorization_artifact=artifact,
        consumption_store=tmp_path / "store",
        repository_sha=REPO_SHA,
        session_id="s1",
        now_unix=OBSERVED_UNIX,
    )
    assert first["authorization_consumed"] is True
    with pytest.raises(AuthorizationConsumptionError):
        consume_public_md_shadow_authorization_v1(
            authorization_artifact=artifact,
            consumption_store=tmp_path / "store",
            repository_sha=REPO_SHA,
            session_id="s2",
            now_unix=OBSERVED_UNIX,
        )


def test_authority_inventory_no_parallel_host() -> None:
    inv = inventory_public_md_shadow_authority_surfaces_v1()
    assert inv["second_canonical_runtime_host_created"] is False
    assert inv["parallel_runtime_authority_created"] is False
    assert inv["legacy_parallel_authority_absent"] is True
    assert inv["core_logic_changed"] is False
    assert inv["selection_authority_unchanged"] is True


def test_public_md_shadow_evidence_end_to_end(fixture_roots: dict) -> None:
    evidence_root = fixture_roots["accounting"].parent / "evidence"
    lock_root = fixture_roots["accounting"].parent / "locks"
    evidence_root.mkdir()
    lock_root.mkdir()
    gate = run_single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1(
        selection_state_root=fixture_roots["selection"],
        ranking_state_root=fixture_roots["ranking"],
        universe_state_root=fixture_roots["universe"],
        reconciliation_state_root=fixture_roots["recon"],
        accounting_state_root=fixture_roots["accounting"],
        evidence_root=evidence_root,
        lock_root=lock_root,
        repository_sha=REPO_SHA,
        baseline_sha=REPO_SHA,
        session_id="test-cap52",
        now_unix=OBSERVED_UNIX,
        mark_price_by_native_id=fixture_roots["marks"],
        authorization_artifact=_auth_artifact(),
        http_fetcher=fixture_roots["mock_fetcher"],
        cycle_count=DEFAULT_CYCLE_COUNT,
        tmp_root=fixture_roots["accounting"].parent / "tmp",
        consumption_store=fixture_roots["accounting"].parent / "auth",
    )
    assert gate.ok
    assert gate.ready_for_activation
    assert gate.runtime_activated is False
    assert gate.status == "READY_FOR_ACTIVATION"
    assert gate.evidence.independent_run["match"] is True
    assert gate.evidence.restart_recovery["RESTART_FINAL_STATE_MATCH"] is True
    assert gate.evidence.restart_recovery["RESTART_EVIDENCE_DIGEST_MATCH"] is True
    assert gate.evidence.verifier_result["ok"] is True
    assert gate.evidence.authorization_consumption["authorization_consumed"] is True
    assert gate.evidence.public_md_capture["network_access_occurred"] is True
    assert gate.evidence.public_md_capture["public_market_data_only"] is True
    assert gate.evidence.public_md_capture["orders_attempted"] is False
    assert gate.evidence.telemetry["cycle_count"] >= 8
    assert gate.evidence.telemetry["typed_volatility_presence_events"] >= 1
    for strata in gate.evidence.telemetry["numeric_max_age_strata_diagnostic"]:
        assert strata["enforcement_enabled"] is False
        assert strata["mutates_alpha_risk_safety"] is False
    assert set(REQUIRED_GATE_FLAGS).issubset(set(gate.gate_flags.flags))
    assert gate.gate_flags.all_true()
    assert "okx_public_market_data_capture" in CALL_GRAPH_AFTER
    assert "public_md_no_order_shadow_replay" in CALL_GRAPH_AFTER
    assert "authorization_contract_validation_and_consumption" in CALL_GRAPH_AFTER

    persist_public_md_shadow_evidence_atomic_v1(
        evidence_root=evidence_root,
        evidence=gate.evidence.to_dict(),
        result=gate.to_dict(),
        gate=gate.gate_flags.to_dict(),
        telemetry=gate.evidence.telemetry,
        restart=gate.evidence.restart_recovery,
        failure_injection=gate.evidence.failure_injection_results,
        capture=gate.evidence.public_md_capture,
        authorization_consumption=gate.evidence.authorization_consumption,
    )
    assert verify_manifest(evidence_root)["ok"] is True


def test_activation_and_no_order_negatives(fixture_roots: dict) -> None:
    evidence_root = fixture_roots["accounting"].parent / "evidence2"
    lock_root = fixture_roots["accounting"].parent / "locks2"
    evidence_root.mkdir()
    lock_root.mkdir()
    gate = run_single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1(
        selection_state_root=fixture_roots["selection"],
        ranking_state_root=fixture_roots["ranking"],
        universe_state_root=fixture_roots["universe"],
        reconciliation_state_root=fixture_roots["recon"] / "neg",
        accounting_state_root=fixture_roots["accounting"] / "neg",
        evidence_root=evidence_root,
        lock_root=lock_root,
        repository_sha=REPO_SHA,
        baseline_sha=REPO_SHA,
        session_id="test-cap52-neg",
        now_unix=OBSERVED_UNIX,
        mark_price_by_native_id=fixture_roots["marks"],
        authorization_artifact=_auth_artifact(),
        http_fetcher=fixture_roots["mock_fetcher"],
        tmp_root=fixture_roots["accounting"].parent / "tmp2",
        consumption_store=fixture_roots["accounting"].parent / "auth2",
    )
    assert gate.evidence.activation_negative["RUNTIME_ACTIVATED"] is False
    assert gate.evidence.activation_negative["status_unchanged"] is True
    assert gate.evidence.network_order_negative["NO_LIVE_ORDER_PATH"] is True
    assert gate.evidence.network_order_negative["NO_TESTNET_ORDER_PATH"] is True
    assert gate.evidence.network_order_negative["NO_PAPER_ORDER_PATH"] is True
    assert gate.evidence.network_order_negative["NO_ORDER_PATH"] is True
    assert gate.evidence.network_order_negative["NETWORK_ACCESS_OCCURRED"] is True


def test_failure_injection_matrix_covered(fixture_roots: dict) -> None:
    evidence_root = fixture_roots["accounting"].parent / "evidence3"
    lock_root = fixture_roots["accounting"].parent / "locks3"
    evidence_root.mkdir()
    lock_root.mkdir()
    gate = run_single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1(
        selection_state_root=fixture_roots["selection"],
        ranking_state_root=fixture_roots["ranking"],
        universe_state_root=fixture_roots["universe"],
        reconciliation_state_root=fixture_roots["recon"] / "fi",
        accounting_state_root=fixture_roots["accounting"] / "fi",
        evidence_root=evidence_root,
        lock_root=lock_root,
        repository_sha=REPO_SHA,
        baseline_sha=REPO_SHA,
        session_id="test-cap52-fi",
        now_unix=OBSERVED_UNIX,
        mark_price_by_native_id=fixture_roots["marks"],
        authorization_artifact=_auth_artifact(),
        http_fetcher=fixture_roots["mock_fetcher"],
        tmp_root=fixture_roots["accounting"].parent / "tmp3",
        consumption_store=fixture_roots["accounting"].parent / "auth3",
    )
    keys = set(gate.evidence.failure_injection_results)
    for required in (
        "STALE_SELECTION",
        "SELECTION_DIGEST_MISMATCH",
        "MISSING_MARK_PRICE",
        "MISSING_TYPED_VOLATILITY",
        "AUTHORIZATION_ALREADY_CONSUMED",
        "LIVE_ORDER_PATH_REACHABLE",
        "TESTNET_ORDER_PATH_REACHABLE",
        "PAPER_ORDER_PATH_REACHABLE",
        "MULTI_FUTURE_ENABLED",
        "NUMERIC_MAX_AGE_ENFORCEMENT_ENABLED",
    ):
        assert required in keys
        assert gate.evidence.failure_injection_results[required]["ok"] is True


def test_entrypoint_script_exists_and_is_no_order() -> None:
    path = (
        REPO_ROOT
        / "scripts/ops/run_single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.py"
    )
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "no live" in lowered or "no_order" in lowered or "no-order" in lowered
    assert "import websocket" not in lowered
    assert "/api/v5/trade/" not in text
    assert "/api/v5/account/" not in text
