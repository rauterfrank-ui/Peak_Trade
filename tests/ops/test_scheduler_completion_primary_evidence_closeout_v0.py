"""Contract tests for scheduler completion primary evidence closeout v0."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_SCHEDULER = REPO_ROOT / "scripts" / "run_scheduler.py"
SHARED_HELPER = REPO_ROOT / "scripts" / "ops" / "primary_evidence_retention_v0.py"
PREFLIGHT = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
HARD_GATE_CONTRACT_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_run_primary_evidence_retention_hard_gate_v0.py"
)
INVARIANT_CONTRACT_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_primary_evidence_retention_invariant_contract_v0.py"
)
BOUNDED_REVIEW_CONTRACT_TESTS = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_bounded_observation_review_durable_primary_evidence_contract_v0.py"
)
MANDATORY_CLOSEOUT_WIRING_TOKEN = "DURABLE_PRIMARY_EVIDENCE_MANDATORY_CLOSEOUT_WIRING_V0=true"


def _preflight_section_2a1() -> str:
    return PREFLIGHT.read_text(encoding="utf-8").split("## 2a.1", 1)[1].split("## 2b.", 1)[0]


def _load_run_scheduler():
    spec = importlib.util.spec_from_file_location("run_scheduler", RUN_SCHEDULER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_scheduler"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def rs():
    return _load_run_scheduler()


def test_cli_flags_present_in_parser(rs) -> None:
    text = RUN_SCHEDULER.read_text(encoding="utf-8")
    assert "--evidence-dir" in text
    assert "--primary-evidence-enforce" in text
    assert "scheduler_completion_closeout_v0.json" in text
    assert "finalize_primary_evidence_root" in text
    assert (
        "def verify_manifest_sha256"
        not in text.split("finalize_scheduler_completion_evidence", 1)[0]
    )


def test_validate_enforce_requires_evidence_dir(rs) -> None:
    assert (
        rs.validate_scheduler_evidence_cli(
            evidence_dir=None,
            primary_evidence_enforce=True,
            dry_run=False,
        )
        == 1
    )


def test_validate_enforce_incompatible_with_dry_run(rs) -> None:
    assert (
        rs.validate_scheduler_evidence_cli(
            evidence_dir=Path("/var/tmp/evidence"),
            primary_evidence_enforce=True,
            dry_run=True,
        )
        == 1
    )


def test_main_enforce_without_evidence_dir_fails_before_loop(rs, monkeypatch) -> None:
    loop_calls: list[object] = []
    monkeypatch.setattr(rs, "run_scheduler_loop", lambda **kwargs: loop_calls.append(kwargs) or 0)

    rc = rs.main(["--once", "--config", "config/scheduler/jobs.toml", "--primary-evidence-enforce"])
    assert rc == 1
    assert loop_calls == []


def test_main_enforce_with_dry_run_fails_before_loop(rs, monkeypatch) -> None:
    loop_calls: list[object] = []
    monkeypatch.setattr(rs, "run_scheduler_loop", lambda **kwargs: loop_calls.append(kwargs) or 0)

    rc = rs.main(
        [
            "--dry-run",
            "--once",
            "--config",
            "config/scheduler/jobs.toml",
            "--evidence-dir",
            "/var/tmp/evidence",
            "--primary-evidence-enforce",
        ],
    )
    assert rc == 1
    assert loop_calls == []


def test_main_default_backward_compatible(rs, monkeypatch) -> None:
    loop_calls: list[dict] = []
    monkeypatch.setattr(rs, "assert_scheduler_start_authorized", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        rs,
        "run_scheduler_loop",
        lambda **kwargs: loop_calls.append(kwargs) or 0,
    )

    rc = rs.main(["--once", "--config", "config/scheduler/jobs.toml"])
    assert rc == 0
    assert len(loop_calls) == 1
    assert loop_calls[0].get("evidence_dir") is None
    assert loop_calls[0].get("primary_evidence_enforce") is False


def test_loop_enforce_writes_closeout_and_manifest(rs, monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(rs, "load_jobs_from_toml", lambda _path: [])
    monkeypatch.setattr(rs, "filter_jobs_by_tags", lambda jobs, *_args, **_kwargs: [])

    rc = rs.run_scheduler_loop(
        Path("config/scheduler/jobs.toml"),
        poll_interval=30,
        once=True,
        include_tags=None,
        exclude_tags=None,
        dry_run=False,
        verbose=False,
        use_registry=False,
        notifier=None,
        evidence_dir=tmp_path,
        primary_evidence_enforce=True,
    )
    assert rc == 0
    closeout = tmp_path / "scheduler_completion_closeout_v0.json"
    assert closeout.is_file()
    payload = json.loads(closeout.read_text(encoding="utf-8"))
    assert payload["evidence_non_authorizing"] is True
    assert payload["dry_run"] is False
    assert (tmp_path / "MANIFEST.sha256").is_file()

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

    ok, msg = verify_manifest_sha256(tmp_path)
    assert ok is True, msg


def test_loop_enforce_fails_closed_on_finalize_failure(rs, monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(rs, "load_jobs_from_toml", lambda _path: [])
    monkeypatch.setattr(rs, "filter_jobs_by_tags", lambda jobs, *_args, **_kwargs: [])

    def _fail(_root: Path) -> tuple[bool, str]:
        return False, "checksum mismatch: scheduler_completion_closeout_v0.json"

    monkeypatch.setattr(
        "scripts.ops.primary_evidence_retention_v0.finalize_primary_evidence_root",
        _fail,
    )

    rc = rs.run_scheduler_loop(
        Path("config/scheduler/jobs.toml"),
        poll_interval=30,
        once=True,
        include_tags=None,
        exclude_tags=None,
        dry_run=False,
        verbose=False,
        use_registry=False,
        notifier=None,
        evidence_dir=tmp_path,
        primary_evidence_enforce=True,
    )
    assert rc == 1


def test_dry_run_main_skips_guard_and_does_not_enforce(rs, monkeypatch, tmp_path: Path) -> None:
    guard_calls: list[object] = []

    def _guard(**kwargs):
        guard_calls.append(kwargs)
        raise AssertionError("guard must not run for dry-run")

    monkeypatch.setattr(rs, "assert_scheduler_start_authorized", _guard)
    monkeypatch.setattr(rs, "load_jobs_from_toml", lambda _path: [])
    monkeypatch.setattr(rs, "filter_jobs_by_tags", lambda jobs, *_args, **_kwargs: [])

    rc = rs.main(
        [
            "--dry-run",
            "--once",
            "--config",
            "config/scheduler/jobs.toml",
            "--evidence-dir",
            str(tmp_path),
        ],
    )
    assert rc == 0
    assert guard_calls == []
    assert (tmp_path / "scheduler_completion_closeout_v0.json").is_file()
    assert not (tmp_path / "MANIFEST.sha256").exists()


def test_non_dry_run_blocked_under_hold_still_exits_2(rs, monkeypatch) -> None:
    monkeypatch.setattr(
        rs,
        "assert_scheduler_start_authorized",
        lambda **kwargs: (_ for _ in ()).throw(SystemExit(rs.SCHEDULER_START_BLOCKED_EXIT)),
    )
    monkeypatch.setattr(rs, "run_scheduler_loop", lambda **kwargs: pytest.fail("loop must not run"))

    with pytest.raises(SystemExit) as exc:
        rs.main(
            [
                "--once",
                "--config",
                "config/scheduler/jobs.toml",
                "--evidence-dir",
                "/var/tmp/evidence",
                "--primary-evidence-enforce",
            ],
        )
    assert exc.value.code == rs.SCHEDULER_START_BLOCKED_EXIT


def test_preflight_documents_scheduler_completion_opt_in() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "scheduler_completion_closeout_v0" in text or "run_scheduler.py" in text
    assert "primary-evidence-enforce" in text or "primary_evidence_enforce" in text


def test_scheduler_completion_owner_locates_mandatory_closeout_wiring_token_in_preflight_2a1() -> (
    None
):
    section = _preflight_section_2a1()
    collapsed = section.replace("**", "").lower()
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in section
    assert "run_scheduler.py" in section or "scheduler" in collapsed
    assert "primary-evidence-enforce" in section or "primary_evidence_enforce" in section
    assert "default off" in collapsed or "opt-in" in collapsed


def test_scheduler_completion_owner_crosslinks_hard_gate_contract_module() -> None:
    owner_text = Path(__file__).read_text(encoding="utf-8")
    hard_gate_text = HARD_GATE_CONTRACT_TESTS.read_text(encoding="utf-8")
    assert HARD_GATE_CONTRACT_TESTS.name in owner_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in hard_gate_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in _preflight_section_2a1()
    assert "finalize_primary_evidence_root" in hard_gate_text


def test_scheduler_completion_owner_crosslinks_invariant_and_bounded_review_contract_modules() -> (
    None
):
    owner_text = Path(__file__).read_text(encoding="utf-8")
    invariant_text = INVARIANT_CONTRACT_TESTS.read_text(encoding="utf-8")
    bounded_text = BOUNDED_REVIEW_CONTRACT_TESTS.read_text(encoding="utf-8")
    assert INVARIANT_CONTRACT_TESTS.name in owner_text
    assert BOUNDED_REVIEW_CONTRACT_TESTS.name in owner_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in invariant_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in bounded_text
    assert (
        "scheduler_completion_closeout_v0" in invariant_text or "run_scheduler.py" in invariant_text
    )


def test_scheduler_completion_owner_preserves_non_authorizing_evidence_boundary() -> None:
    scheduler_text = RUN_SCHEDULER.read_text(encoding="utf-8")
    section = _preflight_section_2a1().replace("**", "").lower()
    assert "evidence_non_authorizing" in scheduler_text
    assert "non-authorizing" in section or "does not authorize runtime" in section
    assert "does not clear preflight blocked" in section or "preflight blocked" in section
    assert "finalize_primary_evidence_root" in SHARED_HELPER.read_text(encoding="utf-8")


def test_scheduler_completion_owner_confirms_no_scheduler_start_from_closeout_contract() -> None:
    scheduler_text = RUN_SCHEDULER.read_text(encoding="utf-8")
    owner_text = Path(__file__).read_text(encoding="utf-8").lower()
    preflight_text = PREFLIGHT.read_text(encoding="utf-8").lower()
    assert "assert_scheduler_start_authorized" in scheduler_text
    assert "SCHEDULER_START_BLOCKED_EXIT" in scheduler_text
    assert "test_non_dry_run_blocked_under_hold_still_exits_2" in owner_text
    assert (
        "start boundary guard unchanged" in preflight_text or "scheduler boundary" in preflight_text
    )
