"""Cap-2.1 eligibility gate for Economic-MD candidates.

Reads structurally/safety eligible instrument IDs from a Cap-2.1 snapshot.
Does not re-interpret Cap-2.1 eligibility and does not add instruments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.economic_md_input_producer_v1.constants_v1 import (
    UNIVERSE_CAPABILITY_ID,
    UNIVERSE_PRODUCER_VERSION,
    UNIVERSE_SCHEMA_VERSION,
)
from src.ops.economic_md_input_producer_v1.reason_codes_v1 import EconomicMdFailureCodeV1
from src.ops.governed_futures_universe_producer_v1.models_v1 import (
    GovernedFuturesUniverseSnapshotV1,
    GovernedUniverseInstrumentV1,
)


@dataclass(frozen=True)
class Cap21EligibleInstrumentV1:
    canonical_instrument_id: str
    venue_native_id: str


@dataclass(frozen=True)
class UniverseGateResultV1:
    ok: bool
    snapshot: GovernedFuturesUniverseSnapshotV1 | None
    eligible: tuple[Cap21EligibleInstrumentV1, ...]
    failure_codes: tuple[str, ...]
    universe_snapshot_reference: Mapping[str, Any]


def load_cap21_eligible_instruments_v1(
    universe_snapshot: Mapping[str, Any] | GovernedFuturesUniverseSnapshotV1 | None,
) -> UniverseGateResultV1:
    if universe_snapshot is None:
        return UniverseGateResultV1(
            ok=False,
            snapshot=None,
            eligible=(),
            failure_codes=(EconomicMdFailureCodeV1.UNIVERSE_SNAPSHOT_MISSING.value,),
            universe_snapshot_reference={},
        )
    try:
        snapshot = (
            universe_snapshot
            if isinstance(universe_snapshot, GovernedFuturesUniverseSnapshotV1)
            else GovernedFuturesUniverseSnapshotV1.from_dict(universe_snapshot)
        )
    except Exception:  # noqa: BLE001
        return UniverseGateResultV1(
            ok=False,
            snapshot=None,
            eligible=(),
            failure_codes=(EconomicMdFailureCodeV1.UNIVERSE_SNAPSHOT_INVALID.value,),
            universe_snapshot_reference={},
        )
    failures: list[str] = []
    if snapshot.schema_version != UNIVERSE_SCHEMA_VERSION:
        failures.append(EconomicMdFailureCodeV1.UNIVERSE_SCHEMA_MISMATCH.value)
    if snapshot.capability_id != UNIVERSE_CAPABILITY_ID:
        failures.append(EconomicMdFailureCodeV1.UNIVERSE_CAPABILITY_MISMATCH.value)
    if snapshot.producer_version != UNIVERSE_PRODUCER_VERSION:
        failures.append(EconomicMdFailureCodeV1.UNIVERSE_SCHEMA_MISMATCH.value)
    recomputed = snapshot.compute_payload_digest()
    if not snapshot.payload_digest or snapshot.payload_digest != recomputed:
        failures.append(EconomicMdFailureCodeV1.UNIVERSE_SNAPSHOT_INVALID.value)
    reference = {
        "capability_id": snapshot.capability_id,
        "payload_digest": snapshot.payload_digest,
        "producer_version": snapshot.producer_version,
        "schema_version": snapshot.schema_version,
        "snapshot_id": snapshot.snapshot_id,
        "source_digest": snapshot.source_digest,
    }
    if failures:
        return UniverseGateResultV1(
            ok=False,
            snapshot=snapshot,
            eligible=(),
            failure_codes=tuple(sorted(set(failures))),
            universe_snapshot_reference=reference,
        )
    eligible: list[Cap21EligibleInstrumentV1] = []
    for row in snapshot.instruments:
        if not isinstance(row, GovernedUniverseInstrumentV1):
            continue
        if row.eligibility is not True:
            continue
        eligible.append(
            Cap21EligibleInstrumentV1(
                canonical_instrument_id=row.canonical_instrument_id,
                venue_native_id=row.venue_native_inst_id,
            )
        )
    eligible.sort(key=lambda item: (item.canonical_instrument_id, item.venue_native_id))
    return UniverseGateResultV1(
        ok=True,
        snapshot=snapshot,
        eligible=tuple(eligible),
        failure_codes=(),
        universe_snapshot_reference=reference,
    )


def assert_instrument_is_cap21_eligible_v1(
    *,
    canonical_instrument_id: str,
    eligible: tuple[Cap21EligibleInstrumentV1, ...],
) -> bool:
    allowed = {row.canonical_instrument_id for row in eligible}
    return canonical_instrument_id in allowed
