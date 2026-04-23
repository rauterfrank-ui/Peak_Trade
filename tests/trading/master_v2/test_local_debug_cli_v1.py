# tests/trading/master_v2/test_local_debug_cli_v1.py
from __future__ import annotations

import json

import pytest

from trading.master_v2.happy_raw_input_v1 import build_master_v2_happy_scenario_raw_input_v1
from trading.master_v2.input_adapter_v1 import adapt_inputs_to_master_v2_flow_v1
from trading.master_v2.local_debug_cli_v1 import (
    LOCAL_DEBUG_CLI_LAYER_VERSION,
    main,
    master_v2_debug_result_to_dict,
    run_master_v2_local_debug_cli_v1,
)


def test_debug_cli_version() -> None:
    assert LOCAL_DEBUG_CLI_LAYER_VERSION == "v1"


def test_run_happy_json_text() -> None:
    out = run_master_v2_local_debug_cli_v1(
        json_text=json.dumps(build_master_v2_happy_scenario_raw_input_v1()),
        run_evaluator=True,
        with_snapshot=True,
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
        json_text=json.dumps(build_master_v2_happy_scenario_raw_input_v1()),
        run_evaluator=False,
        with_snapshot=True,
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
    p.write_text(json.dumps(build_master_v2_happy_scenario_raw_input_v1()), encoding="utf-8")
    out = run_master_v2_local_debug_cli_v1(input_path=p)
    assert out["adapter_ok"] and out["flow_ok"] is True


def test_main_exit_ok(tmp_path, capsys) -> None:
    p = tmp_path / "x.json"
    p.write_text(json.dumps(build_master_v2_happy_scenario_raw_input_v1()), encoding="utf-8")
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
