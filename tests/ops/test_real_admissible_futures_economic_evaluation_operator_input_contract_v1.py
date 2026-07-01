"""Contract tests for real admissible futures economic evaluation operator input v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.backtest import mv2_research_wiring_v1 as mv2_wiring
from src.backtest import (
    real_admissible_futures_economic_evaluation_operator_input_contract_v1 as contract,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / contract.CONTRACT_CONFIG_REL_PATH
RUNNER_SCRIPT = ROOT / "scripts" / "ops" / "run_economic_viability_evidence_evaluation_v1.py"


def test_contract_config_exists_and_version_bound() -> None:
    payload = contract.load_operator_input_contract_v1()
    assert payload["contract_version"] == contract.CONTRACT_VERSION
    assert payload["owner"] == contract.CONTRACT_OWNER
    assert payload["verdict"] == "OPERATOR_INPUT_CONTRACT_COMPLETE"
    assert payload["admissibility_verdict"] == "NO_REAL_ADMISSIBLE_EVIDENCE_PRESENT"


def test_operator_input_contract_ready_fail_closed() -> None:
    result = contract.assert_operator_input_contract_ready_v1()
    assert result.operator_input_contract_complete is True
    assert result.real_evaluation_permitted is False
    assert result.profitability_claim_allowed is False
    assert result.verdict.value == "OPERATOR_INPUT_CONTRACT_COMPLETE"
    assert result.admissibility_verdict == "NO_REAL_ADMISSIBLE_EVIDENCE_PRESENT"
    assert result.unresolved_operator_fields
    assert result.blocked_no_evidence_fields


def test_no_policy_gap_fields() -> None:
    result = contract.evaluate_operator_input_readiness_v1()
    assert not result.policy_gap_fields


def test_resolved_canonical_bindings_present() -> None:
    specs = contract.parse_operator_input_field_specs_v1(contract.load_operator_input_contract_v1())
    resolved_names = {spec.field_name for spec in specs if spec.resolved}
    for field_name in (
        "instrument_id",
        "contract_type",
        "futures_only",
        "bitcoin_direction_allowed",
        "cost_model_version",
        "fee_model_version",
        "slippage_model_version",
        "funding_model_version",
        "execution_model_version",
        "economic_validity_policy_version",
        "economic_validity_thresholds",
    ):
        assert field_name in resolved_names


def test_unresolved_operator_fields_are_required_staging_inputs() -> None:
    result = contract.evaluate_operator_input_readiness_v1()
    for field_name in (
        "dataset_path",
        "dataset_manifest_path",
        "provenance_source_type",
        "provenance_ref",
        "fee_bps",
        "slippage_bps",
        "evaluation_config_path",
        "evidence_output_dir",
    ):
        assert field_name in result.unresolved_operator_fields


def test_fixture_and_spot_staging_rejected() -> None:
    violations = contract.validate_staged_operator_inputs_v1(
        {
            "instrument_id": mv2_wiring.MV2_REQUIRED_INSTRUMENT_ID,
            "provenance_source_type": "test_fixture",
            "provenance_ref": "tests/fixtures/sample",
            "provenance_venue_id": "neutral_offline_venue_v1",
            "provenance_generation_method": "deterministic_test_fixture",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
        }
    )
    assert any("provenance_source_type_forbidden" in item for item in violations)
    assert any("provenance_ref_test_path_forbidden" in item for item in violations)
    assert any("provenance_generation_method_forbidden" in item for item in violations)


def test_kraken_and_btc_tokens_rejected_in_staging() -> None:
    violations = contract.validate_staged_operator_inputs_v1(
        {
            "instrument_id": "inst-btc-usdt-perp",
            "provenance_source_type": "operator_staged_futures_v1",
            "provenance_ref": "operator/staged/kraken_export_v1",
            "provenance_venue_id": "kraken_futures_v1",
            "provenance_generation_method": "operator_curated_versioned_export",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
        }
    )
    assert "instrument_id_not_mv2_required" in violations
    assert "instrument_id_forbidden_token" in violations
    assert "provenance_ref_forbidden_token" in violations
    assert "provenance_venue_id_forbidden_token" in violations


def test_implicit_zero_cost_rejected() -> None:
    violations = contract.validate_staged_operator_inputs_v1(
        {
            "instrument_id": mv2_wiring.MV2_REQUIRED_INSTRUMENT_ID,
            "provenance_source_type": "operator_staged_futures_v1",
            "provenance_ref": "operator/staged/eth_perp_neutral_v1",
            "provenance_venue_id": "neutral_offline_venue_v1",
            "provenance_generation_method": "operator_curated_versioned_export",
            "fee_bps": 0.0,
            "slippage_bps": 5.0,
        }
    )
    assert "fee_bps_implicit_zero_forbidden" in violations


def test_profitability_claim_without_real_evaluation_rejected() -> None:
    violations = contract.validate_staged_operator_inputs_v1(
        {
            "instrument_id": mv2_wiring.MV2_REQUIRED_INSTRUMENT_ID,
            "provenance_source_type": "operator_staged_futures_v1",
            "provenance_ref": "operator/staged/eth_perp_neutral_v1",
            "provenance_venue_id": "neutral_offline_venue_v1",
            "provenance_generation_method": "operator_curated_versioned_export",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
            "profitability_claim_allowed": True,
            "economic_validity_result": "PASS",
        }
    )
    assert "profitability_claim_forbidden" in violations
    assert "economic_validity_pass_claim_forbidden_without_real_evaluation" in violations


def test_real_evaluation_flag_rejected() -> None:
    with pytest.raises(contract.OperatorInputContractError, match="real_evaluation_not_permitted"):
        contract.validate_staged_operator_inputs_v1({}, allow_real_evaluation=True)


def test_runner_has_no_kraken_btc_spot_canonicalization() -> None:
    source = RUNNER_SCRIPT.read_text(encoding="utf-8").lower()
    assert "kraken" not in source
    assert "xbt" not in source
    assert "btc" not in source


def test_contract_module_forbids_kraken_btc_spot_tokens_in_staging() -> None:
    violations = contract.validate_staged_operator_inputs_v1(
        {
            "instrument_id": "inst-btc-usdt-perp",
            "provenance_source_type": "operator_staged_futures_v1",
            "provenance_ref": "operator/staged/kraken_export_v1",
            "provenance_venue_id": "kraken_futures_v1",
            "provenance_generation_method": "operator_curated_versioned_export",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
        }
    )
    assert violations


def test_serialize_manifest_is_deterministic() -> None:
    first = contract.serialize_operator_input_contract_manifest_v1()
    second = contract.serialize_operator_input_contract_manifest_v1()
    assert first == second
    assert first["implementation_digest"] == contract.contract_implementation_digest()


def test_contract_json_matches_field_spec_count() -> None:
    payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    specs = contract.parse_operator_input_field_specs_v1(payload)
    assert len(specs) == len(payload["fields"])
    assert payload["operator_input_required_for_real_evaluation"] is True
    assert payload["real_evaluation_performed"] is False
    assert payload["real_admissible_futures_evidence_present"] is False
