"""Contract characterization for Paper/Shadow 24/7 preflight v0 (read-only, no runtime)."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
SCHEDULER_DAEMON = REPO_ROOT / "docs" / "SCHEDULER_DAEMON.md"
JOBS_TOML = REPO_ROOT / "config" / "scheduler" / "jobs.toml"


def _read_contract() -> str:
    return CONTRACT.read_text(encoding="utf-8")


def _extract_json_example(markdown: str) -> dict[str, object]:
    match = re.search(r"```json\n(.*?)\n```", markdown, re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))


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


def test_scheduler_daemon_links_to_paper_shadow_247_contract() -> None:
    scheduler_text = SCHEDULER_DAEMON.read_text(encoding="utf-8")
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in scheduler_text


def test_scheduler_config_is_not_a_direct_paper_shadow_247_activation() -> None:
    jobs_text = JOBS_TOML.read_text(encoding="utf-8").lower()

    assert "paper_shadow_247" not in jobs_text
    assert "paper-shadow-247" not in jobs_text
    assert "24/7" not in jobs_text
