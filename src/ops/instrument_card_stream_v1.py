"""Continuous instrument-card projections of the existing Paper/Shadow streams.

There is no second decision engine or cursor. Each existing consumer keeps its
original state; this adapter validates and projects its successive source inputs
and actual decisions. It never opens a transport or starts a session.
"""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal, DecimalException
from hashlib import sha256
import json
import math
import re
from pathlib import Path

from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
    bind_zkp_paper_market_v1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    durable_bytes_v1,
    immutable_json_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    RANKED_SWAP_SCOPES,
    SOPH_I17,
)
from src.ops.instrument_card_input_observation_v1 import observe_instrument_card_input_v1
from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import opening_order_side_v1
from src.ops.instrument_card_budget_assessment_v1 import assess_instrument_budget_v1
from src.ops.master_v2_double_play_instrument_cards_v1 import MASTER_V2_DOUBLE_PLAY_UNIVERSE
from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import (
    PUBLIC_V1_BEST_BID_ASK_MAX_AGE_SECONDS,
    PUBLIC_V1_MARK_PRICE_MAX_AGE_SECONDS,
)


SCHEMA = "master_v2_instrument_card_stream.v1"
_LANES = {"LANE_1", "LANE_2", "LANE_4", "LANE_5"}


def plain(value):
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (Decimal, Path)):
        return str(value)
    if hasattr(value, "value"):
        return plain(value.value)
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    return value


def validate_card_market_v1(market, *, bound, lane_id, now):
    """Same complete source contract, regardless of Paper or Shadow origin."""
    if (
        lane_id not in _LANES
        or market.slot.lane_id != lane_id
        or (market.slot.instrument_id, market.slot.native_id)
        != (bound.instrument_id, bound.venue_native_id)
        or bound.venue_native_id.startswith("BTC-")
        or isinstance(now, bool)
        or not math.isfinite(now)
        or now < market.observed_unix
        or market.source_observations is None
    ):
        raise ValueError("CARD_BOUND_INSTRUMENT_SOURCE_OR_CLOCK_MISMATCH")
    observations = market.source_observations
    bodies = market.original_bodies
    for label, receipt in observations.items():
        # Only explicit test receipts may reconstruct their own fixture bytes.
        raw = None if bodies is None else bodies.get(label)
        if raw is None and receipt.transport_class == "FIXTURE":
            raw = json.dumps(receipt.payload).encode()
        if (
            raw is None
            or sha256(raw).hexdigest() != receipt.body_sha256
            or json.loads(raw) != receipt.payload
        ):
            raise ValueError(f"CARD_ORIGINAL_SOURCE_MISMATCH:{label}")
    rebuilt = bind_zkp_paper_market_v1(
        observations,
        policy=market.policy,
        observed_unix=market.observed_unix,
        slot=market.slot,
        original_bodies=bodies,
    )
    if rebuilt != market:
        raise ValueError("CARD_TRANSFORMED_SOURCE_VALUES_MISMATCH")
    # Repeat the original event/capture/knowledge-time admission at consumption.
    bind_zkp_paper_market_v1(
        observations,
        policy=market.policy,
        observed_unix=now,
        slot=market.slot,
        original_bodies=bodies,
    )
    return market


def market_values_v1(market):
    return dict(
        mark_price=float(market.mark),
        index_price=float(market.index_payload["data"][0]["idxPx"]),
        best_bid=float(market.book.bids[0][0]),
        best_ask=float(market.book.asks[0][0]),
        volume_contracts_24h=float(market.volume_contracts),
        open_interest_contracts=float(market.oi_contracts),
        funding_rate=float(market.funding_rate),
        funding_time_unix=market.funding_time_unix,
        finalized_c1=market.candles_payload,
        finalized_mark_window=market.g17_payload,
        contract=plain(market.native_contract),
        bids=plain(market.book.bids),
        asks=plain(market.book.asks),
        book_event_unix=market.book_event_unix,
        mark_event_unix=market.market_event_unix,
        adv_usd=str(market.adv_usd),
        usd_per_usdc=str(market.usd_per_usdc),
    )


def _source_deadline(market):
    limits = [market.funding_time_unix]
    for label in ("mark", "book", "index", "usdc-index", "ticker", "open-interest"):
        receipt = market.source_observations[label]
        age = float(
            PUBLIC_V1_BEST_BID_ASK_MAX_AGE_SECONDS
            if label == "book"
            else PUBLIC_V1_MARK_PRICE_MAX_AGE_SECONDS
        )
        limits.extend(
            (
                int(receipt.payload["data"][0]["ts"]) / 1000 + age,
                datetime.fromisoformat(receipt.acquired_at_utc.replace("Z", "+00:00")).timestamp()
                + age,
            )
        )
    return min(limits)


def _card_assignment(lane_id, ranking_bound, slot_assignment):
    from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
        OccupiedLaneRuntimeInstrumentIdentityV1,
    )

    identity = None
    fields = dict(
        assignment_status="EXPLICIT_ISOLATED_TEST_BINDING", ranking_binding=None, slot_identity=None
    )
    if ranking_bound is not None:
        identity = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
            lane_id=lane_id, bound=ranking_bound
        )
        fields.update(
            assignment_status="ORIGINAL_CAP24_ASSIGNMENT_CARRIED",
            ranking_binding=ranking_bound.to_dict(),
            slot_identity=identity.to_manifest_dict(),
        )
    if slot_assignment is not None:
        fields.update(
            assignment_status="ORIGINAL_N5_SLOT_ASSIGNMENT_CARRIED",
            original_slot_assignment=slot_assignment.card_reference(),
        )
    return identity, fields


class InstrumentCardStreamV1:
    def __init__(
        self,
        *,
        root,
        bound,
        lane_id,
        source_mode,
        session_id,
        budget_source=None,
        ranking_bound=None,
        slot_assignment=None,
    ):
        if lane_id not in _LANES or source_mode not in {"PAPER", "SHADOW"}:
            raise ValueError("CARD_STREAM_SCOPE_INVALID")
        self.root = Path(root) / "instrument-cards" / lane_id
        self.bound, self.lane_id = bound, lane_id
        self.source_mode, self.session_id = source_mode, session_id
        self.budget_source = budget_source
        if slot_assignment is not None:
            ref = slot_assignment.card_reference()
            if (source_mode, lane_id, bound.instrument_id, bound.venue_native_id) != (
                "SHADOW",
                ref["lane_id"],
                ref["instrument_id"],
                ref["venue_native_id"],
            ):
                raise ValueError("CARD_ORIGINAL_SLOT_ASSIGNMENT_MISMATCH")
            ranking_bound = slot_assignment.entry_binding(ranking_bound)
        self.ranking_bound = ranking_bound
        if ranking_bound is not None:
            if (
                (ranking_bound.instrument_id, ranking_bound.venue_native_id)
                != (bound.instrument_id, bound.venue_native_id)
                or not all(
                    getattr(ranking_bound, name)
                    for name in ("ranking_snapshot_id", "universe_snapshot_id", "selection_id")
                )
                or not all(
                    re.fullmatch(r"[0-9a-f]{64}", getattr(ranking_bound, name))
                    for name in ("ranking_integrity_digest", "selection_integrity_digest")
                )
            ):
                raise ValueError("CARD_ORIGINAL_RANKING_ASSIGNMENT_MISMATCH")
        self.slot_identity, self.assignment_fields = _card_assignment(
            lane_id, ranking_bound, slot_assignment
        )
        self.market = None
        self.current = None
        self.last_market_event = None
        latest = self.root / "latest.json"
        if latest.exists():
            record = json.loads(latest.read_bytes())
            if record["sha256"] != canonical_digest_v1(record["body"]):
                raise ValueError("CARD_STREAM_DURABLE_DIGEST_MISMATCH")
            previous = record["body"]
            if (
                previous["instrument_id"],
                previous["venue_native_id"],
                previous["source_mode"],
                previous["session_id"],
                previous["binding"],
            ) != (
                bound.instrument_id,
                bound.venue_native_id,
                source_mode,
                session_id,
                bound.to_dict(),
            ):
                raise ValueError("CARD_STREAM_ORIGINAL_BINDING_CHANGED")
            self.last_market_event = previous.get("mark_event_unix")
            if (
                slot_assignment is None and previous.get("original_slot_assignment") is not None
            ) or any(previous.get(key) != value for key, value in self.assignment_fields.items()):
                raise ValueError("CARD_STREAM_RANKING_ASSIGNMENT_CHANGED")

    def _write(self, body, *, stage):
        body = plain(body)
        record = dict(body=body, sha256=canonical_digest_v1(body))
        raw = (json.dumps(record, sort_keys=True, allow_nan=False) + "\n").encode()
        if body.get("version") is not None:
            if self.market is not None:
                receipts = {}
                for label, source in self.market.source_observations.items():
                    original = (
                        None
                        if self.market.original_bodies is None
                        else self.market.original_bodies.get(label)
                    )
                    if original is None and source.transport_class == "FIXTURE":
                        original = json.dumps(source.payload).encode()
                    # Bytes have already passed validation. Publish them before
                    # latest.json so a visible version always has its originals.
                    source_path = self.root / "sources" / source.body_sha256
                    if source_path.exists():
                        if source_path.read_bytes() != original:
                            raise ValueError("CARD_DURABLE_ORIGINAL_BYTES_CONFLICT")
                    else:
                        durable_bytes_v1(source_path, original)
                    receipts[label] = plain(source)
                immutable_json_v1(
                    self.root / "versions" / body["version"] / "source-receipts.json", receipts
                )
            immutable_json_v1(self.root / "versions" / body["version"] / f"{stage}.json", record)
        durable_bytes_v1(self.root / "latest.json", raw)
        self.current = body
        return deepcopy(body)

    def unavailable_v1(self, reason, *, now):
        self.market = None
        return self._write(
            self._base(status="BLOCKED", now=now, reason=str(reason)), stage="blocked"
        )

    def _base(self, *, status, now, reason=None):
        return dict(
            schema=SCHEMA,
            owner_universe=MASTER_V2_DOUBLE_PLAY_UNIVERSE,
            instrument_id=self.bound.instrument_id,
            venue_native_id=self.bound.venue_native_id,
            binding=self.bound.to_dict(),
            lane_id=self.lane_id,
            source_mode=self.source_mode,
            session_id=self.session_id,
            status=status,
            reason=reason,
            observed_unix=now,
            version=None,
            mark_event_unix=self.last_market_event,
            market=None,
            sources=None,
            liquidity=None,
            master_v2=None,
            budget=None,
            budget_assessment=None,
            runtime_authorization_effect="NONE",
            productive_entry_admitted=False,
            valid_until_unix=None,
            **self.assignment_fields,
        )

    def update_v1(self, market, *, now):
        try:
            validate_card_market_v1(market, bound=self.bound, lane_id=self.lane_id, now=now)
            if (
                self.last_market_event is not None
                and market.market_event_unix < self.last_market_event
            ):
                raise ValueError("CARD_STREAM_OLDER_MARK")
        except (ValueError, TypeError, KeyError) as exc:
            self.unavailable_v1(exc, now=now)
            raise
        body = self._base(status="OBSERVING", now=now)
        body.update(
            valid_until_unix=_source_deadline(market),
            market=market_values_v1(market),
            mark_event_unix=market.market_event_unix,
            sources={
                label: dict(
                    body_sha256=source.body_sha256,
                    acquired_at_utc=source.acquired_at_utc,
                    endpoint=source.endpoint,
                )
                for label, source in market.source_observations.items()
            },
            liquidity={
                side: market.assess_opening_liquidity_v1(side=side) for side in ("BUY", "SELL")
            },
        )
        try:
            body["budget"] = self._budget(market, now=now)
        except (ValueError, TypeError, KeyError, DecimalException) as exc:
            self.unavailable_v1(exc, now=now)
            raise
        if body["budget"]["status"] != "BOUND":
            body["status"] = "BLOCKED_BUDGET_UNBOUND"
        else:
            body["budget_assessment"] = {
                side: assess_instrument_budget_v1(
                    market=market,
                    available_usdc=body["budget"]["available_for_new_entry"],
                    side=side,
                )
                for side in ("BUY", "SELL")
            }
        body["version"] = canonical_digest_v1(body)
        self.market = deepcopy(market)
        self.last_market_event = market.market_event_unix
        return self._write(body, stage="market")

    def current_v1(self, *, now):
        if self.market is None:
            return (
                deepcopy(self.current)
                if self.current is not None
                else self._base(status="BLOCKED", now=now, reason="AWAITING_FRESH_SOURCE")
            )
        try:
            validate_card_market_v1(self.market, bound=self.bound, lane_id=self.lane_id, now=now)
        except (ValueError, TypeError, KeyError) as exc:
            return self.unavailable_v1(exc, now=now)
        body = deepcopy(self.current)
        try:
            budget = self._budget(self.market, now=now)
        except (ValueError, TypeError, KeyError, DecimalException) as exc:
            return self.unavailable_v1(exc, now=now)
        if budget != body["budget"]:
            body["budget"] = budget
            body["budget_assessment"] = (
                None
                if budget["status"] != "BOUND"
                else {
                    side: assess_instrument_budget_v1(
                        market=self.market,
                        available_usdc=budget["available_for_new_entry"],
                        side=side,
                    )
                    for side in ("BUY", "SELL")
                }
            )
            # A new capital observation cannot carry the preceding evaluation
            # as a decision on the new budget. Original core state is untouched.
            body["master_v2"] = None
            body.pop("entry_review", None)
            body["observed_unix"] = now
            body["status"] = (
                "OBSERVING" if budget["status"] == "BOUND" else "BLOCKED_BUDGET_UNBOUND"
            )
            body["version"] = None
            body["version"] = canonical_digest_v1(body)
            return self._write(body, stage="budget-" + canonical_digest_v1(budget))
        return body

    def _budget(self, market, *, now):
        if self.budget_source is None:
            return dict(
                status="UNBOUND",
                available_amount=None,
                currency="USDC",
                observed_unix=now,
                reason="ORIGINAL_SLOT_BUDGET_SOURCE_REQUIRED",
            )
        budget = plain(self.budget_source(market=market, now=now))
        if (
            budget["status"] != "BOUND"
            or not budget.get("owner")
            or budget["lane_id"] != self.lane_id
            or budget["instrument_id"] != self.bound.instrument_id
            or budget["currency"] != "USDC"
            or budget["observed_unix"] != now
            or budget["source_digest"] != canonical_digest_v1(budget["original_snapshot"])
            or not Decimal(budget["available_amount"]).is_finite()
            or Decimal(budget["available_amount"]) < 0
            or not Decimal(budget["available_for_new_entry"]).is_finite()
            or not 0
            <= Decimal(budget["available_for_new_entry"])
            <= Decimal(budget["available_amount"])
        ):
            raise ValueError("CARD_CURRENT_SLOT_BUDGET_BINDING_MISMATCH")
        return budget

    def _observe(self, inp):
        if self.market is None or self.current is None:
            raise ValueError("CARD_MASTER_V2_WITHOUT_CURRENT_MARKET")
        context = inp.canonical_market_context
        values = self.current["market"]
        from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
            extract_finalized_candle_closes_v1,
        )

        closes, _ = extract_finalized_candle_closes_v1(self.market.candles_payload)
        if (
            inp.instrument_id != self.bound.instrument_id
            or context.instrument_id != self.bound.instrument_id
            or tuple(inp.price_path) != tuple(closes)
            or (
                context.mark_price,
                context.index_price,
                context.best_bid,
                context.best_ask,
                context.volume,
                context.open_interest,
                context.funding_rate,
            )
            != tuple(
                values[key]
                for key in (
                    "mark_price",
                    "index_price",
                    "best_bid",
                    "best_ask",
                    "volume_contracts_24h",
                    "open_interest_contracts",
                    "funding_rate",
                )
            )
        ):
            raise ValueError("CARD_ACTUAL_MASTER_V2_SOURCE_MISMATCH")
        self.current["master_v2"] = dict(
            input_digest=inp.input_digest,
            market_context_digest=context.input_digest,
            trading_epoch=inp.trading_epoch,
            prepared_input=plain(inp),
            decision=None,
        )

    @contextmanager
    def observe_v1(self):
        with observe_instrument_card_input_v1(self._observe):
            yield

    def entry_card_v1(self):
        from src.ops.master_v2_card_precheck_v1 import EntryCardV1

        if self.market is None or self.current is None:
            return None
        return EntryCardV1(self.ranking_bound or self.bound, self.market, self.current["budget"])

    def defer_entry_v1(self, review):
        body = deepcopy(self.current)
        status = (
            "WAITING_DISTINCT_MARK"
            if review.get("phase") == "MANAGE_POSITION"
            else "WAITING_ENTRY_CONDITIONS"
        )
        body.update(status=status, master_v2=None, entry_review=review)
        return self._write(body, stage="entry-review-" + canonical_digest_v1(review))

    def complete_v1(self, result):
        if self.current is None or self.market is None:
            return
        path = self.root / "versions" / self.current["version"] / "decision.json"
        if path.exists():
            stored = json.loads(path.read_bytes())
            if stored["sha256"] != canonical_digest_v1(stored["body"]):
                raise ValueError("CARD_STREAM_DURABLE_DIGEST_MISMATCH")
            self.current = stored["body"]
            return deepcopy(self.current)
        body = deepcopy(self.current)
        body["status"] = (
            "BLOCKED_BUDGET_UNBOUND"
            if body["budget"]["status"] != "BOUND"
            else "EVALUATED"
            if body["master_v2"] is not None
            else "OBSERVING"
        )
        if body["master_v2"] is not None:
            body["master_v2"]["decision"] = plain(result)
        return self._write(body, stage="decision")


def read_instrument_card_v1(root, *, bound, lane_id, now, ranking_bound=None, slot_assignment=None):
    """Read a persisted projection with expiry; never revive a stored decision.

    This is a view, not a financial admission. A new entry still needs its
    original decision owner, current budget read and exact-quantity check.
    """
    raw = json.loads((Path(root) / "instrument-cards" / lane_id / "latest.json").read_bytes())
    body = raw["body"]
    if slot_assignment is not None:
        ranking_bound = slot_assignment.entry_binding(ranking_bound)
    _, expected = _card_assignment(lane_id, ranking_bound, slot_assignment)
    if (
        raw["sha256"] != canonical_digest_v1(body)
        or body["binding"] != bound.to_dict()
        or body["lane_id"] != lane_id
        or (slot_assignment is None and body.get("original_slot_assignment") is not None)
        or any(body.get(key) != value for key, value in expected.items())
    ):
        raise ValueError("CARD_READER_DIGEST_OR_IDENTITY_MISMATCH")
    if isinstance(now, bool) or not math.isfinite(now) or now < body["observed_unix"]:
        raise ValueError("CARD_READER_CLOCK_INVALID")
    if body["valid_until_unix"] is None or now >= body["valid_until_unix"]:
        body = dict(
            body,
            status="BLOCKED",
            reason="CARD_SOURCE_EXPIRED_OR_UNAVAILABLE",
            market=None,
            liquidity=None,
            master_v2=None,
            budget=None,
            budget_assessment=None,
        )
    return body


def _validate_first_purchase_v1(entry):
    direction = entry.get("direction")
    if (
        entry.get("entry_action", "FIRST_PURCHASE") != "FIRST_PURCHASE"
        or direction not in {"long", "short"}
        or entry.get("first_purchase_side") != opening_order_side_v1(direction)
    ):
        raise ValueError("CARD_SLOT_ENTRY_BUDGET_BINDING_MISMATCH")


def validate_shadow_slot_entry_budget_v1(*, state, bound, budget, entry):
    """Validate the session, slot, selection and budget represented by a receipt."""
    _validate_first_purchase_v1(entry)
    scope = next(
        (i for i in (*RANKED_SWAP_SCOPES, SOPH_I17) if i.canonical_id == state.instrument_id), None
    )
    if (
        budget["owner"] != "I17_ORIGINAL_ANALYTICAL_PORTFOLIO_AND_SLOT_TEST_POLICY"
        or budget["status"] != "BOUND"
        or budget["currency"] != "USDC"
        or entry["budget_owner"] != budget["owner"]
        or not state.session_id
        or entry["session_id"] != state.session_id
        or entry["binding_scope"] != "ANALYTICAL_SLOT_ENTRY"
        or entry["lane_id"] != budget["lane_id"]
        or scope is None
        or budget["lane_id"] != scope.lane_id
        or scope.native_id != state.venue_instrument_id
        or entry["instrument_id"] != budget["instrument_id"]
        or (state.instrument_id, state.venue_instrument_id)
        != (bound.instrument_id, bound.venue_native_id)
        or (entry["instrument_id"], entry["venue_native_id"])
        != (bound.instrument_id, bound.venue_native_id)
        or (entry["selection_id"], entry["selection_integrity_digest"])
        != (bound.selection_id, bound.selection_integrity_digest)
        or entry["budget_source_digest"] != budget["source_digest"]
        or not Decimal(0) < Decimal(entry["nominal_usdc"]) <= Decimal(budget["available_amount"])
    ):
        raise ValueError("CARD_SLOT_ENTRY_BUDGET_BINDING_MISMATCH")


def bind_shadow_slot_entry_budget_v1(*, state, bound, budget, entry, sizing=None):
    """Keep the analytical sizing amount on the selected slot for its session."""
    validate_shadow_slot_entry_budget_v1(state=state, bound=bound, budget=budget, entry=entry)
    ranked = any(s.canonical_id == state.instrument_id for s in RANKED_SWAP_SCOPES)
    prior = state.ranked_confirmed_entry_budget if ranked else state.soph_confirmed_entry_budget
    if prior is not None and prior != entry:
        raise ValueError("CARD_SLOT_ENTRY_BUDGET_ALREADY_BOUND")
    if ranked:
        validate_ranked_sized_amount_v1(budget, entry, sizing)
        state.ranked_confirmed_entry_budget = dict(entry)
        return state.ranked_confirmed_entry_budget
    else:
        state.soph_confirmed_entry_budget = dict(entry)


def validate_ranked_sized_amount_v1(budget, entry, sizing):
    from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import (
        ReservationSizingBindingV1,
        request_digest_v1,
    )

    if not isinstance(sizing, ReservationSizingBindingV1):
        raise ValueError("SHADOW_FIRST_PURCHASE_ORIGINAL_SIZING_REQUIRED")
    amount = Decimal(entry["nominal_usdt"])
    sizing.validate_v1(amount=amount, decision_id=entry["decision_id"])
    request = sizing.applied_input
    snapshot = budget["original_snapshot"]
    valuation = snapshot["valuation"]
    if (
        budget["source_digest"] != canonical_digest_v1(snapshot)
        or request.config_digest != budget["source_digest"]
        or sizing.request_digest != entry["sizing_request_digest"]
        or request_digest_v1(request) != sizing.request_digest
        or request.reference_price != Decimal(valuation["mark_usdt_per_base"])
        or request.instrument.contract_multiplier != Decimal(entry["base_per_contract"])
        or request.instrument_id != entry["instrument_id"]
        or request.selected_side.lower() != entry["direction"]
        or sizing.decision.quantity_provenance.sizing_ref != entry["sizing_ref"]
        or sizing.decision.final_quantity != Decimal(entry["quantity_contracts"])
        or amount * Decimal(valuation["usdc_per_usdt"]) != Decimal(entry["nominal_usdc"])
        or (amount + Decimal(entry["cost_allowance_usdt"])) * Decimal(valuation["usdc_per_usdt"])
        > Decimal(entry["entry_limit_usdc"])
        or Decimal(entry["entry_limit_usdc"]) > Decimal(budget["available_amount"])
        or entry["fx_sha256"] != valuation["original_fx_sha256"]
        or (
            valuation["decision_id"],
            valuation["lane_id"],
            valuation["instrument_id"],
            valuation["venue_native_id"],
            valuation["entry_selection_digest"],
            valuation["mark_sha256"],
        )
        != (
            entry["decision_id"],
            entry["lane_id"],
            entry["instrument_id"],
            entry["venue_native_id"],
            entry["selection_integrity_digest"],
            entry["mark_sha256"],
        )
    ):
        raise ValueError("SHADOW_FIRST_PURCHASE_SIZED_AMOUNT_MISMATCH")


def ranked_shadow_slot_budget_v1(state, lane, policy, valuation):
    """Cap the analytical allocation in USDC using the original flat USDT model."""
    from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
        PAPER_ALLOCATION_USDC,
    )

    snap = plain(state.portfolio.snapshot())
    fx = Decimal(valuation["usdc_per_usdt"])
    if (
        (lane, state.instrument_id, state.venue_instrument_id)
        not in {(s.lane_id, s.canonical_id, s.native_id) for s in RANKED_SWAP_SCOPES}
        or (
            valuation["lane_id"],
            valuation["instrument_id"],
            valuation["venue_native_id"],
            valuation["status"],
        )
        != (lane, state.instrument_id, state.venue_instrument_id, "OBSERVED")
        or not fx.is_finite()
        or fx <= 0
        or policy.currency != "USDC"
        or lane not in policy.allowed_slot_ids
        or not snap["params"].get("linear_futures_collateral")
        or snap["orders_submitted"] is not False
        or snap["broker_writes"] is not False
        or state.ranked_confirmed_entry_budget is not None
        or snap["applied_fill_ids"]
        or any(Decimal(p["quantity"]) != 0 for p in snap["state"]["positions"].values())
    ):
        raise ValueError("SHADOW_FIRST_PURCHASE_FLAT_BUDGET_REQUIRED")
    available = min(
        PAPER_ALLOCATION_USDC,
        policy.per_slot_reserved_notional_limit,
        Decimal(snap["state"]["equity"]) * fx,
        Decimal(snap["state"]["cash"]) * fx,
    )
    if available <= 0:
        raise ValueError("SHADOW_FIRST_PURCHASE_BUDGET_EXHAUSTED")
    snapshot = dict(
        session_id=state.session_id,
        lane_id=lane,
        original_portfolio=snap,
        policy=policy.to_dict_v1(),
        valuation=valuation,
        portfolio_currency="USDT",
        test_allocation_usdc=str(PAPER_ALLOCATION_USDC),
    )
    return dict(
        status="BOUND",
        owner="I17_ORIGINAL_ANALYTICAL_PORTFOLIO_AND_SLOT_TEST_POLICY",
        lane_id=lane,
        instrument_id=state.instrument_id,
        currency="USDC",
        available_amount=str(available),
        original_snapshot=snapshot,
        source_digest=canonical_digest_v1(snapshot),
        reserved_amount=None,
    )


def shadow_budget_source_v1(state, *, repo):
    """Read the original analytical portfolio and explicit slot test policy.

    Initial allocation is set once, before the first analytical cycle. No
    reservation, private account balance or native execution authority is
    inferred from this model. Subsequent values come from its current state.
    """
    from dataclasses import replace
    from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
        PAPER_ALLOCATION_USDC,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
        load_slot_entry_budget_v1,
    )
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.idempotent_portfolio_v2 import (
        IdempotentPortfolioV2,
    )

    policy = load_slot_entry_budget_v1(
        Path(repo) / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V5.json"
    )
    initialized = False

    def capture(*, market, now):
        nonlocal initialized
        if (
            market.slot.lane_id != SOPH_I17.lane_id
            or state.instrument_id != market.slot.instrument_id
            or state.venue_instrument_id != market.slot.native_id
        ):
            raise ValueError("CARD_SHADOW_BUDGET_FOREIGN_INSTRUMENT")
        cap_usdc = min(
            PAPER_ALLOCATION_USDC,
            policy.per_slot_reserved_notional_limit,
        )
        if not initialized:
            if (
                state.cycle_index
                or state.portfolio.applied_intent_ids
                or state.portfolio.applied_fill_ids
            ):
                raise ValueError("CARD_SHADOW_INITIAL_CAPITAL_REBIND_FORBIDDEN")
            state.portfolio = IdempotentPortfolioV2.from_params(
                replace(
                    state.portfolio.model.params,
                    initial_equity=cap_usdc * market.usd_per_usdc,
                    linear_futures_collateral=True,
                )
            )
            initialized = True
        original = plain(state.portfolio.snapshot())
        marked = deepcopy(state.portfolio.model)
        marked.apply_intended_action(
            instrument_id=state.instrument_id,
            side="HOLD",
            quantity=Decimal(0),
            mark_price=market.mark,
        )
        equity = marked.economic_metrics().equity
        available = max(Decimal(0), min(cap_usdc, equity / market.usd_per_usdc))
        occupied = any(Decimal(p["quantity"]) != 0 for p in original["state"]["positions"].values())
        snapshot = dict(
            original_portfolio=original,
            marked_portfolio=plain(marked.snapshot()),
            policy=policy.to_dict_v1(),
            usd_per_usdc=str(market.usd_per_usdc),
        )
        if state.soph_confirmed_entry_budget is not None:
            _validate_first_purchase_v1(state.soph_confirmed_entry_budget)
            snapshot["confirmed_entry_budget"] = dict(state.soph_confirmed_entry_budget)
        return dict(
            status="BOUND",
            owner="I17_ORIGINAL_ANALYTICAL_PORTFOLIO_AND_SLOT_TEST_POLICY",
            currency="USDC",
            lane_id=market.slot.lane_id,
            instrument_id=state.instrument_id,
            observed_unix=now,
            available_amount=str(available),
            available_for_new_entry="0"
            if occupied or state.soph_confirmed_entry_budget is not None
            else str(available),
            reserved_amount=None,
            reservation_scope="ANALYTICAL_MODEL_WITHOUT_PORTFOLIO_HOLD",
            original_snapshot=snapshot,
            source_digest=canonical_digest_v1(snapshot),
        )

    return capture


def paper_budget_source_v1(session):
    """Project the actual Paper sizing owner's current slot state, not a fixed 25."""

    def capture(*, market, now):
        from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_entry_v1 import (
            current_paper_slot_capital_v1,
        )

        current = session()
        if current.slot != market.slot:
            raise ValueError("CARD_PAPER_BUDGET_FOREIGN_SLOT")
        capital, portfolio, cap = current_paper_slot_capital_v1(
            current.accounting, current.budget, market
        )
        snapshot = dict(
            accounting=current.accounting.to_durable_dict(),
            entry_budget=current.budget.to_dict_v1(),
            marked_portfolio=portfolio.to_dict(),
            cap_usd=str(cap),
            usd_per_usdc=str(market.usd_per_usdc),
        )
        available = max(Decimal(0), min(cap, portfolio.equity))
        return dict(
            status="BOUND",
            lane_id=current.slot.lane_id,
            instrument_id=current.bound.instrument_id,
            currency="USDC",
            observed_unix=now,
            available_amount=str(available / market.usd_per_usdc),
            available_for_new_entry=str(available / market.usd_per_usdc)
            if capital.position is None
            else "0",
            reserved_amount=None,
            reservation_scope="PAPER_ACCOUNTING_WITHOUT_PORTFOLIO_HOLD",
            owner="bounded_peaktrade_system_composition_v1.current_paper_slot_capital_v1",
            original_snapshot=snapshot,
            source_digest=canonical_digest_v1(snapshot),
        )

    return capture


def default_shadow_card_source_v1(*, repo, capture_root=None):
    """Lazy public-only source; the existing Shadow start gate remains in front.

    Reuses the existing public Paper source port and source validators. It does
    not extend I17's own network allowlist or access private account data.
    """
    from src.ops.bounded_peaktrade_system_composition_v1.paper_market_liquidity_v1 import (
        load_paper_liquidity_policy_v1,
        retain_public_paper_sources_v1,
    )
    from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
        collect_zkp_paper_market_v1,
        zkp_public_queries_v1,
    )

    def capture(*, slot, capture_id, clock):
        from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
            FullCoreProductiveReadOnlyGetTransportV1,
        )

        policy = load_paper_liquidity_policy_v1(repo)
        transport = FullCoreProductiveReadOnlyGetTransportV1(
            timeout_seconds=6,
            max_request_count=len(zkp_public_queries_v1(policy.adv_days, slot=slot)),
        )
        output = (
            None
            if capture_root is None
            else Path(capture_root) / sha256(capture_id.encode()).hexdigest()
        )
        with retain_public_paper_sources_v1(output) as retain:
            return collect_zkp_paper_market_v1(
                transport,
                policy=policy,
                capture_id=capture_id,
                clock=clock,
                slot=slot,
                retain=retain,
            )

    return capture


def snapshot_transport_v1(market):
    """The existing normalizer reads exactly this update, without a second GET."""

    class SnapshotTransport:
        def fetch_mark_price(self, *, venue_instrument_id, inst_type):
            if venue_instrument_id != market.slot.native_id or inst_type != "FUTURES":
                raise ValueError("CARD_NORMALIZER_INSTRUMENT_MISMATCH")
            return market.source_observations["mark"]

        def fetch_ticker(self, *, venue_instrument_id):
            if venue_instrument_id != market.slot.native_id:
                raise ValueError("CARD_NORMALIZER_INSTRUMENT_MISMATCH")
            return market.source_observations["ticker"]

    return SnapshotTransport()
