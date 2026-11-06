"""FINAL_CURRENT_AUTHORITY_CLOSURE_V1 — limit/equity bind + layered safety ratification."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RATIFICATION_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "final_current_authority_closure_limit_equity_and_layered_safety_ratification_v1.json"
)


def _load() -> dict:
    return json.loads(RATIFICATION_JSON.read_text(encoding="utf-8"))


def test_limit_equity_ratification_flags() -> None:
    payload = _load()
    le = payload["limit_equity_ratification"]
    assert le["owner_decision"] == "RATIFY_CURRENT_PRODUCTIVE_EQUITY_BINDING"
    assert le["four_crs_dimensions_semantically_distinct"] is True
    assert le["four_crs_dimensions_mathematically_distinct"] is True
    assert le["no_new_limit_policy"] is True
    assert le["no_runtime_behavior_change"] is True
    binding = le["productive_four_slot_binding"]
    assert set(binding) == {
        "scope_capital_limit",
        "per_trade_risk_limit",
        "total_capital_limit",
        "daily_loss_remaining_budget",
    }
    for value in binding.values():
        assert value == "typed_29p_available_for_sizing_account_equity"


def test_layered_safety_ratification_flags() -> None:
    payload = _load()
    ls = payload["layered_safety_ratification"]
    assert ls["new_umbrella_runtime_safety_owner"] is False
    assert ls["cap_11_5_activation"] is False
    assert ls["mv2_dp_can_override_safety"] is False
    assert ls["safety_can_veto_mv2_dp"] is True
    assert ls["kill_all_equals_flatten"] is False
    auth = ls["authorities"]
    assert auth["decision_authority"] == "MASTER_V2_PLUS_DOUBLE_PLAY"
    assert "safety_kernel_offline_replay_binding_adapter_v0" in auth["replay_safety_veto_authority"]
    assert "durable_filegate_join_v1" in auth["durable_kill_switch_authority"]
    assert "current_productive_exact_object_flatten_plan_v1" in auth["flatten_authority"]


def test_markers_no_runtime_or_atlas_scope() -> None:
    markers = _load()["markers"]
    assert markers["RUNTIME_BEHAVIOR_CHANGED"] is False
    assert markers["ATLAS_LEGACY_ERADICATION"] is False
    assert markers["REPOSITORY_WIDE_NUMERIC_CLEANUP"] is False
    assert markers["POST_ALLOWED"] is False
