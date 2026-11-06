"""Passive real-carrier capture at CB-001/CB-002 (V7/V8 observability contract).

Observation-only. Does not alter trading decisions, replay inputs, or protected replay.
Default disabled; explicit session bind + capture_armed for bounded real observation runs.
Output is isolated to an operator-supplied capture root (typically under /tmp).
"""

from __future__ import annotations

import hashlib
import json
from contextvars import ContextVar
from contextvars import Token as _CtxReset
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional

from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
)
from trading.master_v2.integrated_offline_replay_evidence_writer_v1 import (
    _file_sha256,
    _jsonable,
    _write_json,
)

OWNER = "full_core_live_path_composition_root_v1.productive_real_carrier_passive_capture_v1"

REAL_CARRIER_PASSIVE_CAPTURE_SCHEMA_VERSION = "real_carrier_passive_capture.v1"
SAME_RUN_JOIN_MANIFEST_SCHEMA_VERSION = "same_run_join_manifest.v1"

REPLAY_INPUT_ARTIFACT = "replay_input.json"
SAME_RUN_JOIN_MANIFEST_ARTIFACT = "same_run_join_manifest_v1.json"
CAPTURE_MANIFEST_ARTIFACT = "MANIFEST.sha256"

CAPTURE_DEFAULT_ENABLED = False
CAPTURE_FAILURE_POLICY_ARMED = "FAIL_CLOSED_BEFORE_REPLAY"

_session_var: ContextVar[Optional["RealCarrierPassiveCaptureSessionV1"]] = ContextVar(
    "real_carrier_passive_capture_session_v1", default=None
)


class RealCarrierPassiveCaptureError(RuntimeError):
    """Fail-closed passive capture persistence violation (armed path only)."""


@dataclass(frozen=True)
class SameRunJoinManifestV1:
    """CB-002 join keys for atomic same-run carrier evidence (V7 applicability)."""

    schema_version: str
    run_id: str
    cycle_id: str
    replay_id: str
    instrument_id: str
    selection_id: str
    binding_id: str
    trading_epoch: int
    market_observation_epoch: int | None
    confirmation_epoch: int | None
    side: str
    venue_event_time: float | None
    context_reference: str
    input_digest: str
    cursor_restore_status: str
    capture_boundary_cb001: str
    capture_boundary_cb002: str
    captured_at_utc: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "cycle_id": self.cycle_id,
            "replay_id": self.replay_id,
            "instrument_id": self.instrument_id,
            "selection_id": self.selection_id,
            "binding_id": self.binding_id,
            "trading_epoch": int(self.trading_epoch),
            "market_observation_epoch": self.market_observation_epoch,
            "confirmation_epoch": self.confirmation_epoch,
            "side": self.side,
            "venue_event_time": self.venue_event_time,
            "context_reference": self.context_reference,
            "input_digest": self.input_digest,
            "cursor_restore_status": self.cursor_restore_status,
            "capture_boundary_cb001": self.capture_boundary_cb001,
            "capture_boundary_cb002": self.capture_boundary_cb002,
            "captured_at_utc": self.captured_at_utc,
        }


@dataclass
class RealCarrierPassiveCaptureSessionV1:
    enabled: bool
    capture_armed: bool
    capture_root: Path
    run_id: str
    continuous_run_id: str = ""

    def effective_run_id_v1(self) -> str:
        base = str(self.run_id or "").strip()
        cont = str(self.continuous_run_id or "").strip()
        if base and cont:
            return f"{base}+{cont}"
        return base or cont


def bind_real_carrier_passive_capture_session_v1(
    session: RealCarrierPassiveCaptureSessionV1 | None,
) -> _CtxReset:
    return _session_var.set(session)


def reset_real_carrier_passive_capture_session_v1(ctx_reset_handle: _CtxReset) -> None:
    _session_var.reset(ctx_reset_handle)


def active_real_carrier_passive_capture_session_v1() -> RealCarrierPassiveCaptureSessionV1 | None:
    session = _session_var.get()
    if session is None or not session.enabled:
        return None
    return session


def _side_label_v1(side_state: Any) -> str:
    if isinstance(side_state, Enum):
        return str(side_state.value)
    return str(side_state)


def build_same_run_join_manifest_v1(
    *,
    session: RealCarrierPassiveCaptureSessionV1,
    replay_input: IntegratedOfflineReplayInputV1,
    cycle_id: str,
    replay_id: str,
    instrument_id: str,
    selection_id: str,
    binding_id: str,
    trading_epoch: int,
    market_observation_epoch: int | None,
    confirmation_epoch: int | None,
    side_state: Any,
    venue_event_time: float | None,
    context_reference: str,
    input_digest: str,
    cursor_restore_status: str,
) -> SameRunJoinManifestV1:
    return SameRunJoinManifestV1(
        schema_version=SAME_RUN_JOIN_MANIFEST_SCHEMA_VERSION,
        run_id=session.effective_run_id_v1(),
        cycle_id=str(cycle_id),
        replay_id=str(replay_id),
        instrument_id=str(instrument_id),
        selection_id=str(selection_id or ""),
        binding_id=str(binding_id or ""),
        trading_epoch=int(trading_epoch),
        market_observation_epoch=market_observation_epoch,
        confirmation_epoch=confirmation_epoch,
        side=_side_label_v1(side_state),
        venue_event_time=venue_event_time,
        context_reference=str(context_reference),
        input_digest=str(input_digest),
        cursor_restore_status=str(cursor_restore_status),
        capture_boundary_cb001="CB-001-POST-REPLAY-INPUT-BUILD",
        capture_boundary_cb002="CB-002-SAME-RUN-JOIN-MANIFEST",
        captured_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def write_real_carrier_pre_replay_bundle_v1(
    *,
    capture_root: Path,
    replay_input: IntegratedOfflineReplayInputV1,
    join_manifest: SameRunJoinManifestV1,
) -> Path:
    """Write CB-001 replay input + CB-002 join manifest + MANIFEST.sha256."""
    root = Path(capture_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    replay_path = root / REPLAY_INPUT_ARTIFACT
    join_path = root / SAME_RUN_JOIN_MANIFEST_ARTIFACT
    _write_json(replay_path, replay_input)
    _write_json(join_path, join_manifest.to_dict())

    manifest_lines = [
        f"{_file_sha256(replay_path)}  {REPLAY_INPUT_ARTIFACT}\n",
        f"{_file_sha256(join_path)}  {SAME_RUN_JOIN_MANIFEST_ARTIFACT}\n",
    ]
    manifest_path = root / CAPTURE_MANIFEST_ARTIFACT
    manifest_path.write_text("".join(sorted(manifest_lines)), encoding="utf-8")
    return manifest_path


def verify_real_carrier_capture_manifest_v1(manifest_path: Path) -> int:
    """Verify MANIFEST.sha256 for passive capture bundle. Returns 0 on success."""
    manifest = Path(manifest_path).expanduser().resolve()
    if not manifest.is_file():
        return 1
    base = manifest.parent
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, _, name = line.partition("  ")
        file_path = base / name.strip()
        if not file_path.is_file():
            return 2
        if _file_sha256(file_path) != digest.strip():
            return 3
    return 0


def replay_input_json_digest_v1(replay_input: IntegratedOfflineReplayInputV1) -> str:
    payload = json.dumps(
        _jsonable(replay_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def enforce_real_carrier_passive_capture_before_replay_v1(
    *,
    replay_input: IntegratedOfflineReplayInputV1,
    cycle_id: str,
    replay_id: str,
    instrument_id: str,
    selection_id: str,
    binding_id: str,
    trading_epoch: int,
    market_observation_epoch: int | None,
    confirmation_epoch: int | None,
    side_state: Any,
    venue_event_time: float | None,
    context_reference: str,
    input_digest: str,
    cursor_restore_status: str,
) -> str | None:
    """If armed capture is active, persist bundle or return fail-closed reason.

    Returns None when capture is disabled/not armed or persistence succeeded.
    """
    session = active_real_carrier_passive_capture_session_v1()
    if session is None or not session.capture_armed:
        return None
    try:
        join = build_same_run_join_manifest_v1(
            session=session,
            replay_input=replay_input,
            cycle_id=cycle_id,
            replay_id=replay_id,
            instrument_id=instrument_id,
            selection_id=selection_id,
            binding_id=binding_id,
            trading_epoch=trading_epoch,
            market_observation_epoch=market_observation_epoch,
            confirmation_epoch=confirmation_epoch,
            side_state=side_state,
            venue_event_time=venue_event_time,
            context_reference=context_reference,
            input_digest=input_digest,
            cursor_restore_status=cursor_restore_status,
        )
        manifest = write_real_carrier_pre_replay_bundle_v1(
            capture_root=session.capture_root,
            replay_input=replay_input,
            join_manifest=join,
        )
        if verify_real_carrier_capture_manifest_v1(manifest) != 0:
            raise RealCarrierPassiveCaptureError("MANIFEST_VERIFY_FAILED")
    except (OSError, RealCarrierPassiveCaptureError, TypeError, ValueError) as exc:
        return f"REAL_CARRIER_PASSIVE_CAPTURE_FAIL_CLOSED:{exc}"
    return None


def read_captured_replay_input_v1(capture_root: Path) -> Mapping[str, Any]:
    path = Path(capture_root).expanduser().resolve() / REPLAY_INPUT_ARTIFACT
    return json.loads(path.read_text(encoding="utf-8"))
