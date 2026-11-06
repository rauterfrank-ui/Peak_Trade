"""Missing decision context must remain explicit before any Pending mutation."""

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.creation_v1 import (
    maybe_create_natural_enter_pending_outcome_v1,
)
from tests.ops.test_natural_enter_cross_session_outcome_closure_v1 import (
    CANON,
    NATIVE,
    T0,
    _reporting_enter,
)


@pytest.mark.parametrize("field", ["decision_timestamp_unix", "decision_reference_price"])
@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), True, None])
def test_unbound_or_invalid_decision_context_does_not_create_or_raise(tmp_path, field, value):
    args = dict(
        lane_state_root=tmp_path / "lane",
        reporting=_reporting_enter(),
        run_id="unit-test",
        evidence_root=tmp_path / "ev",
        canonical_instrument_id=CANON,
        native_id=NATIVE,
        decision_timestamp_unix=T0,
        decision_reference_price=3500,
    )
    args[field] = value
    out = maybe_create_natural_enter_pending_outcome_v1(**args)
    assert not out.created and out.skipped and out.reason == "PENDING_DECISION_CONTEXT_UNBOUND"
    assert not (tmp_path / "lane").exists()
