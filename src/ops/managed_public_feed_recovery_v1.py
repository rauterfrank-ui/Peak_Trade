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
        receipt = self.observe_v1(stop)
        # Other causes require their own checks before the CAUSE owner can attest.
        if stop["causes"] != ["R01"] or stop["scope"]["instruments"] != [
            self.incident.instrument.venue_native_id
        ]:
            raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_CAUSE_COVERAGE_UNPROVEN")
        return attest_filegate_owner_evidence_v1(
            role="CAUSE",
            stop=stop,
            evidence_sha256=fact_digest(receipt),
            observed_at=datetime.fromisoformat(receipt["verified_at"]).timestamp(),
            expires_at=receipt["mark"]["event_ms"] / 1000 + PUBLIC_V1_MARK_PRICE_MAX_AGE_SECONDS,
            key=key,
        )
