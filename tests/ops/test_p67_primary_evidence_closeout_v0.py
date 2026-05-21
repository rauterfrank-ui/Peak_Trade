"""Contract tests for P67/P72 opt-in primary evidence closeout (no runtime workloads)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
P67_LIBRARY = REPO_ROOT / "src" / "ops" / "p67" / "shadow_session_scheduler_v1.py"
P67_CLI = REPO_ROOT / "src" / "ops" / "p67" / "shadow_session_scheduler_cli_v1.py"
P72_LIBRARY = REPO_ROOT / "src" / "ops" / "p72" / "run_shadowloop_pack_v1.py"
SHARED_HELPER = REPO_ROOT / "scripts" / "ops" / "primary_evidence_retention_v0.py"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.ops.p67.shadow_session_scheduler_v1 import (
    P67RunContextV1,
    run_shadow_session_scheduler_v1,
)
from src.ops.p72 import P72PackContextV1, run_shadowloop_pack_v1


def test_shared_helper_exposes_finalize_primary_evidence_root() -> None:
    text = SHARED_HELPER.read_text(encoding="utf-8")
    assert "def finalize_primary_evidence_root" in text
    assert "write_manifest_sha256" in text
    assert "verify_manifest_sha256" in text


def test_p67_library_wires_opt_in_enforce_and_shared_helper() -> None:
    text = P67_LIBRARY.read_text(encoding="utf-8")
    assert "primary_evidence_enforce: bool = False" in text
    assert "finalize_primary_evidence_root" in text
    assert "def verify_manifest_sha256" not in text


def test_p72_library_wires_opt_in_enforce_and_passes_through_to_p67() -> None:
    text = P72_LIBRARY.read_text(encoding="utf-8")
    assert "primary_evidence_enforce: bool = False" in text
    assert "primary_evidence_enforce=ctx.primary_evidence_enforce" in text
    assert "finalize_primary_evidence_root" in text


def test_p67_cli_scheduler_guard_preserved() -> None:
    text = P67_CLI.read_text(encoding="utf-8")
    guard_idx = text.index("assert_scheduler_start_authorized")
    run_idx = text.index("run_shadow_session_scheduler_v1(ctx)")
    assert guard_idx < run_idx
    assert "scheduler_start_boundary_guard_v0" in text


def test_p67_default_backward_compatible_no_manifest_sha256(tmp_path: Path) -> None:
    run_shadow_session_scheduler_v1(
        P67RunContextV1(
            mode="shadow",
            run_id="compat",
            out_dir=tmp_path,
            iterations=1,
            interval_seconds=0.0,
        ),
    )
    root = tmp_path / "p67_shadow_session_compat"
    assert (root / "manifest.json").exists()
    assert not (root / "MANIFEST.sha256").exists()


def test_p67_enforce_without_out_dir_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="primary_evidence_enforce requires out_dir"):
        run_shadow_session_scheduler_v1(
            P67RunContextV1(
                mode="shadow",
                iterations=1,
                interval_seconds=0.0,
                primary_evidence_enforce=True,
            ),
        )


def test_p67_enforce_writes_and_verifies_manifest_sha256(tmp_path: Path) -> None:
    run_shadow_session_scheduler_v1(
        P67RunContextV1(
            mode="shadow",
            run_id="enforce",
            out_dir=tmp_path,
            iterations=1,
            interval_seconds=0.0,
            primary_evidence_enforce=True,
        ),
    )
    root = tmp_path / "p67_shadow_session_enforce"
    manifest = root / "MANIFEST.sha256"
    assert manifest.is_file()
    from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

    ok, msg = verify_manifest_sha256(root)
    assert ok is True, msg


def test_p67_enforce_fails_closed_on_finalize_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _fail(_root: Path) -> tuple[bool, str]:
        return False, "checksum mismatch: meta.json"

    monkeypatch.setattr(
        "scripts.ops.primary_evidence_retention_v0.finalize_primary_evidence_root",
        _fail,
    )
    with pytest.raises(RuntimeError, match="primary evidence finalize failed"):
        run_shadow_session_scheduler_v1(
            P67RunContextV1(
                mode="shadow",
                run_id="fail",
                out_dir=tmp_path,
                iterations=1,
                interval_seconds=0.0,
                primary_evidence_enforce=True,
            ),
        )


def test_p72_enforce_finalizes_pack_root(tmp_path: Path) -> None:
    out = run_shadowloop_pack_v1(
        P72PackContextV1(
            mode="shadow",
            run_id="pack",
            out_dir=tmp_path,
            allow_bull_strategies=["s1"],
            allow_bear_strategies=["s1"],
            iterations=1,
            interval_seconds=0.0,
            primary_evidence_enforce=True,
        ),
    )
    assert out["gate_ok"] is True
    assert (tmp_path / "MANIFEST.sha256").is_file()
    from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

    ok, msg = verify_manifest_sha256(tmp_path)
    assert ok is True, msg
