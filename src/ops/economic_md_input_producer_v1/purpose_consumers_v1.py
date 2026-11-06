"""Offline purpose-specific data consumers; no strategy/risk/execution authority."""

from dataclasses import dataclass, asdict, replace
from decimal import Decimal
from pathlib import Path

from src.ops.economic_md_input_producer_v1.purpose_admission_v1 import (
    PublicFactPurposePolicyV1,
    admit_public_facts_for_purpose_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    default_store_paths_v1,
    load_all_facts_v1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1

CONSUMERS = {
    "RANKING": "PublicRuntimeEconomicMdPublicSourceV1",
    "TRADING": "occupied_n1_public_c1_v1",
    "LIQUIDITY": "liquidity_public_input_v1",
    "OUTCOME": "offline_o4_public_input_v1",
    "RESEARCH": "offline_research_public_returns_v1",
}


@dataclass(frozen=True)
class PurposeBoundPublicFactSourceV1:
    store_root: str
    policy: PublicFactPurposePolicyV1
    expected_price_kind: str
    expected_volume_unit: str
    as_of_ms: int
    expected_interval_ms: int | None

    def profile_v1(self):
        if type(self.policy) is not PublicFactPurposePolicyV1:
            raise ValueError("DATA_PROFILE_TYPED_POLICY_REQUIRED")
        self.policy.validate_v1()
        allowed_intervals = {
            "RANKING": {60000},
            "TRADING": {60000},
            "RESEARCH": {60000, 3600000},
            "OUTCOME": {3600000},
            "LIQUIDITY": {None},
        }
        if (
            self.expected_interval_ms is not None
            and type(self.expected_interval_ms) is not int
            or self.expected_interval_ms not in allowed_intervals[self.policy.purpose]
        ):
            raise ValueError("DATA_PROFILE_INTERVAL_BINDING_REQUIRED")
        if self.policy.consumer != CONSUMERS[self.policy.purpose]:
            raise ValueError("DATA_PROFILE_CONSUMER_MISMATCH")
        if str(Path(self.store_root).resolve()) != self.store_root:
            raise ValueError("DATA_PROFILE_CANONICAL_ROOT_REQUIRED")
        if self.expected_price_kind not in {"mark_price_candle", "trade_price_candle"}:
            raise ValueError("DATA_PROFILE_PRICE_BASIS_REQUIRED")
        if self.expected_volume_unit not in {"CONTRACTS", "BASE_ASSET", "QUOTE_ASSET"}:
            raise ValueError("DATA_PROFILE_VOLUME_UNIT_REQUIRED")
        return {k: v for k, v in asdict(self).items() if k != "as_of_ms"}

    def at_v1(self, as_of_ms):
        return replace(self, as_of_ms=as_of_ms)

    def facts_v1(self, *, purpose, native_id):
        self.profile_v1()
        kinds = {row[0] for row in self.policy.allowed_sources}
        facts = load_all_facts_v1(default_store_paths_v1(Path(self.store_root)))
        selected = tuple(
            f
            for f in facts
            if f.get("fact_kind") in kinds
            and f.get("instrument", {}).get("venue_native_id") == native_id
        )
        return admit_public_facts_for_purpose_v1(
            selected,
            policy=self.policy,
            purpose=purpose,
            consumer=CONSUMERS[purpose],
            venue_native_id=native_id,
            as_of_ms=self.as_of_ms,
        )

    def ohlcv_v1(self, *, purpose, native_id, interval_ms):
        if interval_ms != self.expected_interval_ms:
            raise ValueError("DATA_PROFILE_WINDOW_MISMATCH")
        facts = self.facts_v1(purpose=purpose, native_id=native_id)
        rows = []
        for fact in facts:
            if (
                fact.get("fact_kind") != "OhlcvIntervalFactV1"
                or fact.get("interval_id") != ("PT1M" if interval_ms == 60000 else "PT1H")
                or fact.get("source_price_kind") != self.expected_price_kind
                or fact.get("volume_unit_semantics") != self.expected_volume_unit
                or str(fact.get("confirm")) != "1"
            ):
                raise ValueError("DATA_FEATURE_INTERVAL_PRICE_BASIS_OR_VOLUME_UNIT_MISMATCH")
            ts = fact.get("interval_start_ms")
            if type(ts) is not int or ts <= 0 or ts % interval_ms:
                raise ValueError("DATA_FEATURE_BAR_TIME_INVALID")
            if ts + interval_ms > self.as_of_ms:
                raise ValueError("DATA_FEATURE_FINALIZED_BAR_NOT_CLOSED_ASOF")
            prices = tuple(
                Decimal(str(fact.get(k))) for k in ("open_px", "high_px", "low_px", "close_px")
            )
            volume = Decimal(str(fact.get("volume")))
            if (
                any(not p.is_finite() or p <= 0 for p in prices)
                or not volume.is_finite()
                or volume < 0
                or prices[1] < max(prices[0], prices[3])
                or prices[2] > min(prices[0], prices[3])
                or prices[1] < prices[2]
            ):
                raise ValueError("DATA_FEATURE_OHLCV_INVALID")
            rows.append((ts, fact))
        from src.ops.peak_trade_public_market_data_runtime_v1.canonical_fact_decoder_v1 import (
            capture_order_key_v1,
            fact_capture_timestamp_v1,
        )

        rows.sort(key=lambda row: (row[0], capture_order_key_v1(fact_capture_timestamp_v1(row[1]))))
        by_start = {}
        fields = ("open_px", "high_px", "low_px", "close_px", "volume")
        for ts, fact in rows:
            prior = by_start.get(ts)
            if prior is not None and any(
                Decimal(str(prior[k])) != Decimal(str(fact[k])) for k in fields
            ):
                old_capture = capture_order_key_v1(fact_capture_timestamp_v1(prior))
                new_capture = capture_order_key_v1(fact_capture_timestamp_v1(fact))
                if old_capture == new_capture:
                    raise ValueError("DATA_FEATURE_AMBIGUOUS_REVISION")
                if not self.policy.allow_corrected or fact["quality"]["corrected"] is not True:
                    raise ValueError("DATA_FEATURE_UNDECLARED_CORRECTION")
            by_start[ts] = fact
        rows = sorted(by_start.items())
        if len(rows) < 2 or any(b[0] - a[0] != interval_ms for a, b in zip(rows, rows[1:])):
            raise ValueError("DATA_FEATURE_GAP_OR_DUPLICATE_OR_SHORT_WINDOW")
        return rows

    def trading_c1_v1(self, *, native_id):
        rows = self.ohlcv_v1(purpose="TRADING", native_id=native_id, interval_ms=60000)
        if len(rows) < 100:
            raise ValueError("DATA_TRADING_C1_100_FINALIZED_BARS_REQUIRED")
        # Unavailable volume currency fields stay empty, never synthetic values.
        payload = {
            "code": "0",
            "instId": native_id,
            "data": [
                [
                    str(ts),
                    f["open_px"],
                    f["high_px"],
                    f["low_px"],
                    f["close_px"],
                    f["volume"],
                    "",
                    "",
                    "1",
                ]
                for ts, f in rows
            ],
        }
        from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.c1_fanout_v1 import (
            extract_lane_closes_v1,
        )

        closes, last = extract_lane_closes_v1(payload)
        if len(closes) != len(rows) or last != rows[-1][0] / 1000:
            raise ValueError("DATA_TRADING_ORIGINAL_C1_PROJECTION_MISMATCH")
        return payload

    def research_returns_v1(self, *, native_id, interval_ms):
        if interval_ms not in {60000, 3600000}:
            raise ValueError("DATA_RESEARCH_INTERVAL_UNSUPPORTED")
        rows = self.ohlcv_v1(purpose="RESEARCH", native_id=native_id, interval_ms=interval_ms)
        import pandas as pd
        from src.experiments.ohlcv_returns_file import load_close_returns_from_ohlcv_frame

        frame = pd.DataFrame(
            {"close": [f["close_px"] for _, f in rows]},
            index=pd.to_datetime([ts for ts, _ in rows], unit="ms", utc=True),
        )
        return load_close_returns_from_ohlcv_frame(frame)

    def liquidity_input_v1(self, *, native_id, required_features):
        required = tuple(required_features)
        if not required or any(
            k not in {"TOP_OF_BOOK_PRICES", "DEPTH", "ADV", "SLIPPAGE"} for k in required
        ):
            raise ValueError("DATA_LIQUIDITY_REQUIRED_FEATURES_INVALID")
        facts = self.facts_v1(purpose="LIQUIDITY", native_id=native_id)
        if any(f["fact_kind"] != "BestBidAskFactV1" for f in facts):
            raise ValueError("DATA_LIQUIDITY_SOURCE_KIND_UNSUPPORTED")
        from src.ops.peak_trade_public_market_data_runtime_v1.canonical_fact_decoder_v1 import (
            fact_event_time_ms_v1,
            fact_capture_timestamp_v1,
            capture_order_key_v1,
        )

        newest = max(
            facts,
            key=lambda f: (
                fact_event_time_ms_v1(f),
                capture_order_key_v1(fact_capture_timestamp_v1(f)),
            ),
        )
        key = (
            fact_event_time_ms_v1(newest),
            capture_order_key_v1(fact_capture_timestamp_v1(newest)),
        )
        if any(
            (fact_event_time_ms_v1(f), capture_order_key_v1(fact_capture_timestamp_v1(f))) == key
            and f != newest
            for f in facts
        ):
            raise ValueError("DATA_LIQUIDITY_CONFLICTING_QUOTES")
        bid, ask = Decimal(newest["bid_px"]), Decimal(newest["ask_px"])
        if not bid.is_finite() or not ask.is_finite() or not 0 < bid <= ask:
            raise ValueError("DATA_LIQUIDITY_QUOTES_INVALID")
        missing = tuple(k for k in required if k != "TOP_OF_BOOK_PRICES")
        return {
            "status": "CANNOT_EVALUATE" if missing else "INPUT_BOUND",
            "canonical_instrument_id": self.policy.canonical_instrument_id,
            "venue_native_id": native_id,
            "bid_px": str(bid),
            "ask_px": str(ask),
            "missing_features": missing,
            "source_fact_digest": canonical_digest_v1(newest),
            "depth": None,
            "adv": None,
            "slippage": None,
            "risk_admitted": False,
        }

    def outcome_snapshot_v1(self, *, native_id, decision_event_ref, n_bars, decision_event=None):
        facts = self.facts_v1(purpose="OUTCOME", native_id=native_id)
        from src.ops.peak_trade_public_market_data_runtime_v1.o4_pt1h_bar_fact_v1 import (
            canonical_bar_envelope_to_o4_bar_element_v1,
        )
        from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_o4_n_bars_snapshot_materialization_v1 import (
            build_o4_n_bars_bar_evidence_snapshot_v1,
        )

        bars = []
        for fact in facts:
            if fact["fact_kind"] != "FinalizedPt1hO4BarFactV1":
                raise ValueError("DATA_OUTCOME_AUTHORITATIVE_O4_KIND_REQUIRED")
            bar = canonical_bar_envelope_to_o4_bar_element_v1(fact["bar"])
            from src.ops.peak_trade_public_market_data_runtime_v1.canonical_fact_decoder_v1 import (
                fact_capture_timestamp_v1,
                capture_order_key_v1,
            )

            seconds, nanos = capture_order_key_v1(fact_capture_timestamp_v1(fact))
            if (
                bar["bar_close_time"] * 1000 > self.as_of_ms
                or bar["bar_close_time"] * 1000000000
                > int(seconds.timestamp()) * 1000000000 + nanos
            ):
                raise ValueError("DATA_OUTCOME_BAR_NOT_CLOSED_AT_CAPTURE_OR_ASOF")
            if (
                bar["canonical_instrument_id"] != self.policy.canonical_instrument_id
                or bar["venue_instrument_id"] != native_id
                or bar["interval"] != "PT1H"
            ):
                raise ValueError("DATA_OUTCOME_O4_IDENTITY_OR_INTERVAL_MISMATCH")
            bars.append(bar)
        return build_o4_n_bars_bar_evidence_snapshot_v1(
            decision_event_ref=decision_event_ref,
            o4_bars=bars,
            n_bars=n_bars,
            decision_event=decision_event,
            o4_interval_id="PT1H",
        )


def purpose_profile_digest_v1(sources):
    if not isinstance(sources, dict) or not sources:
        raise ValueError("DATA_PROFILE_SOURCE_MAP_REQUIRED")
    rows = {}
    for key, source in sources.items():
        if (
            not isinstance(key, str)
            or type(source) is not PurposeBoundPublicFactSourceV1
            or type(source.policy) is not PublicFactPurposePolicyV1
            or key != source.policy.purpose
        ):
            raise ValueError("DATA_PROFILE_SOURCE_KEY_MISMATCH")
        rows[key] = source.profile_v1()
    if set(rows) != set(CONSUMERS):
        raise ValueError("DATA_PROFILE_ALL_FIVE_PURPOSES_REQUIRED")
    return canonical_digest_v1(rows)
