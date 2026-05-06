from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"


def test_paper_only_runtime_min_daemon_120min_evidence_is_documented_as_non_authorizing() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "Paper-only Runtime-Min Daemon 120-Minute Stability Evidence v0" in text
    assert "`paper_runtime_min`" in text
    assert "`paper_shadow_247_paper_only_runtime_min_v0`" in text
    assert "`tests/fixtures/p7/paper_run_min_v0.json`" in text
    assert "bounded runtime: 7200 seconds" in text
    assert "error mentions: 0" in text
    assert "fills count: 2" in text
    assert "fill sides: `BUY`, `SELL`" in text
    assert "fill prices: `100.1`, `99.9`" in text
    assert "fill fees: `0.1001`, `0.0999`" in text
    assert "account cash: 999.6" in text
    assert "post-run preflight status: `BLOCKED`" in text
    assert "`dry_activation_readiness.ready`: `false`" in text
    assert "This evidence is non-authorizing." in text


def test_paper_only_runtime_min_daemon_120min_evidence_does_not_claim_live_readiness() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    required_denials = (
        "It does not prove multi-symbol Paper runtime stability",
        "longer-horizon Paper runtime stability",
        "Shadow runtime stability",
        "broker connectivity",
        "exchange connectivity",
        "order submission",
        "Testnet readiness",
        "Live readiness",
        "Do not use this evidence to authorize Testnet, Live, broker, exchange, or order paths.",
    )

    for denial in required_denials:
        assert denial in text
