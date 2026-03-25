from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/ops/update_officer_summary.py"


def test_cli_help_mentions_webui_trace_semantics():
    import importlib.util

    spec = importlib.util.spec_from_file_location("uo_summary_cli", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    p = mod.build_parser()
    assert "WebUI" in p.description
    assert "explicit" in p.description.lower()


def _qe(
    rank: int,
    topic_id: str,
    worst_priority: str,
    finding_count: int,
    *,
    blocked: int = 0,
    manual: int = 0,
    safe: int = 0,
) -> dict:
    return {
        "topic_id": topic_id,
        "rank": rank,
        "worst_priority": worst_priority,
        "finding_count": finding_count,
        "blocked_count": blocked,
        "manual_review_count": manual,
        "safe_review_count": safe,
        "headline": (
            f"{finding_count} finding(s); worst_priority={worst_priority}; "
            f"blocked={blocked}; manual_review={manual}; safe_review={safe}"
        ),
    }


def _payload(**overrides):
    payload = {
        "officer_version": "v3-min",
        "generated_at": "2026-03-24T10:25:52Z",
        "next_recommended_topic": "ci_integrations",
        "top_priority_reason": "Critical CI surface requires manual review.",
        "recommended_update_queue": [
            _qe(1, "ci_integrations", "p0", 2, blocked=1, manual=1, safe=0),
            _qe(2, "python_dependencies", "p2", 1, safe=1),
        ],
        "recommended_next_action": "Review CI-related updates first.",
        "recommended_review_paths": [".github/workflows"],
        "severity": "critical",
        "reminder_class": "blocked",
        "requires_manual_review": True,
    }
    payload.update(overrides)
    return payload


def _run(*args: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_renders_payload_from_explicit_path(tmp_path):
    payload_path = tmp_path / "notifier_payload.json"
    payload_path.write_text(json.dumps(_payload()), encoding="utf-8")

    result = _run("--payload", str(payload_path))

    assert result.returncode == 0
    assert "Headline:" in result.stdout
    assert "ci_integrations" in result.stdout
    assert result.stderr == ""


def test_cli_renders_payload_from_run_dir(tmp_path):
    payload_path = tmp_path / "notifier_payload.json"
    payload_path.write_text(json.dumps(_payload()), encoding="utf-8")

    result = _run("--run-dir", str(tmp_path))

    assert result.returncode == 0
    assert "Review paths: .github/workflows" in result.stdout


def test_cli_fails_on_missing_input():
    result = _run()

    assert result.returncode == 2
    assert "ERROR:" in result.stderr
    assert "provide --payload or --run-dir" in result.stderr


def test_cli_fails_on_missing_file(tmp_path):
    result = _run("--payload", str(tmp_path / "missing.json"))

    assert result.returncode == 2
    assert "ERROR:" in result.stderr


def test_cli_fails_on_invalid_payload(tmp_path):
    payload_path = tmp_path / "notifier_payload.json"
    invalid = _payload(severity="urgent")
    payload_path.write_text(json.dumps(invalid), encoding="utf-8")

    result = _run("--payload", str(payload_path))

    assert result.returncode == 2
    assert "severity" in result.stderr


def test_cli_fails_when_both_payload_and_run_dir_are_given(tmp_path):
    payload_path = tmp_path / "notifier_payload.json"
    payload_path.write_text(json.dumps(_payload()), encoding="utf-8")

    result = _run("--payload", str(payload_path), "--run-dir", str(tmp_path))

    assert result.returncode == 2
    assert "either --payload or --run-dir" in result.stderr


def test_cli_fails_on_invalid_json(tmp_path):
    path = tmp_path / "notifier_payload.json"
    path.write_text("{not json", encoding="utf-8")
    result = _run("--payload", str(path))
    assert result.returncode == 2
    assert "invalid JSON" in result.stderr
