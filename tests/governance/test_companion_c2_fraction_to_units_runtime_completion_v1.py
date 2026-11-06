"""Governance tests for Companion C2 runtime completion scaffold v1."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.companion_c2_fraction_to_units_runtime_completion_v1 import (
    DECISION_CONFIG,
    WORKPACKAGE_ID,
    load_decision_v1,
    prove_companion_c2_runtime_completion_scaffold_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_decision_config_safety_pins() -> None:
    decision = load_decision_v1(repo_root=REPO_ROOT)
    assert decision["workpackage_id"] == WORKPACKAGE_ID
    assert decision["companion_runtime_conversion_enabled"] is False
    assert decision["runtime_conversion_implemented"] is False
    assert decision["next_productive_conversion_slice_authorized"] is False
    assert decision["external_effect_authorized"] is False
    assert decision["post_allowed"] is False
    assert decision["real_venue_post_allowed"] is False
    assert decision["shadow_session_binding_present"] is False
    assert decision["live_session_binding_present"] is False


def test_scaffold_proof() -> None:
    proof = prove_companion_c2_runtime_completion_scaffold_v1(repo_root=REPO_ROOT)
    assert proof["scaffold_proven"] is True
    assert proof["runtime_conversion_implemented"] is False


def test_shadow_live_still_pass_fraction_unchanged() -> None:
    shadow = (REPO_ROOT / "src/live/shadow_session.py").read_text(encoding="utf-8")
    live = (REPO_ROOT / "src/execution/live_session.py").read_text(encoding="utf-8")
    assert "position_size = self._shadow_cfg.position_fraction" in shadow
    assert "position_size=self._config.position_fraction" in live
    assert "runtime_conversion_v1" not in shadow
    assert "runtime_conversion_v1" not in live


def test_decision_config_on_disk() -> None:
    path = REPO_ROOT / DECISION_CONFIG
    assert path.is_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["conversion_ready"] is True
