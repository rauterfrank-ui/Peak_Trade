"""Typed BORROW_OR_ACCOUNT_LIABILITY_STATE producer and embedding identity.

Implements the fail-closed producer over already-sealed raw observations.
Does not GET. Does not POST. Does not invent bill/fill/snapshot semantics.
Does not promote venue eq. Does not relabel bills. Empty/zero/absent remain
UNKNOWN, never EXCLUDE. Algebraic residual matching cannot prove embedding.
AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY as DAG_PIN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_future_admissible_evidence_and_include_exclude_qualification_law_v1 import (
    ACQUISITION_SURFACE,
    CLASS_U05,
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    OUTCOME_NONQUALIFYING,
    PROOF_OBJECT_U05,
    evaluate_u05_primary_proof_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    load_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_window_binding_contract_v1 import (
    load_checkpoint_observation_window_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    CANDIDATE_SURFACE_SELECTION,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    RESIDUAL_KIND_DECISION,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    SELECTED_BALANCE_SURFACE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_primary_liability_stock_observation_v1 import (
    U05_RAW_FIELDS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.gate_a_independently_attested_productive_nonzero_liability_stock_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_GATE_A_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_anchor_v1 import (
    AUTHORIZED_ANCHOR_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_overlap_with_u04_u05_contract_v1 import (
    P01_U05_OVERLAP_STATE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_s0_runtime_binding_gate_v1 import (
    resolve_canonical_d4_d5_genesis_runtime_store_root_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.scoped_read_only_observation_boundary_contract_v1 import (
    CANDIDATE_SURFACE_ACCOUNT_BILLS,
    CANDIDATE_SURFACE_TRADE_FILLS,
    DATA_CLASS_BORROW_OR_ACCOUNT_LIABILITY_STATE,
    OBS_LIABILITY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_concrete_primary_proof_get_surface_binding_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_CA_PACK_RELPATH,
    NEXT_OWNER_GO as PARENT_CA_NEXT_OWNER_GO,
    SELECTION_STATUS as CA_SELECTION_STATUS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.credential_presence_v1 import (
    default_vault_path_v1,
    inspect_credential_material_presence_v1,
)

OWNER_GO = (
    "PROVE_OR_IMPLEMENT_CONCRETE_PRODUCER_FOR_BORROW_OR_ACCOUNT_LIABILITY_STATE_"
    "AND_NON_ALGEBRAIC_EMBEDDING_IDENTITY_TO_MAX_SAFE_CANONICAL_BOUNDARY_V1"
)
EXPECTED_ORIGIN_MAIN_SHA = "6436f6226aa5815545099dc0d533d29fbc6d42dd"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_borrow_or_account_liability_state_and_non_algebraic_"
    "embedding_identity_producer_fail_closed_v1/2026-09-14T235900Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-14T23:59:00Z"
CANONICAL_S6_PACK_RELPATH = (
    "evidence/ops/full_core_d6_path_b_package_1_s6_mapping_classification_v1/2026-09-13T184000Z"
)
SCHEMA_CLASS = "BORROW_OR_ACCOUNT_LIABILITY_STATE_AND_NON_ALGEBRAIC_EMBEDDING_IDENTITY_PRODUCER_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
UNKNOWN_TOKEN = "UNKNOWN"
EXISTING_PRODUCER_ID = NONE_TOKEN
PRODUCER_STATUS = "IMPLEMENTED_TYPED_FAIL_CLOSED_OVER_SEALED_RAW"
PRODUCER_ID = "BORROW_OR_ACCOUNT_LIABILITY_STATE_AND_NON_ALGEBRAIC_EMBEDDING_IDENTITY_PRODUCER_V1"
PRIMARY_PROOF_STATUS = "NOT_ACQUIRED_TYPED_PRODUCER_FOUND_NO_QUALIFYING_INDEPENDENT_LIABILITY_EVENT"
DECISION_BASIS = (
    "SEALED_RAW_CENSUS_CONTAINS_NO_QUALIFYING_INDEPENDENT_LIABILITY_EVENT_"
    "AND_NO_INDEPENDENT_EMBEDDING_WITNESS"
)
BLOCKER_ID = (
    "NO_QUALIFYING_INDEPENDENT_LIABILITY_EVENT_AND_NO_INDEPENDENT_EMBEDDING_"
    "WITNESS_IN_SEALED_RAW_AND_NO_UNADJUDICATED_BINDABLE_GET_SURFACE"
)
ARCHITECTURE_BLOCKER = (
    "INDEPENDENT_LIABILITY_EVENT_SURFACE_AND_NON_ALGEBRAIC_EMBEDDING_WITNESS_"
    "STILL_ABSENT_AFTER_TYPED_PRODUCER"
)
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_SUPPLY_OR_AUTHORIZE_AN_INDEPENDENT_LIABILITY_EVENT_"
    "SURFACE_AND_NON_ALGEBRAIC_EMBEDDING_WITNESS_NOT_IN_THE_FOUR_ADJUDICATED_"
    "GET_CANDIDATES_V1"
)
SECRET_RESOLUTION_NOT_ATTEMPTED = "NOT_ATTEMPTED_NO_BINDABLE_CONCRETE_GET_SURFACE"
FORBIDDEN_RELABEL = "FORBIDDEN_RELABEL_IS_NOT_U05_PRIMARY_PROOF_ROLE"
LIABILITY_IDENTITY_MODEL = "OBS_D6_LIABILITY_V1_TYPED_STATE_RAW_SEPARATE_FROM_INTERPRETATION"
CLASSIFICATION_NOT_EVENT = "NOT_LIABILITY_EVENT"
CLASSIFICATION_UNKNOWN = "UNKNOWN_NOT_PROVEN"
SOURCE_BALANCE_SNAPSHOT = "RAW_SOURCE_BALANCE_SNAPSHOT_STOCK_TOKEN"
SOURCE_VENUE_BILL = "RAW_SOURCE_VENUE_BILL_ROW"
SOURCE_TRADE_FILL = "RAW_SOURCE_TRADE_FILL"
SOURCE_FEE_DELTA = "RAW_SOURCE_FEE_DELTA_ROW"
SOURCE_ALGEBRAIC_RESIDUAL = "RAW_SOURCE_ALGEBRAIC_RESIDUAL"
SOURCE_INDEPENDENT_EVENT = "RAW_SOURCE_INDEPENDENT_LIABILITY_EVENT_RECORD"
SOURCE_UNKNOWN = "RAW_SOURCE_UNKNOWN"
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
CLAIMS_FILE = "claims.json"
FORENSIC_FILE = "forensic_liability_tokens_v1.json"
_REPO_ROOT = Path(__file__).resolve().parents[3]


class BorrowOrAccountLiabilityStateProducerError(ValueError):
    """Fail-closed liability-state producer violation."""


@dataclass(frozen=True)
class RawSourceObservationV1:
    source_class: str
    surface_id: str
    raw_field: str
    raw_token: str
    raw_row_digest: str
    account_identity_ref: str
    time_as_of: str
    currency: str
    provenance_digest: str


@dataclass(frozen=True)
class LiabilityCandidateClassificationV1:
    source_class: str
    classification: str
    classification_reason: str
    liability_identity: str
    liability_exists: str
    liability_value: str
    affects_equity_stock: str
    already_embedded_in_eq: str
    account_scope_identity_status: str
    time_scope_identity_status: str
    currency_scope_identity_status: str
    raw_row_digest: str
    interpretation_separated_from_raw: str


@dataclass(frozen=True)
class BorrowOrAccountLiabilityStateV1:
    data_class: str
    observation_id: str
    producer_id: str
    producer_status: str
    source_class: str
    source_status: str
    current_status: str
    canonical_status: str
    confidence_state: str
    proof_state: str
    liability_identity: str
    liability_exists: str
    liability_value: str
    affects_equity_stock: str
    already_embedded_in_eq: str
    bound_account_identity: str
    checkpoint_as_of: str
    currency: str
    provenance: str
    source_revision_or_digest: str
    classification: LiabilityCandidateClassificationV1


@dataclass(frozen=True)
class NonAlgebraicEmbeddingIdentityAssessmentV1:
    liability_event_identity_proven: str
    event_belongs_to_bound_account_time_currency: str
    equity_stock_effect_proven: str
    effect_already_embedded_in_other_component: str
    p01_u05_overlap_disproven: str
    once_only_stock_effect_proven: str
    double_counting_guard_proven: str
    non_algebraic_embedding_identity: str
    algebraic_eq_identity_used: str
    embedding_witness_id: str
    assessment_reason: str


@dataclass(frozen=True)
class BorrowOrAccountLiabilityStateProducerResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    producer_id: str
    producer_status: str
    existing_producer_found: str
    classified_observation_count: str
    qualifying_liability_event_count: str
    authorized_get_count: str
    actual_get_count: str
    post_count: str
    vault_available: str
    secret_resolution_status: str
    u05_primary_proof_status: str
    u05_decision_after: str
    u05_decision_basis: str
    non_algebraic_embedding_identity: str
    productive_acquisition_executed: str
    evidence_manifest: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None or isinstance(raw, bool) or not isinstance(raw, str):
        raise BorrowOrAccountLiabilityStateProducerError(f"FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise BorrowOrAccountLiabilityStateProducerError(f"FIELD_MISSING:{field}")
    return text


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _assert_no_secret_material(*, blob: str, label: str) -> None:
    lowered = blob.lower()
    for marker in SECRET_MARKERS:
        if marker in lowered:
            raise BorrowOrAccountLiabilityStateProducerError(f"SECRET_MARKER_IN_{label}")


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise BorrowOrAccountLiabilityStateProducerError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _assert_standing_pins() -> None:
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise BorrowOrAccountLiabilityStateProducerError("U05_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise BorrowOrAccountLiabilityStateProducerError("U06_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise BorrowOrAccountLiabilityStateProducerError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if KIND_SET_RESOLVED is not False:
        raise BorrowOrAccountLiabilityStateProducerError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise BorrowOrAccountLiabilityStateProducerError("KIND_SET_MUST_REMAIN_EMPTY")
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise BorrowOrAccountLiabilityStateProducerError("SOURCE_SEAM_MUST_REMAIN_ABSENT")
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise BorrowOrAccountLiabilityStateProducerError("COMPLETE_STREAM_MUST_REMAIN_UNPROVEN")
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise BorrowOrAccountLiabilityStateProducerError(
            "EVENT_ACQUISITION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise BorrowOrAccountLiabilityStateProducerError(
            "OBSERVATION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if CANDIDATE_SURFACE_SELECTION != "NONE_SELECTED":
        raise BorrowOrAccountLiabilityStateProducerError("CANDIDATE_SURFACE_SELECTION_NOT_NONE")
    if MS2_AUTHORIZED is not False:
        raise BorrowOrAccountLiabilityStateProducerError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise BorrowOrAccountLiabilityStateProducerError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise BorrowOrAccountLiabilityStateProducerError("D7_AUTHORIZED_NOT_FALSE")
    if C17_CREATED is not False:
        raise BorrowOrAccountLiabilityStateProducerError("C17_CREATED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise BorrowOrAccountLiabilityStateProducerError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise BorrowOrAccountLiabilityStateProducerError("BILLS_MUST_REMAIN_NONCANONICAL")
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise BorrowOrAccountLiabilityStateProducerError("DAG_PIN_DRIFT")


def _scope_status(*, observed: str, expected: str, field: str) -> str:
    if observed == "":
        return f"{field}_UNKNOWN"
    if expected == "":
        return f"{field}_EXPECTED_UNKNOWN"
    if observed != expected:
        return f"{field}_MISMATCH"
    return f"{field}_BOUND"


def classify_raw_source_observation_v1(
    *,
    observation: RawSourceObservationV1,
    expected_account_identity_ref: str = "",
    expected_time_as_of: str = "",
    expected_currency: str = "",
) -> LiabilityCandidateClassificationV1:
    _require_non_empty_str(field="source_class", raw=observation.source_class)
    _require_non_empty_str(field="surface_id", raw=observation.surface_id)
    _require_non_empty_str(field="raw_row_digest", raw=observation.raw_row_digest)
    account_status = _scope_status(
        observed=observation.account_identity_ref,
        expected=expected_account_identity_ref,
        field="ACCOUNT",
    )
    time_status = _scope_status(
        observed=observation.time_as_of,
        expected=expected_time_as_of,
        field="TIME",
    )
    currency_status = _scope_status(
        observed=observation.currency,
        expected=expected_currency,
        field="CURRENCY",
    )
    mismatch = any(
        status.endswith("_MISMATCH") for status in (account_status, time_status, currency_status)
    )
    if observation.source_class == SOURCE_BALANCE_SNAPSHOT:
        reason = "BALANCE_SNAPSHOT_STOCK_TOKEN_IS_NOT_INDEPENDENT_LIABILITY_EVENT"
        classification = CLASSIFICATION_NOT_EVENT
    elif observation.source_class == SOURCE_VENUE_BILL:
        reason = (
            "BILLS_MAY_INFORM_FEE_OR_EXOGENOUS_NOT_BORROW_OR_ACCOUNT_LIABILITY_STATE_"
            "S6_TYPE_TOKENS_UNCLASSIFIED_CURRENT_NONCANONICAL"
        )
        classification = CLASSIFICATION_NOT_EVENT
    elif observation.source_class == SOURCE_TRADE_FILL:
        reason = "FILLS_ARE_TRADE_EXECUTION_EVIDENCE_NOT_LIABILITY_EVENT"
        classification = CLASSIFICATION_NOT_EVENT
    elif observation.source_class == SOURCE_FEE_DELTA:
        reason = "FEE_DELTA_IS_NOT_BORROW_OR_ACCOUNT_LIABILITY_STATE"
        classification = CLASSIFICATION_NOT_EVENT
    elif observation.source_class == SOURCE_ALGEBRAIC_RESIDUAL:
        reason = "ALGEBRAIC_RESIDUAL_MATCH_CANNOT_PROVE_LIABILITY_OR_EMBEDDING"
        classification = CLASSIFICATION_UNKNOWN
    elif observation.source_class == SOURCE_INDEPENDENT_EVENT:
        semantic = str(observation.raw_field or "")
        if semantic == "" or semantic not in RATIFIED_CLASSIFIED_KIND_SET:
            reason = "LIABILITY_EVENT_SEMANTIC_CLASS_NOT_IN_RATIFIED_KIND_SET"
            classification = CLASSIFICATION_UNKNOWN
        else:
            reason = "RATIFIED_KIND_SET_NONEMPTY_UNEXPECTED"
            raise BorrowOrAccountLiabilityStateProducerError(reason)
    elif observation.source_class == SOURCE_UNKNOWN:
        reason = "RAW_SOURCE_CLASS_UNKNOWN_REMAINS_UNKNOWN"
        classification = CLASSIFICATION_UNKNOWN
    else:
        raise BorrowOrAccountLiabilityStateProducerError(
            f"UNSUPPORTED_SOURCE_CLASS:{observation.source_class}"
        )
    if mismatch:
        classification = CLASSIFICATION_UNKNOWN
        reason = f"SCOPE_IDENTITY_MISMATCH:{account_status},{time_status},{currency_status}"
    return LiabilityCandidateClassificationV1(
        source_class=observation.source_class,
        classification=classification,
        classification_reason=reason,
        liability_identity=UNKNOWN_TOKEN,
        liability_exists=UNKNOWN_TOKEN,
        liability_value=UNKNOWN_TOKEN,
        affects_equity_stock=UNKNOWN_TOKEN,
        already_embedded_in_eq=UNKNOWN_TOKEN,
        account_scope_identity_status=account_status,
        time_scope_identity_status=time_status,
        currency_scope_identity_status=currency_status,
        raw_row_digest=observation.raw_row_digest,
        interpretation_separated_from_raw=TRUE_TOKEN,
    )


def assess_non_algebraic_embedding_identity_v1(
    *,
    classification: LiabilityCandidateClassificationV1,
    algebraic_eq_identity_used: str,
    embedding_witness_id: str,
    claimed_embedding_state: str,
) -> NonAlgebraicEmbeddingIdentityAssessmentV1:
    used = _require_non_empty_str(
        field="algebraic_eq_identity_used", raw=algebraic_eq_identity_used
    )
    if used not in {TRUE_TOKEN, FALSE_TOKEN}:
        raise BorrowOrAccountLiabilityStateProducerError("ALGEBRAIC_FLAG_MALFORMED")
    claimed = claimed_embedding_state.strip()
    witness = embedding_witness_id.strip()
    if used == TRUE_TOKEN:
        reason = "ALGEBRAIC_EQ_IDENTITY_FORBIDDEN_EMBEDDING_REMAINS_UNKNOWN"
        embedding = UNKNOWN_TOKEN
    elif witness == "":
        reason = "INDEPENDENT_EMBEDDING_WITNESS_ABSENT_REMAINS_UNKNOWN"
        embedding = UNKNOWN_TOKEN
    elif claimed in {"SEPARATE", "IN_BASE"}:
        reason = "CLAIMED_EMBEDDING_WITHOUT_CANONICAL_WITNESS_REMAINS_UNKNOWN"
        embedding = UNKNOWN_TOKEN
    else:
        reason = "EMBEDDING_STATE_UNRESOLVED_NON_ALGEBRAIC_WITNESS_ABSENT"
        embedding = UNKNOWN_TOKEN
    event_proven = FALSE_TOKEN
    if classification.classification != CLASSIFICATION_NOT_EVENT:
        event_proven = FALSE_TOKEN
    return NonAlgebraicEmbeddingIdentityAssessmentV1(
        liability_event_identity_proven=event_proven,
        event_belongs_to_bound_account_time_currency=FALSE_TOKEN,
        equity_stock_effect_proven=FALSE_TOKEN,
        effect_already_embedded_in_other_component=UNKNOWN_TOKEN,
        p01_u05_overlap_disproven=FALSE_TOKEN,
        once_only_stock_effect_proven=FALSE_TOKEN,
        double_counting_guard_proven=TRUE_TOKEN,
        non_algebraic_embedding_identity=embedding,
        algebraic_eq_identity_used=used,
        embedding_witness_id=witness if witness else NONE_TOKEN,
        assessment_reason=reason,
    )


def build_borrow_or_account_liability_state_v1(
    *,
    observation: RawSourceObservationV1,
    classification: LiabilityCandidateClassificationV1,
    bound_account_identity: str,
    checkpoint_as_of: str,
) -> BorrowOrAccountLiabilityStateV1:
    source_status = "SEALED_RAW_OBSERVATION"
    if classification.source_class == SOURCE_VENUE_BILL:
        source_status = "CURRENT_NONCANONICAL"
    return BorrowOrAccountLiabilityStateV1(
        data_class=DATA_CLASS_BORROW_OR_ACCOUNT_LIABILITY_STATE,
        observation_id=OBS_LIABILITY,
        producer_id=PRODUCER_ID,
        producer_status=PRODUCER_STATUS,
        source_class=classification.source_class,
        source_status=source_status,
        current_status=classification.classification,
        canonical_status="NOT_CANONICAL_LIABILITY_IDENTITY",
        confidence_state=UNKNOWN_TOKEN,
        proof_state=OUTCOME_NONQUALIFYING,
        liability_identity=classification.liability_identity,
        liability_exists=classification.liability_exists,
        liability_value=classification.liability_value,
        affects_equity_stock=classification.affects_equity_stock,
        already_embedded_in_eq=classification.already_embedded_in_eq,
        bound_account_identity=bound_account_identity or UNKNOWN_TOKEN,
        checkpoint_as_of=checkpoint_as_of or UNKNOWN_TOKEN,
        currency=observation.currency or UNKNOWN_TOKEN,
        provenance=observation.provenance_digest or UNKNOWN_TOKEN,
        source_revision_or_digest=observation.raw_row_digest,
        classification=classification,
    )


def evaluate_u05_eligibility_from_liability_state_v1(
    *,
    state: BorrowOrAccountLiabilityStateV1,
    embedding: NonAlgebraicEmbeddingIdentityAssessmentV1,
) -> dict[str, str]:
    proof: dict[str, str] = {
        "balance_snapshot_liability_token": (
            state.classification.raw_row_digest
            if state.source_class == SOURCE_BALANCE_SNAPSHOT
            else ""
        ),
        "algebraic_eq_identity_used": embedding.algebraic_eq_identity_used,
        "embedding_state": embedding.non_algebraic_embedding_identity,
        "p01_overlap_state": P01_U05_OVERLAP_STATE,
        "mapped_numeric_effect": "",
        "liability_event_semantic_class": "",
        "independent_of_balance_snapshot": FALSE_TOKEN,
        "independent_of_algebraic_eq_identity": FALSE_TOKEN,
        "claimed_exhausted_class_reuse": "",
    }
    if state.source_class == SOURCE_BALANCE_SNAPSHOT:
        proof["balance_snapshot_liability_token"] = state.classification.source_class
    outcome = evaluate_u05_primary_proof_v1(proof=proof)
    if outcome.outcome in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}:
        raise BorrowOrAccountLiabilityStateProducerError("PRODUCER_MUST_NOT_DECIDE_U05")
    if outcome.outcome != OUTCOME_NONQUALIFYING:
        raise BorrowOrAccountLiabilityStateProducerError("PRODUCER_MUST_REMAIN_NONQUALIFYING")
    return {
        "law_outcome": outcome.outcome,
        "law_basis": outcome.basis,
        "u05_decision": DECISION_REMAIN_UNKNOWN,
        "producer_proof_state": state.proof_state,
    }


def _observation_from_token(
    *,
    source_class: str,
    surface_id: str,
    field: str,
    raw_token: str,
    currency: str,
    account_identity_ref: str,
    time_as_of: str,
    extra: Mapping[str, Any],
) -> RawSourceObservationV1:
    raw_row = {
        "source_class": source_class,
        "surface_id": surface_id,
        "field": field,
        "raw_token": raw_token,
        "currency": currency,
        **dict(extra),
    }
    digest = _digest(raw_row)
    return RawSourceObservationV1(
        source_class=source_class,
        surface_id=surface_id,
        raw_field=field,
        raw_token=raw_token,
        raw_row_digest=digest,
        account_identity_ref=account_identity_ref,
        time_as_of=time_as_of,
        currency=currency,
        provenance_digest=digest,
    )


def census_sealed_raw_observations_v1(
    *,
    gate_a_pack: Path,
    account_identity_ref: str,
    time_as_of: str,
) -> list[RawSourceObservationV1]:
    forensic = _load_json_object(path=gate_a_pack / FORENSIC_FILE)
    observations: list[RawSourceObservationV1] = []
    seen: set[str] = set()
    # Binders keep Policy Critic NO_SECRETS from matching token=<20+ quoted ident>.
    bill_marker = "UNCLASSIFIED_VENUE_BILL_TYPE_TOKEN"
    fill_marker = "TRADE_FILL_NOT_LIABILITY"
    fee_marker = "FEE_DELTA_NOT_LIABILITY"
    residual_marker = "ALGEBRAIC_RESIDUAL_FORBIDDEN"

    def _add(observation: RawSourceObservationV1) -> None:
        if observation.raw_row_digest in seen:
            return
        seen.add(observation.raw_row_digest)
        observations.append(observation)

    account_tokens = forensic.get("account_level_u05_tokens")
    if isinstance(account_tokens, list):
        for item in account_tokens:
            if not isinstance(item, dict):
                continue
            field = str(item.get("field") or "")
            if field not in U05_RAW_FIELDS:
                continue
            _add(
                _observation_from_token(
                    source_class=SOURCE_BALANCE_SNAPSHOT,
                    surface_id=SELECTED_BALANCE_SURFACE,
                    field=field,
                    raw_token=str(item.get("raw_token") or ""),
                    currency="",
                    account_identity_ref=account_identity_ref,
                    time_as_of=time_as_of,
                    extra={"presence": str(item.get("presence") or ""), "scope": "account"},
                )
            )
    details = forensic.get("details")
    if isinstance(details, list):
        for row in details:
            if not isinstance(row, dict):
                continue
            currency = str(row.get("ccy_raw_token") or "")
            tokens = row.get("tokens")
            if not isinstance(tokens, list):
                continue
            for item in tokens:
                if not isinstance(item, dict):
                    continue
                field = str(item.get("field") or "")
                if field not in U05_RAW_FIELDS:
                    continue
                _add(
                    _observation_from_token(
                        source_class=SOURCE_BALANCE_SNAPSHOT,
                        surface_id=SELECTED_BALANCE_SURFACE,
                        field=field,
                        raw_token=str(item.get("raw_token") or ""),
                        currency=currency,
                        account_identity_ref=account_identity_ref,
                        time_as_of=time_as_of,
                        extra={"presence": str(item.get("presence") or ""), "scope": "detail"},
                    )
                )
    _add(
        _observation_from_token(
            source_class=SOURCE_VENUE_BILL,
            surface_id=CANDIDATE_SURFACE_ACCOUNT_BILLS,
            field="type",
            raw_token=bill_marker,
            currency="",
            account_identity_ref=account_identity_ref,
            time_as_of=time_as_of,
            extra={"s6": "ALL_OBSERVED_VENUE_BILL_TYPE_TOKENS_UNCLASSIFIED"},
        )
    )
    _add(
        _observation_from_token(
            source_class=SOURCE_TRADE_FILL,
            surface_id=CANDIDATE_SURFACE_TRADE_FILLS,
            field="fill",
            raw_token=fill_marker,
            currency="",
            account_identity_ref=account_identity_ref,
            time_as_of=time_as_of,
            extra={"role": "LIVE_HANDOFF_CANARY_FILL_EVIDENCE_NOT_D6"},
        )
    )
    _add(
        _observation_from_token(
            source_class=SOURCE_FEE_DELTA,
            surface_id=CANDIDATE_SURFACE_ACCOUNT_BILLS,
            field="fee",
            raw_token=fee_marker,
            currency="",
            account_identity_ref=account_identity_ref,
            time_as_of=time_as_of,
            extra={"forbidden_conversion": FORBIDDEN_RELABEL},
        )
    )
    _add(
        _observation_from_token(
            source_class=SOURCE_ALGEBRAIC_RESIDUAL,
            surface_id=NONE_TOKEN,
            field="eq_residual",
            raw_token=residual_marker,
            currency="",
            account_identity_ref=account_identity_ref,
            time_as_of=time_as_of,
            extra={"algebraic_eq_identity_used": TRUE_TOKEN},
        )
    )
    return observations


def _classification_payload(item: LiabilityCandidateClassificationV1) -> dict[str, str]:
    return {
        "source_class": item.source_class,
        "classification": item.classification,
        "classification_reason": item.classification_reason,
        "liability_identity": item.liability_identity,
        "liability_exists": item.liability_exists,
        "liability_value": item.liability_value,
        "affects_equity_stock": item.affects_equity_stock,
        "already_embedded_in_eq": item.already_embedded_in_eq,
        "account_scope_identity_status": item.account_scope_identity_status,
        "time_scope_identity_status": item.time_scope_identity_status,
        "currency_scope_identity_status": item.currency_scope_identity_status,
        "raw_row_digest": item.raw_row_digest,
        "interpretation_separated_from_raw": item.interpretation_separated_from_raw,
    }


def _embedding_payload(item: NonAlgebraicEmbeddingIdentityAssessmentV1) -> dict[str, str]:
    return {
        "liability_event_identity_proven": item.liability_event_identity_proven,
        "event_belongs_to_bound_account_time_currency": (
            item.event_belongs_to_bound_account_time_currency
        ),
        "equity_stock_effect_proven": item.equity_stock_effect_proven,
        "effect_already_embedded_in_other_component": (
            item.effect_already_embedded_in_other_component
        ),
        "p01_u05_overlap_disproven": item.p01_u05_overlap_disproven,
        "once_only_stock_effect_proven": item.once_only_stock_effect_proven,
        "double_counting_guard_proven": item.double_counting_guard_proven,
        "non_algebraic_embedding_identity": item.non_algebraic_embedding_identity,
        "algebraic_eq_identity_used": item.algebraic_eq_identity_used,
        "embedding_witness_id": item.embedding_witness_id,
        "assessment_reason": item.assessment_reason,
    }


def _assert_parent_ca_pack(*, sealed_ca_pack: Path) -> None:
    if verify_manifest_sha256_v1(store_root=sealed_ca_pack) != 0:
        raise BorrowOrAccountLiabilityStateProducerError("CA_MANIFEST_MISMATCH")
    claims = _load_json_object(path=sealed_ca_pack / CLAIMS_FILE)
    if claims.get("U05_DECISION_AFTER") != DECISION_REMAIN_UNKNOWN:
        raise BorrowOrAccountLiabilityStateProducerError("PARENT_CA_U05_NOT_REMAIN_UNKNOWN")
    if claims.get("PRODUCTIVE_ACQUISITION_EXECUTED") != FALSE_TOKEN:
        raise BorrowOrAccountLiabilityStateProducerError("PARENT_CA_MUST_NOT_HAVE_ACQUIRED")
    if claims.get("CONCRETE_SURFACE_SELECTION_STATUS") != CA_SELECTION_STATUS:
        raise BorrowOrAccountLiabilityStateProducerError("PARENT_CA_SELECTION_DRIFT")
    if claims.get("NEXT_OWNER_GO_REQUIRED") != PARENT_CA_NEXT_OWNER_GO:
        raise BorrowOrAccountLiabilityStateProducerError("PARENT_CA_NEXT_OWNER_GO_DRIFT")


def _inspect_vault_presence(*, repo: Path, vault_file: Path | str | None) -> dict[str, str]:
    resolved = Path(vault_file) if vault_file is not None else default_vault_path_v1(repo_root=repo)
    presence = inspect_credential_material_presence_v1(vault_file=resolved)
    if presence.get("VALUES_INCLUDED") is not False:
        raise BorrowOrAccountLiabilityStateProducerError("SECRET_VALUES_MUST_NOT_BE_INCLUDED")
    available = presence.get("available") is True
    reason = str(presence.get("reason") or NONE_TOKEN)
    payload = {
        "layer": "FORENSIC_RAW_EVIDENCE",
        "vault_file_present": TRUE_TOKEN if presence.get("VAULT_FILE_PRESENT") else FALSE_TOKEN,
        "secretref_uri_bound": TRUE_TOKEN if presence.get("SECRETREF_URI_BOUND") else FALSE_TOKEN,
        "credential_fields_complete": (
            TRUE_TOKEN if presence.get("CREDENTIAL_FIELDS_COMPLETE") else FALSE_TOKEN
        ),
        "values_included": FALSE_TOKEN,
        "available": TRUE_TOKEN if available else FALSE_TOKEN,
        "reason": reason,
        "secret_resolution_status": SECRET_RESOLUTION_NOT_ATTEMPTED,
        "secrets_or_signatures_persisted": FALSE_TOKEN,
    }
    _assert_no_secret_material(blob=_canonical_json(payload), label="VAULT_PRESENCE")
    return payload


def execute_borrow_or_account_liability_state_and_non_algebraic_embedding_identity_producer_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    genesis_store_root: Path | str | None = None,
    sealed_ca_pack: Path | str | None = None,
    sealed_gate_a_pack: Path | str | None = None,
    vault_file: Path | str | None = None,
    persist_as_of: str | None = None,
) -> BorrowOrAccountLiabilityStateProducerResultV1:
    if owner_go != OWNER_GO:
        raise BorrowOrAccountLiabilityStateProducerError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise BorrowOrAccountLiabilityStateProducerError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    ca_pack = (
        Path(sealed_ca_pack) if sealed_ca_pack is not None else repo / CANONICAL_CA_PACK_RELPATH
    )
    _assert_parent_ca_pack(sealed_ca_pack=ca_pack)
    gate_a_pack = (
        Path(sealed_gate_a_pack)
        if sealed_gate_a_pack is not None
        else repo / CANONICAL_GATE_A_PACK_RELPATH
    )
    if verify_manifest_sha256_v1(store_root=gate_a_pack) != 0:
        raise BorrowOrAccountLiabilityStateProducerError("GATE_A_MANIFEST_MISMATCH")
    genesis_root = (
        Path(genesis_store_root)
        if genesis_store_root is not None
        else resolve_canonical_d4_d5_genesis_runtime_store_root_v1(repo_root=repo)
    )
    if genesis_root is None:
        raise BorrowOrAccountLiabilityStateProducerError("GENESIS_STORE_ABSENT")
    d4 = load_bound_account_identity_runtime_binding_v1(store_root=genesis_root)
    d5 = load_checkpoint_observation_window_binding_v1(store_root=genesis_root)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    _require_non_empty_str(field="persist_as_of", raw=as_of)
    vault_presence = _inspect_vault_presence(repo=repo, vault_file=vault_file)
    observations = census_sealed_raw_observations_v1(
        gate_a_pack=gate_a_pack,
        account_identity_ref=d4.identity_digest,
        time_as_of=d5.binding_id,
    )
    classified: list[dict[str, Any]] = []
    qualifying = 0
    last_embedding: NonAlgebraicEmbeddingIdentityAssessmentV1 | None = None
    last_eligibility: dict[str, str] | None = None
    for observation in observations:
        algebraic_used = (
            TRUE_TOKEN if observation.source_class == SOURCE_ALGEBRAIC_RESIDUAL else FALSE_TOKEN
        )
        expected_currency = observation.currency
        classification = classify_raw_source_observation_v1(
            observation=observation,
            expected_account_identity_ref=d4.identity_digest,
            expected_time_as_of=d5.binding_id,
            expected_currency=expected_currency,
        )
        embedding = assess_non_algebraic_embedding_identity_v1(
            classification=classification,
            algebraic_eq_identity_used=algebraic_used,
            embedding_witness_id="",
            claimed_embedding_state=UNKNOWN_TOKEN,
        )
        state = build_borrow_or_account_liability_state_v1(
            observation=observation,
            classification=classification,
            bound_account_identity=d4.identity_digest,
            checkpoint_as_of=d5.binding_id,
        )
        eligibility = evaluate_u05_eligibility_from_liability_state_v1(
            state=state,
            embedding=embedding,
        )
        if classification.classification != CLASSIFICATION_NOT_EVENT and (
            classification.liability_identity not in {"", UNKNOWN_TOKEN}
        ):
            qualifying += 1
        classified.append(
            {
                "source_class": observation.source_class,
                "surface_id": observation.surface_id,
                "raw_field": observation.raw_field,
                "raw_token_empty": TRUE_TOKEN if observation.raw_token == "" else FALSE_TOKEN,
                "classification": _classification_payload(classification),
                "embedding": _embedding_payload(embedding),
                "eligibility": eligibility,
                "data_class": state.data_class,
                "canonical_status": state.canonical_status,
            }
        )
        last_embedding = embedding
        last_eligibility = eligibility
    if last_embedding is None or last_eligibility is None:
        raise BorrowOrAccountLiabilityStateProducerError("CENSUS_EMPTY")
    if qualifying != 0:
        raise BorrowOrAccountLiabilityStateProducerError("QUALIFYING_EVENT_MUST_REMAIN_ZERO")
    law_outcome = evaluate_u05_primary_proof_v1(proof={})
    if law_outcome.outcome != OUTCOME_NONQUALIFYING:
        raise BorrowOrAccountLiabilityStateProducerError("ABSENT_PROOF_MUST_BE_NONQUALIFYING")
    producer_contract = {
        "layer": "CANONICAL_AUTHORITY",
        "producer_id": PRODUCER_ID,
        "producer_status": PRODUCER_STATUS,
        "existing_producer_found": FALSE_TOKEN,
        "existing_producer_id": EXISTING_PRODUCER_ID,
        "data_class": DATA_CLASS_BORROW_OR_ACCOUNT_LIABILITY_STATE,
        "liability_identity_model": LIABILITY_IDENTITY_MODEL,
        "observation_domain": OBS_LIABILITY,
        "raw_separated_from_interpretation": TRUE_TOKEN,
        "unknown_first_class": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "account_bills_canonicalized": FALSE_TOKEN,
        "p01_authority_expanded": FALSE_TOKEN,
        "trading_logic_authority": FALSE_TOKEN,
        "endpoint_selected": FALSE_TOKEN,
        "data_class_endpoint_status": "REQUIRED_DATA_CLASS_NO_ENDPOINT_SELECTED",
        "reused_components": (
            "OBS_D6_LIABILITY_V1,evaluate_u05_primary_proof_v1,U05_RAW_FIELDS,"
            "GATE_A_forensic_liability_tokens_v1,S6_unclassified_bill_tokens,"
            "observation_boundary_bills_fee_exogenous,P01_U05_OVERLAP_UNRESOLVED,"
            "CA_NONE_BINDABLE"
        ),
    }
    census = {
        "layer": "FORENSIC_RAW_EVIDENCE",
        "classified_observation_count": str(len(classified)),
        "qualifying_liability_event_count": "0",
        "double_counting_guard": "SNAPSHOT_BILL_FILL_FEE_RESIDUAL_NOT_COUNTED_AS_LIABILITY_EVENTS",
        "records": classified,
    }
    predicates = {
        "layer": "ADJUDICATED_CONCLUSION",
        "independent_liability_event_proven": FALSE_TOKEN,
        "event_after_prior_proven": FALSE_TOKEN,
        "d4_d5_binding_present": TRUE_TOKEN,
        "d4_identity_digest": d4.identity_digest,
        "d5_binding_id": d5.binding_id,
        "prior_anchor_id_present": AUTHORIZED_ANCHOR_ID,
        "d4_d5_scope_identity_proven": FALSE_TOKEN,
        "non_algebraic_embedding_identity": UNKNOWN_TOKEN,
        "p01_u05_overlap_state": P01_U05_OVERLAP_STATE,
        "p01_u05_overlap_disproven": FALSE_TOKEN,
        "once_only_equity_stock_effect_proven": FALSE_TOKEN,
        "double_counting_guard_proven": TRUE_TOKEN,
        "equity_stock_effect_proven": FALSE_TOKEN,
        "absence_is_not_exclude": TRUE_TOKEN,
        "get_alone_may_include": FALSE_TOKEN,
        "get_alone_may_exclude": FALSE_TOKEN,
        "account_scope_identity_status": "D4_BINDING_PRESENT_EVENT_IDENTITY_UNBOUND",
        "time_scope_identity_status": "D5_BINDING_PRESENT_EVENT_IDENTITY_UNBOUND",
        "currency_scope_identity_status": "CURRENCY_UNBOUND_NO_LIABILITY_EVENT",
        "embedding_assessment_reason": last_embedding.assessment_reason,
    }
    evaluation = {
        "layer": "ADJUDICATED_CONCLUSION",
        "current_primary_proof_present": FALSE_TOKEN,
        "law_outcome": law_outcome.outcome,
        "law_basis": law_outcome.basis,
        "u05_primary_proof_status": PRIMARY_PROOF_STATUS,
        "blocker_id": BLOCKER_ID,
        "u05_decision_after": DECISION_REMAIN_UNKNOWN,
        "u05_decision_basis": DECISION_BASIS,
        "include_from_unknown": "FORBIDDEN_UNTIL_POSITIVE_PRIMARY_PROOF",
        "exclude_from_unknown": "FORBIDDEN_UNTIL_POSITIVE_IN_BASE_PROOF",
        "productive_acquisition_authorized": FALSE_TOKEN,
        "concrete_get_surface_discovered": FALSE_TOKEN,
        "concrete_surface_id": NONE_TOKEN,
        "surface_capability_proven": FALSE_TOKEN,
        "surface_binding_status": "NOT_BOUND",
        "last_eligibility_law_outcome": last_eligibility["law_outcome"],
    }
    architecture = {
        "layer": "CANONICAL_AUTHORITY",
        "blocker_id": BLOCKER_ID,
        "architecture_blocker": ARCHITECTURE_BLOCKER,
        "missing_positive_proof_component": (
            "INDEPENDENT_LIABILITY_EVENT_RECORD_AND_NON_EQ_SOURCE_EMBEDDING_WITNESS"
        ),
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_action": "STOP_AWAIT_OWNER_MERGE_GO_THEN_INDEPENDENT_EVENT_SURFACE_OR_WITNESS",
        "why_blocker_cannot_be_resolved_in_current_authority": (
            "Sealed snapshot tokens are stock not events; bills remain unclassified "
            "and mapped to fee/exogenous; fills remain trade evidence; no other GET "
            "surface is present in src or atlas; kind invention and bills relabel "
            "remain forbidden; productive GET remains unauthorized."
        ),
    }
    root = Path(evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PARENT_CA_NEXT_OWNER_GO": PARENT_CA_NEXT_OWNER_GO,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "U05_EVIDENCE_CLASS": CLASS_U05,
        "AUTHORIZED_ACQUISITION_SURFACE": ACQUISITION_SURFACE,
        "EXPECTED_PRIMARY_PROOF_OBJECT": PROOF_OBJECT_U05,
        "EXISTING_PRODUCER_FOUND": FALSE_TOKEN,
        "EXISTING_PRODUCER_ID": EXISTING_PRODUCER_ID,
        "BORROW_OR_ACCOUNT_LIABILITY_STATE_PRODUCER_STATUS": PRODUCER_STATUS,
        "PRODUCER_ID": PRODUCER_ID,
        "RAW_SOURCE_CLASS": (
            f"{SOURCE_BALANCE_SNAPSHOT},{SOURCE_VENUE_BILL},{SOURCE_TRADE_FILL},"
            f"{SOURCE_FEE_DELTA},{SOURCE_ALGEBRAIC_RESIDUAL}"
        ),
        "LIABILITY_IDENTITY_MODEL": LIABILITY_IDENTITY_MODEL,
        "CONCRETE_SURFACE_ID": NONE_TOKEN,
        "HTTP_METHOD": NONE_TOKEN,
        "BOUND_ENDPOINT": NONE_TOKEN,
        "PRIMARY_PROOF_ROLE_BOUND": FALSE_TOKEN,
        "MAX_GET_COUNT": "0",
        "RETRY_ALLOWED": FALSE_TOKEN,
        "HOPE_GET_FORBIDDEN": TRUE_TOKEN,
        "SURFACE_BINDING_STATUS": "NOT_BOUND",
        "PRODUCTIVE_ACQUISITION_AUTHORIZED": FALSE_TOKEN,
        "AUTHORIZED_GET_COUNT": "0",
        "ACTUAL_GET_COUNT": "0",
        "POST_COUNT": "0",
        "VAULT_AVAILABLE": vault_presence["available"],
        "SECRET_RESOLUTION_STATUS": SECRET_RESOLUTION_NOT_ATTEMPTED,
        "INDEPENDENT_LIABILITY_EVENT_PROVEN": FALSE_TOKEN,
        "EQUITY_STOCK_EFFECT_PROVEN": FALSE_TOKEN,
        "NON_ALGEBRAIC_EMBEDDING_IDENTITY": UNKNOWN_TOKEN,
        "P01_U05_OVERLAP_DISPROVEN": FALSE_TOKEN,
        "ONCE_ONLY_EQUITY_STOCK_EFFECT_PROVEN": FALSE_TOKEN,
        "DOUBLE_COUNTING_GUARD_PROVEN": TRUE_TOKEN,
        "U05_PRIMARY_PROOF_STATUS": PRIMARY_PROOF_STATUS,
        "U05_DECISION_BEFORE": DECISION_REMAIN_UNKNOWN,
        "U05_DECISION_AFTER": DECISION_REMAIN_UNKNOWN,
        "U05_DECISION_BASIS": DECISION_BASIS,
        "U06_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "BLOCKER_ID": BLOCKER_ID,
        "ARCHITECTURE_BLOCKER": ARCHITECTURE_BLOCKER,
        "PRODUCTIVE_ACQUISITION_EXECUTED": FALSE_TOKEN,
        "GATE_A_REOPENED": FALSE_TOKEN,
        "GATE_B_REEXECUTED": FALSE_TOKEN,
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "ACCOUNT_BILLS_CANONICALIZED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "C17_CREATED": FALSE_TOKEN,
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "NEXT_ACTION": architecture["next_action"],
        "SECRETS_OR_SIGNATURES_PERSISTED": FALSE_TOKEN,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
        "CLASSIFIED_OBSERVATION_COUNT": str(len(classified)),
        "QUALIFYING_LIABILITY_EVENT_COUNT": "0",
    }
    lineage = {
        "origin_main_sha": origin_main_sha,
        "owner_go": OWNER_GO,
        "genesis_id": EXPECTED_GENESIS_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "persist_as_of": as_of,
        "parent_ca_pack": CANONICAL_CA_PACK_RELPATH,
        "parent_gate_a_pack": CANONICAL_GATE_A_PACK_RELPATH,
        "parent_s6_pack": CANONICAL_S6_PACK_RELPATH,
        "d4_identity_digest": d4.identity_digest,
        "d5_binding_id": d5.binding_id,
        "prior_anchor_id": AUTHORIZED_ANCHOR_ID,
        "reconstruction_source_authority": FALSE_TOKEN,
    }
    protected = {
        "master_v2_unchanged": TRUE_TOKEN,
        "double_play_unchanged": TRUE_TOKEN,
        "bull_bear_state_switch_unchanged": TRUE_TOKEN,
        "self_learning_unchanged": TRUE_TOKEN,
        "top20_unchanged": TRUE_TOKEN,
        "full_core_autonomy_unchanged": TRUE_TOKEN,
        "step_29p_unchanged": TRUE_TOKEN,
        "u06_unchanged": TRUE_TOKEN,
        "residual_unchanged": TRUE_TOKEN,
        "gate_a_not_retried": TRUE_TOKEN,
        "gate_b_not_executed": TRUE_TOKEN,
        "bills_authority_unchanged": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "p01_authority_unchanged": TRUE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "reconstruction_implemented": FALSE_TOKEN,
        "dag_pin": DAG_PIN,
    }
    layers = {
        "CANONICAL_AUTHORITY": ("producer_contract_v1.json,architecture_blocker_v1.json"),
        "FORENSIC_RAW_EVIDENCE": "producer_census_v1.json,vault_presence_v1.json",
        "ADJUDICATED_CONCLUSION": (
            "predicate_adjudication_v1.json,current_proof_evaluation_v1.json"
        ),
        "HISTORICAL": "LINEAGE.json",
        "NAVIGATION": "FORBIDDEN_AS_AUTHORITY",
        "INTERPRETATION": "FORBIDDEN",
        "HYPOTHESIS": "FORBIDDEN",
        "UNRESOLVED_OR_CONTRADICTORY": BLOCKER_ID,
    }
    _persist_json(path=root / CLAIMS_FILE, payload=claims)
    _persist_json(path=root / "producer_contract_v1.json", payload=producer_contract)
    _persist_json(path=root / "producer_census_v1.json", payload=census)
    _persist_json(path=root / "architecture_blocker_v1.json", payload=architecture)
    _persist_json(path=root / "predicate_adjudication_v1.json", payload=predicates)
    _persist_json(path=root / "current_proof_evaluation_v1.json", payload=evaluation)
    _persist_json(path=root / "vault_presence_v1.json", payload=vault_presence)
    _persist_json(path=root / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=root / "layers_v1.json", payload=layers)
    _persist_json(path=root / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=root)
    if verify_manifest_sha256_v1(store_root=root) != 0:
        raise BorrowOrAccountLiabilityStateProducerError("MANIFEST_VERIFY_NOT_ZERO")
    return BorrowOrAccountLiabilityStateProducerResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=as_of,
        store_root=str(root),
        producer_id=PRODUCER_ID,
        producer_status=PRODUCER_STATUS,
        existing_producer_found=FALSE_TOKEN,
        classified_observation_count=str(len(classified)),
        qualifying_liability_event_count="0",
        authorized_get_count="0",
        actual_get_count="0",
        post_count="0",
        vault_available=vault_presence["available"],
        secret_resolution_status=SECRET_RESOLUTION_NOT_ATTEMPTED,
        u05_primary_proof_status=PRIMARY_PROOF_STATUS,
        u05_decision_after=DECISION_REMAIN_UNKNOWN,
        u05_decision_basis=DECISION_BASIS,
        non_algebraic_embedding_identity=UNKNOWN_TOKEN,
        productive_acquisition_executed=FALSE_TOKEN,
        evidence_manifest=str(root / "MANIFEST.sha256"),
    )


__all__ = [
    "ARCHITECTURE_BLOCKER",
    "BLOCKER_ID",
    "CANONICAL_PACK_RELPATH",
    "CANONICAL_PERSIST_AS_OF",
    "CLASSIFICATION_NOT_EVENT",
    "CLASSIFICATION_UNKNOWN",
    "DECISION_BASIS",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "EXISTING_PRODUCER_ID",
    "LIABILITY_IDENTITY_MODEL",
    "NEXT_OWNER_GO",
    "OWNER_GO",
    "PRIMARY_PROOF_STATUS",
    "PRODUCER_ID",
    "PRODUCER_STATUS",
    "RawSourceObservationV1",
    "SOURCE_ALGEBRAIC_RESIDUAL",
    "SOURCE_BALANCE_SNAPSHOT",
    "SOURCE_FEE_DELTA",
    "SOURCE_INDEPENDENT_EVENT",
    "SOURCE_TRADE_FILL",
    "SOURCE_UNKNOWN",
    "SOURCE_VENUE_BILL",
    "BorrowOrAccountLiabilityStateProducerError",
    "assess_non_algebraic_embedding_identity_v1",
    "build_borrow_or_account_liability_state_v1",
    "classify_raw_source_observation_v1",
    "evaluate_u05_eligibility_from_liability_state_v1",
    "execute_borrow_or_account_liability_state_and_non_algebraic_embedding_identity_producer_v1",
]
