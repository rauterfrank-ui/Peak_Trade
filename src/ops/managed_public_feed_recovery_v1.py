"""Connect managed R01 to the original public session and native mark consumer."""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import os
from pathlib import Path

from src.ops.filegate_recovery_authority_v1 import attest_filegate_owner_evidence_v1
from src.ops.managed_filegate_v1 import ManagedFilegateV1
from src.ops.offline_public_feed_recovery_v1 import (
    OfflinePublicFeedIncidentV1,
    OfflinePublicFeedRecoveryError,
    OfflinePublicFeedRecoveryV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import default_store_paths_v1
from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import (
    PUBLIC_V1_MARK_PRICE_MAX_AGE_SECONDS,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest
from src.ops.peak_trade_public_market_data_runtime_v1.event_sequence_persistence_v1 import (
    SEQUENCE_STATE_FILENAME,
)


@dataclass(frozen=True)
class _ManagedIncident(OfflinePublicFeedIncidentV1):
    canonical_filegate: Path
    original_fact_root: Path

    @property
    def state_path(self) -> Path:
        return self.canonical_filegate

    @property
    def fact_root(self) -> Path:
        return self.original_fact_root

    def binding(self) -> dict:
        return {
            **super().binding(),
            "schema": "managed_public_feed_repair.v1",
            "fact_root": str(self.fact_root),
        }


class ManagedPublicFeedRecoveryV1(OfflinePublicFeedRecoveryV1):
    """Use the same reconnect and proof logic with a managed, independently read stop."""

    def __init__(
        self,
        *,
        writer,
        runtime,
        session_id,
        journal_root,
        clock=lambda: datetime.now(timezone.utc),
    ):
        if type(writer) is not ManagedFilegateV1:
            raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_MANAGED_WRITER_REQUIRED")
        self._writer = writer
        self._stop = writer.inspect_stop_v1()
        native = runtime.venue_native_id
        if (
            "R01" not in self._stop["causes"]
            or native not in self._stop["scope"]["instruments"]
            or not session_id
            or runtime.instrument_ref is None
            or runtime.instrument_ref.venue != "okx_eea"
            or not isinstance(journal_root, Path)
            or not journal_root.is_absolute()
            or journal_root.resolve() != journal_root
            or not journal_root.is_dir()
            or journal_root.stat().st_uid != os.getuid()
            or journal_root.stat().st_mode & 0o077
        ):
            raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_MANAGED_SCOPE_UNPROVEN")
        self._runtime = runtime
        folder = journal_root / (self._stop["stop_id"] + "-" + sha256(native.encode()).hexdigest())
        folder.mkdir(mode=0o700, exist_ok=True)
        super().__init__(
            _ManagedIncident(
                folder,
                session_id,
                runtime.instrument_ref,
                sha256(writer.state_path.read_bytes()).hexdigest(),
                writer.state_path,
                runtime.store_root,
            ),
            clock=clock,
        )

    def _require_scope(self) -> None:
        incident = self.incident
        paths = default_store_paths_v1(incident.fact_root)
        if (
            not incident.fact_root.is_absolute()
            or not incident.fact_root.is_dir()
            or incident.root.resolve() != incident.root
            or incident.root.stat().st_uid != os.getuid()
            or incident.root.stat().st_mode & 0o077
            or any(
                path.resolve() != path or (path.exists() and not path.is_file())
                for path in (
                    incident.state_path,
                    incident.fact_root / SEQUENCE_STATE_FILENAME,
                    paths.finalized_facts,
                    paths.provenance_index,
                    self._journal,
                    self._journal.with_suffix(".json.tmp"),
                    self._lock_path,
                )
            )
        ):
            raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_FOREIGN_STORE")

    def _require_stop(self) -> None:
        self._require_scope()
        if (
            self._writer.inspect_stop_v1() != self._stop
            or sha256(self.incident.state_path.read_bytes()).hexdigest()
            != self.incident.filegate_sha256
        ):
            raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_STOP_CHANGED_OR_UNPROVEN")

    def observe_v1(self, stop):
        if stop != self._stop:
            raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_STOP_CHANGED_OR_UNPROVEN")
        self.repair_and_observe_v1(self._runtime)
        return self.read_verified_repair_v1()

    def attest_v1(self, stop, *, key):
        return attest_managed_public_feed_scope_v1(stop=stop, recoveries=(self,), key=key)


def attest_managed_public_feed_scope_v1(*, stop, recoveries, key):
    """Sign the R01 cause only after all original instrument readers agree on the stop."""
    recoveries = tuple(recoveries)
    if not recoveries or any(
        type(owner) is not ManagedPublicFeedRecoveryV1 for owner in recoveries
    ):
        raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_CAUSE_COVERAGE_UNPROVEN")
    writer = recoveries[0]._writer
    by_native = {owner.incident.instrument.venue_native_id: owner for owner in recoveries}
    if (
        "R01" not in stop["causes"]
        or len(by_native) != len(recoveries)
        or sorted(by_native) != stop["scope"]["instruments"]
        or len({owner.incident.fact_root for owner in recoveries}) != len(recoveries)
        or any(owner._writer is not writer or owner._stop != stop for owner in recoveries)
    ):
        raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_CAUSE_COVERAGE_UNPROVEN")

    for native in stop["scope"]["instruments"]:
        owner = by_native[native]
        owner.repair_and_observe_v1(owner._runtime)
    # Recheck the earliest repair after the last reconnect, which may have
    # consumed its freshness window or crossed a newer kill.
    receipts = {native: owner.read_verified_repair_v1() for native, owner in by_native.items()}
    expires_at = min(
        receipt["mark"]["event_ms"] / 1000 + PUBLIC_V1_MARK_PRICE_MAX_AGE_SECONDS
        for receipt in receipts.values()
    )
    observed_at = max(owner._now().timestamp() for owner in recoveries)
    if observed_at >= expires_at:
        raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_SCOPE_MARK_STALE")
    if writer.inspect_stop_v1() != stop:
        raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_STOP_CHANGED_OR_UNPROVEN")
    evidence = (
        next(iter(receipts.values()))
        if len(receipts) == 1
        else {"schema": "managed_public_feed_scope_repair.v1", "receipts": receipts}
    )
    return attest_filegate_owner_evidence_v1(
        role="CAUSE",
        cause="R01",
        stop=stop,
        evidence_sha256=fact_digest(evidence),
        observed_at=observed_at,
        expires_at=expires_at,
        key=key,
    )
