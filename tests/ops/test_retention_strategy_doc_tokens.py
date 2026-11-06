"""Contract tests for docs/ops/runbooks/retention_strategy.md."""

from pathlib import Path

DOC = Path("docs/ops/runbooks/retention_strategy.md")


def test_doc_exists():
    assert DOC.exists(), f"missing doc: {DOC}"


def test_contract_keywords_present():
    text = DOC.read_text(encoding="utf-8")
    required = [
        "Retention-Fenster",
        "Integrität",
        "rerun",
        "verify",
        "GitHub Artifacts",
        "Long-Term Storage",
        "export-pack-verify",
        "out&#47;ops&#47;",
    ]
    for needle in required:
        assert needle in text, f"missing contract token: {needle}"
