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


def synthetic_current_post_pending_context_v1(envelope, *, account="injected-observer-account"):
    """Real original observer/collector, explicitly injected credential/GET port."""
    from datetime import datetime, timezone
    from dataclasses import replace
    import time
    from tests.ops.test_account_observation_startup_source_v1 import InjectedTransport, credential
    from tests.ops.test_portfolio_budget_host_v1 import _fetch
    from src.ops.okx_eea_private_account_state_runtime_v1.startup_source_v1 import (
        AccountObservationSourceV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_pending_observation_v1 import (
        capture_current_post_pending_v1,
    )

    class Port(InjectedTransport):
        def get(self, **request):
            return replace(
                super().get(**request),
                pretrade_decision_id=request["pretrade_decision_id"],
                acquired_at_utc=datetime.now(timezone.utc).isoformat(),
            )

    source = AccountObservationSourceV1(
        credential=credential(),
        transport=Port(fetch=_fetch(uid=account)),
        expected_account_identity=account,
        session_id="synthetic-live-observation-session",
        clock=time.time,
    )
    source.collect_v1(instrument_ids_by_native_id={envelope.instrument_id: "synthetic-instrument"})
    return capture_current_post_pending_v1(envelope=envelope, source=source)
