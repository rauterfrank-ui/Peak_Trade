"""Focused unit/property tests for unbound derive_scope_event_distances_v1."""

from __future__ import annotations

import ast
import math
from decimal import Decimal
from pathlib import Path

from src.ops.derive_scope_event_distances_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    FAILURE_REASON_INVALID_INPUT,
)
from src.ops.derive_scope_event_distances_v1.derive_v1 import derive_scope_event_distances_v1
from src.ops.derive_scope_event_distances_v1.golden_vectors_v1 import (
    GOLDEN_INVALID_VECTORS_V1,
    GOLDEN_VALID_VECTORS_V1,
)
from src.ops.derive_scope_event_distances_v1.result_v1 import DerivedScopeEventDistancesResultV1

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "src/ops/derive_scope_event_distances_v1"

PRODUCTIVE_CONSUMER_ROOTS: tuple[str, ...] = (
    "src/trading",
    "src/live",
    "src/execution",
    "src/execution_simple",
    "src/ops/decision_config_ownership_and_consumer_closure_v1",
    "src/ops/dynamic_scope_persistence_binding_v1",
    "src/ops/exit_policy_producer_binding_v1",
)

_FORBIDDEN_MODULE_PREFIXES: tuple[str, ...] = (
    "src.ops.derive_scope_event_distances_v1",
    "ops.derive_scope_event_distances_v1",
)

_ALLOWED_PRODUCTIVE_DERIVE_IMPORT_REL_PATHS: frozenset[str] = frozenset(
    {
        "src/trading/master_v2/layer_c_scope_event_distance_binding_v1.py",
    }
)

# Productive bridges must import layer_c binding, not derive_scope_event_distances_v1 directly.
_ALLOWED_LAYER_C_BINDING_IMPORT_REL_PREFIXES: tuple[str, ...] = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/",
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2/",
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
)


def _iter_python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts))


def _imported_modules(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.append(node.module)
    return tuple(names)


def _is_forbidden_import(module: str) -> bool:
    return any(
        module == prefix or module.startswith(f"{prefix}.") for prefix in _FORBIDDEN_MODULE_PREFIXES
    )


def test_golden_valid_vectors_retain_the_full_input_band_in_every_field() -> None:
    assert len(GOLDEN_VALID_VECTORS_V1) >= 6
    for vector in GOLDEN_VALID_VECTORS_V1:
        result = derive_scope_event_distances_v1(vector.current_hysteresis_band)
        assert result.ok is True
        assert result.failure_reason is None
        assert result.up_distance == vector.up_distance == vector.current_hysteresis_band
        assert result.adverse_exit_distance == vector.adverse_exit_distance == result.up_distance
        assert result.reversal_distance == vector.reversal_distance == result.up_distance


def test_deterministic_repeat_of_valid_and_invalid_inputs() -> None:
    for vector in GOLDEN_VALID_VECTORS_V1:
        first = derive_scope_event_distances_v1(vector.current_hysteresis_band)
        second = derive_scope_event_distances_v1(vector.current_hysteresis_band)
        assert first == second
    for vector in GOLDEN_INVALID_VECTORS_V1:
        first = derive_scope_event_distances_v1(vector.current_hysteresis_band)
        second = derive_scope_event_distances_v1(vector.current_hysteresis_band)
        assert first == second
        assert first.ok is False


def test_golden_invalid_vectors_are_fail_closed_result_without_raise() -> None:
    assert len(GOLDEN_INVALID_VECTORS_V1) >= 8
    extra_invalid: tuple[object, ...] = (Decimal("25"),)
    for vector in GOLDEN_INVALID_VECTORS_V1:
        result = derive_scope_event_distances_v1(vector.current_hysteresis_band)
        assert isinstance(result, DerivedScopeEventDistancesResultV1)
        assert result.ok is False
        assert result.up_distance is None
        assert result.adverse_exit_distance is None
        assert result.reversal_distance is None
        assert result.failure_reason == FAILURE_REASON_INVALID_INPUT
    for value in extra_invalid:
        result = derive_scope_event_distances_v1(value)
        assert result.ok is False
        assert result.failure_reason == FAILURE_REASON_INVALID_INPUT
        assert result.up_distance is None


def test_result_contract_authority_effect_is_none() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert DerivedScopeEventDistancesResultV1.AUTHORITY_EFFECT == "NONE"
    valid = derive_scope_event_distances_v1(25.0)
    invalid = derive_scope_event_distances_v1(float("nan"))
    assert valid.AUTHORITY_EFFECT == "NONE"
    assert invalid.AUTHORITY_EFFECT == "NONE"


def test_no_int_decimal_or_string_coercion() -> None:
    assert derive_scope_event_distances_v1(25).ok is False
    assert derive_scope_event_distances_v1(Decimal("25")).ok is False
    assert derive_scope_event_distances_v1("25.0").ok is False
    assert derive_scope_event_distances_v1(25.0).ok is True


def test_nan_inf_zero_and_negative_are_invalid_without_partial_result() -> None:
    for value in (float("nan"), float("inf"), float("-inf"), 0.0, -0.0, -12.5):
        result = derive_scope_event_distances_v1(value)
        assert result.ok is False
        assert result.up_distance is None
        assert result.adverse_exit_distance is None
        assert result.reversal_distance is None


def test_no_one_floor_and_no_hard_max_in_pure_function() -> None:
    tiny = derive_scope_event_distances_v1(0.5)
    large = derive_scope_event_distances_v1(5000.0)
    assert tiny.ok is True
    assert tiny.up_distance == 0.5
    assert tiny.up_distance != 1.0
    assert large.ok is True
    assert large.up_distance == 5000.0


def test_source_has_no_cap63_fallback_or_clamp_literals_as_outputs() -> None:
    derive_source = (PACKAGE_ROOT / "derive_v1.py").read_text(encoding="utf-8")
    assert "200.0" not in derive_source
    assert "clamp" not in derive_source
    assert "fallback" not in derive_source
    assert "hard_max" not in derive_source
    assert "last_derived" not in derive_source
    assert "CAP63" not in derive_source


def test_productive_consumer_callgraph_is_unbound() -> None:
    hits: list[str] = []
    for root in PRODUCTIVE_CONSUMER_ROOTS:
        for path in _iter_python_files(REPO_ROOT / root):
            rel = str(path.relative_to(REPO_ROOT))
            if rel in _ALLOWED_PRODUCTIVE_DERIVE_IMPORT_REL_PATHS:
                continue
            for module in _imported_modules(path):
                if _is_forbidden_import(module):
                    hits.append(f"{rel}:{module}")
    assert hits == []


def test_no_src_tree_outside_package_imports_the_function() -> None:
    hits: list[str] = []
    for path in _iter_python_files(REPO_ROOT / "src"):
        if PACKAGE_ROOT in path.parents or path.parent == PACKAGE_ROOT:
            continue
        rel = str(path.relative_to(REPO_ROOT))
        if rel in _ALLOWED_PRODUCTIVE_DERIVE_IMPORT_REL_PATHS:
            continue
        for module in _imported_modules(path):
            if _is_forbidden_import(module):
                hits.append(f"{rel}:{module}")
    assert hits == []


def test_math_isfinite_rejects_nan_even_when_type_is_float() -> None:
    assert type(float("nan")) is float
    assert math.isfinite(float("nan")) is False
    assert derive_scope_event_distances_v1(float("nan")).ok is False
