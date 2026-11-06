"""Canonical LIVE_PRIVATE_READ_ONLY_PROVEN predicate.

Binds the third §11.14 Live proof-claim field. A single reachability GET is
not this field. §11.13.2 historical proof is not this field. Does not POST.
Does not promote LIVE_ORDER_PLAN_OBSERVED or later fields.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    FORBIDDEN_LIVE_SOURCE_KINDS,
    LIVE_PRIVATE_READ_ONLY_PROVEN_CANONICAL_DEFINITION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)

PRIVATE_READ_ONLY_CONSTITUENTS: tuple[str, ...] = (
    "PREDECESSOR_LIVE_EXECUTION_CODE_EXISTS",
    "PREDECESSOR_LIVE_EXECUTION_PATH_REACHABLE",
    "CURRENT_PRIVATE_GET_CONFIG_HTTP_200_OKX_0",
    "CURRENT_PRIVATE_GET_BALANCE_HTTP_200_OKX_0",
    "BOTH_METHODS_GET",
    "NO_POST",
    "PARSEABLE_ACCOUNT_CONFIG_DATA",
    "PARSEABLE_ACCOUNT_BALANCE_DATA",
    "NO_REDIRECT",
)
PRIVATE_READ_ONLY_CONSTITUENT_COUNT = 9

ADMISSIBILITY_PREDICATE = (
    "LIVE_PRIVATE_READ_ONLY_PROVEN is true iff every bound constituent is "
    "proven on current origin/main: LIVE_EXECUTION_CODE_EXISTS and "
    "LIVE_EXECUTION_PATH_REACHABLE are already true; current authenticated "
    "private GET /api/v5/account/config and GET /api/v5/account/balance each "
    "return HTTP 200 and OKX code 0 with parseable account data; both methods "
    "are GET; no POST; no redirect. A single reachability GET, historical "
    "§11.13.2 proof, credential presence alone, fixture/testnet/sim sources, "
    "and §11.13.2 TRADE=false owner attestation are each insufficient. True "
    "does not promote LIVE_ORDER_PLAN_OBSERVED, submit authorization, POST, "
    "or any later ladder field."
)


def evaluate_private_read_only_conjunction_v1(
    *,
    constituent_values: Mapping[str, bool | None],
    source_kind: str = "GOVERNED_CURRENT_PRIVATE_GET",
) -> dict[str, Any]:
    kind = str(source_kind or "").strip().upper()
    if kind in FORBIDDEN_LIVE_SOURCE_KINDS:
        raise Section1114OfflineSurfaceError(f"FORBIDDEN_LIVE_SOURCE:{kind}")
    missing = [name for name in PRIVATE_READ_ONLY_CONSTITUENTS if name not in constituent_values]
    if missing:
        raise Section1114OfflineSurfaceError(
            "PRIVATE_READ_ONLY_CONSTITUENT_MISSING:" + ",".join(missing)
        )
    false_required: list[str] = []
    unobserved_required: list[str] = []
    for name in PRIVATE_READ_ONLY_CONSTITUENTS:
        value = constituent_values[name]
        if value is None:
            unobserved_required.append(name)
        elif value is not True:
            false_required.append(name)
    if false_required:
        adjudication = "FALSE_REQUIRED_CONSTITUENT"
        claim = False
        reason = "FALSE_REQUIRED_CONSTITUENT:" + ",".join(false_required)
    elif unobserved_required:
        adjudication = "FALSE_UNOBSERVED_REQUIRED_CONSTITUENT"
        claim = False
        reason = "UNOBSERVED_REQUIRED_CONSTITUENT:" + ",".join(unobserved_required)
    else:
        adjudication = "TRUE_CURRENT_PRIVATE_READ_ONLY"
        claim = True
        reason = "FULL_CONJUNCTION_PROVEN"
    return {
        "canonical_definition": LIVE_PRIVATE_READ_ONLY_PROVEN_CANONICAL_DEFINITION,
        "admissibility_predicate": ADMISSIBILITY_PREDICATE,
        "claim_value": claim,
        "adjudication": adjudication,
        "reason": reason,
        "constituents": {
            name: bool(constituent_values[name] is True) for name in PRIVATE_READ_ONLY_CONSTITUENTS
        },
        "false_required": false_required,
        "unobserved_required": unobserved_required,
        "later_ladder_fields_promoted": False,
        "submit_authorization_inferred": False,
        "source_kind": kind,
    }
