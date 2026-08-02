"""Productive Futures Ranking Producer entrypoint (Capability 2.2)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.governed_futures_universe_producer_v1.models_v1 import (
    GovernedFuturesUniverseSnapshotV1,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    load_and_validate_universe_snapshot_v1,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    ALPHA_ALLOWED_DEFAULT,
    CALL_GRAPH,
    CAPABILITY_ID,
    DEFAULT_MAX_UNIVERSE_AGE_SECONDS,
    PRODUCER_VERSION,
    RANKING_POLICY_ID,
    RANKING_POLICY_PROVENANCE,
    RANKING_POLICY_VERSION,
    SCHEMA_VERSION,
    SNAPSHOT_STATE_INTEGRITY_FAILURE,
    SNAPSHOT_STATE_INVALID_INPUT,
    SNAPSHOT_STATE_NO_ELIGIBLE,
    SNAPSHOT_STATE_STALE_INPUT,
    SNAPSHOT_STATE_VALID,
    TOP20_CANDIDATE_CONTEXT_LIMIT,
    UNIVERSE_CAPABILITY_ID,
    UNIVERSE_PRODUCER_VERSION,
    UNIVERSE_SCHEMA_VERSION,
    VENUE,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
    RankingProduceResultV1,
    authority_block,
    compute_config_digest_v1,
    compute_ranking_snapshot_id_v1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    RankingPersistenceError,
    load_and_validate_ranking_snapshot_v1,
    persist_ranking_bundle_atomic_v1,
)
from src.ops.productive_futures_ranking_producer_v1.policy_v1 import policy_descriptor_v1
from src.ops.productive_futures_ranking_producer_v1.ranking_v1 import (
    assert_no_reintroduced_excluded_instruments_v1,
    classify_and_rank_candidates_v1,
)
from src.ops.productive_futures_ranking_producer_v1.reason_codes_v1 import RankingFailureCodeV1
from src.ops.productive_futures_ranking_producer_v1.single_writer_v1 import (
    DuplicateRankingWriterError,
    ProductiveRankingSingleWriterV1,
)


def _rfc3339(unix: float) -> str:
    return datetime.fromtimestamp(unix, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_event_time_unix(value: str) -> Optional[float]:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.isdigit():
        ms = int(raw)
        if ms <= 0:
            return None
        return ms / 1000.0 if ms > 10_000_000_000 else float(ms)
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return datetime.fromisoformat(raw).timestamp()
    except Exception:  # noqa: BLE001
        return None


def _failure_snapshot(
    *,
    repository_sha: str,
    config_digest: str,
    wall_rfc: str,
    event_time: str,
    snapshot_state: str,
    failure_codes: tuple[str, ...],
    universe_snapshot_id: str = "",
    universe_source_digest: str = "",
    universe_payload_digest: str = "",
    ranking_snapshot_id: str | None = None,
) -> ProductiveFuturesRankingSnapshotV1:
    rid = ranking_snapshot_id or compute_ranking_snapshot_id_v1(
        universe_snapshot_id=universe_snapshot_id or "missing",
        universe_source_digest=universe_source_digest or "missing",
        config_digest=config_digest,
        repository_sha=repository_sha,
    )
    return ProductiveFuturesRankingSnapshotV1(
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        producer_version=PRODUCER_VERSION,
        ranking_snapshot_id=rid,
        universe_snapshot_id=universe_snapshot_id,
        universe_source_digest=universe_source_digest,
        universe_payload_digest=universe_payload_digest,
        ranking_policy_id=RANKING_POLICY_ID,
        ranking_policy_version=RANKING_POLICY_VERSION,
        repository_sha=repository_sha,
        config_digest=config_digest,
        event_time=event_time or wall_rfc,
        produced_at_wall_time=wall_rfc,
        candidate_count_total=0,
        eligible_candidate_count=0,
        excluded_candidate_count=0,
        ranked_candidates=(),
        excluded_candidates=(),
        snapshot_state=snapshot_state,
        integrity_digest="",
        alpha_allowed=False,
        top20_candidate_context_limit=TOP20_CANDIDATE_CONTEXT_LIMIT,
        selection_authority_created=False,
        multi_future_authority_created=False,
        dashboard_input_used=False,
        ranking_policy_provenance=RANKING_POLICY_PROVENANCE,
        authority=authority_block(),
        call_graph=CALL_GRAPH,
        failure_codes=failure_codes,
    ).with_integrity_digest()


def _validate_universe_dict_v1(
    universe: Mapping[str, Any],
    *,
    expected_repository_sha: str | None,
    producer_observed_at_unix: float,
    max_universe_age_seconds: float,
) -> tuple[Optional[GovernedFuturesUniverseSnapshotV1], tuple[str, ...], str]:
    failures: list[str] = []
    try:
        snap = GovernedFuturesUniverseSnapshotV1.from_dict(universe)
    except Exception:  # noqa: BLE001
        return (
            None,
            (RankingFailureCodeV1.UNIVERSE_SNAPSHOT_INVALID.value,),
            SNAPSHOT_STATE_INVALID_INPUT,
        )

    if snap.schema_version != UNIVERSE_SCHEMA_VERSION:
        failures.append(RankingFailureCodeV1.UNIVERSE_SCHEMA_MISMATCH.value)
    if snap.capability_id != UNIVERSE_CAPABILITY_ID:
        failures.append(RankingFailureCodeV1.UNIVERSE_CAPABILITY_MISMATCH.value)
    if snap.producer_version != UNIVERSE_PRODUCER_VERSION:
        failures.append(RankingFailureCodeV1.UNIVERSE_SCHEMA_MISMATCH.value)
    if snap.venue != VENUE:
        failures.append(RankingFailureCodeV1.VENUE_NOT_OKX_EEA.value)
    if not snap.snapshot_id:
        failures.append(RankingFailureCodeV1.MISSING_UNIVERSE_SNAPSHOT_ID.value)
    if not snap.source_digest:
        failures.append(RankingFailureCodeV1.MISSING_UNIVERSE_SOURCE_DIGEST.value)
    recomputed = snap.compute_payload_digest()
    if not snap.payload_digest or snap.payload_digest != recomputed:
        failures.append(RankingFailureCodeV1.UNIVERSE_DIGEST_MISMATCH.value)
        failures.append(RankingFailureCodeV1.INTEGRITY_FAILURE.value)
    if expected_repository_sha is not None and snap.repository_sha != expected_repository_sha:
        failures.append(RankingFailureCodeV1.REPOSITORY_SHA_MISMATCH.value)
    if not snap.generated_at_event_time:
        failures.append(RankingFailureCodeV1.MISSING_UNIVERSE_EVENT_TIME.value)

    event_unix = _parse_event_time_unix(snap.generated_at_event_time)
    stale = False
    if event_unix is None and snap.generated_at_event_time:
        failures.append(RankingFailureCodeV1.UNIVERSE_SNAPSHOT_STALE.value)
        stale = True
    elif event_unix is not None:
        age = producer_observed_at_unix - event_unix
        if age > float(max_universe_age_seconds):
            failures.append(RankingFailureCodeV1.UNIVERSE_SNAPSHOT_STALE.value)
            stale = True

    if failures:
        if RankingFailureCodeV1.UNIVERSE_DIGEST_MISMATCH.value in failures:
            state = SNAPSHOT_STATE_INTEGRITY_FAILURE
        elif stale or RankingFailureCodeV1.UNIVERSE_SNAPSHOT_STALE.value in failures:
            state = SNAPSHOT_STATE_STALE_INPUT
        else:
            state = SNAPSHOT_STATE_INVALID_INPUT
        return snap, tuple(sorted(set(failures))), state
    return snap, (), SNAPSHOT_STATE_VALID


def produce_productive_futures_ranking_v1(
    *,
    universe_snapshot: Mapping[str, Any] | None,
    repository_sha: str,
    producer_observed_at_unix: float,
    max_universe_age_seconds: float = DEFAULT_MAX_UNIVERSE_AGE_SECONDS,
    top20_limit: int = TOP20_CANDIDATE_CONTEXT_LIMIT,
    ranking_snapshot_id: str | None = None,
    expected_universe_repository_sha: str | None = None,
    dashboard_payload: Mapping[str, Any] | None = None,
    legacy_ranker_payload: Mapping[str, Any] | None = None,
) -> RankingProduceResultV1:
    """Produce a deterministic ranking snapshot from a Cap 2.1 universe snapshot."""
    wall_rfc = _rfc3339(producer_observed_at_unix)
    config_digest = compute_config_digest_v1(
        repository_sha=repository_sha,
        max_universe_age_seconds=max_universe_age_seconds,
        top20_limit=top20_limit,
    )

    if dashboard_payload is not None:
        snap = _failure_snapshot(
            repository_sha=repository_sha,
            config_digest=config_digest,
            wall_rfc=wall_rfc,
            event_time=wall_rfc,
            snapshot_state=SNAPSHOT_STATE_INVALID_INPUT,
            failure_codes=(RankingFailureCodeV1.DASHBOARD_INPUT_FORBIDDEN.value,),
            ranking_snapshot_id=ranking_snapshot_id,
        )
        return RankingProduceResultV1(snap, False, True, snap.failure_codes)

    if legacy_ranker_payload is not None:
        snap = _failure_snapshot(
            repository_sha=repository_sha,
            config_digest=config_digest,
            wall_rfc=wall_rfc,
            event_time=wall_rfc,
            snapshot_state=SNAPSHOT_STATE_INVALID_INPUT,
            failure_codes=(RankingFailureCodeV1.LEGACY_RANKER_INPUT_FORBIDDEN.value,),
            ranking_snapshot_id=ranking_snapshot_id,
        )
        return RankingProduceResultV1(snap, False, True, snap.failure_codes)

    if universe_snapshot is None:
        snap = _failure_snapshot(
            repository_sha=repository_sha,
            config_digest=config_digest,
            wall_rfc=wall_rfc,
            event_time=wall_rfc,
            snapshot_state=SNAPSHOT_STATE_INVALID_INPUT,
            failure_codes=(RankingFailureCodeV1.UNIVERSE_SNAPSHOT_MISSING.value,),
            ranking_snapshot_id=ranking_snapshot_id,
        )
        return RankingProduceResultV1(snap, False, True, snap.failure_codes)

    if not isinstance(universe_snapshot, Mapping):
        snap = _failure_snapshot(
            repository_sha=repository_sha,
            config_digest=config_digest,
            wall_rfc=wall_rfc,
            event_time=wall_rfc,
            snapshot_state=SNAPSHOT_STATE_INVALID_INPUT,
            failure_codes=(RankingFailureCodeV1.UNIVERSE_SNAPSHOT_INVALID.value,),
            ranking_snapshot_id=ranking_snapshot_id,
        )
        return RankingProduceResultV1(snap, False, True, snap.failure_codes)

    universe, failures, state = _validate_universe_dict_v1(
        universe_snapshot,
        expected_repository_sha=expected_universe_repository_sha,
        producer_observed_at_unix=producer_observed_at_unix,
        max_universe_age_seconds=max_universe_age_seconds,
    )
    if universe is None or failures:
        snap = _failure_snapshot(
            repository_sha=repository_sha,
            config_digest=config_digest,
            wall_rfc=wall_rfc,
            event_time=(
                universe.generated_at_event_time
                if universe is not None and universe.generated_at_event_time
                else wall_rfc
            ),
            snapshot_state=state,
            failure_codes=failures or (RankingFailureCodeV1.UNIVERSE_SNAPSHOT_INVALID.value,),
            universe_snapshot_id=universe.snapshot_id if universe is not None else "",
            universe_source_digest=universe.source_digest if universe is not None else "",
            universe_payload_digest=universe.payload_digest if universe is not None else "",
            ranking_snapshot_id=ranking_snapshot_id,
        )
        return RankingProduceResultV1(snap, False, True, snap.failure_codes)

    universe_dict = universe.to_dict()
    ranked, excluded, _exclusion_counts = classify_and_rank_candidates_v1(
        universe_dict,
        top_n=top20_limit,
    )
    reintro = assert_no_reintroduced_excluded_instruments_v1(
        universe_snapshot=universe_dict,
        ranked=ranked,
    )
    if reintro:
        snap = _failure_snapshot(
            repository_sha=repository_sha,
            config_digest=config_digest,
            wall_rfc=wall_rfc,
            event_time=universe.generated_at_event_time,
            snapshot_state=SNAPSHOT_STATE_INVALID_INPUT,
            failure_codes=reintro,
            universe_snapshot_id=universe.snapshot_id,
            universe_source_digest=universe.source_digest,
            universe_payload_digest=universe.payload_digest,
            ranking_snapshot_id=ranking_snapshot_id,
        )
        return RankingProduceResultV1(snap, False, True, snap.failure_codes)

    # ranked = top-N eligible; excluded tuple may include overflow eligible + true exclusions.
    eligible_count = len([c for c in ranked if c.eligibility_status == "ELIGIBLE"]) + len(
        [c for c in excluded if c.eligibility_status == "ELIGIBLE"]
    )
    excluded_count = len([c for c in excluded if c.eligibility_status == "EXCLUDED"])
    total = eligible_count + excluded_count

    failure_codes: list[str] = []
    if eligible_count == 0:
        snapshot_state = SNAPSHOT_STATE_NO_ELIGIBLE
        failure_codes.append(RankingFailureCodeV1.NO_ELIGIBLE_CANDIDATES.value)
        ok = True  # valid persisted NO_ELIGIBLE state
        hard_stop = False
    else:
        snapshot_state = SNAPSHOT_STATE_VALID
        ok = True
        hard_stop = False

    rid = ranking_snapshot_id or compute_ranking_snapshot_id_v1(
        universe_snapshot_id=universe.snapshot_id,
        universe_source_digest=universe.source_digest,
        config_digest=config_digest,
        repository_sha=repository_sha,
    )
    snap = ProductiveFuturesRankingSnapshotV1(
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        producer_version=PRODUCER_VERSION,
        ranking_snapshot_id=rid,
        universe_snapshot_id=universe.snapshot_id,
        universe_source_digest=universe.source_digest,
        universe_payload_digest=universe.payload_digest,
        ranking_policy_id=RANKING_POLICY_ID,
        ranking_policy_version=RANKING_POLICY_VERSION,
        repository_sha=repository_sha,
        config_digest=config_digest,
        event_time=universe.generated_at_event_time,
        produced_at_wall_time=wall_rfc,
        candidate_count_total=total,
        eligible_candidate_count=eligible_count,
        excluded_candidate_count=excluded_count,
        ranked_candidates=ranked,
        excluded_candidates=tuple(c for c in excluded if c.eligibility_status == "EXCLUDED"),
        snapshot_state=snapshot_state,
        integrity_digest="",
        alpha_allowed=ALPHA_ALLOWED_DEFAULT,
        top20_candidate_context_limit=top20_limit,
        selection_authority_created=False,
        multi_future_authority_created=False,
        dashboard_input_used=False,
        ranking_policy_provenance=RANKING_POLICY_PROVENANCE,
        authority=authority_block(),
        call_graph=CALL_GRAPH,
        failure_codes=tuple(failure_codes),
    ).with_integrity_digest()

    return RankingProduceResultV1(
        snapshot=snap,
        ok=ok,
        hard_stop=hard_stop,
        failure_codes=tuple(failure_codes),
    )


def produce_from_universe_state_root_v1(
    *,
    universe_state_root: Path,
    repository_sha: str,
    producer_observed_at_unix: float,
    max_universe_age_seconds: float = DEFAULT_MAX_UNIVERSE_AGE_SECONDS,
    top20_limit: int = TOP20_CANDIDATE_CONTEXT_LIMIT,
    ranking_snapshot_id: str | None = None,
) -> RankingProduceResultV1:
    loaded = load_and_validate_universe_snapshot_v1(Path(universe_state_root))
    if not loaded.ok or loaded.snapshot is None:
        wall_rfc = _rfc3339(producer_observed_at_unix)
        config_digest = compute_config_digest_v1(
            repository_sha=repository_sha,
            max_universe_age_seconds=max_universe_age_seconds,
            top20_limit=top20_limit,
        )
        codes = (RankingFailureCodeV1.UNIVERSE_SNAPSHOT_MISSING.value,)
        if loaded.failure_codes:
            codes = tuple(
                sorted(
                    set(
                        [
                            RankingFailureCodeV1.UNIVERSE_SNAPSHOT_INVALID.value,
                            *loaded.failure_codes,
                        ]
                    )
                )
            )
        snap = _failure_snapshot(
            repository_sha=repository_sha,
            config_digest=config_digest,
            wall_rfc=wall_rfc,
            event_time=wall_rfc,
            snapshot_state=SNAPSHOT_STATE_INVALID_INPUT,
            failure_codes=codes,
            ranking_snapshot_id=ranking_snapshot_id,
        )
        return RankingProduceResultV1(snap, False, True, snap.failure_codes)
    return produce_productive_futures_ranking_v1(
        universe_snapshot=loaded.snapshot.to_dict(),
        repository_sha=repository_sha,
        producer_observed_at_unix=producer_observed_at_unix,
        max_universe_age_seconds=max_universe_age_seconds,
        top20_limit=top20_limit,
        ranking_snapshot_id=ranking_snapshot_id,
        expected_universe_repository_sha=None,
    )


def run_productive_futures_ranking_producer_v1(
    *,
    state_root: Path,
    universe_snapshot: Mapping[str, Any] | None = None,
    universe_state_root: Path | None = None,
    repository_sha: str,
    producer_observed_at_unix: float,
    session_id: str = "default",
    max_universe_age_seconds: float = DEFAULT_MAX_UNIVERSE_AGE_SECONDS,
    top20_limit: int = TOP20_CANDIDATE_CONTEXT_LIMIT,
    ranking_snapshot_id: str | None = None,
    simulate_partial_write: bool = False,
    simulate_write_failure: bool = False,
    simulate_crash_after_persist_before_confirm: bool = False,
    release_writer: bool = True,
    dashboard_payload: Mapping[str, Any] | None = None,
    legacy_ranker_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Full productive call graph: produce → persist → verify (no selection/alpha)."""
    writer = ProductiveRankingSingleWriterV1(state_root=Path(state_root), session_id=session_id)
    try:
        writer.acquire(now_unix=producer_observed_at_unix)
    except DuplicateRankingWriterError as exc:
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
        if universe_snapshot is None and universe_state_root is not None:
            produced = produce_from_universe_state_root_v1(
                universe_state_root=Path(universe_state_root),
                repository_sha=repository_sha,
                producer_observed_at_unix=producer_observed_at_unix,
                max_universe_age_seconds=max_universe_age_seconds,
                top20_limit=top20_limit,
                ranking_snapshot_id=ranking_snapshot_id,
            )
        else:
            produced = produce_productive_futures_ranking_v1(
                universe_snapshot=universe_snapshot,
                repository_sha=repository_sha,
                producer_observed_at_unix=producer_observed_at_unix,
                max_universe_age_seconds=max_universe_age_seconds,
                top20_limit=top20_limit,
                ranking_snapshot_id=ranking_snapshot_id,
                dashboard_payload=dashboard_payload,
                legacy_ranker_payload=legacy_ranker_payload,
            )

        evidence = build_ranking_evidence_v1(
            produced=produced,
            persistence_path=str(Path(state_root)),
            persistence_verification=None,
            restart_verification=None,
        )
        try:
            persistence = persist_ranking_bundle_atomic_v1(
                state_root=Path(state_root),
                writer=writer,
                snapshot=produced.snapshot,
                evidence=evidence,
                simulate_partial_write=simulate_partial_write,
                simulate_write_failure=simulate_write_failure,
                simulate_crash_after_persist_before_confirm=(
                    simulate_crash_after_persist_before_confirm
                ),
            )
        except RankingPersistenceError as exc:
            evidence = build_ranking_evidence_v1(
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
        evidence = build_ranking_evidence_v1(
            produced=produced,
            persistence_path=persistence["persistence_path"],
            persistence_verification=persistence,
            restart_verification=restart,
        )
        persist_ranking_bundle_atomic_v1(
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
            "eligible_candidate_count": produced.snapshot.eligible_candidate_count,
            "ranked_count": len(produced.snapshot.ranked_candidates),
            "policy": policy_descriptor_v1(),
        }
    finally:
        if release_writer:
            writer.release()


def prove_restart_load_v1(
    *,
    state_root: Path,
    expected_snapshot: ProductiveFuturesRankingSnapshotV1,
) -> dict[str, Any]:
    loaded = load_and_validate_ranking_snapshot_v1(
        Path(state_root),
        expected_repository_sha=expected_snapshot.repository_sha,
        expected_config_digest=expected_snapshot.config_digest,
    )
    if not loaded.ok or loaded.snapshot is None:
        return {
            "ok": False,
            "identical_canonical_truth": False,
            "alpha_allowed_after_restart": False,
            "selection_authority_after_restart": False,
            "failure_codes": list(loaded.failure_codes),
            "detail": loaded.detail,
        }
    identical = loaded.snapshot.integrity_digest == expected_snapshot.integrity_digest
    identical = identical and loaded.snapshot.to_dict() == expected_snapshot.to_dict()
    return {
        "ok": identical,
        "identical_canonical_truth": identical,
        "alpha_allowed_after_restart": False,
        "selection_authority_after_restart": False,
        "loaded_ranking_snapshot_id": loaded.snapshot.ranking_snapshot_id,
        "loaded_integrity_digest": loaded.snapshot.integrity_digest,
        "expected_integrity_digest": expected_snapshot.integrity_digest,
        "failure_codes": [],
    }


def build_ranking_evidence_v1(
    *,
    produced: RankingProduceResultV1,
    persistence_path: str,
    persistence_verification: Optional[Mapping[str, Any]],
    restart_verification: Optional[Mapping[str, Any]],
    extra_failure_codes: tuple[str, ...] = (),
) -> dict[str, Any]:
    snap = produced.snapshot
    recomputed = snap.compute_integrity_digest()
    evidence = {
        "capability_id": CAPABILITY_ID,
        "schema_version": SCHEMA_VERSION,
        "producer_version": PRODUCER_VERSION,
        "ranking_policy_id": RANKING_POLICY_ID,
        "ranking_policy_version": RANKING_POLICY_VERSION,
        "ranking_policy_provenance": RANKING_POLICY_PROVENANCE,
        "policy_descriptor": policy_descriptor_v1(),
        "repository_sha": snap.repository_sha,
        "config_digest": snap.config_digest,
        "universe_snapshot_id": snap.universe_snapshot_id,
        "universe_source_digest": snap.universe_source_digest,
        "universe_payload_digest": snap.universe_payload_digest,
        "event_time": snap.event_time,
        "ranking_snapshot_id": snap.ranking_snapshot_id,
        "integrity_digest": snap.integrity_digest,
        "snapshot_state": snap.snapshot_state,
        "candidate_count_total": snap.candidate_count_total,
        "eligible_candidate_count": snap.eligible_candidate_count,
        "excluded_candidate_count": snap.excluded_candidate_count,
        "ranked_candidates": [c.to_dict() for c in snap.ranked_candidates],
        "excluded_candidates": [c.to_dict() for c in snap.excluded_candidates],
        "persistence_path": persistence_path,
        "persistence_verification": dict(persistence_verification or {}),
        "restart_verification": dict(restart_verification or {}),
        "deterministic_replay_verification": {
            "ok": recomputed == snap.integrity_digest,
            "recomputed_integrity_digest": recomputed,
            "snapshot_integrity_digest": snap.integrity_digest,
        },
        "authority_verification": dict(snap.authority),
        "dashboard_independence": True,
        "dashboard_input_used": False,
        "no_selection_proof": True,
        "selection_authority_created": False,
        "position_authority_created": False,
        "multi_future_authority_created": False,
        "no_alpha_proof": True,
        "no_execution_proof": True,
        "top20_candidate_context_produced": True,
        "legacy_parallel_authority_absent": True,
        "failure_codes": sorted(set(list(produced.failure_codes) + list(extra_failure_codes))),
        "alpha_allowed": False,
        "CODE_EXISTS": True,
        "BOUND": True,
        "RUNTIME_REACHABLE": True,
        "PERSISTED": bool((persistence_verification or {}).get("ok")),
        "RESTART_PROVEN": bool((restart_verification or {}).get("ok")),
        "ACTIVATED": False,
        "SINGLE_SELECTED_FUTURE_CLOSED": False,
        "MULTI_FUTURE_CLOSED": False,
    }
    return evidence
