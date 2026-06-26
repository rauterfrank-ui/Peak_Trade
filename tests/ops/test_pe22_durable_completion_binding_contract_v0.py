"""Static contract: PE-22 durable completion canonical binding registry (Package E E1 / INV-008).

Contract-only binding slice. Closes the proven PE-22 binding-registry gap using the
Package-D dedicated-testowner selector pattern (not the B2 dual-testowner path).

Non-authorizing. No runtime, network, testnet execution, or production mutation.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from typing import Final, Literal, TypedDict

from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
    PE22_INTEGRATION_OWNER,
    default_minimal_completion_integration_input,
    default_minimal_pe22_integration_proof,
    evaluate_durable_run_primary_evidence_completion_integration,
)
from src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE22_CONTRACT_VERSION,
    compute_integration_input_digest as compute_pe22_integration_input_digest,
    compute_integration_proof_digest as compute_pe22_integration_proof_digest,
    evaluate_risk_killswitch_lifecycle_integration,
)
from src.ops.durable_completion_validation.graph import (
    PROOF_BINDING_VALIDATION_GRAPH,
    PROOF_BINDING_VALIDATION_ORDER,
    VALIDATOR_COMPLETION_CHAIN,
    VALIDATOR_EVENT_STREAM,
    VALIDATOR_OPERATOR_CLOSURE,
    VALIDATOR_RECONCILIATION,
    VALIDATOR_TRACEABILITY,
    execute_proof_binding_validation_graph,
)
from src.ops.durable_completion_validation.models import ValidationContext
from src.ops.durable_completion_validation.validators.completion_chain import (
    validate_completion_proof_chain_binding,
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

REPO_ROOT = Path(__file__).resolve().parents[2]

PE22_DURABLE_COMPLETION_BINDING_PACKAGE_MARKER = (
    "PE22_DURABLE_COMPLETION_CANONICAL_BINDING_CONTRACT_V0=true"
)
PE22_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py"
)
INTEGRATION_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
)
PE22_CANONICAL_OWNER_PATH = str(PE22_MODULE.relative_to(REPO_ROOT))
DURABLE_COMPLETION_CANONICAL_OWNER_PATH = str(INTEGRATION_MODULE.relative_to(REPO_ROOT))
DURABLE_COMPLETION_VALIDATION_GRAPH_PATH = "src/ops/durable_completion_validation/graph.py"
DURABLE_COMPLETION_COMPLETION_CHAIN_VALIDATOR_PATH = (
    "src/ops/durable_completion_validation/validators/completion_chain.py"
)

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
ALT_COMMIT_SHA = "1234567890abcdef1234567890abcdef12345678"

BindingLayer = Literal[
    "PE22_UPSTREAM_CANONICAL",
    "PE42_COMPLETION_FACADE",
    "DURABLE_COMPLETION_VALIDATION_GRAPH",
]


class Pe22DurableCompletionBindingRecord(TypedDict):
    binding_id: str
    layer: BindingLayer
    owner_path: str
    downstream_path: str
    digest_fields: tuple[str, ...]
    authority_lift: bool
    operative_risk_evaluation_executed: bool
    operative_killswitch_executed: bool
    operative_flatten_executed: bool
    repair_authority: bool
    trading_authority: bool
    promotion_authority: bool
    reverse_authority_forbidden: bool


PE22_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY: tuple[
    Pe22DurableCompletionBindingRecord, ...
] = (
    {
        "binding_id": "pe22_upstream_canonical",
        "layer": "PE22_UPSTREAM_CANONICAL",
        "owner_path": PE22_CANONICAL_OWNER_PATH,
        "downstream_path": DURABLE_COMPLETION_CANONICAL_OWNER_PATH,
        "digest_fields": (
            "integration_input_digest",
            "integration_proof_digest",
        ),
        "authority_lift": False,
        "operative_risk_evaluation_executed": False,
        "operative_killswitch_executed": False,
        "operative_flatten_executed": False,
        "repair_authority": False,
        "trading_authority": False,
        "promotion_authority": False,
        "reverse_authority_forbidden": True,
    },
    {
        "binding_id": "pe42_completion_facade",
        "layer": "PE42_COMPLETION_FACADE",
        "owner_path": DURABLE_COMPLETION_CANONICAL_OWNER_PATH,
        "downstream_path": DURABLE_COMPLETION_VALIDATION_GRAPH_PATH,
        "digest_fields": ("completion_referenced_pe22_proof_digest",),
        "authority_lift": False,
        "operative_risk_evaluation_executed": False,
        "operative_killswitch_executed": False,
        "operative_flatten_executed": False,
        "repair_authority": False,
        "trading_authority": False,
        "promotion_authority": False,
        "reverse_authority_forbidden": True,
    },
    {
        "binding_id": "durable_completion_validation_graph",
        "layer": "DURABLE_COMPLETION_VALIDATION_GRAPH",
        "owner_path": DURABLE_COMPLETION_COMPLETION_CHAIN_VALIDATOR_PATH,
        "downstream_path": DURABLE_COMPLETION_VALIDATION_GRAPH_PATH,
        "digest_fields": ("completion_referenced_pe22_proof_digest",),
        "authority_lift": False,
        "operative_risk_evaluation_executed": False,
        "operative_killswitch_executed": False,
        "operative_flatten_executed": False,
        "repair_authority": False,
        "trading_authority": False,
        "promotion_authority": False,
        "reverse_authority_forbidden": True,
    },
)

PE22_DURABLE_COMPLETION_DEPENDENCY_DIRECTION: tuple[str, ...] = (
    "pe12_tiny_order_risk_killswitch_static_integration",
    "pe22_risk_killswitch_lifecycle",
    "pe42_durable_completion_facade",
    "durable_completion_validation_graph",
)

_PE22_CANONICAL_IMPORT_MODULE: Final[str] = (
    "src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0"
)
_FORBIDDEN_PARALLEL_PE22_BINDING_SOURCES: Final[frozenset[str]] = frozenset(
    {
        "src.execution.risk_gate",
        "src.risk.live_killswitch",
        "src.ops.recon.reconcile",
    }
)


def _imported_modules_from_source(source_path: Path) -> frozenset[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return frozenset(modules)


@lru_cache(maxsize=1)
def _cached_default_minimal_completion_integration_input():
    return default_minimal_completion_integration_input()


def _graph_context(integration_input, **overrides):
    from src.ops.durable_completion_validation.validators.event_stream import (
        evaluate_glb019_event_stream_validation,
    )

    context = ValidationContext(
        integration_input=integration_input,
        glb019_result=evaluate_glb019_event_stream_validation(
            integration_input.glb019_event_stream_validation_input
        ),
    )
    for key, value in overrides.items():
        setattr(context, key, value)
    return context


def _replace_completion_proof_chain(integration_input, **overrides):
    chain = replace(integration_input.completion_proof_chain, **overrides)
    return replace(integration_input, completion_proof_chain=chain)


def test_pe22_durable_completion_binding_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert PE22_DURABLE_COMPLETION_BINDING_PACKAGE_MARKER in text


def test_pe22_durable_completion_canonical_binding_registry_complete() -> None:
    assert len(PE22_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY) == 3
    binding_ids = {
        record["binding_id"] for record in PE22_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY
    }
    assert binding_ids == {
        "pe22_upstream_canonical",
        "pe42_completion_facade",
        "durable_completion_validation_graph",
    }
    for record in PE22_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY:
        assert record["authority_lift"] is False
        assert record["operative_risk_evaluation_executed"] is False
        assert record["operative_killswitch_executed"] is False
        assert record["operative_flatten_executed"] is False
        assert record["repair_authority"] is False
        assert record["trading_authority"] is False
        assert record["promotion_authority"] is False
        assert record["reverse_authority_forbidden"] is True
        assert Path(REPO_ROOT / record["owner_path"]).exists()


def test_pe22_durable_completion_registry_upstream_owner_matches_pe22_contract() -> None:
    upstream = PE22_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY[0]
    assert upstream["owner_path"] == PE22_CANONICAL_OWNER_PATH
    assert upstream["layer"] == "PE22_UPSTREAM_CANONICAL"
    assert PE22_INTEGRATION_OWNER == PE22_CONTRACT_VERSION


def test_pe22_durable_completion_dependency_direction_is_downstream_only() -> None:
    assert PE22_DURABLE_COMPLETION_DEPENDENCY_DIRECTION == (
        "pe12_tiny_order_risk_killswitch_static_integration",
        "pe22_risk_killswitch_lifecycle",
        "pe42_durable_completion_facade",
        "durable_completion_validation_graph",
    )
    pe22_index = PE22_DURABLE_COMPLETION_DEPENDENCY_DIRECTION.index(
        "pe22_risk_killswitch_lifecycle"
    )
    pe42_index = PE22_DURABLE_COMPLETION_DEPENDENCY_DIRECTION.index(
        "pe42_durable_completion_facade"
    )
    assert pe22_index < pe42_index


def test_pe22_durable_completion_sole_canonical_upstream_module_in_completion_facade() -> None:
    completion_imports = _imported_modules_from_source(INTEGRATION_MODULE)
    pe22_imports = {
        module
        for module in completion_imports
        if module.endswith("risk_killswitch_lifecycle_integration_contract_v0")
    }
    assert pe22_imports == {_PE22_CANONICAL_IMPORT_MODULE}
    assert _FORBIDDEN_PARALLEL_PE22_BINDING_SOURCES.isdisjoint(completion_imports)


def test_pe22_durable_completion_completion_chain_validator_imports_canonical_pe22_owner_only() -> (
    None
):
    validator_path = REPO_ROOT / DURABLE_COMPLETION_COMPLETION_CHAIN_VALIDATOR_PATH
    validator_source = validator_path.read_text(encoding="utf-8")
    assert "completion_referenced_pe22_proof_digest" in validator_source
    assert "reconciliation_review_lifecycle_integration_contract_v0" not in validator_source
    validator_imports = _imported_modules_from_source(validator_path)
    assert "bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0" not in (
        validator_imports
    )
    assert _FORBIDDEN_PARALLEL_PE22_BINDING_SOURCES.isdisjoint(validator_imports)


def test_pe22_durable_completion_binding_authority_neutral_on_happy_path() -> None:
    integration_input = default_minimal_completion_integration_input(
        source_revision=VALID_COMMIT_SHA
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(integration_input)
    pe22_result = evaluate_risk_killswitch_lifecycle_integration(
        integration_input.pe22_risk_killswitch_lifecycle_integration_input
    )
    assert result["integration_pass"] is True
    assert result["authority_lift"] is False
    assert result["pe22_integration_pass"] is True
    assert pe22_result["authority_lift"] is False
    assert pe22_result["operative_risk_evaluation_executed"] is False
    assert pe22_result["operative_killswitch_executed"] is False
    assert pe22_result["operative_flatten_executed"] is False


def test_pe22_source_revision_mismatch_with_completion_input_fails() -> None:
    integration_input = default_minimal_completion_integration_input(
        source_revision=VALID_COMMIT_SHA
    )
    bad_pe22_input = replace(
        integration_input.pe22_risk_killswitch_lifecycle_integration_input,
        source_revision=ALT_COMMIT_SHA,
    )
    bad = replace(
        integration_input,
        pe22_risk_killswitch_lifecycle_integration_input=bad_pe22_input,
        pe22_risk_killswitch_flatten_proof=default_minimal_pe22_integration_proof(
            bad_pe22_input,
            traceability_identity=integration_input.durable_run_root.run_root_digest,
            run_identity_digest=integration_input.run_identity.run_identity_digest,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_pe22_integration_input_digest_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe22_risk_killswitch_flatten_proof=replace(
            integration_input.pe22_risk_killswitch_flatten_proof,
            integration_input_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_input_digest mismatch" in r for r in result["fail_reasons"])


def test_pe22_integration_owner_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe22_risk_killswitch_flatten_proof=replace(
            integration_input.pe22_risk_killswitch_flatten_proof,
            integration_owner="wrong.owner.v0",
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_owner must be" in r for r in result["fail_reasons"])


def test_pe22_referenced_upstream_digest_drift_in_completion_chain_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        completion_proof_chain=replace(
            integration_input.completion_proof_chain,
            completion_referenced_pe22_proof_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "completion_referenced_pe22_proof_digest mismatch" in r for r in result["fail_reasons"]
    )


def test_pe22_completion_binding_source_revision_consistent_on_happy_path() -> None:
    integration_input = default_minimal_completion_integration_input(
        source_revision=VALID_COMMIT_SHA
    )
    pe22_input = integration_input.pe22_risk_killswitch_lifecycle_integration_input
    pe22_proof = integration_input.pe22_risk_killswitch_flatten_proof
    chain = integration_input.completion_proof_chain
    assert pe22_input.source_revision == integration_input.source_revision
    assert pe22_proof.integration_input_digest == compute_pe22_integration_input_digest(pe22_input)
    assert pe22_proof.integration_proof_digest == compute_pe22_integration_proof_digest(pe22_input)
    assert chain.completion_referenced_pe22_proof_digest == pe22_proof.integration_proof_digest


def test_graph_pe22_canonical_binding_registry_aligns_with_integration_owner() -> None:
    assert PE22_DURABLE_COMPLETION_BINDING_PACKAGE_MARKER.endswith("=true")
    assert len(PE22_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY) == 3
    assert PE22_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY[0]["owner_path"] == (
        PE22_CANONICAL_OWNER_PATH
    )
    assert PE22_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY[1]["owner_path"] == (
        DURABLE_COMPLETION_CANONICAL_OWNER_PATH
    )
    assert PE22_DURABLE_COMPLETION_CANONICAL_BINDING_REGISTRY[2]["owner_path"] == (
        DURABLE_COMPLETION_COMPLETION_CHAIN_VALIDATOR_PATH
    )
    assert "pe42_durable_completion_facade" in PE22_DURABLE_COMPLETION_DEPENDENCY_DIRECTION


def test_graph_completion_chain_validator_imports_canonical_pe22_owner_only() -> None:
    completion_chain_source = (
        REPO_ROOT / DURABLE_COMPLETION_COMPLETION_CHAIN_VALIDATOR_PATH
    ).read_text(encoding="utf-8")
    assert "completion_referenced_pe22_proof_digest" in completion_chain_source
    assert (
        "bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0"
        not in completion_chain_source
    )
    assert "src.execution.risk_gate" not in completion_chain_source


def test_graph_completion_chain_validator_is_canonical_pe22_binding_entrypoint() -> None:
    from src.ops.durable_completion_validation import graph

    validators = graph._load_validators()
    assert validators[VALIDATOR_COMPLETION_CHAIN].__name__ == (
        validate_completion_proof_chain_binding.__name__
    )
    assert VALIDATOR_COMPLETION_CHAIN in PROOF_BINDING_VALIDATION_ORDER
    assert VALIDATOR_EVENT_STREAM in PROOF_BINDING_VALIDATION_GRAPH[VALIDATOR_COMPLETION_CHAIN]


def test_graph_pe22_binding_authority_neutral_on_happy_path() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    pe22_result = evaluate_risk_killswitch_lifecycle_integration(
        integration_input.pe22_risk_killswitch_lifecycle_integration_input
    )
    context = ValidationContext(integration_input=integration_input)
    assert not validate_completion_proof_chain_binding(context).fail_reasons
    assert pe22_result["authority_lift"] is False
    assert pe22_result["operative_risk_evaluation_executed"] is False
    assert pe22_result["operative_killswitch_executed"] is False
    assert pe22_result["operative_flatten_executed"] is False


def test_graph_pe22_source_revision_drift_fail_closed_via_completion_chain_validator() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    bad_pe22_input = replace(
        integration_input.pe22_risk_killswitch_lifecycle_integration_input,
        source_revision=ALT_COMMIT_SHA,
    )
    bad = replace(
        integration_input,
        pe22_risk_killswitch_lifecycle_integration_input=bad_pe22_input,
        pe22_risk_killswitch_flatten_proof=default_minimal_pe22_integration_proof(
            bad_pe22_input,
            traceability_identity=integration_input.durable_run_root.run_root_digest,
            run_identity_digest=integration_input.run_identity.run_identity_digest,
        ),
    )
    facade_result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert facade_result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in facade_result["fail_reasons"])
    chain_result = validate_completion_proof_chain_binding(ValidationContext(integration_input=bad))
    assert chain_result.fail_reasons


def test_graph_pe22_integration_input_digest_drift_fail_closed() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe22_risk_killswitch_flatten_proof=replace(
            integration_input.pe22_risk_killswitch_flatten_proof,
            integration_input_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_input_digest mismatch" in r for r in result["fail_reasons"])


def test_graph_pe22_referenced_proof_digest_drift_in_completion_chain_fail_closed() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    bad = _replace_completion_proof_chain(
        integration_input,
        completion_referenced_pe22_proof_digest="0" * 64,
    )
    pe25_input = bad.pe25_closure_integration_input
    pe37_input = bad.pe37_traceability_boundary_input
    pe35_input = bad.pe35_handoff_staleness_revocation_recovery_boundary_input
    context = _graph_context(
        bad,
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
    assert result.fail_reasons
    assert VALIDATOR_COMPLETION_CHAIN not in context.completed_validators
    assert any(
        "dependency failed for 'completion_chain'" in reason for reason in result.fail_reasons
    )


def test_graph_pe22_completion_chain_digest_alignment_fail_closed() -> None:
    integration_input = _cached_default_minimal_completion_integration_input()
    bad = _replace_completion_proof_chain(
        integration_input,
        completion_referenced_pe22_proof_digest="0" * 64,
    )
    result = validate_completion_proof_chain_binding(ValidationContext(integration_input=bad))
    assert any(
        "completion_referenced_pe22_proof_digest mismatch" in reason
        for reason in result.fail_reasons
    )
