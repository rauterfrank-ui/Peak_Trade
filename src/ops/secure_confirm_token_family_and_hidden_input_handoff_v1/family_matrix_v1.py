"""Canonical confirm-token family matrix (immutable descriptive + enforceable metadata)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.constants_v1 import (
    CAPABILITY_ID,
    FAMILY_LEGACY_LITERAL,
    FAMILY_LIVE_ARMED,
    FAMILY_MATRIX_SCHEMA_VERSION,
    FAMILY_PSO_GOVERNED_PUBLIC_MD,
    FAMILY_RESEARCH_S03,
    FAMILY_TESTNET_HARNESS,
    INPUT_EPHEMERAL_HANDLE,
    INPUT_FORBIDDEN_ARGV,
    INPUT_FORBIDDEN_GENERIC_ENV,
    INPUT_GETPASS_HIDDEN,
    INPUT_TOKEN_FILE_EXCEPTION,
    PURPOSE_LEGACY_ONE_SHOT,
    PURPOSE_LIVE_BOUNDED_PILOT,
    PURPOSE_PSO_WALLCLOCK_OBSERVE,
    PURPOSE_S03_ADDITIONAL_EVIDENCE,
    PURPOSE_TESTNET_REACHABILITY,
    STORAGE_FILE_EXCEPTION,
    STORAGE_MEMORY_ONLY,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.errors_v1 import (
    SecureConfirmTokenError,
)


@dataclass(frozen=True)
class ConfirmTokenFamilySpecV1:
    family_id: str
    purpose: str
    mint_path: str
    accepted_input_channels: tuple[str, ...]
    storage_policy: str
    expiry_or_single_use_policy: str
    allowed_consumers: tuple[str, ...]
    o3_activatable: bool
    cross_family_interchangeable: bool
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_FAMILY_MATRIX: dict[str, ConfirmTokenFamilySpecV1] = {
    FAMILY_PSO_GOVERNED_PUBLIC_MD: ConfirmTokenFamilySpecV1(
        family_id=FAMILY_PSO_GOVERNED_PUBLIC_MD,
        purpose=PURPOSE_PSO_WALLCLOCK_OBSERVE,
        mint_path=(
            "src.ops.integrated_paper_shadow_productive_authorization_issuance_"
            "and_real_network_execution_v1.productive_confirm_token_producer_v1."
            "mint_productive_confirm_token_v1"
        ),
        accepted_input_channels=(INPUT_EPHEMERAL_HANDLE, INPUT_TOKEN_FILE_EXCEPTION),
        storage_policy=STORAGE_FILE_EXCEPTION,
        expiry_or_single_use_policy="TTL_BOUNDED_PLUS_FINGERPRINT_REPLAY_LEDGER",
        allowed_consumers=(
            "ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1",
            "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1",
            "ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1",
        ),
        o3_activatable=True,
        cross_family_interchangeable=False,
        notes=(
            "PREFIX_MAY_OVERLAP_S03_BODY_FORMAT",
            "FAMILY_BINDING_REQUIRED_TO_BLOCK_SUBSTITUTION",
            "GENERIC_ENV_AND_ARGV_FORBIDDEN_UNDER_O3",
        ),
    ),
    FAMILY_RESEARCH_S03: ConfirmTokenFamilySpecV1(
        family_id=FAMILY_RESEARCH_S03,
        purpose=PURPOSE_S03_ADDITIONAL_EVIDENCE,
        mint_path=(
            "research.canonical_volatility_numeric_max_age_additional_evidence_s03_"
            "atomic_auth_v2_reissue_consume_execute_v1.ephemeral_token_v1."
            "EphemeralConfirmTokenHandleV1.mint_canonical_v1"
        ),
        accepted_input_channels=(INPUT_EPHEMERAL_HANDLE, INPUT_GETPASS_HIDDEN),
        storage_policy=STORAGE_MEMORY_ONLY,
        expiry_or_single_use_policy="SINGLE_USE_HANDLE_CLEAR_PLUS_REPLAY_SET",
        allowed_consumers=(
            "research.canonical_volatility_numeric_max_age_additional_evidence_s03_"
            "productive_session_execution_owner_v1",
            "research.canonical_volatility_numeric_max_age_additional_evidence_s03_"
            "atomic_auth_v2_reissue_consume_execute_v1",
        ),
        o3_activatable=True,
        cross_family_interchangeable=False,
        notes=(
            "SHARES_PSO_TOKEN_BODY_FORMAT",
            "MUST_NOT_ACCEPT_PSO_FAMILY_BINDING",
            "GETPASS_ALLOWED_ONLY_WHEN_EPHEMERAL_HANDLE_UNAVAILABLE",
        ),
    ),
    FAMILY_TESTNET_HARNESS: ConfirmTokenFamilySpecV1(
        family_id=FAMILY_TESTNET_HARNESS,
        purpose=PURPOSE_TESTNET_REACHABILITY,
        mint_path="STATIC_HARNESS_LITERAL_NOT_MINTED_BY_O3",
        accepted_input_channels=(INPUT_FORBIDDEN_ARGV,),
        storage_policy="STATIC_LITERAL_INACTIVE",
        expiry_or_single_use_policy="REUSABLE_STATIC_UNDER_INACTIVE_CONTRACT",
        allowed_consumers=("scripts.ops.archive_futures_testnet_harness_v0",),
        o3_activatable=False,
        cross_family_interchangeable=False,
        notes=("O3_MUST_NOT_ACTIVATE", "ISOLATED_INACTIVE_FAMILY"),
    ),
    FAMILY_LIVE_ARMED: ConfirmTokenFamilySpecV1(
        family_id=FAMILY_LIVE_ARMED,
        purpose=PURPOSE_LIVE_BOUNDED_PILOT,
        mint_path="STATIC_LIVE_CONFIRM_TOKEN_NOT_MINTED_BY_O3",
        accepted_input_channels=(INPUT_FORBIDDEN_GENERIC_ENV,),
        storage_policy="STATIC_LITERAL_INACTIVE",
        expiry_or_single_use_policy="REUSABLE_STATIC_UNDER_INACTIVE_CONTRACT",
        allowed_consumers=("src.core.environment", "src.execution.live_session"),
        o3_activatable=False,
        cross_family_interchangeable=False,
        notes=("O3_MUST_NOT_ACTIVATE", "PT_LIVE_CONFIRM_TOKEN_ISOLATED"),
    ),
    FAMILY_LEGACY_LITERAL: ConfirmTokenFamilySpecV1(
        family_id=FAMILY_LEGACY_LITERAL,
        purpose=PURPOSE_LEGACY_ONE_SHOT,
        mint_path="STATIC_LEGACY_LITERAL_NOT_MINTED_BY_O3",
        accepted_input_channels=(INPUT_FORBIDDEN_ARGV,),
        storage_policy="STATIC_LITERAL_INACTIVE",
        expiry_or_single_use_policy="REUSABLE_STATIC_UNDER_INACTIVE_CONTRACT",
        allowed_consumers=("legacy_ops_one_shot_scripts",),
        o3_activatable=False,
        cross_family_interchangeable=False,
        notes=("O3_MUST_NOT_ACTIVATE", "LEGACY_ARGV_EXPOSURE_OUT_OF_O3_SCOPE"),
    ),
}


def get_family_spec_v1(family_id: str) -> ConfirmTokenFamilySpecV1:
    try:
        return _FAMILY_MATRIX[str(family_id)]
    except KeyError as exc:
        raise SecureConfirmTokenError("UNKNOWN_CONFIRM_TOKEN_FAMILY", str(family_id)) from exc


def require_activatable_family_v1(family_id: str) -> ConfirmTokenFamilySpecV1:
    spec = get_family_spec_v1(family_id)
    if not spec.o3_activatable:
        raise SecureConfirmTokenError(
            "FAMILY_NOT_ACTIVATABLE_BY_O3",
            spec.family_id,
            payload={"purpose": spec.purpose},
        )
    return spec


def assert_purpose_matches_family_v1(*, family_id: str, purpose: str) -> ConfirmTokenFamilySpecV1:
    spec = get_family_spec_v1(family_id)
    if str(purpose) != spec.purpose:
        raise SecureConfirmTokenError(
            "CONFIRM_TOKEN_PURPOSE_MISMATCH",
            f"family={spec.family_id}",
            payload={"expected_purpose": spec.purpose},
        )
    return spec


def family_matrix_public_v1() -> dict[str, Any]:
    return {
        "capability_id": CAPABILITY_ID,
        "schema_version": FAMILY_MATRIX_SCHEMA_VERSION,
        "token_family_matrix_complete": True,
        "cross_family_substitution_blocked": True,
        "families": {fid: spec.to_dict() for fid, spec in sorted(_FAMILY_MATRIX.items())},
    }


def iter_family_ids_v1() -> tuple[str, ...]:
    return tuple(sorted(_FAMILY_MATRIX.keys()))


def validate_family_matrix_complete_v1() -> Mapping[str, Any]:
    required = {
        FAMILY_PSO_GOVERNED_PUBLIC_MD,
        FAMILY_RESEARCH_S03,
        FAMILY_TESTNET_HARNESS,
        FAMILY_LIVE_ARMED,
        FAMILY_LEGACY_LITERAL,
    }
    missing = sorted(required - set(_FAMILY_MATRIX))
    if missing:
        raise SecureConfirmTokenError("TOKEN_FAMILY_MATRIX_INCOMPLETE", ",".join(missing))
    for spec in _FAMILY_MATRIX.values():
        if spec.cross_family_interchangeable:
            raise SecureConfirmTokenError(
                "FAMILY_MARKED_INTERCHANGEABLE_FORBIDDEN",
                spec.family_id,
            )
    return family_matrix_public_v1()
