"""Focused offline tests: INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.integrated_paper_shadow_observation_session_v1.bundle_verifier_v1 import (
    RESULT_INVALID,
    RESULT_VERIFIED,
    verify_integrated_paper_shadow_observation_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
    PACKAGE_MARKER,
)
from src.ops.integrated_paper_shadow_observation_session_v1.entrypoint_v1 import (
    run_integrated_paper_shadow_observation_cycle_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.evidence_v1 import (
    write_observation_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (
    ObservationMarketTickV1,
    evaluate_market_data_sequence_v1,
    validate_instrument_for_observation_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.no_order_guard_v1 import (
    NoOrderAttestationV1,
    attest_capability_sources_no_order_v1,
    reject_broker_write_attempt_v1,
    reject_order_attempt_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PORTFOLIO_ECONOMICS_MODEL_ID,
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.readiness_producer_v1 import (
    produce_paper_shadow_observation_readiness_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.session_lifecycle_v1 import (
    ObservationLifecycleError,
    ObservationSessionState,
    assert_no_auto_promotion_v1,
    assert_transition_allowed,
    plan_observation_session_lifecycle_v1,
    refuse_wallclock_session_execution_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "config/ops/integrated_paper_shadow_observation_session_v1.toml"
CONTRACT = (
    REPO_ROOT / "docs/ops/runbooks/INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1.md"
)
CLI = REPO_ROOT / "scripts/ops/run_integrated_paper_shadow_observation_session_contract_v1.py"
SHADOW_CONTRACT = REPO_ROOT / "docs/ops/runbooks/SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0.md"
RUNTIME_BRIDGE = REPO_ROOT / "src/trading/master_v2/runtime_bridge_pre_activation_gate_v0.py"
SHADOW_TOML = REPO_ROOT / "config/ops/shadow_preparation_readiness_gate_v0.toml"


def test_package_identity_and_config_defaults() -> None:
    assert PACKAGE_MARKER == "INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1=true"
    assert CAPABILITY_ID == "INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1"
    assert CONFIG.is_file()
    assert CONTRACT.is_file()
    assert CLI.is_file()
    text = CONFIG.read_text(encoding="utf-8")
    assert "orders_allowed = false" in text
    assert "wallclock_session_execution_allowed = false" in text
    assert "operator_go_granted = false" in text
    assert "paper_shadow_observation_authorized = false" in text


def test_portfolio_economics_model_fill_fee_slippage_pnl_funding() -> None:
    model = SimulatedPortfolioEconomicsModelV1()
    assert model.model_id == PORTFOLIO_ECONOMICS_MODEL_ID
    fill = model.apply_intended_action(
        instrument_id="ETH-USD_UM_XPERP-310404",
        side="BUY",
        quantity=Decimal("1"),
        mark_price=Decimal("3500"),
    )
    assert fill is not None
    assert fill.fee > 0
    assert fill.slippage_cost >= 0
    model.apply_intended_action(
        instrument_id="ETH-USD_UM_XPERP-310404",
        side="SELL",
        quantity=Decimal("1"),
        mark_price=Decimal("3510"),
    )
    metrics = model.economic_metrics()
    assert metrics.fill_count == 2
    assert metrics.fees > 0
    snap = model.snapshot()
    assert snap["broker_writes"] is False
    assert snap["orders_submitted"] is False
    digest_a = model.model_digest()
    digest_b = SimulatedPortfolioEconomicsModelV1().model_digest()
    assert digest_a == digest_b


def test_market_data_policy_rejects_btc_spot_duplicates_gaps() -> None:
    assert validate_instrument_for_observation_v1(instrument_id="BTC-USD_UM_XPERP-1")
    assert "SPOT_INSTRUMENT_FORBIDDEN" in validate_instrument_for_observation_v1(
        instrument_id="ETH/USDT"
    )
    ticks = [
        ObservationMarketTickV1(
            instrument_id="ETH-USD_UM_XPERP-310404",
            venue="OKX",
            market_type="FUTURES",
            sequence=1,
            event_ts_unix=100.0,
            receive_ts_unix=100.1,
            mono_ts=1.0,
            mid_price=3500.0,
        ),
        ObservationMarketTickV1(
            instrument_id="ETH-USD_UM_XPERP-310404",
            venue="OKX",
            market_type="FUTURES",
            sequence=1,
            event_ts_unix=101.0,
            receive_ts_unix=101.1,
            mono_ts=2.0,
            mid_price=3501.0,
        ),
    ]
    result = evaluate_market_data_sequence_v1(ticks)
    assert result.ok is False
    assert any("DUPLICATE_SEQUENCE" in b for b in result.blockers)


def test_observation_entrypoint_pass_and_fail_closed_modes() -> None:
    ok = run_integrated_paper_shadow_observation_cycle_v1(mode="observation")
    assert ok.terminal_status == "PASS"
    assert ok.paper_shadow_observation_authorized is False
    assert ok.orders_submitted is False
    assert ok.broker_writes_performed is False
    assert ok.wallclock_session_started is False
    assert ok.authority_effect == AUTHORITY_EFFECT_NONE

    bad_mode = run_integrated_paper_shadow_observation_cycle_v1(mode="shadow")
    assert bad_mode.terminal_status == "FAIL_CLOSED"
    assert any("MODE_MUST_BE_OBSERVATION" in b for b in bad_mode.blockers)

    bad_btc = run_integrated_paper_shadow_observation_cycle_v1(
        mode="observation", instrument_id="BTC-USD_UM_XPERP-1"
    )
    assert bad_btc.terminal_status == "FAIL_CLOSED"


def test_negative_order_and_broker_write_attempts() -> None:
    with pytest.raises(Exception, match="ORDER_REJECTED"):
        reject_order_attempt_v1("place_order")
    with pytest.raises(Exception, match="BROKER_WRITE_REJECTED"):
        reject_broker_write_attempt_v1("broker_write")
    rejected = run_integrated_paper_shadow_observation_cycle_v1(
        mode="observation",
        attempt_order_submission=True,
    )
    assert rejected.terminal_status == "FAIL_CLOSED"
    assert any("ORDER_ATTEMPT_REJECTED" in b for b in rejected.blockers)
    rejected_bw = run_integrated_paper_shadow_observation_cycle_v1(
        mode="observation",
        attempt_broker_write=True,
    )
    assert rejected_bw.terminal_status == "FAIL_CLOSED"
    assert any("BROKER_WRITE_ATTEMPT_REJECTED" in b for b in rejected_bw.blockers)


def test_lifecycle_no_wallclock_no_auto_promotion() -> None:
    plan = plan_observation_session_lifecycle_v1()
    assert plan.wallclock_execution_allowed is False
    assert plan.no_auto_promotion is True
    assert plan.auto_promotion_triggered is False
    assert plan.authority_effect == AUTHORITY_EFFECT_NONE
    assert any("OPERATOR_GO_ABSENT" in b for b in plan.blockers)
    with pytest.raises(ObservationLifecycleError, match="WALLCLOCK"):
        refuse_wallclock_session_execution_v1()
    with pytest.raises(ObservationLifecycleError, match="AUTO_PROMOTION"):
        assert_no_auto_promotion_v1(next_stage="PROMOTION")
    assert_transition_allowed(
        from_state=ObservationSessionState.CREATED,
        to_state=ObservationSessionState.READY,
    )
    with pytest.raises(ObservationLifecycleError):
        assert_transition_allowed(
            from_state=ObservationSessionState.COMPLETED,
            to_state=ObservationSessionState.RUNNING,
        )


def test_readiness_producer_fail_closed_no_force_pass_deterministic() -> None:
    forced = produce_paper_shadow_observation_readiness_v1(repo_root=REPO_ROOT, force_pass=True)
    assert forced.PAPER_SHADOW_OBSERVATION_READINESS_PASS is False
    assert "FORCE_PASS_REJECTED" in forced.readiness_blockers
    assert forced.PAPER_SHADOW_OBSERVATION_AUTHORIZED is False

    a = produce_paper_shadow_observation_readiness_v1(repo_root=REPO_ROOT)
    b = produce_paper_shadow_observation_readiness_v1(repo_root=REPO_ROOT)
    assert a.to_dict() == b.to_dict()
    assert a.authority_effect == AUTHORITY_EFFECT_NONE
    assert a.PAPER_SHADOW_OBSERVATION_AUTHORIZED is False
    # Operator-GO / Session-Preregistration surfaces discovered → readiness may pass.
    # Authorization remains false in repository defaults.
    go_fact = next(
        f
        for f in a.discovery_facts
        if f["fact_id"] == "SESSION_PREREGISTRATION_AND_OPERATOR_GO_CONTRACT_PRESENT"
    )
    assert go_fact["present"] is True
    assert a.PAPER_SHADOW_OBSERVATION_READINESS_PASS is True
    assert any(
        f["fact_id"] == "SIMULATED_PORTFOLIO_FILL_FEE_SLIPPAGE_PNL_MODEL_DEFINED" and f["present"]
        for f in a.discovery_facts
    )


def test_evidence_and_bundle_verifier(tmp_path: Path) -> None:
    cycle = run_integrated_paper_shadow_observation_cycle_v1(mode="observation")
    lifecycle = plan_observation_session_lifecycle_v1()
    no_order = attest_capability_sources_no_order_v1(
        repo_root=REPO_ROOT,
        relative_paths=[
            "src/ops/integrated_paper_shadow_observation_session_v1/entrypoint_v1.py",
            "src/ops/integrated_paper_shadow_observation_session_v1/no_order_guard_v1.py",
        ],
    )
    assert no_order.ok is True
    root = tmp_path / "evidence"
    bundle = write_observation_evidence_bundle_v1(
        evidence_root=root,
        cycle=cycle,
        lifecycle=lifecycle,
        no_order=no_order,
        config_snapshot={"orders_allowed": False},
        code_identity={"capability_id": CAPABILITY_ID},
        session_identity={"session_id": "test_session"},
    )
    assert (root / "evidence_manifest.sha256").is_file()
    assert bundle.session_authorized is False

    verified = verify_integrated_paper_shadow_observation_evidence_bundle_v1(evidence_root=root)
    assert verified.verified is True
    assert verified.result == RESULT_VERIFIED
    assert verified.economic_validity_pass is False
    assert verified.paper_shadow_observation_authorized is False
    assert verified.integrated_economic_evidence_bundle_verified is False

    synthetic = verify_integrated_paper_shadow_observation_evidence_bundle_v1(
        evidence_root=root, allow_synthetic=True
    )
    assert synthetic.verified is False
    assert synthetic.result == RESULT_INVALID
    assert "SYNTHETIC_PASS_FORBIDDEN" in synthetic.blockers

    # Tamper digest
    manifest = root / "session_manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["paper_shadow_observation_authorized"] = True
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    bad = verify_integrated_paper_shadow_observation_evidence_bundle_v1(evidence_root=root)
    assert bad.verified is False


def test_stale_contradictions_reconciled() -> None:
    shadow_doc = SHADOW_CONTRACT.read_text(encoding="utf-8")
    assert (
        "OPEN_BLOCKERS=ECONOMIC_READINESS,RUNTIME_BRIDGE,EXPLICIT_ACTIVATION_GO" not in shadow_doc
    )
    assert "PAPER_SHADOW_OBSERVATION_READINESS" in shadow_doc
    assert "LEGACY_OFFLINE_GATE_DOES_NOT_ALONE_BLOCK_PAPER_SHADOW_READINESS=true" in shadow_doc

    bridge = RUNTIME_BRIDGE.read_text(encoding="utf-8")
    assert "economic_validity_offline_gate_status" not in bridge
    assert "integrated_economic_evidence_bundle_verified_status" in bridge
    assert "INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED" in bridge

    toml = SHADOW_TOML.read_text(encoding="utf-8")
    assert 'CANONICAL_SHADOW_MODE_EXISTS=false"' not in toml.replace(" ", "")
    assert "CANONICAL_STEP_29U_ACTIVATION_UNAUTHORIZED=true" in toml


def test_capability_sources_have_no_forbidden_imports() -> None:
    attestation = attest_capability_sources_no_order_v1(
        repo_root=REPO_ROOT,
        relative_paths=[
            "src/ops/integrated_paper_shadow_observation_session_v1/entrypoint_v1.py",
            "src/ops/integrated_paper_shadow_observation_session_v1/portfolio_economics_model_v1.py",
            "src/ops/integrated_paper_shadow_observation_session_v1/readiness_producer_v1.py",
            "src/ops/integrated_paper_shadow_observation_session_v1/bundle_verifier_v1.py",
            "src/ops/integrated_paper_shadow_observation_session_v1/session_lifecycle_v1.py",
            "src/ops/integrated_paper_shadow_observation_session_v1/market_data_policy_v1.py",
            "src/ops/integrated_paper_shadow_observation_session_v1/no_order_guard_v1.py",
            "src/ops/integrated_paper_shadow_observation_session_v1/evidence_v1.py",
        ],
    )
    assert attestation.ok is True, attestation.blockers
