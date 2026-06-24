"""Fachliche Required-Coverage-Partitionen für den Completion-Integration-Testowner (v0).

Deterministische Node-Klassifikation per pytest-Collect + Name-Regeln.
Kein Cross-Call-State; rein statische Inventar- und Expansionshilfe für CI-Selector.
"""

from __future__ import annotations

import ast
import enum
import re
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Final

INTEGRATION_TEST_OWNER: Final = "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"

COMPLETION_FACADE_PATH: Final = "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"

CORE_ALWAYS_PARTITIONS: Final[tuple[str, ...]] = (
    "core_invariants",
    "core_smoke",
    "core_digest",
)

ALL_PARTITIONS: Final[tuple[str, ...]] = (
    *CORE_ALWAYS_PARTITIONS,
    "core_baseline_input",
    "core_kwargs",
    "core_cross_chain",
    "pe21_reconciliation",
    "pe31_review",
    "pe22_risk_killswitch",
    "pe23_capital",
    "pe24_pilot",
    "pe25_closure",
    "pe35_handoff_recovery",
    "pe37_traceability",
    "pe38_readiness",
    "wallclock",
)

_NODE_ID_RE = re.compile(r"<Function (test_[^>]+)>")


def _base_node_id(node_id: str) -> str:
    return node_id.split("[", 1)[0]


def classify_integration_node_id(node_id: str) -> str:
    """Map a collected pytest node id (test_name or test_name[param]) to one partition."""
    base = _base_node_id(node_id)

    if base in {
        "test_package_marker_present",
        "test_canonical_owners_referenced_not_duplicated",
        "test_global_safety_flags_remain_blocked",
        "test_contract_version_constants",
        "test_default_safety_snapshot_matches_required_invariants",
        "test_bounded_durable_run_required_paths_covered",
        "test_completion_required_paths_bind_to_canonical_testnet_contract",
        "test_generic_bounded_required_paths_not_testnet_completion_source_of_truth",
        "test_full_testnet_artifact_set_passes",
    }:
        return "core_invariants"

    if base.startswith("test_completion_integration_input_digest_"):
        if "pe21" in base:
            return "pe21_reconciliation"
        if "pe31" in base:
            return "pe31_review"
        return "core_digest"

    if base in {
        "test_deterministic_identical_inputs_same_payload_and_digest",
        "test_coherent_static_completion_happy_path_passes",
        "test_valid_static_proof_remains_non_authorizing",
        "test_no_input_mutation_from_evaluation",
        "test_current_lifecycle_state_passes",
        "test_manifest_digest_matches_canonical_entries",
        "test_run_identity_digest_matches_canonical_inputs",
    }:
        return "core_smoke"

    if base.startswith("test_reconciliation_result_") or any(
        base.startswith(prefix)
        for prefix in (
            "test_missing_reconciliation",
            "test_empty_reconciliation",
            "test_wrong_reconciliation",
            "test_alias_reconciliation",
            "test_malformed_reconciliation",
            "test_uppercase_reconciliation",
            "test_duplicate_reconciliation",
            "test_contradictory_reconciliation",
            "test_fill_state",
        )
    ):
        return "pe21_reconciliation"

    if "wallclock" in base:
        return "wallclock"

    if "pe38" in base:
        return "pe38_readiness"

    if base.startswith("test_pe35_") or "pe35_pe21" in base or "semantics_remain_bound" in base:
        return "pe35_handoff_recovery"

    if (
        base.startswith("test_pe37_")
        or base == "test_completion_proof_chain_traceability_drift_fails"
    ):
        return "pe37_traceability"

    if "pe25" in base:
        return "pe25_closure"

    if "pe31" in base:
        return "pe31_review"

    if "pe22" in base:
        return "pe22_risk_killswitch"

    if "pe23" in base:
        return "pe23_capital"

    if "pe24" in base:
        return "pe24_pilot"

    if "pe21" in base:
        return "pe21_reconciliation"

    if base.startswith("test_completion_proof_chain_"):
        for tag, partition in (
            ("pe31", "pe31_review"),
            ("pe22", "pe22_risk_killswitch"),
            ("pe23", "pe23_capital"),
            ("pe24", "pe24_pilot"),
            ("pe25", "pe25_closure"),
            ("pe35", "pe35_handoff_recovery"),
            ("pe37", "pe37_traceability"),
            ("pe38", "pe38_readiness"),
            ("wallclock", "wallclock"),
        ):
            if tag in base:
                return partition
        return "core_cross_chain"

    if base in {
        "test_unknown_extra_fields_fail",
        "test_authority_override_fields_fail",
        "test_completion_claim_without_proof_chain_fails",
    }:
        return "core_kwargs"

    if base.startswith("test_gap") or base == "test_completion_true_with_incomplete_evidence_fails":
        return "core_cross_chain"

    if base.startswith("test_planned_or_simulated") or base.startswith(
        "test_invalid_proof_lifecycle_states_fail"
    ):
        return "core_cross_chain"

    return "core_baseline_input"


@lru_cache(maxsize=1)
def collect_integration_owner_node_ids() -> tuple[str, ...]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", INTEGRATION_TEST_OWNER, "--collect-only", "-q"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in {0, 5}:
        raise RuntimeError(
            f"pytest collect failed for {INTEGRATION_TEST_OWNER}: {proc.stderr or proc.stdout}"
        )
    nodes: list[str] = []
    for line in proc.stdout.splitlines():
        match = _NODE_ID_RE.search(line)
        if match:
            nodes.append(match.group(1))
    return tuple(nodes)


@lru_cache(maxsize=1)
def integration_partition_inventory() -> dict[str, tuple[str, ...]]:
    by_partition: dict[str, list[str]] = {name: [] for name in ALL_PARTITIONS}
    unknown: list[str] = []
    for node_id in collect_integration_owner_node_ids():
        partition = classify_integration_node_id(node_id)
        if partition not in by_partition:
            unknown.append(node_id)
            continue
        by_partition[partition].append(node_id)
    if unknown:
        raise RuntimeError(f"unmapped integration nodes: {unknown[:5]}")
    return {key: tuple(sorted(values)) for key, values in by_partition.items() if values}


def integration_owner_node_count() -> int:
    return len(collect_integration_owner_node_ids())


def partition_union_node_count(partitions: frozenset[str]) -> int:
    inventory = integration_partition_inventory()
    seen: set[str] = set()
    for partition in partitions:
        if partition not in inventory:
            raise KeyError(f"unknown partition: {partition}")
        seen.update(inventory[partition])
    return len(seen)


def expand_partitions_to_pytest_targets(partitions: frozenset[str]) -> tuple[str, ...]:
    inventory = integration_partition_inventory()
    node_ids: set[str] = set()
    for partition in sorted(partitions):
        if partition not in inventory:
            raise KeyError(f"unknown partition: {partition}")
        node_ids.update(inventory[partition])
    return tuple(sorted(f"{INTEGRATION_TEST_OWNER}::{node_id}" for node_id in sorted(node_ids)))


def _file_text(path: str) -> str:
    from pathlib import Path

    return Path(path).read_text(encoding="utf-8")


def partitions_for_changed_files(changed_files: list[str]) -> frozenset[str] | None:
    """Return required partition ids, empty set for graph-only, None for full integration owner."""
    from pathlib import Path

    files = frozenset(changed_files)
    partitions: set[str] = set(CORE_ALWAYS_PARTITIONS)

    if INTEGRATION_TEST_OWNER in files:
        return None

    if COMPLETION_FACADE_PATH in files:
        return None

    integration_scoped = False
    graph_only = True

    path_rules: tuple[tuple[str, str], ...] = (
        (
            "src/ops/bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py",
            "pe21_reconciliation",
        ),
        (
            "src/ops/bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0.py",
            "pe31_review",
        ),
        (
            "src/ops/bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py",
            "pe22_risk_killswitch",
        ),
        (
            "src/ops/bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0.py",
            "pe23_capital",
        ),
        (
            "src/ops/bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0.py",
            "pe24_pilot",
        ),
        (
            "src/ops/bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0.py",
            "pe25_closure",
        ),
        (
            "src/ops/bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0.py",
            "pe35_handoff_recovery",
        ),
        (
            "src/ops/bounded_futures_testnet_operator_review_handoff_boundary_contract_v0.py",
            "pe35_handoff_recovery",
        ),
        (
            "src/ops/bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0.py",
            "pe37_traceability",
        ),
        (
            "src/ops/bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration_contract_v0.py",
            "pe37_traceability",
        ),
        (
            "src/ops/bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0.py",
            "pe37_traceability",
        ),
        (
            "src/ops/bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration_contract_v0.py",
            "pe38_readiness",
        ),
        (
            "src/ops/testnet_wallclock_duration_evidence_contract_v0.py",
            "wallclock",
        ),
        (
            "src/ops/wallclock_session_evidence_v0.py",
            "wallclock",
        ),
    )

    validator_rules: tuple[tuple[str, str], ...] = (
        (
            "src/ops/durable_completion_validation/validators/reconciliation.py",
            "pe21_reconciliation",
        ),
        ("src/ops/durable_completion_validation/validators/recovery.py", "pe35_handoff_recovery"),
        ("src/ops/durable_completion_validation/validators/traceability.py", "pe37_traceability"),
        ("src/ops/durable_completion_validation/validators/operator_closure.py", "pe25_closure"),
        ("src/ops/durable_completion_validation/validators/event_stream.py", "pe38_readiness"),
    )

    for path, partition in path_rules:
        if path in files:
            partitions.add(partition)
            integration_scoped = True
            graph_only = False

    for path, partition in validator_rules:
        if path in files:
            partitions.add(partition)
            partitions.add("core_cross_chain")
            integration_scoped = True
            graph_only = False

    dc_prefix = "src/ops/durable_completion_validation/"
    for path in files:
        if not path.startswith(dc_prefix):
            continue
        name = Path(path).name
        if name == "graph.py":
            continue
        if name in {"models.py", "identity.py", "__init__.py"}:
            if name == "__init__.py":
                return None
            integration_scoped = True
            graph_only = False
            partitions.update({"core_cross_chain", "core_baseline_input"})
            continue
        if name.startswith("validators/") or path.endswith(".py") and "/validators/" in path:
            continue

    if not integration_scoped:
        return frozenset()

    if len(partitions - set(CORE_ALWAYS_PARTITIONS)) > 3:
        partitions.update({"core_baseline_input", "core_kwargs", "core_cross_chain"})

    return frozenset(partitions)


def estimate_partition_seconds(partitions: frozenset[str]) -> int:
    """Conservative serial estimate from historical ~21s/evaluate, ~0.5s static."""
    inventory = integration_partition_inventory()
    owner_text = _file_text(INTEGRATION_TEST_OWNER)
    evaluate_calls = owner_text.count(
        "evaluate_durable_run_primary_evidence_completion_integration("
    )
    eval_ratio = evaluate_calls / max(integration_owner_node_count(), 1)

    total = 0.0
    for partition in partitions:
        nodes = inventory.get(partition, ())
        eval_estimate = len(nodes) * eval_ratio
        total += eval_estimate * 21 + (len(nodes) - eval_estimate) * 0.5
    return int(total)


GLB019_A2B_ALLOWED_FILES: Final[frozenset[str]] = frozenset(
    {
        COMPLETION_FACADE_PATH,
        INTEGRATION_TEST_OWNER,
        "src/ops/durable_completion_validation/graph.py",
        "src/ops/durable_completion_validation/validators/event_stream.py",
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "scripts/ops/durable_completion_integration_partitions_v0.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

GLB019_A2B_ADDITIVE_PARTITIONS: Final[frozenset[str]] = frozenset(
    {
        *CORE_ALWAYS_PARTITIONS,
        "core_cross_chain",
        "pe38_readiness",
    }
)

_GLB019_FACADE_IMPORTS: Final[frozenset[str]] = frozenset(
    {
        "Glb019EventStreamProofBinding",
        "Glb019EventStreamValidationInput",
        "compute_glb019_event_stream_validation_input_digest",
        "default_minimal_glb019_proof_binding",
        "default_minimal_glb019_validation_input",
        "evaluate_glb019_event_stream_validation",
        "validate_glb019_event_stream_validation_input",
    }
)

_GLB019_FACADE_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "glb019_event_stream_validation_input",
        "glb019_event_stream_proof",
    }
)

_GLB019_FACADE_NEW_FUNCTION: Final = "_validate_glb019_event_stream_binding"

_GLB019_FACADE_INPUT_CLASS: Final = "DurableRunPrimaryEvidenceCompletionIntegrationInput"

_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _parse_unified_diff(patch_text: str) -> dict[str, list[str]]:
    by_path: dict[str, list[str]] = {}
    current_path: str | None = None
    for raw_line in patch_text.splitlines():
        if raw_line.startswith("diff --git "):
            parts = raw_line.split()
            current_path = None
            for part in parts[2:4]:
                if part.startswith("b/"):
                    current_path = part[2:]
                    break
                if part.startswith("a/"):
                    continue
            if current_path:
                by_path.setdefault(current_path, [])
            continue
        if current_path is None:
            continue
        if raw_line.startswith(("--- ", "+++ ", "index ", "new file mode", "deleted file mode")):
            continue
        if raw_line.startswith("@@"):
            by_path[current_path].append(raw_line)
            continue
        if raw_line.startswith(("+", "-", " ")):
            by_path[current_path].append(raw_line)
    return by_path


def _apply_unified_hunks(base_text: str, hunk_lines: list[str]) -> str:
    base_lines = base_text.splitlines(keepends=True)
    if base_text and not base_lines:
        base_lines = [base_text]
    if not base_text:
        base_lines = []
    out: list[str] = []
    src_idx = 0
    hunk_idx = 0
    while hunk_idx < len(hunk_lines):
        header = hunk_lines[hunk_idx]
        if not header.startswith("@@"):
            hunk_idx += 1
            continue
        match = _HUNK_HEADER.match(header)
        if not match:
            raise ValueError(f"invalid hunk header: {header!r}")
        old_start = int(match.group(1))
        hunk_idx += 1
        while src_idx < old_start - 1:
            out.append(base_lines[src_idx])
            src_idx += 1
        while hunk_idx < len(hunk_lines) and not hunk_lines[hunk_idx].startswith("@@"):
            line = hunk_lines[hunk_idx]
            if line.startswith(" "):
                if src_idx < len(base_lines):
                    out.append(base_lines[src_idx])
                    src_idx += 1
            elif line.startswith("-"):
                src_idx += 1
            elif line.startswith("+"):
                out.append(line[1:] + ("\n" if not line[1:].endswith("\n") else ""))
            hunk_idx += 1
    out.extend(base_lines[src_idx:])
    return "".join(out)


def _base_file_text(repo_root: Path, path: str) -> str:
    proc = subprocess.run(
        ["git", "show", f"origin/main:{path}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return proc.stdout
    file_path = repo_root / path
    return file_path.read_text(encoding="utf-8") if file_path.is_file() else ""


def _apply_patch_for_file(repo_root: Path, path: str, hunk_lines: list[str]) -> str:
    base_text = _base_file_text(repo_root, path)
    return _apply_unified_hunks(base_text, hunk_lines)


def _module_defs(tree: ast.Module) -> dict[str, ast.AST]:
    out: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = node
    return out


def _class_field_names(class_node: ast.ClassDef) -> set[str]:
    names: set[str] = set()
    for node in class_node.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def _function_calls(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def _stmt_fingerprint(stmt: ast.stmt) -> str:
    return ast.dump(stmt, include_attributes=False)


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _is_glb019_evaluate_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call) and _call_name(node) == "evaluate_glb019_event_stream_validation"
    )


_GLB019_ALLOWED_RETURN_DICT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "glb019_event_stream_proof",
        "glb019_event_stream_validation_input_digest",
    }
)

_GLB019_ALLOWED_CALL_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "glb019_result",
        "glb019_event_stream_validation_input",
        "glb019_event_stream_proof",
    }
)


def _strip_glb019_dict_keys(node: ast.Dict) -> None:
    keep_keys: list[ast.expr | None] = []
    keep_values: list[ast.expr] = []
    for key, value in zip(node.keys, node.values):
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            if key.value in _GLB019_ALLOWED_RETURN_DICT_KEYS:
                continue
        keep_keys.append(key)
        keep_values.append(value)
    node.keys = keep_keys
    node.values = keep_values


def _strip_allowed_glb019_call_keywords(node: ast.Call) -> None:
    node.keywords = [kw for kw in node.keywords if kw.arg not in _GLB019_ALLOWED_CALL_KEYWORDS]


def _clone_statement(stmt: ast.stmt) -> ast.stmt:
    return ast.parse(ast.unparse(stmt)).body[0]  # type: ignore[return-value]


def _strip_allowed_glb019_from_statement(stmt: ast.stmt) -> ast.stmt:
    cloned = _clone_statement(stmt)
    for node in ast.walk(cloned):
        if isinstance(node, ast.Dict):
            _strip_glb019_dict_keys(node)
        if isinstance(node, ast.Call):
            _strip_allowed_glb019_call_keywords(node)
    return cloned


def _is_allowed_validation_context_glb019_delta(after_stmt: ast.stmt) -> bool:
    if not isinstance(after_stmt, ast.Assign):
        return True
    if not (
        isinstance(after_stmt.value, ast.Call) and _call_name(after_stmt.value) == "ValidationContext"
    ):
        return True
    call = after_stmt.value
    glb019_keywords = [kw for kw in call.keywords if kw.arg == "glb019_result"]
    if not glb019_keywords:
        return True
    if len(glb019_keywords) != 1:
        return False
    keyword = glb019_keywords[0]
    return isinstance(keyword.value, ast.Name) and keyword.value.id == "glb019_result"


def _is_allowed_additive_glb019_statement(stmt: ast.stmt) -> bool:
    if not _is_allowed_validation_context_glb019_delta(stmt):
        return False
    if (
        isinstance(stmt, ast.Assign)
        and len(stmt.targets) == 1
        and isinstance(stmt.targets[0], ast.Name)
    ):
        target_name = stmt.targets[0].id
        if target_name == "glb019_result" and _is_glb019_evaluate_call(stmt.value):
            return True
        if target_name == "glb019_validation_input":
            return isinstance(stmt.value, ast.Call) and _call_name(stmt.value) == (
                "default_minimal_glb019_validation_input"
            )
        if target_name == "glb019_proof":
            return isinstance(stmt.value, ast.Call) and _call_name(stmt.value) == (
                "default_minimal_glb019_proof_binding"
            )
        if target_name == "expected_completion_identity_digest":
            return isinstance(stmt.value, ast.Call) and _call_name(stmt.value) == (
                "compute_completion_identity_digest"
            )
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        call = stmt.value
        if _call_name(call) == "extend" and call.args:
            arg = call.args[0]
            if (
                isinstance(arg, ast.Call)
                and _call_name(arg) == "_validate_glb019_event_stream_binding"
            ):
                return True
    return False


def _statements_equivalent_modulo_allowed_glb019(
    before_stmt: ast.stmt,
    after_stmt: ast.stmt,
) -> bool:
    if _stmt_fingerprint(before_stmt) == _stmt_fingerprint(after_stmt):
        return True
    before_norm = _strip_allowed_glb019_from_statement(before_stmt)
    after_norm = _strip_allowed_glb019_from_statement(after_stmt)
    return _stmt_fingerprint(before_norm) == _stmt_fingerprint(after_norm)


def function_statements_preserved_with_allowed_glb019(
    before_fn: ast.FunctionDef,
    after_fn: ast.FunctionDef,
) -> bool:
    """True when baseline general statements match head after removing allowed GLB-019 additions."""
    before_remaining = list(before_fn.body)
    for after_stmt in after_fn.body:
        if _is_allowed_additive_glb019_statement(after_stmt):
            continue
        if not before_remaining:
            return False
        before_stmt = before_remaining[0]
        if not _statements_equivalent_modulo_allowed_glb019(before_stmt, after_stmt):
            return False
        before_remaining.pop(0)
    return not before_remaining


def function_statement_diff_debug(
    before_fn: ast.FunctionDef,
    after_fn: ast.FunctionDef,
) -> dict[str, list[str]]:
    baseline = [_stmt_fingerprint(stmt) for stmt in before_fn.body]
    head = [_stmt_fingerprint(stmt) for stmt in after_fn.body]
    allowed_removed = [
        _stmt_fingerprint(stmt)
        for stmt in after_fn.body
        if _is_allowed_additive_glb019_statement(stmt)
    ]
    head_without_allowed: list[str] = []
    before_remaining = list(before_fn.body)
    mismatch: list[str] = []
    for after_stmt in after_fn.body:
        if _is_allowed_additive_glb019_statement(after_stmt):
            continue
        head_without_allowed.append(_stmt_fingerprint(after_stmt))
        if not before_remaining:
            mismatch.append(f"extra_head:{_stmt_fingerprint(after_stmt)}")
            continue
        before_stmt = before_remaining[0]
        if not _statements_equivalent_modulo_allowed_glb019(before_stmt, after_stmt):
            mismatch.append(
                f"baseline={_stmt_fingerprint(before_stmt)} head={_stmt_fingerprint(after_stmt)}"
            )
        before_remaining.pop(0)
    for stmt in before_remaining:
        mismatch.append(f"missing_head:{_stmt_fingerprint(stmt)}")
    return {
        "BASELINE_GENERAL_STATEMENTS": baseline,
        "HEAD_STATEMENTS": head,
        "REMOVED_ALLOWED_GLB019_FINGERPRINTS": allowed_removed,
        "HEAD_STATEMENTS_WITH_ALLOWED_GLB019_REMOVED": head_without_allowed,
        "REMAINING_DIFFERENCE": mismatch,
    }


def _parse_function_from_module(module_src: str, function_name: str) -> ast.FunctionDef:
    module = ast.parse(module_src)
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return node
    raise ValueError(f"missing function: {function_name}")


def _existing_modified_functions_preserve_general_statements(
    before: ast.Module,
    after: ast.Module,
) -> bool:
    before_defs = _module_defs(before)
    after_defs = _module_defs(after)
    for name, before_fn in before_defs.items():
        if name not in after_defs:
            continue
        after_fn = after_defs[name]
        if not isinstance(before_fn, ast.FunctionDef) or not isinstance(after_fn, ast.FunctionDef):
            continue
        if _stmt_fingerprint_list(before_fn) == _stmt_fingerprint_list(after_fn):
            continue
        if not function_statements_preserved_with_allowed_glb019(before_fn, after_fn):
            return False
    return True


def _stmt_fingerprint_list(fn: ast.FunctionDef) -> list[str]:
    return [_stmt_fingerprint(stmt) for stmt in fn.body]


def _validate_facade_ast(before: ast.Module, after: ast.Module) -> bool:
    before_defs = _module_defs(before)
    after_defs = _module_defs(after)
    new_funcs = set(after_defs) - set(before_defs)
    removed_funcs = set(before_defs) - set(after_defs)
    if removed_funcs:
        return False
    if new_funcs != {_GLB019_FACADE_NEW_FUNCTION}:
        return False
    before_input = before_defs.get(_GLB019_FACADE_INPUT_CLASS)
    after_input = after_defs.get(_GLB019_FACADE_INPUT_CLASS)
    if not isinstance(before_input, ast.ClassDef) or not isinstance(after_input, ast.ClassDef):
        return False
    added_fields = _class_field_names(after_input) - _class_field_names(before_input)
    removed_fields = _class_field_names(before_input) - _class_field_names(after_input)
    if removed_fields:
        return False
    if added_fields != _GLB019_FACADE_FIELDS:
        return False
    new_import_names: set[str] = set()
    for node in after.body:
        if isinstance(node, ast.ImportFrom) and node.module and "event_stream" in node.module:
            for alias in node.names:
                name = alias.asname or alias.name
                new_import_names.add(name)
    if not _GLB019_FACADE_IMPORTS.issubset(new_import_names):
        return False
    validate_fn = after_defs.get(
        "validate_durable_run_primary_evidence_completion_integration_input"
    )
    evaluate_fn = after_defs.get("evaluate_durable_run_primary_evidence_completion_integration")
    dict_fn = after_defs.get("_integration_input_dict")
    default_fn = after_defs.get("default_minimal_completion_integration_input")
    if not all(
        isinstance(fn, ast.FunctionDef) for fn in (validate_fn, evaluate_fn, dict_fn, default_fn)
    ):
        return False
    validate_calls = _function_calls(validate_fn)
    if "_validate_glb019_event_stream_binding" not in validate_calls:
        return False
    if not _existing_modified_functions_preserve_general_statements(before, after):
        return False
    glb019_assignments = [
        stmt
        for stmt in evaluate_fn.body  # type: ignore[union-attr]
        if isinstance(stmt, ast.Assign)
        and len(stmt.targets) == 1
        and isinstance(stmt.targets[0], ast.Name)
        and stmt.targets[0].id == "glb019_result"
        and _is_glb019_evaluate_call(stmt.value)
    ]
    if len(glb019_assignments) != 1:
        return False
    dict_src = ast.unparse(dict_fn)
    if (
        "glb019_event_stream_proof" not in dict_src
        or "glb019_event_stream_validation_input_digest" not in dict_src
    ):
        return False
    default_src = ast.unparse(default_fn)
    if (
        "glb019_event_stream_validation_input=" not in default_src
        or "glb019_event_stream_proof=" not in default_src
    ):
        return False
    return True


def _validate_graph_ast(before: ast.Module, after: ast.Module) -> bool:
    before_src = ast.unparse(before)
    after_src = ast.unparse(after)
    if (
        "VALIDATOR_EVENT_STREAM" not in after_src
        or "validate_glb019_event_stream_proof" not in after_src
    ):
        return False
    if "VALIDATOR_WALLCLOCK" not in after_src:
        return False
    for token in ("VALIDATOR_EVENT_STREAM", "event_stream"):
        if after_src.count(token) <= before_src.count(token):
            return False
    return True


def _validate_event_stream_ast(before: ast.Module, after: ast.Module) -> bool:
    before_defs = _module_defs(before)
    after_defs = _module_defs(after)
    if set(before_defs) != set(after_defs):
        return False
    fn = after_defs.get("validate_glb019_event_stream_proof")
    if not isinstance(fn, ast.FunctionDef):
        return False
    src = ast.unparse(fn)
    if "glb019_result is None" not in src:
        return False
    if " or {}" in src:
        return False
    return True


def _validate_integration_test_ast(before: ast.Module, after: ast.Module) -> bool:
    before_defs = _module_defs(before)
    after_defs = _module_defs(after)
    if set(before_defs) - set(after_defs):
        return False
    new_defs = set(after_defs) - set(before_defs)
    if not new_defs:
        return False
    if any(not name.startswith("test_glb019_") for name in new_defs):
        return False
    for name in before_defs:
        if ast.unparse(before_defs[name]) != ast.unparse(after_defs[name]):
            return False
    return True


def _validate_graph_test_ast(before: ast.Module, after: ast.Module) -> bool:
    before_defs = _module_defs(before)
    after_defs = _module_defs(after)
    removed = set(before_defs) - set(after_defs)
    if removed != {"test_glb019_no_production_graph_activation"}:
        return False
    new_names = set(after_defs) - set(before_defs)
    allowed_new = {
        "test_graph_event_stream_production_activation",
        "test_glb019_production_graph_happy_path",
        "test_glb019_missing_glb019_result_fail_closed",
        "test_glb019_graph_missing_result_blocks_completion_chain",
        "_glb019_result_for",
        "_graph_context",
    }
    if set(new_names) != allowed_new:
        return False
    for name in set(before_defs) & set(after_defs):
        before_fn = before_defs[name]
        after_fn = after_defs[name]
        if ast.unparse(before_fn) == ast.unparse(after_fn):
            continue
        after_src = ast.unparse(after_fn)
        before_src = ast.unparse(before_fn)
        if name == "_minimal_context":
            if "glb019_result=" not in after_src or "ValidationContext(" not in after_src:
                return False
            continue
        if "ValidationContext(" in before_src and "_graph_context(" in after_src:
            continue
        if "VALIDATOR_EVENT_STREAM" in after_src and "VALIDATOR_EVENT_STREAM" not in before_src:
            continue
        if name.startswith("test_glb019_"):
            continue
        if before_src != after_src and not (
            "glb019" in after_src
            or "VALIDATOR_EVENT_STREAM" in after_src
            or "_graph_context" in after_src
        ):
            return False
    return True


def _validate_partitions_ast(before: ast.Module, after: ast.Module) -> bool:
    before_src = ast.unparse(before)
    after_src = ast.unparse(after)
    if before_src == after_src:
        return False
    if after_src.count("glb019") <= before_src.count("glb019"):
        return False
    if "event_stream" not in after_src:
        return False
    if not (
        "glb019' in base or 'event_stream' in base" in after_src
        or 'glb019" in base or "event_stream" in base' in after_src
    ):
        return False
    return len(after_src) > len(before_src)


def _validate_ci_selector_test_ast(before: ast.Module, after: ast.Module) -> bool:
    before_src = ast.unparse(before)
    after_src = ast.unparse(after)
    if before_src == after_src:
        return False
    if "assert len(nodes) == 238" in before_src and "assert len(nodes) == 246" in after_src:
        return before_src.replace("238", "246") == after_src
    return False


_FILE_AST_VALIDATORS = {
    COMPLETION_FACADE_PATH: _validate_facade_ast,
    "src/ops/durable_completion_validation/graph.py": _validate_graph_ast,
    "src/ops/durable_completion_validation/validators/event_stream.py": _validate_event_stream_ast,
    INTEGRATION_TEST_OWNER: _validate_integration_test_ast,
    "tests/ops/test_durable_completion_validation_graph_v1.py": _validate_graph_test_ast,
    "scripts/ops/durable_completion_integration_partitions_v0.py": _validate_partitions_ast,
    "tests/ci/test_ci_diff_aware_test_selection_v1.py": _validate_ci_selector_test_ast,
}


class Glb019A2bChangeContractOutcome(enum.Enum):
    PASS = "pass"
    REJECT = "reject"
    UNAVAILABLE_OR_UNPARSEABLE = "unavailable_or_unparseable"


@dataclass(frozen=True)
class Glb019A2bChangeContractResult:
    outcome: Glb019A2bChangeContractOutcome
    partitions: frozenset[str] | None = None


_GLB019_STRICT_EVALUATE_ASSIGNMENT_PATHS: Final[frozenset[str]] = frozenset(
    {
        COMPLETION_FACADE_PATH,
    }
)


def _module_glb019_structural_constraints_valid(module: ast.Module) -> bool:
    """Fail closed on forbidden GLB-019 evaluate assignment targets in prod facade."""
    for node in ast.walk(module):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and _is_glb019_evaluate_call(node.value)
            and node.targets[0].id != "glb019_result"
        ):
            return False
    return True


def evaluate_glb019_a2b_change_contract(
    patch_text: str,
    *,
    repo_root: Path | None = None,
) -> Glb019A2bChangeContractResult:
    """Tri-state GLB-019 A2/B structural contract: PASS, REJECT, or UNAVAILABLE."""
    if not patch_text.strip():
        return Glb019A2bChangeContractResult(
            Glb019A2bChangeContractOutcome.UNAVAILABLE_OR_UNPARSEABLE
        )
    root = repo_root or Path.cwd()
    try:
        by_path = _parse_unified_diff(patch_text)
    except ValueError:
        return Glb019A2bChangeContractResult(
            Glb019A2bChangeContractOutcome.UNAVAILABLE_OR_UNPARSEABLE
        )
    if not by_path:
        return Glb019A2bChangeContractResult(
            Glb019A2bChangeContractOutcome.UNAVAILABLE_OR_UNPARSEABLE
        )
    if not set(by_path) <= GLB019_A2B_ALLOWED_FILES:
        return Glb019A2bChangeContractResult(Glb019A2bChangeContractOutcome.REJECT)
    if not GLB019_A2B_ALLOWED_FILES.issubset(set(by_path)):
        return Glb019A2bChangeContractResult(Glb019A2bChangeContractOutcome.REJECT)
    for path, hunk_lines in by_path.items():
        validator = _FILE_AST_VALIDATORS.get(path)
        if validator is None:
            return Glb019A2bChangeContractResult(Glb019A2bChangeContractOutcome.REJECT)
        try:
            before_text = _base_file_text(root, path)
            after_text = _apply_patch_for_file(root, path, hunk_lines)
            before_tree = ast.parse(before_text)
            after_tree = ast.parse(after_text)
        except (OSError, SyntaxError, ValueError):
            return Glb019A2bChangeContractResult(
                Glb019A2bChangeContractOutcome.UNAVAILABLE_OR_UNPARSEABLE
            )
        if path in _GLB019_STRICT_EVALUATE_ASSIGNMENT_PATHS and not _module_glb019_structural_constraints_valid(
            after_tree
        ):
            return Glb019A2bChangeContractResult(Glb019A2bChangeContractOutcome.REJECT)
        if not validator(before_tree, after_tree):
            return Glb019A2bChangeContractResult(Glb019A2bChangeContractOutcome.REJECT)
    return Glb019A2bChangeContractResult(
        Glb019A2bChangeContractOutcome.PASS,
        GLB019_A2B_ADDITIVE_PARTITIONS,
    )


def classify_glb019_a2b_additive_patch(
    patch_text: str,
    *,
    repo_root: Path | None = None,
) -> frozenset[str] | None:
    """Return bounded GLB-019 partition ids when patch matches the additive A2/B contract."""
    result = evaluate_glb019_a2b_change_contract(patch_text, repo_root=repo_root)
    if result.outcome == Glb019A2bChangeContractOutcome.PASS:
        return result.partitions
    return None


def collect_glb019_a2b_patch_text(
    *,
    base_ref: str = "origin/main",
    repo_root: Path | None = None,
    changed_files: list[str] | None = None,
) -> str | None:
    """Collect merge-base unified diff for GLB-019 contract paths (CI path)."""
    root = repo_root or Path.cwd()
    if changed_files is not None:
        diff_paths = sorted(set(changed_files) & GLB019_A2B_ALLOWED_FILES)
        if not diff_paths:
            return None
    else:
        diff_paths = sorted(GLB019_A2B_ALLOWED_FILES)
    merge_base = subprocess.run(
        ["git", "merge-base", base_ref, "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if merge_base.returncode != 0 or not merge_base.stdout.strip():
        return None
    mb = merge_base.stdout.strip()
    diff = subprocess.run(
        [
            "git",
            "diff",
            "--no-ext-diff",
            "--unified=0",
            f"{mb}...HEAD",
            "--",
            *diff_paths,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if diff.returncode not in {0, 1}:
        return None
    text = diff.stdout
    return text if text.strip() else None
