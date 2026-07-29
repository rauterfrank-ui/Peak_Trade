"""Authorization-readiness producer (observation-only; never grants Orders/Testnet/Live)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1 import (
    AuthorizationArtifactV1,
    build_authorization_artifact_v1,
    validate_authorization_artifact_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    verify_confirm_token_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
    PACKAGE_MARKER,
    PRODUCER_FAMILY,
    SCHEMA_VERSION,
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
    assert_authorization_preconditions,
)

AUTHORIZATION_READINESS_PRODUCER_ID = (
    "ops.paper_shadow_observation_authorization_readiness_producer_v1"
)


@dataclass
class AuthorizationReadinessChecksV1:
    preregistration_contract_valid: bool = False
    go_contract_valid: bool = False
    scope_match: bool = False
    venue_match: bool = False
    instrument_scope_match: bool = False
    strategy_portfolio_match: bool = False
    repo_sha_match: bool = False
    config_identity_match: bool = False
    code_identity_match: bool = False
    no_order_invariant_match: bool = False
    expiry_valid: bool = False
    not_revoked: bool = False
    not_consumed: bool = False
    enabled_true: bool = False
    armed_true: bool = False
    confirm_token_verified: bool = False
    replay_guard_pass: bool = False
    authority_boundary_pass: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuthorizationReadinessResultV1:
    schema_id: str
    schema_version: str
    producer_id: str
    capability_id: str
    package_marker: str
    authority_effect: str
    PAPER_SHADOW_OBSERVATION_AUTHORIZATION_READINESS_PASS: bool
    PAPER_SHADOW_OBSERVATION_AUTHORIZED: bool
    ORDERS_AUTHORIZED: bool
    TESTNET_AUTHORIZED: bool
    LIVE_AUTHORIZED: bool
    AUTO_PROMOTION_AUTHORIZED: bool
    checks: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def produce_paper_shadow_observation_authorization_readiness_v1(
    *,
    prereg: Optional[SessionPreregistrationContractV1] = None,
    go: Optional[OperatorGoContractV1] = None,
    confirm_token: Optional[str] = None,
    artifact: Optional[AuthorizationArtifactV1] = None,
    now_unix: Optional[float] = None,
    expected_repository_sha: Optional[str] = None,
    previously_seen_fingerprints: frozenset[str] | None = None,
    force_pass: bool = False,
) -> AuthorizationReadinessResultV1:
    notes = [
        "AUTHORIZATION_READINESS_IS_NOT_SESSION_EXECUTION",
        "READINESS_IS_NOT_AUTHORIZATION",
        "ORDERS_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
        f"PRODUCER_FAMILY={PRODUCER_FAMILY}",
    ]
    checks = AuthorizationReadinessChecksV1()
    blockers: list[str] = []

    if force_pass:
        return AuthorizationReadinessResultV1(
            schema_id=AUTHORIZATION_READINESS_PRODUCER_ID,
            schema_version=SCHEMA_VERSION,
            producer_id=AUTHORIZATION_READINESS_PRODUCER_ID,
            capability_id=CAPABILITY_ID,
            package_marker=PACKAGE_MARKER,
            authority_effect=AUTHORITY_EFFECT_NONE,
            PAPER_SHADOW_OBSERVATION_AUTHORIZATION_READINESS_PASS=False,
            PAPER_SHADOW_OBSERVATION_AUTHORIZED=False,
            ORDERS_AUTHORIZED=False,
            TESTNET_AUTHORIZED=False,
            LIVE_AUTHORIZED=False,
            AUTO_PROMOTION_AUTHORIZED=False,
            checks=checks.to_dict(),
            blockers=["FORCE_PASS_REJECTED"],
            notes=notes + ["SYNTHETIC_FORCE_PASS_FORBIDDEN"],
        )

    if prereg is None or go is None:
        blockers.append("PREREG_OR_GO_MISSING")
        return AuthorizationReadinessResultV1(
            schema_id=AUTHORIZATION_READINESS_PRODUCER_ID,
            schema_version=SCHEMA_VERSION,
            producer_id=AUTHORIZATION_READINESS_PRODUCER_ID,
            capability_id=CAPABILITY_ID,
            package_marker=PACKAGE_MARKER,
            authority_effect=AUTHORITY_EFFECT_NONE,
            PAPER_SHADOW_OBSERVATION_AUTHORIZATION_READINESS_PASS=False,
            PAPER_SHADOW_OBSERVATION_AUTHORIZED=False,
            ORDERS_AUTHORIZED=False,
            TESTNET_AUTHORIZED=False,
            LIVE_AUTHORIZED=False,
            AUTO_PROMOTION_AUTHORIZED=False,
            checks=checks.to_dict(),
            blockers=blockers,
            notes=notes,
        )

    prereg_res = validate_preregistration_contract_v1(
        prereg, now_unix=now_unix, expected_repository_sha=expected_repository_sha
    )
    go_res = validate_operator_go_contract_v1(
        go,
        prereg=prereg,
        now_unix=now_unix,
        expected_repository_sha=expected_repository_sha,
    )
    checks.preregistration_contract_valid = prereg_res.ok
    checks.go_contract_valid = go_res.ok
    blockers.extend(prereg_res.blockers)
    blockers.extend(go_res.blockers)

    checks.scope_match = go.session_id == prereg.session_id and (
        not go.scope_digest or go.scope_digest == prereg.scope_digest()
    )
    checks.venue_match = (
        go.venue.upper() == prereg.venue.upper() == "OKX"
        and go.market_type.upper() == prereg.market_type.upper() == "FUTURES"
    )
    checks.instrument_scope_match = not bool(
        set(go.instrument_allowlist) - set(prereg.instrument_allowlist)
    )
    checks.strategy_portfolio_match = go.strategy_portfolio_id == prereg.strategy_portfolio_id
    checks.repo_sha_match = go.expected_repository_sha == prereg.expected_repository_sha and (
        expected_repository_sha is None or go.expected_repository_sha == expected_repository_sha
    )
    checks.config_identity_match = go.config_identity == prereg.config_identity
    checks.code_identity_match = go.code_identity == prereg.code_identity
    checks.no_order_invariant_match = (
        prereg.no_order_invariant
        and prereg.no_orders
        and (not go.orders_authorized)
        and (not go.broker_writes_authorized)
    )
    checks.expiry_valid = "GO_EXPIRED" not in go_res.blockers and (
        "PREREGISTRATION_EXPIRED" not in prereg_res.blockers
    )
    checks.not_revoked = (not go.revoked) and (not prereg.revoked)
    checks.not_consumed = (not go.consumed) and (not prereg.consumed)
    checks.enabled_true = bool(go.enabled and prereg.enabled)
    checks.armed_true = bool(go.armed and prereg.armed)

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
    checks.confirm_token_verified = token_res.ok
    checks.replay_guard_pass = "CONFIRM_TOKEN_REPLAY" not in token_res.blockers and bool(
        confirm_token
    )
    blockers.extend(token_res.blockers)

    checks.authority_boundary_pass = (
        (not go.orders_authorized)
        and (not go.testnet_authorized)
        and (not go.live_authorized)
        and (not go.auto_promotion_authorized)
        and (not go.session_execution_authorized)
        and (not go.network_authorized)
        and (not go.credentials_authorized)
    )
    if not checks.authority_boundary_pass:
        blockers.append("AUTHORITY_BOUNDARY_FAIL")

    for name, ok in checks.to_dict().items():
        if (
            not ok
            and name
            not in {
                # replay_guard_pass already covered via token blockers when token missing
            }
        ):
            if name == "replay_guard_pass" and not confirm_token:
                continue
            blockers.append(f"CHECK_FAIL:{name}")

    authorized = False
    if artifact is not None:
        art_res = validate_authorization_artifact_v1(
            artifact, now_unix=now_unix, expected_repository_sha=expected_repository_sha
        )
        if not art_res.ok:
            blockers.extend(art_res.blockers)
        else:
            authorized = bool(artifact.paper_shadow_observation_authorized)
    elif not blockers and confirm_token and now_unix is not None:
        built = build_authorization_artifact_v1(
            prereg=prereg,
            go=go,
            confirm_token=confirm_token,
            authorization_id=f"auth_{go.go_id}",
            now_unix=now_unix,
            previously_seen_fingerprints=previously_seen_fingerprints,
        )
        if built.ok and built.artifact is not None:
            authorized = True
        else:
            blockers.extend(built.blockers)

    # Authorization readiness can pass without implying default-repo AUTHORIZED.
    # The authorized flag is true only when a verified artifact/build succeeded.
    unique_blockers = sorted(set(blockers))
    authz_ready = not unique_blockers and checks.confirm_token_verified

    return AuthorizationReadinessResultV1(
        schema_id=AUTHORIZATION_READINESS_PRODUCER_ID,
        schema_version=SCHEMA_VERSION,
        producer_id=AUTHORIZATION_READINESS_PRODUCER_ID,
        capability_id=CAPABILITY_ID,
        package_marker=PACKAGE_MARKER,
        authority_effect=AUTHORITY_EFFECT_NONE,
        PAPER_SHADOW_OBSERVATION_AUTHORIZATION_READINESS_PASS=authz_ready,
        PAPER_SHADOW_OBSERVATION_AUTHORIZED=bool(authorized),
        ORDERS_AUTHORIZED=False,
        TESTNET_AUTHORIZED=False,
        LIVE_AUTHORIZED=False,
        AUTO_PROMOTION_AUTHORIZED=False,
        checks=checks.to_dict(),
        blockers=unique_blockers,
        notes=notes,
    )
