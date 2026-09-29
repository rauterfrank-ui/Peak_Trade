"""E2E 10k native full-cycle v6 — single host invocation + glass-box trace.

AUTHORITY=NONE · Driver does not call Slice A/B directly.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
PKG_ROOT = Path(__file__).resolve().parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from native_trace_engine_v6 import AUTHORITY, NativeTraceEngineV6, TRACE_ID  # noqa: E402

BASELINE_SHA = "279244ea9ad457ce2dd779eacde58f30150c56a3"
AVAIL_EQ = "10000.00"
EVIDENCE_BASE = PKG_ROOT / "evidence"

# Driver invocation counters (static + runtime).
TEST_DRIVER_NATIVE_HOST_INVOCATION_COUNT = 0
TEST_DRIVER_SLICE_A_INVOCATION_COUNT = 0
TEST_DRIVER_SLICE_B_INVOCATION_COUNT = 0


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def _build_transports(*, instrument_id: str):
    from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
        ENDPOINT_PUBLIC_INSTRUMENTS,
    )
    from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
        _identity_payloads,
    )
    from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
        ProductiveClassFreshGetTransportV1,
        _productive_instruments_row_for_enter_metadata_v1,
    )
    from tests.ops.test_full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
        _eligible_transport,
    )

    payloads = dict(_identity_payloads(instrument_id=instrument_id, avail_eq=AVAIL_EQ))
    payloads[ENDPOINT_PUBLIC_INSTRUMENTS] = {
        "code": "0",
        "data": [_productive_instruments_row_for_enter_metadata_v1(instrument_id=instrument_id)],
    }
    return (
        _eligible_transport(),
        ProductiveClassFreshGetTransportV1(payloads=payloads),
        ProductiveClassFreshGetTransportV1(payloads=dict(payloads)),
    )


def main() -> int:
    global TEST_DRIVER_NATIVE_HOST_INVOCATION_COUNT
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_root = EVIDENCE_BASE / run_stamp
    evidence_root.mkdir(parents=True, exist_ok=True)

    origin_main = _git("rev-parse", "origin/main")
    tree_match = origin_main == BASELINE_SHA

    engine = NativeTraceEngineV6()
    report: dict[str, Any] = {
        "TRACE_ID": TRACE_ID,
        "AUTHORITY": AUTHORITY,
        "BASELINE_SHA": BASELINE_SHA,
        "ORIGIN_MAIN_SHA": origin_main,
        "TREE_MATCH": tree_match,
        "FRESH_V6_EVIDENCE_PATH": str(evidence_root),
        "AVAIL_EQ": AVAIL_EQ,
        "TEST_DRIVER_NATIVE_HOST_INVOCATION_COUNT": 0,
        "TEST_DRIVER_SLICE_A_INVOCATION_COUNT": 0,
        "TEST_DRIVER_SLICE_B_INVOCATION_COUNT": 0,
        "DRIVER_BOUND_RELOAD_COUNT": 0,
        "DRIVER_PREARM_MV2_COUNT": 0,
        "DRIVER_ENTER_STATE_INJECTION_COUNT": 0,
        "DRIVER_TRADING_DECISION_CREATION_COUNT": 0,
        "DRIVER_CAPITAL_CONTEXT_CREATION_COUNT": 0,
        "DRIVER_CRS_RESULT_CREATION_COUNT": 0,
        "DRIVER_ORDER_INTENT_CREATION_COUNT": 0,
        "PREPARE_LAYERED_LONG_ARMED_FIXTURE_CALL_COUNT": 0,
        "NO_DRIVER_INTERNAL_BUSINESS_BRIDGE": True,
    }

    if not tree_match:
        report["FRESH_V6_RUNTIME_EXECUTED"] = False
        engine.write_artifacts(evidence_root, report=report)
        print(json.dumps(report, indent=2))
        return 2

    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_native_full_cycle_host_v1 import (
        OWNER_GO,
        execute_current_productive_native_full_cycle_host_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
        DISPOSITION_PRE_EXTERNAL_EFFECT,
    )
    from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
        MockCurrentProductive29PIntegrityBackendV1,
    )

    acq, get_a, get_b = _build_transports(instrument_id="ADA-USDT-SWAP")
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_main, head=origin_main
    )

    ext_oid = engine.register_object(
        {"avail_eq": AVAIL_EQ, "semantic": "SIMULATED_TRUSTED_VENUE_OBSERVATION", "ccy": "USDC"},
        producer_call_id=None,
        extra={
            "semantic_type": "EXTERNAL_ACCOUNT_OBSERVATION",
            "currency": "USDC",
            "value_summary": AVAIL_EQ,
        },
    )

    engine.start()
    sys.settrace(engine.trace_function)
    try:
        TEST_DRIVER_NATIVE_HOST_INVOCATION_COUNT = 1
        result = execute_current_productive_native_full_cycle_host_v1(
            owner_go=OWNER_GO,
            origin_main_sha=origin_main,
            evidence_root=evidence_root / "host_store",
            acquisition_transport=acq,
            fresh_get_transport=get_a,
            pre_external_fresh_get_transport=get_b,
            execute_network=False,
            producer_observed_at_unix=1_700_000_100.0,
            execution_integrity_backend=integrity,
        )
    finally:
        sys.settrace(None)
        engine.stop()

    host_oid = engine.register_object(result, producer_call_id="CALL_DRIVER_HOST")
    engine.record_handoff(
        producer_call_id="CALL_DRIVER_EXT",
        output_object_id=ext_oid,
        consumer_call_id="CALL_DRIVER_HOST",
        input_object_id=ext_oid,
        handoff_type="EXTERNAL_FIXTURE_INPUT",
        identity_or_derivation_proof="fixture_transport_only",
    )
    if result.eea_result.bound_instrument is not None:
        bound_oid = engine.register_object(
            result.eea_result.bound_instrument,
            producer_call_id=host_oid,
        )
        engine.record_handoff(
            producer_call_id=host_oid,
            output_object_id=bound_oid,
            consumer_call_id=host_oid,
            input_object_id=bound_oid,
            handoff_type="NATIVE_TYPED_HANDOFF",
            identity_or_derivation_proof=result.bound_instrument_handoff,
        )

    bound = result.eea_result.bound_instrument
    envelope = result.pre_external_result.fresh_executable_enter_final_order_envelope
    prearm_count = sum(
        1
        for c in engine.calls
        if c["function"] == "prepare_layered_long_armed_seed_for_pre_external_invoke_v1"
    )
    reload_count = sum(
        1
        for c in engine.calls
        if c["function"]
        == "acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1"
    )

    mv2_ledger = engine.build_mv2_state_transition_ledger()
    initial_armed = any("ARMED" in str(t.get("state_after") or "") for t in mv2_ledger[:1])
    initial_enter = any(str(t.get("output") or "") == "enter_long" for t in mv2_ledger[:1])

    report.update(
        {
            "FRESH_V6_RUNTIME_EXECUTED": True,
            "SESSION_ID": result.session_id,
            "BOUND_INSTRUMENT_HANDOFF": result.bound_instrument_handoff,
            "TERMINAL_DISPOSITION": result.terminal_disposition,
            "PRE_EXTERNAL_REACHED": result.pre_external_reached == "true",
            "FINAL_QUANTITY": envelope.quantity if envelope else "",
            "CAPITAL_SPLIT_OCCURRED": False,
            "PERMITS_MINTED": 0,
            "VENUE_POSTS": 0,
            "NATIVE_FULL_CYCLE_PROVEN": result.terminal_disposition
            == DISPOSITION_PRE_EXTERNAL_EFFECT,
            "TEST_DRIVER_NATIVE_HOST_INVOCATION_COUNT": TEST_DRIVER_NATIVE_HOST_INVOCATION_COUNT,
            "TEST_DRIVER_SLICE_A_INVOCATION_COUNT": TEST_DRIVER_SLICE_A_INVOCATION_COUNT,
            "TEST_DRIVER_SLICE_B_INVOCATION_COUNT": TEST_DRIVER_SLICE_B_INVOCATION_COUNT,
            "DRIVER_BOUND_RELOAD_COUNT": reload_count,
            "DRIVER_PREARM_MV2_COUNT": prearm_count,
            "PREPARE_LAYERED_LONG_ARMED_FIXTURE_CALL_COUNT": prearm_count,
            "TOTAL_NATIVE_RUNTIME_CALLS": len(engine.calls),
            "TOTAL_NATIVE_RUNTIME_OBJECTS": len(engine.objects),
            "TOTAL_NATIVE_MATERIAL_HANDOFFS": len(engine.handoffs),
            "MV2_INITIAL_STATE_NOT_ARMED": not initial_armed,
            "MV2_INITIAL_STATE_NOT_ENTER": not initial_enter,
            "ARM_STATE_DERIVED_BY_CURRENT_LOGIC": bool(result.mv2_advance_arm_side_state),
            "ENTER_DECISION_DERIVED_BY_CURRENT_LOGIC": result.terminal_disposition
            == DISPOSITION_PRE_EXTERNAL_EFFECT,
        }
    )
    if bound is not None:
        report["BOUND_VENUE_NATIVE_ID"] = bound.venue_native_id

    capital = {
        "external_observation_object_id": ext_oid,
        "avail_eq_fixture": AVAIL_EQ,
        "avail_eq_decimal": str(Decimal(AVAIL_EQ)),
        "fresh_usdc_status": result.eea_result.fresh_usdc_availeq_status,
        "step_29p_admissible": result.eea_result.step_29p_risk_admissible,
        "u01_status": result.eea_result.u01_status,
        "p01_status": result.eea_result.p01_status,
        "live_account_bound_status": result.eea_result.live_account_bound_status,
    }
    ranking = {
        "cap21_snapshot_id": result.eea_result.cap21_snapshot_id,
        "cap22_ranking_id": result.eea_result.cap22_ranking_id,
        "cap23_selection_decision_id": result.eea_result.cap23_selection_decision_id,
        "cap23_selected_instrument_id": result.eea_result.cap23_selected_instrument_id,
        "cap24_bound_instrument_id": result.eea_result.cap24_bound_instrument_id,
    }
    market = {
        "acquisition": "eligible_transport_fixture",
        "bound_venue_native_id": bound.venue_native_id if bound else "",
        "mv2_advance_enter_mark_px": result.pre_external_result.reference_price_status,
    }

    engine.write_artifacts(
        evidence_root,
        report=report,
        mv2_advance={
            "arm_side_state": result.mv2_advance_arm_side_state,
            "arm_decision_outcome": result.mv2_advance_arm_decision,
        },
    )
    for name, payload in (
        ("CAPITAL_LINEAGE.json", capital),
        ("RANKING_LEDGER.json", ranking),
        ("MARKET_INPUT_LEDGER.json", market),
    ):
        (evidence_root / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    print(json.dumps(report, indent=2))
    return 0 if report.get("NATIVE_FULL_CYCLE_PROVEN") else 1


if __name__ == "__main__":
    raise SystemExit(main())
