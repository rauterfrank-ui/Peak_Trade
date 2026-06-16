"""Tests for bounded_daemon_paper_shadow_24h_approval_v0 contract validator."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ops import bounded_daemon_paper_shadow_24h_approval_v0 as contract

ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "ops" / "daemon_paper_shadow_24h_adapter_approval_sample.md"
RUN_ID = "daemon_paper_24h_20260524T093549Z"


def test_fixture_exists() -> None:
    assert FIXTURE.is_file()


def test_sample_fixture_passes_validation() -> None:
    fields = contract.parse_machine_lines(FIXTURE.read_text(encoding="utf-8"))
    issues = contract.validate_approval_record(fields, approved_run_id=RUN_ID)
    assert issues == []


def test_run_id_mismatch_fails() -> None:
    fields = contract.parse_machine_lines(FIXTURE.read_text(encoding="utf-8"))
    issues = contract.validate_approval_record(fields, approved_run_id="other_run_id")
    assert any("APPROVED_RUN_ID mismatch" in issue for issue in issues)


def test_120min_keys_alone_do_not_satisfy_24h_contract() -> None:
    fields = {
        "APPROVE_EXECUTE_PAPER_ONLY_120MIN_NOW": "true",
        "START_PAPER_NOW": "true",
    }
    issues = contract.validate_approval_record(fields, approved_run_id=RUN_ID)
    assert issues


def test_forbidden_testnet_flag_fails() -> None:
    text = FIXTURE.read_text(encoding="utf-8").replace(
        "START_TESTNET_NOW=false", "START_TESTNET_NOW=true"
    )
    fields = contract.parse_machine_lines(text)
    issues = contract.validate_approval_record(fields, approved_run_id=RUN_ID)
    assert any("START_TESTNET_NOW" in issue for issue in issues)


def test_paper_duration_must_be_86400() -> None:
    assert contract.validate_paper_duration_seconds(86400) == []
    assert contract.validate_paper_duration_seconds(7200)


def test_shadow_duration_must_be_1440() -> None:
    assert contract.validate_shadow_duration_minutes(1440) == []
    assert contract.validate_shadow_duration_minutes(10)


@pytest.mark.parametrize(
    "key",
    [
        "APPROVE_EXECUTE_BOUNDED_24H_DAEMON_PAPER_SHADOW_DRY_RUN_NOW",
        "PAPER_LANE_AUTHORIZED",
        "SHADOW_LANE_AUTHORIZED",
    ],
)
def test_missing_required_key_fails(key: str) -> None:
    fields = contract.parse_machine_lines(FIXTURE.read_text(encoding="utf-8"))
    fields.pop(key, None)
    issues = contract.validate_approval_record(fields, approved_run_id=RUN_ID)
    assert any(key in issue for issue in issues)
