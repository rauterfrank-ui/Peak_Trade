"""Focused suite for §11.13.5 LIVE_CANARY_MINIMUM_EXPOSURE authoring surface."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.environment import LIVE_CONFIRM_TOKEN
from src.ops.capability_11_9_live_canary_order_execution_v1 import constants_v1 as cap_11_9
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authorization_v1 import (
    LiveCanaryAuthorizationError,
    default_authorization_is_false_v1,
    validate_live_canary_authorization_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.config_v1 import (
    LiveCanaryConfigError,
    example_incomplete_config_dict_v1,
    load_live_canary_config_v1,
    require_execute_time_fields_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    LIVE_AUTHORIZED,
    LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN,
    OWNER_GO_AUTHORING,
    OWNER_GO_EXECUTE,
    PACKAGE_MARKER,
    PRODUCTIVE_EXECUTE_PATH_READY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exposure_v1 import (
    LiveCanaryExposureError,
    build_canary_exposure_binding_v1,
    exposure_above_minimum_bound_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.forensic_reconciliation_v1 import (
    prove_forensic_classification_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.runner_v1 import (
    LiveCanaryRunnerError,
    assert_execute_refuses_authoring_go_v1,
    run_section_11_13_5_live_canary_minimum_exposure_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_gates_v1 import (
    LiveCanarySubmitGateError,
    evaluate_canary_submit_gates_v1,
    refuse_submit_unless_gates_pass_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.trade_permission_forensic_v1 import (
    build_trade_permission_forensic_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.verifier_v1 import (
    verify_live_canary_authoring_evidence_v1,
)

ORIGIN_SHA = "0f21b53e001e94085941c774a43a27562a1743fe"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _gate_kwargs(**overrides: object) -> dict:
    base = {
        "owner_go": OWNER_GO_EXECUTE,
        "owner_go_consumed": False,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "bound_origin_main_sha": ORIGIN_SHA,
        "expected_origin_main_sha": ORIGIN_SHA,
        "live_canary_authorized": True,
        "live_enabled": True,
        "live_armed": True,
        "confirm_token": LIVE_CONFIRM_TOKEN,
        "blocks_new_entry": False,
        "unresolved_economic_divergence": False,
        "live_reconciliation_proven": True,
        "permission_attestation": {"READ": True, "TRADE": True, "WITHDRAW": False},
        "environment": "LIVE",
        "fixture_or_demo_or_testnet": False,
        "max_notional": "10.0",
        "min_executable_notional": "10.0",
        "order_count": 1,
        "position_count": 0,
        "exposure_above_minimum_bound": False,
    }
    base.update(overrides)
    return base


def test_package_defaults_and_cap_11_9_remain_fixture_only() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    assert LIVE_AUTHORIZED is False
    assert LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN is False
    assert default_authorization_is_false_v1() is True
    assert PRODUCTIVE_EXECUTE_PATH_READY is True
    assert cap_11_9.LIVE_CANARY_MINIMUM_EXPOSURE_ACTIVATED is False


def test_forensic_classification_from_sealed_evidence() -> None:
    result = prove_forensic_classification_contract_v1(repo_root=REPO_ROOT)
    assert result["contract_ok"] is True
    assert result["BLOCKS_NEW_ENTRY_CLEARED"] is False
    assert result["ANY_LAYER_CLASSIFIED_AS_REAL_ECONOMIC_DIVERGENCE_D"] is False


def test_trade_permission_forensic_actually_not_permitted() -> None:
    trade = build_trade_permission_forensic_v1()
    assert trade["DISTINCTION"] == "ACTUALLY_NOT_PERMITTED"
    assert trade["TRADE_ATTESTATION"] is False
    assert trade["AUTOMATIC_API_KEY_PERMISSION_CHANGE"] is False
    assert trade["OWNER_UI_ACTION_REQUIRED"] is True


def test_submit_gates_refuse_each_required_blocker() -> None:
    cases = [
        ({"owner_go": None}, "NO_OWNER_GO"),
        ({"owner_go": OWNER_GO_AUTHORING}, "AUTHORING_GO"),
        ({"owner_go_consumed": True}, "OWNER_GO_CONSUMED"),
        ({"blocks_new_entry": True}, "BLOCKS_NEW_ENTRY"),
        ({"unresolved_economic_divergence": True}, "UNRESOLVED_ECONOMIC"),
        ({"live_reconciliation_proven": False}, "LIVE_RECONCILIATION_PROVEN_FALSE"),
        (
            {"permission_attestation": {"READ": True, "TRADE": False, "WITHDRAW": False}},
            "TRADE_ATTESTATION",
        ),
        ({"live_enabled": False}, "LIVE_ENABLED_FALSE"),
        ({"live_armed": False}, "LIVE_ARMED_FALSE"),
        ({"confirm_token": "WRONG"}, "CONFIRM_TOKEN"),
        ({"bound_origin_main_sha": "deadbeef"}, "ORIGIN_MAIN_SHA"),
        ({"exposure_above_minimum_bound": True}, "EXPOSURE_ABOVE"),
        ({"order_count": 2}, "ORDER_COUNT"),
        ({"position_count": 2}, "POSITION_COUNT"),
        ({"fixture_or_demo_or_testnet": True}, "FIXTURE_TESTNET_DEMO"),
        ({"environment": "TESTNET"}, "ENVIRONMENT_NOT_LIVE"),
        ({"live_canary_authorized": False}, "AUTHORIZED_FALSE"),
        ({"owner_go": "GO_MERGE_SECTION_11_13_5"}, "MERGE_GO"),
        (
            {
                "owner_go": (
                    "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE@0f21b53e001e94085941c774a43a27562a1743fe"
                )
            },
            "PRIOR_CONSUMED_CANARY_GO",
        ),
    ]
    for overrides, needle in cases:
        evaluation = evaluate_canary_submit_gates_v1(**_gate_kwargs(**overrides))
        assert evaluation.submit_allowed is False
        assert any(needle in reason for reason in evaluation.reasons), (needle, evaluation.reasons)
        with pytest.raises(LiveCanarySubmitGateError, match="CANARY_SUBMIT_HARD_BLOCKED"):
            refuse_submit_unless_gates_pass_v1(evaluation)


def test_submit_gates_allow_only_when_all_true() -> None:
    evaluation = evaluate_canary_submit_gates_v1(**_gate_kwargs())
    assert evaluation.submit_allowed is True
    refuse_submit_unless_gates_pass_v1(evaluation)


def test_authorization_rejects_authoring_go_and_wrong_scope() -> None:
    digest = "a" * 64
    with pytest.raises(LiveCanaryAuthorizationError, match="AUTHORING_GO"):
        validate_live_canary_authorization_v1(
            owner_go=OWNER_GO_AUTHORING,
            authorization_scope=AUTHORIZATION_SCOPE,
            bound_origin_main_sha=ORIGIN_SHA,
            expected_origin_main_sha=ORIGIN_SHA,
            bound_config_digest=digest,
            expected_config_digest=digest,
            live_canary_minimum_exposure_authorized=True,
        )
    with pytest.raises(LiveCanaryAuthorizationError, match="SCOPE_MISMATCH"):
        validate_live_canary_authorization_v1(
            owner_go=OWNER_GO_EXECUTE,
            authorization_scope="LIVE_AUTHORIZED",
            bound_origin_main_sha=ORIGIN_SHA,
            expected_origin_main_sha=ORIGIN_SHA,
            bound_config_digest=digest,
            expected_config_digest=digest,
            live_canary_minimum_exposure_authorized=True,
        )
    with pytest.raises(LiveCanaryAuthorizationError, match="OWNER_GO_CONSUMED"):
        validate_live_canary_authorization_v1(
            owner_go=OWNER_GO_EXECUTE,
            authorization_scope=AUTHORIZATION_SCOPE,
            bound_origin_main_sha=ORIGIN_SHA,
            expected_origin_main_sha=ORIGIN_SHA,
            bound_config_digest=digest,
            expected_config_digest=digest,
            live_canary_minimum_exposure_authorized=True,
            owner_go_consumed=True,
        )


def test_exposure_requires_min_sz_only() -> None:
    binding = build_canary_exposure_binding_v1(
        venue="OKX",
        account_scope="acct",
        instrument_min_sz="0.01",
        instrument_lot_sz="0.01",
        instrument_ct_val="0.01",
        instrument_tick_sz="0.1",
        reference_price="100000",
    )
    assert binding.quantity == "0.01"
    assert binding.max_notional == binding.min_executable_notional
    with pytest.raises(LiveCanaryExposureError, match="MINIMUM_EXPOSURE"):
        build_canary_exposure_binding_v1(
            venue="OKX",
            account_scope="acct",
            instrument_min_sz="0.01",
            instrument_lot_sz="0.01",
            instrument_ct_val="0.01",
            instrument_tick_sz="0.1",
            quantity="0.02",
            reference_price="100000",
        )
    assert (
        exposure_above_minimum_bound_v1(
            quantity="0.02",
            instrument_min_sz="0.01",
            max_notional="20",
            min_executable_notional="10",
        )
        is True
    )


def test_secretref_and_demo_binding_rejected_for_execute_fields() -> None:
    cfg = example_incomplete_config_dict_v1()
    cfg.update(
        {
            "venue": "OKX",
            "entity": "OKX Europe Limited",
            "region": "EEA/DE",
            "rest_host": "eea.okx.com",
            "rest_base": "https://eea.okx.com",
            "account_scope": "856964404452495999",
            "instrument_min_sz": "0.01",
            "instrument_lot_sz": "0.01",
            "instrument_ct_val": "0.01",
            "instrument_tick_sz": "0.1",
            "secretref_uri": "secretref://vault/peak-trade/live-dry-run-order-plan/okx",
            "owner_declared_host_allowlist": ["eea.okx.com"],
        }
    )
    with pytest.raises(LiveCanaryConfigError, match="SECRETREF"):
        require_execute_time_fields_v1(cfg)
    cfg["secretref_uri"] = "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"
    cfg["rest_host"] = "demo.okx.com"
    with pytest.raises(LiveCanaryConfigError, match="FORBIDDEN_HOST"):
        require_execute_time_fields_v1(cfg)


def test_runner_preflight_and_execute_fail_closed(tmp_path: Path) -> None:
    result = run_section_11_13_5_live_canary_minimum_exposure_v1(
        mode="preflight",
        origin_main_sha=ORIGIN_SHA,
        seal_forensic_evidence=True,
        evidence_run_root=str(tmp_path / "ev"),
    )
    assert result.ok is True
    assert result.payload["submit_gate"]["SUBMIT_ALLOWED"] is False
    verify = verify_live_canary_authoring_evidence_v1(tmp_path / "ev")
    assert verify["ok"] is True
    assert verify["LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN"] is False

    with pytest.raises(LiveCanaryRunnerError):
        run_section_11_13_5_live_canary_minimum_exposure_v1(
            mode="execute",
            origin_main_sha=ORIGIN_SHA,
            owner_go=OWNER_GO_EXECUTE,
            live_canary_authorized=True,
        )
    assert_execute_refuses_authoring_go_v1()


def test_load_config_rejects_non_live_environment() -> None:
    payload = example_incomplete_config_dict_v1()
    payload["environment"] = "TESTNET"
    with pytest.raises(LiveCanaryConfigError, match="ENVIRONMENT_MUST_BE_LIVE"):
        load_live_canary_config_v1(payload)


def test_governance_matrix_and_prior_go_nonreusable() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.governance_state_matrix_v1 import (
        PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_BINDING,
        prove_canary_governance_matrix_invariants_v1,
        refuse_merge_go_as_canary_execute_v1,
        refuse_prior_consumed_canary_go_reuse_v1,
    )

    proof = prove_canary_governance_matrix_invariants_v1()
    assert proof["ok"] is True
    assert proof["CANARY_SUCCESS_IMPLIES_GENERAL_LIVE"] is False
    assert proof["CANARY_SUCCESS_IMPLIES_EXPOSURE_INCREASE"] is False
    assert proof["PRIOR_OWNER_GO_REUSABLE"] is False
    with pytest.raises(RuntimeError, match="NOT_REUSABLE"):
        refuse_prior_consumed_canary_go_reuse_v1(
            owner_go_binding=PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_BINDING
        )
    with pytest.raises(RuntimeError, match="MERGE_GO"):
        refuse_merge_go_as_canary_execute_v1(owner_go="GO_MERGE_MAIN")


def test_live_canary_cybersecurity_gate_not_passed_under_current_blockers() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cybersecurity_canary_gate_v1 import (
        evaluate_live_canary_cybersecurity_gate_v1,
    )

    result = evaluate_live_canary_cybersecurity_gate_v1(
        pre_live_cybersecurity_gate="PASS",
        productive_surface_merged_to_origin_main=False,
        trade_attestation=False,
        withdraw_attestation=False,
        read_attestation=True,
    )
    assert result["LIVE_CANARY_CYBERSECURITY_GATE"] == "NOT_PASSED"
    assert result["ELIGIBLE_FOR_LIVE_CANARY_EVALUATION"] is False
    assert result["NEW_CANARY_OWNER_GO_GRANTED"] is False
    assert "TRADE_ATTESTATION_FALSE" in result["BLOCKERS"]
    assert result["TRADE_ATTESTATION_DISTINCTION"] == "TRADE_PERMISSION_CONFIRMED_FALSE"


def test_post_merge_pre_canary_readiness_fail_closed(tmp_path: Path) -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_canary_owner_dependency_resolution_v1 import (
        evaluate_pre_canary_readiness_terminal_v1,
    )

    repo = Path(__file__).resolve().parents[2]
    terminal = evaluate_pre_canary_readiness_terminal_v1(
        repo_root=repo,
        merge_commit_sha="b3dadd86d6821882c8184bd1f6f8e207cbc4af43",
    )
    assert terminal["TERMINAL_STATE"] == "FAIL_CLOSED_PRE_CANARY_BLOCKED"
    assert terminal["TRADE_ATTESTATION"] is False
    assert terminal["WITHDRAW_ATTESTATION"] is False
    assert terminal["EXCHANGE_TRUTH_ADOPTION_STATUS"] == "OWNER_POLICIES_REQUIRED_NOT_ADOPTED"
    assert terminal["LIVE_CANARY_CYBERSECURITY_GATE"] == "NOT_PASSED"
    assert terminal["BLOCKS_NEW_ENTRY"] is True
    assert terminal["LIVE_RECONCILIATION_PROVEN"] is False
    assert terminal["LIVE_AUTHORIZED"] is False
    assert terminal["NEW_CANARY_OWNER_GO_GRANTED"] is False
    assert terminal["PRIOR_CANARY_OWNER_GO_REUSED"] is False
    assert terminal["EARLIEST_UNRESOLVED_DEPENDENCY"] == ("OWNER_TRADE_ATTESTATION_FOR_LIVE_CANARY")
    _ = tmp_path  # reserved for future sealed-path fixtures
