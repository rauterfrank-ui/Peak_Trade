"""Contract: Master V2 Local Debug CLI v1 wire-shape (master_v2_debug_result_to_dict / run_master_v2_local_debug_cli_v1).

Non-authorizing reproducibility anchor only — no readiness, gate, execution, or signoff claims.
"""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest

from trading.master_v2.happy_raw_input_v1 import build_master_v2_happy_scenario_raw_input_v1
from trading.master_v2.input_adapter_v1 import (
    INPUT_ADAPTER_LAYER_VERSION,
    adapt_inputs_to_master_v2_flow_v1,
)
from trading.master_v2.local_debug_cli_v1 import (
    LOCAL_DEBUG_CLI_LAYER_VERSION,
    main,
    master_v2_debug_result_to_dict,
    run_master_v2_local_debug_cli_v1,
)
from trading.master_v2.scenario_matrix_v1 import (
    SCENARIO_HAPPY_LIVE_GATED,
    SCENARIO_OPTIONAL_LAYERS_MISSING,
    get_master_v2_scenario_case_v1,
)

_BASE_RESULT_KEYS = frozenset(
    {
        "debug_cli_version",
        "input_adapter_version",
        "adapter_ok",
        "rejection_reason",
        "correlation_id",
    }
)
_SUCCESS_RESULT_KEYS = _BASE_RESULT_KEYS | frozenset(
    {
        "flow_ok",
        "local_flow_rejection",
        "validate_ok",
        "validate_reason_codes",
        "critic_has_error_findings",
        "critic_finding_codes",
        "snapshot",
    }
)
_NON_AUTHORIZING_KEYS = frozenset(
    {
        "authorized",
        "execution_started",
        "armed",
        "promoted",
        "live_started",
        "execution_authorized",
        "ready_for_operator_arming",
    }
)


def _assert_json_native(obj: object, *, depth: int = 0) -> None:
    if depth > 24:
        raise AssertionError("json structure too deep for contract bound")
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert isinstance(k, str), (type(k), obj)
            _assert_json_native(v, depth=depth + 1)
        return
    if isinstance(obj, list):
        for item in obj:
            _assert_json_native(item, depth=depth + 1)
        return
    raise AssertionError(f"non-json-native value: {type(obj)!r}")


def _assert_debug_result_contract(d: dict[str, Any]) -> None:
    assert isinstance(d, dict)
    assert d["debug_cli_version"] == LOCAL_DEBUG_CLI_LAYER_VERSION
    assert d["input_adapter_version"] == INPUT_ADAPTER_LAYER_VERSION
    assert isinstance(d["adapter_ok"], bool)
    if d["rejection_reason"] is not None:
        assert isinstance(d["rejection_reason"], str) and d["rejection_reason"]
    if not d["adapter_ok"]:
        assert set(d.keys()) == _BASE_RESULT_KEYS
        assert d["correlation_id"] is None
        return
    assert set(d.keys()) == _SUCCESS_RESULT_KEYS
    assert isinstance(d["correlation_id"], str) and d["correlation_id"].strip()
    assert d["rejection_reason"] is None
    assert isinstance(d["validate_reason_codes"], list)
    assert isinstance(d["critic_finding_codes"], list)
    if d["flow_ok"] is not None:
        assert isinstance(d["flow_ok"], bool)
    if d["local_flow_rejection"] is not None:
        assert isinstance(d["local_flow_rejection"], str) and d["local_flow_rejection"]
    if d["validate_ok"] is not None:
        assert isinstance(d["validate_ok"], bool)
    if d["critic_has_error_findings"] is not None:
        assert isinstance(d["critic_has_error_findings"], bool)
    for code in d["validate_reason_codes"]:
        assert isinstance(code, str)
    for code in d["critic_finding_codes"]:
        assert isinstance(code, str)
    for forbidden in _NON_AUTHORIZING_KEYS:
        assert forbidden not in d


def _run_without_mutation(
    raw: dict[str, Any],
    *,
    run_evaluator: bool = True,
    with_snapshot: bool = True,
) -> dict[str, Any]:
    original = copy.deepcopy(raw)
    out = run_master_v2_local_debug_cli_v1(
        json_text=json.dumps(raw),
        run_evaluator=run_evaluator,
        with_snapshot=with_snapshot,
    )
    assert raw == original
    return out


def test_debug_cli_contract_v1_valid_baseline_with_evaluator_wire_shape() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    raw = build_master_v2_happy_scenario_raw_input_v1()
    out = _run_without_mutation(raw, run_evaluator=True, with_snapshot=True)
    _assert_debug_result_contract(out)
    assert out["adapter_ok"] is True
    assert out["correlation_id"] == case.packet.correlation_id
    assert out["flow_ok"] is True
    assert out["validate_ok"] is True
    assert out["critic_has_error_findings"] is False
    assert out["snapshot"] is not None
    _assert_json_native(out)
    json.dumps(out)


def test_debug_cli_contract_v1_no_evaluator_packet_enrichment_wire_shape() -> None:
    raw = build_master_v2_happy_scenario_raw_input_v1()
    out = _run_without_mutation(raw, run_evaluator=False, with_snapshot=True)
    _assert_debug_result_contract(out)
    assert out["adapter_ok"] is True
    assert out["flow_ok"] is None
    assert out["local_flow_rejection"] is None
    assert out["validate_ok"] is True
    assert out["snapshot"] is None


def test_debug_cli_contract_v1_optional_layers_missing_adapter_ok() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_OPTIONAL_LAYERS_MISSING)
    raw = {
        "correlation_id": case.packet.correlation_id,
        "staged": {
            "current_stage": case.packet.staged.current_stage.value,
            "requested_stage": case.packet.staged.requested_stage.value,
            "safety_decision_allowed": case.packet.staged.safety_decision_allowed,
            "live_authority_acknowledged": case.packet.staged.live_authority_acknowledged,
        },
    }
    out = _run_without_mutation(raw, run_evaluator=True, with_snapshot=True)
    _assert_debug_result_contract(out)
    assert out["adapter_ok"] is True
    assert out["flow_ok"] is True


def test_debug_cli_contract_v1_debug_result_to_dict_adapter_fail_minimal_keys() -> None:
    ar = adapt_inputs_to_master_v2_flow_v1({"staged": {}})
    d = master_v2_debug_result_to_dict(ar)
    _assert_debug_result_contract(d)
    assert d["adapter_ok"] is False
    assert d.get("flow_ok") is None


def test_debug_cli_contract_v1_fail_closed_invalid_json() -> None:
    with pytest.raises(ValueError, match="INVALID_JSON"):
        run_master_v2_local_debug_cli_v1(json_text="{not json")


def test_debug_cli_contract_v1_fail_closed_empty_input() -> None:
    with pytest.raises(ValueError, match="EMPTY_INPUT"):
        run_master_v2_local_debug_cli_v1(json_text="  \n  ")


def test_debug_cli_contract_v1_fail_closed_root_not_object() -> None:
    with pytest.raises(ValueError, match="JSON_ROOT_MUST_BE_OBJECT"):
        run_master_v2_local_debug_cli_v1(json_text='"x"')


def test_debug_cli_contract_v1_fail_closed_both_json_text_and_input_path() -> None:
    with pytest.raises(ValueError, match="provide only one"):
        run_master_v2_local_debug_cli_v1(json_text="{}", input_path="/tmp/x.json")


def test_debug_cli_contract_v1_fail_closed_missing_input_mode() -> None:
    with pytest.raises(ValueError, match="json_text or input_path is required"):
        run_master_v2_local_debug_cli_v1()


def test_debug_cli_contract_v1_deterministic_output_for_identical_input() -> None:
    raw = build_master_v2_happy_scenario_raw_input_v1()
    first = run_master_v2_local_debug_cli_v1(
        json_text=json.dumps(raw),
        run_evaluator=True,
        with_snapshot=True,
    )
    second = run_master_v2_local_debug_cli_v1(
        json_text=json.dumps(raw),
        run_evaluator=True,
        with_snapshot=True,
    )
    assert first == second


def test_debug_cli_contract_v1_deterministic_repeat_debug_result_to_dict() -> None:
    ar = adapt_inputs_to_master_v2_flow_v1(
        build_master_v2_happy_scenario_raw_input_v1(),
        run_evaluator=True,
        with_snapshot=True,
    )
    first = master_v2_debug_result_to_dict(ar)
    second = master_v2_debug_result_to_dict(ar)
    assert first == second


def test_debug_cli_contract_v1_non_authorizing_success_is_debug_output_only() -> None:
    out = run_master_v2_local_debug_cli_v1(
        json_text=json.dumps(build_master_v2_happy_scenario_raw_input_v1()),
        run_evaluator=True,
        with_snapshot=True,
    )
    _assert_debug_result_contract(out)
    assert out["adapter_ok"] is True
    for forbidden in _NON_AUTHORIZING_KEYS:
        assert forbidden not in out


def test_debug_cli_contract_v1_main_exit_ok_on_adapter_success(tmp_path, capsys) -> None:
    p = tmp_path / "happy.json"
    p.write_text(json.dumps(build_master_v2_happy_scenario_raw_input_v1()), encoding="utf-8")
    code = main(["-f", str(p)])
    assert code == 0
    captured = capsys.readouterr()
    out = json.loads(captured.out)
    _assert_debug_result_contract(out)
    assert out["adapter_ok"] is True


def test_debug_cli_contract_v1_main_exit_fail_on_adapter_reject(tmp_path, capsys) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"staged": {}}), encoding="utf-8")
    code = main(["-f", str(p)])
    assert code == 1
    out = json.loads(capsys.readouterr().out)
    _assert_debug_result_contract(out)
    assert out["adapter_ok"] is False


def test_debug_cli_contract_v1_main_fail_closed_invalid_json_emits_error_wire(
    tmp_path, capsys
) -> None:
    p = tmp_path / "invalid.json"
    p.write_text("{not json", encoding="utf-8")
    code = main(["-f", str(p)])
    assert code == 1
    captured = capsys.readouterr()
    out = json.loads(captured.out)
    assert out["debug_cli_version"] == LOCAL_DEBUG_CLI_LAYER_VERSION
    assert out["adapter_ok"] is False
    assert isinstance(out["rejection_reason"], str)
    assert "INVALID_JSON" in out["rejection_reason"]
