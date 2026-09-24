"""Architecture guards for retained-estimate late-age carrier (research evidence only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1.constants_v1 import (
    BACKDATING_ALLOWED,
    HISTORICAL_EVIDENCE_MUTATION_ALLOWED,
    M9_ENFORCEMENT_ACTIVATED,
    MARK_HISTORY_SCHEMA_MUTATED,
    MV2_DOUBLE_PLAY_AUTHORITY_CHANGED,
    PACKAGE_MARKER,
    PRODUCTION_AUTHORITY_EFFECT,
    REGIME_PIPELINE_MUTATED,
    SPEC_REL_PATH,
    SYNTHETIC_AGING_ALLOWED,
    TRADING_SELECTION_SIZING_SAFETY_EXECUTION_AUTHORITY,
)


def assert_retained_estimate_late_age_architecture_guards_v1(
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    package_dir = root / (
        "src/research/canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1"
    )
    texts: list[str] = []
    for path in sorted(package_dir.glob("*.py")):
        if path.name == "architecture_guards_v1.py":
            continue
        texts.append(path.read_text(encoding="utf-8"))
    blob = "\n".join(texts)
    if "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_RETAINED_ESTIMATE" not in blob:
        raise RuntimeError("package_marker_missing")
    if "LATE_AGE_CARRIER_V1" not in blob:
        raise RuntimeError("package_marker_missing")
    if PRODUCTION_AUTHORITY_EFFECT != "NONE":
        raise RuntimeError("PRODUCTION_AUTHORITY_EFFECT_DRIFT")
    if MV2_DOUBLE_PLAY_AUTHORITY_CHANGED:
        raise RuntimeError("MV2_DOUBLE_PLAY_AUTHORITY_CHANGED")
    if TRADING_SELECTION_SIZING_SAFETY_EXECUTION_AUTHORITY:
        raise RuntimeError("TRADING_AUTHORITY_FLAG_TRUE")
    if M9_ENFORCEMENT_ACTIVATED:
        raise RuntimeError("M9_ENFORCEMENT_ACTIVATED")
    if REGIME_PIPELINE_MUTATED:
        raise RuntimeError("REGIME_PIPELINE_MUTATED")
    if MARK_HISTORY_SCHEMA_MUTATED:
        raise RuntimeError("MARK_HISTORY_SCHEMA_MUTATED")
    if SYNTHETIC_AGING_ALLOWED or BACKDATING_ALLOWED:
        raise RuntimeError("SYNTHETIC_OR_BACKDATING_ALLOWED")
    if HISTORICAL_EVIDENCE_MUTATION_ALLOWED:
        raise RuntimeError("HISTORICAL_EVIDENCE_MUTATION_ALLOWED")
    for forbidden in (
        "LIVE_AUTHORIZED = True",
        "ORDERS_ALLOWED = True",
        "TESTNET_AUTHORIZED = True",
        "demote_trading_gate",
        "time.sleep",
        "asyncio.sleep",
    ):
        if forbidden in blob:
            raise RuntimeError(f"FORBIDDEN_TOKEN:{forbidden}")
    spec = root / SPEC_REL_PATH
    if not spec.is_file():
        raise RuntimeError("spec_missing")
    return {
        "PRODUCTION_AUTHORITY_EFFECT": PRODUCTION_AUTHORITY_EFFECT,
        "MV2_DOUBLE_PLAY_AUTHORITY_CHANGED": False,
        "TRADING_SELECTION_SIZING_SAFETY_EXECUTION_AUTHORITY": False,
        "M9_ENFORCEMENT_ACTIVATED": False,
        "REGIME_PIPELINE_MUTATED": False,
        "MARK_HISTORY_SCHEMA_MUTATED": False,
        "SYNTHETIC_AGING_ALLOWED": False,
        "BACKDATING_ALLOWED": False,
        "HISTORICAL_EVIDENCE_MUTATION_ALLOWED": False,
        "guards_pass": True,
    }
