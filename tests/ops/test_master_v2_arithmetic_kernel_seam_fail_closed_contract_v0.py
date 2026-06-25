"""Static fail-closed contract: Master V2 arithmetic kernel seam v0.

Documents the current unwired state: ``futures_accounting.py`` is the canonical Decimal
kernel candidate, while Master V2 / completion / adapter paths must not claim operative
trading-arithmetic proof. Zero-order and replay-proof classification evidence is not
PnL/fee/fill/position/reconciliation arithmetic evidence.

Non-authorizing. No runtime, network, testnet execution, or kernel wiring.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

from src.ops.bounded_master_v2_testnet_completion_path_wiring_v0 import (
    BoundedMasterV2TestnetCompletionPathWiringResultV0,
    assert_forbidden_testnet_execution_claims_absent,
    build_testnet_bounded_adapter_completion_path_wiring_section,
)
from src.ops.bounded_futures_testnet_zero_order_lifecycle_integration_contract_v0 import (
    AUTHORITY_LIFT as ZERO_ORDER_AUTHORITY_LIFT,
    evaluate_zero_order_lifecycle_integration,
    default_minimal_integration_input,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

PACKAGE_MARKER = "MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_V0=true"
AUTHORITY_LIFT = False

CANONICAL_ARITHMETIC_KERNEL_OWNER = "src/execution/paper/futures_accounting.py"
FUTURE_ARITHMETIC_WIRING_MUST_REUSE_OWNER = CANONICAL_ARITHMETIC_KERNEL_OWNER

_KERNEL_SRC = REPO_ROOT / "src" / "execution" / "paper" / "futures_accounting.py"

_CANONICAL_KERNEL_CALLABLES = (
    "unrealized_pnl",
    "realize_pnl_on_close",
    "notional_value",
    "apply_fee_on_notional",
    "funding_payment_quote",
    "build_futures_paper_accounting_snapshot_v0",
)

_CANONICAL_KERNEL_TYPES = (
    "FuturesPosition",
    "FuturesSide",
    "FuturesPaperAccountingSnapshotV0",
)

# Structured machine-summary keys that must never assert operative trading arithmetic.
_FORBIDDEN_TRADING_ARITHMETIC_PROVEN_KEYS = frozenset(
    {
        "TRADING_ARITHMETIC_PROVEN",
        "ARITHMETIC_KERNEL_BOUND",
        "ARITHMETIC_KERNEL_WIRED",
        "FUTURES_ACCOUNTING_BOUND",
        "FUTURES_ACCOUNTING_WIRED",
        "PNL_PROVEN",
        "PNL_ARITHMETIC_PROVEN",
        "REALIZED_PNL_PROVEN",
        "UNREALIZED_PNL_PROVEN",
        "FEE_ARITHMETIC_PROVEN",
        "FUNDING_ARITHMETIC_PROVEN",
        "SLIPPAGE_ARITHMETIC_PROVEN",
        "FILL_ARITHMETIC_PROVEN",
        "POSITION_ARITHMETIC_PROVEN",
        "RECONCILIATION_ARITHMETIC_PROVEN",
        "OPERATIVE_PNL_EVIDENCE",
        "OPERATIVE_FEE_EVIDENCE",
        "OPERATIVE_FILL_EVIDENCE",
        "OPERATIVE_RECONCILIATION_EVIDENCE",
    }
)

_MASTER_V2_ARITHMETIC_SEAM_PATHS = (
    REPO_ROOT / "src" / "ops" / "bounded_master_v2_testnet_completion_path_wiring_v0.py",
    REPO_ROOT / "src" / "ops" / "offline_master_v2_replay_six_node_validation_graph_binding_v0.py",
    REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py",
    *sorted((REPO_ROOT / "src" / "trading" / "master_v2").glob("*.py")),
    *sorted((REPO_ROOT / "src" / "trading" / "master_v2").glob("**/*.py")),
)


def _imports_futures_accounting_submodule(tree: ast.AST) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name or ""
                if name == "futures_accounting" or name.endswith(".futures_accounting"):
                    violations.append(f"import {name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module
            if mod is not None and (
                mod == "futures_accounting"
                or mod.endswith(".futures_accounting")
                or mod == "src.execution.paper.futures_accounting"
            ):
                violations.append(f"from {mod} import ...")
            if mod == "src.execution.paper":
                for alias in node.names:
                    if alias.name == "futures_accounting":
                        violations.append("from src.execution.paper import futures_accounting")
    return violations


def _assert_no_trading_arithmetic_proven_claims(claims: dict[str, object]) -> None:
    for key in _FORBIDDEN_TRADING_ARITHMETIC_PROVEN_KEYS:
        if claims.get(key) is True:
            raise AssertionError(f"forbidden trading-arithmetic claim: {key}=true")
    assert assert_forbidden_testnet_execution_claims_absent(claims) == []


def _zero_order_wiring_machine_summary() -> dict[str, object]:
    result = BoundedMasterV2TestnetCompletionPathWiringResultV0(
        layer_version="v0",
        wiring_pass=True,
        admission_pass=True,
        fail_reasons=(),
        orders_total=0,
        cancels_total=0,
        fills_total=0,
        positions_opened_total=0,
        bounded_testnet_completion_path_master_v2_wiring_present=True,
        bounded_testnet_completion_path_six_node_graph_wiring_present=True,
        bounded_testnet_completion_path_decision_digest_wiring_present=True,
        bounded_testnet_completion_path_retention_wiring_present=True,
        bounded_testnet_zero_order_admission_boundary_present=True,
        missing_testnet_market_input_fails_closed=False,
        testnet_runner_reuses_canonical_completion_path=True,
        replay_proof_classification_bound=True,
        replay_proof_event_stream_non_authorizing=True,
    )
    return dict(result.to_machine_lines())


def test_canonical_futures_accounting_kernel_identity_and_decimal_semantics() -> None:
    assert _KERNEL_SRC.is_file(), CANONICAL_ARITHMETIC_KERNEL_OWNER
    tree = ast.parse(_KERNEL_SRC.read_text(encoding="utf-8"))
    import_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    import_from_roots = {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "decimal" in import_roots | import_from_roots

    kernel = importlib.import_module("src.execution.paper.futures_accounting")
    for name in _CANONICAL_KERNEL_CALLABLES:
        assert callable(getattr(kernel, name, None)), name
    for name in _CANONICAL_KERNEL_TYPES:
        assert hasattr(kernel, name), name


def test_master_v2_completion_adapter_replay_paths_unwired_from_futures_accounting() -> None:
    seen: set[Path] = set()
    for path in _MASTER_V2_ARITHMETIC_SEAM_PATHS:
        if not path.is_file() or path in seen:
            continue
        seen.add(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        bad = _imports_futures_accounting_submodule(tree)
        assert not bad, f"{path.relative_to(REPO_ROOT)}: forbidden futures_accounting import: {bad}"


def test_completion_and_adapter_machine_summary_forbids_trading_arithmetic_proven_claims() -> None:
    plan_section = build_testnet_bounded_adapter_completion_path_wiring_section(
        run_id="arithmetic-seam-contract-v0",
        mode="plan_only",
        market_input=None,
        retention_verification=None,
    )
    for summary in (
        _zero_order_wiring_machine_summary(),
        plan_section["machine_summary"],
    ):
        _assert_no_trading_arithmetic_proven_claims(summary)
        assert summary["ORDERS_TOTAL"] == 0
        assert summary["FILLS_TOTAL"] == 0


def test_zero_order_lifecycle_and_classification_do_not_imply_arithmetic_evidence() -> None:
    zero_order = evaluate_zero_order_lifecycle_integration(default_minimal_integration_input())
    assert zero_order["orders_created"] == 0
    assert zero_order["positions_changed"] == 0
    _assert_no_trading_arithmetic_proven_claims(zero_order)
    assert zero_order["pe27_zero_order_lifecycle_static_integration_proven"] is True
    assert zero_order["authority_lift"] is False


def test_contract_is_non_authorizing() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_MARKER in text
    assert AUTHORITY_LIFT is False
    assert ZERO_ORDER_AUTHORITY_LIFT is False


def test_future_seam_must_reuse_decimal_kernel_without_formula_duplication() -> None:
    assert FUTURE_ARITHMETIC_WIRING_MUST_REUSE_OWNER == CANONICAL_ARITHMETIC_KERNEL_OWNER
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("test_")
    }
    forbidden_formula_names = {
        "unrealized_pnl",
        "realize_pnl_on_close",
        "notional_value",
        "apply_fee_on_notional",
        "funding_payment_quote",
    }
    assert defined.isdisjoint(forbidden_formula_names)
