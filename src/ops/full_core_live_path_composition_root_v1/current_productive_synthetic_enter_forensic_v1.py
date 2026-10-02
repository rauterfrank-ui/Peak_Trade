"""Forensic-only synthetic ENTER overlay at LIVE-29P join seam (default OFF).

Does not change thresholds, market data, or natural-enter metrics.
RUNTIME_AUTHORIZATION_EFFECT=NONE — no POST, no credentials, no external effects.
"""

from __future__ import annotations

import json
import os
import tempfile
from contextvars import ContextVar
from contextvars import Token as _CtxReset
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)

OWNER = "full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1"

ENTRY_ORIGIN_SYNTHETIC_FORENSIC = "SYNTHETIC_FORENSIC"
INJECTION_POINT_LIVE_29P_JOIN_SEAM_V1 = "LIVE_29P_JOIN_SEAM_BEFORE_29P_V1"
SYNTHETIC_REASON_DOWNSTREAM_LIVENESS = "DOWNSTREAM_LIVENESS_ADJUDICATION"

NATURAL_ENTER_OUTCOMES = frozenset({"enter_long", "enter_short"})
ALLOWED_SYNTHETIC_SIDES = frozenset({"enter_long", "enter_short"})

LEDGER_FILENAME = "synthetic_enter_forensic_v1.jsonl"
SUMMARY_FILENAME = "synthetic_enter_forensic_summary_v1.json"

_session_var: ContextVar["SyntheticEnterForensicSessionV1 | None"] = ContextVar(
    "synthetic_enter_forensic_session_v1", default=None
)


@dataclass
class SyntheticEnterForensicSessionV1:
    enabled: bool
    synthetic_side: str
    inject_cycle_index: int
    product_evidence_root: Path
    continuous_run_id: str
    _applied_cycle_indices: set[int] = field(default_factory=set, repr=False)

    def mark_applied_v1(self, cycle_index: int) -> None:
        self._applied_cycle_indices.add(int(cycle_index))


def bind_synthetic_enter_forensic_session_v1(
    session: SyntheticEnterForensicSessionV1 | None,
) -> _CtxReset:
    return _session_var.set(session)


def reset_synthetic_enter_forensic_session_v1(ctx_reset_handle: _CtxReset) -> None:
    _session_var.reset(ctx_reset_handle)


def active_synthetic_enter_forensic_session_v1() -> SyntheticEnterForensicSessionV1 | None:
    session = _session_var.get()
    if session is None or not session.enabled:
        return None
    return session


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _atomic_append_jsonl_v1(*, path: Path, record: Mapping[str, Any]) -> None:
    line = json.dumps(dict(record), sort_keys=True, ensure_ascii=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def _atomic_write_json_v1(*, path: Path, payload: Mapping[str, Any]) -> None:
    text = json.dumps(dict(payload), indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".syn_", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except OSError:
        tmp_path.unlink(missing_ok=True)
        raise


def read_cycle_index_from_s5_evidence_root_v1(evidence_root: Path) -> int | None:
    auth_path = Path(evidence_root) / "s5_cycle_authorization_v1.json"
    if not auth_path.is_file():
        parent_auth = Path(evidence_root).parent / "s5_cycle_authorization_v1.json"
        auth_path = parent_auth if parent_auth.is_file() else auth_path
    if not auth_path.is_file():
        return None
    try:
        payload = json.loads(auth_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    raw = payload.get("cycle_index")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _natural_outcome_from_replay_v1(replay: IntegratedOfflineReplayResultV1) -> str:
    raw = getattr(getattr(replay, "evidence", None), "decision_outcome", "") or ""
    return str(getattr(raw, "value", raw) or "").strip().lower()


@dataclass(frozen=True)
class SyntheticEnterForensicApplyResultV1:
    replay: IntegratedOfflineReplayResultV1
    applied: bool
    natural_outcome_before: str
    synthetic_side: str
    cycle_index: int | None
    record: dict[str, Any] | None


def maybe_apply_synthetic_enter_forensic_overlay_v1(
    replay: IntegratedOfflineReplayResultV1,
    *,
    cycle_index: int | None,
    cycle_evidence_root: Path | None = None,
) -> SyntheticEnterForensicApplyResultV1:
    """Overlay synthetic enter on replay at LIVE-29P join seam when armed."""
    session = active_synthetic_enter_forensic_session_v1()
    natural_before = _natural_outcome_from_replay_v1(replay)
    if session is None:
        return SyntheticEnterForensicApplyResultV1(
            replay=replay,
            applied=False,
            natural_outcome_before=natural_before,
            synthetic_side="",
            cycle_index=cycle_index,
            record=None,
        )
    if cycle_index is None:
        return SyntheticEnterForensicApplyResultV1(
            replay=replay,
            applied=False,
            natural_outcome_before=natural_before,
            synthetic_side=session.synthetic_side,
            cycle_index=None,
            record=None,
        )
    if int(cycle_index) != int(session.inject_cycle_index):
        return SyntheticEnterForensicApplyResultV1(
            replay=replay,
            applied=False,
            natural_outcome_before=natural_before,
            synthetic_side=session.synthetic_side,
            cycle_index=cycle_index,
            record=None,
        )
    if int(cycle_index) in session._applied_cycle_indices:
        return SyntheticEnterForensicApplyResultV1(
            replay=replay,
            applied=False,
            natural_outcome_before=natural_before,
            synthetic_side=session.synthetic_side,
            cycle_index=cycle_index,
            record=None,
        )
    if natural_before in NATURAL_ENTER_OUTCOMES:
        return SyntheticEnterForensicApplyResultV1(
            replay=replay,
            applied=False,
            natural_outcome_before=natural_before,
            synthetic_side=session.synthetic_side,
            cycle_index=cycle_index,
            record=None,
        )
    side = str(session.synthetic_side or "").strip().lower()
    if side not in ALLOWED_SYNTHETIC_SIDES:
        return SyntheticEnterForensicApplyResultV1(
            replay=replay,
            applied=False,
            natural_outcome_before=natural_before,
            synthetic_side=side,
            cycle_index=cycle_index,
            record=None,
        )

    evidence = replay.evidence
    new_evidence = replace(
        evidence,
        decision_outcome=side,
    )
    new_replay = replace(replay, evidence=new_evidence)
    session.mark_applied_v1(int(cycle_index))

    record: dict[str, Any] = {
        "schema": "synthetic_enter_forensic_apply.v1",
        "owner": OWNER,
        "recorded_at": _utc_now_iso_v1(),
        "continuous_run_id": session.continuous_run_id,
        "cycle_index": int(cycle_index),
        "cycle_evidence_root": str(cycle_evidence_root or ""),
        "entry_origin": ENTRY_ORIGIN_SYNTHETIC_FORENSIC,
        "synthetic_enter": True,
        "natural_enter": False,
        "synthetic_side": side,
        "synthetic_injection_point": INJECTION_POINT_LIVE_29P_JOIN_SEAM_V1,
        "synthetic_reason": SYNTHETIC_REASON_DOWNSTREAM_LIVENESS,
        "natural_outcome_before_overlay": natural_before,
        "decision_outcome_after_overlay": side,
    }
    ledger = Path(session.product_evidence_root) / LEDGER_FILENAME
    _atomic_append_jsonl_v1(path=ledger, record=record)
    summary_path = Path(session.product_evidence_root) / SUMMARY_FILENAME
    summary = {
        "owner": OWNER,
        "continuous_run_id": session.continuous_run_id,
        "synthetic_enter_count": len(session._applied_cycle_indices),
        "synthetic_enter_observed": len(session._applied_cycle_indices) > 0,
        "natural_enter_observed_via_synthetic_path": False,
        "last_record": record,
    }
    _atomic_write_json_v1(path=summary_path, payload=summary)
    if cycle_evidence_root is not None:
        _atomic_write_json_v1(
            path=Path(cycle_evidence_root) / "synthetic_enter_forensic_cycle_v1.json",
            payload=record,
        )

    return SyntheticEnterForensicApplyResultV1(
        replay=new_replay,
        applied=True,
        natural_outcome_before=natural_before,
        synthetic_side=side,
        cycle_index=cycle_index,
        record=record,
    )


def build_synthetic_enter_forensic_session_v1(
    *,
    enabled: bool,
    synthetic_side: str,
    inject_cycle_index: int,
    product_evidence_root: Path,
    continuous_run_id: str,
) -> SyntheticEnterForensicSessionV1:
    side = str(synthetic_side or "enter_short").strip().lower()
    if side not in ALLOWED_SYNTHETIC_SIDES:
        raise ValueError("SYNTHETIC_SIDE_INVALID")
    return SyntheticEnterForensicSessionV1(
        enabled=bool(enabled),
        synthetic_side=side,
        inject_cycle_index=max(1, int(inject_cycle_index)),
        product_evidence_root=Path(product_evidence_root),
        continuous_run_id=str(continuous_run_id),
    )


__all__ = [
    "ALLOWED_SYNTHETIC_SIDES",
    "ENTRY_ORIGIN_SYNTHETIC_FORENSIC",
    "INJECTION_POINT_LIVE_29P_JOIN_SEAM_V1",
    "LEDGER_FILENAME",
    "NATURAL_ENTER_OUTCOMES",
    "OWNER",
    "SUMMARY_FILENAME",
    "SYNTHETIC_REASON_DOWNSTREAM_LIVENESS",
    "SyntheticEnterForensicApplyResultV1",
    "SyntheticEnterForensicSessionV1",
    "active_synthetic_enter_forensic_session_v1",
    "bind_synthetic_enter_forensic_session_v1",
    "build_synthetic_enter_forensic_session_v1",
    "maybe_apply_synthetic_enter_forensic_overlay_v1",
    "read_cycle_index_from_s5_evidence_root_v1",
    "reset_synthetic_enter_forensic_session_v1",
]
