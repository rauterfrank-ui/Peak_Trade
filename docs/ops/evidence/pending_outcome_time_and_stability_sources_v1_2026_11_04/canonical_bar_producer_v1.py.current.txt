"""Sole authoritative public-MD bar producer for CAPABILITY_O4."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.authority_envelope_v1 import (
    AuthoritativeOhlcvBarEnvelopeV1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.bar_state_contract_v1 import (
    BarStateContractErrorV1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    AUTHORITATIVE_BAR_PRODUCER,
    BAR_STATE_CORRECTED,
    BAR_STATE_FINALIZED,
    BAR_STATE_IN_PROGRESS,
    BAR_STATE_MISSING,
    BAR_STATE_STALE,
    CAPABILITY_ID,
    INTERVAL_PT1H,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.correction_revision_contract_v1 import (
    assert_correction_allowed_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.deduplication_contract_v1 import (
    should_advance_authoritative_state_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.finalization_contract_v1 import (
    assert_can_finalize_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.interval_contract_v1 import (
    IntervalContractErrorV1,
    bar_open_close_times_v1,
    normalize_interval_id_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.missing_stale_contract_v1 import (
    mark_missing_bar_v1,
    mark_stale_bar_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.normalized_event_path_v1 import (
    accept_normalized_public_market_event_v1,
    map_normalized_to_observation_identity_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.out_of_order_contract_v1 import (
    classify_or_reject_out_of_order_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceStateV1,
    ObservationClassification,
    initial_observation_acceptance_state_v1,
)


def _bar_key(*, instrument: str, interval: str, open_time: float) -> str:
    return f"{instrument}|{interval}|{open_time:.0f}"


@dataclass
class _MutableBarV1:
    envelope: AuthoritativeOhlcvBarEnvelopeV1
    finalized: bool = False


@dataclass
class CanonicalPublicMdBarProducerV1:
    """Authoritative bar aggregator bound to the canonical normalized event path."""

    session_id: str
    repository_sha: str
    config_digest: str
    interval: str = INTERVAL_PT1H
    acceptor_state: ObservationAcceptanceStateV1 = field(
        default_factory=initial_observation_acceptance_state_v1
    )
    _bars: dict[str, _MutableBarV1] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self.interval = normalize_interval_id_v1(self.interval)
        if not str(self.session_id).strip():
            raise ValueError("SESSION_ID_REQUIRED")
        if not str(self.repository_sha).strip():
            raise ValueError("REPOSITORY_SHA_REQUIRED")
        if not str(self.config_digest).strip():
            raise ValueError("CONFIG_DIGEST_REQUIRED")

    @property
    def producer_id(self) -> str:
        return AUTHORITATIVE_BAR_PRODUCER

    @property
    def capability_id(self) -> str:
        return CAPABILITY_ID

    def ingest_normalized_event(
        self,
        data: NormalizedPublicMarketDataV1,
        *,
        poll_attempt: Optional[int] = None,
        runtime_cycle_index: Optional[int] = None,
        allow_correction_on_finalized: bool = False,
    ) -> dict[str, Any]:
        """Ingest one normalized event through the canonical acceptor + bar contracts."""
        pre_state = self.acceptor_state
        transport_lag = max(0.0, float(data.receive_ts_unix) - float(data.event_ts_unix))
        result, _ = accept_normalized_public_market_event_v1(
            data=data,
            state=pre_state,
            poll_attempt=poll_attempt,
            runtime_cycle_index=runtime_cycle_index,
            transport_latency=transport_lag,
            commit=False,
        )
        classification = result.classification.value
        identity = map_normalized_to_observation_identity_v1(data).to_dict()
        open_time, close_time = bar_open_close_times_v1(
            event_time=float(data.event_ts_unix), interval_id=self.interval
        )
        key = _bar_key(
            instrument=data.canonical_instrument_id,
            interval=self.interval,
            open_time=open_time,
        )
        existing = self._bars.get(key)

        if classification == ObservationClassification.OUT_OF_ORDER.value:
            classify_or_reject_out_of_order_v1(
                classification=classification,
                finalized=bool(existing.finalized) if existing is not None else False,
                attempted_silent_mutation=True,
            )
            return {
                "accepted": False,
                "classification": classification,
                "bar_key": key,
                "advance": False,
            }

        if not should_advance_authoritative_state_v1(classification=classification):
            return {
                "accepted": False,
                "classification": classification,
                "bar_key": key,
                "advance": False,
            }

        _, committed_state = accept_normalized_public_market_event_v1(
            data=data,
            state=pre_state,
            poll_attempt=poll_attempt,
            runtime_cycle_index=runtime_cycle_index,
            transport_latency=transport_lag,
            commit=True,
        )
        self.acceptor_state = committed_state
        px = float(data.mark_px)

        if existing is None:
            envelope = AuthoritativeOhlcvBarEnvelopeV1(
                canonical_instrument_id=data.canonical_instrument_id,
                venue_instrument_id=data.venue_instrument_id,
                venue=data.venue,
                interval=self.interval,
                bar_open_time=open_time,
                bar_close_time=close_time,
                event_time=float(data.event_ts_unix),
                receive_time=float(data.receive_ts_unix),
                first_observation_identity=identity,
                last_observation_identity=identity,
                session_id=self.session_id,
                repository_sha=self.repository_sha,
                config_digest=self.config_digest,
                transport_lag=transport_lag,
                quality_state=BAR_STATE_IN_PROGRESS,
                finalization_state=BAR_STATE_IN_PROGRESS,
                revision=0,
                open=px,
                high=px,
                low=px,
                close=px,
                volume=0.0,
                sample_count=1,
            )
            self._bars[key] = _MutableBarV1(envelope=envelope, finalized=False)
            return {
                "accepted": True,
                "classification": classification,
                "bar_key": key,
                "advance": True,
                "envelope": envelope.to_dict(),
            }

        env = existing.envelope
        if env.canonical_instrument_id != data.canonical_instrument_id:
            raise IntervalContractErrorV1("INSTRUMENT_CROSS_CONTAMINATION")
        if env.interval != self.interval:
            raise IntervalContractErrorV1("INTERVAL_CROSS_CONTAMINATION")
        if env.venue_instrument_id != data.venue_instrument_id:
            raise IntervalContractErrorV1("VENUE_INSTRUMENT_CROSS_CONTAMINATION")

        if existing.finalized:
            if not allow_correction_on_finalized:
                raise BarStateContractErrorV1("FINALIZED_IMMUTABLE_WITHOUT_CORRECTION")
            new_rev = assert_correction_allowed_v1(
                current_state=env.finalization_state,
                current_revision=env.revision,
            )
            corrected = AuthoritativeOhlcvBarEnvelopeV1(
                canonical_instrument_id=env.canonical_instrument_id,
                venue_instrument_id=env.venue_instrument_id,
                venue=env.venue,
                interval=env.interval,
                bar_open_time=env.bar_open_time,
                bar_close_time=env.bar_close_time,
                event_time=float(data.event_ts_unix),
                receive_time=float(data.receive_ts_unix),
                first_observation_identity=dict(env.first_observation_identity),
                last_observation_identity=identity,
                session_id=env.session_id,
                repository_sha=self.repository_sha,
                config_digest=self.config_digest,
                transport_lag=transport_lag,
                quality_state=BAR_STATE_CORRECTED,
                finalization_state=BAR_STATE_CORRECTED,
                revision=new_rev,
                open=env.open,
                high=max(env.high, px),
                low=min(env.low, px),
                close=px,
                volume=env.volume,
                sample_count=env.sample_count + 1,
            )
            existing.envelope = corrected
            return {
                "accepted": True,
                "classification": classification,
                "bar_key": key,
                "advance": True,
                "corrected": True,
                "envelope": corrected.to_dict(),
            }

        updated = AuthoritativeOhlcvBarEnvelopeV1(
            canonical_instrument_id=env.canonical_instrument_id,
            venue_instrument_id=env.venue_instrument_id,
            venue=env.venue,
            interval=env.interval,
            bar_open_time=env.bar_open_time,
            bar_close_time=env.bar_close_time,
            event_time=float(data.event_ts_unix),
            receive_time=float(data.receive_ts_unix),
            first_observation_identity=dict(env.first_observation_identity),
            last_observation_identity=identity,
            session_id=env.session_id,
            repository_sha=self.repository_sha,
            config_digest=self.config_digest,
            transport_lag=transport_lag,
            quality_state=BAR_STATE_IN_PROGRESS,
            finalization_state=BAR_STATE_IN_PROGRESS,
            revision=env.revision,
            open=env.open,
            high=max(env.high, px),
            low=min(env.low, px),
            close=px,
            volume=env.volume,
            sample_count=env.sample_count + 1,
        )
        existing.envelope = updated
        return {
            "accepted": True,
            "classification": classification,
            "bar_key": key,
            "advance": True,
            "envelope": updated.to_dict(),
        }

    def finalize_bar(self, *, canonical_instrument_id: str, bar_open_time: float) -> dict[str, Any]:
        key = _bar_key(
            instrument=canonical_instrument_id,
            interval=self.interval,
            open_time=float(bar_open_time),
        )
        bar = self._bars.get(key)
        if bar is None:
            raise BarStateContractErrorV1(f"BAR_NOT_FOUND:{key}")
        assert_can_finalize_v1(
            current_state=bar.envelope.finalization_state,
            already_finalized=bar.finalized,
        )
        env = bar.envelope
        finalized = AuthoritativeOhlcvBarEnvelopeV1(
            canonical_instrument_id=env.canonical_instrument_id,
            venue_instrument_id=env.venue_instrument_id,
            venue=env.venue,
            interval=env.interval,
            bar_open_time=env.bar_open_time,
            bar_close_time=env.bar_close_time,
            event_time=env.event_time,
            receive_time=env.receive_time,
            first_observation_identity=dict(env.first_observation_identity),
            last_observation_identity=dict(env.last_observation_identity),
            session_id=env.session_id,
            repository_sha=env.repository_sha,
            config_digest=env.config_digest,
            transport_lag=env.transport_lag,
            quality_state=BAR_STATE_FINALIZED,
            finalization_state=BAR_STATE_FINALIZED,
            revision=env.revision,
            open=env.open,
            high=env.high,
            low=env.low,
            close=env.close,
            volume=env.volume,
            sample_count=env.sample_count,
        )
        bar.envelope = finalized
        bar.finalized = True
        return {"ok": True, "bar_key": key, "envelope": finalized.to_dict()}

    def mark_missing(
        self,
        *,
        canonical_instrument_id: str,
        venue_instrument_id: str,
        venue: str,
        bar_open_time: float,
        fabricate_fill: bool = False,
    ) -> dict[str, Any]:
        state = mark_missing_bar_v1(fabricate_fill=fabricate_fill)
        open_time = float(bar_open_time)
        _, close_time = bar_open_close_times_v1(event_time=open_time, interval_id=self.interval)
        key = _bar_key(
            instrument=canonical_instrument_id, interval=self.interval, open_time=open_time
        )
        # Explicit missing placeholder identity — not a fabricated live observation.
        empty_identity = {
            "venue": venue,
            "canonical_instrument_id": canonical_instrument_id,
            "venue_instrument_id": venue_instrument_id,
            "venue_event_time": open_time,
            "mark_price": None,
            "missing": True,
        }
        envelope = AuthoritativeOhlcvBarEnvelopeV1(
            canonical_instrument_id=canonical_instrument_id,
            venue_instrument_id=venue_instrument_id,
            venue=venue,
            interval=self.interval,
            bar_open_time=open_time,
            bar_close_time=close_time,
            event_time=open_time,
            receive_time=open_time,
            first_observation_identity=empty_identity,
            last_observation_identity=empty_identity,
            session_id=self.session_id,
            repository_sha=self.repository_sha,
            config_digest=self.config_digest,
            transport_lag=0.0,
            quality_state=state,
            finalization_state=state,
            revision=0,
            open=0.0,
            high=0.0,
            low=0.0,
            close=0.0,
            volume=0.0,
            sample_count=0,
        )
        self._bars[key] = _MutableBarV1(envelope=envelope, finalized=False)
        return {
            "ok": True,
            "bar_key": key,
            "state": BAR_STATE_MISSING,
            "envelope": envelope.to_dict(),
        }

    def mark_stale(self, *, bar_key: str, fabricate_live: bool = False) -> dict[str, Any]:
        state = mark_stale_bar_v1(fabricate_live=fabricate_live)
        bar = self._bars.get(bar_key)
        if bar is None:
            raise BarStateContractErrorV1(f"BAR_NOT_FOUND:{bar_key}")
        if bar.finalized:
            raise BarStateContractErrorV1("STALE_ON_FINALIZED_FORBIDDEN")
        env = bar.envelope
        stale = AuthoritativeOhlcvBarEnvelopeV1(
            canonical_instrument_id=env.canonical_instrument_id,
            venue_instrument_id=env.venue_instrument_id,
            venue=env.venue,
            interval=env.interval,
            bar_open_time=env.bar_open_time,
            bar_close_time=env.bar_close_time,
            event_time=env.event_time,
            receive_time=env.receive_time,
            first_observation_identity=dict(env.first_observation_identity),
            last_observation_identity=dict(env.last_observation_identity),
            session_id=env.session_id,
            repository_sha=env.repository_sha,
            config_digest=env.config_digest,
            transport_lag=env.transport_lag,
            quality_state=state,
            finalization_state=state,
            revision=env.revision,
            open=env.open,
            high=env.high,
            low=env.low,
            close=env.close,
            volume=env.volume,
            sample_count=env.sample_count,
        )
        bar.envelope = stale
        return {
            "ok": True,
            "bar_key": bar_key,
            "state": BAR_STATE_STALE,
            "envelope": stale.to_dict(),
        }

    def get_envelope(self, bar_key: str) -> Mapping[str, Any] | None:
        bar = self._bars.get(bar_key)
        return None if bar is None else bar.envelope.to_dict()

    def list_envelopes(self) -> list[dict[str, Any]]:
        return [b.envelope.to_dict() for b in self._bars.values()]
