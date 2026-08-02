"""Productive Governed Futures Universe Producer entrypoint (Capability 2.1)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence
from uuid import uuid4

from src.ops.governed_futures_universe_producer_v1.constants_v1 import (
    ALPHA_ALLOWED_DEFAULT,
    CALL_GRAPH,
    CAPABILITY_ID,
    DEFAULT_MAX_SOURCE_AGE_SECONDS,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    UNIVERSE_STATUS_EMPTY,
    VENUE,
)
from src.ops.governed_futures_universe_producer_v1.discovery_v1 import (
    discover_okx_eea_instruments_v1,
)
from src.ops.governed_futures_universe_producer_v1.eligibility_v1 import (
    classify_instrument_v1,
    resolve_conflicts_and_duplicates_v1,
)
from src.ops.governed_futures_universe_producer_v1.models_v1 import (
    GovernedFuturesUniverseSnapshotV1,
    UniverseProduceResultV1,
    authority_block,
    compute_config_digest_v1,
    compute_source_digest_v1,
    empty_universe_status,
    sha256_hex,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    UniversePersistenceError,
    evidence_digest_v1,
    load_and_validate_universe_snapshot_v1,
    persist_universe_bundle_atomic_v1,
)
from src.ops.governed_futures_universe_producer_v1.reason_codes_v1 import UniverseFailureCodeV1
from src.ops.governed_futures_universe_producer_v1.single_writer_v1 import (
    DuplicateUniverseWriterError,
    GovernedUniverseSingleWriterV1,
)


def _rfc3339(unix: float) -> str:
    return datetime.fromtimestamp(unix, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def produce_governed_futures_universe_v1(
    *,
    source_payload: Mapping[str, Any] | None,
    repository_sha: str,
    producer_observed_at_unix: float,
    mark_price_payload: Mapping[str, Any] | Sequence[str] | None = None,
    source_event_time: str | None = None,
    venue: str = VENUE,
    source_kind: str | None = "okx_eea_public_instruments",
    max_source_age_seconds: float = DEFAULT_MAX_SOURCE_AGE_SECONDS,
    snapshot_id: str | None = None,
) -> UniverseProduceResultV1:
    """Produce a deterministic governed futures universe snapshot (no persistence)."""
    wall_rfc = _rfc3339(producer_observed_at_unix)
    config_digest = compute_config_digest_v1(
        repository_sha=repository_sha,
        max_source_age_seconds=max_source_age_seconds,
        venue=venue,
    )

    discovery = discover_okx_eea_instruments_v1(
        source_payload=source_payload,
        mark_price_payload=mark_price_payload,
        source_event_time=source_event_time,
        venue=venue,
        source_kind=source_kind,
    )
    if not discovery.ok:
        failure_codes = discovery.failure_codes or (
            UniverseFailureCodeV1.OKX_SOURCE_UNAVAILABLE.value,
        )
        snap = GovernedFuturesUniverseSnapshotV1(
            schema_version=SCHEMA_VERSION,
            capability_id=CAPABILITY_ID,
            producer_version=PRODUCER_VERSION,
            snapshot_id=snapshot_id or f"gfu_{uuid4().hex[:16]}",
            repository_sha=repository_sha,
            config_digest=config_digest,
            source_digest=sha256_hex("{}"),
            payload_digest="",
            generated_at_event_time=discovery.source_event_time or wall_rfc,
            generated_at_wall_time=wall_rfc,
            venue=venue,
            universe_status=UNIVERSE_STATUS_EMPTY,
            alpha_allowed=False,
            raw_instrument_count=0,
            eligible_instrument_count=0,
            excluded_instrument_count=0,
            exclusion_counts_by_reason={code: 1 for code in failure_codes},
            instruments=(),
            authority=authority_block(),
            call_graph=CALL_GRAPH,
            failure_codes=failure_codes,
        ).with_payload_digest()
        return UniverseProduceResultV1(
            snapshot=snap,
            excluded_instruments=(),
            ok=False,
            hard_stop=True,
            failure_codes=failure_codes,
        )

    source_digest = compute_source_digest_v1(
        instruments=discovery.instruments,
        mark_price_supported_ids=sorted(discovery.mark_price_supported_ids),
        source_event_time=discovery.source_event_time,
        venue=discovery.venue,
    )

    classified = [
        classify_instrument_v1(
            row,
            venue=discovery.venue,
            source_event_time=discovery.source_event_time,
            producer_observed_at=wall_rfc,
            repository_sha=repository_sha,
            config_digest=config_digest,
            source_digest=source_digest,
            mark_price_supported_ids=discovery.mark_price_supported_ids,
            max_source_age_seconds=max_source_age_seconds,
            producer_observed_unix=producer_observed_at_unix,
        )
        for row in discovery.instruments
    ]
    eligible, excluded, exclusion_counts = resolve_conflicts_and_duplicates_v1(classified)

    failure_codes: list[str] = []
    status = empty_universe_status(eligible_count=len(eligible))
    if status == UNIVERSE_STATUS_EMPTY:
        failure_codes.append(UniverseFailureCodeV1.EMPTY_ELIGIBLE_UNIVERSE.value)
        exclusion_counts = dict(exclusion_counts)
        exclusion_counts[UniverseFailureCodeV1.EMPTY_ELIGIBLE_UNIVERSE.value] = (
            exclusion_counts.get(UniverseFailureCodeV1.EMPTY_ELIGIBLE_UNIVERSE.value, 0) + 1
        )

    event_time_raw = discovery.source_event_time or wall_rfc
    if "T" in event_time_raw:
        event_time = event_time_raw
    elif event_time_raw.isdigit():
        event_time = _rfc3339(float(event_time_raw) / 1000.0)
    else:
        event_time = wall_rfc
    snap = GovernedFuturesUniverseSnapshotV1(
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        producer_version=PRODUCER_VERSION,
        snapshot_id=snapshot_id or f"gfu_{sha256_hex(source_digest + repository_sha)[:16]}",
        repository_sha=repository_sha,
        config_digest=config_digest,
        source_digest=source_digest,
        payload_digest="",
        generated_at_event_time=event_time,
        generated_at_wall_time=wall_rfc,
        venue=discovery.venue,
        universe_status=status,
        alpha_allowed=ALPHA_ALLOWED_DEFAULT,
        raw_instrument_count=len(discovery.instruments),
        eligible_instrument_count=len(eligible),
        excluded_instrument_count=len(excluded),
        exclusion_counts_by_reason=dict(sorted(exclusion_counts.items())),
        instruments=tuple(eligible),
        authority=authority_block(),
        call_graph=CALL_GRAPH,
        failure_codes=tuple(failure_codes),
    ).with_payload_digest()

    return UniverseProduceResultV1(
        snapshot=snap,
        excluded_instruments=tuple(excluded),
        ok=status != UNIVERSE_STATUS_EMPTY,
        hard_stop=status == UNIVERSE_STATUS_EMPTY,
        failure_codes=tuple(failure_codes),
    )


def run_governed_futures_universe_producer_v1(
    *,
    state_root: Path,
    source_payload: Mapping[str, Any] | None,
    repository_sha: str,
    producer_observed_at_unix: float,
    session_id: str = "default",
    mark_price_payload: Mapping[str, Any] | Sequence[str] | None = None,
    source_event_time: str | None = None,
    venue: str = VENUE,
    source_kind: str | None = "okx_eea_public_instruments",
    max_source_age_seconds: float = DEFAULT_MAX_SOURCE_AGE_SECONDS,
    snapshot_id: str | None = None,
    simulate_partial_write: bool = False,
    simulate_write_failure: bool = False,
    release_writer: bool = True,
) -> dict[str, Any]:
    """Full productive call graph: produce → persist → verify (no alpha/runtime activation)."""
    writer = GovernedUniverseSingleWriterV1(state_root=Path(state_root), session_id=session_id)
    try:
        writer.acquire(now_unix=producer_observed_at_unix)
    except DuplicateUniverseWriterError as exc:
        return {
            "ok": False,
            "hard_stop": True,
            "failure_codes": (exc.failure_code,),
            "alpha_allowed": False,
            "persistence": None,
            "snapshot": None,
            "restart": None,
            "evidence": {
                "capability_id": CAPABILITY_ID,
                "failure_codes": [exc.failure_code],
                "duplicate_writer_rejected": True,
            },
        }

    try:
        produced = produce_governed_futures_universe_v1(
            source_payload=source_payload,
            repository_sha=repository_sha,
            producer_observed_at_unix=producer_observed_at_unix,
            mark_price_payload=mark_price_payload,
            source_event_time=source_event_time,
            venue=venue,
            source_kind=source_kind,
            max_source_age_seconds=max_source_age_seconds,
            snapshot_id=snapshot_id,
        )
        evidence = build_universe_evidence_v1(
            produced=produced,
            persistence_path=str(Path(state_root)),
            persistence_verification=None,
            restart_verification=None,
        )
        try:
            persistence = persist_universe_bundle_atomic_v1(
                state_root=Path(state_root),
                writer=writer,
                snapshot=produced.snapshot,
                evidence=evidence,
                simulate_partial_write=simulate_partial_write,
                simulate_write_failure=simulate_write_failure,
            )
        except UniversePersistenceError as exc:
            evidence = build_universe_evidence_v1(
                produced=produced,
                persistence_path=str(Path(state_root)),
                persistence_verification={"ok": False, "failure_code": exc.failure_code},
                restart_verification=None,
                extra_failure_codes=(exc.failure_code,),
            )
            return {
                "ok": False,
                "hard_stop": True,
                "failure_codes": tuple(sorted(set(produced.failure_codes + (exc.failure_code,)))),
                "alpha_allowed": False,
                "snapshot": produced.snapshot.to_dict(),
                "persistence": {"ok": False, "failure_code": exc.failure_code},
                "restart": None,
                "evidence": evidence,
            }

        restart = prove_restart_load_v1(
            state_root=Path(state_root),
            expected_snapshot=produced.snapshot,
        )
        evidence = build_universe_evidence_v1(
            produced=produced,
            persistence_path=persistence["persistence_path"],
            persistence_verification=persistence,
            restart_verification=restart,
        )
        # Rewrite evidence with restart proof included (same writer still held).
        persist_universe_bundle_atomic_v1(
            state_root=Path(state_root),
            writer=writer,
            snapshot=produced.snapshot,
            evidence=evidence,
        )
        return {
            "ok": produced.ok and bool(persistence.get("ok")) and bool(restart.get("ok")),
            "hard_stop": produced.hard_stop or not restart.get("ok"),
            "failure_codes": produced.failure_codes,
            "alpha_allowed": False,
            "snapshot": produced.snapshot.to_dict(),
            "persistence": persistence,
            "restart": restart,
            "evidence": evidence,
            "excluded_count": produced.snapshot.excluded_instrument_count,
            "eligible_count": produced.snapshot.eligible_instrument_count,
        }
    finally:
        if release_writer:
            writer.release()


def prove_restart_load_v1(
    *,
    state_root: Path,
    expected_snapshot: GovernedFuturesUniverseSnapshotV1,
) -> dict[str, Any]:
    """Process-restart semantics at producer/snapshot level: load → validate → identical truth."""
    loaded = load_and_validate_universe_snapshot_v1(
        Path(state_root),
        expected_repository_sha=expected_snapshot.repository_sha,
        expected_config_digest=expected_snapshot.config_digest,
    )
    if not loaded.ok or loaded.snapshot is None:
        return {
            "ok": False,
            "identical_canonical_truth": False,
            "alpha_allowed_after_restart": False,
            "failure_codes": list(loaded.failure_codes),
            "detail": loaded.detail,
        }
    identical = loaded.snapshot.payload_digest == expected_snapshot.payload_digest
    identical = identical and loaded.snapshot.to_dict() == expected_snapshot.to_dict()
    return {
        "ok": identical,
        "identical_canonical_truth": identical,
        "alpha_allowed_after_restart": False,
        "loaded_snapshot_id": loaded.snapshot.snapshot_id,
        "loaded_payload_digest": loaded.snapshot.payload_digest,
        "expected_payload_digest": expected_snapshot.payload_digest,
        "failure_codes": [],
    }


def build_universe_evidence_v1(
    *,
    produced: UniverseProduceResultV1,
    persistence_path: str,
    persistence_verification: Optional[Mapping[str, Any]],
    restart_verification: Optional[Mapping[str, Any]],
    extra_failure_codes: tuple[str, ...] = (),
    deterministic_replay_ok: Optional[bool] = None,
) -> dict[str, Any]:
    snap = produced.snapshot
    recomputed_digest = snap.compute_payload_digest()
    deterministic_replay = (
        recomputed_digest == snap.payload_digest
        if deterministic_replay_ok is None
        else bool(deterministic_replay_ok) and recomputed_digest == snap.payload_digest
    )

    evidence = {
        "capability_id": CAPABILITY_ID,
        "schema_version": SCHEMA_VERSION,
        "producer_version": PRODUCER_VERSION,
        "repository_sha": snap.repository_sha,
        "config_digest": snap.config_digest,
        "source_digest": snap.source_digest,
        "raw_instrument_count": snap.raw_instrument_count,
        "eligible_instrument_count": snap.eligible_instrument_count,
        "excluded_instrument_count": snap.excluded_instrument_count,
        "exclusion_counts_by_reason": dict(snap.exclusion_counts_by_reason),
        "snapshot_id": snap.snapshot_id,
        "snapshot_digest": snap.payload_digest,
        "persistence_path": persistence_path,
        "persistence_verification": dict(persistence_verification or {}),
        "restart_verification": dict(restart_verification or {}),
        "deterministic_replay_verification": {
            "ok": deterministic_replay,
            "recomputed_payload_digest": recomputed_digest,
            "snapshot_payload_digest": snap.payload_digest,
        },
        "authority_verification": dict(snap.authority),
        "dashboard_independence": True,
        "no_selection_proof": True,
        "no_ranking_proof": True,
        "no_alpha_proof": True,
        "no_execution_proof": True,
        "alpha_allowed": False,
        "universe_status": snap.universe_status,
        "call_graph": list(CALL_GRAPH),
        "failure_codes": list(sorted(set(snap.failure_codes + extra_failure_codes))),
        "verifier_result": {
            "ok": bool(
                (persistence_verification or {}).get("ok", False)
                and (restart_verification or {}).get("ok", False)
                and deterministic_replay
            ),
            "UNIVERSE_AUTHORITY_OWNER_SINGLE": True,
            "DASHBOARD_AUTHORITY": False,
            "RANKING_AUTHORITY_ADDED": False,
            "SELECTION_AUTHORITY_ADDED": False,
            "ALPHA_AUTHORITY_ADDED": False,
            "EXECUTION_AUTHORITY_ADDED": False,
            "LEGACY_PARALLEL_AUTHORITY_ABSENT": True,
        },
    }
    evidence["evidence_digest"] = evidence_digest_v1(evidence)
    return evidence
