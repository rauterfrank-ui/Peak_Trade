"""Post-closeout projection chain automation contract (phases 2–9, offline fail-closed).

Extends canonical owners without parallel surfaces:
- Phase 2: durable_closeout_copy_verify_v0
- Phase 3: FINAL_MACHINE_LINES + manifest (payload builder contract)
- Phase 4: build_generic_evidence_run_registry_v1
- Phase 5: build_post_closeout_projection_payload_v0
- Phase 6: notion_post_closeout_sync_dry_run_v0
- Phase 7: Market handoff hints file (default-off; not global overlay enablement)
- Phase 8: DURATION_CONTRACT_VALIDATION.txt (separate from projection_ready)
- Phase 9: projection bundle MANIFEST.sha256 verify

Phase 1 (adapter) is out of scope — operator/runtime gated elsewhere.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from tests.fixtures.ops.generic_evidence_run_registry_v1 import projection_consumer_v0 as pc
from tests.ops import test_build_post_closeout_projection_payload_v0 as payload_tests
from tests.ops import test_closeout_final_machine_lines_contract_v0 as ml_contract
from tests.ops import test_durable_closeout_copy_verify_v0 as closeout_tests
from tests.ops import test_projection_chain_synthetic_smoke_v0 as chain_smoke

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_SCRIPT = REPO_ROOT / "scripts/ops/build_generic_evidence_run_registry_v1.py"

CANONICAL_OWNERS: dict[str, str] = {
    "phase_1_adapter": "scripts/ops/run_shadow_bounded_observation_adapter_v0.py",
    "phase_2_durable_closeout": "scripts/ops/durable_closeout_copy_verify_v0.py",
    "phase_3_final_machine_lines": "scripts/ops/build_post_closeout_projection_payload_v0.py",
    "phase_4_registry": "scripts/ops/build_generic_evidence_run_registry_v1.py",
    "phase_5_payload": "scripts/ops/build_post_closeout_projection_payload_v0.py",
    "phase_6_notion_dry_run": "scripts/ops/notion_post_closeout_sync_dry_run_v0.py",
    "phase_7_market": "src/webui/market_surface.py",
}

REUSED_TEST_MODULES: tuple[str, ...] = (
    "tests/ops/test_projection_chain_synthetic_smoke_v0.py",
    "tests/ops/test_closeout_final_machine_lines_contract_v0.py",
    "tests/ops/test_durable_closeout_copy_verify_v0.py",
    "tests/ops/test_build_post_closeout_projection_payload_v0.py",
)


def _load_registry_module():
    spec = importlib.util.spec_from_file_location(
        "build_generic_evidence_run_registry_v1_chain_contract", REGISTRY_SCRIPT
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_archive_shadow_run(archive: Path, run_id: str) -> Path:
    run_dir = pc.write_lane(archive, "shadow", run_id, review="PASS")
    (run_dir / "CLOSEOUT.md").write_text("# synthetic closeout\n", encoding="utf-8")
    wrapper = run_dir / "wrapper_evidence"
    wrapper.mkdir(exist_ok=True)
    (wrapper / "manifest.json").write_text(
        json.dumps(
            {
                "utc_started": "2026-05-27T11:46:06Z",
                "utc_completed": "2026-05-27T11:56:02Z",
                "steps_emitted": 120,
                "step_interval_seconds": 5.0,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return run_dir


def _write_final_machine_lines(closeout: Path, *, complete: bool) -> None:
    if complete:
        lines = dict(payload_tests.REQUIRED_MACHINE_LINES)
        lines.update(ml_contract.REAL10M_BOUNDARY_SAFE_SUPPLEMENTS)
        lines["RUNTIME_COMMANDS_CALLED"] = "true"
        lines["ADAPTER_EXECUTED"] = "true"
    else:
        lines = dict(ml_contract.REAL10M_PHASE3_INCOMPLETE_MACHINE_LINES)
    (closeout / "FINAL_MACHINE_LINES.txt").write_text(
        "\n".join(f"{k}={v}" for k, v in lines.items()) + "\n",
        encoding="utf-8",
    )


def _run_registry_build(archive: Path, registry_json: Path) -> int:
    mod = _load_registry_module()
    registry = mod.build_registry(mod.BuildContext(archive_root=archive, repo_root=REPO_ROOT))
    registry_json.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    return 0


def _run_payload_strict(
    builder, closeout: Path, registry: Path, out: Path, run_id: str
) -> tuple[int, str, str]:
    argv = [
        "--closeout-root",
        str(closeout),
        "--registry-json",
        str(registry),
        "--output-json",
        str(out),
        "--run-id",
        run_id,
        "--repo-commit",
        "de90da8a0000000000000000000000000000000000",
        "--strict",
    ]
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/ops/build_post_closeout_projection_payload_v0.py"),
        ]
        + argv,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
    )
    return proc.returncode, proc.stdout, proc.stderr


def _projection_manifest_verify(projection_dir: Path) -> None:
    files = sorted(
        p.name
        for p in projection_dir.iterdir()
        if p.is_file()
        and p.name
        not in {
            "MANIFEST.sha256",
            "MANIFEST_VERIFY.log",
        }
    )
    lines = []
    for name in files:
        digest = hashlib.sha256((projection_dir / name).read_bytes()).hexdigest()
        lines.append(f"{digest}  {name}")
    manifest = projection_dir / "MANIFEST.sha256"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    verify = subprocess.run(
        ["shasum", "-a", "256", "-c", str(manifest)],
        cwd=str(projection_dir),
        text=True,
        capture_output=True,
    )
    (projection_dir / "MANIFEST_VERIFY.log").write_text(
        verify.stdout + verify.stderr, encoding="utf-8"
    )
    assert verify.returncode == 0, verify.stdout + verify.stderr


def _run_chain_phases_2_through_9(
    tmp_path: Path,
    *,
    complete_machine_lines: bool,
    run_id: str = "shadow_chain_automation_v0",
) -> dict[str, Path]:
    work = tmp_path / "chain_work"
    archive = work / "archive"
    archive.mkdir(parents=True)
    run_dir = _write_archive_shadow_run(archive, run_id)

    closeout_dest = closeout_tests._archive_like_dest(tmp_path, "closeout_dest")
    try:
        closeout_helper = closeout_tests._load_helper()
        rc = closeout_helper.main(
            [
                "--source-dir",
                str(run_dir),
                "--dest-dir",
                str(closeout_dest),
                *closeout_tests._tmp_source_args(),
                "--force",
            ]
        )
        assert rc == 0, "phase 2 durable closeout copy failed"
        assert (closeout_dest / "DURABLE_COPY_README.md").is_file()
        assert (closeout_dest / "MANIFEST.sha256").is_file()

        _write_final_machine_lines(closeout_dest, complete=complete_machine_lines)
        write_manifest_sha256(closeout_dest)
        ok, msg = verify_manifest_sha256(closeout_dest)
        assert ok, f"phase 3 manifest verify: {msg}"

        projection_dir = work / "projection"
        projection_dir.mkdir()
        registry_json = projection_dir / "registry.json"
        assert _run_registry_build(archive, registry_json) == 0

        payload_json = projection_dir / "projection_payload.json"
        builder = payload_tests._load_builder()
        payload_rc, _, payload_err = _run_payload_strict(
            builder, closeout_dest, registry_json, payload_json, run_id
        )

        notion_report = projection_dir / "notion_dry_run_report.json"
        dry_run = chain_smoke._load_module(
            chain_smoke.DRY_RUN_SCRIPT, "notion_dry_run_chain_contract"
        )

        if not complete_machine_lines:
            assert payload_rc == 1
            assert "projection_blocked_reason=missing_boundary_flags" in payload_err
            return {"closeout": closeout_dest, "projection_dir": projection_dir}

        assert payload_rc == 0, payload_err
        payload = json.loads(payload_json.read_text(encoding="utf-8"))
        assert payload["projection_ready"] is True

        notion_argv = [
            "--projection-payload-json",
            str(payload_json),
            "--target-name",
            "Evidence & Closeouts",
            "--boundary-text-verified",
            "--output-report-json",
            str(notion_report),
            "--strict",
        ]
        assert dry_run.main(notion_argv) == 0
        report = json.loads(notion_report.read_text(encoding="utf-8"))
        assert report["write_allowed"] is False
        assert report["dry_run"] is True

        hints = projection_dir / "MARKET_OVERLAY_HINTS.txt"
        hints.write_text(
            "\n".join(
                [
                    "MARKET_OVERLAY_GLOBAL_ENABLED=false",
                    f"PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON={payload_json}",
                    "HANDOFF_HINT_ONLY=true",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        assert "PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED" not in hints.read_text()

        duration_path = projection_dir / "DURATION_CONTRACT_VALIDATION.txt"
        manifest_path = closeout_dest / "wrapper_evidence" / "manifest.json"
        meta = json.loads(manifest_path.read_text(encoding="utf-8"))
        duration_path.write_text(
            "\n".join(
                [
                    "WALL_CLOCK_VALIDATION_REQUIRED=true",
                    "OBSERVED_DURATION_SECONDS=596",
                    "EXPECTED_DURATION_SECONDS=600",
                    f"steps_emitted={meta.get('steps_emitted', 0)}",
                    f"step_interval_seconds={meta.get('step_interval_seconds', 0)}",
                    "PAYLOAD_PROJECTION_READY_NOT_WALL_CLOCK_EVIDENCE=true",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        duration_text = duration_path.read_text(encoding="utf-8")
        assert "OBSERVED_DURATION_SECONDS=" in duration_text
        assert "PAYLOAD_PROJECTION_READY_NOT_WALL_CLOCK_EVIDENCE=true" in duration_text

        serialized_payload = json.dumps(payload)
        for forbidden in (
            "OBSERVED_DURATION_SECONDS",
            "WALL_CLOCK_VALIDATION",
            "step_interval_seconds",
        ):
            assert forbidden not in serialized_payload

        _projection_manifest_verify(projection_dir)

        return {
            "closeout": closeout_dest,
            "projection_dir": projection_dir,
            "payload_json": payload_json,
            "notion_report": notion_report,
        }
    finally:
        closeout_tests._cleanup_archive_like_dest(closeout_dest)


@pytest.fixture(scope="module")
def builder():
    return payload_tests._load_builder()


def test_reuse_drift_guard_canonical_owners_and_no_parallel_surfaces():
    for path in CANONICAL_OWNERS.values():
        assert (REPO_ROOT / path).is_file(), f"missing canonical owner: {path}"
    for mod in REUSED_TEST_MODULES:
        assert (REPO_ROOT / mod).is_file()
    assert (
        REPO_ROOT / "tests/ops/test_closeout_to_projection_chain_automation_contract_v0.py"
    ).is_file()
    assert not (REPO_ROOT / "scripts/ops/post_closeout_chain_execute_v0.py").exists()


def test_phases_2_through_9_happy_path_fail_closed_chain(tmp_path: Path):
    paths = _run_chain_phases_2_through_9(tmp_path, complete_machine_lines=True)
    assert paths["payload_json"].is_file()
    assert paths["notion_report"].is_file()
    assert (paths["projection_dir"] / "MANIFEST.sha256").is_file()
    assert (paths["projection_dir"] / "DURATION_CONTRACT_VALIDATION.txt").is_file()
    assert (paths["projection_dir"] / "MARKET_OVERLAY_HINTS.txt").is_file()


def test_incomplete_final_machine_lines_block_phase_5_strict(tmp_path: Path):
    _run_chain_phases_2_through_9(tmp_path, complete_machine_lines=False)


def test_strict_payload_builder_reports_missing_boundary_flags(
    builder, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    closeout = tmp_path / "closeout"
    registry_path = tmp_path / "registry.json"
    out = tmp_path / "payload.json"
    payload_tests._write_closeout_bundle(closeout)
    (closeout / "FINAL_MACHINE_LINES.txt").write_text(
        "RUNTIME_COMMANDS_CALLED=false\n", encoding="utf-8"
    )
    payload_tests._write_registry(registry_path, tmp_path)

    rc = builder.main(
        [
            "--closeout-root",
            str(closeout),
            "--registry-json",
            str(registry_path),
            "--output-json",
            str(out),
            "--strict",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 1
    assert "projection_blocked_reason=missing_boundary_flags" in captured.err
