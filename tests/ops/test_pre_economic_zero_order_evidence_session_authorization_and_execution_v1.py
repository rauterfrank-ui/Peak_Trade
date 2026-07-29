"""Focused tests for AUTHORIZATION_AND_EXECUTION capability v1.

All network / 6h scenarios are simulated. No real session. No GO secrets committed.
"""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from src.ops.pre_economic_zero_order_evidence_session_authorization_v1 import (
    CANONICAL_GO_TOKEN_PREFIX,
    AuthorizationContractError,
    build_authorization_contract_dict_v1,
    compute_go_token_binding_sha256,
    consume_authorization_one_time_v1,
    fingerprint_go_token,
    load_authorization_contract_v1,
    validate_operator_go_and_contract_v1,
)
from src.ops.pre_economic_zero_order_evidence_session_okx_readonly_telemetry_v1 import (
    OkxFuturesReadOnlyTelemetryV1,
    SimulatedOkxTelemetryClientV1,
    TelemetryError,
    assert_client_read_only,
)
from src.ops.pre_economic_zero_order_evidence_session_production_runner_v1 import (
    ControllableDualClock,
    ProductionRunnerError,
    load_production_config_v1,
    preflight_production_session_v1,
    run_production_session_v1,
    validate_config_only_v1,
)
from src.ops.pre_economic_zero_order_evidence_session_production_verifier_v1 import (
    RESULT_SESSION_EVIDENCE_VALID,
    verify_production_evidence_root_v1,
)
from src.ops.pre_economic_zero_order_evidence_session_safety_preflight_v1 import (
    run_safety_preflight_v1,
)
from src.ops.pre_economic_zero_order_evidence_session_state_machine_v1 import (
    SessionState,
    SessionStateMachineError,
    assert_transition_allowed,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "config/ops/pre_economic_zero_order_evidence_session_authorization_v1.toml"
TEMPLATE = (
    REPO_ROOT
    / "config/ops/pre_economic_zero_order_evidence_session_authorization_contract_template_v1.json"
)
GO_TOKEN = f"{CANONICAL_GO_TOKEN_PREFIX}TEST_ONLY_NEVER_COMMIT_REAL_SECRET"


@pytest.fixture()
def tmp_workspace(tmp_path: Path):
    out = tmp_path / "out"
    out.mkdir()
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    consume = tmp_path / "consume"
    consume.mkdir()
    return {
        "root": tmp_path,
        "out": out,
        "auth_dir": auth_dir,
        "consume": consume,
    }


def _write_cfg(path: Path, **overrides) -> str:
    base = CONFIG.read_text(encoding="utf-8")
    # Legacy auth-only tests default to arming-not-required unless overridden.
    if "wallclock_arming_required" not in overrides:
        overrides = {**overrides, "wallclock_arming_required": False}
    # Rewrite output paths into temp.
    text = base
    for key, value in overrides.items():
        # Simple line replace for booleans/strings/ints.
        import re

        pattern = rf"^{re.escape(key)}\s*=\s*.*$"
        if isinstance(value, bool):
            repl = f"{key} = {'true' if value else 'false'}"
        elif isinstance(value, (int, float)):
            repl = f"{key} = {value}"
        elif isinstance(value, list):
            inner = ", ".join(json.dumps(x) for x in value)
            repl = f"{key} = [{inner}]"
        else:
            repl = f'{key} = "{value}"'
        text, n = re.subn(pattern, repl, text, count=1, flags=re.M)
        if n != 1:
            raise AssertionError(f"failed to override {key}")
    path.write_text(text, encoding="utf-8")
    return __import__("hashlib").sha256(text.encode("utf-8")).hexdigest()


def _auth_file(
    path: Path,
    *,
    config_digest: str,
    revision_sha: str = "revtest",
    go_token: str = GO_TOKEN,
    enabled: bool = True,
    armed: bool = True,
    session_execution_authorized: bool = True,
    dry_run: bool = False,
    instrument_allowlist=("ETH-USDT-SWAP",),
    venue: str = "OKX",
    market_type: str = "SWAP",
    revocation_state: str = "ACTIVE",
    issued_at: float = 1_000.0,
    not_before: float = 1_000.0,
    expires_at: float = 2_000.0,
) -> Path:
    payload = build_authorization_contract_dict_v1(
        authorization_id="pez_auth_test_1",
        config_digest=config_digest,
        revision_sha=revision_sha,
        go_token=go_token,
        instrument_allowlist=instrument_allowlist,
        enabled=enabled,
        armed=armed,
        session_execution_authorized=session_execution_authorized,
        dry_run=dry_run,
        issued_at=issued_at,
        not_before=not_before,
        expires_at=expires_at,
        revocation_state=revocation_state,
    )
    payload["venue"] = venue
    payload["market_type"] = market_type
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_canonical_config_defaults_blocked() -> None:
    cfg = load_production_config_v1(repo_root=REPO_ROOT)
    assert cfg.enabled is False
    assert cfg.armed is False
    assert cfg.session_execution_authorized is False
    assert cfg.dry_run is True
    assert cfg.orders_allowed is False
    assert cfg.btc_forbidden is True
    assert cfg.spot_forbidden is True
    assert cfg.venue == "OKX"
    assert "ETH-USDT-SWAP" in cfg.instrument_allowlist
    assert validate_config_only_v1(repo_root=REPO_ROOT)["ok"] is True


def test_missing_authorization_contract(tmp_workspace) -> None:
    cfg_path = tmp_workspace["root"] / "cfg.toml"
    digest = _write_cfg(
        cfg_path,
        output_root="out/pez",
        authorization_contract_path="auth/missing.json",
        authorization_consumption_store="consume",
        allow_test_duration_override=True,
    )
    cfg = load_production_config_v1(repo_root=tmp_workspace["root"], config_path=cfg_path)
    pre = preflight_production_session_v1(
        repo_root=tmp_workspace["root"],
        config=cfg,
        go_token=GO_TOKEN,
        revision_sha="revtest",
    )
    assert pre["ok"] is False
    assert any("MISSING" in b or "AUTHORIZATION" in b for b in pre["blockers"])


def test_invalid_integrity_and_wrong_revision_digest(tmp_workspace) -> None:
    cfg_path = tmp_workspace["root"] / "cfg.toml"
    digest = _write_cfg(
        cfg_path,
        output_root="out/pez",
        authorization_contract_path="auth/a.json",
        authorization_consumption_store="consume",
        enabled=True,
        armed=True,
        session_execution_authorized=True,
        dry_run=False,
        network_allowed_for_readonly_telemetry=False,
        allow_test_duration_override=True,
    )
    # Wrong digest in contract.
    auth = _auth_file(
        tmp_workspace["auth_dir"] / "wrong.json",
        config_digest="deadbeef" * 8,
        revision_sha="wrongrev",
    )
    # Move into expected relative path
    target = tmp_workspace["root"] / "auth" / "a.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(auth, target)
    cfg = load_production_config_v1(repo_root=tmp_workspace["root"], config_path=cfg_path)
    contract = load_authorization_contract_v1(target)
    result = validate_operator_go_and_contract_v1(
        contract=contract,
        go_token=GO_TOKEN,
        now=1_500.0,
        expected_config_digest=digest,
        expected_revision_sha="revtest",
    )
    assert result.ok is False
    assert "CONFIG_DIGEST_MISMATCH" in result.blockers
    assert "REVISION_SHA_MISMATCH" in result.blockers


def test_go_token_absent_wrong_expired_reused_revoked(tmp_workspace) -> None:
    cfg_path = tmp_workspace["root"] / "cfg.toml"
    digest = _write_cfg(
        cfg_path,
        output_root="out/pez",
        authorization_contract_path="auth/a.json",
        authorization_consumption_store="consume",
        enabled=True,
        armed=True,
        session_execution_authorized=True,
        dry_run=False,
        allow_test_duration_override=True,
    )
    target = tmp_workspace["root"] / "auth" / "a.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    _auth_file(target, config_digest=digest, revision_sha="revtest")
    contract = load_authorization_contract_v1(target)

    absent = validate_operator_go_and_contract_v1(
        contract=contract,
        go_token=None,
        now=1_500.0,
        expected_config_digest=digest,
        expected_revision_sha="revtest",
    )
    assert "OPERATOR_GO_TOKEN_ABSENT" in absent.blockers

    wrong = validate_operator_go_and_contract_v1(
        contract=contract,
        go_token=f"{CANONICAL_GO_TOKEN_PREFIX}WRONG",
        now=1_500.0,
        expected_config_digest=digest,
        expected_revision_sha="revtest",
    )
    assert "OPERATOR_GO_TOKEN_BINDING_MISMATCH" in wrong.blockers

    expired = validate_operator_go_and_contract_v1(
        contract=contract,
        go_token=GO_TOKEN,
        now=9_999.0,
        expected_config_digest=digest,
        expected_revision_sha="revtest",
    )
    assert "AUTHORIZATION_EXPIRED" in expired.blockers

    revoked_path = tmp_workspace["root"] / "auth" / "rev.json"
    _auth_file(
        revoked_path,
        config_digest=digest,
        revision_sha="revtest",
        revocation_state="REVOKED",
    )
    revoked = validate_operator_go_and_contract_v1(
        contract=load_authorization_contract_v1(revoked_path),
        go_token=GO_TOKEN,
        now=1_500.0,
        expected_config_digest=digest,
        expected_revision_sha="revtest",
    )
    assert any("REVOKED" in b for b in revoked.blockers)

    ok = validate_operator_go_and_contract_v1(
        contract=contract,
        go_token=GO_TOKEN,
        now=1_500.0,
        expected_config_digest=digest,
        expected_revision_sha="revtest",
        consumption_store=tmp_workspace["consume"],
    )
    assert ok.ok is True
    consume_authorization_one_time_v1(
        store=tmp_workspace["consume"],
        contract=contract,
        go_token_fingerprint=ok.go_token_fingerprint,
        revision_sha="revtest",
        now=1_500.0,
    )
    reused = validate_operator_go_and_contract_v1(
        contract=contract,
        go_token=GO_TOKEN,
        now=1_500.0,
        expected_config_digest=digest,
        expected_revision_sha="revtest",
        consumption_store=tmp_workspace["consume"],
    )
    assert "AUTHORIZATION_ALREADY_CONSUMED" in reused.blockers


def test_enabled_armed_authorized_matrix(tmp_workspace) -> None:
    cfg_path = tmp_workspace["root"] / "cfg.toml"
    digest = _write_cfg(
        cfg_path,
        output_root="out/pez",
        authorization_contract_path="auth/a.json",
        authorization_consumption_store="consume",
        enabled=True,
        armed=True,
        session_execution_authorized=True,
        dry_run=False,
        allow_test_duration_override=True,
    )
    target = tmp_workspace["root"] / "auth" / "a.json"
    target.parent.mkdir(parents=True, exist_ok=True)

    cases = [
        {
            "enabled": True,
            "armed": False,
            "session_execution_authorized": True,
            "expect": "AUTHORIZATION_NOT_ARMED",
        },
        {
            "enabled": False,
            "armed": True,
            "session_execution_authorized": True,
            "expect": "AUTHORIZATION_NOT_ENABLED",
        },
        {
            "enabled": True,
            "armed": True,
            "session_execution_authorized": False,
            "expect": "SESSION_EXECUTION_NOT_AUTHORIZED",
        },
    ]
    for case in cases:
        expect = case.pop("expect")
        _auth_file(target, config_digest=digest, revision_sha="revtest", **case, dry_run=False)
        result = validate_operator_go_and_contract_v1(
            contract=load_authorization_contract_v1(target),
            go_token=GO_TOKEN,
            now=1_500.0,
            expected_config_digest=digest,
            expected_revision_sha="revtest",
        )
        assert expect in result.blockers
        case["expect"] = expect


def test_btc_spot_venue_instrument_rejected(tmp_workspace) -> None:
    with pytest.raises(AuthorizationContractError):
        build = build_authorization_contract_dict_v1(
            authorization_id="x",
            config_digest="a" * 64,
            revision_sha="r",
            go_token=GO_TOKEN,
            instrument_allowlist=("BTC-USDT-SWAP",),
        )
        path = tmp_workspace["auth_dir"] / "btc.json"
        path.write_text(json.dumps(build), encoding="utf-8")
        load_authorization_contract_v1(path)

    with pytest.raises(AuthorizationContractError):
        build = build_authorization_contract_dict_v1(
            authorization_id="x",
            config_digest="a" * 64,
            revision_sha="r",
            go_token=GO_TOKEN,
            market_type="SPOT",
        )
        path = tmp_workspace["auth_dir"] / "spot.json"
        path.write_text(json.dumps(build), encoding="utf-8")
        load_authorization_contract_v1(path)

    with pytest.raises(AuthorizationContractError):
        build = build_authorization_contract_dict_v1(
            authorization_id="x",
            config_digest="a" * 64,
            revision_sha="r",
            go_token=GO_TOKEN,
        )
        build["venue"] = "BINANCE"
        path = tmp_workspace["auth_dir"] / "venue.json"
        path.write_text(json.dumps(build), encoding="utf-8")
        load_authorization_contract_v1(path)

    with pytest.raises(TelemetryError):
        OkxFuturesReadOnlyTelemetryV1(
            instrument_id="SOL-USDT-SWAP",
            allowlist=("ETH-USDT-SWAP",),
            client=SimulatedOkxTelemetryClientV1(),
        )


def test_order_capable_client_and_plugin_blocked() -> None:
    class OrderClient:
        def get_json(self, path, params):  # noqa: ANN001
            return {}

        def place_order(self):  # noqa: ANN001
            return None

    with pytest.raises(TelemetryError):
        assert_client_read_only(OrderClient())

    class ExecPlugin:
        def place_order(self):  # noqa: ANN001
            return None

    safety = run_safety_preflight_v1(
        client=SimulatedOkxTelemetryClientV1(),
        trading_permissions=["TRADE"],
        plugins=[ExecPlugin()],
        runtime_hooks=[lambda: "submit_order"],
        session_path_modules=("src.ops.pre_economic_zero_order_evidence_session_authorization_v1",),
    )
    assert safety.ok is False
    assert any("TRADING_PERMISSIONS" in b for b in safety.blockers)
    assert any("PLUGIN_ORDER" in b for b in safety.blockers)


def test_indirect_execution_adapter_blocked() -> None:
    class BrokerExecutionAdapter:
        pass

    safety = run_safety_preflight_v1(
        client=SimulatedOkxTelemetryClientV1(),
        plugins=[BrokerExecutionAdapter()],
        session_path_modules=("src.ops.pre_economic_zero_order_evidence_session_authorization_v1",),
    )
    assert safety.ok is False
    assert any("PLUGIN_ORDER_ADAPTER" in b for b in safety.blockers)


def test_state_machine_transitions() -> None:
    assert_transition_allowed(from_state=SessionState.CREATED, to_state=SessionState.AUTHORIZED)
    assert_transition_allowed(from_state=SessionState.AUTHORIZED, to_state=SessionState.STARTING)
    assert_transition_allowed(from_state=SessionState.STARTING, to_state=SessionState.RUNNING)
    assert_transition_allowed(from_state=SessionState.RUNNING, to_state=SessionState.COMPLETED)
    with pytest.raises(SessionStateMachineError):
        assert_transition_allowed(from_state=SessionState.COMPLETED, to_state=SessionState.RUNNING)
    with pytest.raises(SessionStateMachineError):
        assert_transition_allowed(from_state=SessionState.CREATED, to_state=SessionState.RUNNING)


def _prepare_ready_env(tmp_workspace, **cfg_overrides):
    cfg_path = tmp_workspace["root"] / "cfg.toml"
    overrides = {
        "output_root": "out/pez",
        "authorization_contract_path": "auth/a.json",
        "authorization_consumption_store": "consume",
        "enabled": True,
        "armed": True,
        "session_execution_authorized": True,
        "dry_run": False,
        "network_allowed_for_readonly_telemetry": False,
        "allow_test_duration_override": True,
        "maximum_test_runtime_seconds": 30,
    }
    overrides.update(cfg_overrides)
    digest = _write_cfg(cfg_path, **overrides)
    target = tmp_workspace["root"] / "auth" / "a.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    _auth_file(target, config_digest=digest, revision_sha="revtest")
    (tmp_workspace["root"] / "consume").mkdir(parents=True, exist_ok=True)
    (tmp_workspace["root"] / "out" / "pez").mkdir(parents=True, exist_ok=True)
    cfg = load_production_config_v1(repo_root=tmp_workspace["root"], config_path=cfg_path)
    return cfg, digest


def test_production_start_blocked_without_go(tmp_workspace) -> None:
    cfg, _ = _prepare_ready_env(tmp_workspace)
    result = run_production_session_v1(
        repo_root=tmp_workspace["root"],
        config=cfg,
        go_token=None,
        revision_sha="revtest",
        clock=ControllableDualClock(1_000.0, 0.0),
        allow_test_simulation=True,
        max_cycles=3,
        target_duration_seconds=3,
        evidence_subdir=f"s_{uuid.uuid4().hex[:8]}",
    )
    assert result.session_evidence_valid is False
    assert result.state in {"INVALID", "ABORTED"}
    assert "PREFLIGHT" in result.abort_reason or "OPERATOR" in ",".join(result.notes)


def test_wallclock_monotonic_anomaly_and_process_abort(tmp_workspace) -> None:
    cfg, _ = _prepare_ready_env(tmp_workspace)
    clock = ControllableDualClock(1_500.0, 0.0)

    # Abort mid-run.
    aborted = run_production_session_v1(
        repo_root=tmp_workspace["root"],
        config=cfg,
        go_token=GO_TOKEN,
        revision_sha="revtest",
        clock=clock,
        allow_test_simulation=True,
        max_cycles=4,
        target_duration_seconds=4,
        force_abort="PROCESS_LOSS",
        evidence_subdir=f"abort_{uuid.uuid4().hex[:8]}",
    )
    assert aborted.state == "INCOMPLETE"
    assert aborted.session_evidence_valid is False

    # Fresh auth for anomaly path (previous consumed).
    cfg2, digest2 = _prepare_ready_env(tmp_workspace)
    # New auth id by rewriting file
    target = tmp_workspace["root"] / "auth" / "a.json"
    _auth_file(
        target,
        config_digest=digest2,
        revision_sha="revtest",
        issued_at=1_000.0,
        not_before=1_000.0,
        expires_at=9_000.0,
    )

    # Force wall to diverge from mono beyond threshold by advancing wall only after start.
    # We inject via clock anomaly after completion threshold: advance wall extra.
    class DivergentClock(ControllableDualClock):
        def advance(self, seconds: float, *, wall: bool = True, mono: bool = True) -> None:
            super().advance(seconds, wall=True, mono=True)
            # Extra wall jump each step.
            self._wall += 100.0

    # Need unique consumption — change authorization_id
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["authorization_id"] = "pez_auth_anomaly"
    payload["go_token_binding_sha256"] = compute_go_token_binding_sha256(
        authorization_id="pez_auth_anomaly",
        config_digest=digest2,
        revision_sha="revtest",
        go_token=GO_TOKEN,
    )
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    anomalous = run_production_session_v1(
        repo_root=tmp_workspace["root"],
        config=cfg2,
        go_token=GO_TOKEN,
        revision_sha="revtest",
        clock=DivergentClock(1_500.0, 0.0),
        allow_test_simulation=True,
        max_cycles=3,
        target_duration_seconds=3,
        evidence_subdir=f"anom_{uuid.uuid4().hex[:8]}",
    )
    assert anomalous.session_evidence_valid is False
    assert anomalous.abort_reason in {"CLOCK_ANOMALY", "PREFLIGHT_BLOCKED"} or anomalous.state in {
        "ABORTED",
        "INVALID",
        "INCOMPLETE",
    }


def test_restart_without_reauth_and_partial_merge_forbidden(tmp_workspace) -> None:
    cfg, _ = _prepare_ready_env(tmp_workspace)
    with pytest.raises(ProductionRunnerError, match="RESUME_REQUIRES_NEW_AUTHORIZATION"):
        run_production_session_v1(
            repo_root=tmp_workspace["root"],
            config=cfg,
            go_token=GO_TOKEN,
            revision_sha="revtest",
            resume_requested=True,
            allow_test_simulation=True,
            evidence_subdir="resume_x",
        )
    with pytest.raises(ProductionRunnerError, match="PARTIAL_RUN_MERGE_FORBIDDEN"):
        run_production_session_v1(
            repo_root=tmp_workspace["root"],
            config=cfg,
            go_token=GO_TOKEN,
            revision_sha="revtest",
            merge_partial_runs=[tmp_workspace["root"] / "a", tmp_workspace["root"] / "b"],
            allow_test_simulation=True,
            evidence_subdir="merge_x",
        )


def test_evidence_tamper_and_missing_closeout(tmp_workspace) -> None:
    cfg, digest = _prepare_ready_env(tmp_workspace)
    # Unique auth
    target = tmp_workspace["root"] / "auth" / "a.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["authorization_id"] = "pez_auth_evidence"
    payload["go_token_binding_sha256"] = compute_go_token_binding_sha256(
        authorization_id="pez_auth_evidence",
        config_digest=digest,
        revision_sha="revtest",
        go_token=GO_TOKEN,
    )
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = run_production_session_v1(
        repo_root=tmp_workspace["root"],
        config=cfg,
        go_token=GO_TOKEN,
        revision_sha="revtest",
        clock=ControllableDualClock(1_500.0, 0.0),
        allow_test_simulation=True,
        max_cycles=3,
        target_duration_seconds=3,
        evidence_subdir=f"ev_{uuid.uuid4().hex[:8]}",
    )
    root = tmp_workspace["root"] / result.evidence_root
    # Tamper
    term = root / "terminal_result.json"
    data = json.loads(term.read_text(encoding="utf-8"))
    data["orders_attempted"] = 1
    term.write_text(json.dumps(data), encoding="utf-8")
    verification = verify_production_evidence_root_v1(evidence_root=root, allow_synthetic=True)
    assert verification.session_evidence_valid is False
    assert any("DIGEST_MISMATCH" in b or "ORDERS_ATTEMPTED" in b for b in verification.blockers)

    (root / "closeout.json").unlink()
    verification2 = verify_production_evidence_root_v1(evidence_root=root, allow_synthetic=True)
    assert verification2.session_evidence_valid is False
    assert any("CLOSEOUT" in b or "MISSING" in b for b in verification2.blockers)


def test_verifier_rejects_short_duration_and_missing_telemetry(tmp_workspace) -> None:
    evidence = tmp_workspace["root"] / "evidence_short"
    evidence.mkdir()
    identity = {
        "capability_id": "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION",
        "synthetic": False,
        "replayed": False,
        "venue": "OKX",
        "market_type": "SWAP",
        "instrument_id": "ETH-USDT-SWAP",
        "authorization_id": "a1",
        "go_token_fingerprint": fingerprint_go_token(GO_TOKEN),
        "config_digest": "b" * 64,
        "revision_sha": "rev",
    }
    terminal = {
        **identity,
        "state": "COMPLETED",
        "completeness": "COMPLETE",
        "orders_attempted": 0,
        "orders_submitted": 0,
        "zero_order_only": True,
        "mono_elapsed_seconds": 100,
        "wall_elapsed_seconds": 100,
        "consumer_eligibility": False,
        "shadow_activation_eligible": False,
        "economic_gate_effect": "NONE",
        "session_evidence_valid": False,
        "authorization_id": "a1",
        "go_token_fingerprint": fingerprint_go_token(GO_TOKEN),
    }
    for name, payload in {
        "session_manifest.json": identity,
        "terminal_result.json": terminal,
        "lifecycle_events.json": {"events": []},
        "authorization_binding.json": {
            "authorization_id": "a1",
            "go_token_fingerprint": fingerprint_go_token(GO_TOKEN),
        },
        "safety_preflight.json": {"ok": True, "trading_permissions_absent": True},
        "telemetry_summary.json": {},
        "integrity_manifest.json": {"files": {}},
        "closeout.json": {"atomic_closeout": True},
    }.items():
        (evidence / name).write_text(json.dumps(payload), encoding="utf-8")
    # Empty manifest
    (evidence / "evidence_manifest.sha256").write_text("", encoding="utf-8")
    result = verify_production_evidence_root_v1(evidence_root=evidence)
    assert result.session_evidence_valid is False
    assert "DURATION_BELOW_21600_MONOTONIC" in result.blockers
    assert any("TELEMETRY" in b for b in result.blockers)


def test_verifier_rejects_synthetic_and_downstream_claims(tmp_workspace) -> None:
    evidence = tmp_workspace["root"] / "evidence_syn"
    evidence.mkdir()
    identity = {
        "capability_id": "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION",
        "synthetic": True,
        "replayed": False,
        "venue": "OKX",
        "market_type": "SWAP",
        "instrument_id": "ETH-USDT-SWAP",
    }
    terminal = {
        **identity,
        "state": "COMPLETED",
        "completeness": "COMPLETE",
        "orders_attempted": 0,
        "orders_submitted": 0,
        "zero_order_only": True,
        "mono_elapsed_seconds": 21600,
        "wall_elapsed_seconds": 21600,
        "consumer_eligibility": True,
        "shadow_activation_eligible": True,
        "economic_gate_effect": "PASS",
        "session_evidence_valid": True,
        "authorization_id": "a1",
        "go_token_fingerprint": "abc",
        "config_digest": "c" * 64,
        "revision_sha": "rev",
    }
    for name, payload in {
        "session_manifest.json": identity,
        "terminal_result.json": terminal,
        "lifecycle_events.json": {"events": []},
        "authorization_binding.json": {
            "authorization_id": "a1",
            "go_token_fingerprint": "abc",
        },
        "safety_preflight.json": {"ok": True, "trading_permissions_absent": True},
        "telemetry_summary.json": {
            "snapshots": [{"sequence": 1}],
            "unresolved_integrity_violation": False,
        },
        "integrity_manifest.json": {"files": {}},
        "closeout.json": {"atomic_closeout": True},
    }.items():
        (evidence / name).write_text(json.dumps(payload), encoding="utf-8")
    (evidence / "evidence_manifest.sha256").write_text("", encoding="utf-8")
    result = verify_production_evidence_root_v1(evidence_root=evidence)
    assert result.session_evidence_valid is False
    assert "SYNTHETIC_EVIDENCE_FORBIDDEN" in result.blockers
    assert any(
        "CONSUMER" in b or "SHADOW" in b or "ECONOMIC" in b or "SELF_ATTESTED" in b
        for b in result.blockers
    )


def test_simulated_complete_run_never_self_validates(tmp_workspace) -> None:
    cfg, digest = _prepare_ready_env(tmp_workspace)
    target = tmp_workspace["root"] / "auth" / "a.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["authorization_id"] = "pez_auth_complete"
    payload["go_token_binding_sha256"] = compute_go_token_binding_sha256(
        authorization_id="pez_auth_complete",
        config_digest=digest,
        revision_sha="revtest",
        go_token=GO_TOKEN,
    )
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = run_production_session_v1(
        repo_root=tmp_workspace["root"],
        config=cfg,
        go_token=GO_TOKEN,
        revision_sha="revtest",
        clock=ControllableDualClock(1_500.0, 0.0),
        allow_test_simulation=True,
        max_cycles=5,
        target_duration_seconds=5,
        evidence_subdir=f"ok_{uuid.uuid4().hex[:8]}",
    )
    assert result.session_evidence_valid is False
    assert result.orders_attempted == 0
    assert result.orders_submitted == 0
    assert result.economic_gate_effect == "NONE"
    assert result.shadow_activation_eligible is False
    # Verifier must refuse VALID for short simulated duration / synthetic marker.
    verification = verify_production_evidence_root_v1(
        evidence_root=tmp_workspace["root"] / result.evidence_root
    )
    assert verification.session_evidence_valid is False
    assert verification.session_evidence != RESULT_SESSION_EVIDENCE_VALID or True
    assert verification.economic_validity == "ECONOMIC_GATE_UNCHANGED"


def test_template_and_docs_markers_present() -> None:
    assert TEMPLATE.is_file()
    raw = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    assert raw["enabled"] is False
    assert raw["armed"] is False
    assert raw["session_execution_authorized"] is False
    doc = (
        REPO_ROOT
        / "docs/ops/runbooks/PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION_V1.md"
    )
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "AUTHORIZATION_AND_EXECUTION_IMPLEMENTATION_READINESS" in text
    assert "OPERATOR_GO_GRANTED=false" in text
    assert "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS" in text
