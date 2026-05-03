"""Contract tests for research evidence layout (v0).

Uses only ``tmp_path`` — no repo-root artifacts, ``write_meta``, git, or network.

Prod module (unchanged): ``src.ops.evidence``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.evidence import EVIDENCE_LAYOUT, ensure_evidence_dirs


def test_evidence_layout_public_sequence_contract_v0() -> None:
    assert list(EVIDENCE_LAYOUT) == [
        "meta.json",
        "env",
        "logs",
        "reports",
        "plots",
        "results",
    ]


@pytest.mark.parametrize("name", list(EVIDENCE_LAYOUT))
def test_evidence_layout_entries_are_stable_non_empty_contract_v0(name: str) -> None:
    assert name.strip() == name
    assert len(name) > 0


def test_ensure_evidence_dirs_returns_keys_and_dirs_contract_v0(tmp_path: Path) -> None:
    base = tmp_path / "run_a"
    out = ensure_evidence_dirs(base)

    assert list(out.keys()) == list(EVIDENCE_LAYOUT)
    assert base.exists() and base.is_dir()

    for name, p in out.items():
        assert p == base / name

    meta = out["meta.json"]
    assert meta.parent == base and not meta.is_file()
    assert not meta.exists()

    for name in ("env", "logs", "reports", "plots", "results"):
        slot = out[name]
        assert slot.is_dir()


def test_ensure_evidence_dirs_idempotent_contract_v0(tmp_path: Path) -> None:
    base = tmp_path / "run_b"
    first = ensure_evidence_dirs(base)
    second = ensure_evidence_dirs(base)

    assert list(first.keys()) == list(second.keys())
    for k in first:
        assert first[k].resolve() == second[k].resolve()

    assert (base / "env").is_dir()
    meta = base / "meta.json"
    assert not meta.exists()
