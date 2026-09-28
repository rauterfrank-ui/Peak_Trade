"""Machine-readable Owner policy record for persistent Selected-Future confirmation."""

from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_RECORD = (
    _REPO / "config/governance/selected_future_persistent_scope_confirmation_authority_v1.json"
)
_SPEC = _REPO / "docs/ops/specs/SELECTED_FUTURE_PERSISTENT_SCOPE_CONFIRMATION_AUTHORITY_V1.md"


def test_authority_record_fail_closed_flags() -> None:
    payload = json.loads(_RECORD.read_text(encoding="utf-8"))
    assert payload["SELECTED_FUTURE_PERSISTENCE"] is True
    assert payload["ELEMENTARY_DIRECTION_CHANGE_RESELECTS_FUTURE"] is False
    assert payload["ELEMENTARY_DIRECTION_CHANGE_INVALIDATES_OPPOSITE_CANDIDATE"] is False
    assert (
        payload[
            "OD1_SINGLE_LANE_ACTIVATION_IS_CARRIER_ROUTING_NOT_CANDIDATE_INVALIDATION_AUTHORITY"
        ]
        is True
    )
    assert payload["DUAL_CARRIER_PADDING_MUST_NOT_DESTROY_PERSISTENT_CANDIDATE"] is True
    assert payload["external_effect_authorized"] is False
    assert payload["CANDIDATE_INVALIDATION_AUTHORITY_PROVEN"] is False
    assert payload["CONFIRMATION_COUNT_SEMANTICS_AUTHORITY_BLOCKER"] is False
    assert _SPEC.is_file()
