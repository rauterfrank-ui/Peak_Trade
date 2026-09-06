"""Canonical binding attempt for §11.14 Live handoff `pos` semantics.

Fresh forensic census against current authority. Naming match is not identity.
Does not invent a unique meaning from plausibility. Does not mint an owner.
Does not join a writer or reader. Does not GET. Does not POST.
Does not execute a restart. Does not implement a producer.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    OKX_ORDER_DATA_ENTRY_FIELDS_V1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    ACCOUNTING_ONLY_IS_NOT_RESTART,
    A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
    NO_RECLASSIFICATION_OF_EVIDENCE_PACK_AS_CONTROL_HANDOFF,
    NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
    NO_TIMESTAMP_BACKFILL,
    RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
    SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
    VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.position_reconciled_predicate_v1 import (
    ADMISSIBLE_POS_FIELD,
    ADMISSIBLE_SOURCE_KIND as POSITION_RECONCILED_SOURCE_KIND,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET,
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_POS_SIDE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_required_field_contract_v1 import (
    POS_SEMANTICS as HISTORICAL_POS_SEMANTICS,
)

_REJECTED = "POS_DERIVATION_REJECTED"
_UNPROVEN = "POS_DERIVATION_UNPROVEN"
_ACCEPTED = "POS_DERIVATION_ACCEPTED"

POS_SEMANTICS = "UNPROVEN"
POS_SEMANTICS_STATUS = "UNPROVEN"
POS_CANONICAL_MEANING = "UNPROVEN"
POS_UNIT = "UNPROVEN"
POS_SIGN_SEMANTICS = "UNPROVEN"
POS_POS_SIDE_RELATION = "UNPROVEN"
POS_INSTRUMENT_BINDING = "MUST_EQUAL_BOUND_INSTID;UNIT_DIMENSION_UNPROVEN"
POS_POSITION_MODE_BINDING = "UNPROVEN"
POS_ACCOUNT_MODE_BINDING = "UNPROVEN"
POS_SEMANTICS_CAN_BE_BOUND_FROM_EXISTING_AUTHORITY = False
NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED = True
PROPOSED_NEXT_SLICE = "SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_SEMANTICS_AND_CONTRACT_V1"
ACK_ALLOWLIST = tuple(OKX_ORDER_DATA_ENTRY_FIELDS_V1)
ACK_OMITS_POS = "pos" not in ACK_ALLOWLIST
ACK_OMITS_POS_SIDE = "posSide" not in ACK_ALLOWLIST
ACK_OMITS_INST_ID = "instId" not in ACK_ALLOWLIST
ACK_OMITS_SZ = "sz" not in ACK_ALLOWLIST

_PROVEN_CONSTRAINTS: tuple[str, ...] = (
    "required nonempty Decimal-parseable string once a producer exists",
    "nonzero when bound fillSz is nonzero",
    "Peak_Trade-owned contemporaneous pre-restart capture",
    "must Decimal-equal bound Live submit/fill/position identity once produced",
    "instId must equal BOUND_INSTID",
    "must not be venue GET copy, accounting, fillSz, submitted sz, or retro synthesis",
)

_UNPROVEN_MEANING_AXES: tuple[str, ...] = (
    "intended vs acknowledged vs filled vs venue-raw vs accounting",
    "contracts vs venue contract count vs base vs quote vs normalized strategy qty",
    "signed vs unsigned magnitude plus posSide",
    "net-mode vs long/short position-mode semantics",
    "exact contemporaneous capture moment",
)


def _candidate(
    *,
    candidate_id: str,
    source_path: str,
    symbol_or_field: str,
    authority_class: str,
    runtime_or_offline: str,
    raw_or_normalized: str,
    unit: str,
    sign_semantics: str,
    pos_side_semantics: str,
    instrument_binding: str,
    account_mode_binding: str,
    position_mode_binding: str,
    producer: str,
    consumers: str,
    contemporaneous_at_handoff: str,
    peak_trade_owned: str,
    canonically_bound: bool,
    acceptable_for_handoff_pos: str,
    rejection_reason: str,
    disposition: str,
) -> dict[str, Any]:
    acceptable_bool = acceptable_for_handoff_pos == "true"
    return {
        "CANDIDATE_ID": candidate_id,
        "SOURCE_PATH": source_path,
        "SYMBOL_OR_FIELD": symbol_or_field,
        "AUTHORITY_CLASS": authority_class,
        "RUNTIME_OR_OFFLINE": runtime_or_offline,
        "RAW_OR_NORMALIZED": raw_or_normalized,
        "UNIT": unit,
        "SIGN_SEMANTICS": sign_semantics,
        "POS_SIDE_SEMANTICS": pos_side_semantics,
        "INSTRUMENT_BINDING": instrument_binding,
        "ACCOUNT_MODE_BINDING": account_mode_binding,
        "POSITION_MODE_BINDING": position_mode_binding,
        "PRODUCER": producer,
        "CONSUMERS": consumers,
        "CONTEMPORANEOUS_AT_HANDOFF": contemporaneous_at_handoff,
        "PEAK_TRADE_OWNED": peak_trade_owned,
        "CANONICALLY_BOUND": canonically_bound,
        "ACCEPTABLE_FOR_HANDOFF_POS": acceptable_for_handoff_pos,
        "ACCEPTABLE_FOR_HANDOFF_POS_BOOL": acceptable_bool,
        "REJECTION_REASON": rejection_reason,
        "DISPOSITION": disposition,
    }


_CANDIDATES: tuple[dict[str, Any], ...] = (
    _candidate(
        candidate_id="C01_ORDER_PLAN_QTY",
        source_path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"),
        symbol_or_field="LiveCanaryOrderPlanV1.sz",
        authority_class="PEAK_TRADE_ORDER_PLAN",
        runtime_or_offline="RUNTIME",
        raw_or_normalized="NORMALIZED",
        unit="contracts_as_order_plan_qty_not_handoff_pos",
        sign_semantics="unsigned_plan_magnitude",
        pos_side_semantics="omitted_from_plan",
        instrument_binding="plan_instId",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="order_plan_v1",
        consumers="submit_gates; submit_transport",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason=(
            "Order-plan sz is intended submit quantity. Authority does not equate "
            "submitted quantity with filled or handoff pos. "
            "ORDER_PLAN_QTY_UNIT=contracts is entry/order-plan, not POS_UNIT."
        ),
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C02_SUBMITTED_ORDER_SZ",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
        ),
        symbol_or_field="POST /api/v5/trade/order sz",
        authority_class="VENUE_SUBMIT_BODY",
        runtime_or_offline="RUNTIME",
        raw_or_normalized="RAW",
        unit="venue_sz_as_submitted_not_handoff_pos",
        sign_semantics="unsigned_submit_magnitude",
        pos_side_semantics="posSide_on_submit_body_not_handoff_pos",
        instrument_binding="submit_instId",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="canary_submit_transport",
        consumers="venue ACK path",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason=(
            "Submitted sz is the order size sent. FILL_IS_NOT_POSITION_PROOF and "
            "submitted quantity is not filled position. Not a handoff pos producer."
        ),
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C03_ACKNOWLEDGED_SZ",
        source_path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/http_client_v1.py"),
        symbol_or_field="ACK data[].sz",
        authority_class="VENUE_ACK_ALLOWLIST",
        runtime_or_offline="RUNTIME",
        raw_or_normalized="RAW",
        unit="ABSENT",
        sign_semantics="ABSENT",
        pos_side_semantics="ABSENT",
        instrument_binding="ABSENT",
        account_mode_binding="ABSENT",
        position_mode_binding="ABSENT",
        producer="OKX_ORDER_DATA_ENTRY_FIELDS_V1",
        consumers="submit_ack observed identity",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason=(
            "ACK allowlist is sCode,sMsg,ordId,clOrdId,tag. sz, pos, posSide, and "
            "instId are omitted. Acknowledged size is absent, not unproven."
        ),
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C04_FILL_SZ",
        source_path=(
            "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "restart_reconstructed_identity_v1.py"
        ),
        symbol_or_field="BOUND_FILL_SZ / fillSz",
        authority_class="BOUND_LIVE_FILL_IDENTITY",
        runtime_or_offline="OFFLINE",
        raw_or_normalized="RAW",
        unit="UNPROVEN_FILL_DIMENSION",
        sign_semantics="unsigned_fill_magnitude_not_handoff_sign",
        pos_side_semantics="BOUND_POS_SIDE=net is fill identity not handoff pos",
        instrument_binding="BOUND_INSTID",
        account_mode_binding="UNPROVEN",
        position_mode_binding="net_bound_for_fill_identity_only",
        producer="LIVE_FILL_OBSERVED identity bind",
        consumers="LIVE_POSITION_RECONCILED predicate; offline placeholder",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason=(
            "fillSz is bound Live fill identity. FILL_IS_NOT_POSITION_PROOF. "
            "Handoff required field is pos, not fillSz. Sign must not be derived "
            "from fillSz. Numeric equality with venue pos under "
            "LIVE_POSITION_RECONCILED is that field only."
        ),
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C05_ACCUMULATED_FILLS",
        source_path="OKX fill / order history accFillSz; fillSz sum",
        symbol_or_field="accFillSz / summed fillSz",
        authority_class="VENUE_OR_POST_HOC_ARITHMETIC",
        runtime_or_offline="OFFLINE",
        raw_or_normalized="NORMALIZED",
        unit="UNPROVEN",
        sign_semantics="UNPROVEN",
        pos_side_semantics="UNPROVEN",
        instrument_binding="UNPROVEN",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="post-hoc fill accumulation",
        consumers="NONE_AS_HANDOFF",
        contemporaneous_at_handoff="false",
        peak_trade_owned="false",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason=(
            "Accumulated fills are still fill quantity. Post-hoc arithmetic is "
            "POST_HOC_DERIVATION. Retroactive synthesis is forbidden."
        ),
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C06_OKX_POSITION_GET_POS",
        source_path=(
            "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "position_reconciled_predicate_v1.py"
        ),
        symbol_or_field="GET /api/v5/account/positions pos",
        authority_class="VENUE_GET_ACCOUNTING_PATH",
        runtime_or_offline="RUNTIME",
        raw_or_normalized="RAW",
        unit="UNPROVEN_AS_HANDOFF_POS_UNIT",
        sign_semantics="UNPROVEN_AS_HANDOFF_SIGN; venue net-mode pos is not bound",
        pos_side_semantics="venue posSide is not handoff pos",
        instrument_binding="venue instId row; must equal BOUND_INSTID for reconciled",
        account_mode_binding="UNPROVEN_FOR_HANDOFF",
        position_mode_binding="UNPROVEN_FOR_HANDOFF",
        producer="LIVE_POSITION_RECONCILED GET",
        consumers="LIVE_POSITION_RECONCILED; LIVE_ACCOUNTING_RECONSTRUCTED",
        contemporaneous_at_handoff="false",
        peak_trade_owned="false",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason=(
            "Token name pos in a venue response is not Peak_Trade handoff pos. "
            "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF. Using GET pos would "
            "violate HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET and "
            "HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH. GET timing is "
            "post-fill accounting, not Peak_Trade-owned pre-restart capture. "
            "Zero/missing/empty distinctions belong to LIVE_POSITION_RECONCILED, "
            "not this field. POS_UNIT remains UNPROVEN even if venue documents "
            "contract count; that documentation is not Peak_Trade handoff authority."
        ),
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C07_ACCOUNTING_POSITION",
        source_path=(
            "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "accounting_reconstructed_adjudication_v1.py"
        ),
        symbol_or_field="LIVE_ACCOUNTING_RECONSTRUCTED position",
        authority_class="PEAK_TRADE_ACCOUNTING",
        runtime_or_offline="OFFLINE",
        raw_or_normalized="NORMALIZED",
        unit="UNPROVEN",
        sign_semantics="UNPROVEN",
        pos_side_semantics="UNPROVEN",
        instrument_binding="BOUND_INSTID via accounting identity",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="LIVE_ACCOUNTING_RECONSTRUCTED",
        consumers="restart predecessor only",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason="ACCOUNTING_ONLY_IS_NOT_RESTART. Accounting is predecessor, not handoff pos.",
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C08_PRODUCTIVE_PORTFOLIO_POSITION",
        source_path="src/portfolio/ / productive portfolio surfaces",
        symbol_or_field="portfolio position",
        authority_class="PRODUCTIVE_PORTFOLIO",
        runtime_or_offline="RUNTIME",
        raw_or_normalized="NORMALIZED",
        unit="UNPROVEN",
        sign_semantics="UNPROVEN",
        pos_side_semantics="UNPROVEN",
        instrument_binding="UNPROVEN",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="portfolio",
        consumers="NONE_AS_HANDOFF",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason=(
            "Productive portfolio position is not the §11.14 Live canary handoff "
            "pos producer and is not identity-bound contemporaneous pre-restart capture."
        ),
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C09_EXECUTION_LEDGER_DDO",
        source_path="src/learning/deterministic_decision_outcome_v0/",
        symbol_or_field="DDO / execution ledger outcome",
        authority_class="DDO",
        runtime_or_offline="RUNTIME",
        raw_or_normalized="NORMALIZED",
        unit="UNPROVEN",
        sign_semantics="UNPROVEN",
        pos_side_semantics="UNPROVEN",
        instrument_binding="UNPROVEN",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="deterministic_decision_outcome",
        consumers="A1 durability surfaces",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason=(
            "DDO/execution-ledger outcomes are not identity-bound Live canary "
            "handoff pos. Forbidden owner reuse includes DDO storage owner."
        ),
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C10_LIVE_CANARY_RETURN_PAYLOAD",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
        ),
        symbol_or_field="_entry_submit_returned_payload_v1",
        authority_class="CANARY_ACK_RETURN",
        runtime_or_offline="RUNTIME",
        raw_or_normalized="RAW",
        unit="ABSENT_POS_FIELD",
        sign_semantics="ABSENT",
        pos_side_semantics="ABSENT",
        instrument_binding="plan_instId_not_ack_field",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="canary ACK return payload",
        consumers="LIVE_SUBMIT_ACK_OBSERVED",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason=(
            "Fresh re-adjudication vs PR #6317 UNPROVEN: ACK allowlist proves pos "
            "is omitted. Partial ACK identity plus plan sz is not handoff pos. A "
            "future payload field would be a new producer, not this existing one."
        ),
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C11_A1_WAL",
        source_path="src/learning/mutation_critical_control_state_storage_v1/",
        symbol_or_field="MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER",
        authority_class="A1_WAL",
        runtime_or_offline="RUNTIME",
        raw_or_normalized="NORMALIZED",
        unit="UNPROVEN",
        sign_semantics="UNPROVEN",
        pos_side_semantics="UNPROVEN",
        instrument_binding="UNPROVEN",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="A1 WAL",
        consumers="A1 admission/supervisor (inactive for this field)",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason="A1_WAL_AS_LIVE_HANDOFF_ALLOWED=false. A1 WAL is not Live identity-bound pre-restart handoff.",
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C12_FILEGATE",
        source_path="FILEGATE_KILL_SWITCH",
        symbol_or_field="filegate kill-switch",
        authority_class="KILL_SWITCH",
        runtime_or_offline="RUNTIME",
        raw_or_normalized="RAW",
        unit="NOT_A_QUANTITY",
        sign_semantics="NOT_A_QUANTITY",
        pos_side_semantics="NOT_A_QUANTITY",
        instrument_binding="NONE",
        account_mode_binding="NONE",
        position_mode_binding="NONE",
        producer="FILEGATE",
        consumers="kill-switch",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason="FILEGATE is a kill-switch, not a quantity producer. Forbidden owner reuse.",
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C13_CAP72_SIDESTATE",
        source_path="Cap-7.2 SideState persist",
        symbol_or_field="SideState",
        authority_class="CAP_72_SIDESTATE_PERSIST",
        runtime_or_offline="RUNTIME",
        raw_or_normalized="NORMALIZED",
        unit="UNPROVEN",
        sign_semantics="UNPROVEN",
        pos_side_semantics="side_state_not_handoff_pos",
        instrument_binding="UNPROVEN",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="Cap-7.2 SideState",
        consumers="Cap 7.2 lifecycle",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason="Cap-7.2 SideState is not this Live canary handoff pos producer. Forbidden owner reuse.",
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C14_TESTNET_DURABLE_STATE",
        source_path="evidence/ops/section_11_12_testnet_restart_proven_v1/",
        symbol_or_field="testnet restart durable_state",
        authority_class="TESTNET_CAMPAIGN_DURABLE_STATE",
        runtime_or_offline="OFFLINE",
        raw_or_normalized="NORMALIZED",
        unit="UNPROVEN",
        sign_semantics="UNPROVEN",
        pos_side_semantics="UNPROVEN",
        instrument_binding="TESTNET_INSTID_NOT_THIS_LIVE_IDENTITY",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="TESTNET_RESTART_PROVEN",
        consumers="historical Testnet restart field",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason="TESTNET_RESTART_PROVEN is not this Live field. No Testnet result may satisfy a Live evidence field.",
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C15_EVIDENCE_PACK_VALUES",
        source_path="evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/",
        symbol_or_field="pack literals / POS_SEMANTICS_ADJUDICATION.json",
        authority_class="EVIDENCE_PACK",
        runtime_or_offline="OFFLINE",
        raw_or_normalized="NORMALIZED",
        unit="UNPROVEN",
        sign_semantics="UNPROVEN",
        pos_side_semantics="UNPROVEN",
        instrument_binding="historical identity citations",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="evidence packs",
        consumers="offline adjudication",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason="NO_RECLASSIFICATION_OF_EVIDENCE_PACK_AS_CONTROL_HANDOFF. Pack values are not a contemporaneous producer.",
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C16_OFFLINE_CODEC_PLACEHOLDER",
        source_path=(
            "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "restart_reconstructed_handoff_offline_codec_v1.py"
        ),
        symbol_or_field="codec input pos",
        authority_class="OFFLINE_CODEC",
        runtime_or_offline="OFFLINE",
        raw_or_normalized="NORMALIZED",
        unit="CONSUMED_NOT_PRODUCED",
        sign_semantics="CONSUMED_NOT_PRODUCED",
        pos_side_semantics="CONSUMED_NOT_PRODUCED",
        instrument_binding="codec instId input",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="NONE; codec is a consumer",
        consumers="offline restart validators",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason="Offline codec consumes pos. It does not produce contemporaneous handoff pos.",
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C17_P08_HISTORICAL_CAPTURED_POS",
        source_path="evidence/ops/section_11_13_5_p08_* / bound P08 closed pack",
        symbol_or_field="historical captured pos=1",
        authority_class="HISTORICAL_P08",
        runtime_or_offline="OFFLINE",
        raw_or_normalized="RAW",
        unit="UNPROVEN",
        sign_semantics="UNPROVEN",
        pos_side_semantics="UNPROVEN",
        instrument_binding="other_window_not_this_handoff",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="P08 historical capture",
        consumers="P08 closeout",
        contemporaneous_at_handoff="false",
        peak_trade_owned="UNPROVEN",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason=(
            "P08 historical captured pos belongs to another window and another field. "
            "It is not contemporaneous §11.14 Live pre-restart handoff pos for the "
            "bound canary identity. Retroactive reuse is forbidden."
        ),
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C18_EXECUTION_LEDGER_POSITION_MODEL",
        source_path="src/execution/ledger/models.py",
        symbol_or_field="Position",
        authority_class="EXECUTION_LEDGER_MODEL",
        runtime_or_offline="RUNTIME",
        raw_or_normalized="NORMALIZED",
        unit="UNPROVEN",
        sign_semantics="UNPROVEN",
        pos_side_semantics="UNPROVEN",
        instrument_binding="UNPROVEN",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="execution ledger Position model",
        consumers="execution ledger",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason=(
            "Execution ledger Position is not the §11.14 Live canary handoff pos "
            "producer. This slice does not mutate src/execution/**."
        ),
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C19_OWNER_BIND_FILLSZ_PLACEHOLDER",
        source_path=(
            "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
            "restart_reconstructed_owner_bind_execute_v1.py"
        ),
        symbol_or_field="offline placeholder pos=BOUND_FILL_SZ",
        authority_class="OFFLINE_PLACEHOLDER",
        runtime_or_offline="OFFLINE",
        raw_or_normalized="SYNTHETIC",
        unit="COPIED_FILL_SZ_NOT_POS_UNIT",
        sign_semantics="COPIED_FROM_FILL_SZ_FORBIDDEN",
        pos_side_semantics="BOUND_POS_SIDE copied as identity not pos meaning",
        instrument_binding="BOUND_INSTID",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="owner-bind offline placeholder",
        consumers="offline codec tests",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason=(
            "Offline placeholder copies fillSz into pos. Forbidden as productive "
            "handoff producer. No sign derivation from fillSz. No retro synthesis."
        ),
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C20_ABSENT_DURABLE_LIVE_WRITER",
        source_path="NONE",
        symbol_or_field="SECTION_11_14_LIVE_DURABLE_STATE_WRITER",
        authority_class="ABSENT",
        runtime_or_offline="NONE",
        raw_or_normalized="ABSENT",
        unit="ABSENT",
        sign_semantics="ABSENT",
        pos_side_semantics="ABSENT",
        instrument_binding="ABSENT",
        account_mode_binding="ABSENT",
        position_mode_binding="ABSENT",
        producer="NONE",
        consumers="NONE",
        contemporaneous_at_handoff="false",
        peak_trade_owned="false",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason="No Live canary durable_state writer exists. Absence is not a producer.",
        disposition=_REJECTED,
    ),
    _candidate(
        candidate_id="C21_SIMULATED_EXECUTION_POSITION",
        source_path="src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/",
        symbol_or_field="SimulatedExecutionPort position",
        authority_class="SIMULATED_EXECUTION",
        runtime_or_offline="RUNTIME",
        raw_or_normalized="NORMALIZED",
        unit="UNPROVEN",
        sign_semantics="UNPROVEN",
        pos_side_semantics="UNPROVEN",
        instrument_binding="UNPROVEN",
        account_mode_binding="UNPROVEN",
        position_mode_binding="UNPROVEN",
        producer="simulated execution",
        consumers="internal simulated economics",
        contemporaneous_at_handoff="false",
        peak_trade_owned="true",
        canonically_bound=False,
        acceptable_for_handoff_pos="false",
        rejection_reason="No Testnet, fixture or simulated result may satisfy a Live evidence field.",
        disposition=_REJECTED,
    ),
)


def bind_okx_pos_versus_handoff_pos_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_OKX_POS_VERSUS_HANDOFF_POS_V1",
        "TOKEN_NAME_IDENTITY_IS_NOT_SEMANTIC_IDENTITY": True,
        "VENUE_RESPONSE_FIELD": {
            "endpoint": "GET /api/v5/account/positions",
            "schema_field": ADMISSIBLE_POS_FIELD,
            "source_kind": POSITION_RECONCILED_SOURCE_KIND,
            "used_by": "LIVE_POSITION_RECONCILED",
            "net_vs_long_short": "UNPROVEN_AS_HANDOFF_SEMANTICS",
            "sign_behavior": "UNPROVEN_AS_HANDOFF_SIGN",
            "unit": "UNPROVEN_AS_HANDOFF_POS_UNIT",
            "contract_vs_base": "UNPROVEN_AS_HANDOFF_DIMENSION",
            "instrument_dependency": "row instId must equal BOUND_INSTID for reconciled",
            "posSide_behavior": "BOUND_POS_SIDE=net is fill/reconcile identity not handoff pos",
            "account_position_mode_assumptions": "UNPROVEN_FOR_HANDOFF",
            "zero_missing_empty_distinguishable": (
                "LIVE_POSITION_RECONCILED fail-closed distinctions are not this field"
            ),
            "get_timing_contemporaneous_pre_restart": False,
            "violates_handoff_distinct_from_accounting_venue_get": True,
            "HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET": HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET,
            "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF": (
                VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF
            ),
        },
        "PEAK_TRADE_HANDOFF_SEMANTICS": {
            "required_fields": list(REQUIRED_HANDOFF_FIELDS),
            "POS_SEMANTICS": POS_SEMANTICS,
            "POS_CANONICAL_MEANING": POS_CANONICAL_MEANING,
            "POS_UNIT": POS_UNIT,
            "unique_meaning_from_existing_authority": False,
        },
        "CONTEMPORANEOUS_PRODUCER_OF_HANDOFF_SEMANTICS": "NONE",
    }


def bind_pos_unit_proof_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_POS_UNIT_PROOF_V1",
        "POS_UNIT": POS_UNIT,
        "dimensions_examined": (
            "contracts",
            "venue_contract_count",
            "base_asset_quantity",
            "quote_value",
            "normalized_strategy_quantity",
            "signed_contracts",
            "unsigned_magnitude_plus_posSide",
        ),
        "order_plan_qty_unit_is_not_handoff_pos_unit": True,
        "p10_target_position_qty_unit": "UNPROVEN",
        "numeric_one_across_plan_fill_and_venue_pos_does_not_bind_kind": True,
        "conversion_required": "UNPROVEN",
        "conversion_inputs": "UNPROVEN",
        "contract_metadata_stand": "UNPROVEN",
        "rounding_rules": "UNPROVEN",
        "freshness_requirements": "UNPROVEN",
        "canonical_conversion_exists_for_handoff_pos": False,
        "new_conversion_implemented": False,
        "POS_UNIT_CAN_BE_BOUND_FROM_EXISTING_AUTHORITY": False,
    }


def bind_pos_sign_proof_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_POS_SIGN_PROOF_V1",
        "POS_SIGN_SEMANTICS": POS_SIGN_SEMANTICS,
        "POS_POS_SIDE_RELATION": POS_POS_SIDE_RELATION,
        "sign_in_pos": "UNPROVEN",
        "posSide": BOUND_POS_SIDE,
        "posSide_is_not_pos": True,
        "net_mode": "BOUND_FOR_FILL_IDENTITY_ONLY",
        "long_short_mode": "UNPROVEN_FOR_HANDOFF",
        "order_side": "NOT_HANDOFF_POS",
        "fill_direction": "NOT_HANDOFF_POS",
        "signed_required": "UNPROVEN",
        "unsigned_magnitude_plus_posSide_required": "UNPROVEN",
        "derivation_from_fillSz_forbidden": True,
        "BOUND_FILL_SZ": BOUND_FILL_SZ,
    }


def bind_pos_temporal_provenance_v1() -> dict[str, Any]:
    rows = []
    for row in _CANDIDATES:
        rows.append(
            {
                "CANDIDATE_ID": row["CANDIDATE_ID"],
                "CONTEMPORANEOUS_AT_HANDOFF": row["CONTEMPORANEOUS_AT_HANDOFF"],
                "PEAK_TRADE_OWNED": row["PEAK_TRADE_OWNED"],
                "CAN_EMIT_WITHOUT_RETRO_SYNTHESIS": False,
                "PROVENANCE_PRESENT": False,
                "ATTEMPT_SESSION_IDENTITY_PRESENT": False,
                "BOUND_INSTID_PRESENT": row["INSTRUMENT_BINDING"] == "BOUND_INSTID",
                "SEMANTICALLY_CORRECT_IS_NOT_AUTOMATICALLY_ACCEPTABLE_PRODUCER": True,
                "REJECTION_REASON": row["REJECTION_REASON"],
            }
        )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_POS_TEMPORAL_PROVENANCE_V1",
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
        "NO_TIMESTAMP_BACKFILL": NO_TIMESTAMP_BACKFILL,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
        "ACCEPTABLE_CONTEMPORANEOUS_PRODUCER_COUNT": 0,
        "rows": rows,
    }


def bind_required_new_producer_contract_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_REQUIRED_NEW_POS_PRODUCER_CONTRACT_V1",
        "IMPLEMENTATION_AUTHORIZED": False,
        "REQUIRED_NEW_PRODUCER_RESPONSIBILITY": (
            "Emit the required Peak_Trade-owned contemporaneous pre-restart "
            "handoff pos string for the bound Live identity after Owner binds "
            "unique meaning, unit, and sign. Contract only; no implementation."
        ),
        "REQUIRED_NEW_PRODUCER_INPUTS": (
            "UNPROVEN until POS_CANONICAL_MEANING/POS_UNIT/POS_SIGN_SEMANTICS "
            "are Owner-bound. Forbidden inputs remain venue GET pos, accounting, "
            "fillSz, submitted sz, ACK payload, codec placeholders, FILEGATE, "
            "historical P08, and fillSz-copied placeholders."
        ),
        "REQUIRED_NEW_PRODUCER_OUTPUT": (
            "required nonempty Decimal-parseable pos string; must Decimal-equal "
            "bound Live identity once produced; instId must equal BOUND_INSTID"
        ),
        "REQUIRED_NEW_PRODUCER_UNIT": "UNPROVEN; must be explicit when Owner-bound",
        "REQUIRED_NEW_PRODUCER_PROVENANCE": (
            "Peak_Trade-owned contemporaneous capture with attempt/session identity "
            "and bound instId; no timestamp backfill; no synthetic pre-restart provenance"
        ),
        "REQUIRED_NEW_PRODUCER_TIMING": (
            "PRE_RESTART_CONTEMPORANEOUS; exact moment UNPROVEN while meaning UNPROVEN"
        ),
        "REQUIRED_NEW_PRODUCER_FORBIDDEN_DERIVATIONS": (
            "A_submitted_sz",
            "B_signed_submitted_sz",
            "C_acknowledged_sz",
            "D_cumulative_fill",
            "E_fresh_venue_GET",
            "F_accounting_position",
            "G_reconciliation_result",
            "H_order_lifecycle_state",
            "I_preexisting_position_plus_fills",
            "J_canary_ACK_return_payload_field",
            "FILEGATE",
            "offline_codec_placeholder",
            "historical_P08_captured_pos",
            "owner_bind_fillSz_placeholder",
        ),
        "BOUND_INSTID": BOUND_INSTID,
        "ACK_ALLOWLIST": list(ACK_ALLOWLIST),
        "ACK_OMITS_POS": ACK_OMITS_POS,
        "ACK_OMITS_POS_SIDE": ACK_OMITS_POS_SIDE,
        "ACK_OMITS_INST_ID": ACK_OMITS_INST_ID,
        "ACK_OMITS_SZ": ACK_OMITS_SZ,
    }


def bind_pos_downstream_effect_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_POS_SEMANTICS_DOWNSTREAM_EFFECT_V1",
        "POS_SEMANTICS": POS_SEMANTICS,
        "COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED": False,
        "OWNER_MINT_CAN_NOW_BE_ADJUDICATED": False,
        "WRITER_BIND_CAN_NOW_BE_ADJUDICATED": False,
        "READER_BIND_CAN_NOW_BE_ADJUDICATED": False,
        "LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED": False,
        "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_SEAM": "UNPROVEN",
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN": False,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
        "FIRST_OWNER_PRODUCTIVELY_BOUND": False,
        "STORAGE_OWNER_MINTED": False,
        "WRITER_BOUND": False,
        "READER_BOUND": False,
        "CAPTURE_SEAM_BOUND": False,
        "PRODUCTIVE_BINDING_PRESENT": False,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "DEPENDENT_MUTATION_ALLOWED": False,
        "PRODUCTIVE_HOST_BINDING": False,
        "ADMISSION_TRUE": False,
        "SUPERVISOR_ACTIVATED": False,
        "IMPLEMENTATION_AUTHORIZED": False,
        "REASON": ("POS_SEMANTICS remains UNPROVEN. Downstream promotion stays fail-closed."),
    }


def bind_pos_semantics_canonical_binding_v1() -> dict[str, Any]:
    if HISTORICAL_POS_SEMANTICS != "UNPROVEN":
        raise Section1114OfflineSurfaceError("HISTORICAL_POS_SEMANTICS_DRIFT")
    if POS_SEMANTICS_CAN_BE_BOUND_FROM_EXISTING_AUTHORITY is True:
        raise Section1114OfflineSurfaceError(
            "POS_SEMANTICS_MUST_REMAIN_UNBOUND_FROM_EXISTING_AUTHORITY"
        )
    if POS_SEMANTICS != "UNPROVEN":
        raise Section1114OfflineSurfaceError("POS_SEMANTICS_MUST_REMAIN_UNPROVEN")
    if NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED is not True:
        raise Section1114OfflineSurfaceError("NEW_POS_PRODUCER_MUST_REMAIN_REQUIRED")
    if ACK_OMITS_POS is not True:
        raise Section1114OfflineSurfaceError("ACK_ALLOWLIST_MUST_OMIT_POS")
    acceptable = [row for row in _CANDIDATES if row["ACCEPTABLE_FOR_HANDOFF_POS_BOOL"] is True]
    rejected = [row for row in _CANDIDATES if row["DISPOSITION"] == _REJECTED]
    unproven = [row for row in _CANDIDATES if row["DISPOSITION"] == _UNPROVEN]
    accepted_ids = [row["CANDIDATE_ID"] for row in acceptable]
    rejected_with_reason = [
        {
            "CANDIDATE_ID": row["CANDIDATE_ID"],
            "SOURCE_PATH": row["SOURCE_PATH"],
            "SYMBOL_OR_FIELD": row["SYMBOL_OR_FIELD"],
            "REJECTION_REASON": row["REJECTION_REASON"],
        }
        for row in rejected
    ]
    unproven_ids = [row["CANDIDATE_ID"] for row in unproven]
    if acceptable:
        raise Section1114OfflineSurfaceError("POS_ACCEPTABLE_PRODUCER_MUST_REMAIN_ZERO")
    if unproven:
        raise Section1114OfflineSurfaceError("POS_UNPROVEN_PRODUCER_MUST_REMAIN_EMPTY")
    if len(rejected) != len(_CANDIDATES):
        raise Section1114OfflineSurfaceError("POS_CANDIDATE_DISPOSITION_DRIFT")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_POS_SEMANTICS_CANONICAL_BINDING_V1",
        "POS_SEMANTICS": POS_SEMANTICS,
        "POS_SEMANTICS_STATUS": POS_SEMANTICS_STATUS,
        "POS_CANONICAL_MEANING": POS_CANONICAL_MEANING,
        "POS_UNIT": POS_UNIT,
        "POS_SIGN_SEMANTICS": POS_SIGN_SEMANTICS,
        "POS_POS_SIDE_RELATION": POS_POS_SIDE_RELATION,
        "POS_INSTRUMENT_BINDING": POS_INSTRUMENT_BINDING,
        "POS_POSITION_MODE_BINDING": POS_POSITION_MODE_BINDING,
        "POS_ACCOUNT_MODE_BINDING": POS_ACCOUNT_MODE_BINDING,
        "POS_ACCEPTABLE_PRODUCER_COUNT": 0,
        "POS_ACCEPTABLE_PRODUCERS": accepted_ids,
        "POS_REJECTED_PRODUCER_COUNT": len(rejected),
        "POS_REJECTED_PRODUCERS_WITH_REASON": rejected_with_reason,
        "POS_UNPROVEN_PRODUCER_COUNT": 0,
        "POS_UNPROVEN_PRODUCERS": unproven_ids,
        "POS_SEMANTICS_CAN_BE_BOUND_FROM_EXISTING_AUTHORITY": (
            POS_SEMANTICS_CAN_BE_BOUND_FROM_EXISTING_AUTHORITY
        ),
        "NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED": (NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED),
        "PROVEN_CONSTRAINTS_NOT_UNIQUE_MEANING": list(_PROVEN_CONSTRAINTS),
        "UNPROVEN_MEANING_AXES": list(_UNPROVEN_MEANING_AXES),
        "TOKEN_NAME_IDENTITY_IS_NOT_SEMANTIC_IDENTITY": True,
        "NO_UNIQUE_CANONICAL_MEANING_FROM_AUTHORITY": True,
        "NORMALIZATION_FROM_PLAUSIBILITY_FORBIDDEN": True,
        "PR_6317_REJECTIONS_NOT_BLINDLY_REUSED": True,
        "LIVE_CANARY_RETURN_PAYLOAD_FRESH_DISPOSITION": _REJECTED,
        "LIVE_CANARY_RETURN_PAYLOAD_PRIOR_DISPOSITION": _UNPROVEN,
        "ACK_ALLOWLIST": list(ACK_ALLOWLIST),
        "ACK_OMITS_POS": ACK_OMITS_POS,
        "ACCOUNTING_ONLY_IS_NOT_RESTART": ACCOUNTING_ONLY_IS_NOT_RESTART,
        "A1_WAL_AS_LIVE_HANDOFF_ALLOWED": A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
        "NO_RECLASSIFICATION_OF_EVIDENCE_PACK_AS_CONTROL_HANDOFF": (
            NO_RECLASSIFICATION_OF_EVIDENCE_PACK_AS_CONTROL_HANDOFF
        ),
        "HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET": HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET,
        "candidates": list(_CANDIDATES),
        "okx_versus_handoff": bind_okx_pos_versus_handoff_pos_v1(),
        "unit_proof": bind_pos_unit_proof_v1(),
        "sign_proof": bind_pos_sign_proof_v1(),
        "temporal_provenance": bind_pos_temporal_provenance_v1(),
        "required_new_producer_contract": bind_required_new_producer_contract_v1(),
        "downstream_effect": bind_pos_downstream_effect_v1(),
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "IMPLEMENTATION_AUTHORIZED": False,
    }
