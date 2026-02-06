from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


def test_passes_on_repo_main_files() -> None:
    r = run(
        [
            "python3",
            "src/governance/validate_ai_matrix_vs_registry.py",
            "docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md",
            "config/model_registry.toml",
        ]
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "[PASS]" in r.stdout


def test_fails_on_registry_reference_drift(tmp_path: Path) -> None:
    # minimal matrix row for L0 only (parser will flag missing layers, but we mainly want reference drift)
    matrix = tmp_path / "m.md"
    matrix.write_text("| **L0** | x | x | RO | gpt-5.2 | — | o3-pro | x | x |\n", encoding="utf-8")

    reg = tmp_path / "r.toml"
    reg.write_text(
        textwrap.dedent("""
        # Reference: docs/governance/ai_autonomy/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md

        [layer_mapping.L0]
        autonomy = "RO"
        primary = "gpt-5.2"
        fallback = []
        critic = "o3-pro"

        [models]
        "gpt-5.2" = {}
        "o3-pro" = {}
        """).strip()
        + "\n",
        encoding="utf-8",
    )

    r = run(
        [
            "python3",
            "src/governance/validate_ai_matrix_vs_registry.py",
            str(matrix),
            str(reg),
        ]
    )
    assert r.returncode == 2
    assert "REGISTRY_REFERENCE_DRIFT" in (r.stdout + r.stderr)
