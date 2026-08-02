"""Raw metadata validation, futures-only/BTC filters, normalization, eligibility."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Optional, Sequence

from src.ops.governed_futures_universe_producer_v1.constants_v1 import (
    ACTIVE_TRADING_STATES,
    FORBIDDEN_BASE_ASSETS,
    FORBIDDEN_INSTRUMENT_TOKENS,
    PRODUCER_VERSION,
    SUPPORTED_CT_TYPES,
    SUPPORTED_INST_TYPES,
    VENUE,
)
from src.ops.governed_futures_universe_producer_v1.models_v1 import GovernedUniverseInstrumentV1
from src.ops.governed_futures_universe_producer_v1.reason_codes_v1 import UniverseFailureCodeV1
from src.research.instrument_id_canonicalization_v1 import (
    InstrumentIdCanonicalizationInputV1,
    canonicalize_instrument_id_v1,
)

_ASSET_FROM_INST = re.compile(r"^([A-Z0-9]+)-([A-Z0-9]+)(?:-([A-Z0-9]+))?$")


def _bounded_token_match(text: str, token: str) -> bool:
    pattern = rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])"
    return re.search(pattern, text.lower()) is not None


def _is_btc_instrument(inst: Mapping[str, Any], *, base: str, inst_id: str) -> bool:
    if base in FORBIDDEN_BASE_ASSETS:
        return True
    values = [
        inst_id,
        base,
        str(inst.get("uly") or ""),
        str(inst.get("ctValCcy") or ""),
        str(inst.get("baseCcy") or ""),
    ]
    for value in values:
        lowered = value.lower()
        for token in FORBIDDEN_INSTRUMENT_TOKENS:
            if _bounded_token_match(lowered, token):
                return True
    return False


def _parse_positive_decimal(raw: Any) -> tuple[Optional[str], Optional[str]]:
    """Return (normalized_str, error_kind) where error_kind is missing|invalid|None."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None, "missing"
    if isinstance(raw, float):
        # Reject binary floats — venue metadata must be exact string/int decimals.
        return None, "invalid"
    try:
        value = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError, ArithmeticError):
        return None, "invalid"
    if value <= 0:
        return None, "invalid"
    # Normalize without scientific notation / trailing zeros where possible.
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


def _ms_or_iso_to_rfc3339(value: str) -> Optional[str]:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.isdigit():
        ms = int(raw)
        if ms <= 0:
            return None
        dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    # Accept already-ISO timestamps.
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_event_time_unix(value: str) -> Optional[float]:
    rfc = _ms_or_iso_to_rfc3339(value)
    if rfc is None:
        return None
    return datetime.fromisoformat(rfc.replace("Z", "+00:00")).timestamp()


def _expiry_yyyymmdd(exp_rfc3339: str) -> Optional[str]:
    try:
        dt = datetime.fromisoformat(exp_rfc3339.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.strftime("%Y%m%d")


def classify_instrument_v1(
    inst: Mapping[str, Any],
    *,
    venue: str,
    source_event_time: str,
    producer_observed_at: str,
    repository_sha: str,
    config_digest: str,
    source_digest: str,
    mark_price_supported_ids: frozenset[str],
    max_source_age_seconds: float,
    producer_observed_unix: float,
) -> GovernedUniverseInstrumentV1:
    """Fail-closed eligibility classification for one venue instrument row."""
    reasons: list[str] = []
    inst_id = str(inst.get("instId") or "").strip()
    if not inst_id:
        reasons.append(UniverseFailureCodeV1.MISSING_NATIVE_INST_ID.value)

    inst_type = str(inst.get("instType") or "").strip().upper()
    if inst_type == "SPOT":
        reasons.append(UniverseFailureCodeV1.SPOT_INSTRUMENT.value)
    elif inst_type not in SUPPORTED_INST_TYPES:
        reasons.append(UniverseFailureCodeV1.UNSUPPORTED_INSTRUMENT_TYPE.value)

    base, quote = _extract_base_quote(inst, inst_id)
    settle = str(inst.get("settleCcy") or "").strip().upper()
    if not base:
        reasons.append(UniverseFailureCodeV1.MISSING_BASE_CURRENCY.value)
    if not quote:
        reasons.append(UniverseFailureCodeV1.MISSING_QUOTE_CURRENCY.value)
    if not settle:
        reasons.append(UniverseFailureCodeV1.MISSING_SETTLEMENT_CURRENCY.value)

    if inst_id and _is_btc_instrument(inst, base=base, inst_id=inst_id):
        reasons.append(UniverseFailureCodeV1.BTC_INSTRUMENT.value)

    ct_type = str(inst.get("ctType") or "").strip().lower()
    if ct_type not in SUPPORTED_CT_TYPES:
        reasons.append(UniverseFailureCodeV1.UNSUPPORTED_CONTRACT_TYPE.value)

    state = str(inst.get("state") or "").strip().lower()
    if not state:
        reasons.append(UniverseFailureCodeV1.UNKNOWN_TRADING_STATUS.value)
    elif state not in ACTIVE_TRADING_STATES:
        reasons.append(UniverseFailureCodeV1.INACTIVE_OR_SUSPENDED.value)

    tick_sz, tick_err = _parse_positive_decimal(inst.get("tickSz"))
    if tick_err == "missing":
        reasons.append(UniverseFailureCodeV1.MISSING_TICK_SIZE.value)
    elif tick_err == "invalid":
        reasons.append(UniverseFailureCodeV1.INVALID_TICK_SIZE.value)

    lot_sz, lot_err = _parse_positive_decimal(inst.get("lotSz"))
    if lot_err == "missing":
        reasons.append(UniverseFailureCodeV1.MISSING_LOT_SIZE.value)
    elif lot_err == "invalid":
        reasons.append(UniverseFailureCodeV1.INVALID_LOT_SIZE.value)

    min_sz, min_err = _parse_positive_decimal(inst.get("minSz"))
    if min_err == "missing":
        reasons.append(UniverseFailureCodeV1.MISSING_MINIMUM_ORDER_SIZE.value)
    elif min_err == "invalid":
        reasons.append(UniverseFailureCodeV1.INVALID_MINIMUM_ORDER_SIZE.value)

    ct_val, ct_err = _parse_positive_decimal(inst.get("ctVal"))
    if ct_err == "missing":
        reasons.append(UniverseFailureCodeV1.MISSING_CONTRACT_VALUE.value)
    elif ct_err == "invalid":
        reasons.append(UniverseFailureCodeV1.INVALID_CONTRACT_VALUE.value)

    ct_val_ccy = str(inst.get("ctValCcy") or "").strip().upper()
    if not ct_val_ccy:
        reasons.append(UniverseFailureCodeV1.MISSING_CONTRACT_VALUE_CURRENCY.value)

    mark_supported = bool(inst_id) and inst_id in mark_price_supported_ids
    if not mark_supported:
        reasons.append(UniverseFailureCodeV1.MARK_PRICE_UNSUPPORTED.value)

    # Market-data support requires complete instrument metadata presence (already checked)
    # plus mark-price support for this capability scope.
    market_data_supported = mark_supported and tick_sz is not None and lot_sz is not None
    if not market_data_supported:
        reasons.append(UniverseFailureCodeV1.MARKET_DATA_UNSUPPORTED.value)

    if not source_event_time:
        reasons.append(UniverseFailureCodeV1.MISSING_SOURCE_EVENT_TIME.value)
    else:
        event_unix = _parse_event_time_unix(source_event_time)
        if event_unix is None:
            reasons.append(UniverseFailureCodeV1.STALE_SOURCE_EVENT_TIME.value)
        elif producer_observed_unix - event_unix > float(max_source_age_seconds):
            reasons.append(UniverseFailureCodeV1.STALE_SOURCE_EVENT_TIME.value)

    expiry_time: Optional[str] = None
    perpetual_or_expiry = "perpetual"
    contract_type = "linear_perpetual"
    market_type = "perpetual"

    if inst_type == "FUTURES":
        perpetual_or_expiry = "expiry"
        contract_type = "linear_dated_future"
        market_type = "futures"
        exp_raw = str(inst.get("expTime") or "").strip()
        if not exp_raw or exp_raw in {"0", "None", "null"}:
            reasons.append(UniverseFailureCodeV1.MISSING_EXPIRY_FOR_DATED_FUTURE.value)
        else:
            expiry_time = _ms_or_iso_to_rfc3339(exp_raw)
            if expiry_time is None:
                reasons.append(UniverseFailureCodeV1.INVALID_EXPIRY_FOR_DATED_FUTURE.value)

    if inst_type == "SWAP":
        exp_raw = str(inst.get("expTime") or "").strip()
        if exp_raw and exp_raw not in {"0", "None", "null"}:
            # SWAP with expiry is unsupported in this producer scope.
            reasons.append(UniverseFailureCodeV1.UNSUPPORTED_INSTRUMENT_TYPE.value)

    canonical_id = ""
    if not reasons:
        canon_kwargs: dict[str, Any] = {
            "venue_id": venue,
            "market_type": market_type,
            "contract_type": contract_type,
            "base_asset": base,
            "quote_asset": quote,
            "settlement_asset": settle,
            "venue_symbol": inst_id,
            "native_instrument_id": inst_id.lower(),
        }
        if contract_type == "linear_dated_future" and expiry_time:
            yyyymmdd = _expiry_yyyymmdd(expiry_time)
            if yyyymmdd:
                canon_kwargs["contract_expiry"] = yyyymmdd
        canon = canonicalize_instrument_id_v1(InstrumentIdCanonicalizationInputV1(**canon_kwargs))
        if not canon.success or not canon.instrument_id:
            reasons.append(UniverseFailureCodeV1.CANONICALIZATION_FAILED.value)
            for code in canon.error_codes:
                if code not in reasons:
                    reasons.append(code)
        else:
            canonical_id = canon.instrument_id

    eligible = not reasons
    data_quality = "PASS" if eligible else "FAIL_CLOSED"
    source_event_rfc = _ms_or_iso_to_rfc3339(source_event_time) or source_event_time

    return GovernedUniverseInstrumentV1(
        canonical_instrument_id=canonical_id or f"excluded:{inst_id or 'missing'}",
        venue=venue or VENUE,
        venue_native_inst_id=inst_id,
        instrument_type=inst_type or "UNKNOWN",
        base_currency=base,
        quote_currency=quote,
        settlement_currency=settle,
        contract_type=contract_type,
        perpetual_or_expiry_semantics=perpetual_or_expiry,
        expiry_time=expiry_time,
        tick_size=tick_sz or "",
        lot_size=lot_sz or "",
        minimum_order_size=min_sz or "",
        contract_value=ct_val or "",
        contract_value_currency=ct_val_ccy,
        trading_status=state or "unknown",
        mark_price_supported=mark_supported,
        market_data_supported=bool(market_data_supported and eligible),
        data_quality_status=data_quality,
        source_event_time=source_event_rfc,
        producer_observed_at=producer_observed_at,
        producer_version=PRODUCER_VERSION,
        repository_sha=repository_sha,
        config_digest=config_digest,
        source_digest=source_digest,
        eligibility=eligible,
        exclusion_reason_codes=tuple(sorted(set(reasons))),
    )


def resolve_conflicts_and_duplicates_v1(
    classified: Sequence[GovernedUniverseInstrumentV1],
) -> tuple[list[GovernedUniverseInstrumentV1], list[GovernedUniverseInstrumentV1], dict[str, int]]:
    """Apply duplicate / conflicting-ID fail-closed demotions after per-row classification."""
    exclusion_counts: dict[str, int] = {}
    by_native: dict[str, list[GovernedUniverseInstrumentV1]] = {}
    for row in classified:
        key = row.venue_native_inst_id or f"__missing_{id(row)}"
        by_native.setdefault(key, []).append(row)

    demoted: list[GovernedUniverseInstrumentV1] = []
    survivors: list[GovernedUniverseInstrumentV1] = []

    for native, group in by_native.items():
        if native.startswith("__missing_"):
            for row in group:
                if row.eligibility:
                    demoted.append(_demote(row, UniverseFailureCodeV1.MISSING_NATIVE_INST_ID.value))
                else:
                    demoted.append(row)
            continue
        if len(group) > 1:
            for row in group:
                demoted.append(_demote(row, UniverseFailureCodeV1.DUPLICATE_INSTRUMENT.value))
                exclusion_counts[UniverseFailureCodeV1.DUPLICATE_INSTRUMENT.value] = (
                    exclusion_counts.get(UniverseFailureCodeV1.DUPLICATE_INSTRUMENT.value, 0) + 1
                )
            continue
        survivors.append(group[0])

    # Conflicting canonical IDs: same canonical maps to different natives among eligible.
    by_canonical: dict[str, list[GovernedUniverseInstrumentV1]] = {}
    for row in survivors:
        if not row.eligibility:
            continue
        by_canonical.setdefault(row.canonical_instrument_id, []).append(row)

    conflict_canonicals = {
        cid
        for cid, group in by_canonical.items()
        if len({r.venue_native_inst_id for r in group}) > 1
    }
    # Conflicting native IDs: same native already handled as duplicate; also catch
    # eligible rows that somehow share native with different canonicals (should not).
    final_eligible: list[GovernedUniverseInstrumentV1] = []
    final_excluded: list[GovernedUniverseInstrumentV1] = []
    for row in survivors:
        if not row.eligibility:
            final_excluded.append(row)
            for code in row.exclusion_reason_codes:
                exclusion_counts[code] = exclusion_counts.get(code, 0) + 1
            continue
        if row.canonical_instrument_id in conflict_canonicals:
            demoted_row = _demote(row, UniverseFailureCodeV1.CONFLICTING_CANONICAL_IDS.value)
            final_excluded.append(demoted_row)
            exclusion_counts[UniverseFailureCodeV1.CONFLICTING_CANONICAL_IDS.value] = (
                exclusion_counts.get(UniverseFailureCodeV1.CONFLICTING_CANONICAL_IDS.value, 0) + 1
            )
            continue
        final_eligible.append(row)

    for row in demoted:
        final_excluded.append(row)
        for code in row.exclusion_reason_codes:
            exclusion_counts[code] = exclusion_counts.get(code, 0) + 1

    # Conflicting native IDs across different canonicals after demotion path:
    # if two eligible survivors somehow have identical native with different canonical
    # (already prevented by duplicate), emit CONFLICTING_NATIVE_IDS when same native
    # appears with different canonical among excluded+eligible set from original.
    native_to_canonicals: dict[str, set[str]] = {}
    for row in classified:
        if not row.venue_native_inst_id:
            continue
        if row.canonical_instrument_id.startswith("excluded:"):
            continue
        native_to_canonicals.setdefault(row.venue_native_inst_id, set()).add(
            row.canonical_instrument_id
        )
    for native, cans in native_to_canonicals.items():
        if len(cans) > 1:
            # Ensure reason is recorded even if already demoted as duplicate.
            exclusion_counts[UniverseFailureCodeV1.CONFLICTING_NATIVE_IDS.value] = (
                exclusion_counts.get(UniverseFailureCodeV1.CONFLICTING_NATIVE_IDS.value, 0) + 1
            )
            rebuilt_eligible: list[GovernedUniverseInstrumentV1] = []
            for row in final_eligible:
                if row.venue_native_inst_id == native:
                    demoted_row = _demote(row, UniverseFailureCodeV1.CONFLICTING_NATIVE_IDS.value)
                    final_excluded.append(demoted_row)
                else:
                    rebuilt_eligible.append(row)
            final_eligible = rebuilt_eligible

    final_eligible.sort(key=lambda r: r.canonical_instrument_id)
    final_excluded.sort(key=lambda r: (r.venue_native_inst_id, r.canonical_instrument_id))
    return final_eligible, final_excluded, exclusion_counts


def _demote(row: GovernedUniverseInstrumentV1, code: str) -> GovernedUniverseInstrumentV1:
    codes = tuple(sorted(set(row.exclusion_reason_codes + (code,))))
    return GovernedUniverseInstrumentV1(
        canonical_instrument_id=row.canonical_instrument_id,
        venue=row.venue,
        venue_native_inst_id=row.venue_native_inst_id,
        instrument_type=row.instrument_type,
        base_currency=row.base_currency,
        quote_currency=row.quote_currency,
        settlement_currency=row.settlement_currency,
        contract_type=row.contract_type,
        perpetual_or_expiry_semantics=row.perpetual_or_expiry_semantics,
        expiry_time=row.expiry_time,
        tick_size=row.tick_size,
        lot_size=row.lot_size,
        minimum_order_size=row.minimum_order_size,
        contract_value=row.contract_value,
        contract_value_currency=row.contract_value_currency,
        trading_status=row.trading_status,
        mark_price_supported=row.mark_price_supported,
        market_data_supported=False,
        data_quality_status="FAIL_CLOSED",
        source_event_time=row.source_event_time,
        producer_observed_at=row.producer_observed_at,
        producer_version=row.producer_version,
        repository_sha=row.repository_sha,
        config_digest=row.config_digest,
        source_digest=row.source_digest,
        eligibility=False,
        exclusion_reason_codes=codes,
    )
