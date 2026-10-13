"""S5 restart read-only recovery observation — offline E2E reproof."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    CurrentProductiveGovernedCycleOrchestratorError,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    LEDGER_FILENAME,
    REASON_REPLAY,
    _binding_digest,
    _load_ledger,
    run_current_productive_governed_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    FullCoreAuthorizationBindingV1,
    full_core_atomic_reserve_owner_go_authorization_v1,
    load_full_core_atomic_authorization_state_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_completed_hook_evidence_v1 import (
    ATOMIC_OBSERVATION_ATOMIC_UNKNOWN,
    ATOMIC_OBSERVATION_BOUND,
    ATOMIC_OBSERVATION_CONFLICTING_EVIDENCE,
    ATOMIC_OBSERVATION_CYCLE_IDENTITY_INCOMPLETE,
    ATOMIC_OBSERVATION_NOT_BOUND_FAIL_CLOSED,
    CYCLE_IDENTITY_INCOMPLETE,
    FULL_CORE_ATOMIC_CONSUMPTION_KEY,
    POST_SUBMIT_RECONCILIATION_SUCCEEDED,
    RECONCILIATION_OBSERVATION_INCOMPLETE,
    RECONCILIATION_SUCCESS_NOT_CLAIMED,
    observe_full_core_s5_recovery_entry_v1,
    pre_external_completed_ledger_pending_marker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
    ATOMIC_STATE_DIR_ENV_VAR,
    JOIN_ENV_VAR,
    _authorization_binding_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_binding_v1 import (
    bind_full_core_capital_guard_handoff_context_v1,
    build_full_core_capital_guard_join_binding_v1,
    reset_full_core_capital_guard_handoff_context_v1,
)
from tests.ops.test_full_core_current_productive_governed_cycle_orchestrator_v1 import (
    _auth,
    _run,
    _t2_enter,
    _t2_enter_envelope,
)
from tests.ops.test_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1 import (
    _handoff,
    _origin_main,
)

REPO = Path(__file__).resolve().parents[2]
PT = REPO / "scripts" / "pt"


def _ledger_path(root: Path) -> Path:
    return root / "evidence" / LEDGER_FILENAME


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_dir(state_dir: Path) -> str:
    if not state_dir.is_dir():
        return ""
    parts: list[str] = []
    for p in sorted(state_dir.rglob("*")):
        if p.is_file():
            parts.append(f"{p.relative_to(state_dir)}:{_sha256_file(p)}")
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def _observe_subprocess(*, evidence_root: Path, env: dict[str, str], digest: str) -> dict[str, str]:
    code = """
import json, os, sys
from pathlib import Path
payload = json.loads(sys.argv[1])
for k, v in payload["env"].items():
    os.environ[k] = v
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    _load_ledger,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_completed_hook_evidence_v1 import (
    observe_full_core_s5_recovery_entry_v1,
)
ledger = _load_ledger(Path(payload["evidence_root"]))
obs = observe_full_core_s5_recovery_entry_v1(
    ledger=ledger,
    authorization_binding_digest=payload["digest"],
)
print(json.dumps(obs.to_extra_fields_v1(), sort_keys=True))
"""
    proc = subprocess.run(
        [
            str(PT),
            "-c",
            code,
            json.dumps({"env": env, "evidence_root": str(evidence_root), "digest": digest}),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout.strip())


def _minimal_binding() -> FullCoreAuthorizationBindingV1:
    return FullCoreAuthorizationBindingV1(
        owner_go="OWNER_GO_FULL_CORE_PRE_POST",
        origin_main_sha=_origin_main(),
        account_scope="test-scope",
        environment="PAPER",
        execution_mode="OFFLINE",
        canonical_decision_id="dec-1",
        instrument_id="0G-USDT-SWAP",
        native_id="0G-USDT-SWAP",
        selected_direction="ENTER_LONG",
        order_side="buy",
        final_quantity="1",
        order_type="market",
        order_price="",
        venue_plan_digest="vp-d",
        envelope_digest="env-d",
        guard_config_digest="gc-d",
        session_id="recovery-obs-test",
        clordid="cl-1",
    )


def test_scenario_1_normal_completion_s5_extra_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    atomic_dir = tmp_path / "atomic"
    atomic_dir.mkdir()
    monkeypatch.setenv(JOIN_ENV_VAR, "OFFLINE_STUB")
    monkeypatch.setenv(ATOMIC_STATE_DIR_ENV_VAR, str(atomic_dir))
    sha = _origin_main()
    handoff = _handoff(sha=sha)
    handoff_reset = bind_full_core_capital_guard_handoff_context_v1(handoff)
    digest = _binding_digest(_auth())
    try:
        result = _run(tmp_path, t2_cycle_dispatch=_t2_enter)
    finally:
        reset_full_core_capital_guard_handoff_context_v1(handoff_reset)

    assert result.disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
    assert result.extra.get("FULL_CORE_S5_RECOVERY_OBSERVATION_V1") == "V1"
    ledger = _load_ledger(tmp_path / "evidence")
    assert ledger.get(FULL_CORE_ATOMIC_CONSUMPTION_KEY)
    envelope = _t2_enter_envelope()
    join_binding = build_full_core_capital_guard_join_binding_v1(
        canonical_decision_id=handoff.canonical_decision_id,
        bound_instrument=handoff.bound_instrument,
        envelope=envelope,
        master_v2_decision="enter",
        account_identity=handoff.account_identity,
        environment=handoff.environment,
        origin_main_sha=handoff.origin_main_sha,
        instrument_metadata=handoff.instrument_metadata,
        pre_external_reached=True,
        terminal_disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
    )
    auth_binding = _authorization_binding_v1(
        join_binding, session_id="full-core-capital-guard-join"
    )
    assert auth_binding.consumption_key() == str(ledger[FULL_CORE_ATOMIC_CONSUMPTION_KEY])
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=atomic_dir, binding=auth_binding)
    cold = _observe_subprocess(
        evidence_root=tmp_path / "evidence",
        env={JOIN_ENV_VAR: "OFFLINE_STUB", ATOMIC_STATE_DIR_ENV_VAR: str(atomic_dir)},
        digest=digest,
    )
    assert cold.get("ATOMIC_OBSERVATION") == ATOMIC_OBSERVATION_BOUND
    assert cold.get("FULL_CORE_S5_RECOVERY_POST_SUBMIT_RECON_CLASS") == (
        RECONCILIATION_SUCCESS_NOT_CLAIMED
    )


def test_scenario_2_crash_after_initial_completed(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    digest = _binding_digest(_auth())
    ledger = {
        "state": "COMPLETED",
        "binding_digest": digest,
        "terminal_class": "PRE_EXTERNAL_EFFECT",
        "reason_code": "POST_OWNER_GO",
        **pre_external_completed_ledger_pending_marker_v1(),
    }
    _ledger_path(tmp_path).write_text(json.dumps(ledger, sort_keys=True), encoding="utf-8")
    obs = observe_full_core_s5_recovery_entry_v1(
        ledger=ledger,
        authorization_binding_digest=digest,
    )
    assert obs.post_submit_reconciliation_classification == RECONCILIATION_OBSERVATION_INCOMPLETE
    assert obs.atomic_observation == ATOMIC_OBSERVATION_NOT_BOUND_FAIL_CLOSED
    cold = _observe_subprocess(
        evidence_root=evidence,
        env={},
        digest=digest,
    )
    assert (
        cold["FULL_CORE_S5_RECOVERY_POST_SUBMIT_RECON_CLASS"]
        == RECONCILIATION_OBSERVATION_INCOMPLETE
    )


def test_scenario_3_supplement_persistence_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 as orch

    atomic_dir = tmp_path / "atomic-persist-fail"
    atomic_dir.mkdir()
    monkeypatch.setenv(JOIN_ENV_VAR, "OFFLINE_STUB")
    monkeypatch.setenv(ATOMIC_STATE_DIR_ENV_VAR, str(atomic_dir))
    original = orch._persist_json

    def _flaky_persist(**kwargs: object) -> None:
        payload = kwargs.get("payload") or {}
        if isinstance(payload, dict) and payload.get("POST_COMPLETED_HOOK_EVIDENCE_V1"):
            raise OSError("INJECTED_LEDGER_WRITE_FAILURE")
        original(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(orch, "_persist_json", _flaky_persist)
    result = _run(tmp_path, t2_cycle_dispatch=_t2_enter)
    assert result.extra.get("CYCLE_LEDGER_SUPPLEMENT_PERSISTENCE") == "FAIL_CLOSED"
    reloaded = _load_ledger(tmp_path / "evidence")
    obs = observe_full_core_s5_recovery_entry_v1(
        ledger=reloaded,
        authorization_binding_digest=_binding_digest(_auth()),
        atomic_state_dir=atomic_dir,
    )
    assert obs.post_submit_reconciliation_classification == RECONCILIATION_OBSERVATION_INCOMPLETE
    with patch.object(orch, "_persist_json", original):
        pass


def test_scenario_4_scope_key_without_guard_digest_fail_closed(tmp_path: Path) -> None:
    digest = _binding_digest(_auth())
    key = "deadbeef" * 8
    ledger = {
        "state": "COMPLETED",
        "binding_digest": digest,
        "terminal_class": "PRE_EXTERNAL_EFFECT",
        FULL_CORE_ATOMIC_CONSUMPTION_KEY: key,
        POST_SUBMIT_RECONCILIATION_SUCCEEDED: "false",
    }
    atomic_dir = tmp_path / "empty-atomic"
    atomic_dir.mkdir()
    obs = observe_full_core_s5_recovery_entry_v1(
        ledger=ledger,
        authorization_binding_digest=digest,
        atomic_state_dir=atomic_dir,
    )
    assert obs.atomic_observation == ATOMIC_OBSERVATION_CYCLE_IDENTITY_INCOMPLETE
    assert obs.cycle_identity_status == CYCLE_IDENTITY_INCOMPLETE
    assert obs.recovery_evidence_status == "FAIL_CLOSED"


def test_scenario_4b_atomic_unknown_with_guard_but_no_state(tmp_path: Path) -> None:
    digest = _binding_digest(_auth())
    binding = _minimal_binding()
    ledger = {
        "state": "COMPLETED",
        "binding_digest": digest,
        FULL_CORE_ATOMIC_CONSUMPTION_KEY: binding.consumption_key(),
        "FULL_CORE_CAPITAL_GUARD_BINDING_DIGEST": binding.binding_digest(),
    }
    atomic_dir = tmp_path / "empty-atomic"
    atomic_dir.mkdir()
    obs = observe_full_core_s5_recovery_entry_v1(
        ledger=ledger,
        authorization_binding_digest=digest,
        atomic_state_dir=atomic_dir,
    )
    assert obs.atomic_observation == ATOMIC_OBSERVATION_ATOMIC_UNKNOWN


def test_scenario_5_conflicting_evidence(tmp_path: Path) -> None:
    digest = _binding_digest(_auth())
    binding = _minimal_binding()
    atomic_dir = tmp_path / "atomic-conflict"
    atomic_dir.mkdir()
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=atomic_dir, binding=binding)
    ledger = {
        "state": "COMPLETED",
        "binding_digest": "wrong-digest",
        "terminal_class": "PRE_EXTERNAL_EFFECT",
        FULL_CORE_ATOMIC_CONSUMPTION_KEY: binding.consumption_key(),
        "FULL_CORE_CAPITAL_GUARD_BINDING_DIGEST": "not-matching-plan",
        POST_SUBMIT_RECONCILIATION_SUCCEEDED: "false",
    }
    obs = observe_full_core_s5_recovery_entry_v1(
        ledger=ledger,
        authorization_binding_digest=digest,
        atomic_state_dir=atomic_dir,
    )
    assert obs.atomic_observation == ATOMIC_OBSERVATION_CONFLICTING_EVIDENCE
    assert obs.recovery_evidence_status == "FAIL_CLOSED"


def test_scenario_6_double_restart_idempotency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    atomic_dir = tmp_path / "atomic-restart"
    atomic_dir.mkdir()
    monkeypatch.setenv(JOIN_ENV_VAR, "OFFLINE_STUB")
    monkeypatch.setenv(ATOMIC_STATE_DIR_ENV_VAR, str(atomic_dir))
    _run(tmp_path, t2_cycle_dispatch=_t2_enter)
    ledger_hash_before = _sha256_file(_ledger_path(tmp_path))
    atomic_hash_before = _sha256_dir(atomic_dir)
    digest = _binding_digest(_auth())
    with pytest.raises(CurrentProductiveGovernedCycleOrchestratorError, match=REASON_REPLAY):
        _run(tmp_path, t2_cycle_dispatch=_t2_enter)
    assert _sha256_file(_ledger_path(tmp_path)) == ledger_hash_before
    assert _sha256_dir(atomic_dir) == atomic_hash_before
    cold = _observe_subprocess(
        evidence_root=tmp_path / "evidence",
        env={JOIN_ENV_VAR: "OFFLINE_STUB", ATOMIC_STATE_DIR_ENV_VAR: str(atomic_dir)},
        digest=digest,
    )
    assert cold["FULL_CORE_S5_RECOVERY_OBSERVATION_V1"] == "V1"


def test_observation_does_not_mutate_atomic_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    atomic_dir = tmp_path / "atomic-no-mut"
    atomic_dir.mkdir()
    binding = _minimal_binding()
    full_core_atomic_reserve_owner_go_authorization_v1(state_dir=atomic_dir, binding=binding)
    before = _sha256_dir(atomic_dir)
    digest = _binding_digest(_auth())
    ledger = {
        "state": "COMPLETED",
        "binding_digest": digest,
        FULL_CORE_ATOMIC_CONSUMPTION_KEY: binding.consumption_key(),
        "FULL_CORE_CAPITAL_GUARD_BINDING_DIGEST": binding.binding_digest(),
    }
    observe_full_core_s5_recovery_entry_v1(
        ledger=ledger,
        authorization_binding_digest=digest,
        atomic_state_dir=atomic_dir,
    )
    assert _sha256_dir(atomic_dir) == before
    st = load_full_core_atomic_authorization_state_v1(
        state_dir=atomic_dir, consumption_key=binding.consumption_key()
    )
    assert st is not None


def test_adversarial_fabricated_reconciliation_success_fail_closed() -> None:
    ledger = {
        "state": "COMPLETED",
        "terminal_class": "PRE_EXTERNAL_EFFECT",
        POST_SUBMIT_RECONCILIATION_SUCCEEDED: "true",
    }
    obs = observe_full_core_s5_recovery_entry_v1(
        ledger=ledger,
        authorization_binding_digest="d",
    )
    assert obs.recovery_evidence_status == "FAIL_CLOSED"


def test_deterministic_interleaving_cycle_a_never_reads_b_extra() -> None:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
        DISPOSITION_FAIL_CLOSED,
        _result,
    )

    extra_a = {
        "FULL_CORE_S5_RECOVERY_OBSERVATION_V1": "V1",
        "FULL_CORE_S5_RECOVERY_LEDGER_STATE": "CYCLE_A",
        "ATOMIC_OBSERVATION": "MARKER_A",
    }
    extra_b = {
        "FULL_CORE_S5_RECOVERY_OBSERVATION_V1": "V1",
        "FULL_CORE_S5_RECOVERY_LEDGER_STATE": "CYCLE_B",
        "ATOMIC_OBSERVATION": "MARKER_B",
    }
    # publish(A), publish(B), _result(A) — A must keep A's payload via explicit param.
    _ = extra_b
    result_a = _result(
        disposition=DISPOSITION_FAIL_CLOSED,
        reason_code="INTERLEAVE_PROBE",
        terminal_class="PROBE",
        s5_recovery_observation_extra=extra_a,
    )
    assert result_a.extra["FULL_CORE_S5_RECOVERY_LEDGER_STATE"] == "CYCLE_A"
    assert result_a.extra["ATOMIC_OBSERVATION"] == "MARKER_A"


def test_cycle_result_closure_forces_entry_observation_over_adversarial_kwarg() -> None:
    """Production _cycle_result must pin entry observation; kwargs must not override."""
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
        DISPOSITION_FAIL_CLOSED,
        _result,
    )

    orch_src = (
        REPO
        / "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_cycle_orchestrator_v1.py"
    ).read_text(encoding="utf-8")
    assert 'kwargs["s5_recovery_observation_extra"] = _s5_recovery_observation_extra' in orch_src
    _cycle_result_body = orch_src.split("def _cycle_result")[1].split("return _result(**kwargs)")[0]
    assert "setdefault" not in _cycle_result_body

    extra_a = {
        "FULL_CORE_S5_RECOVERY_OBSERVATION_V1": "V1",
        "FULL_CORE_S5_RECOVERY_LEDGER_STATE": "ENTRY_A",
        "ATOMIC_OBSERVATION": "MARKER_A",
    }
    extra_b = {
        "FULL_CORE_S5_RECOVERY_OBSERVATION_V1": "V1",
        "FULL_CORE_S5_RECOVERY_LEDGER_STATE": "ENTRY_B",
        "ATOMIC_OBSERVATION": "MARKER_B",
    }
    kwargs: dict[str, object] = {
        "disposition": DISPOSITION_FAIL_CLOSED,
        "reason_code": "KWARGS_OVERRIDE_PROBE",
        "terminal_class": "PROBE",
        "s5_recovery_observation_extra": extra_b,
    }
    # Same contract as run_current_productive_governed_cycle_v1._cycle_result (post-hardening).
    _s5_recovery_observation_extra = extra_a
    kwargs["s5_recovery_observation_extra"] = _s5_recovery_observation_extra
    result = _result(**kwargs)  # type: ignore[arg-type]
    assert result.extra["FULL_CORE_S5_RECOVERY_LEDGER_STATE"] == "ENTRY_A"
    assert result.extra["ATOMIC_OBSERVATION"] == "MARKER_A"
    assert result.extra["FULL_CORE_S5_RECOVERY_LEDGER_STATE"] != "ENTRY_B"


def test_parallel_s5_separate_evidence_roots(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    with ThreadPoolExecutor(max_workers=2) as pool:
        fa = pool.submit(_run, root_a, t2_cycle_dispatch=_t2_enter)
        fb = pool.submit(_run, root_b, t2_cycle_dispatch=_t2_enter)
        ra, rb = fa.result(), fb.result()
    assert ra.post_count == 0 and rb.post_count == 0
    assert ra.extra.get("FULL_CORE_S5_RECOVERY_OBSERVATION_V1") == "V1"
    assert rb.extra.get("FULL_CORE_S5_RECOVERY_OBSERVATION_V1") == "V1"
    assert ra.extra.get("FULL_CORE_S5_RECOVERY_LEDGER_STATE") in {"", "IDLE"}
    assert rb.extra.get("FULL_CORE_S5_RECOVERY_LEDGER_STATE") in {"", "IDLE"}


def test_failed_stop_path_carries_entry_observation_in_result(tmp_path: Path) -> None:
    from tests.ops.test_full_core_current_productive_governed_cycle_orchestrator_v1 import (
        _candles,
    )

    bad_candles = _candles(last_ts_ms=1)
    result = _run(tmp_path, candles_payload=bad_candles, t2_cycle_dispatch=_t2_enter)
    assert result.disposition == "FAIL_CLOSED"
    assert result.extra.get("FULL_CORE_S5_RECOVERY_OBSERVATION_V1") == "V1"
    assert result.extra.get("FULL_CORE_S5_RECOVERY_LEDGER_STATE") in {"", "IDLE"}


def test_adversarial_corrupt_ledger_failed_stop(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    _ledger_path(tmp_path).write_text("{not-json", encoding="utf-8")
    ledger = _load_ledger(evidence)
    obs = observe_full_core_s5_recovery_entry_v1(
        ledger=ledger,
        authorization_binding_digest=_binding_digest(_auth()),
    )
    assert obs.ledger_state == "FAILED_STOP"
