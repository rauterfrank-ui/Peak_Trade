"""Offline GET /api/v5/account/positions query grammar from §11.13.5.Z2CE.

Builds the proven REST query. Does not GET, does not claim completeness,
and does not treat filtered or unfiltered empty as zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

POSITION_STATE_ENDPOINT = "/api/v5/account/positions"
INSTTYPE_QUERY_PARAM = "OPTIONAL"
INSTID_QUERY_PARAM = "OPTIONAL_MAX_10_COMMA_SEPARATED"
POSID_QUERY_PARAM = "OPTIONAL_MAX_20_COMMA_SEPARATED"
INSTFAMILY_IS_NOT_A_POSITIONS_REST_QUERY_PARAM = True
MAX_INSTID_VALUES = 10
MAX_POSID_VALUES = 20
UNFILTERED_EMPTY_IS_NOT_ZERO = True
FILTERED_EMPTY_IS_NOT_ZERO = True
HTTP_OK_DOES_NOT_PROVE_COMPLETENESS = True
QUERY_COMPLETENESS_PROVEN = False
THIS_BUILDER_DOES_NOT_GET = True
THIS_BUILDER_DOES_NOT_PROVE_CURRENT_SUI_ZERO = True


class LiveCanaryAccountPositionsQueryGrammarError(RuntimeError):
    """Fail-closed positions query-grammar violation."""


@dataclass(frozen=True)
class AccountPositionsQueryV1:
    """Proven grammar only. Not a completeness certificate and not a GET."""

    endpoint: str
    query: dict[str, str]
    inst_id_filter_present: bool
    pos_id_filter_present: bool
    completeness_proven: bool
    empty_result_is_zero: bool

    def path_with_query(self) -> str:
        if not self.query:
            return self.endpoint
        return f"{self.endpoint}?{urlencode(self.query)}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "query": dict(self.query),
            "path_with_query": self.path_with_query(),
            "inst_id_filter_present": self.inst_id_filter_present,
            "pos_id_filter_present": self.pos_id_filter_present,
            "completeness_proven": self.completeness_proven,
            "empty_result_is_zero": self.empty_result_is_zero,
            "HTTP_OK_DOES_NOT_PROVE_COMPLETENESS": HTTP_OK_DOES_NOT_PROVE_COMPLETENESS,
            "THIS_BUILDER_DOES_NOT_GET": THIS_BUILDER_DOES_NOT_GET,
        }


def _csv_values(raw: str | None, *, max_values: int, label: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    text = str(raw).strip()
    if not text:
        return ()
    parts = tuple(item.strip() for item in text.split(",") if item.strip())
    if len(parts) > max_values:
        raise LiveCanaryAccountPositionsQueryGrammarError(f"{label}_COUNT_EXCEEDS_MAX")
    return parts


def build_account_positions_query_v1(
    *,
    inst_type: str | None = None,
    inst_id: str | None = None,
    pos_id: str | None = None,
) -> AccountPositionsQueryV1:
    """Build the Z2CE REST query. Never issues a network call."""
    query: dict[str, str] = {}
    inst_type_norm = str(inst_type or "").strip()
    if inst_type_norm:
        query["instType"] = inst_type_norm
    inst_ids = _csv_values(inst_id, max_values=MAX_INSTID_VALUES, label="INSTID")
    if inst_ids:
        query["instId"] = ",".join(inst_ids)
    pos_ids = _csv_values(pos_id, max_values=MAX_POSID_VALUES, label="POSID")
    if pos_ids:
        query["posId"] = ",".join(pos_ids)
    if "instFamily" in query:
        raise LiveCanaryAccountPositionsQueryGrammarError("INSTFAMILY_FORBIDDEN")
    return AccountPositionsQueryV1(
        endpoint=POSITION_STATE_ENDPOINT,
        query=query,
        inst_id_filter_present=bool(inst_ids),
        pos_id_filter_present=bool(pos_ids),
        completeness_proven=False,
        empty_result_is_zero=False,
    )
