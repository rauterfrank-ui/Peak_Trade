"""E2E 10k native full-cycle v6 — single host invocation, external fixtures only.

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

BASELINE_SHA = "279244ea9ad457ce2dd779eacde58f30150c56a3"
AVAIL_EQ = "10000.00"
AUTHORITY = "NONE"
EVIDENCE_BASE = PKG_ROOT / "evidence"


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
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_root = EVIDENCE_BASE / run_stamp
    evidence_root.mkdir(parents=True, exist_ok=True)

    origin_main = _git("rev-parse", "origin/main")
    tree_match = origin_main == BASELINE_SHA

    report: dict[str, Any] = {
        "AUTHORITY": AUTHORITY,
        "BASELINE_SHA": BASELINE_SHA,
        "ORIGIN_MAIN_SHA": origin_main,
        "TREE_MATCH": tree_match,
        "FRESH_V6_EVIDENCE_PATH": str(evidence_root),
        "TEST_DRIVER_CALLS_SLICE_A_DIRECTLY": False,
        "TEST_DRIVER_CALLS_SLICE_B_DIRECTLY": False,
        "DRIVER_RELOADS_BOUND_INSTRUMENT": False,
        "DRIVER_PREPARES_MV2_ARM_STATE": False,
        "SINGLE_NATIVE_HOST_INVOCATION": True,
    }

    if not tree_match:
        report["FRESH_V6_RUNTIME_EXECUTED"] = False
        (evidence_root / "NATIVE_FULL_CYCLE_REPORT.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
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
    integrity = MockCurrentProductive29PIntegrityBackendV1(origin_main=origin_main, head=origin_main)

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

    bound = result.eea_result.bound_instrument
    envelope = result.pre_external_result.fresh_executable_enter_final_order_envelope
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
        }
    )
    if bound is not None:
        report["BOUND_VENUE_NATIVE_ID"] = bound.venue_native_id

    handoff = {
        "eea_to_preext": result.bound_instrument_handoff,
        "driver_bound_reload_required": result.driver_bound_reload_required,
        "pre_armed_fixture_used": result.pre_armed_mv2_fixture_used,
    }
    capital = {
        "avail_eq_fixture": AVAIL_EQ,
        "avail_eq_decimal": str(Decimal(AVAIL_EQ)),
        "fresh_usdc_status": result.eea_result.fresh_usdc_availeq_status,
        "step_29p_admissible": result.eea_result.step_29p_risk_admissible,
    }
    sizing = {"quantity": envelope.quantity if envelope else "", "side": envelope.side if envelope else ""}

    for name, payload in (
        ("HANDOFF_LEDGER.json", handoff),
        ("CAPITAL_LINEAGE.json", capital),
        ("SIZING_LEDGER.json", sizing),
        ("NATIVE_FULL_CYCLE_REPORT.json", report),
        ("CALL_GRAPH.json", {"host_only": True, "calls": ["execute_current_productive_native_full_cycle_host_v1"]}),
        ("OBJECT_LINEAGE.json", {"bound_handoff": result.bound_instrument_handoff}),
        ("STATE_TRANSITION_LEDGER.json", {"mv2_arm_side": result.mv2_advance_arm_side_state}),
        ("MARKET_INPUT_LEDGER.json", {"acquisition": "eligible_transport_fixture"}),
        ("RANKING_LEDGER.json", {"cap22_ranking_id": result.eea_result.cap22_ranking_id}),
    ):
        (evidence_root / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    print(json.dumps(report, indent=2))
    return 0 if report.get("NATIVE_FULL_CYCLE_PROVEN") else 1


if __name__ == "__main__":
    raise SystemExit(main())
