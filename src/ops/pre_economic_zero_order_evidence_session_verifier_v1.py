"""Read-only verifier for Pre-Economic Zero-Order Evidence session artifacts v1.

Capability: PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_IMPLEMENTATION_READINESS_V1

Consumes evidence roots produced by the session runner. Never executes a
session, never grants Economic / Shadow / Runtime authority, and never treats
dry-run implementation evidence as an authorized 6h session.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.pre_economic_zero_order_evidence_session_contract_v1 import (
    REQUIRED_DECISION_LOGIC_BINDINGS,
    evaluate_pre_economic_zero_order_evidence_session_contract_v1,
    PreEconomicZeroOrderEvidenceSessionOverridesV1,
)
from src.ops.pre_economic_zero_order_evidence_session_runner_v1 import (
    CAPABILITY_ID,
    CONTRACT_VERSION,
    EVIDENCE_SCHEMA_VERSION,
    PACKAGE_MARKER,
    PRODUCTION_SESSION_DURATION_SECONDS,
    RUNTIME_AUTHORITY_NONE,
    SCHEMA_ID,
    SCHEMA_VERSION,
    SESSION_CONTRACT_ID,
    TelemetryState,
    load_session_config_v1,
)

PRODUCER_FAMILY = "ops.pre_economic_zero_order_evidence_session_verifier_v1"
VERIFIER_SCHEMA_ID = PRODUCER_FAMILY
VERIFIER_SCHEMA_VERSION = "v1"

RESULT_IMPLEMENTATION_READINESS_PASS = "IMPLEMENTATION_READINESS_PASS"
RESULT_IMPLEMENTATION_READINESS_BLOCKED = "IMPLEMENTATION_READINESS_BLOCKED"
RESULT_SESSION_EVIDENCE_VALID = "SESSION_EVIDENCE_VALID"
RESULT_SESSION_EVIDENCE_INVALID = "SESSION_EVIDENCE_INVALID"
RESULT_SESSION_EVIDENCE_INCOMPLETE = "SESSION_EVIDENCE_INCOMPLETE"
RESULT_SESSION_NOT_AUTHORIZED = "SESSION_NOT_AUTHORIZED"
RESULT_ECONOMIC_GATE_UNCHANGED = "ECONOMIC_GATE_UNCHANGED"
RESULT_SHADOW_ACTIVATION_INELIGIBLE = "SHADOW_ACTIVATION_INELIGIBLE"

REQUIRED_ARTIFACTS = (
    "session_manifest.json",
    "lifecycle_events.json",
    "heartbeat_summary.json",
    "abort_summary.json",
    "terminal_result.json",
    "integrity_manifest.json",
    "effective_config_snapshot.json",
    "evidence_manifest.sha256",
)


class PreEconomicSessionVerifierError(ValueError):
    """Fail-closed verifier error."""


@dataclass(frozen=True)
class VerificationResultV1:
    schema_id: str
    schema_version: str
    capability_id: str
    session_id: str | None
    implementation_readiness: str
    session_evidence: str
    economic_validity: str
    shadow_activation: str
    consumer_eligibility: bool
    blockers: tuple[str, ...]
    orders_attempted: int
    orders_submitted: int
    zero_order_enforced: bool
    runtime_authority: str
    operator_go_present: bool
    six_hour_session_executed: bool
    session_execution_authorized: bool
    integrity_status: str
    completeness: str
    terminal_state: str | None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreEconomicSessionVerifierError(f"ARTIFACT_UNREADABLE:{path.name}") from exc


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_manifest(text: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 2:
            raise PreEconomicSessionVerifierError("MANIFEST_LINE_INVALID")
        digest, name = parts
        mapping[name] = digest
    return mapping


def verify_session_evidence_root_v1(
    *,
    evidence_root: Path,
    repo_root: Optional[Path] = None,
    expect_authorized_six_hour_session: bool = False,
) -> VerificationResultV1:
    """Verify a session evidence root (read-only).

    ``expect_authorized_six_hour_session`` must remain False for this capability.
    A true value is rejected fail-closed because authorization is out of scope.
    """

    blockers: list[str] = []
    notes: list[str] = [
        RESULT_ECONOMIC_GATE_UNCHANGED,
        RESULT_SHADOW_ACTIVATION_INELIGIBLE,
    ]

    if expect_authorized_six_hour_session:
        blockers.append("AUTHORIZED_SIX_HOUR_EXPECTATION_OUT_OF_SCOPE")

    root = evidence_root
    if not root.exists() or not root.is_dir():
        return VerificationResultV1(
            schema_id=VERIFIER_SCHEMA_ID,
            schema_version=VERIFIER_SCHEMA_VERSION,
            capability_id=CAPABILITY_ID,
            session_id=None,
            implementation_readiness=RESULT_IMPLEMENTATION_READINESS_BLOCKED,
            session_evidence=RESULT_SESSION_EVIDENCE_INCOMPLETE,
            economic_validity=RESULT_ECONOMIC_GATE_UNCHANGED,
            shadow_activation=RESULT_SHADOW_ACTIVATION_INELIGIBLE,
            consumer_eligibility=False,
            blockers=("EVIDENCE_ROOT_MISSING",),
            orders_attempted=0,
            orders_submitted=0,
            zero_order_enforced=True,
            runtime_authority=RUNTIME_AUTHORITY_NONE,
            operator_go_present=False,
            six_hour_session_executed=False,
            session_execution_authorized=False,
            integrity_status="FAIL",
            completeness="INCOMPLETE",
            terminal_state=None,
            notes=tuple(notes),
        )

    missing = [name for name in REQUIRED_ARTIFACTS if not (root / name).is_file()]
    if missing:
        blockers.append("MISSING_ARTIFACTS:" + ",".join(missing))

    session_id: str | None = None
    terminal: dict[str, Any] = {}
    lifecycle: dict[str, Any] = {}
    heartbeat: dict[str, Any] = {}
    abort: dict[str, Any] = {}
    integrity: dict[str, Any] = {}
    manifest_map: dict[str, str] = {}
    identity: dict[str, Any] = {}
    config_snap: dict[str, Any] = {}

    try:
        if (root / "session_manifest.json").is_file():
            identity = _load_json(root / "session_manifest.json")
            if not isinstance(identity, dict):
                blockers.append("SESSION_MANIFEST_NOT_OBJECT")
            else:
                session_id = str(identity.get("session_id") or "") or None
                if identity.get("evidence_schema_version") != EVIDENCE_SCHEMA_VERSION:
                    blockers.append("INCOMPATIBLE_EVIDENCE_SCHEMA_VERSION")
                if identity.get("contract_version") != CONTRACT_VERSION:
                    blockers.append("CONTRACT_VERSION_MISMATCH")
                if identity.get("runtime_authority") != RUNTIME_AUTHORITY_NONE:
                    blockers.append("RUNTIME_AUTHORITY_NOT_NONE")
        if (root / "terminal_result.json").is_file():
            terminal = _load_json(root / "terminal_result.json")
            if not isinstance(terminal, dict):
                blockers.append("TERMINAL_NOT_OBJECT")
                terminal = {}
        if (root / "lifecycle_events.json").is_file():
            lifecycle = _load_json(root / "lifecycle_events.json")
            if not isinstance(lifecycle, dict):
                blockers.append("LIFECYCLE_NOT_OBJECT")
                lifecycle = {}
        if (root / "heartbeat_summary.json").is_file():
            heartbeat = _load_json(root / "heartbeat_summary.json")
            if not isinstance(heartbeat, dict):
                blockers.append("HEARTBEAT_NOT_OBJECT")
                heartbeat = {}
        if (root / "abort_summary.json").is_file():
            abort = _load_json(root / "abort_summary.json")
            if not isinstance(abort, dict):
                blockers.append("ABORT_NOT_OBJECT")
                abort = {}
        if (root / "integrity_manifest.json").is_file():
            integrity = _load_json(root / "integrity_manifest.json")
            if not isinstance(integrity, dict):
                blockers.append("INTEGRITY_MANIFEST_NOT_OBJECT")
                integrity = {}
        if (root / "effective_config_snapshot.json").is_file():
            config_snap = _load_json(root / "effective_config_snapshot.json")
            if not isinstance(config_snap, dict):
                blockers.append("CONFIG_SNAPSHOT_NOT_OBJECT")
                config_snap = {}
        if (root / "evidence_manifest.sha256").is_file():
            manifest_map = _parse_manifest(
                (root / "evidence_manifest.sha256").read_text(encoding="utf-8")
            )
    except PreEconomicSessionVerifierError as exc:
        blockers.append(str(exc))

    # Integrity: every non-manifest artifact digest must match.
    for name, expected in list(manifest_map.items()):
        if name == "evidence_manifest.sha256":
            continue
        path = root / name
        if not path.is_file():
            blockers.append(f"MANIFEST_FILE_MISSING:{name}")
            continue
        actual = _file_sha256(path)
        if actual != expected:
            blockers.append(f"DIGEST_MISMATCH:{name}")

    integrity_files = integrity.get("files") if isinstance(integrity.get("files"), dict) else {}
    for name, expected in integrity_files.items():
        path = root / str(name)
        if not path.is_file():
            blockers.append(f"INTEGRITY_FILE_MISSING:{name}")
            continue
        if _file_sha256(path) != expected:
            blockers.append(f"INTEGRITY_DIGEST_MISMATCH:{name}")

    orders_attempted = int(terminal.get("orders_attempted", 0) or 0)
    orders_submitted = int(terminal.get("orders_submitted", 0) or 0)
    zero_order = bool(terminal.get("zero_order_enforced", False))
    runtime_authority = str(terminal.get("runtime_authority") or "")
    operator_go = bool(terminal.get("operator_go_present", False))
    consumer_eligibility = bool(terminal.get("consumer_eligibility", False))
    terminal_state = terminal.get("terminal_state")
    completeness = str(terminal.get("completeness") or "INCOMPLETE")
    elapsed = float(terminal.get("elapsed_seconds") or 0.0)
    mode = str(terminal.get("mode") or "")

    if session_id and terminal.get("session_id") and terminal.get("session_id") != session_id:
        blockers.append("SESSION_ID_MISMATCH_TERMINAL")
    if session_id and lifecycle.get("session_id") and lifecycle.get("session_id") != session_id:
        blockers.append("SESSION_ID_MISMATCH_LIFECYCLE")
    if session_id and heartbeat.get("session_id") and heartbeat.get("session_id") != session_id:
        blockers.append("SESSION_ID_MISMATCH_HEARTBEAT")
    if session_id and abort.get("session_id") and abort.get("session_id") != session_id:
        blockers.append("SESSION_ID_MISMATCH_ABORT")

    if orders_attempted != 0:
        blockers.append("ORDERS_ATTEMPTED_NONZERO")
    if orders_submitted != 0:
        blockers.append("ORDERS_SUBMITTED_NONZERO")
    if not zero_order:
        blockers.append("ZERO_ORDER_NOT_ENFORCED")
    if runtime_authority != RUNTIME_AUTHORITY_NONE:
        blockers.append("RUNTIME_AUTHORITY_INVALID")
    if consumer_eligibility:
        blockers.append("CONSUMER_ELIGIBILITY_MUST_BE_FALSE")
    if operator_go:
        # This capability's proof path must not claim operator GO for real session.
        blockers.append("OPERATOR_GO_PRESENT_IN_CAPABILITY_EVIDENCE")
    if mode not in {"DRY_RUN_OFFLINE", "UNAUTHORIZED"}:
        blockers.append(f"UNALLOWED_MODE:{mode}")
    if elapsed >= float(PRODUCTION_SESSION_DURATION_SECONDS):
        blockers.append("SIX_HOUR_DURATION_CLAIMED_WITHOUT_AUTHORIZATION")

    events = lifecycle.get("events") if isinstance(lifecycle.get("events"), list) else []
    prev_seq = 0
    prev_elapsed = -1.0
    terminal_seen = False
    for event in events:
        if not isinstance(event, dict):
            blockers.append("LIFECYCLE_EVENT_NOT_OBJECT")
            continue
        seq = int(event.get("sequence") or 0)
        elapsed_e = float(event.get("elapsed_seconds") or 0.0)
        state = str(event.get("state") or "")
        if seq <= prev_seq:
            blockers.append("NON_MONOTONE_SEQUENCE")
        if elapsed_e + 1e-12 < prev_elapsed:
            blockers.append("NON_MONOTONE_TIME")
        if terminal_seen:
            blockers.append("EVENT_AFTER_TERMINAL")
        if state in {
            TelemetryState.ABORTED.value,
            TelemetryState.COMPLETED.value,
            TelemetryState.INVALID.value,
        }:
            if terminal_seen:
                blockers.append("DUPLICATE_TERMINAL_EVENT")
            terminal_seen = True
        prev_seq = seq
        prev_elapsed = elapsed_e

    if not terminal_state:
        blockers.append("MISSING_TERMINAL_STATE")
        completeness = "INCOMPLETE"
    elif str(terminal_state) == TelemetryState.COMPLETED.value and completeness != "COMPLETE":
        blockers.append("COMPLETED_WITHOUT_COMPLETE_FLAG")

    hb_count = int(heartbeat.get("heartbeat_count") or 0)
    if bool(heartbeat.get("stale")):
        blockers.append("HEARTBEAT_STALE")
    if str(terminal_state) == TelemetryState.COMPLETED.value and hb_count <= 0:
        blockers.append("MISSING_HEARTBEATS")

    # Sensitive values must not leak into config snapshot.
    for key in config_snap:
        key_l = str(key).lower()
        if any(frag in key_l for frag in ("secret", "token", "password", "api_key")):
            if config_snap[key] != "[REDACTED]":
                blockers.append(f"SECRET_NOT_REDACTED:{key}")

    if repo_root is not None and config_snap.get("config_path") == (
        "config/ops/pre_economic_zero_order_evidence_session_v1.toml"
    ):
        try:
            cfg = load_session_config_v1(repo_root=repo_root.resolve())
            snap_digest = config_snap.get("config_digest")
            if snap_digest and snap_digest != cfg.config_digest:
                blockers.append("CONFIG_DIGEST_MISMATCH")
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"CONFIG_LOAD_FAILED:{type(exc).__name__}")
    elif repo_root is not None and config_snap.get("config_digest"):
        # Non-canonical / test configs: ensure snapshot is self-consistent only.
        if not isinstance(config_snap.get("config_digest"), str):
            blockers.append("CONFIG_DIGEST_INVALID")

    integrity_status = (
        "PASS"
        if not any(
            b.startswith("DIGEST_MISMATCH")
            or b.startswith("INTEGRITY_DIGEST_MISMATCH")
            or b.startswith("MANIFEST_")
            or b == "MISSING_ARTIFACTS:" + ",".join(missing)
            for b in blockers
            if True
        )
        and not missing
        else "FAIL"
    )
    if any(
        b.startswith("DIGEST_MISMATCH") or b.startswith("INTEGRITY_DIGEST_MISMATCH")
        for b in blockers
    ):
        integrity_status = "FAIL"

    six_hour_executed = bool(terminal.get("six_hour_session_executed", False))
    if six_hour_executed:
        blockers.append("SIX_HOUR_SESSION_EXECUTED_CLAIM_FORBIDDEN")

    session_authorized = bool(terminal.get("session_execution_authorized", False))
    if session_authorized:
        blockers.append("SESSION_EXECUTION_AUTHORIZED_CLAIM_FORBIDDEN")

    # Session evidence classification for this capability:
    # dry-run complete artifacts prove implementation readiness only.
    session_evidence = RESULT_SESSION_NOT_AUTHORIZED
    if missing or not terminal_state:
        session_evidence = RESULT_SESSION_EVIDENCE_INCOMPLETE
    elif integrity_status == "FAIL" or any(
        b.startswith("DIGEST_MISMATCH") or b.startswith("INTEGRITY_") for b in blockers
    ):
        session_evidence = RESULT_SESSION_EVIDENCE_INVALID
    elif str(terminal_state) == TelemetryState.COMPLETED.value and completeness == "COMPLETE":
        # Explicitly NOT RESULT_SESSION_EVIDENCE_VALID for authorized 6h session.
        session_evidence = RESULT_SESSION_NOT_AUTHORIZED
        notes.append("DRY_RUN_COMPLETE_BUT_SESSION_NOT_AUTHORIZED")
    elif str(terminal_state) in {
        TelemetryState.ABORTED.value,
        TelemetryState.INVALID.value,
    }:
        if integrity_status == "FAIL":
            session_evidence = RESULT_SESSION_EVIDENCE_INVALID
        else:
            session_evidence = RESULT_SESSION_NOT_AUTHORIZED
            notes.append(f"ABORT_NOT_SUCCESS:{abort.get('abort_reason')}")

    # Implementation readiness: technical surfaces work under dry-run.
    impl_blockers = [
        b
        for b in blockers
        if b
        not in {
            "OPERATOR_GO_PRESENT_IN_CAPABILITY_EVIDENCE",
        }
    ]
    # Operator GO in evidence blocks readiness for this capability's proof path.
    implementation_readiness = RESULT_IMPLEMENTATION_READINESS_BLOCKED
    if (
        not impl_blockers
        and session_evidence == RESULT_SESSION_NOT_AUTHORIZED
        and str(terminal_state) == TelemetryState.COMPLETED.value
        and completeness == "COMPLETE"
        and integrity_status == "PASS"
        and orders_attempted == 0
        and orders_submitted == 0
        and zero_order
        and runtime_authority == RUNTIME_AUTHORITY_NONE
        and not operator_go
        and not six_hour_executed
        and not session_authorized
        and mode == "DRY_RUN_OFFLINE"
        and hb_count > 0
    ):
        implementation_readiness = RESULT_IMPLEMENTATION_READINESS_PASS
    else:
        if not blockers:
            blockers.append("IMPLEMENTATION_READINESS_CONDITIONS_UNMET")

    # Never emit SESSION_EVIDENCE_VALID from this capability verifier.
    if session_evidence == RESULT_SESSION_EVIDENCE_VALID:
        session_evidence = RESULT_SESSION_NOT_AUTHORIZED
        blockers.append("SESSION_EVIDENCE_VALID_SUPPRESSED")

    return VerificationResultV1(
        schema_id=VERIFIER_SCHEMA_ID,
        schema_version=VERIFIER_SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        session_id=session_id,
        implementation_readiness=implementation_readiness,
        session_evidence=session_evidence,
        economic_validity=RESULT_ECONOMIC_GATE_UNCHANGED,
        shadow_activation=RESULT_SHADOW_ACTIVATION_INELIGIBLE,
        consumer_eligibility=False,
        blockers=tuple(dict.fromkeys(blockers)),
        orders_attempted=orders_attempted,
        orders_submitted=orders_submitted,
        zero_order_enforced=zero_order,
        runtime_authority=runtime_authority or RUNTIME_AUTHORITY_NONE,
        operator_go_present=operator_go,
        six_hour_session_executed=False,
        session_execution_authorized=False,
        integrity_status=integrity_status,
        completeness=completeness,
        terminal_state=str(terminal_state) if terminal_state else None,
        notes=tuple(notes),
    )


def evaluate_implementation_readiness_binding_v1(
    *,
    repo_root: Path,
    evidence_root: Optional[Path] = None,
) -> dict[str, Any]:
    """Bind implementation readiness into the existing session contract surface.

    Implementation readiness may PASS. Session remains NOT_AUTHORIZED.
    Economic gate and Shadow activation remain unchanged / ineligible.
    """

    verification: VerificationResultV1 | None = None
    if evidence_root is not None:
        verification = verify_session_evidence_root_v1(
            evidence_root=evidence_root,
            repo_root=repo_root,
            expect_authorized_six_hour_session=False,
        )
        impl_pass = verification.implementation_readiness == RESULT_IMPLEMENTATION_READINESS_PASS
    else:
        # Structural readiness: config + modules importable, no session evidence yet.
        cfg = load_session_config_v1(repo_root=repo_root)
        impl_pass = (
            cfg.capability_id == CAPABILITY_ID
            and cfg.session_execution_authorized is False
            and cfg.zero_order_enforced is True
            and cfg.runtime_authority == RUNTIME_AUTHORITY_NONE
            and cfg.dry_run is True
        )
        # Without evidence, readiness of *implementation surfaces* can still be
        # asserted only after a successful dry-run verification. Structural probe
        # alone remains BLOCKED for IMPLEMENTATION_READINESS_PASS.
        impl_pass = False

    bindings = {k: True for k in REQUIRED_DECISION_LOGIC_BINDINGS}
    contract = evaluate_pre_economic_zero_order_evidence_session_contract_v1(
        overrides=PreEconomicZeroOrderEvidenceSessionOverridesV1(
            operator_go_present=False,
            decision_logic_bound=bindings,
            implementation_readiness_passed=bool(
                verification
                and verification.implementation_readiness == RESULT_IMPLEMENTATION_READINESS_PASS
            ),
            requested_duration_seconds=PRODUCTION_SESSION_DURATION_SECONDS,
        )
    )

    return {
        "package_marker": PACKAGE_MARKER,
        "capability_id": CAPABILITY_ID,
        "session_contract_id": SESSION_CONTRACT_ID,
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "implementation_readiness": (
            RESULT_IMPLEMENTATION_READINESS_PASS
            if verification
            and verification.implementation_readiness == RESULT_IMPLEMENTATION_READINESS_PASS
            else RESULT_IMPLEMENTATION_READINESS_BLOCKED
        ),
        "session_evidence": (
            verification.session_evidence if verification else RESULT_SESSION_NOT_AUTHORIZED
        ),
        "session_evidence_absent_without_root": evidence_root is None,
        "economic_validity": RESULT_ECONOMIC_GATE_UNCHANGED,
        "shadow_activation": RESULT_SHADOW_ACTIVATION_INELIGIBLE,
        "consumer_eligibility": False,
        "six_hour_session_ready": False,
        "session_admissible": False,
        "contract_six_hour_session_ready": contract.six_hour_session_ready,
        "contract_blockers": list(contract.blockers),
        "verification": verification.to_dict() if verification else None,
        "orders_allowed": False,
        "runtime_authority": RUNTIME_AUTHORITY_NONE,
        "session_execution_authorized": False,
        "six_hour_session_executed": False,
        "structural_probe_impl_pass_suppressed": True,
        "notes": [
            "IMPLEMENTATION_READINESS_REQUIRES_VALID_DRY_RUN_EVIDENCE",
            "SESSION_EVIDENCE_REMAINS_NOT_AUTHORIZED",
            "ECONOMIC_GATE_UNCHANGED",
            "SHADOW_ACTIVATION_INELIGIBLE",
            "EXPLICIT_OPERATOR_GO_STILL_REQUIRED_FOR_REAL_SESSION",
        ],
    }
