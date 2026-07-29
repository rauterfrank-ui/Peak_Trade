"""Authorization artifact builder/parser (observation-only, non-executing)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    assert_no_plaintext_token_fields,
    verify_confirm_token_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.constants_v1 import (
    AUTHORIZATION_ARTIFACT_SCHEMA_VERSION,
    CAPABILITY_ID,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    OperatorGoContractV1,
    validate_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    SessionPreregistrationContractV1,
    validate_preregistration_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.state_machine_v1 import (
    AuthorizationArmingState,
    assert_authorization_preconditions,
    derive_arming_state,
)

_KNOWN_FIELDS = frozenset(
    {
        "schema_version",
        "capability_id",
        "authorization_id",
        "session_id",
        "go_id",
        "issued_at",
        "expires_at",
        "expected_repository_sha",
        "config_identity",
        "code_identity",
        "scope_digest",
        "confirm_token_fingerprint",
        "confirm_token_binding_sha256",
        "arming_state",
        "paper_shadow_observation_authorized",
        "orders_authorized",
        "testnet_authorized",
        "live_authorized",
        "auto_promotion_authorized",
        "session_execution_authorized",
        "network_authorized",
        "credentials_authorized",
        "single_use",
        "consumed",
        "revoked",
        "revocation_state",
        "fixture_non_authoritative",
        "notes",
    }
)


class AuthorizationArtifactError(ValueError):
    """Fail-closed authorization artifact error."""


@dataclass(frozen=True)
class AuthorizationArtifactV1:
    schema_version: str
    capability_id: str
    authorization_id: str
    session_id: str
    go_id: str
    issued_at: float
    expires_at: float
    expected_repository_sha: str
    config_identity: str
    code_identity: str
    scope_digest: str
    confirm_token_fingerprint: str
    confirm_token_binding_sha256: str
    arming_state: str
    paper_shadow_observation_authorized: bool
    orders_authorized: bool
    testnet_authorized: bool
    live_authorized: bool
    auto_promotion_authorized: bool
    session_execution_authorized: bool
    network_authorized: bool
    credentials_authorized: bool
    single_use: bool
    consumed: bool
    revoked: bool
    revocation_state: str
    fixture_non_authoritative: bool = False
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["notes"] = list(self.notes)
        return payload


@dataclass
class AuthorizationBuildResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    artifact: Optional[AuthorizationArtifactV1] = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "artifact": None if self.artifact is None else self.artifact.to_dict(),
            "session_executed": False,
        }


def build_authorization_artifact_v1(
    *,
    prereg: SessionPreregistrationContractV1,
    go: OperatorGoContractV1,
    confirm_token: str,
    authorization_id: str,
    now_unix: float,
    previously_seen_fingerprints: frozenset[str] | None = None,
    force_pass: bool = False,
) -> AuthorizationBuildResultV1:
    notes = [
        "AUTHORIZATION_IS_NOT_EXECUTION",
        "NO_SESSION_STARTED",
        "NO_ORDERS_TESTNET_LIVE",
        "NO_PLAINTEXT_TOKEN_IN_ARTIFACT",
    ]
    if force_pass:
        return AuthorizationBuildResultV1(
            ok=False,
            blockers=["FORCE_PASS_REJECTED"],
            notes=notes + ["SYNTHETIC_FORCE_PASS_FORBIDDEN"],
        )

    blockers: list[str] = []
    prereg_res = validate_preregistration_contract_v1(prereg, now_unix=now_unix)
    go_res = validate_operator_go_contract_v1(go, prereg=prereg, now_unix=now_unix)
    blockers.extend(prereg_res.blockers)
    blockers.extend(go_res.blockers)

    arming_blocker = assert_authorization_preconditions(enabled=go.enabled, armed=go.armed)
    if arming_blocker:
        blockers.append(arming_blocker)

    token_res = verify_confirm_token_v1(
        confirm_token=confirm_token,
        expected_binding_sha256=go.confirm_token_binding_sha256,
        session_id=go.session_id,
        scope_digest=prereg.scope_digest(),
        expires_at=go.expires_at,
        repository_sha=go.expected_repository_sha,
        previously_seen_fingerprints=previously_seen_fingerprints,
    )
    blockers.extend(token_res.blockers)

    if blockers:
        return AuthorizationBuildResultV1(ok=False, blockers=sorted(set(blockers)), notes=notes)

    state = derive_arming_state(
        enabled=True,
        armed=True,
        authorized=True,
        consumed=False,
        expired=False,
        revoked=False,
        rejected=False,
    )
    artifact = AuthorizationArtifactV1(
        schema_version=AUTHORIZATION_ARTIFACT_SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        authorization_id=str(authorization_id),
        session_id=go.session_id,
        go_id=go.go_id,
        issued_at=float(now_unix),
        expires_at=go.expires_at,
        expected_repository_sha=go.expected_repository_sha,
        config_identity=go.config_identity,
        code_identity=go.code_identity,
        scope_digest=prereg.scope_digest(),
        confirm_token_fingerprint=token_res.fingerprint,
        confirm_token_binding_sha256=go.confirm_token_binding_sha256,
        arming_state=state.value,
        paper_shadow_observation_authorized=True,
        orders_authorized=False,
        testnet_authorized=False,
        live_authorized=False,
        auto_promotion_authorized=False,
        session_execution_authorized=False,
        network_authorized=False,
        credentials_authorized=False,
        single_use=True,
        consumed=False,
        revoked=False,
        revocation_state="none",
        fixture_non_authoritative=bool(
            prereg.fixture_non_authoritative or go.fixture_non_authoritative
        ),
        notes=(
            "SCOPED_OBSERVATION_AUTHORIZATION_ONLY",
            "SESSION_EXECUTION_NOT_GRANTED",
            "ORDERS_AUTHORIZED=false",
            "TESTNET_AUTHORIZED=false",
            "LIVE_AUTHORIZED=false",
            "AUTO_PROMOTION_AUTHORIZED=false",
        ),
    )
    return AuthorizationBuildResultV1(ok=True, artifact=artifact, notes=notes)


def parse_authorization_artifact_v1(raw: Mapping[str, Any]) -> AuthorizationArtifactV1:
    assert_no_plaintext_token_fields(raw)
    unknown = sorted(set(raw) - _KNOWN_FIELDS)
    if unknown:
        raise AuthorizationArtifactError("AUTH_UNKNOWN_FIELDS:" + ",".join(unknown))

    def _req(name: str) -> Any:
        if name not in raw:
            raise AuthorizationArtifactError(f"AUTH_FIELD_MISSING:{name}")
        return raw[name]

    notes_raw = raw.get("notes", ())
    notes = tuple(str(x) for x in notes_raw) if isinstance(notes_raw, (list, tuple)) else ()
    return AuthorizationArtifactV1(
        schema_version=str(_req("schema_version")),
        capability_id=str(_req("capability_id")),
        authorization_id=str(_req("authorization_id")),
        session_id=str(_req("session_id")),
        go_id=str(_req("go_id")),
        issued_at=float(_req("issued_at")),
        expires_at=float(_req("expires_at")),
        expected_repository_sha=str(_req("expected_repository_sha")),
        config_identity=str(_req("config_identity")),
        code_identity=str(_req("code_identity")),
        scope_digest=str(_req("scope_digest")),
        confirm_token_fingerprint=str(_req("confirm_token_fingerprint")),
        confirm_token_binding_sha256=str(_req("confirm_token_binding_sha256")),
        arming_state=str(_req("arming_state")),
        paper_shadow_observation_authorized=bool(_req("paper_shadow_observation_authorized")),
        orders_authorized=bool(_req("orders_authorized")),
        testnet_authorized=bool(_req("testnet_authorized")),
        live_authorized=bool(_req("live_authorized")),
        auto_promotion_authorized=bool(_req("auto_promotion_authorized")),
        session_execution_authorized=bool(_req("session_execution_authorized")),
        network_authorized=bool(_req("network_authorized")),
        credentials_authorized=bool(_req("credentials_authorized")),
        single_use=bool(_req("single_use")),
        consumed=bool(_req("consumed")),
        revoked=bool(_req("revoked")),
        revocation_state=str(_req("revocation_state")),
        fixture_non_authoritative=bool(raw.get("fixture_non_authoritative", False)),
        notes=notes,
    )


def load_authorization_artifact_v1(path: Path) -> AuthorizationArtifactV1:
    if not path.is_file():
        raise AuthorizationArtifactError("AUTHORIZATION_ARTIFACT_MISSING")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AuthorizationArtifactError(f"AUTHORIZATION_ARTIFACT_PARSE_ERROR:{exc}") from exc
    if not isinstance(raw, dict):
        raise AuthorizationArtifactError("AUTHORIZATION_ARTIFACT_NOT_OBJECT")
    return parse_authorization_artifact_v1(raw)


def validate_authorization_artifact_v1(
    artifact: AuthorizationArtifactV1,
    *,
    now_unix: Optional[float] = None,
    expected_repository_sha: Optional[str] = None,
) -> AuthorizationBuildResultV1:
    blockers: list[str] = []
    notes = ["AUTHORIZATION_ARTIFACT_VALIDATION", "NO_SESSION_EXECUTION"]
    if artifact.schema_version != AUTHORIZATION_ARTIFACT_SCHEMA_VERSION:
        blockers.append("AUTH_SCHEMA_VERSION_MISMATCH")
    if artifact.capability_id != CAPABILITY_ID:
        blockers.append("AUTH_CAPABILITY_MISMATCH")
    if artifact.arming_state != AuthorizationArmingState.AUTHORIZED.value:
        if artifact.arming_state not in {
            AuthorizationArmingState.CONSUMED.value,
            AuthorizationArmingState.EXPIRED.value,
            AuthorizationArmingState.REVOKED.value,
        }:
            blockers.append(f"AUTH_ARMING_STATE_INVALID:{artifact.arming_state}")
    if artifact.orders_authorized or artifact.testnet_authorized or artifact.live_authorized:
        blockers.append("AUTH_NEGATIVE_AUTHORITY_VIOLATION")
    if artifact.auto_promotion_authorized:
        blockers.append("AUTH_AUTO_PROMOTION_VIOLATION")
    if artifact.session_execution_authorized:
        blockers.append("AUTH_SESSION_EXECUTION_CLAIM_FORBIDDEN")
    if artifact.network_authorized or artifact.credentials_authorized:
        blockers.append("AUTH_NETWORK_OR_CREDENTIALS_CLAIM_FORBIDDEN")
    if not artifact.single_use:
        blockers.append("AUTH_SINGLE_USE_REQUIRED")
    if artifact.consumed:
        blockers.append("AUTH_CONSUMED")
    if artifact.revoked or artifact.revocation_state.strip().lower() == "revoked":
        blockers.append("AUTH_REVOKED")
    if now_unix is not None and now_unix > artifact.expires_at:
        blockers.append("AUTH_EXPIRED")
    if (
        expected_repository_sha is not None
        and artifact.expected_repository_sha != expected_repository_sha
    ):
        blockers.append("AUTH_REPOSITORY_SHA_MISMATCH")
    if not artifact.paper_shadow_observation_authorized:
        blockers.append("AUTH_NOT_MARKED_AUTHORIZED")
    return AuthorizationBuildResultV1(
        ok=not blockers,
        blockers=blockers,
        artifact=artifact,
        notes=notes,
    )
