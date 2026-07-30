"""Evidence stream writer for hardening v2 probes/sessions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (
    AI_LAYER_CAN_OVERRIDE_DECISIONS,
    AI_LAYER_NON_AUTHORITY,
    AI_LAYER_ROLE,
    CAPABILITY_ID,
    OWNER,
    PACKAGE_MARKER,
    REQUIRED_EVIDENCE_STREAMS,
    SCHEMA_VERSION,
    SESSION_RESTART_POLICY,
)


def _canonical(payload: Mapping[str, Any] | list[Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _append(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(_canonical(dict(payload)) + "\n")


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), sort_keys=True, indent=2) + "\n", encoding="utf-8")


def append_productive_cycle_evidence_streams_v2(
    *,
    append_event: Callable[[str, Mapping[str, Any]], None],
    session_id: str,
    cycle: Mapping[str, Any],
) -> None:
    """Append one productive bridge cycle into runbook-required evidence streams.

    Used by the productive wallclock session path so offline probes and wallclock
    sessions share the same stream schema and linkage fields.
    """
    pb = cycle.get("price_basis") or {}
    fr = cycle.get("feature_regime") or {}
    snap = cycle.get("portfolio_snapshot") or {}
    state = snap.get("state") or {}
    append_event(
        "feature_trace.jsonl",
        {
            "session_id": session_id,
            "cycle_id": cycle.get("cycle_id"),
            "decision_id": cycle.get("decision_id"),
            "feature_digest": cycle.get("feature_digest"),
            "feature_regime": fr,
            "ai_layer_non_authority": AI_LAYER_NON_AUTHORITY,
            "ai_layer_can_override_decisions": AI_LAYER_CAN_OVERRIDE_DECISIONS,
        },
    )
    append_event(
        "regime_trace.jsonl",
        {
            "session_id": session_id,
            "cycle_id": cycle.get("cycle_id"),
            "regime_id": fr.get("regime_id"),
            "regime_digest": cycle.get("regime_digest"),
            "default_regime_fallback_active": cycle.get("default_regime_fallback_active"),
        },
    )
    append_event(
        "risk_sizing_trace.jsonl",
        {
            "session_id": session_id,
            "cycle_id": cycle.get("cycle_id"),
            "decision_id": cycle.get("decision_id"),
            "risk_decision_id": cycle.get("risk_decision_id"),
            "risk_sizing_result": cycle.get("risk_sizing_result"),
            "safety_evaluation": cycle.get("safety_evaluation"),
        },
    )
    append_event(
        "order_intent_trace.jsonl",
        {
            "session_id": session_id,
            "cycle_id": cycle.get("cycle_id"),
            "decision_id": cycle.get("decision_id"),
            "risk_decision_id": cycle.get("risk_decision_id"),
            "intent_id": cycle.get("intent_id"),
            "intended_action": cycle.get("intended_action"),
            "decision_producer": (cycle.get("intended_action") or {}).get("decision_producer"),
            "ai_layer_non_authority": AI_LAYER_NON_AUTHORITY,
            "ai_layer_can_override_decisions": AI_LAYER_CAN_OVERRIDE_DECISIONS,
            "ai_layer_role": AI_LAYER_ROLE,
        },
    )
    append_event(
        "portfolio_snapshots.jsonl",
        {
            "session_id": session_id,
            "cycle_id": cycle.get("cycle_id"),
            "portfolio_state_before_hash": cycle.get("portfolio_state_before_hash"),
            "portfolio_state_after_hash": cycle.get("portfolio_state_after_hash"),
            "snapshot": snap,
        },
    )
    append_event(
        "equity_curve.jsonl",
        {
            "session_id": session_id,
            "cycle_id": cycle.get("cycle_id"),
            "equity": state.get("equity"),
            "peak_equity": state.get("peak_equity"),
            "drawdown": state.get("max_drawdown"),
            "exposure": (cycle.get("economic_metrics") or {}).get("exposure"),
        },
    )
    append_event(
        "runtime_events.jsonl",
        {
            "session_id": session_id,
            "cycle_id": cycle.get("cycle_id"),
            "event": "bridge_cycle_completed",
            "forced_wiring": cycle.get("forced_wiring"),
            "call_graph": cycle.get("call_graph"),
            "ai_layer_non_authority": AI_LAYER_NON_AUTHORITY,
            "price_basis_mid": pb.get("mid_price"),
            "market_data_reference": cycle.get("market_data_reference"),
        },
    )
    if (cycle.get("safety_evaluation") or {}).get("safety_result") == "BLOCKED":
        append_event(
            "killstate_events.jsonl",
            {
                "session_id": session_id,
                "cycle_id": cycle.get("cycle_id"),
                "trigger": (cycle.get("safety_evaluation") or {}).get("veto_reason"),
                "source": "bridge_safety_evaluation",
            },
        )
    fill = cycle.get("fill")
    if fill is not None:
        append_event("simulated_fill_trace.jsonl", dict(fill))


def persist_hardening_evidence_bundle_v2(
    *,
    evidence_root: Path,
    session_id: str,
    cycles: Sequence[Mapping[str, Any]],
    fill_ledger: Sequence[Mapping[str, Any]],
    portfolio_snapshot: Mapping[str, Any],
    economic_metrics: Mapping[str, Any],
    verification: Mapping[str, Any],
    authorization_status: str = "NOT_APPLICABLE",
    mode: str = "offline_probe",
    exclude_from_economic_metrics: bool = False,
) -> dict[str, Any]:
    root = Path(evidence_root)
    root.mkdir(parents=True, exist_ok=True)

    _write_json(
        root / "session_manifest.json",
        {
            "capability_id": CAPABILITY_ID,
            "package_marker": PACKAGE_MARKER,
            "schema_version": SCHEMA_VERSION,
            "owner": OWNER,
            "session_id": session_id,
            "mode": mode,
            "session_restart_policy": SESSION_RESTART_POLICY,
            "exclude_from_economic_metrics": exclude_from_economic_metrics,
            "config_digest": (cycles[-1].get("config_digest") if cycles else ""),
        },
    )
    _write_json(
        root / "authorization_consumption.json",
        {
            "status": authorization_status,
            "consumed": False,
            "productive_authorization": False,
            "mode": mode,
        },
    )

    for name in (
        "market_data_sequence.jsonl",
        "feature_trace.jsonl",
        "regime_trace.jsonl",
        "decision_trace.jsonl",
        "risk_sizing_trace.jsonl",
        "order_intent_trace.jsonl",
        "simulated_fill_trace.jsonl",
        "portfolio_snapshots.jsonl",
        "equity_curve.jsonl",
        "runtime_events.jsonl",
        "killstate_events.jsonl",
    ):
        (root / name).write_text("", encoding="utf-8")

    for cycle in cycles:
        pb = cycle.get("price_basis") or {}
        _append(
            root / "market_data_sequence.jsonl",
            {
                "session_id": session_id,
                "cycle_id": cycle.get("cycle_id"),
                "mid_price": pb.get("mid_price")
                or (cycle.get("feature_regime") or {}).get("mark_price"),
                "market_data_reference": cycle.get("market_data_reference"),
                "price_basis": pb,
            },
        )
        fr = cycle.get("feature_regime") or {}
        _append(
            root / "feature_trace.jsonl",
            {
                "session_id": session_id,
                "cycle_id": cycle.get("cycle_id"),
                "decision_id": cycle.get("decision_id"),
                "feature_digest": cycle.get("feature_digest"),
                "feature_regime": fr,
            },
        )
        _append(
            root / "regime_trace.jsonl",
            {
                "session_id": session_id,
                "cycle_id": cycle.get("cycle_id"),
                "regime_id": fr.get("regime_id"),
                "regime_digest": cycle.get("regime_digest"),
                "default_regime_fallback_active": cycle.get("default_regime_fallback_active"),
            },
        )
        _append(
            root / "decision_trace.jsonl",
            {
                "session_id": session_id,
                "cycle_id": cycle.get("cycle_id"),
                "decision_id": cycle.get("decision_id"),
                "decision_outcome": cycle.get("decision_outcome"),
                "decision_authority_owner": cycle.get("decision_authority_owner"),
                "feature_digest": cycle.get("feature_digest"),
                "regime_digest": cycle.get("regime_digest"),
                "intended_action": cycle.get("intended_action"),
            },
        )
        _append(
            root / "risk_sizing_trace.jsonl",
            {
                "session_id": session_id,
                "cycle_id": cycle.get("cycle_id"),
                "decision_id": cycle.get("decision_id"),
                "risk_decision_id": cycle.get("risk_decision_id"),
                "risk_sizing_result": cycle.get("risk_sizing_result"),
                "safety_evaluation": cycle.get("safety_evaluation"),
            },
        )
        _append(
            root / "order_intent_trace.jsonl",
            {
                "session_id": session_id,
                "cycle_id": cycle.get("cycle_id"),
                "decision_id": cycle.get("decision_id"),
                "risk_decision_id": cycle.get("risk_decision_id"),
                "intent_id": cycle.get("intent_id"),
                "intended_action": cycle.get("intended_action"),
            },
        )
        snap = cycle.get("portfolio_snapshot") or {}
        state = snap.get("state") or {}
        _append(
            root / "portfolio_snapshots.jsonl",
            {
                "session_id": session_id,
                "cycle_id": cycle.get("cycle_id"),
                "portfolio_state_before_hash": cycle.get("portfolio_state_before_hash"),
                "portfolio_state_after_hash": cycle.get("portfolio_state_after_hash"),
                "snapshot": snap,
            },
        )
        _append(
            root / "equity_curve.jsonl",
            {
                "session_id": session_id,
                "cycle_id": cycle.get("cycle_id"),
                "equity": state.get("equity"),
                "peak_equity": state.get("peak_equity"),
                "drawdown": state.get("max_drawdown"),
                "exposure": (cycle.get("economic_metrics") or {}).get("exposure"),
            },
        )
        _append(
            root / "runtime_events.jsonl",
            {
                "session_id": session_id,
                "cycle_id": cycle.get("cycle_id"),
                "event": "bridge_cycle_completed",
                "forced_wiring": cycle.get("forced_wiring"),
            },
        )
        if (cycle.get("safety_evaluation") or {}).get("safety_result") == "BLOCKED":
            _append(
                root / "killstate_events.jsonl",
                {
                    "session_id": session_id,
                    "cycle_id": cycle.get("cycle_id"),
                    "trigger": (cycle.get("safety_evaluation") or {}).get("veto_reason"),
                },
            )

    for fill in fill_ledger:
        _append(root / "simulated_fill_trace.jsonl", dict(fill))

    metrics_out = dict(economic_metrics)
    if exclude_from_economic_metrics:
        metrics_out = {
            "excluded": True,
            "reason": "FORCED_WIRING_FIXTURE_EXCLUDED_FROM_ECONOMIC_METRICS",
            "raw_present_but_excluded": True,
        }
    _write_json(root / "economic_metrics.json", metrics_out)
    _write_json(root / "portfolio_snapshot.json", dict(portfolio_snapshot))
    _write_json(root / "full_economic_reconstruction_verifier.json", dict(verification))
    _write_json(
        root / "completion_verdict.json",
        {
            "ok": bool(verification.get("ok")),
            "capability_id": CAPABILITY_ID,
            "mode": mode,
            "exclude_from_economic_metrics": exclude_from_economic_metrics,
        },
    )

    digests: dict[str, str] = {}
    for name in REQUIRED_EVIDENCE_STREAMS:
        path = root / name
        if path.is_file():
            digests[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    integrity = {"digests": digests, "capability_id": CAPABILITY_ID, "session_id": session_id}
    _write_json(root / "integrity_manifest.json", integrity)
    return {"ok": True, "evidence_root": str(root), "digests": digests}
