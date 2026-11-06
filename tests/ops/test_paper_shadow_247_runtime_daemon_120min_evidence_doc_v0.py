from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"


def test_paper_only_runtime_daemon_120min_evidence_is_documented_as_non_authorizing() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "Paper-only Runtime Daemon 120-Minute Stability Evidence v0" in text
    assert "`paper_runtime`" in text
    assert "`paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0`" in text
    assert "`tests/fixtures/p7/paper_run_high_vol_no_trade_v0.json`" in text
    assert "bounded runtime: 7200 seconds" in text
    assert "runtime job mentions: 3" in text
    assert "no-due-job observations: 239" in text
    assert "error mentions: 0" in text
    assert "fills count: 0" in text
    assert "account cash: 1000.0" in text
    assert "positions shape: `{}`" in text
    assert "flat positions accepted: `true`" in text
    assert "post-run preflight status: `BLOCKED`" in text
    assert "`dry_activation_readiness.ready`: `false`" in text
    assert "This evidence is non-authorizing." in text


def test_paper_only_runtime_daemon_120min_evidence_documents_flat_positions_shape() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "The empty positions object `{}` is accepted as the flat position representation" in text
    assert "there were no fills and the account remained flat" in text
    assert "equivalent to no open BTC exposure" in text
    assert "fixture-level expectation may name `BTC: 0.0`" in text


def test_paper_only_runtime_daemon_120min_evidence_does_not_claim_live_readiness() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    required_denials = (
        "It does not prove multi-run Paper runtime stability",
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
