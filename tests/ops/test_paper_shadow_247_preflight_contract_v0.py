"""Contract characterization for Paper/Shadow 24/7 preflight v0 (read-only, no runtime)."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
CHARTER = REPO_ROOT / "docs" / "ops" / "runbooks" / "SHADOW_247_GOVERNANCE_CHARTER_V0.md"
CHARTER_NAME = "SHADOW_247_GOVERNANCE_CHARTER_V0.md"
SCHEDULER_DAEMON = REPO_ROOT / "docs" / "SCHEDULER_DAEMON.md"
JOBS_TOML = REPO_ROOT / "config" / "scheduler" / "jobs.toml"


def _read_contract() -> str:
    return CONTRACT.read_text(encoding="utf-8")


def _extract_json_example(markdown: str) -> dict[str, object]:
    match = re.search(r"```json\n(.*?)\n```", markdown, re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))


def test_paper_shadow_247_contract_links_governance_charter_without_overriding_blocked_v0() -> None:
    text = _read_contract()
    assert CHARTER.is_file()
    assert f"]({CHARTER_NAME})" in text
    assert "Shadow-247 governance charter" in text
    assert "**STOP_IDLE**" in text
    assert "**does not** override this document" in text
    assert "**BLOCKED** status" in text
    assert "governance-only" in text
    assert "runtime approval" in text


def test_paper_shadow_247_contract_links_charter_24h_evidence_semantics_without_changing_blocked_v0() -> (
    None
):
    """Regression anchor for PR #3562 — preflight navigation to charter 24h tier only."""
    text = _read_contract()
    assert CHARTER.is_file()
    assert "24h bounded Shadow dry-run candidate" in text
    assert CHARTER_NAME in text
    assert "Status and scope" in text
    assert "**documentary**" in text
    assert "**non-authorizing**" in text
    assert "**does not** change this contract" in text
    assert "**BLOCKED** status" in text
    assert "assists navigation only" in text


def test_paper_shadow_247_contract_is_blocked_and_non_authorizing() -> None:
    text = _read_contract()

    assert "Current status: **BLOCKED**." in text
    assert "**STOP — do not activate Paper/Shadow 24/7.**" in text
    assert "are **not** trading authority" in text
    assert "must not be interpreted as daemon activation" in text
    assert "does **not** start a daemon" in text


def test_paper_shadow_247_contract_defines_dry_run_only_command() -> None:
    text = _read_contract()

    expected_cmd = (
        "python3 scripts/run_scheduler.py --config config/scheduler/jobs.toml "
        "--dry-run --once --verbose"
    )
    assert expected_cmd in text
    assert "planning and diagnostics" in text
    assert "must not be interpreted as daemon activation" in text


def test_paper_shadow_247_contract_example_report_is_blocked_json() -> None:
    payload = _extract_json_example(_read_contract())

    assert payload["schema_version"] == "paper_shadow_247_preflight_contract.v0"
    assert payload["status"] == "BLOCKED"
    assert payload["canonical_candidate_jobs"] == []
    assert payload["candidate_commands"] == []
    assert payload["output_paths"] == []
    assert payload["stop_commands"] == []
    assert payload["emergency_stop_commands"] == []
    assert payload["activation_authorized"] is False
    rf = payload["risk_flags"]
    assert rf == {
        "live": False,
        "testnet": False,
        "broker": False,
        "exchange": False,
        "orders": False,
    }
    reasons = payload["status_reasons"]
    assert isinstance(reasons, list)
    assert "paper_shadow_247_owner_entrypoint_missing" in reasons
    assert "paper_shadow_247_canonical_job_set_missing" in reasons


def test_paper_shadow_247_contract_includes_post_pr3376_readiness_closeout() -> None:
    text = _read_contract()

    assert "## Post-PR3376 operator readiness closeout v0" in text
    assert "ops-paper-shadow-247-readiness" in text
    assert "#3371" in text and "#3376" in text
    assert "does **not** authorize scheduler execution" in text
    assert "scripts/ops/report_paper_shadow_247_preflight_status.py" in text
    assert "scripts/ops/snapshot_operator_stop_signals.py" in text


def test_scheduler_daemon_links_to_paper_shadow_247_contract() -> None:
    scheduler_text = SCHEDULER_DAEMON.read_text(encoding="utf-8")
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in scheduler_text


def test_scheduler_config_exposes_read_only_paper_shadow_247_preflight_job_only() -> None:
    jobs_text = JOBS_TOML.read_text(encoding="utf-8")

    assert "paper_shadow_247_paper_only_preflight_status_v0" in jobs_text
    assert "report_paper_shadow_247_preflight_status.py" in jobs_text
    assert "paper_only = true" in jobs_text.lower()
    assert "dry_run_visible = true" in jobs_text.lower()

    lowered = jobs_text.lower()
    assert "run_shadow_paper_session" not in lowered
