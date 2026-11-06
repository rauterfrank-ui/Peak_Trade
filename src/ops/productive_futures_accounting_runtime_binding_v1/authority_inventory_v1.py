"""Inventory of accounting authority surfaces for Cap 3.1 legacy check."""

from __future__ import annotations

from typing import Any

from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    AUTHORITY_OWNER,
    CANONICAL_KERNEL_OWNER,
    CANONICAL_KERNEL_PATH,
    SINGLE_WRITER_IDENTITY,
)


def inventory_accounting_authority_surfaces_v1() -> dict[str, Any]:
    """Declare productive vs legacy/local accounting authorities."""
    return {
        "productive_accounting_authority": AUTHORITY_OWNER,
        "canonical_kernel_owner": CANONICAL_KERNEL_OWNER,
        "canonical_kernel_path": CANONICAL_KERNEL_PATH,
        "single_writer_identity": SINGLE_WRITER_IDENTITY,
        "legacy_or_local_surfaces": [
            {
                "path": "src/ops/integrated_paper_shadow_observation_session_v1/portfolio_economics_model_v1.py",
                "role": "LEGACY_SIMULATED_PORTFOLIO_SHELL",
                "productive_accounting_authority": False,
                "notes": "Fill/economics shell may remain for non-productive research; Cap 3.1 productive PnL authority is canonical futures_accounting via binding.",
            },
            {
                "path": "src/execution/position_ledger.py",
                "role": "EXECUTION_LEDGER_LOCAL_ACCOUNTING",
                "productive_accounting_authority": False,
            },
            {
                "path": "src/execution/ledger/pnl.py",
                "role": "EXECUTION_LEDGER_LOCAL_ACCOUNTING",
                "productive_accounting_authority": False,
            },
            {
                "path": "src/backtest/p28/accounting_v1.py",
                "role": "BACKTEST_LOCAL",
                "productive_accounting_authority": False,
            },
            {
                "path": "src/backtest/p29/accounting_v2.py",
                "role": "BACKTEST_LOCAL",
                "productive_accounting_authority": False,
            },
        ],
        "dashboard_authority_effect": False,
        "allowlist_selection_authority": False,
        "direct_instrument_override_allowed": False,
        "second_accounting_kernel_created": False,
        "canonical_kernel_reused": True,
    }
