"""Tests for durable completion validation graph architecture v1."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from dataclasses import replace

import pytest

from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
    classify_master_v2_binding_presence,
    default_minimal_completion_integration_input,
    evaluate_durable_run_primary_evidence_completion_integration,
    validate_durable_run_primary_evidence_completion_integration_input,
)
from src.ops.durable_completion_validation.graph import (
    PROOF_BINDING_VALIDATION_GRAPH,
    PROOF_BINDING_VALIDATION_ORDER,
    VALIDATOR_COMPLETION_CHAIN,
    VALIDATOR_EVENT_STREAM,
    VALIDATOR_OPERATOR_CLOSURE,
    VALIDATOR_RECONCILIATION,
    VALIDATOR_RECOVERY,
    VALIDATOR_TRACEABILITY,
    VALIDATOR_WALLCLOCK,
    execute_proof_binding_validation_graph,
    proof_binding_validation_graph_is_cycle_free,
)
from src.ops.durable_completion_validation.models import ValidationContext, ValidationResult
from src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0 import (
    ARTIFACT_FILL_STATE_SNAPSHOT,
    ManifestEntry,
    compute_manifest_digest,
)
from src.ops.bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0 import (
    evaluate_reconciliation_review_lifecycle_integration,
)
from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    evaluate_handoff_staleness_revocation_recovery_boundary,
)
from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
    evaluate_durable_evidence_traceability_boundary,
)
from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
    evaluate_operator_closure_lifecycle_integration,
)
from src.ops.durable_completion_validation.validators.recovery import (
    validate_recovery_proof_binding,
)
from src.ops.durable_completion_validation.validators.reconciliation import (
    validate_pe21_reconciliation_result_manifest_integrity,
    validate_reconciliation_proof_binding,
)
from src.ops.durable_completion_validation.validators.traceability import (
    validate_traceability_proof_binding,
)
from src.ops.durable_completion_validation.validators.operator_closure import (
    validate_operator_closure_proof_binding,
)
from src.ops.durable_completion_validation.validators.completion_chain import (
    validate_completion_proof_chain_binding,
)
from src.ops.durable_completion_validation.validators.wallclock import (
    validate_wallclock_proof_binding,
)
from src.ops.testnet_wallclock_duration_evidence_contract_v0 import (
    REQUIRED_WALLCLOCK_FIELD_NAMES,
    evaluate_wallclock_duration_evidence,
)
from src.ops.wallclock_session_evidence_v0 import evaluate_wallclock_evidence_fields


@lru_cache(maxsize=1)
def _cached_default_minimal_completion_integration_input():
    """Module-scoped cache: building minimal integration input runs full offline evidence chain."""
    return default_minimal_completion_integration_input()


def _glb019_result_for(integration_input):
    from src.ops.durable_completion_validation.validators.event_stream import (
        evaluate_glb019_event_stream_validation,
    )

    return evaluate_glb019_event_stream_validation(
        integration_input.glb019_event_stream_validation_input
    )


def _minimal_context(**overrides: Any) -> ValidationContext:
    integration_input = _cached_default_minimal_completion_integration_input()
    context = ValidationContext(
        integration_input=integration_input,
        glb019_result=_glb019_result_for(integration_input),
    )
    for key, value in overrides.items():
        setattr(context, key, value)
    return context


def _graph_context(integration_input, **overrides: Any) -> ValidationContext:
    context = ValidationContext(
        integration_input=integration_input,
        glb019_result=_glb019_result_for(integration_input),
    )
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


def test_graph_has_single_wallclock_validator_node() -> None:
    wallclock_nodes = [
        node for node in PROOF_BINDING_VALIDATION_ORDER if node == VALIDATOR_WALLCLOCK
    ]
    assert wallclock_nodes == [VALIDATOR_WALLCLOCK]
    assert VALIDATOR_WALLCLOCK in PROOF_BINDING_VALIDATION_GRAPH
    assert PROOF_BINDING_VALIDATION_ORDER.index(VALIDATOR_WALLCLOCK) < (
        PROOF_BINDING_VALIDATION_ORDER.index(VALIDATOR_EVENT_STREAM)
    )
    assert PROOF_BINDING_VALIDATION_ORDER.index(VALIDATOR_EVENT_STREAM) < (
        PROOF_BINDING_VALIDATION_ORDER.index(VALIDATOR_COMPLETION_CHAIN)
    )


def test_graph_event_stream_production_activation() -> None:
    from src.ops.durable_completion_validation import graph
    from src.ops.durable_completion_validation.validators.event_stream import (
        validate_glb019_event_stream_proof,
    )

    assert VALIDATOR_EVENT_STREAM in graph.PROOF_BINDING_VALIDATION_GRAPH
    assert VALIDATOR_EVENT_STREAM in graph.PROOF_BINDING_VALIDATION_ORDER
    assert VALIDATOR_EVENT_STREAM in graph._load_validators()
    assert (
        graph._load_validators()[VALIDATOR_EVENT_STREAM].__name__
        == validate_glb019_event_stream_proof.__name__
    )
    assert VALIDATOR_EVENT_STREAM in PROOF_BINDING_VALIDATION_GRAPH[VALIDATOR_COMPLETION_CHAIN]


def test_graph_missing_validator_is_fail_closed() -> None:
    context = _minimal_context()
    partial_validators = {
        VALIDATOR_RECONCILIATION: lambda _ctx: ValidationResult(),
        VALIDATOR_RECOVERY: lambda _ctx: ValidationResult(),
        VALIDATOR_TRACEABILITY: lambda _ctx: ValidationResult(),
        VALIDATOR_EVENT_STREAM: lambda _ctx: ValidationResult(),
        VALIDATOR_COMPLETION_CHAIN: lambda _ctx: ValidationResult(),
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
        VALIDATOR_WALLCLOCK: lambda _ctx: ValidationResult(),
        VALIDATOR_EVENT_STREAM: lambda _ctx: ValidationResult(),
        VALIDATOR_COMPLETION_CHAIN: lambda _ctx: ValidationResult(fail_reasons=("should not run",)),
    }
    result = execute_proof_binding_validation_graph(context, validators=validators)
    assert any("dependency failed for 'traceability'" in reason for reason in result.fail_reasons)
    assert any(
        "dependency failed for 'operator_closure'" in reason for reason in result.fail_reasons
    )
    assert any(
        "dependency failed for 'completion_chain'" in reason for reason in result.fail_reasons
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
        VALIDATOR_WALLCLOCK: lambda _ctx: ValidationResult(),
        VALIDATOR_EVENT_STREAM: lambda _ctx: ValidationResult(),
        VALIDATOR_COMPLETION_CHAIN: lambda _ctx: ValidationResult(),
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
        VALIDATOR_WALLCLOCK: lambda _ctx: ValidationResult(),
        VALIDATOR_EVENT_STREAM: lambda _ctx: ValidationResult(),
        VALIDATOR_COMPLETION_CHAIN: lambda _ctx: ValidationResult(fail_reasons=("epsilon",)),
    }
    result = execute_proof_binding_validation_graph(context, validators=validators)
    assert set(result.fail_reasons) == {
        "alpha",
        "beta",
        "validation_graph: dependency failed for 'traceability': ['recovery']",
        "validation_graph: dependency failed for 'operator_closure': ['traceability', 'recovery']",
        "validation_graph: dependency failed for 'completion_chain': ['operator_closure', 'traceability', 'recovery']",
    }


def test_reconciliation_manifest_validator_matches_input_validation_path() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
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
    integration_input = _cached_default_minimal_completion_integration_input()
    direct = validate_pe21_reconciliation_result_manifest_integrity(integration_input)
    input_fail_reasons = validate_durable_run_primary_evidence_completion_integration_input(
        integration_input
    )
    fill_manifest_reasons = [
        reason for reason in input_fail_reasons if reason.startswith("pe21_fill_state_manifest")
    ]
    assert not fill_manifest_reasons
    assert not direct.fail_reasons


def _replace_pe21_manifest_entries(integration_input, manifest_entries: tuple[ManifestEntry, ...]):
    manifest_digest = compute_manifest_digest(manifest_entries)
    pe21_input = integration_input.pe21_integration_input
    binding = replace(
        pe21_input.primary_evidence_binding,
        manifest_entries=manifest_entries,
        manifest_digest=manifest_digest,
        manifest_proof_identity=manifest_digest,
    )
    pe21_input = replace(pe21_input, primary_evidence_binding=binding)
    return replace(integration_input, pe21_integration_input=pe21_input)


def test_graph_reconciliation_validator_composes_pe21_fill_manifest_integrity() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    context = ValidationContext(
        integration_input=integration_input,
        pe31_result=evaluate_reconciliation_review_lifecycle_integration(
            integration_input.pe31_reconciliation_review_integration_input
        ),
    )
    assert not validate_reconciliation_proof_binding(context).fail_reasons


def test_graph_reconciliation_validator_missing_fill_manifest_fail_closed() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    entries = tuple(
        entry
        for entry in integration_input.pe21_integration_input.primary_evidence_binding.manifest_entries
        if entry.relative_path != ARTIFACT_FILL_STATE_SNAPSHOT
    )
    bad = _replace_pe21_manifest_entries(integration_input, entries)
    context = _graph_context(
        bad,
        pe31_result=evaluate_reconciliation_review_lifecycle_integration(
            bad.pe31_reconciliation_review_integration_input
        ),
    )
    result = execute_proof_binding_validation_graph(context)
    assert any(
        "pe21_fill_state_manifest: FILL_STATE_SNAPSHOT.json manifest entry required" in reason
        for reason in result.fail_reasons
    )


def _replace_pe34_handoff(integration_input, **overrides):
    pe35_input = integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input
    pe34_handoff = replace(pe35_input.pe34_handoff, **overrides)
    pe35_input = replace(pe35_input, pe34_handoff=pe34_handoff)
    return replace(
        integration_input,
        pe35_handoff_staleness_revocation_recovery_boundary_input=pe35_input,
    )


def test_graph_recovery_validator_composes_pe35_handoff_input_validation() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    pe35_input = integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input
    context = ValidationContext(
        integration_input=integration_input,
        pe35_result=evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input),
    )
    assert not validate_recovery_proof_binding(context).fail_reasons


def test_graph_recovery_validator_missing_pe34_handoff_id_fail_closed() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    bad = _replace_pe34_handoff(integration_input, handoff_id="")
    pe35_input = bad.pe35_handoff_staleness_revocation_recovery_boundary_input
    context = _graph_context(
        bad,
        pe35_result=evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input),
    )
    result = execute_proof_binding_validation_graph(context)
    assert any("handoff_id required" in reason for reason in result.fail_reasons)


def _replace_pe37_archive_binding(integration_input, **overrides):
    pe37_input = integration_input.pe37_traceability_boundary_input
    pe16 = replace(pe37_input.pe16_archive_binding, **overrides)
    pe37_input = replace(pe37_input, pe16_archive_binding=pe16)
    return replace(integration_input, pe37_traceability_boundary_input=pe37_input)


def test_graph_traceability_validator_composes_pe37_handoff_input_validation() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    pe37_input = integration_input.pe37_traceability_boundary_input
    context = ValidationContext(
        integration_input=integration_input,
        pe37_result=evaluate_durable_evidence_traceability_boundary(pe37_input),
    )
    assert not validate_traceability_proof_binding(context).fail_reasons


def test_graph_traceability_validator_missing_pe16_archive_manifest_fail_closed() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    bad = _replace_pe37_archive_binding(integration_input, archive_manifest_digest="")
    pe37_input = bad.pe37_traceability_boundary_input
    pe35_input = bad.pe35_handoff_staleness_revocation_recovery_boundary_input
    context = _graph_context(
        bad,
        pe31_result=evaluate_reconciliation_review_lifecycle_integration(
            bad.pe31_reconciliation_review_integration_input
        ),
        pe35_result=evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input),
        pe37_result=evaluate_durable_evidence_traceability_boundary(pe37_input),
    )
    result = execute_proof_binding_validation_graph(context)
    assert any(
        "pe16_archive: archive_manifest_digest required" in reason for reason in result.fail_reasons
    )
    assert VALIDATOR_TRACEABILITY not in context.completed_validators


def _replace_pe25_closure_input(integration_input, **overrides):
    pe25_input = integration_input.pe25_closure_integration_input
    pe25_input = replace(pe25_input, **overrides)
    return replace(integration_input, pe25_closure_integration_input=pe25_input)


def test_graph_operator_closure_validator_composes_pe25_closure_input_validation() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    pe25_input = integration_input.pe25_closure_integration_input
    pe25_result = evaluate_operator_closure_lifecycle_integration(pe25_input)
    context = ValidationContext(
        integration_input=integration_input,
        pe25_result=pe25_result,
        admission_result={
            "integration_pass": True,
            "integration_proof_digest": (
                integration_input.pe25_operator_closure_proof.admission_integration_proof_digest
            ),
        },
    )
    assert not validate_operator_closure_proof_binding(context).fail_reasons


def test_graph_operator_closure_validator_missing_closure_id_fail_closed() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    bad = _replace_pe25_closure_input(integration_input, closure_id="")
    pe25_input = bad.pe25_closure_integration_input
    pe37_input = bad.pe37_traceability_boundary_input
    pe35_input = bad.pe35_handoff_staleness_revocation_recovery_boundary_input
    context = _graph_context(
        bad,
        pe31_result=evaluate_reconciliation_review_lifecycle_integration(
            bad.pe31_reconciliation_review_integration_input
        ),
        pe35_result=evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input),
        pe37_result=evaluate_durable_evidence_traceability_boundary(pe37_input),
        pe25_result=evaluate_operator_closure_lifecycle_integration(pe25_input),
        admission_result={
            "integration_pass": True,
            "integration_proof_digest": (
                bad.pe25_operator_closure_proof.admission_integration_proof_digest
            ),
        },
    )
    result = execute_proof_binding_validation_graph(context)
    assert any("closure_id required" in reason for reason in result.fail_reasons)
    assert VALIDATOR_OPERATOR_CLOSURE not in context.completed_validators


def test_graph_wallclock_validator_imports_canonical_owners_only() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    wallclock_source = (
        repo_root / "src" / "ops" / "durable_completion_validation" / "validators" / "wallclock.py"
    ).read_text(encoding="utf-8")
    assert "testnet_wallclock_duration_evidence_contract_v0" in wallclock_source
    assert "wallclock_session_evidence_v0" in wallclock_source
    assert evaluate_wallclock_evidence_fields.__module__ == "src.ops.wallclock_session_evidence_v0"
    assert (
        evaluate_wallclock_duration_evidence.__module__
        == "src.ops.testnet_wallclock_duration_evidence_contract_v0"
    )
    assert "def evaluate_wallclock" not in wallclock_source
    assert "hashlib" not in wallclock_source


def test_wallclock_validator_happy_path_matches_integration_wallclock_checks() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    assert not validate_wallclock_proof_binding(
        ValidationContext(integration_input=integration_input)
    ).fail_reasons
    input_fail_reasons = validate_durable_run_primary_evidence_completion_integration_input(
        integration_input
    )
    assert not [reason for reason in input_fail_reasons if "wallclock" in reason]


def _replace_wallclock_evidence_proof(integration_input, **overrides):
    proof = replace(integration_input.wallclock_evidence_proof, **overrides)
    return replace(integration_input, wallclock_evidence_proof=proof)


def _replace_completion_proof_chain(integration_input, **overrides):
    chain = replace(integration_input.completion_proof_chain, **overrides)
    return replace(integration_input, completion_proof_chain=chain)


def test_graph_wallclock_validator_composes_binding() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    assert not validate_wallclock_proof_binding(
        ValidationContext(integration_input=integration_input)
    ).fail_reasons


def test_graph_wallclock_validator_missing_required_fields_fail_closed() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    incomplete_evidence = {
        key: value
        for key, value in integration_input.wallclock_evidence_proof.wallclock_evidence.items()
        if key != REQUIRED_WALLCLOCK_FIELD_NAMES[0]
    }
    bad = _replace_wallclock_evidence_proof(
        integration_input,
        wallclock_evidence=incomplete_evidence,
    )
    result = validate_wallclock_proof_binding(ValidationContext(integration_input=bad))
    assert any("missing required fields" in reason for reason in result.fail_reasons)


def test_graph_wallclock_validator_semantic_drift_fail_closed() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    invalid_evidence = dict(integration_input.wallclock_evidence_proof.wallclock_evidence)
    invalid_evidence["elapsed_wall_clock_seconds"] = 0
    invalid_evidence["invalid_if_elapsed_below_min"] = True
    bad = _replace_wallclock_evidence_proof(
        integration_input,
        wallclock_evidence=invalid_evidence,
    )
    result = validate_wallclock_proof_binding(ValidationContext(integration_input=bad))
    assert any("wallclock_proof:" in reason for reason in result.fail_reasons)


def test_graph_wallclock_validator_digest_coherence_drift_fail_closed() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    bad = _replace_completion_proof_chain(
        integration_input,
        completion_referenced_wallclock_evidence_digest="0" * 64,
    )
    result = validate_wallclock_proof_binding(ValidationContext(integration_input=bad))
    assert any(
        "completion_referenced_wallclock_evidence_digest mismatch" in reason
        for reason in result.fail_reasons
    )


def test_graph_wallclock_failure_blocks_completion_chain() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    bad = _replace_wallclock_evidence_proof(
        integration_input,
        duration_proven=False,
    )
    context = _graph_context(integration_input=bad)
    result = execute_proof_binding_validation_graph(context)
    assert any("wallclock_proof:" in reason for reason in result.fail_reasons)
    assert VALIDATOR_WALLCLOCK not in context.completed_validators
    assert VALIDATOR_COMPLETION_CHAIN not in context.completed_validators


def test_completion_proof_chain_validator_matches_input_validation_path() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    direct = validate_completion_proof_chain_binding(
        ValidationContext(integration_input=integration_input)
    )
    input_fail_reasons = validate_durable_run_primary_evidence_completion_integration_input(
        integration_input
    )
    chain_reasons = [
        reason for reason in input_fail_reasons if reason.startswith("completion_proof_chain:")
    ]
    assert list(direct.fail_reasons) == chain_reasons


def test_graph_completion_chain_validator_composes_binding() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    assert not validate_completion_proof_chain_binding(
        ValidationContext(integration_input=integration_input)
    ).fail_reasons


def test_graph_completion_chain_validator_pe35_digest_drift_fail_closed() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    bad = _replace_completion_proof_chain(
        integration_input,
        completion_referenced_pe35_boundary_result_digest="0" * 64,
    )
    pe25_input = bad.pe25_closure_integration_input
    pe37_input = bad.pe37_traceability_boundary_input
    pe35_input = bad.pe35_handoff_staleness_revocation_recovery_boundary_input
    context = _graph_context(
        bad,
        pe31_result=evaluate_reconciliation_review_lifecycle_integration(
            bad.pe31_reconciliation_review_integration_input
        ),
        pe35_result=evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input),
        pe37_result=evaluate_durable_evidence_traceability_boundary(pe37_input),
        pe25_result=evaluate_operator_closure_lifecycle_integration(pe25_input),
        admission_result={
            "integration_pass": True,
            "integration_proof_digest": (
                bad.pe25_operator_closure_proof.admission_integration_proof_digest
            ),
        },
    )
    result = execute_proof_binding_validation_graph(context)
    assert any(
        "completion_referenced_pe35_boundary_result_digest mismatch" in reason
        for reason in result.fail_reasons
    )
    assert VALIDATOR_COMPLETION_CHAIN not in context.completed_validators


def test_graph_completion_chain_validator_wallclock_digest_drift_fail_closed() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    bad = _replace_completion_proof_chain(
        integration_input,
        completion_referenced_wallclock_evidence_digest="0" * 64,
    )
    pe25_input = bad.pe25_closure_integration_input
    pe37_input = bad.pe37_traceability_boundary_input
    pe35_input = bad.pe35_handoff_staleness_revocation_recovery_boundary_input
    context = _graph_context(
        bad,
        pe31_result=evaluate_reconciliation_review_lifecycle_integration(
            bad.pe31_reconciliation_review_integration_input
        ),
        pe35_result=evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input),
        pe37_result=evaluate_durable_evidence_traceability_boundary(pe37_input),
        pe25_result=evaluate_operator_closure_lifecycle_integration(pe25_input),
        admission_result={
            "integration_pass": True,
            "integration_proof_digest": (
                bad.pe25_operator_closure_proof.admission_integration_proof_digest
            ),
        },
    )
    result = execute_proof_binding_validation_graph(context)
    assert any(
        "completion_referenced_wallclock_evidence_digest mismatch" in reason
        for reason in result.fail_reasons
    )
    assert VALIDATOR_COMPLETION_CHAIN not in context.completed_validators


def test_graph_completion_chain_validator_pe38_digest_drift_fail_closed() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    bad = _replace_completion_proof_chain(
        integration_input,
        completion_referenced_pe38_readiness_review_proof_digest="0" * 64,
    )
    pe25_input = bad.pe25_closure_integration_input
    pe37_input = bad.pe37_traceability_boundary_input
    pe35_input = bad.pe35_handoff_staleness_revocation_recovery_boundary_input
    context = _graph_context(
        bad,
        pe31_result=evaluate_reconciliation_review_lifecycle_integration(
            bad.pe31_reconciliation_review_integration_input
        ),
        pe35_result=evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input),
        pe37_result=evaluate_durable_evidence_traceability_boundary(pe37_input),
        pe25_result=evaluate_operator_closure_lifecycle_integration(pe25_input),
        admission_result={
            "integration_pass": True,
            "integration_proof_digest": (
                bad.pe25_operator_closure_proof.admission_integration_proof_digest
            ),
        },
    )
    result = execute_proof_binding_validation_graph(context)
    assert any(
        "completion_referenced_pe38_readiness_review_proof_digest mismatch" in reason
        for reason in result.fail_reasons
    )
    assert VALIDATOR_COMPLETION_CHAIN not in context.completed_validators


def test_evaluate_graph_compatibility_happy_path() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    result = evaluate_durable_run_primary_evidence_completion_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["fail_reasons"] == []


def test_evaluate_graph_compatibility_pe31_mismatch_fails() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
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


def test_graph_testnet_completion_includes_wallclock_required_path_binding() -> None:
    from scripts.ops.primary_evidence_retention_v0 import (
        BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS,
    )
    from src.ops.wallclock_session_evidence_v0 import WALLCLOCK_EVIDENCE_FILENAME

    integration_input = _cached_default_minimal_completion_integration_input()
    artifact_paths = {entry.relative_path for entry in integration_input.artifact_checksums}
    assert WALLCLOCK_EVIDENCE_FILENAME in artifact_paths
    assert artifact_paths == set(BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS)
    result = execute_proof_binding_validation_graph(_minimal_context())
    assert not any("missing required artifact paths" in reason for reason in result.fail_reasons)


def test_graph_retention_review_completion_share_canonical_testnet_paths() -> None:
    from scripts.ops.primary_evidence_retention_v0 import (
        BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
        BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS,
        BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS,
        PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
    )
    from src.ops.wallclock_session_evidence_v0 import WALLCLOCK_EVIDENCE_FILENAME

    repo_root = Path(__file__).resolve().parents[2]
    review_source = (
        repo_root / "scripts" / "ops" / "review_testnet_bounded_observation_evidence_v0.py"
    ).read_text(encoding="utf-8")
    assert "BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS" in review_source
    integration_input = _cached_default_minimal_completion_integration_input()
    completion_paths = {entry.relative_path for entry in integration_input.artifact_checksums}
    assert completion_paths == set(BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS)
    assert WALLCLOCK_EVIDENCE_FILENAME in BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS
    assert WALLCLOCK_EVIDENCE_FILENAME not in BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS
    assert WALLCLOCK_EVIDENCE_FILENAME not in PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS
    assert (
        BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS
        == BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS
    )


def test_graph_seven_vs_eight_path_drift_fail_closed() -> None:
    from scripts.ops.primary_evidence_retention_v0 import (
        BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
        BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS,
    )
    from src.ops.wallclock_session_evidence_v0 import WALLCLOCK_EVIDENCE_FILENAME

    integration_input = _cached_default_minimal_completion_integration_input()
    seven_path_artifacts = tuple(
        entry
        for entry in integration_input.artifact_checksums
        if entry.relative_path in BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS
    )
    assert len(seven_path_artifacts) == len(BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS)
    assert len(BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS) == (
        len(BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS) + 1
    )
    bad = replace(integration_input, artifact_checksums=seven_path_artifacts)
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(WALLCLOCK_EVIDENCE_FILENAME in reason for reason in result["fail_reasons"])
    graph_result = execute_proof_binding_validation_graph(_graph_context(bad))
    assert graph_result.fail_reasons


def test_legacy_ops_only_completion_chain_master_v2_binding_not_present() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    assert (
        classify_master_v2_binding_presence(
            binding=integration_input.master_v2_decision_state_digest_binding,
            chain=integration_input.completion_proof_chain,
        )
        == "MASTER_V2_BINDING_NOT_PRESENT"
    )
    assert not validate_completion_proof_chain_binding(
        ValidationContext(integration_input=integration_input)
    ).fail_reasons


_GLB019_TEST_DIGEST = "a" * 64
_GLB019_CORRELATION_ID = "glb019-test-correlation-v0"

FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
LIVE_AUTHORIZED = False
ORDERS_AUTHORIZED = False
CREDENTIALS_ALLOWED = False
ZERO_ORDER_REQUIRED = True


def _glb019_validation_input(**overrides: Any):
    from src.ops.durable_completion_validation.validators.event_stream import (
        default_minimal_glb019_validation_input,
    )

    base = default_minimal_glb019_validation_input(
        source_revision="test-source-revision-v0",
        completion_identity_digest=_GLB019_TEST_DIGEST,
        manifest_identity_digest=_GLB019_TEST_DIGEST,
        run_identity_digest=_GLB019_TEST_DIGEST,
        correlation_id=_GLB019_CORRELATION_ID,
    )
    if not overrides:
        return base
    return replace(base, **overrides)


def _glb019_proof_context(**overrides: Any) -> ValidationContext:
    from src.ops.durable_completion_validation.validators.event_stream import (
        default_minimal_glb019_proof_binding,
        evaluate_glb019_event_stream_validation,
    )

    validation_input = _glb019_validation_input()
    glb019_result = evaluate_glb019_event_stream_validation(validation_input)
    proof = default_minimal_glb019_proof_binding(validation_input, glb019_result)
    integration_input = SimpleNamespace(
        source_revision=validation_input.source_revision,
        glb019_event_stream_validation_input=validation_input,
        glb019_event_stream_proof=proof,
    )
    context = ValidationContext(
        integration_input=integration_input,
        glb019_result=glb019_result,
    )
    for key, value in overrides.items():
        setattr(context, key, value)
    return context


def test_glb019_canonical_export_present() -> None:
    from src.ops.durable_completion_validation import validators

    assert "event_stream" in validators.__all__
    assert hasattr(validators, "event_stream")
    assert validators.event_stream.validate_glb019_event_stream_proof.__name__ == (
        "validate_glb019_event_stream_proof"
    )


def test_glb019_production_graph_happy_path() -> None:
    from src.ops.durable_completion_validation.validators.event_stream import (
        validate_glb019_event_stream_proof,
    )

    context = _minimal_context()
    assert not validate_glb019_event_stream_proof(context).fail_reasons
    result = execute_proof_binding_validation_graph(context)
    assert VALIDATOR_EVENT_STREAM in context.completed_validators
    assert not any("glb019" in reason for reason in result.fail_reasons)


def test_glb019_missing_glb019_result_fail_closed() -> None:
    from src.ops.durable_completion_validation.validators.event_stream import (
        validate_glb019_event_stream_proof,
    )

    context = _glb019_proof_context(glb019_result=None)
    result = validate_glb019_event_stream_proof(context)
    assert any("glb019_result required" in reason for reason in result.fail_reasons)


def test_glb019_graph_missing_result_blocks_completion_chain() -> None:
    context = _glb019_proof_context(glb019_result=None)
    result = execute_proof_binding_validation_graph(context)
    assert any("glb019_result required" in reason for reason in result.fail_reasons)
    assert VALIDATOR_EVENT_STREAM not in context.completed_validators
    assert VALIDATOR_COMPLETION_CHAIN not in context.completed_validators


def test_glb019_valid_event_stream_accepted() -> None:
    from src.ops.durable_completion_validation.validators.event_stream import (
        evaluate_glb019_event_stream_validation,
        validate_glb019_event_stream_proof,
    )

    validation_input = _glb019_validation_input()
    result = evaluate_glb019_event_stream_validation(validation_input)
    assert result["validation_pass"] is True
    assert result["fail_reasons"] == []
    assert not validate_glb019_event_stream_proof(_glb019_proof_context()).fail_reasons


def test_glb019_missing_event_stream_fail_closed() -> None:
    from src.ops.durable_completion_validation.validators.event_stream import (
        Glb019EventStreamValidationInput,
        evaluate_glb019_event_stream_validation,
    )

    empty = Glb019EventStreamValidationInput(
        boundary_owner="glb019_event_stream_static_boundary_v0",
        source_revision="test-source-revision-v0",
        completion_identity_digest=_GLB019_TEST_DIGEST,
        manifest_identity_digest=_GLB019_TEST_DIGEST,
        run_identity_digest=_GLB019_TEST_DIGEST,
        correlation_id=_GLB019_CORRELATION_ID,
        events=(),
    )
    result = evaluate_glb019_event_stream_validation(empty)
    assert result["validation_pass"] is False
    assert any("events required" in reason for reason in result["fail_reasons"])


def test_glb019_empty_sequence_fail_closed() -> None:
    from src.ops.durable_completion_validation.validators.event_stream import (
        evaluate_glb019_event_stream_validation,
    )

    broken_input = replace(_glb019_validation_input(), events=())
    result = evaluate_glb019_event_stream_validation(broken_input)
    assert result["validation_pass"] is False
    assert broken_input.events == ()


def test_glb019_invalid_order_fail_closed() -> None:
    from src.ops.durable_completion_validation.validators.event_stream import (
        evaluate_glb019_event_stream_validation,
    )

    base_input = _glb019_validation_input()
    reordered = tuple(
        replace(record, sequence=index + 1) for index, record in enumerate(base_input.events)
    )
    broken = replace(base_input, events=reordered)
    result = evaluate_glb019_event_stream_validation(broken)
    assert result["validation_pass"] is False
    assert any("sequence ordering" in reason for reason in result["fail_reasons"])


def test_glb019_duplicate_event_fail_closed() -> None:
    from src.ops.durable_completion_validation.validators.event_stream import (
        evaluate_glb019_event_stream_validation,
    )

    base_input = _glb019_validation_input()
    duplicate = replace(base_input.events[0], event_id=base_input.events[1].event_id)
    broken = replace(base_input, events=(duplicate, *base_input.events[1:]))
    result = evaluate_glb019_event_stream_validation(broken)
    assert result["validation_pass"] is False
    assert any("duplicate event_id" in reason for reason in result["fail_reasons"])


def test_glb019_identity_mismatch_fail_closed() -> None:
    from src.ops.durable_completion_validation.validators.event_stream import (
        evaluate_glb019_event_stream_validation,
    )

    base_input = _glb019_validation_input()
    mismatched = replace(
        base_input.events[0],
        correlation_id="other-correlation-id",
    )
    broken = replace(base_input, events=(mismatched, *base_input.events[1:]))
    result = evaluate_glb019_event_stream_validation(broken)
    assert result["validation_pass"] is False
    assert any("correlation_id mismatch" in reason for reason in result["fail_reasons"])


def test_glb019_manifest_mismatch_fail_closed() -> None:
    from src.ops.durable_completion_validation.validators.event_stream import (
        validate_glb019_event_stream_proof,
    )

    context = _glb019_proof_context()
    broken_proof = replace(
        context.integration_input.glb019_event_stream_proof,
        manifest_identity_digest="b" * 64,
    )
    broken_integration = SimpleNamespace(
        source_revision=context.integration_input.source_revision,
        glb019_event_stream_validation_input=context.integration_input.glb019_event_stream_validation_input,
        glb019_event_stream_proof=broken_proof,
    )
    result = validate_glb019_event_stream_proof(
        replace(context, integration_input=broken_integration)
    )
    assert any("manifest_identity_digest drift" in reason for reason in result.fail_reasons)


def test_glb019_owner_drift_fail_closed() -> None:
    from src.ops.durable_completion_validation.validators.event_stream import (
        validate_glb019_event_stream_proof,
    )

    context = _glb019_proof_context()
    broken_proof = replace(
        context.integration_input.glb019_event_stream_proof,
        boundary_owner="wrong_owner",
    )
    broken_integration = SimpleNamespace(
        source_revision=context.integration_input.source_revision,
        glb019_event_stream_validation_input=context.integration_input.glb019_event_stream_validation_input,
        glb019_event_stream_proof=broken_proof,
    )
    result = validate_glb019_event_stream_proof(
        replace(context, integration_input=broken_integration)
    )
    assert any("boundary_owner must be" in reason for reason in result.fail_reasons)


def test_glb019_deterministic_result_confirmed() -> None:
    from src.ops.durable_completion_validation.validators.event_stream import (
        evaluate_glb019_event_stream_validation,
    )

    validation_input = _glb019_validation_input()
    first = evaluate_glb019_event_stream_validation(validation_input)
    second = evaluate_glb019_event_stream_validation(validation_input)
    assert first == second


def test_glb019_missing_event_class_fail_closed() -> None:
    from src.ops.durable_completion_validation.validators.event_stream import (
        evaluate_glb019_event_stream_validation,
    )

    base_input = _glb019_validation_input()
    trimmed_events = tuple(
        record for record in base_input.events if record.event_class != "state_transition"
    )
    broken_input = replace(base_input, events=trimmed_events)
    result = evaluate_glb019_event_stream_validation(broken_input)
    assert result["validation_pass"] is False
    assert any("state_transition" in reason for reason in result["fail_reasons"])


def test_glb019_proof_validation_result_digest_mismatch_fail_closed() -> None:
    from src.ops.durable_completion_validation.validators.event_stream import (
        validate_glb019_event_stream_proof,
    )

    context = _glb019_proof_context()
    broken_proof = replace(
        context.integration_input.glb019_event_stream_proof,
        validation_result_digest="0" * 64,
    )
    broken_integration = SimpleNamespace(
        source_revision=context.integration_input.source_revision,
        glb019_event_stream_validation_input=context.integration_input.glb019_event_stream_validation_input,
        glb019_event_stream_proof=broken_proof,
    )
    result = validate_glb019_event_stream_proof(
        replace(context, integration_input=broken_integration)
    )
    assert any("validation_result_digest" in reason for reason in result.fail_reasons)


def test_glb019_event_stream_validator_no_slice_b_integration_import() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    event_stream_source = (
        repo_root
        / "src"
        / "ops"
        / "durable_completion_validation"
        / "validators"
        / "event_stream.py"
    ).read_text(encoding="utf-8")
    assert (
        "bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0"
        not in event_stream_source
    )


def test_glb019_zero_order_and_safety_assertions() -> None:
    assert FUTURES_ONLY is True
    assert BITCOIN_DIRECTION_ALLOWED is False
    assert LIVE_AUTHORIZED is False
    assert ORDERS_AUTHORIZED is False
    assert CREDENTIALS_ALLOWED is False
    assert ZERO_ORDER_REQUIRED is True
