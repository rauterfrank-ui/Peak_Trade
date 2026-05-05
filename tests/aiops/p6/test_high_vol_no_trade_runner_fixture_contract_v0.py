import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_SPEC = REPO_ROOT / "tests" / "fixtures" / "p6" / "shadow_session_high_vol_no_trade_v0.json"
RUNNER_SPEC = (
    REPO_ROOT / "tests" / "fixtures" / "p6" / "shadow_session_high_vol_no_trade_runner_v0.json"
)
P4C_CAPSULE = REPO_ROOT / "tests" / "fixtures" / "p4c" / "capsule_high_vol_no_trade_v0.json"
P5A_INPUT = REPO_ROOT / "tests" / "fixtures" / "p5a" / "input_high_vol_no_trade_v0.json"
P7_SPEC = REPO_ROOT / "tests" / "fixtures" / "p7" / "paper_run_high_vol_no_trade_v0.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_runner_fixture_has_existing_runner_compatible_shape() -> None:
    spec = _load(RUNNER_SPEC)

    assert spec["schema_version"] == "p6.shadow_session_runner_spec.v0"
    assert spec["capsule_path"] == "tests/fixtures/p4c/capsule_high_vol_no_trade_v0.json"
    assert spec["p5a_input_path"] == "tests/fixtures/p5a/input_high_vol_no_trade_v0.json"
    assert spec["p7_spec_path"] == "tests/fixtures/p7/paper_run_high_vol_no_trade_v0.json"

    assert "inputs" not in spec
    assert "paper_run_spec_path" not in spec


def test_runner_fixture_is_derived_from_contract_spec_without_changing_contract() -> None:
    contract = _load(CONTRACT_SPEC)
    runner = _load(RUNNER_SPEC)

    assert runner["scenario"] == contract["scenario"] == "high_vol_no_trade"
    assert runner["profile"] == contract["profile"] == "high_vol_no_trade"
    assert runner["expected_decision"] == contract["expected_decision"] == "NO_TRADE"
    assert runner["expected_regime"] == contract["expected_regime"] == "VOL_EXTREME"
    assert runner["expected_fills"] == contract["expected_fills"] == []
    assert runner["expected_positions"] == contract["expected_positions"] == {"BTC": 0.0}


def test_runner_fixture_references_existing_consistent_inputs() -> None:
    runner = _load(RUNNER_SPEC)
    capsule = _load(P4C_CAPSULE)
    p5a = _load(P5A_INPUT)
    p7 = _load(P7_SPEC)

    assert Path(runner["capsule_path"]) == P4C_CAPSULE.relative_to(REPO_ROOT)
    assert Path(runner["p5a_input_path"]) == P5A_INPUT.relative_to(REPO_ROOT)
    assert Path(runner["p7_spec_path"]) == P7_SPEC.relative_to(REPO_ROOT)

    assert capsule["scenario"] == p5a["scenario"] == p7["scenario"] == runner["scenario"]
    assert capsule["decision"] == p5a["decision"] == p7["decision"] == runner["expected_decision"]
    assert p5a["no_trade"] is True
    assert p7["orders"] == []
    assert p7["expected_fills"] == []
    assert p7["expected_positions"] == {"BTC": 0.0}


def test_runner_fixture_is_non_authorizing() -> None:
    runner = _load(RUNNER_SPEC)

    for key in (
        "activation_authorized",
        "scheduler_authorized",
        "daemon_authorized",
        "testnet_authorized",
        "live_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert runner[key] is False


def test_runner_fixture_is_portable_and_offline_only() -> None:
    text = RUNNER_SPEC.read_text(encoding="utf-8")
    runner = _load(RUNNER_SPEC)

    assert "/Users/" not in text
    assert "/tmp/" not in text
    assert "api_key" not in text.lower()
    assert "secret" not in text.lower()
    assert "runner_compatible_fixture_only" in runner["notes"]
    assert "does_not_run_shadow" in runner["notes"]
    assert "does_not_run_paper" in runner["notes"]
