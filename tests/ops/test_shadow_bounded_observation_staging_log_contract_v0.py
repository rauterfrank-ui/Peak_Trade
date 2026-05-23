"""Static contract tests for Shadow bounded observation staging log paths (v0).

Verankert die Staging-Log-Pfade für detached/manuelle Shadow-Starts an der Governance-Charter-
Sektion und am Review-Enforcer — ohne Laufzeit, ohne Adapter-Execute, ohne Gate-Freigabe.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHARTER = REPO_ROOT / "docs" / "ops" / "runbooks" / "SHADOW_247_GOVERNANCE_CHARTER_V0.md"
REVIEW_SCRIPT = REPO_ROOT / "scripts" / "ops" / "review_shadow_bounded_observation_evidence_v0.py"
ADAPTER_SCRIPT = REPO_ROOT / "scripts" / "ops" / "run_shadow_bounded_observation_adapter_v0.py"

STAGING_LOG_SECTION_HEADING = (
    "## Detached / manual bounded Shadow launch — staging log contract (v0)"
)
# Docs token policy: illustrative paths in charter use &#47; encoding.
STAGING_STDOUT_CHARTER = "logs&#47;wrapper_stdout.log"
STAGING_STDERR_CHARTER = "logs&#47;wrapper_stderr.log"
STAGING_STDOUT_LITERAL = "logs/wrapper_stdout.log"
STAGING_STDERR_LITERAL = "logs/wrapper_stderr.log"
CONTRACT_TOKEN = "SHADOW_BOUNDED_STAGING_LOG_CONTRACT_V0=true"


def _staging_log_section() -> str:
    text = CHARTER.read_text(encoding="utf-8")
    start = text.index(STAGING_LOG_SECTION_HEADING)
    end = text.index("## Activation ladder", start)
    return text[start:end]


def test_staging_log_contract_section_exists_in_governance_charter_v0() -> None:
    section = _staging_log_section()
    assert STAGING_STDOUT_CHARTER in section
    assert STAGING_STDERR_CHARTER in section
    assert "{staging_root}&#47;logs&#47;wrapper_stdout.log" in section
    assert "detached&#47;" in section
    assert "staging&#47;logs&#47;" in section
    assert "review_shadow_bounded_observation_evidence_v0.py" in section
    assert "run_shadow_bounded_observation_adapter_v0.py" in section
    assert CONTRACT_TOKEN in section
    assert "**Non-authorizing:**" in section


def test_staging_log_contract_forbids_weakening_review_enforcer_v0() -> None:
    section = _staging_log_section()
    collapsed = section.replace("**", "")
    assert "hard-fails" in section
    assert "do not weaken review" in collapsed


def test_review_enforcer_references_wrapper_staging_log_paths_v0() -> None:
    text = REVIEW_SCRIPT.read_text(encoding="utf-8")
    assert "wrapper_stdout.log" in text
    assert "wrapper_stderr.log" in text
    assert "missing logs/wrapper_stdout.log" in text
    assert "missing logs/wrapper_stderr.log" in text


def test_adapter_expected_artifacts_include_staging_log_paths_v0() -> None:
    text = ADAPTER_SCRIPT.read_text(encoding="utf-8")
    assert STAGING_STDOUT_LITERAL in text
    assert STAGING_STDERR_LITERAL in text
    assert "expected_artifacts" in text
