"""First-party query grammars reused from Z2CH / Z2V / Z2CE.

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
from src.ops.section_11_13_5_p08_distinct_first_party_evidence_v1.constants_v1 import (
    ENDPOINT_ACCOUNT_POSITION_RISK,
    ENDPOINT_ACCOUNT_POSITIONS_HISTORY,
    HISTORY_PAGE_LIMIT,
    TARGET_INST_TYPE,
    TARGET_INSTRUMENT_ID,
)


class P08DistinctFirstPartyQueryGrammarError(RuntimeError):
    """Fail-closed first-party query-grammar violation."""


@dataclass(frozen=True)
class DistinctFirstPartyQueryV1:
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


def build_target_positions_history_query_v1(
    *,
    inst_type: str = TARGET_INST_TYPE,
    inst_id: str = TARGET_INSTRUMENT_ID,
    after: str | None = None,
) -> DistinctFirstPartyQueryV1:
    """Z2CH proven grammar: instType=FUTURES&instId=<target>."""
    inst_type_norm = str(inst_type or "").strip()
    inst_id_norm = str(inst_id or "").strip()
    if not inst_type_norm:
        raise P08DistinctFirstPartyQueryGrammarError("INSTTYPE_REQUIRED_FOR_HISTORY_TARGET")
    if not inst_id_norm:
        raise P08DistinctFirstPartyQueryGrammarError("INSTID_REQUIRED_FOR_HISTORY_TARGET")
    query = {"instType": inst_type_norm, "instId": inst_id_norm, "limit": str(HISTORY_PAGE_LIMIT)}
    after_norm = str(after or "").strip()
    if after_norm:
        query["after"] = after_norm
    if "instFamily" in query:
        raise P08DistinctFirstPartyQueryGrammarError("INSTFAMILY_FORBIDDEN")
    return DistinctFirstPartyQueryV1(
        endpoint=ENDPOINT_ACCOUNT_POSITIONS_HISTORY,
        query=query,
        purpose="POSID_RECOVERY_AND_THREE_MONTH_EVER_HELD_WINDOW",
        completeness_proven=False,
        empty_result_is_zero=False,
        is_canonical_p08_authority=False,
    )


def build_typed_positions_history_query_v1(
    *,
    inst_type: str = TARGET_INST_TYPE,
) -> DistinctFirstPartyQueryV1:
    """Subset of Z2CH proven params: instType only, no instId."""
    inst_type_norm = str(inst_type or "").strip()
    if not inst_type_norm:
        raise P08DistinctFirstPartyQueryGrammarError("INSTTYPE_REQUIRED_FOR_TYPED_HISTORY")
    query = {"instType": inst_type_norm, "limit": str(HISTORY_PAGE_LIMIT)}
    return DistinctFirstPartyQueryV1(
        endpoint=ENDPOINT_ACCOUNT_POSITIONS_HISTORY,
        query=query,
        purpose="DISCRIMINATE_TARGET_FILTER_INCOMPLETENESS_VS_TYPED_EMPTY",
        completeness_proven=False,
        empty_result_is_zero=False,
        is_canonical_p08_authority=False,
    )


def build_account_position_risk_query_v1(
    *,
    inst_type: str = TARGET_INST_TYPE,
) -> DistinctFirstPartyQueryV1:
    """Z2V proven grammar: instType=FUTURES."""
    inst_type_norm = str(inst_type or "").strip()
    if not inst_type_norm:
        raise P08DistinctFirstPartyQueryGrammarError("INSTTYPE_REQUIRED_FOR_POSITION_RISK")
    query = {"instType": inst_type_norm}
    return DistinctFirstPartyQueryV1(
        endpoint=ENDPOINT_ACCOUNT_POSITION_RISK,
        query=query,
        purpose="INDEPENDENT_POSDATA_CROSS_CHECK_NOT_CANONICAL",
        completeness_proven=False,
        empty_result_is_zero=False,
        is_canonical_p08_authority=False,
    )


def build_proven_posid_positions_query_v1(*, pos_id: str) -> AccountPositionsQueryV1:
    """Reuse Z2CE positions grammar. Caller must supply independently proven posId."""
    pos_id_norm = str(pos_id or "").strip()
    if not pos_id_norm:
        raise P08DistinctFirstPartyQueryGrammarError(
            "POSID_REQUIRED_AND_MUST_BE_INDEPENDENTLY_PROVEN"
        )
    built = build_account_positions_query_v1(pos_id=pos_id_norm)
    if not built.pos_id_filter_present:
        raise P08DistinctFirstPartyQueryGrammarError("POSID_FILTER_MISSING")
    if built.inst_id_filter_present:
        raise P08DistinctFirstPartyQueryGrammarError("POSID_PATH_MUST_NOT_ADD_INSTID")
    if "instType" in built.query:
        raise P08DistinctFirstPartyQueryGrammarError("POSID_PATH_MUST_NOT_ADD_INSTTYPE")
    return built
