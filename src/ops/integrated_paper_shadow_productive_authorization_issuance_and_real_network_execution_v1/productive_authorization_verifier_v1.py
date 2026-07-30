"""Canonical verifiers for productive issuance artifacts and authorization bundles (v2 only)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.authorization_artifact_v2 import (
    AuthorizationArtifactV2,
    load_authorization_artifact_dict_v2,
    parse_authorization_artifact_v2,
    validate_authorization_artifact_v2,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.constants_v1 import (
    AUTHORIZATION_SCHEMA,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZATION_SCHEMA_REJECTED_LEGACY,
    AUTHORIZED_NETWORK_SCOPE,
    AUTHORIZED_VENUE,
    CANONICAL_RUNBOOK_SHA256,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.v1_quarantine_v1 import (
    classify_authorization_schema_for_wallclock_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.constants_v1 import (  # noqa: E501
    CANONICAL_HOST,
    CANONICAL_INSTRUMENT_ID,
    NETWORK_SCOPE,
    PRODUCER_FAMILY,
    SCHEMA_VERSION,
    SESSION_EXECUTION_SCOPE,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    fingerprint_confirm_token,
    redact_mapping_for_logs,
    verify_confirm_token_v1,
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

VERIFIER_ID = "ops.integrated_paper_shadow_productive_authorization_issuance_verifier_v1"


@dataclass
class ProductiveVerificationResultV1:
    ok: bool
    verified: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    confirm_token_fingerprint: str = ""
    productive: bool = False

    def to_dict(self) -> dict[str, Any]:
        return redact_mapping_for_logs(
            asdict(self)
            | {
                "verifier_id": VERIFIER_ID,
                "schema_version": SCHEMA_VERSION,
                "producer_family": PRODUCER_FAMILY,
                "canonical_authorization_schema": AUTHORIZATION_SCHEMA,
            }
        )


def _reject_fixture(
    *,
    prereg: SessionPreregistrationContractV1,
    go: OperatorGoContractV1,
) -> list[str]:
    blockers: list[str] = []
    if prereg.fixture_non_authoritative:
        blockers.append("FIXTURE_PREREGISTRATION_REJECTED")
    if go.fixture_non_authoritative:
        blockers.append("FIXTURE_OPERATOR_GO_REJECTED")
    notes_blob = " ".join(prereg.notes) + " " + " ".join(go.notes)
    if "FIXTURE_NON_AUTHORITATIVE" in notes_blob or "NOT_A_PRODUCTION_GO" in notes_blob:
        blockers.append("FIXTURE_NOTES_REJECTED_FOR_PRODUCTIVE")
    return blockers


def verify_productive_preregistration_v1(
    prereg: SessionPreregistrationContractV1,
    *,
    now_unix: float,
    expected_repository_sha: Optional[str] = None,
) -> ProductiveVerificationResultV1:
    notes = ["VERIFY_PRODUCTIVE_PREREGISTRATION"]
    blockers = list(
        validate_preregistration_contract_v1(
            prereg, now_unix=now_unix, expected_repository_sha=expected_repository_sha
        ).blockers
    )
    if prereg.fixture_non_authoritative:
        blockers.append("FIXTURE_PREREGISTRATION_REJECTED")
    if list(prereg.instrument_allowlist) != [CANONICAL_INSTRUMENT_ID]:
        blockers.append("INSTRUMENT_BINDING_MISMATCH")
    if prereg.network_scope != NETWORK_SCOPE:
        blockers.append("NETWORK_SCOPE_MISMATCH")
    if prereg.session_execution_scope != SESSION_EXECUTION_SCOPE:
        blockers.append("SESSION_EXECUTION_SCOPE_MISMATCH")
    if CANONICAL_HOST not in " ".join(prereg.notes):
        blockers.append("HOST_ALLOWLIST_ATTESTATION_MISSING")
    ok = not blockers
    return ProductiveVerificationResultV1(
        ok=ok, verified=ok, blockers=sorted(set(blockers)), notes=notes, productive=ok
    )


def verify_productive_confirm_token_challenge_v1(
    *,
    confirm_token: str,
    prereg: SessionPreregistrationContractV1,
    go: OperatorGoContractV1,
    previously_seen_fingerprints: frozenset[str] | None = None,
) -> ProductiveVerificationResultV1:
    notes = ["VERIFY_CONFIRM_TOKEN_CHALLENGE", "NO_PLAINTEXT_IN_RESULT"]
    token_res = verify_confirm_token_v1(
        confirm_token=confirm_token,
        expected_binding_sha256=go.confirm_token_binding_sha256,
        session_id=go.session_id,
        scope_digest=prereg.scope_digest(),
        expires_at=go.expires_at,
        repository_sha=go.expected_repository_sha,
        previously_seen_fingerprints=previously_seen_fingerprints,
    )
    blockers = list(token_res.blockers)
    if go.session_id != prereg.session_id:
        blockers.append("SESSION_ID_MISMATCH")
    if go.confirm_token_binding_sha256 != prereg.confirm_token_binding_sha256:
        blockers.append("BINDING_HASH_MISMATCH")
    ok = not blockers
    return ProductiveVerificationResultV1(
        ok=ok,
        verified=ok,
        blockers=sorted(set(blockers)),
        notes=notes,
        confirm_token_fingerprint=token_res.fingerprint,
        productive=ok,
    )


def verify_productive_operator_go_v1(
    go: OperatorGoContractV1,
    *,
    prereg: SessionPreregistrationContractV1,
    now_unix: float,
    expected_repository_sha: Optional[str] = None,
) -> ProductiveVerificationResultV1:
    notes = ["VERIFY_PRODUCTIVE_OPERATOR_GO"]
    blockers = list(
        validate_operator_go_contract_v1(
            go, prereg=prereg, now_unix=now_unix, expected_repository_sha=expected_repository_sha
        ).blockers
    )
    blockers.extend(_reject_fixture(prereg=prereg, go=go))
    if not go.network_authorized or go.network_scope != NETWORK_SCOPE:
        blockers.append("PRODUCTIVE_NETWORK_SCOPE_REQUIRED")
    if not go.session_execution_authorized or go.session_execution_scope != SESSION_EXECUTION_SCOPE:
        blockers.append("PRODUCTIVE_SESSION_EXECUTION_SCOPE_REQUIRED")
    if go.paper_execution_authorized or go.orders_authorized or go.credentials_authorized:
        blockers.append("UNSAFE_AUTHORITY_FLAG")
    ok = not blockers
    return ProductiveVerificationResultV1(
        ok=ok, verified=ok, blockers=sorted(set(blockers)), notes=notes, productive=ok
    )


def verify_productive_authorization_bundle_v1(
    *,
    prereg: SessionPreregistrationContractV1,
    go: OperatorGoContractV1,
    artifact: AuthorizationArtifactV2,
    confirm_token: str,
    now_unix: float,
    expected_repository_sha: Optional[str] = None,
    previously_seen_fingerprints: frozenset[str] | None = None,
    expected_runbook_sha256: str = CANONICAL_RUNBOOK_SHA256,
) -> ProductiveVerificationResultV1:
    notes = [
        "VERIFY_PRODUCTIVE_AUTHORIZATION_BUNDLE_V2",
        "V1_REJECTED",
        "FIXTURES_REJECTED",
    ]
    blockers: list[str] = []
    blockers.extend(
        verify_productive_preregistration_v1(
            prereg, now_unix=now_unix, expected_repository_sha=expected_repository_sha
        ).blockers
    )
    blockers.extend(
        verify_productive_operator_go_v1(
            go,
            prereg=prereg,
            now_unix=now_unix,
            expected_repository_sha=expected_repository_sha,
        ).blockers
    )
    blockers.extend(_reject_fixture(prereg=prereg, go=go))
    validated = validate_authorization_artifact_v2(
        artifact,
        expected_repository_sha=expected_repository_sha or prereg.expected_repository_sha,
        expected_runbook_sha256=expected_runbook_sha256,
        expected_preregistration_id=prereg.session_id,
        expected_preregistration_digest=prereg.scope_digest(),
        now_unix=now_unix,
    )
    blockers.extend(validated.blockers)
    if artifact.schema != AUTHORIZATION_SCHEMA:
        blockers.append(AUTHORIZATION_SCHEMA_REJECTED_LEGACY)
    if artifact.venue != AUTHORIZED_VENUE:
        blockers.append("VENUE_MISMATCH")
    if artifact.network_scope != AUTHORIZED_NETWORK_SCOPE:
        blockers.append("NETWORK_SCOPE_MISMATCH")
    if artifact.preregistration_id != prereg.session_id:
        blockers.append("PREREGISTRATION_ID_MISMATCH")
    if artifact.preregistration_digest != prereg.scope_digest():
        blockers.append("PREREGISTRATION_DIGEST_MISMATCH")
    token_res = verify_productive_confirm_token_challenge_v1(
        confirm_token=confirm_token,
        prereg=prereg,
        go=go,
        previously_seen_fingerprints=previously_seen_fingerprints,
    )
    blockers.extend(token_res.blockers)
    fp = fingerprint_confirm_token(confirm_token)
    if fp != artifact.confirm_token_fingerprint:
        blockers.append("CONFIRM_TOKEN_MISMATCH")
    if go.consumed or prereg.consumed:
        blockers.append("ALREADY_CONSUMED")
    if list(go.instrument_allowlist) != [CANONICAL_INSTRUMENT_ID]:
        blockers.append("INSTRUMENT_MISMATCH")
    ok = not blockers
    return ProductiveVerificationResultV1(
        ok=ok,
        verified=ok,
        blockers=sorted(set(blockers)),
        notes=notes,
        confirm_token_fingerprint=token_res.confirm_token_fingerprint,
        productive=ok,
    )


def verify_productive_authorization_bundle_paths_v1(
    *,
    preregistration_path: Path,
    operator_go_path: Path,
    authorization_artifact_path: Path,
    confirm_token: str,
    now_unix: float,
    expected_repository_sha: Optional[str] = None,
    previously_seen_fingerprints: frozenset[str] | None = None,
) -> ProductiveVerificationResultV1:
    try:
        prereg = parse_preregistration_contract_v1(
            load_preregistration_contract_dict_v1(preregistration_path)
        )
        go = parse_operator_go_contract_v1(load_operator_go_contract_dict_v1(operator_go_path))
        raw = load_authorization_artifact_dict_v2(authorization_artifact_path)
        kind, kind_blockers = classify_authorization_schema_for_wallclock_v1(raw)
        if kind != "v2":
            return ProductiveVerificationResultV1(
                ok=False,
                verified=False,
                blockers=sorted(set(kind_blockers or [AUTHORIZATION_SCHEMA_REJECTED_LEGACY])),
                notes=["VERIFY_PATHS", "V1_OR_LEGACY_REJECTED"],
            )
        artifact = parse_authorization_artifact_v2(raw)
    except Exception as exc:  # noqa: BLE001
        return ProductiveVerificationResultV1(
            ok=False,
            verified=False,
            blockers=[f"ARTIFACT_LOAD_FAILED:{type(exc).__name__}"],
            notes=["VERIFY_PATHS"],
        )
    return verify_productive_authorization_bundle_v1(
        prereg=prereg,
        go=go,
        artifact=artifact,
        confirm_token=confirm_token,
        now_unix=now_unix,
        expected_repository_sha=expected_repository_sha,
        previously_seen_fingerprints=previously_seen_fingerprints,
    )
