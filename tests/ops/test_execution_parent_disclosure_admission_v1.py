"""Execution disclosure admission stays beside membership. Offline only."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from scripts.ops.execution_parent_disclosure_v1.bind_v1 import bind_execution_disclosure_v1
from scripts.ops.execution_parent_disclosure_v1.constants_v1 import (
    ACTIVATION,
    AUTHORITY,
    EXPECTED_BASELINE_SHA,
    EXPECTED_BASELINE_TREE,
    STATUS_ADMITTED,
    STATUS_DISCLOSURE_SCOPE_ABSENT,
    STATUS_LOADER_REJECT,
    STATUS_REJECTED,
    STATUS_UNEXPECTED_MEMBERSHIP_ACCEPTED,
)
from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    STATUS_FORGED_PROVENANCE,
    STATUS_INVALID_PROVENANCE,
    STATUS_PIN_MISMATCH,
    STATUS_SCOPE_EMPTY,
)
from tests.ops.guardian_framework_fixtures_v1 import (
    CENSUS_EMBEDDED_PIN,
    LANDSCAPE_EMBEDDED_COMMIT,
    LANDSCAPE_EMBEDDED_TREE,
    honest_provenance,
)

_PACKAGE = Path("scripts/ops/execution_parent_disclosure_v1")
_OBSERVED_PATH = "scripts/ops/guardian_parent_slot_loader_v1/load_v1.py"
_FORBIDDEN_IMPORT_PREFIXES = (
    "trading",
    "src.trading",
    "src.execution",
    "src.risk",
    "double_play",
    "execution_guardian_binding_verifier_v1",
    "ghosv_bounded_context_v1",
    "scoped_ghv_crosswalk_adapter_v1",
    "scoped_causal_graph_adapter_v1",
    "generic_ghosv_kernel_v1",
)


def _provenance() -> dict[str, dict[str, str]]:
    body = honest_provenance()
    body["domain_evidence"] = {
        "commit_pin": EXPECTED_BASELINE_SHA,
        "tree_pin": EXPECTED_BASELINE_TREE,
    }
    return body


def _observed() -> dict[str, object]:
    return {
        "subject_id": "execution-loader-entry",
        "classification": "OBSERVED",
        "path": _OBSERVED_PATH,
        "symbol": "load_parent_slots_v1",
        "start_line": 34,
        "end_line": 34,
    }


def _unknown() -> dict[str, object]:
    return {
        "subject_id": "execution-not-inventoried",
        "classification": "UNKNOWN",
        "unknown_reason": "subject inventory is not part of admission",
    }


def _bind(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "authoritative_commit_sha": EXPECTED_BASELINE_SHA,
        "authoritative_tree_sha": EXPECTED_BASELINE_TREE,
        "declared_commit_sha": EXPECTED_BASELINE_SHA,
        "declared_tree_sha": EXPECTED_BASELINE_TREE,
        "provenance": _provenance(),
        "disclosure_subjects": [_observed()],
    }
    payload.update(overrides)
    return bind_execution_disclosure_v1(**payload)


def _assert_locked(result: dict[str, object]) -> None:
    assert result["authority"] == AUTHORITY
    assert result["trading_authority"] == AUTHORITY
    assert result["safety_authority"] == AUTHORITY
    assert result["execution_authority"] == AUTHORITY
    assert result["post_authority"] == AUTHORITY
    assert result["activation"] == ACTIVATION
    assert result["membership_ratified"] is False
    assert result["guardian_ratified"] is False
    assert result["domain_bound"] is False
    assert result["operationally_ready"] is False
    assert result["causal_closure_proven"] is False
    assert result["current_validated"] is False
    assert result["post_allowed"] is False
    assert result["external_effect_authorized"] is False
    assert result["productive_activation"] is False
    assert result["double_play_full_owner_lock"] == "LEVEL_3"
    assert result["domain_functional_members"] == []
    assert result["functional_membership_derived"] is False
    assert result["parent_assignment_performed"] is False
    assert result["adapters_invoked"] is False
    assert result["files_written"] is False
    assert result["instrument_ids"] == {
        "ghv_id": "PARENT_EXECUTION_GHV",
        "causal_graph_id": "PARENT_EXECUTION_CURRENT_CAUSAL_GRAPH",
        "ghosv_id": "PARENT_EXECUTION_GHOSV",
    }


def test_valid_pin_and_empty_membership_reach_scope_empty() -> None:
    result = _bind()

    assert result["status"] == STATUS_ADMITTED
    assert result["membership_binding_status"] == STATUS_SCOPE_EMPTY
    assert result["historical_sources"] == [
        "census",
        "landscape_commit",
        "landscape_tree",
        "graph",
    ]
    _assert_locked(result)


def test_empty_disclosure_subjects_are_absent() -> None:
    result = _bind(disclosure_subjects=[])

    assert result["status"] == STATUS_DISCLOSURE_SCOPE_ABSENT
    assert result["membership_binding_status"] == STATUS_SCOPE_EMPTY
    assert result["observed_subjects"] == []
    assert result["unknown_subjects"] == []
    _assert_locked(result)


def test_filled_execution_membership_scope_stays_loader_rejected(tmp_path: Path) -> None:
    registry = json.loads(
        Path("config/governance/guardian_parent_slot_registry_v1.json").read_text(encoding="utf-8")
    )
    execution = next(slot for slot in registry["slots"] if slot["parent_id"] == "PARENT_EXECUTION")
    execution["scope"]["domain_functional_members"] = ["smuggled-member"]
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")

    result = _bind(registry_path=path)

    assert result["status"] == STATUS_LOADER_REJECT
    assert (
        "membership_present:PARENT_EXECUTION:domain_functional_members" in result["loader_reasons"]
    )
    assert result["observed_subjects"] == []
    _assert_locked(result)


def test_forged_current_provenance_is_rejected() -> None:
    provenance = _provenance()
    provenance["census"]["currency"] = "CURRENT"

    result = _bind(provenance=provenance)

    assert result["status"] == STATUS_FORGED_PROVENANCE
    assert "census_currency_forged_current" in result["reasons"]
    assert result["observed_subjects"] == []
    _assert_locked(result)


def test_wrong_declared_commit_is_pin_mismatch() -> None:
    result = _bind(declared_commit_sha=CENSUS_EMBEDDED_PIN)

    assert result["status"] == STATUS_PIN_MISMATCH
    assert "commit" in result["mismatches"]
    _assert_locked(result)


def test_wrong_authoritative_tree_is_baseline_mismatch() -> None:
    result = _bind(authoritative_tree_sha=LANDSCAPE_EMBEDDED_TREE)

    assert result["status"] == STATUS_PIN_MISMATCH
    assert result["mismatches"] == ["baseline_tree"]
    _assert_locked(result)


def test_invalid_provenance_is_rejected() -> None:
    provenance = _provenance()
    del provenance["census"]

    result = _bind(provenance=provenance)

    assert result["status"] == STATUS_INVALID_PROVENANCE
    assert "provenance_missing:census" in result["reasons"]
    _assert_locked(result)


def test_observed_subject_requires_path_symbol_and_lines() -> None:
    result = _bind()

    assert result["status"] == STATUS_ADMITTED
    assert result["observed_subjects"] == [
        {
            "subject_id": "execution-loader-entry",
            "classification": "OBSERVED",
            "path": _OBSERVED_PATH,
            "symbol": "load_parent_slots_v1",
            "start_line": 34,
            "end_line": 34,
            "tree_sha": EXPECTED_BASELINE_TREE,
            "functional_membership": False,
        }
    ]
    missing = dict(_observed())
    missing["symbol"] = "not_a_real_symbol"
    rejected = _bind(disclosure_subjects=[missing])
    assert rejected["status"] == STATUS_REJECTED
    assert rejected["reasons"] == ["disclosure_subjects[0]_symbol_absent"]
    assert rejected["observed_subjects"] == []
    _assert_locked(result)
    _assert_locked(rejected)


def test_unknown_subject_stays_unknown_and_not_a_member() -> None:
    result = _bind(disclosure_subjects=[_unknown()])

    assert result["status"] == STATUS_ADMITTED
    assert result["unknown_subjects"] == [
        {
            "subject_id": "execution-not-inventoried",
            "classification": "UNKNOWN",
            "unknown_reason": "subject inventory is not part of admission",
            "functional_membership": False,
        }
    ]
    assert result["observed_subjects"] == []
    assert result["domain_functional_members"] == []
    _assert_locked(result)


def test_unexpected_membership_accepted_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "scripts.ops.execution_parent_disclosure_v1.bind_v1.bind_pin_and_scope_v1",
        lambda **kwargs: {"status": "ACCEPTED", "stale_sources": [], "reasons": []},
    )

    result = _bind()

    assert result["status"] == STATUS_UNEXPECTED_MEMBERSHIP_ACCEPTED
    assert result["membership_binding_status"] == "ACCEPTED"
    assert result["observed_subjects"] == []
    _assert_locked(result)


def test_authority_and_activation_never_succeed() -> None:
    result = _bind(authority="TRADE", activation="ENABLED", guardian_ratified=True)

    assert result["status"] == STATUS_REJECTED
    assert result["reasons"] == [
        "authority_rejected",
        "activation_rejected",
        "guardian_ratification_rejected",
    ]
    _assert_locked(result)


def test_admission_call_does_not_write(monkeypatch: pytest.MonkeyPatch) -> None:
    def _forbid(*args: object, **kwargs: object) -> None:
        raise AssertionError("admission write")

    monkeypatch.setattr(Path, "write_text", _forbid)
    monkeypatch.setattr(Path, "mkdir", _forbid)

    result = _bind(disclosure_subjects=[_observed(), _unknown()])

    assert result["status"] == STATUS_ADMITTED
    assert result["files_written"] is False
    assert len(result["observed_subjects"]) == 1
    assert len(result["unknown_subjects"]) == 1


def test_package_has_no_productive_or_writer_imports() -> None:
    modules = sorted(_PACKAGE.glob("*.py"))
    assert modules
    for path in modules:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
            elif isinstance(node, ast.Call):
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else ""
                assert name not in {"write_text", "mkdir", "write_bytes"}
        for imported in imports:
            assert all(prefix not in imported for prefix in _FORBIDDEN_IMPORT_PREFIXES)
        text = path.read_text(encoding="utf-8")
        assert "checkout" not in text
        assert "git commit" not in text


def test_historical_pins_are_not_relabeled_current() -> None:
    result = _bind()

    assert result["current_validated"] is False
    assert CENSUS_EMBEDDED_PIN != EXPECTED_BASELINE_SHA
    assert LANDSCAPE_EMBEDDED_COMMIT != EXPECTED_BASELINE_SHA
    assert LANDSCAPE_EMBEDDED_TREE != EXPECTED_BASELINE_TREE
    assert "census" in result["historical_sources"]
    assert "landscape_commit" in result["historical_sources"]
