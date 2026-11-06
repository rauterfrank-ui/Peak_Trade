"""CURRENT_PRODUCTIVE G17 typed-vol mark-history checkpoint persist/restore.

Joins existing G17 mark-history persistence APIs into the CURRENT_PRODUCTIVE
Full-Core cycle. Does not bind CMC, mutate the presence gate, own
HardeningSession/SideState, schedule economic_md, or change Master-V2 formulas.

Missing file creates an empty producer and ingests JOIN-1 extracted samples.
Present file restores history/acceptance only; the volatility estimate stays
unset until a later DISTINCT ingest produces. Corrupt or incompatible payloads
fail closed with no empty-create and no rewrite.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_pt1m_mark_sample_adapter_v1 import (
    FullCoreG17Pt1mMarkIngestFieldsV1,
    g17_ingest_kwargs_from_extracted_sample_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
)
from trading.master_v2.canonical_volatility_runtime_mark_history_v1 import (
    RuntimeMarkHistoryError,
    atomic_write_history_persistence_v1,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
    TypedRuntimeProducerResultV1,
)

PACKAGE_MARKER = "FULL_CORE_G17_TYPED_VOL_MARK_HISTORY_CHECKPOINT_V1=true"
ARTIFACT_ID = "CURRENT_PRODUCTIVE_G17_TYPED_VOL_MARK_HISTORY_CHECKPOINT_V1"
CHECKPOINT_OWNER = (
    "ops.full_core_live_path_composition_root_v1."
    "current_productive_g17_typed_vol_mark_history_checkpoint_v1"
)
CHECKPOINT_FILENAME = "current_productive_g17_typed_vol_mark_history_checkpoint_v1.json"
CHECKPOINT_PER_RUN_DIRNAME = "g17_mark_history"
CMC_BINDING_PERFORMED = False
PRESENCE_GATE_MUTATED = False
HARDENING_SESSION_OWNER = False
SIDESTATE_CURSOR_OWNER = False
ECONOMIC_MD_OWNER = False
GLOBAL_SINGLETON = False
ESTIMATE_REMATERIALIZED_ON_RESTORE = False

DISPOSITION_MISSING_CREATED = "missing_created"
DISPOSITION_RESTORED = "restored"
DISPOSITION_FAIL_CLOSED_CORRUPT = "fail_closed_corrupt"
DISPOSITION_FAIL_CLOSED_IDENTITY_MISMATCH = "fail_closed_identity_mismatch"


class CurrentProductiveG17CheckpointError(ValueError):
    """Fail-closed CURRENT_PRODUCTIVE G17 checkpoint violation."""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)


@dataclass(frozen=True)
class CurrentProductiveG17CheckpointResultV1:
    disposition: str
    fail_closed: bool
    reason_code: str
    persistence_path: str
    history_digest: str
    observation_count_prices: int
    last_outcome: str
    estimate_present: bool
    producer: CanonicalVolatilityTypedRuntimeProducerScaffoldV1 | None


def current_productive_g17_checkpoint_path_v1(store_root: Path) -> Path:
    return Path(store_root) / CHECKPOINT_FILENAME


def assert_checkpoint_is_sibling_to_sidestate_cursor_v1() -> None:
    if CHECKPOINT_FILENAME == CURSOR_FILENAME:
        raise CurrentProductiveG17CheckpointError("CHECKPOINT_INSIDE_CURSOR_SCHEMA")
    if CHECKPOINT_PER_RUN_DIRNAME == "cursor":
        raise CurrentProductiveG17CheckpointError("CHECKPOINT_REUSES_CURSOR_STORE")


def _empty_fail_closed(
    *,
    disposition: str,
    reason_code: str,
    persistence_path: Path,
) -> CurrentProductiveG17CheckpointResultV1:
    return CurrentProductiveG17CheckpointResultV1(
        disposition=disposition,
        fail_closed=True,
        reason_code=reason_code,
        persistence_path=str(persistence_path),
        history_digest="",
        observation_count_prices=0,
        last_outcome="",
        estimate_present=False,
        producer=None,
    )


def _identity_tuple(
    *,
    venue: str,
    canonical_instrument_id: str,
    venue_instrument_id: str,
) -> tuple[str, str, str]:
    return (
        str(venue or "").strip(),
        str(canonical_instrument_id or "").strip(),
        str(venue_instrument_id or "").strip(),
    )


def _result_from_producer(
    producer: CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
    *,
    disposition: str,
    reason_code: str,
    last_outcome: str,
) -> CurrentProductiveG17CheckpointResultV1:
    port = producer.output_port_v1()
    return CurrentProductiveG17CheckpointResultV1(
        disposition=disposition,
        fail_closed=False,
        reason_code=reason_code,
        persistence_path=str(producer.persistence_path or ""),
        history_digest=producer.history.history_digest,
        observation_count_prices=producer.history.observation_count_prices,
        last_outcome=last_outcome,
        estimate_present=port.estimate is not None,
        producer=producer,
    )


def _ingest_extracted_samples_v1(
    producer: CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
    samples: Sequence[FullCoreG17Pt1mMarkIngestFieldsV1],
) -> str:
    last_outcome = ""
    for sample in samples:
        ingested: TypedRuntimeProducerResultV1 = producer.ingest_finalized_pt1m_mark_sample_v1(
            **g17_ingest_kwargs_from_extracted_sample_v1(sample)
        )
        last_outcome = ingested.outcome.value
    return last_outcome


def _mirror_existing_checkpoint_v1(
    producer: CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
    extra_persist_roots: Sequence[Path],
) -> None:
    primary = producer.persistence_path
    if primary is None or not Path(primary).is_file():
        return
    for root in extra_persist_roots:
        dest = current_productive_g17_checkpoint_path_v1(root)
        if dest.resolve() == Path(primary).resolve():
            continue
        atomic_write_history_persistence_v1(path=dest, host=producer.history)


def apply_current_productive_g17_typed_vol_mark_history_checkpoint_v1(
    *,
    store_root: Path,
    venue: str,
    canonical_instrument_id: str,
    venue_instrument_id: str,
    samples: Sequence[FullCoreG17Pt1mMarkIngestFieldsV1] = (),
    extra_persist_roots: Sequence[Path] = (),
) -> CurrentProductiveG17CheckpointResultV1:
    """Create or restore the G17 host, then ingest JOIN-1 extracted samples.

    Corrupt/incompatible files fail closed. Missing files create an empty host.
    Restore never rematerializes the volatility estimate.
    """
    assert_checkpoint_is_sibling_to_sidestate_cursor_v1()
    expected = _identity_tuple(
        venue=venue,
        canonical_instrument_id=canonical_instrument_id,
        venue_instrument_id=venue_instrument_id,
    )
    if not expected[0] or not expected[1] or not expected[2]:
        path = current_productive_g17_checkpoint_path_v1(store_root)
        return _empty_fail_closed(
            disposition=DISPOSITION_FAIL_CLOSED_IDENTITY_MISMATCH,
            reason_code="CHECKPOINT_BOUND_IDENTITY_INCOMPLETE",
            persistence_path=path,
        )
    path = current_productive_g17_checkpoint_path_v1(store_root)
    if path.exists() and not path.is_file():
        return _empty_fail_closed(
            disposition=DISPOSITION_FAIL_CLOSED_CORRUPT,
            reason_code="CHECKPOINT_PATH_NOT_FILE",
            persistence_path=path,
        )
    if path.is_file():
        try:
            producer = (
                CanonicalVolatilityTypedRuntimeProducerScaffoldV1.restore_from_persistence_v1(
                    persistence_path=path,
                )
            )
        except RuntimeMarkHistoryError as exc:
            return _empty_fail_closed(
                disposition=DISPOSITION_FAIL_CLOSED_CORRUPT,
                reason_code=str(exc),
                persistence_path=path,
            )
        restored = _identity_tuple(
            venue=producer.history.venue,
            canonical_instrument_id=producer.history.canonical_instrument_id,
            venue_instrument_id=producer.history.venue_instrument_id,
        )
        if restored != expected:
            return _empty_fail_closed(
                disposition=DISPOSITION_FAIL_CLOSED_IDENTITY_MISMATCH,
                reason_code="CHECKPOINT_IDENTITY_MISMATCH",
                persistence_path=path,
            )
        last_outcome = _ingest_extracted_samples_v1(producer, samples)
        _mirror_existing_checkpoint_v1(producer, extra_persist_roots)
        return _result_from_producer(
            producer,
            disposition=DISPOSITION_RESTORED,
            reason_code="CHECKPOINT_RESTORED",
            last_outcome=last_outcome,
        )
    producer = CanonicalVolatilityTypedRuntimeProducerScaffoldV1.create(
        venue=expected[0],
        canonical_instrument_id=expected[1],
        venue_instrument_id=expected[2],
        persistence_path=path,
    )
    last_outcome = _ingest_extracted_samples_v1(producer, samples)
    _mirror_existing_checkpoint_v1(producer, extra_persist_roots)
    return _result_from_producer(
        producer,
        disposition=DISPOSITION_MISSING_CREATED,
        reason_code="CHECKPOINT_MISSING_CREATED",
        last_outcome=last_outcome,
    )


__all__ = [
    "ARTIFACT_ID",
    "CHECKPOINT_FILENAME",
    "CHECKPOINT_OWNER",
    "CHECKPOINT_PER_RUN_DIRNAME",
    "CMC_BINDING_PERFORMED",
    "CurrentProductiveG17CheckpointError",
    "CurrentProductiveG17CheckpointResultV1",
    "DISPOSITION_FAIL_CLOSED_CORRUPT",
    "DISPOSITION_FAIL_CLOSED_IDENTITY_MISMATCH",
    "DISPOSITION_MISSING_CREATED",
    "DISPOSITION_RESTORED",
    "ECONOMIC_MD_OWNER",
    "ESTIMATE_REMATERIALIZED_ON_RESTORE",
    "GLOBAL_SINGLETON",
    "HARDENING_SESSION_OWNER",
    "PACKAGE_MARKER",
    "PRESENCE_GATE_MUTATED",
    "SIDESTATE_CURSOR_OWNER",
    "apply_current_productive_g17_typed_vol_mark_history_checkpoint_v1",
    "assert_checkpoint_is_sibling_to_sidestate_cursor_v1",
    "current_productive_g17_checkpoint_path_v1",
]
