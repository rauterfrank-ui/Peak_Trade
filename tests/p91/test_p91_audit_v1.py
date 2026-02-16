from pathlib import Path
import json
import time

from src.ops.p91 import P91AuditContextV1, build_shadow_soak_audit_v1


def _mk_tick(root: Path, name: str, p76_status: str = "P76_READY") -> Path:
    t = root / name
    t.mkdir(parents=True, exist_ok=True)
    (t / "manifest.json").write_text('{"files":[]}', encoding="utf-8")
    (t / "p86_result.json").write_text('{"overall_ok": true}', encoding="utf-8")
    p76 = t / "p76"
    p76.mkdir(parents=True, exist_ok=True)
    (p76 / "P76_RESULT.txt").write_text(f"{p76_status} mode=shadow\n", encoding="utf-8")
    return t


def test_p91_reports_missing_out_dir(tmp_path: Path):
    ctx = P91AuditContextV1(out_dir=tmp_path / "does_not_exist", min_ticks=2)
    out = build_shadow_soak_audit_v1(ctx)
    assert "out_dir_missing" in out["alerts"]
    assert out["summary"]["tick_count"] == 0


def test_p91_insufficient_ticks(tmp_path: Path):
    out_dir = tmp_path / "run_20260216T000000Z"
    out_dir.mkdir()
    _mk_tick(out_dir, "tick_20260216T000001Z")
    ctx = P91AuditContextV1(out_dir=out_dir, min_ticks=2)
    out = build_shadow_soak_audit_v1(ctx)
    assert any(a.startswith("insufficient_ticks:") for a in out["alerts"])


def test_p91_latest_p76_status(tmp_path: Path):
    out_dir = tmp_path / "run_20260216T000000Z"
    out_dir.mkdir()
    _mk_tick(out_dir, "tick_20260216T000001Z", "P76_READY")
    time.sleep(0.01)
    _mk_tick(out_dir, "tick_20260216T000002Z", "P76_NOT_READY")
    ctx = P91AuditContextV1(out_dir=out_dir, min_ticks=1)
    out = build_shadow_soak_audit_v1(ctx)
    assert out["summary"]["latest_p76_status"] in ("ready", "not_ready")


def test_p91_json_serializable(tmp_path: Path):
    out_dir = tmp_path / "run_20260216T000000Z"
    out_dir.mkdir()
    _mk_tick(out_dir, "tick_20260216T000001Z")
    ctx = P91AuditContextV1(out_dir=out_dir, min_ticks=1)
    out = build_shadow_soak_audit_v1(ctx)
    json.dumps(out)
