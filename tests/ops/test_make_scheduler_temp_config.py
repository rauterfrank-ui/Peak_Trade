"""Tests for scripts/ops/make_scheduler_temp_config.py — temp scheduler config with absolute outdir."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef,import-untyped]

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "ops" / "make_scheduler_temp_config.py"
FIXTURE_JOB_ARGS = ROOT / "tests" / "fixtures" / "ops" / "make_scheduler_temp_config_job_args.toml"
FIXTURE_INLINE = (
    ROOT / "tests" / "fixtures" / "ops" / "make_scheduler_temp_config_inline_outdir.toml"
)
FIXTURE_DUP = ROOT / "tests" / "fixtures" / "ops" / "make_scheduler_temp_config_duplicate_name.toml"
REPO_JOBS = ROOT / "config" / "scheduler" / "jobs.toml"


def _load_mod():
    spec = importlib.util.spec_from_file_location("make_scheduler_temp_config", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_script_exists() -> None:
    assert SCRIPT.is_file()


def test_job_args_block_success(tmp_path: Path) -> None:
    mod = _load_mod()
    out = tmp_path / "jobs.out.toml"
    abs_outdir = "/tmp/peak_trade_make_scheduler_temp_config_job_args"
    assert (
        mod.main(
            [
                "make_scheduler_temp_config.py",
                "--source",
                str(FIXTURE_JOB_ARGS),
                "--job",
                "target_runtime_v0",
                "--outdir",
                abs_outdir,
                "--output",
                str(out),
            ]
        )
        == 0
    )
    data = tomllib.loads(out.read_text(encoding="utf-8"))
    jobs = {j["name"]: j for j in data["job"]}
    assert jobs["other_job"]["enabled"] is True
    assert jobs["target_runtime_v0"]["enabled"] is True
    assert jobs["target_runtime_v0"]["args"]["outdir"] == abs_outdir


def test_inline_args_outdir_success(tmp_path: Path) -> None:
    mod = _load_mod()
    out = tmp_path / "jobs.inline.toml"
    abs_outdir = "/tmp/peak_trade_make_scheduler_temp_config_inline"
    assert (
        mod.main(
            [
                "make_scheduler_temp_config.py",
                "--source",
                str(FIXTURE_INLINE),
                "--job",
                "inline_outdir_job",
                "--outdir",
                abs_outdir,
                "--output",
                str(out),
            ]
        )
        == 0
    )
    data = tomllib.loads(out.read_text(encoding="utf-8"))
    job = data["job"][0]
    assert job["name"] == "inline_outdir_job"
    assert job["enabled"] is True
    assert job["args"]["outdir"] == abs_outdir


def test_rejects_relative_outdir(tmp_path: Path) -> None:
    mod = _load_mod()
    out = tmp_path / "x.toml"
    assert (
        mod.main(
            [
                "make_scheduler_temp_config.py",
                "--source",
                str(FIXTURE_JOB_ARGS),
                "--job",
                "target_runtime_v0",
                "--outdir",
                "relative/path",
                "--output",
                str(out),
            ]
        )
        == mod.USAGE_EXIT
    )
    assert not out.exists()


def test_missing_job(tmp_path: Path) -> None:
    mod = _load_mod()
    out = tmp_path / "x.toml"
    assert (
        mod.main(
            [
                "make_scheduler_temp_config.py",
                "--source",
                str(FIXTURE_JOB_ARGS),
                "--job",
                "no_such_job",
                "--outdir",
                "/tmp/x",
                "--output",
                str(out),
            ]
        )
        == mod.USAGE_EXIT
    )


def test_duplicate_job_name(tmp_path: Path) -> None:
    mod = _load_mod()
    out = tmp_path / "x.toml"
    assert (
        mod.main(
            [
                "make_scheduler_temp_config.py",
                "--source",
                str(FIXTURE_DUP),
                "--job",
                "dup",
                "--outdir",
                "/tmp/x",
                "--output",
                str(out),
            ]
        )
        == mod.USAGE_EXIT
    )


def test_refuses_overwrite_without_force(tmp_path: Path) -> None:
    mod = _load_mod()
    out = tmp_path / "out.toml"
    out.write_text("x=1\n", encoding="utf-8")
    rc = mod.main(
        [
            "make_scheduler_temp_config.py",
            "--source",
            str(FIXTURE_JOB_ARGS),
            "--job",
            "target_runtime_v0",
            "--outdir",
            "/tmp/a",
            "--output",
            str(out),
        ]
    )
    assert rc == mod.USAGE_EXIT


def test_force_overwrites(tmp_path: Path) -> None:
    mod = _load_mod()
    out = tmp_path / "out.toml"
    out.write_text("x=1\n", encoding="utf-8")
    assert (
        mod.main(
            [
                "make_scheduler_temp_config.py",
                "--source",
                str(FIXTURE_JOB_ARGS),
                "--job",
                "target_runtime_v0",
                "--outdir",
                "/tmp/abs_force_test",
                "--output",
                str(out),
                "--force",
            ]
        )
        == 0
    )
    data = tomllib.loads(out.read_text(encoding="utf-8"))
    assert any(
        j.get("name") == "target_runtime_v0"
        and j.get("args", {}).get("outdir") == "/tmp/abs_force_test"
        for j in data["job"]
    )


def test_source_unchanged(tmp_path: Path) -> None:
    mod = _load_mod()
    before = FIXTURE_JOB_ARGS.read_bytes()
    out = tmp_path / "out.toml"
    assert (
        mod.main(
            [
                "make_scheduler_temp_config.py",
                "--source",
                str(FIXTURE_JOB_ARGS),
                "--job",
                "target_runtime_v0",
                "--outdir",
                "/tmp/abs_unchanged",
                "--output",
                str(out),
            ]
        )
        == 0
    )
    assert FIXTURE_JOB_ARGS.read_bytes() == before


def test_real_repo_runtime_min_job(tmp_path: Path) -> None:
    mod = _load_mod()
    out = tmp_path / "repo_slice.toml"
    abs_out = "/tmp/peak_trade_repo_runtime_min_abs_outdir"
    assert (
        mod.main(
            [
                "make_scheduler_temp_config.py",
                "--source",
                str(REPO_JOBS),
                "--job",
                "paper_shadow_247_paper_only_runtime_min_v0",
                "--outdir",
                abs_out,
                "--output",
                str(out),
            ]
        )
        == 0
    )
    data = tomllib.loads(out.read_text(encoding="utf-8"))
    target = next(
        j for j in data["job"] if j["name"] == "paper_shadow_247_paper_only_runtime_min_v0"
    )
    assert target["enabled"] is True
    assert target["args"]["outdir"] == abs_out
    before = REPO_JOBS.read_bytes()
    assert REPO_JOBS.read_bytes() == before


def test_real_repo_high_vol_inline_outdir(tmp_path: Path) -> None:
    mod = _load_mod()
    out = tmp_path / "repo_high.toml"
    abs_out = "/tmp/peak_trade_repo_high_vol_abs"
    assert (
        mod.main(
            [
                "make_scheduler_temp_config.py",
                "--source",
                str(REPO_JOBS),
                "--job",
                "paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0",
                "--outdir",
                abs_out,
                "--output",
                str(out),
            ]
        )
        == 0
    )
    data = tomllib.loads(out.read_text(encoding="utf-8"))
    target = next(
        j
        for j in data["job"]
        if j["name"] == "paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0"
    )
    assert target["enabled"] is True
    assert target["args"]["outdir"] == abs_out
