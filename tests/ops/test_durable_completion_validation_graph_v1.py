"""Tests for durable completion validation graph architecture v1."""

from __future__ import annotations

from typing import Any

from dataclasses import replace

import pytest

from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
    default_minimal_completion_integration_input,
    evaluate_durable_run_primary_evidence_completion_integration,
    validate_durable_run_primary_evidence_completion_integration_input,
)
from src.ops.durable_completion_validation.graph import (
    PROOF_BINDING_VALIDATION_GRAPH,
    PROOF_BINDING_VALIDATION_ORDER,
    VALIDATOR_OPERATOR_CLOSURE,
    VALIDATOR_RECONCILIATION,
    VALIDATOR_RECOVERY,
    VALIDATOR_TRACEABILITY,
    execute_proof_binding_validation_graph,
    proof_binding_validation_graph_is_cycle_free,
)
from src.ops.durable_completion_validation.models import ValidationContext, ValidationResult
from src.ops.durable_completion_validation.validators.reconciliation import (
    validate_pe21_reconciliation_result_manifest_integrity,
)


def _minimal_context(**overrides: Any) -> ValidationContext:
    integration_input = default_minimal_completion_integration_input()
    context = ValidationContext(integration_input=integration_input)
    for key, value in overrides.items():
        setattr(context, key, value)
    return context


def test_graph_is_cycle_free() -> None:
    assert proof_binding_validation_graph_is_cycle_free() is True


def test_graph_explicit_order_matches_dependencies() -> None:
    seen: set[str] = set()
    for validator_id in PROOF_BINDING_VALIDATION_ORDER:
        for dependency in PROOF_BINDING_VALIDATION_GRAPH[validator_id]:
            assert dependency in seen, f"{validator_id} depends on {dependency} before it runs"
        seen.add(validator_id)


def test_graph_missing_validator_is_fail_closed() -> None:
    context = _minimal_context()
    partial_validators = {
        VALIDATOR_RECONCILIATION: lambda _ctx: ValidationResult(),
        VALIDATOR_RECOVERY: lambda _ctx: ValidationResult(),
        VALIDATOR_TRACEABILITY: lambda _ctx: ValidationResult(),
    }
    result = execute_proof_binding_validation_graph(
        context,
        validators=partial_validators,
    )
    assert any("missing validator implementation" in reason for reason in result.fail_reasons)
    assert VALIDATOR_OPERATOR_CLOSURE not in context.completed_validators


def test_graph_missing_dependency_is_fail_closed() -> None:
    context = _minimal_context()

    def failing_recovery(_ctx: ValidationContext) -> ValidationResult:
        return ValidationResult(fail_reasons=("pe35_proof: recovery_boundary_bound must be true",))

    validators = {
        VALIDATOR_RECONCILIATION: lambda _ctx: ValidationResult(),
        VALIDATOR_RECOVERY: failing_recovery,
        VALIDATOR_TRACEABILITY: lambda _ctx: ValidationResult(fail_reasons=("should not run",)),
        VALIDATOR_OPERATOR_CLOSURE: lambda _ctx: ValidationResult(fail_reasons=("should not run",)),
    }
    result = execute_proof_binding_validation_graph(context, validators=validators)
    assert any("dependency failed for 'traceability'" in reason for reason in result.fail_reasons)
    assert any(
        "dependency failed for 'operator_closure'" in reason for reason in result.fail_reasons
    )
    assert VALIDATOR_TRACEABILITY not in context.completed_validators
    assert VALIDATOR_OPERATOR_CLOSURE not in context.completed_validators


def test_graph_exception_is_fail_closed() -> None:
    context = _minimal_context()

    def exploding(_ctx: ValidationContext) -> ValidationResult:
        raise RuntimeError("validator exploded")

    validators = {
        VALIDATOR_RECONCILIATION: exploding,
        VALIDATOR_RECOVERY: lambda _ctx: ValidationResult(),
        VALIDATOR_TRACEABILITY: lambda _ctx: ValidationResult(),
        VALIDATOR_OPERATOR_CLOSURE: lambda _ctx: ValidationResult(),
    }
    result = execute_proof_binding_validation_graph(context, validators=validators)
    assert any(
        "validator 'reconciliation' raised RuntimeError: validator exploded" in reason
        for reason in result.fail_reasons
    )


def test_graph_aggregates_fail_reasons_from_executed_validators() -> None:
    context = _minimal_context()
    validators = {
        VALIDATOR_RECONCILIATION: lambda _ctx: ValidationResult(fail_reasons=("alpha",)),
        VALIDATOR_RECOVERY: lambda _ctx: ValidationResult(fail_reasons=("beta",)),
        VALIDATOR_TRACEABILITY: lambda _ctx: ValidationResult(fail_reasons=("gamma",)),
        VALIDATOR_OPERATOR_CLOSURE: lambda _ctx: ValidationResult(fail_reasons=("delta",)),
    }
    result = execute_proof_binding_validation_graph(context, validators=validators)
    assert set(result.fail_reasons) == {
        "alpha",
        "beta",
        "validation_graph: dependency failed for 'traceability': ['recovery']",
        "validation_graph: dependency failed for 'operator_closure': ['traceability', 'recovery']",
    }


def test_reconciliation_manifest_validator_matches_input_validation_path() -> None:
    integration_input = default_minimal_completion_integration_input()
    direct = validate_pe21_reconciliation_result_manifest_integrity(integration_input)
    input_fail_reasons = validate_durable_run_primary_evidence_completion_integration_input(
        integration_input
    )
    manifest_reasons = [
        reason
        for reason in input_fail_reasons
        if reason.startswith("pe21_reconciliation_result_manifest")
    ]
    assert list(direct.fail_reasons) == manifest_reasons


def test_fill_state_manifest_validator_matches_input_validation_path() -> None:
    integration_input = default_minimal_completion_integration_input()
    direct = validate_pe21_reconciliation_result_manifest_integrity(integration_input)
    input_fail_reasons = validate_durable_run_primary_evidence_completion_integration_input(
        integration_input
    )
    fill_manifest_reasons = [
        reason for reason in input_fail_reasons if reason.startswith("pe21_fill_state_manifest")
    ]
    assert not fill_manifest_reasons
    assert not direct.fail_reasons


def test_evaluate_graph_compatibility_happy_path() -> None:
    integration_input = default_minimal_completion_integration_input()
    result = evaluate_durable_run_primary_evidence_completion_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["fail_reasons"] == []


def test_evaluate_graph_compatibility_pe31_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    broken = replace(
        integration_input,
        pe31_reconciliation_review_integration_proof=replace(
            integration_input.pe31_reconciliation_review_integration_proof,
            integration_proof_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(broken)
    assert result["integration_pass"] is False
    assert any("pe31_proof" in reason for reason in result["fail_reasons"])
