"""Explicit offline outcomes using the existing Pending journal as sole job owner.

Capsules and owner journals live outside purgeable lanes. No natural capture
claim, fixture promotion, scheduler, productive apply or POSITION_LIFECYCLE.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    evaluate_offline_bundle_v0,
    persist_evaluation_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_runtime_productive_host_v1 import (
    derive_productive_n_bars_evaluation_identity_v1,
)
from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    run_offline_n_bars_horizon_pipeline_v1,
    validate_n_bars_measurement_artifacts_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_outcome_evidence_ingest_v1 import (
    ingest_evaluation_bundle_into_learning_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.optimization_provenance_eligibility_v1 import (
    require_optimization_provenance_eligibility_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_scope_guard_v1 import (
    require_learning_scope_v1,
)
from src.learning.deterministic_decision_outcome_v0.outcome_evidence_provenance_bindings_v1 import (
    ProvenanceProducerBindingV1,
    ProvenanceBindingContextV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    validate_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.measured_return_calibration_v1 import (
    calibrate_explicit_measured_return_v1,
    read_measured_return_calibration_v1,
)
from src.ops.economic_md_input_producer_v1.purpose_consumers_v1 import (
    PurposeBoundPublicFactSourceV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_pending_decision_context_v1 import (
    PendingDecisionContextV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_pending_decision_lineage_v1 import (
    load_bound_pending_decision_identity_v1,
)
from src.learning.deterministic_decision_outcome_v0.o4_n_bars_bar_evidence_bridge_contracts_v1 import (
    mint_ddo_content_ref_v1,
)
from .constants_v1 import (
    SCHEMA_VERSION,
    EVENT_CREATED,
    EVENT_HORIZON_PROGRESS,
    EVENT_CLOSED,
    EVENT_FAILED,
    STATUS_PENDING,
    STATUS_IN_PROGRESS,
    STATUS_CLOSED,
    STATUS_FAILED_TERMINAL,
)
from .id_v1 import pending_outcome_id_from_decision_event_ref_v1
from .store_v1 import (
    load_pending_outcome_by_decision_ref_v1,
    load_pending_outcome_events_v1,
    persist_record_v1,
    replace_record_v1,
)
from .types_v1 import NaturalEnterPendingOutcomeRecordV1
from .retention_v1 import (
    canonical_bytes_v1,
    digest_v1,
    durable_bytes_v1,
    immutable_json_v1,
    exclusive_v1,
    fsync_tree_v1,
)


class OfflineOutcomeError(ValueError):
    pass


def _plain(value):
    if isinstance(value, Mapping):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def _utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat().replace("+00:00", "Z")


def _finite_positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def _ledger(root):
    return AppendOnlyDdoLedgerV0(root / "LANE_1/ddo_learning_capture_v1.jsonl")


def offline_return_target_v1(*, context: PendingDecisionContextV1, n_bars: int, venue: str) -> dict:
    if (
        type(n_bars) is not int
        or n_bars < 2
        or not _finite_positive(context.decision_timestamp_unix)
    ):
        raise OfflineOutcomeError("OFFLINE_RETURN_TARGET_INVALID")
    start = math.ceil(context.decision_timestamp_unix / 3600) * 3600
    return {
        "schema_version": "measured_return_forecast_target_v1",
        "price_basis_kind": "O4_BAR_CLOSE_FINALIZED",
        "outcome_scalar_kind": "LOG_RETURN",
        "instrument_ref": mint_ddo_content_ref_v1(
            prefix="ddo.o4.inst.",
            payload={
                "canonical_instrument_id": context.instrument_id,
                "venue": venue,
                "venue_instrument_id": context.native_id,
            },
        ),
        "bar_spec_ref": mint_ddo_content_ref_v1(
            prefix="ddo.o4.barspec.", payload={"o4_interval_id": "PT1H"}
        ),
        "n_bars": n_bars,
        "horizon_start_time_utc": _utc(start),
        "return_start_close_time_utc": _utc(start + 3600),
        "return_end_close_time_utc": _utc(start + n_bars * 3600),
    }


def _size(root):
    paths = list(root.rglob("*")) if root.exists() else []
    if any(p.is_symlink() for p in paths):
        raise OfflineOutcomeError("OFFLINE_RETENTION_SYMLINK_FORBIDDEN")
    return sum(p.stat().st_size for p in paths if p.is_file())


def create_explicit_offline_pending_v1(
    *,
    retention_root: Path,
    source_lane_root: Path,
    source_ledger: Path,
    context: PendingDecisionContextV1,
    dpo: Mapping[str, str],
    source: PurposeBoundPublicFactSourceV1,
    source_class: str,
    forecast: Mapping[str, Any],
    account_identity: str,
    venue: str,
    n_bars: int,
    expires_at_unix: float,
    retry_interval_seconds: float,
    max_attempts: int,
    max_retained_jobs: int,
    retained_bytes_backpressure_threshold: int,
) -> Path:
    """Opt-in only. No job is created by the blocked natural capture path."""
    retention_root, source_lane_root, source_ledger = (
        Path(p).resolve() for p in (retention_root, source_lane_root, source_ledger)
    )
    if source_lane_root not in source_ledger.parents:
        raise OfflineOutcomeError("OFFLINE_SOURCE_LEDGER_OUTSIDE_LANE")
    if retention_root == source_lane_root or source_lane_root in retention_root.parents:
        raise OfflineOutcomeError("OFFLINE_RETENTION_MUST_SURVIVE_LANE_RELEASE")
    if type(source) is not PurposeBoundPublicFactSourceV1 or source.policy.purpose != "OUTCOME":
        raise OfflineOutcomeError("OFFLINE_OUTCOME_SOURCE_REQUIRED")
    profile = _plain(source.profile_v1())
    if source.policy.canonical_instrument_id != context.instrument_id:
        raise OfflineOutcomeError("OFFLINE_SOURCE_INSTRUMENT_MISMATCH")
    if source_class != "SYNTHETIC_OFFLINE":
        raise OfflineOutcomeError("OFFLINE_SOURCE_CLASS_REQUIRED")
    target = offline_return_target_v1(context=context, n_bars=n_bars, venue=venue)
    end = datetime.fromisoformat(
        target["return_end_close_time_utc"].replace("Z", "+00:00")
    ).timestamp()
    if (
        not _finite_positive(expires_at_unix)
        or expires_at_unix <= end
        or not _finite_positive(retry_interval_seconds)
        or any(
            type(v) is not int or v <= 0
            for v in (max_attempts, max_retained_jobs, retained_bytes_backpressure_threshold)
        )
        or not isinstance(account_identity, str)
        or not account_identity.strip()
    ):
        raise OfflineOutcomeError("OFFLINE_EXPLICIT_POLICY_REQUIRED")
    f = _plain(validate_forecast_evidence_v1(forecast))
    if (
        f["provenance"].get("source_class") != source_class
        or f["provenance"].get("measured_return_target_v1") != target
        or f.get("decision_event_ref") != dpo.get("decision_event_ref")
        or f.get("selected_instrument_ref") != target["instrument_ref"]
        or f["outcome_binding_mode"] != "ACTUAL"
        or datetime.fromisoformat(f["forecast_created_at_utc"].replace("Z", "+00:00")).timestamp()
        > context.decision_timestamp_unix
    ):
        raise OfflineOutcomeError("OFFLINE_FORECAST_NOT_BOUND_AT_DECISION")
    key = digest_v1(
        {
            "decision": dpo.get("decision_event_ref"),
            "target": target,
            "account": account_identity,
            "source_class": source_class,
        }
    )
    root = retention_root / "jobs_v1" / key
    with exclusive_v1(retention_root / ".offline.writer.lock"):
        if (root / "capsule_v1.json").exists() and load_pending_outcome_events_v1(root):
            prior, _rec, _events = _load(root)
            inputs = {
                "source_lane_root": str(source_lane_root),
                "source_ledger": str(source_ledger),
                "context": asdict(context),
                "dpo": dict(dpo),
                "forecast": f,
                "source_profile": profile,
                "expires_at_unix": expires_at_unix,
                "retry_interval_seconds": retry_interval_seconds,
                "max_attempts": max_attempts,
                "max_retained_jobs": max_retained_jobs,
                "retained_bytes_backpressure_threshold": retained_bytes_backpressure_threshold,
            }
            if any(prior[k] != v for k, v in inputs.items()):
                raise OfflineOutcomeError("OFFLINE_CAPSULE_INPUT_CONFLICT")
            read_explicit_offline_pending_v1(root)
            return root
        owner = AppendOnlyDdoLedgerV0(source_ledger)
        with owner._exclusive_writer():
            bound = load_bound_pending_decision_identity_v1(
                ledger_path=source_ledger, context=context, dpo=dpo
            )
            if bound is None:
                raise OfflineOutcomeError("OFFLINE_DECISION_LINEAGE_UNBOUND")
            records = owner.read_all()
            decision = owner.get(dpo["decision_event_ref"])
            # Keep complete source bytes, reject later records instead of silently
            # filtering/rebuilding the original ledger or claiming absent snapshots.
            if any(
                datetime.fromisoformat(r["event_time_utc"].replace("Z", "+00:00")).timestamp()
                > context.decision_timestamp_unix
                for r in records
            ):
                raise OfflineOutcomeError("OFFLINE_DECISION_CAPSULE_HAS_FUTURE_RECORDS")
            if decision["code_sha"] == "UNKNOWN" or decision["config_hash"] == "UNKNOWN":
                raise OfflineOutcomeError("OFFLINE_DECISION_CONFIGURATION_UNBOUND")
            raw = source_ledger.read_bytes()
        scope = {
            "account_identity": account_identity,
            "code_sha": decision["code_sha"],
            "config_hash": decision["config_hash"],
            "market_observation_source": source_class,
            "outcome_semantic_class": "INTERNAL_SIMULATED_OUTCOME",
            "external_capital_flow_class": "NONE",
            "outcome_scalar_kind": "LOG_RETURN",
            "evaluation_horizon": "N_BARS",
            "metric_version": "FIRST_LAST_CLOSE_LOG_RETURN_V1",
            "target": target,
        }
        scope["evidence_pool_class"] = scope["outcome_semantic_class"]
        capsule = {
            "schema_version": "explicit_offline_pending_capsule.v1",
            "job_id": key,
            "source_lane_root": str(source_lane_root),
            "source_ledger": str(source_ledger),
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "context": asdict(context),
            "dpo": dict(dpo),
            "target": target,
            "scope": scope,
            "source_profile": profile,
            "forecast": f,
            "expires_at_unix": expires_at_unix,
            "retry_interval_seconds": retry_interval_seconds,
            "max_attempts": max_attempts,
            "retained_bytes_backpressure_threshold": retained_bytes_backpressure_threshold,
            "max_retained_jobs": max_retained_jobs,
            "absent_snapshots_not_reconstructed": [
                k
                for k in (
                    "market_snapshot_ref",
                    "feature_snapshot_ref",
                    "risk_snapshot_ref",
                    "position_snapshot_ref",
                )
                if decision.get(k) in (None, "UNKNOWN")
            ],
        }
        if not root.exists():
            jobs = list((retention_root / "jobs_v1").glob("*"))
            if (
                len(jobs) >= max_retained_jobs
                or _size(retention_root) + len(raw) * 2 + len(canonical_bytes_v1(capsule))
                > retained_bytes_backpressure_threshold
            ):
                raise OfflineOutcomeError("OFFLINE_RETENTION_BACKPRESSURE")
        root.mkdir(parents=True, exist_ok=True)
        immutable_json_v1(root / "capsule_v1.json", capsule)
        src_copy = root / "decision_source.jsonl"
        if src_copy.exists() and src_copy.read_bytes() != raw:
            raise OfflineOutcomeError("OFFLINE_CAPSULE_SOURCE_CHANGED")
        if not src_copy.exists():
            durable_bytes_v1(src_copy, raw)
        if not _ledger(root).ledger_path.exists():
            durable_bytes_v1(_ledger(root).ledger_path, raw)
        if load_pending_outcome_by_decision_ref_v1(root, dpo["decision_event_ref"]) is None:
            now = _utc(context.decision_timestamp_unix)
            rec = NaturalEnterPendingOutcomeRecordV1(
                schema_version=SCHEMA_VERSION,
                pending_outcome_id=pending_outcome_id_from_decision_event_ref_v1(
                    dpo["decision_event_ref"]
                ),
                decision_event_ref=dpo["decision_event_ref"],
                dpo_ref=dpo["dpo_ref"],
                decision_id=bound.policy_decision_id,
                correlation_id=bound.correlation_id,
                cycle_id=context.cycle_id,
                source_run_id=key,
                source_session_id=context.cycle_id,
                source_evidence_root=str(root),
                canonical_instrument_id=context.instrument_id,
                native_id=context.native_id,
                side=dpo["selected_side"].upper(),
                decision_timestamp_unix=context.decision_timestamp_unix,
                decision_reference_price=context.reference_price,
                market_context_ref=context.market_context_ref,
                n_bars_required=n_bars,
                bars_observed=0,
                finalized_bar_identities=(),
                status=STATUS_PENDING,
                created_at_utc=now,
                updated_at_utc=now,
            )
            persist_record_v1(
                root,
                event_type=EVENT_CREATED,
                record=rec,
                detail={"offline_capsule_digest": digest_v1(capsule), "stage": "WAITING_HORIZON"},
            )
        fsync_tree_v1(root)
        read_explicit_offline_pending_v1(root)
        return root


def _load(root):
    root = Path(root).resolve()
    _size(root)  # reject owner/capsule symlinks before any read or replay
    c = json.loads((root / "capsule_v1.json").read_bytes())
    if root.name != c["job_id"] or c["schema_version"] != "explicit_offline_pending_capsule.v1":
        raise OfflineOutcomeError("OFFLINE_CAPSULE_IDENTITY_MISMATCH")
    raw = (root / "decision_source.jsonl").read_bytes()
    if hashlib.sha256(raw).hexdigest() != c["source_sha256"]:
        raise OfflineOutcomeError("OFFLINE_CAPSULE_SOURCE_CHANGED")
    if not _ledger(root).ledger_path.read_bytes().startswith(raw):
        raise OfflineOutcomeError("OFFLINE_WORKING_LEDGER_SOURCE_PREFIX_CHANGED")
    context = PendingDecisionContextV1(**c["context"])
    if (
        load_bound_pending_decision_identity_v1(
            ledger_path=root / "decision_source.jsonl", context=context, dpo=c["dpo"]
        )
        is None
    ):
        raise OfflineOutcomeError("OFFLINE_RETAINED_LINEAGE_UNBOUND")
    events = load_pending_outcome_events_v1(root)
    if not events or events[0]["detail"].get("offline_capsule_digest") != digest_v1(c):
        raise OfflineOutcomeError("OFFLINE_CAPSULE_JOURNAL_MISMATCH")
    rec = load_pending_outcome_by_decision_ref_v1(root, c["dpo"]["decision_event_ref"])
    if (
        rec is None
        or rec.source_run_id != c["job_id"]
        or rec.n_bars_required != c["target"]["n_bars"]
    ):
        raise OfflineOutcomeError("OFFLINE_PENDING_IDENTITY_MISMATCH")
    return c, rec, events


def _measurement(root, c):
    m = json.loads((root / "offline_measurement_v1.json").read_bytes())
    if m["capsule_digest"] != digest_v1(c):
        raise OfflineOutcomeError("OFFLINE_MEASUREMENT_CAPSULE_MISMATCH")
    validate_n_bars_measurement_artifacts_v1(
        m["observation"], m["measurement"], m["information_set"]
    )
    if m["observation"]["decision_event_ref"] != c["dpo"]["decision_event_ref"]:
        raise OfflineOutcomeError("OFFLINE_MEASUREMENT_DECISION_MISMATCH")
    o = m["observation"]
    actual_target = {
        "schema_version": "measured_return_forecast_target_v1",
        "price_basis_kind": m["measurement"]["price_basis_kind"],
        "outcome_scalar_kind": o["outcome_scalar_kind"],
        "instrument_ref": o["instrument_ref"],
        "bar_spec_ref": o["bar_spec_ref"],
        "n_bars": o["n_bars"],
        "horizon_start_time_utc": o["horizon_start_time_utc"],
        "return_start_close_time_utc": o["bar_close_times_utc"][0],
        "return_end_close_time_utc": o["bar_close_times_utc"][-1],
    }
    if actual_target != c["target"] or m["source_class"] != c["scope"]["market_observation_source"]:
        raise OfflineOutcomeError("OFFLINE_MEASUREMENT_TARGET_MISMATCH")
    original = _ledger(root).get(c["dpo"]["decision_event_ref"])
    replay = run_offline_n_bars_horizon_pipeline_v1(
        original, m["snapshot"], outcome_scalar_kind="LOG_RETURN"
    )
    if (
        m["observation"] != _plain(replay["evaluation_observation"])
        or m["measurement"] != _plain(replay["materialization"].measurement_evidence_artifact)
        or m["information_set"]
        != _plain(replay["materialization"].evaluation_time_information_set_artifact)
    ):
        raise OfflineOutcomeError("OFFLINE_MEASUREMENT_REPLAY_MISMATCH")
    return m


def read_explicit_offline_pending_v1(root: Path) -> dict:
    """Projection from the original authoritative Pending journal, never a new index."""
    root = Path(root).resolve()
    c, rec, events = _load(root)
    result = {
        "job_id": c["job_id"],
        "pending_status": rec.status,
        "stage": events[-1]["detail"].get("stage", "WAITING_HORIZON"),
        "attempts": sum(e["detail"].get("offline_attempt_charged") is True for e in events),
        "source_class": c["scope"]["market_observation_source"],
        "independent_sample_count": 0,
    }
    if rec.status == STATUS_CLOSED:
        ack = json.loads((root / "consumer_ack_v1.json").read_bytes())
        if rec.closure_refs.get("offline_consumer_ack_digest") != digest_v1(ack):
            raise OfflineOutcomeError("OFFLINE_CONSUMER_ACK_MISMATCH")
        m = _measurement(root, c)
        if ack["measurement_digest"] != digest_v1(m) or ack["capsule_digest"] != digest_v1(c):
            raise OfflineOutcomeError("OFFLINE_CONSUMER_ACK_SOURCE_MISMATCH")
        ledger = _ledger(root)
        for item in ack["ddo_consumers"]:
            row = _plain(ledger.get(item["record_id"]))
            if digest_v1(row) != item["digest"]:
                raise OfflineOutcomeError("OFFLINE_CONSUMER_RECORD_CHANGED")
        exported = json.loads((root / "optimization_input_v1.json").read_bytes())
        if digest_v1(exported) != ack["optimization_input_digest"]:
            raise OfflineOutcomeError("OFFLINE_OPTIMIZATION_RECEIPT_CHANGED")
        from src.experiments.canonical_optimization_universe_learning_input_v1 import (
            CanonicalOptimizationUniverseLearningInputRequestV1,
            validate_canonical_optimization_universe_learning_input_v1,
        )

        replayed = _plain(
            validate_canonical_optimization_universe_learning_input_v1(
                CanonicalOptimizationUniverseLearningInputRequestV1(
                    learning_evidence=exported["evidence"]
                )
            )
        )
        if replayed != exported["consumer_result"]:
            raise OfflineOutcomeError("OFFLINE_OPTIMIZATION_READBACK_MISMATCH")
        numeric = read_measured_return_calibration_v1(
            durable_store_root=root / "mi_consumer",
            durable_evidence_id=ack["mi_durable_id"],
            forecast_evidence_id=c["forecast"]["forecast_evidence_id"],
            actual_outcome_ref=m["observation"]["actual_outcome_ref"],
        )
        if numeric != ack["numeric_readback"]:
            raise OfflineOutcomeError("OFFLINE_CONSUMER_NUMERIC_MISMATCH")
        result.update(stage="INGESTED", independent_sample_count=1, numeric_readback=numeric)
    return result


def _progress(root, rec, *, stage, detail=None, terminal=False):
    new = replace_record_v1(
        rec,
        status=STATUS_FAILED_TERMINAL if terminal else STATUS_IN_PROGRESS,
        failure_reason=stage if terminal else "",
    )
    persist_record_v1(
        root,
        event_type=EVENT_FAILED if terminal else EVENT_HORIZON_PROGRESS,
        record=new,
        expected_record=rec,
        detail={"stage": stage, **(detail or {})},
    )
    return new


def advance_explicit_offline_pending_v1(
    *, root: Path, as_of_unix: float, source: PurposeBoundPublicFactSourceV1 | None
) -> dict:
    root = Path(root).resolve()
    with exclusive_v1(root.parent.parent / ".offline.writer.lock"):
        c, rec, events = _load(root)
        if rec.status in {STATUS_CLOSED, STATUS_FAILED_TERMINAL}:
            return read_explicit_offline_pending_v1(root)
        if not _finite_positive(as_of_unix) or as_of_unix < rec.decision_timestamp_unix:
            raise OfflineOutcomeError("OFFLINE_ASOF_INVALID")
        attempts = [
            e["detail"] for e in events if e["detail"].get("offline_attempt_charged") is True
        ]
        measured = (root / "offline_measurement_v1.json").exists()
        if attempts and as_of_unix < attempts[-1]["as_of_unix"]:
            raise OfflineOutcomeError("OFFLINE_ASOF_REGRESSION")
        if not measured and as_of_unix > c["expires_at_unix"]:
            _progress(root, rec, stage="EXPIRED", terminal=True)
            return read_explicit_offline_pending_v1(root)
        if (
            not measured
            and attempts
            and as_of_unix < attempts[-1]["as_of_unix"] + c["retry_interval_seconds"]
        ):
            return {**read_explicit_offline_pending_v1(root), "stage": "WAITING_RETRY"}
        if not measured and len(attempts) >= c["max_attempts"]:
            _progress(root, rec, stage="RETRY_BUDGET_EXHAUSTED", terminal=True)
            return read_explicit_offline_pending_v1(root)
        if _size(root.parent.parent) >= c["retained_bytes_backpressure_threshold"]:
            return {**read_explicit_offline_pending_v1(root), "stage": "STORAGE_BACKPRESSURE"}
        if not measured:
            rec = _progress(
                root,
                rec,
                stage="MEASUREMENT_ATTEMPT",
                detail={
                    "offline_attempt_charged": True,
                    "as_of_unix": as_of_unix,
                },
            )
            if source is None:
                _progress(
                    root,
                    rec,
                    stage="WAITING_SOURCE",
                    detail={"reason": "BLOCKED_UNVERIFIED_SOURCE"},
                )
                return read_explicit_offline_pending_v1(root)
            if (
                type(source) is not PurposeBoundPublicFactSourceV1
                or _plain(source.profile_v1()) != c["source_profile"]
                or type(source.as_of_ms) is not int
                or source.as_of_ms != round(as_of_unix * 1000)
            ):
                _progress(
                    root,
                    rec,
                    stage="QUARANTINED",
                    terminal=True,
                    detail={"reason": "SOURCE_PROFILE_OR_CLOCK_MISMATCH"},
                )
                return read_explicit_offline_pending_v1(root)
            # Capsule knowledge time, not the old capture's market timestamp,
            # anchors the existing O4 selector. Original DecisionEvent stays intact.
            original = _ledger(root).get(rec.decision_event_ref)
            selector = {**dict(original), "event_time_utc": _utc(rec.decision_timestamp_unix)}
            try:
                snap = source.outcome_snapshot_v1(
                    native_id=rec.native_id,
                    decision_event_ref=rec.decision_event_ref,
                    n_bars=rec.n_bars_required,
                    decision_event=selector,
                )
            except (ValueError, DdoValidationError) as exc:
                reason = str(exc)
                waiting = any(
                    k in reason
                    for k in ("INSUFFICIENT", "MISSING", "NO_FACTS", "STALE", "UNAVAILABLE_ASOF")
                )
                stage = (
                    (
                        "WAITING_STALE_SOURCE"
                        if "STALE" in reason or getattr(exc, "availability", "") == "STALE"
                        else "WAITING_HORIZON"
                    )
                    if waiting
                    else "QUARANTINED"
                )
                _progress(root, rec, stage=stage, terminal=not waiting, detail={"reason": reason})
                return read_explicit_offline_pending_v1(root)
            expected_start = c["target"]["horizon_start_time_utc"]
            if snap["horizon_start_time_utc"] != expected_start:
                _progress(
                    root,
                    rec,
                    stage="QUARANTINED",
                    terminal=True,
                    detail={"reason": "FIXED_HORIZON_ANCHOR_MISMATCH"},
                )
                return read_explicit_offline_pending_v1(root)
            pipe = run_offline_n_bars_horizon_pipeline_v1(
                original, snap, outcome_scalar_kind="LOG_RETURN"
            )
            mat = pipe["materialization"]
            measurement = {
                "schema_version": "explicit_offline_pending_measurement.v1",
                "capsule_digest": digest_v1(c),
                "observed_as_of_unix": as_of_unix,
                "source_class": c["scope"]["market_observation_source"],
                "snapshot": _plain(snap),
                "observation": _plain(pipe["evaluation_observation"]),
                "measurement": _plain(mat.measurement_evidence_artifact),
                "information_set": _plain(mat.evaluation_time_information_set_artifact),
            }
            # No partial/non-OK supplier result can become an outcome or a zero.
            validate_n_bars_measurement_artifacts_v1(
                measurement["observation"],
                measurement["measurement"],
                measurement["information_set"],
            )
            if measurement["observation"]["horizon_observation_status"] != "OK":
                raise OfflineOutcomeError("OFFLINE_MEASUREMENT_INCOMPLETE")
            if (
                _size(root.parent.parent) + len(canonical_bytes_v1(measurement))
                >= c["retained_bytes_backpressure_threshold"]
            ):
                return {**read_explicit_offline_pending_v1(root), "stage": "STORAGE_BACKPRESSURE"}
            immutable_json_v1(root / "offline_measurement_v1.json", measurement)
        _consume(root, c, rec)
        return read_explicit_offline_pending_v1(root)


def _consume(root, c, rec):
    m = _measurement(root, c)
    ledger = _ledger(root)
    decision = ledger.get(rec.decision_event_ref)
    obs = m["observation"]
    identity = derive_productive_n_bars_evaluation_identity_v1(
        decision_record_id=rec.decision_event_ref,
        evaluation_time_utc=obs["evaluation_time_utc"],
        correlation_id=c["job_id"],
        code_sha=c["scope"]["code_sha"],
        config_hash=c["scope"]["config_hash"],
    )
    binding = ProvenanceProducerBindingV1.EXPLICIT_OFFLINE_SYNTHETIC_N_BARS
    bundle = evaluate_offline_bundle_v0(
        decision,
        obs,
        identity=identity,
        records_by_id={r["record_id"]: dict(r) for r in ledger.read_all()},
        provenance_binding=binding,
        provenance_context=ProvenanceBindingContextV1(
            decision_event_ref=rec.decision_event_ref,
            producer_id=__name__,
            instrument_id=rec.canonical_instrument_id,
            venue_native_id=rec.native_id,
            cycle_id=rec.cycle_id,
            outcome_scalar_kind="LOG_RETURN",
            evaluation_horizon="N_BARS",
            decision_timestamp_utc=_utc(rec.decision_timestamp_unix),
            evaluation_timestamp_utc=obs["evaluation_time_utc"],
            lineage_digest=digest_v1(c),
        ),
    )
    outcome = bundle["outcome_record"]
    require_learning_scope_v1(outcome=outcome, scope=c["scope"], target=c["target"])
    persist_evaluation_bundle_v0(
        ledger,
        outcome=outcome,
        attribution=bundle["attribution_record"],
        counterfactual=bundle["counterfactual_record"],
    )
    learning = ingest_evaluation_bundle_into_learning_state_v1(
        ledger,
        state_scope_id="ddo.lscope." + digest_v1(c["scope"])[:40],
        outcome=outcome,
        attribution=bundle["attribution_record"],
        counterfactual=bundle["counterfactual_record"],
        event_time_utc=obs["evaluation_time_utc"],
        correlation_id=c["job_id"],
        cycle_id=rec.cycle_id,
    )
    state = learning["learning_state_record"]
    evidence = export_learning_evidence_from_state_v1(state)
    require_learning_scope_v1(outcome=outcome, scope=c["scope"], target=c["target"])
    require_optimization_provenance_eligibility_v1(evidence)
    from src.experiments.canonical_optimization_universe_learning_input_v1 import (
        CanonicalOptimizationUniverseLearningInputRequestV1,
        validate_canonical_optimization_universe_learning_input_v1,
    )

    opt = _plain(
        validate_canonical_optimization_universe_learning_input_v1(
            CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=evidence)
        )
    )
    if opt["status"] != "ACCEPTED_OFFLINE_RESEARCH_INPUT":
        raise OfflineOutcomeError("OFFLINE_OPTIMIZATION_INPUT_REJECTED")
    exported = {"evidence": _plain(evidence), "consumer_result": opt}
    immutable_json_v1(root / "optimization_input_v1.json", exported)
    require_learning_scope_v1(outcome=outcome, scope=c["scope"], target=c["target"])
    mi = calibrate_explicit_measured_return_v1(
        forecast_evidence=c["forecast"],
        evaluation_observation=obs,
        measurement_evidence=m["measurement"],
        evaluation_information_set=m["information_set"],
        durable_store_root=root / "mi_consumer",
    )
    numeric = read_measured_return_calibration_v1(
        durable_store_root=root / "mi_consumer",
        durable_evidence_id=mi["persistence"]["durable_evidence_id"],
        forecast_evidence_id=mi["forecast_evidence_id"],
        actual_outcome_ref=obs["actual_outcome_ref"],
    )
    ack = {
        "schema_version": "explicit_offline_consumer_ack.v1",
        "capsule_digest": digest_v1(c),
        "measurement_digest": digest_v1(m),
        "mi_durable_id": mi["persistence"]["durable_evidence_id"],
        "numeric_readback": _plain(numeric),
        "optimization_input_digest": digest_v1(exported),
        "ddo_consumers": [],
    }
    for row in (outcome, state):
        stored = _plain(ledger.get(row["record_id"]))
        if stored != _plain(row):
            raise OfflineOutcomeError("OFFLINE_CONSUMER_READBACK_MISMATCH")
        ack["ddo_consumers"].append({"record_id": row["record_id"], "digest": digest_v1(stored)})
    fsync_tree_v1(root)
    immutable_json_v1(root / "consumer_ack_v1.json", ack)
    new = replace_record_v1(
        rec,
        status=STATUS_CLOSED,
        bars_observed=rec.n_bars_required,
        finalized_bar_identities=obs["bar_identity_refs"],
        closure_refs={
            "offline_consumer_ack_digest": digest_v1(ack),
            "actual_outcome_ref": obs["actual_outcome_ref"],
        },
    )
    persist_record_v1(
        root,
        event_type=EVENT_CLOSED,
        record=new,
        expected_record=rec,
        detail={"stage": "INGESTED", "independent_sample_count": 1},
    )
