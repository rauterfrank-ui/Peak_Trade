"""GHV PRE_EXTERNAL runtime flight recorder + continuation snapshot (observation-only).

AUTHORITY=NONE — does not change trading decisions, replay, safety, or POST paths.
"""

from __future__ import annotations

import hashlib
import json
import re
from contextvars import ContextVar
from datetime import date, datetime, timezone
from decimal import Decimal
from contextvars import Token as _CtxReset
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)

OWNER = "full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1"

FLIGHT_RECORD_SCHEMA_VERSION = "ghv_pre_external_runtime_flight_record.v1"
FLIGHT_RECORD_FILENAME = "ghv_pre_external_runtime_flight_record_v1.jsonl"
CAPTURE_MANIFEST_FILENAME = "ghv_pre_external_runtime_capture_manifest_v1.json"
CONTINUATION_SNAPSHOT_DIRNAME = "ghv_pre_external_continuation_snapshot_v1"
CONTINUATION_SNAPSHOT_MANIFEST = "ghv_pre_external_continuation_snapshot_manifest_v1.json"
CAUSAL_BLOCKER_REPORT_FILENAME = "ghv_pre_external_causal_blocker_report_v1.json"
GHV_ROOT_CHANGE_EVENT_ID = "GHV_SYNTHETIC_ENTER_SHORT_CYCLE_1"

RECORDER_AUTHORITY = "NONE"
RECORDER_CAPTURE_FAILURE_CHANGES_DECISION = False

_FORBIDDEN_SECRET_KEYS = frozenset(
    {
        "api_key",
        "api_secret",
        "apikey",
        "secret",
        "passphrase",
        "private_key",
        "secret_key",
        "signing_secret",
    }
)

_session_var: ContextVar[Optional["GhvPreExternalRuntimeFlightRecorderSessionV1"]] = ContextVar(
    "ghv_pre_external_runtime_flight_recorder_session_v1",
    default=None,
)


class GhvPreExternalRuntimeFlightRecorderError(RuntimeError):
    """Fail-closed flight recorder persistence violation."""


@dataclass
class GhvPreExternalRuntimeFlightRecorderSessionV1:
    enabled: bool
    product_evidence_root: Path
    run_id: str
    continuous_run_id: str
    repository_sha: str = ""
    cycle_index: int | None = None
    _generation_counter: int = field(default=0, repr=False)
    _lineage_root: str = field(default="gen_root", repr=False)

    def next_generation_id_v1(
        self,
        *,
        stage: str,
        parent_generation_id: str,
        replay: IntegratedOfflineReplayResultV1 | None,
    ) -> str:
        self._generation_counter += 1
        replay_anchor = ""
        if replay is not None and replay.evidence is not None:
            replay_anchor = str(
                replay.evidence.semantic_digest
                or replay.evidence.replay_id
                or replay.evidence.decision_id
                or ""
            )
        raw = (f"{parent_generation_id}|{stage}|{self._generation_counter}|{replay_anchor}").encode(
            "utf-8"
        )
        return f"gen_{hashlib.sha256(raw).hexdigest()[:24]}"


def bind_ghv_pre_external_runtime_flight_recorder_session_v1(
    session: GhvPreExternalRuntimeFlightRecorderSessionV1 | None,
) -> _CtxReset:
    return _session_var.set(session)


def reset_ghv_pre_external_runtime_flight_recorder_session_v1(
    ctx_reset_handle: _CtxReset,
) -> None:
    _session_var.reset(ctx_reset_handle)


def active_ghv_pre_external_runtime_flight_recorder_session_v1() -> (
    GhvPreExternalRuntimeFlightRecorderSessionV1 | None
):
    session = _session_var.get()
    if session is None or not session.enabled:
        return None
    return session


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _jsonable(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: _jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, Mapping):
        return {str(k): _jsonable(v) for k, v in sorted(obj.items())}
    if isinstance(obj, Path):
        return str(obj)
    return obj


def _assert_no_secrets(payload: Any, *, path: str = "") -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            key_s = str(key)
            normalized = key_s.lower().replace("-", "_")
            if normalized in _FORBIDDEN_SECRET_KEYS:
                raise GhvPreExternalRuntimeFlightRecorderError(
                    f"SECRET_KEY_FORBIDDEN:{path}.{key_s}"
                )
            _assert_no_secrets(value, path=f"{path}.{key_s}" if path else key_s)
        return
    if isinstance(payload, (list, tuple)):
        for idx, item in enumerate(payload):
            _assert_no_secrets(item, path=f"{path}[{idx}]")


def _replay_summary_v1(replay: IntegratedOfflineReplayResultV1 | None) -> dict[str, Any]:
    if replay is None or replay.evidence is None:
        return {
            "decision_outcome": "",
            "selected_side": "",
            "replay_pass": False,
            "replay_id": "",
            "semantic_digest": "",
        }
    ev = replay.evidence
    raw_outcome = ev.decision_outcome
    outcome = str(getattr(raw_outcome, "value", raw_outcome) or "")
    raw_side = ev.selected_side
    side = str(getattr(raw_side, "value", raw_side) or raw_side or "")
    ts = getattr(replay, "replay_execution_safety", None)
    safety_summary: dict[str, Any] = {}
    if ts is not None:
        safety_summary = _jsonable(ts)
    sizing = None
    if replay.intermediate is not None:
        sizing = replay.intermediate.capital_risk_sizing_decision
    sizing_summary = _jsonable(sizing) if sizing is not None else None
    return {
        "decision_outcome": outcome,
        "selected_side": side,
        "replay_pass": bool(replay.replay_pass),
        "replay_id": str(ev.replay_id or ""),
        "semantic_digest": str(ev.semantic_digest or ""),
        "reason_codes": list(ev.reason_codes or ()),
        "replay_execution_safety": safety_summary,
        "sizing_state": sizing_summary,
    }


def append_flight_record_stage_v1(
    *,
    stage: str,
    producer_symbol: str,
    consumer_symbol: str,
    parent_generation_id: str,
    replay: IntegratedOfflineReplayResultV1 | None = None,
    extra: Mapping[str, Any] | None = None,
    predicate_traces: tuple[Mapping[str, Any], ...] = (),
) -> str | None:
    session = active_ghv_pre_external_runtime_flight_recorder_session_v1()
    if session is None:
        return None
    try:
        return _append_flight_record_stage_inner_v1(
            session=session,
            stage=stage,
            producer_symbol=producer_symbol,
            consumer_symbol=consumer_symbol,
            parent_generation_id=parent_generation_id,
            replay=replay,
            extra=extra,
            predicate_traces=predicate_traces,
        )
    except GhvPreExternalRuntimeFlightRecorderError:
        if RECORDER_CAPTURE_FAILURE_CHANGES_DECISION:
            raise
        return None


def _append_flight_record_stage_inner_v1(
    *,
    session: GhvPreExternalRuntimeFlightRecorderSessionV1,
    stage: str,
    producer_symbol: str,
    consumer_symbol: str,
    parent_generation_id: str,
    replay: IntegratedOfflineReplayResultV1 | None,
    extra: Mapping[str, Any] | None,
    predicate_traces: tuple[Mapping[str, Any], ...],
) -> str:
    generation_id = session.next_generation_id_v1(
        stage=stage,
        parent_generation_id=parent_generation_id,
        replay=replay,
    )
    row: dict[str, Any] = {
        "schema_version": FLIGHT_RECORD_SCHEMA_VERSION,
        "owner": OWNER,
        "repository_sha": session.repository_sha,
        "run_id": session.run_id,
        "continuous_run_id": session.continuous_run_id,
        "cycle_index": session.cycle_index,
        "capture_timestamp": _utc_now_iso(),
        "stage": stage,
        "producer_symbol": producer_symbol,
        "consumer_symbol": consumer_symbol,
        "object_generation_id": generation_id,
        "parent_generation_id": parent_generation_id,
        "recorder_authority": RECORDER_AUTHORITY,
        **_replay_summary_v1(replay),
    }
    if extra:
        row.update(_jsonable(dict(extra)))
    if predicate_traces:
        row["predicate_traces"] = [_jsonable(dict(p)) for p in predicate_traces]
    from src.ops.full_core_live_path_composition_root_v1.ghv_system_wide_canary_surface_discovery_v1 import (
        attach_canary_correlation_to_flight_row_v1,
    )

    row = attach_canary_correlation_to_flight_row_v1(row)
    _assert_no_secrets(row)
    path = session.product_evidence_root / FLIGHT_RECORD_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    return generation_id


def sync_flight_recorder_cycle_from_s5_evidence_root_v1(*, s5_evidence_root: Path) -> None:
    session = active_ghv_pre_external_runtime_flight_recorder_session_v1()
    if session is None:
        return
    auth_path = Path(s5_evidence_root).parent / "s5_cycle_authorization_v1.json"
    if not auth_path.is_file():
        return
    try:
        payload = json.loads(auth_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    session.cycle_index = int(payload.get("cycle_index") or 0) or None


def record_ghv_root_change_event_v1(
    *,
    parent_generation_id: str,
    pre_overlay_generation: str,
    replay_before: IntegratedOfflineReplayResultV1,
    replay_after: IntegratedOfflineReplayResultV1,
    synthetic_side: str,
    cycle_index: int,
) -> str | None:
    """Root GHV Synthetic Cycle-1 change event (observation-only)."""
    before = _replay_summary_v1(replay_before)
    after = _replay_summary_v1(replay_after)
    changed: list[str] = []
    for key in ("decision_outcome", "selected_side"):
        if before.get(key) != after.get(key):
            changed.append(key)
    return append_flight_record_stage_v1(
        stage="GHV_ROOT_CHANGE_EVENT",
        producer_symbol="maybe_apply_synthetic_enter_forensic_overlay_v1",
        consumer_symbol="join_current_productive_enter_live_29p_before_venue_plan_v1",
        parent_generation_id=parent_generation_id,
        replay=replay_after,
        extra={
            "change_event_id": GHV_ROOT_CHANGE_EVENT_ID,
            "synthetic_decision": synthetic_side,
            "synthetic_selected_side": "short" if synthetic_side == "enter_short" else "long",
            "cycle_index": cycle_index,
            "pre_overlay_generation": pre_overlay_generation,
            "decision_before": before.get("decision_outcome"),
            "decision_after": after.get("decision_outcome"),
            "selected_side_before": before.get("selected_side"),
            "selected_side_after": after.get("selected_side"),
            "changed_fields": changed,
            "direct_consumers": [
                "join_current_productive_enter_live_29p_before_venue_plan_v1",
                "reapply_forensic_synthetic_safety_reprojection_on_replay_v1",
            ],
            "transitive_consumers": [
                "compose_core_live_execution_intent_v1",
                "try_bind_current_productive_venue_plan_v1",
            ],
            "unknown_fanout": [],
            "golden_happy_vector_centered": True,
            "ghv_forensic_observability_owner": (
                "productive_golden_happy_vector_forensic_observability_v1"
            ),
        },
    )


def record_pr7013_safety_reprojection_v1(
    *,
    parent_generation_id: str,
    replay_before: IntegratedOfflineReplayResultV1,
    replay_after: IntegratedOfflineReplayResultV1,
    helper_control_flow_reached: bool,
    helper_preconditions_satisfied: bool,
    helper_executed: bool,
) -> str | None:
    before = _replay_summary_v1(replay_before)
    after = _replay_summary_v1(replay_after)
    return append_flight_record_stage_v1(
        stage="PR7013_FORENSIC_SYNTHETIC_SAFETY_REPROJECTION",
        producer_symbol="reapply_forensic_synthetic_safety_reprojection_on_replay_v1",
        consumer_symbol="try_bind_current_productive_venue_plan_v1",
        parent_generation_id=parent_generation_id,
        replay=replay_after,
        extra={
            "helper_control_flow_reached": helper_control_flow_reached,
            "helper_preconditions_satisfied": helper_preconditions_satisfied,
            "helper_executed": helper_executed,
            "input_generation_id": parent_generation_id,
            "decision_before": before.get("decision_outcome"),
            "decision_after": after.get("decision_outcome"),
            "selected_side_before": before.get("selected_side"),
            "selected_side_after": after.get("selected_side"),
            "replay_execution_safety_before": before.get("replay_execution_safety"),
            "replay_execution_safety_after": after.get("replay_execution_safety"),
        },
    )


def persist_continuation_snapshot_v1(
    *,
    parent_generation_id: str,
    post_live_29p_replay: IntegratedOfflineReplayResultV1,
    bound_instrument: BoundInstrumentV1,
    composed_epoch: str,
    session_id: str,
    run_id_suffix: str,
    synthetic_overlay_applied: bool,
    live_29p_status: str,
    live_29p_first_blocker: str,
    captured_external_get_contracts: Mapping[str, Any] | None = None,
    venue_plan_input_generation_id: str | None = None,
) -> Path | None:
    session = active_ghv_pre_external_runtime_flight_recorder_session_v1()
    if session is None:
        return None
    snap_root = session.product_evidence_root / CONTINUATION_SNAPSHOT_DIRNAME
    snap_root.mkdir(parents=True, exist_ok=True)
    replay_bundle_dir = snap_root / "replay_bundle"
    replay_bundle_dir.mkdir(parents=True, exist_ok=True)
    bundle_payload = _jsonable(post_live_29p_replay)
    _assert_no_secrets(bundle_payload)
    (replay_bundle_dir / "integrated_offline_replay_result_v1.json").write_text(
        json.dumps(bundle_payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest: dict[str, Any] = {
        "schema_version": "ghv_pre_external_continuation_snapshot_manifest.v1",
        "owner": OWNER,
        "repository_sha": session.repository_sha,
        "run_id": session.run_id,
        "continuous_run_id": session.continuous_run_id,
        "cycle_index": session.cycle_index,
        "capture_seam": "POST_LIVE_29P_REBOUND_BEFORE_VENUE_PLAN",
        "parent_generation_id": parent_generation_id,
        "venue_plan_input_generation_id": venue_plan_input_generation_id or parent_generation_id,
        "composed_epoch": composed_epoch,
        "session_id": session_id,
        "run_id_suffix": run_id_suffix,
        "synthetic_overlay_applied": synthetic_overlay_applied,
        "live_29p_status": live_29p_status,
        "live_29p_first_blocker": live_29p_first_blocker,
        "bound_instrument": _jsonable(bound_instrument),
        "replay_bundle_relpath": "replay_bundle/integrated_offline_replay_result_v1.json",
        "captured_external_get_contracts": _jsonable(dict(captured_external_get_contracts or {})),
    }
    _assert_no_secrets(manifest)
    manifest_path = snap_root / CONTINUATION_SNAPSHOT_MANIFEST
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    append_flight_record_stage_v1(
        stage="CONTINUATION_SNAPSHOT_PERSISTED",
        producer_symbol="persist_continuation_snapshot_v1",
        consumer_symbol="ghv_pre_external_continuation_harness_v1",
        parent_generation_id=parent_generation_id,
        replay=post_live_29p_replay,
        extra={
            "continuation_snapshot_manifest": str(
                manifest_path.relative_to(session.product_evidence_root)
            ),
            "capture_seam": manifest["capture_seam"],
        },
    )
    _refresh_capture_manifest_v1(session)
    return manifest_path


def _refresh_capture_manifest_v1(session: GhvPreExternalRuntimeFlightRecorderSessionV1) -> None:
    manifest = {
        "schema_version": "ghv_pre_external_runtime_capture_manifest.v1",
        "owner": OWNER,
        "repository_sha": session.repository_sha,
        "run_id": session.run_id,
        "continuous_run_id": session.continuous_run_id,
        "flight_record": FLIGHT_RECORD_FILENAME,
        "continuation_snapshot_dir": CONTINUATION_SNAPSHOT_DIRNAME,
        "recorder_authority": RECORDER_AUTHORITY,
    }
    path = session.product_evidence_root / CAPTURE_MANIFEST_FILENAME
    path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def load_replay_from_continuation_snapshot_v1(
    snapshot_root: Path,
) -> tuple[dict[str, Any], IntegratedOfflineReplayResultV1]:
    """Load manifest + replay from a continuation snapshot directory."""
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        IntegratedOfflineReplayIntermediateV1,
        IntegratedOfflineReplayResultV1,
    )
    from trading.master_v2.canonical_trading_decision_evidence_v1 import (
        CanonicalTradingDecisionEvidenceV1,
    )

    root = Path(snapshot_root).resolve()
    manifest = json.loads((root / CONTINUATION_SNAPSHOT_MANIFEST).read_text(encoding="utf-8"))
    replay_path = root / str(manifest["replay_bundle_relpath"])
    raw = json.loads(replay_path.read_text(encoding="utf-8"))
    evidence_raw = raw.get("evidence") or {}
    evidence = CanonicalTradingDecisionEvidenceV1(**evidence_raw)
    intermediate_raw = raw.get("intermediate")
    intermediate = (
        IntegratedOfflineReplayIntermediateV1(**intermediate_raw)
        if intermediate_raw is not None
        else None
    )
    replay = IntegratedOfflineReplayResultV1(
        evidence=evidence,
        intermediate=intermediate,
        replay_pass=bool(raw.get("replay_pass")),
        fail_reasons=tuple(raw.get("fail_reasons") or ()),
        capital_risk_mode=str(raw.get("capital_risk_mode") or ""),
    )
    if raw.get("replay_execution_safety") is not None:
        from trading.master_v2.replay_execution_safety_contract_v1 import (
            ReplayExecutionSafetyV1,
        )

        replay = IntegratedOfflineReplayResultV1(
            evidence=evidence,
            intermediate=intermediate,
            replay_pass=bool(raw.get("replay_pass")),
            fail_reasons=tuple(raw.get("fail_reasons") or ()),
            capital_risk_mode=str(raw.get("capital_risk_mode") or ""),
            replay_execution_safety=ReplayExecutionSafetyV1(**raw["replay_execution_safety"]),
        )
    return manifest, replay


def bound_instrument_from_manifest_v1(manifest: Mapping[str, Any]) -> BoundInstrumentV1:
    return BoundInstrumentV1(**dict(manifest["bound_instrument"]))


__all__ = [
    "CAUSAL_BLOCKER_REPORT_FILENAME",
    "CONTINUATION_SNAPSHOT_DIRNAME",
    "FLIGHT_RECORD_FILENAME",
    "FLIGHT_RECORD_SCHEMA_VERSION",
    "GhvPreExternalRuntimeFlightRecorderError",
    "GhvPreExternalRuntimeFlightRecorderSessionV1",
    "OWNER",
    "RECORDER_AUTHORITY",
    "RECORDER_CAPTURE_FAILURE_CHANGES_DECISION",
    "active_ghv_pre_external_runtime_flight_recorder_session_v1",
    "append_flight_record_stage_v1",
    "bind_ghv_pre_external_runtime_flight_recorder_session_v1",
    "bound_instrument_from_manifest_v1",
    "load_replay_from_continuation_snapshot_v1",
    "persist_continuation_snapshot_v1",
    "record_ghv_root_change_event_v1",
    "record_pr7013_safety_reprojection_v1",
    "reset_ghv_pre_external_runtime_flight_recorder_session_v1",
]
