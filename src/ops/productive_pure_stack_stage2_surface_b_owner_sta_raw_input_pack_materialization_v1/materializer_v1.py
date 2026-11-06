"""Materialize Surface-B raw input observation pack from sealed tip-proof bytes.

SCOPE=RAW_INPUT_PACK_MATERIALIZATION_ONLY
No network fetch. No campaign start. No input-authority / runtime flips.
Uses recorded Owner/STA instance values and sealed OKX tip-proof raw bytes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    digest_mapping,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.models_v1 import (
    InstrumentBindingV1,
    MarkPriceInputV1,
    ObservationPackV1,
    VenueNativeCandleInputV1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.observation_pack_v1 import (
    build_observation_pack_v1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.pt1m_finalized_ohlcv_producer_v1 import (
    produce_pt1m_finalized_ohlcv_bars_v1,
)
from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1.validator_v1 import (
    evaluate_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1,
    okx_row_is_finalized_v1,
)
from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_v1 import (
    constants_v1 as C,
)


class RawInputPackMaterializationErrorV1(ValueError):
    """Fail-closed raw input-pack materialization error."""


def compute_pack_materialization_config_digest_v1(
    *,
    dataset_id: str,
    scenario_id: str,
    seed: int,
) -> str:
    """Pack-only config digest with explicit null campaign_id (leave-null ratification)."""
    return digest_mapping(
        {
            "campaign_id": None,
            "dataset_id": dataset_id,
            "scenario_id": scenario_id,
            "seed": int(seed),
            "productive_activation": False,
            "input_authority": False,
            "runtime_implemented": False,
            "pack_materialization": True,
        }
    )


def parse_okx_finalized_candles_v1(
    rows: Sequence[Sequence[Any]],
) -> tuple[VenueNativeCandleInputV1, ...]:
    out: list[VenueNativeCandleInputV1] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Sequence) or isinstance(row, (str, bytes)):
            raise RawInputPackMaterializationErrorV1(f"CANDLE_ROW_INVALID:{index}")
        if not okx_row_is_finalized_v1(row):
            continue
        try:
            et = int(str(row[0])) // 1000
            out.append(
                VenueNativeCandleInputV1(
                    event_time_epoch_s=et,
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5]),
                    venue_finalized=True,
                    open_tip=False,
                )
            )
        except (TypeError, ValueError, IndexError) as exc:
            raise RawInputPackMaterializationErrorV1(f"CANDLE_PARSE_FAILED:{index}") from exc
    if not out:
        raise RawInputPackMaterializationErrorV1("NO_FINALIZED_CANDLES")
    return tuple(out)


def parse_okx_finalized_marks_v1(
    rows: Sequence[Sequence[Any]],
) -> tuple[MarkPriceInputV1, ...]:
    """Parse OKX mark-price candles; close (index 4) is the mark observation."""
    out: list[MarkPriceInputV1] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Sequence) or isinstance(row, (str, bytes)):
            raise RawInputPackMaterializationErrorV1(f"MARK_ROW_INVALID:{index}")
        if not okx_row_is_finalized_v1(row):
            continue
        try:
            et = int(str(row[0])) // 1000
            out.append(MarkPriceInputV1(event_time_epoch_s=et, mark_price=float(row[4])))
        except (TypeError, ValueError, IndexError) as exc:
            raise RawInputPackMaterializationErrorV1(f"MARK_PARSE_FAILED:{index}") from exc
    if not out:
        raise RawInputPackMaterializationErrorV1("NO_FINALIZED_MARKS")
    return tuple(out)


def materialize_raw_input_observation_pack_v1(
    *,
    repo_root: Path,
    candle_raw_bytes: bytes | None = None,
    mark_raw_bytes: bytes | None = None,
) -> ObservationPackV1:
    """Materialize immutable ObservationPackV1 from sealed tip-proof raw bytes.

    Does not start a campaign, flip INPUT_AUTHORITY/RUNTIME_IMPLEMENTED, or
    invent campaign_id / regime_coverage values.
    """
    root = Path(repo_root).resolve()
    if candle_raw_bytes is None:
        candle_raw_bytes = (root / C.CANDLE_RAW_REL).read_bytes()
    if mark_raw_bytes is None:
        mark_raw_bytes = (root / C.MARK_RAW_REL).read_bytes()

    tip_proof = evaluate_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1(
        candle_raw_bytes=candle_raw_bytes,
        mark_raw_bytes=mark_raw_bytes,
        binding_raw=dict(C.INSTRUMENT_BINDING),
        authorized_network_fetch=True,
    )
    if tip_proof.get("raw_source_digest") != C.RAW_SOURCE_DIGEST:
        raise RawInputPackMaterializationErrorV1("RAW_SOURCE_DIGEST_MISMATCH")
    if tip_proof.get("exclusive_tip_event_time_epoch_s") != C.EVENT_TIME_EPOCH_S:
        raise RawInputPackMaterializationErrorV1("EXCLUSIVE_TIP_MISMATCH")

    candle_payload = json.loads(candle_raw_bytes.decode("utf-8"))
    mark_payload = json.loads(mark_raw_bytes.decode("utf-8"))
    if not isinstance(candle_payload, Mapping) or not isinstance(mark_payload, Mapping):
        raise RawInputPackMaterializationErrorV1("RAW_JSON_OBJECT_REQUIRED")
    candle_rows = candle_payload.get("data")
    mark_rows = mark_payload.get("data")
    if not isinstance(candle_rows, list) or not isinstance(mark_rows, list):
        raise RawInputPackMaterializationErrorV1("DATA_LIST_REQUIRED")

    candles = parse_okx_finalized_candles_v1(candle_rows)
    marks = parse_okx_finalized_marks_v1(mark_rows)
    binding = InstrumentBindingV1(**dict(C.INSTRUMENT_BINDING))
    bars = produce_pt1m_finalized_ohlcv_bars_v1(
        binding=binding,
        dataset_id=C.DATASET_ID,
        candles=candles,
        marks=marks,
    )
    if len(bars) != C.BAR_COUNT:
        raise RawInputPackMaterializationErrorV1("BAR_COUNT_MISMATCH")
    if bars[0].event_time_epoch_s != C.FIRST_BAR_OPEN_EVENT_TIME_EPOCH_S:
        raise RawInputPackMaterializationErrorV1("FIRST_BAR_MISMATCH")
    if bars[-1].event_time_epoch_s != C.LAST_BAR_OPEN_EVENT_TIME_EPOCH_S:
        raise RawInputPackMaterializationErrorV1("LAST_BAR_MISMATCH")

    config_digest = compute_pack_materialization_config_digest_v1(
        dataset_id=C.DATASET_ID,
        scenario_id=C.SCENARIO_ID,
        seed=C.SEED,
    )
    if config_digest != C.CONFIG_DIGEST:
        raise RawInputPackMaterializationErrorV1("CONFIG_DIGEST_MISMATCH")

    pack = build_observation_pack_v1(
        binding=binding,
        bars=bars,
        dataset_id=C.DATASET_ID,
        repository_sha=C.REPOSITORY_SHA,
        config_digest=config_digest,
        raw_source_digest=C.RAW_SOURCE_DIGEST,
        ingestion_timestamp=C.INGESTION_TIMESTAMP,
        finalization_timestamp=C.FINALIZATION_TIMESTAMP,
    )
    if pack.observation_pack_digest != C.OBSERVATION_PACK_DIGEST:
        raise RawInputPackMaterializationErrorV1("OBSERVATION_PACK_DIGEST_MISMATCH")
    if pack.provenance.event_time_range.end_epoch_s_exclusive != C.EVENT_TIME_EPOCH_S:
        raise RawInputPackMaterializationErrorV1("PACK_EXCLUSIVE_TIP_MISMATCH")
    return pack


__all__ = [
    "RawInputPackMaterializationErrorV1",
    "compute_pack_materialization_config_digest_v1",
    "materialize_raw_input_observation_pack_v1",
    "parse_okx_finalized_candles_v1",
    "parse_okx_finalized_marks_v1",
]
