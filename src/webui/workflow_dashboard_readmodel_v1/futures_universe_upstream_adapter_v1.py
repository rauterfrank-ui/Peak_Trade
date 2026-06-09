"""Upstream futures universe → universe_selection_readmodel.v1 mapping (U1 — pure, no I/O)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.double_play_futures_input_producer import FuturesProducerPacket

from .universe_selection_contract_v1 import (
    FORBIDDEN_SELECTED_SYMBOLS,
    FORBIDDEN_TRUTH_SOURCE_KINDS,
    MAX_RANKING_ROWS,
    MAX_UNIVERSE_ROWS,
    MISSING_TRUTH_FUTURE_DETAIL,
    MISSING_TRUTH_PNL,
    MISSING_TRUTH_RANKING,
    MISSING_TRUTH_SELECTED,
    MISSING_TRUTH_UNIVERSE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STORAGE_RELATIVE_PATH,
    validate_universe_selection_payload,
)
from .universe_selection_producer_v1 import PRODUCER_CONTRACT

FUTURES_UNIVERSE_UPSTREAM_ADAPTER_VERSION = "v1"
UPSTREAM_ADAPTER_CONTRACT = "futures_universe_upstream_adapter.v1"

ELIGIBLE_MARKET_TYPES = frozenset(
    {
        FuturesMarketType.FUTURES,
        FuturesMarketType.PERPETUAL,
        FuturesMarketType.SWAP,
    }
)

FORBIDDEN_UPSTREAM_SOURCE_MARKERS = frozenset(
    {
        "market_ranking_funnel_readmodel.v0",
        "market_surface",
        "market_surface_dummy",
        "get_market_dummy",
        "btc_usd_dummy_default",
    }
)

INELIGIBLE_SPOT_SYMBOLS = frozenset(
    {
        "BTC/USD",
        "BTC/EUR",
        "ETH/USD",
        "BTCUSD",
        "BTC-USD",
        "BTCEUR",
        "ETHUSD",
    }
)

REASON_UPSTREAM_SOURCE_EMPTY = "UPSTREAM_SOURCE_EMPTY"
REASON_MARKET_SURFACE_NOT_OBSERVABILITY_TRUTH = "MARKET_SURFACE_NOT_OBSERVABILITY_TRUTH"
REASON_SPOT_OR_NON_DERIVATIVE_SELECTED_FUTURE_REJECTED = (
    "SPOT_OR_NON_DERIVATIVE_SELECTED_FUTURE_REJECTED"
)
REASON_SELECTED_FUTURE_NOT_IN_ELIGIBLE_UNIVERSE = "SELECTED_FUTURE_NOT_IN_ELIGIBLE_UNIVERSE"
REASON_INELIGIBLE_MARKET_TYPE = "INELIGIBLE_MARKET_TYPE"
REASON_INELIGIBLE_INSTRUMENT_METADATA_INCOMPLETE = "INELIGIBLE_INSTRUMENT_METADATA_INCOMPLETE"
REASON_INELIGIBLE_CANDIDATE_VALIDATION_INCOMPLETE = "INELIGIBLE_CANDIDATE_VALIDATION_INCOMPLETE"
REASON_INELIGIBLE_SPOT_SYMBOL = "INELIGIBLE_SPOT_SYMBOL"
CANDIDATE_VALIDATION_PROJECTION_SOURCE = "candidate_validation_bridge"


@dataclass(frozen=True)
class FuturesUniverseUpstreamInputV1:
    """Governed upstream input for futures-only universe/ranking/selection mapping."""

    source_run_id: str
    source_stage: str
    generated_at: str
    packets: tuple[FuturesProducerPacket, ...]
    upstream_source_kind: str | None = None
    upstream_producer_id: str | None = None
    selected_candidate_id: str | None = None
    evidence_links: tuple[str, ...] = ()
    fixture_marked: bool = False
    candidate_validation_projection: bool = False
    instrument_raw_by_candidate_id: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class EligibilityExclusionV1:
    candidate_id: str
    symbol: str
    reason: str


@dataclass(frozen=True)
class FuturesUniverseUpstreamAdapterResultV1:
    """Pure adapter outcome — payload always contract-valid; status signals mapping mode."""

    status: str
    payload: dict[str, Any]
    rejection_reasons: tuple[str, ...]
    eligibility_exclusions: tuple[EligibilityExclusionV1, ...]


def _normalize_symbol(symbol: str) -> str:
    return symbol.upper().replace("-", "").replace("/", "")


def _is_spot_symbol(symbol: str) -> bool:
    if symbol in INELIGIBLE_SPOT_SYMBOLS or symbol in FORBIDDEN_SELECTED_SYMBOLS:
        return True
    normalized = _normalize_symbol(symbol)
    if normalized in INELIGIBLE_SPOT_SYMBOLS:
        return True
    if "/" in symbol:
        return True
    return False


def is_forbidden_upstream_source(
    *,
    upstream_source_kind: str | None,
    upstream_producer_id: str | None,
) -> bool:
    markers = (
        upstream_source_kind,
        upstream_producer_id,
    )
    for marker in markers:
        if not marker:
            continue
        text = marker.strip()
        if text in FORBIDDEN_UPSTREAM_SOURCE_MARKERS:
            return True
        if text in FORBIDDEN_TRUTH_SOURCE_KINDS:
            return True
    return False


def evaluate_packet_eligibility(packet: FuturesProducerPacket) -> tuple[bool, str | None]:
    """Return (eligible, exclusion_reason). Futures/derivative-only; no symbol heuristics alone."""
    symbol = packet.candidate.symbol
    if _is_spot_symbol(symbol):
        return False, REASON_INELIGIBLE_SPOT_SYMBOL
    if packet.candidate.market_type not in ELIGIBLE_MARKET_TYPES:
        return False, REASON_INELIGIBLE_MARKET_TYPE
    if not packet.instrument.complete:
        return False, REASON_INELIGIBLE_INSTRUMENT_METADATA_INCOMPLETE
    return True, None


def evaluate_packet_eligibility_candidate_validation(
    packet: FuturesProducerPacket,
    *,
    raw_instrument: Mapping[str, Any] | None,
) -> tuple[bool, str | None]:
    """Candidate-validation projection eligibility — strict instrument.complete not required."""
    symbol = packet.candidate.symbol
    if _is_spot_symbol(symbol):
        return False, REASON_INELIGIBLE_SPOT_SYMBOL
    if packet.candidate.market_type not in ELIGIBLE_MARKET_TYPES:
        return False, REASON_INELIGIBLE_MARKET_TYPE
    if packet.candidate.live_authorization:
        return False, REASON_INELIGIBLE_MARKET_TYPE
    if raw_instrument is None or raw_instrument.get("candidate_validation_complete") is not True:
        return False, REASON_INELIGIBLE_CANDIDATE_VALIDATION_INCOMPLETE
    instrument = packet.instrument
    provider_flags = (
        instrument.contract_size_known,
        instrument.tick_size_known,
        instrument.step_size_known,
        instrument.min_qty_known,
        instrument.margin_asset_known,
        instrument.settlement_asset_known,
        instrument.leverage_bounds_known,
    )
    if not all(provider_flags) or instrument.missing_fields:
        return False, REASON_INELIGIBLE_CANDIDATE_VALIDATION_INCOMPLETE
    return True, None


def _missing_truth_payload(
    *,
    source_run_id: str,
    source_stage: str,
    generated_at: str,
    evidence_links: tuple[str, ...],
    fixture_marked: bool,
    rejection_reasons: tuple[str, ...],
) -> dict[str, Any]:
    links = [item.strip() for item in evidence_links if item and item.strip()]
    payload: dict[str, Any] = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "source_run_id": source_run_id.strip(),
        "source_stage": source_stage.strip().lower(),
        "non_authorizing": True,
        "fixture_marked": fixture_marked,
        "universe": [],
        "ranking": [],
        "selected_future": {"truth_status": "NOT_PERSISTED"},
        "market_snapshot": {
            "truth_status": "NOT_PERSISTED",
            "source_kind": "NOT_PERSISTED",
            "snapshot_id": None,
            "exchange": None,
            "captured_at": None,
        },
        "evidence": {
            "producer_contract": PRODUCER_CONTRACT,
            "upstream_adapter": UPSTREAM_ADAPTER_CONTRACT,
            "storage_target": STORAGE_RELATIVE_PATH,
            "manifest_verify_rc_expected": 0,
            "links": links,
            "rejection_reasons": list(rejection_reasons),
        },
        "missing_truth": {
            "universe": MISSING_TRUTH_UNIVERSE,
            "ranking": MISSING_TRUTH_RANKING,
            "selected_future": MISSING_TRUTH_SELECTED,
            "future_detail": MISSING_TRUTH_FUTURE_DETAIL,
            "orders_fills_pnl": MISSING_TRUTH_PNL,
        },
    }
    validate_universe_selection_payload(payload)
    return payload


def _sort_key(packet: FuturesProducerPacket) -> tuple[int, str]:
    rank = packet.ranking.rank
    sort_rank = rank if isinstance(rank, int) and rank > 0 else 10_000
    return (sort_rank, packet.candidate.candidate_id)


def _universe_row(packet: FuturesProducerPacket) -> dict[str, Any]:
    row: dict[str, Any] = {
        "row_id": packet.candidate.candidate_id,
        "symbol": packet.candidate.symbol,
        "rank": packet.ranking.rank if packet.ranking.rank is not None else 0,
        "exchange": packet.candidate.exchange,
        "notes": "futures_upstream_adapter_v1",
    }
    return row


def _ranking_row(packet: FuturesProducerPacket) -> dict[str, Any]:
    row: dict[str, Any] = {
        "row_id": f"r-{packet.candidate.candidate_id}",
        "symbol": packet.candidate.symbol,
        "rank": packet.ranking.rank if packet.ranking.rank is not None else 0,
        "notes": "futures_upstream_adapter_v1",
    }
    if packet.ranking.score is not None:
        row["display_score"] = packet.ranking.score
    return row


def _selected_future_row(packet: FuturesProducerPacket, *, selection_reason: str) -> dict[str, Any]:
    return {
        "row_id": f"s-{packet.candidate.candidate_id}",
        "symbol": packet.candidate.symbol,
        "rank": packet.ranking.rank if packet.ranking.rank is not None else 1,
        "truth_status": "PERSISTED",
        "selection_reason": selection_reason,
        "notes": "futures_upstream_adapter_v1 — non-authorizing observability truth",
    }


def _market_snapshot_from_packet(packet: FuturesProducerPacket) -> dict[str, Any]:
    provenance = packet.provenance
    return {
        "truth_status": "PERSISTED",
        "source_kind": "futures_upstream_adapter_v1",
        "snapshot_id": provenance.dataset_id,
        "exchange": packet.candidate.exchange,
        "captured_at": None,
    }


def map_futures_packets_to_universe_selection_readmodel(
    upstream_input: FuturesUniverseUpstreamInputV1,
) -> FuturesUniverseUpstreamAdapterResultV1:
    """Map governed FuturesProducerPacket inputs to a contract-valid readmodel payload."""
    rejection_reasons: list[str] = []
    exclusions: list[EligibilityExclusionV1] = []

    if is_forbidden_upstream_source(
        upstream_source_kind=upstream_input.upstream_source_kind,
        upstream_producer_id=upstream_input.upstream_producer_id,
    ):
        rejection_reasons.append(REASON_MARKET_SURFACE_NOT_OBSERVABILITY_TRUTH)
        payload = _missing_truth_payload(
            source_run_id=upstream_input.source_run_id,
            source_stage=upstream_input.source_stage,
            generated_at=upstream_input.generated_at,
            evidence_links=upstream_input.evidence_links,
            fixture_marked=upstream_input.fixture_marked,
            rejection_reasons=tuple(rejection_reasons),
        )
        return FuturesUniverseUpstreamAdapterResultV1(
            status="missing_truth",
            payload=payload,
            rejection_reasons=tuple(rejection_reasons),
            eligibility_exclusions=(),
        )

    if not upstream_input.packets:
        rejection_reasons.append(REASON_UPSTREAM_SOURCE_EMPTY)
        payload = _missing_truth_payload(
            source_run_id=upstream_input.source_run_id,
            source_stage=upstream_input.source_stage,
            generated_at=upstream_input.generated_at,
            evidence_links=upstream_input.evidence_links,
            fixture_marked=upstream_input.fixture_marked,
            rejection_reasons=tuple(rejection_reasons),
        )
        return FuturesUniverseUpstreamAdapterResultV1(
            status="missing_truth",
            payload=payload,
            rejection_reasons=tuple(rejection_reasons),
            eligibility_exclusions=(),
        )

    eligible_packets: list[FuturesProducerPacket] = []
    for packet in upstream_input.packets:
        eligible, reason = evaluate_packet_eligibility(packet)
        if eligible:
            eligible_packets.append(packet)
        elif reason is not None:
            exclusions.append(
                EligibilityExclusionV1(
                    candidate_id=packet.candidate.candidate_id,
                    symbol=packet.candidate.symbol,
                    reason=reason,
                )
            )

    eligible_packets.sort(key=_sort_key)
    universe_packets = eligible_packets[:MAX_UNIVERSE_ROWS]
    ranking_packets = eligible_packets[:MAX_RANKING_ROWS]

    universe_rows = [_universe_row(packet) for packet in universe_packets]
    ranking_rows = [_ranking_row(packet) for packet in ranking_packets]

    eligible_by_id = {packet.candidate.candidate_id: packet for packet in eligible_packets}
    packets_by_id = {packet.candidate.candidate_id: packet for packet in upstream_input.packets}
    selected_packet: FuturesProducerPacket | None = None
    selection_reason = "upstream_top_ranked_eligible"

    if upstream_input.selected_candidate_id:
        selected_id = upstream_input.selected_candidate_id.strip()
        raw_packet = packets_by_id.get(selected_id)
        if raw_packet is None:
            rejection_reasons.append(REASON_SELECTED_FUTURE_NOT_IN_ELIGIBLE_UNIVERSE)
        else:
            eligible, reason = evaluate_packet_eligibility(raw_packet)
            if not eligible:
                if _is_spot_symbol(raw_packet.candidate.symbol) or (
                    raw_packet.candidate.market_type not in ELIGIBLE_MARKET_TYPES
                ):
                    rejection_reasons.append(REASON_SPOT_OR_NON_DERIVATIVE_SELECTED_FUTURE_REJECTED)
                elif reason is not None:
                    rejection_reasons.append(reason)
                else:
                    rejection_reasons.append(REASON_SELECTED_FUTURE_NOT_IN_ELIGIBLE_UNIVERSE)
            elif selected_id not in {packet.candidate.candidate_id for packet in universe_packets}:
                rejection_reasons.append(REASON_SELECTED_FUTURE_NOT_IN_ELIGIBLE_UNIVERSE)
            else:
                selected_packet = raw_packet
                selection_reason = "upstream_explicit_selection"
    elif ranking_packets:
        selected_packet = ranking_packets[0]
        selection_reason = "upstream_top_ranked_eligible"

    has_universe = bool(universe_rows)
    has_ranking = bool(ranking_rows)
    has_selected = selected_packet is not None

    if not has_universe and not has_ranking:
        rejection_reasons.append(REASON_UPSTREAM_SOURCE_EMPTY)
        payload = _missing_truth_payload(
            source_run_id=upstream_input.source_run_id,
            source_stage=upstream_input.source_stage,
            generated_at=upstream_input.generated_at,
            evidence_links=upstream_input.evidence_links,
            fixture_marked=upstream_input.fixture_marked,
            rejection_reasons=tuple(rejection_reasons),
        )
        return FuturesUniverseUpstreamAdapterResultV1(
            status="missing_truth",
            payload=payload,
            rejection_reasons=tuple(rejection_reasons),
            eligibility_exclusions=tuple(exclusions),
        )

    selected_block: dict[str, Any]
    if has_selected and selected_packet is not None:
        selected_block = _selected_future_row(selected_packet, selection_reason=selection_reason)
    else:
        selected_block = {"truth_status": "NOT_PERSISTED"}

    snapshot_packet = selected_packet or (universe_packets[0] if universe_packets else None)
    if snapshot_packet is not None and has_selected:
        market_snapshot = _market_snapshot_from_packet(snapshot_packet)
        future_detail_status = "AVAILABLE"
    else:
        market_snapshot = {
            "truth_status": "NOT_PERSISTED",
            "source_kind": "NOT_PERSISTED",
            "snapshot_id": None,
            "exchange": None,
            "captured_at": None,
        }
        future_detail_status = MISSING_TRUTH_FUTURE_DETAIL

    links = [item.strip() for item in upstream_input.evidence_links if item and item.strip()]
    payload: dict[str, Any] = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "generated_at": upstream_input.generated_at,
        "source_run_id": upstream_input.source_run_id.strip(),
        "source_stage": upstream_input.source_stage.strip().lower(),
        "non_authorizing": True,
        "fixture_marked": upstream_input.fixture_marked,
        "universe": universe_rows,
        "ranking": ranking_rows,
        "selected_future": selected_block,
        "market_snapshot": market_snapshot,
        "evidence": {
            "producer_contract": PRODUCER_CONTRACT,
            "upstream_adapter": UPSTREAM_ADAPTER_CONTRACT,
            "storage_target": STORAGE_RELATIVE_PATH,
            "manifest_verify_rc_expected": 0,
            "links": links,
            "rejection_reasons": list(rejection_reasons),
            "eligibility_exclusions": [
                {"candidate_id": item.candidate_id, "symbol": item.symbol, "reason": item.reason}
                for item in exclusions
            ],
        },
        "missing_truth": {
            "universe": "PERSISTED" if has_universe else MISSING_TRUTH_UNIVERSE,
            "ranking": "PERSISTED" if has_ranking else MISSING_TRUTH_RANKING,
            "selected_future": "PERSISTED" if has_selected else MISSING_TRUTH_SELECTED,
            "future_detail": future_detail_status,
            "orders_fills_pnl": MISSING_TRUTH_PNL,
        },
    }
    validate_universe_selection_payload(payload)

    status = "ok" if has_universe and has_ranking and has_selected else "partial"
    return FuturesUniverseUpstreamAdapterResultV1(
        status=status,
        payload=payload,
        rejection_reasons=tuple(rejection_reasons),
        eligibility_exclusions=tuple(exclusions),
    )


def map_futures_packets_to_universe_selection_readmodel_candidate_validation(
    upstream_input: FuturesUniverseUpstreamInputV1,
) -> FuturesUniverseUpstreamAdapterResultV1:
    """Map candidate_validation_complete packets to a non-truth projection payload (no selected future)."""
    if not upstream_input.candidate_validation_projection:
        msg = (
            "candidate_validation_projection must be true for "
            "map_futures_packets_to_universe_selection_readmodel_candidate_validation"
        )
        raise ValueError(msg)

    rejection_reasons: list[str] = []
    exclusions: list[EligibilityExclusionV1] = []

    if is_forbidden_upstream_source(
        upstream_source_kind=upstream_input.upstream_source_kind,
        upstream_producer_id=upstream_input.upstream_producer_id,
    ):
        rejection_reasons.append(REASON_MARKET_SURFACE_NOT_OBSERVABILITY_TRUTH)
        payload = _missing_truth_payload(
            source_run_id=upstream_input.source_run_id,
            source_stage=upstream_input.source_stage,
            generated_at=upstream_input.generated_at,
            evidence_links=upstream_input.evidence_links,
            fixture_marked=upstream_input.fixture_marked,
            rejection_reasons=tuple(rejection_reasons),
        )
        return FuturesUniverseUpstreamAdapterResultV1(
            status="missing_truth",
            payload=payload,
            rejection_reasons=tuple(rejection_reasons),
            eligibility_exclusions=(),
        )

    if not upstream_input.packets:
        rejection_reasons.append(REASON_UPSTREAM_SOURCE_EMPTY)
        payload = _missing_truth_payload(
            source_run_id=upstream_input.source_run_id,
            source_stage=upstream_input.source_stage,
            generated_at=upstream_input.generated_at,
            evidence_links=upstream_input.evidence_links,
            fixture_marked=upstream_input.fixture_marked,
            rejection_reasons=tuple(rejection_reasons),
        )
        return FuturesUniverseUpstreamAdapterResultV1(
            status="missing_truth",
            payload=payload,
            rejection_reasons=tuple(rejection_reasons),
            eligibility_exclusions=(),
        )

    if upstream_input.selected_candidate_id:
        rejection_reasons.append(REASON_SELECTED_FUTURE_NOT_IN_ELIGIBLE_UNIVERSE)

    raw_by_id = upstream_input.instrument_raw_by_candidate_id
    eligible_packets: list[FuturesProducerPacket] = []
    for packet in upstream_input.packets:
        raw_instrument = raw_by_id.get(packet.candidate.candidate_id)
        eligible, reason = evaluate_packet_eligibility_candidate_validation(
            packet,
            raw_instrument=raw_instrument,
        )
        if eligible:
            eligible_packets.append(packet)
        elif reason is not None:
            exclusions.append(
                EligibilityExclusionV1(
                    candidate_id=packet.candidate.candidate_id,
                    symbol=packet.candidate.symbol,
                    reason=reason,
                )
            )

    eligible_packets.sort(key=_sort_key)
    universe_packets = eligible_packets[:MAX_UNIVERSE_ROWS]
    ranking_packets = eligible_packets[:MAX_RANKING_ROWS]
    universe_rows = [_universe_row(packet) for packet in universe_packets]
    ranking_rows = [_ranking_row(packet) for packet in ranking_packets]

    if not universe_rows and not ranking_rows:
        rejection_reasons.append(REASON_UPSTREAM_SOURCE_EMPTY)
        payload = _missing_truth_payload(
            source_run_id=upstream_input.source_run_id,
            source_stage=upstream_input.source_stage,
            generated_at=upstream_input.generated_at,
            evidence_links=upstream_input.evidence_links,
            fixture_marked=upstream_input.fixture_marked,
            rejection_reasons=tuple(rejection_reasons),
        )
        return FuturesUniverseUpstreamAdapterResultV1(
            status="missing_truth",
            payload=payload,
            rejection_reasons=tuple(rejection_reasons),
            eligibility_exclusions=tuple(exclusions),
        )

    links = [item.strip() for item in upstream_input.evidence_links if item and item.strip()]
    payload: dict[str, Any] = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "generated_at": upstream_input.generated_at,
        "source_run_id": upstream_input.source_run_id.strip(),
        "source_stage": upstream_input.source_stage.strip().lower(),
        "non_authorizing": True,
        "fixture_marked": False,
        "real_metadata_source_marked": True,
        "observability_truth_allowed": False,
        "universe": universe_rows,
        "ranking": ranking_rows,
        "selected_future": {"truth_status": "NOT_PERSISTED"},
        "market_snapshot": {
            "truth_status": "NOT_PERSISTED",
            "source_kind": "NOT_PERSISTED",
            "snapshot_id": None,
            "exchange": None,
            "captured_at": None,
        },
        "evidence": {
            "producer_contract": PRODUCER_CONTRACT,
            "upstream_adapter": UPSTREAM_ADAPTER_CONTRACT,
            "storage_target": STORAGE_RELATIVE_PATH,
            "manifest_verify_rc_expected": 0,
            "links": links,
            "rejection_reasons": list(rejection_reasons),
            "projection_source": CANDIDATE_VALIDATION_PROJECTION_SOURCE,
            "candidate_validation_projection": True,
            "eligibility_exclusions": [
                {"candidate_id": item.candidate_id, "symbol": item.symbol, "reason": item.reason}
                for item in exclusions
            ],
        },
        "missing_truth": {
            "universe": "PERSISTED" if universe_rows else MISSING_TRUTH_UNIVERSE,
            "ranking": "PERSISTED" if ranking_rows else MISSING_TRUTH_RANKING,
            "selected_future": MISSING_TRUTH_SELECTED,
            "future_detail": MISSING_TRUTH_FUTURE_DETAIL,
            "orders_fills_pnl": MISSING_TRUTH_PNL,
        },
    }
    validate_universe_selection_payload(payload)
    status = (
        "candidate_validation_projection"
        if universe_rows or ranking_rows
        else "missing_truth"
    )
    return FuturesUniverseUpstreamAdapterResultV1(
        status=status,
        payload=payload,
        rejection_reasons=tuple(rejection_reasons),
        eligibility_exclusions=tuple(exclusions),
    )


def map_futures_packet_sequence(
    *,
    source_run_id: str,
    source_stage: str,
    generated_at: str,
    packets: Sequence[FuturesProducerPacket],
    upstream_source_kind: str | None = None,
    upstream_producer_id: str | None = None,
    selected_candidate_id: str | None = None,
    evidence_links: tuple[str, ...] = (),
    fixture_marked: bool = False,
) -> FuturesUniverseUpstreamAdapterResultV1:
    """Convenience wrapper for tuple/sequence packet inputs."""
    return map_futures_packets_to_universe_selection_readmodel(
        FuturesUniverseUpstreamInputV1(
            source_run_id=source_run_id,
            source_stage=source_stage,
            generated_at=generated_at,
            packets=tuple(packets),
            upstream_source_kind=upstream_source_kind,
            upstream_producer_id=upstream_producer_id,
            selected_candidate_id=selected_candidate_id,
            evidence_links=evidence_links,
            fixture_marked=fixture_marked,
        )
    )
