"""Owner-level §11.14 Live handoff `pos` producer semantics and contract.

This slice binds unique meaning, unit, and sign for a new Peak_Trade-owned
contemporaneous producer at contract level only. It does not implement a
writer, mint an owner, GET, POST, or execute a restart. Historical
`POS_SEMANTICS=UNPROVEN` records are not reinterpreted.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_TD_MODE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    ONE_CONTRACT_EQUALS_ONE_SUI,
    ORDER_PLAN_QTY_DOMAIN,
    ORDER_PLAN_QTY_UNIT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.xperp_310404_economic_baseline_contract_v1 import (
    live_eea_xperp_310404_economic_baseline_contract_v1,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.contract_v1 import (
    NUMBER_OF_CONTRACTS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    ACCOUNTING_ONLY_IS_NOT_RESTART,
    A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
    LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION,
    NO_RECLASSIFICATION_OF_EVIDENCE_PACK_AS_CONTROL_HANDOFF,
    NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
    NO_TIMESTAMP_BACKFILL,
    RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
    HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
    VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_SIDE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET,
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_predicate_v1 import (
    RESTART_IDENTITY_EQUATION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_semantics_canonical_binding_v1 import (
    NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED as HISTORICAL_NEW_PRODUCER_REQUIRED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_semantics_canonical_binding_v1 import (
    POS_SEMANTICS as HISTORICAL_POS_SEMANTICS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_semantics_canonical_binding_v1 import (
    bind_pos_semantics_canonical_binding_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_required_field_contract_v1 import (
    POS_SEMANTICS as HISTORICAL_REQUIRED_FIELD_POS_SEMANTICS,
)

_REJECTED = "POS_MEANING_REJECTED"
_SELECTED = "POS_MEANING_SELECTED"
_UNPROVEN = "POS_MEANING_UNPROVEN"

POS_SEMANTICS = "PROVEN"
POS_SEMANTICS_STATUS = "PROVEN"
POS_SEMANTICS_CANONICALLY_BOUND = True
POS_CANONICAL_MEANING = (
    "Peak_Trade-owned contemporaneous resulting/current position quantity "
    "for BOUND_INSTID as of handoff-commit immediately before restart. This "
    "quantity is the restart-control-state `pos` component of "
    "{clOrdId, ordId, instId, posSide, pos}. It is not venue accounting, "
    "not intended submit quantity, not acknowledged quantity, not fillSz, "
    "not cumulative fills, not economic notional, and not strategy state."
)
POS_UNIT = "VENUE_CONTRACT_COUNT_NUMBER_OF_CONTRACTS"
POS_SIGN_SEMANTICS = "UNSIGNED_MAGNITUDE"
POS_POS_SIDE_RELATION = (
    "MANDATORY_IDENTITY_FIELD_NET_MODE_TOKEN_NOT_DIRECTION; "
    "posSide=net does not encode long/short; direction is out of scope for "
    "this single field"
)
POS_POSITION_MODE_BINDING = (
    "ACCOUNT_CONFIG_POSMODE_RAW_net_mode; bound Live fill/position identity "
    "uses posSide=net; net_mode is not long/short mode"
)
POS_ACCOUNT_MODE_BINDING = (
    "IRRELEVANT_FOR_HANDOFF_POS_QUANTITY; tdMode=cross is margin mode and "
    "does not change the quantity domain or unsigned-magnitude sign model"
)
POS_TEMPORAL_MEANING = (
    "HANDOFF_COMMIT_IMMEDIATELY_BEFORE_RESTART_DESCRIBING_RESULTING_POSITION_"
    "AFTER_BOUND_FILL_AND_BEFORE_RESTART"
)
POS_IDENTITY_BINDING = (
    "Must Decimal-equal bound Live submit/fill/position identity once "
    f"produced; clOrdId={BOUND_CLORDID}; ordId={BOUND_ORDID}; "
    f"instId={BOUND_INSTID}; posSide={BOUND_POS_SIDE}"
)
POS_INSTRUMENT_BINDING = f"MUST_EQUAL_BOUND_INSTID={BOUND_INSTID}"
POS_DECIMAL_RULE = (
    "nonempty Decimal-parseable string; equality is Decimal equality, not "
    "string identity; scientific notation is not required; negative values "
    "are forbidden under UNSIGNED_MAGNITUDE"
)
POS_ZERO_RULE = (
    "zero means silent reinitialization of restart-control-state; zero is "
    "not missing/empty; zero is forbidden when bound fillSz is nonzero"
)
POS_NONZERO_RULE = f"nonzero required when BOUND_FILL_SZ={BOUND_FILL_SZ} is nonzero"
SELECTED_SEMANTIC_ID = (
    "S05_PEAK_TRADE_OWNED_RESULTING_CURRENT_POSITION_QTY_VENUE_CONTRACT_COUNT_UNSIGNED"
)
NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED = True
PRODUCER_ID = "SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_V1"
HANDOFF_SCHEMA_VERSION = "section_11_14_live_durable_pre_restart_handoff.v1"
PROPOSED_NEXT_SLICE = "SECTION_11_14_LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_PROOF_V1"
WHAT_SECTION_11_14_RESTART_RECONSTRUCTS = (
    "Peak_Trade durable pre-restart control-state identity for the bound "
    "Live canary attempt, distinct from venue GET / accounting, from which "
    "offline reconstruction proceeds without re-submit and without silent "
    "reinitialization. Not exchange/accounting state, not execution intent, "
    "not filled execution state as fillSz, not economic notional, and not "
    "strategy state."
)
FORBIDDEN_DERIVATIONS: tuple[str, ...] = (
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
    "K_fillSz_copy",
    "L_order_side_plus_fillSz_as_signed_pos",
    "FILEGATE",
    "offline_codec_placeholder",
    "historical_P08_captured_pos",
    "owner_bind_fillSz_placeholder",
    "A1_WAL",
    "evidence_pack_value",
    "timestamp_backfill",
    "synthetic_pre_restart_provenance",
)


def _meaning_candidate(
    *,
    semantic_id: str,
    meaning: str,
    source_of_truth: str,
    temporal_meaning: str,
    unit: str,
    sign_model: str,
    pos_side_relation: str,
    position_mode_relation: str,
    account_mode_relation: str,
    handoff_suitable: str,
    rejection_reason: str,
    disposition: str,
) -> dict[str, Any]:
    if handoff_suitable not in {"true", "false", "unproven"}:
        raise Section1114OfflineSurfaceError("HANDOFF_SUITABLE_TOKEN_INVALID")
    return {
        "SEMANTIC_ID": semantic_id,
        "MEANING": meaning,
        "SOURCE_OF_TRUTH": source_of_truth,
        "TEMPORAL_MEANING": temporal_meaning,
        "UNIT": unit,
        "SIGN_MODEL": sign_model,
        "POS_SIDE_RELATION": pos_side_relation,
        "POSITION_MODE_RELATION": position_mode_relation,
        "ACCOUNT_MODE_RELATION": account_mode_relation,
        "HANDOFF_SUITABLE": handoff_suitable,
        "HANDOFF_SUITABLE_BOOL": handoff_suitable == "true",
        "REJECTION_REASON": rejection_reason,
        "DISPOSITION": disposition,
    }


_MEANING_CANDIDATES: tuple[dict[str, Any], ...] = (
    _meaning_candidate(
        semantic_id="S01_INTENDED_SUBMITTED_POSITION_QUANTITY",
        meaning="Intended submitted position/order quantity from the plan or Place Order sz.",
        source_of_truth="order_plan_v1 sz / POST trade/order sz",
        temporal_meaning="pre-submit / post-submit intended",
        unit="VENUE_CONTRACT_COUNT_AS_ORDER_PLAN_NOT_HANDOFF_POS",
        sign_model="unsigned_plan_magnitude",
        pos_side_relation="posSide omitted on observed net-mode plan",
        position_mode_relation="net_mode plan omits posSide",
        account_mode_relation="IRRELEVANT",
        handoff_suitable="false",
        rejection_reason=(
            "Intended submit quantity is not resulting position. "
            "FILL_IS_NOT_POSITION_PROOF. Submitted sz is not handoff pos."
        ),
        disposition=_REJECTED,
    ),
    _meaning_candidate(
        semantic_id="S02_ACKNOWLEDGED_QUANTITY",
        meaning="Quantity acknowledged on the synchronous Place Order ACK.",
        source_of_truth="ACK data[] allowlist",
        temporal_meaning="ACK-received",
        unit="ABSENT",
        sign_model="ABSENT",
        pos_side_relation="ABSENT",
        position_mode_relation="ABSENT",
        account_mode_relation="ABSENT",
        handoff_suitable="false",
        rejection_reason=(
            "ACK allowlist is sCode,sMsg,ordId,clOrdId,tag. sz, pos, posSide, "
            "and instId are omitted. Acknowledged size is absent, not unproven."
        ),
        disposition=_REJECTED,
    ),
    _meaning_candidate(
        semantic_id="S03_EXECUTION_FILL_QUANTITY",
        meaning="Single-fill execution quantity fillSz.",
        source_of_truth="BOUND_FILL_SZ / LIVE_FILL_OBSERVED",
        temporal_meaning="fill-observed",
        unit="UNPROVEN_AS_HANDOFF_POS_UNIT",
        sign_model="unsigned_fill_magnitude",
        pos_side_relation="BOUND_POS_SIDE=net is fill identity not handoff pos",
        position_mode_relation="net_bound_for_fill_identity_only",
        account_mode_relation="IRRELEVANT",
        handoff_suitable="false",
        rejection_reason=(
            "FILL_IS_NOT_POSITION_PROOF. Handoff required field is pos, not "
            "fillSz. Sign must not be derived from fillSz. Numeric equality "
            "with bound identity is a later constraint on a produced pos, "
            "not permission to copy fillSz."
        ),
        disposition=_REJECTED,
    ),
    _meaning_candidate(
        semantic_id="S04_CUMULATIVE_FILLED_QUANTITY",
        meaning="Accumulated fills accFillSz or summed fillSz.",
        source_of_truth="venue fill/order history or post-hoc arithmetic",
        temporal_meaning="order-terminal reconstructed after the fact",
        unit="UNPROVEN",
        sign_model="UNPROVEN",
        pos_side_relation="UNPROVEN",
        position_mode_relation="UNPROVEN",
        account_mode_relation="UNPROVEN",
        handoff_suitable="false",
        rejection_reason=(
            "Accumulated fills remain fill quantity. Post-hoc arithmetic is "
            "POST_HOC_DERIVATION. Retroactive synthesis is forbidden."
        ),
        disposition=_REJECTED,
    ),
    _meaning_candidate(
        semantic_id=SELECTED_SEMANTIC_ID,
        meaning=POS_CANONICAL_MEANING,
        source_of_truth=(
            "Owner-bound Peak_Trade contemporaneous producer "
            f"{PRODUCER_ID}; not venue GET and not fillSz copy"
        ),
        temporal_meaning=POS_TEMPORAL_MEANING,
        unit=POS_UNIT,
        sign_model=POS_SIGN_SEMANTICS,
        pos_side_relation=POS_POS_SIDE_RELATION,
        position_mode_relation=POS_POSITION_MODE_BINDING,
        account_mode_relation=POS_ACCOUNT_MODE_BINDING,
        handoff_suitable="true",
        rejection_reason="",
        disposition=_SELECTED,
    ),
    _meaning_candidate(
        semantic_id="S06_VENUE_RAW_ACCOUNTING_POSITION_QUANTITY",
        meaning="Venue GET /account/positions pos row for the bound instrument.",
        source_of_truth="GET /api/v5/account/positions",
        temporal_meaning="position-reconciled / accounting observation",
        unit="NUMBER_OF_CONTRACTS_AS_VENUE_ACCOUNTING_NOT_HANDOFF",
        sign_model="venue_net_mode_signed_or_unbound_as_handoff",
        pos_side_relation="venue posSide is not handoff pos",
        position_mode_relation="UNPROVEN_FOR_HANDOFF",
        account_mode_relation="UNPROVEN_FOR_HANDOFF",
        handoff_suitable="false",
        rejection_reason=(
            "Token name pos is not Peak_Trade handoff pos. "
            "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF. "
            "HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET. "
            "ACCOUNTING_ONLY_IS_NOT_RESTART."
        ),
        disposition=_REJECTED,
    ),
    _meaning_candidate(
        semantic_id="S07_PEAK_TRADE_NORMALIZED_POSITION_QUANTITY",
        meaning="A Peak_Trade-normalized strategy or portfolio position quantity.",
        source_of_truth="productive portfolio / execution-ledger Position / STEP-29P",
        temporal_meaning="UNPROVEN",
        unit="UNPROVEN",
        sign_model="UNPROVEN",
        pos_side_relation="UNPROVEN",
        position_mode_relation="UNPROVEN",
        account_mode_relation="UNPROVEN",
        handoff_suitable="false",
        rejection_reason=(
            "No Peak_Trade-normalized strategy quantity is identity-bound to "
            "this Live canary handoff. STEP-29P is orthogonal. Productive "
            "portfolio and execution-ledger Position are not this producer."
        ),
        disposition=_REJECTED,
    ),
    _meaning_candidate(
        semantic_id="S08_ECONOMIC_EXPOSURE_QUANTITY",
        meaning="Notional, quote, or economic exposure quantity.",
        source_of_truth="qty * ctVal * markPx / quote notional",
        temporal_meaning="UNPROVEN",
        unit="NOTIONAL_OR_QUOTE_NOT_HANDOFF_POS",
        sign_model="UNPROVEN",
        pos_side_relation="UNPROVEN",
        position_mode_relation="UNPROVEN",
        account_mode_relation="UNPROVEN",
        handoff_suitable="false",
        rejection_reason=(
            "LIVE_RESTART_RECONSTRUCTED reconstructs control-state identity, "
            "not economic notional. Instrument notional_formula is not the "
            "handoff pos field. ONE_CONTRACT_EQUALS_ONE_SUI remains false."
        ),
        disposition=_REJECTED,
    ),
    _meaning_candidate(
        semantic_id="S09_RESTART_CONTROL_STATE_QUANTITY_AS_SEPARATE_KIND",
        meaning=(
            "A control-state token that is not a position quantity, stored in the field named pos."
        ),
        source_of_truth="none; would overload the identity equation",
        temporal_meaning="immediately-before-restart",
        unit="NOT_A_POSITION_QUANTITY",
        sign_model="NOT_A_POSITION_QUANTITY",
        pos_side_relation="UNPROVEN",
        position_mode_relation="UNPROVEN",
        account_mode_relation="UNPROVEN",
        handoff_suitable="false",
        rejection_reason=(
            "The restart identity equation requires Decimal pos equal to the "
            "bound Live submit/fill/position identity. A non-quantity control "
            "token would overload `pos`. Restart-control-state is the ROLE of "
            "S05, not a second quantity in the same field. No schema split is "
            "required while direction remains out of scope."
        ),
        disposition=_REJECTED,
    ),
)


def bind_what_restart_reconstructs_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_WHAT_RESTART_RECONSTRUCTS_V1",
        "WHAT_SECTION_11_14_RESTART_RECONSTRUCTS": WHAT_SECTION_11_14_RESTART_RECONSTRUCTS,
        "LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION": (
            LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION
        ),
        "RESTART_IDENTITY_EQUATION": RESTART_IDENTITY_EQUATION,
        "REQUIRED_HANDOFF_FIELDS": list(REQUIRED_HANDOFF_FIELDS),
        "RECONSTRUCTS_EXCHANGE_ACCOUNTING_STATE": False,
        "RECONSTRUCTS_PEAK_TRADE_CONTROL_STATE": True,
        "RECONSTRUCTS_EXECUTION_INTENT": False,
        "RECONSTRUCTS_FILLED_EXECUTION_STATE_AS_FILLSZ": False,
        "RECONSTRUCTS_ECONOMIC_POSITION_NOTIONAL": False,
        "RECONSTRUCTS_STRATEGY_STATE": False,
        "SINGLE_FIELD_POS_OVERLOAD_REQUIRED": False,
        "SCHEMA_SPLIT_REQUIRED_NOW": False,
        "DIRECTION_OUT_OF_SCOPE_FOR_THIS_FIELD": True,
        "FLATTEN_SIGN_IS_LATER_SCHEMA_IF_NEEDED": True,
        "ACCOUNTING_ONLY_IS_NOT_RESTART": ACCOUNTING_ONLY_IS_NOT_RESTART,
        "HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET": HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET,
    }


def bind_pos_unit_adjudication_v1() -> dict[str, Any]:
    instrument = live_eea_xperp_310404_economic_baseline_contract_v1()
    if ONE_CONTRACT_EQUALS_ONE_SUI is not False:
        raise Section1114OfflineSurfaceError("ONE_CONTRACT_EQUALS_ONE_SUI_MUST_REMAIN_FALSE")
    if ORDER_PLAN_QTY_UNIT == POS_UNIT:
        raise Section1114OfflineSurfaceError("ORDER_PLAN_QTY_UNIT_MUST_NOT_ALIAS_POS_UNIT")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_POS_UNIT_PRODUCER_CONTRACT_V1",
        "POS_UNIT": POS_UNIT,
        "QUANTITY_DOMAIN": "VENUE_CONTRACT_COUNT",
        "OFFICIAL_UNIT_PHRASE": "number of contracts",
        "P11_NUMBER_OF_CONTRACTS_IS_INSTRUMENT_DOMAIN_NOT_HANDOFF_PRODUCER": True,
        "P11_NUMBER_OF_CONTRACTS": NUMBER_OF_CONTRACTS,
        "ORDER_PLAN_QTY_UNIT": ORDER_PLAN_QTY_UNIT,
        "ORDER_PLAN_QTY_DOMAIN": ORDER_PLAN_QTY_DOMAIN,
        "ORDER_PLAN_QTY_UNIT_IS_NOT_HANDOFF_POS_UNIT": True,
        "TARGET_POSITION_QTY_UNIT_IS_NOT_ALIASED": True,
        "ONE_CONTRACT_EQUALS_ONE_SUI": ONE_CONTRACT_EQUALS_ONE_SUI,
        "NOT_BASE_ASSET_AMOUNT": True,
        "NOT_QUOTE_CURRENCY_AMOUNT": True,
        "NOT_NOTIONAL": True,
        "NOT_NORMALIZED_STRATEGY_QTY": True,
        "NUMERIC_ONE_DOES_NOT_BIND_KIND": True,
        "CTVAL_IS_NOT_CONVERSION_FACTOR": True,
        "CONVERSION_REQUIRED": False,
        "CONVERSION_FORMULA": "NONE_IDENTITY_DOMAIN",
        "CONVERSION_BELONGS": "NOWHERE_NO_CONVERSION",
        "instrument_identity": instrument["instrument_identity"],
        "ctVal": instrument["ctVal"],
        "ctValCcy": instrument["ctValCcy"],
        "ctMult": instrument["ctMult"],
        "ctType": instrument["ctType"],
        "lotSz": instrument["lotSz"],
        "minSz": instrument["minSz"],
        "notional_formula": instrument["notional_formula"],
        "lotSz_and_minSz_are_admissibility_not_unit_source": True,
        "new_conversion_implemented": False,
    }


def bind_pos_sign_adjudication_v1() -> dict[str, Any]:
    if BOUND_POS_SIDE != "net":
        raise Section1114OfflineSurfaceError("BOUND_POS_SIDE_MUST_REMAIN_NET")
    if BOUND_SIDE != "buy":
        raise Section1114OfflineSurfaceError("BOUND_SIDE_MUST_REMAIN_BUY")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_POS_SIGN_PRODUCER_CONTRACT_V1",
        "POS_SIGN_SEMANTICS": POS_SIGN_SEMANTICS,
        "POS_POS_SIDE_RELATION": POS_POS_SIDE_RELATION,
        "POS_POSITION_MODE_BINDING": POS_POSITION_MODE_BINDING,
        "MODEL_A_SIGNED_QUANTITY_POSSIDE_REDUNDANT": False,
        "MODEL_B_UNSIGNED_MAGNITUDE_PLUS_MANDATORY_POSSIDE": True,
        "MODEL_B_POSSIDE_DOES_NOT_ENCODE_DIRECTION_IN_NET_MODE": True,
        "MODEL_C_OTHER": False,
        "posSide": BOUND_POS_SIDE,
        "posSide_is_not_pos": True,
        "posSide_net_DOES_NOT_CONVEY_LONG": True,
        "posSide_net_DOES_NOT_CONVEY_SHORT": True,
        "posSide_net_CONVEYS_NET_MODE_IDENTITY_TOKEN": True,
        "long_short_mode": "NOT_CURRENT_PRODUCTIVE_MODE",
        "order_side": BOUND_SIDE,
        "order_side_is_not_handoff_pos_sign": True,
        "fill_direction_from_fillSz_forbidden": True,
        "derivation_from_fillSz_forbidden": True,
        "derivation_from_order_side_plus_fill_forbidden": True,
        "BOUND_FILL_SZ": BOUND_FILL_SZ,
        "NEGATIVE_VALUES_FORBIDDEN": True,
        "FLATTEN_ECONOMIC_SIGN_OUT_OF_SCOPE": True,
        "SCHEMA_SPLIT_DEFERRED_UNTIL_DIRECTION_REQUIRED": True,
    }


def bind_pos_account_mode_adjudication_v1() -> dict[str, Any]:
    if DEFAULT_TD_MODE != "cross":
        raise Section1114OfflineSurfaceError("DEFAULT_TD_MODE_MUST_REMAIN_CROSS")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_POS_ACCOUNT_MODE_PRODUCER_CONTRACT_V1",
        "POS_ACCOUNT_MODE_BINDING": POS_ACCOUNT_MODE_BINDING,
        "tdMode": DEFAULT_TD_MODE,
        "acctLv": "UNBOUND_AND_IRRELEVANT_TO_POS_QUANTITY",
        "mgnMode_does_not_change_quantity_domain": True,
        "cross_versus_isolated_does_not_change_unsigned_magnitude_model": True,
        "IRRELEVANT_PROVEN": True,
    }


def bind_new_pos_producer_contract_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_NEW_POS_PRODUCER_CONTRACT_V1",
        "PRODUCER_ID": PRODUCER_ID,
        "PRODUCER_RESPONSIBILITY": (
            "Emit the Peak_Trade-owned contemporaneous pre-restart handoff pos "
            "string for the bound Live identity under the selected S05 "
            "meaning, unit, and unsigned-magnitude sign model. Contract only."
        ),
        "PRODUCER_INPUTS": (
            "Peak_Trade-owned contemporaneous resulting/current position "
            "quantity at handoff-commit whose quantity domain is "
            "VENUE_CONTRACT_COUNT; plus bound identity "
            f"(instId={BOUND_INSTID}, clOrdId={BOUND_CLORDID}, "
            f"ordId={BOUND_ORDID}, posSide={BOUND_POS_SIDE}). Exact capture "
            "seam remains UNPROVEN and is not this producer implementation. "
            "Forbidden sources are excluded."
        ),
        "PRODUCER_OUTPUT": (
            "required nonempty Decimal-parseable unsigned pos string in "
            f"{POS_UNIT}; must Decimal-equal bound Live identity once "
            f"produced; instId must equal {BOUND_INSTID}"
        ),
        "PRODUCER_UNIT": POS_UNIT,
        "PRODUCER_SIGN_MODEL": POS_SIGN_SEMANTICS,
        "PRODUCER_TEMPORAL_POINT": POS_TEMPORAL_MEANING,
        "PRODUCER_IDENTITY_BINDING": POS_IDENTITY_BINDING,
        "PRODUCER_INSTID_BINDING": POS_INSTRUMENT_BINDING,
        "PRODUCER_ATTEMPT_BINDING": (
            "attempt/session specific; records are not durable owner identity"
        ),
        "PRODUCER_SESSION_BINDING": "bound Live canary session identity required",
        "PRODUCER_ORDER_BINDING": f"clOrdId={BOUND_CLORDID}; ordId={BOUND_ORDID}",
        "PRODUCER_FILL_BINDING": (
            "must be after the bound fill identity exists; must not copy "
            f"fillSz={BOUND_FILL_SZ}; must Decimal-equal bound identity once produced"
        ),
        "PRODUCER_PROVENANCE": (
            "Peak_Trade-owned contemporaneous capture with attempt/session "
            "identity and bound instId; no timestamp backfill; no synthetic "
            "pre-restart provenance"
        ),
        "PRODUCER_DECIMAL_RULE": POS_DECIMAL_RULE,
        "PRODUCER_ZERO_RULE": POS_ZERO_RULE,
        "PRODUCER_FAILURE_POLICY": (
            "fail-closed: emit nothing rather than a forbidden derivation; "
            "do not substitute venue GET pos, fillSz, submitted sz, ACK, "
            "accounting, codec placeholders, FILEGATE, historical P08, A1 WAL, "
            "or evidence-pack values; do not invent sign from fillSz or order side"
        ),
        "PRODUCER_FORBIDDEN_DERIVATIONS": list(FORBIDDEN_DERIVATIONS),
        "PEAK_TRADE_OWNED": True,
        "CONTEMPORANEOUS": True,
        "PRE_RESTART": True,
        "IDENTITY_BOUND": True,
        "BOUND_TO_BOUND_INSTID": True,
        "DETERMINISTIC_FROM_AUTHORIZED_INPUTS": True,
        "FAIL_CLOSED": True,
        "NON_RETROACTIVE": True,
        "IMPLEMENTATION_AUTHORIZED": False,
        "NEW_PRODUCER_IMPLEMENTED": False,
        "PRODUCER_CONTRACT_COMPLETE": True,
    }


def bind_handoff_schema_version_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_HANDOFF_SCHEMA_VERSION_V1",
        "SCHEMA_CHANGE_REQUIRED": False,
        "HANDOFF_SCHEMA_VERSION": HANDOFF_SCHEMA_VERSION,
        "REQUIRED_HANDOFF_FIELDS": list(REQUIRED_HANDOFF_FIELDS),
        "POS_FIELD_SEMANTIC_CLARIFICATION_BOUND": True,
        "NEW_FIELDS_ADDED": False,
        "DIRECTION_FIELD_ADDED": False,
        "HISTORICAL_DATA_REINTERPRETATION_ALLOWED": False,
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
        "NO_TIMESTAMP_BACKFILL": NO_TIMESTAMP_BACKFILL,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
        "PRODUCTIVE_MIGRATION_IMPLEMENTED": False,
        "FUTURE_DIRECTION_REQUIRES_V2_FIELD_NOT_POS_OVERLOAD": True,
    }


def bind_pos_downstream_effect_after_producer_contract_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_POS_PRODUCER_CONTRACT_DOWNSTREAM_EFFECT_V1",
        "POS_SEMANTICS": POS_SEMANTICS,
        "POS_SEMANTICS_CANONICALLY_BOUND": POS_SEMANTICS_CANONICALLY_BOUND,
        "NEW_PRODUCER_CONTRACT_DEFINED": True,
        "NEW_PRODUCER_IMPLEMENTED": False,
        "COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED": True,
        "OWNER_MINT_CAN_NOW_BE_ADJUDICATED": False,
        "WRITER_BIND_CAN_NOW_BE_ADJUDICATED": False,
        "READER_BIND_CAN_NOW_BE_ADJUDICATED": False,
        "LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED": False,
        "COMPLETE_CAPTURE_SEAM": "UNPROVEN",
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_SEAM": "UNPROVEN",
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN": False,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
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
        "CAN_NOW_BE_ADJUDICATED_IS_NOT_PROVEN": True,
        "REASON": (
            "POS_SEMANTICS is Owner-bound. Capture seam can now be "
            "adjudicated and remains UNPROVEN. Owner mint, writer, reader, "
            "and restart reconstruction stay fail-closed."
        ),
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "WHY_THIS_IS_EARLIEST": (
            "Architecture DAG SLICE_2 is complete-capture-seam proof. "
            "Owner mint requires POS_SEMANTICS proven AND complete capture "
            "seam proven. Writer/reader and LIVE_RESTART_RECONSTRUCTED "
            "remain later."
        ),
    }


def bind_pos_producer_semantics_and_contract_v1() -> dict[str, Any]:
    if HISTORICAL_POS_SEMANTICS != "UNPROVEN":
        raise Section1114OfflineSurfaceError("HISTORICAL_POS_SEMANTICS_MUST_REMAIN_UNPROVEN")
    if HISTORICAL_REQUIRED_FIELD_POS_SEMANTICS != "UNPROVEN":
        raise Section1114OfflineSurfaceError(
            "HISTORICAL_REQUIRED_FIELD_POS_SEMANTICS_MUST_REMAIN_UNPROVEN"
        )
    if HISTORICAL_NEW_PRODUCER_REQUIRED is not True:
        raise Section1114OfflineSurfaceError("HISTORICAL_NEW_PRODUCER_REQUIRED_DRIFT")
    historical = bind_pos_semantics_canonical_binding_v1()
    if int(historical["POS_ACCEPTABLE_PRODUCER_COUNT"]) != 0:
        raise Section1114OfflineSurfaceError("HISTORICAL_ACCEPTABLE_PRODUCER_MUST_REMAIN_ZERO")
    if POS_SEMANTICS != "PROVEN":
        raise Section1114OfflineSurfaceError("POS_SEMANTICS_MUST_BE_PROVEN")
    if POS_SEMANTICS_CANONICALLY_BOUND is not True:
        raise Section1114OfflineSurfaceError("POS_SEMANTICS_MUST_BE_CANONICALLY_BOUND")
    selected = [row for row in _MEANING_CANDIDATES if row["DISPOSITION"] == _SELECTED]
    rejected = [row for row in _MEANING_CANDIDATES if row["DISPOSITION"] == _REJECTED]
    unproven = [row for row in _MEANING_CANDIDATES if row["DISPOSITION"] == _UNPROVEN]
    if len(selected) != 1:
        raise Section1114OfflineSurfaceError("POS_SELECTED_SEMANTIC_MUST_BE_UNIQUE")
    if selected[0]["SEMANTIC_ID"] != SELECTED_SEMANTIC_ID:
        raise Section1114OfflineSurfaceError("POS_SELECTED_SEMANTIC_ID_DRIFT")
    if unproven:
        raise Section1114OfflineSurfaceError("POS_UNPROVEN_MEANING_MUST_REMAIN_EMPTY")
    if len(selected) + len(rejected) != len(_MEANING_CANDIDATES):
        raise Section1114OfflineSurfaceError("POS_MEANING_DISPOSITION_DRIFT")
    producer = bind_new_pos_producer_contract_v1()
    if producer["PRODUCER_CONTRACT_COMPLETE"] is not True:
        raise Section1114OfflineSurfaceError("PRODUCER_CONTRACT_MUST_BE_COMPLETE")
    if producer["NEW_PRODUCER_IMPLEMENTED"] is not False:
        raise Section1114OfflineSurfaceError("NEW_PRODUCER_MUST_REMAIN_UNIMPLEMENTED")
    if producer["IMPLEMENTATION_AUTHORIZED"] is not False:
        raise Section1114OfflineSurfaceError("IMPLEMENTATION_MUST_REMAIN_UNAUTHORIZED")
    downstream = bind_pos_downstream_effect_after_producer_contract_v1()
    if downstream["COMPLETE_CAPTURE_SEAM"] != "UNPROVEN":
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    if downstream["COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED"] is not True:
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_NOW_BE_ADJUDICABLE")
    if downstream["OWNER_MINT_CAN_NOW_BE_ADJUDICATED"] is True:
        raise Section1114OfflineSurfaceError("OWNER_MINT_MUST_REMAIN_UNADJUDICABLE")
    if downstream["NEW_PRODUCER_IMPLEMENTED"] is True:
        raise Section1114OfflineSurfaceError("NEW_PRODUCER_MUST_REMAIN_UNIMPLEMENTED")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_POS_PRODUCER_SEMANTICS_AND_CONTRACT_V1",
        "POS_SEMANTICS": POS_SEMANTICS,
        "POS_SEMANTICS_STATUS": POS_SEMANTICS_STATUS,
        "POS_SEMANTICS_CANONICALLY_BOUND": POS_SEMANTICS_CANONICALLY_BOUND,
        "POS_CANONICAL_MEANING": POS_CANONICAL_MEANING,
        "POS_UNIT": POS_UNIT,
        "POS_SIGN_SEMANTICS": POS_SIGN_SEMANTICS,
        "POS_POS_SIDE_RELATION": POS_POS_SIDE_RELATION,
        "POS_POSITION_MODE_BINDING": POS_POSITION_MODE_BINDING,
        "POS_ACCOUNT_MODE_BINDING": POS_ACCOUNT_MODE_BINDING,
        "POS_TEMPORAL_MEANING": POS_TEMPORAL_MEANING,
        "POS_IDENTITY_BINDING": POS_IDENTITY_BINDING,
        "POS_INSTRUMENT_BINDING": POS_INSTRUMENT_BINDING,
        "POS_DECIMAL_RULE": POS_DECIMAL_RULE,
        "POS_ZERO_RULE": POS_ZERO_RULE,
        "POS_NONZERO_RULE": POS_NONZERO_RULE,
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "SELECTED_SEMANTIC_UNIQUE": True,
        "REJECTED_SEMANTIC_CANDIDATE_COUNT": len(rejected),
        "UNPROVEN_SEMANTIC_CANDIDATE_COUNT": 0,
        "NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED": True,
        "NEW_PRODUCER_CONTRACT_DEFINED": True,
        "NEW_PRODUCER_IMPLEMENTED": False,
        "TOKEN_NAME_IDENTITY_IS_NOT_SEMANTIC_IDENTITY": True,
        "HISTORICAL_POS_SEMANTICS_REMAINS_UNPROVEN": True,
        "HISTORICAL_POS_SEMANTICS_NOT_REINTERPRETED": True,
        "PRIOR_PRODUCER_REJECTIONS_NOT_OVERTURNED": True,
        "HISTORICAL_ACCEPTABLE_PRODUCER_COUNT": historical["POS_ACCEPTABLE_PRODUCER_COUNT"],
        "A1_WAL_AS_LIVE_HANDOFF_ALLOWED": A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
        "NO_RECLASSIFICATION_OF_EVIDENCE_PACK_AS_CONTROL_HANDOFF": (
            NO_RECLASSIFICATION_OF_EVIDENCE_PACK_AS_CONTROL_HANDOFF
        ),
        "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF": (
            VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF
        ),
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
        "NO_TIMESTAMP_BACKFILL": NO_TIMESTAMP_BACKFILL,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
        "IMPLEMENTATION_AUTHORIZED": False,
        "meaning_candidates": list(_MEANING_CANDIDATES),
        "what_restart_reconstructs": bind_what_restart_reconstructs_v1(),
        "unit_adjudication": bind_pos_unit_adjudication_v1(),
        "sign_adjudication": bind_pos_sign_adjudication_v1(),
        "account_mode_adjudication": bind_pos_account_mode_adjudication_v1(),
        "producer_contract": producer,
        "schema_version": bind_handoff_schema_version_v1(),
        "downstream_effect": downstream,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "PRODUCER_ID": PRODUCER_ID,
        "PRODUCER_CONTRACT_COMPLETE": True,
        "HANDOFF_SCHEMA_VERSION": HANDOFF_SCHEMA_VERSION,
        "SCHEMA_CHANGE_REQUIRED": False,
        "HISTORICAL_DATA_REINTERPRETATION_ALLOWED": False,
    }
