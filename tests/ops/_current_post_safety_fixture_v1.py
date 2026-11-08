"""Explicit ACTIVE original writer in temporary test scope; no real state reads."""

import pytest

from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState


@pytest.fixture(autouse=True)
def synthetic_active_post_safety_v1(tmp_path_factory, monkeypatch):
    # Separate from the tested submit root so unchanged no-write assertions
    # still measure only the actual consumer's operational directory.
    path = tmp_path_factory.mktemp("synthetic-original-post-safety") / "state.json"
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(path))
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    StatePersistence(str(path)).save(KillSwitchState.ACTIVE)
    return path


def synthetic_current_post_quantity_context_v1(envelope):
    """Explicit fresh synthetic original GETs for direct lower-wrapper tests."""
    from tests.ops.test_prepost_position_source_admission_v1 import Port, _bound
    from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
        collect_fresh_pretrade_runtime_get_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_venue_quantity_v1 import (
        capture_current_post_venue_quantity_v1,
    )

    port = Port()

    def bind(value):
        if isinstance(value, dict):
            return {key: bind(item) for key, item in value.items()}
        if isinstance(value, list):
            return [bind(item) for item in value]
        return envelope.instrument_id if value == _bound().venue_native_id else value

    port.base.payloads = bind(port.base.payloads)
    decision = "synthetic-current-quantity:" + envelope.envelope_id
    results = {}
    collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id=decision,
        instrument_id=envelope.instrument_id,
        td_mode=envelope.td_mode,
        limit_px=envelope.price,
        inst_type="SWAP" if envelope.instrument_id.endswith("-SWAP") else "FUTURES",
        transport=port,
        require_collection=True,
        collected_results=results,
    )
    return capture_current_post_venue_quantity_v1(
        envelope=envelope, results=results, acquisition_decision_id=decision
    )
