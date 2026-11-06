"""Contract tests for canary_micro_live_readiness_v1."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = ["tests.meta.canary_micro_live_readiness_v1_fixtures"]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1 import PLAN_ARTIFACT_REL
from src.meta.learning_loop.canary_micro_live_readiness_v1 import (
    CANARY_CAPITAL_ENVELOPE_POLICY,
    CANARY_INPUT_ARTIFACT_REL,
    CANARY_MICRO_LIVE_READINESS_AUTHORITY_INVARIANTS,
    NON_LIVE_SLO_GATE_NAMES,
    READINESS_ARTIFACT_REL,
    CanaryMicroLiveReadinessError,
    build_autonomous_non_live_orchestration_to_canary_readiness_input_v1,
    build_canary_micro_live_readiness_evidence_v1,
    build_canary_readiness_input_request_from_plan_bundle,
    build_readiness_request_from_canary_input_bundle,
    default_canary_micro_live_readiness_request,
    default_canary_readiness_input_request,
    evaluate_autonomous_non_live_orchestration_to_canary_readiness_input_v1,
    evaluate_canary_micro_live_readiness_evidence_v1,
    produce_autonomous_non_live_orchestration_to_canary_readiness_input_v1,
    produce_canary_micro_live_readiness_evidence_v1,
    reverify_autonomous_non_live_orchestration_to_canary_readiness_input_v1,
    reverify_canary_micro_live_readiness_evidence_v1,
    serialize_autonomous_non_live_orchestration_to_canary_readiness_input_v1,
    serialize_canary_micro_live_readiness_evidence_v1,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from tests.meta.canary_micro_live_readiness_v1_fixtures import (
    build_bitcoin_plan_source,
    build_not_ready_plan_source,
    build_valid_canary_input_request,
    build_valid_readiness_request,
    minimal_invalid_digest,
    produce_canary_input_fixture,
    produce_full_step28_chain_fixtures,
    produce_readiness_fixture,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.canary_micro_live_readiness_v1.is_under_tmp",
        lambda _path: False,
    )


def _durable_output(tmp_path: Path, name: str) -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


# --- Contract A: autonomous_non_live_orchestration_to_canary_readiness_input_v1 ---


def test_canary_input_happy_path() -> None:
    contract = build_autonomous_non_live_orchestration_to_canary_readiness_input_v1()
    assert contract["canary_input_status"] == "READY"
    assert contract["offline_projection_only"] is True
    assert contract["readiness_authorized"] is False
    assert contract["live_authorized"] is False
    assert contract["runtime_authorized"] is False


def test_canary_input_deterministic_repeat() -> None:
    request = build_valid_canary_input_request()
    assert build_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
        request
    ) == build_autonomous_non_live_orchestration_to_canary_readiness_input_v1(request)


def test_canary_input_canonical_json_stability() -> None:
    contract = build_autonomous_non_live_orchestration_to_canary_readiness_input_v1()
    assert serialize_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
        contract
    ) == deterministic_json_dumps(contract)


def test_canary_input_producer_replay_and_manifest(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "canary_input_out")
    produce_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
        request=default_canary_readiness_input_request(),
        output_dir=out,
    )
    verified = reverify_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
        output_dir=out
    )
    ok, _msg = verify_manifest_sha256(out)
    assert ok
    assert verified["canary_input_status"] == "READY"


def test_canary_input_not_ready_for_blocked_plan() -> None:
    contract = build_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
        default_canary_readiness_input_request(build_not_ready_plan_source())
    )
    assert contract["canary_input_status"] in {"NOT_READY", "INVALID"}


def test_canary_input_rejects_bitcoin_plan_source() -> None:
    contract = build_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
        default_canary_readiness_input_request(build_bitcoin_plan_source())
    )
    assert contract["canary_input_status"] in {"NOT_READY", "INVALID"}
    assert "BITCOIN_INSTRUMENT_REJECTED" in contract["blocking_reasons"] or any(
        "BITCOIN" in reason for reason in contract["blocking_reasons"]
    )


@pytest.mark.parametrize(
    ("override", "expected_code"),
    [
        ({"readiness_authorization_requested": True}, "READINESS_AUTHORIZATION_REQUESTED"),
        ({"live_authorization_requested": True}, "LIVE_AUTHORIZATION_REQUESTED"),
        ({"activation_requested": True}, "ACTIVATION_REQUESTED"),
        ({"capital_limit_increase_requested": True}, "CAPITAL_LIMIT_INCREASE_REQUESTED"),
        ({"authority_lease_issuance_requested": True}, "AUTHORITY_LEASE_ISSUANCE_REQUESTED"),
    ],
)
def test_canary_input_rejects_forbidden_requests(override: dict, expected_code: str) -> None:
    contract = build_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
        build_valid_canary_input_request(**override)
    )
    assert contract["canary_input_status"] == "INVALID"
    assert expected_code in contract["blocking_reasons"]


def test_canary_input_futures_only_constraints() -> None:
    contract = build_autonomous_non_live_orchestration_to_canary_readiness_input_v1()
    assert contract["futures_only"] is True
    assert contract["bitcoin_direction_allowed"] is False
    assert contract["spot_allowed"] is False
    assert contract["synthetic_spot_allowed"] is False


def test_canary_input_from_plan_bundle(tmp_path: Path) -> None:
    from tests.meta.autonomous_non_live_orchestration_plan_v1_fixtures import (
        produce_plan_fixture,
    )

    plan_bundle = produce_plan_fixture(tmp_path, "plan_for_canary_input")
    request = build_canary_readiness_input_request_from_plan_bundle(plan_bundle)
    contract = build_autonomous_non_live_orchestration_to_canary_readiness_input_v1(request)
    assert contract["canary_input_status"] == "READY"


# --- Contract B: canary_micro_live_readiness_evidence_v1 ---


def test_readiness_default_is_not_ready() -> None:
    contract = build_canary_micro_live_readiness_evidence_v1()
    assert contract["readiness_status"] == "READINESS_NOT_READY"
    assert contract["decision_code"] == "READINESS_NOT_READY"
    assert contract["live_authorized"] is False
    assert contract["orders_allowed"] is False
    assert contract["scheduler_runtime_allowed"] is False
    assert contract["ready_for_operator_arming"] is False


def test_readiness_is_evidence_not_authority() -> None:
    contract = build_canary_micro_live_readiness_evidence_v1()
    assert contract["offline_readiness_evidence_only"] is True
    assert contract["readiness_does_not_activate"] is True
    assert contract["readiness_does_not_issue_authority"] is True
    assert contract["implicit_eligibility_pass"] is False
    assert contract["implicit_deploy_inactive_pass"] is False
    assert "READINESS_IS_EVIDENCE_NOT_AUTHORITY" in contract["prerequisite_reasons"]


def test_readiness_deterministic_repeat() -> None:
    request = build_valid_readiness_request()
    assert build_canary_micro_live_readiness_evidence_v1(
        request
    ) == build_canary_micro_live_readiness_evidence_v1(request)


def test_readiness_canonical_json_stability() -> None:
    contract = build_canary_micro_live_readiness_evidence_v1()
    assert serialize_canary_micro_live_readiness_evidence_v1(contract) == deterministic_json_dumps(
        contract
    )


def test_readiness_producer_replay_and_manifest(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "readiness_out")
    produce_canary_micro_live_readiness_evidence_v1(
        request=default_canary_micro_live_readiness_request(),
        output_dir=out,
    )
    verified = reverify_canary_micro_live_readiness_evidence_v1(output_dir=out)
    ok, _msg = verify_manifest_sha256(out)
    assert ok
    assert verified["readiness_status"] == "READINESS_NOT_READY"


def test_readiness_binds_capital_envelope_read_only() -> None:
    contract = build_canary_micro_live_readiness_evidence_v1()
    binding = contract["canary_capital_envelope_binding"]
    assert binding["total_limit_usd"] == CANARY_CAPITAL_ENVELOPE_POLICY["total_limit_usd"]
    assert binding["order_limit_usd"] == CANARY_CAPITAL_ENVELOPE_POLICY["order_limit_usd"]
    assert binding["daily_loss_limit_usd"] == CANARY_CAPITAL_ENVELOPE_POLICY["daily_loss_limit_usd"]
    assert binding["max_positions"] == CANARY_CAPITAL_ENVELOPE_POLICY["max_positions"]
    assert binding["capital_authority_issued"] is False


def test_readiness_binds_non_live_slo_policy_schema_only() -> None:
    contract = build_canary_micro_live_readiness_evidence_v1()
    binding = contract["non_live_slo_policy_binding"]
    assert binding["binding_mode"] == "READ_ONLY_POLICY_SCHEMA"
    gate_names = [gate["gate_name"] for gate in binding["gates"]]
    assert gate_names == list(NON_LIVE_SLO_GATE_NAMES)
    assert all(gate["measurement_status"] == "NOT_AVAILABLE" for gate in binding["gates"])
    assert all(gate["pass_status"] == "NOT_PROVEN" for gate in binding["gates"])


def test_readiness_candidate_metadata_not_bound() -> None:
    contract = build_canary_micro_live_readiness_evidence_v1()
    candidate = contract["bounded_live_canary_candidate"]
    assert candidate["binding_mode"] == "METADATA_ONLY_NO_ACTIVATION"
    for slot_name in ("venue_slot", "instrument_slot", "champion_slot", "challenger_slot"):
        assert candidate[slot_name]["status"] == "NOT_BOUND"


def test_readiness_blocked_for_canary_input_digest_mismatch() -> None:
    canary_input = build_autonomous_non_live_orchestration_to_canary_readiness_input_v1()
    contract = build_canary_micro_live_readiness_evidence_v1(
        default_canary_micro_live_readiness_request(
            canary_input,
            source_canary_input_digest=minimal_invalid_digest(),
        )
    )
    assert contract["readiness_status"] == "READINESS_BLOCKED"
    assert "CANARY_INPUT_DIGEST_MISMATCH" in contract["blocking_reasons"]


def test_readiness_invalid_for_bitcoin_instrument_scope() -> None:
    canary_input = build_autonomous_non_live_orchestration_to_canary_readiness_input_v1()
    canary_input = dict(canary_input)
    canary_input["instrument_scope"] = "BTC-USDT-SWAP"
    contract = build_canary_micro_live_readiness_evidence_v1(
        default_canary_micro_live_readiness_request(canary_input)
    )
    assert contract["readiness_status"] == "READINESS_INVALID"
    assert "BITCOIN_INSTRUMENT_REJECTED" in contract["blocking_reasons"]


@pytest.mark.parametrize(
    ("override", "expected_code"),
    [
        ({"readiness_activation_requested": True}, "READINESS_ACTIVATION_REQUESTED"),
        ({"readiness_arming_requested": True}, "READINESS_ARMING_REQUESTED"),
        (
            {"readiness_live_authorization_requested": True},
            "READINESS_LIVE_AUTHORIZATION_REQUESTED",
        ),
        ({"implicit_eligibility_pass_requested": True}, "IMPLICIT_ELIGIBILITY_PASS_REJECTED"),
        (
            {"implicit_deploy_inactive_pass_requested": True},
            "IMPLICIT_DEPLOY_INACTIVE_PASS_REJECTED",
        ),
        ({"capital_limit_increase_requested": True}, "CAPITAL_LIMIT_INCREASE_REQUESTED"),
    ],
)
def test_readiness_rejects_forbidden_requests(override: dict, expected_code: str) -> None:
    contract = build_canary_micro_live_readiness_evidence_v1(
        build_valid_readiness_request(**override)
    )
    assert contract["readiness_status"] == "READINESS_INVALID"
    assert expected_code in contract["blocking_reasons"]


def test_readiness_futures_only_constraints() -> None:
    contract = build_canary_micro_live_readiness_evidence_v1()
    assert contract["futures_only"] is True
    assert contract["bitcoin_direction_allowed"] is False
    assert contract["instrument_scope"] == "GENERIC-FUTURES-PERP-001"


def test_readiness_from_canary_input_bundle(tmp_path: Path) -> None:
    canary_bundle = produce_canary_input_fixture(tmp_path, "canary_bundle_for_readiness")
    request = build_readiness_request_from_canary_input_bundle(canary_bundle)
    contract = build_canary_micro_live_readiness_evidence_v1(request)
    assert contract["readiness_status"] == "READINESS_NOT_READY"


def test_full_step28_chain_fixtures(tmp_path: Path) -> None:
    plan, canary_input, readiness = produce_full_step28_chain_fixtures(tmp_path)
    assert (plan / PLAN_ARTIFACT_REL).is_file()
    assert (canary_input / CANARY_INPUT_ARTIFACT_REL).is_file()
    assert (readiness / READINESS_ARTIFACT_REL).is_file()


def test_authority_invariants_present() -> None:
    assert CANARY_MICRO_LIVE_READINESS_AUTHORITY_INVARIANTS["step28_offline_only"] is True
    assert (
        CANARY_MICRO_LIVE_READINESS_AUTHORITY_INVARIANTS["readiness_is_evidence_not_authority"]
        is True
    )
    assert CANARY_MICRO_LIVE_READINESS_AUTHORITY_INVARIANTS["runtime_effect"] is False
    assert CANARY_MICRO_LIVE_READINESS_AUTHORITY_INVARIANTS["non_authorizing"] is True
    assert CANARY_MICRO_LIVE_READINESS_AUTHORITY_INVARIANTS["live_authorized"] is False
    assert CANARY_MICRO_LIVE_READINESS_AUTHORITY_INVARIANTS["orders_allowed"] is False


def test_readiness_not_ready_even_when_canary_input_ready() -> None:
    canary_input = build_autonomous_non_live_orchestration_to_canary_readiness_input_v1()
    assert canary_input["canary_input_status"] == "READY"
    readiness = build_canary_micro_live_readiness_evidence_v1()
    assert readiness["readiness_status"] == "READINESS_NOT_READY"


def test_canary_input_rejects_missing_plan_bundle(tmp_path: Path) -> None:
    with pytest.raises(CanaryMicroLiveReadinessError):
        build_canary_readiness_input_request_from_plan_bundle(tmp_path / "missing")


def test_readiness_rejects_spot_market_type() -> None:
    canary_input = build_autonomous_non_live_orchestration_to_canary_readiness_input_v1()
    canary_input = dict(canary_input)
    canary_input["market_type"] = "SPOT"
    contract = build_canary_micro_live_readiness_evidence_v1(
        default_canary_micro_live_readiness_request(canary_input)
    )
    assert contract["readiness_status"] == "READINESS_INVALID"
    assert "SPOT_MARKET_TYPE_REJECTED" in contract["blocking_reasons"]
