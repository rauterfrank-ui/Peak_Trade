"""Deterministic synthetic GLB-019 A2/B patch builder for selector contract tests (v0)."""

from __future__ import annotations

import difflib
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

from scripts.ops.durable_completion_integration_partitions_v0 import _base_file_text

_REPO_ROOT = Path(__file__).resolve().parents[2]

_FACADE_PATH = "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
_INTEGRATION_TEST_OWNER = "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
_GRAPH_PATH = "src/ops/durable_completion_validation/graph.py"
_EVENT_STREAM_PATH = "src/ops/durable_completion_validation/validators/event_stream.py"
_GRAPH_TEST_OWNER = "tests/ops/test_durable_completion_validation_graph_v1.py"
_PARTITIONS_PATH = "scripts/ops/durable_completion_integration_partitions_v0.py"
_CI_SELECTOR_TEST = "tests/ci/test_ci_diff_aware_test_selection_v1.py"

_GLB019_A2B_ALLOWED_FILES: tuple[str, ...] = (
    _FACADE_PATH,
    _INTEGRATION_TEST_OWNER,
    _GRAPH_PATH,
    _EVENT_STREAM_PATH,
    _GRAPH_TEST_OWNER,
    _PARTITIONS_PATH,
    _CI_SELECTOR_TEST,
)


def _baseline_text(path: str) -> str:
    text = _base_file_text(_REPO_ROOT, path)
    if not text.strip():
        raise RuntimeError(
            f"unable to resolve baseline for {path!r}: "
            "tried git show origin/main and workspace file"
        )
    return text


def _format_git_unified_diff(path: str, before: str, after: str) -> str:
    if before == after:
        return ""
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    if before and not before.endswith("\n"):
        before_lines = [line + "\n" for line in before.splitlines()]
    if after and not after.endswith("\n"):
        after_lines = [line + "\n" for line in after.splitlines()]
    diff_lines = list(
        difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )
    if not diff_lines:
        return ""
    return f"diff --git a/{path} b/{path}\n" + "".join(diff_lines)


def _mutate_partitions(before: str) -> str:
    needle = '    if "wallclock" in base:\n        return "wallclock"\n\n'
    insert = (
        '    if "wallclock" in base:\n'
        '        return "wallclock"\n\n'
        '    if "glb019" in base or "event_stream" in base:\n'
        '        return "pe38_readiness"\n\n'
    )
    if needle not in before:
        raise ValueError("partitions anchor missing")
    return before.replace(needle, insert, 1)


def _mutate_event_stream(before: str) -> str:
    needle = (
        "def validate_glb019_event_stream_proof(context: ValidationContext) -> ValidationResult:\n"
        '    """Bind canonical GLB-019 validation result into durable completion proof graph."""\n'
        "    fail_reasons: list[str] = []\n"
        "    integration_input = context.integration_input\n"
        "    glb019_result = context.glb019_result or {}\n"
    )
    replacement = (
        "def validate_glb019_event_stream_proof(context: ValidationContext) -> ValidationResult:\n"
        '    """Bind canonical GLB-019 validation result into durable completion proof graph."""\n'
        "    if context.glb019_result is None:\n"
        "        return ValidationResult(\n"
        "            fail_reasons=(\n"
        '                "glb019_event_stream_validation: glb019_result required in validation context",\n'
        "            )\n"
        "        )\n"
        "    fail_reasons: list[str] = []\n"
        "    integration_input = context.integration_input\n"
        "    glb019_result = context.glb019_result\n"
    )
    if needle not in before:
        raise ValueError("event_stream anchor missing")
    return before.replace(needle, replacement, 1)


def _mutate_graph(before: str) -> str:
    out = before
    replacements = [
        (
            'VALIDATOR_WALLCLOCK = "wallclock"\n',
            'VALIDATOR_WALLCLOCK = "wallclock"\nVALIDATOR_EVENT_STREAM = "event_stream"\n',
        ),
        (
            "    VALIDATOR_WALLCLOCK: (),\n",
            "    VALIDATOR_WALLCLOCK: (),\n    VALIDATOR_EVENT_STREAM: (),\n",
        ),
        (
            "        VALIDATOR_WALLCLOCK,\n",
            "        VALIDATOR_WALLCLOCK,\n        VALIDATOR_EVENT_STREAM,\n",
        ),
        ("    VALIDATOR_WALLCLOCK,\n", "    VALIDATOR_WALLCLOCK,\n    VALIDATOR_EVENT_STREAM,\n"),
        ("        completion_chain,\n", "        completion_chain,\n        event_stream,\n"),
        (
            "        VALIDATOR_WALLCLOCK: wallclock.validate_wallclock_proof_binding,\n",
            "        VALIDATOR_WALLCLOCK: wallclock.validate_wallclock_proof_binding,\n"
            "        VALIDATOR_EVENT_STREAM: event_stream.validate_glb019_event_stream_proof,\n",
        ),
    ]
    for old, new in replacements:
        if old not in out:
            raise ValueError(f"graph anchor missing: {old!r}")
        out = out.replace(old, new, 1)
    return out


def _mutate_ci_selector_test(before: str) -> str:
    return before.replace("assert len(nodes) == 238", "assert len(nodes) == 246", 1)


_SYNTHETIC_INTEGRATION_TESTS = """


def test_glb019_happy_path_passes_non_authorizing() -> None:
    integration_input = default_minimal_completion_integration_input()
    result = evaluate_durable_run_primary_evidence_completion_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["fail_reasons"] == []
    assert integration_input.non_authorizing is True
    assert integration_input.glb019_event_stream_proof.event_stream_non_authorizing is True
    assert result["operative_run_completion_recorded"] is False
    assert result["authority_lift"] is False


def test_glb019_missing_validation_input_fail_closed() -> None:
    from types import SimpleNamespace

    integration_input = default_minimal_completion_integration_input()
    legacy = SimpleNamespace(
        **{
            field.name: getattr(integration_input, field.name)
            for field in integration_input.__dataclass_fields__.values()
            if field.name != "glb019_event_stream_validation_input"
        }
    )
    fail_reasons = validate_durable_run_primary_evidence_completion_integration_input(legacy)  # type: ignore[arg-type]
    assert any("glb019_event_stream_validation_input required" in reason for reason in fail_reasons)


def test_glb019_missing_proof_fail_closed() -> None:
    from types import SimpleNamespace

    integration_input = default_minimal_completion_integration_input()
    legacy = SimpleNamespace(
        **{
            field.name: getattr(integration_input, field.name)
            for field in integration_input.__dataclass_fields__.values()
            if field.name != "glb019_event_stream_proof"
        }
    )
    fail_reasons = validate_durable_run_primary_evidence_completion_integration_input(legacy)  # type: ignore[arg-type]
    assert any("glb019_event_stream_proof required" in reason for reason in fail_reasons)


def test_glb019_run_identity_drift_fail_closed() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        glb019_event_stream_validation_input=replace(
            integration_input.glb019_event_stream_validation_input,
            run_identity_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("run_identity_digest drift" in reason for reason in result["fail_reasons"])


def test_glb019_source_revision_drift_fail_closed() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        glb019_event_stream_validation_input=replace(
            integration_input.glb019_event_stream_validation_input,
            source_revision="1" * 40,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in reason for reason in result["fail_reasons"])


def test_glb019_proof_digest_drift_fail_closed() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        glb019_event_stream_proof=replace(
            integration_input.glb019_event_stream_proof,
            validation_result_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("validation_result_digest mismatch" in reason for reason in result["fail_reasons"])


def test_glb019_digest_sensitivity() -> None:
    base = default_minimal_completion_integration_input()
    variant = replace(
        base,
        glb019_event_stream_validation_input=replace(
            base.glb019_event_stream_validation_input,
            correlation_id="glb019-digest-variant-v0",
        ),
    )
    assert compute_completion_integration_input_digest(
        base
    ) != compute_completion_integration_input_digest(variant)


def test_glb019_deterministic_repeat() -> None:
    integration_input = default_minimal_completion_integration_input()
    first = evaluate_durable_run_primary_evidence_completion_integration(integration_input)
    second = evaluate_durable_run_primary_evidence_completion_integration(integration_input)
    assert first == second
    assert first["integration_input_digest"] == second["integration_input_digest"]
"""


def _mutate_integration_test_owner(before: str) -> str:
    if not before.endswith("\n"):
        before += "\n"
    return before + _SYNTHETIC_INTEGRATION_TESTS


_GRAPH_TEST_HELPERS = """

def _glb019_result_for(integration_input):
    from src.ops.durable_completion_validation.validators.event_stream import (
        evaluate_glb019_event_stream_validation,
    )

    return evaluate_glb019_event_stream_validation(
        integration_input.glb019_event_stream_validation_input
    )


def _graph_context(integration_input, **overrides: Any) -> ValidationContext:
    context = ValidationContext(
        integration_input=integration_input,
        glb019_result=_glb019_result_for(integration_input),
    )
    for key, value in overrides.items():
        setattr(context, key, value)
    return context
"""

_GRAPH_TEST_EVENT_STREAM_ACTIVATION = """

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

"""

_GRAPH_TEST_PRODUCTION_HAPPY = """

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

"""


def _mutate_graph_test(before: str) -> str:
    out = before
    out = out.replace(
        "    VALIDATOR_COMPLETION_CHAIN,\n    VALIDATOR_OPERATOR_CLOSURE,",
        "    VALIDATOR_COMPLETION_CHAIN,\n    VALIDATOR_EVENT_STREAM,\n    VALIDATOR_OPERATOR_CLOSURE,",
        1,
    )
    anchor = (
        "def _cached_default_minimal_completion_integration_input():\n"
        '    """Module-scoped cache: building minimal integration input runs full offline evidence chain."""\n'
        "    return default_minimal_completion_integration_input()\n\n\n"
    )
    if anchor not in out:
        raise ValueError("graph test helper anchor missing")
    out = out.replace(anchor, anchor + _GRAPH_TEST_HELPERS.lstrip("\n"), 1)
    out = out.replace(
        "    context = ValidationContext(integration_input=integration_input)\n",
        "    context = ValidationContext(\n"
        "        integration_input=integration_input,\n"
        "        glb019_result=_glb019_result_for(integration_input),\n"
        "    )\n",
        1,
    )
    out = out.replace(
        "    assert PROOF_BINDING_VALIDATION_ORDER.index(VALIDATOR_WALLCLOCK) < (\n"
        "        PROOF_BINDING_VALIDATION_ORDER.index(VALIDATOR_COMPLETION_CHAIN)\n"
        "    )\n",
        "    assert PROOF_BINDING_VALIDATION_ORDER.index(VALIDATOR_WALLCLOCK) < (\n"
        "        PROOF_BINDING_VALIDATION_ORDER.index(VALIDATOR_EVENT_STREAM)\n"
        "    )\n"
        "    assert PROOF_BINDING_VALIDATION_ORDER.index(VALIDATOR_EVENT_STREAM) < (\n"
        "        PROOF_BINDING_VALIDATION_ORDER.index(VALIDATOR_COMPLETION_CHAIN)\n"
        "    )\n",
        1,
    )
    out = out.replace(
        "def test_graph_missing_validator_is_fail_closed() -> None:",
        _GRAPH_TEST_EVENT_STREAM_ACTIVATION.lstrip("\n")
        + "def test_graph_missing_validator_is_fail_closed() -> None:",
        1,
    )
    for old_block in (
        "        VALIDATOR_TRACEABILITY: lambda _ctx: ValidationResult(),\n        VALIDATOR_COMPLETION_CHAIN:",
        "        VALIDATOR_WALLCLOCK: lambda _ctx: ValidationResult(),\n        VALIDATOR_COMPLETION_CHAIN:",
    ):
        new_block = old_block.replace(
            "VALIDATOR_COMPLETION_CHAIN:",
            "VALIDATOR_EVENT_STREAM: lambda _ctx: ValidationResult(),\n        VALIDATOR_COMPLETION_CHAIN:",
        )
        if old_block not in out:
            raise ValueError(f"graph test partial validator anchor missing: {old_block!r}")
        out = out.replace(old_block, new_block, 1)
    replacements = [
        (
            "    bad = _replace_pe21_manifest_entries(integration_input, entries)\n"
            "    context = ValidationContext(\n        integration_input=bad,",
            "    bad = _replace_pe21_manifest_entries(integration_input, entries)\n"
            "    context = _graph_context(\n        bad,",
        ),
        (
            "    context = ValidationContext(\n        integration_input=bad,\n"
            "        pe35_result=evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input),",
            "    context = _graph_context(\n        bad,\n"
            "        pe35_result=evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input),",
        ),
        (
            "    context = ValidationContext(\n        integration_input=bad,\n"
            "        pe31_result=evaluate_reconciliation_review_lifecycle_integration(",
            "    context = _graph_context(\n        bad,\n"
            "        pe31_result=evaluate_reconciliation_review_lifecycle_integration(",
        ),
        (
            "    context = ValidationContext(integration_input=bad)\n"
            "    result = execute_proof_binding_validation_graph(context)\n"
            '    assert any("wallclock_proof:" in reason for reason in result.fail_reasons)',
            "    context = _graph_context(integration_input=bad)\n"
            "    result = execute_proof_binding_validation_graph(context)\n"
            '    assert any("wallclock_proof:" in reason for reason in result.fail_reasons)',
        ),
    ]
    for old, new in replacements:
        if old not in out:
            raise ValueError(f"graph test context anchor missing: {old[:40]!r}")
        out = out.replace(old, new, 1)
    out = out.replace(
        "    graph_result = execute_proof_binding_validation_graph(ValidationContext(integration_input=bad))",
        "    graph_result = execute_proof_binding_validation_graph(_graph_context(bad))",
        1,
    )
    old_no_prod = """def test_glb019_no_production_graph_activation() -> None:
    from src.ops.durable_completion_validation import graph

    assert "event_stream" not in graph.PROOF_BINDING_VALIDATION_GRAPH
    assert "event_stream" not in graph.PROOF_BINDING_VALIDATION_ORDER
    graph_source = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "ops"
        / "durable_completion_validation"
        / "graph.py"
    ).read_text(encoding="utf-8")
    assert "event_stream" not in graph_source


"""
    if old_no_prod not in out:
        raise ValueError("graph test no-production anchor missing")
    out = out.replace(old_no_prod, _GRAPH_TEST_PRODUCTION_HAPPY.lstrip("\n"), 1)
    return out


_FACADE_IMPORT_BLOCK = """from src.ops.durable_completion_validation.validators.event_stream import (
    Glb019EventStreamProofBinding,
    Glb019EventStreamValidationInput,
    compute_validation_input_digest as compute_glb019_event_stream_validation_input_digest,
    default_minimal_glb019_proof_binding,
    default_minimal_glb019_validation_input,
    evaluate_glb019_event_stream_validation,
    validate_glb019_event_stream_validation_input,
)
"""

_FACADE_VALIDATE_BINDING_FN = """

def _validate_glb019_event_stream_binding(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
    *,
    completion_identity_digest: str,
    manifest_identity_digest: str,
    run_identity_digest: str,
) -> list[str]:
    fail_reasons: list[str] = []
    validation_input = getattr(integration_input, "glb019_event_stream_validation_input", None)
    proof = getattr(integration_input, "glb019_event_stream_proof", None)
    if validation_input is None:
        fail_reasons.append("glb019_event_stream_validation_input required")
        return fail_reasons
    if proof is None:
        fail_reasons.append("glb019_event_stream_proof required")
        return fail_reasons

    fail_reasons.extend(validate_glb019_event_stream_validation_input(validation_input))
    if validation_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "glb019_event_stream_validation_input: source_revision mismatch with completion input"
        )
    if validation_input.run_identity_digest != run_identity_digest:
        fail_reasons.append("glb019_event_stream_validation_input: run_identity_digest drift")
    if validation_input.manifest_identity_digest != manifest_identity_digest:
        fail_reasons.append("glb019_event_stream_validation_input: manifest_identity_digest drift")
    if validation_input.completion_identity_digest != completion_identity_digest:
        fail_reasons.append(
            "glb019_event_stream_validation_input: completion_identity_digest drift"
        )

    glb019_result = evaluate_glb019_event_stream_validation(validation_input)
    prefix = "glb019_event_stream_proof"
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append(f"{prefix}: source_revision mismatch")
    if proof.validation_input_digest != glb019_result["validation_input_digest"]:
        fail_reasons.append(f"{prefix}: validation_input_digest mismatch")
    if proof.validation_result_digest != glb019_result["validation_result_digest"]:
        fail_reasons.append(f"{prefix}: validation_result_digest mismatch")
    if proof.event_stream_identity != glb019_result["event_stream_identity"]:
        fail_reasons.append(f"{prefix}: event_stream_identity mismatch")
    if not glb019_result["validation_pass"]:
        fail_reasons.append("glb019_event_stream_validation: canonical evaluation failed")
        fail_reasons.extend(
            f"glb019_event_stream_validation: {reason}"
            for reason in glb019_result.get("fail_reasons", [])
        )
    return _sorted_unique(fail_reasons)


"""


def _mutate_facade(before: str) -> str:
    out = before
    out = out.replace(
        "    evaluate_wallclock_duration_evidence,\n)\nfrom src.ops.wallclock_session_evidence_v0 import (",
        "    evaluate_wallclock_duration_evidence,\n)\n"
        + _FACADE_IMPORT_BLOCK
        + "from src.ops.wallclock_session_evidence_v0 import (",
        1,
    )
    out = out.replace(
        "    contract_versions: ContractVersionsInput\n    futures_only: bool = True",
        "    contract_versions: ContractVersionsInput\n"
        "    glb019_event_stream_validation_input: Glb019EventStreamValidationInput\n"
        "    glb019_event_stream_proof: Glb019EventStreamProofBinding\n"
        "    futures_only: bool = True",
        1,
    )
    out = out.replace(
        "    return _sorted_unique(fail_reasons)\n\n\ndef _validate_pe38_readiness_review_integration_proof(",
        "    return _sorted_unique(fail_reasons)\n"
        + _FACADE_VALIDATE_BINDING_FN
        + "def _validate_pe38_readiness_review_integration_proof(",
        1,
    )
    out = out.replace(
        "            artifact_checksums=integration_input.artifact_checksums,\n        )\n    )\n\n    post_write = integration_input.post_write_verification",
        "            artifact_checksums=integration_input.artifact_checksums,\n        )\n    )\n"
        "    expected_completion_identity_digest = compute_completion_identity_digest(\n"
        "        run_root_digest=durable_root.run_root_digest,\n"
        "        manifest_digest=integration_input.manifest_proof.manifest_digest,\n"
        "        source_revision=integration_input.source_revision,\n"
        "    )\n"
        "    fail_reasons.extend(\n"
        "        _validate_glb019_event_stream_binding(\n"
        "            integration_input,\n"
        "            completion_identity_digest=expected_completion_identity_digest,\n"
        "            manifest_identity_digest=integration_input.manifest_proof.manifest_digest,\n"
        "            run_identity_digest=run_identity.run_identity_digest,\n"
        "        )\n"
        "    )\n\n    post_write = integration_input.post_write_verification",
        1,
    )
    out = out.replace(
        '        "futures_only": integration_input.futures_only,\n        "gap2a1_enforcement": asdict(integration_input.gap2a1_enforcement),',
        '        "futures_only": integration_input.futures_only,\n'
        '        "glb019_event_stream_proof": asdict(integration_input.glb019_event_stream_proof),\n'
        '        "glb019_event_stream_validation_input_digest": (\n'
        "            compute_glb019_event_stream_validation_input_digest(\n"
        "                integration_input.glb019_event_stream_validation_input\n"
        "            )\n"
        "        ),\n"
        '        "gap2a1_enforcement": asdict(integration_input.gap2a1_enforcement),',
        1,
    )
    out = out.replace(
        "    pe25_result = evaluate_operator_closure_lifecycle_integration(\n"
        "        integration_input.pe25_closure_integration_input\n"
        "    )\n"
        "    from src.ops.durable_completion_validation.graph import execute_proof_binding_validation_graph",
        "    pe25_result = evaluate_operator_closure_lifecycle_integration(\n"
        "        integration_input.pe25_closure_integration_input\n"
        "    )\n"
        "    glb019_result = evaluate_glb019_event_stream_validation(\n"
        "        integration_input.glb019_event_stream_validation_input\n"
        "    )\n"
        "    from src.ops.durable_completion_validation.graph import execute_proof_binding_validation_graph",
        1,
    )
    out = out.replace(
        "            admission_result=admission_result,\n        )\n    )",
        "            admission_result=admission_result,\n            glb019_result=glb019_result,\n        )\n    )",
        1,
    )
    out = out.replace(
        "        source_revision=source_revision,\n    )\n    pe23_proof = default_minimal_pe23_integration_proof(",
        "        source_revision=source_revision,\n    )\n"
        "    glb019_validation_input = default_minimal_glb019_validation_input(\n"
        "        source_revision=source_revision,\n"
        "        completion_identity_digest=completion_identity_digest,\n"
        "        manifest_identity_digest=manifest_digest,\n"
        "        run_identity_digest=run_identity_digest,\n"
        "        correlation_id=run_id,\n"
        "    )\n"
        "    glb019_result = evaluate_glb019_event_stream_validation(glb019_validation_input)\n"
        "    glb019_proof = default_minimal_glb019_proof_binding(glb019_validation_input, glb019_result)\n"
        "    pe23_proof = default_minimal_pe23_integration_proof(",
        1,
    )
    out = out.replace(
        "        safety_snapshot=default_minimal_safety_snapshot(),\n        contract_versions=ContractVersionsInput(",
        "        safety_snapshot=default_minimal_safety_snapshot(),\n"
        "        glb019_event_stream_validation_input=glb019_validation_input,\n"
        "        glb019_event_stream_proof=glb019_proof,\n"
        "        contract_versions=ContractVersionsInput(",
        1,
    )
    return out


_MUTATORS: dict[str, Callable[[str], str]] = {
    _PARTITIONS_PATH: _mutate_partitions,
    _EVENT_STREAM_PATH: _mutate_event_stream,
    _GRAPH_PATH: _mutate_graph,
    _CI_SELECTOR_TEST: _mutate_ci_selector_test,
    _INTEGRATION_TEST_OWNER: _mutate_integration_test_owner,
    _GRAPH_TEST_OWNER: _mutate_graph_test,
    _FACADE_PATH: _mutate_facade,
}


@lru_cache(maxsize=1)
def synthetic_glb019_a2b_positive_patch_text() -> str:
    chunks: list[str] = []
    for path in _GLB019_A2B_ALLOWED_FILES:
        before = _baseline_text(path)
        after = _MUTATORS[path](before)
        chunk = _format_git_unified_diff(path, before, after)
        if not chunk:
            raise ValueError(f"synthetic patch produced no diff for {path}")
        chunks.append(chunk.rstrip("\n"))
    return "\n".join(chunks) + "\n"


def synthetic_glb019_a2b_reject_patch_text() -> str:
    patch = synthetic_glb019_a2b_positive_patch_text()
    return patch.replace(
        "    glb019_result = evaluate_glb019_event_stream_validation(validation_input)",
        "    pe21_result = evaluate_glb019_event_stream_validation(validation_input)",
        1,
    )
