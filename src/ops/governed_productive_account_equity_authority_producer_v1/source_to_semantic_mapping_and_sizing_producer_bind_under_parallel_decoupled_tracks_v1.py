"""Ratify CURRENT_PRODUCTIVE source→semantic mapping under parallel-decoupled tracks.

Consumes Owner-GO
OWNER_GO_RATIFY_SOURCE_TO_SEMANTIC_MAPPING_AND_BIND_AVAILABLE_FOR_SIZING_
PRODUCER_UNDER_PARALLEL_DECOUPLED_TRACKS_V1.

Offline/contract-only: no GET, no POST, no numeric CURRENT venue bind.
Producer wrap is the ratified Source→Semantic boundary for OPTION_B.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Tuple

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    REQUIRED_SETTLEMENT_CURRENCY,
    RISK_EQUITY_DIMENSION,
    evaluate_step_29p_capital_risk_admissibility_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY,
    CURRENT_PRODUCTIVE_SELECTED_AVAILABLE_FOR_SIZING_SOURCE,
    GOVERNED_PRODUCER_CREATED,
    LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE,
    MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING,
    P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_RESOLVED,
    RECONCILIATION_CONTRACT_CREATED,
    SEMANTIC_MAPPING_PROVEN,
    SOURCE_SELECTED,
    SOURCE_SELECTED_OBJECT,
    SOURCE_TO_SEMANTIC_MAPPING_RATIFIED_UNDER_PARALLEL_DECOUPLED_TRACKS_V1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    OBSERVATION_SURFACE,
    PRODUCER_IDENTITY,
    CurrentProductiveUsdcFreeMarginObservationV1,
    bind_step_29p_typed_equity_from_risk_capital_v1,
    produce_current_productive_29p_risk_capital_v1,
    reject_direct_avail_eq_29p_claim_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    CurrentProductiveAccountEligibilityFactV1,
    CurrentProductiveP01ReductionFactV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.running_account_equity_parallel_decoupled_tracks_authority_interface_reconciliation_contract_v1 import (
    AUTHORITY_MODEL,
    DIMENSION_ID,
    OBSERVATION_IS_NOT_AUTHORITY,
    OWNER_DECISION_1,
    PARALLEL_DECOUPLED_TRACKS_AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_CREATED,
    SILENT_EQUIVALENCE_OR_SUBSTITUTION_FORBIDDEN,
    build_running_account_equity_parallel_decoupled_tracks_authority_interface_reconciliation_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u04_pending_order_reservation_or_account_equity_mapping_v1 import (
    reject_eq_as_source_authority_v1,
)

OWNER_GO = (
    "OWNER_GO_RATIFY_SOURCE_TO_SEMANTIC_MAPPING_AND_BIND_AVAILABLE_FOR_SIZING_"
    "PRODUCER_UNDER_PARALLEL_DECOUPLED_TRACKS_V1"
)
EXPECTED_ORIGIN_MAIN_SHA = "389cc5f91da08d30c9ae65af05b6d9f914e8ac45"
SCHEMA_CLASS = (
    "SOURCE_TO_SEMANTIC_MAPPING_AND_SIZING_PRODUCER_BIND_UNDER_PARALLEL_DECOUPLED_TRACKS_V1"
)
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORIZATION_EFFECT = "NONE"

SOURCE_OBJECT = CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY
SOURCE_INPUT = OBSERVATION_SURFACE
TARGET_SEMANTIC = RISK_EQUITY_DIMENSION
SETTLEMENT_CURRENCY = REQUIRED_SETTLEMENT_CURRENCY
TRANSFORM = CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA

NUMERIC_CURRENT_VENUE_VALUE_BOUND = False
NETWORK_ACCESS_PERFORMED = False
EXTERNAL_EFFECT_AUTHORIZED = False
QUARANTINE_USED_AS_AUTHORITY = False

NEXT_OWNER_GO_CANDIDATE = (
    "OWNER_GO_REQUIRED_TO_PERFORM_FRESH_TRUSTED_READ_ONLY_GET_OF_DETAILS_USDC_"
    "AVAILEQ_AND_PRODUCE_29P_SIZING_VALUE_V1"
)

CANONICAL_PACK_RELPATH = (
    "evidence/ops/source_to_semantic_mapping_and_sizing_producer_bind_"
    "under_parallel_decoupled_tracks_v1/2026-09-22T062500Z"
)

FALSE_TOKEN = "false"
TRUE_TOKEN = "true"


class SourceToSemanticMappingBindError(ValueError):
    """Fail-closed mapping ratification / offline proof violation."""


@dataclass(frozen=True)
class OfflineStep29PE2EProofResultV1:
    produced: str
    dimension_id: str
    producer_identity: str
    typed_equity_raw: str
    typed_source_field: str
    step_29p_evaluated: str
    reason_codes: Tuple[str, ...]


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def reject_consume_execute_after_mapping_ratification_v1(*, wp_label: str) -> None:
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is True:
        raise SourceToSemanticMappingBindError(
            f"CONSUME_BASELINE_SUPERSEDED_BY_MAPPING_RATIFICATION_V1:{wp_label}"
        )


def _require_ratified_mapping_pins_v1() -> None:
    if SOURCE_TO_SEMANTIC_MAPPING_RATIFIED_UNDER_PARALLEL_DECOUPLED_TRACKS_V1 is not True:
        raise SourceToSemanticMappingBindError("MAPPING_RATIFICATION_FLAG_FALSE")
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not True:
        raise SourceToSemanticMappingBindError("CANONICALLY_VALID_MAPPING_FALSE")
    if SEMANTIC_MAPPING_PROVEN is not True:
        raise SourceToSemanticMappingBindError("SEMANTIC_MAPPING_PROVEN_FALSE")
    if MAPPING_PROVEN is not True:
        raise SourceToSemanticMappingBindError("MAPPING_PROVEN_FALSE")
    if MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING is not True:
        raise SourceToSemanticMappingBindError("MAPPED_TO_SIZING_FALSE")
    if SOURCE_SELECTED is not True:
        raise SourceToSemanticMappingBindError("SOURCE_SELECTED_FALSE")
    if SOURCE_SELECTED_OBJECT != SOURCE_OBJECT:
        raise SourceToSemanticMappingBindError("SOURCE_SELECTED_OBJECT_DRIFT")
    if CURRENT_PRODUCTIVE_SELECTED_AVAILABLE_FOR_SIZING_SOURCE != SOURCE_OBJECT:
        raise SourceToSemanticMappingBindError("CURRENT_PRODUCTIVE_SELECTED_SOURCE_DRIFT")
    if PRODUCER_IDENTITY != SOURCE_OBJECT:
        raise SourceToSemanticMappingBindError("PRODUCER_IDENTITY_DRIFT")
    if TRANSFORM != "DETAILS_USDC_AVAILEQ_MINUS_CONDITIONAL_P01_USDC_V1":
        raise SourceToSemanticMappingBindError("TRANSFORM_DRIFT")
    if GOVERNED_PRODUCER_CREATED is not False:
        raise SourceToSemanticMappingBindError("LEGACY_GOVERNED_PRODUCER_SLOT_MUST_STAY_FALSE")
    if RECONCILIATION_CONTRACT_CREATED is not False:
        raise SourceToSemanticMappingBindError("OPTION_D_RECONCILIATION_MUST_STAY_FALSE")
    if LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE is not False:
        raise SourceToSemanticMappingBindError("LEGACY_RECONSTRUCTION_MUST_STAY_FALSE")
    if PARALLEL_DECOUPLED_TRACKS_AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_CREATED is not True:
        raise SourceToSemanticMappingBindError("PARALLEL_TRACKS_CONTRACT_MISSING")
    if OWNER_DECISION_1 != "C":
        raise SourceToSemanticMappingBindError("OWNER_DECISION_1_DRIFT")


def _require_parallel_track_separation_v1() -> None:
    build_running_account_equity_parallel_decoupled_tracks_authority_interface_reconciliation_contract_v1(
        contract_id="PARALLEL_TRACKS_SEPARATION_GUARD_FIXTURE"
    )


def prove_static_producer_to_step29p_trace_v1() -> dict[str, str]:
    _require_ratified_mapping_pins_v1()
    return {
        "source_object": SOURCE_OBJECT,
        "source_input_class": "TYPED_CURRENT_VENUE_OBSERVATION_EVIDENCE_NOT_AUTHORITY",
        "source_input_surface": SOURCE_INPUT,
        "transform": TRANSFORM,
        "target_semantic": TARGET_SEMANTIC,
        "settlement_currency": SETTLEMENT_CURRENCY,
        "producer_module": (
            "current_productive_29p_risk_capital_model_v1.produce_current_productive_29p_risk_capital_v1"
        ),
        "bind_module": (
            "current_productive_29p_risk_capital_model_v1.bind_step_29p_typed_equity_from_risk_capital_v1"
        ),
        "consumer_module": (
            "step_29p_capital_risk_admissibility_v1.evaluate_step_29p_capital_risk_admissibility_v1"
        ),
        "u04_double_subtraction_guard": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION,
        "observation_is_not_authority": str(OBSERVATION_IS_NOT_AUTHORITY),
        "silent_substitution_forbidden": str(SILENT_EQUIVALENCE_OR_SUBSTITUTION_FORBIDDEN),
    }


def prove_u04_double_subtraction_absent_v1(
    *,
    observation: CurrentProductiveUsdcFreeMarginObservationV1,
    p01: CurrentProductiveP01ReductionFactV1,
    eligibility: CurrentProductiveAccountEligibilityFactV1,
    u04_present: bool,
) -> None:
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
        CurrentProductiveU04ReservationFactV1,
    )

    u04 = None
    if u04_present:
        u04 = CurrentProductiveU04ReservationFactV1(
            fact_id="CURRENT_PRODUCTIVE_U04_PENDING_ORDER_RESERVATION",
            value="10",
            settlement_currency="USDC",
            bound_account_identity=observation.bound_account_identity,
            bound_venue_identity=observation.bound_venue_identity,
            bound_td_mode=observation.bound_td_mode,
            decision_epoch=observation.decision_epoch,
            observed_at_as_of=observation.observed_at_as_of,
            age_seconds="1",
            freshness_max_age="5",
            provenance_digest="a" * 64,
            source_class="RESERVATION",
            empty_reservation_proven="false",
        )
    output = produce_current_productive_29p_risk_capital_v1(
        observation=observation,
        p01=p01,
        eligibility=eligibility,
        u04=u04,
    )
    if u04_present and output.produced != FALSE_TOKEN:
        raise SourceToSemanticMappingBindError("U04_DOUBLE_SUBTRACTION_NOT_BLOCKED")
    if not u04_present and output.produced != TRUE_TOKEN:
        raise SourceToSemanticMappingBindError("BASE_PRODUCE_FAILED_WITHOUT_U04")


def prove_p01_applies_without_directive_fail_closed_v1(
    *,
    observation: CurrentProductiveUsdcFreeMarginObservationV1,
    p01_applies: CurrentProductiveP01ReductionFactV1,
    eligibility: CurrentProductiveAccountEligibilityFactV1,
) -> None:
    if P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_RESOLVED is True:
        raise SourceToSemanticMappingBindError("P01_DIRECTIVE_TEST_PRECONDITION_DRIFT")
    output = produce_current_productive_29p_risk_capital_v1(
        observation=observation,
        p01=p01_applies,
        eligibility=eligibility,
    )
    if output.produced != FALSE_TOKEN:
        raise SourceToSemanticMappingBindError("P01_APPLIES_WITHOUT_DIRECTIVE_MUST_FAIL_CLOSED")
    if "P01_APPLIES_WITHOUT_CANONICAL_DIRECTIVE_SOURCE" not in output.reason_codes:
        raise SourceToSemanticMappingBindError("P01_FAIL_CLOSED_REASON_MISSING")


def run_offline_step29p_e2e_proof_v1(
    *,
    observation: CurrentProductiveUsdcFreeMarginObservationV1,
    p01: CurrentProductiveP01ReductionFactV1,
    eligibility: CurrentProductiveAccountEligibilityFactV1,
    fresh_pretrade_get_status: str = FreshPretradeGetStatusV1.MISSING.value,
    live_account_bound_status: str = LiveAccountBoundStatusV1.MISSING.value,
) -> OfflineStep29PE2EProofResultV1:
    _require_ratified_mapping_pins_v1()
    output = produce_current_productive_29p_risk_capital_v1(
        observation=observation,
        p01=p01,
        eligibility=eligibility,
    )
    if output.produced != TRUE_TOKEN:
        raise SourceToSemanticMappingBindError(
            f"PRODUCER_OUTPUT_NOT_PRODUCED:{','.join(output.reason_codes)}"
        )
    if output.dimension_id != TARGET_SEMANTIC:
        raise SourceToSemanticMappingBindError("DIMENSION_MISMATCH")
    if output.producer_identity != SOURCE_OBJECT:
        raise SourceToSemanticMappingBindError("PRODUCER_IDENTITY_MISMATCH")
    claim = bind_step_29p_typed_equity_from_risk_capital_v1(
        output=output,
        fresh_pretrade_get_status=fresh_pretrade_get_status,
        live_account_bound_status=live_account_bound_status,
        expected_instrument_id="SUI-USDC-SWAP",
        observed_instrument_id="SUI-USDC-SWAP",
        fresh_evidence_fetched=False,
        fresh_evidence_validated=False,
    )
    if claim.equity_dimension != TARGET_SEMANTIC:
        raise SourceToSemanticMappingBindError("CLAIM_DIMENSION_MISMATCH")
    if claim.typed_account_equity_source_field != SOURCE_OBJECT:
        raise SourceToSemanticMappingBindError("CLAIM_MUST_USE_PRODUCER_NOT_VENUE_FIELD")
    if "availEq" in claim.typed_account_equity_source_field.lower():
        raise SourceToSemanticMappingBindError("DIRECT_AVAILEQ_CLAIM_LEAK")

    class _Capital:
        evidence_status = "MISSING"
        capital_authority_class = "OBSERVED_NOT_RISK_ADMISSIBLE"
        risk_admissible = False

    admissibility = evaluate_step_29p_capital_risk_admissibility_v1(
        capital=_Capital(),
        claim=claim,
    )
    return OfflineStep29PE2EProofResultV1(
        produced=output.produced,
        dimension_id=output.dimension_id,
        producer_identity=output.producer_identity,
        typed_equity_raw=claim.typed_account_equity_raw,
        typed_source_field=claim.typed_account_equity_source_field,
        step_29p_evaluated=TRUE_TOKEN,
        reason_codes=tuple(admissibility.reason_codes),
    )


def reject_reconstruction_as_sizing_source_v1(*, claimed: str) -> None:
    if claimed in {
        "OPTION_D",
        "RECONSTRUCTION",
        "EQUITY_STOCK",
        "RECONSTRUCTED_EQUITY",
    }:
        raise SourceToSemanticMappingBindError(f"RECONSTRUCTION_TRACK_NOT_SIZING_SOURCE:{claimed}")


def execute_source_to_semantic_mapping_and_sizing_producer_bind_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
) -> dict[str, str]:
    if owner_go != OWNER_GO:
        raise SourceToSemanticMappingBindError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise SourceToSemanticMappingBindError("ORIGIN_MAIN_SHA_MISMATCH")
    if LIVE_ENABLED is not True or LIVE_ARMED is not True or WIRE_SEND_PERMITTED is not True:
        raise SourceToSemanticMappingBindError("STANDING_LIVE_GATES_UNEXPECTED")
    _require_ratified_mapping_pins_v1()
    _require_parallel_track_separation_v1()
    reject_eq_as_source_authority_v1(claimed="false")

    epoch = "2026-09-22T06:25:00Z"
    digest = "b" * 64
    observation = CurrentProductiveUsdcFreeMarginObservationV1(
        fact_id="CURRENT_PRODUCTIVE_USDC_FREE_MARGIN_OBSERVATION",
        surface=OBSERVATION_SURFACE,
        value="100.00",
        settlement_currency=SETTLEMENT_CURRENCY,
        selected_ccy="USDC",
        bound_account_identity="acct-fixture-1",
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=epoch,
        observed_at_as_of=epoch,
        age_seconds="1",
        freshness_max_age="5",
        provenance_digest=digest,
        already_net_of_in_use="true",
        account_level_avail_eq_used="false",
        fallback_chain_used="false",
    )
    p01 = CurrentProductiveP01ReductionFactV1(
        fact_id="CURRENT_PRODUCTIVE_P01_GOVERNED_REDUCTION",
        applicability_state="DOES_NOT_APPLY",
        value="",
        settlement_currency=SETTLEMENT_CURRENCY,
        bound_account_identity="acct-fixture-1",
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=epoch,
        observed_at_as_of=epoch,
        age_seconds="1",
        freshness_max_age="5",
        provenance_digest=digest,
        source_class="GOVERNED_CONDITIONAL",
    )
    eligibility = CurrentProductiveAccountEligibilityFactV1(
        fact_id="CURRENT_PRODUCTIVE_U01_ACCOUNT_ELIGIBILITY",
        account_mode="FUTURES_MODE",
        bound_account_identity="acct-fixture-1",
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=epoch,
        provenance_digest=digest,
    )
    prove_u04_double_subtraction_absent_v1(
        observation=observation,
        p01=p01,
        eligibility=eligibility,
        u04_present=True,
    )
    prove_u04_double_subtraction_absent_v1(
        observation=observation,
        p01=p01,
        eligibility=eligibility,
        u04_present=False,
    )
    p01_applies = CurrentProductiveP01ReductionFactV1(
        fact_id="CURRENT_PRODUCTIVE_P01_GOVERNED_REDUCTION",
        applicability_state="APPLIES",
        value="5.00",
        settlement_currency=SETTLEMENT_CURRENCY,
        bound_account_identity="acct-fixture-1",
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=epoch,
        observed_at_as_of=epoch,
        age_seconds="1",
        freshness_max_age="5",
        provenance_digest=digest,
        source_class="GOVERNED_CONDITIONAL",
    )
    prove_p01_applies_without_directive_fail_closed_v1(
        observation=observation,
        p01_applies=p01_applies,
        eligibility=eligibility,
    )
    e2e = run_offline_step29p_e2e_proof_v1(
        observation=observation,
        p01=p01,
        eligibility=eligibility,
    )
    trace = prove_static_producer_to_step29p_trace_v1()
    claims = {
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "RUNTIME_AUTHORIZATION_EFFECT": RUNTIME_AUTHORIZATION_EFFECT,
        "OWNER_DECISION_1": OWNER_DECISION_1,
        "AUTHORITY_MODEL": AUTHORITY_MODEL,
        "DIMENSION_ID": DIMENSION_ID,
        "SOURCE_OBJECT": SOURCE_OBJECT,
        "SOURCE_INPUT": SOURCE_INPUT,
        "TARGET_SEMANTIC": TARGET_SEMANTIC,
        "SETTLEMENT_CURRENCY": SETTLEMENT_CURRENCY,
        "TRANSFORM": TRANSFORM,
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING": TRUE_TOKEN,
        "MAPPING_PROVEN": TRUE_TOKEN,
        "MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING": TRUE_TOKEN,
        "SOURCE_SELECTED": TRUE_TOKEN,
        "SOURCE_SELECTED_OBJECT": SOURCE_SELECTED_OBJECT,
        "ACCOUNT_EQUITY_AUTHORITY_OWNER": "UNRESOLVED",
        "RECONCILIATION_CONTRACT_CREATED": FALSE_TOKEN,
        "EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "NETWORK_ACCESS_PERFORMED": FALSE_TOKEN,
        "NUMERIC_CURRENT_VENUE_VALUE_BOUND": FALSE_TOKEN,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
        "NEXT_OWNER_GO_CANDIDATE": NEXT_OWNER_GO_CANDIDATE,
        "OFFLINE_STEP29P_E2E_PROVEN": TRUE_TOKEN,
        "TYPED_EQUITY_RAW": e2e.typed_equity_raw,
        "TYPED_SOURCE_FIELD": e2e.typed_source_field,
        "U04_DOUBLE_SUBTRACTION_PROVEN_ABSENT": TRUE_TOKEN,
        "P01_FAIL_CLOSED_PROVEN": TRUE_TOKEN,
        "QUARANTINE_USED_AS_AUTHORITY": FALSE_TOKEN,
        "TRACE": trace,
    }
    if evidence_root is not None:
        store = evidence_root
        store.mkdir(parents=True, exist_ok=True)
        (store / "claims.json").write_text(_canonical_json(claims) + "\n", encoding="utf-8")
        manifest = {"claims.json": _sha256_text(_canonical_json(claims))}
        (store / "evidence_manifest.json").write_text(
            _canonical_json(manifest) + "\n", encoding="utf-8"
        )
    return {
        k: str(v) if not isinstance(v, dict) else json.dumps(v, sort_keys=True)
        for k, v in claims.items()
    }


__all__ = [
    "OWNER_GO",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "SOURCE_OBJECT",
    "SOURCE_INPUT",
    "TARGET_SEMANTIC",
    "TRANSFORM",
    "execute_source_to_semantic_mapping_and_sizing_producer_bind_v1",
    "prove_static_producer_to_step29p_trace_v1",
    "run_offline_step29p_e2e_proof_v1",
    "reject_consume_execute_after_mapping_ratification_v1",
    "SourceToSemanticMappingBindError",
    "OfflineStep29PE2EProofResultV1",
]
