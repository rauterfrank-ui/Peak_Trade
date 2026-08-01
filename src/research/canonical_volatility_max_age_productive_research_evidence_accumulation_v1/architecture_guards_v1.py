"""Architecture guards: accumulation must not become trading authority."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    ALPHA_MUTATION_OCCURRED,
    BLOCKED_FOR_PARAMETER_DECISION,
    CONFIG_MUTATION_OCCURRED,
    COUNTERFACTUAL_ONLY,
    ENFORCEMENT_APPLIED,
    EVIDENCE_SUFFICIENT_FOR_PARAMETER_DECISION,
    FORBIDDEN_IMPORT_SUBSTRINGS,
    HARD_STOP,
    LIVE_AUTHORIZATION,
    LIVE_TESTNET_ORDER_ACTIVATION_OCCURRED,
    NUMERIC_MAX_AGE_DECIDED,
    NUMERIC_PRODUCTIVE_ACCUMULATION_CAPABILITY_ID,
    NUMERIC_THRESHOLD_SELECTED,
    ORDER_AUTHORITY_INTRODUCED,
    PARAMETER_PROMOTED,
    PRODUCTIVE_POLICY_MUTATION_OCCURRED,
    PRODUCTIVE_TRADING_BEHAVIOR_CHANGED,
    READY_FOR_ENFORCEMENT,
    READY_FOR_PARAMETER_PROMOTION,
    READY_FOR_THRESHOLD_SELECTION,
    REGIME_LABEL_IS_RESEARCH_METADATA_ONLY,
    REGIME_LABEL_MUTATES_ALPHA,
    REGIME_LABEL_MUTATES_POLICY,
    REGIME_LABEL_MUTATES_POSITION,
    REVIEW_MODE_ID,
    THRESHOLD_STATUS,
)


def assert_architecture_guards_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    package_dir = (
        root
        / "src/research/canonical_volatility_max_age_productive_research_evidence_accumulation_v1"
    )
    import_lines: list[str] = []
    code_parts: list[str] = []
    for path in sorted(package_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if path.name not in {"architecture_guards_v1.py", "constants_v1.py"}:
            code_parts.append(text)
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                import_lines.append(stripped)
    code_blob = "\n".join(code_parts)
    imports_blob = "\n".join(import_lines)

    for token in FORBIDDEN_IMPORT_SUBSTRINGS:
        if token in imports_blob:
            raise RuntimeError(f"TRADING_AUTHORITY_IMPORT_FORBIDDEN:{token}")

    forbidden_true = (
        "NUMERIC_THRESHOLD_SELECTED = True",
        "PARAMETER_PROMOTED = True",
        "ENFORCEMENT_APPLIED = True",
        "NUMERIC_MAX_AGE_DECIDED = True",
        "LIVE_AUTHORIZATION = True",
        "READY_FOR_THRESHOLD_SELECTION = True",
        "READY_FOR_PARAMETER_PROMOTION = True",
        "READY_FOR_ENFORCEMENT = True",
        "ALPHA_MUTATION_OCCURRED = True",
        "PRODUCTIVE_POLICY_MUTATION_OCCURRED = True",
        "CONFIG_MUTATION_OCCURRED = True",
        "PRODUCTIVE_TRADING_BEHAVIOR_CHANGED = True",
        "ORDER_AUTHORITY_INTRODUCED = True",
        "REGIME_LABEL_MUTATES_ALPHA = True",
        "REGIME_LABEL_MUTATES_POLICY = True",
        "REGIME_LABEL_MUTATES_POSITION = True",
    )
    for token in forbidden_true:
        if token in code_blob:
            raise RuntimeError(f"FORBIDDEN_AUTHORITY_FLAG:{token}")

    if "demote_trading_gate" in code_blob:
        raise RuntimeError("TRADING_GATE_DEMOTION_FORBIDDEN")
    for order_token in ("place_order(", "submit_order("):
        if order_token in code_blob:
            raise RuntimeError("ORDER_PATH_FORBIDDEN")
    if "RECOMMENDED_SINGLE_THRESHOLD" in code_blob:
        raise RuntimeError("THRESHOLD_RECOMMENDATION_FORBIDDEN")

    if (
        NUMERIC_THRESHOLD_SELECTED
        or PARAMETER_PROMOTED
        or ENFORCEMENT_APPLIED
        or NUMERIC_MAX_AGE_DECIDED
        or LIVE_AUTHORIZATION
        or READY_FOR_THRESHOLD_SELECTION
        or READY_FOR_PARAMETER_PROMOTION
        or READY_FOR_ENFORCEMENT
        or ALPHA_MUTATION_OCCURRED
        or PRODUCTIVE_POLICY_MUTATION_OCCURRED
        or CONFIG_MUTATION_OCCURRED
        or PRODUCTIVE_TRADING_BEHAVIOR_CHANGED
        or LIVE_TESTNET_ORDER_ACTIVATION_OCCURRED
        or ORDER_AUTHORITY_INTRODUCED
        or REGIME_LABEL_MUTATES_ALPHA
        or REGIME_LABEL_MUTATES_POLICY
        or REGIME_LABEL_MUTATES_POSITION
    ):
        raise RuntimeError("AUTHORITY_FLAG_DRIFT")
    if THRESHOLD_STATUS != "UNRESOLVED_MAX_AGE":
        raise RuntimeError("THRESHOLD_STATUS_DRIFT")
    if not HARD_STOP:
        raise RuntimeError("HARD_STOP_REQUIRED")
    if not REGIME_LABEL_IS_RESEARCH_METADATA_ONLY:
        raise RuntimeError("REGIME_METADATA_MUST_REMAIN_NON_AUTHORITY")

    bridge = (
        root
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
        / "hardening_cycle_bridge_v2.py"
    ).read_text(encoding="utf-8")
    if "accumulate_productive_research_evidence_from_cycle_v1" not in bridge:
        raise RuntimeError("BRIDGE_MUST_BIND_PRODUCTIVE_EVIDENCE_ACCUMULATION")
    if "stamp_productive_bridge_cycle_authority_v1" not in bridge:
        raise RuntimeError("BRIDGE_MUST_STAMP_PRODUCTIVE_BRIDGE_AUTHORITY")
    if "project_to_join_ledger=True" not in bridge:
        raise RuntimeError("BRIDGE_MUST_PROJECT_PRODUCTIVE_JOIN_LEDGER")

    cli_path = (
        root
        / "scripts/ops"
        / "run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py"
    )
    cli = cli_path.read_text(encoding="utf-8")
    if "productive-bridge-accumulate" not in cli:
        raise RuntimeError("CLI_MUST_EXPOSE_PRODUCTIVE_BRIDGE_ACCUMULATE_MODE")
    # Productive mode must not call the synthetic probe helper.
    productive_block_start = cli.find('args.mode == "productive-bridge-accumulate"')
    if productive_block_start < 0:
        raise RuntimeError("CLI_PRODUCTIVE_MODE_BLOCK_MISSING")
    productive_block = cli[productive_block_start : productive_block_start + 2500]
    if "_synthetic_probe_cycles_v1" in productive_block:
        raise RuntimeError("PRODUCTIVE_MODE_MUST_NOT_USE_SYNTHETIC_PROBE_CYCLES")

    binding_mod = (package_dir / "productive_bridge_binding_v1.py").read_text(encoding="utf-8")
    if "bind_accumulation_state_to_hardened_bridge_session_v1" not in binding_mod:
        raise RuntimeError("PRODUCTIVE_BRIDGE_BINDING_API_MISSING")

    runner_mod = (package_dir / "productive_bridge_runner_v1.py").read_text(encoding="utf-8")
    if "ProductiveNaturalAgeLifecycleCmcBindingHostV1" not in runner_mod:
        raise RuntimeError("PRODUCTIVE_BRIDGE_MUST_BIND_NATURAL_AGE_LIFECYCLE_HOST")
    if "CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.create" in runner_mod:
        raise RuntimeError("PRODUCTIVE_BRIDGE_MUST_NOT_CREATE_LEGACY_CMC_BINDING_HOST")

    for required_module in (
        "preregistration_v1.py",
        "counterfactual_grid_v1.py",
        "evaluability_v1.py",
        "session_campaign_preregistration_v1.py",
    ):
        if not (package_dir / required_module).is_file():
            raise RuntimeError(f"NUMERIC_PRODUCTIVE_MODULE_MISSING:{required_module}")

    prereg_mod = (package_dir / "preregistration_v1.py").read_text(encoding="utf-8")
    if "RESEARCH_AGE_CANDIDATE_GRID_SECONDS" not in prereg_mod:
        raise RuntimeError("PREREGISTRATION_RESEARCH_GRID_MISSING")
    if "NON_PROMOTION_INVARIANT_V1" not in prereg_mod:
        raise RuntimeError("PREREGISTRATION_NON_PROMOTION_MISSING")
    if "evaluability-report" not in cli:
        raise RuntimeError("CLI_MUST_EXPOSE_EVALUABILITY_REPORT_MODE")
    if "render-session-preregistration" not in cli:
        raise RuntimeError("CLI_MUST_EXPOSE_RENDER_SESSION_PREREGISTRATION_MODE")
    if "verify-session-preregistration" not in cli:
        raise RuntimeError("CLI_MUST_EXPOSE_VERIFY_SESSION_PREREGISTRATION_MODE")
    session_prereg = (package_dir / "session_campaign_preregistration_v1.py").read_text(
        encoding="utf-8"
    )
    if '"network_authorized": False' not in session_prereg:
        raise RuntimeError("SESSION_PREREG_MUST_DECLARE_NETWORK_UNAUTHORIZED")
    if "parent_dirs_materialized_by_preregistration" not in session_prereg:
        raise RuntimeError("SESSION_PREREG_MUST_FORBID_PARENT_DIR_MATERIALIZATION")
    if not COUNTERFACTUAL_ONLY:
        raise RuntimeError("COUNTERFACTUAL_ONLY_REQUIRED")
    if not BLOCKED_FOR_PARAMETER_DECISION:
        raise RuntimeError("PARAMETER_DECISION_MUST_REMAIN_BLOCKED")
    if EVIDENCE_SUFFICIENT_FOR_PARAMETER_DECISION:
        raise RuntimeError("PARAMETER_DECISION_SUFFICIENCY_DRIFT")
    if REVIEW_MODE_ID != NUMERIC_PRODUCTIVE_ACCUMULATION_CAPABILITY_ID:
        raise RuntimeError("REVIEW_MODE_ID_DRIFT")

    return {
        "guards_pass": True,
        "hard_stop": HARD_STOP,
        "no_alpha_mutation_guard_pass": True,
        "no_order_authority_guard_pass": True,
        "no_policy_mutation_guard_pass": True,
        "regime_label_is_research_metadata_only": REGIME_LABEL_IS_RESEARCH_METADATA_ONLY,
        "threshold_status": THRESHOLD_STATUS,
        "review_mode_id": REVIEW_MODE_ID,
        "blocked_for_parameter_decision": BLOCKED_FOR_PARAMETER_DECISION,
        "counterfactual_only": COUNTERFACTUAL_ONLY,
    }
