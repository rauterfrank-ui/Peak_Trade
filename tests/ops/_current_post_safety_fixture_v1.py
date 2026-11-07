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
