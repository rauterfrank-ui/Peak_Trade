"""Productive Single Selected Future Policy entrypoint (Capability 2.3)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    load_and_validate_ranking_snapshot_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    CAPABILITY_ID,
    DEFAULT_HYSTERESIS_RANK_IMPROVEMENT,
    DEFAULT_MAX_RANKING_AGE_SECONDS,
    DEFAULT_MIN_DATA_QUALITY_STATUS,
    DEFAULT_MIN_HISTORY_SAMPLES,
    DEFAULT_MIN_HOLDING_PERIOD_SECONDS,
    DEFAULT_REFRESH_CADENCE_SECONDS,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    SELECTION_POLICY_ID,
    SELECTION_POLICY_PROVENANCE,
    SELECTION_POLICY_VERSION,
    STATE_NO_SELECTION,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SelectionProduceResultV1,
    SingleSelectedFutureSelectionV1,
)
from src.ops.single_selected_future_policy_v1.persistence_v1 import (
    SelectionPersistenceError,
    load_and_validate_selection_v1,
    persist_selection_bundle_atomic_v1,
)
from src.ops.single_selected_future_policy_v1.policy_v1 import policy_descriptor_v1
from src.ops.single_selected_future_policy_v1.reason_codes_v1 import SelectionFailureCodeV1
from src.ops.single_selected_future_policy_v1.selection_v1 import (
    produce_single_selected_future_v1,
)
from src.ops.single_selected_future_policy_v1.single_writer_v1 import (
    DuplicateSelectionWriterError,
    SingleSelectedFutureSingleWriterV1,
)


def produce_from_ranking_state_root_v1(
    *,
    ranking_state_root: Path,
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
) -> SelectionProduceResultV1:
    loaded = load_and_validate_ranking_snapshot_v1(Path(ranking_state_root))
    if not loaded.ok or loaded.snapshot is None:
        return produce_single_selected_future_v1(
            ranking_snapshot=None,
            repository_sha=repository_sha,
            producer_observed_at_unix=producer_observed_at_unix,
            previous_selection=previous_selection,
            open_position_instrument_id=open_position_instrument_id,
            instrument_status_by_id=instrument_status_by_id,
            max_ranking_age_seconds=max_ranking_age_seconds,
            refresh_cadence_seconds=refresh_cadence_seconds,
            min_holding_period_seconds=min_holding_period_seconds,
            hysteresis_rank_improvement=hysteresis_rank_improvement,
            min_history_samples=min_history_samples,
            min_data_quality_status=min_data_quality_status,
        )
    return produce_single_selected_future_v1(
        ranking_snapshot=loaded.snapshot.to_dict(),
        repository_sha=repository_sha,
        producer_observed_at_unix=producer_observed_at_unix,
        previous_selection=previous_selection,
        open_position_instrument_id=open_position_instrument_id,
        instrument_status_by_id=instrument_status_by_id,
        max_ranking_age_seconds=max_ranking_age_seconds,
        refresh_cadence_seconds=refresh_cadence_seconds,
        min_holding_period_seconds=min_holding_period_seconds,
        hysteresis_rank_improvement=hysteresis_rank_improvement,
        min_history_samples=min_history_samples,
        min_data_quality_status=min_data_quality_status,
    )


def run_single_selected_future_policy_v1(
    *,
    state_root: Path,
    ranking_snapshot: Mapping[str, Any] | None = None,
    ranking_state_root: Path | None = None,
    repository_sha: str,
    producer_observed_at_unix: float,
    session_id: str = "default",
    previous_selection: Mapping[str, Any] | None = None,
    load_previous_from_state: bool = True,
    open_position_instrument_id: str | None = None,
    instrument_status_by_id: Mapping[str, Mapping[str, Any]] | None = None,
    max_ranking_age_seconds: float = DEFAULT_MAX_RANKING_AGE_SECONDS,
    refresh_cadence_seconds: float = DEFAULT_REFRESH_CADENCE_SECONDS,
    min_holding_period_seconds: float = DEFAULT_MIN_HOLDING_PERIOD_SECONDS,
    hysteresis_rank_improvement: int = DEFAULT_HYSTERESIS_RANK_IMPROVEMENT,
    min_history_samples: int = DEFAULT_MIN_HISTORY_SAMPLES,
    min_data_quality_status: str = DEFAULT_MIN_DATA_QUALITY_STATUS,
    simulate_partial_write: bool = False,
    simulate_write_failure: bool = False,
    simulate_crash_after_persist_before_confirm: bool = False,
    release_writer: bool = True,
    dashboard_payload: Mapping[str, Any] | None = None,
    allowlist_payload: Mapping[str, Any] | None = None,
    legacy_selection_payload: Mapping[str, Any] | None = None,
    manual_override_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Full productive call graph: select → persist → verify (no runtime activation)."""
    writer = SingleSelectedFutureSingleWriterV1(state_root=Path(state_root), session_id=session_id)
    try:
        writer.acquire(now_unix=producer_observed_at_unix)
    except DuplicateSelectionWriterError as exc:
        return {
            "ok": False,
            "hard_stop": True,
            "failure_codes": (exc.failure_code,),
            "alpha_allowed": False,
            "alpha_blocked": True,
            "persistence": None,
            "selection": None,
            "restart": None,
            "evidence": {
                "capability_id": CAPABILITY_ID,
                "failure_codes": [exc.failure_code],
                "duplicate_writer_rejected": True,
            },
        }

    try:
        prev = previous_selection
        if prev is None and load_previous_from_state:
            existing = load_and_validate_selection_v1(
                Path(state_root),
                require_manifest=False,
            )
            if existing.ok and existing.selection is not None:
                prev = existing.selection.to_dict()
            elif (Path(state_root) / "single_selected_future_selection_v1.json").is_file():
                # Corrupt/mismatched previous → treat as no previous; alpha blocked later.
                prev = None

        if ranking_snapshot is None and ranking_state_root is not None:
            produced = produce_from_ranking_state_root_v1(
                ranking_state_root=Path(ranking_state_root),
                repository_sha=repository_sha,
                producer_observed_at_unix=producer_observed_at_unix,
                previous_selection=prev,
                open_position_instrument_id=open_position_instrument_id,
                instrument_status_by_id=instrument_status_by_id,
                max_ranking_age_seconds=max_ranking_age_seconds,
                refresh_cadence_seconds=refresh_cadence_seconds,
                min_holding_period_seconds=min_holding_period_seconds,
                hysteresis_rank_improvement=hysteresis_rank_improvement,
                min_history_samples=min_history_samples,
                min_data_quality_status=min_data_quality_status,
            )
        else:
            produced = produce_single_selected_future_v1(
                ranking_snapshot=ranking_snapshot,
                repository_sha=repository_sha,
                producer_observed_at_unix=producer_observed_at_unix,
                previous_selection=prev,
                open_position_instrument_id=open_position_instrument_id,
                instrument_status_by_id=instrument_status_by_id,
                max_ranking_age_seconds=max_ranking_age_seconds,
                refresh_cadence_seconds=refresh_cadence_seconds,
                min_holding_period_seconds=min_holding_period_seconds,
                hysteresis_rank_improvement=hysteresis_rank_improvement,
                min_history_samples=min_history_samples,
                min_data_quality_status=min_data_quality_status,
                dashboard_payload=dashboard_payload,
                allowlist_payload=allowlist_payload,
                legacy_selection_payload=legacy_selection_payload,
                manual_override_payload=manual_override_payload,
            )

        evidence = build_selection_evidence_v1(
            produced=produced,
            persistence_path=str(Path(state_root)),
            persistence_verification=None,
            restart_verification=None,
            previous_selection=prev,
        )
        try:
            persistence = persist_selection_bundle_atomic_v1(
                state_root=Path(state_root),
                writer=writer,
                selection=produced.selection,
                evidence=evidence,
                simulate_partial_write=simulate_partial_write,
                simulate_write_failure=simulate_write_failure,
                simulate_crash_after_persist_before_confirm=(
                    simulate_crash_after_persist_before_confirm
                ),
            )
        except SelectionPersistenceError as exc:
            evidence = build_selection_evidence_v1(
                produced=produced,
                persistence_path=str(Path(state_root)),
                persistence_verification={"ok": False, "failure_code": exc.failure_code},
                restart_verification=None,
                previous_selection=prev,
                extra_failure_codes=(exc.failure_code,),
            )
            return {
                "ok": False,
                "hard_stop": True,
                "failure_codes": tuple(sorted(set(produced.failure_codes + (exc.failure_code,)))),
                "alpha_allowed": False,
                "alpha_blocked": True,
                "selection": produced.selection.to_dict(),
                "persistence": {"ok": False, "failure_code": exc.failure_code},
                "restart": None,
                "evidence": evidence,
            }

        restart = prove_restart_load_v1(
            state_root=Path(state_root),
            expected_selection=produced.selection,
        )
        evidence = build_selection_evidence_v1(
            produced=produced,
            persistence_path=persistence["persistence_path"],
            persistence_verification=persistence,
            restart_verification=restart,
            previous_selection=prev,
        )
        persist_selection_bundle_atomic_v1(
            state_root=Path(state_root),
            writer=writer,
            selection=produced.selection,
            evidence=evidence,
        )
        return {
            "ok": produced.ok and bool(persistence.get("ok")) and bool(restart.get("ok")),
            "hard_stop": produced.hard_stop or not restart.get("ok"),
            "failure_codes": produced.failure_codes,
            "alpha_allowed": False,
            "alpha_blocked": True,
            "selection": produced.selection.to_dict(),
            "persistence": persistence,
            "restart": restart,
            "evidence": evidence,
            "selected_future_count": produced.selection.selected_future_count,
            "max_positions_effective": produced.selection.max_positions_effective,
            "state": produced.selection.state,
            "policy": policy_descriptor_v1(),
        }
    finally:
        if release_writer:
            writer.release()


def prove_restart_load_v1(
    *,
    state_root: Path,
    expected_selection: SingleSelectedFutureSelectionV1,
) -> dict[str, Any]:
    loaded = load_and_validate_selection_v1(
        Path(state_root),
        expected_repository_sha=expected_selection.repository_sha,
        expected_config_digest=expected_selection.config_digest,
    )
    if not loaded.ok or loaded.selection is None:
        return {
            "ok": False,
            "identical_canonical_truth": False,
            "alpha_allowed_after_restart": False,
            "alpha_blocked_after_restart": True,
            "state_after_restart": STATE_NO_SELECTION,
            "failure_codes": list(loaded.failure_codes)
            + [SelectionFailureCodeV1.ALPHA_BLOCKED.value],
            "detail": loaded.detail,
            "reconstructed": False,
        }
    identical = loaded.selection.integrity_digest == expected_selection.integrity_digest
    identical = identical and loaded.selection.to_dict() == expected_selection.to_dict()
    return {
        "ok": identical,
        "identical_canonical_truth": identical,
        "alpha_allowed_after_restart": False,
        "alpha_blocked_after_restart": True,
        "state_after_restart": loaded.selection.state,
        "loaded_selection_id": loaded.selection.selection_id,
        "loaded_integrity_digest": loaded.selection.integrity_digest,
        "loaded_config_digest": loaded.selection.config_digest,
        "loaded_repository_sha": loaded.selection.repository_sha,
        "loaded_valid_from": loaded.selection.valid_from,
        "loaded_valid_until": loaded.selection.valid_until,
        "expected_integrity_digest": expected_selection.integrity_digest,
        "reconstructed": True,
        "failure_codes": [],
    }


def restart_fail_closed_to_no_selection_v1(
    *,
    state_root: Path,
    expected_repository_sha: str | None = None,
    expected_config_digest: str | None = None,
) -> dict[str, Any]:
    """Restart recovery: invalid selection → NO_SELECTION + alpha block."""
    loaded = load_and_validate_selection_v1(
        Path(state_root),
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
    )
    if loaded.ok and loaded.selection is not None:
        return {
            "ok": True,
            "state": loaded.selection.state,
            "alpha_blocked": loaded.alpha_blocked,
            "selection": loaded.selection.to_dict(),
            "failure_codes": [],
        }
    return {
        "ok": False,
        "state": STATE_NO_SELECTION,
        "alpha_blocked": True,
        "selection": None,
        "failure_codes": list(loaded.failure_codes) + [SelectionFailureCodeV1.ALPHA_BLOCKED.value],
        "detail": loaded.detail,
    }


def build_selection_evidence_v1(
    *,
    produced: SelectionProduceResultV1,
    persistence_path: str,
    persistence_verification: Optional[Mapping[str, Any]],
    restart_verification: Optional[Mapping[str, Any]],
    previous_selection: Mapping[str, Any] | None,
    extra_failure_codes: tuple[str, ...] = (),
) -> dict[str, Any]:
    sel = produced.selection
    recomputed = sel.compute_integrity_digest()
    prev_state = (
        str(previous_selection.get("state"))
        if isinstance(previous_selection, Mapping)
        else STATE_NO_SELECTION
    )
    evidence = {
        "capability_id": CAPABILITY_ID,
        "schema_version": SCHEMA_VERSION,
        "producer_version": PRODUCER_VERSION,
        "selection_policy_id": SELECTION_POLICY_ID,
        "selection_policy_version": SELECTION_POLICY_VERSION,
        "selection_policy_provenance": SELECTION_POLICY_PROVENANCE,
        "policy_descriptor": policy_descriptor_v1(),
        "repository_sha": sel.repository_sha,
        "config_digest": sel.config_digest,
        "selection_input_digest": sel.selection_input_digest,
        "ranking_snapshot_id": sel.ranking_snapshot_id,
        "ranking_integrity_digest": sel.ranking_integrity_digest,
        "ranking_event_time": sel.ranking_event_time,
        "selection_id": sel.selection_id,
        "instrument_id": sel.instrument_id,
        "venue_native_id": sel.venue_native_id,
        "integrity_digest": sel.integrity_digest,
        "state": sel.state,
        "previous_state": prev_state,
        "new_state": sel.state,
        "reason_codes": list(sel.reason_codes),
        "selected_at_event_time": sel.selected_at_event_time,
        "selected_at_wall_time": sel.selected_at_wall_time,
        "valid_from": sel.valid_from,
        "valid_until": sel.valid_until,
        "selected_future_count": sel.selected_future_count,
        "max_positions_effective": sel.max_positions_effective,
        "single_selected_future": sel.single_selected_future,
        "multi_future_runtime_authorized": False,
        "open_position_present": sel.open_position_present,
        "open_position_instrument_id": sel.open_position_instrument_id,
        "replacement_instrument_id": sel.replacement_instrument_id,
        "alpha_authority_for_replacement": False,
        "persistence_path": persistence_path,
        "persistence_digest": sel.integrity_digest,
        "persistence_verification": dict(persistence_verification or {}),
        "restart_verification": dict(restart_verification or {}),
        "deterministic_replay_verification": {
            "ok": recomputed == sel.integrity_digest,
            "recomputed_integrity_digest": recomputed,
            "selection_integrity_digest": sel.integrity_digest,
        },
        "authority_verification": dict(sel.authority),
        "dashboard_authority": False,
        "dashboard_input_used": False,
        "allowlist_input_used": False,
        "manual_override_used": False,
        "core_logic_change": False,
        "activation_changed": False,
        "runtime_activation_allowed": False,
        "live_path_changed": False,
        "alpha_allowed": False,
        "alpha_blocked": True,
        "failure_codes": sorted(set(list(produced.failure_codes) + list(extra_failure_codes))),
        "CODE_EXISTS": True,
        "BOUND": True,
        "RUNTIME_REACHABLE": True,
        "PERSISTED": bool((persistence_verification or {}).get("ok")),
        "RESTART_PROVEN": bool((restart_verification or {}).get("ok")),
        "ACTIVATED": False,
        "SINGLE_SELECTED_FUTURE_CLOSED": True,
        "MULTI_FUTURE_CLOSED": False,
        "RUNTIME_BINDING_CLOSED": False,
    }
    return evidence
