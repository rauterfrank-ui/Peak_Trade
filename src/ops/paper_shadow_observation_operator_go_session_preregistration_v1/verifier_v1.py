"""Canonical verifier for preregistration / GO / authorization artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1 import (
    AuthorizationArtifactV1,
    load_authorization_artifact_v1,
    validate_authorization_artifact_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    verify_confirm_token_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
    SCHEMA_VERSION,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    OperatorGoContractV1,
    load_operator_go_contract_dict_v1,
    parse_operator_go_contract_v1,
    validate_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    SessionPreregistrationContractV1,
    load_preregistration_contract_dict_v1,
    parse_preregistration_contract_v1,
    validate_preregistration_contract_v1,
)

VERIFIER_ID = "ops.paper_shadow_observation_operator_go_session_preregistration_verifier_v1"
RESULT_PASS = "PAPER_SHADOW_OBSERVATION_AUTHORIZATION_BUNDLE_VERIFIED"
RESULT_FAIL = "PAPER_SHADOW_OBSERVATION_AUTHORIZATION_BUNDLE_INVALID"


@dataclass
class AuthorizationBundleVerificationResultV1:
    result: str
    verified: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    authority_effect: str = AUTHORITY_EFFECT_NONE
    paper_shadow_observation_authorized: bool = False
    orders_authorized: bool = False
    testnet_authorized: bool = False
    live_authorized: bool = False
    session_executed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verify_paper_shadow_observation_authorization_bundle_v1(
    *,
    prereg: Optional[SessionPreregistrationContractV1] = None,
    go: Optional[OperatorGoContractV1] = None,
    artifact: Optional[AuthorizationArtifactV1] = None,
    prereg_path: Optional[Path] = None,
    go_path: Optional[Path] = None,
    artifact_path: Optional[Path] = None,
    confirm_token: Optional[str] = None,
    now_unix: Optional[float] = None,
    expected_repository_sha: Optional[str] = None,
    previously_seen_fingerprints: frozenset[str] | None = None,
    require_artifact: bool = False,
) -> AuthorizationBundleVerificationResultV1:
    """Deterministic offline verifier. Never mutates artifacts or starts sessions."""
    notes = [
        f"VERIFIER_ID={VERIFIER_ID}",
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "VERIFIER_NO_NETWORK",
        "VERIFIER_NO_RUNTIME",
        "VERIFIER_NO_MUTATION",
        "AUTHORIZATION_IS_NOT_EXECUTION",
    ]
    blockers: list[str] = []

    if prereg is None and prereg_path is not None:
        try:
            prereg = parse_preregistration_contract_v1(
                load_preregistration_contract_dict_v1(prereg_path)
            )
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"PREREG_LOAD_FAIL:{exc}")
    if go is None and go_path is not None:
        try:
            go = parse_operator_go_contract_v1(load_operator_go_contract_dict_v1(go_path))
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"GO_LOAD_FAIL:{exc}")
    if artifact is None and artifact_path is not None:
        try:
            artifact = load_authorization_artifact_v1(artifact_path)
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"ARTIFACT_LOAD_FAIL:{exc}")

    if prereg is None:
        blockers.append("PREREGISTRATION_ABSENT")
    if go is None:
        blockers.append("OPERATOR_GO_ABSENT")
    if require_artifact and artifact is None:
        blockers.append("AUTHORIZATION_ARTIFACT_ABSENT")

    if prereg is not None:
        pr = validate_preregistration_contract_v1(
            prereg, now_unix=now_unix, expected_repository_sha=expected_repository_sha
        )
        blockers.extend(pr.blockers)
        if not prereg.evidence_root or not prereg.evidence_target_paths:
            blockers.append("EVIDENCE_PATHS_INVALID")
    if go is not None:
        gr = validate_operator_go_contract_v1(
            go,
            prereg=prereg,
            now_unix=now_unix,
            expected_repository_sha=expected_repository_sha,
        )
        blockers.extend(gr.blockers)

    authorized = False
    if prereg is not None and go is not None and confirm_token is not None:
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

    if artifact is not None:
        ar = validate_authorization_artifact_v1(
            artifact, now_unix=now_unix, expected_repository_sha=expected_repository_sha
        )
        blockers.extend(ar.blockers)
        if prereg is not None and artifact.session_id != prereg.session_id:
            blockers.append("ARTIFACT_SESSION_MISMATCH")
        if go is not None and artifact.go_id != go.go_id:
            blockers.append("ARTIFACT_GO_ID_MISMATCH")
        if prereg is not None and artifact.scope_digest != prereg.scope_digest():
            blockers.append("ARTIFACT_SCOPE_DIGEST_MISMATCH")
        authorized = bool(artifact.paper_shadow_observation_authorized) and not blockers

    unique = sorted(set(blockers))
    ok = not unique and prereg is not None and go is not None
    if require_artifact:
        ok = ok and artifact is not None and authorized

    return AuthorizationBundleVerificationResultV1(
        result=RESULT_PASS if ok else RESULT_FAIL,
        verified=ok,
        blockers=unique,
        notes=notes + [f"SCHEMA_VERSION={SCHEMA_VERSION}"],
        authority_effect=AUTHORITY_EFFECT_NONE,
        paper_shadow_observation_authorized=bool(authorized and ok),
        orders_authorized=False,
        testnet_authorized=False,
        live_authorized=False,
        session_executed=False,
    )
