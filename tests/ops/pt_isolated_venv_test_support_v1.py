"""Shared fixture for checkout-local isolated test venvs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts.runtime.pt_worktree_environment_v1 import write_env_fingerprint


def complete_isolated_test_venv(repo: Path) -> None:
    """Give a fake checkout a lockfile, editable binding, and fingerprint.

    ``.venv/bin/python`` must already exist. Does not create a venv or install
    packages. Uses the same ``repo`` Path object later passed to validators.
    """
    if not (repo / "uv.lock").is_file():
        (repo / "uv.lock").write_text("peak-trade-test-lock\n", encoding="utf-8")
    (repo / "src").mkdir(exist_ok=True)
    site = (
        repo
        / ".venv"
        / "lib"
        / f"python{sys.version_info.major}.{sys.version_info.minor}"
        / "site-packages"
    )
    dist = site / "peak_trade-0.1.0.dist-info"
    dist.mkdir(parents=True, exist_ok=True)
    (site / "__editable__.peak_trade-0.1.0.pth").write_text(f"{repo / 'src'}\n", encoding="utf-8")
    (dist / "direct_url.json").write_text(
        json.dumps({"url": Path(repo).as_uri(), "dir_info": {"editable": True}}),
        encoding="utf-8",
    )
    write_env_fingerprint(repo, python_version=sys.version.split()[0])
