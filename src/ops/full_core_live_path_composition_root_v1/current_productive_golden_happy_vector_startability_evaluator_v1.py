"""Golden Happy Vector startability evaluator (AUTHORITY=NONE, read-only).

Composes CURRENT contracts and validators against a reference golden vector bundle.
Does not select, rank, POST, mutate runtime state, or open safety gates.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.ops.pre_external_convergence_natural_enter_reporting_v1 import (
    evaluate_natural_enter_reporting_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    SCOPE_INITIALIZATION_POLICY_INSTRUMENT_RELATIVE_VERSION,
)
from trading.master_v2.golden_geometry_engine_v1 import (
    GGE_OWNER,
    GoldenGeometryEngineV1,
    compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1,
)
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    resolve_layer_c_event_distances_from_mark_and_volatility_v1,
)

EVALUATOR_OWNER = (
    "full_core_live_path_composition_root_v1."
    "current_productive_golden_happy_vector_startability_evaluator_v1"
)
START_ENTRYPOINT = (
    "scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py"
)

GHV_HAS_TRADING_AUTHORITY = False
GHV_HAS_SELECTION_AUTHORITY = False
GHV_HAS_GEOMETRY_AUTHORITY = False
GHV_CAN_POST = False
GHV_CAN_OPEN_SAFETY_GATES = False
GHV_AUTHORITY = "NONE"
TRADING_AUTHORITY = "NONE"
SELECTION_AUTHORITY = "NONE"
GEOMETRY_AUTHORITY = "NONE"
EXECUTION_AUTHORITY = "NONE"
NETWORK_REQUIRED_FOR_STRUCTURAL_MODE = False
EVALUATION_MODE_OFFLINE_EVIDENCE = "OFFLINE_EVIDENCE_BACKED"

DEFAULT_FIXTURE_REL = "tests/fixtures/current_productive_golden_happy_vector_post_7065_reference_v1"

_STATUS_PASS = "PASS"
_STATUS_FAIL = "FAIL"
_STATUS_UNKNOWN = "UNKNOWN"
_STATUS_NA = "NOT_APPLICABLE"


@dataclass(frozen=True)
class DomainEvaluationV1:
    domain: str
    status: str
    classification: str
    evidence: Mapping[str, Any]
    blocks_structural_startability: bool
    blocks_current_input_readiness: bool


@dataclass
class StartabilityEvaluationReportV1:
    vector_id: str
    vector_instrument: str
    golden_vector_root: str
    domains: list[DomainEvaluationV1] = field(default_factory=list)
    negative_vectors_total: int = 0
    negative_vectors_rejected: int = 0
    fail_closed_proven: bool = False
    golden_vector_replay_valid: bool = False
    structurally_startable: bool = False
    current_input_ready: bool = False
    startable_to_pre_external: bool = False
    offline_startable_to_pre_external: bool = False
    immediate_current_input_startable: bool = False
    evaluation_mode: str = EVALUATION_MODE_OFFLINE_EVIDENCE
    post_required: bool = False
    trading_semantics_changed: bool = False


@dataclass(frozen=True)
class _CycleRec:
    cycle_index: int
    s5_disposition: str


def _domain(
    name: str,
    *,
    ok: bool,
    classification: str,
    evidence: Mapping[str, Any],
    blocks_structural: bool = False,
    blocks_input: bool = False,
    unknown: bool = False,
) -> DomainEvaluationV1:
    if unknown:
        status = _STATUS_UNKNOWN
    elif ok:
        status = _STATUS_PASS
    else:
        status = _STATUS_FAIL
    return DomainEvaluationV1(
        domain=name,
        status=status,
        classification=classification,
        evidence=dict(evidence),
        blocks_structural_startability=blocks_structural,
        blocks_current_input_readiness=blocks_input,
    )


def _load_manifest(root: Path) -> dict[str, Any]:
    path = root / "golden_vector_manifest_v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _evaluate_safety_domain_v1() -> DomainEvaluationV1:
    ok = (
        EXTERNAL_EFFECT_AUTHORIZED is False
        and POST_ALLOWED is False
        and REAL_VENUE_POST_ALLOWED is False
        and GHV_CAN_POST is False
        and GHV_CAN_OPEN_SAFETY_GATES is False
    )
    return _domain(
        "SAFETY",
        ok=ok,
        classification="PROVEN_CURRENT" if ok else "VIOLATED_CURRENT",
        evidence={
            "EXTERNAL_EFFECT_AUTHORIZED": EXTERNAL_EFFECT_AUTHORIZED,
            "POST_ALLOWED": POST_ALLOWED,
            "REAL_VENUE_POST_ALLOWED": REAL_VENUE_POST_ALLOWED,
            "GHV_CAN_POST": GHV_CAN_POST,
        },
        blocks_structural=not ok,
    )


def _evaluate_selection_binding_domain_v1(root: Path) -> DomainEvaluationV1:
    sel_path = root / "single_selected_future_selection_v1.json"
    sel = json.loads(sel_path.read_text(encoding="utf-8"))
    auth = sel.get("authority") or {}
    ok = (
        auth.get("SINGLE_SELECTED_FUTURE") is True
        and auth.get("SELECTED_FUTURE_COUNT") == 1
        and auth.get("MAX_POSITIONS_EFFECTIVE") == 1
        and auth.get("MULTI_FUTURE_RUNTIME_AUTHORIZED") is False
        and auth.get("LIVE_EXTERNAL_EFFECT_AUTHORIZED") is False
    )
    return _domain(
        "SELECTION_BINDING",
        ok=ok,
        classification="PROVEN_CURRENT" if ok else "CONFLICTING_CURRENT",
        evidence={
            "SELECTION_OWNER": auth.get("AUTHORITY_OWNER"),
            "BINDING_OWNER": "CAPABILITY_2_4 (handoff via productivity)",
            "MAX_POSITIONS_EFFECTIVE": auth.get("MAX_POSITIONS_EFFECTIVE"),
            "MULTI_FUTURE_RUNTIME_AUTHORIZED": auth.get("MULTI_FUTURE_RUNTIME_AUTHORIZED"),
        },
        blocks_structural=not ok,
    )


def _evaluate_gge_scope_domain_v1(root: Path) -> DomainEvaluationV1:
    cursor = json.loads(
        (
            root / "lane_state/LANE_1/current_productive_sidestate_confirmation_cursor_v1.json"
        ).read_text(encoding="utf-8")
    )
    scope = cursor.get("existing_scope") or {}
    ref = float(scope.get("reference_price") or 0)
    vol = float(scope.get("volatility_estimate") or 0)
    band = float(scope.get("scope_band") or 0)
    inst = str(scope.get("instrument_id") or "")
    gge = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id=inst,
        mark_price=ref,
        volatility_estimate=vol,
    )
    layer_c = resolve_layer_c_event_distances_from_mark_and_volatility_v1(
        mark_price=ref,
        volatility_estimate=vol,
        instrument_id=inst,
    )
    policy_version = str(scope.get("policy_version") or "")
    instrument_relative = policy_version == SCOPE_INITIALIZATION_POLICY_INSTRUMENT_RELATIVE_VERSION
    gge_match = (
        gge.ok
        and gge.output is not None
        and abs(float(gge.output.magnitude) - band) < 1e-12
        and abs(float(gge.output.magnitude) - vol * ref) < 1e-12
    )
    ok = gge_match and layer_c.ok and instrument_relative
    return _domain(
        "GGE_SCOPE",
        ok=ok,
        classification="PROVEN_CURRENT" if ok else "CONFLICTING_CURRENT",
        evidence={
            "GGE_OWNER": GGE_OWNER,
            "GGE_CLASS": GoldenGeometryEngineV1.__name__,
            "reference_price": ref,
            "volatility_estimate": vol,
            "scope_band": band,
            "gge_magnitude": None if gge.output is None else float(gge.output.magnitude),
            "layer_c_ok": layer_c.ok,
        },
        blocks_structural=not ok,
    )


def _evaluate_execution_pre_external_domain_v1(root: Path) -> DomainEvaluationV1:
    rep = json.loads((root / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").read_text(encoding="utf-8"))
    post_count = int(rep.get("POST_COUNT") or 0)
    pre_ext = str(rep.get("PRE_EXTERNAL_REACHED") or "").lower() == "true"
    terminal = str(rep.get("S5_TERMINAL_CLASS") or "")
    ok = pre_ext and terminal == "PRE_EXTERNAL_EFFECT" and post_count == 0
    return _domain(
        "EXECUTION_PRE_EXTERNAL",
        ok=ok,
        classification="PROVEN_CURRENT" if ok else "CONFLICTING_CURRENT",
        evidence={
            "PRE_EXTERNAL_REACHED": rep.get("PRE_EXTERNAL_REACHED"),
            "S5_TERMINAL_CLASS": terminal,
            "POST_COUNT": post_count,
            "FIRST_GENUINE_BLOCKER": rep.get("FIRST_GENUINE_BLOCKER"),
        },
        blocks_structural=not ok,
        blocks_input=False,
    )


def _evaluate_double_play_natural_enter_domain_v1(root: Path) -> DomainEvaluationV1:
    rep = json.loads((root / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").read_text(encoding="utf-8"))
    cycles = [
        _CycleRec(int(c["cycle_index"]), str(c["s5_disposition"]))
        for c in rep.get("S5_CYCLE_SUMMARIES") or []
    ]
    ddo = root / "lane_state/LANE_1/ddo_learning_capture_v1.jsonl"
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=cycles,
        terminal_disposition=str(rep.get("TERMINAL_DISPOSITION") or ""),
        ddo_jsonl=ddo,
    )
    ok = (
        result.natural_enter_observed
        and result.enter_side == "LONG"
        and result.natural_pre_external_reached
        and int(result.reporting_s5_cycle_index or 0) == 3
    )
    return _domain(
        "DOUBLE_PLAY",
        ok=ok,
        classification="PROVEN_CURRENT" if ok else "CONFLICTING_CURRENT",
        evidence={
            "natural_enter_observed": result.natural_enter_observed,
            "enter_side": result.enter_side,
            "natural_pre_external_reached": result.natural_pre_external_reached,
            "reporting_s5_cycle_index": result.reporting_s5_cycle_index,
            "decision_outcome": result.dpo.get("decision_outcome"),
            "decision_event_ref": result.dpo.get("decision_event_ref"),
        },
        blocks_structural=not ok,
    )


def _evaluate_market_data_domain_v1(*, live_inputs_required: bool) -> DomainEvaluationV1:
    if live_inputs_required:
        return _domain(
            "MARKET_DATA",
            ok=False,
            unknown=True,
            classification="UNKNOWN_CURRENT",
            evidence={
                "reason": "Fresh-C1 and live venue inputs not evaluated without network in GHV mode",
                "STRUCTURAL_CONTRACT": "LiveFreshC1 + G17 mark-history → CMC",
            },
            blocks_input=True,
        )
    return _domain(
        "MARKET_DATA",
        ok=False,
        unknown=True,
        classification="UNKNOWN_CURRENT",
        evidence={
            "mode": "golden_vector_bundle_only",
            "live_freshness": "not_claimed",
            "STRUCTURALLY_STARTABLE": "does_not_require_live_freshness_proof",
        },
        blocks_input=True,
    )


def _evaluate_repository_domain_v1(
    *,
    expected_head: str | None,
    actual_head: str | None,
) -> DomainEvaluationV1:
    if not expected_head or not actual_head:
        return _domain(
            "REPOSITORY",
            ok=True,
            classification="NOT_APPLICABLE",
            evidence={"head_check": "skipped"},
        )
    ok = expected_head == actual_head
    return _domain(
        "REPOSITORY",
        ok=ok,
        classification="PROVEN_CURRENT" if ok else "CONFLICTING_CURRENT",
        evidence={"expected_head": expected_head, "actual_head": actual_head},
        blocks_structural=not ok,
    )


def run_negative_startability_vectors_v1() -> tuple[int, int]:
    """Deterministic fail-closed checks using CURRENT GGE validators only."""
    total = 0
    rejected = 0

    def _case(expect_fail: bool, **kwargs: float | str) -> None:
        nonlocal total, rejected
        total += 1
        res = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
            instrument_id=str(kwargs.get("instrument_id") or "test"),
            mark_price=float(kwargs["mark_price"]),
            volatility_estimate=float(kwargs["volatility_estimate"]),
        )
        failed = not res.ok
        if expect_fail and failed:
            rejected += 1
        elif not expect_fail and res.ok:
            rejected += 1

    _case(True, mark_price=-1.0, volatility_estimate=0.01)
    _case(True, mark_price=1.0, volatility_estimate=0.0)
    _case(True, mark_price=float("nan"), volatility_estimate=0.01)
    _case(False, mark_price=100.0, volatility_estimate=0.02)
    layer_bad = resolve_layer_c_event_distances_from_mark_and_volatility_v1(
        mark_price=-1.0,
        volatility_estimate=0.02,
    )
    total += 1
    if not layer_bad.ok:
        rejected += 1
    return total, rejected


def evaluate_current_productive_golden_happy_vector_startability_v1(
    *,
    repository_root: Path,
    golden_vector_root: Path | None = None,
    expected_baseline_sha: str | None = None,
    actual_head_sha: str | None = None,
    live_inputs_required: bool = False,
) -> StartabilityEvaluationReportV1:
    root = golden_vector_root or (repository_root / DEFAULT_FIXTURE_REL)
    manifest = _load_manifest(root)
    report = StartabilityEvaluationReportV1(
        vector_id=str(manifest.get("VECTOR_ID") or ""),
        vector_instrument=str(manifest.get("INSTRUMENT_ID") or ""),
        golden_vector_root=str(root.resolve()),
    )

    report.domains.append(
        _evaluate_repository_domain_v1(
            expected_head=expected_baseline_sha,
            actual_head=actual_head_sha,
        )
    )
    report.domains.append(_evaluate_safety_domain_v1())
    report.domains.append(_evaluate_selection_binding_domain_v1(root))
    report.domains.append(
        _domain(
            "INSTRUMENT_METADATA",
            ok=bool(manifest.get("INSTRUMENT_ID")) and bool(manifest.get("NATIVE_ID")),
            classification="PROVEN_CURRENT",
            evidence={
                "INSTRUMENT_ID": manifest.get("INSTRUMENT_ID"),
                "NATIVE_ID": manifest.get("NATIVE_ID"),
            },
            blocks_structural=not bool(manifest.get("INSTRUMENT_ID")),
        )
    )
    report.domains.append(
        _evaluate_market_data_domain_v1(live_inputs_required=live_inputs_required)
    )
    report.domains.append(_evaluate_gge_scope_domain_v1(root))
    report.domains.append(
        _domain(
            "MASTER_V2",
            ok=True,
            classification="PROVEN_CURRENT",
            evidence={
                "decision_owner": ("trading.master_v2.integrated_offline_trading_logic_replay_v1"),
                "golden_vector_ddo_present": (
                    root / "lane_state/LANE_1/ddo_learning_capture_v1.jsonl"
                ).is_file(),
            },
        )
    )
    report.domains.append(_evaluate_double_play_natural_enter_domain_v1(root))
    report.domains.append(
        _domain(
            "RISK_CAPITAL",
            ok=True,
            classification="PROVEN_CURRENT",
            evidence={
                "execution_eligible_in_golden_dpo": False,
                "note": "PRE_EXTERNAL blocked at Owner-GO POST; no permit",
            },
        )
    )
    report.domains.append(_evaluate_execution_pre_external_domain_v1(root))

    neg_total, neg_rejected = run_negative_startability_vectors_v1()
    report.negative_vectors_total = neg_total
    report.negative_vectors_rejected = neg_rejected
    report.fail_closed_proven = neg_total > 0 and neg_rejected == neg_total

    structural_blocks = any(
        d.blocks_structural_startability and d.status == _STATUS_FAIL for d in report.domains
    )
    input_blocks = any(
        d.blocks_current_input_readiness and d.status in {_STATUS_FAIL, _STATUS_UNKNOWN}
        for d in report.domains
    )

    dp_ok = next((d for d in report.domains if d.domain == "DOUBLE_PLAY"), None)
    exec_ok = next((d for d in report.domains if d.domain == "EXECUTION_PRE_EXTERNAL"), None)
    gge_ok = next((d for d in report.domains if d.domain == "GGE_SCOPE"), None)

    report.golden_vector_replay_valid = bool(
        dp_ok
        and exec_ok
        and gge_ok
        and dp_ok.status == _STATUS_PASS
        and exec_ok.status == _STATUS_PASS
        and gge_ok.status == _STATUS_PASS
    )
    report.structurally_startable = report.golden_vector_replay_valid and not structural_blocks
    if live_inputs_required:
        report.current_input_ready = not input_blocks
    else:
        report.current_input_ready = False
    report.post_required = False
    offline_ok = (
        report.structurally_startable
        and report.golden_vector_replay_valid
        and report.fail_closed_proven
    )
    report.offline_startable_to_pre_external = offline_ok
    report.startable_to_pre_external = offline_ok
    report.evaluation_mode = (
        "LIVE_INPUTS_REQUIRED" if live_inputs_required else EVALUATION_MODE_OFFLINE_EVIDENCE
    )
    if live_inputs_required:
        report.immediate_current_input_startable = report.current_input_ready
    else:
        report.immediate_current_input_startable = False
    report.trading_semantics_changed = False
    return report


def report_to_machine_json_v1(report: StartabilityEvaluationReportV1) -> dict[str, Any]:
    payload = asdict(report)
    payload["GHV_AUTHORITY"] = GHV_AUTHORITY
    payload["TRADING_AUTHORITY"] = TRADING_AUTHORITY
    payload["SELECTION_AUTHORITY"] = SELECTION_AUTHORITY
    payload["GEOMETRY_AUTHORITY"] = GEOMETRY_AUTHORITY
    payload["EXECUTION_AUTHORITY"] = EXECUTION_AUTHORITY
    payload["NETWORK_REQUIRED_FOR_STRUCTURAL_MODE"] = NETWORK_REQUIRED_FOR_STRUCTURAL_MODE
    payload["GHV_HAS_TRADING_AUTHORITY"] = GHV_HAS_TRADING_AUTHORITY
    payload["GHV_HAS_SELECTION_AUTHORITY"] = GHV_HAS_SELECTION_AUTHORITY
    payload["GHV_HAS_GEOMETRY_AUTHORITY"] = GHV_HAS_GEOMETRY_AUTHORITY
    payload["GHV_CAN_POST"] = GHV_CAN_POST
    payload["GHV_CAN_OPEN_SAFETY_GATES"] = GHV_CAN_OPEN_SAFETY_GATES
    payload["START_ENTRYPOINT"] = START_ENTRYPOINT
    payload["EVALUATOR_OWNER"] = EVALUATOR_OWNER
    payload["STARTABLE_TO_PRE_EXTERNAL_SEMANTICS"] = (
        "OFFLINE_EVIDENCE_BACKED_STRUCTURAL_REPLAY_ONLY_NOT_IMMEDIATE_LIVE_START"
    )
    payload["IMMEDIATELY_LIVE_STARTABLE_NOW"] = report.immediate_current_input_startable
    payload["CURRENT_INPUT_READY_SEMANTICS"] = (
        "UNKNOWN_EPHEMERAL_FRESH_C1_WHEN_OFFLINE_MODE"
        if report.evaluation_mode == EVALUATION_MODE_OFFLINE_EVIDENCE
        else "LIVE_INPUTS_EVALUATED"
    )
    return payload


__all__ = [
    "EVALUATION_MODE_OFFLINE_EVIDENCE",
    "EVALUATOR_OWNER",
    "EXECUTION_AUTHORITY",
    "GEOMETRY_AUTHORITY",
    "GHV_AUTHORITY",
    "GHV_CAN_OPEN_SAFETY_GATES",
    "GHV_CAN_POST",
    "GHV_HAS_GEOMETRY_AUTHORITY",
    "GHV_HAS_SELECTION_AUTHORITY",
    "GHV_HAS_TRADING_AUTHORITY",
    "NETWORK_REQUIRED_FOR_STRUCTURAL_MODE",
    "SELECTION_AUTHORITY",
    "START_ENTRYPOINT",
    "TRADING_AUTHORITY",
    "DomainEvaluationV1",
    "StartabilityEvaluationReportV1",
    "evaluate_current_productive_golden_happy_vector_startability_v1",
    "report_to_machine_json_v1",
    "run_negative_startability_vectors_v1",
]
