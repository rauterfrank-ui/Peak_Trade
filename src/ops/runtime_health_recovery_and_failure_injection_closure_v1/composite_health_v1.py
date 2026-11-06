"""Deterministic composite end-to-end health derivation for O6."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.component_health_v1 import (
    ComponentHealthReportV1,
    assert_non_healthy_cannot_render_green_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.constants_v1 import (
    COMPONENT_DASHBOARD_BACKEND,
    COMPONENT_MARKET_DATA,
    COMPONENT_PERSISTENCE,
    COMPONENT_READ_MODEL_PROJECTOR,
    COMPONENT_RUNTIME,
    COMPONENT_SUPERVISOR,
    COMPOSITE_DASHBOARD_BACKEND_HEALTH,
    COMPOSITE_END_TO_END_DATA_HEALTH,
    COMPOSITE_HEALTH_KEYS,
    COMPOSITE_HOST_HEALTH,
    COMPOSITE_MARKET_DATA_HEALTH,
    COMPOSITE_PERSISTENCE_HEALTH,
    COMPOSITE_READ_MODEL_HEALTH,
    COMPOSITE_RUNTIME_HEALTH,
    HEALTH_HEALTHY,
    HEALTH_MISSING_SOURCE,
    HEALTH_SEVERITY,
    HEALTH_STATES,
    NON_HEALTHY_STATES,
)


class CompositeHealthErrorV1(ValueError):
    """Fail-closed composite-health contract violation."""


def _worst(states: Sequence[str]) -> str:
    if not states:
        return HEALTH_MISSING_SOURCE
    return max(states, key=lambda s: HEALTH_SEVERITY.get(s, 99))


def _require_component(
    reports: Mapping[str, ComponentHealthReportV1 | Mapping[str, Any]],
    component: str,
) -> str:
    if component not in reports:
        return HEALTH_MISSING_SOURCE
    raw = reports[component]
    if isinstance(raw, ComponentHealthReportV1):
        state = raw.classification
    else:
        state = str(raw.get("classification") or HEALTH_MISSING_SOURCE)
    state = state.strip().upper()
    if state not in HEALTH_STATES:
        raise CompositeHealthErrorV1(f"UNKNOWN_COMPONENT_STATE:{component}:{state}")
    return state


def derive_composite_health_v1(
    reports: Mapping[str, ComponentHealthReportV1 | Mapping[str, Any]],
) -> dict[str, Any]:
    """Derive composite health from explicit component reports.

    END_TO_END_DATA_HEALTH is the worst of the data path surfaces and must never
    be HEALTHY when any of market-data / read-model / dashboard is non-healthy.
    """
    host = _require_component(reports, COMPONENT_SUPERVISOR)
    market = _require_component(reports, COMPONENT_MARKET_DATA)
    runtime = _require_component(reports, COMPONENT_RUNTIME)
    persistence = _require_component(reports, COMPONENT_PERSISTENCE)
    read_model = _require_component(reports, COMPONENT_READ_MODEL_PROJECTOR)
    dashboard = _require_component(reports, COMPONENT_DASHBOARD_BACKEND)

    end_to_end = _worst([market, runtime, persistence, read_model, dashboard])

    composite = {
        COMPOSITE_HOST_HEALTH: host,
        COMPOSITE_MARKET_DATA_HEALTH: market,
        COMPOSITE_RUNTIME_HEALTH: runtime,
        COMPOSITE_PERSISTENCE_HEALTH: persistence,
        COMPOSITE_READ_MODEL_HEALTH: read_model,
        COMPOSITE_DASHBOARD_BACKEND_HEALTH: dashboard,
        COMPOSITE_END_TO_END_DATA_HEALTH: end_to_end,
    }

    # Stale/disconnected/missing dashboard data must block end-to-end healthy.
    if dashboard in NON_HEALTHY_STATES and end_to_end == HEALTH_HEALTHY:
        raise CompositeHealthErrorV1("STALE_DASHBOARD_MUST_BLOCK_E2E_HEALTHY")
    if market in NON_HEALTHY_STATES and end_to_end == HEALTH_HEALTHY:
        raise CompositeHealthErrorV1("STALE_MARKET_DATA_MUST_BLOCK_E2E_HEALTHY")
    if read_model in NON_HEALTHY_STATES and end_to_end == HEALTH_HEALTHY:
        raise CompositeHealthErrorV1("STALE_READ_MODEL_MUST_BLOCK_E2E_HEALTHY")

    may_render_green = end_to_end == HEALTH_HEALTHY and all(
        composite[key] == HEALTH_HEALTHY for key in COMPOSITE_HEALTH_KEYS
    )
    if not may_render_green:
        assert_non_healthy_cannot_render_green_v1(
            classification=end_to_end,
            render_as_healthy=False,
        )

    return {
        "ok": True,
        "composite": composite,
        "may_render_green": may_render_green,
        "end_to_end_blocks_stale_dashboard": True,
        "derived_not_guessed": True,
        "process_existence_alone_insufficient": True,
    }


def composite_health_contract_v1() -> dict[str, Any]:
    return {
        "composite_keys": list(COMPOSITE_HEALTH_KEYS),
        "states": sorted(HEALTH_STATES),
        "severity": dict(HEALTH_SEVERITY),
        "stale_dashboard_cannot_be_green": True,
        "derived_not_guessed": True,
    }
