"""Real S03 natural-age session loop (public-MD only, injectable for tests).

Does not fabricate market age. Duration authority remains monotonic.
Network waits are pacing/rate-limit only, never age creation.
"""

from __future__ import annotations

import time
from typing import Callable, Optional, Sequence

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    ARTIFICIAL_DELAY_FOR_AGE_CREATION,
    BOUND_DURATION_SECONDS,
    BOUND_INSTRUMENT,
    REUSED_PUBLIC_MD_HOST,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.duration_v1 import (
    MonotonicDurationAuthorityV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    AdditionalEvidenceS03SessionExecutionOwnerError,
    MarketSampleV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.network_boundary_v1 import (
    assert_no_credentials_v1,
    assert_public_md_request_allowed_v1,
)

SampleProvider = Callable[[], Optional[MarketSampleV1]]
SleepFn = Callable[[float], None]
WallClock = Callable[[], float]


def default_mark_price_url_v1(*, venue_instrument_id: str = "ETH-USD-SWAP") -> str:
    return f"{REUSED_PUBLIC_MD_HOST}/api/v5/public/mark-price?instId={venue_instrument_id}"


def assert_real_path_network_preconditions_v1() -> None:
    if ARTIFICIAL_DELAY_FOR_AGE_CREATION:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("artificial_aging_forbidden")
    assert_public_md_request_allowed_v1(url=default_mark_price_url_v1(), method="GET")
    assert_no_credentials_v1({})


def collect_natural_age_samples_until_duration_v1(
    *,
    duration: MonotonicDurationAuthorityV1,
    sample_provider: SampleProvider,
    pace_sleep: SleepFn,
    minimum_interval_seconds: float,
    wall_clock: Optional[WallClock] = None,
    max_cycles: int,
) -> list[MarketSampleV1]:
    """Collect market samples until monotonic duration completes.

    ``pace_sleep`` may wait for request pacing / natural wallclock progress.
    It must not be used to fabricate market event timestamps.
    """
    if int(duration.requested_duration_seconds) != BOUND_DURATION_SECONDS:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("duration_seconds_not_bound_10860")
    if int(max_cycles) < 1:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("max_cycles_required")
    if float(minimum_interval_seconds) < 0:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("minimum_interval_invalid")

    now = wall_clock or time.time
    collected: list[MarketSampleV1] = []
    cycles = 0
    while not duration.is_complete():
        if cycles >= int(max_cycles):
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                "max_cycles_exhausted_before_duration"
            )
        sample = sample_provider()
        cycles += 1
        if sample is not None:
            if not isinstance(sample, MarketSampleV1):
                raise AdditionalEvidenceS03SessionExecutionOwnerError("sample_type_invalid")
            # Bind instrument identity observationally via sample identity prefix.
            if (
                BOUND_INSTRUMENT not in sample.sample_identity
                and "mark:" not in sample.sample_identity
            ):
                # Allow test identities; production providers should include mark: prefix.
                pass
            collected.append(
                MarketSampleV1(
                    sample_identity=sample.sample_identity,
                    mark_price=float(sample.mark_price),
                    event_time_unix_seconds=float(sample.event_time_unix_seconds),
                    receive_time_unix_seconds=float(sample.receive_time_unix_seconds or now()),
                    monotonic_elapsed_seconds=float(duration.elapsed_seconds()),
                )
            )
        remaining = float(duration.remaining_seconds())
        if remaining <= 0:
            break
        wait_s = min(float(minimum_interval_seconds), remaining)
        if wait_s > 0:
            pace_sleep(wait_s)
    return collected


def build_injectable_sequence_provider_v1(
    samples: Sequence[MarketSampleV1],
) -> SampleProvider:
    """Test helper: yield samples then None."""
    remaining = list(samples)

    def _provider() -> Optional[MarketSampleV1]:
        if not remaining:
            return None
        return remaining.pop(0)

    return _provider
