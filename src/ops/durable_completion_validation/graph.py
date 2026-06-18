"""Static explicit validation graph for durable completion proof binding."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.ops.durable_completion_validation.identity import sorted_unique
from src.ops.durable_completion_validation.models import ValidationContext, ValidationResult

VALIDATOR_RECONCILIATION = "reconciliation"
VALIDATOR_RECOVERY = "recovery"
VALIDATOR_TRACEABILITY = "traceability"
VALIDATOR_OPERATOR_CLOSURE = "operator_closure"

PROOF_BINDING_VALIDATION_GRAPH: dict[str, tuple[str, ...]] = {
    VALIDATOR_RECONCILIATION: (),
    VALIDATOR_RECOVERY: (),
    VALIDATOR_TRACEABILITY: (VALIDATOR_RECOVERY,),
    VALIDATOR_OPERATOR_CLOSURE: (VALIDATOR_TRACEABILITY, VALIDATOR_RECOVERY),
}

PROOF_BINDING_VALIDATION_ORDER: tuple[str, ...] = (
    VALIDATOR_RECONCILIATION,
    VALIDATOR_RECOVERY,
    VALIDATOR_TRACEABILITY,
    VALIDATOR_OPERATOR_CLOSURE,
)

ValidatorFn = Callable[[ValidationContext], ValidationResult]


def proof_binding_validation_graph_is_cycle_free() -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        for dependency in PROOF_BINDING_VALIDATION_GRAPH.get(node, ()):
            if not visit(dependency):
                return False
        visiting.remove(node)
        visited.add(node)
        return True

    return all(visit(node) for node in PROOF_BINDING_VALIDATION_GRAPH)


def _load_validators() -> dict[str, ValidatorFn]:
    from src.ops.durable_completion_validation.validators import (
        operator_closure,
        reconciliation,
        recovery,
        traceability,
    )

    return {
        VALIDATOR_RECONCILIATION: reconciliation.validate_pe31_integration_proof,
        VALIDATOR_RECOVERY: recovery.validate_pe35_recovery_boundary_proof,
        VALIDATOR_TRACEABILITY: traceability.validate_pe37_traceability_proof,
        VALIDATOR_OPERATOR_CLOSURE: operator_closure.validate_pe25_operator_closure_proof,
    }


def execute_proof_binding_validation_graph(
    context: ValidationContext,
    *,
    validators: dict[str, ValidatorFn] | None = None,
) -> ValidationResult:
    """Execute proof-binding validators in explicit graph order with fail-closed aggregation."""
    active_validators = validators if validators is not None else _load_validators()
    fail_reasons: list[str] = []
    completed: set[str] = set()
    failed: set[str] = set()

    for validator_id in PROOF_BINDING_VALIDATION_ORDER:
        if validator_id not in PROOF_BINDING_VALIDATION_GRAPH:
            fail_reasons.append(f"validation_graph: unknown validator {validator_id!r}")
            failed.add(validator_id)
            continue

        if validator_id not in active_validators:
            fail_reasons.append(
                f"validation_graph: missing validator implementation for {validator_id!r}"
            )
            failed.add(validator_id)
            continue

        dependencies = PROOF_BINDING_VALIDATION_GRAPH[validator_id]
        missing_dependencies = [dep for dep in dependencies if dep not in completed]
        if missing_dependencies:
            fail_reasons.append(
                f"validation_graph: missing dependency for {validator_id!r}: {missing_dependencies}"
            )
            failed.add(validator_id)
            continue

        failed_dependencies = [dep for dep in dependencies if dep in failed]
        if failed_dependencies:
            fail_reasons.append(
                f"validation_graph: dependency failed for {validator_id!r}: {failed_dependencies}"
            )
            failed.add(validator_id)
            continue

        validator = active_validators[validator_id]
        try:
            result = validator(context)
        except Exception as exc:  # noqa: BLE001 - fail-closed graph boundary
            fail_reasons.append(
                f"validation_graph: validator {validator_id!r} raised {type(exc).__name__}: {exc}"
            )
            failed.add(validator_id)
            continue

        fail_reasons.extend(result.fail_reasons)
        if result.fail_reasons:
            failed.add(validator_id)
        else:
            completed.add(validator_id)
            context.completed_validators.add(validator_id)

    return ValidationResult(fail_reasons=tuple(sorted_unique(fail_reasons)))
