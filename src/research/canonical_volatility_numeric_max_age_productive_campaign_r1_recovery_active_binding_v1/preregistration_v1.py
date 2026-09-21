"""Build R1 active-campaign preregistration payload (no execution authority)."""

from __future__ import annotations

from typing import Any

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    DEFAULT_JOIN_LEDGER_RELATIVE_PATH,
    DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH,
    DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_campaign_preregistration_v1 import (
    ABORT_BLOCK_CRITERIA,
    AUTHORITY_STATE,
    BOUND_DESIGN_PREREGISTRATION_DIGEST,
    BOUND_PRODUCTIVE_PREREGISTRATION_DIGEST,
    BOUND_RESEARCH_AGE_GRID_SECONDS,
    CAMPAIGN_PURPOSE,
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    CREATED_AT_UTC,
    ENUMERATED_MARKET_REGIME_NAMES_INVENTED,
    ENUMERATED_VOLATILITY_REGIME_NAMES_INVENTED,
    LIFECYCLE_TRANSITIONS,
    MAXIMUM_CYCLES_PER_SESSION,
    MAXIMUM_RESTART_GENERATIONS,
    MAXIMUM_SESSIONS_PER_RUN,
    MINIMUM_COMPUTED_AGE_OBSERVATIONS,
    MINIMUM_DISTINCT_EVIDENCE_RECORDS,
    MINIMUM_DISTINCT_OBSERVATIONS_PER_AGE_BUCKET,
    MINIMUM_DISTINCT_SESSIONS,
    MINIMUM_INDEPENDENT_SESSIONS,
    MINIMUM_INSTRUMENTS,
    MINIMUM_MARKET_REGIMES,
    MINIMUM_VOLATILITY_REGIMES,
    NON_PROMOTION_INVARIANTS,
    PUBLIC_MD_ALLOWED_ENDPOINTS,
    PUBLIC_MD_ALLOWED_METHOD,
    PUBLIC_MD_HOST,
    PUBLIC_MD_TRANSPORT,
    PUBLIC_MD_VENUE,
    PUBLIC_MD_VENUE_SCOPE,
    REGIME_LABEL_AUTHORITY,
    REQUIRED_OBSERVATION_BINDINGS,
    SAMPLE_EVENT_TIME_BINDINGS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    VENUE_BINDING_AUTHORITY,
    VOLATILITY_REGIME_LABEL_AUTHORITY,
    CampaignSessionLifecycleStateV1,
    ProductiveEvidenceSessionPlanV1,
    _assert_public_endpoint_allowlist_aligned,
    _build_reachability_7200_plan,
    _campaign_durable_paths,
    _digest_v1,
    _resolve_venue_native_instrument_id_offline,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.disposition_v1 import (
    assert_campaign_not_tombstone_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.identity_v1 import (
    derive_r1_campaign_identity_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.models_v1 import (
    ProductiveCampaignR1RecoveryError,
)


def build_r1_active_preregistration_payload_v1(*, repository_sha: str) -> dict[str, Any]:
    """Structural twin of productive session preregistration for a fresh SHA/campaign."""
    _assert_public_endpoint_allowlist_aligned()
    identity = derive_r1_campaign_identity_v1(repository_sha=repository_sha)
    campaign_id = identity["campaign_id"]
    assert_campaign_not_tombstone_v1(campaign_id)
    venue_native = _resolve_venue_native_instrument_id_offline()
    campaign_paths = _campaign_durable_paths(campaign_id=campaign_id)

    sessions: list[ProductiveEvidenceSessionPlanV1] = []
    for idx, session_id in enumerate(
        (identity["session_01_id"], identity["session_02_id"]), start=1
    ):
        session_manifest = (
            "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
            f"campaigns/{campaign_id}/sessions/session_{idx:02d}_manifest.json"
        )
        sessions.append(
            ProductiveEvidenceSessionPlanV1(
                session_id=session_id,
                campaign_id=campaign_id,
                session_index=idx,
                lifecycle_initial_state=CampaignSessionLifecycleStateV1.PREREGISTERED.value,
                independent_session=True,
                resume_policy={
                    "process_restart_requires_same_session_id": True,
                    "process_restart_requires_explicit_resume_token": True,
                    "process_restart_increments_restart_generation_by_one": True,
                    "restart_is_not_a_new_independent_session": True,
                    "restart_cannot_fabricate_coverage": True,
                },
                restart_generation_initial=0,
                maximum_restart_generations=MAXIMUM_RESTART_GENERATIONS,
                planned_start_not_authorized=True,
                planned_end_condition=(
                    "COMPLETE_WHEN_SESSION_CYCLE_BUDGET_OR_OPERATOR_STOP;"
                    "ABORT_ON_FAIL_CLOSED_CRITERIA;"
                    "NO_AUTO_PROMOTION"
                ),
                maximum_cycles_per_session=MAXIMUM_CYCLES_PER_SESSION,
                maximum_sessions_per_run=MAXIMUM_SESSIONS_PER_RUN,
                expected_durable_paths={
                    "session_manifest_path": session_manifest,
                    "typed_volatility_persistence_path": campaign_paths[
                        "typed_volatility_persistence_path"
                    ],
                },
                no_runtime_side_effects=True,
            )
        )

    session_ids = tuple(s.session_id for s in sessions)
    public_md_plan: dict[str, Any] = {
        "venue": PUBLIC_MD_VENUE,
        "venue_scope": PUBLIC_MD_VENUE_SCOPE,
        "host": PUBLIC_MD_HOST,
        "transport": PUBLIC_MD_TRANSPORT,
        "credentials_required": False,
        "websocket_allowed": False,
        "private_endpoints_allowed": False,
        "order_endpoints_allowed": False,
        "mutation_methods_allowed": False,
        "allowed_http_methods": [PUBLIC_MD_ALLOWED_METHOD],
        "allowed_endpoints": list(PUBLIC_MD_ALLOWED_ENDPOINTS),
        "canonical_instrument_id": CANONICAL_INSTRUMENT_ID,
        "venue_native_instrument_id": venue_native,
        "venue_native_instrument_id_resolution": "EXISTING_VENUE_BINDING_AUTHORITY_ONLY",
        "venue_binding_authority": VENUE_BINDING_AUTHORITY,
        "instrument_substitution_forbidden": True,
        "network_authorized": False,
        "feed_activation_requires_separate_authorization": True,
        "orders_technically_excluded": True,
        "private_endpoints_excluded": True,
        "credentials_not_required": True,
        "plan_status": "PREREGISTERED_UNAUTHORIZED",
    }
    coverage_plan: dict[str, Any] = {
        "minimum_independent_sessions": MINIMUM_INDEPENDENT_SESSIONS,
        "minimum_distinct_sessions": MINIMUM_DISTINCT_SESSIONS,
        "minimum_distinct_evidence_records": MINIMUM_DISTINCT_EVIDENCE_RECORDS,
        "minimum_market_regimes": MINIMUM_MARKET_REGIMES,
        "minimum_volatility_regimes": MINIMUM_VOLATILITY_REGIMES,
        "minimum_instruments": MINIMUM_INSTRUMENTS,
        "minimum_computed_age_observations": MINIMUM_COMPUTED_AGE_OBSERVATIONS,
        "minimum_distinct_observations_per_age_bucket": (
            MINIMUM_DISTINCT_OBSERVATIONS_PER_AGE_BUCKET
        ),
        "research_age_grid_seconds": list(BOUND_RESEARCH_AGE_GRID_SECONDS),
        "age_bucket_observation_plan": {
            str(bucket): {
                "minimum_distinct_observations": MINIMUM_DISTINCT_OBSERVATIONS_PER_AGE_BUCKET,
                "synthetic_observation_forbidden": True,
            }
            for bucket in BOUND_RESEARCH_AGE_GRID_SECONDS
        },
        "market_regime_label_authority": REGIME_LABEL_AUTHORITY,
        "volatility_regime_label_authority": VOLATILITY_REGIME_LABEL_AUTHORITY,
        "enumerated_market_regime_names_invented": ENUMERATED_MARKET_REGIME_NAMES_INVENTED,
        "enumerated_volatility_regime_names_invented": (
            ENUMERATED_VOLATILITY_REGIME_NAMES_INVENTED
        ),
    }
    durable_path_plan: dict[str, Any] = {
        "productive_ledger_path": DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH,
        "quarantine_ledger_path": DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH,
        "join_projection_path": DEFAULT_JOIN_LEDGER_RELATIVE_PATH,
        "campaign_specific_paths": campaign_paths,
        "tmp_authority_prohibited": True,
        "parent_dirs_materialized_by_preregistration": False,
        "materialization_requires_separate_campaign_authorization": True,
        "paths_repository_relative": True,
        "paths_traversal_safe": True,
        "foreign_campaign_artifact_overwrite_forbidden": True,
    }
    provisional: dict[str, Any] = {
        "abort_block_criteria": list(ABORT_BLOCK_CRITERIA),
        "authority_state": AUTHORITY_STATE,
        "campaign_id": campaign_id,
        "campaign_purpose": CAMPAIGN_PURPOSE,
        "capability_id": CAPABILITY_ID,
        "coverage_plan": coverage_plan,
        "created_at_utc": CREATED_AT_UTC,
        "design_preregistration_digest": BOUND_DESIGN_PREREGISTRATION_DIGEST,
        "durable_path_plan": durable_path_plan,
        "enforcement_authorized": False,
        "evidence_write_authorized": False,
        "execution_authorized": False,
        "lifecycle_transitions": list(LIFECYCLE_TRANSITIONS),
        "network_authorized": False,
        "non_promotion_invariants": dict(NON_PROMOTION_INVARIANTS),
        "parameter_decision_authorized": False,
        "productive_preregistration_digest": BOUND_PRODUCTIVE_PREREGISTRATION_DIGEST,
        "public_md_plan": public_md_plan,
        "reachability_7200_plan": _build_reachability_7200_plan(
            campaign_id=campaign_id, session_ids=session_ids
        ),
        "repository_sha": str(repository_sha).strip(),
        "required_observation_bindings": list(REQUIRED_OBSERVATION_BINDINGS),
        "research_age_grid_seconds": list(BOUND_RESEARCH_AGE_GRID_SECONDS),
        "sample_event_time_bindings": dict(SAMPLE_EVENT_TIME_BINDINGS),
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "sessions": [s.to_dict() for s in sessions],
    }
    provisional["preregistration_digest"] = _digest_v1(provisional)
    return provisional


def verify_r1_active_preregistration_payload_v1(
    payload: dict[str, Any],
    *,
    expected_repository_sha: str,
    expected_campaign_id: str,
    expected_session_ids: tuple[str, ...],
) -> dict[str, Any]:
    """Structural verify for R1 prereg — not compared to frozen historical artifact."""
    if not isinstance(payload, dict):
        raise ProductiveCampaignR1RecoveryError("r1_prereg_not_object")
    recomputed = _digest_v1(payload)
    if recomputed != payload.get("preregistration_digest"):
        raise ProductiveCampaignR1RecoveryError("r1_prereg_digest_mismatch")
    if payload.get("repository_sha") != expected_repository_sha:
        raise ProductiveCampaignR1RecoveryError("r1_prereg_repository_sha_mismatch")
    if payload.get("campaign_id") != expected_campaign_id:
        raise ProductiveCampaignR1RecoveryError("r1_prereg_campaign_mismatch")
    assert_campaign_not_tombstone_v1(str(payload.get("campaign_id") or ""))
    sessions = payload.get("sessions") or []
    session_ids = tuple(str(s.get("session_id")) for s in sessions)
    if session_ids != expected_session_ids:
        raise ProductiveCampaignR1RecoveryError("r1_prereg_session_ids_mismatch")
    if payload.get("execution_authorized") is not False:
        raise ProductiveCampaignR1RecoveryError("r1_prereg_execution_must_be_unauthorized")
    if payload.get("network_authorized") is not False:
        raise ProductiveCampaignR1RecoveryError("r1_prereg_network_must_be_unauthorized")
    if payload.get("evidence_write_authorized") is not False:
        raise ProductiveCampaignR1RecoveryError("r1_prereg_evidence_write_must_be_unauthorized")
    md = payload.get("public_md_plan") or {}
    if list(md.get("allowed_http_methods") or []) != [PUBLIC_MD_ALLOWED_METHOD]:
        raise ProductiveCampaignR1RecoveryError("r1_prereg_md_method_not_get_only")
    reach = payload.get("reachability_7200_plan") or {}
    dist = reach.get("session_distribution") or {}
    if dist.get("early_estimate_producer_session_id") != expected_session_ids[0]:
        raise ProductiveCampaignR1RecoveryError("r1_prereg_early_session_mismatch")
    if dist.get("late_age_observation_session_id") != expected_session_ids[1]:
        raise ProductiveCampaignR1RecoveryError("r1_prereg_late_session_mismatch")
    return {
        "status": "PASS",
        "campaign_id": expected_campaign_id,
        "preregistration_digest": payload.get("preregistration_digest"),
        "session_ids": list(expected_session_ids),
        "repository_sha": expected_repository_sha,
    }
