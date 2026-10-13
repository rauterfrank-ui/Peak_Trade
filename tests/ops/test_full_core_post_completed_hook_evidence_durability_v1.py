"""Offline durability: post-COMPLETED lifecycle/capital-guard hook evidence."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    LEDGER_FILENAME,
    _load_ledger,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    STATE_HALTED_UNRESOLVED,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1 import (
    CycleLifecycleWiringMode,
    CycleSubmitInjectionKind,
    bind_full_core_cycle_lifecycle_wiring_invocation_v1,
    reset_full_core_cycle_lifecycle_wiring_invocation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_completed_hook_evidence_v1 import (
    LIFECYCLE_FAIL_CLOSED_NOT_RECONCILIATION_SUCCESS,
    LIFECYCLE_OBSERVATION_NOT_INVOKED,
    POST_SUBMIT_RECONCILIATION_SUCCEEDED,
    POST_SUBMIT_RECONCILIATION_SUCCEEDED_VALUE,
    RECONCILIATION_OBSERVATION_INCOMPLETE,
    RECONCILIATION_SUCCESS_NOT_CLAIMED,
    classify_post_submit_reconciliation_observation_v1,
    merge_allowlisted_post_completed_hook_claims_v1,
    pre_external_completed_ledger_pending_marker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_binding_v1 import (
    bind_full_core_capital_guard_handoff_context_v1,
    reset_full_core_capital_guard_handoff_context_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
    ATOMIC_STATE_DIR_ENV_VAR,
    JOIN_ENV_VAR,
)
from tests.ops.test_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1 import (
    _envelope,
    _handoff,
    _origin_main,
    _wiring_request,
)
from tests.ops.test_full_core_current_productive_governed_cycle_orchestrator_v1 import (
    _run,
    _t2_enter,
)


def _ledger(tmp_path: Path) -> dict:
    return json.loads((tmp_path / "evidence" / LEDGER_FILENAME).read_text(encoding="utf-8"))


def test_completed_then_lifecycle_fail_closed_persisted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.ops.full_core_live_path_composition_root_v1 import (
        full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1 as wiring_mod,
    )

    sha = _origin_main()
    atomic_dir = tmp_path / "atomic"
    atomic_dir.mkdir()
    monkeypatch.setenv(JOIN_ENV_VAR, "OFFLINE_STUB")
    monkeypatch.setenv(ATOMIC_STATE_DIR_ENV_VAR, str(atomic_dir))
    handoff_reset = bind_full_core_capital_guard_handoff_context_v1(_handoff(sha=sha))
    wiring_req = _wiring_request(
        sha=sha,
        submit_kind=CycleSubmitInjectionKind.NOT_ATTEMPTED,
        state_dir=atomic_dir,
    )
    wiring_reset = bind_full_core_cycle_lifecycle_wiring_invocation_v1(request=wiring_req)

    def _run_crash(**_kwargs: object) -> None:
        raise RuntimeError("DURABILITY_INJECTED_LIFECYCLE_FAIL")

    monkeypatch.setattr(
        wiring_mod,
        "run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1",
        _run_crash,
    )
    try:
        result = _run(tmp_path, t2_cycle_dispatch=_t2_enter)
    finally:
        reset_full_core_cycle_lifecycle_wiring_invocation_v1(wiring_reset)
        reset_full_core_capital_guard_handoff_context_v1(handoff_reset)

    assert result.disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
    ledger = _ledger(tmp_path)
    assert ledger["FULL_CORE_CYCLE_LIFECYCLE_WIRING"] == "FAIL_CLOSED"
    assert (
        ledger[POST_SUBMIT_RECONCILIATION_SUCCEEDED] == POST_SUBMIT_RECONCILIATION_SUCCEEDED_VALUE
    )
    assert "DURABILITY_INJECTED_LIFECYCLE_FAIL" in str(
        ledger.get("FULL_CORE_CYCLE_LIFECYCLE_WIRING_EXCEPTION_MESSAGE") or ""
    )


def test_restart_reload_shows_lifecycle_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    test_completed_then_lifecycle_fail_closed_persisted(tmp_path, monkeypatch)
    reloaded = _load_ledger(tmp_path / "evidence")
    assert reloaded["FULL_CORE_CYCLE_LIFECYCLE_WIRING"] == "FAIL_CLOSED"


def test_unexpected_lifecycle_exception_no_crash_no_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    test_completed_then_lifecycle_fail_closed_persisted(tmp_path, monkeypatch)
    ledger = _ledger(tmp_path)
    assert ledger.get("FULL_CORE_CYCLE_LIFECYCLE_GHV_FORWARD") is None
    assert ledger.get("FULL_CORE_CYCLE_LIFECYCLE_RECON_OUTCOME") is None


def test_closure_claims_preserve_lifecycle_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.ops.full_core_live_path_composition_root_v1.full_core_post_completed_hook_evidence_v1 import (
        extract_allowlisted_lifecycle_claims_v1,
    )

    test_completed_then_lifecycle_fail_closed_persisted(tmp_path, monkeypatch)
    ledger = _ledger(tmp_path)
    cycle_extra = {str(k): str(v) for k, v in ledger.items() if isinstance(v, str)}
    extracted = extract_allowlisted_lifecycle_claims_v1(cycle_extra)
    assert extracted.get("FULL_CORE_CYCLE_LIFECYCLE_WIRING") == "FAIL_CLOSED"


def test_lifecycle_disabled_not_invoked_in_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from dataclasses import replace

    sha = _origin_main()
    atomic_dir = tmp_path / "atomic-disabled"
    atomic_dir.mkdir()
    monkeypatch.setenv(JOIN_ENV_VAR, "OFFLINE_STUB")
    monkeypatch.setenv(ATOMIC_STATE_DIR_ENV_VAR, str(atomic_dir))
    handoff_reset = bind_full_core_capital_guard_handoff_context_v1(_handoff(sha=sha))
    disabled_req = replace(
        _wiring_request(
            sha=sha,
            submit_kind=CycleSubmitInjectionKind.NOT_ATTEMPTED,
            state_dir=atomic_dir,
        ),
        mode=CycleLifecycleWiringMode.DISABLED,
    )
    wiring_reset = bind_full_core_cycle_lifecycle_wiring_invocation_v1(request=disabled_req)
    try:
        _run(tmp_path, t2_cycle_dispatch=_t2_enter)
    finally:
        reset_full_core_cycle_lifecycle_wiring_invocation_v1(wiring_reset)
        reset_full_core_capital_guard_handoff_context_v1(handoff_reset)
    ledger = _ledger(tmp_path)
    assert ledger["FULL_CORE_CYCLE_LIFECYCLE_WIRING"] == "DISABLED_IN_CONTEXT"
    assert ledger.get("FULL_CORE_CYCLE_LIFECYCLE_RECON_OUTCOME") is None


def test_default_no_invocation_not_invoked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    atomic_dir = tmp_path / "atomic-default"
    atomic_dir.mkdir()
    monkeypatch.setenv(JOIN_ENV_VAR, "OFFLINE_STUB")
    monkeypatch.setenv(ATOMIC_STATE_DIR_ENV_VAR, str(atomic_dir))
    _run(tmp_path, t2_cycle_dispatch=_t2_enter)
    ledger = _ledger(tmp_path)
    assert ledger["FULL_CORE_CYCLE_LIFECYCLE_WIRING"] == LIFECYCLE_OBSERVATION_NOT_INVOKED


def test_repeated_cycle_ledger_supplement_idempotent_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(JOIN_ENV_VAR, "OFFLINE_STUB")
    for suffix in ("a", "b"):
        root = tmp_path / suffix
        atomic_dir = root / "atomic"
        atomic_dir.mkdir(parents=True)
        monkeypatch.setenv(ATOMIC_STATE_DIR_ENV_VAR, str(atomic_dir))
        _run(root, t2_cycle_dispatch=_t2_enter)
    first = _ledger(tmp_path / "a")
    second = _ledger(tmp_path / "b")
    assert first["FULL_CORE_CYCLE_LIFECYCLE_WIRING"] == second["FULL_CORE_CYCLE_LIFECYCLE_WIRING"]
    assert first[POST_SUBMIT_RECONCILIATION_SUCCEEDED] == POST_SUBMIT_RECONCILIATION_SUCCEEDED_VALUE


def test_atomic_state_authoritative_over_lifecycle_recon_claim(tmp_path: Path) -> None:
    from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
        OUTCOME_HALTED_UNRESOLVED,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1 import (
        run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1,
    )
    from tests.ops.test_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1 import (
        _cycle,
    )

    sha = _origin_main()
    res = run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1(
        cycle=_cycle(envelope=_envelope()),
        handoff=_handoff(sha=sha),
        request=_wiring_request(
            sha=sha,
            submit_kind=CycleSubmitInjectionKind.UNKNOWN_TIMEOUT,
            state_dir=tmp_path,
            apply_durable=True,
        ),
    )
    assert res.lifecycle is not None
    assert res.lifecycle.reconciliation.decision.outcome == OUTCOME_HALTED_UNRESOLVED
    assert res.lifecycle.reconciliation.atomic_state_after in {
        STATE_HALTED_UNRESOLVED,
        "RECONCILIATION_PENDING",
    }
    assert res.lifecycle.reconciliation.atomic_state_after != "TERMINAL_RECONCILED"
    assert res.lifecycle.reconciliation.decision.recommended_atomic_state != "TERMINAL_RECONCILED"


def test_persistence_failure_surfaces_fail_closed(
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
    assert classify_post_submit_reconciliation_observation_v1(reloaded) == (
        RECONCILIATION_OBSERVATION_INCOMPLETE
    )
    with patch.object(orch, "_persist_json", original):
        pass


def test_crash_window_after_first_completed_ledger_write() -> None:
    """Simulate process death after first COMPLETED persist, before supplement."""
    ledger = {
        "state": "COMPLETED",
        "terminal_class": "PRE_EXTERNAL_EFFECT",
        "reason_code": "POST_OWNER_GO",
        **pre_external_completed_ledger_pending_marker_v1(),
    }
    assert classify_post_submit_reconciliation_observation_v1(ledger) == (
        RECONCILIATION_OBSERVATION_INCOMPLETE
    )
    assert (
        ledger[POST_SUBMIT_RECONCILIATION_SUCCEEDED] != POST_SUBMIT_RECONCILIATION_SUCCEEDED_VALUE
    )


def test_fail_closed_ledger_not_reconciliation_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    test_completed_then_lifecycle_fail_closed_persisted(tmp_path, monkeypatch)
    ledger = _ledger(tmp_path)
    assert classify_post_submit_reconciliation_observation_v1(ledger) == (
        LIFECYCLE_FAIL_CLOSED_NOT_RECONCILIATION_SUCCESS
    )


def test_recorded_supplement_does_not_claim_reconciliation_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    atomic_dir = tmp_path / "atomic-recorded"
    atomic_dir.mkdir()
    monkeypatch.setenv(JOIN_ENV_VAR, "OFFLINE_STUB")
    monkeypatch.setenv(ATOMIC_STATE_DIR_ENV_VAR, str(atomic_dir))
    _run(tmp_path, t2_cycle_dispatch=_t2_enter)
    ledger = _ledger(tmp_path)
    assert classify_post_submit_reconciliation_observation_v1(ledger) == (
        RECONCILIATION_SUCCESS_NOT_CLAIMED
    )


def test_closure_claims_json_persistence_reload_lifecycle_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.ops.full_core_live_path_composition_root_v1 import (
        full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1 as wiring_mod,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
        _persist_json,
    )

    sha = _origin_main()
    atomic_dir = tmp_path / "atomic-claims"
    atomic_dir.mkdir()
    monkeypatch.setenv(JOIN_ENV_VAR, "OFFLINE_STUB")
    monkeypatch.setenv(ATOMIC_STATE_DIR_ENV_VAR, str(atomic_dir))
    handoff_reset = bind_full_core_capital_guard_handoff_context_v1(_handoff(sha=sha))
    wiring_req = _wiring_request(
        sha=sha,
        submit_kind=CycleSubmitInjectionKind.NOT_ATTEMPTED,
        state_dir=atomic_dir,
    )
    wiring_reset = bind_full_core_cycle_lifecycle_wiring_invocation_v1(request=wiring_req)

    def _claims_injected_fail(**_kwargs: object) -> None:
        raise RuntimeError("CLAIMS_PERSISTENCE_INJECTED_FAIL")

    monkeypatch.setattr(
        wiring_mod,
        "run_full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1",
        _claims_injected_fail,
    )
    try:
        result = _run(tmp_path, t2_cycle_dispatch=_t2_enter)
    finally:
        reset_full_core_cycle_lifecycle_wiring_invocation_v1(wiring_reset)
        reset_full_core_capital_guard_handoff_context_v1(handoff_reset)
    claims: dict[str, object] = {"POST_COUNT": "0"}
    merge_allowlisted_post_completed_hook_claims_v1(claims, result.extra)
    claims_path = tmp_path / "store" / "claims.json"
    _persist_json(path=claims_path, payload=claims)
    loaded = json.loads(claims_path.read_text(encoding="utf-8"))
    assert loaded.get("FULL_CORE_CYCLE_LIFECYCLE_WIRING") == "FAIL_CLOSED"
    assert loaded.get("POST_SUBMIT_RECONCILIATION_SUCCEEDED") == (
        POST_SUBMIT_RECONCILIATION_SUCCEEDED_VALUE
    )
