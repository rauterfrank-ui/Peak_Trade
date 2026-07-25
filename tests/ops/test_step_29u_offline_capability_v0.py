"""Capability-level tests for STEP 29U offline capability v0."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.okx_futures_shadow_no_order_entrypoint_v0 import (
    OkxFuturesShadowNoOrderCycleResultV0,
    run_okx_futures_shadow_no_order_cycle_v0,
)
from src.ops.step_29u_offline_capability_v0 import (
    ALLOWED_TRANSITIONS,
    CAPABILITY_ID,
    CLI_RELPATH,
    FORBIDDEN_IMPORT_SURFACES,
    FORBIDDEN_STATE_NAMES,
    LIFECYCLE_OWNER,
    PACKAGE_MARKER,
    RESULT_BLOCKED,
    RESULT_ERROR,
    RESULT_PASS,
    FailureClassV0,
    SessionStateV0,
    Step29UOfflineCapabilityError,
    build_mode_identity_v0,
    resolve_evidence_dir,
    run_step_29u_offline_capability_v0,
    transition_state_v0,
    validate_mode_identity_v0,
    verify_capability_evidence_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / CLI_RELPATH
INVENTORY = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "runbooks"
    / "STEP_29U_CANONICAL_BINDING_AND_IMPLEMENTATION_INVENTORY_V0.md"
)
READINESS = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0.md"
)
GIT_SHA = "40f356e357d3a8bcb13cae065103bb6d8eda5417"


def _pass_cycle(**overrides: object) -> OkxFuturesShadowNoOrderCycleResultV0:
    base = run_okx_futures_shadow_no_order_cycle_v0(
        mode="shadow",
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    if not overrides:
        return base
    return replace(base, **overrides)  # type: ignore[arg-type]


def test_package_marker_and_owners() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    assert CAPABILITY_ID == "STEP_29U_OFFLINE_CAPABILITY_V0"
    assert LIFECYCLE_OWNER == "ops.step_29u_offline_capability_v0"
    assert CLI.is_file()


def test_a_valid_hold_cycle_reaches_pass(tmp_path: Path) -> None:
    out = tmp_path / "ev"
    out_rel = str(out.relative_to(tmp_path))
    # Use tmp as repo root for evidence isolation
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        output_path=out_rel,
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(),
    )
    assert result.capability_result == RESULT_PASS
    assert result.final_state == SessionStateV0.COMPLETED.value
    assert result.step_29u_implemented is True
    assert result.step_29u_bound_offline is True
    assert result.step_29u_verified_offline is True
    assert result.step_29u_activated is False
    assert result.orders_created is False
    assert result.orders_submitted is False
    assert result.network_runtime_used is False
    assert result.scheduler_activated is False
    assert result.runtime_activated is False
    assert len(result.cycles) == 1
    assert result.cycles[0].direction == "HOLD"


def test_b_decision_consumed_without_recompute(tmp_path: Path) -> None:
    cycle = _pass_cycle()
    seen: dict[str, object] = {}

    def runner(**kwargs: object) -> OkxFuturesShadowNoOrderCycleResultV0:
        seen["called"] = True
        seen["mode"] = kwargs.get("mode")
        return cycle

    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=runner,
    )
    assert seen["called"] is True
    assert seen["mode"] == "shadow"
    assert result.cycles[0].decision_result == cycle.decision_result
    assert result.cycles[0].cycle_payload["decision_result"] == cycle.decision_result


def test_c_risk_veto_reaches_blocked(tmp_path: Path) -> None:
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(risk_sizing_result="VETO"),
    )
    assert result.capability_result == RESULT_BLOCKED
    assert result.failure_class == FailureClassV0.RISK_BLOCKED.value


def test_d_missing_decision_fails_closed(tmp_path: Path) -> None:
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(decision_result=""),
    )
    assert result.capability_result in {RESULT_BLOCKED, RESULT_ERROR}
    assert result.failure_class == FailureClassV0.DECISION_MISSING.value


def test_e_missing_risk_fails_closed(tmp_path: Path) -> None:
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(risk_sizing_result=""),
    )
    assert result.failure_class == FailureClassV0.RISK_MISSING.value


def test_f_identity_contradiction_fails_closed(tmp_path: Path) -> None:
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        output_path="ev",
        overwrite_evidence=True,
        identity_overrides={"orders_allowed": True},
        cycle_runner=lambda **kwargs: _pass_cycle(),
    )
    assert result.capability_result == RESULT_BLOCKED
    assert result.failure_class == FailureClassV0.IDENTITY_INVALID.value


def test_g_btc_rejected(tmp_path: Path) -> None:
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        instrument_id="BTC-USD_UM_XPERP",
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(
            terminal_status="BLOCKED",
            blockers=("bitcoin_instruments_excluded",),
            decision_result="HOLD",
            risk_sizing_result="NONE",
        ),
    )
    assert result.capability_result == RESULT_BLOCKED
    assert result.failure_class == FailureClassV0.IDENTITY_INVALID.value


def test_h_spot_rejected(tmp_path: Path) -> None:
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        instrument_id="ETH-USDT-SPOT",
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(
            terminal_status="BLOCKED",
            blockers=("spot_instruments_excluded",),
            decision_result="HOLD",
            risk_sizing_result="NONE",
        ),
    )
    assert result.capability_result == RESULT_BLOCKED


def test_i_non_okx_venue_rejected(tmp_path: Path) -> None:
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        venue="KRAKEN",
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(),
    )
    assert result.capability_result == RESULT_BLOCKED
    assert "VENUE_NOT_OKX" in result.reason_codes


def test_j_network_capable_dependency_rejected(tmp_path: Path) -> None:
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        network_runtime_enabled=True,
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(),
    )
    assert result.capability_result == RESULT_BLOCKED
    assert "NETWORK_RUNTIME_ENABLED" in result.reason_codes


def test_k_order_capable_dependency_rejected(tmp_path: Path) -> None:
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        order_submission_enabled=True,
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(),
    )
    assert result.capability_result == RESULT_BLOCKED
    assert result.failure_class == FailureClassV0.EXECUTION_BOUNDARY_VIOLATION.value


def test_l_scheduler_activation_config_rejected(tmp_path: Path) -> None:
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        scheduler_enabled=True,
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(),
    )
    assert result.capability_result == RESULT_BLOCKED
    assert "SCHEDULER_OR_DAEMON_ENABLED" in result.reason_codes


def test_m_invalid_lifecycle_transition_rejected() -> None:
    with pytest.raises(Step29UOfflineCapabilityError):
        transition_state_v0(current=SessionStateV0.CREATED, target=SessionStateV0.COMPLETED)
    for name in FORBIDDEN_STATE_NAMES:
        assert name not in {s.name for s in SessionStateV0}
    assert SessionStateV0.READY in ALLOWED_TRANSITIONS[SessionStateV0.VALIDATING]


def test_n_reconciliation_mismatch_rejected(tmp_path: Path) -> None:
    bad = _pass_cycle(direction="LONG")
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: bad,
    )
    assert result.capability_result in {RESULT_BLOCKED, RESULT_ERROR}
    assert result.failure_class in {
        FailureClassV0.RECONCILIATION_MISMATCH.value,
        FailureClassV0.DECISION_INVALID.value,
    }


def test_o_evidence_path_escape_rejected(tmp_path: Path) -> None:
    with pytest.raises(Step29UOfflineCapabilityError):
        resolve_evidence_dir(repo_root=tmp_path, output_path="../escape")
    with pytest.raises(Step29UOfflineCapabilityError):
        resolve_evidence_dir(repo_root=tmp_path, output_path="/tmp/abs")


def test_p_malformed_evidence_rejected(tmp_path: Path) -> None:
    d = tmp_path / "ev"
    d.mkdir()
    (d / "evidence_manifest.sha256").write_text("deadbeef  capability_result.json\n")
    (d / "capability_result.json").write_text("{not-json", encoding="utf-8")
    ok, reasons = verify_capability_evidence_v0(evidence_dir=d)
    assert ok is False
    assert "RESULT_MALFORMED" in reasons


def test_q_digest_tampering_detected(tmp_path: Path) -> None:
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(),
    )
    assert result.capability_result == RESULT_PASS
    evidence_dir = tmp_path / "ev"
    target = evidence_dir / "capability_result.json"
    target.write_text(target.read_text(encoding="utf-8") + " ", encoding="utf-8")
    ok, reasons = verify_capability_evidence_v0(evidence_dir=evidence_dir)
    assert ok is False
    assert any(r.startswith("DIGEST_MISMATCH:") for r in reasons)


def test_r_repeated_bounded_cycles_deterministic(tmp_path: Path) -> None:
    a = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=3,
        output_path="ev_a",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(),
    )
    b = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=3,
        output_path="ev_b",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(),
    )
    assert a.capability_result == b.capability_result == RESULT_PASS
    assert (
        [c.direction for c in a.cycles]
        == [c.direction for c in b.cycles]
        == [
            "HOLD",
            "HOLD",
            "HOLD",
        ]
    )


def test_s_operator_entrypoint_exit_codes(tmp_path: Path) -> None:
    out = tmp_path / "cli_ev"
    out.mkdir()
    # Copy minimal: run CLI with repo_root=REPO_ROOT but evidence under tmp via relative path
    # Use REPO_ROOT and write under out/ops path inside tmp by setting repo-root=tmp and
    # ensuring cycle_runner isn't available — CLI uses real cycle. Real cycle needs full repo.
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--repo-root",
            str(REPO_ROOT),
            "--cycle-count",
            "1",
            "--output-path",
            "out/ops/step29u_test_cli_evidence",
            "--overwrite-evidence",
            "--source-git-sha",
            GIT_SHA,
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "CAPABILITY_RESULT=STEP_29U_OFFLINE_CAPABILITY_PASS" in proc.stdout

    blocked = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--repo-root",
            str(REPO_ROOT),
            "--cycle-count",
            "1",
            "--output-path",
            "out/ops/step29u_test_cli_blocked",
            "--overwrite-evidence",
            "--orders",
            "--source-git-sha",
            GIT_SHA,
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert blocked.returncode == 2


def test_t_evidence_reader_verifier_passes_on_valid_output(tmp_path: Path) -> None:
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(),
    )
    ok, reasons = verify_capability_evidence_v0(evidence_dir=tmp_path / "ev")
    assert ok is True
    assert reasons == ()
    assert result.evidence_manifest_sha256
    manifest = (tmp_path / "ev" / "evidence_manifest.sha256").read_text(encoding="utf-8")
    assert hashlib.sha256(manifest.encode("utf-8")).hexdigest() == result.evidence_manifest_sha256


def test_persisted_pass_result_has_verified_offline_true(tmp_path: Path) -> None:
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(),
    )
    assert result.capability_result == RESULT_PASS
    assert result.step_29u_verified_offline is True
    on_disk = json.loads((tmp_path / "ev" / "capability_result.json").read_text(encoding="utf-8"))
    assert on_disk["capability_result"] == RESULT_PASS
    assert on_disk["step_29u_verified_offline"] is True
    assert on_disk["step_29u_implemented"] is True
    assert on_disk["step_29u_bound_offline"] is True
    assert on_disk["step_29u_activated"] is False


def test_pass_cannot_coexist_with_verified_offline_false_on_disk(tmp_path: Path) -> None:
    from src.ops.step_29u_offline_capability_v0 import write_capability_evidence_manifest_v0

    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(),
    )
    assert result.capability_result == RESULT_PASS
    path = tmp_path / "ev" / "capability_result.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["step_29u_verified_offline"] = False
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifacts = {
        name: hashlib.sha256((tmp_path / "ev" / name).read_bytes()).hexdigest()
        for name in (
            "capability_result.json",
            "cycles.json",
            "lifecycle_transitions.json",
            "mode_identity.json",
        )
    }
    write_capability_evidence_manifest_v0(evidence_dir=tmp_path / "ev", artifacts=artifacts)
    ok, reasons = verify_capability_evidence_v0(evidence_dir=tmp_path / "ev")
    assert ok is False
    assert "PASS_WITHOUT_VERIFIED_OFFLINE" in reasons


def test_manifest_covers_final_persisted_digests_after_writeback(tmp_path: Path) -> None:
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(),
    )
    assert result.capability_result == RESULT_PASS
    evidence_dir = tmp_path / "ev"
    for line in (
        (evidence_dir / "evidence_manifest.sha256").read_text(encoding="utf-8").splitlines()
    ):
        if not line.strip():
            continue
        digest, name = line.split()
        actual = hashlib.sha256((evidence_dir / name).read_bytes()).hexdigest()
        assert actual == digest
    on_disk = json.loads((evidence_dir / "capability_result.json").read_text(encoding="utf-8"))
    assert on_disk["step_29u_verified_offline"] is True
    expected = hashlib.sha256((evidence_dir / "capability_result.json").read_bytes()).hexdigest()
    listed = {
        name: digest
        for digest, name in (
            line.split()
            for line in (evidence_dir / "evidence_manifest.sha256").read_text().splitlines()
            if line.strip()
        )
    }
    assert listed["capability_result.json"] == expected


def test_failed_verifier_cannot_produce_final_pass(tmp_path: Path) -> None:
    from src.ops.step_29u_offline_capability_v0 import write_capability_evidence_manifest_v0

    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(),
    )
    assert result.capability_result == RESULT_PASS
    bad = json.loads((tmp_path / "ev" / "capability_result.json").read_text(encoding="utf-8"))
    bad["capability_result"] = RESULT_PASS
    bad["step_29u_verified_offline"] = False
    (tmp_path / "ev" / "capability_result.json").write_text(
        json.dumps(bad, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    artifacts = {
        name: hashlib.sha256((tmp_path / "ev" / name).read_bytes()).hexdigest()
        for name in (
            "capability_result.json",
            "cycles.json",
            "lifecycle_transitions.json",
            "mode_identity.json",
        )
    }
    write_capability_evidence_manifest_v0(evidence_dir=tmp_path / "ev", artifacts=artifacts)
    ok, reasons = verify_capability_evidence_v0(evidence_dir=tmp_path / "ev")
    assert ok is False
    assert "PASS_WITHOUT_VERIFIED_OFFLINE" in reasons


def test_u_readiness_producer_still_cannot_bind_or_activate() -> None:
    text = READINESS.read_text(encoding="utf-8")
    assert "READINESS_PRODUCER_CANNOT_BIND_STEP_29U=true" in text
    assert "READINESS_PRODUCER_CANNOT_IMPLEMENT_STEP_29U=true" in text
    assert "READINESS_PRODUCER_CANNOT_ACTIVATE_STEP_29U=true" in text


def test_v_no_second_authority_owner() -> None:
    identity = build_mode_identity_v0(
        instrument_id=PRODUCTION_INSTRUMENT_ID, source_git_sha=GIT_SHA
    )
    assert validate_mode_identity_v0(identity) == ()
    assert LIFECYCLE_OWNER == "ops.step_29u_offline_capability_v0"


def test_w_preserved_inventory_contract_consistent() -> None:
    text = INVENTORY.read_text(encoding="utf-8")
    assert "STEP_29U_BINDING_IMPLEMENTATION_INVENTORY_V0=true" in text
    assert "STEP_29U_ACTIVATION_PASS=false" in text
    assert "CANONICAL_STEP_29U_ABSENT=OPEN_INTENTIONAL_ACTIVATION_PREREQUISITE" in text
    assert "STEP_29U_IMPLEMENTED=true" in text
    assert "STEP_29U_BOUND_OFFLINE=true" in text
    assert "ops.step_29u_offline_capability_v0" in text


def test_x_no_import_from_forbidden_legacy_shadow_surfaces() -> None:
    src = (REPO_ROOT / "src/ops/step_29u_offline_capability_v0/__init__.py").read_text(
        encoding="utf-8"
    )
    import_lines = [
        line.strip()
        for line in src.splitlines()
        if line.strip().startswith("import ") or line.strip().startswith("from ")
    ]
    joined = "\n".join(import_lines)
    for surface in FORBIDDEN_IMPORT_SURFACES:
        assert surface not in joined
    assert "from src.orders.shadow" not in joined
    assert "from src.live.shadow_session" not in joined
    assert "import src.orders.shadow" not in joined
    assert FORBIDDEN_IMPORT_SURFACES  # registry remains explicit


def test_y_no_runtime_scheduler_network_order_side_effect(tmp_path: Path) -> None:
    result = run_step_29u_offline_capability_v0(
        repo_root=tmp_path,
        source_git_sha=GIT_SHA,
        cycle_count=1,
        output_path="ev",
        overwrite_evidence=True,
        cycle_runner=lambda **kwargs: _pass_cycle(),
    )
    assert result.runtime_activated is False
    assert result.scheduler_activated is False
    assert result.network_runtime_used is False
    assert result.orders_created is False
    assert result.orders_submitted is False
    assert result.capital_changed is False
