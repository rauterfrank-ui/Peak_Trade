from __future__ import annotations

from pathlib import Path

from src.aiops.p7.reconciliation import reconcile_p7_outdir


def test_reconcile_p7_outdir_smoke(tmp_path: Path) -> None:
    p7 = tmp_path / "p7"
    p7.mkdir()

    (p7 / "p7_fills.json").write_text("[]", encoding="utf-8")
    (p7 / "p7_account.json").write_text('{"equity": 1000.0}', encoding="utf-8")
    (p7 / "p7_evidence_manifest.json").write_text(
        '{"artifacts":["p7_fills.json","p7_account.json","p7_evidence_manifest.json"]}',
        encoding="utf-8",
    )

    res = reconcile_p7_outdir(p7)
    assert res.ok
    assert res.metrics["fills_count"] == 0


def test_reconcile_missing_files_fails(tmp_path: Path) -> None:
    p7 = tmp_path / "p7"
    p7.mkdir()

    res = reconcile_p7_outdir(p7)
    assert not res.ok
    assert any(i.code == "MISSING_FILE" for i in res.issues)
