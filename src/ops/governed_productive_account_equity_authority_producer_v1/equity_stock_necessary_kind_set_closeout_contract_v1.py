"""D6 Mini-Slice 1 EQUITY_STOCK necessary kind-set closeout.

Named include/exclude/unknown adjudication. Does not invent classified
kinds. Does not treat empty as zero necessary events. Does not release
Mini-Slice 2. No venue GET. Not reconstruction. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.classified_event_kind_set_and_source_seam_contract_v1 import (
    DISPOSITION_C01_C16_FORBIDDEN,
    DISPOSITION_EXCLUDED,
    DISPOSITION_NOT_EQUITY_STOCK,
    DISPOSITION_NOT_EVENT_KIND,
    DISPOSITION_UNKNOWN,
    build_forensic_event_kind_census_findings_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_COMPLETENESS_PRECONDITIONS_PROVEN,
    EARLIEST_D6_KIND_SET_DEPENDENCY,
    EVENT_KIND_SOURCE_SEAM_SELECTED,
    KIND_SET_CLOSEOUT_CREATED,
    KIND_SET_CLOSEOUT_STATUS,
    KIND_SET_RESOLVED,
    MS1_KIND_SET_FULLY_CLOSED,
    MS2_AUTHORIZED,
    NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    SOURCE_SELECTED,
    UNKNOWN_NECESSARY_CLASS_REMAINS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
    RATIFIED_CLASSIFIED_KIND_SET_RESOLVED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.source_candidate_v1 import (
    C01_C16_IDS,
)

SCHEMA_CLASS = "EQUITY_STOCK_NECESSARY_KIND_SET_CLOSEOUT_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
LAYER_CANONICAL_AUTHORITY = "CANONICAL_AUTHORITY"
LAYER_FORENSIC_RAW = "FORENSIC_RAW"
LAYER_ADJUDICATED = "ALREADY_ADJUDICATED"
LAYER_UNRESOLVED = "UNRESOLVED_OR_CONTRADICTORY"
DISPOSITION_INCLUDE = "INCLUDED_RATIFIED_CLASSIFIED_EQUITY_STOCK_KIND"
CLOSEOUT_STATUS_FAIL_CLOSED = "FAIL_CLOSED_NAMED_REMAINING_UNKNOWN"
NAMED_REMAINING_UNKNOWN_TOKEN = ",".join(NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES)
EXCLUDED_CANDIDATE_IDS: Tuple[str, ...] = (
    "UNKNOWN",
    "UNCLASSIFIED",
    "FILL",
    "U02_REALIZED_PNL",
    "U03_UNREALIZED_PNL_MTM",
    "U04_PENDING_ORDER_RESERVATION",
    "P01_GOVERNED_RISK_CAPITAL_REDUCTION",
    "C01_THROUGH_C16",
    "EXECUTION_LEDGER_FILL_OR_MARK",
)
REQUIRED_UNKNOWN_CANDIDATE_IDS: Tuple[str, ...] = NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES
FORBIDDEN_RECLASSIFY_IDS: Tuple[str, ...] = (
    "FILL",
    "U02_REALIZED_PNL",
    "U03_UNREALIZED_PNL_MTM",
    "U04_PENDING_ORDER_RESERVATION",
    "P01_GOVERNED_RISK_CAPITAL_REDUCTION",
    "C01_THROUGH_C16",
)


class EquityStockNecessaryKindSetCloseoutContractError(ValueError):
    """Fail-closed necessary kind-set closeout violation."""


@dataclass(frozen=True)
class NecessaryKindDispositionRecordV1:
    candidate_id: str
    layer: str
    disposition: str
    equity_stock_kind_status: str
    evidence_refs: str
    rationale: str


@dataclass(frozen=True)
class EquityStockNecessaryKindSetCloseoutV1:
    closeout_id: str
    included_classified_kinds: str
    excluded_candidate_ids: str
    named_remaining_unknown_necessary_classes: str
    kind_set_resolved: str
    unknown_necessary_class_remains: str
    absence_is_not_zero_events: str
    ms1_kind_set_fully_closed: str
    ms2_authorized: str
    authorized_productive_event_source_seam_present: str
    event_kind_source_seam_selected: str
    source_selected: str
    raw_eq_source_authority: str
    complete_event_stream_proven: str
    d6_completeness_preconditions_proven: str
    reconstruction_engine_created: str
    c17_created: str
    closeout_status: str
    earliest_d6_kind_set_dependency: str
    authority_effect: str
    provenance_digest: str


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_kind_set_closeout_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            f"KIND_SET_CLOSEOUT_FIELD_MISSING:{field}"
        )
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise EquityStockNecessaryKindSetCloseoutContractError(
            f"KIND_SET_CLOSEOUT_FIELD_NOT_STRING:{field}"
        )
    text = raw.strip()
    if text == "" or text != raw:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            f"KIND_SET_CLOSEOUT_FIELD_MISSING:{field}"
        )
    return text


def _assert_shared_pins() -> None:
    if ACCOUNT_EQUITY_AUTHORITY_OWNER != (
        "ops.governed_productive_account_equity_authority_producer_v1"
    ):
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "KIND_SET_CLOSEOUT_AUTHORITY_OWNER_MUTATED"
        )
    if KIND_SET_CLOSEOUT_CREATED is not True:
        raise EquityStockNecessaryKindSetCloseoutContractError("KIND_SET_CLOSEOUT_CREATED_NOT_TRUE")
    if KIND_SET_RESOLVED is not False:
        raise EquityStockNecessaryKindSetCloseoutContractError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET_RESOLVED is not False:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "TAXONOMY_KIND_SET_RESOLVED_NOT_FALSE"
        )
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "CLASSIFIED_KIND_SET_MUST_REMAIN_EMPTY_FAIL_CLOSED"
        )
    if UNKNOWN_NECESSARY_CLASS_REMAINS is not True:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "UNKNOWN_NECESSARY_CLASS_MUST_REMAIN"
        )
    if MS1_KIND_SET_FULLY_CLOSED is not False:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "MS1_KIND_SET_FULLY_CLOSED_NOT_FALSE"
        )
    if MS2_AUTHORIZED is not False:
        raise EquityStockNecessaryKindSetCloseoutContractError("MS2_AUTHORIZED_NOT_FALSE")
    if KIND_SET_CLOSEOUT_STATUS != CLOSEOUT_STATUS_FAIL_CLOSED:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "KIND_SET_CLOSEOUT_STATUS_NOT_FAIL_CLOSED_NAMED_REMAINING_UNKNOWN"
        )
    if EARLIEST_D6_KIND_SET_DEPENDENCY != (
        "NAMED_REMAINING_UNKNOWN_NECESSARY_EQUITY_STOCK_KIND_SET"
    ):
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "EARLIEST_D6_KIND_SET_DEPENDENCY_DRIFT"
        )
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_NOT_ABSENT"
        )
    if EVENT_KIND_SOURCE_SEAM_SELECTED is not False:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "EVENT_KIND_SOURCE_SEAM_SELECTED_NOT_FALSE"
        )
    if SOURCE_SELECTED is not False:
        raise EquityStockNecessaryKindSetCloseoutContractError("SOURCE_SELECTED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise EquityStockNecessaryKindSetCloseoutContractError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "COMPLETE_EVENT_STREAM_PROVEN_NOT_FALSE"
        )
    if D6_COMPLETENESS_PRECONDITIONS_PROVEN is not False:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "D6_COMPLETENESS_PRECONDITIONS_PROVEN_NOT_FALSE"
        )
    if C17_CREATED is not False:
        raise EquityStockNecessaryKindSetCloseoutContractError("C17_CREATED_NOT_FALSE")
    if RECONSTRUCTION_ENGINE_CREATED is not False:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "RECONSTRUCTION_ENGINE_CREATED_NOT_FALSE"
        )
    if NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES != REQUIRED_UNKNOWN_CANDIDATE_IDS:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES_DRIFT"
        )
    if len(C01_C16_IDS) != 16:
        raise EquityStockNecessaryKindSetCloseoutContractError("C01_C16_IDENTITY_DRIFT")


def build_necessary_kind_disposition_records_v1() -> Tuple[NecessaryKindDispositionRecordV1, ...]:
    _assert_shared_pins()
    runbook = "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
    taxonomy = (
        "src/ops/governed_productive_account_equity_authority_producer_v1/"
        "equity_affecting_event_taxonomy_contract_v1.py"
    )
    algebra = (
        "src/ops/governed_productive_account_equity_authority_producer_v1/"
        "reconstruction_algebra_contract_v1.py"
    )
    census = (
        "src/ops/governed_productive_account_equity_authority_producer_v1/"
        "classified_event_kind_set_and_source_seam_contract_v1.py"
    )
    records = (
        NecessaryKindDispositionRecordV1(
            candidate_id="UNKNOWN",
            layer=LAYER_CANONICAL_AUTHORITY,
            disposition=DISPOSITION_UNKNOWN,
            equity_stock_kind_status="REPRESENTABLE_NOT_CLASSIFIED",
            evidence_refs=f"{runbook}#11.2.1.AR;{taxonomy}",
            rationale="UNKNOWN remains representable and reconstruction-invalid; not a ratified classified kind",
        ),
        NecessaryKindDispositionRecordV1(
            candidate_id="UNCLASSIFIED",
            layer=LAYER_CANONICAL_AUTHORITY,
            disposition=DISPOSITION_UNKNOWN,
            equity_stock_kind_status="REPRESENTABLE_NOT_CLASSIFIED",
            evidence_refs=f"{runbook}#11.2.1.AR;{taxonomy}",
            rationale="UNCLASSIFIED remains representable and reconstruction-invalid; not a ratified classified kind",
        ),
        NecessaryKindDispositionRecordV1(
            candidate_id="FILL",
            layer=LAYER_ADJUDICATED,
            disposition=DISPOSITION_EXCLUDED,
            equity_stock_kind_status="UNRATIFIED_TEST_TOKEN_NOT_RECLASSIFIED",
            evidence_refs=f"{census};{taxonomy}",
            rationale="FILL remains an unratified test token; Mini-Slice 1 does not reclassify it into the kind set",
        ),
        NecessaryKindDispositionRecordV1(
            candidate_id="U02_REALIZED_PNL",
            layer=LAYER_ADJUDICATED,
            disposition=DISPOSITION_NOT_EVENT_KIND,
            equity_stock_kind_status="ALGEBRA_TERM_EMBEDDED_NOT_EVENT_KIND",
            evidence_refs=f"{runbook}#11.2.1.AR;{algebra}",
            rationale="U02 is EMBEDDED_NOT_SEPARATE; algebra terms are not classified EQUITY_STOCK event kinds",
        ),
        NecessaryKindDispositionRecordV1(
            candidate_id="U03_UNREALIZED_PNL_MTM",
            layer=LAYER_ADJUDICATED,
            disposition=DISPOSITION_NOT_EVENT_KIND,
            equity_stock_kind_status="ALGEBRA_TERM_EMBEDDED_NOT_EVENT_KIND",
            evidence_refs=f"{runbook}#11.2.1.AR;{algebra}",
            rationale="U03 is EMBEDDED_NOT_SEPARATE; algebra terms are not classified EQUITY_STOCK event kinds",
        ),
        NecessaryKindDispositionRecordV1(
            candidate_id="U04_PENDING_ORDER_RESERVATION",
            layer=LAYER_ADJUDICATED,
            disposition=DISPOSITION_NOT_EQUITY_STOCK,
            equity_stock_kind_status="NOT_EQUITY_STOCK_KIND",
            evidence_refs=f"{runbook}#11.2.1.AR;{algebra}",
            rationale="U04 belongs to AVAILABLE_FOR_SIZING / RISK-SIZING and is not a D6 EQUITY_STOCK kind",
        ),
        NecessaryKindDispositionRecordV1(
            candidate_id="P01_GOVERNED_RISK_CAPITAL_REDUCTION",
            layer=LAYER_ADJUDICATED,
            disposition=DISPOSITION_NOT_EQUITY_STOCK,
            equity_stock_kind_status="NOT_EQUITY_SOURCE_OR_EVENT_KIND",
            evidence_refs=f"{runbook}#11.2.1.AR;{algebra}",
            rationale="P01 is applied after equity and is never an equity source or EQUITY_STOCK event kind",
        ),
        NecessaryKindDispositionRecordV1(
            candidate_id="C01_THROUGH_C16",
            layer=LAYER_ADJUDICATED,
            disposition=DISPOSITION_C01_C16_FORBIDDEN,
            equity_stock_kind_status="FORBIDDEN_AS_EVENT_TAXONOMY",
            evidence_refs=f"{runbook}#11.2.1.S;{census}",
            rationale="C01-C16 remain rejected source candidates and are not event taxonomy",
        ),
        NecessaryKindDispositionRecordV1(
            candidate_id="EXECUTION_LEDGER_FILL_OR_MARK",
            layer=LAYER_ADJUDICATED,
            disposition=DISPOSITION_EXCLUDED,
            equity_stock_kind_status="INTERNAL_LEDGER_NOT_D6_KIND",
            evidence_refs="src/execution/ledger/engine.py",
            rationale="Execution-ledger FILL/MARK is not a ratified D6 EQUITY_STOCK classified kind",
        ),
        NecessaryKindDispositionRecordV1(
            candidate_id="U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            layer=LAYER_UNRESOLVED,
            disposition=DISPOSITION_UNKNOWN,
            equity_stock_kind_status="CONDITIONAL_UNRATIFIED_UNKNOWN",
            evidence_refs=f"{runbook}#11.2.1.AR;{algebra}",
            rationale=(
                "U05_PLACEMENT allows EQUITY_STOCK only if genuine borrow/liability is not already "
                "embedded; algebra inclusion remains unresolved; placement is not kind ratification"
            ),
        ),
        NecessaryKindDispositionRecordV1(
            candidate_id="U06_FEE_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            layer=LAYER_UNRESOLVED,
            disposition=DISPOSITION_UNKNOWN,
            equity_stock_kind_status="EVENT_OR_RECONCILIATION_PLACEMENT_NOT_KIND",
            evidence_refs=f"{runbook}#11.2.1.AR;{algebra}",
            rationale=(
                "U06_PLACEMENT is EVENT_OR_RECONCILIATION_NOT_BLIND_SUBTRACTION; that placement is "
                "not classified FEE kind ratification; algebra inclusion remains unresolved"
            ),
        ),
        NecessaryKindDispositionRecordV1(
            candidate_id="RESIDUAL_UNNAMED_NECESSARY_EQUITY_STOCK_EVENT_CLASS",
            layer=LAYER_UNRESOLVED,
            disposition=DISPOSITION_UNKNOWN,
            equity_stock_kind_status="INVENTORY_COMPLETENESS_UNPROVEN",
            evidence_refs=f"{runbook}#11.2.1.AV;{taxonomy}",
            rationale=(
                "No canonical proof that the inventoried candidates exhaust all necessary "
                "EQUITY_STOCK-affecting classes; unnamed residual remains unknown; inventing "
                "deposit/transfer/funding/liquidation/convert kinds is forbidden"
            ),
        ),
    )
    included = tuple(
        record.candidate_id for record in records if record.disposition == DISPOSITION_INCLUDE
    )
    if included:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "INCLUDED_CLASSIFIED_KINDS_MUST_REMAIN_NONE_RATIFIED"
        )
    unknown_ids = tuple(
        record.candidate_id
        for record in records
        if record.candidate_id in REQUIRED_UNKNOWN_CANDIDATE_IDS
    )
    if unknown_ids != REQUIRED_UNKNOWN_CANDIDATE_IDS:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES_INCOMPLETE"
        )
    for record in records:
        if record.candidate_id in FORBIDDEN_RECLASSIFY_IDS and record.disposition in (
            DISPOSITION_INCLUDE,
            DISPOSITION_UNKNOWN,
        ):
            raise EquityStockNecessaryKindSetCloseoutContractError(
                f"FORBIDDEN_RECLASSIFY:{record.candidate_id}"
            )
    census_findings = build_forensic_event_kind_census_findings_v1()
    census_ids = {finding.candidate_id for finding in census_findings}
    if "FILL" not in census_ids or "U04_PENDING_ORDER_RESERVATION" not in census_ids:
        raise EquityStockNecessaryKindSetCloseoutContractError("PARENT_KIND_CENSUS_DRIFT")
    return records


def build_equity_stock_necessary_kind_set_closeout_v1(
    *,
    closeout_id: str,
) -> EquityStockNecessaryKindSetCloseoutV1:
    _assert_shared_pins()
    closeout = _require_non_empty_str(field="closeout_id", raw=closeout_id)
    records = build_necessary_kind_disposition_records_v1()
    excluded = ",".join(
        record.candidate_id for record in records if record.candidate_id in EXCLUDED_CANDIDATE_IDS
    )
    unknown_ids = ",".join(
        record.candidate_id
        for record in records
        if record.candidate_id in REQUIRED_UNKNOWN_CANDIDATE_IDS
    )
    if unknown_ids != NAMED_REMAINING_UNKNOWN_TOKEN:
        raise EquityStockNecessaryKindSetCloseoutContractError(
            "NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES_TOKEN_DRIFT"
        )
    if excluded != ",".join(EXCLUDED_CANDIDATE_IDS):
        raise EquityStockNecessaryKindSetCloseoutContractError("EXCLUDED_CANDIDATE_IDS_DRIFT")
    payload = {
        "closeout_id": closeout,
        "included_classified_kinds": "NONE_RATIFIED",
        "excluded_candidate_ids": excluded,
        "named_remaining_unknown_necessary_classes": unknown_ids,
        "kind_set_resolved": FALSE_TOKEN,
        "unknown_necessary_class_remains": TRUE_TOKEN,
        "absence_is_not_zero_events": TRUE_TOKEN,
        "ms1_kind_set_fully_closed": FALSE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "authorized_productive_event_source_seam_present": FALSE_TOKEN,
        "event_kind_source_seam_selected": FALSE_TOKEN,
        "source_selected": FALSE_TOKEN,
        "raw_eq_source_authority": FALSE_TOKEN,
        "complete_event_stream_proven": FALSE_TOKEN,
        "d6_completeness_preconditions_proven": FALSE_TOKEN,
        "reconstruction_engine_created": FALSE_TOKEN,
        "c17_created": FALSE_TOKEN,
        "closeout_status": CLOSEOUT_STATUS_FAIL_CLOSED,
        "earliest_d6_kind_set_dependency": EARLIEST_D6_KIND_SET_DEPENDENCY,
        "authority_effect": AUTHORITY_EFFECT,
    }
    digest = compute_kind_set_closeout_digest_v1(payload)
    return EquityStockNecessaryKindSetCloseoutV1(**payload, provenance_digest=digest)
