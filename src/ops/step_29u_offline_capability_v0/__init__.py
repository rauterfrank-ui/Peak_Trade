"""STEP 29U Offline Capability v0 — non-activating composition root.

Owns offline Shadow mode identity, lifecycle orchestration, session state
machine, failure classification, and immutable audit evidence. Consumes
canonical Master V2 / Double Play decision evidence and Risk/Sizing via the
existing OKX Futures offline no-order cycle. Does not activate Runtime,
Scheduler, network Runtime, or orders.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Optional

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.okx_futures_shadow_no_order_entrypoint_v0 import (
    OkxFuturesShadowNoOrderCycleResultV0,
    run_okx_futures_shadow_no_order_cycle_core_v0,
    serialize_okx_futures_shadow_no_order_cycle_result_v0,
)

PACKAGE_MARKER = "STEP_29U_OFFLINE_CAPABILITY_V0=true"
PRODUCER_FAMILY = "ops.step_29u_offline_capability_v0"
SCHEMA_ID = PRODUCER_FAMILY
SCHEMA_VERSION = "v0"
CAPABILITY_ID = "STEP_29U_OFFLINE_CAPABILITY_V0"
LIFECYCLE_OWNER = PRODUCER_FAMILY
CLI_RELPATH = "scripts/ops/run_step_29u_offline_capability_v0.py"
CANONICAL_STEP_29U_REFERENCE = (
    "docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md##STEP_29U"
)
INVENTORY_REFERENCE = (
    "docs/ops/runbooks/STEP_29U_CANONICAL_BINDING_AND_IMPLEMENTATION_INVENTORY_V0.md"
)

RESULT_PASS: Literal["STEP_29U_OFFLINE_CAPABILITY_PASS"] = "STEP_29U_OFFLINE_CAPABILITY_PASS"
RESULT_BLOCKED: Literal["STEP_29U_OFFLINE_CAPABILITY_BLOCKED"] = (
    "STEP_29U_OFFLINE_CAPABILITY_BLOCKED"
)
RESULT_ERROR: Literal["STEP_29U_OFFLINE_CAPABILITY_ERROR"] = "STEP_29U_OFFLINE_CAPABILITY_ERROR"

Mode = Literal["SHADOW_OFFLINE"]
REQUIRED_MODE: Mode = "SHADOW_OFFLINE"
REQUIRED_VENUE = "OKX"
REQUIRED_INSTRUMENT_CLASS = "USDT_PERPETUAL_FUTURES"

FORBIDDEN_IMPORT_SURFACES = frozenset(
    {
        "src.orders.shadow",
        "scripts.run_shadow_execution",
        "src.live.shadow_session",
        "scripts.run_shadow_paper_session",
    }
)

_BITCOIN_FRAGMENTS = frozenset({"BTC", "XBT", "BITCOIN"})
_SPOT_FRAGMENTS = frozenset({"SPOT", "/EUR", "/USD", "/USDT"})
_PATH_ESCAPE = re.compile(r"(^|/)\.\.(/|$)")


class Step29UOfflineCapabilityError(ValueError):
    """Fail-closed capability error."""


class FailureClassV0(str, Enum):
    IDENTITY_INVALID = "IDENTITY_INVALID"
    PREREQUISITE_MISSING = "PREREQUISITE_MISSING"
    DECISION_MISSING = "DECISION_MISSING"
    DECISION_INVALID = "DECISION_INVALID"
    RISK_MISSING = "RISK_MISSING"
    RISK_BLOCKED = "RISK_BLOCKED"
    EXECUTION_BOUNDARY_VIOLATION = "EXECUTION_BOUNDARY_VIOLATION"
    RECONCILIATION_MISMATCH = "RECONCILIATION_MISMATCH"
    STATE_TRANSITION_INVALID = "STATE_TRANSITION_INVALID"
    EVIDENCE_INVALID = "EVIDENCE_INVALID"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class SessionStateV0(str, Enum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    READY = "READY"
    RUNNING = "RUNNING"
    RECONCILING = "RECONCILING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


ALLOWED_TRANSITIONS: dict[SessionStateV0, frozenset[SessionStateV0]] = {
    SessionStateV0.CREATED: frozenset({SessionStateV0.VALIDATING, SessionStateV0.ERROR}),
    SessionStateV0.VALIDATING: frozenset(
        {SessionStateV0.READY, SessionStateV0.BLOCKED, SessionStateV0.ERROR}
    ),
    SessionStateV0.READY: frozenset(
        {SessionStateV0.RUNNING, SessionStateV0.BLOCKED, SessionStateV0.ERROR}
    ),
    SessionStateV0.RUNNING: frozenset(
        {SessionStateV0.RECONCILING, SessionStateV0.BLOCKED, SessionStateV0.ERROR}
    ),
    SessionStateV0.RECONCILING: frozenset(
        {SessionStateV0.COMPLETED, SessionStateV0.BLOCKED, SessionStateV0.ERROR}
    ),
    SessionStateV0.COMPLETED: frozenset(),
    SessionStateV0.BLOCKED: frozenset(),
    SessionStateV0.ERROR: frozenset(),
}

FORBIDDEN_STATE_NAMES = frozenset({"ARMED", "ACTIVATED", "LIVE", "ORDERING", "SCHEDULED"})


@dataclass(frozen=True)
class Step29UModeIdentityV0:
    capability_id: str
    schema_id: str
    schema_version: str
    canonical_step_29u_reference: str
    mode: Mode
    venue: str
    instrument_class: str
    instrument_id: str
    btc_excluded: bool
    spot_excluded: bool
    orders_allowed: bool
    network_runtime_allowed: bool
    scheduler_allowed: bool
    runtime_activation_allowed: bool
    source_git_sha: str
    effective_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LifecycleTransitionV0:
    from_state: str
    to_state: str
    reason: str


@dataclass
class CycleRecordV0:
    cycle_index: int
    decision_result: str
    direction: str
    decision_reason_codes: tuple[str, ...]
    risk_sizing_result: str
    execution_intent_result: str
    reconciliation_audit_result: str
    terminal_status: str
    cycle_payload: dict[str, Any]


@dataclass
class Step29UOfflineCapabilityResultV0:
    capability_result: str
    failure_class: str | None
    reason_codes: tuple[str, ...]
    identity: dict[str, Any]
    session_id: str
    lifecycle_owner: str
    lifecycle_transitions: list[LifecycleTransitionV0] = field(default_factory=list)
    cycles: list[CycleRecordV0] = field(default_factory=list)
    final_state: str = SessionStateV0.CREATED.value
    orders_created: bool = False
    orders_submitted: bool = False
    network_runtime_used: bool = False
    scheduler_activated: bool = False
    runtime_activated: bool = False
    capital_changed: bool = False
    step_29u_implemented: bool = True
    step_29u_bound_offline: bool = True
    step_29u_verified_offline: bool = False
    step_29u_activated: bool = False
    evidence_dir: str | None = None
    evidence_manifest_sha256: str | None = None
    schema_id: str = SCHEMA_ID
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_result": self.capability_result,
            "failure_class": self.failure_class,
            "reason_codes": list(self.reason_codes),
            "identity": self.identity,
            "session_id": self.session_id,
            "lifecycle_owner": self.lifecycle_owner,
            "lifecycle_transitions": [asdict(t) for t in self.lifecycle_transitions],
            "cycles": [
                {
                    "cycle_index": c.cycle_index,
                    "decision_result": c.decision_result,
                    "direction": c.direction,
                    "decision_reason_codes": list(c.decision_reason_codes),
                    "risk_sizing_result": c.risk_sizing_result,
                    "execution_intent_result": c.execution_intent_result,
                    "reconciliation_audit_result": c.reconciliation_audit_result,
                    "terminal_status": c.terminal_status,
                    "cycle_payload": c.cycle_payload,
                }
                for c in self.cycles
            ],
            "final_state": self.final_state,
            "orders_created": self.orders_created,
            "orders_submitted": self.orders_submitted,
            "network_runtime_used": self.network_runtime_used,
            "scheduler_activated": self.scheduler_activated,
            "runtime_activated": self.runtime_activated,
            "capital_changed": self.capital_changed,
            "step_29u_implemented": self.step_29u_implemented,
            "step_29u_bound_offline": self.step_29u_bound_offline,
            "step_29u_verified_offline": self.step_29u_verified_offline,
            "step_29u_activated": self.step_29u_activated,
            "evidence_dir": self.evidence_dir,
            "evidence_manifest_sha256": self.evidence_manifest_sha256,
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "canonical_step_29u_absent_activation_prerequisite": (
                "OPEN_INTENTIONAL_ACTIVATION_PREREQUISITE"
            ),
            "activation_authorized": False,
        }


def build_mode_identity_v0(
    *,
    instrument_id: str,
    source_git_sha: str,
    effective_at: str = "1970-01-01T00:00:00Z",
) -> Step29UModeIdentityV0:
    return Step29UModeIdentityV0(
        capability_id=CAPABILITY_ID,
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        canonical_step_29u_reference=CANONICAL_STEP_29U_REFERENCE,
        mode=REQUIRED_MODE,
        venue=REQUIRED_VENUE,
        instrument_class=REQUIRED_INSTRUMENT_CLASS,
        instrument_id=instrument_id,
        btc_excluded=True,
        spot_excluded=True,
        orders_allowed=False,
        network_runtime_allowed=False,
        scheduler_allowed=False,
        runtime_activation_allowed=False,
        source_git_sha=source_git_sha,
        effective_at=effective_at,
    )


def validate_mode_identity_v0(identity: Step29UModeIdentityV0) -> tuple[str, ...]:
    reasons: list[str] = []
    if identity.capability_id != CAPABILITY_ID:
        reasons.append("IDENTITY_CAPABILITY_ID_MISMATCH")
    if identity.schema_id != SCHEMA_ID or identity.schema_version != SCHEMA_VERSION:
        reasons.append("IDENTITY_SCHEMA_MISMATCH")
    if identity.mode != REQUIRED_MODE:
        reasons.append("IDENTITY_MODE_INVALID")
    if identity.venue.upper() != REQUIRED_VENUE:
        reasons.append("IDENTITY_VENUE_NOT_OKX")
    if identity.instrument_class != REQUIRED_INSTRUMENT_CLASS:
        reasons.append("IDENTITY_INSTRUMENT_CLASS_INVALID")
    if not identity.btc_excluded:
        reasons.append("IDENTITY_BTC_NOT_EXCLUDED")
    if not identity.spot_excluded:
        reasons.append("IDENTITY_SPOT_NOT_EXCLUDED")
    if identity.orders_allowed:
        reasons.append("IDENTITY_ORDERS_ALLOWED")
    if identity.network_runtime_allowed:
        reasons.append("IDENTITY_NETWORK_RUNTIME_ALLOWED")
    if identity.scheduler_allowed:
        reasons.append("IDENTITY_SCHEDULER_ALLOWED")
    if identity.runtime_activation_allowed:
        reasons.append("IDENTITY_RUNTIME_ACTIVATION_ALLOWED")
    if not identity.source_git_sha or identity.source_git_sha.strip() in {"", "UNKNOWN"}:
        reasons.append("IDENTITY_GIT_SHA_MISSING")
    instr = identity.instrument_id.upper()
    if any(frag in instr for frag in _BITCOIN_FRAGMENTS):
        reasons.append("IDENTITY_BTC_INSTRUMENT")
    if "SPOT" in instr or any(frag in identity.instrument_id for frag in ("/EUR", "/USD")):
        # USDT-perp ids may contain USDT; reject explicit SPOT markers only.
        if "SPOT" in instr:
            reasons.append("IDENTITY_SPOT_INSTRUMENT")
    return tuple(reasons)


def transition_state_v0(
    *,
    current: SessionStateV0,
    target: SessionStateV0,
) -> SessionStateV0:
    if target.name in FORBIDDEN_STATE_NAMES:
        raise Step29UOfflineCapabilityError(
            f"{FailureClassV0.STATE_TRANSITION_INVALID.value}:FORBIDDEN_STATE:{target}"
        )
    allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise Step29UOfflineCapabilityError(
            f"{FailureClassV0.STATE_TRANSITION_INVALID.value}:{current.value}->{target.value}"
        )
    return target


def _classify_cycle_failure(
    cycle: OkxFuturesShadowNoOrderCycleResultV0,
) -> tuple[str, str] | None:
    """Return (failure_class, reason) or None when cycle is acceptable HOLD PASS."""
    if cycle.real_order_submission or cycle.order_capable_client_instantiated:
        return (
            FailureClassV0.EXECUTION_BOUNDARY_VIOLATION.value,
            "ORDER_CAPABLE_PATH",
        )
    if cycle.exchange_order_submission or cycle.testnet_order_submission:
        return (
            FailureClassV0.EXECUTION_BOUNDARY_VIOLATION.value,
            "ORDER_SUBMISSION_CLAIMED",
        )
    if cycle.live_activation or cycle.scheduler:
        return (
            FailureClassV0.EXECUTION_BOUNDARY_VIOLATION.value,
            "ACTIVATION_OR_SCHEDULER_CLAIMED",
        )
    if not cycle.decision_result:
        return FailureClassV0.DECISION_MISSING.value, "DECISION_MISSING"
    if cycle.decision_result.upper() != "HOLD" and cycle.terminal_status == "PASS":
        return FailureClassV0.DECISION_INVALID.value, "NON_HOLD_PASS_UNSUPPORTED"
    if not cycle.risk_sizing_result:
        return FailureClassV0.RISK_MISSING.value, "RISK_MISSING"
    risk = str(cycle.risk_sizing_result).upper()
    if "VETO" in risk or "BLOCK" in risk or risk in {"REJECT", "DENIED"}:
        return FailureClassV0.RISK_BLOCKED.value, f"RISK_BLOCKED:{cycle.risk_sizing_result}"
    if cycle.terminal_status != "PASS":
        if cycle.blockers:
            joined = ",".join(cycle.blockers)
            upper = joined.upper()
            if "BTC" in upper or "BITCOIN" in upper:
                return FailureClassV0.IDENTITY_INVALID.value, joined
            if "SPOT" in upper:
                return FailureClassV0.IDENTITY_INVALID.value, joined
            if "MODE" in upper or "VENUE" in upper or "OKX" in upper:
                return FailureClassV0.IDENTITY_INVALID.value, joined
            if "SCHEDULER" in upper or "DAEMON" in upper or "LIVE" in upper:
                return FailureClassV0.PREREQUISITE_MISSING.value, joined
            if "ORDER" in upper:
                return FailureClassV0.EXECUTION_BOUNDARY_VIOLATION.value, joined
            return FailureClassV0.PREREQUISITE_MISSING.value, joined
        return FailureClassV0.INTERNAL_ERROR.value, f"CYCLE_{cycle.terminal_status}"
    if not cycle.reconciliation_audit_result:
        return FailureClassV0.RECONCILIATION_MISMATCH.value, "RECON_MISSING"
    if cycle.direction.upper() != "HOLD":
        return FailureClassV0.RECONCILIATION_MISMATCH.value, "DIRECTION_NOT_HOLD"
    return None


def resolve_evidence_dir(*, repo_root: Path, output_path: str) -> Path:
    raw = str(output_path or "").strip()
    if not raw:
        raise Step29UOfflineCapabilityError(
            f"{FailureClassV0.EVIDENCE_INVALID.value}:OUTPUT_PATH_EMPTY"
        )
    if raw.startswith("/") or _PATH_ESCAPE.search(raw) or "\\" in raw:
        raise Step29UOfflineCapabilityError(f"{FailureClassV0.EVIDENCE_INVALID.value}:PATH_ESCAPE")
    root = repo_root.resolve()
    dest = (root / raw).resolve()
    try:
        dest.relative_to(root)
    except ValueError as exc:
        raise Step29UOfflineCapabilityError(
            f"{FailureClassV0.EVIDENCE_INVALID.value}:PATH_OUTSIDE_REPO"
        ) from exc
    return dest


def _atomic_write_text(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent, prefix=f".tmp_{path.name}_", suffix=".partial"
    )
    closed = False
    try:
        with os.fdopen(fd, "wb") as handle:
            closed = True
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        raise
    finally:
        if not closed:
            try:
                os.close(fd)
            except OSError:
                pass
    return hashlib.sha256(data).hexdigest()


def _ensure_evidence_dir(*, evidence_dir: Path, overwrite: bool) -> None:
    if evidence_dir.exists() and any(evidence_dir.iterdir()) and not overwrite:
        raise Step29UOfflineCapabilityError(
            f"{FailureClassV0.EVIDENCE_INVALID.value}:EVIDENCE_DIR_NONEMPTY"
        )
    evidence_dir.mkdir(parents=True, exist_ok=True)


def write_capability_evidence_content_v0(
    *,
    result: Step29UOfflineCapabilityResultV0,
    evidence_dir: Path,
    overwrite: bool = False,
) -> dict[str, str]:
    """Persist content artifacts only (no manifest)."""
    _ensure_evidence_dir(evidence_dir=evidence_dir, overwrite=overwrite)
    payload = result.to_dict()
    artifacts: dict[str, str] = {
        "capability_result.json": _atomic_write_text(
            evidence_dir / "capability_result.json",
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
        ),
        "mode_identity.json": _atomic_write_text(
            evidence_dir / "mode_identity.json",
            json.dumps(result.identity, indent=2, sort_keys=True) + "\n",
        ),
        "lifecycle_transitions.json": _atomic_write_text(
            evidence_dir / "lifecycle_transitions.json",
            json.dumps([asdict(t) for t in result.lifecycle_transitions], indent=2) + "\n",
        ),
        "cycles.json": _atomic_write_text(
            evidence_dir / "cycles.json",
            json.dumps(payload["cycles"], indent=2, sort_keys=True) + "\n",
        ),
    }
    return artifacts


def write_capability_evidence_manifest_v0(
    *,
    evidence_dir: Path,
    artifacts: Mapping[str, str],
) -> str:
    """Write digest manifest only after all final content files exist."""
    manifest_lines = [f"{digest}  {name}" for name, digest in sorted(artifacts.items())]
    manifest_text = "\n".join(manifest_lines) + "\n"
    _atomic_write_text(evidence_dir / "evidence_manifest.sha256", manifest_text)
    return hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()


def write_capability_evidence_v0(
    *,
    result: Step29UOfflineCapabilityResultV0,
    evidence_dir: Path,
    overwrite: bool = False,
) -> str:
    """Write final content artifacts then regenerate the digest manifest."""
    artifacts = write_capability_evidence_content_v0(
        result=result,
        evidence_dir=evidence_dir,
        overwrite=overwrite,
    )
    return write_capability_evidence_manifest_v0(
        evidence_dir=evidence_dir,
        artifacts=artifacts,
    )


def verify_capability_evidence_v0(*, evidence_dir: Path) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    manifest_path = evidence_dir / "evidence_manifest.sha256"
    result_path = evidence_dir / "capability_result.json"
    if not manifest_path.is_file():
        return False, (FailureClassV0.EVIDENCE_INVALID.value, "MANIFEST_MISSING")
    if not result_path.is_file():
        return False, (FailureClassV0.EVIDENCE_INVALID.value, "RESULT_MISSING")
    try:
        payload = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, (FailureClassV0.EVIDENCE_INVALID.value, "RESULT_MALFORMED")
    if payload.get("schema_id") != SCHEMA_ID:
        reasons.append("SCHEMA_ID_MISMATCH")
    if payload.get("step_29u_activated") is True:
        reasons.append("ACTIVATION_CLAIMED")
    if payload.get("orders_submitted") is True or payload.get("orders_created") is True:
        reasons.append("ORDERS_CLAIMED")
    if payload.get("runtime_activated") is True or payload.get("scheduler_activated") is True:
        reasons.append("RUNTIME_OR_SCHEDULER_CLAIMED")
    # PASS must never coexist with unverified or contradictory verified claims on disk.
    if payload.get("capability_result") == RESULT_PASS:
        if payload.get("step_29u_verified_offline") is not True:
            reasons.append("PASS_WITHOUT_VERIFIED_OFFLINE")
        if payload.get("step_29u_implemented") is not True:
            reasons.append("PASS_WITHOUT_IMPLEMENTED")
        if payload.get("step_29u_bound_offline") is not True:
            reasons.append("PASS_WITHOUT_BOUND_OFFLINE")
        if payload.get("step_29u_activated") is True:
            reasons.append("PASS_WITH_ACTIVATED")
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 2:
            reasons.append("MANIFEST_LINE_INVALID")
            continue
        expected, name = parts[0], parts[1]
        path = evidence_dir / name
        if not path.is_file():
            reasons.append(f"ARTIFACT_MISSING:{name}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            reasons.append(f"DIGEST_MISMATCH:{name}")
    return (not reasons), tuple(reasons)


def run_step_29u_offline_capability_v0(
    *,
    repo_root: Path,
    source_git_sha: str,
    cycle_count: int = 1,
    instrument_id: str | None = None,
    output_path: str | None = None,
    overwrite_evidence: bool = False,
    cycle_runner: Callable[..., OkxFuturesShadowNoOrderCycleResultV0] | None = None,
    live_enabled: bool = False,
    order_submission_enabled: bool = False,
    testnet_order_submission_enabled: bool = False,
    capital_change_enabled: bool = False,
    scheduler_enabled: bool = False,
    daemon_enabled: bool = False,
    network_runtime_enabled: bool = False,
    runtime_activation_enabled: bool = False,
    venue: str = REQUIRED_VENUE,
    identity_overrides: Mapping[str, Any] | None = None,
    ephemeral_pass_when_preverified: bool = False,
) -> Step29UOfflineCapabilityResultV0:
    """Single lifecycle owner: validate → bounded cycles → reconcile → evidence."""
    if cycle_count < 1:
        raise Step29UOfflineCapabilityError(
            f"{FailureClassV0.PREREQUISITE_MISSING.value}:CYCLE_COUNT_REQUIRED"
        )
    if cycle_count > 64:
        raise Step29UOfflineCapabilityError(
            f"{FailureClassV0.PREREQUISITE_MISSING.value}:CYCLE_COUNT_UNBOUNDED"
        )

    selected = (
        PRODUCTION_INSTRUMENT_ID
        if instrument_id is None or not str(instrument_id).strip()
        else str(instrument_id).strip()
    )
    session_id = f"step29u-offline-{source_git_sha[:12]}-{cycle_count}"
    identity = build_mode_identity_v0(instrument_id=selected, source_git_sha=source_git_sha)
    if identity_overrides:
        data = identity.to_dict()
        data.update(dict(identity_overrides))
        identity = Step29UModeIdentityV0(**data)

    result = Step29UOfflineCapabilityResultV0(
        capability_result=RESULT_ERROR,
        failure_class=None,
        reason_codes=(),
        identity=identity.to_dict(),
        session_id=session_id,
        lifecycle_owner=LIFECYCLE_OWNER,
    )
    state = SessionStateV0.CREATED

    def _record(to: SessionStateV0, reason: str) -> None:
        nonlocal state
        prev = state
        state = transition_state_v0(current=state, target=to)
        result.lifecycle_transitions.append(
            LifecycleTransitionV0(from_state=prev.value, to_state=to.value, reason=reason)
        )
        result.final_state = state.value

    def _finish(
        capability_result: str,
        *,
        failure_class: str | None,
        reasons: tuple[str, ...],
        terminal: SessionStateV0,
        terminal_reason: str,
    ) -> Step29UOfflineCapabilityResultV0:
        if state not in {SessionStateV0.BLOCKED, SessionStateV0.ERROR, SessionStateV0.COMPLETED}:
            try:
                _record(terminal, terminal_reason)
            except Step29UOfflineCapabilityError as exc:
                result.capability_result = RESULT_ERROR
                result.failure_class = FailureClassV0.STATE_TRANSITION_INVALID.value
                result.reason_codes = (str(exc),)
                result.final_state = SessionStateV0.ERROR.value
                return result
        result.capability_result = capability_result
        result.failure_class = failure_class
        result.reason_codes = reasons
        result.step_29u_verified_offline = False
        if output_path:
            try:
                evidence_dir = resolve_evidence_dir(repo_root=repo_root, output_path=output_path)
                result.evidence_dir = str(evidence_dir.relative_to(repo_root.resolve()))
                # 1) Persist content with verified_offline=false (provisional for PASS).
                artifacts = write_capability_evidence_content_v0(
                    result=result,
                    evidence_dir=evidence_dir,
                    overwrite=overwrite_evidence,
                )
                # 2) For PASS, set verified only after content exists, rewrite result,
                #    then generate the manifest from final digests and verify on disk.
                if capability_result == RESULT_PASS:
                    result.step_29u_verified_offline = True
                    artifacts = write_capability_evidence_content_v0(
                        result=result,
                        evidence_dir=evidence_dir,
                        overwrite=True,
                    )
                manifest_sha = write_capability_evidence_manifest_v0(
                    evidence_dir=evidence_dir,
                    artifacts=artifacts,
                )
                result.evidence_manifest_sha256 = manifest_sha
                ok, verify_reasons = verify_capability_evidence_v0(evidence_dir=evidence_dir)
                if not ok:
                    # Fail closed: never leave PASS+verified contradiction on disk.
                    result.capability_result = RESULT_ERROR
                    result.failure_class = FailureClassV0.EVIDENCE_INVALID.value
                    result.reason_codes = tuple([*result.reason_codes, *verify_reasons])
                    result.final_state = SessionStateV0.ERROR.value
                    result.step_29u_verified_offline = False
                    artifacts = write_capability_evidence_content_v0(
                        result=result,
                        evidence_dir=evidence_dir,
                        overwrite=True,
                    )
                    result.evidence_manifest_sha256 = write_capability_evidence_manifest_v0(
                        evidence_dir=evidence_dir,
                        artifacts=artifacts,
                    )
            except Step29UOfflineCapabilityError as exc:
                result.capability_result = RESULT_ERROR
                result.failure_class = FailureClassV0.EVIDENCE_INVALID.value
                result.reason_codes = (*result.reason_codes, str(exc))
                result.final_state = SessionStateV0.ERROR.value
                result.step_29u_verified_offline = False
        elif capability_result == RESULT_PASS:
            if ephemeral_pass_when_preverified:
                # Canonical evidence already verified by the shadow binding owner.
                result.capability_result = RESULT_PASS
                result.failure_class = failure_class
                result.reason_codes = reasons
                result.step_29u_verified_offline = True
                return result
            # PASS requires finalized verified evidence.
            result.capability_result = RESULT_ERROR
            result.failure_class = FailureClassV0.EVIDENCE_INVALID.value
            result.reason_codes = (*reasons, "EVIDENCE_OUTPUT_PATH_REQUIRED_FOR_PASS")
            result.final_state = SessionStateV0.ERROR.value
            result.step_29u_verified_offline = False
        return result

    try:
        _record(SessionStateV0.VALIDATING, "start_validation")
    except Step29UOfflineCapabilityError as exc:
        result.capability_result = RESULT_ERROR
        result.failure_class = FailureClassV0.STATE_TRANSITION_INVALID.value
        result.reason_codes = (str(exc),)
        result.final_state = SessionStateV0.ERROR.value
        return result

    if venue.upper() != REQUIRED_VENUE:
        return _finish(
            RESULT_BLOCKED,
            failure_class=FailureClassV0.IDENTITY_INVALID.value,
            reasons=("VENUE_NOT_OKX",),
            terminal=SessionStateV0.BLOCKED,
            terminal_reason="venue_rejected",
        )
    if network_runtime_enabled:
        return _finish(
            RESULT_BLOCKED,
            failure_class=FailureClassV0.PREREQUISITE_MISSING.value,
            reasons=("NETWORK_RUNTIME_ENABLED",),
            terminal=SessionStateV0.BLOCKED,
            terminal_reason="network_rejected",
        )
    if runtime_activation_enabled or live_enabled:
        return _finish(
            RESULT_BLOCKED,
            failure_class=FailureClassV0.PREREQUISITE_MISSING.value,
            reasons=("RUNTIME_ACTIVATION_ENABLED",),
            terminal=SessionStateV0.BLOCKED,
            terminal_reason="activation_rejected",
        )
    if scheduler_enabled or daemon_enabled:
        return _finish(
            RESULT_BLOCKED,
            failure_class=FailureClassV0.PREREQUISITE_MISSING.value,
            reasons=("SCHEDULER_OR_DAEMON_ENABLED",),
            terminal=SessionStateV0.BLOCKED,
            terminal_reason="scheduler_rejected",
        )
    if order_submission_enabled or testnet_order_submission_enabled:
        return _finish(
            RESULT_BLOCKED,
            failure_class=FailureClassV0.EXECUTION_BOUNDARY_VIOLATION.value,
            reasons=("ORDER_SUBMISSION_ENABLED",),
            terminal=SessionStateV0.BLOCKED,
            terminal_reason="orders_rejected",
        )
    if capital_change_enabled:
        return _finish(
            RESULT_BLOCKED,
            failure_class=FailureClassV0.PREREQUISITE_MISSING.value,
            reasons=("CAPITAL_CHANGE_ENABLED",),
            terminal=SessionStateV0.BLOCKED,
            terminal_reason="capital_rejected",
        )

    identity_reasons = validate_mode_identity_v0(identity)
    if identity_reasons:
        return _finish(
            RESULT_BLOCKED,
            failure_class=FailureClassV0.IDENTITY_INVALID.value,
            reasons=identity_reasons,
            terminal=SessionStateV0.BLOCKED,
            terminal_reason="identity_invalid",
        )

    _record(SessionStateV0.READY, "identity_valid")
    runner = cycle_runner or run_okx_futures_shadow_no_order_cycle_core_v0
    _record(SessionStateV0.RUNNING, f"start_cycles:{cycle_count}")

    for idx in range(cycle_count):
        try:
            cycle = runner(
                mode="shadow",
                instrument_id=selected,
                live_enabled=False,
                order_submission_enabled=False,
                testnet_order_submission_enabled=False,
                capital_change_enabled=False,
                scheduler_enabled=False,
                daemon_enabled=False,
            )
        except Exception as exc:  # noqa: BLE001 — fail-closed capability boundary
            return _finish(
                RESULT_ERROR,
                failure_class=FailureClassV0.INTERNAL_ERROR.value,
                reasons=(f"CYCLE_RUNNER_EXCEPTION:{exc}",),
                terminal=SessionStateV0.ERROR,
                terminal_reason="cycle_exception",
            )
        if cycle is None:
            return _finish(
                RESULT_ERROR,
                failure_class=FailureClassV0.DECISION_MISSING.value,
                reasons=("CYCLE_RESULT_MISSING",),
                terminal=SessionStateV0.ERROR,
                terminal_reason="cycle_missing",
            )
        classified = _classify_cycle_failure(cycle)
        record = CycleRecordV0(
            cycle_index=idx + 1,
            decision_result=str(cycle.decision_result),
            direction=str(cycle.direction),
            decision_reason_codes=tuple(cycle.reason_codes),
            risk_sizing_result=str(cycle.risk_sizing_result),
            execution_intent_result=str(cycle.execution_intent_result),
            reconciliation_audit_result=str(cycle.reconciliation_audit_result),
            terminal_status=str(cycle.terminal_status),
            cycle_payload=serialize_okx_futures_shadow_no_order_cycle_result_v0(cycle),
        )
        result.cycles.append(record)
        if classified is not None:
            failure_class, reason = classified
            blocked = failure_class != FailureClassV0.INTERNAL_ERROR.value
            return _finish(
                RESULT_BLOCKED if blocked else RESULT_ERROR,
                failure_class=failure_class,
                reasons=(reason,),
                terminal=SessionStateV0.BLOCKED if blocked else SessionStateV0.ERROR,
                terminal_reason=reason,
            )

    _record(SessionStateV0.RECONCILING, "reconcile_cycles")
    if not result.cycles:
        return _finish(
            RESULT_ERROR,
            failure_class=FailureClassV0.RECONCILIATION_MISMATCH.value,
            reasons=("NO_CYCLES",),
            terminal=SessionStateV0.ERROR,
            terminal_reason="no_cycles",
        )
    for cycle_rec in result.cycles:
        payload = cycle_rec.cycle_payload
        if payload.get("decision_result") != cycle_rec.decision_result:
            return _finish(
                RESULT_ERROR,
                failure_class=FailureClassV0.RECONCILIATION_MISMATCH.value,
                reasons=("DECISION_PROVENANCE_MISMATCH",),
                terminal=SessionStateV0.ERROR,
                terminal_reason="recon_mismatch",
            )
        if payload.get("risk_sizing_result") != cycle_rec.risk_sizing_result:
            return _finish(
                RESULT_ERROR,
                failure_class=FailureClassV0.RECONCILIATION_MISMATCH.value,
                reasons=("RISK_PROVENANCE_MISMATCH",),
                terminal=SessionStateV0.ERROR,
                terminal_reason="recon_mismatch",
            )
        if str(payload.get("direction", "")).upper() != "HOLD":
            return _finish(
                RESULT_ERROR,
                failure_class=FailureClassV0.RECONCILIATION_MISMATCH.value,
                reasons=("HOLD_MISMATCH",),
                terminal=SessionStateV0.ERROR,
                terminal_reason="recon_mismatch",
            )

    _record(SessionStateV0.COMPLETED, "cycles_reconciled")
    return _finish(
        RESULT_PASS,
        failure_class=None,
        reasons=("BOUNDED_HOLD_CYCLES_COMPLETE",),
        terminal=SessionStateV0.COMPLETED,
        terminal_reason="already_completed",
    )


def result_to_machine_lines(result: Step29UOfflineCapabilityResultV0) -> list[str]:
    data = result.to_dict()
    lines: list[str] = []
    for key in (
        "capability_result",
        "failure_class",
        "final_state",
        "session_id",
        "lifecycle_owner",
        "orders_created",
        "orders_submitted",
        "network_runtime_used",
        "scheduler_activated",
        "runtime_activated",
        "step_29u_implemented",
        "step_29u_bound_offline",
        "step_29u_verified_offline",
        "step_29u_activated",
        "evidence_dir",
        "evidence_manifest_sha256",
    ):
        value = data.get(key)
        if isinstance(value, bool):
            rendered = str(value).lower()
        elif value is None:
            rendered = ""
        else:
            rendered = str(value)
        lines.append(f"{key.upper()}={rendered}")
    lines.append(f"CYCLE_COUNT={len(result.cycles)}")
    lines.append(
        "REASON_CODES=[" + ",".join(result.reason_codes) + "]"
        if result.reason_codes
        else "REASON_CODES=[]"
    )
    return lines


__all__ = [
    "PACKAGE_MARKER",
    "PRODUCER_FAMILY",
    "SCHEMA_ID",
    "SCHEMA_VERSION",
    "CAPABILITY_ID",
    "LIFECYCLE_OWNER",
    "CLI_RELPATH",
    "RESULT_PASS",
    "RESULT_BLOCKED",
    "RESULT_ERROR",
    "FailureClassV0",
    "SessionStateV0",
    "ALLOWED_TRANSITIONS",
    "FORBIDDEN_STATE_NAMES",
    "FORBIDDEN_IMPORT_SURFACES",
    "Step29UOfflineCapabilityError",
    "Step29UModeIdentityV0",
    "Step29UOfflineCapabilityResultV0",
    "build_mode_identity_v0",
    "validate_mode_identity_v0",
    "transition_state_v0",
    "resolve_evidence_dir",
    "write_capability_evidence_v0",
    "write_capability_evidence_content_v0",
    "write_capability_evidence_manifest_v0",
    "verify_capability_evidence_v0",
    "run_step_29u_offline_capability_v0",
    "result_to_machine_lines",
]
