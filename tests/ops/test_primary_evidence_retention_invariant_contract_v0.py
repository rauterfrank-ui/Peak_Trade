"""Static contract tests for primary evidence retention invariant v0 (offline, no runtime)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_OWNER = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
)
PAPER_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_paper_only_bounded_observation_adapter_v0.py"
SHADOW_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_shadow_bounded_observation_adapter_v0.py"
TESTNET_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py"
SHARED_HELPER = REPO_ROOT / "scripts" / "ops" / "primary_evidence_retention_v0.py"
P79_SHELL = REPO_ROOT / "scripts" / "ops" / "p79_supervisor_health_gate_v1.sh"
P79_VERIFY = REPO_ROOT / "scripts" / "ops" / "p79_supervisor_evidence_manifest_verify_v0.py"
P101_SCRIPT = REPO_ROOT / "scripts" / "ops" / "p101_stop_playbook_v1.sh"
PACK_SCRIPT = REPO_ROOT / "scripts" / "ops" / "pack_online_readiness_supervisor_evidence_v0.py"


def _owner_text() -> str:
    return CANONICAL_OWNER.read_text(encoding="utf-8")


def _adapter_text() -> str:
    return PAPER_ADAPTER.read_text(encoding="utf-8")


def _p101_text() -> str:
    return P101_SCRIPT.read_text(encoding="utf-8")


def test_canonical_owner_exists() -> None:
    assert CANONICAL_OWNER.is_file()


def test_canonical_owner_declares_primary_evidence_required_for_every_run() -> None:
    text = _owner_text()
    assert "PRIMARY_EVIDENCE_REQUIRED_FOR_EVERY_RUN=true" in text
    assert "## 2a. Primary evidence retention invariant v0" in text


def test_canonical_owner_applies_to_all_run_types() -> None:
    text = _owner_text()
    for run_type in (
        "Paper",
        "Shadow",
        "Testnet",
        "Live/Canary",
        "Scheduler",
        "Supervisor",
        "Daemon",
        "Smoke",
        "bounded trial",
        "runtime adapter",
    ):
        assert run_type in text


def test_canonical_owner_requires_durable_archive_outside_tmp() -> None:
    text = _owner_text()
    assert "durable archive outside `/tmp`" in text
    assert "archive verification passes" in text


def test_canonical_owner_requires_manifest_and_sha256_verification() -> None:
    text = _owner_text()
    assert "MANIFEST.sha256" in text
    assert "shasum -a 256 -c" in text
    assert "RC=0" in text


def test_canonical_owner_requires_closeout_and_postrun_review() -> None:
    text = _owner_text()
    assert "closeout present" in text
    assert "postrun/review present" in text
    assert "REVIEW_RESULT.json" in text


def test_canonical_owner_rejects_non_primary_evidence_sources() -> None:
    text = _owner_text()
    forbidden = (
        "/tmp`-only artifacts",
        "transcript-only evidence",
        "Notion pointer-only evidence",
        "chat-summary-only evidence",
        "unverified archive copies",
    )
    for phrase in forbidden:
        assert phrase in text


def test_canonical_owner_forbids_gate_clearance_from_documentary_only() -> None:
    text = _owner_text()
    assert "No gate clearance" in text
    assert "degraded or documentary evidence alone" in text


def test_canonical_owner_no_automatic_24h_72h_rerun_after_paper120() -> None:
    text = _owner_text()
    assert "automatic **24h** or **72h** rerun requirement" in text
    assert "Paper120" in text


def test_canonical_owner_run_not_complete_until_archive_verification() -> None:
    text = _owner_text()
    assert "A run is **not complete** until **archive verification passes**" in text


def test_paper_adapter_plan_only_default_and_execute_gated() -> None:
    text = _adapter_text()
    assert "plan-only default" in text
    assert "--plan-only" in text or '"plan-only"' in text
    assert "--execute" in text
    assert "requires --approval-record" in text or "execute requires --approval-record" in text


def test_paper_adapter_archive_root_must_be_outside_tmp() -> None:
    text = _adapter_text()
    assert "archive root must be outside /tmp" in text


def test_canonical_owner_references_paper_adapter_implementation() -> None:
    text = _owner_text()
    assert "run_paper_only_bounded_observation_adapter_v0.py" in text
    assert "primary_evidence_retention_v0.py" in text
    assert "plan-only default" in text
    assert "archive root outside `/tmp`" in text


def test_shared_helper_module_exists() -> None:
    assert SHARED_HELPER.is_file()
    text = SHARED_HELPER.read_text(encoding="utf-8")
    assert "def write_manifest_sha256" in text
    assert "def verify_manifest_sha256" in text
    assert "def finalize_primary_evidence_root" in text


def test_canonical_owner_references_scheduler_completion_opt_in() -> None:
    text = _owner_text()
    assert "run_scheduler.py" in text
    assert "primary-evidence-enforce" in text or "primary_evidence_enforce" in text
    assert "scheduler_completion_closeout_v0" in text


def test_canonical_owner_references_supervisor_pack_closeout() -> None:
    text = _owner_text()
    assert "pack_online_readiness_supervisor_evidence_v0.py" in text
    assert "supervisor_session_closeout_v0" in text


def test_canonical_owner_references_p79_archive_manifest_gate() -> None:
    text = _owner_text()
    assert "p79_supervisor_health_gate_v1.sh" in text
    assert "ARCHIVE_ROOT" in text
    assert "verify_manifest_sha256" in text
    assert "supervisor_session_closeout_v0" in text
    assert "MANIFEST.sha256" in text
    assert "non-authorizing" in text
    assert "does not start/stop supervisor" in text


def test_canonical_owner_references_p101_post_stop_operator_hints() -> None:
    text = _owner_text()
    assert "p101_stop_playbook_v1.sh" in text
    assert "P101_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS" in text
    assert "pack_online_readiness_supervisor_evidence_v0.py" in text
    assert "ARCHIVE_ROOT" in text
    assert "does not execute pack" in text.lower()
    assert "operator must" in text.lower()
    assert "non-authorizing" in text
    assert "Online-daemon automatic pack remains unimplemented" in text


def test_p79_archive_root_mode_in_health_gate_shell() -> None:
    assert P79_SHELL.is_file()
    text = P79_SHELL.read_text(encoding="utf-8")
    assert "ARCHIVE_ROOT" in text
    assert "mutually exclusive" in text
    assert "p79_supervisor_evidence_manifest_verify_v0.py" in text
    assert "evidence_non_authorizing" in text


def test_p79_verifier_reuses_shared_manifest_helper() -> None:
    assert P79_VERIFY.is_file()
    text = P79_VERIFY.read_text(encoding="utf-8")
    assert "verify_manifest_sha256" in text
    assert "primary_evidence_retention_v0" in text
    assert "def verify_manifest_sha256" not in text
    assert "subprocess" not in text
    assert "launchctl " not in text


def test_p79_verifier_checks_closeout_and_manifest_non_authorizing() -> None:
    text = P79_VERIFY.read_text(encoding="utf-8")
    assert "CLOSEOUT_FILENAME" in text or "supervisor_session_closeout_v0" in text
    assert "MANIFEST_FILENAME" in text or "MANIFEST.sha256" in text
    assert "evidence_non_authorizing" in text
    assert "LIVE_ALLOWED" not in text
    assert "BROKER_EXCHANGE_ALLOWED" not in text


def test_p101_stop_playbook_post_stop_hint_references_wrapper_and_optional_p79() -> None:
    assert P101_SCRIPT.is_file()
    text = _p101_text()
    assert "run_online_readiness_post_stop_pack_v0.sh" in text
    assert "--p79-archive-verify" in text
    assert "P101_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS.txt" in text
    assert "--primary-evidence-enforce" in text


def test_p101_stop_playbook_post_stop_hint_markers_non_authorizing() -> None:
    text = _p101_text()
    for marker in (
        "HINT_ONLY=true",
        "WRAPPER_REFERENCED=true",
        "WRAPPER_NOT_EXECUTED_BY_P101=true",
        "PACK_NOT_EXECUTED_BY_P101=true",
        "P79_ARCHIVE_VERIFY_NOT_EXECUTED_BY_P101=true",
        "OPERATOR_MUST_RUN_EXPLICITLY=true",
        "EVIDENCE_NON_AUTHORIZING=true",
    ):
        assert marker in text


def test_p101_stop_playbook_does_not_auto_execute_wrapper_pack_or_p79_archive_verify() -> None:
    lines = _p101_text().splitlines()
    wrapper_offenders = [
        line
        for line in lines
        if "run_online_readiness_post_stop_pack_v0.sh" in line
        and not line.strip().startswith("#")
        and not line.strip().startswith("echo")
    ]
    assert wrapper_offenders == []
    pack_offenders = [
        line
        for line in lines
        if "pack_online_readiness_supervisor_evidence_v0.py" in line
        and not line.strip().startswith("#")
        and not line.strip().startswith("echo")
    ]
    assert pack_offenders == []
    p79_offenders = [
        line
        for line in lines
        if "p79_supervisor_health_gate_v1.sh" in line
        and "ARCHIVE_ROOT" in line
        and not line.strip().startswith("echo")
    ]
    assert p79_offenders == []


def test_p101_stop_playbook_no_new_launchctl_or_supervisor_start() -> None:
    text = _p101_text()
    assert "launchctl bootstrap" not in text
    assert "launchctl kickstart" not in text
    assert "online_readiness_supervisor_v1.sh start" not in text
    assert "online_readiness_daemon_v1.sh" not in text


def test_canonical_owner_references_p67_p72_opt_in_enforce() -> None:
    text = _owner_text()
    assert "primary_evidence_enforce=True" in text
    assert "finalize_primary_evidence_root" in text


def test_bounded_adapters_import_shared_helper_not_duplicate_verify() -> None:
    for path in (PAPER_ADAPTER, SHADOW_ADAPTER, TESTNET_ADAPTER):
        text = path.read_text(encoding="utf-8")
        assert "primary_evidence_retention_v0" in text
        assert "def verify_manifest_sha256" not in text


def test_paper_adapter_verifies_manifest_after_archive_copy() -> None:
    text = PAPER_ADAPTER.read_text(encoding="utf-8")
    execute = text.split("def execute_plan", 1)[1].split("\ndef build_arg_parser", 1)[0]
    assert "verify_manifest_sha256(archive_dest)" in execute
    assert execute.index("verify_manifest_sha256(archive_dest)") > execute.rindex("shutil.copy")
    assert "MANIFEST_VERIFY_RC=0" in execute


def test_verify_manifest_sha256_fails_closed_on_missing(tmp_path) -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

    ok, reason = verify_manifest_sha256(tmp_path)
    assert ok is False
    assert reason == "MANIFEST.sha256 missing"


def test_verify_manifest_sha256_detects_checksum_mismatch(tmp_path) -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import (
        verify_manifest_sha256,
        write_manifest_sha256,
    )

    data = tmp_path / "data.txt"
    data.write_text("hello", encoding="utf-8")
    write_manifest_sha256(tmp_path)
    data.write_text("tampered", encoding="utf-8")
    ok, reason = verify_manifest_sha256(tmp_path)
    assert ok is False
    assert "checksum mismatch" in reason


def test_write_and_verify_manifest_roundtrip(tmp_path) -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import (
        verify_manifest_sha256,
        write_manifest_sha256,
    )

    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    write_manifest_sha256(tmp_path)
    ok, reason = verify_manifest_sha256(tmp_path)
    assert ok is True, reason
