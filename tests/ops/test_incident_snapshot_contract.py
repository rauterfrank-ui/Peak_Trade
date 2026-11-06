from pathlib import Path

SCRIPT = Path("scripts/ops/build_incident_snapshot.sh")


def test_contract_keywords_present():
    text = SCRIPT.read_text(encoding="utf-8")
    required = [
        "manifest.json",
        "SHA256SUMS.txt",
        "incident_summary.json",
        "incident_summary.md",
        "STRICT",
        "INCIDENT_SLUG",
        "__MISSING__",
        "NO_TRADE default preserved",
        "incident_",
    ]
    for needle in required:
        assert needle in text, f"missing contract token: {needle}"
