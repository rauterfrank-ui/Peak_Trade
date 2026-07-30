"""Wallclock observation evidence writer (immutable + append-only)."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
    EVIDENCE_SCHEMA_ID,
    EVIDENCE_SCHEMA_VERSION,
    EXECUTION_CLASS_ANALYTICAL,
    PACKAGE_MARKER,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.killstate_runtime_v1 import (
    TerminalVerdict,
)

REQUIRED_IMMUTABLE = (
    "prereg.json",
    "operator_go.json",
    "authorization_artifact.json",
    "authorization_consumption_record.json",
    "authorization_consumption.json",
    "session_manifest.json",
    "config_snapshot.json",
    "scope_digest.txt",
    "repo_sha.txt",
    "runtime_env_fingerprint.json",
    "venue_instrument_binding.json",
    "planned_actual_timestamps.json",
    "observation_cycle_counters.json",
    "shutdown_reason.json",
    "no_order_attestation.json",
    "network_boundary_attestation.json",
    "portfolio_snapshot.json",
    "economic_metrics.json",
    "completion_verdict.json",
    "terminal_verdict.json",
    "integrity_manifest.json",
    "evidence_manifest.sha256",
)

APPEND_ONLY = (
    "heartbeat.jsonl",
    "connectivity_events.jsonl",
    "reconnect_events.jsonl",
    "stale_events.jsonl",
    "market_data_sequence.jsonl",
    "feature_trace.jsonl",
    "regime_trace.jsonl",
    "decision_trace.jsonl",
    "risk_telemetry.jsonl",
    "risk_sizing_trace.jsonl",
    "order_intent_trace.jsonl",
    "simulated_fill_trace.jsonl",
    "portfolio_snapshots.jsonl",
    "equity_curve.jsonl",
    "runtime_events.jsonl",
    "killstate_events.jsonl",
    "bridge_cycle_ledger.jsonl",
    "bridge_fill_ledger.jsonl",
    "simulated_fills.jsonl",
)


class WallclockEvidenceError(RuntimeError):
    """Fail-closed evidence writer error."""


def _canonical_json(payload: Mapping[str, Any] | list[Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    fd = os.open(str(tmp), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(str(tmp), str(path))


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = _canonical_json(dict(payload)) + "\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())


@dataclass
class WallclockEvidenceWriterV1:
    evidence_root: Path
    digests: dict[str, str] = field(default_factory=dict)
    finalized: bool = False
    incomplete: bool = False

    def write_immutable_json(self, name: str, payload: Mapping[str, Any]) -> None:
        if self.finalized:
            raise WallclockEvidenceError("EVIDENCE_TAMPER")
        text = _canonical_json(dict(payload)) + "\n"
        path = self.evidence_root / name
        if path.exists():
            raise WallclockEvidenceError(f"IMMUTABLE_ALREADY_EXISTS:{name}")
        try:
            _atomic_write_text(path, text)
        except OSError as exc:
            raise WallclockEvidenceError(f"EVIDENCE_SINK_FAILURE:{exc}") from exc
        self.digests[name] = _sha256_text(text)

    def write_immutable_text(self, name: str, text: str) -> None:
        if self.finalized:
            raise WallclockEvidenceError("EVIDENCE_TAMPER")
        body = text if text.endswith("\n") else text + "\n"
        path = self.evidence_root / name
        if path.exists():
            raise WallclockEvidenceError(f"IMMUTABLE_ALREADY_EXISTS:{name}")
        try:
            _atomic_write_text(path, body)
        except OSError as exc:
            raise WallclockEvidenceError(f"EVIDENCE_SINK_FAILURE:{exc}") from exc
        self.digests[name] = _sha256_text(body)

    def append_event(self, name: str, payload: Mapping[str, Any]) -> None:
        if self.finalized:
            raise WallclockEvidenceError("EVIDENCE_TAMPER")
        if name not in APPEND_ONLY:
            raise WallclockEvidenceError(f"NOT_APPEND_ONLY:{name}")
        try:
            _append_jsonl(self.evidence_root / name, payload)
        except OSError as exc:
            raise WallclockEvidenceError(f"EVIDENCE_SINK_FAILURE:{exc}") from exc

    def ensure_append_files(self) -> None:
        for name in APPEND_ONLY:
            path = self.evidence_root / name
            if not path.exists():
                path.write_text("", encoding="utf-8")

    def finalize(
        self,
        *,
        verdict: TerminalVerdict,
        incomplete: bool,
        extras: Optional[Mapping[str, Any]] = None,
    ) -> None:
        if self.finalized:
            raise WallclockEvidenceError("ALREADY_FINALIZED")
        self.incomplete = incomplete
        # digest append-only files at finalize
        for name in APPEND_ONLY:
            path = self.evidence_root / name
            if path.is_file():
                self.digests[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        terminal = {
            "schema_id": EVIDENCE_SCHEMA_ID,
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "capability_id": CAPABILITY_ID,
            "package_marker": PACKAGE_MARKER,
            "verdict": verdict.value,
            "incomplete": incomplete,
            "authority_effect": AUTHORITY_EFFECT_NONE,
            "economic_validity_pass": False,
            "promotion_pass": False,
            "execution_class": EXECUTION_CLASS_ANALYTICAL,
            "paper_execution": False,
            "orders_submitted": False,
            "credentials_used": False,
            "extras": dict(extras or {}),
        }
        self.write_immutable_json("terminal_verdict.json", terminal)
        integrity = {
            "schema_id": EVIDENCE_SCHEMA_ID,
            "digests": dict(sorted(self.digests.items())),
            "incomplete": incomplete,
            "verdict": verdict.value,
        }
        integrity_text = _canonical_json(integrity) + "\n"
        _atomic_write_text(self.evidence_root / "integrity_manifest.json", integrity_text)
        self.digests["integrity_manifest.json"] = _sha256_text(integrity_text)
        lines = [f"{digest}  {name}" for name, digest in sorted(self.digests.items())]
        manifest = "\n".join(lines) + "\n"
        _atomic_write_text(self.evidence_root / "evidence_manifest.sha256", manifest)
        # fsync directory best-effort
        try:
            fd = os.open(str(self.evidence_root), os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        except OSError as exc:
            raise WallclockEvidenceError(f"EVIDENCE_SINK_FAILURE:{exc}") from exc
        self.finalized = True
