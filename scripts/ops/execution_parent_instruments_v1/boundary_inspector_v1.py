"""Read-only execution boundary inspector. AUTHORITY=NONE.

Observes caller, permit, durable-consume, submission, transport, and ack
surfaces that the three existing instruments do not take as inputs.
Impact uses the existing propagate_change_impact_v1 path. Static source
evidence is never stored as runtime proof.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.ops.execution_parent_disclosure_v1.constants_v1 import (
    ACTIVATION,
    AUTHORITY,
    DOUBLE_PLAY_FULL_OWNER_LOCK,
)
from scripts.ops.execution_parent_instruments_v1.inventory_v1 import (
    CALL_EDGES,
    FORWARD_ORIGIN,
    MISSION_END,
    OBSERVED_SUBJECTS,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.impact_v1 import (
    propagate_change_impact_v1,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.traversal_v1 import (
    traverse_forensic_graph_v1,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DECISION = FORWARD_ORIGIN
_SEND = MISSION_END
_REPLAY = "execution.boundary.trading_replay"
_ONE_SHOT = "execution.submission.one_shot_join"
_FORBIDDEN_POST_MARKER = "REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE"
_SEND_SYMBOL = "attempt_envelope_bound_external_effect_send_v1"
_REFERENCE_ROLES = {
    _DECISION: "DECISION_CYCLE",
    _REPLAY: "TRADING_REPLAY",
    _SEND: "SUBMISSION_SEAM",
    _ONE_SHOT: "ONE_SHOT_JOIN",
}
_CYCLE_SYMBOL = "run_current_productive_master_v2_runtime_cycle_v1"

_CALLERS: tuple[dict[str, Any], ...] = (
    {
        "subject_id": "execution.caller.persisted_cursor",
        "symbol": (
            "execute_current_productive_fresh_runtime_from_persisted_cursor_"
            "to_pre_external_effect_applicability_v1"
        ),
        "path": (
            "src/ops/governed_productive_account_equity_authority_producer_v1/"
            "current_productive_fresh_runtime_from_persisted_cursor_to_pre_external_"
            "effect_applicability_v1.py"
        ),
        "start_line": 589,
        "end_line": 1460,
        "source_sha256": "cd5354501023402275c04bd4611c8f469385f4e728857f95ad453ce76f2758b7",
        "call_line": 983,
        "probe_line": 1133,
        "cross_parent": "EQUITY_AUTHORITY_PRODUCER",
    },
    {
        "subject_id": "execution.caller.envelope_post_boundary",
        "symbol": "execute_current_productive_fresh_runtime_cycle_to_exact_envelope_bound_v1",
        "path": (
            "src/ops/governed_productive_account_equity_authority_producer_v1/"
            "current_productive_fresh_runtime_cycle_to_exact_envelope_bound_single_use_"
            "post_boundary_v1.py"
        ),
        "start_line": 204,
        "end_line": 790,
        "source_sha256": "1f644987befa4cfdfe83d2031582c97fd17337e661abc577f9abeb5472374a81",
        "call_line": 482,
        "probe_line": 577,
        "cross_parent": "EQUITY_AUTHORITY_PRODUCER",
    },
    {
        "subject_id": "execution.caller.non_executable_v1",
        "symbol": "execute_current_productive_fresh_runtime_cycle_after_non_executable_decision_v1",
        "path": (
            "src/ops/governed_productive_account_equity_authority_producer_v1/"
            "current_productive_fresh_runtime_cycle_after_non_executable_decision_v1.py"
        ),
        "start_line": 361,
        "end_line": 1048,
        "source_sha256": "c5177fb81730c85fd237b2446cde9de1081c1ddf517ac1165a02813e1368dad2",
        "call_line": 652,
        "probe_line": 763,
        "cross_parent": "EQUITY_AUTHORITY_PRODUCER",
    },
    {
        "subject_id": "execution.caller.non_executable_v2",
        "symbol": "execute_current_productive_fresh_runtime_cycle_after_non_executable_decision_v2",
        "path": (
            "src/ops/governed_productive_account_equity_authority_producer_v1/"
            "current_productive_fresh_runtime_cycle_after_non_executable_decision_v2.py"
        ),
        "start_line": 364,
        "end_line": 1053,
        "source_sha256": "a0a336ea5c92d78c6def7fef9261dd5031eb2f166fecaeeb1125deff3d740306",
        "call_line": 657,
        "probe_line": 768,
        "cross_parent": "EQUITY_AUTHORITY_PRODUCER",
    },
    {
        "subject_id": "execution.caller.non_executable_v3",
        "symbol": "execute_current_productive_fresh_runtime_cycle_after_non_executable_decision_v3",
        "path": (
            "src/ops/governed_productive_account_equity_authority_producer_v1/"
            "current_productive_fresh_runtime_cycle_after_non_executable_decision_v3.py"
        ),
        "start_line": 375,
        "end_line": 1089,
        "source_sha256": "689966c4383333adccb3e9f9c82274b6230100d65efa564255b2e3b135760544",
        "call_line": 680,
        "probe_line": 804,
        "cross_parent": "EQUITY_AUTHORITY_PRODUCER",
    },
    {
        "subject_id": "execution.caller.flatten_occupancy",
        "symbol": (
            "execute_current_productive_fresh_runtime_cycle_after_flatten_occupancy_absent_v1"
        ),
        "path": (
            "src/ops/governed_productive_account_equity_authority_producer_v1/"
            "current_productive_fresh_runtime_cycle_after_flatten_occupancy_absent_v1.py"
        ),
        "start_line": 361,
        "end_line": 1046,
        "source_sha256": "75c92f5563e9566a733fe57a5b1c8ee2375e2f511807804226b82e2bac60c55f",
        "call_line": 652,
        "probe_line": 763,
        "cross_parent": "EQUITY_AUTHORITY_PRODUCER",
    },
    {
        "subject_id": "execution.caller.layered_long",
        "symbol": "_offline_mv2_cycle_v1",
        "path": (
            "src/ops/full_core_live_path_composition_root_v1/"
            "current_productive_layered_long_mv2_state_advance_for_pre_external_v1.py"
        ),
        "start_line": 96,
        "end_line": 127,
        "source_sha256": "f74789b01a3b808e97e57f0022ac6c70b70b2dc5f54728a699948b1e2deb177a",
        "call_line": 108,
        "probe_line": None,
        "cross_parent": "COMPOSITION_ROOT",
    },
    {
        "subject_id": "execution.caller.n5_invoke",
        "symbol": "invoke_occupied_lane_mv2_dp_decision_state_consumer_v1",
        "path": (
            "src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_"
            "addressing_join_v1/addressing_join_v1.py"
        ),
        "start_line": 418,
        "end_line": 504,
        "source_sha256": "697f79dabdcc174adb43745200512e33ee819c97085b7d5163812b4bdb17e1bc",
        "call_line": 468,
        "probe_line": None,
        "cross_parent": "MF_N5",
    },
    {
        "subject_id": "execution.caller.n5_carry",
        "symbol": "carry_occupied_lane_mv2_dp_decision_state_in_memory_v1",
        "path": (
            "src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_"
            "addressing_join_v1/addressing_join_v1.py"
        ),
        "start_line": 507,
        "end_line": 618,
        "source_sha256": "254a7528b658b9e312365afea08abc03c8f75b0f44deefbe84dc099fb078ff01",
        "call_line": 582,
        "probe_line": None,
        "cross_parent": "MF_N5",
    },
    {
        "subject_id": "execution.caller.n5_restore",
        "symbol": "restore_occupied_lane_mv2_dp_decision_state_cursor_v1",
        "path": (
            "src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_"
            "addressing_join_v1/addressing_join_v1.py"
        ),
        "start_line": 695,
        "end_line": 789,
        "source_sha256": "0efe91629bd9e22649f9c1c211c9d6599dade2852c02c6f7919e9878cb6ecaf2",
        "call_line": 753,
        "probe_line": None,
        "cross_parent": "MF_N5",
    },
)

_SEPARATION: tuple[dict[str, Any], ...] = (
    {
        "subject_id": "execution.permit.issue",
        "symbol": "issue_external_effect_permit_v1",
        "path": "src/ops/full_core_live_path_composition_root_v1/external_effect_permit_v1.py",
        "start_line": 182,
        "end_line": 254,
        "source_sha256": "c51266866c3fa7582357e3c9d0ef4eba91701d5150e4716e34999899c3240b48",
        "role": "PERMIT",
    },
    {
        "subject_id": "execution.persistence.durable_consume",
        "symbol": "persist_external_effect_durable_consume_v1",
        "path": (
            "src/ops/full_core_live_path_composition_root_v1/"
            "external_effect_permit_durable_consume_v1.py"
        ),
        "start_line": 133,
        "end_line": 169,
        "source_sha256": "e7e7689fa763b2c3b623109b9a0daa188236acf0647c5a4cc6c1f0c53236c253",
        "role": "DURABLE_CONSUME",
    },
    {
        "subject_id": "execution.ack.lifecycle_join",
        "symbol": "join_full_core_post_result_to_lifecycle_v1",
        "path": (
            "src/ops/full_core_live_path_composition_root_v1/"
            "full_core_post_response_to_ack_mapper_v1.py"
        ),
        "start_line": 218,
        "end_line": 280,
        "source_sha256": "4eabbdd67066db89cc66f4caa338b978efea9c5747aedf09415aa3abd15afd25",
        "role": "ACK",
    },
    {
        "subject_id": "execution.transport.one_shot_http",
        "symbol": "_DurableConsumeThenK1HttpTransportV1",
        "path": (
            "src/ops/full_core_live_path_composition_root_v1/"
            "current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_"
            "and_post_join_v1.py"
        ),
        "start_line": 334,
        "end_line": 433,
        "source_sha256": "6a82f3eedd626304e97066a7b7a09d1622d841eba2aba6f899daa7638369942e",
        "role": "TRANSPORT",
    },
)

_INTERNAL_EDGES: tuple[dict[str, Any], ...] = (
    {
        "edge_id": "execution.submission.one_shot_join.CALLS.permit",
        "source_subject_id": _ONE_SHOT,
        "target_subject_id": "execution.permit.issue",
        "callee_symbol": "issue_external_effect_permit_v1",
        "evidence_line": 520,
        "role": "PERMIT",
    },
    {
        "edge_id": "execution.submission.one_shot_join.CALLS.send_seam",
        "source_subject_id": _ONE_SHOT,
        "target_subject_id": _SEND,
        "callee_symbol": _SEND_SYMBOL,
        "evidence_line": 570,
        "role": "SUBMISSION_SEAM",
    },
    {
        "edge_id": "execution.submission.send_seam.CALLS.durable_consume",
        "source_subject_id": _SEND,
        "target_subject_id": "execution.persistence.durable_consume",
        "callee_symbol": "persist_external_effect_durable_consume_v1",
        "evidence_line": 163,
        "role": "DURABLE_CONSUME",
    },
    {
        "edge_id": "execution.submission.send_seam.CALLS.ack",
        "source_subject_id": _SEND,
        "target_subject_id": "execution.ack.lifecycle_join",
        "callee_symbol": "join_full_core_post_result_to_lifecycle_v1",
        "evidence_line": 212,
        "role": "ACK",
    },
    {
        "edge_id": "execution.submission.send_seam.CALLS.transport",
        "source_subject_id": _SEND,
        "target_subject_id": "execution.transport.one_shot_http",
        "callee_symbol": "post_trade_order",
        "evidence_line": 179,
        "role": "SUBMISSION_TRANSPORT",
    },
)

_UNKNOWN_EDGES: tuple[dict[str, str], ...] = (
    {
        "edge_id": "execution.decision.runtime_cycle.edge.submission.unknown",
        "reason": "no proven call from the decision cycle to submission",
    },
    {
        "edge_id": "execution.decision.runtime_cycle.edge.offline_path.unknown",
        "reason": "no src caller links the decision cycle to the offline pre-external path",
    },
    {
        "edge_id": "execution.pre_external.fresh_runtime_applicability.edge.submission.unknown",
        "reason": "pre-external applicability does not call the submission seam",
    },
    {
        "edge_id": "execution.caller.productive_selection.unknown",
        "reason": "no evidence selects one additional caller as the productive entry",
    },
)


def run_execution_boundary_inspector_v1(
    *,
    current_commit_sha: str,
    current_tree_sha: str,
    repo_root: Path | None = None,
    changed_paths: Sequence[str] = (),
    fixture_blobs: Mapping[str, str | None] | None = None,
) -> dict[str, Any]:
    """Validate bound windows and hand changed subjects to the impact path."""
    root = _REPO_ROOT if repo_root is None else repo_root
    pin_reason = _pin_reason(root, current_commit_sha, current_tree_sha)
    if pin_reason is not None:
        return _fail(pin_reason)
    subjects = _subject_records()
    blobs, blob_reason = _load_blobs(root, current_tree_sha, subjects, fixture_blobs)
    if blob_reason is not None:
        return _fail(blob_reason)
    evidence_reasons = _evidence_reasons(subjects, blobs)
    edges, probes, absent, edge_reasons = _relations(subjects, blobs)
    reasons = [*evidence_reasons, *edge_reasons]
    changed = _changed_subjects(subjects, changed_paths, evidence_reasons)
    impact = _impacts(subjects, edges, changed)
    walks = _walks(edges)
    status = "FAIL_CLOSED" if reasons else "ACCEPTED"
    return _envelope(
        status,
        reasons=reasons,
        baseline_commit=current_commit_sha,
        baseline_tree=current_tree_sha,
        subjects=subjects,
        edges=edges,
        probes=probes,
        absent_in_inspected_scope=absent,
        unknown_edges=[_unknown(edge) for edge in _UNKNOWN_EDGES],
        changed_subject_ids=sorted(changed),
        unbound_changed_paths=_unbound(subjects, changed_paths),
        impact=impact,
        **walks,
    )


def _subject_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in _CALLERS:
        body = dict(record)
        body["role"] = "ADDITIONAL_CALLER"
        body["ownership"] = "UNKNOWN"
        body["membership_ratified"] = False
        records.append(body)
    for record in _SEPARATION:
        body = dict(record)
        body["ownership"] = "UNKNOWN"
        body["membership_ratified"] = False
        body["cross_parent"] = "COMPOSITION_ROOT"
        records.append(body)
    by_id = {str(record["subject_id"]): record for record in OBSERVED_SUBJECTS}
    for subject_id, role in _REFERENCE_ROLES.items():
        source = by_id[subject_id]
        records.append(
            {
                "subject_id": subject_id,
                "symbol": source["symbol"],
                "path": source["path"],
                "start_line": source["start_line"],
                "end_line": source["end_line"],
                "source_sha256": source["source_sha256"],
                "role": role,
                "ownership": "UNKNOWN",
                "membership_ratified": False,
                "cross_parent": "TRADING_BOUNDARY" if subject_id == _REPLAY else "REFERENCE",
            }
        )
    return records


def _pin_reason(root: Path, commit_sha: str, tree_sha: str) -> str | None:
    actual = _git(root, "rev-parse", f"{commit_sha}^{{tree}}")
    if actual is None:
        return "missing_pin_evidence"
    if actual.strip() != tree_sha:
        return "stale_commit_tree"
    return None


def _load_blobs(
    root: Path,
    tree_sha: str,
    subjects: Sequence[Mapping[str, Any]],
    fixture_blobs: Mapping[str, str | None] | None,
) -> tuple[dict[str, list[str]], str | None]:
    blobs: dict[str, list[str]] = {}
    for subject in subjects:
        path = str(subject["path"])
        if path in blobs:
            continue
        if fixture_blobs is not None and path in fixture_blobs:
            fixture = fixture_blobs[path]
            if fixture is None:
                return {}, f"missing_evidence:{path}"
            blobs[path] = fixture.splitlines()
            continue
        blob = _git(root, "show", f"{tree_sha}:{path}")
        if blob is None:
            return {}, f"missing_evidence:{path}"
        blobs[path] = blob.splitlines()
    return blobs, None


def _evidence_reasons(
    subjects: Sequence[Mapping[str, Any]],
    blobs: Mapping[str, list[str]],
) -> list[str]:
    reasons: list[str] = []
    for subject in subjects:
        lines = blobs[str(subject["path"])]
        start = int(subject["start_line"])
        end = int(subject["end_line"])
        subject_id = str(subject["subject_id"])
        if start < 1 or end > len(lines) or start > end:
            reasons.append(f"subject_lines:{subject_id}")
            continue
        window = lines[start - 1 : end]
        digest = hashlib.sha256("\n".join(window).encode()).hexdigest()
        if digest != subject["source_sha256"]:
            reasons.append(f"subject_hash_mismatch:{subject_id}")
        if _symbol_in(window, str(subject["symbol"])) is False:
            reasons.append(f"subject_symbol_absent:{subject_id}")
    return reasons


def _relations(
    subjects: Sequence[Mapping[str, Any]],
    blobs: Mapping[str, list[str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    by_id = {str(subject["subject_id"]): subject for subject in subjects}
    edges: list[dict[str, Any]] = []
    probes: list[dict[str, Any]] = []
    absent: list[dict[str, Any]] = []
    reasons: list[str] = []
    for caller in _CALLERS:
        source = by_id[str(caller["subject_id"])]
        lines = blobs[str(source["path"])]
        edge, reason = _call_edge(
            edge_id=f"{caller['subject_id']}.CALLS.decision_cycle",
            source=source,
            target_id=_DECISION,
            callee=_CYCLE_SYMBOL,
            line_no=int(caller["call_line"]),
            lines=lines,
            role="ADDITIONAL_CALLER",
        )
        if reason is not None:
            reasons.append(reason)
        elif edge is not None:
            edges.append(edge)
        window = _window(lines, source)
        if _symbol_in(window, _SEND_SYMBOL):
            reasons.append(f"absence_contradicted:{caller['subject_id']}")
        else:
            absent.append(
                {
                    "subject_id": caller["subject_id"],
                    "absent_symbol": _SEND_SYMBOL,
                    "proof_status": "ABSENT_IN_INSPECTED_SCOPE",
                    "runtime_status": "UNKNOWN",
                }
            )
        probe_line = caller["probe_line"]
        if probe_line is None:
            continue
        if _FORBIDDEN_POST_MARKER not in "\n".join(window):
            reasons.append(f"probe_token_absent:{caller['subject_id']}")
            continue
        if _symbol_in([lines[int(probe_line) - 1]], "post_trade_order") is False:
            reasons.append(f"probe_line_absent:{caller['subject_id']}")
            continue
        probes.append(
            {
                "subject_id": caller["subject_id"],
                "evidence_line": int(probe_line),
                "evidence_path": source["path"],
                "role": "MUST_NOT_POST_PROBE",
                "target_subject_id": None,
                "submission_edge": False,
                "proof_status": "STATIC_SOURCE_PROVEN",
                "runtime_status": "UNKNOWN",
            }
        )
    for spec in _INTERNAL_EDGES:
        source = by_id[str(spec["source_subject_id"])]
        edge, reason = _call_edge(
            edge_id=str(spec["edge_id"]),
            source=source,
            target_id=str(spec["target_subject_id"]),
            callee=str(spec["callee_symbol"]),
            line_no=int(spec["evidence_line"]),
            lines=blobs[str(source["path"])],
            role=str(spec["role"]),
        )
        if reason is not None:
            reasons.append(reason)
        elif edge is not None:
            edges.append(edge)
    replay = next(edge for edge in CALL_EDGES if edge["target_subject_id"] == _REPLAY)
    source = by_id[_DECISION]
    edge, reason = _call_edge(
        edge_id=str(replay["edge_id"]),
        source=source,
        target_id=_REPLAY,
        callee=str(replay["callee_symbol"]),
        line_no=int(replay["evidence_line"]),
        lines=blobs[str(source["path"])],
        role="TRADING_REPLAY",
    )
    if reason is not None:
        reasons.append(reason)
    elif edge is not None:
        edges.append(edge)
    return edges, probes, absent, reasons


def _call_edge(
    *,
    edge_id: str,
    source: Mapping[str, Any],
    target_id: str,
    callee: str,
    line_no: int,
    lines: list[str],
    role: str,
) -> tuple[dict[str, Any] | None, str | None]:
    start = int(source["start_line"])
    end = int(source["end_line"])
    if not start <= line_no <= end:
        return None, f"edge_line_outside_source:{edge_id}"
    if line_no > len(lines) or _symbol_in([lines[line_no - 1]], callee) is False:
        return None, f"edge_call_absent:{edge_id}"
    return (
        {
            "edge_id": edge_id,
            "source_native_id": str(source["subject_id"]),
            "target_native_id": target_id,
            "role": role,
            "evidence_line": line_no,
            "evidence_path": str(source["path"]),
            "causal_traversal_eligible": True,
            "typed_edge": {"edge_type": "CALLS", "trading_authority_implied": False},
            "proof_status": "STATIC_SOURCE_PROVEN",
            "runtime_status": "UNKNOWN",
            "submission_edge": target_id == _SEND,
        },
        None,
    )


def _changed_subjects(
    subjects: Sequence[Mapping[str, Any]],
    changed_paths: Sequence[str],
    evidence_reasons: Sequence[str],
) -> set[str]:
    by_path: dict[str, list[str]] = {}
    for subject in subjects:
        by_path.setdefault(str(subject["path"]), []).append(str(subject["subject_id"]))
    changed: set[str] = set()
    for path in changed_paths:
        changed.update(by_path.get(path, []))
    for reason in evidence_reasons:
        if reason.startswith("subject_hash_mismatch:"):
            changed.add(reason.split(":", 1)[1])
    return changed


def _unbound(subjects: Sequence[Mapping[str, Any]], changed_paths: Sequence[str]) -> list[str]:
    bound = {str(subject["path"]) for subject in subjects}
    return sorted(path for path in changed_paths if path not in bound)


def _impacts(
    subjects: Sequence[Mapping[str, Any]],
    edges: Sequence[Mapping[str, Any]],
    changed: set[str],
) -> dict[str, Any]:
    if not changed:
        return {
            "binding": "propagate_change_impact_v1",
            "propagation_status": "NOT_RUN",
            "impacted_native_ids": [],
            "coverage_gaps": [],
            "runtime_proven": False,
            "safety_classification": "UNKNOWN",
        }
    nodes = [{"source_native_id": str(subject["subject_id"])} for subject in subjects]
    census = [
        {"object_id": str(subject["subject_id"]), "reachability": "UNKNOWN"} for subject in subjects
    ]
    causal = [dict(edge) for edge in edges if edge.get("causal_traversal_eligible") is True]
    impacted: set[str] = set()
    gaps: list[str] = []
    statuses: list[str] = []
    for seed in sorted(changed):
        propagated = propagate_change_impact_v1(
            nodes=nodes,
            edges=causal,
            census_objects=census,
            seed_native_id=seed,
            causal_only=True,
            max_depth=2,
        )
        impacted.update(propagated.impacted_native_ids)
        gaps.extend(propagated.coverage_gaps)
        statuses.append(propagated.propagation_status)
    status = "UNKNOWN" if any(item == "UNKNOWN" for item in statuses) else statuses[0]
    return {
        "binding": "propagate_change_impact_v1",
        "propagation_status": status,
        "impacted_native_ids": sorted(impacted),
        "coverage_gaps": sorted(set(gaps)),
        "runtime_proven": False,
        "safety_classification": "UNKNOWN",
    }


def _walks(edges: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    nodes = [{"source_native_id": edge["source_native_id"]} for edge in edges]
    nodes.extend({"source_native_id": edge["target_native_id"]} for edge in edges)
    causal = [dict(edge) for edge in edges]
    forward = traverse_forensic_graph_v1(
        nodes=nodes,
        edges=causal,
        origin_native_id="execution.caller.envelope_post_boundary",
        direction="FORWARD",
        causal_only=True,
        max_depth=1,
    )
    reverse = traverse_forensic_graph_v1(
        nodes=nodes,
        edges=causal,
        origin_native_id=_DECISION,
        direction="REVERSE",
        causal_only=True,
        max_depth=1,
    )
    transitive = traverse_forensic_graph_v1(
        nodes=nodes,
        edges=causal,
        origin_native_id="execution.caller.envelope_post_boundary",
        direction="FORWARD",
        causal_only=True,
        max_depth=2,
    )
    return {
        "forward_from_envelope_post_boundary": list(forward.reachable_native_ids),
        "reverse_from_decision_cycle": list(reverse.reachable_native_ids),
        "transitive_from_envelope_post_boundary": list(transitive.reachable_native_ids),
    }


def _unknown(edge: Mapping[str, str]) -> dict[str, str]:
    return {
        "edge_id": edge["edge_id"],
        "reason": edge["reason"],
        "proof_status": "UNKNOWN",
        "runtime_status": "UNKNOWN",
        "ownership": "UNKNOWN",
    }


def _window(lines: list[str], subject: Mapping[str, Any]) -> list[str]:
    start = int(subject["start_line"])
    end = int(subject["end_line"])
    if start < 1 or end > len(lines) or start > end:
        return []
    return lines[start - 1 : end]


def _symbol_in(lines: Sequence[str], symbol: str) -> bool:
    pattern = re.compile(rf"\b{re.escape(symbol)}\b")
    return any(pattern.search(line) for line in lines)


def _git(root: Path, *args: str) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def _fail(reason: str) -> dict[str, Any]:
    return _envelope("FAIL_CLOSED", reasons=[reason], impact=_idle_impact())


def _idle_impact() -> dict[str, Any]:
    return {
        "binding": "propagate_change_impact_v1",
        "propagation_status": "NOT_RUN",
        "impacted_native_ids": [],
        "coverage_gaps": [],
        "runtime_proven": False,
        "safety_classification": "UNKNOWN",
    }


def _envelope(status: str, **extra: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "instrument_id": "PARENT_EXECUTION_BOUNDARY_INSPECTOR",
        "status": status,
        "authority": AUTHORITY,
        "activation": ACTIVATION,
        "membership_ratified": False,
        "guardian_ratified": False,
        "domain_bound": False,
        "operationally_ready": False,
        "causal_closure_proven": False,
        "current_runtime_proven": False,
        "current_validated": False,
        "post_allowed": False,
        "external_effect_authorized": False,
        "productive_activation": False,
        "double_play_full_owner_lock": DOUBLE_PLAY_FULL_OWNER_LOCK,
        "files_written": False,
        "repository_evidence_write": False,
        "safety_classification": "UNKNOWN",
        "decision_to_submission": "UNKNOWN",
        "productive_runtime_reachability": "UNKNOWN",
        "coverage": "PARTIAL",
        "trading_decision_semantics_delta": "ZERO",
        "reasons": [],
    }
    body.update(extra)
    return body
