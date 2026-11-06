"""Contract tests for repeated P7 Shadow one-shot dry-run governance runbook v0."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "P7_SHADOW_REPEATED_ONE_SHOT_DRY_RUN_GOVERNANCE_V0.md"
)
ACCEPTANCE_NAME = "P7_SHADOW_ONE_SHOT_ACCEPTANCE_CONTRACT_V0.md"
PREFLIGHT_NAME = "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"

EXPECTED_SECTION_PREFIXES: tuple[str, ...] = tuple(f"## {i}." for i in range(1, 12))


def _read() -> str:
    return GOVERNANCE.read_text(encoding="utf-8")


def test_p7_shadow_repeated_governance_doc_has_stable_outline_v0() -> None:
    text = _read()
    for heading in EXPECTED_SECTION_PREFIXES:
        assert heading in text, f"missing section heading {heading!r}"


def test_p7_shadow_repeated_governance_doc_links_canonical_runbooks_v0() -> None:
    text = _read()
    assert f"]({ACCEPTANCE_NAME})" in text
    assert f"]({PREFLIGHT_NAME})" in text
    assert ACCEPTANCE_NAME in text
    assert PREFLIGHT_NAME in text


def test_p7_shadow_repeated_governance_doc_states_not_pre_authorized_v0() -> None:
    text = _read()
    assert "manual repeated dry-runs are not pre-authorized" in text
    assert "does **not** authorize scheduling" in text
    assert "daemon activation" in text
    assert "24/7 Paper/Shadow operation" in text


def test_p7_shadow_repeated_governance_doc_forbids_runtime_authorization_payloads_v0() -> None:
    """Guard against accidentally documenting activation as authorized."""
    text = _read()
    assert '"activation_authorized": true' not in text
    assert '"activation_authorized":true' not in text


def test_p7_shadow_repeated_governance_doc_references_p7_ctl_and_preflight_reporter_v0() -> None:
    text = _read()
    assert "scripts/ops/p7_ctl.py" in text
    assert "scripts/ops/report_paper_shadow_247_preflight_status.py" in text


def test_p7_shadow_repeated_governance_doc_lists_fixture_contract_test_v0() -> None:
    text = _read()
    assert "tests/ops/test_p7_shadow_one_shot_acceptance_contract_v0.py" in text


def test_one_shot_acceptance_runbook_links_repeated_governance_v0() -> None:
    acceptance = (
        REPO_ROOT / "docs" / "ops" / "runbooks" / "P7_SHADOW_ONE_SHOT_ACCEPTANCE_CONTRACT_V0.md"
    )
    body = acceptance.read_text(encoding="utf-8")
    assert "P7_SHADOW_REPEATED_ONE_SHOT_DRY_RUN_GOVERNANCE_V0.md" in body
