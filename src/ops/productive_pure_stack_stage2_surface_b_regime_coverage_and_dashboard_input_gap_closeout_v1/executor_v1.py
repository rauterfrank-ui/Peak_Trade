"""Execute Surface-B regime-coverage producer against sealed ObservationPackV1.

SCOPE=REGIME_COVERAGE_EXECUTION_AND_DASHBOARD_INPUT_GAP_CLOSEOUT_ONLY
No campaign start. No INPUT_AUTHORITY / RUNTIME_IMPLEMENTED flips.
No dashboard logic or authority change. No trading-logic / orders effects.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_sta_open_inputs_closeout_v1.validator_v1 import (
    assert_provable_eth_usdt_swap_compatibility_v1,
    derive_non_invented_coverage_counts_v1,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_and_dashboard_input_gap_closeout_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1 import (
    constants_v1 as PC,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.models_v1 import (
    RegimeCoverageBarInputV1,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.producer_v1 import (
    produce_regime_coverage_labels_v1,
)


class RegimeCoverageDashboardInputGapCloseoutErrorV1(ValueError):
    """Fail-closed regime-coverage / dashboard input-gap closeout error."""


def _require_mapping(raw: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1(f"MAPPING_REQUIRED:{label}")
    return raw


def load_canonical_observation_pack_v1(repo_root: Path) -> dict[str, Any]:
    path = Path(repo_root).resolve() / C.OBSERVATION_PACK_REL
    payload = json.loads(path.read_text(encoding="utf-8"))
    pack = dict(_require_mapping(payload, label="observation_pack"))
    if pack.get("observation_pack_digest") != C.OBSERVATION_PACK_DIGEST:
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1("OBSERVATION_PACK_DIGEST_MISMATCH")
    return pack


def bars_from_observation_pack_v1(
    pack: Mapping[str, Any],
) -> tuple[RegimeCoverageBarInputV1, ...]:
    bars_raw = pack.get("bars")
    if not isinstance(bars_raw, list) or not bars_raw:
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1("BARS_REQUIRED")
    out: list[RegimeCoverageBarInputV1] = []
    for index, raw in enumerate(bars_raw):
        bar = _require_mapping(raw, label=f"bars[{index}]")
        try:
            out.append(
                RegimeCoverageBarInputV1(
                    instrument_id=str(bar["instrument_id"]),
                    event_time_epoch_s=int(bar["event_time_epoch_s"]),
                    open=float(bar["open"]),
                    high=float(bar["high"]),
                    low=float(bar["low"]),
                    close=float(bar["close"]),
                    mark_price=float(bar["mark_price"]),
                    volume=float(bar["volume"]),
                    finalized=bool(bar["finalized"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise RegimeCoverageDashboardInputGapCloseoutErrorV1(
                f"BAR_PARSE_FAILED:{index}"
            ) from exc
    if len(out) != C.BAR_COUNT:
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1("BAR_COUNT_MISMATCH")
    return tuple(out)


def build_regime_coverage_instance_v1(
    *,
    producer_digest: str,
    counts: Mapping[str, int],
    observation_count: int,
    instrument_binding: Mapping[str, Any],
    compatibility: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "versioned_producer_id": C.VERSIONED_PRODUCER_ID,
        "producer_digest": producer_digest,
        "observation_pack_digest": C.OBSERVATION_PACK_DIGEST,
        "instrument_id": C.INSTRUMENT_ID,
        "as_of_event_time_epoch_s": C.AS_OF_EVENT_TIME_EPOCH_S,
        "partition_id": C.PARTITION_ID,
        "observation_count": int(observation_count),
        "regime_coverage_counts": dict(counts),
        "threshold_authority_ref": C.THRESHOLD_AUTHORITY_REF,
        "lookback_window_authority_ref": C.LOOKBACK_WINDOW_AUTHORITY_REF,
        "taxonomy_sink_labels": list(PC.TAXONOMY_SINK_LABELS),
        "productive_emission": False,
        "regime_coverage_producer_available": False,
        "regime_coverage_status": C.REGIME_COVERAGE_STATUS,
        "canonical_binding": {
            "observation_pack_digest": C.OBSERVATION_PACK_DIGEST,
            "producer_digest": producer_digest,
            "instrument_binding": dict(instrument_binding),
            "eth_usdt_swap_compatibility": dict(compatibility),
        },
    }


def execute_regime_coverage_against_canonical_pack_v1(
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Run authorized producer + STA count derivation on sealed merged pack."""
    root = Path(repo_root).resolve()
    pack = load_canonical_observation_pack_v1(root)
    binding = _require_mapping(pack.get("instrument_binding"), label="instrument_binding")
    bars = bars_from_observation_pack_v1(pack)
    provenance = _require_mapping(pack.get("provenance"), label="provenance")
    event_range = _require_mapping(
        provenance.get("event_time_range"), label="provenance.event_time_range"
    )
    as_of = int(event_range["end_epoch_s_exclusive"])
    if as_of != C.AS_OF_EVENT_TIME_EPOCH_S:
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1("AS_OF_MISMATCH")
    instrument_id = str(provenance.get("instrument_id") or "")
    if instrument_id != C.INSTRUMENT_ID:
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1("INSTRUMENT_ID_MISMATCH")

    result = produce_regime_coverage_labels_v1(
        instrument_id=instrument_id,
        as_of_event_time_epoch_s=as_of,
        bars=bars,
    )
    if result.producer_digest != C.PRODUCER_DIGEST:
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1("PRODUCER_DIGEST_MISMATCH")
    if result.coverage_counts is not None or result.regime_coverage_instance is not None:
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1(
            "PRODUCER_MUST_LEAVE_COUNTS_INSTANCE_NULL"
        )
    if result.productive_emission is not False:
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1(
            "PRODUCTIVE_EMISSION_MUST_REMAIN_FALSE"
        )

    observations = [o.to_dict() for o in result.observations]
    counts = derive_non_invented_coverage_counts_v1(
        observations=observations,
        versioned_producer_id=C.VERSIONED_PRODUCER_ID,
        producer_digest=result.producer_digest,
        partition_id=C.PARTITION_ID,
        threshold_authority_ref=C.THRESHOLD_AUTHORITY_REF,
        lookback_authority_ref=C.LOOKBACK_WINDOW_AUTHORITY_REF,
    )
    if dict(counts) != dict(C.REGIME_COVERAGE_COUNTS):
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1("REGIME_COVERAGE_COUNTS_MISMATCH")

    triad = json.loads((root / C.TRIAD_MANIFEST_REL).read_text(encoding="utf-8"))
    compatibility = assert_provable_eth_usdt_swap_compatibility_v1(
        instrument_binding=binding,
        triad_manifest=_require_mapping(triad, label="triad_manifest"),
        candle_join_ref=C.CANDLE_JOIN_REF,
        mark_join_ref=C.MARK_JOIN_REF,
        raw_pt1m_pack_ref=C.RAW_PT1M_PACK_REF,
    )
    instance = build_regime_coverage_instance_v1(
        producer_digest=result.producer_digest,
        counts=counts,
        observation_count=len(observations),
        instrument_binding=binding,
        compatibility=compatibility,
    )
    return {
        "observation_pack_digest": C.OBSERVATION_PACK_DIGEST,
        "producer_digest": result.producer_digest,
        "versioned_producer_id": C.VERSIONED_PRODUCER_ID,
        "instrument_id": instrument_id,
        "as_of_event_time_epoch_s": as_of,
        "bar_count": len(bars),
        "observation_count": len(observations),
        "regime_coverage_counts": dict(counts),
        "regime_coverage_instance": instance,
        "canonical_binding_ok": True,
        "campaign_start": False,
        "input_authority_flip": False,
        "runtime_implemented_flip": False,
        "dashboard_logic_change": False,
        "dashboard_authority_effect": C.DASHBOARD_AUTHORITY_EFFECT,
        "trading_logic_change": False,
        "orders_testnet_live": False,
        "regime_coverage_producer_available": False,
        "regime_coverage_status": C.REGIME_COVERAGE_STATUS,
        "productive_emission": False,
    }


__all__ = [
    "RegimeCoverageDashboardInputGapCloseoutErrorV1",
    "bars_from_observation_pack_v1",
    "build_regime_coverage_instance_v1",
    "execute_regime_coverage_against_canonical_pack_v1",
    "load_canonical_observation_pack_v1",
]
