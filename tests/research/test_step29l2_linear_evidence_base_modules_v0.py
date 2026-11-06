from src.research.linear_evidence.diagnostics import (
    AUTHORITY_EFFECT as DIAG_AUTHORITY_EFFECT,
    RUNTIME_EFFECT as DIAG_RUNTIME_EFFECT,
    attach_authority_neutral_fields,
    compute_residual_diagnostics,
)
from src.research.linear_evidence.report import normalize_linear_evidence_report


def test_linear_evidence_base_modules_are_authority_neutral():
    payload = attach_authority_neutral_fields({"status": "DIAGNOSTIC_ONLY"})
    assert payload["authority_effect"] == "NONE"
    assert payload["runtime_effect"] == "NONE"
    assert DIAG_AUTHORITY_EFFECT == "NONE"
    assert DIAG_RUNTIME_EFFECT == "NONE"


def test_residual_diagnostics_are_deterministic_and_authority_neutral():
    result = compute_residual_diagnostics([1.0, -1.0, 2.0])
    assert result.n_samples == 3
    assert result.mae == 4.0 / 3.0
    assert result.max_abs_error == 2.0
    assert result.authority_effect == "NONE"
    assert result.runtime_effect == "NONE"


def test_report_normalization_injects_required_effect_tokens():
    report = normalize_linear_evidence_report({"evidence_type": "cost_model"})
    assert report["authority_effect"] == "NONE"
    assert report["runtime_effect"] == "NONE"
    assert report["cost_policy_output"] == "diagnostic_only"
