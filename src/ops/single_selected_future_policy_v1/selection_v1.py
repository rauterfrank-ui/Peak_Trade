"""Deterministic single-future selection engine (Capability 2.3)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    ALPHA_ALLOWED_DEFAULT,
    CALL_GRAPH,
    CAPABILITY_ID,
    DEFAULT_HYSTERESIS_RANK_IMPROVEMENT,
    DEFAULT_MAX_RANKING_AGE_SECONDS,
    DEFAULT_MIN_DATA_QUALITY_STATUS,
    DEFAULT_MIN_HISTORY_SAMPLES,
    DEFAULT_MIN_HOLDING_PERIOD_SECONDS,
    DEFAULT_REFRESH_CADENCE_SECONDS,
    MAX_POSITIONS_EFFECTIVE,
    PRODUCER_VERSION,
    RANKING_CAPABILITY_ID,
    RANKING_PRODUCER_VERSION,
    RANKING_SCHEMA_VERSION,
    SCHEMA_VERSION,
    SELECTED_FUTURE_COUNT,
    SELECTION_POLICY_ID,
    SELECTION_POLICY_PROVENANCE,
    SELECTION_POLICY_VERSION,
    SINGLE_SELECTED_FUTURE,
    STATE_NO_SELECTION,
    STATE_REPLACEMENT_PENDING,
    STATE_SELECTED_ACTIVE,
    STATE_SELECTED_DEGRADED,
    STATE_SELECTED_EXIT_ONLY,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SelectionProduceResultV1,
    SingleSelectedFutureSelectionV1,
    authority_block,
    compute_config_digest_v1,
    compute_selection_id_v1,
    compute_selection_input_digest_v1,
)
from src.ops.single_selected_future_policy_v1.policy_v1 import (
    candidate_exclusion_codes_v1,
    is_selection_eligible_v1,
    rank_of_instrument_v1,
    soft_degradation_codes_v1,
)
from src.ops.single_selected_future_policy_v1.reason_codes_v1 import SelectionFailureCodeV1


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


def _valid_until_rfc(
    *,
    selected_at_event_time: str,
    refresh_cadence_seconds: float,
    min_holding_period_seconds: float,
    fallback_unix: float,
) -> str:
    """Validity horizon bound to selection event-time (not wall-clock observe time)."""
    base = _parse_event_time_unix(selected_at_event_time)
    if base is None:
        base = float(fallback_unix)
    horizon = max(float(refresh_cadence_seconds), float(min_holding_period_seconds))
    return _rfc3339(base + horizon)


def _failure_selection(
    *,
    repository_sha: str,
    config_digest: str,
    wall_rfc: str,
    event_time: str,
    failure_codes: tuple[str, ...],
    ranking_snapshot_id: str = "",
    ranking_integrity_digest: str = "",
    ranking_event_time: str = "",
    selection_input_digest: str = "",
    previous: SingleSelectedFutureSelectionV1 | None = None,
    state: str = STATE_NO_SELECTION,
    reason_codes: tuple[str, ...] | None = None,
) -> SingleSelectedFutureSelectionV1:
    reasons = reason_codes if reason_codes is not None else failure_codes
    sid = compute_selection_id_v1(
        ranking_snapshot_id=ranking_snapshot_id or "missing",
        ranking_integrity_digest=ranking_integrity_digest or "missing",
        instrument_id="",
        config_digest=config_digest,
        repository_sha=repository_sha,
        state=state,
    )
    return SingleSelectedFutureSelectionV1(
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        producer_version=PRODUCER_VERSION,
        selection_id=sid,
        instrument_id="",
        venue_native_id="",
        ranking_snapshot_id=ranking_snapshot_id,
        ranking_integrity_digest=ranking_integrity_digest,
        ranking_event_time=ranking_event_time or event_time,
        selected_at_event_time=event_time or wall_rfc,
        selected_at_wall_time=wall_rfc,
        valid_from=event_time or wall_rfc,
        valid_until=wall_rfc,
        policy_version=SELECTION_POLICY_VERSION,
        policy_id=SELECTION_POLICY_ID,
        config_digest=config_digest,
        repository_sha=repository_sha,
        reason_codes=reasons,
        state=state,
        integrity_digest="",
        previous_state=previous.state if previous is not None else STATE_NO_SELECTION,
        previous_selection_id=previous.selection_id if previous is not None else "",
        previous_instrument_id=previous.instrument_id if previous is not None else "",
        selected_future_count=SELECTED_FUTURE_COUNT,
        max_positions_effective=MAX_POSITIONS_EFFECTIVE,
        single_selected_future=SINGLE_SELECTED_FUTURE,
        multi_future_runtime_authorized=False,
        alpha_allowed=False,
        alpha_authority_for_replacement=False,
        dashboard_input_used=False,
        allowlist_input_used=False,
        manual_override_used=False,
        selection_input_digest=selection_input_digest,
        policy_provenance=SELECTION_POLICY_PROVENANCE,
        authority=authority_block(),
        call_graph=CALL_GRAPH,
        failure_codes=failure_codes,
    ).with_integrity_digest()


def _validate_ranking_dict_v1(
    ranking: Mapping[str, Any],
    *,
    expected_repository_sha: str | None,
    producer_observed_at_unix: float,
    max_ranking_age_seconds: float,
) -> tuple[Optional[ProductiveFuturesRankingSnapshotV1], tuple[str, ...]]:
    failures: list[str] = []
    try:
        snap = ProductiveFuturesRankingSnapshotV1.from_dict(ranking)
    except Exception:  # noqa: BLE001
        return None, (SelectionFailureCodeV1.RANKING_SNAPSHOT_INVALID.value,)

    if snap.schema_version != RANKING_SCHEMA_VERSION:
        failures.append(SelectionFailureCodeV1.RANKING_SCHEMA_MISMATCH.value)
    if snap.capability_id != RANKING_CAPABILITY_ID:
        failures.append(SelectionFailureCodeV1.RANKING_CAPABILITY_MISMATCH.value)
    if snap.producer_version != RANKING_PRODUCER_VERSION:
        failures.append(SelectionFailureCodeV1.RANKING_SCHEMA_MISMATCH.value)
    if not snap.ranking_snapshot_id:
        failures.append(SelectionFailureCodeV1.MISSING_RANKING_SNAPSHOT_ID.value)
    recomputed = snap.compute_integrity_digest()
    if not snap.integrity_digest or snap.integrity_digest != recomputed:
        failures.append(SelectionFailureCodeV1.RANKING_DIGEST_MISMATCH.value)
        failures.append(SelectionFailureCodeV1.INTEGRITY_FAILURE.value)
    if expected_repository_sha is not None and snap.repository_sha != expected_repository_sha:
        failures.append(SelectionFailureCodeV1.REPOSITORY_SHA_MISMATCH.value)
    if not snap.event_time:
        failures.append(SelectionFailureCodeV1.MISSING_RANKING_EVENT_TIME.value)

    event_unix = _parse_event_time_unix(snap.event_time)
    if event_unix is None and snap.event_time:
        failures.append(SelectionFailureCodeV1.RANKING_SNAPSHOT_STALE.value)
    elif event_unix is not None:
        age = producer_observed_at_unix - event_unix
        if age > float(max_ranking_age_seconds):
            failures.append(SelectionFailureCodeV1.RANKING_SNAPSHOT_STALE.value)

    if snap.selection_authority_created:
        # Cap 2.2 must not claim selection authority.
        failures.append(SelectionFailureCodeV1.RANKING_SNAPSHOT_INVALID.value)

    return snap, tuple(sorted(set(failures)))


def _pick_top_eligible(
    ranked: list[Mapping[str, Any]],
    *,
    instrument_status_by_id: Mapping[str, Mapping[str, Any]] | None,
    min_history_samples: int,
    min_data_quality_status: str,
) -> tuple[
    Optional[Mapping[str, Any]], tuple[str, ...], list[tuple[Mapping[str, Any], tuple[str, ...]]]
]:
    evaluated: list[tuple[Mapping[str, Any], tuple[str, ...]]] = []
    # Deterministic: rank asc, then venue_native_id, then canonical_instrument_id.
    ordered = sorted(
        ranked,
        key=lambda c: (
            int(c.get("rank") or 10**9),
            str(c.get("venue_native_id") or ""),
            str(c.get("canonical_instrument_id") or ""),
        ),
    )
    for cand in ordered:
        cid = str(cand.get("canonical_instrument_id") or "")
        native = str(cand.get("venue_native_id") or "")
        status = None
        if instrument_status_by_id:
            status = instrument_status_by_id.get(cid) or instrument_status_by_id.get(native)
        codes = candidate_exclusion_codes_v1(
            cand,
            instrument_status=status,
            min_history_samples=min_history_samples,
            min_data_quality_status=min_data_quality_status,
        )
        evaluated.append((cand, codes))
        if is_selection_eligible_v1(codes):
            return cand, (), evaluated
    if not ordered:
        return None, (SelectionFailureCodeV1.NO_CANDIDATES.value,), evaluated
    # Aggregate top exclusion reasons for evidence.
    top_codes = (
        evaluated[0][1] if evaluated else (SelectionFailureCodeV1.NO_ELIGIBLE_SELECTION.value,)
    )
    return (
        None,
        tuple(sorted(set(top_codes + (SelectionFailureCodeV1.NO_ELIGIBLE_SELECTION.value,)))),
        evaluated,
    )


def produce_single_selected_future_v1(
    *,
    ranking_snapshot: Mapping[str, Any] | None,
    repository_sha: str,
    producer_observed_at_unix: float,
    previous_selection: Mapping[str, Any] | SingleSelectedFutureSelectionV1 | None = None,
    open_position_instrument_id: str | None = None,
    instrument_status_by_id: Mapping[str, Mapping[str, Any]] | None = None,
    max_ranking_age_seconds: float = DEFAULT_MAX_RANKING_AGE_SECONDS,
    refresh_cadence_seconds: float = DEFAULT_REFRESH_CADENCE_SECONDS,
    min_holding_period_seconds: float = DEFAULT_MIN_HOLDING_PERIOD_SECONDS,
    hysteresis_rank_improvement: int = DEFAULT_HYSTERESIS_RANK_IMPROVEMENT,
    min_history_samples: int = DEFAULT_MIN_HISTORY_SAMPLES,
    min_data_quality_status: str = DEFAULT_MIN_DATA_QUALITY_STATUS,
    expected_ranking_repository_sha: str | None = None,
    dashboard_payload: Mapping[str, Any] | None = None,
    allowlist_payload: Mapping[str, Any] | None = None,
    legacy_selection_payload: Mapping[str, Any] | None = None,
    manual_override_payload: Mapping[str, Any] | None = None,
) -> SelectionProduceResultV1:
    """Produce exactly one selected future (or NO_SELECTION) from Cap 2.2 ranking."""
    wall_rfc = _rfc3339(producer_observed_at_unix)
    config_digest = compute_config_digest_v1(
        repository_sha=repository_sha,
        max_ranking_age_seconds=max_ranking_age_seconds,
        refresh_cadence_seconds=refresh_cadence_seconds,
        min_holding_period_seconds=min_holding_period_seconds,
        hysteresis_rank_improvement=hysteresis_rank_improvement,
        min_history_samples=min_history_samples,
        min_data_quality_status=min_data_quality_status,
    )

    previous: SingleSelectedFutureSelectionV1 | None = None
    if previous_selection is not None:
        if isinstance(previous_selection, SingleSelectedFutureSelectionV1):
            previous = previous_selection
        else:
            previous = SingleSelectedFutureSelectionV1.from_dict(previous_selection)

    if dashboard_payload is not None:
        sel = _failure_selection(
            repository_sha=repository_sha,
            config_digest=config_digest,
            wall_rfc=wall_rfc,
            event_time=wall_rfc,
            failure_codes=(SelectionFailureCodeV1.DASHBOARD_INPUT_FORBIDDEN.value,),
            previous=previous,
        )
        return SelectionProduceResultV1(sel, False, True, sel.failure_codes, True)

    if allowlist_payload is not None:
        sel = _failure_selection(
            repository_sha=repository_sha,
            config_digest=config_digest,
            wall_rfc=wall_rfc,
            event_time=wall_rfc,
            failure_codes=(SelectionFailureCodeV1.ALLOWLIST_INPUT_FORBIDDEN.value,),
            previous=previous,
        )
        return SelectionProduceResultV1(sel, False, True, sel.failure_codes, True)

    if legacy_selection_payload is not None:
        sel = _failure_selection(
            repository_sha=repository_sha,
            config_digest=config_digest,
            wall_rfc=wall_rfc,
            event_time=wall_rfc,
            failure_codes=(SelectionFailureCodeV1.LEGACY_SELECTION_INPUT_FORBIDDEN.value,),
            previous=previous,
        )
        return SelectionProduceResultV1(sel, False, True, sel.failure_codes, True)

    if manual_override_payload is not None:
        sel = _failure_selection(
            repository_sha=repository_sha,
            config_digest=config_digest,
            wall_rfc=wall_rfc,
            event_time=wall_rfc,
            failure_codes=(SelectionFailureCodeV1.MANUAL_OVERRIDE_FORBIDDEN.value,),
            previous=previous,
        )
        return SelectionProduceResultV1(sel, False, True, sel.failure_codes, True)

    if ranking_snapshot is None:
        sel = _failure_selection(
            repository_sha=repository_sha,
            config_digest=config_digest,
            wall_rfc=wall_rfc,
            event_time=wall_rfc,
            failure_codes=(
                SelectionFailureCodeV1.RANKING_SNAPSHOT_MISSING.value,
                SelectionFailureCodeV1.ALPHA_BLOCKED.value,
            ),
            previous=previous,
        )
        return SelectionProduceResultV1(sel, False, True, sel.failure_codes, True)

    if not isinstance(ranking_snapshot, Mapping):
        sel = _failure_selection(
            repository_sha=repository_sha,
            config_digest=config_digest,
            wall_rfc=wall_rfc,
            event_time=wall_rfc,
            failure_codes=(SelectionFailureCodeV1.RANKING_SNAPSHOT_INVALID.value,),
            previous=previous,
        )
        return SelectionProduceResultV1(sel, False, True, sel.failure_codes, True)

    ranking, failures = _validate_ranking_dict_v1(
        ranking_snapshot,
        expected_repository_sha=expected_ranking_repository_sha,
        producer_observed_at_unix=producer_observed_at_unix,
        max_ranking_age_seconds=max_ranking_age_seconds,
    )
    if ranking is None or failures:
        # Stale/invalid ranking with open position → EXIT_ONLY on previous instrument.
        if (
            previous is not None
            and previous.instrument_id
            and open_position_instrument_id
            and open_position_instrument_id == previous.instrument_id
        ):
            state = STATE_SELECTED_EXIT_ONLY
            codes = tuple(
                sorted(
                    set(
                        list(failures or (SelectionFailureCodeV1.RANKING_SNAPSHOT_INVALID.value,))
                        + [
                            SelectionFailureCodeV1.OPEN_POSITION_BLOCKS_SWITCH.value,
                            SelectionFailureCodeV1.ALPHA_BLOCKED.value,
                        ]
                    )
                )
            )
            sel = SingleSelectedFutureSelectionV1(
                schema_version=SCHEMA_VERSION,
                capability_id=CAPABILITY_ID,
                producer_version=PRODUCER_VERSION,
                selection_id=compute_selection_id_v1(
                    ranking_snapshot_id=(
                        ranking.ranking_snapshot_id if ranking is not None else "invalid"
                    ),
                    ranking_integrity_digest=(
                        ranking.integrity_digest if ranking is not None else "invalid"
                    ),
                    instrument_id=previous.instrument_id,
                    config_digest=config_digest,
                    repository_sha=repository_sha,
                    state=state,
                ),
                instrument_id=previous.instrument_id,
                venue_native_id=previous.venue_native_id,
                ranking_snapshot_id=(
                    ranking.ranking_snapshot_id
                    if ranking is not None
                    else previous.ranking_snapshot_id
                ),
                ranking_integrity_digest=(
                    ranking.integrity_digest
                    if ranking is not None
                    else previous.ranking_integrity_digest
                ),
                ranking_event_time=(
                    ranking.event_time if ranking is not None else previous.ranking_event_time
                ),
                selected_at_event_time=previous.selected_at_event_time,
                selected_at_wall_time=wall_rfc,
                valid_from=previous.valid_from,
                valid_until=wall_rfc,
                policy_version=SELECTION_POLICY_VERSION,
                policy_id=SELECTION_POLICY_ID,
                config_digest=config_digest,
                repository_sha=repository_sha,
                reason_codes=codes,
                state=state,
                integrity_digest="",
                previous_state=previous.state,
                previous_selection_id=previous.selection_id,
                previous_instrument_id=previous.instrument_id,
                selected_rank=previous.selected_rank,
                selected_future_count=SELECTED_FUTURE_COUNT,
                max_positions_effective=MAX_POSITIONS_EFFECTIVE,
                single_selected_future=True,
                multi_future_runtime_authorized=False,
                alpha_allowed=False,
                alpha_authority_for_replacement=False,
                open_position_present=True,
                open_position_instrument_id=open_position_instrument_id,
                selection_input_digest="",
                authority=authority_block(),
                call_graph=CALL_GRAPH,
                failure_codes=codes,
            ).with_integrity_digest()
            return SelectionProduceResultV1(sel, True, False, codes, True)

        sel = _failure_selection(
            repository_sha=repository_sha,
            config_digest=config_digest,
            wall_rfc=wall_rfc,
            event_time=(
                ranking.event_time if ranking is not None and ranking.event_time else wall_rfc
            ),
            failure_codes=tuple(
                sorted(
                    set(
                        list(failures or (SelectionFailureCodeV1.RANKING_SNAPSHOT_INVALID.value,))
                        + [SelectionFailureCodeV1.ALPHA_BLOCKED.value]
                    )
                )
            ),
            ranking_snapshot_id=ranking.ranking_snapshot_id if ranking is not None else "",
            ranking_integrity_digest=ranking.integrity_digest if ranking is not None else "",
            ranking_event_time=ranking.event_time if ranking is not None else "",
            previous=previous,
        )
        return SelectionProduceResultV1(sel, False, True, sel.failure_codes, True)

    ranked = [c.to_dict() for c in ranking.ranked_candidates]
    input_digest = compute_selection_input_digest_v1(
        ranking_snapshot_id=ranking.ranking_snapshot_id,
        ranking_integrity_digest=ranking.integrity_digest,
        ranking_event_time=ranking.event_time,
        config_digest=config_digest,
        open_position_instrument_id=open_position_instrument_id or "",
        instrument_status_overlay=dict(instrument_status_by_id or {}),
    )

    top, excl_codes, _evaluated = _pick_top_eligible(
        ranked,
        instrument_status_by_id=instrument_status_by_id,
        min_history_samples=min_history_samples,
        min_data_quality_status=min_data_quality_status,
    )

    open_pos = str(open_position_instrument_id or "").strip()
    open_present = bool(open_pos)

    # No eligible candidate path.
    if top is None:
        if open_present and previous is not None and previous.instrument_id == open_pos:
            state = STATE_SELECTED_EXIT_ONLY
            codes = tuple(
                sorted(
                    set(
                        list(excl_codes)
                        + [
                            SelectionFailureCodeV1.OPEN_POSITION_BLOCKS_SWITCH.value,
                            SelectionFailureCodeV1.ALPHA_BLOCKED.value,
                        ]
                    )
                )
            )
            sel = SingleSelectedFutureSelectionV1(
                schema_version=SCHEMA_VERSION,
                capability_id=CAPABILITY_ID,
                producer_version=PRODUCER_VERSION,
                selection_id=compute_selection_id_v1(
                    ranking_snapshot_id=ranking.ranking_snapshot_id,
                    ranking_integrity_digest=ranking.integrity_digest,
                    instrument_id=previous.instrument_id,
                    config_digest=config_digest,
                    repository_sha=repository_sha,
                    state=state,
                ),
                instrument_id=previous.instrument_id,
                venue_native_id=previous.venue_native_id,
                ranking_snapshot_id=ranking.ranking_snapshot_id,
                ranking_integrity_digest=ranking.integrity_digest,
                ranking_event_time=ranking.event_time,
                selected_at_event_time=previous.selected_at_event_time,
                selected_at_wall_time=wall_rfc,
                valid_from=previous.valid_from,
                valid_until=_valid_until_rfc(
                    selected_at_event_time=previous.selected_at_event_time,
                    refresh_cadence_seconds=refresh_cadence_seconds,
                    min_holding_period_seconds=min_holding_period_seconds,
                    fallback_unix=producer_observed_at_unix,
                ),
                policy_version=SELECTION_POLICY_VERSION,
                policy_id=SELECTION_POLICY_ID,
                config_digest=config_digest,
                repository_sha=repository_sha,
                reason_codes=codes,
                state=state,
                integrity_digest="",
                previous_state=previous.state,
                previous_selection_id=previous.selection_id,
                previous_instrument_id=previous.instrument_id,
                selected_rank=previous.selected_rank,
                selected_future_count=SELECTED_FUTURE_COUNT,
                max_positions_effective=MAX_POSITIONS_EFFECTIVE,
                single_selected_future=True,
                multi_future_runtime_authorized=False,
                alpha_allowed=False,
                alpha_authority_for_replacement=False,
                open_position_present=True,
                open_position_instrument_id=open_pos,
                selection_input_digest=input_digest,
                authority=authority_block(),
                call_graph=CALL_GRAPH,
                failure_codes=codes,
            ).with_integrity_digest()
            return SelectionProduceResultV1(sel, True, False, codes, True)

        codes = tuple(sorted(set(list(excl_codes) + [SelectionFailureCodeV1.ALPHA_BLOCKED.value])))
        sel = _failure_selection(
            repository_sha=repository_sha,
            config_digest=config_digest,
            wall_rfc=wall_rfc,
            event_time=ranking.event_time,
            failure_codes=codes,
            ranking_snapshot_id=ranking.ranking_snapshot_id,
            ranking_integrity_digest=ranking.integrity_digest,
            ranking_event_time=ranking.event_time,
            selection_input_digest=input_digest,
            previous=previous,
        )
        return SelectionProduceResultV1(sel, True, False, codes, True)

    candidate_id = str(top.get("canonical_instrument_id") or "")
    candidate_native = str(top.get("venue_native_id") or "")
    candidate_rank = int(top.get("rank") or 0)

    reasons: list[str] = []
    state = STATE_SELECTED_ACTIVE
    instrument_id = candidate_id
    venue_native_id = candidate_native
    selected_rank = candidate_rank
    replacement_id = ""
    replacement_native = ""
    selected_at_event = ranking.event_time
    valid_from = ranking.event_time

    # Evaluate degradation of selected/current instrument via overlay.
    status = None
    if instrument_status_by_id:
        status = instrument_status_by_id.get(candidate_id) or instrument_status_by_id.get(
            candidate_native
        )
    top_codes = candidate_exclusion_codes_v1(
        top,
        instrument_status=status,
        min_history_samples=min_history_samples,
        min_data_quality_status=min_data_quality_status,
    )
    # top is eligible by construction; overlay-only soft degradation after pick is N/A.
    _ = top_codes

    if previous is not None and previous.instrument_id:
        prev_id = previous.instrument_id
        prev_rank = rank_of_instrument_v1(ranked, prev_id)
        prev_selected_unix = _parse_event_time_unix(previous.selected_at_event_time)
        holding_elapsed = (
            producer_observed_at_unix - prev_selected_unix
            if prev_selected_unix is not None
            else float("inf")
        )

        # Check current selection health for DEGRADED / EXIT_ONLY.
        prev_status = None
        if instrument_status_by_id:
            prev_status = instrument_status_by_id.get(prev_id) or instrument_status_by_id.get(
                previous.venue_native_id
            )
        prev_cand = next(
            (
                c
                for c in ranked
                if str(c.get("canonical_instrument_id") or "") == prev_id
                or str(c.get("venue_native_id") or "") == previous.venue_native_id
            ),
            None,
        )
        if prev_cand is not None:
            prev_excl = candidate_exclusion_codes_v1(
                prev_cand,
                instrument_status=prev_status,
                min_history_samples=min_history_samples,
                min_data_quality_status=min_data_quality_status,
            )
        elif prev_status is not None:
            prev_excl = candidate_exclusion_codes_v1(
                {
                    "eligibility_status": "ELIGIBLE",
                    "data_quality_status": str(prev_status.get("data_quality_status") or "PASS"),
                },
                instrument_status=prev_status,
                min_history_samples=min_history_samples,
                min_data_quality_status=min_data_quality_status,
            )
        else:
            prev_excl = ()

        switch_desired = candidate_id != prev_id

        if open_present and open_pos == prev_id and switch_desired:
            # Keep current instrument; persist replacement as pending only.
            state = STATE_REPLACEMENT_PENDING
            instrument_id = prev_id
            venue_native_id = previous.venue_native_id
            selected_rank = int(prev_rank or previous.selected_rank or 0)
            replacement_id = candidate_id
            replacement_native = candidate_native
            selected_at_event = previous.selected_at_event_time
            valid_from = previous.valid_from
            reasons.extend(
                [
                    SelectionFailureCodeV1.OPEN_POSITION_BLOCKS_SWITCH.value,
                    SelectionFailureCodeV1.REPLACEMENT_PENDING.value,
                    SelectionFailureCodeV1.ALPHA_BLOCKED.value,
                ]
            )
        elif open_present and open_pos == prev_id and prev_excl:
            state = STATE_SELECTED_EXIT_ONLY
            instrument_id = prev_id
            venue_native_id = previous.venue_native_id
            selected_rank = int(prev_rank or previous.selected_rank or 0)
            selected_at_event = previous.selected_at_event_time
            valid_from = previous.valid_from
            reasons.extend(list(prev_excl))
            reasons.append(SelectionFailureCodeV1.ALPHA_BLOCKED.value)
        elif switch_desired:
            # Min holding + hysteresis for churn control when no open position blocks.
            if holding_elapsed < float(min_holding_period_seconds):
                state = STATE_SELECTED_ACTIVE
                instrument_id = prev_id
                venue_native_id = previous.venue_native_id
                selected_rank = int(prev_rank or previous.selected_rank or 0)
                selected_at_event = previous.selected_at_event_time
                valid_from = previous.valid_from
                reasons.append(SelectionFailureCodeV1.WITHIN_MIN_HOLDING_PERIOD.value)
            elif prev_rank is not None and (prev_rank - candidate_rank) < int(
                hysteresis_rank_improvement
            ):
                # New candidate not sufficiently better.
                state = STATE_SELECTED_ACTIVE
                instrument_id = prev_id
                venue_native_id = previous.venue_native_id
                selected_rank = int(prev_rank)
                selected_at_event = previous.selected_at_event_time
                valid_from = previous.valid_from
                reasons.append(SelectionFailureCodeV1.HYSTERESIS_BLOCKS_CHURN.value)
            else:
                state = STATE_SELECTED_ACTIVE
                reasons.append("SELECTION_REFRESHED")
        else:
            # Same instrument retained.
            soft = soft_degradation_codes_v1(prev_status)
            if prev_excl:
                # Hard exclusions on retained instrument without open position already
                # force a different top; if we are here, treat as degraded retention.
                state = STATE_SELECTED_DEGRADED
                reasons.extend(list(prev_excl))
            elif soft:
                state = STATE_SELECTED_DEGRADED
                reasons.extend(list(soft))
            else:
                state = STATE_SELECTED_ACTIVE
            instrument_id = prev_id
            venue_native_id = previous.venue_native_id
            selected_rank = int(prev_rank or candidate_rank or previous.selected_rank or 0)
            selected_at_event = previous.selected_at_event_time
            valid_from = previous.valid_from
    else:
        reasons.append("INITIAL_SELECTION")
        soft_new = soft_degradation_codes_v1(status)
        if soft_new:
            state = STATE_SELECTED_DEGRADED
            reasons.extend(list(soft_new))

    # Alpha remains non-activated in Cap 2.3; selection authority only.
    alpha_allowed = ALPHA_ALLOWED_DEFAULT
    alpha_blocked = True
    if state in {STATE_SELECTED_EXIT_ONLY, STATE_REPLACEMENT_PENDING, STATE_NO_SELECTION}:
        reasons.append(SelectionFailureCodeV1.ALPHA_BLOCKED.value)
    if state == STATE_SELECTED_DEGRADED:
        reasons.append(SelectionFailureCodeV1.ALPHA_BLOCKED.value)

    failure_codes = tuple(
        sorted(
            {
                c
                for c in reasons
                if c
                in {
                    SelectionFailureCodeV1.OPEN_POSITION_BLOCKS_SWITCH.value,
                    SelectionFailureCodeV1.REPLACEMENT_PENDING.value,
                    SelectionFailureCodeV1.ALPHA_BLOCKED.value,
                    SelectionFailureCodeV1.DATA_QUALITY_FAILURE.value,
                    SelectionFailureCodeV1.MINIMUM_HISTORY_FAILURE.value,
                    SelectionFailureCodeV1.MARK_PRICE_MISSING.value,
                    SelectionFailureCodeV1.INSTRUMENT_SUSPENDED.value,
                    SelectionFailureCodeV1.INSTRUMENT_INVALID.value,
                    SelectionFailureCodeV1.DATA_LOSS.value,
                    SelectionFailureCodeV1.WITHIN_MIN_HOLDING_PERIOD.value,
                    SelectionFailureCodeV1.HYSTERESIS_BLOCKS_CHURN.value,
                }
            }
        )
    )

    sel = SingleSelectedFutureSelectionV1(
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        producer_version=PRODUCER_VERSION,
        selection_id=compute_selection_id_v1(
            ranking_snapshot_id=ranking.ranking_snapshot_id,
            ranking_integrity_digest=ranking.integrity_digest,
            instrument_id=instrument_id,
            config_digest=config_digest,
            repository_sha=repository_sha,
            state=state,
        ),
        instrument_id=instrument_id,
        venue_native_id=venue_native_id,
        ranking_snapshot_id=ranking.ranking_snapshot_id,
        ranking_integrity_digest=ranking.integrity_digest,
        ranking_event_time=ranking.event_time,
        selected_at_event_time=selected_at_event,
        selected_at_wall_time=wall_rfc,
        valid_from=valid_from,
        valid_until=_valid_until_rfc(
            selected_at_event_time=selected_at_event,
            refresh_cadence_seconds=refresh_cadence_seconds,
            min_holding_period_seconds=min_holding_period_seconds,
            fallback_unix=producer_observed_at_unix,
        ),
        policy_version=SELECTION_POLICY_VERSION,
        policy_id=SELECTION_POLICY_ID,
        config_digest=config_digest,
        repository_sha=repository_sha,
        reason_codes=tuple(sorted(set(reasons))),
        state=state,
        integrity_digest="",
        previous_state=previous.state if previous is not None else STATE_NO_SELECTION,
        previous_selection_id=previous.selection_id if previous is not None else "",
        previous_instrument_id=previous.instrument_id if previous is not None else "",
        replacement_instrument_id=replacement_id,
        replacement_venue_native_id=replacement_native,
        selected_rank=selected_rank,
        selected_future_count=SELECTED_FUTURE_COUNT,
        max_positions_effective=MAX_POSITIONS_EFFECTIVE,
        single_selected_future=True,
        multi_future_runtime_authorized=False,
        alpha_allowed=alpha_allowed,
        alpha_authority_for_replacement=False,
        open_position_present=open_present,
        open_position_instrument_id=open_pos,
        dashboard_input_used=False,
        allowlist_input_used=False,
        manual_override_used=False,
        selection_input_digest=input_digest,
        policy_provenance=SELECTION_POLICY_PROVENANCE,
        authority=authority_block(),
        call_graph=CALL_GRAPH,
        failure_codes=failure_codes,
    ).with_integrity_digest()

    # Exactly one selected future when not NO_SELECTION.
    assert sel.selected_future_count == 1
    assert sel.max_positions_effective == 1
    assert sel.multi_future_runtime_authorized is False
    if sel.state != STATE_NO_SELECTION:
        assert bool(sel.instrument_id)

    return SelectionProduceResultV1(
        selection=sel,
        ok=True,
        hard_stop=False,
        failure_codes=failure_codes,
        alpha_blocked=alpha_blocked,
    )
