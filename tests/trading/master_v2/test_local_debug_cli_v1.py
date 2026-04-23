# tests/trading/master_v2/test_local_debug_cli_v1.py
from __future__ import annotations

import json

import pytest

from trading.master_v2.input_adapter_v1 import adapt_inputs_to_master_v2_flow_v1
from trading.master_v2.local_debug_cli_v1 import (
    LOCAL_DEBUG_CLI_LAYER_VERSION,
    main,
    master_v2_debug_result_to_dict,
    run_master_v2_local_debug_cli_v1,
)
from trading.master_v2.scenario_matrix_v1 import (
    SCENARIO_HAPPY_LIVE_GATED,
    get_master_v2_scenario_case_v1,
)


def _happy_raw() -> dict:
    c = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    p = c.packet
    assert p.universe and p.doubleplay and p.scope_envelope and p.risk_cap and p.safety
    return {
        "correlation_id": p.correlation_id,
        "staged": {
            "current_stage": p.staged.current_stage.value,
            "requested_stage": p.staged.requested_stage.value,
            "safety_decision_allowed": p.staged.safety_decision_allowed,
            "live_authority_acknowledged": p.staged.live_authority_acknowledged,
        },
        "universe": {
            "layer_version": p.universe.layer_version,
            "symbols": list(p.universe.symbols),
        },
        "doubleplay": {
            "layer_version": p.doubleplay.layer_version,
            "resolution": p.doubleplay.resolution,
        },
        "scope_envelope": {
            "layer_version": p.scope_envelope.layer_version,
            "within_envelope": p.scope_envelope.within_envelope,
        },
        "risk_cap": {
            "layer_version": p.risk_cap.layer_version,
            "cap_satisfied": p.risk_cap.cap_satisfied,
        },
        "safety": {
            "layer_version": p.safety.layer_version,
            "safety_decision_allowed": p.safety.safety_decision_allowed,
        },
    }


def test_debug_cli_version() -> None:
    assert LOCAL_DEBUG_CLI_LAYER_VERSION == "v1"


def test_run_happy_json_text() -> None:
    out = run_master_v2_local_debug_cli_v1(
        json_text=json.dumps(_happy_raw()), run_evaluator=True, with_snapshot=True
    )
    assert out["debug_cli_version"] == "v1"
    assert out["adapter_ok"] is True
    assert out["rejection_reason"] is None
    assert out["flow_ok"] is True
    assert out["validate_ok"] is True
    assert out["critic_has_error_findings"] is False
    assert out["snapshot"] is not None


def test_run_no_evaluator() -> None:
    out = run_master_v2_local_debug_cli_v1(
        json_text=json.dumps(_happy_raw()), run_evaluator=False, with_snapshot=True
    )
    assert out["adapter_ok"] is True
    assert out["flow_ok"] is None
    assert out["validate_ok"] is True
    assert out["snapshot"] is None


def test_reject_invalid_json() -> None:
    with pytest.raises(ValueError, match="INVALID_JSON"):
        run_master_v2_local_debug_cli_v1(json_text="{not json")


def test_reject_empty_input() -> None:
    with pytest.raises(ValueError, match="EMPTY_INPUT"):
        run_master_v2_local_debug_cli_v1(json_text="  \n  ")


def test_reject_root_not_object() -> None:
    with pytest.raises(ValueError, match="JSON_ROOT_MUST_BE_OBJECT"):
        run_master_v2_local_debug_cli_v1(json_text='"x"')


def test_master_v2_debug_result_to_dict_adapter_fail() -> None:
    ar = adapt_inputs_to_master_v2_flow_v1({"staged": {}})
    d = master_v2_debug_result_to_dict(ar)
    assert d["adapter_ok"] is False
    assert d.get("flow_ok") is None


def test_file_input(tmp_path) -> None:
    p = tmp_path / "in.json"
    p.write_text(json.dumps(_happy_raw()), encoding="utf-8")
    out = run_master_v2_local_debug_cli_v1(input_path=p)
    assert out["adapter_ok"] and out["flow_ok"] is True


def test_main_exit_ok(tmp_path, capsys) -> None:
    p = tmp_path / "x.json"
    p.write_text(json.dumps(_happy_raw()), encoding="utf-8")
    code = main(["-f", str(p)])
    assert code == 0
    captured = capsys.readouterr()
    o = json.loads(captured.out)
    assert o["adapter_ok"] is True


def test_main_exit_fail_adapter(tmp_path, capsys) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"staged": {}}), encoding="utf-8")
    code = main(["-f", str(p)])
    assert code == 1
    o = json.loads(capsys.readouterr().out)
    assert o.get("adapter_ok") is False
