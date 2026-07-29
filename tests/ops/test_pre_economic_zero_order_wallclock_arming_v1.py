"""Focused tests for PRE_ECONOMIC_ZERO_ORDER_WALLCLOCK_EXECUTION_ARMING_V1.

Simulated clocks only. No real 6h session. No GO secrets committed.
Canonical State Switch via transition_state; no Switch/Stay placeholders.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from src.ops.pre_economic_zero_order_decision_cycle_observer_v1 import DecisionCycleObserverV1
from src.ops.pre_economic_zero_order_economic_evidence_v1 import (
    validate_decision_record_completeness,
)
from src.ops.pre_economic_zero_order_evidence_session_authorization_v1 import (
    CANONICAL_GO_TOKEN_PREFIX,
    build_authorization_contract_dict_v1,
)
from src.ops.pre_economic_zero_order_evidence_session_production_runner_v1 import (
    ControllableDualClock,
    ProductionRunnerError,
    forbid_order_attempt,
    load_production_config_v1,
    preflight_production_session_v1,
    run_production_session_v1,
)
from src.ops.pre_economic_zero_order_evidence_session_production_verifier_v1 import (
    verify_production_evidence_root_v1,
)
from src.ops.pre_economic_zero_order_wallclock_arming_v1 import (
    DEFAULT_MAX_ARMING_TTL_SECONDS,
    TRUTH_CLAIM,
    build_wallclock_arming_lease_dict_v1,
    wallclock_arming_defaults_blocked_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "config/ops/pre_economic_zero_order_evidence_session_authorization_v1.toml"
GO_TOKEN = f"{CANONICAL_GO_TOKEN_PREFIX}TEST_ONLY_NEVER_COMMIT_REAL_SECRET"


@pytest.fixture()
def tmp_workspace(tmp_path: Path):
    out = tmp_path / "out"
    out.mkdir()
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    arm_dir = tmp_path / "arm"
    arm_dir.mkdir()
    consume = tmp_path / "consume"
    consume.mkdir()
    arm_consume = tmp_path / "arm_consume"
    arm_consume.mkdir()
    return {
        "root": tmp_path,
        "out": out,
        "auth_dir": auth_dir,
        "arm_dir": arm_dir,
        "consume": consume,
        "arm_consume": arm_consume,
    }


def _write_cfg(path: Path, **overrides) -> str:
    import re

    text = CONFIG.read_text(encoding="utf-8")
    defaults = {
        "wallclock_arming_required": True,
        "output_root": "out/pez",
        "authorization_contract_path": "auth/a.json",
        "authorization_consumption_store": "consume",
        "wallclock_arming_lease_path": "arm/lease.json",
        "wallclock_arming_consumption_store": "arm_consume",
        "allow_test_duration_override": True,
    }
    merged = {**defaults, **overrides}
    for key, value in merged.items():
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


def _auth_and_arm(
    ws,
    *,
    digest: str,
    enabled: bool = True,
    armed: bool = True,
    session_execution_authorized: bool = True,
    dry_run: bool = False,
    wallclock_execution_authorized: bool = True,
    go_token: str = GO_TOKEN,
    issued_at: float = 1_000.0,
    expires_at: float = 2_000.0,
    arm_expires_at: float = 1_800.0,
) -> tuple[Path, Path]:
    auth_path = ws["root"] / "auth" / "a.json"
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_payload = build_authorization_contract_dict_v1(
        authorization_id="pez_auth_arm_1",
        config_digest=digest,
        revision_sha="revtest",
        go_token=go_token,
        enabled=enabled,
        armed=armed,
        session_execution_authorized=session_execution_authorized,
        dry_run=dry_run,
        issued_at=issued_at,
        not_before=issued_at,
        expires_at=expires_at,
    )
    auth_path.write_text(
        json.dumps(auth_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lease_path = ws["root"] / "arm" / "lease.json"
    lease_path.parent.mkdir(parents=True, exist_ok=True)
    lease_payload = build_wallclock_arming_lease_dict_v1(
        arming_id="pez_arm_1",
        authorization_id="pez_auth_arm_1",
        config_digest=digest,
        revision_sha="revtest",
        go_token=go_token,
        issued_at=issued_at,
        not_before=issued_at,
        expires_at=arm_expires_at,
        max_arming_ttl_seconds=DEFAULT_MAX_ARMING_TTL_SECONDS,
        wallclock_execution_authorized=wallclock_execution_authorized,
        dry_run=dry_run,
        session_execution_authorized=session_execution_authorized,
    )
    lease_path.write_text(
        json.dumps(lease_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return auth_path, lease_path


def test_safety_defaults_blocked() -> None:
    cfg = load_production_config_v1(repo_root=REPO_ROOT)
    assert cfg.enabled is False
    assert cfg.armed is False
    assert cfg.dry_run is True
    assert cfg.session_execution_authorized is False
    assert cfg.orders_allowed is False
    assert cfg.broker_write is False
    assert cfg.live_authorized is False
    assert cfg.paper_authorized is False
    assert cfg.testnet_authorized is False
    assert cfg.shadow_activation_authorized is False
    assert cfg.wallclock_execution_authorized is False
    defaults = wallclock_arming_defaults_blocked_v1()
    assert defaults["orders"] is False
    assert defaults["truth_claim"] == TRUTH_CLAIM


def test_go_absent_or_invalid_blocks(tmp_workspace) -> None:
    cfg_path = tmp_workspace["root"] / "cfg.toml"
    digest = _write_cfg(
        cfg_path,
        enabled=True,
        armed=True,
        session_execution_authorized=True,
        dry_run=False,
    )
    _auth_and_arm(tmp_workspace, digest=digest)
    cfg = load_production_config_v1(repo_root=tmp_workspace["root"], config_path=cfg_path)
    absent = preflight_production_session_v1(
        repo_root=tmp_workspace["root"],
        config=cfg,
        go_token=None,
        revision_sha="revtest",
        now=1_500.0,
    )
    assert absent["ok"] is False
    assert "OPERATOR_GO_TOKEN_ABSENT" in absent["blockers"]

    bad = preflight_production_session_v1(
        repo_root=tmp_workspace["root"],
        config=cfg,
        go_token=f"{CANONICAL_GO_TOKEN_PREFIX}WRONG",
        revision_sha="revtest",
        now=1_500.0,
    )
    assert bad["ok"] is False
    assert any("BINDING_MISMATCH" in b or "ARMING_GO" in b for b in bad["blockers"])


def test_arming_absent_blocks_even_with_valid_go(tmp_workspace) -> None:
    cfg_path = tmp_workspace["root"] / "cfg.toml"
    digest = _write_cfg(
        cfg_path,
        enabled=True,
        armed=True,
        session_execution_authorized=True,
        dry_run=False,
        wallclock_arming_lease_path="arm/missing.json",
    )
    auth_path = tmp_workspace["root"] / "auth" / "a.json"
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_payload = build_authorization_contract_dict_v1(
        authorization_id="pez_auth_arm_1",
        config_digest=digest,
        revision_sha="revtest",
        go_token=GO_TOKEN,
        enabled=True,
        armed=True,
        session_execution_authorized=True,
        dry_run=False,
        issued_at=1_000.0,
        not_before=1_000.0,
        expires_at=2_000.0,
    )
    auth_path.write_text(
        json.dumps(auth_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    cfg = load_production_config_v1(repo_root=tmp_workspace["root"], config_path=cfg_path)
    pre = preflight_production_session_v1(
        repo_root=tmp_workspace["root"],
        config=cfg,
        go_token=GO_TOKEN,
        revision_sha="revtest",
        now=1_500.0,
    )
    assert pre["ok"] is False
    assert any("WALLCLOCK_ARMING" in b for b in pre["blockers"])


def test_dry_run_true_blocks_production(tmp_workspace) -> None:
    cfg_path = tmp_workspace["root"] / "cfg.toml"
    digest = _write_cfg(
        cfg_path,
        enabled=True,
        armed=True,
        session_execution_authorized=True,
        dry_run=True,
    )
    _auth_and_arm(tmp_workspace, digest=digest, dry_run=True)
    cfg = load_production_config_v1(repo_root=tmp_workspace["root"], config_path=cfg_path)
    pre = preflight_production_session_v1(
        repo_root=tmp_workspace["root"],
        config=cfg,
        go_token=GO_TOKEN,
        revision_sha="revtest",
        now=1_500.0,
    )
    assert pre["ok"] is False
    assert any("DRY_RUN" in b for b in pre["blockers"])


def test_orders_broker_write_impossible() -> None:
    with pytest.raises(ProductionRunnerError, match="ORDER_ATTEMPT_FORBIDDEN"):
        forbid_order_attempt("place_order")
    cfg = load_production_config_v1(repo_root=REPO_ROOT)
    assert cfg.orders_allowed is False
    assert cfg.broker_writes_allowed is False
    assert cfg.broker_write is False


def test_duration_bound_and_simulated_complete(tmp_workspace) -> None:
    cfg_path = tmp_workspace["root"] / "cfg.toml"
    digest = _write_cfg(
        cfg_path,
        enabled=True,
        armed=True,
        session_execution_authorized=True,
        dry_run=False,
        maximum_test_runtime_seconds=30,
    )
    _auth_and_arm(tmp_workspace, digest=digest)
    cfg = load_production_config_v1(repo_root=tmp_workspace["root"], config_path=cfg_path)
    clock = ControllableDualClock(_wall=1_500.0, _mono=0.0)
    result = run_production_session_v1(
        repo_root=tmp_workspace["root"],
        config=cfg,
        go_token=GO_TOKEN,
        revision_sha="revtest",
        clock=clock,
        allow_test_simulation=True,
        target_duration_seconds=10,
        max_cycles=5,
        evidence_subdir="sim1",
    )
    assert result.state == "COMPLETED"
    assert result.orders_attempted == 0
    assert result.orders_submitted == 0
    assert TRUTH_CLAIM in result.notes
    assert "ECONOMIC_VALIDITY_PASS" not in "".join(result.notes)
    evidence = tmp_workspace["root"] / result.evidence_root
    decisions = (
        (evidence / "economic_decisions.jsonl").read_text(encoding="utf-8").strip().splitlines()
    )
    assert decisions
    for line in decisions:
        row = json.loads(line)
        assert "switch_stay_state" not in row
        assert "state_switch" in row
        assert validate_decision_record_completeness(row) == []
    summary = json.loads((evidence / "session_economic_summary.json").read_text(encoding="utf-8"))
    assert "state_switch_transitions" in summary
    assert "switch_stale_count" in summary
    assert "switch_events" not in summary
    assert summary["economic_validity_pass"] is False
    assert summary["orders"] is False


def test_go_alone_without_arming_cannot_start(tmp_workspace) -> None:
    cfg_path = tmp_workspace["root"] / "cfg.toml"
    digest = _write_cfg(
        cfg_path,
        enabled=True,
        armed=True,
        session_execution_authorized=True,
        dry_run=False,
        wallclock_arming_required=True,
        wallclock_arming_lease_path="arm/missing.json",
    )
    auth_path = tmp_workspace["root"] / "auth" / "a.json"
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_payload = build_authorization_contract_dict_v1(
        authorization_id="pez_auth_arm_1",
        config_digest=digest,
        revision_sha="revtest",
        go_token=GO_TOKEN,
        enabled=True,
        armed=True,
        session_execution_authorized=True,
        dry_run=False,
        issued_at=1_000.0,
        not_before=1_000.0,
        expires_at=2_000.0,
    )
    auth_path.write_text(
        json.dumps(auth_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    cfg = load_production_config_v1(repo_root=tmp_workspace["root"], config_path=cfg_path)
    clock = ControllableDualClock(_wall=1_500.0, _mono=0.0)
    result = run_production_session_v1(
        repo_root=tmp_workspace["root"],
        config=cfg,
        go_token=GO_TOKEN,
        revision_sha="revtest",
        clock=clock,
        allow_test_simulation=True,
        target_duration_seconds=10,
        max_cycles=2,
        evidence_subdir="blocked_go_only",
    )
    assert result.state != "COMPLETED"
    assert "PREFLIGHT_BLOCKED" in result.abort_reason or "WALLCLOCK_ARMING" in result.abort_reason


def test_canonical_state_switch_not_switch_stay() -> None:
    obs = DecisionCycleObserverV1(instrument="ETH-USDT-SWAP")
    r1 = obs.observe(
        timestamp=1.0,
        cycle_index=0,
        snapshot={"instrument_id": "ETH-USDT-SWAP", "sequence": 1},
        mid_price=100.0,
    )
    r2 = obs.observe(
        timestamp=2.0,
        cycle_index=1,
        snapshot={"instrument_id": "ETH-USDT-SWAP", "sequence": 2},
        mid_price=100.2,
    )
    for rec in (r1, r2):
        payload = rec.to_dict()
        assert "switch_stay_state" not in payload
        assert "state_switch" in payload
        assert payload["state_switch"]["owner"] == "trading.master_v2.double_play_state"
        assert payload["provenance"]["state_switch_owner"] == "trading.master_v2.double_play_state"
    stale = obs.observe(
        timestamp=20.0,
        cycle_index=2,
        snapshot={"instrument_id": "ETH-USDT-SWAP", "sequence": 3},
        mid_price=100.2,
        force_switch_availability="STALE",
    )
    assert stale.state_switch["availability"] == "STALE"
    assert stale.rejection_or_no_trade_reason == "STATE_SWITCH_EVIDENCE_STALE"
    assert obs.state.switch_stale_count >= 1


def test_interruption_recovery_no_silent_resume(tmp_workspace) -> None:
    cfg_path = tmp_workspace["root"] / "cfg.toml"
    digest = _write_cfg(
        cfg_path,
        enabled=True,
        armed=True,
        session_execution_authorized=True,
        dry_run=False,
    )
    _auth_and_arm(tmp_workspace, digest=digest)
    cfg = load_production_config_v1(repo_root=tmp_workspace["root"], config_path=cfg_path)
    clock = ControllableDualClock(_wall=1_500.0, _mono=0.0)
    result = run_production_session_v1(
        repo_root=tmp_workspace["root"],
        config=cfg,
        go_token=GO_TOKEN,
        revision_sha="revtest",
        clock=clock,
        allow_test_simulation=True,
        target_duration_seconds=10,
        max_cycles=3,
        force_abort="PROCESS_LOSS",
        evidence_subdir="abort1",
    )
    assert result.completeness in {"INCOMPLETE", "ABORTED", "INVALID"}
    with pytest.raises(ProductionRunnerError, match="RESUME_REQUIRES_NEW_AUTHORIZATION"):
        run_production_session_v1(
            repo_root=tmp_workspace["root"],
            config=cfg,
            go_token=GO_TOKEN,
            revision_sha="revtest",
            clock=ControllableDualClock(_wall=1_600.0, _mono=0.0),
            allow_test_simulation=True,
            target_duration_seconds=10,
            max_cycles=2,
            resume_requested=True,
            evidence_subdir="resume_forbidden",
        )


def test_no_downstream_authority_and_verifier(tmp_workspace) -> None:
    cfg_path = tmp_workspace["root"] / "cfg.toml"
    digest = _write_cfg(
        cfg_path,
        enabled=True,
        armed=True,
        session_execution_authorized=True,
        dry_run=False,
    )
    _auth_and_arm(tmp_workspace, digest=digest)
    cfg = load_production_config_v1(repo_root=tmp_workspace["root"], config_path=cfg_path)
    clock = ControllableDualClock(_wall=1_500.0, _mono=0.0)
    result = run_production_session_v1(
        repo_root=tmp_workspace["root"],
        config=cfg,
        go_token=GO_TOKEN,
        revision_sha="revtest",
        clock=clock,
        allow_test_simulation=True,
        target_duration_seconds=10,
        max_cycles=4,
        evidence_subdir="verify1",
    )
    assert result.consumer_eligibility is False
    assert result.shadow_activation_eligible is False
    assert result.economic_gate_effect == "NONE"
    evidence = tmp_workspace["root"] / result.evidence_root
    verified = verify_production_evidence_root_v1(
        evidence_root=evidence,
        expected_config_digest=digest,
        expected_revision_sha="revtest",
        allow_synthetic=True,
    )
    # Duration below 21600 in simulation → incomplete or invalid, never economic pass.
    assert (
        verified.session_evidence_valid is False
        or verified.economic_validity == "ECONOMIC_GATE_UNCHANGED"
    )
    assert verified.economic_validity == "ECONOMIC_GATE_UNCHANGED"
    assert verified.shadow_activation == "SHADOW_ACTIVATION_INELIGIBLE"
    assert verified.orders_allowed is False
    assert any(TRUTH_CLAIM in n for n in verified.notes)
