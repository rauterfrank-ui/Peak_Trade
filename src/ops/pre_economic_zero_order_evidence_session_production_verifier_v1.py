"""Production verifier for Pre-Economic Zero-Order Evidence session v1.

Only this verifier may emit SESSION_EVIDENCE_VALID.
Fail-closed. Never grants Economic/Shadow/Paper/Testnet/Live/Order authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.pre_economic_zero_order_evidence_session_authorization_v1 import (
    CAPABILITY_ID,
    PRODUCTION_SESSION_DURATION_SECONDS,
    VENUE_OKX,
    ALLOWED_MARKET_TYPES,
    assert_instrument_allowed,
    AuthorizationContractError,
)

PACKAGE_MARKER = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_PRODUCTION_VERIFIER_V1=true"
RESULT_SESSION_EVIDENCE_VALID = "SESSION_EVIDENCE_VALID"
RESULT_SESSION_EVIDENCE_INVALID = "SESSION_EVIDENCE_INVALID"
RESULT_SESSION_EVIDENCE_INCOMPLETE = "SESSION_EVIDENCE_INCOMPLETE"
RESULT_SESSION_NOT_AUTHORIZED = "SESSION_NOT_AUTHORIZED"

REQUIRED_ARTIFACTS = (
    "session_manifest.json",
    "terminal_result.json",
    "lifecycle_events.json",
    "authorization_binding.json",
    "safety_preflight.json",
    "telemetry_summary.json",
    "integrity_manifest.json",
    "evidence_manifest.sha256",
    "closeout.json",
)


@dataclass
class ProductionVerificationResultV1:
    session_evidence: str
    session_evidence_valid: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    economic_validity: str = "ECONOMIC_GATE_UNCHANGED"
    shadow_activation: str = "SHADOW_ACTIVATION_INELIGIBLE"
    consumer_eligibility: bool = False
    orders_allowed: bool = False
    runtime_authority: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_production_evidence_root_v1(
    *,
    evidence_root: Path,
    expected_config_digest: Optional[str] = None,
    expected_revision_sha: Optional[str] = None,
    expected_authorization_id: Optional[str] = None,
    max_clock_drift_seconds: float = 30.0,
    allow_synthetic: bool = False,
) -> ProductionVerificationResultV1:
    blockers: list[str] = []
    notes = [
        "PRODUCTION_VERIFIER_ONLY_MAY_SET_SESSION_EVIDENCE_VALID",
        "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false",
        "SHADOW_ACTIVATION_AUTHORIZED=false",
        "ORDERS=false",
        "DOWNSTREAM_GATES_REMAIN_BLOCKED",
    ]

    if not evidence_root.is_dir():
        return ProductionVerificationResultV1(
            session_evidence=RESULT_SESSION_EVIDENCE_INVALID,
            session_evidence_valid=False,
            blockers=["EVIDENCE_ROOT_MISSING"],
            notes=notes,
        )

    missing = [name for name in REQUIRED_ARTIFACTS if not (evidence_root / name).is_file()]
    if missing:
        blockers.append("MISSING_ARTIFACTS:" + ",".join(missing))

    terminal: dict[str, Any] = {}
    manifest: dict[str, Any] = {}
    telemetry: dict[str, Any] = {}
    safety: dict[str, Any] = {}
    auth_binding: dict[str, Any] = {}
    closeout: dict[str, Any] = {}

    try:
        if (evidence_root / "terminal_result.json").is_file():
            terminal = _load_json(evidence_root / "terminal_result.json")
        if (evidence_root / "session_manifest.json").is_file():
            manifest = _load_json(evidence_root / "session_manifest.json")
        if (evidence_root / "telemetry_summary.json").is_file():
            telemetry = _load_json(evidence_root / "telemetry_summary.json")
        if (evidence_root / "safety_preflight.json").is_file():
            safety = _load_json(evidence_root / "safety_preflight.json")
        if (evidence_root / "authorization_binding.json").is_file():
            auth_binding = _load_json(evidence_root / "authorization_binding.json")
        if (evidence_root / "closeout.json").is_file():
            closeout = _load_json(evidence_root / "closeout.json")
    except json.JSONDecodeError as exc:
        blockers.append(f"JSON_PARSE_ERROR:{exc}")

    # Integrity manifest check.
    manifest_path = evidence_root / "evidence_manifest.sha256"
    if manifest_path.is_file():
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                blockers.append("MANIFEST_LINE_INVALID")
                continue
            digest, name = parts[0], parts[1]
            if name == "evidence_manifest.sha256":
                continue
            target = evidence_root / name
            if not target.is_file():
                blockers.append(f"MANIFEST_MISSING_FILE:{name}")
                continue
            if _file_digest(target) != digest:
                blockers.append(f"DIGEST_MISMATCH:{name}")

    if bool(manifest.get("synthetic")) and not allow_synthetic:
        blockers.append("SYNTHETIC_EVIDENCE_FORBIDDEN")
    if bool(manifest.get("replayed")) or bool(terminal.get("replayed")):
        blockers.append("REPLAYED_EVIDENCE_FORBIDDEN")

    if str(manifest.get("capability_id") or terminal.get("capability_id") or "") != CAPABILITY_ID:
        blockers.append("CAPABILITY_MISMATCH")

    venue = str(terminal.get("venue") or manifest.get("venue") or "")
    market_type = str(terminal.get("market_type") or manifest.get("market_type") or "")
    instrument = str(terminal.get("instrument_id") or manifest.get("instrument_id") or "")
    if venue != VENUE_OKX:
        blockers.append(f"VENUE_FORBIDDEN:{venue}")
    if market_type not in ALLOWED_MARKET_TYPES:
        blockers.append(f"MARKET_TYPE_FORBIDDEN:{market_type}")
    try:
        assert_instrument_allowed(
            instrument_id=instrument,
            allowlist=(instrument,) if instrument else tuple(),
            btc_forbidden=True,
            spot_forbidden=True,
            market_type=market_type or "SWAP",
        )
    except AuthorizationContractError as exc:
        blockers.append(str(exc))

    auth_id = str(auth_binding.get("authorization_id") or terminal.get("authorization_id") or "")
    if not auth_id:
        blockers.append("AUTHORIZATION_ID_ABSENT")
    if expected_authorization_id and auth_id != expected_authorization_id:
        blockers.append("AUTHORIZATION_ID_MISMATCH")
    if not str(
        auth_binding.get("go_token_fingerprint") or terminal.get("go_token_fingerprint") or ""
    ):
        blockers.append("GO_TOKEN_FINGERPRINT_ABSENT")

    cfg_digest = str(terminal.get("config_digest") or manifest.get("config_digest") or "")
    rev = str(terminal.get("revision_sha") or manifest.get("revision_sha") or "")
    if expected_config_digest and cfg_digest != expected_config_digest:
        blockers.append("CONFIG_DIGEST_MISMATCH")
    if expected_revision_sha and rev != expected_revision_sha:
        blockers.append("REVISION_SHA_MISMATCH")

    if int(terminal.get("orders_attempted", 0)) != 0:
        blockers.append("ORDERS_ATTEMPTED_NONZERO")
    if int(terminal.get("orders_submitted", 0)) != 0:
        blockers.append("ORDERS_SUBMITTED_NONZERO")
    if (
        terminal.get("zero_order_only") is not True
        and terminal.get("zero_order_enforced") is not True
    ):
        blockers.append("ZERO_ORDER_NOT_ENFORCED")

    if safety and safety.get("ok") is False:
        blockers.append("SAFETY_PREFLIGHT_FAILED")
    if safety and not safety.get("trading_permissions_absent", True):
        blockers.append("TRADING_PERMISSIONS_PRESENT")

    mono_elapsed = float(terminal.get("mono_elapsed_seconds") or 0.0)
    wall_elapsed = float(terminal.get("wall_elapsed_seconds") or 0.0)
    if mono_elapsed + 1e-9 < float(PRODUCTION_SESSION_DURATION_SECONDS):
        blockers.append("DURATION_BELOW_21600_MONOTONIC")
    if abs(wall_elapsed - mono_elapsed) > float(max_clock_drift_seconds):
        blockers.append("CLOCK_ANOMALY")

    if telemetry.get("unresolved_integrity_violation"):
        blockers.append("TELEMETRY_INTEGRITY_VIOLATION")
    if not telemetry:
        blockers.append("TELEMETRY_SUMMARY_ABSENT")
    snapshots = telemetry.get("snapshots") or []
    if not snapshots:
        blockers.append("TELEMETRY_SNAPSHOTS_ABSENT")

    if closeout.get("atomic_closeout") is not True:
        blockers.append("ATOMIC_CLOSEOUT_MISSING")

    completeness = str(terminal.get("completeness") or "")
    state = str(terminal.get("state") or "")
    if completeness != "COMPLETE" or state != "COMPLETED":
        blockers.append("SESSION_NOT_COMPLETE")

    # Partial-run merge markers
    if terminal.get("merged_partial_runs") or manifest.get("merged_partial_runs"):
        blockers.append("PARTIAL_RUN_MERGE_FORBIDDEN")
    if terminal.get("resumed_without_reauth"):
        blockers.append("RESUME_WITHOUT_REAUTH")

    # Downstream authority must remain blocked on evidence.
    if terminal.get("consumer_eligibility") is True:
        blockers.append("CONSUMER_ELIGIBILITY_CLAIM_FORBIDDEN")
    if terminal.get("shadow_activation_eligible") is True:
        blockers.append("SHADOW_ELIGIBILITY_CLAIM_FORBIDDEN")
    if str(terminal.get("economic_gate_effect") or "NONE") != "NONE":
        blockers.append("ECONOMIC_GATE_EFFECT_CLAIM_FORBIDDEN")
    if terminal.get("session_evidence_valid") is True:
        # Evidence must not self-attest; only this verifier decides.
        blockers.append("SELF_ATTESTED_VALID_FORBIDDEN")

    session_evidence = RESULT_SESSION_EVIDENCE_INVALID
    session_valid = False
    if not blockers and completeness == "COMPLETE":
        session_evidence = RESULT_SESSION_EVIDENCE_VALID
        session_valid = True
    elif "DURATION_BELOW_21600_MONOTONIC" in blockers or completeness == "INCOMPLETE":
        session_evidence = RESULT_SESSION_EVIDENCE_INCOMPLETE
    elif not auth_id:
        session_evidence = RESULT_SESSION_NOT_AUTHORIZED

    return ProductionVerificationResultV1(
        session_evidence=session_evidence,
        session_evidence_valid=session_valid,
        blockers=blockers,
        notes=notes,
        economic_validity="ECONOMIC_GATE_UNCHANGED",
        shadow_activation="SHADOW_ACTIVATION_INELIGIBLE",
        consumer_eligibility=False,
        orders_allowed=False,
        runtime_authority="NONE",
    )
