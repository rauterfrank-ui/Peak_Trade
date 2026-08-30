"""Master V2 structural eligibility V1 (PERP_SWAP_ONLY, NO_ASSET_EXCLUDE).

OWNER_POLICY_VERSION=V1
HISTORICAL_CLAIM=false

Reuses Cap 2.1 discovery parsing and mark-presence inventory only. Does not
import Cap 2.1 BTC exclusion, FUTURES eligibility, or a linear-only contract policy.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Optional, Sequence

from src.ops.master_v2_minimal_selector_v1.constants_v1 import (
    ACTIVE_TRADING_STATE,
    EMPTY_EXPIRY_TOKENS,
    INSTRUMENT_TYPE_FUTURES,
    INSTRUMENT_TYPE_SPOT,
    INSTRUMENT_TYPE_SWAP,
    VENUE,
    VENUE_ALIASES,
)
from src.ops.master_v2_minimal_selector_v1.models_v1 import StructuralEligibilityRowV1
from src.ops.master_v2_minimal_selector_v1.reason_codes_v1 import StructuralExclusionCodeV1

_ASSET_FROM_INST = re.compile(r"^([A-Z0-9]+)-([A-Z0-9]+)(?:-([A-Z0-9]+))?$")


def normalize_venue_v1(venue: str) -> str:
    raw = str(venue or "").strip()
    if raw in VENUE_ALIASES:
        return VENUE
    return raw


def is_okx_eea_venue_v1(venue: str) -> bool:
    return normalize_venue_v1(venue) == VENUE


def expiry_is_empty_v1(raw: Any) -> bool:
    if raw is None:
        return True
    token = str(raw).strip()
    return token in EMPTY_EXPIRY_TOKENS


def _parse_positive_decimal(raw: Any) -> tuple[Optional[str], Optional[str]]:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None, "missing"
    if isinstance(raw, float):
        return None, "invalid"
    try:
        value = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError, ArithmeticError):
        return None, "invalid"
    if value <= 0:
        return None, "invalid"
    normalized = format(value.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized, None


def _extract_base_quote(inst: Mapping[str, Any], inst_id: str) -> tuple[str, str]:
    base = str(inst.get("baseCcy") or "").strip().upper()
    quote = str(inst.get("quoteCcy") or "").strip().upper()
    if not base or not quote:
        match = _ASSET_FROM_INST.fullmatch(inst_id.upper())
        if match:
            if not base:
                base = match.group(1)
            if not quote:
                quote = match.group(2)
    if not base:
        uly = str(inst.get("uly") or "").strip().upper()
        if "-" in uly:
            base = uly.split("-", 1)[0]
    return base, quote


def classify_structural_eligibility_v1(
    inst: Mapping[str, Any],
    *,
    venue: str,
    mark_price_supported_ids: frozenset[str],
) -> StructuralEligibilityRowV1:
    """Classify one census row. Candidate order is not used."""
    reasons: list[str] = []
    inst_id = str(inst.get("instId") or "").strip()
    if not inst_id:
        reasons.append(StructuralExclusionCodeV1.MISSING_NATIVE_INST_ID.value)

    row_venue = str(inst.get("venue") or venue or "").strip()
    if not is_okx_eea_venue_v1(row_venue):
        reasons.append(StructuralExclusionCodeV1.VENUE_NOT_OKX_EEA.value)

    inst_type = str(inst.get("instType") or "").strip().upper()
    exp_empty = expiry_is_empty_v1(inst.get("expTime"))

    if inst_type == INSTRUMENT_TYPE_SPOT:
        reasons.append(StructuralExclusionCodeV1.SPOT_INSTRUMENT.value)
    elif inst_type == INSTRUMENT_TYPE_FUTURES:
        reasons.append(StructuralExclusionCodeV1.DATED_FUTURES_INSTRUMENT.value)
    elif inst_type == INSTRUMENT_TYPE_SWAP:
        if not exp_empty:
            reasons.append(StructuralExclusionCodeV1.SWAP_WITH_EXPIRY.value)
    else:
        reasons.append(StructuralExclusionCodeV1.UNSUPPORTED_INSTRUMENT_TYPE.value)

    base, quote = _extract_base_quote(inst, inst_id)
    settle = str(inst.get("settleCcy") or "").strip().upper()
    ct_val_ccy = str(inst.get("ctValCcy") or "").strip().upper()
    ct_type = str(inst.get("ctType") or "").strip()

    missing_meta = False
    invalid_meta = False
    if not base or not quote or not settle or not ct_val_ccy or not ct_type:
        missing_meta = True

    for field in ("tickSz", "lotSz", "minSz", "ctVal"):
        _normalized, err = _parse_positive_decimal(inst.get(field))
        if err == "missing":
            missing_meta = True
        elif err == "invalid":
            invalid_meta = True

    if missing_meta:
        reasons.append(StructuralExclusionCodeV1.MISSING_REQUIRED_METADATA.value)
    if invalid_meta:
        reasons.append(StructuralExclusionCodeV1.INVALID_REQUIRED_METADATA.value)

    state = str(inst.get("state") or "").strip().lower()
    if not state:
        reasons.append(StructuralExclusionCodeV1.UNKNOWN_TRADING_STATUS.value)
    elif state != ACTIVE_TRADING_STATE:
        reasons.append(StructuralExclusionCodeV1.INACTIVE_OR_SUSPENDED.value)

    mark_present = bool(inst_id) and inst_id in mark_price_supported_ids
    if not mark_present:
        reasons.append(StructuralExclusionCodeV1.MISSING_MARK_PRESENCE.value)

    unique_reasons = tuple(sorted(set(reasons)))
    return StructuralEligibilityRowV1(
        venue_native_inst_id=inst_id,
        instrument_type=inst_type or "UNKNOWN",
        eligible=len(unique_reasons) == 0,
        exclusion_reason_codes=unique_reasons,
        mark_price_present=mark_present,
        exp_time_empty=exp_empty,
        base_currency=base,
        quote_currency=quote,
    )


def classify_census_rows_v1(
    instruments: Sequence[Mapping[str, Any]],
    *,
    venue: str,
    mark_price_supported_ids: frozenset[str],
) -> tuple[tuple[StructuralEligibilityRowV1, ...], bool]:
    """Return classified rows and whether the census has duplicate native ids."""
    rows = tuple(
        classify_structural_eligibility_v1(
            inst,
            venue=venue,
            mark_price_supported_ids=mark_price_supported_ids,
        )
        for inst in instruments
    )
    seen: dict[str, int] = {}
    for row in rows:
        if not row.venue_native_inst_id:
            continue
        seen[row.venue_native_inst_id] = seen.get(row.venue_native_inst_id, 0) + 1
    has_duplicates = any(count > 1 for count in seen.values())
    if not has_duplicates:
        return rows, False
    demoted: list[StructuralEligibilityRowV1] = []
    for row in rows:
        if row.venue_native_inst_id and seen.get(row.venue_native_inst_id, 0) > 1:
            codes = tuple(
                sorted(
                    set(row.exclusion_reason_codes)
                    | {StructuralExclusionCodeV1.DUPLICATE_NATIVE_ID.value}
                )
            )
            demoted.append(
                StructuralEligibilityRowV1(
                    venue_native_inst_id=row.venue_native_inst_id,
                    instrument_type=row.instrument_type,
                    eligible=False,
                    exclusion_reason_codes=codes,
                    mark_price_present=row.mark_price_present,
                    exp_time_empty=row.exp_time_empty,
                    base_currency=row.base_currency,
                    quote_currency=row.quote_currency,
                )
            )
        else:
            demoted.append(row)
    return tuple(demoted), True
