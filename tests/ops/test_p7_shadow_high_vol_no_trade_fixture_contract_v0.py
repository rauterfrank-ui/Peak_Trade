import json
from pathlib import Path

from tests.ops.p7_shadow_one_shot_acceptance_bundle_v0 import (
    p7_shadow_acceptance_fixture_profiles_v0,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = (
    REPO_ROOT / "tests" / "fixtures" / "p7_shadow_one_shot_acceptance_high_vol_no_trade_v0"
)
BASELINE_DIR = REPO_ROOT / "tests" / "fixtures" / "p7_shadow_one_shot_acceptance_v0"


def _json_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.json"))


def _load(relpath: str) -> object:
    return json.loads((FIXTURE_DIR / relpath).read_text(encoding="utf-8"))


def test_high_vol_no_trade_fixture_has_same_relative_artifact_set_as_baseline() -> None:
    baseline = {path.relative_to(BASELINE_DIR).as_posix() for path in _json_files(BASELINE_DIR)}
    candidate = {path.relative_to(FIXTURE_DIR).as_posix() for path in _json_files(FIXTURE_DIR)}

    assert len(candidate) == 11
    assert candidate == baseline


def test_high_vol_no_trade_fixture_json_is_valid_and_portable() -> None:
    for path in _json_files(FIXTURE_DIR):
        data = json.loads(path.read_text(encoding="utf-8"))
        serialized = json.dumps(data, sort_keys=True)
        assert "/Users/" not in serialized
        assert "/tmp/" not in serialized


def test_high_vol_no_trade_fixture_declares_no_trade_semantics() -> None:
    summary = _load("shadow_session_summary.json")
    trade_plan = _load("p5a/l3_trade_plan_advisory.json")

    assert isinstance(summary, dict)
    assert isinstance(trade_plan, dict)
    assert summary["scenario"] == "high_vol_no_trade"
    assert summary["regime"] == "VOL_EXTREME"
    assert summary["decision"] == "NO_TRADE"
    assert summary["trade_allowed"] is False
    assert trade_plan["scenario"] == "high_vol_no_trade"
    assert trade_plan["regime"] == "VOL_EXTREME"
    assert trade_plan["decision"] == "NO_TRADE"
    assert trade_plan["trade_allowed"] is False


def test_high_vol_no_trade_fixture_has_empty_fills_and_flat_account() -> None:
    fills = _load("p7/fills.json")
    promoted_fills = _load("p7_fills.json")
    account = _load("p7/account.json")
    promoted_account = _load("p7_account.json")

    assert isinstance(fills, dict)
    assert isinstance(promoted_fills, dict)
    assert fills["fills"] == []
    assert promoted_fills["fills"] == []
    assert isinstance(account, dict)
    assert isinstance(promoted_account, dict)
    assert all(value == 0.0 for value in account.get("positions", {}).values())
    assert all(value == 0.0 for value in promoted_account.get("positions", {}).values())


def test_fixture_profiles_register_high_vol_no_trade_family() -> None:
    profiles = p7_shadow_acceptance_fixture_profiles_v0()

    assert profiles["high_vol_no_trade"] == {
        "fixture_dir": "tests/fixtures/p7_shadow_one_shot_acceptance_high_vol_no_trade_v0",
        "expected_scenario": "high_vol_no_trade",
        "expected_decision": "NO_TRADE",
        "fills_may_be_empty": True,
    }
