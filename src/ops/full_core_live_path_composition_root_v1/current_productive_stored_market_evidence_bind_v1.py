"""Bind stored public-market evidence into the native full-cycle host.

Reads durable GET bodies already on disk. Does not GET, POST, or fill a
missing volume, open-interest, funding, bid, ask, mark, or index field.
RUNTIME_AUTHORIZATION_EFFECT=NONE.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    extract_finalized_candle_closes_v1,
    extract_funding_rate_v1,
    extract_mark_and_index_from_payload_v1,
    extract_open_interest_v1,
    extract_ticker_fields_v1,
)

CANDLE_BODY_NAME = "raw_public_candles_get_v1.json"
CANDLE_PROVENANCE_NAME = "raw_public_candles_get_provenance_v1.json"


class StoredMarketEvidenceBindError(RuntimeError):
    """Fail-closed stored market evidence violation."""


@dataclass(frozen=True)
class StoredMarketEvidenceAssessmentV1:
    native_id: str
    finalized_closes: tuple[float, ...]
    last_finalized_event_ts_unix: float | None
    observed_unix: float | None
    volume: float | None
    open_interest: float | None
    funding_rate: float | None
    bid_px: float | None
    ask_px: float | None
    mark_px: float | None
    index_px: float | None
    mark_payload: Mapping[str, Any] | None
    ticker_payload: Mapping[str, Any] | None
    index_tickers_payload: Mapping[str, Any] | None
    body_sha256_matches: bool
    post_count_zero: bool
    missing_fields: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return self.body_sha256_matches and self.post_count_zero and not self.missing_fields


@dataclass(frozen=True)
class StoredBalanceAuthorityAssessmentV1:
    usable_for_capital_context: bool
    reason: str
    observed_at_utc: str


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mapping(payload: Any) -> Mapping[str, Any] | None:
    if isinstance(payload, Mapping):
        return payload
    return None


def assess_stored_market_evidence_directory_v1(
    *,
    evidence_dir: Path,
    native_id: str,
) -> StoredMarketEvidenceAssessmentV1:
    """Assess one evidence directory for one instrument.

    Sibling files for a different instrument are ignored. Missing fields stay
    missing.
    """

    wanted = str(native_id or "").strip()
    if not wanted:
        raise StoredMarketEvidenceBindError("NATIVE_ID_REQUIRED")
    root = Path(evidence_dir)
    body_path = root / CANDLE_BODY_NAME
    provenance_path = root / CANDLE_PROVENANCE_NAME
    if not body_path.is_file() or not provenance_path.is_file():
        raise StoredMarketEvidenceBindError("STORED_CANDLE_FILES_MISSING")
    provenance = _mapping(_load_json(provenance_path))
    body = _mapping(_load_json(body_path))
    if provenance is None or body is None:
        raise StoredMarketEvidenceBindError("STORED_CANDLE_JSON_NOT_OBJECT")

    missing: list[str] = []
    provenance_native = str(provenance.get("C1_GATE_NATIVE_ID") or "").strip()
    if provenance_native != wanted:
        missing.append("instrument_mismatch")
    endpoint = str(provenance.get("ENDPOINT") or "")
    if f"instId={wanted}" not in endpoint:
        missing.append("endpoint_instrument")
    body_sha = _sha256_file(body_path)
    sha_ok = body_sha == str(provenance.get("BODY_SHA256") or "")
    if not sha_ok:
        missing.append("body_sha256")
    post_count_zero = str(provenance.get("POST_COUNT") or "") == "0"
    if not post_count_zero:
        missing.append("post_count")
    if str(provenance.get("VENUE_MUTATION_PERFORMED") or "").lower() == "true":
        missing.append("venue_mutation")

    closes, last_ts = extract_finalized_candle_closes_v1(body)
    if not closes or last_ts is None:
        missing.append("finalized_closes")
    observed_raw = provenance.get("OBSERVED_AT_UNIX")
    try:
        observed_unix = float(observed_raw) if observed_raw not in (None, "") else None
    except (TypeError, ValueError):
        observed_unix = None
    if observed_unix is None:
        missing.append("observed_unix")

    found: dict[str, Any] = {}
    for path in sorted(root.glob("*.json")):
        if path.name in {CANDLE_BODY_NAME, CANDLE_PROVENANCE_NAME}:
            continue
        payload = _mapping(_load_json(path))
        if payload is None:
            continue
        _absorb_same_instrument_payload_v1(payload, native_id=wanted, found=found)

    volume = found.get("volume")
    open_interest = found.get("open_interest")
    funding_rate = found.get("funding_rate")
    bid_px = found.get("bid_px")
    ask_px = found.get("ask_px")
    mark_px = found.get("mark_px")
    index_px = found.get("index_px")
    for name, value in (
        ("vol24h", volume),
        ("open_interest", open_interest),
        ("funding_rate", funding_rate),
        ("bid_px", bid_px),
        ("ask_px", ask_px),
        ("mark_px", mark_px),
        ("index_px", index_px),
    ):
        if value is None:
            missing.append(name)

    return StoredMarketEvidenceAssessmentV1(
        native_id=wanted,
        finalized_closes=tuple(closes),
        last_finalized_event_ts_unix=last_ts,
        observed_unix=observed_unix,
        volume=None if volume is None else float(volume),
        open_interest=None if open_interest is None else float(open_interest),
        funding_rate=None if funding_rate is None else float(funding_rate),
        bid_px=None if bid_px is None else float(bid_px),
        ask_px=None if ask_px is None else float(ask_px),
        mark_px=None if mark_px is None else float(mark_px),
        index_px=None if index_px is None else float(index_px),
        mark_payload=found.get("mark_payload"),
        ticker_payload=found.get("ticker_payload"),
        index_tickers_payload=found.get("index_tickers_payload"),
        body_sha256_matches=sha_ok,
        post_count_zero=post_count_zero,
        missing_fields=tuple(missing),
    )


def _absorb_same_instrument_payload_v1(
    payload: Mapping[str, Any],
    *,
    native_id: str,
    found: dict[str, Any],
) -> None:
    bid, ask, volume, ticker_index = extract_ticker_fields_v1(payload, native_id=native_id)
    if volume is not None and "volume" not in found:
        found["volume"] = volume
        found["bid_px"] = bid
        found["ask_px"] = ask
        found["ticker_payload"] = payload
        if ticker_index is not None and "index_px" not in found:
            found["index_px"] = ticker_index
    open_interest = extract_open_interest_v1(payload, native_id=native_id)
    if open_interest is not None and "open_interest" not in found:
        found["open_interest"] = open_interest
    funding_rate = extract_funding_rate_v1(payload, native_id=native_id)
    if funding_rate is not None and "funding_rate" not in found:
        found["funding_rate"] = funding_rate
    mark_px, mark_index = extract_mark_and_index_from_payload_v1(payload, native_id=native_id)
    if mark_px is not None and "mark_px" not in found:
        found["mark_px"] = mark_px
        found["mark_payload"] = payload
        if mark_index is not None:
            found["index_px"] = mark_index
    rows = payload.get("data")
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            if str(row.get("instId") or "").strip() not in {"", native_id}:
                continue
            if row.get("idxPx") is not None and "index_tickers_payload" not in found:
                found["index_tickers_payload"] = payload


def assess_stored_balance_authority_v1(
    *,
    capture_path: Path,
) -> StoredBalanceAuthorityAssessmentV1:
    """Classify a stored balance capture. A false authority flag is not equity."""

    payload = _mapping(_load_json(Path(capture_path)))
    if payload is None:
        return StoredBalanceAuthorityAssessmentV1(
            usable_for_capital_context=False,
            reason="BALANCE_CAPTURE_NOT_OBJECT",
            observed_at_utc="",
        )
    observed = str(payload.get("response_utc") or payload.get("request_utc") or "")
    authority = str(payload.get("venue_eq_source_authority") or "").lower()
    if authority != "true":
        return StoredBalanceAuthorityAssessmentV1(
            usable_for_capital_context=False,
            reason="VENUE_EQ_SOURCE_AUTHORITY_FALSE",
            observed_at_utc=observed,
        )
    return StoredBalanceAuthorityAssessmentV1(
        usable_for_capital_context=True,
        reason="VENUE_EQ_SOURCE_AUTHORITY_TRUE",
        observed_at_utc=observed,
    )
