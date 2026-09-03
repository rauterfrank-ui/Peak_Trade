"""First-party query grammars for P08 identifier-recovery GETs.

Builds proven REST queries only. Does not GET, does not claim completeness,
does not invent posId, and does not treat empty as zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.account_positions_query_grammar_v1 import (
    AccountPositionsQueryV1,
    build_account_positions_query_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.category_c_open_algo_pending_observer_v1 import (
    build_category_c_orders_algo_pending_endpoint_v1,
)
from src.ops.section_11_13_5_p08_read_only_closure_v1.constants_v1 import (
    ENDPOINT_ORDERS_HISTORY,
    ENDPOINT_ORDERS_PENDING,
    ENDPOINT_TRADE_FILLS,
    PAGE_LIMIT,
    TARGET_INST_TYPE,
    TARGET_INSTRUMENT_ID,
)


class P08ReadOnlyClosureQueryGrammarError(RuntimeError):
    """Fail-closed first-party query-grammar violation."""


@dataclass(frozen=True)
class IdentifierRecoveryQueryV1:
    """Proven grammar only. Not a completeness certificate and not a GET."""

    endpoint: str
    query: dict[str, str]
    purpose: str
    completeness_proven: bool
    empty_result_is_zero: bool
    is_canonical_p08_authority: bool

    def path_with_query(self) -> str:
        if not self.query:
            return self.endpoint
        return f"{self.endpoint}?{urlencode(self.query)}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "query": dict(self.query),
            "path_with_query": self.path_with_query(),
            "purpose": self.purpose,
            "completeness_proven": self.completeness_proven,
            "empty_result_is_zero": self.empty_result_is_zero,
            "is_canonical_p08_authority": self.is_canonical_p08_authority,
            "THIS_BUILDER_DOES_NOT_GET": True,
        }


def _bound_target(*, inst_type: str, inst_id: str) -> tuple[str, str]:
    inst_type_norm = str(inst_type or "").strip()
    inst_id_norm = str(inst_id or "").strip()
    if not inst_type_norm:
        raise P08ReadOnlyClosureQueryGrammarError("INSTTYPE_REQUIRED")
    if not inst_id_norm:
        raise P08ReadOnlyClosureQueryGrammarError("INSTID_REQUIRED")
    if inst_id_norm != TARGET_INSTRUMENT_ID:
        raise P08ReadOnlyClosureQueryGrammarError("INSTRUMENT_BINDING_MISMATCH")
    if inst_type_norm != TARGET_INST_TYPE:
        raise P08ReadOnlyClosureQueryGrammarError("INST_TYPE_BINDING_MISMATCH")
    return inst_type_norm, inst_id_norm


def build_target_orders_pending_query_v1(
    *,
    inst_type: str = TARGET_INST_TYPE,
    inst_id: str = TARGET_INSTRUMENT_ID,
) -> IdentifierRecoveryQueryV1:
    inst_type_norm, inst_id_norm = _bound_target(inst_type=inst_type, inst_id=inst_id)
    query = {"instType": inst_type_norm, "instId": inst_id_norm}
    return IdentifierRecoveryQueryV1(
        endpoint=ENDPOINT_ORDERS_PENDING,
        query=query,
        purpose="POSID_RECOVERY_FROM_WORKING_ORDERS_NOT_CURRENT_POSITION",
        completeness_proven=False,
        empty_result_is_zero=False,
        is_canonical_p08_authority=False,
    )


def build_target_orders_history_query_v1(
    *,
    inst_type: str = TARGET_INST_TYPE,
    inst_id: str = TARGET_INSTRUMENT_ID,
) -> IdentifierRecoveryQueryV1:
    inst_type_norm, inst_id_norm = _bound_target(inst_type=inst_type, inst_id=inst_id)
    query = {"instType": inst_type_norm, "instId": inst_id_norm, "limit": str(PAGE_LIMIT)}
    return IdentifierRecoveryQueryV1(
        endpoint=ENDPOINT_ORDERS_HISTORY,
        query=query,
        purpose="POSID_RECOVERY_FROM_ORDER_HISTORY_NOT_CURRENT_POSITION",
        completeness_proven=False,
        empty_result_is_zero=False,
        is_canonical_p08_authority=False,
    )


def build_target_fills_query_v1(
    *,
    inst_type: str = TARGET_INST_TYPE,
    inst_id: str = TARGET_INSTRUMENT_ID,
) -> IdentifierRecoveryQueryV1:
    inst_type_norm, inst_id_norm = _bound_target(inst_type=inst_type, inst_id=inst_id)
    query = {"instType": inst_type_norm, "instId": inst_id_norm, "limit": str(PAGE_LIMIT)}
    return IdentifierRecoveryQueryV1(
        endpoint=ENDPOINT_TRADE_FILLS,
        query=query,
        purpose="POSID_RECOVERY_FROM_FILLS_NOT_CURRENT_POSITION",
        completeness_proven=False,
        empty_result_is_zero=False,
        is_canonical_p08_authority=False,
    )


def build_target_algo_pending_path_v1(*, ord_type: str) -> str:
    ord_type_norm = str(ord_type or "").strip()
    if not ord_type_norm:
        raise P08ReadOnlyClosureQueryGrammarError("ORDTYPE_REQUIRED_FOR_ALGO_PENDING")
    return build_category_c_orders_algo_pending_endpoint_v1(
        ord_type=ord_type_norm,
        instrument_id=TARGET_INSTRUMENT_ID,
        inst_type=TARGET_INST_TYPE,
        limit=PAGE_LIMIT,
    )


def build_proven_posid_positions_query_v1(*, pos_id: str) -> AccountPositionsQueryV1:
    pos_id_norm = str(pos_id or "").strip()
    if not pos_id_norm:
        raise P08ReadOnlyClosureQueryGrammarError("POSID_REQUIRED_AND_MUST_BE_INDEPENDENTLY_PROVEN")
    built = build_account_positions_query_v1(pos_id=pos_id_norm)
    if not built.pos_id_filter_present:
        raise P08ReadOnlyClosureQueryGrammarError("POSID_FILTER_MISSING")
    if built.inst_id_filter_present:
        raise P08ReadOnlyClosureQueryGrammarError("POSID_PATH_MUST_NOT_ADD_INSTID")
    if "instType" in built.query:
        raise P08ReadOnlyClosureQueryGrammarError("POSID_PATH_MUST_NOT_ADD_INSTTYPE")
    return built
