from pathlib import Path


def test_monthly_digest_contract_files_exist_and_named() -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts/ops/registry_monthly_digest.py"
    runbook = root / "docs/ops/runbooks/registry_monthly_digest.md"
    assert script.exists()
    assert runbook.exists()
    txt = script.read_text(encoding="utf-8")
    assert "monthly_digest_latest.md" in txt
    assert "monthly_digest_latest.json" in txt
