"""Scoped Safety release and original S6 continuation for the offline feed profile."""

from contextlib import contextmanager
from dataclasses import asdict, replace
from datetime import datetime
import fcntl
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    atomic_write_json,
    canonical_json_dumps,
    canonical_json_text,
)
from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_governed_continuous_cycle_orchestrator_v1 as s6,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    cursor_last_accepted_c1_venue_event_time_v1,
    load_current_productive_c1_cursor_or_reason_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    build_s8_occupied_lane_pairs_v1,
    make_n1_occupied_lane_s5_runner_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
    map_injected_candles_payload_to_current_productive_c1_observation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
)
from src.ops.full_core_live_path_composition_root_v1.durable_filegate_join_v1 import (
    read_durable_filegate_join_evidence_v1,
)
from src.ops.offline_public_feed_account_reconciliation_v1 import (
    _inspect_stopped_account,
    capture_offline_feed_account_reconciliation_v1,
)
from src.ops.offline_filegate_witness_v1 import OfflineFilegateWitnessV1
from src.ops.offline_public_feed_recovery_v1 import (
    OfflinePublicFeedRecoveryError,
    OfflinePublicFeedRecoveryV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    default_store_paths_v1,
    load_all_facts_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.event_sequence_persistence_v1 import (
    load_event_sequence_state_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.freshness_v1 import (
    classify_live_mark_price_freshness_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
    require_budget_head_read_only_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    EVIDENCE_FILENAME,
    MANIFEST_FILENAME,
    PORTFOLIO_STATE_FILENAME,
)
from src.ops.productive_reconciliation_runtime_binding_v1.persistence_v1 import verify_manifest
from src.risk_layer.kill_switch.core import KillSwitch
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState

MANDATE_SCHEMA = "offline_public_feed_restart_mandate.v1"
RECEIPT_SCHEMA = "offline_public_feed_restart_release.v1"


class OfflinePublicFeedRestartV1:
    """Explicit one-cycle R01 profile with a provisioned, scoped Safety mandate."""

    def __init__(
        self,
        repair: OfflinePublicFeedRecoveryV1,
        *,
        authority_key: bytes,
        witness_directory: Path | None = None,
    ):
        if type(repair) is not OfflinePublicFeedRecoveryV1:
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_BOUND_REPAIR_REQUIRED")
        if type(authority_key) is not bytes or len(authority_key) < 32:
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_AUTHORITY_KEY_REQUIRED")
        self.repair = repair
        self._key = authority_key
        self._witness = (
            None
            if witness_directory is None
            else OfflineFilegateWitnessV1(
                directory=witness_directory,
                state_path=repair.incident.state_path,
                key=hmac.digest(authority_key, b"offline-filegate-witness.v1", "sha256"),
            )
        )

    @contextmanager
    def _writer(self):
        self.repair._require_scope()
        root = self.repair.incident.root
        lock = root / "offline-feed-safety.lock"
        filegate = self.repair.incident.state_path
        if any(
            path.resolve() != path
            for path in (lock, root / "backups", filegate.with_suffix(".json.tmp"))
        ):
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_WRITER_SCOPE_UNPROVEN")
        with lock.open("a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            self.repair._require_scope()
            yield

    @contextmanager
    def _resume_lock(self):
        self.repair._require_scope()
        lock = self.repair.incident.root / "offline-feed-resume.lock"
        if lock.resolve() != lock or (lock.exists() and not lock.is_file()):
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_WRITER_SCOPE_UNPROVEN")
        with lock.open("a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            yield

    def _mac(self, body):
        return hmac.digest(self._key, canonical_json_dumps(body).encode(), "sha256").hex()

    def _verified_body(self, record, *, schema):
        try:
            body = record["body"]
            if (
                set(record) == {"body", "signature"}
                and body["schema"] == schema
                and (hmac.compare_digest(record["signature"], self._mac(body)))
            ):
                return body
        except (KeyError, TypeError, ValueError):
            pass
        raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_AUTHORITY_INVALID")

    def _read_active(self, mandate):
        path = self.repair.incident.state_path
        raw = path.read_bytes()
        current = read_durable_filegate_join_evidence_v1(state_path=str(path))
        if (
            path.read_bytes() != raw
            or current.evidence_status != "TRUSTED_PRESENT"
            or current.state_name != "ACTIVE"
            or current.blocked is not False
            or current.boolean_reader_blocked is not False
            or os.environ.get("PEAK_KILL_SWITCH") == "1"
        ):
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_ACTIVE_UNPROVEN")
        self.repair._require_scope()
        release = self._verified_body(
            json.loads(raw).get("offline_recovery_release"), schema=RECEIPT_SCHEMA
        )
        if (
            release["mandate_sha256"] != fact_digest(mandate)
            or release["account_evidence"]["feed_binding"] != self.repair.incident.binding()
        ):
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_RELEASE_BINDING_CHANGED")
        if self._witness is not None:
            self._witness.require_match_v1(raw, state="ACTIVE")
        return release, sha256(raw).hexdigest()

    def initialize_witness_v1(self):
        """Provision once while the exact original stop can still be proved."""
        if self._witness is None:
            raise OfflinePublicFeedRecoveryError("FILEGATE_WITNESS_REQUIRED")
        with self._writer():
            self.repair._require_stop()
            raw = self.repair.incident.state_path.read_bytes()
            if sha256(raw).hexdigest() != self.repair.incident.filegate_sha256:
                raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_STOP_CHANGED_OR_UNPROVEN")
            self._witness.bootstrap_v1(raw)
            self._witness.require_match_v1(raw, state="KILLED")

    def _require_stop(self):
        self.repair._require_stop()
        raw = self.repair.incident.state_path.read_bytes()
        if sha256(raw).hexdigest() != self.repair.incident.filegate_sha256:
            raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_STOP_CHANGED_OR_UNPROVEN")
        if self._witness is not None:
            self._witness.require_match_v1(raw, state="KILLED")
        return raw

    def observe_filegate_integrity_v1(self):
        """Fence missing, contradictory or rolled-back state with a new original kill."""
        if self._witness is None:
            raise OfflinePublicFeedRecoveryError("FILEGATE_WITNESS_REQUIRED")
        with self._writer():
            path = self.repair.incident.state_path
            raw = path.read_bytes() if path.is_file() else None
            evidence = read_durable_filegate_join_evidence_v1(state_path=str(path))
            if raw is not None and path.read_bytes() != raw:
                raise OfflinePublicFeedRecoveryError("FILEGATE_OBSERVATION_CHANGED")
            anchored = False
            try:
                head = self._witness.read_v1()
                anchored = (
                    raw is not None
                    and evidence.evidence_status == "TRUSTED_PRESENT"
                    and evidence.state_name == head["state"]
                    and sha256(raw).hexdigest() == head["filegate_sha256"]
                )
            except OfflinePublicFeedRecoveryError:
                head = None
            if anchored:
                return {
                    "status": "STOP_CONFIRMED" if evidence.blocked else "ACTIVE_HEAD_CONFIRMED",
                    "filegate_sha256": head["filegate_sha256"],
                    "witness_generation": head["generation"],
                    "stop_reason": json.loads(raw).get("trigger_reason")
                    if evidence.blocked
                    else None,
                }
            if evidence.evidence_status == "TRUSTED_PRESENT" and evidence.blocked:
                # An original stop from another writer may be newer. Preserve it.
                return {"status": "BLOCKED_UNANCHORED", "reason": "FILEGATE_STOP_NOT_WITNESSED"}
            if (raw is None and path.exists()) or (raw is not None and path.read_bytes() != raw):
                raise OfflinePublicFeedRecoveryError("FILEGATE_OBSERVATION_CHANGED")
            reason = "FILEGATE_INTEGRITY_UNPROVEN"
            self._kill_locked(reason)
            return {
                "status": "BLOCKED_INTEGRITY_KILL",
                "reason": reason,
                "filegate_sha256": self._read_kill(reason),
                "previous_witness_generation": None if head is None else head["generation"],
            }

    def record_kill_v1(self, *, reason: str) -> str:
        """The isolated Safety entry publishes a new revision even when already stopped."""
        if type(reason) is not str or not reason or reason != reason.strip():
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_KILL_REASON_REQUIRED")
        with self._writer():
            self._kill_locked(reason)
            return self._read_kill(reason)

    def _read_kill(self, reason):
        path = self.repair.incident.state_path
        raw = path.read_bytes()
        evidence = read_durable_filegate_join_evidence_v1(state_path=str(path))
        if (
            evidence.evidence_status != "TRUSTED_PRESENT"
            or evidence.state_name != "KILLED"
            or evidence.blocked is not True
            or evidence.boolean_reader_blocked is not True
            or json.loads(raw)["trigger_reason"] != reason
            or path.read_bytes() != raw
        ):
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_KILL_READBACK_UNPROVEN")
        return sha256(raw).hexdigest()

    def inspect_stopped_account_v1(self, *, host, bound, stop_sha256):
        """Reconcile the bound account under the witnessed stop, including unresolved orders."""
        if self._witness is None:
            raise OfflinePublicFeedRecoveryError("FILEGATE_WITNESS_REQUIRED")
        path = self.repair.incident.state_path

        def require_stop():
            self.repair._require_scope()
            raw = path.read_bytes()
            evidence = read_durable_filegate_join_evidence_v1(state_path=str(path))
            if (
                evidence.evidence_status != "TRUSTED_PRESENT"
                or evidence.state_name != "KILLED"
                or evidence.blocked is not True
                or evidence.boolean_reader_blocked is not True
                or sha256(raw).hexdigest() != stop_sha256
                or path.read_bytes() != raw
            ):
                raise OfflinePublicFeedRecoveryError("FILEGATE_OBSERVATION_STOP_CHANGED")
            self._witness.require_match_v1(raw, state="KILLED")

        require_stop()
        return _inspect_stopped_account(
            self.repair.incident,
            host=host,
            bindings={"LANE_1": bound},
            require_stop=require_stop,
        )

    def _kill_locked(self, reason):
        path = self.repair.incident.state_path
        with self._staged_original_store() as store:
            store.save(KillSwitchState.KILLED, killed_at=self.repair._now(), trigger_reason=reason)
            killed = store.load()
        if killed is None or killed.get("state") != "KILLED":
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_ORIGINAL_KILL_UNPROVEN")
        payload = {**killed, "offline_kill_id": uuid4().hex}
        if self._witness is not None:
            try:
                self._witness.publish_v1(payload)
            except (OSError, OfflinePublicFeedRecoveryError):
                # KILL has priority even when the witness is unavailable.
                pass
        atomic_write_json(path=path, payload=payload)

    @contextmanager
    def _staged_original_store(self):
        # The isolated writer lock covers the candidate and its publication.
        with TemporaryDirectory(prefix=".feed-safety-", dir=self.repair.incident.root) as root:
            yield StatePersistence(str(Path(root) / "state.json"))

    def _scope(self, host, bound, authorization):
        incident = self.repair.incident
        if type(host) is not PortfolioBudgetHostV1 or host.closed:
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_HOST_SCOPE_UNPROVEN")
        pairs = build_s8_occupied_lane_pairs_v1(
            lane_state_root=incident.root / "lanes", bound=bound
        )
        cursor_root = Path(pairs["LANE_1"][0].lane_state_root)
        cursor_path = cursor_root / CURSOR_FILENAME
        if (
            type(authorization) is not s6.CurrentProductiveGovernedContinuousCycleRunAuthorizationV1
            or authorization.max_cycles_per_run != 1
            or authorization.native_id != bound.venue_native_id
            or authorization.native_id != incident.instrument.venue_native_id
            or bound.instrument_id != incident.instrument.canonical_instrument_id
            or host.root != incident.root / "host"
            or host.session_id != incident.session_id
            or host.execution_environment != "INTERNAL_SIMULATED_EXECUTION"
            or cursor_path.resolve() != cursor_path
            or not cursor_path.is_file()
        ):
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_HOST_SCOPE_UNPROVEN")
        s6._validate_authorization(authorization)
        return pairs, cursor_root, cursor_path

    def _cursor(self, root, *, bound):
        cursor, _ = load_current_productive_c1_cursor_or_reason_v1(root)
        if (
            cursor is None
            or cursor.get("instrument_id") != bound.instrument_id
            or cursor.get("venue_native_id") != bound.venue_native_id
        ):
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_CURSOR_UNPROVEN")
        return cursor_last_accepted_c1_venue_event_time_v1(cursor)

    def _require_mandate(self, mandate, *, host, bound, authorization, cursor_path):
        body = self._verified_body(mandate, schema=MANDATE_SCHEMA)
        expected = {
            "schema": MANDATE_SCHEMA,
            "incident": self.repair.incident.binding(),
            "environment": host.execution_environment,
            "host_root": str(host.root),
            "account": host.expected_account_identity,
            "repository_sha": host.repository_sha,
            "selected_instrument": bound.to_dict(),
            "authorization": asdict(authorization),
            "cursor_path": str(cursor_path),
        }
        if set(body) != {*expected, "cursor_sha256", "expires_at"} or any(
            body.get(key) != value for key, value in expected.items()
        ):
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_MANDATE_SCOPE_CHANGED")
        return body

    def _require_fresh(self, approval, account):
        now = self.repair._now()
        self._require_approval_time(approval, now=now)
        captured = datetime.fromisoformat(account["feed_mark_captured_at"])
        if (
            not 0
            <= now.timestamp() - account["observed_at_unix"]
            <= account["account_inventory_max_age_seconds"]
            or not 0 <= now.timestamp() - account["account_inventory_completed_unix"]
            or not all(
                classify_live_mark_price_freshness_v1(age_seconds=age).publishable
                for age in (
                    now.timestamp() - captured.timestamp(),
                    now.timestamp() - account["feed_mark_event_ms"] / 1000,
                )
            )
        ):
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_EVIDENCE_EXPIRED")

    def _require_approval_time(self, approval, *, now):
        expires = datetime.fromisoformat(approval["expires_at"])
        if expires.utcoffset() is None or now >= expires:
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_EVIDENCE_EXPIRED")

    def _require_original_sources(self, host, account):
        root = host.root / "reconciliation"
        manifest = root / MANIFEST_FILENAME
        if (
            any(
                path.resolve() != path
                for path in (manifest, root / PORTFOLIO_STATE_FILENAME, root / EVIDENCE_FILENAME)
            )
            or sha256(manifest.read_bytes()).hexdigest()
            != account["persisted_portfolio_manifest_sha256"]
        ):
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_PORTFOLIO_CHANGED")
        verify_manifest(root)
        require_budget_head_read_only_v1(
            host.root / "owner",
            account_identity=account["account"],
            expected_digest=account["durable_budget_head"],
        )
        incident = self.repair.incident
        sequence = load_event_sequence_state_v1(incident.fact_root)
        if sequence.last_event_id_by_stream.get(
            incident.mark_stream
        ) != f"{incident.mark_stream}:{account['feed_mark_row_sha256']}" or not any(
            fact_digest(fact) == account["feed_mark_fact_sha256"]
            for fact in load_all_facts_v1(default_store_paths_v1(incident.fact_root))
        ):
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_ORIGINAL_MARK_CHANGED")

    def activate_v1(self, *, host, bound, authorization, mandate):
        """Run the independent checks and consume the mandate in the original writer."""
        _, cursor_root, cursor_path = self._scope(host, bound, authorization)
        approval = self._require_mandate(
            mandate, host=host, bound=bound, authorization=authorization, cursor_path=cursor_path
        )
        path = self.repair.incident.state_path
        with self._writer():
            if json.loads(path.read_bytes()).get("state") == "ACTIVE":
                return self._read_active(mandate)[0]
            self._require_stop()
            self._require_approval_time(approval, now=self.repair._now())
            if (
                sha256(cursor_path.read_bytes()).hexdigest() != approval["cursor_sha256"]
                or self._cursor(cursor_root, bound=bound) != authorization.expected_cursor_floor
            ):
                raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_CURSOR_CHANGED")

        account = capture_offline_feed_account_reconciliation_v1(
            self.repair, host=host, bindings={"LANE_1": bound}
        )
        with self._writer():
            self._require_stop()
            self._require_fresh(approval, account)
            self._require_original_sources(host, account)
            if (
                sha256(cursor_path.read_bytes()).hexdigest() != approval["cursor_sha256"]
                or self._cursor(cursor_root, bound=bound) != authorization.expected_cursor_floor
            ):
                raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_CURSOR_CHANGED")
            if (
                host.owner.local_commitment_readback_v1().generation_digest
                != account["local_commitment_generation"]
            ):
                raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_COMMITMENTS_CHANGED")
            body = {
                "schema": RECEIPT_SCHEMA,
                "mandate_sha256": fact_digest(mandate),
                "account_evidence": account,
                "activated_at": self.repair._now().isoformat(),
            }
            stopped = self._require_stop()
            with self._staged_original_store() as store:
                store.state_file.write_bytes(stopped)
                # The original writer stages RECOVERING while FILEGATE stays KILLED.
                switch = KillSwitch({"recovery_cooldown_seconds": 0}, persistence=store)
                if (
                    not switch.request_recovery("offline-feed-mandate")
                    or not switch.complete_recovery()
                ):
                    raise OfflinePublicFeedRecoveryError(
                        "OFFLINE_RESTART_ORIGINAL_TRANSITION_DENIED"
                    )
                active = store.load()
            if active is None or active.get("state") != "ACTIVE":
                raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_ORIGINAL_TRANSITION_DENIED")
            self._require_stop()
            payload = {
                **active,
                "offline_recovery_release": {"body": body, "signature": self._mac(body)},
            }
            if self._witness is not None:
                # A crash between the stores leaves the original consumer blocked.
                self._witness.publish_v1(payload)
                if path.read_bytes() != stopped:
                    raise OfflinePublicFeedRecoveryError("FEED_RECOVERY_STOP_CHANGED_OR_UNPROVEN")
                self._witness.require_match_v1(
                    canonical_json_text(payload).encode(), state="ACTIVE"
                )
            atomic_write_json(path=path, payload=payload)
            return self._read_active(mandate)[0]

    def resume_v1(self, *, host, bound, authorization, mandate, observation, g17_producers):
        """Admit one finalized C1 at the original host and cold-read its durable result."""
        pairs, cursor_root, cursor_path = self._scope(host, bound, authorization)
        approval = self._require_mandate(
            mandate, host=host, bound=bound, authorization=authorization, cursor_path=cursor_path
        )
        with self._resume_lock():
            release, active_revision = self._read_active(mandate)
            account = release["account_evidence"]
            evidence_root = self.repair.incident.root / "host-restart" / release["mandate_sha256"]
            ledger = evidence_root / s6.LEDGER_FILENAME
            if ledger.resolve() != ledger:
                raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_HOST_LEDGER_SCOPE_UNPROVEN")
            try:
                if ledger.is_file():
                    result = self._read_host_result(ledger, cursor_root, bound, authorization)
                    self._read_active(mandate)
                    return result
                self._require_fresh(approval, account)
                if (
                    sha256(cursor_path.read_bytes()).hexdigest() != approval["cursor_sha256"]
                    or self._cursor(cursor_root, bound=bound) != authorization.expected_cursor_floor
                ):
                    raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_CURSOR_CHANGED")
                observation = self._require_observation(observation, account, authorization)
                runner = make_n1_occupied_lane_s5_runner_v1(
                    composed_pairs=pairs,
                    g17_producers=g17_producers,
                    cycle_id_prefix_base="offline-public-feed-restart",
                )

                def check_admission(_cycle):
                    if self._read_active(mandate)[1] != active_revision:
                        raise OfflinePublicFeedRecoveryError(
                            "OFFLINE_RESTART_ACTIVE_REVISION_CHANGED"
                        )
                    self._require_fresh(approval, account)
                    self._require_original_sources(host, account)

                def guarded_runner(**kwargs):
                    check_admission(1)
                    return runner(**kwargs)

                result = s6.run_current_productive_governed_continuous_cycle_run_v1(
                    authorization=authorization,
                    origin_main_sha=host.repository_sha,
                    cursor_store_root=cursor_root,
                    lock_root=evidence_root / "lock",
                    evidence_root=evidence_root,
                    observation_source=s6.ScriptedContinuousObservationSourceV1([observation]),
                    s5_runner=guarded_runner,
                    iteration_authority_gate_v1=check_admission,
                )
                check_admission(1)
                if result.disposition not in {
                    s6.DISPOSITION_MAX_CYCLES,
                    s6.DISPOSITION_PRE_EXTERNAL_EFFECT,
                }:
                    raise OfflinePublicFeedRecoveryError(
                        "OFFLINE_RESTART_HOST_DENIED:" + result.reason_code
                    )
                return self._read_host_result(ledger, cursor_root, bound, authorization)
            except Exception:
                # Preserve a newer independent veto if it is already on disk.
                with self._writer():
                    path = self.repair.incident.state_path
                    if path.is_file() and sha256(path.read_bytes()).hexdigest() == active_revision:
                        self._kill_locked("OFFLINE_RESTART_ADMISSION_FAILED")
                raise

    def recover_and_resume_v1(
        self, *, runtime, host, bound, authorization, mandate, observation, g17_producers
    ):
        """The automatic R01 entry point for the explicitly provisioned offline profile."""
        _, _, cursor_path = self._scope(host, bound, authorization)
        approval = self._require_mandate(
            mandate, host=host, bound=bound, authorization=authorization, cursor_path=cursor_path
        )
        with self._writer():
            needs_repair = (
                json.loads(self.repair.incident.state_path.read_bytes())["state"] == "KILLED"
            )
            if needs_repair:
                self._require_stop()
                self._require_approval_time(approval, now=self.repair._now())
        if needs_repair:
            self.repair.repair_and_observe_v1(runtime)
        release = self.activate_v1(
            host=host, bound=bound, authorization=authorization, mandate=mandate
        )
        if (
            type(observation) is s6.InjectedContinuousObservationV1
            and not observation.mark_acquired_at_utc
        ):
            observation = replace(
                observation,
                mark_acquired_at_utc=release["account_evidence"]["feed_mark_captured_at"],
            )
        return self.resume_v1(
            host=host,
            bound=bound,
            authorization=authorization,
            mandate=mandate,
            observation=observation,
            g17_producers=g17_producers,
        )

    def _require_observation(self, observation, account, authorization):
        if type(observation) is not s6.InjectedContinuousObservationV1:
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_ORIGINAL_OBSERVATION_REQUIRED")
        # Detach the already-bound inputs so a caller cannot alter them during admission.
        observation = s6.InjectedContinuousObservationV1(
            **json.loads(canonical_json_dumps(asdict(observation)))
        )
        if (
            not observation.mark_price_payload
            or observation.mark_price_payload.get("code") != "0"
            or not isinstance(rows := observation.mark_price_payload.get("data"), list)
            or len(rows) != 1
            or fact_digest(rows[0]) != account["feed_mark_row_sha256"]
            or observation.mark_acquired_at_utc != account["feed_mark_captured_at"]
            or fact_digest(observation.occupancy_payloads) != account["occupancy_payload_sha256"]
            or observation.candles_payload.get("instId") != authorization.native_id
        ):
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_ORIGINAL_OBSERVATION_MISMATCH")
        mapped = map_injected_candles_payload_to_current_productive_c1_observation_v1(
            owner_go=s6.EH_SEAM_OWNER_GO,
            candles_payload=observation.candles_payload,
            native_id=authorization.native_id,
        )
        mark_event = account["feed_mark_event_ms"] / 1000
        latest_closed_c1 = (int(mark_event) // 60 - 1) * 60
        if (
            mapped.observation is None
            or mapped.observation.venue_event_time != authorization.expected_cursor_floor + 60
            or mapped.observation.venue_event_time != latest_closed_c1
        ):
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_NEXT_FINALIZED_C1_UNPROVEN")
        return observation

    def _read_host_result(self, ledger, cursor_root, bound, authorization):
        result = json.loads(ledger.read_bytes())
        floor = self._cursor(cursor_root, bound=bound)
        if (
            result["state"] != s6.STATE_COMPLETED
            or result["s5_invoke_count"] != 1
            or len(result["consumed_instance_ids"]) != 1
            or result["native_id"] != bound.venue_native_id
            or result["expected_cursor_floor"] != authorization.expected_cursor_floor
            or result["last_accepted_c1"] != floor
            or floor != authorization.expected_cursor_floor + 60
            or result.get("completed_cursor_sha256")
            != sha256((cursor_root / CURSOR_FILENAME).read_bytes()).hexdigest()
            or result["POST_COUNT"] != "0"
            or result["PERMIT_CREATED"] != "false"
            or result["EXTERNAL_EFFECT_COUNT"] != "0"
        ):
            raise OfflinePublicFeedRecoveryError("OFFLINE_RESTART_HOST_READBACK_UNPROVEN")
        return {
            "run_id": result["run_id"],
            "consumed_cycle_id": result["consumed_instance_ids"][0],
            "cursor_before": authorization.expected_cursor_floor,
            "cursor_after": floor,
            "ledger_sha256": sha256(ledger.read_bytes()).hexdigest(),
        }
