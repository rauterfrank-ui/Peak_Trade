"""D6 named remaining-unknown EQUITY_STOCK kind-set evidence persist.

Persists the closed read-only adjudication. Does not ratify kinds.
Does not re-decide INCLUDE/EXCLUDE. Does not release Mini-Slice 2.
No venue GET. Not reconstruction. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_COMPLETENESS_PRECONDITIONS_PROVEN,
    EARLIEST_D6_KIND_SET_DEPENDENCY,
    EVENT_KIND_SOURCE_SEAM_SELECTED,
    HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES,
    KIND_SET_EVIDENCE_PERSIST_CREATED,
    KIND_SET_EVIDENCE_PERSIST_STATUS,
    KIND_SET_RESOLVED,
    MS1_KIND_SET_FULLY_CLOSED,
    MS2_AUTHORIZED,
    NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    RESIDUAL_COMPLETENESS_PROVEN,
    RESIDUAL_KIND_DECISION,
    RESIDUAL_NO_REMAINDER_NORMALIZED,
    SOURCE_SELECTED,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
    UNKNOWN_NECESSARY_CLASS_REMAINS,
    U05_PLACEMENT,
    U06_PLACEMENT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
    RATIFIED_CLASSIFIED_KIND_SET_RESOLVED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.classified_event_kind_set_and_source_seam_contract_v1 import (
    DISPOSITION_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_stock_necessary_kind_set_closeout_contract_v1 import (
    REQUIRED_UNKNOWN_CANDIDATE_IDS,
    build_necessary_kind_disposition_records_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_overlap_with_u04_u05_contract_v1 import (
    P01_U05_OVERLAP_ADJUDICATION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    EMBEDDED_CONDITIONAL,
    INCLUSION_UNRESOLVED,
    U05_LIABILITIES_BORROWINGS,
    U06_FEES,
)

SCHEMA_CLASS = "NAMED_REMAINING_UNKNOWN_KIND_SET_EVIDENCE_PERSIST_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
DECISION_REMAIN_UNKNOWN = "REMAIN_UNKNOWN"
EVIDENCE_STATUS_FAIL_CLOSED = "FAIL_CLOSED_THREE_CANDIDATES_REMAIN_UNKNOWN"
HYPOTHESIS_ONLY_TOKEN = ",".join(HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES)
LAYER_CANONICAL_AUTHORITY = "CANONICAL_AUTHORITY"
LAYER_FORENSIC_RAW = "FORENSIC_RAW_EVIDENCE"
LAYER_ADJUDICATED = "ALREADY_ADJUDICATED"
LAYER_HYPOTHESIS = "HYPOTHESIS"
LAYER_UNRESOLVED = "UNRESOLVED_OR_CONTRADICTORY"
CANDIDATE_U05 = "U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND"
CANDIDATE_U06 = "U06_FEE_AS_CLASSIFIED_EQUITY_STOCK_KIND"
CANDIDATE_RESIDUAL = "RESIDUAL_UNNAMED_NECESSARY_EQUITY_STOCK_EVENT_CLASS"


class NamedRemainingUnknownKindSetEvidencePersistContractError(ValueError):
    """Fail-closed named remaining-unknown kind-set evidence persist violation."""


@dataclass(frozen=True)
class NamedRemainingUnknownKindEvidenceRecordV1:
    candidate_id: str
    decision: str
    layer: str
    economic_semantics: str
    embedding_status: str
    why_not_include: str
    why_not_exclude: str
    evidence_refs: str


@dataclass(frozen=True)
class NamedRemainingUnknownKindSetEvidencePersistV1:
    persist_id: str
    u05_kind_decision: str
    u06_kind_decision: str
    residual_kind_decision: str
    ratified_classified_event_kind_set: str
    kind_set_resolved: str
    unknown_necessary_class_remains: str
    ms1_kind_set_fully_closed: str
    ms2_authorized: str
    residual_completeness_proven: str
    residual_no_remainder_normalized: str
    hypothesis_only_classes: str
    p01_u05_overlap_adjudication: str
    evidence_persist_status: str
    earliest_d6_kind_set_dependency: str
    authority_effect: str
    provenance_digest: str


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_kind_set_evidence_persist_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            f"KIND_SET_EVIDENCE_FIELD_MISSING:{field}"
        )
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            f"KIND_SET_EVIDENCE_FIELD_NOT_STRING:{field}"
        )
    text = raw.strip()
    if text == "" or text != raw:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            f"KIND_SET_EVIDENCE_FIELD_MISSING:{field}"
        )
    return text


def _assert_shared_pins() -> None:
    if ACCOUNT_EQUITY_AUTHORITY_OWNER != (
        "ops.governed_productive_account_equity_authority_producer_v1"
    ):
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "KIND_SET_EVIDENCE_AUTHORITY_OWNER_MUTATED"
        )
    if KIND_SET_EVIDENCE_PERSIST_CREATED is not True:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "KIND_SET_EVIDENCE_PERSIST_CREATED_NOT_TRUE"
        )
    if KIND_SET_EVIDENCE_PERSIST_STATUS != EVIDENCE_STATUS_FAIL_CLOSED:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "KIND_SET_EVIDENCE_PERSIST_STATUS_DRIFT"
        )
    if KIND_SET_RESOLVED is not False:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "KIND_SET_RESOLVED_NOT_FALSE"
        )
    if RATIFIED_CLASSIFIED_KIND_SET_RESOLVED is not False:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "TAXONOMY_KIND_SET_RESOLVED_NOT_FALSE"
        )
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "CLASSIFIED_KIND_SET_MUST_REMAIN_EMPTY_FAIL_CLOSED"
        )
    if UNKNOWN_NECESSARY_CLASS_REMAINS is not True:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "UNKNOWN_NECESSARY_CLASS_MUST_REMAIN"
        )
    if MS1_KIND_SET_FULLY_CLOSED is not False:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "MS1_KIND_SET_FULLY_CLOSED_NOT_FALSE"
        )
    if MS2_AUTHORIZED is not False:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError("MS2_AUTHORIZED_NOT_FALSE")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "U05_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "U06_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if RESIDUAL_COMPLETENESS_PROVEN is not False:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "RESIDUAL_COMPLETENESS_MUST_REMAIN_UNPROVEN"
        )
    if RESIDUAL_NO_REMAINDER_NORMALIZED is not False:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "RESIDUAL_NO_REMAINDER_NORMALIZATION_FORBIDDEN"
        )
    if NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES != REQUIRED_UNKNOWN_CANDIDATE_IDS:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES_DRIFT"
        )
    if P01_U05_OVERLAP_ADJUDICATION != "UNKNOWN_RELATIONSHIP_FAIL_CLOSED":
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "P01_U05_OVERLAP_ADJUDICATION_DRIFT"
        )
    if U05_PLACEMENT != "EQUITY_STOCK_ONLY_IF_BORROW_LIAB_NOT_ALREADY_EMBEDDED":
        raise NamedRemainingUnknownKindSetEvidencePersistContractError("U05_PLACEMENT_DRIFT")
    if U06_PLACEMENT != "EVENT_OR_RECONCILIATION_NOT_BLIND_SUBTRACTION":
        raise NamedRemainingUnknownKindSetEvidencePersistContractError("U06_PLACEMENT_DRIFT")
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_NOT_ABSENT"
        )
    if EVENT_KIND_SOURCE_SEAM_SELECTED is not False:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "EVENT_KIND_SOURCE_SEAM_SELECTED_NOT_FALSE"
        )
    if SOURCE_SELECTED is not False:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError("SOURCE_SELECTED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "COMPLETE_EVENT_STREAM_PROVEN_NOT_FALSE"
        )
    if D6_COMPLETENESS_PRECONDITIONS_PROVEN is not False:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "D6_COMPLETENESS_PRECONDITIONS_PROVEN_NOT_FALSE"
        )
    if C17_CREATED is not False:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError("C17_CREATED_NOT_FALSE")
    if RECONSTRUCTION_ENGINE_CREATED is not False:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "RECONSTRUCTION_ENGINE_CREATED_NOT_FALSE"
        )
    if EARLIEST_D6_KIND_SET_DEPENDENCY != (
        "NAMED_REMAINING_UNKNOWN_NECESSARY_EQUITY_STOCK_KIND_SET"
    ):
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "EARLIEST_D6_KIND_SET_DEPENDENCY_DRIFT"
        )


def build_named_remaining_unknown_kind_evidence_records_v1() -> Tuple[
    NamedRemainingUnknownKindEvidenceRecordV1, ...
]:
    _assert_shared_pins()
    parent = {
        record.candidate_id: record for record in build_necessary_kind_disposition_records_v1()
    }
    for candidate_id in REQUIRED_UNKNOWN_CANDIDATE_IDS:
        parent_record = parent[candidate_id]
        if parent_record.disposition != DISPOSITION_UNKNOWN:
            raise NamedRemainingUnknownKindSetEvidencePersistContractError(
                f"PARENT_CLOSEOUT_DECISION_DRIFT:{candidate_id}"
            )
    runbook = "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
    algebra = (
        "src/ops/governed_productive_account_equity_authority_producer_v1/"
        "reconstruction_algebra_contract_v1.py"
    )
    overlap = (
        "src/ops/governed_productive_account_equity_authority_producer_v1/"
        "p01_overlap_with_u04_u05_contract_v1.py"
    )
    closeout = (
        "src/ops/governed_productive_account_equity_authority_producer_v1/"
        "equity_stock_necessary_kind_set_closeout_contract_v1.py"
    )
    return (
        NamedRemainingUnknownKindEvidenceRecordV1(
            candidate_id=CANDIDATE_U05,
            decision=DECISION_REMAIN_UNKNOWN,
            layer=LAYER_UNRESOLVED,
            economic_semantics=(
                "Genuine borrow/account liability reduces EQUITY_STOCK once if present "
                f"and not embedded; policy={U05_LIABILITIES_BORROWINGS}; "
                f"placement={U05_PLACEMENT}; placement is not kind ratification"
            ),
            embedding_status=f"{EMBEDDED_CONDITIONAL};inclusion={INCLUSION_UNRESOLVED}",
            why_not_include=(
                "Placement is not kind ratification; algebra term is not an event kind; "
                "no productive borrow observation; P01 overlap does not ratify a U05 kind"
            ),
            why_not_exclude=(
                "U05 is not EMBEDDED_NOT_SEPARATE; unknown inclusion cannot prove absence "
                "of a necessary EQUITY_STOCK delta"
            ),
            evidence_refs=f"{runbook}#11.2.1.AR;{runbook}#11.2.1.T;{algebra};{overlap};{closeout}",
        ),
        NamedRemainingUnknownKindEvidenceRecordV1(
            candidate_id=CANDIDATE_U06,
            decision=DECISION_REMAIN_UNKNOWN,
            layer=LAYER_UNRESOLVED,
            economic_semantics=(
                "Accrued/already-charged fee counted once in base or as a single subtraction; "
                f"policy={U06_FEES}; future fees are not U06; "
                f"placement={U06_PLACEMENT}; blind subtraction forbidden"
            ),
            embedding_status=(
                f"{EMBEDDED_CONDITIONAL};inclusion={INCLUSION_UNRESOLVED};"
                "base_or_event_or_reconciliation_unresolved"
            ),
            why_not_include=(
                "Event-or-reconciliation placement is not FEE kind ratification; "
                "bills/fills are not D6 authority"
            ),
            why_not_exclude=("Placement allows EVENT; fee inclusion remains blocking/unresolved"),
            evidence_refs=f"{runbook}#11.2.1.AR;{runbook}#11.2.1.T;{algebra};{closeout}",
        ),
        NamedRemainingUnknownKindEvidenceRecordV1(
            candidate_id=CANDIDATE_RESIDUAL,
            decision=DECISION_REMAIN_UNKNOWN,
            layer=LAYER_UNRESOLVED,
            economic_semantics=(
                "Modeled classes do not positively exhaust necessary EQUITY_STOCK event "
                "classes; residual unnamed class remains; "
                f"hypothesis_only={HYPOTHESIS_ONLY_TOKEN}"
            ),
            embedding_status="INVENTORY_COMPLETENESS_UNPROVEN",
            why_not_include=(
                "Inventing deposit/withdrawal/transfer/funding/interest/liquidation/convert "
                "kinds from plausibility is forbidden"
            ),
            why_not_exclude=(
                "Residual cannot become NO_REMAINDER without positive completeness proof"
            ),
            evidence_refs=f"{runbook}#11.2.1.AV;{runbook}#11.2.1.AW;{closeout}",
        ),
    )


def build_named_remaining_unknown_kind_set_evidence_persist_v1(
    *,
    persist_id: str,
) -> NamedRemainingUnknownKindSetEvidencePersistV1:
    _assert_shared_pins()
    persist = _require_non_empty_str(field="persist_id", raw=persist_id)
    records = build_named_remaining_unknown_kind_evidence_records_v1()
    by_id = {record.candidate_id: record for record in records}
    if tuple(by_id[candidate_id].decision for candidate_id in REQUIRED_UNKNOWN_CANDIDATE_IDS) != (
        DECISION_REMAIN_UNKNOWN,
        DECISION_REMAIN_UNKNOWN,
        DECISION_REMAIN_UNKNOWN,
    ):
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "NAMED_REMAINING_UNKNOWN_DECISIONS_MUST_REMAIN_UNKNOWN"
        )
    if by_id[CANDIDATE_U05].decision != U05_KIND_DECISION:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError("U05_DECISION_PIN_DRIFT")
    if by_id[CANDIDATE_U06].decision != U06_KIND_DECISION:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError("U06_DECISION_PIN_DRIFT")
    if by_id[CANDIDATE_RESIDUAL].decision != RESIDUAL_KIND_DECISION:
        raise NamedRemainingUnknownKindSetEvidencePersistContractError(
            "RESIDUAL_DECISION_PIN_DRIFT"
        )
    payload = {
        "persist_id": persist,
        "u05_kind_decision": U05_KIND_DECISION,
        "u06_kind_decision": U06_KIND_DECISION,
        "residual_kind_decision": RESIDUAL_KIND_DECISION,
        "ratified_classified_event_kind_set": "EMPTY_FAIL_CLOSED",
        "kind_set_resolved": FALSE_TOKEN,
        "unknown_necessary_class_remains": TRUE_TOKEN,
        "ms1_kind_set_fully_closed": FALSE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "residual_completeness_proven": FALSE_TOKEN,
        "residual_no_remainder_normalized": FALSE_TOKEN,
        "hypothesis_only_classes": HYPOTHESIS_ONLY_TOKEN,
        "p01_u05_overlap_adjudication": P01_U05_OVERLAP_ADJUDICATION,
        "evidence_persist_status": EVIDENCE_STATUS_FAIL_CLOSED,
        "earliest_d6_kind_set_dependency": EARLIEST_D6_KIND_SET_DEPENDENCY,
        "authority_effect": AUTHORITY_EFFECT,
    }
    digest = compute_kind_set_evidence_persist_digest_v1(payload)
    return NamedRemainingUnknownKindSetEvidencePersistV1(
        **payload,
        provenance_digest=digest,
    )
