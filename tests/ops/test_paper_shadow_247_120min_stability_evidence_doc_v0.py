from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"


def test_paper_shadow_247_120min_stability_evidence_is_documented_as_non_authorizing() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "Paper-only Tag-Gated Scheduler Daemon Stability Evidence v0" in text
    assert "`paper_shadow_247`" in text
    assert "`paper_shadow_247_paper_only_preflight_status_v0`" in text
    assert "bounded runtime: 7200 seconds" in text
    assert "scheduler iterations: 240" in text
    assert "executed jobs: 1" in text
    assert "no-due-job observations: 239" in text
    assert "error mentions: 0" in text
    assert "post-run preflight status: `BLOCKED`" in text
    assert "`dry_activation_readiness.ready`: `false`" in text
    assert "This evidence is non-authorizing." in text


def test_paper_shadow_247_120min_stability_evidence_does_not_claim_runtime_or_live_readiness() -> (
    None
):
    text = RUNBOOK.read_text(encoding="utf-8")

    required_denials = (
        "It does not prove Paper runtime stability",
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
