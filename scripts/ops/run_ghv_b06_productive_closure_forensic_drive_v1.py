#!/usr/bin/env python3
"""GHV B06 productive closure + identity alignment forensic driver (offline)."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

BASE_SHA = "d62eb64ca83e1562b9f8bf7d1506cf65535f51d3"
OBSERVED_UNIX = 1_700_000_100.0
POST6999 = (
    REPO
    / "evidence/ops/golden_happy_vector_instrumented_information_funnel_post6999_v1/20261001T212755Z"
)


@dataclass
class BoundaryRecord:
    boundary_id: str
    traversed: bool
    identity: str = ""
    failure_cause: str = ""


@dataclass
class DriveResult:
    pass_name: str
    boundaries: list[BoundaryRecord] = field(default_factory=list)
    first_failed: str = ""
    first_cause: str = ""
    selected_native: str = ""
    downstream: dict = field(default_factory=dict)


def _perp(inst_id: str, base: str) -> dict[str, str]:
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


def _on_only_acq():
    from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
        EeaUniverseAcquisitionResultV1,
    )
    from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
        SOURCE_KIND,
    )

    row = _perp("ON-USDT-SWAP", "ON")
    return EeaUniverseAcquisitionResultV1(
        ok=True,
        host="eea.okx.com",
        venue="okx_eea",
        source_kind=SOURCE_KIND,
        source_event_time="1700000000000",
        instruments_payload={"code": "0", "msg": "", "data": [row]},
        mark_price_payload={
            "code": "0",
            "msg": "",
            "data": [{"instId": "ON-USDT-SWAP", "markPx": "100.5"}],
        },
        endpoints_used=("/api/v5/public/instruments",),
        methods_used=("GET",),
        post_count="0",
        request_count=2,
        venue_live_contact=False,
        failure_codes=(),
        provenance={"ghv_b06_on_only": True},
    )


def _run_upstream(
    *,
    store: Path,
    integrated_eval: bool,
    on_only: bool,
) -> DriveResult:
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap21_to_cap23_productive_persistence_v1 import (
        run_cap21_to_cap23_persist_productive_v1,
    )
    from src.ops.single_selected_future_policy_v1.residency_eligibility_gate_v1 import (
        Cap23ResidencyEligibilityGateConfigV1,
    )
    from src.ops.top20_opportunity_evaluation_residency_v1.models_v1 import ResidencyRuntimeConfigV1
    from src.ops.top20_opportunity_evaluation_residency_v1.persistence_v1 import load_store_v1
    from src.ops.top20_opportunity_evaluation_residency_v1.scoped_productive_residency_evaluation_completion_v1 import (
        ScopedResidencyIntegratedEvaluationConfigV1,
    )
    from tests.ops._productive_economic_md_inject_helpers_v1 import (
        injected_economic_md_source_for_venue_native_ids_v1,
    )

    out = DriveResult(pass_name="upstream")
    acq = _on_only_acq() if on_only else None
    if acq is None:
        from tests.ops.test_full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
            _eligible_rows,
            _okx_envelope,
        )
        from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
            EeaUniverseAcquisitionResultV1,
        )

        rows = _eligible_rows()
        ids = [r["instId"] for r in rows]
        acq = EeaUniverseAcquisitionResultV1(
            ok=True,
            host="eea.okx.com",
            venue="okx_eea",
            source_kind="okx_eea_public_instruments",
            source_event_time="1700000000000",
            instruments_payload=_okx_envelope(rows=rows),
            mark_price_payload=_okx_envelope(
                rows=[{"instId": i, "markPx": "100.5"} for i in ids],
            ),
            endpoints_used=("/api/v5/public/instruments",),
            methods_used=("GET",),
            post_count="0",
            request_count=2,
            venue_live_contact=False,
            failure_codes=(),
            provenance={},
        )
        md = injected_economic_md_source_for_venue_native_ids_v1(ids)
    else:
        md = injected_economic_md_source_for_venue_native_ids_v1(["ON-USDT-SWAP"])

    gate = Cap23ResidencyEligibilityGateConfigV1(
        enabled=True,
        scoped_productive_activation=True,
    )
    residency_cfg = ResidencyRuntimeConfigV1(enabled=True)
    eval_cfg = None
    if integrated_eval and POST6999.is_dir():
        eval_cfg = ScopedResidencyIntegratedEvaluationConfigV1(
            dataset_root=POST6999,
            repository_sha=BASE_SHA,
            max_cycles=4,
            max_duration_seconds=180.0,
            g17_provision="natural_checkpoint",
        )

    persist = run_cap21_to_cap23_persist_productive_v1(
        acquisition=acq,
        store=store,
        repository_sha=BASE_SHA,
        observed_unix=OBSERVED_UNIX,
        session_id_prefix="ghv-b06",
        economic_md_public_source=md,
        residency_runtime_config=residency_cfg,
        cap23_residency_eligibility_gate=gate,
        scoped_top20_evaluation_residency_v1=True,
        scoped_residency_integrated_evaluation=eval_cfg,
    )
    out.boundaries.append(BoundaryRecord("B01-B05", persist.ok or "COMPLETION" in persist.status))
    b06 = persist.ok or "COMPLETION" not in str(persist.status)
    if not integrated_eval:
        b06 = False
    if persist.ok:
        res_root = store / "runtime_state/ranking/top20_evaluation_residency_v1"
        completed = any(
            r.state == "COMPLETED_EVALUATION_WINDOW" for r in load_store_v1(res_root).records
        )
        events_path = res_root / "residency_events.jsonl"
        has_event = events_path.is_file() and "EVALUATION_OBSERVED" in events_path.read_text(
            encoding="utf-8"
        )
        b06 = completed and has_event
    out.boundaries.append(
        BoundaryRecord(
            "B06_EVALUATION_COMPLETION_WITNESS",
            b06,
            failure_cause="" if b06 else str(persist.status),
        )
    )
    if not b06:
        out.first_failed = "B06_EVALUATION_COMPLETION_WITNESS"
        out.first_cause = str(persist.status)
        return out
    out.boundaries.append(BoundaryRecord("B07_CAP23", persist.ok))
    if persist.selection:
        out.selected_native = str(persist.selection.venue_native_id)
        out.boundaries.append(BoundaryRecord("B08_CAP24_BIND", True, identity=out.selected_native))
    return out


def main() -> int:
    report: dict = {"BASE_SHA": BASE_SHA}
    with tempfile.TemporaryDirectory() as td:
        store0 = Path(td) / "pass0"
        store0.mkdir()
        p0 = _run_upstream(store=store0, integrated_eval=False, on_only=True)
        report["GHV_PASS0"] = asdict(p0)

    with tempfile.TemporaryDirectory() as td:
        store1 = Path(td) / "pass1"
        store1.mkdir()
        p1 = _run_upstream(store=store1, integrated_eval=True, on_only=True)
        report["GHV_PASS1"] = asdict(p1)

    with tempfile.TemporaryDirectory() as td:
        store2 = Path(td) / "pass2"
        store2.mkdir()
        p2 = _run_upstream(store=store2, integrated_eval=True, on_only=False)
        report["GHV_PASS2_MULTI_INSTRUMENT"] = asdict(p2)
        report["IDENTITY_DIVERGENCE"] = {
            "on_only_selected": report["GHV_PASS1"].get("selected_native"),
            "multi_selected": p2.selected_native,
            "replay_instrument": "ON-USDT-SWAP",
            "match_on_only": report["GHV_PASS1"].get("selected_native") == "ON-USDT-SWAP",
        }

    out_path = REPO / "runtime/governance/ghv_b06_productive_closure_forensic_drive_v1.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"written": str(out_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
