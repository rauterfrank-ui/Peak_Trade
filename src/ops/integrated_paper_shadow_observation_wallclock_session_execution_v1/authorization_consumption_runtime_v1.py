"""Atomic authorization consumption before first network byte."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Set

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    NETWORK_SCOPE,
    SESSION_EXECUTION_SCOPE,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.wallclock_evidence_v1 import (
    WallclockEvidenceWriterV1,
    _atomic_write_text,
    _canonical_json,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1 import (
    AuthorizationArtifactV1,
    validate_authorization_artifact_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    fingerprint_confirm_token,
    verify_confirm_token_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.consumption_revocation_v1 import (
    transition_consume_authorization_artifact_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    OperatorGoContractV1,
    validate_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    SessionPreregistrationContractV1,
    validate_preregistration_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.verifier_v1 import (
    verify_paper_shadow_observation_authorization_bundle_v1,
)


class AuthorizationConsumptionError(RuntimeError):
    """Fail-closed consumption error."""


@dataclass
class AuthorizationConsumptionResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    consumed_artifact: Optional[AuthorizationArtifactV1] = None
    confirm_token_fingerprint: str = ""
    consumption_record: dict[str, Any] = field(default_factory=dict)
    transport_open_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "confirm_token_fingerprint": self.confirm_token_fingerprint,
            "consumption_record": dict(self.consumption_record),
            "transport_open_allowed": self.transport_open_allowed,
            "consumed_artifact": None
            if self.consumed_artifact is None
            else self.consumed_artifact.to_dict(),
        }


def _load_fingerprint_ledger(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.add(line)
    return out


def _append_fingerprint(path: Path, fingerprint: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(fingerprint + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def consume_authorization_for_wallclock_start_v1(
    *,
    prereg: SessionPreregistrationContractV1,
    go: OperatorGoContractV1,
    artifact: AuthorizationArtifactV1,
    confirm_token: str,
    evidence_writer: WallclockEvidenceWriterV1,
    artifact_path: Path,
    now_unix: float,
    expected_repository_sha: str,
    fingerprint_ledger_path: Path,
    known_session_ids: Optional[Set[str]] = None,
) -> AuthorizationConsumptionResultV1:
    """Verify offline, persist consumption, mark artifact consumed, THEN allow transport."""
    blockers: list[str] = []

    pr = validate_preregistration_contract_v1(
        prereg, now_unix=now_unix, expected_repository_sha=expected_repository_sha
    )
    blockers.extend(pr.blockers)
    gr = validate_operator_go_contract_v1(
        go, prereg=prereg, now_unix=now_unix, expected_repository_sha=expected_repository_sha
    )
    blockers.extend(gr.blockers)
    ar = validate_authorization_artifact_v1(
        artifact, now_unix=now_unix, expected_repository_sha=expected_repository_sha
    )
    blockers.extend(ar.blockers)

    if not go.network_authorized or go.network_scope != NETWORK_SCOPE:
        blockers.append("WALLCLOCK_NETWORK_SCOPE_REQUIRED")
    if not go.session_execution_authorized or go.session_execution_scope != SESSION_EXECUTION_SCOPE:
        blockers.append("WALLCLOCK_SESSION_EXECUTION_SCOPE_REQUIRED")
    if not artifact.network_authorized or artifact.network_scope != NETWORK_SCOPE:
        blockers.append("ARTIFACT_NETWORK_SCOPE_REQUIRED")
    if (
        not artifact.session_execution_authorized
        or artifact.session_execution_scope != SESSION_EXECUTION_SCOPE
    ):
        blockers.append("ARTIFACT_SESSION_EXECUTION_SCOPE_REQUIRED")

    if go.venue.upper() != "OKX" or prereg.venue.upper() != "OKX":
        blockers.append("VENUE_MUST_BE_OKX")
    if go.market_type.upper() != "FUTURES" or prereg.market_type.upper() != "FUTURES":
        blockers.append("MARKET_TYPE_MUST_BE_FUTURES")
    if list(go.instrument_allowlist) != [CANONICAL_INSTRUMENT_ID]:
        blockers.append("INSTRUMENT_MUST_BE_EXACT_CANONICAL")
    if list(prereg.instrument_allowlist) != [CANONICAL_INSTRUMENT_ID]:
        blockers.append("PREREG_INSTRUMENT_MUST_BE_EXACT_CANONICAL")
    if now_unix < prereg.earliest_start:
        blockers.append("START_BEFORE_EARLIEST")
    if now_unix > go.expires_at or now_unix > prereg.expires_at or now_unix > artifact.expires_at:
        blockers.append("START_AFTER_EXPIRY")

    ledger = _load_fingerprint_ledger(fingerprint_ledger_path)
    token_res = verify_confirm_token_v1(
        confirm_token=confirm_token,
        expected_binding_sha256=go.confirm_token_binding_sha256,
        session_id=go.session_id,
        scope_digest=prereg.scope_digest(),
        expires_at=go.expires_at,
        repository_sha=go.expected_repository_sha,
        previously_seen_fingerprints=frozenset(ledger),
    )
    blockers.extend(token_res.blockers)

    verified = verify_paper_shadow_observation_authorization_bundle_v1(
        prereg=prereg,
        go=go,
        artifact=artifact,
        confirm_token=confirm_token,
        now_unix=now_unix,
        expected_repository_sha=expected_repository_sha,
        previously_seen_fingerprints=frozenset(ledger),
        require_artifact=True,
    )
    if not verified.verified:
        blockers.extend(verified.blockers)

    known = known_session_ids or set()
    if go.session_id in known:
        blockers.append("ABORT_DUPLICATE_SESSION")

    if go.consumed or artifact.consumed or prereg.consumed:
        blockers.append("ALREADY_CONSUMED")
    if go.revoked or artifact.revoked or prereg.revoked:
        blockers.append("REVOKED")

    unique = sorted(set(blockers))
    if unique:
        return AuthorizationConsumptionResultV1(ok=False, blockers=unique)

    fp = token_res.fingerprint or fingerprint_confirm_token(confirm_token)
    try:
        consumed = transition_consume_authorization_artifact_v1(artifact, now_unix=now_unix)
    except Exception as exc:  # noqa: BLE001
        return AuthorizationConsumptionResultV1(
            ok=False, blockers=[f"CONSUME_TRANSITION_FAILED:{exc}"]
        )

    record = {
        "session_id": go.session_id,
        "go_id": go.go_id,
        "authorization_id": artifact.authorization_id,
        "consumed_at": now_unix,
        "confirm_token_fingerprint": fp,
        "scope_digest": prereg.scope_digest(),
        "expected_repository_sha": expected_repository_sha,
        "network_scope": NETWORK_SCOPE,
        "session_execution_scope": SESSION_EXECUTION_SCOPE,
        "instrument": CANONICAL_INSTRUMENT_ID,
        "planned_duration_seconds": go.planned_duration_seconds,
        "transport_open_allowed_after_persist": True,
    }

    # Persist order: consumption record, artifact CONSUMED, fingerprint, fsync.
    evidence_writer.write_immutable_json("prereg.json", prereg.to_dict())
    evidence_writer.write_immutable_json("operator_go.json", go.to_dict())
    evidence_writer.write_immutable_json("authorization_artifact.json", consumed.to_dict())
    evidence_writer.write_immutable_json("authorization_consumption_record.json", record)
    evidence_writer.write_immutable_json(
        "authorization_consumption.json",
        {
            "status": "CONSUMED",
            "consumed": True,
            "productive_authorization": True,
            "mode": "productive_wallclock",
            "forced_wiring_fixture": False,
            "session_id": go.session_id,
            "authorization_id": artifact.authorization_id,
            "confirm_token_fingerprint": fp,
        },
    )
    evidence_writer.write_immutable_text("scope_digest.txt", prereg.scope_digest())
    evidence_writer.write_immutable_text("repo_sha.txt", expected_repository_sha)

    _atomic_write_text(artifact_path, _canonical_json(consumed.to_dict()) + "\n")
    _append_fingerprint(fingerprint_ledger_path, fp)

    try:
        fd = os.open(str(evidence_writer.evidence_root), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        return AuthorizationConsumptionResultV1(ok=False, blockers=[f"EVIDENCE_SINK_FAILURE:{exc}"])

    return AuthorizationConsumptionResultV1(
        ok=True,
        consumed_artifact=consumed,
        confirm_token_fingerprint=fp,
        consumption_record=record,
        transport_open_allowed=True,
    )
