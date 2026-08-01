"""Architecture guards: accumulation must not become trading authority."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    ALPHA_MUTATION_OCCURRED,
    CONFIG_MUTATION_OCCURRED,
    ENFORCEMENT_APPLIED,
    FORBIDDEN_IMPORT_SUBSTRINGS,
    HARD_STOP,
    LIVE_AUTHORIZATION,
    LIVE_TESTNET_ORDER_ACTIVATION_OCCURRED,
    NUMERIC_MAX_AGE_DECIDED,
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

    return {
        "guards_pass": True,
        "hard_stop": HARD_STOP,
        "no_alpha_mutation_guard_pass": True,
        "no_order_authority_guard_pass": True,
        "no_policy_mutation_guard_pass": True,
        "regime_label_is_research_metadata_only": REGIME_LABEL_IS_RESEARCH_METADATA_ONLY,
        "threshold_status": THRESHOLD_STATUS,
    }
