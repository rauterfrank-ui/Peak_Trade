"""Architecture guards for multi-session typed-vol actionable-strata evidence v1."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.constants_v1 import (
    ARTIFACT_RELATIVE_PATH,
    DOUBLE_PLAY_TRADING_LOGIC_UNCHANGED,
    FORBIDDEN_SCAFFOLD_SUBSTRINGS,
    HARDCODED_3600_SECOND_BRANCH_FORBIDDEN,
    HARDCODED_AGE_DECISION_PROBE_FORBIDDEN,
    MASTER_V2_ORCHESTRATION_SEMANTICS_UNCHANGED,
    NUMERIC_MAX_AGE_SELECTED,
    PACKAGE_MARKER,
    POLICY_ENFORCEMENT_ADDED,
    PRODUCTIVE_SESSION_EXECUTION_IN_DEFAULT_IMPORT,
    READY_FOR_POLICY_ENFORCEMENT,
    READY_FOR_POLICY_IMPLEMENTATION,
    READY_FOR_POLICY_SELECTION,
    REUSED_CMC_BINDER,
    REUSED_S03_INDEPENDENCE,
    REUSED_TYPED_MATERIALIZER,
    SPEC_RELATIVE_PATH,
    STATIC_VOLATILITY_DEFAULT_FORBIDDEN,
    SYNTHETIC_VOLATILITY_VALUES_FORBIDDEN,
)


def assert_architecture_guards_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    package_dir = Path(__file__).resolve().parent

    if not PACKAGE_MARKER.endswith("=true"):
        raise RuntimeError("PACKAGE_MARKER_INVALID")
    if PRODUCTIVE_SESSION_EXECUTION_IN_DEFAULT_IMPORT:
        raise RuntimeError("default_import_must_not_execute_sessions")
    if (
        READY_FOR_POLICY_SELECTION
        or READY_FOR_POLICY_IMPLEMENTATION
        or READY_FOR_POLICY_ENFORCEMENT
    ):
        raise RuntimeError("policy_readiness_must_remain_false")
    if NUMERIC_MAX_AGE_SELECTED or POLICY_ENFORCEMENT_ADDED:
        raise RuntimeError("policy_selection_or_enforcement_flag_true")
    if not (
        SYNTHETIC_VOLATILITY_VALUES_FORBIDDEN
        and STATIC_VOLATILITY_DEFAULT_FORBIDDEN
        and HARDCODED_AGE_DECISION_PROBE_FORBIDDEN
        and HARDCODED_3600_SECOND_BRANCH_FORBIDDEN
    ):
        raise RuntimeError("scaffold_forbid_flags_disabled")
    if not (MASTER_V2_ORCHESTRATION_SEMANTICS_UNCHANGED and DOUBLE_PLAY_TRADING_LOGIC_UNCHANGED):
        raise RuntimeError("core_strategy_unchanged_flags_disabled")

    for rel in (ARTIFACT_RELATIVE_PATH, SPEC_RELATIVE_PATH):
        if not (root / rel).is_file():
            raise RuntimeError(f"missing_capability_artifact:{rel}")

    # S03 orchestrator must no longer contain scaffolds.
    s03_orch = (
        root / "src/research/canonical_volatility_numeric_max_age_additional_evidence_"
        "s03_productive_session_execution_owner_v1/orchestrator_v1.py"
    )
    text = s03_orch.read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_SCAFFOLD_SUBSTRINGS:
        if forbidden in text:
            raise RuntimeError(f"s03_scaffold_still_present:{forbidden}")
    if "write_typed_s03_session_cycle_evidence_v1" not in text:
        raise RuntimeError("s03_orchestrator_missing_typed_cycle_writer")

    cycle = (package_dir / "s03_typed_evidence_cycle_v1.py").read_text(encoding="utf-8")
    harness = (package_dir / "full_alpha_counterfactual_harness_v1.py").read_text(encoding="utf-8")
    typed = (package_dir / "typed_volatility_comparison_v1.py").read_text(encoding="utf-8")
    for required, blob in (
        (REUSED_TYPED_MATERIALIZER, typed),
        (REUSED_CMC_BINDER, harness),
        (REUSED_S03_INDEPENDENCE, cycle),
    ):
        if required not in blob:
            raise RuntimeError(f"missing_reuse:{required}")

    return {
        "ok": True,
        "SYNTHETIC_VOLATILITY_SCAFFOLD_REMOVED": True,
        "HARDCODED_AGE_DECISION_PROBE_REMOVED": True,
        "NO_CORE_ALPHA_CHANGE": True,
    }
