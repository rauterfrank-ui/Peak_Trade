"""Bind F1/M9 prospective campaign to CURRENT authorized public MD supplier (metadata only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    REAL_MD_SUPPLIER_ID,
    REAL_MD_SUPPLIER_MODULE,
)


def resolve_real_md_supplier_binding_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    module_path = REAL_MD_SUPPLIER_MODULE.replace(".", "/")
    py_path = root / "src" / f"{module_path}.py"
    resolved = py_path.is_file()
    return {
        "real_md_supplier_resolved": resolved,
        "real_md_supplier_id": REAL_MD_SUPPLIER_ID if resolved else None,
        "real_md_supplier_module": REAL_MD_SUPPLIER_MODULE,
        "private_api_credentials_required": False,
        "order_endpoint_allowed": False,
        "account_endpoint_allowed": False,
        "synthetic_fallback_satisfies_real": False,
        "fixture_fallback_satisfies_real": False,
        "missing_real_md_execution_dependency": not resolved,
    }


__all__ = ["resolve_real_md_supplier_binding_v1"]
