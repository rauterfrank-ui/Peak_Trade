"""Registry contract for STEP 29M macd v1 real economic evaluation v2 reevaluation."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
V2_EVIDENCE_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "implementation/step29m_macd_v1_real_admissible_futures_economic_reevaluation_v2_20260701T212345Z"
)
INVALIDATED_EVIDENCE_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "implementation/step29m_macd_v1_real_admissible_futures_economic_evaluation_v1_20260701T161757Z"
)


def _read_registry() -> str:
    assert PROGRESS_REGISTRY.is_file()
    return PROGRESS_REGISTRY.read_text(encoding="utf-8")


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _step_29m_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29M — Economic Viability Evidence v1")
    end = text.index("#### RUNBOOK_STEP_29N — Promotion Economic Gate Binding v1", start)
    return text[start:end]


def test_macd_v1_real_evaluation_registry_truth_v2_complete() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    for scope in (text, section):
        assert _field_value(scope, "REAL_EVALUATION_PERFORMED") == "true"
        assert _field_value(scope, "REAL_ADMISSIBLE_FUTURES_EVIDENCE_BOUND") == "true"
        assert _field_value(scope, "ECONOMIC_VALIDITY_RESULT") == "FAILED"
        assert _field_value(scope, "PROFITABILITY_CLAIM_ALLOWED") == "false"
        assert (
            _field_value(scope, "REAL_EVALUATION_INPUT_STATUS")
            == "MACD_V1_EVALUATION_V2_INVALIDATED_SIZING_ADMISSIBILITY_DEFECT"
        )
        assert _field_value(scope, "LAST_EVALUATED_STRATEGY_ID") == "macd"
        assert _field_value(scope, "LAST_EVALUATED_STRATEGY_VERSION") == "v1"
        assert _field_value(scope, "LAST_EVALUATED_CONFIG_VERSION") == "v2"


def test_macd_v1_real_evaluation_evidence_ref_bound() -> None:
    section = _step_29m_section(_read_registry())
    assert str(V2_EVIDENCE_DIR) in _field_value(section, "MACD_V1_REAL_EVALUATION_EVIDENCE_REF")
    assert str(INVALIDATED_EVIDENCE_DIR) in _field_value(section, "INVALIDATED_EVALUATION_REF")
    assert str(V2_EVIDENCE_DIR) in _field_value(section, "INVALIDATED_V2_EVALUATION_REF")


def test_macd_v1_real_evaluation_evidence_manifest_immutable() -> None:
    if not V2_EVIDENCE_DIR.is_dir():
        return
    summary = json.loads(
        (V2_EVIDENCE_DIR / "EVALUATION_RUN_SUMMARY.json").read_text(encoding="utf-8")
    )
    assert summary["REAL_EVALUATION_PERFORMED"] is True
    assert summary["ECONOMIC_VALIDITY_RESULT"] == "FAIL"
    assert summary["PROFITABILITY_CLAIM_ALLOWED"] is False
    assert summary["MANIFEST_VERIFY_RC"] == 0
    assert summary["LAST_EVALUATED_CONFIG_VERSION"] == "v2"
