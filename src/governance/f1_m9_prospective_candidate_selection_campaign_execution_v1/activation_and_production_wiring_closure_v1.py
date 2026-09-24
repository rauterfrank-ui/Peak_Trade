"""Closure proof for F1/M9 REAL campaign activation and production wiring v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.orchestration_constants_v1 import (
    REAL_CAMPAIGN_EXECUTION_ENABLED_IN_PROCESS,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.production_real_public_md_session_adapter_v1 import (
    PRODUCTION_ADAPTER_CLASS_ID,
    PRODUCTION_ADAPTER_OWNER_ID,
    build_production_real_public_md_session_adapter_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.real_public_md_session_adapter_v1 import (
    FakeRealPublicMdSessionAdapterV1,
    resolve_canonical_real_md_supplier_runtime_binding_v1,
)

SCHEMA_VERSION: Final[str] = "f1_m9_real_campaign_activation_and_production_wiring_closure/v1"
WORKPACKAGE_ID: Final[str] = "F1_M9_REAL_CAMPAIGN_ACTIVATION_AND_PRODUCTION_WIRING_V1"
DECISION_CONFIG: Final[str] = (
    "config/governance/f1_m9_real_campaign_activation_and_production_wiring_v1_decision_v1.json"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/F1_M9_REAL_CAMPAIGN_ACTIVATION_AND_PRODUCTION_WIRING_NORMATIVE_V1.md"
)


def prove_f1_m9_real_campaign_activation_and_production_wiring_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[3]
    required = (
        root / NORMATIVE_SPEC,
        root / DECISION_CONFIG,
        root / "scripts/run_f1_m9_prospective_real_authorized_campaign_execution_v1.py",
        root / "src/ops/peak_trade_python_script_entry_bootstrap_v1.py",
        root / "src/governance/f1_m9_prospective_candidate_selection_campaign_execution_v1/"
        "production_real_public_md_session_adapter_v1.py",
        root / "tests/governance/test_f1_m9_real_campaign_activation_and_production_wiring_v1.py",
        root / "tests/governance/test_f1_m9_production_real_cli_entry_execution_smoke_v1.py",
    )
    if not all(p.is_file() for p in required):
        return False
    if not REAL_CAMPAIGN_EXECUTION_ENABLED_IN_PROCESS:
        return False
    supplier = resolve_canonical_real_md_supplier_runtime_binding_v1(repo_root=root)
    if not supplier.get("real_md_supplier_runtime_bound"):
        return False
    adapter = build_production_real_public_md_session_adapter_v1()
    if isinstance(adapter, FakeRealPublicMdSessionAdapterV1):
        return False
    if type(adapter).__name__ != PRODUCTION_ADAPTER_CLASS_ID:
        return False
    run_source = (
        root / "scripts/run_f1_m9_prospective_real_authorized_campaign_execution_v1.py"
    ).read_text(encoding="utf-8")
    bootstrap_source = (root / "src/ops/peak_trade_python_script_entry_bootstrap_v1.py").read_text(
        encoding="utf-8"
    )
    if "FakeRealPublicMdSessionAdapterV1" in run_source:
        return False
    if "build_production_real_public_md_session_adapter_v1" not in run_source:
        return False
    if "peak_trade_python_script_entry_bootstrap_v1" not in run_source:
        return False
    if "ensure_peak_trade_script_entry_bootstrap_v1" not in bootstrap_source:
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if decision.get("production_adapter_owner_id") != PRODUCTION_ADAPTER_OWNER_ID:
        return False
    flags = (
        "real_campaign_execution_process_enabled",
        "canonical_real_cli_bootstrap_ready",
        "production_public_md_adapter_present",
        "production_public_md_adapter_canonical_supplier_bound",
        "production_real_entry_wired",
        "fresh_authorization_can_reach_real_effect_boundary",
        "no_further_code_change_required_for_real_run",
    )
    if not all(decision.get(k) is True for k in flags):
        return False
    if decision.get("campaign_executed") is True:
        return False
    if decision.get("public_market_data_external_read_occurred") is True:
        return False
    return True


__all__ = [
    "DECISION_CONFIG",
    "NORMATIVE_SPEC",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "prove_f1_m9_real_campaign_activation_and_production_wiring_v1",
]
