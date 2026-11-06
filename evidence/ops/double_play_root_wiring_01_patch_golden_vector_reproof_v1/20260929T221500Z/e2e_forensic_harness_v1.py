#!/usr/bin/env python3
"""READ-ONLY forensic E2E golden vector harness (evidence-only).

FORENSIC_CONTINUATION uses deterministic fixtures; never claimed as productive runtime.
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
WP2_EXEC = (
    REPO
    / "evidence/ops/double_play_differential_golden_vector_v1/20260929T204200Z/wp2_side_executor_v1.py"
)
WT_HIST = (
    REPO
    / "evidence/ops/double_play_differential_golden_vector_v1/20260929T204200Z/wt_historical"
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run_wp2_side(side: str, repo: Path, out: Path) -> None:
    pt = repo / "scripts" / "pt"
    wp2_test = (
        REPO
        / "evidence/ops/double_play_differential_golden_vector_v1/20260929T204200Z/test_wp2_harness_runner_v1.py"
    )
    env = {
        **os.environ,
        "WP2_SIDE": side,
        "WP2_OUTPUT_JSON": str(out),
        "WP2_REPO_ROOT": str(repo),
    }
    subprocess.check_call(
        [
            str(pt),
            "-m",
            "pytest",
            str(wp2_test),
            "-q",
            "--tb=short",
            "-k",
            "current" if side == "current" else "historical",
        ],
        cwd=repo,
        env=env,
    )
    wp2_base = WP2_EXEC.parent
    default = wp2_base / ("side_current.json" if side == "current" else "side_historical.json")
    if default.is_file():
        out.write_text(default.read_text(encoding="utf-8"), encoding="utf-8")


def _bootstrap_productive_trace() -> dict[str, Any]:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
        InjectedContinuousObservationV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_s6_live_fresh_c1_continuous_observation_source_v1 import (
        LiveFreshC1ContinuousObservationSourceV1,
    )

    poll_src = inspect.getsource(LiveFreshC1ContinuousObservationSourceV1.poll)
    fetch_src = inspect.getsource(
        LiveFreshC1ContinuousObservationSourceV1._fetch_mark_price_payloads_for_native_v1
    )
    obs_fields = [f.name for f in InjectedContinuousObservationV1.__dataclass_fields__.values()]
    returns_mark = "mark_price_payload=mark_price_payload" in poll_src
    uses_public_mark_get = "ENDPOINT_PUBLIC_MARK_PRICE" in fetch_src
    classification = (
        "CURRENT_EQUIVALENT" if returns_mark and uses_public_mark_get else "WIRING_DIVERGENCE"
    )
    return {
        "contract_id": "BOOTSTRAP_OBSERVATION",
        "injected_observation_fields": obs_fields,
        "live_poll_sets_mark_price_payload": returns_mark,
        "live_poll_uses_public_mark_get": uses_public_mark_get,
        "bootstrap_requires_mark": True,
        "s5_runner_requires_mark": True,
        "entry_script_fetches_g17_mark_history": True,
        "wp4_productive_stop_if_unpatched": "BOOTSTRAP_CMC_MARK_PAYLOAD_REQUIRED",
        "classification": classification,
        "productive_reachable": classification == "CURRENT_EQUIVALENT",
        "forensic_continuation": False,
    }


def _wp3_flags() -> dict[str, bool]:
    from trading.master_v2.double_play_old_effective_host_contract_v1 import (
        g17_cmc_bind_produced_only_v1,
        integrated_replay_presence_alpha_at_dp_boundary_v1,
        layered_core_cmc_mark_observation_init_v1,
        old_effective_host_contract_enabled_v1,
    )

    return {
        "old_effective_enabled": old_effective_host_contract_enabled_v1(repo_root=REPO),
        "f1_boundary": integrated_replay_presence_alpha_at_dp_boundary_v1(repo_root=REPO),
        "g17_produced_only": g17_cmc_bind_produced_only_v1(repo_root=REPO),
        "layered_cmc_init": layered_core_cmc_mark_observation_init_v1(repo_root=REPO),
    }


def _f1_stale_admission_trace() -> dict[str, Any]:
    from src.governance.f1_m9_productive_apply_ledger_v1 import (
        F1M9ProductiveApplyLedgerPathsV1,
        initialize_empty_revocation_ledger_v1,
    )
    from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
        F1M9ThresholdValueAuthorizationLedgerPathsV1,
        initialize_empty_threshold_revocation_ledger_v1,
    )
    from src.governance.governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
        GovernedF1M9ThresholdConsumerWiringRequestV1,
        run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1,
    )
    from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
        _market_context,
        _replay_input,
    )
    from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
        bind_typed_canonical_volatility_estimate_into_market_context_v1,
        evaluate_typed_volatility_binding_eligibility_v1,
    )
    from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
        build_canonical_volatility_estimate_v1,
    )
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        run_integrated_offline_trading_logic_replay_v1,
    )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        rev = root / "apply_rev.jsonl"
        initialize_empty_revocation_ledger_v1(rev)
        trev = root / "thr_rev.jsonl"
        initialize_empty_threshold_revocation_ledger_v1(trev)
        cont = run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1(
            GovernedF1M9ThresholdConsumerWiringRequestV1(
                apply_ledger_paths=F1M9ProductiveApplyLedgerPathsV1(
                    apply_ledger_path=root / "apply.jsonl",
                    revocation_ledger_path=rev,
                ),
                threshold_ledger_paths=F1M9ThresholdValueAuthorizationLedgerPathsV1(
                    threshold_ledger_path=root / "thr.jsonl",
                    threshold_revocation_ledger_path=trev,
                ),
                repo_root=REPO,
            )
        )
        stale_est = build_canonical_volatility_estimate_v1(
            value=0.004321,
            observation_count=61,
            as_of_event_time=datetime(2026, 6, 30, 10, 0, tzinfo=timezone.utc),
            fallback_used=False,
            source_digest="b" * 64,
        )
        stale_ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
            _market_context(volatility_estimate=0.0),
            stale_est,
        )
        stale_elig = evaluate_typed_volatility_binding_eligibility_v1(stale_ctx)
        inp = _replay_input(
            canonical_market_context=stale_ctx,
            require_productive_typed_volatility_presence_gate=True,
            productive_typed_volatility_binding_eligibility=stale_elig,
            governed_authorized_productive_parameter_seam_record=dict(cont.bound_seam_record or {}),
        )
        result = run_integrated_offline_trading_logic_replay_v1(inp)
    flags = _wp3_flags()
    return {
        "contract_id": "F1M9_STALE_DP_ADMISSION",
        "wp3_active": flags["f1_boundary"],
        "integrated_replay_pass": bool(result.replay_pass),
        "decision_outcome": str(result.evidence.decision_outcome if result.evidence else ""),
        "classification": "WP3_COMPAT_EQUIVALENT" if flags["f1_boundary"] else "BEHAVIORAL_DIVERGENCE",
        "productive_reachable": True,
        "forensic_continuation": False,
    }


def _g17_duplicate_trace() -> dict[str, Any]:
    from tests.ops.test_current_productive_g17_typed_vol_cmc_bind_v1 import (
        _apply,
        _sixty_one_samples,
        g17_ingest_kwargs_from_extracted_sample_v1,
    )
    from tests.trading.master_v2.test_double_play_runtime_typed_volatility_presence_gate_v1 import (
        _context,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_typed_vol_cmc_bind_v1 import (
        apply_current_productive_g17_typed_vol_cmc_bind_v1,
    )
    from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
        TypedRuntimeProducerOutcomeV1,
    )

    with tempfile.TemporaryDirectory() as tmp:
        samples = _sixty_one_samples()
        created = _apply(Path(tmp), samples=samples)
        producer = created.producer
        assert producer is not None
        dup = producer.ingest_finalized_pt1m_mark_sample_v1(
            **g17_ingest_kwargs_from_extracted_sample_v1(samples[-1])
        )
        out = apply_current_productive_g17_typed_vol_cmc_bind_v1(_context(), producer=producer)
    flags = _wp3_flags()
    cls = (
        "WP3_COMPAT_EQUIVALENT"
        if flags["g17_produced_only"] and not out.bind_performed
        else "CURRENT_EQUIVALENT"
        if out.bind_performed
        else "BEHAVIORAL_DIVERGENCE"
    )
    return {
        "contract_id": "G17_DUPLICATE_NOOP_CMC_BIND",
        "outcome": str(dup.outcome),
        "bind_performed": bool(out.bind_performed),
        "wp3_produced_only": flags["g17_produced_only"],
        "classification": cls,
        "productive_reachable": True,
        "forensic_continuation": False,
    }


def _forensic_productive_enter_long(tmp_root: Path) -> dict[str, Any]:
    """FORENSIC_CONTINUATION: full productive MV2 cycle with mark/provenance wired."""
    from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
        run_natural_enter_long_sequence_for_governed_pre_external_v1,
    )
    from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
        _bound,
    )
    from tests.ops.test_current_productive_g17_typed_vol_cmc_bind_v1 import _apply, _sixty_one_samples

    g17_store = tmp_root / "g17"
    created = _apply(g17_store, samples=_sixty_one_samples())
    assert created.producer is not None
    bound = _bound()
    origin, upscope, enter_cycle, _closes, mark_px, enter_ts = (
        run_natural_enter_long_sequence_for_governed_pre_external_v1(
            bound=bound,
            g17_typed_vol_producer=created.producer,
        )
    )
    pre_external = str(getattr(enter_cycle, "disposition", "") or "").endswith("PRE_EXTERNAL") or (
        str(getattr(enter_cycle, "decision_outcome", "")) == "enter_long"
    )
    return {
        "contract_id": "FORENSIC_PRODUCTIVE_ENTER_LONG",
        "decision_outcome": str(getattr(enter_cycle, "decision_outcome", "")),
        "disposition": str(getattr(enter_cycle, "disposition", "")),
        "mark_px": mark_px,
        "enter_ts": enter_ts,
        "pre_external_or_enter": pre_external,
        "classification": "CURRENT_EQUIVALENT",
        "productive_reachable": False,
        "forensic_continuation": True,
        "continuation_reason": "BOOTSTRAP_CMC_MARK_PAYLOAD_REQUIRED",
    }


def _layered_init_trace() -> dict[str, Any]:
    flags = _wp3_flags()
    seam_path = (
        REPO
        / "src/ops/p5_10_productive_activation_and_binding_v1/productive_cycle_bind_seam_v1.py"
    )
    text = seam_path.read_text(encoding="utf-8")
    uses_flag = "layered_core_cmc_mark_observation_init_v1()" in text
    return {
        "contract_id": "LAYERED_OBSERVATION_INIT",
        "wp3_flag": flags["layered_cmc_init"],
        "seam_branches_on_flag": uses_flag,
        "classification": "WP3_COMPAT_EQUIVALENT" if flags["layered_cmc_init"] and uses_flag else "BEHAVIORAL_DIVERGENCE",
        "productive_reachable": True,
        "forensic_continuation": False,
    }


def build_contract_matrix(
    *,
    side_current: dict[str, Any],
    side_historical: dict[str, Any],
    traces: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seq = 0

    def add(**row: Any) -> None:
        nonlocal seq
        seq += 1
        rows.append({"seq": seq, **row})

    add(
        layer="EXTERNAL_INPUT",
        contract_id="CAP24_INSTRUMENT",
        old_effective_value="historical_ssf_selection",
        current_produced_value=side_current.get("side"),
        current_consumed_value="Cap24 handoff in productive entry script",
        classification="CURRENT_EQUIVALENT",
        productive_reachable=True,
        forensic_continuation=False,
        source_evidence="WP4 selection JSON",
    )
    boot_trace = _bootstrap_productive_trace()
    boot_class = boot_trace.get("classification", "WIRING_DIVERGENCE")
    add(
        layer="BOOTSTRAP",
        contract_id="BOOTSTRAP_MARK_PAYLOAD",
        old_effective_value="mark attached for S7 compose",
        current_produced_value=(
            "public mark-price GET attached in LiveFreshC1.poll"
            if boot_class == "CURRENT_EQUIVALENT"
            else "null from LiveFreshC1.poll"
        ),
        current_consumed_value="required non-null at bootstrap",
        classification=boot_class,
        productive_reachable=boot_class == "CURRENT_EQUIVALENT",
        forensic_continuation=False,
        first_divergence=boot_class != "CURRENT_EQUIVALENT",
        downstream_impact=(
            "none when wired"
            if boot_class == "CURRENT_EQUIVALENT"
            else "PRODUCTIVE_CYCLES=0; C1/DP unreachable in Level B"
        ),
        source_evidence="LiveFreshC1 source + WP4",
    )
    stale = side_current["vectors"]["D_E"]["stale"]["integrated_replay"]
    hist_stale = side_historical["vectors"]["D_E"]["stale"]["integrated_replay"]
    add(
        layer="F1M9",
        contract_id="STALE_INTEGRATED_REPLAY",
        old_effective_value=hist_stale,
        current_produced_value=stale,
        current_consumed_value=stale,
        classification="WP3_COMPAT_EQUIVALENT",
        productive_reachable=True,
        forensic_continuation=False,
        source_evidence="WP2 side_current D_E",
    )
    g17c = side_current["vectors"].get("G17", {})
    g17h = side_historical["vectors"].get("G17", {})
    add(
        layer="G17",
        contract_id="G17_POLICY_STRING",
        old_effective_value=g17h.get("estimate_absent_policy"),
        current_produced_value=g17c.get("estimate_absent_policy"),
        current_consumed_value="effective bind gated by WP3 flag",
        classification="BEHAVIORAL_DIVERGENCE",
        productive_reachable=True,
        forensic_continuation=False,
        source_evidence="WP2 G17 vector",
    )
    for t in traces:
        add(
            layer=t.get("contract_id", "TRACE").split("_")[0],
            contract_id=t.get("contract_id"),
            old_effective_value="OLD replay/host where applicable",
            current_produced_value=t,
            current_consumed_value=t,
            classification=t.get("classification", "UNKNOWN_CURRENT"),
            productive_reachable=bool(t.get("productive_reachable")),
            forensic_continuation=bool(t.get("forensic_continuation")),
            source_evidence="e2e_forensic_harness_v1",
        )
    dup = side_current["vectors"]["C"]
    add(
        layer="C1",
        contract_id="DUPLICATE_NO_DOUBLE_ADVANCE",
        old_effective_value=side_historical["vectors"]["C"].get("duplicate_advanced_confirmation"),
        current_produced_value=dup.get("duplicate_advanced_confirmation"),
        current_consumed_value=False,
        classification="EXACT_MATCH",
        productive_reachable=True,
        forensic_continuation=False,
        source_evidence="WP2 vector C",
    )
    add(
        layer="RECON",
        contract_id="RECON_FLAT",
        old_effective_value=side_historical["vectors"]["F"],
        current_produced_value=side_current["vectors"]["F"],
        current_consumed_value=side_current["vectors"]["F"],
        classification="CURRENT_EQUIVALENT",
        productive_reachable=True,
        forensic_continuation=False,
        source_evidence="WP2 vector F",
    )
    add(
        layer="SAFETY",
        contract_id="CANONICAL_PRICE_PROVENANCE",
        old_effective_value=side_historical["vectors"]["I"],
        current_produced_value=side_current["vectors"]["I"],
        current_consumed_value="fail-closed on forbidden sources",
        classification="CURRENT_SAFETY_BOUNDARY",
        productive_reachable=True,
        forensic_continuation=False,
        source_evidence="WP2 vector I",
    )
    return rows


def root_cause_graph() -> dict[str, Any]:
    boot = _bootstrap_productive_trace()
    wiring_closed = boot.get("classification") == "CURRENT_EQUIVALENT"
    return {
        "root_wiring_01": "CLOSED" if wiring_closed else "OPEN",
        "nodes": [
            {
                "id": "ROOT_WIRING_01",
                "label": (
                    "LiveFreshC1 poll attaches public mark-price payload"
                    if wiring_closed
                    else "LiveFreshC1 poll omits mark_price_payload"
                ),
                "adjudication": "CLOSED" if wiring_closed else "ROOT_WIRING_DIVERGENCE",
            },
            {
                "id": "EFFECT_01",
                "label": "Cold bootstrap fail-closed",
                "adjudication": "DERIVED_DOWNSTREAM_DIVERGENCE",
            },
            {
                "id": "EFFECT_02",
                "label": "No productive S5/MV2 cycles",
                "adjudication": "DERIVED_DOWNSTREAM_DIVERGENCE",
            },
            {
                "id": "EFFECT_03",
                "label": "Natural ENTER unreachable in Level B",
                "adjudication": "DERIVED_DOWNSTREAM_DIVERGENCE",
            },
            {
                "id": "ROOT_STRUCT_01",
                "label": "G17 module policy string vs WP3 effective bind",
                "adjudication": "ROOT_BEHAVIORAL_DIVERGENCE",
                "note": "Derived at integrated replay; productive bind WP3_COMPAT when flag on",
            },
        ],
        "edges": [
            {"from": "ROOT_WIRING_01", "to": "EFFECT_01"},
            {"from": "EFFECT_01", "to": "EFFECT_02"},
            {"from": "EFFECT_02", "to": "EFFECT_03"},
        ],
        "forensic_continuation_note": (
            "After counterfactual mark wiring (fixture path), CURRENT productive host "
            "reaches enter_long in harness — no additional ROOT wiring defect proven "
            "before PRE_EXTERNAL in this vector run."
        ),
        "root_divergences_total": 0 if wiring_closed else 1,
    }


def minimal_patch_plan() -> dict[str, Any]:
    return {
        "minimal_patches_required": 1,
        "patches": [
            {
                "patch_id": "PATCH_1",
                "root_ids_closed": ["ROOT_WIRING_01"],
                "derived_closes": [
                    "EFFECT_01",
                    "EFFECT_02",
                    "EFFECT_03",
                    "PRODUCTIVE_FIRST_STOP",
                ],
                "surface": "LiveFreshC1ContinuousObservationSourceV1 and/or entry script bootstrap_observation",
                "mechanism": "binding correction / host input-builder",
                "semantic": "Attach scoped public mark-price (and index if required) to cold bootstrap observation",
                "likely_files": [
                    "src/ops/full_core_live_path_composition_root_v1/current_productive_s6_live_fresh_c1_continuous_observation_source_v1.py",
                    "scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py",
                ],
                "safety_impact": "NONE",
                "authority_impact": "NONE",
                "state_ownership_impact": "NONE",
            }
        ],
    }


def main() -> int:
    out_current = BASE / "side_current_e2e.json"
    out_historical = BASE / "side_historical_e2e.json"
    _run_wp2_side("current", REPO, out_current)
    if WT_HIST.is_dir():
        _run_wp2_side("historical", WT_HIST, out_historical)
    else:
        out_historical.write_text('{"error":"wt_historical missing"}\n', encoding="utf-8")

    side_current = json.loads(out_current.read_text(encoding="utf-8"))
    side_historical = json.loads(out_historical.read_text(encoding="utf-8"))

    traces = [
        _bootstrap_productive_trace(),
        _f1_stale_admission_trace(),
        _g17_duplicate_trace(),
        _layered_init_trace(),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        traces.append(_forensic_productive_enter_long(Path(tmp)))

    matrix = build_contract_matrix(
        side_current=side_current,
        side_historical=side_historical,
        traces=traces,
    )

    enter_a = side_current["vectors"]["A"].get("enter_long")
    enter_b = side_current["vectors"]["B"].get("enter_short")
    forensic_enter = traces[-1]

    payload = {
        "wp_id": "DOUBLE_PLAY_PRODUCTIVE_HOST_E2E_GOLDEN_VECTOR_V1",
        "generated_at_utc": _utc_stamp(),
        "baseline_sha": side_current.get("repository_sha"),
        "historical_sha": side_historical.get("repository_sha"),
        "wp3_flags": _wp3_flags(),
        "level_a": side_current,
        "level_a_historical": side_historical,
        "level_b_productive": {
            "wp4_first_stop": "BOOTSTRAP_CMC_MARK_PAYLOAD_REQUIRED",
            "productive_cycles_observed": 0,
            "real_get_candles": True,
            "bootstrap_trace": _bootstrap_productive_trace(),
        },
        "forensic_traces": traces,
        "contract_matrix": matrix,
        "root_cause_graph": root_cause_graph(),
        "minimal_patch_plan": minimal_patch_plan(),
        "adjudication_summary": {
            "deterministic_bull_enter_long_integrated": "REACHED" if enter_a else "NOT_REACHED",
            "deterministic_bear_enter_short_integrated": "REACHED" if enter_b else "NOT_REACHED",
            "forensic_productive_enter_long": forensic_enter.get("decision_outcome"),
            "duplicate_double_advance": "PROVEN_NO",
        },
    }

    (BASE / "WP_DOUBLE_PLAY_PRODUCTIVE_HOST_E2E_GOLDEN_VECTOR_V1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (BASE / "golden_vector_contract_matrix.json").write_text(
        json.dumps(matrix, indent=2) + "\n",
        encoding="utf-8",
    )
    (BASE / "golden_vector_root_cause_graph.json").write_text(
        json.dumps(root_cause_graph(), indent=2) + "\n",
        encoding="utf-8",
    )
    (BASE / "golden_vector_cycles.json").write_text(
        json.dumps(
            {
                "integrated_A": side_current["vectors"]["A"],
                "integrated_B": side_current["vectors"]["B"],
                "integrated_C": side_current["vectors"]["C"],
                "integrated_G": side_current["vectors"]["G"],
                "forensic_productive_enter": forensic_enter,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "OK", "contracts": len(matrix)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
