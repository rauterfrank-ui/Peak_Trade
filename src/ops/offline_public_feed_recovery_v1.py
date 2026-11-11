"""Bounded public-feed repair and mark readback under an existing offline FILEGATE kill."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    atomic_write_json,
)
from src.ops.full_core_live_path_composition_root_v1.durable_filegate_join_v1 import (
    read_durable_filegate_join_evidence_v1,
)
from src.ops.gates.risk_gate import kill_switch_state_path_from_env
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    default_store_paths_v1,
    load_all_facts_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.event_sequence_persistence_v1 import (
    SEQUENCE_STATE_FILENAME,
    load_event_sequence_state_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import InstrumentRefV1, fact_digest
from src.ops.peak_trade_public_market_data_runtime_v1.freshness_v1 import (
    classify_live_mark_price_freshness_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.runtime_orchestrator_v1 import (
    PublicMarketDataRuntimeV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_binding_v1 import (
    load_ratified_eea_public_ws_binding_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_transport_v1 import PublicWsTransportV1

_SCHEMA = "offline_public_feed_repair.v1"


class OfflinePublicFeedRecoveryError(ValueError):
    pass


@dataclass(frozen=True)
class OfflinePublicFeedIncidentV1:
    """The pre-existing Safety stop and the exact public session affected by it."""

    root: Path
    session_id: str
    instrument: InstrumentRefV1
    filegate_sha256: str

    @property
    def state_path(self) -> Path:
        return self.root / "offline-public-feed-filegate.json"

    @property
    def fact_root(self) -> Path:
        return self.root / "public-feed-facts"

    @property
    def reason(self) -> str:
        return f"PUBLIC_FEED_LOSS:{self.session_id}:{self.instrument.venue_native_id}"

    @property
    def mark_stream(self) -> str:
        return json.dumps(["mark-price", self.instrument.venue_native_id], separators=(",", ":"))

    def binding(self) -> dict:
        return {
            "schema": _SCHEMA,
            "state_path": str(self.state_path),
            "filegate_sha256": self.filegate_sha256,
            "session_id": self.session_id,
            "instrument": self.instrument.to_dict(),
        }


class OfflinePublicFeedRecoveryV1:
    """Reconnect once per pinned stop. Subsequent observations reuse that session."""

    def __init__(
        self,
        incident: OfflinePublicFeedIncidentV1,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        self.incident = incident
        self._clock = clock
        self._journal = incident.root / "public-feed-repair.json"
        self._lock_path = incident.root / "public-feed-repair.lock"
        self._reconnected_transport: PublicWsTransportV1 | None = None

    def _now(self) -> datetime:
        now = self._clock()
        if type(now) is not datetime or now.utcoffset() is None:
            raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_AWARE_CLOCK_REQUIRED")
        return now

    def _require_scope(self) -> None:
        incident = self.incident
        root = incident.root
        if (
            not root.is_absolute()
            or root.resolve() != root
            or not root.is_dir()
            or root.stat().st_uid != os.getuid()
            or root.stat().st_mode & 0o077
            or kill_switch_state_path_from_env() != str(incident.state_path)
            or not incident.session_id
            or type(incident.instrument) is not InstrumentRefV1
            or incident.instrument.venue != "okx_eea"
            or not all(incident.instrument.to_dict().values())
        ):
            raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_OFFLINE_SCOPE_REQUIRED")
        paths = default_store_paths_v1(incident.fact_root)
        for path in (
            incident.state_path,
            incident.fact_root / SEQUENCE_STATE_FILENAME,
            paths.finalized_facts,
            paths.provenance_index,
            self._journal,
            self._journal.with_suffix(".json.tmp"),
            self._lock_path,
        ):
            if path.resolve() != path or (path.exists() and not path.is_file()):
                raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_FOREIGN_STORE")

    def _require_stop(self) -> None:
        self._require_scope()
        path = self.incident.state_path
        try:
            before = path.read_bytes()
            evidence = read_durable_filegate_join_evidence_v1(state_path=str(path))
            state = json.loads(before)
            if (
                hashlib.sha256(before).hexdigest() != self.incident.filegate_sha256
                or path.read_bytes() != before
                or kill_switch_state_path_from_env() != str(path)
                or os.environ.get("PEAK_KILL_SWITCH") == "1"
                or evidence.evidence_status != "TRUSTED_PRESENT"
                or evidence.state_name != "KILLED"
                or evidence.blocked is not True
                or evidence.boolean_reader_blocked is not True
                or state["trigger_reason"] != self.incident.reason
                or not state["killed_at"]
            ):
                raise ValueError("unbound feed stop")
        except (OSError, KeyError, TypeError, ValueError) as exc:
            raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_STOP_CHANGED_OR_UNPROVEN") from exc

    @contextmanager
    def _lock(self):
        self._require_stop()
        with self._lock_path.open("a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            self._require_stop()
            yield

    def _read_journal(self) -> dict | None:
        try:
            record = json.loads(self._journal.read_text(encoding="utf-8"))
            body = record["body"]
            if (
                body["binding"] != self.incident.binding()
                or body["stage"] not in {"ATTEMPT_RESERVED", "RECONNECTED", "MARK_VERIFIED"}
                or record["sha256"] != fact_digest(body)
            ):
                raise ValueError("invalid repair journal")
            return body
        except FileNotFoundError:
            return None
        except (KeyError, TypeError, ValueError) as exc:
            raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_JOURNAL_UNPROVEN") from exc

    def _save(self, body: dict) -> None:
        self._require_stop()
        atomic_write_json(path=self._journal, payload={"body": body, "sha256": fact_digest(body)})
        self._require_stop()
        if self._read_journal() != body:
            raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_JOURNAL_READBACK_MISMATCH")

    def _load_mark(self, journal: dict, facts: list, *, now: datetime) -> dict:
        incident = self.incident
        stream = incident.mark_stream
        sequence = load_event_sequence_state_v1(incident.fact_root)
        current_ms = sequence.last_event_ts_ms_by_stream.get(stream)
        current_id = sequence.last_event_id_by_stream.get(stream)
        for fact in reversed(facts):
            if fact.get("fact_kind") != "MarkPriceFactV1" or fact["instrument"] != (
                incident.instrument.to_dict()
            ):
                continue
            provenance = fact["provenance"]
            times = fact["timestamps"]
            quality = fact["quality"]
            if (
                provenance["session_id"] != incident.session_id
                or provenance["transport"] != "ws"
                or provenance["endpoint_or_channel"] != "mark-price"
                or times["source_clock_class"] != "venue_event_ms"
                or times["venue_event_time_ms"] != current_ms
                or f"{stream}:{provenance['raw_payload_digest']}" != current_id
                or any(quality[key] for key in ("missing", "stale", "duplicate", "out_of_order"))
            ):
                continue
            event = current_ms / 1000
            captured = datetime.fromisoformat(times["captured_at"])
            if (
                current_ms <= journal["previous_mark_ms"]
                or event < datetime.fromisoformat(journal["attempted_at"]).timestamp()
                or captured < datetime.fromisoformat(journal["reconnected_at"])
                or not all(
                    classify_live_mark_price_freshness_v1(age_seconds=age).publishable
                    for age in (
                        captured.timestamp() - event,
                        now.timestamp() - captured.timestamp(),
                        now.timestamp() - event,
                    )
                )
            ):
                break
            return {
                "fact_sha256": fact_digest(fact),
                "mark_px": fact["mark_px"],
                "event_ms": current_ms,
                "captured_at": times["captured_at"],
                "event_id": current_id,
            }
        raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_FRESH_BOUND_MARK_UNPROVEN")

    def repair_and_observe_v1(self, runtime: PublicMarketDataRuntimeV1) -> dict:
        """Run original reconnect and observe. A later call may poll the same repaired session."""
        incident = self.incident
        transport = runtime.ws_transport
        if (
            type(runtime) is not PublicMarketDataRuntimeV1
            or type(transport) is not PublicWsTransportV1
            or runtime.store_root != incident.fact_root
            or runtime.instrument_ref != incident.instrument
            or runtime.canonical_instrument_id != incident.instrument.canonical_instrument_id
            or runtime.venue_native_id != incident.instrument.venue_native_id
            or transport.venue_native_id != incident.instrument.venue_native_id
            or transport.binding != load_ratified_eea_public_ws_binding_v1()
            or runtime.rest_fetch_json is not None
        ):
            raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_ORIGINAL_SESSION_MISMATCH")

        with self._lock():
            journal = self._read_journal()
            paths = default_store_paths_v1(incident.fact_root)
            if journal is not None and journal["stage"] == "MARK_VERIFIED":
                return self._verify_journal(journal)
            runtime.load_durable_event_state()
            if journal is None:
                previous = runtime.event_state.last_event_ts_ms_by_stream.get(incident.mark_stream)
                if previous is None:
                    raise OfflinePublicFeedRecoveryError(
                        "FEED_RECOVERY_PREVIOUS_MARK_CURSOR_REQUIRED"
                    )
                journal = {
                    "binding": incident.binding(),
                    "stage": "ATTEMPT_RESERVED",
                    "previous_mark_ms": previous,
                    "attempted_at": self._now().isoformat(),
                }
                self._save(journal)
                transport.reconnect_resubscribe()
                journal.update(stage="RECONNECTED", reconnected_at=self._now().isoformat())
                self._save(journal)
                self._reconnected_transport = transport
            elif journal["stage"] != "RECONNECTED" or self._reconnected_transport is not transport:
                raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_ATTEMPT_NOT_REPLAYABLE")
            self._require_stop()
            before = len(load_all_facts_v1(paths))
            runtime.run_observation_cycle(
                captured_at=lambda: self._now().isoformat(),
                session_id=incident.session_id,
            )
            now = self._now()
            mark = self._load_mark(journal, load_all_facts_v1(paths)[before:], now=now)
            journal.update(stage="MARK_VERIFIED", mark=mark, verified_at=now.isoformat())
            self._save(journal)
            return self._verify_journal(journal)

    def _verify_journal(self, journal: dict | None) -> dict:
        if journal is None or journal["stage"] != "MARK_VERIFIED":
            raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_MARK_RECEIPT_MISSING")
        facts = load_all_facts_v1(default_store_paths_v1(self.incident.fact_root))
        mark = self._load_mark(journal, facts, now=self._now())
        if mark != journal["mark"]:
            raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_MARK_READBACK_MISMATCH")
        self._require_stop()
        return journal

    def read_verified_repair_v1(self) -> dict:
        """Cold-read and independently recheck mark evidence against the current stop."""
        with self._lock():
            return self._verify_journal(self._read_journal())
