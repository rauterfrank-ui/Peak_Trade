"""Campaign/session preregistration for productive max-age evidence accumulation.

Preregisters a versioned, digestsable campaign and independent sessions for a
later separately authorized public-read-only market-data campaign.

Hard bounds of this module:
- no runtime session start
- no network I/O
- no market-data fetch
- no evidence / ledger writes
- no parent-dir materialization
- no authorization issuance or consumption
- no threshold selection / enforcement
- no mutation of existing research preregistration digests
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from ops.bounded_futures_testnet_venue_binding_v0 import (
    OKX_EEA_PUBLIC_ENDPOINT_ALLOWLIST,
    PRODUCTION_INSTRUMENT_ID,
    default_okx_europe_xperp_production_binding,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    DEFAULT_JOIN_LEDGER_RELATIVE_PATH,
    DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH,
    DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH,
    MAX_PRODUCTIVE_BRIDGE_CYCLES_PER_SESSION,
    MAX_PRODUCTIVE_BRIDGE_SESSIONS_PER_RUN,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
    digest_excluding_keys,
    sha256_hex_text,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.preregistration_v1 import (
    RESEARCH_AGE_CANDIDATE_GRID_SECONDS,
    build_productive_evidence_accumulation_preregistration_v1,
)
from trading.master_v2.canonical_volatility_hot_path_contract_closure_v1 import (
    EXIT_PRECEDENCE_PRESERVED as HOT_PATH_EXIT_PRECEDENCE_PRESERVED,
    REVERSAL_REDUCE_FIRST_PRESERVED as HOT_PATH_REVERSAL_REDUCE_FIRST_PRESERVED,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    build_ratified_max_age_research_design_contract_v1,
)

SCHEMA_NAME = "canonical_volatility_numeric_max_age_productive_evidence_session_preregistration"
SCHEMA_VERSION = "v1"
CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_EVIDENCE_SESSION_PREREGISTRATION_V1"
)
REVIEW_MODE_ID = CAPABILITY_ID

BOUND_REPOSITORY_SHA = "e9c1871ea7b493cde9f49eb517910b1a7134fb5b"
BOUND_PRODUCTIVE_PREREGISTRATION_DIGEST = (
    "777e3dd8aa3458f8687cabbadf63016ac478b5385568ee3d54d22c119880a62e"
)
BOUND_DESIGN_PREREGISTRATION_DIGEST = (
    "965f6e09e50e434e363d380c2d62e43041a37ad7d87956e590609a16f011b537"
)
BOUND_RESEARCH_AGE_GRID_SECONDS: tuple[int, ...] = (60, 120, 300, 600, 900, 1800, 3600, 7200)

# Fixed issuance timestamp — digest-stable; not a runtime wallclock sample.
CREATED_AT_UTC = "2026-08-01T00:00:00Z"
AUTHORITY_STATE = "PREREGISTERED_UNAUTHORIZED"

CAMPAIGN_PURPOSE = (
    "Preregister a productive Canonical-Volatility numeric max-age research "
    "evidence accumulation campaign and independent sessions for a later "
    "separately authorized public-read-only market-data campaign; accumulate "
    "counterfactual age-grid evidence only; never select or enforce a threshold."
)

MINIMUM_INDEPENDENT_SESSIONS = 2
MINIMUM_DISTINCT_SESSIONS = 2
MINIMUM_DISTINCT_EVIDENCE_RECORDS = 8
MINIMUM_MARKET_REGIMES = 2
MINIMUM_VOLATILITY_REGIMES = 1
MINIMUM_INSTRUMENTS = 1
MINIMUM_COMPUTED_AGE_OBSERVATIONS = 1
MINIMUM_DISTINCT_OBSERVATIONS_PER_AGE_BUCKET = 1

MAXIMUM_RESTART_GENERATIONS = 16
MAXIMUM_CYCLES_PER_SESSION = MAX_PRODUCTIVE_BRIDGE_CYCLES_PER_SESSION
MAXIMUM_SESSIONS_PER_RUN = MAX_PRODUCTIVE_BRIDGE_SESSIONS_PER_RUN

PUBLIC_MD_VENUE = "OKX"
PUBLIC_MD_VENUE_SCOPE = "OKX_EEA_FUTURES_PUBLIC_MARKET_DATA"
PUBLIC_MD_HOST = "https://eea.okx.com"
PUBLIC_MD_TRANSPORT = "HTTPS_REST_GET_ONLY"
PUBLIC_MD_ALLOWED_METHOD = "GET"
PUBLIC_MD_ALLOWED_ENDPOINTS: tuple[str, ...] = (
    "/api/v5/public/time",
    "/api/v5/public/instruments",
    "/api/v5/public/mark-price",
    "/api/v5/market/ticker",
    "/api/v5/market/tickers",
)
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"
VENUE_BINDING_AUTHORITY = (
    "ops.bounded_futures_testnet_venue_binding_v0.default_okx_europe_xperp_production_binding"
)

REGIME_LABEL_AUTHORITY = "TYPED_FEATURE_REGIME_METADATA_AUTHORITY_ONLY"
VOLATILITY_REGIME_LABEL_AUTHORITY = "TYPED_OR_EXPLICIT_RESEARCH_LABEL_AUTHORITY_ONLY"
# Explicit: no invented fixed market/volatility regime name enumeration here.
ENUMERATED_MARKET_REGIME_NAMES_INVENTED = False
ENUMERATED_VOLATILITY_REGIME_NAMES_INVENTED = False

ARTIFACT_RELATIVE_PATH = (
    "config/research/"
    "canonical_volatility_numeric_max_age_productive_evidence_session_preregistration_v1.json"
)
SPEC_RELATIVE_PATH = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_"
    "EVIDENCE_SESSION_PREREGISTRATION_V1.md"
)

REQUIRED_OBSERVATION_BINDINGS: tuple[str, ...] = (
    "market_sample_id",
    "venue",
    "canonical_instrument_id",
    "venue_native_instrument_id",
    "event_time",
    "receive_time",
    "source_sequence_or_equivalent",
    "mark_price",
    "sample_digest",
    "volatility_estimate_id",
    "volatility_as_of_event_time",
    "computed_age_seconds",
    "session_id",
    "restart_generation",
    "market_regime_label",
    "volatility_regime_label",
)

SAMPLE_EVENT_TIME_BINDINGS: Mapping[str, Any] = {
    "CANONICAL_TIME_DOMAIN": "MARKET_EVENT_TIME",
    "RUNTIME_CYCLE_IS_NOT_MARKET_SAMPLE": True,
    "DECISION_EPOCH_IS_NOT_MARKET_SAMPLE": True,
    "REPEATED_POLL_RESULT_CANNOT_FABRICATE_MARKET_TIME": True,
    "DUPLICATE_SAMPLE_CANNOT_CREATE_NEW_AGE_OBSERVATION": True,
    "OUT_OF_ORDER_POLICY_MUST_USE_EXISTING_TYPED_POLICY": True,
    "DISTINCT_OBSERVATION_POLICY_MUST_USE_EXISTING_TYPED_POLICY": True,
}

NON_PROMOTION_INVARIANTS: Mapping[str, Any] = {
    "COUNTERFACTUAL_ONLY": True,
    "ENFORCEMENT_APPLIED": False,
    "MAX_AGE_THRESHOLD_SELECTED": False,
    "MAX_AGE_ENFORCEMENT_ENABLED": False,
    "ALPHA_SEMANTICS_CHANGED": False,
    "STATE_SEMANTICS_CHANGED": False,
    "COMPOSITION_AUTHORITY_CHANGED": False,
    "EXIT_PRECEDENCE_PRESERVED": True,
    "REVERSAL_REDUCE_FIRST_PRESERVED": True,
    "AUTO_PROMOTION_ALLOWED": False,
}

ABORT_BLOCK_CRITERIA: tuple[str, ...] = (
    "REPOSITORY_SHA_DRIFT",
    "PREREGISTRATION_DIGEST_DRIFT",
    "DESIGN_DIGEST_DRIFT",
    "CAMPAIGN_ID_REUSE",
    "UNAUTHORIZED_SESSION_START",
    "NETWORK_ACCESS_BEFORE_SEPARATE_AUTHORIZATION",
    "EVIDENCE_WRITE_BEFORE_SEPARATE_AUTHORIZATION",
    "ENDPOINT_HOST_METHOD_INSTRUMENT_DRIFT",
    "PRIVATE_ENDPOINT_OR_CREDENTIAL_REQUIREMENT",
    "MISSING_TYPED_VOLATILITY_BINDING",
    "SYNTHETIC_OR_FIXTURE_AUTHORITY",
    "DUPLICATE_OR_OUT_OF_ORDER_POLICY_DRIFT",
    "LEDGER_CHAIN_OR_SCHEMA_ERROR",
    "UNNATURAL_7200_BUCKET_SYNTHESIS",
    "THRESHOLD_SELECTION",
    "ENFORCEMENT_ACTIVATION",
    "ALPHA_STATE_COMPOSITION_MUTATION",
)


class CampaignSessionLifecycleStateV1(str, Enum):
    PREREGISTERED = "PREREGISTERED"
    AUTHORIZED = "AUTHORIZED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


LIFECYCLE_TRANSITIONS: tuple[str, ...] = (
    "PREREGISTERED→AUTHORIZED(separate_authorization)",
    "AUTHORIZED→ACTIVE",
    "ACTIVE→COMPLETED|ABORTED",
)


def _deterministic_campaign_id(*, repository_sha: str) -> str:
    material = "|".join(
        [
            SCHEMA_NAME,
            SCHEMA_VERSION,
            CAPABILITY_ID,
            repository_sha,
            "productive_evidence_campaign",
        ]
    )
    suffix = sha256_hex_text(material)[:16]
    return f"cv_maxage_productive_evidence_campaign_v1_{suffix}"


def _deterministic_session_id(*, campaign_id: str, session_index: int) -> str:
    material = "|".join([campaign_id, f"session_index={session_index}", SCHEMA_VERSION])
    suffix = sha256_hex_text(material)[:12]
    return f"{campaign_id}_s{session_index:02d}_{suffix}"


def _resolve_venue_native_instrument_id_offline() -> str:
    """Resolve via existing venue-binding authority only (no network, no invent)."""
    binding = default_okx_europe_xperp_production_binding()
    native = str(binding.instrument_id or "").strip()
    if not native:
        raise ProductiveEvidenceAccumulationError("venue_native_instrument_id_unresolved")
    if native != PRODUCTION_INSTRUMENT_ID:
        raise ProductiveEvidenceAccumulationError("venue_binding_instrument_drift")
    if native != CANONICAL_INSTRUMENT_ID:
        raise ProductiveEvidenceAccumulationError("canonical_instrument_binding_drift")
    return native


def _assert_public_endpoint_allowlist_aligned() -> None:
    expected = frozenset(PUBLIC_MD_ALLOWED_ENDPOINTS)
    if expected != OKX_EEA_PUBLIC_ENDPOINT_ALLOWLIST:
        raise ProductiveEvidenceAccumulationError("public_endpoint_allowlist_drift")


def _campaign_durable_paths(*, campaign_id: str) -> dict[str, str]:
    base = (
        "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
        f"campaigns/{campaign_id}"
    )
    return {
        "typed_volatility_persistence_path": f"{base}/typed_volatility_persistence.jsonl",
        "campaign_manifest_path": f"{base}/campaign_manifest.json",
        "session_manifests_glob": f"{base}/sessions/session_*_manifest.json",
        "terminal_campaign_verdict_path": f"{base}/terminal_campaign_verdict.json",
        "evaluability_report_path": f"{base}/evaluability_report.json",
    }


def _build_reachability_7200_plan(
    *, campaign_id: str, session_ids: Sequence[str]
) -> dict[str, Any]:
    early_session = session_ids[0]
    late_session = session_ids[1]
    return {
        "target_bucket_seconds": 7200,
        "natural_reachability_required": True,
        "synthetic_market_time_prohibited": True,
        "poll_cycles_are_not_market_time": True,
        "duplicate_samples_are_not_new_age_observations": True,
        "artificially_stale_timestamp_prohibited": True,
        "volatility_estimate_reuse_outside_lifecycle_prohibited": True,
        "minimum_campaign_event_time_span_seconds": 7201,
        "minimum_campaign_wallclock_span_seconds": 7201,
        "session_distribution": {
            "early_estimate_producer_session_id": early_session,
            "late_age_observation_session_id": late_session,
            "independent_sessions": list(session_ids),
            "note": (
                "Session 1 produces an early valid VolatilityEstimate whose real "
                "as_of_event_time is retained. Later distinct market samples in the "
                "same or subsequent independent session(s) naturally increase "
                "computed_age_seconds = event_time - volatility_as_of_event_time "
                "until >= 7200. Bucket coverage may span multiple sessions and "
                "process restarts; no single session is guaranteed to cover every bucket."
            ),
        },
        "estimate_history_retention": {
            "as_of_event_time_immutable_after_production": True,
            "restarts_may_reload_same_estimate_history": True,
            "reload_does_not_count_as_new_estimate": True,
            "resume_requires_same_session_id_plus_resume_token_and_restart_generation_plus_one": True,
        },
        "fail_closed_if_unreachable": {
            "coverage_incomplete_when_7200_bucket_missing": True,
            "unnatural_synthesis_is_abort": True,
            "terminal_verdict_on_missing_natural_reachability": "COVERAGE_INCOMPLETE_FAIL_CLOSED",
        },
        "repository_runtime_bounds": {
            "maximum_cycles_per_session": MAXIMUM_CYCLES_PER_SESSION,
            "minimum_independent_sessions": MINIMUM_INDEPENDENT_SESSIONS,
            "maximum_sessions_per_run": MAXIMUM_SESSIONS_PER_RUN,
            "no_exact_polling_cadence_as_market_time": True,
            "campaign_may_accumulate_across_sessions_and_process_restarts": True,
        },
        "campaign_id": campaign_id,
    }


@dataclass(frozen=True)
class ProductiveEvidenceSessionPlanV1:
    session_id: str
    campaign_id: str
    session_index: int
    lifecycle_initial_state: str
    independent_session: bool
    resume_policy: Mapping[str, Any]
    restart_generation_initial: int
    maximum_restart_generations: int
    planned_start_not_authorized: bool
    planned_end_condition: str
    maximum_cycles_per_session: int
    maximum_sessions_per_run: int
    expected_durable_paths: Mapping[str, str]
    no_runtime_side_effects: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "expected_durable_paths": dict(self.expected_durable_paths),
            "independent_session": self.independent_session,
            "lifecycle_initial_state": self.lifecycle_initial_state,
            "maximum_cycles_per_session": self.maximum_cycles_per_session,
            "maximum_restart_generations": self.maximum_restart_generations,
            "maximum_sessions_per_run": self.maximum_sessions_per_run,
            "no_runtime_side_effects": self.no_runtime_side_effects,
            "planned_end_condition": self.planned_end_condition,
            "planned_start_not_authorized": self.planned_start_not_authorized,
            "restart_generation_initial": self.restart_generation_initial,
            "resume_policy": dict(self.resume_policy),
            "session_id": self.session_id,
            "session_index": self.session_index,
        }


@dataclass(frozen=True)
class ProductiveEvidenceCampaignSessionPreregistrationV1:
    schema_name: str
    schema_version: str
    campaign_id: str
    campaign_purpose: str
    repository_sha: str
    productive_preregistration_digest: str
    design_preregistration_digest: str
    research_age_grid_seconds: tuple[int, ...]
    created_at_utc: str
    preregistration_digest: str
    authority_state: str
    execution_authorized: bool
    evidence_write_authorized: bool
    network_authorized: bool
    parameter_decision_authorized: bool
    enforcement_authorized: bool
    sessions: tuple[ProductiveEvidenceSessionPlanV1, ...]
    public_md_plan: Mapping[str, Any]
    sample_event_time_bindings: Mapping[str, Any]
    required_observation_bindings: tuple[str, ...]
    coverage_plan: Mapping[str, Any]
    reachability_7200_plan: Mapping[str, Any]
    durable_path_plan: Mapping[str, Any]
    non_promotion_invariants: Mapping[str, Any]
    abort_block_criteria: tuple[str, ...]
    lifecycle_transitions: tuple[str, ...]
    capability_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "abort_block_criteria": list(self.abort_block_criteria),
            "authority_state": self.authority_state,
            "campaign_id": self.campaign_id,
            "campaign_purpose": self.campaign_purpose,
            "capability_id": self.capability_id,
            "coverage_plan": dict(self.coverage_plan),
            "created_at_utc": self.created_at_utc,
            "design_preregistration_digest": self.design_preregistration_digest,
            "durable_path_plan": dict(self.durable_path_plan),
            "enforcement_authorized": self.enforcement_authorized,
            "evidence_write_authorized": self.evidence_write_authorized,
            "execution_authorized": self.execution_authorized,
            "lifecycle_transitions": list(self.lifecycle_transitions),
            "network_authorized": self.network_authorized,
            "non_promotion_invariants": dict(self.non_promotion_invariants),
            "parameter_decision_authorized": self.parameter_decision_authorized,
            "preregistration_digest": self.preregistration_digest,
            "productive_preregistration_digest": self.productive_preregistration_digest,
            "public_md_plan": dict(self.public_md_plan),
            "reachability_7200_plan": dict(self.reachability_7200_plan),
            "repository_sha": self.repository_sha,
            "required_observation_bindings": list(self.required_observation_bindings),
            "research_age_grid_seconds": list(self.research_age_grid_seconds),
            "sample_event_time_bindings": dict(self.sample_event_time_bindings),
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "sessions": [s.to_dict() for s in self.sessions],
        }


def _digest_v1(payload: Mapping[str, Any]) -> str:
    return digest_excluding_keys(payload, exclude=("preregistration_digest",))


def build_productive_evidence_campaign_session_preregistration_v1() -> (
    ProductiveEvidenceCampaignSessionPreregistrationV1
):
    """Build the immutable campaign/session preregistration artifact (no side effects)."""
    _assert_public_endpoint_allowlist_aligned()

    productive = build_productive_evidence_accumulation_preregistration_v1()
    design = build_ratified_max_age_research_design_contract_v1()

    if productive.productive_preregistration_digest != BOUND_PRODUCTIVE_PREREGISTRATION_DIGEST:
        raise ProductiveEvidenceAccumulationError(
            "bound_productive_preregistration_digest_mismatch"
        )
    if design.preregistration_digest != BOUND_DESIGN_PREREGISTRATION_DIGEST:
        raise ProductiveEvidenceAccumulationError("bound_design_preregistration_digest_mismatch")
    if tuple(RESEARCH_AGE_CANDIDATE_GRID_SECONDS) != BOUND_RESEARCH_AGE_GRID_SECONDS:
        raise ProductiveEvidenceAccumulationError("bound_research_age_grid_mismatch")
    if not HOT_PATH_EXIT_PRECEDENCE_PRESERVED:
        raise ProductiveEvidenceAccumulationError("exit_precedence_not_preserved")
    if not HOT_PATH_REVERSAL_REDUCE_FIRST_PRESERVED:
        raise ProductiveEvidenceAccumulationError("reversal_reduce_first_not_preserved")

    repository_sha = BOUND_REPOSITORY_SHA
    campaign_id = _deterministic_campaign_id(repository_sha=repository_sha)
    venue_native = _resolve_venue_native_instrument_id_offline()
    campaign_paths = _campaign_durable_paths(campaign_id=campaign_id)

    sessions: list[ProductiveEvidenceSessionPlanV1] = []
    for idx in range(1, MINIMUM_INDEPENDENT_SESSIONS + 1):
        session_id = _deterministic_session_id(campaign_id=campaign_id, session_index=idx)
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
    if len(set(session_ids)) != len(session_ids):
        raise ProductiveEvidenceAccumulationError("session_ids_not_unique")
    if any(s.lifecycle_initial_state != "PREREGISTERED" for s in sessions):
        raise ProductiveEvidenceAccumulationError("session_must_start_preregistered")
    if any(s.lifecycle_initial_state == "ACTIVE" for s in sessions):
        raise ProductiveEvidenceAccumulationError("session_already_active_forbidden")

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
        "repository_sha": repository_sha,
        "required_observation_bindings": list(REQUIRED_OBSERVATION_BINDINGS),
        "research_age_grid_seconds": list(BOUND_RESEARCH_AGE_GRID_SECONDS),
        "sample_event_time_bindings": dict(SAMPLE_EVENT_TIME_BINDINGS),
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "sessions": [s.to_dict() for s in sessions],
    }
    digest = _digest_v1(provisional)

    return ProductiveEvidenceCampaignSessionPreregistrationV1(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        campaign_id=campaign_id,
        campaign_purpose=CAMPAIGN_PURPOSE,
        repository_sha=repository_sha,
        productive_preregistration_digest=BOUND_PRODUCTIVE_PREREGISTRATION_DIGEST,
        design_preregistration_digest=BOUND_DESIGN_PREREGISTRATION_DIGEST,
        research_age_grid_seconds=BOUND_RESEARCH_AGE_GRID_SECONDS,
        created_at_utc=CREATED_AT_UTC,
        preregistration_digest=digest,
        authority_state=AUTHORITY_STATE,
        execution_authorized=False,
        evidence_write_authorized=False,
        network_authorized=False,
        parameter_decision_authorized=False,
        enforcement_authorized=False,
        sessions=tuple(sessions),
        public_md_plan=public_md_plan,
        sample_event_time_bindings=dict(SAMPLE_EVENT_TIME_BINDINGS),
        required_observation_bindings=REQUIRED_OBSERVATION_BINDINGS,
        coverage_plan=coverage_plan,
        reachability_7200_plan=_build_reachability_7200_plan(
            campaign_id=campaign_id, session_ids=session_ids
        ),
        durable_path_plan=durable_path_plan,
        non_promotion_invariants=dict(NON_PROMOTION_INVARIANTS),
        abort_block_criteria=ABORT_BLOCK_CRITERIA,
        lifecycle_transitions=LIFECYCLE_TRANSITIONS,
        capability_id=CAPABILITY_ID,
    )


def verify_productive_evidence_campaign_session_preregistration_v1(
    contract: ProductiveEvidenceCampaignSessionPreregistrationV1 | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Read-only verification of schema, digests, bindings, coverage, reachability."""
    expected = build_productive_evidence_campaign_session_preregistration_v1()
    if contract is None:
        actual = expected
        payload = expected.to_dict()
    elif isinstance(contract, ProductiveEvidenceCampaignSessionPreregistrationV1):
        actual = contract
        payload = contract.to_dict()
    else:
        payload = dict(contract)
        actual = expected

    recomputed = _digest_v1(payload)
    if recomputed != payload.get("preregistration_digest"):
        raise ProductiveEvidenceAccumulationError("session_preregistration_digest_mismatch")
    if payload.get("preregistration_digest") != expected.preregistration_digest:
        raise ProductiveEvidenceAccumulationError("session_preregistration_digest_drift")
    if payload.get("repository_sha") != BOUND_REPOSITORY_SHA:
        raise ProductiveEvidenceAccumulationError("repository_sha_binding_mismatch")
    if payload.get("productive_preregistration_digest") != BOUND_PRODUCTIVE_PREREGISTRATION_DIGEST:
        raise ProductiveEvidenceAccumulationError("productive_digest_binding_mismatch")
    if payload.get("design_preregistration_digest") != BOUND_DESIGN_PREREGISTRATION_DIGEST:
        raise ProductiveEvidenceAccumulationError("design_digest_binding_mismatch")
    if list(payload.get("research_age_grid_seconds") or []) != list(
        BOUND_RESEARCH_AGE_GRID_SECONDS
    ):
        raise ProductiveEvidenceAccumulationError("research_age_grid_binding_mismatch")
    if payload.get("execution_authorized") is not False:
        raise ProductiveEvidenceAccumulationError("execution_must_be_unauthorized")
    if payload.get("network_authorized") is not False:
        raise ProductiveEvidenceAccumulationError("network_must_be_unauthorized")
    if payload.get("evidence_write_authorized") is not False:
        raise ProductiveEvidenceAccumulationError("evidence_write_must_be_unauthorized")
    if payload.get("parameter_decision_authorized") is not False:
        raise ProductiveEvidenceAccumulationError("parameter_decision_must_be_unauthorized")
    if payload.get("enforcement_authorized") is not False:
        raise ProductiveEvidenceAccumulationError("enforcement_must_be_unauthorized")

    sessions = payload.get("sessions") or []
    if len(sessions) < MINIMUM_INDEPENDENT_SESSIONS:
        raise ProductiveEvidenceAccumulationError("minimum_independent_sessions_unmet")
    session_ids = [str(s["session_id"]) for s in sessions]
    if len(set(session_ids)) != len(session_ids):
        raise ProductiveEvidenceAccumulationError("session_ids_not_unique")
    for sess in sessions:
        if sess.get("lifecycle_initial_state") != "PREREGISTERED":
            raise ProductiveEvidenceAccumulationError("session_not_preregistered")
        if sess.get("lifecycle_initial_state") == "ACTIVE":
            raise ProductiveEvidenceAccumulationError("session_already_active")
        if int(sess.get("maximum_cycles_per_session", 0)) > MAXIMUM_CYCLES_PER_SESSION:
            raise ProductiveEvidenceAccumulationError("cycles_per_session_exceeded")
        if int(sess.get("maximum_sessions_per_run", 0)) > MAXIMUM_SESSIONS_PER_RUN:
            raise ProductiveEvidenceAccumulationError("sessions_per_run_exceeded")
        if sess.get("no_runtime_side_effects") is not True:
            raise ProductiveEvidenceAccumulationError("runtime_side_effects_forbidden")
        if sess.get("planned_start_not_authorized") is not True:
            raise ProductiveEvidenceAccumulationError("planned_start_must_be_unauthorized")

    md = payload.get("public_md_plan") or {}
    if md.get("venue") != PUBLIC_MD_VENUE:
        raise ProductiveEvidenceAccumulationError("public_md_venue_mismatch")
    if md.get("host") != PUBLIC_MD_HOST:
        raise ProductiveEvidenceAccumulationError("public_md_host_mismatch")
    if list(md.get("allowed_http_methods") or []) != [PUBLIC_MD_ALLOWED_METHOD]:
        raise ProductiveEvidenceAccumulationError("public_md_method_not_get_only")
    if list(md.get("allowed_endpoints") or []) != list(PUBLIC_MD_ALLOWED_ENDPOINTS):
        raise ProductiveEvidenceAccumulationError("public_md_endpoints_mismatch")
    if md.get("private_endpoints_allowed") is not False:
        raise ProductiveEvidenceAccumulationError("private_endpoints_must_be_excluded")
    if md.get("order_endpoints_allowed") is not False:
        raise ProductiveEvidenceAccumulationError("order_endpoints_must_be_excluded")
    if md.get("mutation_methods_allowed") is not False:
        raise ProductiveEvidenceAccumulationError("mutation_methods_must_be_excluded")
    if md.get("canonical_instrument_id") != CANONICAL_INSTRUMENT_ID:
        raise ProductiveEvidenceAccumulationError("instrument_binding_mismatch")
    if md.get("network_authorized") is not False:
        raise ProductiveEvidenceAccumulationError("md_network_must_be_unauthorized")

    durable = payload.get("durable_path_plan") or {}
    for key in ("productive_ledger_path", "quarantine_ledger_path", "join_projection_path"):
        path = str(durable.get(key) or "")
        if not path or path.startswith("/tmp") or "/tmp/" in path:
            raise ProductiveEvidenceAccumulationError("tmp_authority_prohibited")
        if path.startswith("/") or ".." in Path(path).parts:
            raise ProductiveEvidenceAccumulationError("durable_path_not_repo_relative_safe")
    if durable.get("parent_dirs_materialized_by_preregistration") is not False:
        raise ProductiveEvidenceAccumulationError("parent_dir_materialization_forbidden")

    reach = payload.get("reachability_7200_plan") or {}
    if reach.get("target_bucket_seconds") != 7200:
        raise ProductiveEvidenceAccumulationError("reachability_7200_missing")
    if reach.get("synthetic_market_time_prohibited") is not True:
        raise ProductiveEvidenceAccumulationError("synthetic_market_time_must_be_prohibited")
    if int(reach.get("minimum_campaign_event_time_span_seconds") or 0) <= 7200:
        raise ProductiveEvidenceAccumulationError("event_time_span_requirement_incomplete")
    if reach.get("natural_reachability_required") is not True:
        raise ProductiveEvidenceAccumulationError("natural_reachability_required")

    inv = payload.get("non_promotion_invariants") or {}
    for key, expected_value in NON_PROMOTION_INVARIANTS.items():
        if inv.get(key) is not expected_value:
            raise ProductiveEvidenceAccumulationError(f"non_promotion_invariant_drift:{key}")

    coverage = payload.get("coverage_plan") or {}
    if coverage.get("enumerated_market_regime_names_invented") is not False:
        raise ProductiveEvidenceAccumulationError("invented_market_regime_names_forbidden")
    if coverage.get("enumerated_volatility_regime_names_invented") is not False:
        raise ProductiveEvidenceAccumulationError("invented_volatility_regime_names_forbidden")

    if isinstance(actual, ProductiveEvidenceCampaignSessionPreregistrationV1):
        schema_name = actual.schema_name
    else:
        schema_name = payload.get("schema_name")
    return {
        "status": "PASS",
        "schema_name": schema_name,
        "schema_version": SCHEMA_VERSION,
        "campaign_id": payload.get("campaign_id"),
        "session_ids": session_ids,
        "preregistration_digest": payload.get("preregistration_digest"),
        "repository_sha": payload.get("repository_sha"),
        "execution_authorized": False,
        "network_authorized": False,
        "evidence_write_authorized": False,
        "reachability_7200_plan_complete": True,
        "parent_dirs_materialized": False,
        "capability_id": CAPABILITY_ID,
        "review_mode": REVIEW_MODE_ID,
    }


def assert_preregistration_does_not_materialize_paths_v1(*, repo_root: Path) -> None:
    """Confirm campaign parent dirs are not created by build/verify alone."""
    before = build_productive_evidence_campaign_session_preregistration_v1()
    campaign_paths = before.durable_path_plan["campaign_specific_paths"]
    parent = (Path(repo_root) / campaign_paths["campaign_manifest_path"]).parent
    existed_before = parent.exists()
    verify_productive_evidence_campaign_session_preregistration_v1(before)
    if not existed_before and parent.exists():
        raise ProductiveEvidenceAccumulationError("campaign_parent_dir_materialized")


def render_session_preregistration_v1() -> dict[str, Any]:
    """Return JSON-serializable preregistration payload (read-only)."""
    return build_productive_evidence_campaign_session_preregistration_v1().to_dict()


def load_and_verify_session_preregistration_artifact_v1(
    *,
    artifact_path: Path,
) -> dict[str, Any]:
    """Load a frozen artifact JSON and verify against the builder (read-only)."""
    import json

    payload = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
    return verify_productive_evidence_campaign_session_preregistration_v1(payload)
