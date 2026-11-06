from __future__ import annotations

from pathlib import Path


def test_p128_stub_exists() -> None:
    assert Path("src/execution/networked/transport_stub_v1.py").is_file()


def test_p128_docs_exist() -> None:
    assert Path("docs/analysis/p128/README.md").is_file()
