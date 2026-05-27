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
import shutil
import subprocess
import sys
from dataclasses import dataclass, replace
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


@dataclass(frozen=True)
class PostCloseoutAutomationReadinessInputs:
    """Synthetic post-closeout automation readiness audit (tests only; not production API)."""

    closeout_root: Path | None = None
    registry_json: Path | None = None
    projection_dir: Path | None = None
    projection_payload_path: Path | None = None
    projection_payload: dict | None = None
    notion_report_path: Path | None = None
    notion_report: dict | None = None
    market_hints_path: Path | None = None
    duration_validation_path: Path | None = None
    closeout_manifest_verify_ok: bool = False
    projection_manifest_verify_ok: bool = False
    machine_lines_keys_complete: bool | None = None
    manual_recovery_required: bool = True
    hook_automation_owner_status: str = "not_implemented"
    claimed_full_post_closeout_automation_implemented: bool = False
    notion_write_occurred: bool = False


def _parse_machine_lines_file(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        parsed[key.strip()] = value.strip()
    return parsed


def build_post_closeout_automation_readiness_summary(
    inp: PostCloseoutAutomationReadinessInputs,
) -> tuple[bool, list[str]]:
    """Return (readiness_ok, blockers) for v0 synthetic post-closeout automation claims.

    ``projection_ready`` alone does **not** imply full post-closeout automation readiness.
    """
    blockers: list[str] = []

    if inp.notion_write_occurred:
        blockers.append("notion_write_occurred_v0_forbidden")

    if inp.manual_recovery_required:
        blockers.append("manual_recovery_required")

    if inp.claimed_full_post_closeout_automation_implemented:
        if inp.hook_automation_owner_status != "identified":
            blockers.append("full_automation_claim_requires_hook_owner_identified")

    if inp.closeout_root is None or not inp.closeout_root.is_dir():
        blockers.append("durable_closeout_missing")
    else:
        if not (inp.closeout_root / "DURABLE_COPY_README.md").is_file():
            blockers.append("durable_closeout_readme_missing")
        if not (inp.closeout_root / "MANIFEST.sha256").is_file():
            blockers.append("closeout_manifest_missing")
        if not (inp.closeout_root / "FINAL_MACHINE_LINES.txt").is_file():
            blockers.append("final_machine_lines_missing")
        else:
            ml_path = inp.closeout_root / "FINAL_MACHINE_LINES.txt"
            if inp.machine_lines_keys_complete is False:
                blockers.append("final_machine_lines_incomplete")
            elif inp.machine_lines_keys_complete is None:
                fields = _parse_machine_lines_file(ml_path)
                for key in payload_tests.REQUIRED_MACHINE_LINES:
                    if key not in fields:
                        blockers.append(f"missing_machine_line_key:{key}")
                        break

    if not inp.closeout_manifest_verify_ok:
        blockers.append("closeout_manifest_verify_not_ok")

    if inp.registry_json is None or not inp.registry_json.is_file():
        blockers.append("registry_json_missing")

    if inp.projection_payload_path is None or not inp.projection_payload_path.is_file():
        blockers.append("projection_payload_missing")

    payload = inp.projection_payload
    if payload is None and inp.projection_payload_path and inp.projection_payload_path.is_file():
        payload = json.loads(inp.projection_payload_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        blockers.append("projection_payload_unreadable")
    else:
        if payload.get("projection_ready") is not True:
            blockers.append("projection_ready_not_true")
        blob = json.dumps(payload)
        for token in (
            "OBSERVED_DURATION_SECONDS",
            "WALL_CLOCK_VALIDATION",
            "step_interval_seconds",
        ):
            if token in blob:
                blockers.append(f"projection_payload_must_not_embed_duration_token:{token}")

    notion = inp.notion_report
    if inp.notion_report_path and inp.notion_report_path.is_file() and notion is None:
        notion = json.loads(inp.notion_report_path.read_text(encoding="utf-8"))
    if notion is None:
        blockers.append("notion_dry_run_report_missing")
    else:
        if notion.get("write_allowed") is not False:
            blockers.append("notion_write_allowed_must_be_false_v0")
        if notion.get("dry_run") is not True:
            blockers.append("notion_dry_run_must_be_true_v0")

    if inp.market_hints_path is None or not inp.market_hints_path.is_file():
        blockers.append("market_handoff_hints_not_persisted")

    if inp.duration_validation_path is None or not inp.duration_validation_path.is_file():
        blockers.append("duration_validation_artifact_missing")

    if inp.projection_dir is None or not inp.projection_dir.is_dir():
        blockers.append("projection_dir_missing")
    elif not (inp.projection_dir / "MANIFEST.sha256").is_file():
        blockers.append("projection_manifest_missing")
    elif not inp.projection_manifest_verify_ok:
        blockers.append("projection_manifest_verify_not_ok")

    if payload and isinstance(payload, dict):
        auth = payload.get("authority") or {}
        for key, expected in (
            ("live_authority", False),
            ("testnet_authority", False),
            ("broker_exchange_authority", False),
        ):
            if auth.get(key) is not expected:
                blockers.append(f"authority_boundary:{key}")

    return (len(blockers) == 0, blockers)


def _synthetic_chain_readiness_inputs(
    paths: dict[str, Path],
) -> PostCloseoutAutomationReadinessInputs:
    """Map a successful ``_run_chain_phases_2_through_9`` result to readiness inputs."""
    proj = paths["projection_dir"]
    closeout = paths["closeout"]
    return PostCloseoutAutomationReadinessInputs(
        closeout_root=closeout,
        registry_json=proj / "registry.json",
        projection_dir=proj,
        projection_payload_path=paths["payload_json"],
        notion_report_path=paths["notion_report"],
        market_hints_path=proj / "MARKET_OVERLAY_HINTS.txt",
        duration_validation_path=proj / "DURATION_CONTRACT_VALIDATION.txt",
        closeout_manifest_verify_ok=True,
        projection_manifest_verify_ok=True,
        manual_recovery_required=False,
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

        # ``closeout_dest`` lives under repo ``out/`` and is removed in ``finally``; keep a tmp_path
        # snapshot so readiness checks can still inspect durable closeout layout after return.
        closeout_snapshot = work / "closeout_readiness_snapshot"
        if closeout_snapshot.exists():
            shutil.rmtree(closeout_snapshot)
        shutil.copytree(closeout_dest, closeout_snapshot)

        return {
            "closeout": closeout_snapshot,
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


def test_post_closeout_automation_readiness_true_offline_synthetic_chain(tmp_path: Path):
    paths = _run_chain_phases_2_through_9(tmp_path, complete_machine_lines=True)
    ok, blockers = build_post_closeout_automation_readiness_summary(
        _synthetic_chain_readiness_inputs(paths)
    )
    assert ok is True
    assert blockers == []


def test_readiness_false_when_manual_recovery_required_despite_artifacts(tmp_path: Path):
    paths = _run_chain_phases_2_through_9(tmp_path, complete_machine_lines=True)
    inp = replace(_synthetic_chain_readiness_inputs(paths), manual_recovery_required=True)
    ok, blockers = build_post_closeout_automation_readiness_summary(inp)
    assert ok is False
    assert "manual_recovery_required" in blockers


def test_readiness_false_when_market_hints_not_persisted(tmp_path: Path):
    paths = _run_chain_phases_2_through_9(tmp_path, complete_machine_lines=True)
    hints = paths["projection_dir"] / "MARKET_OVERLAY_HINTS.txt"
    hints.unlink()
    ok, blockers = build_post_closeout_automation_readiness_summary(
        _synthetic_chain_readiness_inputs(paths)
    )
    assert ok is False
    assert "market_handoff_hints_not_persisted" in blockers


def test_readiness_false_when_duration_validation_artifact_missing(tmp_path: Path):
    paths = _run_chain_phases_2_through_9(tmp_path, complete_machine_lines=True)
    dur = paths["projection_dir"] / "DURATION_CONTRACT_VALIDATION.txt"
    dur.unlink()
    ok, blockers = build_post_closeout_automation_readiness_summary(
        _synthetic_chain_readiness_inputs(paths)
    )
    assert ok is False
    assert "duration_validation_artifact_missing" in blockers


def test_readiness_false_when_notion_write_occurred_v0(tmp_path: Path):
    paths = _run_chain_phases_2_through_9(tmp_path, complete_machine_lines=True)
    inp = replace(_synthetic_chain_readiness_inputs(paths), notion_write_occurred=True)
    ok, blockers = build_post_closeout_automation_readiness_summary(inp)
    assert ok is False
    assert "notion_write_occurred_v0_forbidden" in blockers


def test_readiness_false_when_projection_manifest_verify_not_ok(tmp_path: Path):
    paths = _run_chain_phases_2_through_9(tmp_path, complete_machine_lines=True)
    payload = json.loads(paths["payload_json"].read_text(encoding="utf-8"))
    assert payload.get("projection_ready") is True
    inp = replace(_synthetic_chain_readiness_inputs(paths), projection_manifest_verify_ok=False)
    ok, blockers = build_post_closeout_automation_readiness_summary(inp)
    assert ok is False
    assert "projection_manifest_verify_not_ok" in blockers


def test_readiness_false_full_automation_claim_requires_hook_owner(tmp_path: Path):
    paths = _run_chain_phases_2_through_9(tmp_path, complete_machine_lines=True)
    inp = replace(
        _synthetic_chain_readiness_inputs(paths),
        claimed_full_post_closeout_automation_implemented=True,
        hook_automation_owner_status="not_implemented",
    )
    ok, blockers = build_post_closeout_automation_readiness_summary(inp)
    assert ok is False
    assert "full_automation_claim_requires_hook_owner_identified" in blockers


def test_readiness_true_when_hook_owner_identified_and_full_automation_claimed(tmp_path: Path):
    paths = _run_chain_phases_2_through_9(tmp_path, complete_machine_lines=True)
    inp = replace(
        _synthetic_chain_readiness_inputs(paths),
        claimed_full_post_closeout_automation_implemented=True,
        hook_automation_owner_status="identified",
    )
    ok, blockers = build_post_closeout_automation_readiness_summary(inp)
    assert ok is True
    assert blockers == []


def test_projection_ready_true_alone_insufficient_for_full_automation_readiness(tmp_path: Path):
    paths = _run_chain_phases_2_through_9(tmp_path, complete_machine_lines=True)
    payload = json.loads(paths["payload_json"].read_text(encoding="utf-8"))
    assert payload.get("projection_ready") is True
    inp = PostCloseoutAutomationReadinessInputs(
        projection_payload=payload,
        projection_payload_path=paths["payload_json"],
        manual_recovery_required=False,
        closeout_manifest_verify_ok=True,
        projection_manifest_verify_ok=True,
    )
    ok, blockers = build_post_closeout_automation_readiness_summary(inp)
    assert ok is False
    assert "durable_closeout_missing" in blockers


def test_readiness_false_when_projection_ready_not_true(tmp_path: Path):
    paths = _run_chain_phases_2_through_9(tmp_path, complete_machine_lines=True)
    bad = json.loads(paths["payload_json"].read_text(encoding="utf-8"))
    bad["projection_ready"] = False
    inp = replace(_synthetic_chain_readiness_inputs(paths), projection_payload=bad)
    ok, blockers = build_post_closeout_automation_readiness_summary(inp)
    assert ok is False
    assert "projection_ready_not_true" in blockers


def test_readiness_false_when_notion_report_write_allowed_not_false_v0(tmp_path: Path):
    paths = _run_chain_phases_2_through_9(tmp_path, complete_machine_lines=True)
    report_path = paths["notion_report"]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["write_allowed"] = True
    report_path.write_text(json.dumps(report) + "\n", encoding="utf-8")
    ok, blockers = build_post_closeout_automation_readiness_summary(
        _synthetic_chain_readiness_inputs(paths)
    )
    assert ok is False
    assert "notion_write_allowed_must_be_false_v0" in blockers


def test_readiness_false_when_notion_report_not_dry_run(tmp_path: Path):
    paths = _run_chain_phases_2_through_9(tmp_path, complete_machine_lines=True)
    report_path = paths["notion_report"]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["dry_run"] = False
    report_path.write_text(json.dumps(report) + "\n", encoding="utf-8")
    ok, blockers = build_post_closeout_automation_readiness_summary(
        _synthetic_chain_readiness_inputs(paths)
    )
    assert ok is False
    assert "notion_dry_run_must_be_true_v0" in blockers


def test_readiness_false_when_payload_authority_boundary_violation(tmp_path: Path):
    paths = _run_chain_phases_2_through_9(tmp_path, complete_machine_lines=True)
    bad = json.loads(paths["payload_json"].read_text(encoding="utf-8"))
    bad.setdefault("authority", {})["live_authority"] = True
    inp = replace(_synthetic_chain_readiness_inputs(paths), projection_payload=bad)
    ok, blockers = build_post_closeout_automation_readiness_summary(inp)
    assert ok is False
    assert "authority_boundary:live_authority" in blockers
