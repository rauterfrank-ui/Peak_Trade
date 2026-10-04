"""Contract tests for canonical Shadow runtime enablement v1."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    EXECUTION_LANE_LIVE,
    EXECUTION_LANE_SHADOW,
    EXTERNAL_EFFECT_AUTHORIZED,
    LIVE_PRE_EXTERNAL_TERMINAL,
    POST_ALLOWED,
    SHADOW_ACTIVATION_OPERATOR_GO,
    SHADOW_PRE_EXTERNAL_CONTINUATION,
    TESTNET_AUTHORIZED,
)
from src.ops.canonical_shadow_runtime_enablement_v1.pre_external_lane_isolation_v1 import (
    PreExternalLaneIsolationError,
    resolve_post_pre_external_continuation_v1,
)
from src.ops.canonical_shadow_runtime_enablement_v1.proof_v1 import (
    prove_canonical_shadow_runtime_safety_v1,
)
from src.ops.canonical_shadow_runtime_enablement_v1.readiness_evaluator_v1 import (
    evaluate_shadow_readiness_dimensions_v1,
)
from src.ops.canonical_shadow_runtime_enablement_v1.shadow_cycle_entrypoint_v1 import (
    run_canonical_shadow_runtime_offline_cycle_v1,
)
from src.ops.canonical_shadow_runtime_enablement_v1.shadow_execution_sink_v1 import (
    ShadowExecutionRequestV1,
    execute_shadow_simulated_intent_v1,
)
from src.ops.canonical_shadow_runtime_enablement_v1.shadow_runtime_bridge_v1 import (
    evaluate_shadow_runtime_bridge_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.bridge_binding_v1 import (
    ensure_accounting_session_v1,
)
from src.ops.ghv_regression_corpus_provenance_v1 import (
    GHV_E2E_EXPECTED_CYCLE_COUNT,
    LAB_SMOKE_CYCLE_LINES,
    classify_corpus_line_count_v1,
)

_INSTRUMENT = "ETH-USD_UM_XPERP-TEST"
_MARK = Decimal("2500.00")


def test_standing_safety_constants_fail_closed() -> None:
    assert POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_PRE_EXTERNAL_TERMINAL is True


def test_live_pre_external_terminal_shadow_only_continuation() -> None:
    assert (
        resolve_post_pre_external_continuation_v1(
            execution_lane=EXECUTION_LANE_LIVE,
            pre_external_reached=True,
        )
        == "TERMINAL_PRE_EXTERNAL"
    )
    assert (
        resolve_post_pre_external_continuation_v1(
            execution_lane=EXECUTION_LANE_SHADOW,
            pre_external_reached=True,
        )
        == SHADOW_PRE_EXTERNAL_CONTINUATION
    )
    with pytest.raises(PreExternalLaneIsolationError):
        resolve_post_pre_external_continuation_v1(
            execution_lane="TESTNET",
            pre_external_reached=True,
        )


def test_bridge_fail_closed_without_operator_go() -> None:
    bridge = evaluate_shadow_runtime_bridge_v1(
        operator_go_token=None,
        observation_authorization_present=True,
    )
    assert bridge.bridge_activated is False
    assert bridge.runtime_bridge_state == "BOUND_READY"


def test_bridge_activated_only_with_go_and_observation_auth() -> None:
    bridge = evaluate_shadow_runtime_bridge_v1(
        operator_go_token=SHADOW_ACTIVATION_OPERATOR_GO,
        observation_authorization_present=True,
    )
    assert bridge.bridge_activated is True
    assert bridge.blockers == ()


def test_shadow_sink_zero_external_counts() -> None:
    session = ensure_accounting_session_v1(instrument_id=_INSTRUMENT, state_root=None)
    portfolio = SimulatedPortfolioEconomicsModelV1(
        PortfolioEconomicsModelParamsV1(initial_equity=Decimal("100000"))
    )
    req = ShadowExecutionRequestV1(
        instrument_id=_INSTRUMENT,
        side="buy",
        quantity="1",
        mark_price=str(_MARK),
        session_id="shadow-test-session",
        cycle_index=1,
    )
    _out, ev = execute_shadow_simulated_intent_v1(
        request=req,
        session=session,
        portfolio=portfolio,
    )
    assert ev.REAL_POST_COUNT == 0
    assert ev.TESTNET_POST_COUNT == 0
    assert ev.WIRE_SEND_COUNT == 0
    assert ev.EXTERNAL_EFFECT_COUNT == 0


def test_offline_cycle_fail_closed_without_activation() -> None:
    session = ensure_accounting_session_v1(instrument_id=_INSTRUMENT, state_root=None)
    portfolio = SimulatedPortfolioEconomicsModelV1(
        PortfolioEconomicsModelParamsV1(initial_equity=Decimal("100000"))
    )
    result = run_canonical_shadow_runtime_offline_cycle_v1(
        disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
        instrument_id=_INSTRUMENT,
        side="buy",
        quantity="1",
        mark_price=str(_MARK),
        session_id="shadow-test-session",
        cycle_index=1,
        session=session,
        portfolio=portfolio,
    )
    assert result.ok is False
    assert result.execution_evidence is None


def test_offline_cycle_succeeds_when_bridge_activated() -> None:
    session = ensure_accounting_session_v1(instrument_id=_INSTRUMENT, state_root=None)
    portfolio = SimulatedPortfolioEconomicsModelV1(
        PortfolioEconomicsModelParamsV1(initial_equity=Decimal("100000"))
    )
    result = run_canonical_shadow_runtime_offline_cycle_v1(
        disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
        instrument_id=_INSTRUMENT,
        side="buy",
        quantity="1",
        mark_price=str(_MARK),
        session_id="shadow-test-session",
        cycle_index=1,
        session=session,
        portfolio=portfolio,
        operator_go_token=SHADOW_ACTIVATION_OPERATOR_GO,
        observation_authorization_present=True,
    )
    assert result.ok is True
    assert result.execution_evidence is not None
    assert result.execution_evidence["REAL_POST_COUNT"] == 0


def test_static_safety_proof_passes() -> None:
    proof = prove_canonical_shadow_runtime_safety_v1()
    assert proof["ok"] is True


def test_readiness_improves_execution_simulation_when_activated() -> None:
    off = evaluate_shadow_readiness_dimensions_v1(bridge_activated=False)
    on = evaluate_shadow_readiness_dimensions_v1(bridge_activated=True)
    off_exec = next(d for d in off["DIMENSIONS"] if d["NAME"] == "EXECUTION_SIMULATION_READY")
    on_exec = next(d for d in on["DIMENSIONS"] if d["NAME"] == "EXECUTION_SIMULATION_READY")
    assert off_exec["STATUS"] == "PROVEN_NOT_READY"
    assert on_exec["STATUS"] == "PROVEN_READY"


def test_corpus_line_count_classifier_disambiguates_smoke() -> None:
    assert classify_corpus_line_count_v1(line_count=GHV_E2E_EXPECTED_CYCLE_COUNT) == (
        "MATCHES_E2E_CYCLE_COUNT"
    )
    assert classify_corpus_line_count_v1(line_count=LAB_SMOKE_CYCLE_LINES) == (
        "MATCHES_LAB_SMOKE_SUBSET"
    )
