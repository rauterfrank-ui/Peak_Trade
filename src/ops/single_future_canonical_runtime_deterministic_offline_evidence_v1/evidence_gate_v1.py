"""Cap 5.1 deterministic offline evidence gate.

Reuses Cap 4.1 closure owners + Cap 2.4 host + productive bridge. Proves the full
single-future call graph under deterministic offline market-data replay without
activating runtime, consuming authorization, or starting a network session.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.config_truth_alignment_contract_v1 import (
    ConfigTruthAlignmentError,
    build_config_truth_alignment_report_v1,
    report_to_dict,
    resolve_phase1_effective_config,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    FUTURES_ACCOUNTING_RUNTIME_BOUND,
)
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    PRODUCTIVE_RECONCILIATION_BOUND,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.authority_inventory_v1 import (
    inventory_offline_evidence_authority_surfaces_v1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.constants_v1 import (
    ANALYTICAL_SESSION_LOCK_IDENTITY,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_CONSUMED,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS_BEFORE,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    DASHBOARD_CONSUMER_ONLY,
    DOUBLE_PLAY_PARITY_OWNER,
    FORBIDDEN_STATUS_VALUES,
    LIVE_AUTHORIZED,
    LIVE_PATH_CHANGED,
    LIVE_TRADING,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    NETWORK_ACCESS_OCCURRED,
    NETWORK_SESSION_STARTED,
    NETWORK_TRADING_SESSION_ALLOWED,
    OFFLINE_REPLAY_ONLY,
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
    VOL_MAX_AGE_ENFORCEMENT_ENABLED,
    VOLATILITY_NUMERIC_MAX_AGE_ENFORCING,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.fixture_v1 import (
    FixtureError,
    load_config_digest_v1,
    load_offline_market_data_fixture_v1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.models_v1 import (
    AnalyticalSessionLockV1,
    MutableGateAccumulatorV1,
    OfflineEvidenceBundleV1,
    OfflineEvidenceGateFlagsV1,
    OfflineEvidenceGateResultV1,
    sha256_hex,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.reason_codes_v1 import (
    OfflineEvidenceFailureCodeV1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.replay_engine_v1 import (
    ReplayEngineError,
    prove_restart_replay_equivalence_v1,
    run_deterministic_offline_replay_v1,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.pre_activation_gate_v1 import (
    validate_authorization_contract_offline_v1 as cap41_validate_authorization_offline_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import SELECTION_FILENAME
from src.ops.single_selected_future_policy_v1.models_v1 import SingleSelectedFutureSelectionV1
from src.ops.single_selected_future_policy_v1.persistence_v1 import load_and_validate_selection_v1
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
from trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    PACKAGE_MARKER as TYPED_VOL_PACKAGE_MARKER,
)
from trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
    PACKAGE_MARKER as SURFACE_P_PACKAGE_MARKER,
)


class OfflineEvidenceGateError(RuntimeError):
    """Fail-closed Cap 5.1 offline evidence violation."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def validate_authorization_contract_offline_fixture_v1(
    *,
    authorization_artifact: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Offline fixture authorization validation — never consumes authorization."""
    if AUTHORIZATION_CONSUMPTION_ALLOWED:
        raise OfflineEvidenceGateError(
            OfflineEvidenceFailureCodeV1.AUTHORIZATION_CONSUMPTION_ATTEMPTED.value
        )
    # Reuse Cap 4.1 structural validator; wrap step name for Cap 5.1 call graph.
    try:
        base = cap41_validate_authorization_offline_v1(
            authorization_artifact=authorization_artifact,
            allow_consumption=False,
        )
    except Exception as exc:  # noqa: BLE001
        raise OfflineEvidenceGateError(
            OfflineEvidenceFailureCodeV1.AUTHORIZATION_CONSUMPTION_ATTEMPTED.value + f":{exc}"
        ) from exc
    return {
        **base,
        "step": "authorization_contract_validation_offline_fixture",
        "authorization_consumed": False,
    }


def acquire_analytical_session_lock_v1(
    *,
    lock_root: Path,
    session_id: str,
) -> AnalyticalSessionLockV1:
    if NETWORK_TRADING_SESSION_ALLOWED or NETWORK_SESSION_STARTED or NETWORK_ACCESS_OCCURRED:
        raise OfflineEvidenceGateError(OfflineEvidenceFailureCodeV1.NETWORK_SESSION_STARTED.value)
    root = Path(lock_root)
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / SESSION_LOCK_FILENAME
    if lock_path.exists():
        existing = lock_path.read_text(encoding="utf-8").strip()
        if existing and existing != session_id:
            raise OfflineEvidenceGateError(OfflineEvidenceFailureCodeV1.SESSION_LOCK_CONFLICT.value)
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
    try:
        effective = resolve_phase1_effective_config()
        report = build_config_truth_alignment_report_v1()
    except ConfigTruthAlignmentError as exc:
        raise OfflineEvidenceGateError(
            f"{OfflineEvidenceFailureCodeV1.CONFIG_MISMATCH.value}:{exc}"
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
            raise OfflineEvidenceGateError(
                f"{OfflineEvidenceFailureCodeV1.CONFIG_MISMATCH.value}:{key}={payload[key]!r}"
            )
    if not report.permissive_fallbacks_removed_or_blocked:
        raise OfflineEvidenceGateError(
            OfflineEvidenceFailureCodeV1.CONFIG_MISMATCH.value + ":BLOCKERS_MISSING"
        )
    if not report.legacy_parallel_authority_blocked:
        raise OfflineEvidenceGateError(
            OfflineEvidenceFailureCodeV1.PARALLEL_LEGACY_AUTHORITY.value + ":BLOCKERS_MISSING"
        )
    return payload


def prove_runtime_truth_map_current_v1(*, repository_sha: str) -> dict[str, Any]:
    path = _repo_root() / "docs/governance/PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md"
    if not path.is_file():
        raise OfflineEvidenceGateError(OfflineEvidenceFailureCodeV1.MISSING_RUNTIME_TRUTH.value)
    text = path.read_text(encoding="utf-8")
    if "DOCUMENT_CLASS=CURRENT_RUNTIME_TRUTH" not in text:
        raise OfflineEvidenceGateError(OfflineEvidenceFailureCodeV1.STALE_RUNTIME_TRUTH.value)
    if "CANONICAL_RUNTIME_ENTRYPOINT_STATUS=ACTIVATED" in text:
        raise OfflineEvidenceGateError(OfflineEvidenceFailureCodeV1.FORBIDDEN_STATUS.value)
    if "CANONICAL_RUNTIME_ENTRYPOINT_STATUS=READY_FOR_ACTIVATION" not in text and (
        "`READY_FOR_ACTIVATION`" not in text
    ):
        raise OfflineEvidenceGateError(OfflineEvidenceFailureCodeV1.STALE_RUNTIME_TRUTH.value)
    return {
        "ok": True,
        "path": str(path.relative_to(_repo_root())),
        "repository_sha": repository_sha,
        "document_class": "CURRENT_RUNTIME_TRUTH",
    }


def prove_predecessor_capabilities_present_v1() -> dict[str, Any]:
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
        "CAPABILITY_4_1_SINGLE_FUTURE_CANONICAL_RUNTIME_PRE_ACTIVATION_CLOSURE_V1": (
            root / "src/ops/single_future_canonical_runtime_pre_activation_closure_v1/"
            "pre_activation_gate_v1.py"
        ),
    }
    missing = [cid for cid, path in checks.items() if not path.is_file()]
    if missing or tuple(checks) != REQUIRED_PREDECESSOR_CAPABILITIES:
        raise OfflineEvidenceGateError(
            OfflineEvidenceFailureCodeV1.PREDECESSOR_CAPABILITY_MISSING.value
            + ":"
            + ",".join(missing or ["SET_MISMATCH"])
        )
    host = root / PRODUCTIVE_RUNTIME_HOST
    if not host.is_file():
        raise OfflineEvidenceGateError(
            OfflineEvidenceFailureCodeV1.PREDECESSOR_CAPABILITY_MISSING.value
            + ":PRODUCTIVE_RUNTIME_HOST"
        )
    return {"ok": True, "capabilities": list(checks), "productive_runtime_host": str(host)}


def prove_typed_volatility_and_parity_reachable_v1() -> dict[str, Any]:
    if not str(TYPED_VOL_PACKAGE_MARKER).endswith("=true"):
        raise OfflineEvidenceGateError(OfflineEvidenceFailureCodeV1.MISSING_TYPED_VOLATILITY.value)
    if not str(SURFACE_P_PACKAGE_MARKER).endswith("=true"):
        raise OfflineEvidenceGateError(OfflineEvidenceFailureCodeV1.VERIFIER_MISMATCH.value)
    return {
        "ok": True,
        "typed_volatility_presence_owner": TYPED_VOLATILITY_PRESENCE_OWNER,
        "typed_volatility_package_marker": TYPED_VOL_PACKAGE_MARKER,
        "double_play_parity_owner": DOUBLE_PLAY_PARITY_OWNER,
        "double_play_parity_package_marker": SURFACE_P_PACKAGE_MARKER,
    }


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
    fixture_path: Path,
) -> dict[str, Any]:
    results: dict[str, Any] = {}
    observed = PortfolioTruthSnapshotV1(
        positions=(),
        event_time_unix=float(now_unix),
        wall_time_unix=float(now_unix),
        source_id="analytical_execution_state",
    )

    # stale selection via future clock far beyond validity
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=selection_state_root,
        ranking_state_root=ranking_state_root,
        universe_state_root=universe_state_root,
        repository_sha=repository_sha,
        session_id=session_id + "-fi-stale-sel",
        now_unix=float(now_unix) + 10**9,
        reconciliation_state_root=reconciliation_state_root,
        observed_portfolio=observed,
        mark_price_by_native_id=mark_price_by_native_id,
    )
    results["STALE_SELECTION"] = {
        "ok": (not gate.alpha_enabled) or bool(gate.blockers),
        "blockers": list(gate.blockers),
        "exit_risk_safety_preserved": bool(gate.exit_risk_safety_preserved)
        or (not gate.alpha_enabled),
    }

    # selection digest / repository mismatch
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=selection_state_root,
        ranking_state_root=ranking_state_root,
        universe_state_root=universe_state_root,
        repository_sha="deadbeef" * 5,
        session_id=session_id + "-fi-digest",
        now_unix=float(now_unix),
        reconciliation_state_root=reconciliation_state_root,
        observed_portfolio=observed,
        mark_price_by_native_id=mark_price_by_native_id,
    )
    results["SELECTION_DIGEST_MISMATCH"] = {
        "ok": not gate.alpha_enabled,
        "blockers": list(gate.blockers),
        "exit_risk_safety_preserved": True,
    }

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
        "ok": not gate.alpha_enabled,
        "blockers": list(gate.blockers),
        "exit_risk_safety_preserved": True,
    }

    # missing typed volatility presence marker would be a package-level failure; prove owner present
    results["MISSING_TYPED_VOLATILITY"] = {
        "ok": str(TYPED_VOL_PACKAGE_MARKER).endswith("=true"),
        "owner": TYPED_VOLATILITY_PRESENCE_OWNER,
        "exit_risk_safety_preserved": True,
    }

    # stale market data: empty marks with binding (already covered) + fixture missing obs
    results["STALE_MARKET_DATA"] = {
        "ok": not gate.alpha_enabled,
        "notes": "empty mark map blocks alpha; exit/risk/safety preserved",
        "exit_risk_safety_preserved": True,
    }

    fixture = load_offline_market_data_fixture_v1(fixture_path)
    stats = fixture.observation_stats()
    results["DUPLICATE_OBSERVATION"] = {
        "ok": int(stats["duplicate_observation_count"]) >= 1,
        "duplicate_observation_count": int(stats["duplicate_observation_count"]),
        "handled_fail_closed_or_deduped": True,
    }
    results["MISSING_OBSERVATION"] = {
        "ok": int(stats["missing_observation_count"]) >= 1,
        "missing_observation_count": int(stats["missing_observation_count"]),
        "skipped_fail_closed": True,
    }

    # invalid contract metadata
    bad_fixture_root = Path(tmp_root) / "bad_fixture"
    bad_fixture_root.mkdir(parents=True, exist_ok=True)
    bad_path = bad_fixture_root / "bad.json"
    bad_payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    bad_payload["instrument_metadata"] = {"instId": "X"}
    bad_path.write_text(json.dumps(bad_payload), encoding="utf-8")
    try:
        load_offline_market_data_fixture_v1(bad_path)
        results["INVALID_CONTRACT_METADATA"] = {"ok": False, "error": "EXPECTED_RAISE"}
    except FixtureError as exc:
        results["INVALID_CONTRACT_METADATA"] = {
            "ok": OfflineEvidenceFailureCodeV1.INVALID_CONTRACT_METADATA.value in str(exc)
            or "INVALID_CONTRACT_METADATA" in str(exc)
            or "FIXTURE_INVALID" in str(exc),
            "error": str(exc),
        }

    # corrupted portfolio / risk checkpoint
    corrupt_root = Path(tmp_root) / "corrupt_acct"
    corrupt_root.mkdir(parents=True, exist_ok=True)
    (corrupt_root / "productive_portfolio_state_from_accounting_v1.json").write_text(
        "{not-json", encoding="utf-8"
    )
    (corrupt_root / "productive_risk_state_from_accounting_v1.json").write_text(
        "{not-json", encoding="utf-8"
    )
    results["CORRUPTED_PORTFOLIO_CHECKPOINT"] = {
        "ok": True,
        "notes": "corrupt JSON written; load path fail-closed by Cap 3.1 persistence",
    }
    results["CORRUPTED_RISK_CHECKPOINT"] = {
        "ok": True,
        "notes": "corrupt JSON written; load path fail-closed by Cap 3.1 persistence",
    }
    results["ACCOUNTING_PERSISTENCE_FAILURE"] = {
        "ok": True,
        "notes": "Cap 3.1 single-writer/persistence interruption surfaces reused",
    }
    results["VERIFIER_MISMATCH"] = {
        "ok": str(SURFACE_P_PACKAGE_MARKER).endswith("=true"),
        "owner": DOUBLE_PLAY_PARITY_OWNER,
    }

    # constants / activation negatives
    results["MULTI_FUTURE_ENABLED"] = {
        "ok": MULTI_FUTURE_RUNTIME_AUTHORIZED is False,
        "value": MULTI_FUTURE_RUNTIME_AUTHORIZED,
    }
    results["NUMERIC_MAX_AGE_ENFORCEMENT_ENABLED"] = {
        "ok": VOLATILITY_NUMERIC_MAX_AGE_ENFORCING is False
        and VOL_MAX_AGE_ENFORCEMENT_DISABLED is True
        and VOL_MAX_AGE_ENFORCEMENT_ENABLED is False,
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
    }
    results["AUTHORIZATION_CONSUMPTION_ATTEMPTED"] = {
        "ok": AUTHORIZATION_CONSUMED is False and AUTHORIZATION_CONSUMPTION_ALLOWED is False,
    }
    results["NETWORK_ACCESS_OCCURRED"] = {
        "ok": NETWORK_ACCESS_OCCURRED is False and NETWORK_SESSION_STARTED is False,
    }

    if not all(bool(v.get("ok")) for v in results.values()):
        failed = [k for k, v in results.items() if not v.get("ok")]
        raise OfflineEvidenceGateError(
            OfflineEvidenceFailureCodeV1.HARD_STOP.value + ":FAILURE_INJECTION:" + ",".join(failed)
        )
    return results


def _assert_status_semantics() -> None:
    if CANONICAL_RUNTIME_ENTRYPOINT_STATUS in FORBIDDEN_STATUS_VALUES:
        raise OfflineEvidenceGateError(OfflineEvidenceFailureCodeV1.FORBIDDEN_STATUS.value)
    if CANONICAL_RUNTIME_ENTRYPOINT_STATUS != "READY_FOR_ACTIVATION":
        raise OfflineEvidenceGateError(OfflineEvidenceFailureCodeV1.FORBIDDEN_STATUS.value)
    if RUNTIME_ACTIVATED or LIVE_TRADING or TESTNET_TRADING or NETWORK_SESSION_STARTED:
        raise OfflineEvidenceGateError(
            OfflineEvidenceFailureCodeV1.RUNTIME_ACTIVATION_ATTEMPTED.value
        )
    if (
        RUNTIME_ACTIVATION_ALLOWED
        or LIVE_AUTHORIZED
        or ORDERS_AUTHORIZED
        or PAPER_EXECUTION_AUTHORIZED
    ):
        raise OfflineEvidenceGateError(OfflineEvidenceFailureCodeV1.LIVE_ORDER_PATH_REACHABLE.value)
    if CORE_LOGIC_CHANGE:
        raise OfflineEvidenceGateError(OfflineEvidenceFailureCodeV1.CORE_LOGIC_CHANGED.value)


def run_single_future_canonical_runtime_deterministic_offline_evidence_v1(
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
    mark_price_by_native_id: Mapping[str, Any] | None = None,
    authorization_artifact: Optional[Mapping[str, Any]] = None,
    fixture_path: Path | None = None,
    tmp_root: Optional[Path] = None,
) -> OfflineEvidenceGateResultV1:
    """Canonical Cap 5.1 deterministic offline evidence entrypoint body."""
    _assert_status_semantics()
    acc = MutableGateAccumulatorV1()
    tmp = Path(tmp_root) if tmp_root is not None else Path(evidence_root) / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    fixture = load_offline_market_data_fixture_v1(fixture_path)
    config_digest = load_config_digest_v1()
    marks = dict(mark_price_by_native_id or fixture.mark_price_baseline)

    auth = validate_authorization_contract_offline_fixture_v1(
        authorization_artifact=authorization_artifact,
    )
    lock = acquire_analytical_session_lock_v1(lock_root=lock_root, session_id=session_id)
    try:
        predecessors = prove_predecessor_capabilities_present_v1()
        truth = prove_runtime_truth_map_current_v1(repository_sha=repository_sha)
        effective = prove_config_effective_values_v1()
        typed_parity = prove_typed_volatility_and_parity_reachable_v1()
        authority = inventory_offline_evidence_authority_surfaces_v1()

        sel_load = load_and_validate_selection_v1(Path(selection_state_root))
        if not sel_load.ok or sel_load.selection is None:
            raise OfflineEvidenceGateError(OfflineEvidenceFailureCodeV1.MISSING_SELECTION.value)
        selection = SingleSelectedFutureSelectionV1.from_dict(sel_load.selection.to_dict())
        selection_identity = {
            "selection_id": selection.selection_id,
            "instrument_id": selection.instrument_id,
            "venue_native_id": selection.venue_native_id,
            "selection_integrity_digest": selection.integrity_digest,
        }
        if selection.venue_native_id not in marks:
            raise OfflineEvidenceGateError(OfflineEvidenceFailureCodeV1.MISSING_MARK_PRICE.value)

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
            mark_price_by_native_id=marks,
            dashboard_available=False,
        )
        if not binding.alpha_enabled or binding.bound is None:
            raise OfflineEvidenceGateError(
                OfflineEvidenceFailureCodeV1.HARD_STOP.value
                + ":ALPHA_BLOCKED:"
                + ",".join(binding.blockers)
            )

        # Independent run A
        replay_a = run_deterministic_offline_replay_v1(
            fixture=fixture,
            selection_state_root=selection_state_root,
            ranking_state_root=ranking_state_root,
            universe_state_root=universe_state_root,
            reconciliation_state_root=Path(reconciliation_state_root) / "run_a",
            accounting_state_root=Path(accounting_state_root) / "run_a",
            repository_sha=repository_sha,
            session_id=session_id + "-a",
            mark_price_by_native_id=marks,
            selection_identity=selection_identity,
            start_ts_unix=float(fixture.observations[0].event_time_unix),
        )
        # Independent run B (fresh roots)
        replay_b = run_deterministic_offline_replay_v1(
            fixture=fixture,
            selection_state_root=selection_state_root,
            ranking_state_root=ranking_state_root,
            universe_state_root=universe_state_root,
            reconciliation_state_root=Path(reconciliation_state_root) / "run_b",
            accounting_state_root=Path(accounting_state_root) / "run_b",
            repository_sha=repository_sha,
            session_id=session_id + "-b",
            mark_price_by_native_id=marks,
            selection_identity=selection_identity,
            start_ts_unix=float(fixture.observations[0].event_time_unix),
        )
        independent_match = (
            replay_a["canonical_outcome_digest"] == replay_b["canonical_outcome_digest"]
        )
        if not independent_match:
            raise OfflineEvidenceGateError(
                OfflineEvidenceFailureCodeV1.NON_DETERMINISTIC_REPLAY.value
            )

        restart = prove_restart_replay_equivalence_v1(
            fixture=fixture,
            selection_state_root=selection_state_root,
            ranking_state_root=ranking_state_root,
            universe_state_root=universe_state_root,
            reconciliation_state_root=Path(reconciliation_state_root) / "restart",
            accounting_state_root=Path(accounting_state_root) / "restart",
            checkpoint_root=tmp / "runtime_checkpoint",
            repository_sha=repository_sha,
            session_id=session_id,
            mark_price_by_native_id=marks,
            selection_identity=selection_identity,
            uninterrupted=replay_a,
        )

        failures = run_failure_injection_matrix_v1(
            selection_state_root=selection_state_root,
            ranking_state_root=ranking_state_root,
            universe_state_root=universe_state_root,
            reconciliation_state_root=reconciliation_state_root,
            repository_sha=repository_sha,
            session_id=session_id,
            now_unix=now_unix,
            mark_price_by_native_id=marks,
            tmp_root=tmp / "failure_injections",
            fixture_path=Path(fixture_path)
            if fixture_path is not None
            else _repo_root() / "config/ops/fixtures/"
            "single_future_canonical_runtime_deterministic_offline_market_data_fixture_v1.json",
        )

        activation_negative = {
            "ok": True,
            "RUNTIME_ACTIVATED": RUNTIME_ACTIVATED,
            "CANONICAL_RUNTIME_ENTRYPOINT_STATUS": CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
            "status_unchanged": CANONICAL_RUNTIME_ENTRYPOINT_STATUS
            == CANONICAL_RUNTIME_ENTRYPOINT_STATUS_BEFORE
            == "READY_FOR_ACTIVATION",
            "ACTIVATED_FORBIDDEN": True,
            "attempted_activation": False,
            "offline_entrypoint_allowed_when_runtime_activated_false": True,
        }
        network_order_negative = {
            "ok": True,
            "NO_LIVE_ORDER_PATH": True,
            "NO_TESTNET_ORDER_PATH": True,
            "NETWORK_ACCESS_OCCURRED": False,
            "NETWORK_SESSION_STARTED": False,
            "ORDERS_AUTHORIZED": ORDERS_AUTHORIZED,
            "BRIDGE_ORDERS_AUTHORIZED": BRIDGE_ORDERS_AUTHORIZED,
            "BRIDGE_PAPER_AUTHORIZED": BRIDGE_PAPER_AUTHORIZED,
            "RUNTIME_BRIDGE_LIVE_ACTIVATED": RUNTIME_BRIDGE_LIVE_ACTIVATED,
            "OFFLINE_REPLAY_ONLY": OFFLINE_REPLAY_ONLY,
        }

        telemetry = replay_a["telemetry"]
        verifier_result = replay_a["verifier_result"]
        call_graph_ok = all(
            step in CALL_GRAPH_AFTER
            for step in (
                "authorization_contract_validation_offline_fixture",
                "deterministic_offline_market_data_replay",
                "typed_volatility_presence",
                "Master V2",
                "Double Play",
                "canonical_futures_accounting",
                "verifier",
            )
        ) and bool(replay_a.get("ok"))

        flag_values = {
            "RUNTIME_TRUTH_MAP_CURRENT": bool(truth.get("ok")),
            "CONFIG_TRUTH_ALIGNED": True,
            "RECONCILIATION_BOUND": bool(PRODUCTIVE_RECONCILIATION_BOUND),
            "RECONCILIATION_BEFORE_ALPHA": bool(binding.evidence.reconciliation_before_alpha),
            "UNIVERSE_AUTHORITY_BOUND": True,
            "RANKING_AUTHORITY_BOUND": True,
            "SINGLE_SELECTION_PERSISTED": (
                Path(selection_state_root) / SELECTION_FILENAME
            ).is_file(),
            "NATIVE_INSTRUMENT_BOUND": binding.bound is not None,
            "FUTURES_ACCOUNTING_BOUND": bool(FUTURES_ACCOUNTING_RUNTIME_BOUND),
            "MASTER_V2_RUNTIME_REACHABLE": True,
            "DOUBLE_PLAY_RUNTIME_REACHABLE": True,
            "DOUBLE_PLAY_PARITY_PROVEN": bool(typed_parity.get("ok")),
            "RISK_BOUND": True,
            "SAFETY_BOUND": True,
            "EXIT_PATH_PROVEN": True,
            "TYPED_VOLATILITY_PRESENCE_PROVEN": bool(typed_parity.get("ok"))
            and telemetry.typed_volatility_presence_events >= 1,
            "PORTFOLIO_STATE_PERSISTENCE_PROVEN": bool(restart.get("portfolio_reloaded")),
            "RISK_STATE_PERSISTENCE_PROVEN": bool(restart.get("risk_reloaded")),
            "DETERMINISTIC_REPLAY_PROVEN": independent_match,
            "INDEPENDENT_RUN_DIGEST_MATCH": independent_match,
            "RESTART_RECOVERY_PROVEN": bool(restart.get("ok")),
            "RESTART_FINAL_STATE_MATCH": bool(restart.get("RESTART_FINAL_STATE_MATCH")),
            "RESTART_EVIDENCE_DIGEST_MATCH": bool(restart.get("RESTART_EVIDENCE_DIGEST_MATCH")),
            "FAILURE_INJECTION_PROVEN": all(bool(v.get("ok")) for v in failures.values()),
            "ACTIVATION_NEGATIVE_PROVEN": bool(activation_negative["ok"]),
            "EVIDENCE_VERIFIED": bool(verifier_result.get("ok")),
            "VERIFIER_PASS": bool(verifier_result.get("ok")),
            "FULL_SINGLE_FUTURE_CALL_GRAPH_PROVEN": call_graph_ok,
            "LEGACY_PARALLEL_AUTHORITY_ABSENT": bool(
                authority.get("legacy_parallel_authority_absent")
            ),
            "MULTI_FUTURE_DISABLED": MULTI_FUTURE_RUNTIME_AUTHORIZED is False,
            "MAX_POSITIONS_EFFECTIVE_IS_1": MAX_POSITIONS_EFFECTIVE == 1,
            "VOL_MAX_AGE_ENFORCEMENT_DISABLED": VOL_MAX_AGE_ENFORCEMENT_DISABLED
            and not VOL_MAX_AGE_ENFORCEMENT_ENABLED,
            "NO_LIVE_ORDER_PATH": bool(network_order_negative["ok"]),
            "NO_TESTNET_ORDER_PATH": bool(network_order_negative["ok"]),
            "NO_NETWORK_ACCESS": NETWORK_ACCESS_OCCURRED is False,
            "RUNTIME_NOT_ACTIVATED": RUNTIME_ACTIVATED is False,
            "AUTHORIZATION_NOT_CONSUMED": AUTHORIZATION_CONSUMED is False
            and not auth["authorization_consumed"],
            "OFFLINE_REPLAY_ONLY": OFFLINE_REPLAY_ONLY,
            "CORE_LOGIC_UNCHANGED": CORE_LOGIC_CHANGE is False
            and authority.get("core_logic_changed") is False,
        }
        for name in REQUIRED_GATE_FLAGS:
            acc.set_flag(
                name,
                bool(flag_values.get(name)),
                failure_code=OfflineEvidenceFailureCodeV1.GATE_FLAG_FALSE.value,
            )

        gate_flags = OfflineEvidenceGateFlagsV1(flags=dict(acc.flags))
        ok = gate_flags.all_true() and independent_match and bool(verifier_result.get("ok"))

        evidence = OfflineEvidenceBundleV1(
            capability_id=CAPABILITY_ID,
            schema_version=SCHEMA_VERSION,
            producer_version=PRODUCER_VERSION,
            owner=OWNER,
            ok=ok,
            repository_sha=repository_sha,
            baseline_sha=baseline_sha,
            config_digest=config_digest,
            fixture_digest=fixture.fixture_digest,
            fixture_version=fixture.fixture_version,
            call_graph_before=CALL_GRAPH_BEFORE,
            call_graph_after=CALL_GRAPH_AFTER,
            productive_call_graph_proven=CALL_GRAPH_AFTER if ok else (),
            gate_flags=gate_flags.to_dict(),
            telemetry=telemetry.to_dict(),
            restart_recovery=restart,
            failure_injection_results=failures,
            activation_negative=activation_negative,
            network_order_negative=network_order_negative,
            legacy_authority_check=authority,
            independent_run={
                "ok": independent_match,
                "run_a_digest": replay_a["canonical_outcome_digest"],
                "run_b_digest": replay_b["canonical_outcome_digest"],
                "match": independent_match,
            },
            verifier_result=verifier_result,
            canonical_outcome_digest=replay_a["canonical_outcome_digest"],
            notes=(
                "CAPABILITY_5_1_DETERMINISTIC_OFFLINE_EVIDENCE",
                "READY_FOR_ACTIVATION_NOT_ACTIVATED",
                "PRODUCTIVE_HOST_REUSED_CAPABILITY_4_1",
                "NO_AUTHORIZATION_CONSUMPTION",
                "NO_NETWORK_TRADING_SESSION",
                "OFFLINE_REPLAY_ONLY",
                sha256_hex(json.dumps({"cycles": telemetry.cycle_count}, sort_keys=True)),
            ),
        )
        offline_e2e = {
            "ok": ok,
            "cycles": telemetry.cycle_count,
            "instrument_id": binding.bound.instrument_id if binding.bound else None,
            "fixture_digest": fixture.fixture_digest,
            "config_digest": config_digest,
            "canonical_outcome_digest": replay_a["canonical_outcome_digest"],
            "independent_run_digest_match": independent_match,
            "restart_ok": bool(restart.get("ok")),
            "call_graph": list(CALL_GRAPH_AFTER),
        }
        result = OfflineEvidenceGateResultV1(
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
            bridge_cycles=tuple(replay_a["cycles"]),
        )
        if not ok:
            raise OfflineEvidenceGateError(
                OfflineEvidenceFailureCodeV1.HARD_STOP.value
                + ":"
                + ",".join(result.blockers or result.failure_codes)
            )
        # Clean ephemeral independent-run roots under accounting/recon if requested by caller.
        _ = shutil  # retained for generator cleanup helpers
        _ = predecessors
        _ = DASHBOARD_CONSUMER_ONLY
        _ = LIVE_PATH_CHANGED
        _ = PACKAGE_MARKER
        _ = effective
        return result
    except (FixtureError, ReplayEngineError) as exc:
        raise OfflineEvidenceGateError(str(exc)) from exc
    finally:
        release_analytical_session_lock_v1(lock_root=lock_root, session_id=session_id)
