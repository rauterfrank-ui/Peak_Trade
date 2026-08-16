"""Focused suite for §11.13.5 LIVE_CANARY_MINIMUM_EXPOSURE authoring surface."""

from __future__ import annotations

import json
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
    CANARY_SUBMIT_TRANSPORT_IMPLEMENTED,
    CANARY_SUBMIT_TRANSPORT_SCOPE,
    DEFAULT_INST_TYPE,
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_RULE_TYPE,
    GENERAL_LIVE_SUBMIT_UNLOCKED,
    SETTLEMENT_ACCOUNT_TRUTH,
    LIVE_AUTHORIZED,
    LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN,
    OWNER_GO_AUTHORING,
    OWNER_GO_EXECUTE,
    PACKAGE_MARKER,
    PRODUCTIVE_EXECUTE_PATH_READY,
    REQUIRED_SECRETREF_URI,
    SUBMIT_UNLOCKED,
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
        "live_canary_cybersecurity_gate": "PASS",
        "rest_host": "eea.okx.com",
        "secretref_uri": REQUIRED_SECRETREF_URI,
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
    assert CANARY_SUBMIT_TRANSPORT_IMPLEMENTED is True
    assert CANARY_SUBMIT_TRANSPORT_SCOPE == "SECTION_11_13_5_LIVE_CANARY_MINIMUM_EXPOSURE_ONLY"
    assert GENERAL_LIVE_SUBMIT_UNLOCKED is False
    assert SUBMIT_UNLOCKED is False
    assert DEFAULT_INSTRUMENT_ID == "BTC-USD_UM_XPERP-310404"
    assert DEFAULT_INST_TYPE == "FUTURES"
    assert DEFAULT_RULE_TYPE == "xperp"
    assert SETTLEMENT_ACCOUNT_TRUTH == "USDC"


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
        ({"live_canary_cybersecurity_gate": "NOT_PASSED"}, "CYBERSECURITY_GATE"),
        ({"rest_host": "www.okx.com"}, "REST_HOST_NOT_PRODUCTION_EEA"),
        (
            {"secretref_uri": "secretref://vault/peak-trade/live-shadow-recon/okx"},
            "SECRETREF_URI_BINDING_MISMATCH",
        ),
        ({"open_order_count": 1}, "OPEN_ORDER_PRESENT"),
        ({"open_position_count": 1}, "OPEN_POSITION_PRESENT"),
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
        instrument_min_sz="1",
        instrument_lot_sz="1",
        instrument_ct_val="0.0001",
        instrument_tick_sz="0.1",
        reference_price="63028",
    )
    assert binding.quantity == "1"
    assert binding.max_notional == binding.min_executable_notional
    with pytest.raises(LiveCanaryExposureError, match="MINIMUM_EXPOSURE"):
        build_canary_exposure_binding_v1(
            venue="OKX",
            account_scope="acct",
            instrument_min_sz="1",
            instrument_lot_sz="1",
            instrument_ct_val="0.0001",
            instrument_tick_sz="0.1",
            quantity="2",
            reference_price="63028",
        )
    assert (
        exposure_above_minimum_bound_v1(
            quantity="2",
            instrument_min_sz="1",
            max_notional="20",
            min_executable_notional="10",
        )
        is True
    )
    with pytest.raises(LiveCanaryExposureError, match="INTEGER_CONTRACT_REQUIRED"):
        build_canary_exposure_binding_v1(
            venue="OKX",
            account_scope="acct",
            instrument_min_sz="0.01",
            instrument_lot_sz="0.01",
            instrument_ct_val="0.01",
            instrument_tick_sz="0.1",
            reference_price="63028",
        )


def test_execute_fields_reject_swap_and_demo_instrument_ids() -> None:
    cfg = example_incomplete_config_dict_v1()
    cfg.update(
        {
            "venue": "OKX",
            "entity": "OKX Europe Limited",
            "region": "EEA/DE",
            "rest_host": "eea.okx.com",
            "rest_base": "https://eea.okx.com",
            "account_scope": "856964404452495999",
            "secretref_uri": REQUIRED_SECRETREF_URI,
            "owner_declared_host_allowlist": ["eea.okx.com"],
            "instrument_id": "BTC-USDT-SWAP",
        }
    )
    with pytest.raises(LiveCanaryConfigError, match="INSTRUMENT_BINDING_MISMATCH"):
        require_execute_time_fields_v1(cfg)
    cfg["instrument_id"] = "BTC-USD_UM_XPERP-310328"
    with pytest.raises(LiveCanaryConfigError, match="INSTRUMENT_BINDING_MISMATCH"):
        require_execute_time_fields_v1(cfg)


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
            "instrument_min_sz": "1",
            "instrument_lot_sz": "1",
            "instrument_ct_val": "0.0001",
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


def test_canary_trade_capability_attestation_fail_closed_when_canary_secretref_missing(
    tmp_path: Path,
) -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_trade_capability_attestation_v1 import (
        OWNER_GO_TRADE_KEY_ATTESTATION,
        TERMINAL_FAIL_CLOSED,
        evaluate_live_canary_canary_trade_capability_attestation_v1,
    )

    ops_local = tmp_path / ".ops_local"
    ops_local.mkdir()
    result = evaluate_live_canary_canary_trade_capability_attestation_v1(
        ops_local_root=ops_local,
        origin_main_sha="abc1234",
        owner_go=OWNER_GO_TRADE_KEY_ATTESTATION,
    )
    assert result["TERMINAL_STATE"] == TERMINAL_FAIL_CLOSED
    assert result["TRADE_ATTESTATION"] is False
    assert result["WITHDRAW_ATTESTATION"] is False
    assert result["SECRETREF_STATUS"] == "MISSING_FAIL_CLOSED"
    assert result["CANARY_TRADE_KEY_BINDING"] == "NOT_PROVEN_FAIL_CLOSED"
    assert result["PRIOR_DRY_RUN_KEY_REUSED"] is False
    assert result["LIVE_AUTHORIZED"] is False
    assert result["LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED"] is False
    assert result["BLOCKS_NEW_ENTRY"] is True
    assert result["LIVE_RECONCILIATION_PROVEN"] is False
    assert result["ORDER_EFFECT"] == "NONE"
    assert result["SECRET_VALUE_ACCESS"] == "NONE"
    assert result["LIVE_CANARY_CYBERSECURITY_GATE"] == "NOT_PASSED"
    assert "CANARY_SECRETREF_URI_ABSENT" in result["BLOCKERS"]
    assert result["CANONICAL_NEXT_STEP"].startswith("OWNER_ACTIONS_CREATE_OR_SELECT_")


def test_canary_trade_capability_attestation_rejects_wrong_owner_go(tmp_path: Path) -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_trade_capability_attestation_v1 import (
        LiveCanaryTradeKeyAttestationError,
        evaluate_live_canary_canary_trade_capability_attestation_v1,
    )

    ops_local = tmp_path / ".ops_local"
    ops_local.mkdir()
    with pytest.raises(LiveCanaryTradeKeyAttestationError, match="OWNER_GO_MISBOUND"):
        evaluate_live_canary_canary_trade_capability_attestation_v1(
            ops_local_root=ops_local,
            origin_main_sha="abc1234",
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        )


def test_canary_trade_capability_attestation_proven_with_dedicated_secretref(
    tmp_path: Path,
) -> None:
    import json

    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_trade_capability_attestation_v1 import (
        OWNER_GO_TRADE_KEY_ATTESTATION,
        REQUIRED_SECRETREF_URI,
        TERMINAL_PROVEN,
        evaluate_live_canary_canary_trade_capability_attestation_v1,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        REUSED_BINDING_ACCOUNT_SCOPE,
        REUSED_BINDING_ENTITY,
        REUSED_BINDING_REGION,
        REUSED_BINDING_REST_HOST,
        REUSED_BINDING_VENUE,
        REQUIRED_CREDENTIAL_CLASS,
    )

    ops_local = tmp_path / ".ops_local"
    vault = (
        ops_local
        / "section_11_13_5_live_canary_minimum_exposure"
        / "secrets"
        / "secretref_vault.json"
    )
    vault.parent.mkdir(parents=True)
    vault.write_text(
        json.dumps(
            {
                REQUIRED_SECRETREF_URI: {
                    "api_key": "A" * 36,
                    "api_secret": "B" * 32,
                    "passphrase": "C" * 14,
                }
            }
        ),
        encoding="utf-8",
    )
    # Distinct prior dry-run material must not equal canary material.
    dry = ops_local / "section_11_13_4_live_dry_run_order_plan" / "secrets" / "secretref_vault.json"
    dry.parent.mkdir(parents=True)
    dry.write_text(
        json.dumps(
            {
                "secretref://vault/peak-trade/live-dry-run-order-plan/okx": {
                    "api_key": "D" * 36,
                    "api_secret": "E" * 32,
                    "passphrase": "F" * 14,
                }
            }
        ),
        encoding="utf-8",
    )
    owner_perm = {
        "READ": True,
        "TRADE": True,
        "WITHDRAW": False,
        "credential_class": REQUIRED_CREDENTIAL_CLASS,
        "secretref_uri": REQUIRED_SECRETREF_URI,
        "venue": REUSED_BINDING_VENUE,
        "entity": REUSED_BINDING_ENTITY,
        "region": REUSED_BINDING_REGION,
        "rest_host": REUSED_BINDING_REST_HOST,
        "account_scope": REUSED_BINDING_ACCOUNT_SCOPE,
    }
    result = evaluate_live_canary_canary_trade_capability_attestation_v1(
        ops_local_root=ops_local,
        origin_main_sha="abc1234",
        owner_go=OWNER_GO_TRADE_KEY_ATTESTATION,
        owner_permission_attestation=owner_perm,
    )
    assert result["TERMINAL_STATE"] == TERMINAL_PROVEN
    assert result["TRADE_ATTESTATION"] is True
    assert result["WITHDRAW_ATTESTATION"] is False
    assert result["READ_ATTESTATION"] is True
    assert result["SECRETREF_STATUS"] == "RESOLVED"
    assert result["CANARY_TRADE_KEY_BINDING"] == "PROVEN"
    assert result["PRIOR_DRY_RUN_KEY_REUSED"] is False
    assert result["LIVE_AUTHORIZED"] is False
    assert result["LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED"] is False
    assert result["BLOCKS_NEW_ENTRY"] is True
    assert result["LIVE_CANARY_CYBERSECURITY_GATE"] == "NOT_PASSED"
    assert result["EARLIEST_UNRESOLVED_DEPENDENCY"] == "OWNER_GO_EXCHANGE_TRUTH_ADOPTION"
    assert "SEALED_PRIOR_DRY_RUN_KEY_TRADE_FALSE_NOT_REUSABLE" not in result["BLOCKERS"]


def test_exchange_truth_adoption_rejects_wrong_owner_go(tmp_path: Path) -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exchange_truth_adoption_v1 import (
        LiveCanaryExchangeTruthAdoptionError,
        evaluate_exchange_truth_adoption_v1,
    )

    with pytest.raises(LiveCanaryExchangeTruthAdoptionError, match="OWNER_GO_MISBOUND"):
        evaluate_exchange_truth_adoption_v1(
            repo_root=tmp_path,
            origin_main_sha="abc1234",
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            trade_key_attestation={},
        )


def test_exchange_truth_adoption_fail_closed_without_trade_attestation(tmp_path: Path) -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exchange_truth_adoption_v1 import (
        STATUS_NOT_ADOPTED,
        TERMINAL_FAIL_CLOSED,
        evaluate_exchange_truth_adoption_v1,
    )

    # Minimal repo layout so forensic sealed evidence can resolve from real repo.
    repo = Path(__file__).resolve().parents[2]
    result = evaluate_exchange_truth_adoption_v1(
        repo_root=repo,
        origin_main_sha="abc1234",
        trade_key_attestation={},
    )
    assert result["TERMINAL_STATE"] == TERMINAL_FAIL_CLOSED
    assert result["EXCHANGE_TRUTH_ADOPTION_STATUS"] == STATUS_NOT_ADOPTED
    assert result["BLOCKS_NEW_ENTRY"] is True
    assert result["LIVE_AUTHORIZED"] is False
    assert result["LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED"] is False
    assert result["LIVE_CANARY_CYBERSECURITY_GATE"] == "NOT_PASSED"
    assert "TRADE_KEY_ATTESTATION_INPUT_ABSENT" in result["BLOCKERS"]
    _ = tmp_path


def test_exchange_truth_adoption_adopted_proven_keeps_cyber_gate_blocked() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        REUSED_BINDING_ACCOUNT_SCOPE,
        REUSED_BINDING_ENTITY,
        REUSED_BINDING_REGION,
        REUSED_BINDING_REST_HOST,
        REUSED_BINDING_VENUE,
        REQUIRED_CREDENTIAL_CLASS,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exchange_truth_adoption_v1 import (
        REQUIRED_SECRETREF_URI,
        STATUS_ADOPTED_PROVEN,
        TERMINAL_ADOPTED_CYBER_NOT_PASSED,
        evaluate_exchange_truth_adoption_v1,
    )

    repo = Path(__file__).resolve().parents[2]
    att = {
        "READ_ATTESTATION": True,
        "TRADE_ATTESTATION": True,
        "WITHDRAW_ATTESTATION": False,
        "KEY_BINDING_STATUS": "PROVEN",
        "CANARY_TRADE_KEY_BINDING": "PROVEN",
        "SECRETREF_STATUS": "RESOLVED",
        "SECRETREF_URI_CONTRACT": REQUIRED_SECRETREF_URI,
        "VENUE": REUSED_BINDING_VENUE,
        "LEGAL_ENTITY": REUSED_BINDING_ENTITY,
        "REGION": REUSED_BINDING_REGION,
        "REST_HOST": REUSED_BINDING_REST_HOST,
        "ACCOUNT_SCOPE": REUSED_BINDING_ACCOUNT_SCOPE,
        "KEY_CLASS": REQUIRED_CREDENTIAL_CLASS,
        "PRIOR_DRY_RUN_KEY_REUSED": False,
        "OKX_RESTRICTIONS_AFTER_RESET": "24h_no_withdrawals_and_no_p2p_sell",
    }
    result = evaluate_exchange_truth_adoption_v1(
        repo_root=repo,
        origin_main_sha="20f2eb51d933f67b7ff0d57d7aef94b767e68f99",
        trade_key_attestation=att,
        okx_temp_security_clearance_evidence_present=False,
    )
    assert result["EXCHANGE_TRUTH_ADOPTION_STATUS"] == STATUS_ADOPTED_PROVEN
    assert result["TERMINAL_STATE"] == TERMINAL_ADOPTED_CYBER_NOT_PASSED
    assert result["LIVE_CANARY_CYBERSECURITY_GATE"] == "NOT_PASSED"
    assert result["BLOCKS_NEW_ENTRY"] is True
    assert result["LIVE_RECONCILIATION_PROVEN"] is False
    assert result["LIVE_AUTHORIZED"] is False
    assert result["LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED"] is False
    assert result["LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN"] is False
    assert result["ECONOMIC_BASELINE_ADOPTION_STATUS"] == "OWNER_POLICIES_REQUIRED_NOT_ADOPTED"
    assert result["ECONOMIC_DIVERGENCE_STATUS"] == "UNRESOLVED_BLOCKS_NEW_ENTRY"
    assert result["OWNER_ECONOMIC_BASELINE_POLICIES_ADOPTED_BY_THIS_GO"] is False
    assert result["OKX_TEMP_SECURITY_RESTRICTION"] == "24h_no_withdrawals_and_no_p2p_sell"
    assert result["OKX_TEMP_SECURITY_RESTRICTION_BYPASS_FORBIDDEN"] is True
    assert "LIVE_RECONCILIATION_PROVEN_FALSE" in result["GATE_BLOCKERS"]
    assert "BLOCKS_NEW_ENTRY_OR_UNRESOLVED_DIVERGENCE" in result["GATE_BLOCKERS"]
    assert "OKX_TEMP_SECURITY_RESTRICTION_CLEARANCE_EVIDENCE_ABSENT" in result["GATE_BLOCKERS"]
    assert result["EARLIEST_UNRESOLVED_DEPENDENCY"] == "LIVE_RECONCILIATION_PROVEN_FALSE"
    assert result["CANONICAL_NEXT_STEP"] != "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
    assert result["EXCHANGE_TRUTH_ADOPTION_IS_NOT_CANARY_AUTHORIZATION"] is True
    assert result["EXCHANGE_TRUTH_ADOPTION_IS_NOT_GENERAL_LIVE_AUTHORIZATION"] is True


def test_live_canary_cybersecurity_gate_requires_exchange_truth_when_supplied() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cybersecurity_canary_gate_v1 import (
        evaluate_live_canary_cybersecurity_gate_v1,
    )

    result = evaluate_live_canary_cybersecurity_gate_v1(
        productive_surface_merged_to_origin_main=True,
        trade_attestation=True,
        withdraw_attestation=False,
        read_attestation=True,
        permission_attestation={"READ": True, "TRADE": True, "WITHDRAW": False},
        exchange_truth_adoption_status="OWNER_POLICIES_REQUIRED_NOT_ADOPTED",
        canary_key_binding_status="PROVEN",
        secretref_status="RESOLVED",
        okx_temp_security_restriction="24h_no_withdrawals_and_no_p2p_sell",
        okx_temp_security_clearance_evidence_present=False,
        canary_credential_isolation_proven=True,
        live_testnet_isolation_proven=True,
        default_block_fail_closed_proven=True,
        one_shot_owner_go_separation_proven=True,
    )
    assert result["LIVE_CANARY_CYBERSECURITY_GATE"] == "NOT_PASSED"
    assert "EXCHANGE_TRUTH_ADOPTION_NOT_ADOPTED" in result["BLOCKERS"]
    assert "OKX_TEMP_SECURITY_RESTRICTION_CLEARANCE_EVIDENCE_ABSENT" in result["BLOCKERS"]


def test_economic_baseline_rejects_wrong_owner_go(tmp_path: Path) -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.economic_baseline_and_okx_clearance_v1 import (
        EconomicBaselineAndOkxClearanceError,
        evaluate_economic_baseline_and_okx_clearance_v1,
    )

    with pytest.raises(EconomicBaselineAndOkxClearanceError, match="OWNER_GO_MISBOUND"):
        evaluate_economic_baseline_and_okx_clearance_v1(
            repo_root=tmp_path,
            origin_main_sha="abc",
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            reconciliation_eval={"ALL_LAYERS_MATCH": True},
            exchange_snapshot={},
            local_expected_state_adopted={},
            okx_clearance={},
        )


def test_economic_baseline_recon_proven_clearance_absent_blocks_cyber_gate() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        REUSED_BINDING_ACCOUNT_SCOPE,
        REUSED_BINDING_ENTITY,
        REUSED_BINDING_REGION,
        REUSED_BINDING_REST_HOST,
        REUSED_BINDING_VENUE,
        REQUIRED_CREDENTIAL_CLASS,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.economic_baseline_and_okx_clearance_v1 import (
        CLEARANCE_ABSENT_OR_UNPROVEN,
        TERMINAL_RECON_PROVEN_CLEARANCE_UNPROVEN,
        evaluate_economic_baseline_and_okx_clearance_v1,
        evaluate_okx_temp_security_clearance_v1,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exchange_truth_adoption_v1 import (
        REQUIRED_SECRETREF_URI,
        STATUS_ADOPTED_PROVEN,
    )

    repo = Path(__file__).resolve().parents[2]
    sealed = (
        repo
        / "evidence/ops/section_11_13_5_economic_baseline_and_okx_clearance_v1/20260812T153425Z"
    )
    exchange = json.loads(
        (sealed / "EXCHANGE_SNAPSHOT.sanitized.json").read_text(encoding="utf-8")
    )["layers"]
    local = json.loads(
        (sealed / "LOCAL_EXPECTED_STATE_ADOPTED.sanitized.json").read_text(encoding="utf-8")
    )["layers"]
    recon = json.loads((sealed / "RECONCILIATION_AFTER_ADOPTION.json").read_text(encoding="utf-8"))
    clearance = evaluate_okx_temp_security_clearance_v1(
        restriction_still_active=True,
        clearance_evidence_present_proven=False,
        evidence_source="TEST_SOURCE",
        observed_at_utc="2026-08-12T15:34:25Z",
        restriction_expires_at_local="2026-08-13T15:48:50+02:00",
    )
    att = {
        "READ_ATTESTATION": True,
        "TRADE_ATTESTATION": True,
        "WITHDRAW_ATTESTATION": False,
        "KEY_BINDING_STATUS": "PROVEN",
        "SECRETREF_STATUS": "RESOLVED",
        "SECRETREF_URI_CONTRACT": REQUIRED_SECRETREF_URI,
        "VENUE": REUSED_BINDING_VENUE,
        "LEGAL_ENTITY": REUSED_BINDING_ENTITY,
        "REGION": REUSED_BINDING_REGION,
        "REST_HOST": REUSED_BINDING_REST_HOST,
        "ACCOUNT_SCOPE": REUSED_BINDING_ACCOUNT_SCOPE,
        "KEY_CLASS": REQUIRED_CREDENTIAL_CLASS,
        "PRIOR_DRY_RUN_KEY_REUSED": False,
    }
    result = evaluate_economic_baseline_and_okx_clearance_v1(
        repo_root=repo,
        origin_main_sha="74a32e2db1a383dd6ebe0f7ce8f2edd11a915074",
        reconciliation_eval=recon,
        exchange_snapshot=exchange,
        local_expected_state_adopted=local,
        okx_clearance=clearance,
        productive_private_read_summary={"GET_REQUEST_COUNT": 4, "WRITE_REQUEST_COUNT": 0},
        trade_key_attestation=att,
    )
    assert result["EXCHANGE_TRUTH_ADOPTION_STATUS"] == STATUS_ADOPTED_PROVEN
    assert result["LIVE_RECONCILIATION_PROVEN"] is True
    assert result["BLOCKS_NEW_ENTRY"] is False
    assert result["ECONOMIC_DIVERGENCE_STATUS"] == "RESOLVED_NO_UNRESOLVED_DIVERGENCE"
    assert result["OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE"] == CLEARANCE_ABSENT_OR_UNPROVEN
    assert result["LIVE_CANARY_CYBERSECURITY_GATE"] == "NOT_PASSED"
    assert result["TERMINAL_STATE"] == TERMINAL_RECON_PROVEN_CLEARANCE_UNPROVEN
    assert result["LIVE_AUTHORIZED"] is False
    assert result["LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED"] is False
    assert result["ORDER_EFFECT"] == "NONE"
    assert "OKX_TEMP_SECURITY_RESTRICTION_CLEARANCE_EVIDENCE_ABSENT" in result["GATE_BLOCKERS"]
    assert result["CANONICAL_NEXT_STEP"] != "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"


def test_sealed_economic_baseline_evidence_verifier_pass() -> None:
    from scripts.ops.verify_section_11_13_5_economic_baseline_and_okx_clearance_v1 import (
        verify_section_11_13_5_economic_baseline_and_okx_clearance_evidence_v1,
    )

    repo = Path(__file__).resolve().parents[2]
    root = (
        repo
        / "evidence/ops/section_11_13_5_economic_baseline_and_okx_clearance_v1/20260812T153425Z"
    )
    result = verify_section_11_13_5_economic_baseline_and_okx_clearance_evidence_v1(root)
    assert result["ok"] is True
    assert result["MANIFEST_VERIFY_RC"] == 0
    assert result["LIVE_RECONCILIATION_PROVEN"] is True
    assert result["BLOCKS_NEW_ENTRY"] is False
    assert result["OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE"] == "ABSENT_OR_UNPROVEN"
    assert result["LIVE_CANARY_CYBERSECURITY_GATE"] == "NOT_PASSED"


def test_cybersecurity_gate_passes_only_with_full_prerequisites() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cybersecurity_canary_gate_v1 import (
        evaluate_live_canary_cybersecurity_gate_v1,
    )

    blocked = evaluate_live_canary_cybersecurity_gate_v1(
        productive_surface_merged_to_origin_main=True,
        trade_attestation=True,
        withdraw_attestation=False,
        read_attestation=True,
        permission_attestation={"READ": True, "TRADE": True, "WITHDRAW": False},
        exchange_truth_adoption_status="ADOPTED_PROVEN",
        canary_key_binding_status="PROVEN",
        secretref_status="RESOLVED",
        okx_temp_security_restriction="24h_no_withdrawals_and_no_p2p_sell",
        okx_temp_security_clearance_evidence_present=False,
        canary_credential_isolation_proven=True,
        live_testnet_isolation_proven=True,
        default_block_fail_closed_proven=True,
        one_shot_owner_go_separation_proven=True,
        live_reconciliation_proven=True,
        blocks_new_entry=False,
        unresolved_economic_divergence_blocks_new_entry=False,
    )
    assert blocked["LIVE_CANARY_CYBERSECURITY_GATE"] == "NOT_PASSED"
    assert "OKX_TEMP_SECURITY_RESTRICTION_CLEARANCE_EVIDENCE_ABSENT" in blocked["BLOCKERS"]

    passed = evaluate_live_canary_cybersecurity_gate_v1(
        productive_surface_merged_to_origin_main=True,
        trade_attestation=True,
        withdraw_attestation=False,
        read_attestation=True,
        permission_attestation={"READ": True, "TRADE": True, "WITHDRAW": False},
        exchange_truth_adoption_status="ADOPTED_PROVEN",
        canary_key_binding_status="PROVEN",
        secretref_status="RESOLVED",
        okx_temp_security_restriction=None,
        okx_temp_security_clearance_evidence_present=True,
        canary_credential_isolation_proven=True,
        live_testnet_isolation_proven=True,
        default_block_fail_closed_proven=True,
        one_shot_owner_go_separation_proven=True,
        live_reconciliation_proven=True,
        blocks_new_entry=False,
        unresolved_economic_divergence_blocks_new_entry=False,
    )
    assert passed["LIVE_CANARY_CYBERSECURITY_GATE"] == "PASS"
    assert passed["LIVE_AUTHORIZED"] is False
    assert passed["NEW_CANARY_OWNER_GO_GRANTED"] is False
    binding = passed["INSTRUMENT_BINDING_SECURITY"]
    assert binding["instrument_id"] == "BTC-USD_UM_XPERP-310404"
    assert binding["inst_type"] == "FUTURES"
    assert binding["prior_swap_instrument_pass_not_inherited"] is True
    assert binding["demo_310328_alias_forbidden"] is True
