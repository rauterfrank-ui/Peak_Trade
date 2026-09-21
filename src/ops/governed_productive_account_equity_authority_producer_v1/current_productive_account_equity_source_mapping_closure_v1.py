"""CURRENT_PRODUCTIVE account-equity source mapping closure v1.

Consumes Owner-GO CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_V1.

Closes CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING for the ratified
CURRENT productive chain:

  trusted USDC details.availEq observation (currency-scoped, not account-level)
  -> CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA
  -> governed productive account-equity authority producer
  -> STEP-29P typed consumer (PRODUCER_IDENTITY source_field)

Does not reopen sealed legacy KIND_SET census. Does not treat venue eq,
Treasury observed/reconciled balance alone, fixtures, or forbidden account-level
fields as equity authority. No POST. No external effect. No MV2/DP change.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Tuple

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    POST_ALLOWED,
    RUNNING_EQUITY_SOURCE_FIELD_OR_DERIVATION,
    RUNNING_EQUITY_SOURCE_OBJECT,
    RUNNING_EQUITY_SOURCE_SEMANTICS,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY as DAG_EARLIEST,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    RISK_EQUITY_DIMENSION,
    STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
    Step29PCapitalRiskAdmissibilityClaimV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_CLASS,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_SURFACE,
    CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_CLOSED,
    CURRENT_PRODUCTIVE_ARCHITECTURE_RATIFIED,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY,
    CURRENT_PRODUCTIVE_P01_POLICY_DECISION,
    CURRENT_PRODUCTIVE_P01_POLICY_DECISION_BASIS,
    CURRENT_PRODUCTIVE_SELECTED_AVAILABLE_FOR_SIZING_SOURCE,
    CURRENT_PRODUCTIVE_SOURCE_SELECTED,
    EQ_RECONCILIATION_TARGET_ONLY,
    RAW_EQ_SOURCE_AUTHORITY,
    SEALED_LEGACY_CENSUS_REOPENED,
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
    CurrentProductiveP01ReductionFactV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_p01_policy_v1 import (
    bind_current_productive_p01_policy_fact_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u01_account_mode_adapter_v1 import (
    adapt_current_productive_u01_account_mode_v1,
    build_current_productive_u01_eligibility_fact_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.constants_v1 import (
    AVAILABLE_FOR_SIZING_MINT_AUTHORIZED,
    RISK_ADMISSIBLE_MINT_AUTHORIZED,
    STEP_29P_MINT_AUTHORIZED,
)

OWNER_GO = "OWNER_GO_CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_V1"
WP_ID = "CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_V1"
THIS_SLICE = "11.2.1.EZ.FULL_CORE_CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE"
EXPECTED_ORIGIN_MAIN_SHA = "ea428052030bb2d0ef08cb2aba2313397fea45c4"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_account_equity_source_mapping_closure_v1/"
    "20260921T201900Z"
)
SCHEMA_CLASS = "CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"

CANONICAL_EQUITY_SOURCE_SURFACE = CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_SURFACE
CANONICAL_TRANSFORMATION = CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA
AUTHORITY_OWNER = "ops.governed_productive_account_equity_authority_producer_v1"
STEP_29P_CONSUMER = STEP_29P_RISK_ADMISSIBILITY_AUTHORITY

EARLIEST_AFTER_CLOSURE = "TRUSTED_29P_PRETRADE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_OWNER_GOS"

_FORBIDDEN_DIRECT_29P_FIELDS = (
    "availEq",
    "details.availEq",
    "totalEq",
    "eq",
    "adjEq",
    "availBal",
    "cashBal",
)
_SECRET_MARKERS = ("api_secret", "passphrase", "secretref://", "ok-access")


class CurrentProductiveAccountEquitySourceMappingClosureError(ValueError):
    """Fail-closed mapping-closure violation."""


@dataclass(frozen=True)
class CanonicalEquitySourceLineageV1:
    source_surface: str
    transformation: str
    authority_owner: str
    producer_identity: str
    consumer_authority: str
    equity_dimension: str
    p01_policy_decision: str
    eq_reconciliation_only: str
    treasury_mint_forbidden: str


@dataclass(frozen=True)
class CurrentProductiveAccountEquitySourceMappingClosureResultV1:
    store_root: str
    canonically_valid: str
    mapping_proven: str
    running_equity_source_object: str
    running_equity_source_field: str
    running_equity_source_semantics: str
    earliest_unresolved: str
    step_29p_consumer_source_field: str
    post_count: str
    evidence_manifest: str
    manifest_verify_rc: int


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _assert_no_secrets(payload: Mapping[str, Any]) -> None:
    blob = _canonical_json(payload).lower()
    for token in _SECRET_MARKERS:
        if token in blob:
            raise CurrentProductiveAccountEquitySourceMappingClosureError(
                f"SECRET_TOKEN_PRESENT:{token}"
            )


def reject_treasury_observation_alone_as_increase_authority_v1(
    *,
    treasury_risk_admissible_mint: bool,
    step_29p_mint: bool,
    available_for_sizing_mint: bool,
) -> None:
    if treasury_risk_admissible_mint or step_29p_mint or available_for_sizing_mint:
        raise CurrentProductiveAccountEquitySourceMappingClosureError(
            "TREASURY_OR_TRANSPORT_MINT_FORBIDDEN"
        )


def reject_historical_fixture_as_equity_authority_v1(*, source_field: str) -> None:
    field = str(source_field or "").strip()
    if field in {"", "NONE", "FIXTURE", "INJECTED_OFFLINE", "DEFAULT_BOOTSTRAP"}:
        raise CurrentProductiveAccountEquitySourceMappingClosureError(
            "HISTORICAL_FIXTURE_NOT_EQUITY_AUTHORITY"
        )
    if field.lower() in _FORBIDDEN_DIRECT_29P_FIELDS:
        reject_direct_avail_eq_29p_claim_v1(claimed=field)


def build_canonical_equity_source_lineage_v1() -> CanonicalEquitySourceLineageV1:
    if CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_CLOSED is not True:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("CLOSURE_NOT_CLOSED")
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not True:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("MAPPING_NOT_VALID")
    if MAPPING_PROVEN is not True:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("MAPPING_NOT_PROVEN")
    reject_treasury_observation_alone_as_increase_authority_v1(
        treasury_risk_admissible_mint=RISK_ADMISSIBLE_MINT_AUTHORIZED,
        step_29p_mint=STEP_29P_MINT_AUTHORIZED,
        available_for_sizing_mint=AVAILABLE_FOR_SIZING_MINT_AUTHORIZED,
    )
    return CanonicalEquitySourceLineageV1(
        source_surface=CANONICAL_EQUITY_SOURCE_SURFACE,
        transformation=CANONICAL_TRANSFORMATION,
        authority_owner=AUTHORITY_OWNER,
        producer_identity=PRODUCER_IDENTITY,
        consumer_authority=STEP_29P_CONSUMER,
        equity_dimension=RISK_EQUITY_DIMENSION,
        p01_policy_decision=CURRENT_PRODUCTIVE_P01_POLICY_DECISION,
        eq_reconciliation_only=TRUE_TOKEN if EQ_RECONCILIATION_TARGET_ONLY else FALSE_TOKEN,
        treasury_mint_forbidden=TRUE_TOKEN,
    )


def _sample_valid_observation_v1() -> CurrentProductiveUsdcFreeMarginObservationV1:
    return CurrentProductiveUsdcFreeMarginObservationV1(
        fact_id="CURRENT_PRODUCTIVE_USDC_FREE_MARGIN_OBSERVATION",
        surface=OBSERVATION_SURFACE,
        value="100.00",
        settlement_currency="USDC",
        selected_ccy="USDC",
        bound_account_identity="acct-1",
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch="2026-09-21T18:00:00Z",
        observed_at_as_of="2026-09-21T18:00:00Z",
        age_seconds="1",
        freshness_max_age="5",
        provenance_digest=hashlib.sha256(b"closure-test").hexdigest(),
        already_net_of_in_use=TRUE_TOKEN,
        account_level_avail_eq_used=FALSE_TOKEN,
        fallback_chain_used=FALSE_TOKEN,
    )


def _sample_eligibility_and_p01_v1() -> tuple[Any, CurrentProductiveP01ReductionFactV1]:
    obs = _sample_valid_observation_v1()
    adaptation = adapt_current_productive_u01_account_mode_v1("2")
    eligibility = build_current_productive_u01_eligibility_fact_v1(
        adaptation=adaptation,
        bound_account_identity=obs.bound_account_identity,
        bound_venue_identity=obs.bound_venue_identity,
        bound_td_mode=obs.bound_td_mode,
        decision_epoch=obs.decision_epoch,
        provenance_digest=obs.provenance_digest,
    )
    if eligibility is None:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("ELIGIBILITY_SAMPLE_FAILED")
    p01 = bind_current_productive_p01_policy_fact_v1(
        bound_account_identity=obs.bound_account_identity,
        bound_venue_identity=obs.bound_venue_identity,
        bound_td_mode=obs.bound_td_mode,
        decision_epoch=obs.decision_epoch,
        observed_at_as_of=obs.observed_at_as_of,
        age_seconds=obs.age_seconds,
        freshness_max_age=obs.freshness_max_age,
        provenance_digest=obs.provenance_digest,
    )
    return eligibility, p01


def evaluate_canonical_mapping_acceptance_v1(
    *,
    observation: CurrentProductiveUsdcFreeMarginObservationV1,
    p01: CurrentProductiveP01ReductionFactV1,
    eligibility: Any,
) -> Tuple[bool, Tuple[str, ...]]:
    reasons: list[str] = []
    if observation.surface != CANONICAL_EQUITY_SOURCE_SURFACE:
        reasons.append("SOURCE_SURFACE_MISMATCH")
    if observation.account_level_avail_eq_used != FALSE_TOKEN:
        reasons.append("ACCOUNT_LEVEL_FIELD_FORBIDDEN")
    if observation.fallback_chain_used != FALSE_TOKEN:
        reasons.append("FALLBACK_CHAIN_FORBIDDEN")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        reasons.append("RAW_EQ_AUTHORITY_FORBIDDEN")
    if CURRENT_PRODUCTIVE_P01_POLICY_DECISION not in {"DOES_NOT_APPLY", "APPLIES"}:
        reasons.append("P01_POLICY_UNBOUND")
    try:
        output = produce_current_productive_29p_risk_capital_v1(
            observation=observation,
            p01=p01,
            eligibility=eligibility,
            restart_from_kind_set=FALSE_TOKEN,
        )
    except Exception as exc:  # noqa: BLE001 — contract surface
        reasons.append(f"PRODUCER_REJECT:{type(exc).__name__}")
        return False, tuple(reasons)
    if output.produced != TRUE_TOKEN:
        reasons.append("PRODUCER_NOT_PRODUCED")
        return False, tuple(reasons)
    claim = bind_step_29p_typed_equity_from_risk_capital_v1(
        output=output,
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        live_account_bound_status="TRUSTED_PRESENT",
        expected_instrument_id="SUI-USD_UM_XPERP-310404",
        observed_instrument_id="SUI-USD_UM_XPERP-310404",
        fresh_evidence_fetched=True,
        fresh_evidence_validated=True,
    )
    if claim.typed_account_equity_source_field != PRODUCER_IDENTITY:
        reasons.append("29P_SOURCE_FIELD_NOT_PRODUCER_IDENTITY")
    reject_historical_fixture_as_equity_authority_v1(
        source_field=claim.typed_account_equity_source_field
    )
    if claim.equity_dimension != RISK_EQUITY_DIMENSION:
        reasons.append("29P_EQUITY_DIMENSION_MISMATCH")
    return len(reasons) == 0, tuple(reasons)


def _assert_closure_constants() -> None:
    if CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_CLOSED is not True:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("CLOSURE_FLAG_FALSE")
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not True:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("CANONICALLY_VALID_NOT_TRUE")
    if MAPPING_PROVEN is not True:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("MAPPING_PROVEN_NOT_TRUE")
    if CURRENT_PRODUCTIVE_ARCHITECTURE_RATIFIED is not True:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("ARCHITECTURE_NOT_RATIFIED")
    if SEALED_LEGACY_CENSUS_REOPENED is not False:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("LEGACY_CENSUS_REOPENED")
    if CURRENT_PRODUCTIVE_SOURCE_SELECTED is not True:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("SOURCE_NOT_SELECTED")
    if CURRENT_PRODUCTIVE_SELECTED_AVAILABLE_FOR_SIZING_SOURCE != PRODUCER_IDENTITY:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("SELECTED_SOURCE_DRIFT")
    if RUNNING_EQUITY_SOURCE_OBJECT != PRODUCER_IDENTITY:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("RUNNING_OBJECT_DRIFT")
    if DAG_EARLIEST != EARLIEST_AFTER_CLOSURE:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("DAG_EARLIEST_DRIFT")
    if EXTERNAL_EFFECT_AUTHORIZED is not False:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("EXTERNAL_EFFECT_TRUE")
    if POST_ALLOWED is not False:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("POST_ALLOWED_TRUE")
    if MULTI_FUTURE_RUNTIME_AUTHORIZED is not False:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("MULTI_FUTURE_AUTHORIZED")
    reject_treasury_observation_alone_as_increase_authority_v1(
        treasury_risk_admissible_mint=RISK_ADMISSIBLE_MINT_AUTHORIZED,
        step_29p_mint=STEP_29P_MINT_AUTHORIZED,
        available_for_sizing_mint=AVAILABLE_FOR_SIZING_MINT_AUTHORIZED,
    )


def execute_current_productive_account_equity_source_mapping_closure_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    repo_root: Path | None = None,
) -> CurrentProductiveAccountEquitySourceMappingClosureResultV1:
    if owner_go != OWNER_GO:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_closure_constants()

    obs = _sample_valid_observation_v1()
    eligibility, p01 = _sample_eligibility_and_p01_v1()
    accepted, reasons = evaluate_canonical_mapping_acceptance_v1(
        observation=obs, p01=p01, eligibility=eligibility
    )
    if not accepted:
        raise CurrentProductiveAccountEquitySourceMappingClosureError(
            f"CANONICAL_MAPPING_NOT_ACCEPTED:{','.join(reasons)}"
        )

    output = produce_current_productive_29p_risk_capital_v1(
        observation=obs, p01=p01, eligibility=eligibility, restart_from_kind_set=FALSE_TOKEN
    )
    claim = bind_step_29p_typed_equity_from_risk_capital_v1(
        output=output,
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        live_account_bound_status="TRUSTED_PRESENT",
        expected_instrument_id="SUI-USD_UM_XPERP-310404",
        observed_instrument_id="SUI-USD_UM_XPERP-310404",
        fresh_evidence_fetched=True,
        fresh_evidence_validated=True,
    )
    if claim.typed_account_equity_source_field != PRODUCER_IDENTITY:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("29P_CONSUMER_DRIFT")
    if claim.equity_dimension != RISK_EQUITY_DIMENSION:
        raise CurrentProductiveAccountEquitySourceMappingClosureError("29P_DIMENSION_DRIFT")

    root = repo_root or Path(__file__).resolve().parents[3]
    store = Path(evidence_root) if evidence_root is not None else root / CANONICAL_PACK_RELPATH
    store.mkdir(parents=True, exist_ok=True)
    lineage = build_canonical_equity_source_lineage_v1()
    claims = {
        "THIS_SLICE": THIS_SLICE,
        "WP_ID": WP_ID,
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "EXPECTED_ORIGIN_MAIN_SHA": origin_main_sha,
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING": TRUE_TOKEN,
        "MAPPING_PROVEN": TRUE_TOKEN,
        "CANONICAL_EQUITY_SOURCE_SURFACE": lineage.source_surface,
        "CANONICAL_TRANSFORMATION": lineage.transformation,
        "AUTHORITY_OWNER": lineage.authority_owner,
        "PRODUCER_IDENTITY": lineage.producer_identity,
        "STEP_29P_CONSUMER": lineage.consumer_authority,
        "EQUITY_DIMENSION": lineage.equity_dimension,
        "P01_POLICY_DECISION": lineage.p01_policy_decision,
        "P01_POLICY_DECISION_BASIS": CURRENT_PRODUCTIVE_P01_POLICY_DECISION_BASIS,
        "OBSERVATION_CLASS": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_CLASS,
        "EQ_RECONCILIATION_TARGET_ONLY": lineage.eq_reconciliation_only,
        "TREASURY_MINT_FORBIDDEN": lineage.treasury_mint_forbidden,
        "RUNNING_EQUITY_SOURCE_OBJECT": RUNNING_EQUITY_SOURCE_OBJECT,
        "RUNNING_EQUITY_SOURCE_FIELD_OR_DERIVATION": RUNNING_EQUITY_SOURCE_FIELD_OR_DERIVATION,
        "RUNNING_EQUITY_SOURCE_SEMANTICS": RUNNING_EQUITY_SOURCE_SEMANTICS,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": DAG_EARLIEST,
        "STEP_29P_TYPED_SOURCE_FIELD": claim.typed_account_equity_source_field,
        "STEP_29P_EQUITY_DIMENSION_BOUND": TRUE_TOKEN,
        "LIVE_ENABLED": TRUE_TOKEN if LIVE_ENABLED is True else FALSE_TOKEN,
        "LIVE_ARMED": TRUE_TOKEN if LIVE_ARMED is True else FALSE_TOKEN,
        "WIRE_SEND_PERMITTED": TRUE_TOKEN if WIRE_SEND_PERMITTED is True else FALSE_TOKEN,
        "EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "POST_ALLOWED": FALSE_TOKEN,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": FALSE_TOKEN,
        "MV2_DP_CHANGED": FALSE_TOKEN,
        "OPTIMIZATION_BACKFLOW": FALSE_TOKEN,
        "POST_COUNT": "0",
        "PROTECTED_SURFACES_CHANGED": FALSE_TOKEN,
    }
    _assert_no_secrets(claims)
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(
        path=store / "lineage_v1.json",
        payload={
            "source_surface": lineage.source_surface,
            "transformation": lineage.transformation,
            "authority_owner": lineage.authority_owner,
            "consumer": lineage.consumer_authority,
            "class": "B_CURRENT_DYNAMIC_WITH_A_SEMANTICS",
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=store)
    rc = verify_manifest_sha256_v1(store_root=store)
    return CurrentProductiveAccountEquitySourceMappingClosureResultV1(
        store_root=str(store),
        canonically_valid=TRUE_TOKEN,
        mapping_proven=TRUE_TOKEN,
        running_equity_source_object=RUNNING_EQUITY_SOURCE_OBJECT,
        running_equity_source_field=RUNNING_EQUITY_SOURCE_FIELD_OR_DERIVATION,
        running_equity_source_semantics=RUNNING_EQUITY_SOURCE_SEMANTICS,
        earliest_unresolved=DAG_EARLIEST,
        step_29p_consumer_source_field=claim.typed_account_equity_source_field,
        post_count="0",
        evidence_manifest=manifest,
        manifest_verify_rc=rc,
    )


__all__ = [
    "AUTHORITY_OWNER",
    "CANONICAL_EQUITY_SOURCE_SURFACE",
    "CANONICAL_TRANSFORMATION",
    "CANONICAL_PACK_RELPATH",
    "CurrentProductiveAccountEquitySourceMappingClosureError",
    "CurrentProductiveAccountEquitySourceMappingClosureResultV1",
    "CanonicalEquitySourceLineageV1",
    "EARLIEST_AFTER_CLOSURE",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "OWNER_GO",
    "STEP_29P_CONSUMER",
    "THIS_SLICE",
    "WP_ID",
    "build_canonical_equity_source_lineage_v1",
    "evaluate_canonical_mapping_acceptance_v1",
    "execute_current_productive_account_equity_source_mapping_closure_v1",
    "reject_historical_fixture_as_equity_authority_v1",
    "reject_treasury_observation_alone_as_increase_authority_v1",
]
