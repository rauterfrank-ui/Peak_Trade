"""CURRENT_PRODUCTIVE DK/MV2 typed-volatility hot-path join (JOIN-1 → JOIN-2).

Extracts finalized PT1M mark-price history, restores/creates the G17 producer
checkpoint, and returns the producer handle for Master-V2 replay. Does not
perform CMC bind (owned by master-v2 cycle), mutate the presence gate, or POST.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_pt1m_mark_sample_adapter_v1 import (
    ENDPOINT_HISTORY_MARK_PRICE_CANDLES,
    extract_full_core_g17_pt1m_mark_ingest_fields_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_typed_vol_mark_history_checkpoint_v1 import (
    CHECKPOINT_PER_RUN_DIRNAME,
    apply_current_productive_g17_typed_vol_mark_history_checkpoint_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.constants_v1 import (
    DEFAULT_VENUE,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
)

PACKAGE_MARKER = "FULL_CORE_G17_DK_MV2_TYPED_VOL_HOT_PATH_JOIN_V1=true"
JOIN_OWNER = (
    "ops.full_core_live_path_composition_root_v1."
    "current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1"
)
CMC_BINDING_PERFORMED = False
PRESENCE_GATE_MUTATED = False
HARDENING_SESSION_OWNER = False


class CurrentProductiveG17DkMv2HotPathJoinError(ValueError):
    """Fail-closed DK/MV2 typed-volatility hot-path join violation."""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)


@dataclass(frozen=True)
class CurrentProductiveG17DkMv2HotPathJoinResultV1:
    producer: CanonicalVolatilityTypedRuntimeProducerScaffoldV1 | None
    fail_closed: bool
    reason_code: str
    extraction_failure_codes: tuple[str, ...]
    checkpoint_disposition: str
    estimate_present: bool
    checkpoint_store_root: str
    source_endpoint: str


def current_productive_g17_dk_checkpoint_store_root_v1(evidence_store_root: Path) -> Path:
    return Path(evidence_store_root) / CHECKPOINT_PER_RUN_DIRNAME


def prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
    *,
    evidence_store_root: Path,
    bound_instrument: BoundInstrumentV1,
    mark_candles_payload: Mapping[str, Any] | None,
    receive_or_capture_timestamp: str,
) -> CurrentProductiveG17DkMv2HotPathJoinResultV1:
    """JOIN-1 extract + JOIN-2 checkpoint; producer for ``g17_typed_vol_producer``."""
    instrument_id = str(bound_instrument.instrument_id or "").strip()
    venue_native_id = str(bound_instrument.venue_native_id or "").strip() or instrument_id
    checkpoint_root = current_productive_g17_dk_checkpoint_store_root_v1(evidence_store_root)
    checkpoint_root.mkdir(parents=True, exist_ok=True)

    extracted = extract_full_core_g17_pt1m_mark_ingest_fields_v1(
        mark_candles_payload,
        venue=DEFAULT_VENUE,
        canonical_instrument_id=instrument_id,
        venue_instrument_id=venue_native_id,
        receive_or_capture_timestamp=str(receive_or_capture_timestamp),
        source_endpoint=ENDPOINT_HISTORY_MARK_PRICE_CANDLES,
    )
    if extracted.failure_codes:
        return CurrentProductiveG17DkMv2HotPathJoinResultV1(
            producer=None,
            fail_closed=True,
            reason_code="G17_MARK_SAMPLE_EXTRACTION_FAIL_CLOSED",
            extraction_failure_codes=tuple(extracted.failure_codes),
            checkpoint_disposition="",
            estimate_present=False,
            checkpoint_store_root=str(checkpoint_root),
            source_endpoint=extracted.source_endpoint,
        )

    checkpoint = apply_current_productive_g17_typed_vol_mark_history_checkpoint_v1(
        store_root=checkpoint_root,
        venue=DEFAULT_VENUE,
        canonical_instrument_id=instrument_id,
        venue_instrument_id=venue_native_id,
        samples=extracted.samples,
    )
    if checkpoint.fail_closed:
        return CurrentProductiveG17DkMv2HotPathJoinResultV1(
            producer=None,
            fail_closed=True,
            reason_code=str(checkpoint.reason_code or "G17_CHECKPOINT_FAIL_CLOSED"),
            extraction_failure_codes=(),
            checkpoint_disposition=str(checkpoint.disposition),
            estimate_present=False,
            checkpoint_store_root=str(checkpoint_root),
            source_endpoint=extracted.source_endpoint,
        )

    return CurrentProductiveG17DkMv2HotPathJoinResultV1(
        producer=checkpoint.producer,
        fail_closed=False,
        reason_code="",
        extraction_failure_codes=(),
        checkpoint_disposition=str(checkpoint.disposition),
        estimate_present=bool(checkpoint.estimate_present),
        checkpoint_store_root=str(checkpoint_root),
        source_endpoint=extracted.source_endpoint,
    )


__all__ = [
    "CMC_BINDING_PERFORMED",
    "CurrentProductiveG17DkMv2HotPathJoinError",
    "CurrentProductiveG17DkMv2HotPathJoinResultV1",
    "HARDENING_SESSION_OWNER",
    "JOIN_OWNER",
    "PACKAGE_MARKER",
    "PRESENCE_GATE_MUTATED",
    "current_productive_g17_dk_checkpoint_store_root_v1",
    "prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1",
]
