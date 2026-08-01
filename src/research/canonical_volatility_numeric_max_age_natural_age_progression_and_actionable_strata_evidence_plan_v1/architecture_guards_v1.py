"""Architecture guards for natural age progression evidence plan capability."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.constants_v1 import (
    ALPHA_MUTATION,
    BLOCKED_FOR_PARAMETER_DECISION,
    BULL_BEAR_LOGIC_CHANGED,
    DOUBLE_PLAY_LOGIC_CHANGED,
    ENFORCEMENT_APPLIED,
    FORBIDDEN_IMPORT_SUBSTRINGS,
    HARD_STOP,
    LIVE_AUTHORIZATION,
    MASTER_V2_LOGIC_CHANGED,
    NO_POLICY_ENFORCEMENT,
    NUMERIC_MAX_AGE_ENFORCING,
    NUMERIC_MAX_AGE_SELECTED,
    READY_FOR_NUMERIC_MAX_AGE_POLICY_DECISION,
    READY_FOR_PRODUCTIVE_SESSION_EXECUTION,
    REVIEW_MODE_ID,
    STATE_MUTATION,
    THRESHOLD_SELECTED,
)


def assert_architecture_guards_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    package_dir = root / (
        "src/research/canonical_volatility_numeric_max_age_natural_age_progression_"
        "and_actionable_strata_evidence_plan_v1"
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
        if token in imports_blob or token in code_blob:
            raise RuntimeError(f"TRADING_AUTHORITY_IMPORT_FORBIDDEN:{token}")

    forbidden_true = (
        "NUMERIC_MAX_AGE_SELECTED = True",
        "NUMERIC_MAX_AGE_ENFORCING = True",
        "ENFORCEMENT_APPLIED = True",
        "THRESHOLD_SELECTED = True",
        "ALPHA_MUTATION = True",
        "STATE_MUTATION = True",
        "LIVE_AUTHORIZATION = True",
        "MASTER_V2_LOGIC_CHANGED = True",
        "DOUBLE_PLAY_LOGIC_CHANGED = True",
        "BULL_BEAR_LOGIC_CHANGED = True",
        "READY_FOR_PRODUCTIVE_SESSION_EXECUTION = True",
        "READY_FOR_NUMERIC_MAX_AGE_POLICY_DECISION = True",
        "NO_POLICY_ENFORCEMENT = False",
    )
    for token in forbidden_true:
        if token in code_blob:
            raise RuntimeError(f"FORBIDDEN_AUTHORITY_FLAG:{token}")

    if "time.sleep" in code_blob or "asyncio.sleep" in code_blob:
        raise RuntimeError("SLEEP_BASED_AGE_SYNTHESIS_FORBIDDEN")
    if "demote_trading_gate" in code_blob:
        raise RuntimeError("TRADING_GATE_DEMOTION_FORBIDDEN")

    if (
        NUMERIC_MAX_AGE_SELECTED
        or NUMERIC_MAX_AGE_ENFORCING
        or ENFORCEMENT_APPLIED
        or THRESHOLD_SELECTED
        or ALPHA_MUTATION
        or STATE_MUTATION
        or LIVE_AUTHORIZATION
        or MASTER_V2_LOGIC_CHANGED
        or DOUBLE_PLAY_LOGIC_CHANGED
        or BULL_BEAR_LOGIC_CHANGED
        or READY_FOR_PRODUCTIVE_SESSION_EXECUTION
        or READY_FOR_NUMERIC_MAX_AGE_POLICY_DECISION
        or not NO_POLICY_ENFORCEMENT
        or not HARD_STOP
        or not BLOCKED_FOR_PARAMETER_DECISION
    ):
        raise RuntimeError("CAPABILITY_GUARD_DRIFT")

    from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.productive_natural_age_lifecycle_binding_v1 import (
        assert_natural_age_lifecycle_productive_binding_guards_v1,
    )

    productive_binding = assert_natural_age_lifecycle_productive_binding_guards_v1(repo_root=root)

    return {
        "review_mode": REVIEW_MODE_ID,
        "guards_pass": True,
        "numeric_max_age_selected": NUMERIC_MAX_AGE_SELECTED,
        "numeric_max_age_enforcing": NUMERIC_MAX_AGE_ENFORCING,
        "enforcement_applied": ENFORCEMENT_APPLIED,
        "hard_stop": HARD_STOP,
        "blocked_for_parameter_decision": BLOCKED_FOR_PARAMETER_DECISION,
        "ready_for_productive_session_execution": READY_FOR_PRODUCTIVE_SESSION_EXECUTION,
        "ready_for_numeric_max_age_policy_decision": READY_FOR_NUMERIC_MAX_AGE_POLICY_DECISION,
        "NATURAL_AGE_LIFECYCLE_HOST_PRODUCTIVE_BOUND": productive_binding[
            "NATURAL_AGE_LIFECYCLE_HOST_PRODUCTIVE_BOUND"
        ],
        "LEGACY_PER_SAMPLE_REMATERIALIZATION_UNREACHABLE": productive_binding[
            "LEGACY_PER_SAMPLE_REMATERIALIZATION_UNREACHABLE"
        ],
        "SECOND_AGE_AUTHORITY_PRESENT": productive_binding["SECOND_AGE_AUTHORITY_PRESENT"],
        "SECOND_DECISION_AUTHORITY_PRESENT": productive_binding[
            "SECOND_DECISION_AUTHORITY_PRESENT"
        ],
        "MASTER_V2_LOGIC_CHANGED": MASTER_V2_LOGIC_CHANGED,
        "DOUBLE_PLAY_LOGIC_CHANGED": DOUBLE_PLAY_LOGIC_CHANGED,
    }
