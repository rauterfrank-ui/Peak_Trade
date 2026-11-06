"""Fail-closed canonical ladder-order enforcement."""

from __future__ import annotations

from typing import Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LADDER_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)


def assert_ladder_order_v1(values: Mapping[str, bool]) -> None:
    """Reject any true later stage while an earlier required stage is not true.

    Canonical §11.14 lists a strict arrow chain and does not authorize skipping.
    Interpretation is labeled: no extra edges are invented beyond that chain.
    """

    unknown = set(values) - set(LADDER_FIELDS)
    if unknown:
        raise Section1114OfflineSurfaceError("UNKNOWN_LADDER_FIELD:" + ",".join(sorted(unknown)))
    predecessor_unproven = False
    for field_name in LADDER_FIELDS:
        claimed = bool(values.get(field_name) is True)
        if predecessor_unproven and claimed:
            raise Section1114OfflineSurfaceError(f"LADDER_ORDER_VIOLATION:{field_name}")
        if not claimed:
            predecessor_unproven = True
