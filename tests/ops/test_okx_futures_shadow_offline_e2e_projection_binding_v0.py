"""Focused tests for OKX Futures Shadow offline e2e projection binding v0."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from src.ops.bounded_futures_testnet_venue_binding_v0 import (
    PRODUCTION_INSTRUMENT_ID,
    VENUE_OKX_EUROPE,
)
from src.ops.okx_futures_shadow_no_order_entrypoint_v0 import (
    OkxFuturesShadowNoOrderCycleResultV0,
    run_okx_futures_shadow_no_order_cycle_v0,
)
from src.ops.okx_futures_shadow_offline_e2e_projection_binding_v0 import (
    BINDING_STATUS_BLOCKED,
    BINDING_STATUS_ERROR,
    BINDING_STATUS_PASS,
    CLI_RELPATH,
    EXPECTED_DECISION,
    EXPECTED_EXECUTION_PROJECTION,
    EXPECTED_RECONCILIATION,
    EXPECTED_RISK_SIZING,
    EXPECTED_SAFETY,
    PACKAGE_MARKER,
    PRODUCER_FAMILY,
    READINESS_STATUS_BLOCKED,
    READINESS_STATUS_READY,
    SCHEMA_ID,
    run_okx_futures_shadow_offline_e2e_projection_binding_v0,
)
from src.ops.shadow_preparation_readiness_gate_v0 import (
    CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY,
    DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
    PreparationStatusV0,
    PROJECTION_SCHEMA_ID,
    ShadowPreparationReadinessGateError,
    evaluate_shadow_preparation_readiness_gate_v0,
    load_shadow_preparation_readiness_gate_config_v0,
    write_shadow_preparation_readiness_projection_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "config" / "ops" / "shadow_preparation_readiness_gate_v0.toml"
CLI = REPO_ROOT / CLI_RELPATH
BINDING_MODULE = (
    REPO_ROOT / "src" / "ops" / "okx_futures_shadow_offline_e2e_projection_binding_v0.py"
)
EVALUATED_AT = "2026-07-25T18:00:00Z"
AS_OF = "2026-07-25T18:00:30Z"


def _collect_required_relative_paths(cfg: dict) -> set[str]:
    paths: set[str] = set()
    for surface in cfg["historical_surfaces"]:
        paths.add(str(surface["path"]).strip())
    for component in cfg["mindestkontrakt_components"]:
        for evidence_path in component.get("evidence_paths") or []:
            paths.add(str(evidence_path).strip())
    paths.add(str(cfg[CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY]).strip())
    return paths


def _materialize_temp_repo(tmp_path: Path) -> tuple[Path, dict]:
    cfg = load_shadow_preparation_readiness_gate_config_v0(CONFIG, repo_root=REPO_ROOT)
    for relative in _collect_required_relative_paths(cfg):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(f"# stub:{relative}\n", encoding="utf-8")
    config_dest = tmp_path / "config" / "ops" / "shadow_preparation_readiness_gate_v0.toml"
    config_dest.parent.mkdir(parents=True, exist_ok=True)
    config_dest.write_text(CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "out" / "ops").mkdir(parents=True, exist_ok=True)
    return tmp_path, cfg


def _ready_like_evaluation(base):
    inventory = tuple(
        replace(record, preparation_status=PreparationStatusV0.PRESENT)
        for record in base.mindestkontrakt_inventory
    )
    return replace(
        base,
        shadow_preparation_complete=True,
        blockers=(),
        unmet_gates=(),
        mindestkontrakt_inventory=inventory,
    )


def _patch_ready_evaluate(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    real_evaluate = evaluate_shadow_preparation_readiness_gate_v0
    calls = {"n": 0}

    def _ready_evaluate(**kwargs):
        calls["n"] += 1
        return _ready_like_evaluation(real_evaluate(**kwargs))

    monkeypatch.setattr(
        "src.ops.okx_futures_shadow_offline_e2e_projection_binding_v0."
        "evaluate_shadow_preparation_readiness_gate_v0",
        _ready_evaluate,
    )
    return calls


def _pass_cycle(**kwargs: Any) -> OkxFuturesShadowNoOrderCycleResultV0:
    return run_okx_futures_shadow_no_order_cycle_v0(
        mode=kwargs.get("mode", "shadow"),
        instrument_id=kwargs.get("instrument_id", PRODUCTION_INSTRUMENT_ID),
    )


def test_package_marker_and_schema_identity() -> None:
    assert PACKAGE_MARKER == "OKX_FUTURES_SHADOW_OFFLINE_E2E_PROJECTION_BINDING_V0=true"
    assert PRODUCER_FAMILY == SCHEMA_ID
    assert PRODUCER_FAMILY.endswith("_v0")
    assert CLI.is_file()
    assert BINDING_MODULE.is_file()


def test_a_valid_hold_cycle_produces_verified_durable_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    _patch_ready_evaluate(monkeypatch)
    result = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    assert result.binding_status == BINDING_STATUS_PASS
    assert result.readiness_result == READINESS_STATUS_READY
    assert result.cycle_invoked is True
    assert result.final_decision == EXPECTED_DECISION
    assert result.risk_sizing_result == EXPECTED_RISK_SIZING
    assert result.safety_result == EXPECTED_SAFETY
    assert result.execution_projection_result == EXPECTED_EXECUTION_PROJECTION
    assert result.reconciliation_result == EXPECTED_RECONCILIATION
    assert result.venue == VENUE_OKX_EUROPE
    assert result.instrument_class == "FUTURES"
    assert result.btc_excluded is True
    assert result.spot_excluded is True
    assert result.futures_only is True
    assert result.order_submission_count == 0
    assert result.order_capable_client_instantiated is False
    assert result.verification_verified is True
    assert result.verification_result == "PASS"
    assert result.projection_schema_id == PROJECTION_SCHEMA_ID
    assert result.projection_sha256
    assert (root / result.projection_path).is_file()
    assert result.cycle_projection is not None
    assert result.cycle_projection["decision_result"] == "hold"
    assert result.network_access is False
    assert result.background_process_left_running is False


def test_b_readiness_blocked_prevents_cycle_invocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    cycle_calls = {"n": 0}

    def _cycle(**kwargs):
        cycle_calls["n"] += 1
        return _pass_cycle(**kwargs)

    result = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
        cycle_runner=_cycle,
    )
    assert result.binding_status == BINDING_STATUS_BLOCKED
    assert result.readiness_result == READINESS_STATUS_BLOCKED
    assert result.cycle_invoked is False
    assert cycle_calls["n"] == 0
    assert "READINESS_BLOCKED_CYCLE_NOT_INVOKED" in result.reason_codes
    assert result.verification_verified is True


def test_c_invalid_or_missing_cycle_result_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    _patch_ready_evaluate(monkeypatch)

    missing = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
        cycle_runner=lambda **_kwargs: None,  # type: ignore[return-value, misc]
    )
    assert missing.binding_status == BINDING_STATUS_ERROR
    assert "CYCLE_RESULT_MISSING" in missing.reason_codes
    assert missing.binding_status != BINDING_STATUS_PASS

    def _invalid(**_kwargs):
        base = _pass_cycle()
        return replace(base, decision_result="")

    invalid = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
        cycle_runner=_invalid,
    )
    assert invalid.binding_status == BINDING_STATUS_ERROR
    assert any(code.startswith("CYCLE_RESULT_INVALID") for code in invalid.reason_codes)


def test_d_non_okx_venue_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    _patch_ready_evaluate(monkeypatch)

    def _bad_venue(**_kwargs):
        return replace(_pass_cycle(), venue="kraken")

    result = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
        cycle_runner=_bad_venue,
    )
    assert result.binding_status == BINDING_STATUS_ERROR
    assert "CYCLE_VENUE_NOT_OKX" in result.reason_codes


def test_e_spot_instrument_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    _patch_ready_evaluate(monkeypatch)

    def _spot(**_kwargs):
        return replace(
            _pass_cycle(),
            market_classification="SPOT",
            futures_only=False,
            spot_excluded=False,
        )

    result = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
        cycle_runner=_spot,
    )
    assert result.binding_status == BINDING_STATUS_ERROR
    assert "CYCLE_SPOT_NOT_EXCLUDED" in result.reason_codes or (
        "CYCLE_INSTRUMENT_CLASS_NOT_FUTURES" in result.reason_codes
    )


def test_f_btc_instrument_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    _patch_ready_evaluate(monkeypatch)

    def _btc(**_kwargs):
        return replace(_pass_cycle(), btc_excluded=False)

    result = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
        cycle_runner=_btc,
    )
    assert result.binding_status == BINDING_STATUS_ERROR
    assert "CYCLE_BTC_NOT_EXCLUDED" in result.reason_codes


def test_g_nonzero_order_submission_count_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    _patch_ready_evaluate(monkeypatch)

    def _submitted(**_kwargs):
        return replace(_pass_cycle(), real_order_submission=True)

    result = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
        cycle_runner=_submitted,
    )
    assert result.binding_status == BINDING_STATUS_ERROR
    assert "CYCLE_ORDER_SUBMISSION_COUNT_NONZERO" in result.reason_codes


def test_h_order_capable_client_instantiation_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    _patch_ready_evaluate(monkeypatch)

    def _client(**_kwargs):
        return replace(_pass_cycle(), order_capable_client_instantiated=True)

    result = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
        cycle_runner=_client,
    )
    assert result.binding_status == BINDING_STATUS_ERROR
    assert "CYCLE_ORDER_CAPABLE_CLIENT_INSTANTIATED" in result.reason_codes


def test_i_safety_result_other_than_pass_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    _patch_ready_evaluate(monkeypatch)

    def _unsafe(**_kwargs):
        return replace(_pass_cycle(), safety_result="BLOCK")

    result = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
        cycle_runner=_unsafe,
    )
    assert result.binding_status == BINDING_STATUS_ERROR
    assert "CYCLE_SAFETY_NOT_PASS" in result.reason_codes


def test_j_projection_writer_failure_returns_error_no_false_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    _patch_ready_evaluate(monkeypatch)

    def _fail_write(**_kwargs):
        raise ShadowPreparationReadinessGateError("PROJECTION_TEMP_WRITE_FAILED:boom")

    monkeypatch.setattr(
        "src.ops.okx_futures_shadow_offline_e2e_projection_binding_v0."
        "write_shadow_preparation_readiness_projection_v0",
        _fail_write,
    )
    result = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
    )
    assert result.binding_status == BINDING_STATUS_ERROR
    assert result.binding_status != BINDING_STATUS_PASS
    assert any(code.startswith("PROJECTION_WRITE_FAILED:") for code in result.reason_codes)
    assert result.cycle_invoked is False


def test_k_projection_reader_verifier_failure_returns_error_no_false_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    _patch_ready_evaluate(monkeypatch)

    def _fail_verify(**_kwargs):
        raise OSError("verify boom")

    monkeypatch.setattr(
        "src.ops.okx_futures_shadow_offline_e2e_projection_binding_v0."
        "verify_shadow_preparation_readiness_projection_v0",
        _fail_verify,
    )
    result = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
    )
    assert result.binding_status == BINDING_STATUS_ERROR
    assert result.binding_status != BINDING_STATUS_PASS
    assert any(code.startswith("PROJECTION_VERIFY_FAILED:") for code in result.reason_codes)


def test_l_schema_or_digest_mismatch_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    _patch_ready_evaluate(monkeypatch)
    real_write = write_shadow_preparation_readiness_projection_v0

    def _write_bad_schema(**kwargs):
        meta = real_write(**kwargs)
        dest = root / meta.output_path
        payload = json.loads(dest.read_text(encoding="utf-8"))
        payload["schema_id"] = "wrong.schema"
        dest.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        return meta

    monkeypatch.setattr(
        "src.ops.okx_futures_shadow_offline_e2e_projection_binding_v0."
        "write_shadow_preparation_readiness_projection_v0",
        _write_bad_schema,
    )
    result = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
    )
    assert result.binding_status == BINDING_STATUS_ERROR
    assert result.binding_status != BINDING_STATUS_PASS
    assert result.reason_codes
    assert any(
        code in {"SCHEMA_MISMATCH", "DIGEST_MISMATCH"} or "SCHEMA" in code or "DIGEST" in code
        for code in result.reason_codes
    )


def test_m_repeated_deterministic_invocation_no_competing_truth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    _patch_ready_evaluate(monkeypatch)
    first = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    second = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    assert first.binding_status == BINDING_STATUS_PASS
    assert second.binding_status == BINDING_STATUS_PASS
    assert first.schema_id == second.schema_id == SCHEMA_ID
    assert first.projection_schema_id == second.projection_schema_id == PROJECTION_SCHEMA_ID
    assert first.projection_path == second.projection_path
    assert first.projection_sha256 == second.projection_sha256
    assert first.cycle_projection == second.cycle_projection


def test_n_no_network_and_no_background_after_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    real_evaluate = evaluate_shadow_preparation_readiness_gate_v0

    def _ready_evaluate(**kwargs):
        return _ready_like_evaluation(real_evaluate(**kwargs))

    # CLI imports the binding module; patch at source used by subprocess is harder.
    # Prove binding result flags + no socket usage in-process, then CLI blocked path.
    monkeypatch.setattr(
        "src.ops.okx_futures_shadow_offline_e2e_projection_binding_v0."
        "evaluate_shadow_preparation_readiness_gate_v0",
        _ready_evaluate,
    )
    opened: list[Any] = []
    real_socket = socket.socket

    class _GuardSocket(real_socket):
        def __init__(self, *args, **kwargs):
            opened.append(True)
            raise AssertionError("network socket opened")

    monkeypatch.setattr(socket, "socket", _GuardSocket)
    result = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
        mode="shadow",
    )
    assert result.binding_status == BINDING_STATUS_PASS
    assert result.network_access is False
    assert result.background_process_left_running is False
    assert opened == []

    # Natural blocked CLI path (no monkeypatch in child): exit 2, no hang.
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--repo-root",
            str(root),
            "--mode",
            "shadow",
            "--output-path",
            DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
            "--evaluated-at",
            EVALUATED_AT,
            "--as-of",
            AS_OF,
            "--json",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["binding_status"] == BINDING_STATUS_BLOCKED
    assert payload["cycle_invoked"] is False
    assert payload["network_access"] is False
    assert payload["background_process_left_running"] is False
