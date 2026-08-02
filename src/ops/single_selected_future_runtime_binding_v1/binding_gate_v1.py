"""Cap 2.4 runtime binding gate: persisted selection → native instrument → recon → alpha."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    load_and_validate_universe_snapshot_v1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    load_and_validate_ranking_snapshot_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.startup_gate_v1 import (
    run_productive_reconciliation_startup_gate_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as SSF_MAX_POSITIONS,
    SELECTED_FUTURE_COUNT as SSF_SELECTED_COUNT,
    STATE_NO_SELECTION as SSF_NO_SELECTION,
)
from src.ops.single_selected_future_policy_v1.persistence_v1 import (
    load_and_validate_selection_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    ALPHA_ALLOWED_STATES,
    CALL_GRAPH,
    CALL_GRAPH_BINDING_PREFIX,
    CAPABILITY_ID,
    EXIT_RISK_SAFETY_PRESERVED_STATES,
    LIVE_AUTHORIZED,
    LIVE_TRADING_STATUS,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    ORDERS_AUTHORIZED,
    OWNER,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    SELECTED_FUTURE_COUNT,
    SELECTION_CONSUMER_IDENTITY,
    STATE_NO_SELECTION,
    STATE_SELECTED_ACTIVE,
    SUSPENDED_TRADING_STATUSES,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import (
    BoundInstrumentV1,
    RuntimeBindingEvidenceV1,
    RuntimeBindingGateResultV1,
    authority_block,
    compute_config_digest_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.reason_codes_v1 import (
    BindingFailureCodeV1,
)
from src.ops.single_selected_future_runtime_binding_v1.single_consumer_v1 import (
    DuplicateSelectionConsumerError,
    SelectionRuntimeBindingConsumerV1,
)


def _parse_rfc3339(value: str) -> Optional[float]:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).astimezone(timezone.utc).timestamp()
    except Exception:  # noqa: BLE001
        return None


def _fail(
    *,
    failure_codes: Sequence[str],
    repository_sha: str,
    config_digest: str,
    selection_state: str = STATE_NO_SELECTION,
    hard_stop: bool = False,
    exit_risk_safety_preserved: bool = False,
    instrument_id: str = "",
    venue_native_id: str = "",
    selection_id: str = "",
    selection_integrity_digest: str = "",
    ranking_snapshot_id: str = "",
    ranking_integrity_digest: str = "",
    universe_snapshot_id: str = "",
    notes: Sequence[str] = (),
    reconciliation_before_alpha: bool = False,
    reconciliation_alpha_enabled: bool = False,
    reconciliation_result: Optional[Mapping[str, Any]] = None,
    bound: Optional[BoundInstrumentV1] = None,
) -> RuntimeBindingGateResultV1:
    codes = tuple(sorted(set(str(c) for c in failure_codes)))
    if BindingFailureCodeV1.ALPHA_BLOCKED.value not in codes:
        codes = tuple(sorted(set(codes) | {BindingFailureCodeV1.ALPHA_BLOCKED.value}))
    evidence = RuntimeBindingEvidenceV1(
        capability_id=CAPABILITY_ID,
        schema_version=SCHEMA_VERSION,
        producer_version=PRODUCER_VERSION,
        owner=OWNER,
        ok=False,
        alpha_enabled=False,
        new_alpha_allowed=False,
        exit_risk_safety_preserved=bool(exit_risk_safety_preserved),
        hard_stop=bool(hard_stop),
        selection_state=selection_state,
        instrument_id=instrument_id,
        venue_native_id=venue_native_id,
        selection_id=selection_id,
        selection_integrity_digest=selection_integrity_digest,
        ranking_snapshot_id=ranking_snapshot_id,
        ranking_integrity_digest=ranking_integrity_digest,
        universe_snapshot_id=universe_snapshot_id,
        repository_sha=repository_sha,
        config_digest=config_digest,
        reconciliation_before_alpha=reconciliation_before_alpha,
        reconciliation_alpha_enabled=reconciliation_alpha_enabled,
        reason_codes=codes,
        failure_codes=codes,
        call_graph=CALL_GRAPH_BINDING_PREFIX,
        authority=authority_block(),
        notes=tuple(notes),
        bound=None if bound is None else bound.to_dict(),
    )
    return RuntimeBindingGateResultV1(
        ok=False,
        alpha_enabled=False,
        new_alpha_allowed=False,
        exit_risk_safety_preserved=bool(exit_risk_safety_preserved),
        hard_stop=bool(hard_stop),
        selection_state=selection_state,
        bound=bound,
        evidence=evidence,
        blockers=codes,
        reconciliation_result=(
            None if reconciliation_result is None else dict(reconciliation_result)
        ),
    )


def run_single_selected_future_runtime_binding_gate_v1(
    *,
    selection_state_root: Path,
    ranking_state_root: Path,
    universe_state_root: Path,
    repository_sha: str,
    session_id: str,
    now_unix: float,
    reconciliation_state_root: Path,
    observed_portfolio: PortfolioTruthSnapshotV1,
    expected_selection_config_digest: str | None = None,
    expected_selection_integrity_digest: str | None = None,
    mark_price_by_native_id: Mapping[str, Any] | None = None,
    safety_venue_allowlist: Sequence[str] | None = None,
    dashboard_selected_instrument: str | None = None,
    dashboard_available: bool = True,
    direct_instrument_override: str | None = None,
    allow_research_direct_instrument: bool = False,
    consumer_identity: str = SELECTION_CONSUMER_IDENTITY,
    inject_conflicting_consumer: bool = False,
    skip_reconciliation: bool = False,
    require_position_truth_if_open_claimed: bool = True,
) -> RuntimeBindingGateResultV1:
    """Bind Cap 2.3 selection into the productive analytical runtime host.

    Order: selection load/validate → ranking/universe refs → native bind →
    reconciliation → alpha gate. No network, no orders, no activation.
    """
    if LIVE_AUTHORIZED or ORDERS_AUTHORIZED or MULTI_FUTURE_RUNTIME_AUTHORIZED:
        raise RuntimeError("INVARIANT_VIOLATION_AUTHORITY_FLAGS")

    cfg_digest = compute_config_digest_v1(repository_sha=repository_sha)
    consumer_root = Path(selection_state_root)

    if inject_conflicting_consumer:
        poison = SelectionRuntimeBindingConsumerV1(
            state_root=consumer_root,
            consumer_identity="legacy_parallel_selection_consumer",
            session_id="poison",
        )
        poison.acquire(now_unix=now_unix)

    if direct_instrument_override and not allow_research_direct_instrument:
        return _fail(
            failure_codes=(BindingFailureCodeV1.DIRECT_INSTRUMENT_OVERRIDE_REJECTED.value,),
            repository_sha=repository_sha,
            config_digest=cfg_digest,
            notes=("PRODUCTIVE_ENTRYPOINT_REJECTS_DIRECT_INSTRUMENT_OVERRIDE",),
        )

    if safety_venue_allowlist is not None and len(tuple(safety_venue_allowlist)) == 0:
        # Empty allowlist as selection owner is forbidden; non-empty is safety-only.
        return _fail(
            failure_codes=(BindingFailureCodeV1.ALLOWLIST_SELECTION_AUTHORITY_REJECTED.value,),
            repository_sha=repository_sha,
            config_digest=cfg_digest,
            notes=("EMPTY_ALLOWLIST_CANNOT_BECOME_SELECTION_AUTHORITY",),
        )

    consumer = SelectionRuntimeBindingConsumerV1(
        state_root=consumer_root,
        consumer_identity=consumer_identity,
        session_id=session_id,
    )
    try:
        consumer.acquire(now_unix=now_unix)
    except DuplicateSelectionConsumerError as exc:
        return _fail(
            failure_codes=(
                BindingFailureCodeV1.DUPLICATE_SELECTION_CONSUMER.value,
                BindingFailureCodeV1.CONFLICTING_SELECTION_CONSUMER.value,
            ),
            repository_sha=repository_sha,
            config_digest=cfg_digest,
            hard_stop=True,
            notes=(str(exc),),
        )

    try:
        loaded = load_and_validate_selection_v1(
            Path(selection_state_root),
            expected_repository_sha=repository_sha,
            expected_config_digest=expected_selection_config_digest,
            require_manifest=True,
        )
        if not loaded.ok or loaded.selection is None:
            codes = list(loaded.failure_codes) or [BindingFailureCodeV1.SELECTION_MISSING.value]
            if loaded.detail == "SELECTION_MISSING":
                codes.append(BindingFailureCodeV1.NO_SELECTION.value)
                codes.append(BindingFailureCodeV1.SELECTION_MISSING.value)
            else:
                codes.append(BindingFailureCodeV1.CORRUPT_SELECTION.value)
            mapped: list[str] = []
            for code in codes:
                if code in {
                    "CORRUPT_PERSISTED_SELECTION",
                    "INTEGRITY_FAILURE",
                }:
                    mapped.append(BindingFailureCodeV1.CORRUPT_SELECTION.value)
                    mapped.append(BindingFailureCodeV1.SELECTION_DIGEST_MISMATCH.value)
                elif code == "REPOSITORY_SHA_MISMATCH":
                    mapped.append(BindingFailureCodeV1.REPOSITORY_SHA_MISMATCH.value)
                elif code == "CONFIG_DIGEST_MISMATCH":
                    mapped.append(BindingFailureCodeV1.CONFIG_DIGEST_MISMATCH.value)
                elif code == "DASHBOARD_INPUT_FORBIDDEN":
                    mapped.append(BindingFailureCodeV1.DASHBOARD_AUTHORITY_REJECTED.value)
                elif code == "ALLOWLIST_INPUT_FORBIDDEN":
                    mapped.append(BindingFailureCodeV1.ALLOWLIST_SELECTION_AUTHORITY_REJECTED.value)
                else:
                    mapped.append(code)
            return _fail(
                failure_codes=mapped,
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=(
                    loaded.selection.state if loaded.selection is not None else STATE_NO_SELECTION
                ),
            )

        selection = loaded.selection
        if (
            expected_selection_integrity_digest is not None
            and selection.integrity_digest != expected_selection_integrity_digest
        ):
            return _fail(
                failure_codes=(BindingFailureCodeV1.SELECTION_DIGEST_MISMATCH.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
                selection_integrity_digest=selection.integrity_digest,
            )

        if int(selection.selected_future_count) != SELECTED_FUTURE_COUNT:
            return _fail(
                failure_codes=(BindingFailureCodeV1.SELECTED_FUTURE_COUNT_VIOLATION.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
            )
        if int(selection.max_positions_effective) != MAX_POSITIONS_EFFECTIVE:
            return _fail(
                failure_codes=(BindingFailureCodeV1.MAX_POSITIONS_VIOLATION.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
            )
        if selection.multi_future_runtime_authorized or MULTI_FUTURE_RUNTIME_AUTHORIZED:
            return _fail(
                failure_codes=(BindingFailureCodeV1.MULTI_FUTURE_UNAUTHORIZED.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
            )
        if int(SSF_SELECTED_COUNT) != 1 or int(SSF_MAX_POSITIONS) != 1:
            return _fail(
                failure_codes=(BindingFailureCodeV1.MAX_POSITIONS_VIOLATION.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
            )

        if selection.state == SSF_NO_SELECTION or selection.state == STATE_NO_SELECTION:
            return _fail(
                failure_codes=(BindingFailureCodeV1.NO_SELECTION.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=STATE_NO_SELECTION,
                selection_id=selection.selection_id,
                selection_integrity_digest=selection.integrity_digest,
            )

        valid_from = _parse_rfc3339(selection.valid_from)
        valid_until = _parse_rfc3339(selection.valid_until)
        if valid_from is not None and now_unix < valid_from:
            return _fail(
                failure_codes=(BindingFailureCodeV1.SELECTION_NOT_YET_VALID.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
                selection_integrity_digest=selection.integrity_digest,
                instrument_id=selection.instrument_id,
                venue_native_id=selection.venue_native_id,
            )
        if valid_until is not None and now_unix > valid_until:
            # Distinguish stale (past valid_until within grace semantics) vs expired.
            age_past = now_unix - valid_until
            code = (
                BindingFailureCodeV1.SELECTION_EXPIRED.value
                if age_past > 0
                else BindingFailureCodeV1.SELECTION_STALE.value
            )
            # Explicit stale vs expired: expired when past valid_until; stale alias for
            # operators that treat age overflow as stale.
            codes = (
                BindingFailureCodeV1.SELECTION_EXPIRED.value,
                BindingFailureCodeV1.SELECTION_STALE.value,
            )
            return _fail(
                failure_codes=codes,
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
                selection_integrity_digest=selection.integrity_digest,
                instrument_id=selection.instrument_id,
                venue_native_id=selection.venue_native_id,
                notes=(f"AGE_PAST_VALID_UNTIL={age_past}", code),
            )

        ranking_loaded = load_and_validate_ranking_snapshot_v1(
            Path(ranking_state_root),
            require_manifest=True,
        )
        if not ranking_loaded.ok or ranking_loaded.snapshot is None:
            return _fail(
                failure_codes=(BindingFailureCodeV1.RANKING_SNAPSHOT_MISSING.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
                selection_integrity_digest=selection.integrity_digest,
                instrument_id=selection.instrument_id,
                venue_native_id=selection.venue_native_id,
                ranking_snapshot_id=selection.ranking_snapshot_id,
            )
        ranking = ranking_loaded.snapshot
        if ranking.ranking_snapshot_id != selection.ranking_snapshot_id:
            return _fail(
                failure_codes=(BindingFailureCodeV1.RANKING_SNAPSHOT_MISMATCH.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
                ranking_snapshot_id=selection.ranking_snapshot_id,
                ranking_integrity_digest=selection.ranking_integrity_digest,
            )
        if ranking.integrity_digest != selection.ranking_integrity_digest:
            return _fail(
                failure_codes=(
                    BindingFailureCodeV1.RANKING_DIGEST_MISMATCH.value,
                    BindingFailureCodeV1.RANKING_SNAPSHOT_MISMATCH.value,
                ),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
                ranking_snapshot_id=selection.ranking_snapshot_id,
                ranking_integrity_digest=selection.ranking_integrity_digest,
            )

        universe_loaded = load_and_validate_universe_snapshot_v1(
            Path(universe_state_root),
            require_manifest=True,
        )
        if not universe_loaded.ok or universe_loaded.snapshot is None:
            return _fail(
                failure_codes=(BindingFailureCodeV1.UNIVERSE_SNAPSHOT_MISSING.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
                ranking_snapshot_id=ranking.ranking_snapshot_id,
                ranking_integrity_digest=ranking.integrity_digest,
            )
        universe = universe_loaded.snapshot
        if universe.snapshot_id != ranking.universe_snapshot_id:
            return _fail(
                failure_codes=(BindingFailureCodeV1.UNIVERSE_SNAPSHOT_MISMATCH.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
                ranking_snapshot_id=ranking.ranking_snapshot_id,
                universe_snapshot_id=ranking.universe_snapshot_id,
            )

        instrument_row = None
        for row in universe.instruments:
            if row.canonical_instrument_id == selection.instrument_id:
                instrument_row = row
                break
        if instrument_row is None:
            return _fail(
                failure_codes=(BindingFailureCodeV1.INSTRUMENT_NOT_GOVERNED.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
                instrument_id=selection.instrument_id,
                venue_native_id=selection.venue_native_id,
                ranking_snapshot_id=ranking.ranking_snapshot_id,
                universe_snapshot_id=universe.snapshot_id,
            )
        if not instrument_row.eligibility:
            return _fail(
                failure_codes=(BindingFailureCodeV1.INSTRUMENT_NOT_ELIGIBLE.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
                instrument_id=selection.instrument_id,
                venue_native_id=selection.venue_native_id,
                universe_snapshot_id=universe.snapshot_id,
            )
        if instrument_row.venue_native_inst_id != selection.venue_native_id:
            return _fail(
                failure_codes=(BindingFailureCodeV1.NATIVE_VENUE_ID_MISMATCH.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
                instrument_id=selection.instrument_id,
                venue_native_id=selection.venue_native_id,
                universe_snapshot_id=universe.snapshot_id,
            )

        status = str(instrument_row.trading_status or "").strip().lower()
        if status in SUSPENDED_TRADING_STATUSES or status == "suspended":
            code = (
                BindingFailureCodeV1.INSTRUMENT_EXPIRED.value
                if status in {"expired", "settle", "settled"}
                else BindingFailureCodeV1.INSTRUMENT_SUSPENDED.value
            )
            return _fail(
                failure_codes=(code, BindingFailureCodeV1.INSTRUMENT_INVALID.value),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
                instrument_id=selection.instrument_id,
                venue_native_id=selection.venue_native_id,
                exit_risk_safety_preserved=selection.state in EXIT_RISK_SAFETY_PRESERVED_STATES
                or bool(selection.open_position_present),
                universe_snapshot_id=universe.snapshot_id,
            )
        if status and status != LIVE_TRADING_STATUS:
            return _fail(
                failure_codes=(BindingFailureCodeV1.INSTRUMENT_INVALID.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
                instrument_id=selection.instrument_id,
                venue_native_id=selection.venue_native_id,
                universe_snapshot_id=universe.snapshot_id,
            )
        if instrument_row.expiry_time:
            exp_ts = _parse_rfc3339(str(instrument_row.expiry_time))
            if exp_ts is not None and now_unix >= exp_ts:
                return _fail(
                    failure_codes=(BindingFailureCodeV1.INSTRUMENT_EXPIRED.value,),
                    repository_sha=repository_sha,
                    config_digest=cfg_digest,
                    selection_state=selection.state,
                    selection_id=selection.selection_id,
                    instrument_id=selection.instrument_id,
                    venue_native_id=selection.venue_native_id,
                    exit_risk_safety_preserved=True,
                    universe_snapshot_id=universe.snapshot_id,
                )

        if not instrument_row.mark_price_supported or not instrument_row.market_data_supported:
            return _fail(
                failure_codes=(BindingFailureCodeV1.MARKET_DATA_UNAVAILABLE.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
                instrument_id=selection.instrument_id,
                venue_native_id=selection.venue_native_id,
                universe_snapshot_id=universe.snapshot_id,
            )
        marks = dict(mark_price_by_native_id or {})
        mark_val = marks.get(selection.venue_native_id)
        if mark_val is None or str(mark_val).strip() == "":
            return _fail(
                failure_codes=(BindingFailureCodeV1.MARK_PRICE_MISSING.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=selection.state,
                selection_id=selection.selection_id,
                instrument_id=selection.instrument_id,
                venue_native_id=selection.venue_native_id,
                universe_snapshot_id=universe.snapshot_id,
            )

        if safety_venue_allowlist is not None:
            allowed = {str(x) for x in safety_venue_allowlist}
            # Safety allowlist may only admit/deny the already-selected instrument.
            if selection.venue_native_id not in allowed:
                return _fail(
                    failure_codes=(BindingFailureCodeV1.ALLOWLIST_CONFLICT.value,),
                    repository_sha=repository_sha,
                    config_digest=cfg_digest,
                    selection_state=selection.state,
                    selection_id=selection.selection_id,
                    instrument_id=selection.instrument_id,
                    venue_native_id=selection.venue_native_id,
                    notes=("ALLOWLIST_IS_SAFETY_ONLY_NOT_SELECTION_OWNER",),
                )

        notes: list[str] = []
        if not dashboard_available:
            notes.append("DASHBOARD_UNAVAILABLE_NO_AUTHORITY_EFFECT")
        if dashboard_selected_instrument:
            notes.append("DASHBOARD_CONFLICTING_INSTRUMENT_IGNORED")
            if str(dashboard_selected_instrument) not in {
                selection.instrument_id,
                selection.venue_native_id,
            }:
                notes.append(BindingFailureCodeV1.DASHBOARD_CONFLICTING_INSTRUMENT_IGNORED.value)

        bound = BoundInstrumentV1(
            instrument_id=selection.instrument_id,
            venue_native_id=selection.venue_native_id,
            ranking_snapshot_id=ranking.ranking_snapshot_id,
            ranking_integrity_digest=ranking.integrity_digest,
            universe_snapshot_id=universe.snapshot_id,
            selection_id=selection.selection_id,
            selection_integrity_digest=selection.integrity_digest,
            selection_state=selection.state,
            selected_future_count=SELECTED_FUTURE_COUNT,
            max_positions_effective=MAX_POSITIONS_EFFECTIVE,
        )

        state = selection.state
        new_alpha_from_state = state in ALPHA_ALLOWED_STATES
        exit_preserved = state in EXIT_RISK_SAFETY_PRESERVED_STATES or bool(
            selection.open_position_present
        )

        if (
            require_position_truth_if_open_claimed
            and selection.open_position_present
            and not observed_portfolio.positions
        ):
            return _fail(
                failure_codes=(BindingFailureCodeV1.POSITION_TRUTH_MISSING.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=state,
                selection_id=selection.selection_id,
                selection_integrity_digest=selection.integrity_digest,
                instrument_id=bound.instrument_id,
                venue_native_id=bound.venue_native_id,
                ranking_snapshot_id=bound.ranking_snapshot_id,
                ranking_integrity_digest=bound.ranking_integrity_digest,
                universe_snapshot_id=bound.universe_snapshot_id,
                hard_stop=True,
                exit_risk_safety_preserved=False,
                bound=bound,
                notes=("OPEN_POSITION_CLAIMED_BUT_POSITION_TRUTH_MISSING",),
            )

        recon_result: Optional[dict[str, Any]] = None
        recon_alpha = False
        if skip_reconciliation:
            return _fail(
                failure_codes=(BindingFailureCodeV1.RECONCILIATION_BLOCKED_ALPHA.value,),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=state,
                selection_id=selection.selection_id,
                instrument_id=bound.instrument_id,
                venue_native_id=bound.venue_native_id,
                ranking_snapshot_id=bound.ranking_snapshot_id,
                universe_snapshot_id=bound.universe_snapshot_id,
                reconciliation_before_alpha=False,
                bound=bound,
                notes=("RECONCILIATION_MUST_PRECEDE_ALPHA",),
            )

        gate = run_productive_reconciliation_startup_gate_v1(
            state_root=Path(reconciliation_state_root),
            observed=observed_portfolio,
            session_id=session_id,
            repository_sha=repository_sha,
            now_unix=now_unix,
        )
        recon_result = {
            "ok": gate.ok,
            "alpha_enabled": gate.alpha_enabled,
            "classification": gate.classification.value,
            "hard_stop": gate.hard_stop,
            "blockers": list(gate.blockers),
            "master_v2_reconciliation_state": gate.master_v2_reconciliation_state,
        }
        recon_alpha = bool(gate.alpha_enabled)
        if gate.hard_stop or not gate.alpha_enabled:
            return _fail(
                failure_codes=(
                    BindingFailureCodeV1.RECONCILIATION_BLOCKED_ALPHA.value,
                    *(
                        (BindingFailureCodeV1.RECONCILIATION_HARD_STOP.value,)
                        if gate.hard_stop
                        else ()
                    ),
                ),
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                selection_state=state,
                selection_id=selection.selection_id,
                selection_integrity_digest=selection.integrity_digest,
                instrument_id=bound.instrument_id,
                venue_native_id=bound.venue_native_id,
                ranking_snapshot_id=bound.ranking_snapshot_id,
                ranking_integrity_digest=bound.ranking_integrity_digest,
                universe_snapshot_id=bound.universe_snapshot_id,
                hard_stop=bool(gate.hard_stop),
                exit_risk_safety_preserved=exit_preserved,
                reconciliation_before_alpha=True,
                reconciliation_alpha_enabled=False,
                reconciliation_result=recon_result,
                bound=bound,
                notes=tuple(notes),
            )

        if not new_alpha_from_state:
            evidence = RuntimeBindingEvidenceV1(
                capability_id=CAPABILITY_ID,
                schema_version=SCHEMA_VERSION,
                producer_version=PRODUCER_VERSION,
                owner=OWNER,
                ok=True,
                alpha_enabled=False,
                new_alpha_allowed=False,
                exit_risk_safety_preserved=True,
                hard_stop=False,
                selection_state=state,
                instrument_id=bound.instrument_id,
                venue_native_id=bound.venue_native_id,
                selection_id=bound.selection_id,
                selection_integrity_digest=bound.selection_integrity_digest,
                ranking_snapshot_id=bound.ranking_snapshot_id,
                ranking_integrity_digest=bound.ranking_integrity_digest,
                universe_snapshot_id=bound.universe_snapshot_id,
                repository_sha=repository_sha,
                config_digest=cfg_digest,
                reconciliation_before_alpha=True,
                reconciliation_alpha_enabled=recon_alpha,
                reason_codes=(BindingFailureCodeV1.STATE_BLOCKS_NEW_ALPHA.value,),
                failure_codes=(BindingFailureCodeV1.STATE_BLOCKS_NEW_ALPHA.value,),
                call_graph=CALL_GRAPH,
                authority=authority_block(),
                notes=tuple(notes)
                + (
                    "NATIVE_INSTRUMENT_BOUND",
                    "RECONCILIATION_BEFORE_ALPHA",
                    "EXIT_RISK_SAFETY_PRESERVED",
                ),
                bound=bound.to_dict(),
            )
            return RuntimeBindingGateResultV1(
                ok=True,
                alpha_enabled=False,
                new_alpha_allowed=False,
                exit_risk_safety_preserved=True,
                hard_stop=False,
                selection_state=state,
                bound=bound,
                evidence=evidence,
                blockers=(BindingFailureCodeV1.STATE_BLOCKS_NEW_ALPHA.value,),
                reconciliation_result=recon_result,
            )

        evidence = RuntimeBindingEvidenceV1(
            capability_id=CAPABILITY_ID,
            schema_version=SCHEMA_VERSION,
            producer_version=PRODUCER_VERSION,
            owner=OWNER,
            ok=True,
            alpha_enabled=True,
            new_alpha_allowed=True,
            exit_risk_safety_preserved=True,
            hard_stop=False,
            selection_state=STATE_SELECTED_ACTIVE,
            instrument_id=bound.instrument_id,
            venue_native_id=bound.venue_native_id,
            selection_id=bound.selection_id,
            selection_integrity_digest=bound.selection_integrity_digest,
            ranking_snapshot_id=bound.ranking_snapshot_id,
            ranking_integrity_digest=bound.ranking_integrity_digest,
            universe_snapshot_id=bound.universe_snapshot_id,
            repository_sha=repository_sha,
            config_digest=cfg_digest,
            reconciliation_before_alpha=True,
            reconciliation_alpha_enabled=recon_alpha,
            reason_codes=("BINDING_OK", "SELECTED_ACTIVE", "RECONCILIATION_BEFORE_ALPHA"),
            failure_codes=(),
            call_graph=CALL_GRAPH,
            authority=authority_block(),
            notes=tuple(notes)
            + (
                "PERSISTED_SELECTION_CONSUMED",
                "SELECTION_INTEGRITY_VALIDATED",
                "RANKING_REFERENCE_VALIDATED",
                "UNIVERSE_REFERENCE_VALIDATED",
                "NATIVE_INSTRUMENT_BOUND",
                "RECONCILIATION_BEFORE_ALPHA",
                "EXACTLY_ONE_SELECTED_FUTURE",
                "MAX_POSITIONS=1",
                "MULTI_FUTURE_RUNTIME_AUTHORIZED=false",
                "DASHBOARD_AUTHORITY_EFFECT=false",
                "ALLOWLIST_SELECTION_AUTHORITY=false",
                "CORE_LOGIC_CHANGE=false",
                "ACTIVATION_CHANGED=false",
                "LIVE_PATH_CHANGED=false",
            ),
            bound=bound.to_dict(),
        )
        return RuntimeBindingGateResultV1(
            ok=True,
            alpha_enabled=True,
            new_alpha_allowed=True,
            exit_risk_safety_preserved=True,
            hard_stop=False,
            selection_state=STATE_SELECTED_ACTIVE,
            bound=bound,
            evidence=evidence,
            blockers=(),
            reconciliation_result=recon_result,
        )
    finally:
        consumer.release()
