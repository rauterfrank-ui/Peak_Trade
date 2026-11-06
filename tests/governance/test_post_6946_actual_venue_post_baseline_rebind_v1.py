"""POST-6946 baseline rebind decision contract."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
    BASELINE_AUTHORITY_CLASS,
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    PREVIOUS_RECORDED_POST_SLICE_BASELINE_SHA,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DECISION = (
    REPO_ROOT / "config/governance/post_6946_actual_venue_post_baseline_rebind_v1_decision_v1.json"
)


def test_post_6946_decision_aligns_with_runtime_pin() -> None:
    payload = json.loads(DECISION.read_text(encoding="utf-8"))
    assert payload["owner_go"] is True
    assert payload["recorded_post_slice_baseline_sha"] == EXPECTED_BASELINE_ORIGIN_MAIN_SHA
    assert payload["previous_recorded_post_slice_baseline_sha"] == (
        PREVIOUS_RECORDED_POST_SLICE_BASELINE_SHA
    )
    assert payload["baseline_authority_class"] == BASELINE_AUTHORITY_CLASS
    assert payload["self_referential_pin_loop_remediated"] is True
    assert payload["actual_venue_post_performed"] is False
