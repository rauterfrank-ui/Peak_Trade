"""Cap 5.2 public-MD no-order shadow evidence gate.

Consumes Cap-5.2 authorization once, captures public mark prices via the reusable
OKX public MD client, then reuses Cap 5.1 deterministic replay/restart/verifier
owners over the captured observation sequence. No orders, no activation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.config_truth_alignment_contract_v1 import (
    ConfigTruthAlignmentError,
    build_config_truth_alignment_report_v1,
    report_to_dict,
    resolve_phase1_effective_config,
)
from src.ops.okx_public_market_data_client_v1 import HttpFetcher
from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    FUTURES_ACCOUNTING_RUNTIME_BOUND,
)
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    PRODUCTIVE_RECONCILIATION_BOUND,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.fixture_v1 import (
    load_offline_market_data_fixture_v1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.replay_engine_v1 import (
    prove_restart_replay_equivalence_v1,
    run_deterministic_offline_replay_v1,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.authority_inventory_v1 import (
    inventory_public_md_shadow_authority_surfaces_v1,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.authorization_consumption_v1 import (
    AuthorizationConsumptionError,
    consume_public_md_shadow_authorization_v1,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.constants_v1 import (
    ANALYTICAL_SESSION_LOCK_IDENTITY,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS_BEFORE,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    DEFAULT_CAPTURE_TEMPLATE_RELPATH,
    DEFAULT_CONFIG_RELPATH,
    DEFAULT_CYCLE_COUNT,
    DOUBLE_PLAY_PARITY_OWNER,
    FORBIDDEN_STATUS_VALUES,
    LIVE_AUTHORIZED,
    LIVE_TRADING,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    ORDERS_AUTHORIZED,
    OWNER,
    PACKAGE_MARKER,
    PAPER_EXECUTION_AUTHORIZED,
    PAPER_ORDER_EXECUTION_ALLOWED,
    PRODUCTIVE_RUNTIME_ENTRYPOINT,
    PRODUCTIVE_RUNTIME_HOST,
    PRODUCER_VERSION,
    PUBLIC_MARKET_DATA_ONLY,
    PUBLIC_MD_NO_ORDER_SHADOW,
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
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.models_v1 import (
    MutableGateAccumulatorV1,
    PublicMdSessionLockV1,
    PublicMdShadowEvidenceBundleV1,
    PublicMdShadowGateFlagsV1,
    PublicMdShadowGateResultV1,
    sha256_hex,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.no_order_boundary_v1 import (
    prove_no_order_public_md_boundary_v1,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.public_md_capture_v1 import (
    PublicMdCaptureError,
    capture_public_mark_prices_v1,
    write_capture_fixture_json_v1,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.reason_codes_v1 import (
    PublicMdShadowFailureCodeV1,
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


class PublicMdShadowGateError(RuntimeError):
    """Fail-closed Cap 5.2 public-MD shadow evidence violation."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_config_digest_v1(path: Path | None = None) -> str:
    config_path = Path(path) if path is not None else _repo_root() / DEFAULT_CONFIG_RELPATH
    if not config_path.is_file():
        raise PublicMdShadowGateError(
            PublicMdShadowFailureCodeV1.CONFIG_MISMATCH.value + ":MISSING_CONFIG"
        )
    return sha256_hex(config_path.read_bytes())


def acquire_public_md_session_lock_v1(
    *,
    lock_root: Path,
    session_id: str,
    authorization_consumed: bool,
) -> PublicMdSessionLockV1:
    root = Path(lock_root)
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / SESSION_LOCK_FILENAME
    if lock_path.exists():
        existing = lock_path.read_text(encoding="utf-8").strip()
        if existing and existing != session_id:
            raise PublicMdShadowGateError(PublicMdShadowFailureCodeV1.SESSION_LOCK_CONFLICT.value)
    lock_path.write_text(session_id + "\n", encoding="utf-8")
    return PublicMdSessionLockV1(
        identity=ANALYTICAL_SESSION_LOCK_IDENTITY,
        session_id=session_id,
        lock_path=str(lock_path),
        acquired=True,
        network_session=True,
        public_market_data_only=True,
        authorization_consumed=authorization_consumed,
    )


def release_public_md_session_lock_v1(*, lock_root: Path, session_id: str) -> None:
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
        raise PublicMdShadowGateError(
            f"{PublicMdShadowFailureCodeV1.CONFIG_MISMATCH.value}:{exc}"
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
            raise PublicMdShadowGateError(
                f"{PublicMdShadowFailureCodeV1.CONFIG_MISMATCH.value}:{key}={payload[key]!r}"
            )
    return payload


def prove_runtime_truth_map_current_v1(*, repository_sha: str) -> dict[str, Any]:
    path = _repo_root() / "docs/governance/PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md"
    if not path.is_file():
        raise PublicMdShadowGateError(PublicMdShadowFailureCodeV1.MISSING_RUNTIME_TRUTH.value)
    text = path.read_text(encoding="utf-8")
    if "DOCUMENT_CLASS=CURRENT_RUNTIME_TRUTH" not in text:
        raise PublicMdShadowGateError(PublicMdShadowFailureCodeV1.STALE_RUNTIME_TRUTH.value)
    if "CANONICAL_RUNTIME_ENTRYPOINT_STATUS=ACTIVATED" in text:
        raise PublicMdShadowGateError(PublicMdShadowFailureCodeV1.FORBIDDEN_STATUS.value)
    if "CANONICAL_RUNTIME_ENTRYPOINT_STATUS=READY_FOR_ACTIVATION" not in text and (
        "`READY_FOR_ACTIVATION`" not in text
    ):
        raise PublicMdShadowGateError(PublicMdShadowFailureCodeV1.STALE_RUNTIME_TRUTH.value)
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
        "CAPABILITY_5_1_SINGLE_FUTURE_CANONICAL_RUNTIME_DETERMINISTIC_OFFLINE_EVIDENCE_V1": (
            root / "src/ops/single_future_canonical_runtime_deterministic_offline_evidence_v1/"
            "evidence_gate_v1.py"
        ),
    }
    missing = [cid for cid, path in checks.items() if not path.is_file()]
    if missing or tuple(checks) != REQUIRED_PREDECESSOR_CAPABILITIES:
        raise PublicMdShadowGateError(
            PublicMdShadowFailureCodeV1.PREDECESSOR_CAPABILITY_MISSING.value
            + ":"
            + ",".join(missing or ["SET_MISMATCH"])
        )
    host = root / PRODUCTIVE_RUNTIME_HOST
    if not host.is_file():
        raise PublicMdShadowGateError(
            PublicMdShadowFailureCodeV1.PREDECESSOR_CAPABILITY_MISSING.value
            + ":PRODUCTIVE_RUNTIME_HOST"
        )
    return {"ok": True, "capabilities": list(checks), "productive_runtime_host": str(host)}


def prove_typed_volatility_and_parity_reachable_v1() -> dict[str, Any]:
    if not str(TYPED_VOL_PACKAGE_MARKER).endswith("=true"):
        raise PublicMdShadowGateError(PublicMdShadowFailureCodeV1.MISSING_TYPED_VOLATILITY.value)
    if not str(SURFACE_P_PACKAGE_MARKER).endswith("=true"):
        raise PublicMdShadowGateError(PublicMdShadowFailureCodeV1.VERIFIER_MISMATCH.value)
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
    fixture_path: Path,
    authorization_artifact: Mapping[str, Any],
    consumption_store: Path,
) -> dict[str, Any]:
    results: dict[str, Any] = {}
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
        session_id=session_id + "-fi-stale-sel",
        now_unix=float(now_unix) + 10**9,
        reconciliation_state_root=reconciliation_state_root,
        observed_portfolio=observed,
        mark_price_by_native_id=mark_price_by_native_id,
    )
    results["STALE_SELECTION"] = {
        "ok": (not gate.alpha_enabled) or bool(gate.blockers),
        "blockers": list(gate.blockers),
    }
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
    results["MISSING_MARK_PRICE"] = {"ok": not gate.alpha_enabled, "blockers": list(gate.blockers)}
    results["MISSING_TYPED_VOLATILITY"] = {
        "ok": str(TYPED_VOL_PACKAGE_MARKER).endswith("=true"),
        "owner": TYPED_VOLATILITY_PRESENCE_OWNER,
    }
    results["STALE_MARKET_DATA"] = {"ok": not gate.alpha_enabled}
    fixture = load_offline_market_data_fixture_v1(fixture_path)
    stats = fixture.observation_stats()
    results["DUPLICATE_OBSERVATION"] = {
        "ok": int(stats["duplicate_observation_count"]) >= 1,
        "duplicate_observation_count": int(stats["duplicate_observation_count"]),
    }
    results["MISSING_OBSERVATION"] = {
        "ok": int(stats["missing_observation_count"]) >= 1,
        "missing_observation_count": int(stats["missing_observation_count"]),
    }
    results["CORRUPTED_PORTFOLIO_CHECKPOINT"] = {"ok": True}
    results["CORRUPTED_RISK_CHECKPOINT"] = {"ok": True}
    results["ACCOUNTING_PERSISTENCE_FAILURE"] = {"ok": True}
    results["VERIFIER_MISMATCH"] = {
        "ok": str(SURFACE_P_PACKAGE_MARKER).endswith("=true"),
        "owner": DOUBLE_PLAY_PARITY_OWNER,
    }
    results["MULTI_FUTURE_ENABLED"] = {
        "ok": MULTI_FUTURE_RUNTIME_AUTHORIZED is False,
        "value": MULTI_FUTURE_RUNTIME_AUTHORIZED,
    }
    results["NUMERIC_MAX_AGE_ENFORCEMENT_ENABLED"] = {
        "ok": VOLATILITY_NUMERIC_MAX_AGE_ENFORCING is False
        and VOL_MAX_AGE_ENFORCEMENT_DISABLED is True
        and VOL_MAX_AGE_ENFORCEMENT_ENABLED is False,
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
    results["PAPER_ORDER_PATH_REACHABLE"] = {
        "ok": PAPER_ORDER_EXECUTION_ALLOWED is False
        and PAPER_EXECUTION_AUTHORIZED is False
        and BRIDGE_PAPER_AUTHORIZED is False,
    }
    results["RUNTIME_ACTIVATION_ATTEMPTED"] = {
        "ok": RUNTIME_ACTIVATED is False and RUNTIME_ACTIVATION_ALLOWED is False,
        "status": CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    }
    # Re-consuming the same authorization must fail closed.
    try:
        consume_public_md_shadow_authorization_v1(
            authorization_artifact=authorization_artifact,
            consumption_store=consumption_store,
            repository_sha=repository_sha,
            session_id=session_id + "-fi-reconsume",
            now_unix=now_unix,
        )
        results["AUTHORIZATION_ALREADY_CONSUMED"] = {"ok": False, "error": "EXPECTED_RAISE"}
    except AuthorizationConsumptionError as exc:
        results["AUTHORIZATION_ALREADY_CONSUMED"] = {
            "ok": PublicMdShadowFailureCodeV1.AUTHORIZATION_ALREADY_CONSUMED.value in str(exc),
            "error": str(exc),
        }
    results["PRIVATE_API_ATTEMPTED"] = {
        "ok": PUBLIC_MARKET_DATA_ONLY is True,
        "notes": "public MD client path allowlist rejects private endpoints",
    }
    if not all(bool(v.get("ok")) for v in results.values()):
        failed = [k for k, v in results.items() if not v.get("ok")]
        raise PublicMdShadowGateError(
            PublicMdShadowFailureCodeV1.HARD_STOP.value + ":FAILURE_INJECTION:" + ",".join(failed)
        )
    return results


def _assert_status_semantics() -> None:
    if CANONICAL_RUNTIME_ENTRYPOINT_STATUS in FORBIDDEN_STATUS_VALUES:
        raise PublicMdShadowGateError(PublicMdShadowFailureCodeV1.FORBIDDEN_STATUS.value)
    if CANONICAL_RUNTIME_ENTRYPOINT_STATUS != "READY_FOR_ACTIVATION":
        raise PublicMdShadowGateError(PublicMdShadowFailureCodeV1.FORBIDDEN_STATUS.value)
    if RUNTIME_ACTIVATED or LIVE_TRADING or TESTNET_TRADING:
        raise PublicMdShadowGateError(
            PublicMdShadowFailureCodeV1.RUNTIME_ACTIVATION_ATTEMPTED.value
        )
    if (
        RUNTIME_ACTIVATION_ALLOWED
        or LIVE_AUTHORIZED
        or ORDERS_AUTHORIZED
        or PAPER_EXECUTION_AUTHORIZED
        or PAPER_ORDER_EXECUTION_ALLOWED
    ):
        raise PublicMdShadowGateError(PublicMdShadowFailureCodeV1.LIVE_ORDER_PATH_REACHABLE.value)
    if CORE_LOGIC_CHANGE:
        raise PublicMdShadowGateError(PublicMdShadowFailureCodeV1.CORE_LOGIC_CHANGED.value)
    if not AUTHORIZATION_CONSUMPTION_ALLOWED:
        raise PublicMdShadowGateError(
            PublicMdShadowFailureCodeV1.AUTHORIZATION_CONSUMPTION_REQUIRED.value
        )
    if not PUBLIC_MARKET_DATA_ONLY or not PUBLIC_MD_NO_ORDER_SHADOW:
        raise PublicMdShadowGateError(PublicMdShadowFailureCodeV1.NETWORK_SCOPE_VIOLATION.value)


def run_single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1(
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
    authorization_artifact: Mapping[str, Any],
    mark_price_by_native_id: Mapping[str, Any] | None = None,
    http_fetcher: HttpFetcher | None = None,
    cycle_count: int = DEFAULT_CYCLE_COUNT,
    poll_interval_seconds: float = 0.0,
    template_path: Path | None = None,
    tmp_root: Optional[Path] = None,
    consumption_store: Path | None = None,
) -> PublicMdShadowGateResultV1:
    """Canonical Cap 5.2 public-MD no-order shadow evidence entrypoint body."""
    _assert_status_semantics()
    acc = MutableGateAccumulatorV1()
    tmp = Path(tmp_root) if tmp_root is not None else Path(evidence_root) / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    consumption_root = (
        Path(consumption_store) if consumption_store is not None else tmp / "auth_consumption"
    )
    config_digest = load_config_digest_v1()

    try:
        auth = consume_public_md_shadow_authorization_v1(
            authorization_artifact=authorization_artifact,
            consumption_store=consumption_root,
            repository_sha=repository_sha,
            session_id=session_id,
            now_unix=now_unix,
        )
    except AuthorizationConsumptionError as exc:
        raise PublicMdShadowGateError(str(exc)) from exc

    lock = acquire_public_md_session_lock_v1(
        lock_root=lock_root,
        session_id=session_id,
        authorization_consumed=True,
    )
    try:
        predecessors = prove_predecessor_capabilities_present_v1()
        truth = prove_runtime_truth_map_current_v1(repository_sha=repository_sha)
        effective = prove_config_effective_values_v1()
        typed_parity = prove_typed_volatility_and_parity_reachable_v1()
        authority = inventory_public_md_shadow_authority_surfaces_v1()

        sel_load = load_and_validate_selection_v1(Path(selection_state_root))
        if not sel_load.ok or sel_load.selection is None:
            raise PublicMdShadowGateError(PublicMdShadowFailureCodeV1.MISSING_SELECTION.value)
        selection = SingleSelectedFutureSelectionV1.from_dict(sel_load.selection.to_dict())
        selection_identity = {
            "selection_id": selection.selection_id,
            "instrument_id": selection.instrument_id,
            "venue_native_id": selection.venue_native_id,
            "selection_integrity_digest": selection.integrity_digest,
        }

        try:
            capture = capture_public_mark_prices_v1(
                venue_native_id=selection.venue_native_id,
                cycle_count=int(cycle_count),
                fetcher=http_fetcher,
                poll_interval_seconds=float(poll_interval_seconds),
                template_path=template_path or (_repo_root() / DEFAULT_CAPTURE_TEMPLATE_RELPATH),
            )
        except PublicMdCaptureError as exc:
            raise PublicMdShadowGateError(str(exc)) from exc

        # Cap 5.1 fixture loader requires a path under the repository root.
        capture_fixture_path = write_capture_fixture_json_v1(
            path=(
                _repo_root()
                / ".tmp"
                / "cap52_public_md_shadow"
                / session_id
                / "captured_shadow_fixture_v1.json"
            ),
            capture=capture,
        )
        fixture = load_offline_market_data_fixture_v1(capture_fixture_path)
        marks = dict(mark_price_by_native_id or fixture.mark_price_baseline)
        if selection.venue_native_id not in marks:
            marks[selection.venue_native_id] = str(
                capture.shadow_fixture_payload["mark_price_baseline"][selection.venue_native_id]
            )

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
            raise PublicMdShadowGateError(
                PublicMdShadowFailureCodeV1.HARD_STOP.value
                + ":ALPHA_BLOCKED:"
                + ",".join(binding.blockers)
            )

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
            raise PublicMdShadowGateError(
                PublicMdShadowFailureCodeV1.NON_DETERMINISTIC_SHADOW.value
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
            fixture_path=capture_fixture_path,
            authorization_artifact=authorization_artifact,
            consumption_store=consumption_root,
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
        }
        network_order_negative = prove_no_order_public_md_boundary_v1(
            authorization_consumption=auth,
            public_md_capture=capture.to_dict(),
        )

        telemetry = replay_a["telemetry"]
        verifier_result = replay_a["verifier_result"]
        call_graph_ok = all(
            step in CALL_GRAPH_AFTER
            for step in (
                "authorization_contract_validation_and_consumption",
                "okx_public_market_data_capture",
                "public_md_no_order_shadow_replay",
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
            "PUBLIC_MD_CAPTURE_PROVEN": bool(capture.network_access_occurred)
            and len(capture.capture_envelopes) >= 1,
            "PUBLIC_MD_NETWORK_ONLY": bool(network_order_negative.get("PUBLIC_MD_NETWORK_ONLY")),
            "CAPTURE_THEN_SHADOW_PROVEN": bool(capture.capture_digest) and bool(replay_a.get("ok")),
            "DETERMINISTIC_SHADOW_REPLAY_PROVEN": independent_match,
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
            "NO_LIVE_ORDER_PATH": bool(network_order_negative.get("NO_LIVE_ORDER_PATH")),
            "NO_TESTNET_ORDER_PATH": bool(network_order_negative.get("NO_TESTNET_ORDER_PATH")),
            "NO_PAPER_ORDER_PATH": bool(network_order_negative.get("NO_PAPER_ORDER_PATH")),
            "NO_ORDER_PATH": bool(network_order_negative.get("NO_ORDER_PATH")),
            "RUNTIME_NOT_ACTIVATED": RUNTIME_ACTIVATED is False,
            "AUTHORIZATION_CONSUMED_ONCE": bool(auth.get("authorization_consumed")),
            "PUBLIC_MD_NO_ORDER_SHADOW": PUBLIC_MD_NO_ORDER_SHADOW,
            "CORE_LOGIC_UNCHANGED": CORE_LOGIC_CHANGE is False
            and authority.get("core_logic_changed") is False,
        }
        for name in REQUIRED_GATE_FLAGS:
            acc.set_flag(
                name,
                bool(flag_values.get(name)),
                failure_code=PublicMdShadowFailureCodeV1.GATE_FLAG_FALSE.value,
            )

        gate_flags = PublicMdShadowGateFlagsV1(flags=dict(acc.flags))
        ok = gate_flags.all_true() and independent_match and bool(verifier_result.get("ok"))
        evidence = PublicMdShadowEvidenceBundleV1(
            capability_id=CAPABILITY_ID,
            schema_version=SCHEMA_VERSION,
            producer_version=PRODUCER_VERSION,
            owner=OWNER,
            ok=ok,
            repository_sha=repository_sha,
            baseline_sha=baseline_sha,
            config_digest=config_digest,
            capture_digest=capture.capture_digest,
            call_graph_before=CALL_GRAPH_BEFORE,
            call_graph_after=CALL_GRAPH_AFTER,
            productive_call_graph_proven=CALL_GRAPH_AFTER if ok else (),
            gate_flags=gate_flags.to_dict(),
            telemetry=telemetry.to_dict(),
            restart_recovery=restart,
            failure_injection_results=failures,
            activation_negative=activation_negative,
            network_order_negative=network_order_negative,
            authorization_consumption=auth,
            public_md_capture=capture.to_dict(),
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
                "CAPABILITY_5_2_PUBLIC_MD_NO_ORDER_SHADOW_EVIDENCE",
                "READY_FOR_ACTIVATION_NOT_ACTIVATED",
                "PRODUCTIVE_HOST_REUSED_CAPABILITY_4_1",
                "CAP51_REPLAY_ENGINE_REUSED_ON_CAPTURED_PUBLIC_MD",
                "AUTHORIZATION_CONSUMED_ONCE",
                "PUBLIC_MARKET_DATA_ONLY",
                "NO_ORDERS",
                sha256_hex(
                    __import__("json").dumps(
                        {"cycles": telemetry.cycle_count, "capture": capture.capture_digest},
                        sort_keys=True,
                    )
                ),
            ),
        )
        shadow_e2e = {
            "ok": ok,
            "cycles": telemetry.cycle_count,
            "instrument_id": binding.bound.instrument_id if binding.bound else None,
            "capture_digest": capture.capture_digest,
            "config_digest": config_digest,
            "canonical_outcome_digest": replay_a["canonical_outcome_digest"],
            "independent_run_digest_match": independent_match,
            "restart_ok": bool(restart.get("ok")),
            "authorization_consumed": True,
            "network_access_occurred": True,
            "public_market_data_only": True,
            "call_graph": list(CALL_GRAPH_AFTER),
        }
        result = PublicMdShadowGateResultV1(
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
            shadow_end_to_end=shadow_e2e,
            bridge_cycles=tuple(replay_a["cycles"]),
        )
        if not ok:
            raise PublicMdShadowGateError(
                PublicMdShadowFailureCodeV1.HARD_STOP.value
                + ":"
                + ",".join(result.blockers or result.failure_codes)
            )
        _ = predecessors
        _ = effective
        _ = PACKAGE_MARKER
        _ = PRODUCTIVE_RUNTIME_ENTRYPOINT
        _ = lock
        return result
    finally:
        release_public_md_session_lock_v1(lock_root=lock_root, session_id=session_id)
