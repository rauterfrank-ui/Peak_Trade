"""Bundle verifier for Integrated Paper-Shadow Observation evidence v1.

Fail-closed. Never emits synthetic PASS for incomplete/contradictory bundles.
Never grants ECONOMIC_VALIDITY_PASS or session authorization.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.integrated_paper_shadow_observation_session_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
)
from src.ops.integrated_paper_shadow_observation_session_v1.evidence_v1 import (
    EVIDENCE_SCHEMA_ID,
    REQUIRED_EVIDENCE_ARTIFACTS,
)

VERIFIER_ID = "ops.integrated_paper_shadow_observation_bundle_verifier_v1"
RESULT_VERIFIED = "INTEGRATED_PAPER_SHADOW_OBSERVATION_EVIDENCE_VERIFIED"
RESULT_INVALID = "INTEGRATED_PAPER_SHADOW_OBSERVATION_EVIDENCE_INVALID"
RESULT_INCOMPLETE = "INTEGRATED_PAPER_SHADOW_OBSERVATION_EVIDENCE_INCOMPLETE"


@dataclass
class ObservationBundleVerificationResultV1:
    result: str
    verified: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    authority_effect: str = AUTHORITY_EFFECT_NONE
    economic_validity_pass: bool = False
    paper_shadow_observation_authorized: bool = False
    integrated_economic_evidence_bundle_verified: bool = False
    consumer_eligibility: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_integrated_paper_shadow_observation_evidence_bundle_v1(
    *,
    evidence_root: Path,
    allow_synthetic: bool = False,
    require_cycle_pass: bool = True,
) -> ObservationBundleVerificationResultV1:
    notes = [
        "VERIFIER_DOES_NOT_GRANT_AUTHORIZATION",
        "VERIFIER_DOES_NOT_SET_ECONOMIC_VALIDITY_PASS",
        "VERIFIER_REJECTS_SYNTHETIC_PASS",
        f"VERIFIER_ID={VERIFIER_ID}",
        f"CAPABILITY_ID={CAPABILITY_ID}",
    ]
    blockers: list[str] = []
    if allow_synthetic:
        return ObservationBundleVerificationResultV1(
            result=RESULT_INVALID,
            verified=False,
            blockers=["SYNTHETIC_PASS_FORBIDDEN"],
            notes=notes,
        )
    root = evidence_root.resolve()
    if not root.is_dir():
        return ObservationBundleVerificationResultV1(
            result=RESULT_INVALID,
            verified=False,
            blockers=["EVIDENCE_ROOT_MISSING"],
            notes=notes,
        )

    missing = [name for name in REQUIRED_EVIDENCE_ARTIFACTS if not (root / name).is_file()]
    if missing:
        blockers.append("MISSING_ARTIFACTS:" + ",".join(missing))

    # Verify sha256 manifest when present.
    manifest_path = root / "evidence_manifest.sha256"
    if manifest_path.is_file():
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                blockers.append(f"MANIFEST_LINE_MALFORMED:{line}")
                continue
            digest, rel = parts[0], parts[1]
            path = root / rel
            if not path.is_file():
                blockers.append(f"MANIFEST_TARGET_MISSING:{rel}")
                continue
            actual = _file_digest(path)
            if actual != digest:
                blockers.append(f"MANIFEST_DIGEST_MISMATCH:{rel}")

    session: dict[str, Any] = {}
    no_order: dict[str, Any] = {}
    replay: dict[str, Any] = {}
    if (root / "session_manifest.json").is_file():
        try:
            session = _load_json(root / "session_manifest.json")
        except json.JSONDecodeError:
            blockers.append("SESSION_MANIFEST_MALFORMED")
    if (root / "no_order_attestation.json").is_file():
        try:
            no_order = _load_json(root / "no_order_attestation.json")
        except json.JSONDecodeError:
            blockers.append("NO_ORDER_ATTESTATION_MALFORMED")
    if (root / "replay_metadata.json").is_file():
        try:
            replay = _load_json(root / "replay_metadata.json")
        except json.JSONDecodeError:
            blockers.append("REPLAY_METADATA_MALFORMED")

    if session:
        if session.get("schema_id") != EVIDENCE_SCHEMA_ID:
            blockers.append("SESSION_SCHEMA_ID_MISMATCH")
        if session.get("capability_id") != CAPABILITY_ID:
            blockers.append("SESSION_CAPABILITY_MISMATCH")
        if session.get("paper_shadow_observation_authorized") is True:
            blockers.append("UNAUTHORIZED_AUTHORIZATION_CLAIM")
        if session.get("wallclock_session_started") is True:
            blockers.append("WALLCLOCK_SESSION_CLAIM_FORBIDDEN")
        if require_cycle_pass and session.get("terminal_status") != "PASS":
            blockers.append("CYCLE_TERMINAL_STATUS_NOT_PASS")

    if no_order:
        if no_order.get("ok") is not True:
            blockers.append("NO_ORDER_ATTESTATION_NOT_OK")
        if no_order.get("orders_submitted", 0) not in (0, False):
            blockers.append("ORDERS_SUBMITTED_CLAIM")
        if no_order.get("broker_writes_performed", 0) not in (0, False):
            blockers.append("BROKER_WRITES_CLAIM")

    if replay:
        if replay.get("orders_submitted") is True:
            blockers.append("REPLAY_ORDERS_SUBMITTED")
        if replay.get("broker_writes_performed") is True:
            blockers.append("REPLAY_BROKER_WRITES")
        if replay.get("network_used") is True:
            blockers.append("REPLAY_NETWORK_USED")
        if replay.get("credentials_used") is True:
            blockers.append("REPLAY_CREDENTIALS_USED")

    if blockers:
        incomplete = any(b.startswith("MISSING_ARTIFACTS:") for b in blockers)
        return ObservationBundleVerificationResultV1(
            result=RESULT_INCOMPLETE if incomplete and len(blockers) == 1 else RESULT_INVALID,
            verified=False,
            blockers=blockers,
            notes=notes,
        )

    return ObservationBundleVerificationResultV1(
        result=RESULT_VERIFIED,
        verified=True,
        blockers=[],
        notes=notes
        + [
            "EVIDENCE_BUNDLE_STRUCTURALLY_VERIFIED",
            "ECONOMIC_VALIDITY_PASS=false",
            "PAPER_SHADOW_OBSERVATION_AUTHORIZED=false",
            "INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED=false",
        ],
        authority_effect=AUTHORITY_EFFECT_NONE,
        economic_validity_pass=False,
        paper_shadow_observation_authorized=False,
        integrated_economic_evidence_bundle_verified=False,
        consumer_eligibility=False,
    )
