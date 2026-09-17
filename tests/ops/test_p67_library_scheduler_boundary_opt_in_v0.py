"""p67 library scheduler boundary opt-in owner after p67 surface removal.

The previous opt-in tests imported ``src.ops.p67``. That package is owner-removed.
This module keeps the histogram reuse-owner path without restoring p67.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_p67_scheduler_surface_removed() -> None:
    assert not (REPO_ROOT / "src" / "ops" / "p67" / "shadow_session_scheduler_v1.py").is_file()
    assert not (REPO_ROOT / "src" / "ops" / "p67" / "shadow_session_scheduler_cli_v1.py").is_file()
    assert not (REPO_ROOT / "src" / "ops" / "p72" / "run_shadowloop_pack_v1.py").is_file()
