"""Review independent instrument cards outside the protected runtime."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime
import hashlib
import json
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from src.ops.bounded_peaktrade_system_composition_v1.paper_market_liquidity_v1 import (
    validate_public_paper_sources_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import IsolatedLaneSlotV1
from src.ops.full_core_live_path_composition_root_v1.current_productive_candidate_input_gate_v1 import (
    finalized_candidate_candle_history_rejection_codes_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_CANDLES,
    ENDPOINT_MARKET_TICKER,
    ENDPOINT_PUBLIC_FUNDING_RATE,
    ENDPOINT_PUBLIC_OPEN_INTEREST,
    extract_finalized_candle_closes_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
)
from trading.master_v2.canonical_market_context_v1 import (
    compute_canonical_market_context_input_digest,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.golden_geometry_engine_v1 import (
    compute_canonical_base_geometry_magnitude_from_market_context_v1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.integrated_offline_replay_evidence_writer_v1 import _jsonable
from src.ops.master_v2_double_play_instrument_cards_v1 import (
    OfflineInstrumentCandidateCardV1,
    OfflineInstrumentCandidateReviewV1,
)


def bind_archived_candidate_captures_v1(
    card: OfflineInstrumentCandidateCardV1,
    *,
    observations: Mapping[str, FreshPretradeGetTransportResultV1],
    raw_bodies: Mapping[str, bytes],
) -> OfflineInstrumentCandidateCardV1:
    """Bind retained public GET receipts and their original bytes to one card version."""
    queries = {}
    for label, receipt in observations.items():
        endpoint = urlsplit(receipt.endpoint)
        queries[label] = (endpoint.path, dict(parse_qsl(endpoint.query)))
    payloads, _, _ = validate_public_paper_sources_v1(
        observations,
        queries=queries,
        observed_unix=_unix(card.replay_input.canonical_market_context.decision_time),
    )
    captures = {}
    for label, receipt in observations.items():
        path, query = queries[label]
        if path not in {
            ENDPOINT_MARKET_CANDLES,
            ENDPOINT_MARKET_TICKER,
            ENDPOINT_PUBLIC_OPEN_INTEREST,
            ENDPOINT_PUBLIC_FUNDING_RATE,
        } or (path == ENDPOINT_MARKET_CANDLES and query.get("bar") != "1m"):
            continue
        raw = raw_bodies[label]
        if (
            hashlib.sha256(raw).hexdigest() != receipt.body_sha256
            or json.loads(raw) != payloads[label]
        ):
            raise ValueError(f"candidate_original_capture_mismatch:{label}")
        if path in captures:
            raise ValueError(f"candidate_duplicate_source:{path}")
        captures[path] = {
            "request_path": path,
            "request_query": query,
            "native_id": card.binding.venue_native_id,
            "get_performed": receipt.get_performed,
            "auth_required": receipt.auth_header_sent,
            "http_status": receipt.http_status,
            "captured_at_utc": receipt.acquired_at_utc,
            "payload": payloads[label],
            "body_sha256": receipt.body_sha256,
            "raw_hex": raw.hex(),
        }
    return replace(card, market_captures=captures)


def _unix(time: str) -> float:
    stamp = datetime.fromisoformat(time.replace("Z", "+00:00"))
    if stamp.utcoffset() is None:
        raise ValueError("timezone_required")
    return stamp.timestamp()


def _read_capture(
    card: OfflineInstrumentCandidateCardV1, path: str, decision_unix: float
) -> tuple[Mapping[str, Any], float]:
    native = card.binding.venue_native_id
    capture = card.market_captures[path]
    query = capture["request_query"]
    payload = capture["payload"]
    rows = payload["data"]
    if "raw_hex" in capture:
        raw = bytes.fromhex(capture["raw_hex"])
        if hashlib.sha256(raw).hexdigest() != capture["body_sha256"] or json.loads(raw) != payload:
            raise ValueError(f"candidate_original_capture_mismatch:{path}")
    if (
        capture["request_path"] != path
        or capture["native_id"] != native
        or not isinstance(query, Mapping)
        or query.get("instId") != native
        or capture["get_performed"] is not True
        or capture["auth_required"] is not False
        or capture["http_status"] != 200
        or payload["code"] != "0"
        or not isinstance(rows, list)
    ):
        raise ValueError(f"market_capture_identity_or_source:{path}")
    captured_unix = _unix(capture["captured_at_utc"])
    if not 0 < captured_unix <= decision_unix:
        raise ValueError(f"market_capture_time:{path}")
    if path == ENDPOINT_MARKET_CANDLES:
        if query.get("bar") != "1m" or payload.get("instId", native) != native:
            raise ValueError(f"market_capture_identity_or_source:{path}")
    else:
        if len(rows) != 1 or rows[0]["instId"] != native:
            raise ValueError(f"market_capture_identity_or_source:{path}")
        if not 0 < int(rows[0]["ts"]) / 1000 <= captured_unix:
            raise ValueError(f"market_capture_time:{path}")
    return payload, captured_unix


def _review_card(
    instrument_id: str,
    card: OfflineInstrumentCandidateCardV1,
    ranked_slot_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
) -> OfflineInstrumentCandidateReviewV1:
    replay_input = card.replay_input
    context = replay_input.canonical_market_context
    binding = card.binding
    if card.source_mode not in {"PAPER", "SHADOW", "OFFLINE_FIXTURE"}:
        raise ValueError("candidate_source_mode_invalid")
    if (
        replay_input.regime_bull_bear_switch_evidence_path is not None
        or replay_input.current_instrument_capital_risk_sizing_boundary_state_file is not None
    ):
        raise ValueError("offline_card_requires_in_memory_replay")
    card_digest = hashlib.sha256(
        json.dumps(_jsonable(card), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    if not instrument_id or not binding.venue_native_id or instrument_id != binding.instrument_id:
        raise ValueError("instrument_binding_mismatch")
    if replay_input.instrument_id != instrument_id or context.instrument_id != instrument_id:
        raise ValueError("market_context_instrument_mismatch")
    slot_identity = card.slot_identity
    if slot_identity is not None:
        slot, current_bound = ranked_slot_pairs[slot_identity.lane_id]
        if (
            not isinstance(slot_identity, OccupiedLaneRuntimeInstrumentIdentityV1)
            or slot_identity.lane_id not in LANE_IDS
            or not isinstance(slot, IsolatedLaneSlotV1)
            or current_bound != binding
            or slot.lane_id != slot_identity.lane_id
            or slot.occupancy != "OCCUPIED"
            or slot.canonical_instrument_id != instrument_id
            or slot.universe_snapshot_id != binding.universe_snapshot_id
            or slot.ranking_snapshot_id != binding.ranking_snapshot_id
            or slot.ranking_integrity_digest != binding.ranking_integrity_digest
            or slot_identity
            != OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
                lane_id=slot_identity.lane_id, bound=binding
            )
        ):
            raise ValueError("candidate_slot_binding_mismatch")
    digest = compute_canonical_market_context_input_digest(context)
    if context.input_digest != digest:
        raise ValueError("market_context_digest_mismatch")
    if replay_input.venue_flat is not True or replay_input.existing_position_side.value != "none":
        raise ValueError("candidate_must_be_flat")
    decision_unix = _unix(context.decision_time)
    confirmation_key = replay_input.confirmation_progress_instrument
    if confirmation_key is not None and (
        confirmation_key.canonical_instrument_id != instrument_id
        or confirmation_key.venue_instrument_id != binding.venue_native_id
    ):
        raise ValueError("confirmation_instrument_mismatch")
    acceptance = replay_input.observation_acceptance_result
    if acceptance is not None:
        identity = acceptance.observation_identity
        if identity is not None and (
            identity.canonical_instrument_id != instrument_id
            or identity.venue_instrument_id != binding.venue_native_id
            or identity.mark_price != context.mark_price
            or identity.venue_event_time > decision_unix
        ):
            raise ValueError("confirmation_observation_mismatch")
    card.price_provenance.validate_against_cycle_inputs_v1(
        mark_px=context.mark_price,
        index_px=context.index_price,
        venue_native_id=binding.venue_native_id,
        observed_unix=decision_unix,
    )
    candles, candles_captured_unix = _read_capture(card, ENDPOINT_MARKET_CANDLES, decision_unix)
    history_reasons = finalized_candidate_candle_history_rejection_codes_v1(candles)
    if history_reasons:
        raise ValueError(",".join(history_reasons))
    closes, last_open_unix = extract_finalized_candle_closes_v1(candles)
    if (
        closes != replay_input.price_path
        or last_open_unix is None
        or last_open_unix + 60 > candles_captured_unix
    ):
        raise ValueError("market_capture_c1_history_mismatch")
    ticker = _read_capture(card, ENDPOINT_MARKET_TICKER, decision_unix)[0]["data"][0]
    interest = _read_capture(card, ENDPOINT_PUBLIC_OPEN_INTEREST, decision_unix)[0]["data"][0]
    funding_row = _read_capture(card, ENDPOINT_PUBLIC_FUNDING_RATE, decision_unix)[0]["data"][0]
    bid, ask, volume, oi, funding = (
        float(raw)
        for raw in (
            ticker["bidPx"],
            ticker["askPx"],
            ticker["vol24h"],
            interest["oi"],
            funding_row["fundingRate"],
        )
    )
    if (bid, ask, volume, oi, funding) != (
        context.best_bid,
        context.best_ask,
        context.volume,
        context.open_interest,
        context.funding_rate,
    ):
        raise ValueError("market_capture_values_do_not_match_context")

    replay = run_integrated_offline_trading_logic_replay_v1(replay_input)
    evidence = replay.evidence
    gge_digest = None
    if replay.intermediate is not None:
        market_context = replay.intermediate.market_context
        scope = replay.intermediate.scope_initialization.scope
        if (
            scope is not None
            and scope.source_input_digest == digest
            and scope.initialized_at_trading_epoch == context.trading_epoch
        ):
            gge = compute_canonical_base_geometry_magnitude_from_market_context_v1(market_context)
            if gge.output is not None and gge.output.magnitude == scope.initial_volatility_distance:
                gge_digest = gge.output.input_digest
    entry = replay.replay_pass and evidence.decision_outcome in {
        DecisionOutcome.ENTER_LONG.value,
        DecisionOutcome.ENTER_SHORT.value,
    }
    return OfflineInstrumentCandidateReviewV1(
        status="OFFLINE_ENTRY_DECISION" if entry else "NO_ENTRY",
        reasons=tuple(dict.fromkeys((*replay.fail_reasons, *evidence.reason_codes))),
        card_digest=card_digest,
        source_mode=card.source_mode,
        decision_outcome=evidence.decision_outcome,
        decision_time=context.decision_time,
        market_context_digest=digest,
        gge_input_digest=gge_digest,
        decision_digest=evidence.semantic_digest,
        lane_id=None if slot_identity is None else slot_identity.lane_id,
        instrument_epoch=None
        if slot_identity is None
        else slot_identity.lane_identity.instrument_epoch,
    )


def review_offline_instrument_candidate_cards_v1(
    cards: Mapping[str, OfflineInstrumentCandidateCardV1],
    *,
    ranked_slot_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]] | None = None,
) -> dict[str, OfflineInstrumentCandidateReviewV1]:
    """Evaluate each candidate through the existing pure replay, with no runtime authority."""
    counts = Counter(
        card.binding.venue_native_id
        for card in cards.values()
        if isinstance(card, OfflineInstrumentCandidateCardV1)
        and isinstance(card.binding, BoundInstrumentV1)
        and isinstance(card.binding.venue_native_id, str)
    )
    lane_counts = Counter(
        card.slot_identity.lane_id
        for card in cards.values()
        if isinstance(card, OfflineInstrumentCandidateCardV1)
        and isinstance(card.slot_identity, OccupiedLaneRuntimeInstrumentIdentityV1)
        and isinstance(card.slot_identity.lane_id, str)
    )
    reviews = {}
    for instrument_id, card in cards.items():
        try:
            if not isinstance(card, OfflineInstrumentCandidateCardV1) or not isinstance(
                card.binding, BoundInstrumentV1
            ):
                raise ValueError("instrument_card_or_binding_invalid")
            if counts[card.binding.venue_native_id] != 1:
                raise ValueError("duplicate_venue_instrument")
            if card.slot_identity is not None and lane_counts[card.slot_identity.lane_id] != 1:
                raise ValueError("duplicate_slot_assignment")
            reviews[instrument_id] = _review_card(instrument_id, card, ranked_slot_pairs or {})
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
            reviews[instrument_id] = OfflineInstrumentCandidateReviewV1(
                status="REJECTED_INPUT", reasons=(str(exc),)
            )
    return reviews
