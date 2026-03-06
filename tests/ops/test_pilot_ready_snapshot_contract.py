from pathlib import Path

SCRIPT = Path("scripts/ops/build_pilot_ready_snapshot.sh")


def test_contract_keywords_present():
    text = SCRIPT.read_text(encoding="utf-8")
    required = [
        "manifest.json",
        "SHA256SUMS.txt",
        "snapshot_summary.json",
        "snapshot_summary.md",
        "STRICT",
        "__MISSING__",
        "NO_TRADE default preserved",
        "pilot_ready_snapshot_",
    ]
    for needle in required:
        assert needle in text, f"missing contract token: {needle}"
