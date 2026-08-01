"""Architecture guards: research evidence must not become trading authority."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    ALPHA_DECISION_MUTATION_ALLOWED,
    ENFORCEMENT_APPLIED,
    ENFORCEMENT_DURING_RESEARCH,
    FORBIDDEN_IMPORT_SUBSTRINGS,
    HARD_STOP,
    LIVE_AUTHORIZATION,
    NUMERIC_MAX_AGE_DECIDED,
    NUMERIC_THRESHOLD_SELECTED,
    PARAMETER_PROMOTED,
    READY_FOR_ENFORCEMENT,
    READY_FOR_PARAMETER_PROMOTION,
    READY_FOR_THRESHOLD_SELECTION,
    THRESHOLD_STATUS,
)


def assert_architecture_guards_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    package_dir = (
        root / "src/research/canonical_volatility_numeric_max_age_parameter_research_execution_v1"
    )
    sources: list[str] = []
    import_lines: list[str] = []
    for path in sorted(package_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        sources.append(text)
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                import_lines.append(stripped)
    blob = "\n".join(sources)
    imports_blob = "\n".join(import_lines)

    for token in FORBIDDEN_IMPORT_SUBSTRINGS:
        if token in imports_blob:
            raise RuntimeError(f"TRADING_AUTHORITY_IMPORT_FORBIDDEN:{token}")

    # Scan logic excluding the architecture-guard definition itself.
    code_before_guards = "\n".join(
        p.read_text(encoding="utf-8")
        for p in sorted(package_dir.glob("*.py"))
        if p.name != "architecture_guards_v1.py" and p.name != "constants_v1.py"
    )

    forbidden_true_assignments = (
        "NUMERIC_THRESHOLD_SELECTED = True",
        "PARAMETER_PROMOTED = True",
        "ENFORCEMENT_APPLIED = True",
        "ENFORCEMENT_DURING_RESEARCH = True",
        "ALPHA_DECISION_MUTATION_ALLOWED = True",
        "NUMERIC_MAX_AGE_DECIDED = True",
        "LIVE_AUTHORIZATION = True",
        "READY_FOR_THRESHOLD_SELECTION = True",
        "READY_FOR_PARAMETER_PROMOTION = True",
        "READY_FOR_ENFORCEMENT = True",
    )
    for token in forbidden_true_assignments:
        if token in code_before_guards:
            raise RuntimeError(f"FORBIDDEN_AUTHORITY_FLAG:{token}")

    if "RECOMMENDED_SINGLE_THRESHOLD =" in code_before_guards:
        raise RuntimeError("SINGLE_THRESHOLD_RECOMMENDATION_FORBIDDEN")
    if "demote_trading_gate" in code_before_guards:
        raise RuntimeError("TRADING_GATE_DEMOTION_FORBIDDEN")
    for order_token in ("place_order(", "submit_order("):
        if order_token in code_before_guards:
            raise RuntimeError("ORDER_PATH_FORBIDDEN")
    _ = blob  # retained for full-package presence in future extensions

    if (
        NUMERIC_THRESHOLD_SELECTED
        or PARAMETER_PROMOTED
        or ENFORCEMENT_APPLIED
        or ENFORCEMENT_DURING_RESEARCH
        or ALPHA_DECISION_MUTATION_ALLOWED
        or NUMERIC_MAX_AGE_DECIDED
        or LIVE_AUTHORIZATION
        or READY_FOR_THRESHOLD_SELECTION
        or READY_FOR_PARAMETER_PROMOTION
        or READY_FOR_ENFORCEMENT
    ):
        raise RuntimeError("AUTHORITY_FLAG_DRIFT")
    if THRESHOLD_STATUS != "UNRESOLVED_MAX_AGE":
        raise RuntimeError("THRESHOLD_STATUS_DRIFT")
    if not HARD_STOP:
        raise RuntimeError("HARD_STOP_REQUIRED")

    return {
        "guards_pass": True,
        "threshold_status": THRESHOLD_STATUS,
        "numeric_threshold_selected": NUMERIC_THRESHOLD_SELECTED,
        "parameter_promoted": PARAMETER_PROMOTED,
        "enforcement_applied": ENFORCEMENT_APPLIED,
        "hard_stop": HARD_STOP,
        "trading_authority_imports_absent": True,
    }
