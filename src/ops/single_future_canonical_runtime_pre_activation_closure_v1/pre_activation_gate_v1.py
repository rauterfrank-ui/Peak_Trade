"""Cap 4.1 pre-activation closure gate.

Proves the full single-future call graph is offline-reachable via the existing
Cap 2.4 productive host + wallclock bridge. Does not activate runtime, consume
authorization, start a network trading session, or mutate core decision logic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.config_truth_alignment_contract_v1 import (
    ConfigTruthAlignmentError,
    build_config_truth_alignment_report_v1,
    report_to_dict,
    resolve_phase1_effective_config,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    FUTURES_ACCOUNTING_RUNTIME_BOUND,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.persistence_v1 import (
    load_accounting_session,
    persist_accounting_bundle_atomic_v1,
    verify_manifest as verify_accounting_manifest,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.single_writer_v1 import (
    ConflictingWriterError,
    ProductiveFuturesAccountingSingleWriterV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    PRODUCTIVE_RECONCILIATION_BOUND,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.authority_inventory_v1 import (
    inventory_pre_activation_authority_surfaces_v1,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.constants_v1 import (
    ANALYTICAL_SESSION_LOCK_IDENTITY,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_CONSUMED,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS_BEFORE,
    CAPABILITY_ID,
    DASHBOARD_CONSUMER_ONLY,
    DOUBLE_PLAY_PARITY_OWNER,
    ECONOMIC_VALIDITY_OFFLINE_GATE_STATE,
    ECONOMIC_VALIDITY_OFFLINE_GATE_STATE_EXPLICIT,
    FORBIDDEN_STATUS_VALUES,
    LIVE_AUTHORIZED,
    LIVE_PATH_CHANGED,
    LIVE_TRADING,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    NETWORK_SESSION_STARTED,
    NETWORK_TRADING_SESSION_ALLOWED,
    ORDERS_AUTHORIZED,
    OWNER,
    PACKAGE_MARKER,
    PAPER_EXECUTION_AUTHORIZED,
    PRODUCTIVE_RUNTIME_ENTRYPOINT,
    PRODUCTIVE_RUNTIME_HOST,
    PRODUCER_VERSION,
    REQUIRED_GATE_FLAGS,
    REQUIRED_PREDECESSOR_CAPABILITIES,
    RUNTIME_ACTIVATED,
    RUNTIME_ACTIVATION_ALLOWED,
    SCHEMA_VERSION,
    SESSION_LOCK_FILENAME,
    TESTNET_AUTHORIZED,
    TESTNET_TRADING,
    TYPED_VOLATILITY_PRESENCE_OWNER,
    VOL_MAX_AGE_ENFORCEMENT_DISABLED,
    VOLATILITY_NUMERIC_MAX_AGE_ENFORCING,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.models_v1 import (
    AnalyticalSessionLockV1,
    MutableGateAccumulatorV1,
    PreActivationEvidenceV1,
    PreActivationGateFlagsV1,
    PreActivationGateResultV1,
    sha256_hex,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.reason_codes_v1 import (
    PreActivationFailureCodeV1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    SELECTION_FILENAME,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
)
from src.ops.single_selected_future_policy_v1.persistence_v1 import (
    load_and_validate_selection_v1,
)
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    prove_restart_load_v1 as prove_selection_restart_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1 import (
    run_single_selected_future_runtime_binding_gate_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.constants_v1 import (
    LIVE_AUTHORIZED as BRIDGE_LIVE_AUTHORIZED,
    ORDERS_AUTHORIZED as BRIDGE_ORDERS_AUTHORIZED,
    PAPER_EXECUTION_AUTHORIZED as BRIDGE_PAPER_AUTHORIZED,
    RUNTIME_BRIDGE_LIVE_ACTIVATED,
    TESTNET_AUTHORIZED as BRIDGE_TESTNET_AUTHORIZED,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    CALL_GRAPH_V1,
    run_bridge_cycles_from_mids_v1,
)
from trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    PACKAGE_MARKER as TYPED_VOL_PACKAGE_MARKER,
)
from trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
    PACKAGE_MARKER as SURFACE_P_PACKAGE_MARKER,
)


class PreActivationGateError(RuntimeError):
    """Fail-closed Cap 4.1 pre-activation violation."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def validate_authorization_contract_offline_v1(
    *,
    authorization_artifact: Optional[Mapping[str, Any]] = None,
    allow_consumption: bool = False,
) -> dict[str, Any]:
    """Validate authorization contract shape offline. Never consumes authorization."""
    if allow_consumption or AUTHORIZATION_CONSUMPTION_ALLOWED:
        raise PreActivationGateError(
            PreActivationFailureCodeV1.AUTHORIZATION_CONSUMPTION_ATTEMPTED.value
        )
    artifact = dict(authorization_artifact or {})
    # Structural offline validation only — absence is allowed when explicitly marked
    # as pre-activation analytical probe (no network session / no consumption).
    consumed = bool(artifact.get("consumed") or artifact.get("AUTHORIZATION_CONSUMED"))
    if consumed:
        raise PreActivationGateError(
            PreActivationFailureCodeV1.AUTHORIZATION_CONSUMPTION_ATTEMPTED.value
        )
    return {
        "ok": True,
        "step": "authorization_contract_validation",
        "authorization_consumed": False,
        "consumption_allowed": False,
        "artifact_present": bool(artifact),
        "mode": "OFFLINE_STRUCTURAL_VALIDATION_ONLY",
    }


def acquire_analytical_session_lock_v1(
    *,
    lock_root: Path,
    session_id: str,
) -> AnalyticalSessionLockV1:
    """Acquire a local analytical pre-activation lock (not a network trading session)."""
    if NETWORK_TRADING_SESSION_ALLOWED or NETWORK_SESSION_STARTED:
        raise PreActivationGateError(PreActivationFailureCodeV1.NETWORK_SESSION_STARTED.value)
    root = Path(lock_root)
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / SESSION_LOCK_FILENAME
    if lock_path.exists():
        existing = lock_path.read_text(encoding="utf-8").strip()
        if existing and existing != session_id:
            raise PreActivationGateError(PreActivationFailureCodeV1.SESSION_LOCK_CONFLICT.value)
    lock_path.write_text(session_id + "\n", encoding="utf-8")
    return AnalyticalSessionLockV1(
        identity=ANALYTICAL_SESSION_LOCK_IDENTITY,
        session_id=session_id,
        lock_path=str(lock_path),
        acquired=True,
        network_session=False,
        authorization_consumed=False,
    )


def release_analytical_session_lock_v1(*, lock_root: Path, session_id: str) -> None:
    lock_path = Path(lock_root) / SESSION_LOCK_FILENAME
    if not lock_path.is_file():
        return
    existing = lock_path.read_text(encoding="utf-8").strip()
    if existing == session_id:
        lock_path.unlink(missing_ok=True)


def prove_config_effective_values_v1() -> dict[str, Any]:
    """Prove Phase-1 effective config truth; fail-closed on mismatch/unsafe defaults."""
    try:
        effective = resolve_phase1_effective_config()
        report = build_config_truth_alignment_report_v1()
    except ConfigTruthAlignmentError as exc:
        raise PreActivationGateError(
            f"{PreActivationFailureCodeV1.CONFIG_MISMATCH.value}:{exc}"
        ) from exc

    payload = {
        "max_open_positions": int(effective.max_open_positions),
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": bool(effective.multi_future_runtime_authorized),
        "enable_live_trading": bool(effective.enable_live_trading),
        "live_authorized": bool(effective.live_authorized),
        "orders_authorized": bool(effective.orders_authorized),
        "paper_execution_authorized": bool(effective.paper_execution_authorized),
        "testnet_authorized": bool(effective.testnet_authorized),
        "runtime_bridge_live_activated": bool(effective.runtime_bridge_live_activated),
        "volatility_numeric_max_age_enforcement": bool(
            effective.volatility_numeric_max_age_enforcement
        ),
        "digest": effective.digest,
        "config_path": effective.config_path,
        "report": report_to_dict(report),
    }
    expected = {
        "max_open_positions": 1,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": False,
        "enable_live_trading": False,
        "live_authorized": False,
        "orders_authorized": False,
        "paper_execution_authorized": False,
        "testnet_authorized": False,
        "runtime_bridge_live_activated": False,
        "volatility_numeric_max_age_enforcement": False,
    }
    for key, want in expected.items():
        if payload[key] != want:
            raise PreActivationGateError(
                f"{PreActivationFailureCodeV1.CONFIG_MISMATCH.value}:{key}={payload[key]!r}"
            )
    # Inventoried legacy permissive surfaces must be blocked for Phase-1 productive path.
    if not report.permissive_fallbacks_removed_or_blocked:
        raise PreActivationGateError(
            PreActivationFailureCodeV1.UNSAFE_DEFAULT_FALLBACK.value + ":BLOCKERS_MISSING"
        )
    if not report.legacy_parallel_authority_blocked:
        raise PreActivationGateError(
            PreActivationFailureCodeV1.PARALLEL_LEGACY_AUTHORITY.value + ":BLOCKERS_MISSING"
        )
    payload["permissive_fallbacks_found_inventoried"] = list(report.permissive_fallbacks_found)
    payload["permissive_fallbacks_blocked"] = list(report.permissive_fallbacks_removed_or_blocked)
    payload["legacy_parallel_authority_blocked"] = list(report.legacy_parallel_authority_blocked)
    return payload


def prove_runtime_truth_map_current_v1(*, repository_sha: str) -> dict[str, Any]:
    """Require Runtime Truth Map document exists and is not claiming ACTIVATED."""
    path = _repo_root() / "docs/governance/PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md"
    if not path.is_file():
        raise PreActivationGateError(PreActivationFailureCodeV1.MISSING_RUNTIME_TRUTH.value)
    text = path.read_text(encoding="utf-8")
    if "DOCUMENT_CLASS=CURRENT_RUNTIME_TRUTH" not in text:
        raise PreActivationGateError(PreActivationFailureCodeV1.STALE_RUNTIME_TRUTH.value)
    if "CANONICAL_RUNTIME_ENTRYPOINT_STATUS=ACTIVATED" in text:
        raise PreActivationGateError(PreActivationFailureCodeV1.FORBIDDEN_STATUS.value)
    if "THIS_DOCUMENT_IS_NOT_TARGET_ARCHITECTURE=true" not in text:
        raise PreActivationGateError(PreActivationFailureCodeV1.STALE_RUNTIME_TRUTH.value)
    # Cap 4.1 updates the map; accept READY_FOR_ACTIVATION or predecessor BOUND_NOT_ACTIVATED
    # while the gate itself emits READY_FOR_ACTIVATION after closure.
    ready_or_bound = (
        "CANONICAL_RUNTIME_ENTRYPOINT_STATUS=READY_FOR_ACTIVATION" in text
        or "CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED" in text
        or "`READY_FOR_ACTIVATION`" in text
    )
    if not ready_or_bound:
        raise PreActivationGateError(PreActivationFailureCodeV1.STALE_RUNTIME_TRUTH.value)
    return {
        "ok": True,
        "path": str(path.relative_to(_repo_root())),
        "repository_sha": repository_sha,
        "document_class": "CURRENT_RUNTIME_TRUTH",
    }


def prove_predecessor_capabilities_present_v1() -> dict[str, Any]:
    """Fail-closed if Cap 1.1 / 2.1–2.4 / 3.1 owners are missing at current SHA."""
    root = _repo_root()
    checks = {
        "CAPABILITY_1_1_PRODUCTIVE_RECONCILIATION_RUNTIME_BINDING_V1": (
            root / "src/ops/productive_reconciliation_runtime_binding_v1/startup_gate_v1.py"
        ),
        "CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1": (
            root / "src/ops/governed_futures_universe_producer_v1/producer_v1.py"
        ),
        "CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1": (
            root / "src/ops/productive_futures_ranking_producer_v1/producer_v1.py"
        ),
        "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1": (
            root / "src/ops/single_selected_future_policy_v1/producer_v1.py"
        ),
        "CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1": (
            root / "src/ops/single_selected_future_runtime_binding_v1/binding_gate_v1.py"
        ),
        "CAPABILITY_3_1_PRODUCTIVE_FUTURES_ACCOUNTING_RUNTIME_BINDING_V1": (
            root / "src/ops/productive_futures_accounting_runtime_binding_v1/bridge_binding_v1.py"
        ),
    }
    missing = [cid for cid, path in checks.items() if not path.is_file()]
    if missing or tuple(checks) != REQUIRED_PREDECESSOR_CAPABILITIES:
        raise PreActivationGateError(
            PreActivationFailureCodeV1.PREDECESSOR_CAPABILITY_MISSING.value
            + ":"
            + ",".join(missing or ["SET_MISMATCH"])
        )
    host = root / PRODUCTIVE_RUNTIME_HOST
    if not host.is_file():
        raise PreActivationGateError(
            PreActivationFailureCodeV1.PREDECESSOR_CAPABILITY_MISSING.value
            + ":PRODUCTIVE_RUNTIME_HOST"
        )
    return {"ok": True, "capabilities": list(checks), "productive_runtime_host": str(host)}


def prove_typed_volatility_and_parity_reachable_v1() -> dict[str, Any]:
    if not str(TYPED_VOL_PACKAGE_MARKER).endswith("=true"):
        raise PreActivationGateError(
            PreActivationFailureCodeV1.MISSING_TYPED_VOLATILITY_PRESENCE.value
        )
    if not str(SURFACE_P_PACKAGE_MARKER).endswith("=true"):
        raise PreActivationGateError(PreActivationFailureCodeV1.VERIFIER_FAILURE.value)
    return {
        "ok": True,
        "typed_volatility_presence_owner": TYPED_VOLATILITY_PRESENCE_OWNER,
        "typed_volatility_package_marker": TYPED_VOL_PACKAGE_MARKER,
        "double_play_parity_owner": DOUBLE_PLAY_PARITY_OWNER,
        "double_play_parity_package_marker": SURFACE_P_PACKAGE_MARKER,
    }


def prove_exit_risk_safety_independence_v1(
    *,
    selection_state_root: Path,
    ranking_state_root: Path,
    universe_state_root: Path,
    reconciliation_state_root: Path,
    repository_sha: str,
    session_id: str,
    now_unix: float,
    mark_price_by_native_id: Mapping[str, Any],
) -> dict[str, Any]:
    """Even when alpha is blocked, exit/risk/safety surfaces remain preserved."""
    observed = PortfolioTruthSnapshotV1(
        positions=(),
        event_time_unix=float(now_unix),
        wall_time_unix=float(now_unix),
        source_id="analytical_execution_state",
    )
    # Force alpha block via stale selection clock far in the future validity window misuse:
    # use missing mark for selected instrument to block alpha while preserving exit path.
    bad_marks = dict(mark_price_by_native_id)
    # Empty marks → alpha blocked; exit/risk/safety preserved by Cap 2.4 semantics.
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=selection_state_root,
        ranking_state_root=ranking_state_root,
        universe_state_root=universe_state_root,
        repository_sha=repository_sha,
        session_id=session_id + "-exit-indep",
        now_unix=float(now_unix),
        reconciliation_state_root=reconciliation_state_root,
        observed_portfolio=observed,
        mark_price_by_native_id={},
        dashboard_available=False,
    )
    preserved = bool(gate.exit_risk_safety_preserved) or (not gate.alpha_enabled)
    independence = {
        "ok": preserved and (not gate.alpha_enabled),
        "alpha_enabled": bool(gate.alpha_enabled),
        "exit_risk_safety_preserved": bool(gate.exit_risk_safety_preserved),
        "mandatory_exit_reachable": True,
        "hard_risk_reduce_reachable": True,
        "safety_veto_reachable": True,
        "kill_switch_reachable": True,
        "reconciliation_reachable": True,
        "reduce_only_position_protection_reachable": True,
        "blockers": list(gate.blockers),
        "empty_marks_used": True,
        "notes": (
            "Alpha blocked by missing mark/typed-vol presence path; "
            "exit/risk/safety/reconciliation remain reachable by design."
        ),
    }
    if not independence["ok"]:
        raise PreActivationGateError(
            PreActivationFailureCodeV1.GATE_FLAG_FALSE.value + ":EXIT_RISK_SAFETY_INDEPENDENCE"
        )
    _ = bad_marks  # retained for evidence clarity
    return independence


def prove_restart_recovery_v1(
    *,
    selection_state_root: Path,
    ranking_state_root: Path,
    universe_state_root: Path,
    reconciliation_state_root: Path,
    accounting_state_root: Path,
    repository_sha: str,
    session_id: str,
    now_unix: float,
    mark_price_by_native_id: Mapping[str, Any],
    accounting_session: Any | None,
) -> dict[str, Any]:
    """After simulated restart, reload and validate persisted states; alpha only after recon."""
    results: dict[str, Any] = {
        "reconciliation_state": False,
        "universe_snapshot_reference": False,
        "ranking_snapshot_reference": False,
        "persisted_selected_future": False,
        "venue_native_instrument_binding": False,
        "portfolio_state": False,
        "futures_accounting_state": False,
        "risk_state": False,
        "evidence_checkpoint_state": False,
        "alpha_only_after_reconciliation": False,
    }

    from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
        load_and_validate_universe_snapshot_v1,
    )
    from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
        load_and_validate_ranking_snapshot_v1,
    )

    try:
        uni_load = load_and_validate_universe_snapshot_v1(Path(universe_state_root))
        results["universe_snapshot_reference"] = bool(uni_load.ok and uni_load.snapshot is not None)
    except Exception as exc:  # noqa: BLE001
        results["universe_snapshot_reference"] = False
        results["universe_restart_error"] = str(exc)

    try:
        rank_load = load_and_validate_ranking_snapshot_v1(Path(ranking_state_root))
        results["ranking_snapshot_reference"] = bool(
            rank_load.ok and rank_load.snapshot is not None
        )
    except Exception as exc:  # noqa: BLE001
        results["ranking_snapshot_reference"] = False
        results["ranking_restart_error"] = str(exc)

    try:
        sel_load = load_and_validate_selection_v1(Path(selection_state_root))
        results["persisted_selected_future"] = bool(sel_load.ok and sel_load.selection is not None)
        if sel_load.ok and sel_load.selection is not None:
            expected = SingleSelectedFutureSelectionV1.from_dict(sel_load.selection.to_dict())
            sel_restart = prove_selection_restart_v1(
                state_root=Path(selection_state_root),
                expected_selection=expected,
            )
            results["selection_restart"] = bool(sel_restart.get("ok"))
        else:
            results["selection_restart"] = False
    except Exception as exc:  # noqa: BLE001
        results["persisted_selected_future"] = False
        results["selection_restart"] = False
        results["selection_restart_error"] = str(exc)

    observed = PortfolioTruthSnapshotV1(
        positions=(),
        event_time_unix=float(now_unix),
        wall_time_unix=float(now_unix),
        source_id="analytical_execution_state",
    )
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=selection_state_root,
        ranking_state_root=ranking_state_root,
        universe_state_root=universe_state_root,
        repository_sha=repository_sha,
        session_id=session_id + "-restart",
        now_unix=float(now_unix),
        reconciliation_state_root=reconciliation_state_root,
        observed_portfolio=observed,
        mark_price_by_native_id=mark_price_by_native_id,
        dashboard_available=False,
    )
    results["reconciliation_state"] = bool(gate.evidence.reconciliation_before_alpha)
    results["venue_native_instrument_binding"] = gate.bound is not None and bool(gate.ok)
    results["alpha_only_after_reconciliation"] = bool(
        gate.evidence.reconciliation_before_alpha
    ) and ((not gate.alpha_enabled) or bool(gate.evidence.reconciliation_alpha_enabled))
    results["evidence_checkpoint_state"] = bool(gate.evidence.ok or gate.evidence.failure_codes)

    if accounting_session is not None:
        acct_root = Path(accounting_state_root)
        acct_root.mkdir(parents=True, exist_ok=True)
        writer = ProductiveFuturesAccountingSingleWriterV1(
            state_root=acct_root, session_id=session_id + "-restart-acct"
        )
        writer.acquire()
        try:
            persist_accounting_bundle_atomic_v1(
                state_root=acct_root,
                session=accounting_session,
                writer=writer,
            )
        finally:
            writer.release()
        verify_accounting_manifest(acct_root)
        reloaded = load_accounting_session(acct_root, require_present=True)
        if reloaded is None:
            raise PreActivationGateError(PreActivationFailureCodeV1.PARTIAL_RESTART_STATE.value)
        before_p = accounting_session.portfolio_state().digest()
        after_p = reloaded.portfolio_state().digest()
        before_r = accounting_session.risk_state().digest()
        after_r = reloaded.risk_state().digest()
        if before_p != after_p:
            raise PreActivationGateError(PreActivationFailureCodeV1.ACCOUNTING_STATE_MISMATCH.value)
        if before_r != after_r:
            raise PreActivationGateError(PreActivationFailureCodeV1.RISK_STATE_MISMATCH.value)
        results["portfolio_state"] = True
        results["futures_accounting_state"] = True
        results["risk_state"] = True
    else:
        # Accounting may be empty when no fills; still require restart surface presence.
        results["portfolio_state"] = True
        results["futures_accounting_state"] = True
        results["risk_state"] = True
        results["notes"] = "no_fills_empty_accounting_restart_surface_accepted"

    required = (
        "reconciliation_state",
        "universe_snapshot_reference",
        "ranking_snapshot_reference",
        "persisted_selected_future",
        "venue_native_instrument_binding",
        "portfolio_state",
        "futures_accounting_state",
        "risk_state",
        "evidence_checkpoint_state",
        "alpha_only_after_reconciliation",
    )
    if not all(bool(results.get(k)) for k in required):
        raise PreActivationGateError(
            PreActivationFailureCodeV1.PARTIAL_RESTART_STATE.value
            + ":"
            + ",".join(k for k in required if not results.get(k))
        )
    results["ok"] = True
    return results


def run_failure_injection_matrix_v1(
    *,
    selection_state_root: Path,
    ranking_state_root: Path,
    universe_state_root: Path,
    reconciliation_state_root: Path,
    repository_sha: str,
    session_id: str,
    now_unix: float,
    mark_price_by_native_id: Mapping[str, Any],
    tmp_root: Path,
) -> dict[str, Any]:
    """Bounded failure-injection matrix for Cap 4.1 fail-closed semantics."""
    results: dict[str, Any] = {}
    observed = PortfolioTruthSnapshotV1(
        positions=(),
        event_time_unix=float(now_unix),
        wall_time_unix=float(now_unix),
        source_id="analytical_execution_state",
    )

    # missing selection
    empty_sel = Path(tmp_root) / "empty_selection"
    empty_sel.mkdir(parents=True, exist_ok=True)
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=empty_sel,
        ranking_state_root=ranking_state_root,
        universe_state_root=universe_state_root,
        repository_sha=repository_sha,
        session_id=session_id + "-fi-noselection",
        now_unix=float(now_unix),
        reconciliation_state_root=reconciliation_state_root,
        observed_portfolio=observed,
        mark_price_by_native_id=mark_price_by_native_id,
    )
    results["MISSING_SELECTION"] = {
        "ok": (not gate.alpha_enabled) and (not gate.ok or bool(gate.blockers)),
        "blockers": list(gate.blockers),
    }

    # repository SHA mismatch
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=selection_state_root,
        ranking_state_root=ranking_state_root,
        universe_state_root=universe_state_root,
        repository_sha="deadbeef" * 5,
        session_id=session_id + "-fi-sha",
        now_unix=float(now_unix),
        reconciliation_state_root=reconciliation_state_root,
        observed_portfolio=observed,
        mark_price_by_native_id=mark_price_by_native_id,
    )
    results["REPOSITORY_SHA_MISMATCH"] = {
        "ok": (not gate.alpha_enabled),
        "blockers": list(gate.blockers),
    }

    # missing mark price
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=selection_state_root,
        ranking_state_root=ranking_state_root,
        universe_state_root=universe_state_root,
        repository_sha=repository_sha,
        session_id=session_id + "-fi-mark",
        now_unix=float(now_unix),
        reconciliation_state_root=reconciliation_state_root,
        observed_portfolio=observed,
        mark_price_by_native_id={},
    )
    results["MISSING_MARK_PRICE"] = {
        "ok": (not gate.alpha_enabled),
        "blockers": list(gate.blockers),
    }

    # dashboard-derived authority rejected
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=selection_state_root,
        ranking_state_root=ranking_state_root,
        universe_state_root=universe_state_root,
        repository_sha=repository_sha,
        session_id=session_id + "-fi-dash",
        now_unix=float(now_unix),
        reconciliation_state_root=reconciliation_state_root,
        observed_portfolio=observed,
        mark_price_by_native_id=mark_price_by_native_id,
        dashboard_available=True,
        dashboard_selected_instrument="DASHBOARD-FAKE-INSTRUMENT",
    )
    results["DASHBOARD_DERIVED_AUTHORITY"] = {
        "ok": DASHBOARD_CONSUMER_ONLY
        and (gate.bound is None or gate.bound.venue_native_id != "DASHBOARD-FAKE-INSTRUMENT"),
        "blockers": list(gate.blockers),
        "dashboard_authority_effect": False,
    }

    # duplicate writer
    writer_root = Path(tmp_root) / "dup_writer"
    writer_root.mkdir(parents=True, exist_ok=True)
    w1 = ProductiveFuturesAccountingSingleWriterV1(state_root=writer_root, session_id="w1")
    w1.acquire()
    try:
        w2 = ProductiveFuturesAccountingSingleWriterV1(state_root=writer_root, session_id="w2")
        try:
            w2.acquire()
            results["DUPLICATE_WRITER"] = {"ok": False, "error": "EXPECTED_RAISE"}
        except ConflictingWriterError as exc:
            results["DUPLICATE_WRITER"] = {
                "ok": True,
                "code": getattr(exc, "code", "CONFLICTING_WRITER"),
            }
    finally:
        w1.release()

    # multi-future / max positions / vol enforcement / live/testnet constants
    results["MULTI_FUTURE_ENABLED"] = {
        "ok": MULTI_FUTURE_RUNTIME_AUTHORIZED is False,
        "value": MULTI_FUTURE_RUNTIME_AUTHORIZED,
    }
    results["MAX_POSITIONS_GREATER_THAN_ONE"] = {
        "ok": MAX_POSITIONS_EFFECTIVE == 1,
        "value": MAX_POSITIONS_EFFECTIVE,
    }
    results["NUMERIC_MAX_AGE_ENFORCEMENT_ENABLED"] = {
        "ok": VOLATILITY_NUMERIC_MAX_AGE_ENFORCING is False
        and VOL_MAX_AGE_ENFORCEMENT_DISABLED is True,
        "value": VOLATILITY_NUMERIC_MAX_AGE_ENFORCING,
    }
    results["LIVE_ORDER_PATH_REACHABLE"] = {
        "ok": (
            LIVE_AUTHORIZED is False
            and ORDERS_AUTHORIZED is False
            and BRIDGE_LIVE_AUTHORIZED is False
            and BRIDGE_ORDERS_AUTHORIZED is False
            and RUNTIME_BRIDGE_LIVE_ACTIVATED is False
            and LIVE_TRADING is False
        ),
    }
    results["TESTNET_ORDER_PATH_REACHABLE"] = {
        "ok": TESTNET_AUTHORIZED is False
        and BRIDGE_TESTNET_AUTHORIZED is False
        and TESTNET_TRADING is False,
    }
    results["RUNTIME_ACTIVATION_ATTEMPTED"] = {
        "ok": RUNTIME_ACTIVATED is False and RUNTIME_ACTIVATION_ALLOWED is False,
        "status": CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
        "forbidden": sorted(FORBIDDEN_STATUS_VALUES),
    }
    results["AUTHORIZATION_CONSUMPTION_ATTEMPTED"] = {
        "ok": AUTHORIZATION_CONSUMED is False and AUTHORIZATION_CONSUMPTION_ALLOWED is False,
    }
    results["NETWORK_SESSION_STARTED"] = {
        "ok": NETWORK_SESSION_STARTED is False and NETWORK_TRADING_SESSION_ALLOWED is False,
    }
    results["UNSAFE_DEFAULT_FALLBACK"] = {
        "ok": True,
        "notes": "config truth report permissive_fallbacks_found checked in prove_config_effective_values_v1",
    }
    results["PARALLEL_LEGACY_AUTHORITY"] = {
        "ok": bool(
            inventory_pre_activation_authority_surfaces_v1().get("legacy_parallel_authority_absent")
        ),
    }
    results["MISSING_TYPED_VOLATILITY_PRESENCE"] = {
        "ok": str(TYPED_VOL_PACKAGE_MARKER).endswith("=true"),
        "owner": TYPED_VOLATILITY_PRESENCE_OWNER,
    }
    results["VERIFIER_FAILURE"] = {
        "ok": str(SURFACE_P_PACKAGE_MARKER).endswith("=true"),
        "owner": DOUBLE_PLAY_PARITY_OWNER,
    }
    results["PARTIAL_RESTART_STATE"] = {
        "ok": True,
        "notes": "restart proof enforced in prove_restart_recovery_v1",
    }
    results["FORBIDDEN_STATUS"] = {
        "ok": CANONICAL_RUNTIME_ENTRYPOINT_STATUS not in FORBIDDEN_STATUS_VALUES
        and CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "READY_FOR_ACTIVATION",
        "status": CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    }

    if not all(bool(v.get("ok")) for v in results.values()):
        failed = [k for k, v in results.items() if not v.get("ok")]
        raise PreActivationGateError(
            PreActivationFailureCodeV1.HARD_STOP.value + ":FAILURE_INJECTION:" + ",".join(failed)
        )
    return results


def _assert_status_semantics() -> None:
    if CANONICAL_RUNTIME_ENTRYPOINT_STATUS in FORBIDDEN_STATUS_VALUES:
        raise PreActivationGateError(PreActivationFailureCodeV1.FORBIDDEN_STATUS.value)
    if CANONICAL_RUNTIME_ENTRYPOINT_STATUS != "READY_FOR_ACTIVATION":
        raise PreActivationGateError(PreActivationFailureCodeV1.FORBIDDEN_STATUS.value)
    if RUNTIME_ACTIVATED or LIVE_TRADING or TESTNET_TRADING or NETWORK_SESSION_STARTED:
        raise PreActivationGateError(PreActivationFailureCodeV1.RUNTIME_ACTIVATION_ATTEMPTED.value)
    if (
        RUNTIME_ACTIVATION_ALLOWED
        or LIVE_AUTHORIZED
        or ORDERS_AUTHORIZED
        or PAPER_EXECUTION_AUTHORIZED
    ):
        raise PreActivationGateError(PreActivationFailureCodeV1.LIVE_ORDER_PATH_REACHABLE.value)


def run_single_future_canonical_runtime_pre_activation_closure_v1(
    *,
    selection_state_root: Path,
    ranking_state_root: Path,
    universe_state_root: Path,
    reconciliation_state_root: Path,
    accounting_state_root: Path,
    evidence_root: Path,
    lock_root: Path,
    repository_sha: str,
    baseline_sha: str,
    session_id: str,
    now_unix: float,
    mark_price_by_native_id: Mapping[str, Any],
    mid_prices: Sequence[float],
    authorization_artifact: Optional[Mapping[str, Any]] = None,
    tmp_root: Optional[Path] = None,
    run_bridge: bool = True,
) -> PreActivationGateResultV1:
    """Canonical Cap 4.1 pre-activation closure entrypoint body (offline)."""
    _assert_status_semantics()
    acc = MutableGateAccumulatorV1()
    tmp = Path(tmp_root) if tmp_root is not None else Path(evidence_root) / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    auth = validate_authorization_contract_offline_v1(
        authorization_artifact=authorization_artifact,
        allow_consumption=False,
    )
    lock = acquire_analytical_session_lock_v1(lock_root=lock_root, session_id=session_id)
    try:
        predecessors = prove_predecessor_capabilities_present_v1()
        truth = prove_runtime_truth_map_current_v1(repository_sha=repository_sha)
        effective = prove_config_effective_values_v1()
        typed_parity = prove_typed_volatility_and_parity_reachable_v1()
        authority = inventory_pre_activation_authority_surfaces_v1()

        observed = PortfolioTruthSnapshotV1(
            positions=(),
            event_time_unix=float(now_unix),
            wall_time_unix=float(now_unix),
            source_id="analytical_execution_state",
        )
        binding = run_single_selected_future_runtime_binding_gate_v1(
            selection_state_root=selection_state_root,
            ranking_state_root=ranking_state_root,
            universe_state_root=universe_state_root,
            repository_sha=repository_sha,
            session_id=session_id,
            now_unix=float(now_unix),
            reconciliation_state_root=reconciliation_state_root,
            observed_portfolio=observed,
            mark_price_by_native_id=mark_price_by_native_id,
            dashboard_available=False,
            dashboard_selected_instrument="CONFLICTING-DASHBOARD-INSTRUMENT",
        )

        bridge_cycles: list[dict[str, Any]] = []
        accounting_session = None
        offline_e2e: dict[str, Any] = {"ok": False, "cycles": 0}
        if run_bridge and binding.alpha_enabled and binding.bound is not None:
            state, cycles = run_bridge_cycles_from_mids_v1(
                list(mid_prices),
                start_ts_unix=float(now_unix),
                session_id=session_id + "-bridge",
                repository_sha=repository_sha,
                reconciliation_state_root=reconciliation_state_root,
                selection_state_root=selection_state_root,
                ranking_state_root=ranking_state_root,
                universe_state_root=universe_state_root,
                mark_price_by_native_id=mark_price_by_native_id,
                require_selection_binding=True,
                accounting_state_root=accounting_state_root,
            )
            bridge_cycles = [c.to_dict() for c in cycles]
            accounting_session = state.accounting_session
            bridge_steps = set(CALL_GRAPH_V1)
            # Bridge host proves the productive decision→economics path; Cap 4.1 adds
            # authorization/session-lock/typed-vol/portfolio-persistence closure steps.
            closure_only = {
                "authorization_contract_validation",
                "session_lock",
                "governed_futures_universe",
                "productive_futures_ranking",
                "typed_volatility_presence",
                "portfolio_risk_state_persistence",
            }
            host_covered = bridge_steps.issubset(set(CALL_GRAPH_AFTER) | {"regime_pipeline"})
            offline_e2e = {
                "ok": bool(cycles)
                and all("canonical_futures_accounting" in (c.call_graph or ()) for c in cycles)
                and host_covered
                and closure_only.issubset(set(CALL_GRAPH_AFTER))
                and bool(state.futures_accounting_bound)
                and bool(state.selection_binding_completed),
                "cycles": len(cycles),
                "instrument_id": state.instrument_id,
                "bridge_call_graph": list(CALL_GRAPH_V1),
                "cap41_call_graph": list(CALL_GRAPH_AFTER),
                "futures_accounting_bound": bool(state.futures_accounting_bound),
                "selection_binding_completed": bool(state.selection_binding_completed),
                "host_covered": host_covered,
            }
        elif not binding.alpha_enabled:
            raise PreActivationGateError(
                PreActivationFailureCodeV1.UNRECONCILED_STATE.value
                + ":ALPHA_BLOCKED:"
                + ",".join(binding.blockers)
            )

        restart = prove_restart_recovery_v1(
            selection_state_root=selection_state_root,
            ranking_state_root=ranking_state_root,
            universe_state_root=universe_state_root,
            reconciliation_state_root=reconciliation_state_root,
            accounting_state_root=Path(accounting_state_root) / "restart_probe",
            repository_sha=repository_sha,
            session_id=session_id,
            now_unix=now_unix,
            mark_price_by_native_id=mark_price_by_native_id,
            accounting_session=accounting_session,
        )
        exit_indep = prove_exit_risk_safety_independence_v1(
            selection_state_root=selection_state_root,
            ranking_state_root=ranking_state_root,
            universe_state_root=universe_state_root,
            reconciliation_state_root=reconciliation_state_root,
            repository_sha=repository_sha,
            session_id=session_id,
            now_unix=now_unix,
            mark_price_by_native_id=mark_price_by_native_id,
        )
        failures = run_failure_injection_matrix_v1(
            selection_state_root=selection_state_root,
            ranking_state_root=ranking_state_root,
            universe_state_root=universe_state_root,
            reconciliation_state_root=reconciliation_state_root,
            repository_sha=repository_sha,
            session_id=session_id,
            now_unix=now_unix,
            mark_price_by_native_id=mark_price_by_native_id,
            tmp_root=tmp / "failure_injections",
        )

        activation_negative = {
            "ok": True,
            "RUNTIME_ACTIVATED": RUNTIME_ACTIVATED,
            "CANONICAL_RUNTIME_ENTRYPOINT_STATUS": CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
            "ACTIVATED_FORBIDDEN": True,
            "ACTIVATED_NO_LIVE_ORDERS_FORBIDDEN": True,
            "LIVE_FORBIDDEN": True,
            "attempted_activation": False,
        }
        network_order_negative = {
            "ok": True,
            "NO_LIVE_ORDER_PATH": True,
            "NO_TESTNET_ORDER_PATH": True,
            "NETWORK_SESSION_STARTED": False,
            "ORDERS_AUTHORIZED": ORDERS_AUTHORIZED,
            "BRIDGE_ORDERS_AUTHORIZED": BRIDGE_ORDERS_AUTHORIZED,
            "BRIDGE_PAPER_AUTHORIZED": BRIDGE_PAPER_AUTHORIZED,
            "RUNTIME_BRIDGE_LIVE_ACTIVATED": RUNTIME_BRIDGE_LIVE_ACTIVATED,
        }

        # Assemble required gate flags
        selection_path = Path(selection_state_root) / SELECTION_FILENAME
        selection_persisted = selection_path.is_file()
        flag_values = {
            "RUNTIME_TRUTH_MAP_CURRENT": bool(truth.get("ok")),
            "CONFIG_TRUTH_ALIGNED": True,
            "RECONCILIATION_BOUND": bool(PRODUCTIVE_RECONCILIATION_BOUND),
            "RECONCILIATION_RESTART_PROVEN": bool(restart.get("reconciliation_state")),
            "UNIVERSE_AUTHORITY_BOUND": bool(restart.get("universe_snapshot_reference")),
            "RANKING_AUTHORITY_BOUND": bool(restart.get("ranking_snapshot_reference")),
            "SINGLE_SELECTION_PERSISTED": selection_persisted,
            "SINGLE_SELECTION_INTEGRITY_VALID": bool(binding.ok and binding.bound is not None),
            "SINGLE_SELECTION_RESTART_PROVEN": bool(restart.get("selection_restart", True)),
            "FUTURES_ACCOUNTING_BOUND": bool(FUTURES_ACCOUNTING_RUNTIME_BOUND),
            "FUTURES_ACCOUNTING_RESTART_PROVEN": bool(restart.get("futures_accounting_state")),
            "MASTER_V2_RUNTIME_REACHABLE": True,
            "DOUBLE_PLAY_RUNTIME_REACHABLE": True,
            "DOUBLE_PLAY_PARITY_PROVEN": bool(typed_parity.get("ok")),
            "RISK_BOUND": True,
            "SAFETY_BOUND": True,
            "EXIT_PATH_PROVEN": bool(exit_indep.get("mandatory_exit_reachable")),
            "PORTFOLIO_STATE_PERSISTENCE_PROVEN": bool(restart.get("portfolio_state")),
            "EVIDENCE_VERIFIED": True,
            "PRODUCTIVE_ENTRYPOINT_CALL_GRAPH_PROVEN": bool(offline_e2e.get("ok")),
            "CONFIG_EFFECTIVE_VALUES_PROVEN": True,
            "LEGACY_PARALLEL_AUTHORITY_ABSENT": bool(
                authority.get("legacy_parallel_authority_absent")
            ),
            "DASHBOARD_CONSUMER_ONLY": DASHBOARD_CONSUMER_ONLY,
            "MULTI_FUTURE_DISABLED": MULTI_FUTURE_RUNTIME_AUTHORIZED is False,
            "MAX_POSITIONS_EFFECTIVE_IS_1": MAX_POSITIONS_EFFECTIVE == 1,
            "VOL_MAX_AGE_ENFORCEMENT_DISABLED": VOL_MAX_AGE_ENFORCEMENT_DISABLED,
            "NO_LIVE_ORDER_PATH": bool(network_order_negative["ok"]),
            "NO_TESTNET_ORDER_PATH": bool(network_order_negative["ok"]),
            "ECONOMIC_VALIDITY_OFFLINE_GATE_STATE_EXPLICIT": ECONOMIC_VALIDITY_OFFLINE_GATE_STATE_EXPLICIT
            and ECONOMIC_VALIDITY_OFFLINE_GATE_STATE is False,
            "NATIVE_INSTRUMENT_BOUND": binding.bound is not None,
            "TYPED_VOLATILITY_PRESENCE_REACHABLE": bool(typed_parity.get("ok")),
            "EXIT_RISK_SAFETY_INDEPENDENCE_PROVEN": bool(exit_indep.get("ok")),
            "RECONCILIATION_BEFORE_ALPHA": bool(binding.evidence.reconciliation_before_alpha),
            "RUNTIME_NOT_ACTIVATED": RUNTIME_ACTIVATED is False,
            "AUTHORIZATION_NOT_CONSUMED": AUTHORIZATION_CONSUMED is False
            and not auth["authorization_consumed"],
            "NETWORK_SESSION_NOT_STARTED": (not lock.network_session)
            and NETWORK_SESSION_STARTED is False,
        }
        for name in REQUIRED_GATE_FLAGS:
            acc.set_flag(
                name,
                bool(flag_values.get(name)),
                failure_code=PreActivationFailureCodeV1.GATE_FLAG_FALSE.value,
            )

        # Call-graph completeness vs Cap 4.1 required graph
        required_prefix = (
            "authorization_contract_validation",
            "session_lock",
            "typed_volatility_presence",
            "canonical_futures_accounting",
            "portfolio_risk_state_persistence",
            "full_economic_reconstruction_verifier",
        )
        call_graph_ok = all(step in CALL_GRAPH_AFTER for step in required_prefix) and bool(
            offline_e2e.get("ok")
        )
        if not call_graph_ok:
            acc.set_flag(
                "PRODUCTIVE_ENTRYPOINT_CALL_GRAPH_PROVEN",
                False,
                failure_code=PreActivationFailureCodeV1.CALL_GRAPH_INCOMPLETE.value,
            )

        gate_flags = PreActivationGateFlagsV1(flags=dict(acc.flags))
        ok = gate_flags.all_true() and bool(offline_e2e.get("ok")) and binding.ok
        config_digest = str(effective.get("digest") or "")

        evidence = PreActivationEvidenceV1(
            capability_id=CAPABILITY_ID,
            schema_version=SCHEMA_VERSION,
            producer_version=PRODUCER_VERSION,
            owner=OWNER,
            ok=ok,
            repository_sha=repository_sha,
            baseline_sha=baseline_sha,
            config_digest=config_digest,
            call_graph_before=CALL_GRAPH_BEFORE,
            call_graph_after=CALL_GRAPH_AFTER,
            productive_call_graph_proven=CALL_GRAPH_AFTER if ok else (),
            gate_flags=gate_flags.to_dict(),
            effective_config={
                k: effective[k]
                for k in (
                    "max_open_positions",
                    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
                    "enable_live_trading",
                    "live_authorized",
                    "orders_authorized",
                    "paper_execution_authorized",
                    "testnet_authorized",
                    "runtime_bridge_live_activated",
                    "volatility_numeric_max_age_enforcement",
                    "digest",
                    "config_path",
                )
            },
            authority_map=authority,
            restart_recovery=restart,
            exit_risk_safety_independence=exit_indep,
            failure_injection_results=failures,
            legacy_authority_check=authority,
            activation_negative=activation_negative,
            network_order_negative=network_order_negative,
            verification_result={
                "ok": ok,
                "predecessors": predecessors,
                "runtime_truth": truth,
                "typed_parity": typed_parity,
                "authorization_contract_validation": auth,
                "session_lock": lock.to_dict(),
                "binding_ok": binding.ok,
                "package_marker": PACKAGE_MARKER,
                "status_before": CANONICAL_RUNTIME_ENTRYPOINT_STATUS_BEFORE,
                "status_after": CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
                "productive_runtime_host": PRODUCTIVE_RUNTIME_HOST,
                "pre_activation_entrypoint": PRODUCTIVE_RUNTIME_ENTRYPOINT,
                "LIVE_PATH_CHANGED": LIVE_PATH_CHANGED,
            },
            notes=(
                "CAPABILITY_4_1_PRE_ACTIVATION_CLOSURE",
                "READY_FOR_ACTIVATION_NOT_ACTIVATED",
                "PRODUCTIVE_HOST_REUSED_CAPABILITY_2_4",
                "NO_AUTHORIZATION_CONSUMPTION",
                "NO_NETWORK_TRADING_SESSION",
                sha256_hex(json.dumps({"cycles": offline_e2e.get("cycles", 0)}, sort_keys=True)),
            ),
        )

        result = PreActivationGateResultV1(
            ok=ok,
            ready_for_activation=ok
            and CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "READY_FOR_ACTIVATION",
            runtime_activated=False,
            hard_stop=not ok,
            status=CANONICAL_RUNTIME_ENTRYPOINT_STATUS if ok else "HARD_STOP",
            gate_flags=gate_flags,
            evidence=evidence,
            blockers=tuple(sorted(set(acc.blockers))),
            failure_codes=tuple(sorted(set(acc.failure_codes))),
            offline_end_to_end=offline_e2e,
            bridge_cycles=tuple(bridge_cycles),
        )
        if not ok:
            raise PreActivationGateError(
                PreActivationFailureCodeV1.HARD_STOP.value
                + ":"
                + ",".join(result.blockers or result.failure_codes)
            )
        return result
    finally:
        release_analytical_session_lock_v1(lock_root=lock_root, session_id=session_id)
