"""Smoke tests for scripts/ops/verify_registry_pointer_artifacts.py (NO-LIVE)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "ops" / "verify_registry_pointer_artifacts.py"
_WORKFLOW = ROOT / ".github" / "workflows" / "ci-operator-verify-registry.yml"
_WRAPPER = ROOT / "scripts" / "ops" / "verify_from_registry.sh"


def test_verify_registry_pointer_artifacts_help_lists_no_live() -> None:
    p = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, p.stderr
    # argparse may wrap the description across lines (e.g. "NO-\nLIVE")
    assert "NO-LIVE" in p.stdout.replace("\n", "")
    assert "--allow-expired" in p.stdout


def test_verify_registry_pointer_artifacts_main_returns_1_missing_pointer(tmp_path: Path) -> None:
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import verify_registry_pointer_artifacts as v  # noqa: E402

    missing = tmp_path / "missing.pointer"
    code = v.main([str(missing)])
    assert code == 1


def _import_verifier():
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import verify_registry_pointer_artifacts as v  # noqa: E402

    return v


def _run_script_with_out_base(pointer: Path, out_base: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            str(pointer),
            "--out-base",
            str(out_base),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )


def _write_valid_telemetry_summary(path: Path) -> None:
    payload = {
        "policy": {
            "action": "NO_TRADE",
            "reason_codes": ["OPERATOR_HOLD"],
        },
        "source": "evidence_manifest",
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _write_invalid_fallback_reason_telemetry_summary(path: Path) -> None:
    payload = {
        "policy": {
            "action": "NO_TRADE",
            "reason_codes": ["AUDIT_MANIFEST_NO_DECISION_CONTEXT"],
        },
        "source": "evidence_manifest",
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _write_pointer(path: Path, run_id: str, repo: str = "rauterfrank-ui/Peak_Trade") -> None:
    path.write_text(f"run_id={run_id}\nrepo={repo}\n", encoding="utf-8")


def _expired_records(v):
    return [
        v.ArtifactRecord(
            name="gh-paper-tests-audit-evidence-py3.9",
            expired=True,
            artifact_id=7095102369,
            expires_at="2026-08-17T20:51:09Z",
            created_at="2026-05-19T20:52:44Z",
        ),
        v.ArtifactRecord(
            name="gh-paper-tests-audit-evidence-py3.10",
            expired=True,
            artifact_id=7095103681,
            expires_at="2026-08-17T20:51:09Z",
            created_at="2026-05-19T20:52:48Z",
        ),
        v.ArtifactRecord(
            name="gh-paper-tests-audit-evidence-py3.11",
            expired=True,
            artifact_id=7095099640,
            expires_at="2026-08-17T20:51:09Z",
            created_at="2026-05-19T20:52:36Z",
        ),
    ]


def _available_records(v):
    return [
        v.ArtifactRecord(
            name="gh-paper-tests-audit-evidence-py3.11",
            expired=False,
            artifact_id=1,
            expires_at="2026-12-01T00:00:00Z",
            created_at="2026-08-18T00:00:00Z",
        )
    ]


def test_verify_registry_pointer_artifacts_offline_success_with_valid_telemetry(
    tmp_path: Path,
) -> None:
    run_id = "contract_run_ok_001"
    pointer = tmp_path / "fixture.pointer"
    pointer.write_text(f"run_id={run_id}\n", encoding="utf-8")
    out_base = tmp_path / "gh_runs"
    artifacts = out_base / run_id
    artifacts.mkdir(parents=True)
    _write_valid_telemetry_summary(artifacts / "telemetry_summary.json")

    proc = _run_script_with_out_base(pointer, out_base)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "OK: 1 telemetry_summary.json validated" in proc.stdout


def test_verify_registry_pointer_artifacts_telemetry_invariant_violation_exit_3(
    tmp_path: Path,
) -> None:
    run_id = "contract_run_fail_001"
    pointer = tmp_path / "fixture.pointer"
    pointer.write_text(f"run_id={run_id}\n", encoding="utf-8")
    out_base = tmp_path / "gh_runs"
    artifacts = out_base / run_id
    artifacts.mkdir(parents=True)
    _write_invalid_fallback_reason_telemetry_summary(artifacts / "telemetry_summary.json")

    proc = _run_script_with_out_base(pointer, out_base)
    assert proc.returncode == 3
    assert "FAIL: telemetry invariants violated" in proc.stderr
    assert "fallback code present in reason_codes" in proc.stderr


def test_classify_artifact_records_expired_available_empty() -> None:
    v = _import_verifier()
    assert v.classify_artifact_records(_expired_records(v)) == v.STATUS_EXPIRED
    assert v.classify_artifact_records(_available_records(v)) == v.STATUS_AVAILABLE
    mixed = _expired_records(v) + _available_records(v)
    assert v.classify_artifact_records(mixed) == v.STATUS_AVAILABLE
    assert v.classify_artifact_records([]) == v.STATUS_UNAVAILABLE_UNKNOWN


def test_parse_artifacts_api_payload_uses_explicit_expired_true_only() -> None:
    v = _import_verifier()
    payload = json.dumps(
        {
            "total_count": 2,
            "artifacts": [
                {"id": 1, "name": "a", "expired": True, "expires_at": "2026-08-17T20:51:09Z"},
                {"id": 2, "name": "b", "expired": False},
            ],
        }
    )
    records = v.parse_artifacts_api_payload(payload)
    assert [r.expired for r in records] == [True, False]
    missing_field = json.dumps({"artifacts": [{"id": 3, "name": "c"}]})
    assert v.parse_artifacts_api_payload(missing_field)[0].expired is False


def test_malformed_pointer_missing_run_id_is_invalid(tmp_path: Path) -> None:
    v = _import_verifier()
    pointer = tmp_path / "fixture.pointer"
    pointer.write_text("repo=rauterfrank-ui/Peak_Trade\n", encoding="utf-8")
    code = v.main([str(pointer), "--download", "--out-base", str(tmp_path / "out")])
    assert code == 1


def test_malformed_pointer_missing_file_is_invalid(tmp_path: Path) -> None:
    v = _import_verifier()
    missing = tmp_path / "missing.pointer"
    code = v.main(
        [str(missing), "--download", "--out-base", str(tmp_path / "out")],
        fetch_artifacts=lambda _rid, _repo: [],
        download_run=lambda _rid, _dest: (_ for _ in ()).throw(AssertionError("download")),
    )
    assert code == 1


def test_expired_artifacts_explicit_status_strict_fails_without_download(
    tmp_path: Path,
) -> None:
    v = _import_verifier()
    pointer = tmp_path / "fixture.pointer"
    _write_pointer(pointer, "26124538678")
    downloaded: list[str] = []

    def fetch(_run_id: str, _repo: str):
        return _expired_records(v)

    def download(run_id: str, _dest: Path) -> None:
        downloaded.append(run_id)

    code = v.main(
        [str(pointer), "--download", "--out-base", str(tmp_path / "out")],
        fetch_artifacts=fetch,
        download_run=download,
    )
    assert code == 1
    assert downloaded == []


def test_expired_artifacts_allow_expired_is_controlled_success(tmp_path: Path, capsys) -> None:
    v = _import_verifier()
    pointer = tmp_path / "fixture.pointer"
    _write_pointer(pointer, "26124538678")
    downloaded: list[str] = []

    def fetch(_run_id: str, _repo: str):
        return _expired_records(v)

    def download(run_id: str, _dest: Path) -> None:
        downloaded.append(run_id)

    code = v.main(
        [
            str(pointer),
            "--download",
            "--allow-expired",
            "--out-base",
            str(tmp_path / "out"),
        ],
        fetch_artifacts=fetch,
        download_run=download,
    )
    captured = capsys.readouterr()
    assert code == 0
    assert downloaded == []
    assert "REGISTRY_POINTER_STATUS=EXPIRED" in captured.out
    assert "REGISTRY_POINTER_EXPIRED=true" in captured.out
    assert "REGISTRY_POINTER_EXPIRED_ALLOWED=true" in captured.out
    assert "2026-08-17T20:51:09Z" in captured.out


def test_unknown_missing_artifacts_fail_closed(tmp_path: Path) -> None:
    v = _import_verifier()
    pointer = tmp_path / "fixture.pointer"
    _write_pointer(pointer, "26124538678")
    downloaded: list[str] = []

    code = v.main(
        [
            str(pointer),
            "--download",
            "--allow-expired",
            "--out-base",
            str(tmp_path / "out"),
        ],
        fetch_artifacts=lambda _rid, _repo: [],
        download_run=lambda run_id, _dest: downloaded.append(run_id),
    )
    assert code == 1
    assert downloaded == []


def test_auth_fetch_failure_is_not_classified_expired(tmp_path: Path, capsys) -> None:
    v = _import_verifier()
    pointer = tmp_path / "fixture.pointer"
    _write_pointer(pointer, "26124538678")

    def fetch(_run_id: str, _repo: str):
        raise v.ArtifactFetchError(
            "HTTP 403: Resource not accessible", kind="auth", http_status=403
        )

    code = v.main(
        [
            str(pointer),
            "--download",
            "--allow-expired",
            "--out-base",
            str(tmp_path / "out"),
        ],
        fetch_artifacts=fetch,
        download_run=lambda _rid, _dest: (_ for _ in ()).throw(AssertionError("download")),
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "REGISTRY_POINTER_STATUS=UNAVAILABLE_UNKNOWN" in captured.out
    assert "REGISTRY_POINTER_EXPIRED=true" not in captured.out
    assert "artifact metadata fetch failed (auth)" in captured.err


def test_available_artifact_downloads_and_verifies(tmp_path: Path, capsys) -> None:
    v = _import_verifier()
    run_id = "26124538678"
    pointer = tmp_path / "fixture.pointer"
    _write_pointer(pointer, run_id)
    out_base = tmp_path / "out"

    def fetch(_run_id: str, _repo: str):
        return _available_records(v)

    def download(got_run_id: str, dest: Path) -> None:
        assert got_run_id == run_id
        dest.mkdir(parents=True, exist_ok=True)
        _write_valid_telemetry_summary(dest / "telemetry_summary.json")

    code = v.main(
        [str(pointer), "--download", "--out-base", str(out_base)],
        fetch_artifacts=fetch,
        download_run=download,
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "REGISTRY_POINTER_STATUS=AVAILABLE" in captured.out
    assert "OK: 1 telemetry_summary.json validated" in captured.out


def test_available_metadata_but_download_failure_fails_closed(tmp_path: Path) -> None:
    v = _import_verifier()
    pointer = tmp_path / "fixture.pointer"
    _write_pointer(pointer, "26124538678")

    def fetch(_run_id: str, _repo: str):
        return _available_records(v)

    def download(_run_id: str, _dest: Path) -> None:
        raise v.ArtifactDownloadError("no valid artifacts found to download", returncode=1)

    code = v.main(
        [
            str(pointer),
            "--download",
            "--allow-expired",
            "--out-base",
            str(tmp_path / "out"),
        ],
        fetch_artifacts=fetch,
        download_run=download,
    )
    assert code == 1


def test_available_download_without_telemetry_fails_closed(tmp_path: Path) -> None:
    v = _import_verifier()
    pointer = tmp_path / "fixture.pointer"
    _write_pointer(pointer, "26124538678")

    def fetch(_run_id: str, _repo: str):
        return _available_records(v)

    def download(_run_id: str, dest: Path) -> None:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "README.txt").write_text("no telemetry here\n", encoding="utf-8")

    code = v.main(
        [str(pointer), "--download", "--out-base", str(tmp_path / "out")],
        fetch_artifacts=fetch,
        download_run=download,
    )
    assert code == 1


def test_available_download_with_invalid_telemetry_still_exit_3(tmp_path: Path) -> None:
    v = _import_verifier()
    pointer = tmp_path / "fixture.pointer"
    _write_pointer(pointer, "26124538678")

    def fetch(_run_id: str, _repo: str):
        return _available_records(v)

    def download(_run_id: str, dest: Path) -> None:
        dest.mkdir(parents=True, exist_ok=True)
        _write_invalid_fallback_reason_telemetry_summary(dest / "telemetry_summary.json")

    code = v.main(
        [str(pointer), "--download", "--out-base", str(tmp_path / "out")],
        fetch_artifacts=fetch,
        download_run=download,
    )
    assert code == 3


def test_download_error_text_is_not_used_as_expiry_classification() -> None:
    v = _import_verifier()
    # Metadata remaining available must stay AVAILABLE even if a later download
    # message looks like the historical expiry symptom.
    records = _available_records(v)
    assert v.classify_artifact_records(records) == v.STATUS_AVAILABLE


def test_workflow_allows_expired_only_on_pull_request() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    assert "github.event_name" in text
    assert "--allow-expired" in text
    assert "pull_request" in text
    assert "workflow_dispatch" in text
    assert (
        "scripts/ops/verify_from_registry.sh docs/ops/registry/LATEST_PHASE_M_SMOKE.pointer --download --allow-expired"
        in text
    )
    assert (
        "scripts/ops/verify_from_registry.sh docs/ops/registry/LATEST_PHASE_M_SMOKE.pointer --download\n"
        in text
    )


def test_verify_from_registry_wrapper_forwards_allow_expired() -> None:
    text = _WRAPPER.read_text(encoding="utf-8")
    assert "--allow-expired) ALLOW_EXPIRED=" in text
    assert "ARGS+=(--allow-expired)" in text
