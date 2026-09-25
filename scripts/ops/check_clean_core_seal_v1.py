#!/usr/bin/env python3
"""CLEAN_CORE_SEAL_V1 — static repository/CI seal verifier.

Stdlib only. No trading-package import. No runtime hook.

Exit codes:
  0 — SEALED checkpoint matches
  1 — seal violation
  2 — usage / IO error
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "clean_core_seal_manifest_v1"
ACCEPTED_STATE = "SEALED"
MANIFEST_REL = "config/governance/clean_core_seal_manifest_v1.json"
LINT_GATE_REL = ".github/workflows/lint_gate.yml"
LINT_GATE_NEEDLE = "scripts/ops/check_clean_core_seal_v1.py"
WHOLE_FILE = "WHOLE_FILE"
MIXED_FILE = "MIXED_FILE"

# Frozen census membership (paths/modes/symbols). Digests live only in the manifest.
CENSUS_MEMBERS: tuple[dict[str, Any], ...] = (
    {
        "id": "SEAL_CORE_01",
        "path": "src/trading/master_v2/double_play_state.py",
        "mode": WHOLE_FILE,
    },
    {
        "id": "SEAL_CORE_02",
        "path": "src/trading/master_v2/chop_scope_event_policy_binding_v1.py",
        "mode": MIXED_FILE,
        "definitions": (
            "apply_chop_scope_event_policy_v1",
            "chop_scope_policy_blocks_side_transition_v1",
        ),
        "assignments": (),
    },
    {
        "id": "SEAL_CORE_03",
        "path": "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
        "mode": MIXED_FILE,
        "definitions": (
            "EntryExitDirectionState",
            "PositionState",
            "ReconciliationState",
            "TradingGate",
            "SafetyMode",
            "ExistingPositionSide",
            "ExitClass",
            "DecisionOutcome",
            "EntryEligibility",
            "PositionManagementAction",
            "ReversalState",
            "PolicyBlockedReason",
            "DecisionPrecedenceStage",
            "PolicySignalV0",
            "DoublePlayEntryExitPolicyV0",
            "DoublePlayEntryExitPolicyInputV0",
            "EntryExitPolicyDecisionV0",
            "evaluate_double_play_entry_exit_policy_v0",
        ),
        "assignments": (),
    },
    {
        "id": "SEAL_CORE_04",
        "path": "src/trading/master_v2/double_play_composition_matrix_v1.py",
        "mode": MIXED_FILE,
        "definitions": (
            "CompositionDirectionState",
            "PositionManagementContext",
            "CompositionStatus",
            "CompositionSelectedSide",
            "CompositionConflictStatus",
            "CompositionChopGuardStatus",
            "CompositionBlockedReason",
            "BothCandidateOutcome",
            "BothInvalidOutcome",
            "SuitabilityResultRefV1",
            "DoublePlayCompositionPolicyV1",
            "DoublePlayCompositionInputV1",
            "DoublePlayCompositionResultV1",
            "evaluate_double_play_composition_matrix_v1",
        ),
        "assignments": (),
    },
    {
        "id": "SEAL_CORE_05",
        "path": "src/trading/master_v2/survival_assessment_v1.py",
        "mode": WHOLE_FILE,
    },
    {
        "id": "SEAL_CORE_06",
        "path": "src/trading/master_v2/suitability_binding_v1.py",
        "mode": WHOLE_FILE,
    },
    {
        "id": "SEAL_CORE_07",
        "path": "src/trading/master_v2/post_confirmation_survival_suitability_composition_binding_v1.py",
        "mode": MIXED_FILE,
        "definitions": (
            "assert_post_c3_downstream_confirmation_non_authority_v1",
            "assert_c4_c3_assessment_identity_binding_v1",
        ),
        "assignments": (
            "COMPOSITION_REMAINS_SOLE_CONFIRMED_ADMISSIBILITY_GATE",
            "SURVIVAL_CONFIRMED_EARLY_GATE",
            "SUITABILITY_CONFIRMED_EARLY_GATE",
        ),
    },
    {
        "id": "SEAL_CORE_08",
        "path": "src/trading/master_v2/directional_assessment_v1.py",
        "mode": MIXED_FILE,
        "definitions": (
            "DirectionalAssessmentSide",
            "DirectionalAssessmentStatus",
            "DirectionalAssessmentHardBlockReason",
            "ScopeEventRefV1",
            "DirectionalConfirmationStateV1",
            "DirectionalAssessmentPolicyV1",
            "DirectionalAssessmentInputV1",
            "DirectionalAssessmentV1",
            "validate_directional_assessment_policy",
            "compute_signal_strength",
            "compute_directional_confidence",
            "_collect_input_gate_blocks",
            "_finalize_assessment",
        ),
        "assignments": (),
    },
    {
        "id": "SEAL_CORE_09",
        "path": "src/trading/master_v2/directional_assessment_confirmation_integration_v1.py",
        "mode": WHOLE_FILE,
    },
    {
        "id": "SEAL_CORE_10",
        "path": "src/trading/master_v2/canonical_market_context_v1.py",
        "mode": WHOLE_FILE,
    },
    {
        "id": "SEAL_CORE_11",
        "path": "src/trading/master_v2/canonical_scope_initialization_v1.py",
        "mode": WHOLE_FILE,
    },
    {
        "id": "SEAL_CORE_12",
        "path": "src/trading/master_v2/deterministic_scope_event_generator_v1.py",
        "mode": MIXED_FILE,
        "definitions": (
            "ScopeDirectionState",
            "ScopeCandidateKind",
            "CanonicalScopeEventType",
            "ScopeEventBlockReason",
            "ScopeEventGeneratorPolicyV1",
            "ScopeCooldownStateV1",
            "ScopeConfirmationStateV1",
            "ScopeEventGeneratorInputV1",
            "EvaluatedThresholdsV1",
            "ScopeEventSemanticBindingV1",
            "ScopeEventEvidenceV1",
            "generate_deterministic_scope_event",
        ),
        "assignments": (),
    },
    {
        "id": "SEAL_CORE_13",
        "path": "src/trading/market_state/distinct_market_observation_acceptor_v1.py",
        "mode": MIXED_FILE,
        "definitions": (
            "ObservationClassification",
            "ObservationReasonCode",
            "ObservationTransportMetadataV1",
            "ObservationCandidateV1",
            "ObservationAcceptanceStateV1",
            "ObservationAcceptanceResultV1",
            "evaluate_distinct_market_observation_v1",
            "commit_observation_acceptance_v1",
            "DistinctMarketObservationAcceptorV1",
        ),
        "assignments": (),
    },
    {
        "id": "SEAL_CORE_14",
        "path": "src/trading/market_state/directional_confirmation_progress_v1.py",
        "mode": WHOLE_FILE,
    },
    {
        "id": "SEAL_CORE_15",
        "path": "src/trading/market_state/observation_identity_v1.py",
        "mode": MIXED_FILE,
        "definitions": (
            "MarketObservationEpoch",
            "InstrumentObservationKeyV1",
            "ObservationIdentityV1",
        ),
        "assignments": ("DISTINCTNESS_IDENTITY_FIELDS",),
    },
    {
        "id": "SEAL_CORE_16",
        "path": "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
        "mode": MIXED_FILE,
        "definitions": (
            "_canonical_scope_event_to_scope_event",
            "_side_state_to_entry_exit_direction",
            "_rules_for_cycle_v1",
            "_resolve_c3_confirmation_binding_v1",
            "_survival_input_for_assessment",
            "_suitability_input_for_assessment",
            "resolve_integrated_scope_adverse_exit_signal_v0",
            "resolve_integrated_reversal_preparation_entry_exit_binding_v0",
        ),
        "assignments": (
            "_FORBIDDEN_INSTRUMENT_SUBSTRINGS",
            "_DEFAULT_STATIC_LIMITS",
            "_DEFAULT_RUNTIME_ENVELOPE",
            "_DEFAULT_SCOPE_RULES",
        ),
        "join_projection": {
            "function": "run_integrated_offline_trading_logic_replay_v1",
            "callee_names": (
                "bind_canonical_market_context_event",
                "with_computed_input_digest",
                "initialize_canonical_scope",
                "_rules_for_cycle_v1",
                "derive_active_side",
                "update_dynamic_boundaries",
                "generate_deterministic_scope_event",
                "with_computed_scope_event_digest",
                "_canonical_scope_event_to_scope_event",
                "_resolve_c3_confirmation_binding_v1",
                "evaluate_elementary_direction_from_observation_acceptance_v1",
                "prior_presence_from_dual_carrier_v1",
                "apply_single_lane_confirmation_lifecycle_v1",
                "evaluate_directional_assessment_with_confirmation_progress_v1",
                "active_single_lane_presence_v1",
                "persist_single_lane_into_dual_carrier_v1",
                "assert_post_c3_downstream_confirmation_non_authority_v1",
                "_survival_input_for_assessment",
                "evaluate_survival_assessment_v1",
                "_suitability_input_for_assessment",
                "evaluate_suitability_binding_v1",
                "build_single_lane_composition_candidate_v1",
                "assert_c4_single_lane_assessment_identity_binding_v1",
                "compute_composition_input_digest",
                "evaluate_double_play_composition_matrix_v1",
                "transition_state",
                "resolve_integrated_scope_adverse_exit_signal_v0",
                "resolve_integrated_reversal_preparation_entry_exit_binding_v0",
                "_side_state_to_entry_exit_direction",
                "compute_entry_exit_policy_input_digest",
                "evaluate_double_play_entry_exit_policy_v0",
            ),
        },
    },
    {
        "id": "SEAL_CORE_17",
        "path": "src/trading/master_v2/reversal_preparation_scenario_binding_adapter_v0.py",
        "mode": MIXED_FILE,
        "definitions": (
            "is_reversal_preparation_composition_v0",
            "derive_reversal_preparation_position_context_v0",
            "project_composition_for_reversal_preparation_entry_exit_v0",
        ),
        "assignments": (),
    },
    {
        "id": "SEAL_CORE_18",
        "path": "src/trading/master_v2/scope_event_generator_scenario_binding_adapter_v0.py",
        "mode": MIXED_FILE,
        "definitions": ("derive_scope_adverse_exit_signal_v0",),
        "assignments": (),
    },
    {
        "id": "SEAL_CORE_19",
        "path": "src/trading/master_v2/canonical_volatility_binding_and_provenance_transport_v1.py",
        "mode": MIXED_FILE,
        "definitions": ("resolve_legacy_volatility_float_for_consumer_v1",),
        "assignments": (),
    },
    {
        "id": "SEAL_CORE_20",
        "path": "src/trading/master_v2/canonical_volatility_default_quarantine_v1.py",
        "mode": MIXED_FILE,
        "definitions": (
            "admit_positive_volatility_without_strategy_floor_v1",
            "require_admitted_legacy_volatility_float_v1",
            "quarantine_explicit_replay_default_volatility_v1",
        ),
        "assignments": (),
    },
)

FROZEN_PATHS: tuple[str, ...] = tuple(str(m["path"]) for m in CENSUS_MEMBERS)
FROZEN_MEMBER_COUNT = len(CENSUS_MEMBERS)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_text(payload: str) -> str:
    return _sha256_bytes(payload.encode("utf-8"))


def whole_file_digest(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_dump(node: ast.AST) -> str:
    return ast.dump(node, include_attributes=False)


def _strip_function_decorators(node: ast.AST) -> ast.AST:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        copied = copy.deepcopy(node)
        copied.decorator_list = []
        return copied
    return node


def _iter_module_definitions(tree: ast.Module) -> list[tuple[str, ast.AST, str]]:
    found: list[tuple[str, ast.AST, str]] = []
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found.append((stmt.name, stmt, "definition"))
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    found.append((target.id, stmt, "assignment"))
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            found.append((stmt.target.id, stmt, "assignment"))
    return found


def _call_name(func: ast.AST) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _walk_calls_in_order(node: ast.AST) -> Iterable[ast.Call]:
    if isinstance(node, ast.Call):
        yield node
    for child in ast.iter_child_nodes(node):
        yield from _walk_calls_in_order(child)


def join_callee_projection(fn_node: ast.AST, allowed: tuple[str, ...]) -> tuple[str, ...]:
    allow = set(allowed)
    names: list[str] = []
    for call in _walk_calls_in_order(fn_node):
        name = _call_name(call.func)
        if name is not None and name in allow:
            names.append(name)
    return tuple(names)


def resolve_protected_nodes(
    source: str, *, definitions: tuple[str, ...], assignments: tuple[str, ...]
) -> tuple[dict[str, ast.AST], list[str]]:
    errors: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {}, [f"parse_failure:{exc}"]
    if not isinstance(tree, ast.Module):
        return {}, ["parse_failure:not_a_module"]

    index: dict[tuple[str, str], list[ast.AST]] = {}
    for name, node, kind in _iter_module_definitions(tree):
        index.setdefault((kind, name), []).append(node)

    resolved: dict[str, ast.AST] = {}
    wanted: list[tuple[str, str]] = [("definition", n) for n in definitions] + [
        ("assignment", n) for n in assignments
    ]
    for kind, name in wanted:
        hits = index.get((kind, name), [])
        if not hits:
            errors.append(f"missing_protected_symbol:{kind}:{name}")
            continue
        if len(hits) > 1:
            errors.append(f"duplicate_protected_symbol:{kind}:{name}")
            continue
        node = hits[0]
        if kind == "definition":
            node = _strip_function_decorators(node)
        resolved[f"{kind}:{name}"] = node
    return resolved, errors


def mixed_member_digest(
    source: str,
    *,
    definitions: tuple[str, ...],
    assignments: tuple[str, ...],
    join_projection: dict[str, Any] | None = None,
) -> tuple[str, list[str], dict[str, str]]:
    resolved, errors = resolve_protected_nodes(
        source, definitions=definitions, assignments=assignments
    )
    parts: dict[str, str] = {}
    for key in sorted(resolved):
        parts[key] = _sha256_text(_canonical_dump(resolved[key]))

    sequence: list[str] = []
    if join_projection:
        fn_name = str(join_projection["function"])
        allowed = tuple(join_projection["callee_names"])
        fn_resolved, fn_errors = resolve_protected_nodes(
            source, definitions=(fn_name,), assignments=()
        )
        errors.extend(fn_errors)
        fn_node = fn_resolved.get(f"definition:{fn_name}")
        if fn_node is not None:
            sequence = list(join_callee_projection(fn_node, allowed))
            parts[f"join_projection:{fn_name}"] = _sha256_text("\n".join(sequence) + "\n")
            parts[f"join_projection_sequence:{fn_name}"] = json.dumps(
                sequence, separators=(",", ":")
            )

    if errors:
        return "", errors, parts
    digest_parts = {
        key: value
        for key, value in parts.items()
        if not key.startswith("join_projection_sequence:")
    }
    canonical = json.dumps(digest_parts, sort_keys=True, separators=(",", ":"))
    return _sha256_text(canonical), [], parts


def census_index() -> dict[str, dict[str, Any]]:
    return {str(m["id"]): m for m in CENSUS_MEMBERS}


def _fail(messages: list[str]) -> int:
    payload = {
        "CLEAN_CORE_SEAL_V1": "FAIL",
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "ERRORS": messages,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1


def _ok(extra: dict[str, Any]) -> int:
    payload = {
        "CLEAN_CORE_SEAL_V1": "PASS",
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "STATE": ACCEPTED_STATE,
        "MEMBER_COUNT": FROZEN_MEMBER_COUNT,
        **extra,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def load_manifest(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.is_file():
        return None, ["missing_manifest"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"malformed_manifest:{exc}"]
    if not isinstance(data, dict):
        return None, ["malformed_manifest:not_an_object"]
    return data, []


def validate_manifest_schema(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("unsupported_manifest_version")
    if manifest.get("state") != ACCEPTED_STATE:
        errors.append("manifest_state_not_sealed")
    if manifest.get("unseal_implemented") is True:
        errors.append("unseal_implemented_forbidden")
    members = manifest.get("members")
    if not isinstance(members, list):
        errors.append("malformed_manifest:members")
        return errors
    if len(members) != FROZEN_MEMBER_COUNT:
        errors.append("membership_count_mismatch")
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    frozen = census_index()
    for raw in members:
        if not isinstance(raw, dict):
            errors.append("malformed_manifest:member_not_object")
            continue
        member_id = raw.get("id")
        path = raw.get("path")
        mode = raw.get("mode")
        if member_id in seen_ids:
            errors.append(f"duplicate_member_id:{member_id}")
        seen_ids.add(str(member_id))
        if path in seen_paths:
            errors.append(f"duplicate_member_path:{path}")
        seen_paths.add(str(path))
        if member_id not in frozen:
            errors.append(f"unknown_member_id:{member_id}")
            continue
        expected = frozen[str(member_id)]
        if path != expected["path"]:
            errors.append(f"member_path_mismatch:{member_id}")
        if mode != expected["mode"]:
            errors.append(f"member_mode_mismatch:{member_id}")
        if expected["mode"] == MIXED_FILE:
            defs = tuple(raw.get("definitions") or ())
            assigns = tuple(raw.get("assignments") or ())
            if defs != tuple(expected.get("definitions") or ()):
                errors.append(f"protected_definitions_mismatch:{member_id}")
            if assigns != tuple(expected.get("assignments") or ()):
                errors.append(f"protected_assignments_mismatch:{member_id}")
            if "join_projection" in expected:
                jp = raw.get("join_projection") or {}
                exp_jp = expected["join_projection"]
                if jp.get("function") != exp_jp["function"]:
                    errors.append(f"join_projection_function_mismatch:{member_id}")
                if tuple(jp.get("callee_names") or ()) != tuple(exp_jp["callee_names"]):
                    errors.append(f"join_projection_callees_mismatch:{member_id}")
    missing_ids = [mid for mid in frozen if mid not in seen_ids]
    for mid in missing_ids:
        errors.append(f"census_member_removed:{mid}")
    extra_ids = sorted(seen_ids - set(frozen))
    for mid in extra_ids:
        errors.append(f"census_member_added:{mid}")
    if set(seen_paths) != set(FROZEN_PATHS) and "malformed_manifest:members" not in errors:
        missing_paths = sorted(set(FROZEN_PATHS) - seen_paths)
        extra_paths = sorted(seen_paths - set(FROZEN_PATHS))
        for path in missing_paths:
            errors.append(f"census_path_removed:{path}")
        for path in extra_paths:
            errors.append(f"census_path_added:{path}")
    return errors


def lint_gate_binding_errors(repo_root: Path) -> list[str]:
    path = repo_root / LINT_GATE_REL
    if not path.is_file():
        return ["lint_gate_workflow_missing"]
    text = path.read_text(encoding="utf-8")
    if LINT_GATE_NEEDLE not in text:
        return ["lint_gate_verifier_not_invoked"]
    if "detect.outputs.applicable" in text:
        # Fail only if the seal step itself is applicable-gated.
        lines = text.splitlines()
        seal_idx = None
        for i, line in enumerate(lines):
            if LINT_GATE_NEEDLE in line:
                seal_idx = i
                break
        if seal_idx is None:
            return ["lint_gate_verifier_not_invoked"]
        window = "\n".join(lines[max(0, seal_idx - 12) : seal_idx + 1])
        if "steps.detect.outputs.applicable" in window:
            return ["lint_gate_verifier_applicable_gated"]
    return []


def verify_member(repo_root: Path, member: dict[str, Any], frozen: dict[str, Any]) -> list[str]:
    rel = str(frozen["path"])
    path = repo_root / rel
    if not path.is_file():
        return [f"missing_protected_path:{rel}"]
    mode = frozen["mode"]
    if mode == WHOLE_FILE:
        actual = whole_file_digest(path)
        expected = member.get("content_sha256")
        if actual != expected:
            return [f"whole_file_digest_mismatch:{rel}"]
        return []
    source = path.read_text(encoding="utf-8")
    digest, errors, _parts = mixed_member_digest(
        source,
        definitions=tuple(frozen.get("definitions") or ()),
        assignments=tuple(frozen.get("assignments") or ()),
        join_projection=frozen.get("join_projection"),
    )
    if errors:
        return [f"{rel}:{err}" for err in errors]
    expected = member.get("ast_sha256")
    if digest != expected:
        return [f"protected_ast_digest_mismatch:{rel}"]
    return []


def compute_member_record(repo_root: Path, frozen: dict[str, Any]) -> dict[str, Any]:
    rel = str(frozen["path"])
    path = repo_root / rel
    record: dict[str, Any] = {
        "id": frozen["id"],
        "path": rel,
        "mode": frozen["mode"],
    }
    if frozen["mode"] == WHOLE_FILE:
        record["content_sha256"] = whole_file_digest(path)
        return record
    source = path.read_text(encoding="utf-8")
    digest, errors, parts = mixed_member_digest(
        source,
        definitions=tuple(frozen.get("definitions") or ()),
        assignments=tuple(frozen.get("assignments") or ()),
        join_projection=frozen.get("join_projection"),
    )
    if errors:
        raise RuntimeError(f"{rel}: " + ";".join(errors))
    record["definitions"] = list(frozen.get("definitions") or ())
    record["assignments"] = list(frozen.get("assignments") or ())
    if "join_projection" in frozen:
        jp = frozen["join_projection"]
        record["join_projection"] = {
            "function": jp["function"],
            "callee_names": list(jp["callee_names"]),
        }
        seq_key = f"join_projection_sequence:{jp['function']}"
        record["join_projection_sequence"] = json.loads(parts[seq_key])
    record["ast_sha256"] = digest
    return record


def emit_manifest(repo_root: Path) -> dict[str, Any]:
    members = [compute_member_record(repo_root, frozen) for frozen in CENSUS_MEMBERS]
    return {
        "schema_version": SCHEMA_VERSION,
        "state": ACCEPTED_STATE,
        "document_class": "SUBORDINATE_ALLOWLIST_NOT_SECOND_SSOT",
        "canonical_authority": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        "census_bound_origin_main_sha": "44946b4b85076f8c7ed17cbcb4ba4cda5f8695c5",
        "seal_core_count": FROZEN_MEMBER_COUNT,
        "whole_file_count": sum(1 for m in CENSUS_MEMBERS if m["mode"] == WHOLE_FILE),
        "mixed_file_count": sum(1 for m in CENSUS_MEMBERS if m["mode"] == MIXED_FILE),
        "unseal_implemented": False,
        "runtime_performance_overhead": "ZERO",
        "runtime_import": False,
        "hash_strategy": {
            "whole_file": "sha256_of_exact_repository_file_bytes",
            "mixed_file": "sha256_of_canonical_ast_dump_include_attributes_false_decorators_stripped_on_functions",
            "replay_join": "ordered_sealed_callee_name_projection_of_run_integrated_offline_trading_logic_replay_v1",
        },
        "members": members,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CLEAN_CORE_SEAL_V1 static verifier")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--emit-manifest", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--require-lint-gate-binding", action="store_true", default=True)
    parser.add_argument("--skip-lint-gate-binding", action="store_true")
    args = parser.parse_args(argv)

    repo_root = (args.repo_root or Path(__file__).resolve().parents[2]).resolve()
    manifest_path = args.manifest or (repo_root / MANIFEST_REL)

    if args.emit_manifest:
        try:
            payload = emit_manifest(repo_root)
        except Exception as exc:
            print(f"ERR: {exc}", file=sys.stderr)
            return 2
        text = json.dumps(payload, indent=2, sort_keys=False) + "\n"
        if args.output is not None:
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0

    errors: list[str] = []
    if not args.skip_lint_gate_binding and args.require_lint_gate_binding:
        errors.extend(lint_gate_binding_errors(repo_root))

    manifest, load_errors = load_manifest(manifest_path)
    if load_errors:
        return _fail(errors + load_errors)
    assert manifest is not None
    errors.extend(validate_manifest_schema(manifest))
    if errors:
        return _fail(errors)

    frozen = census_index()
    for member in manifest["members"]:
        member_id = str(member["id"])
        errors.extend(verify_member(repo_root, member, frozen[member_id]))
    if errors:
        return _fail(errors)
    return _ok(
        {
            "MANIFEST": str(manifest_path.relative_to(repo_root)),
            "LINT_GATE_BINDING": "PASS",
        }
    )


if __name__ == "__main__":
    sys.exit(main())
