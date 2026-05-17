"""Static contract for Shadow 24/7 Futures executable-start template (runbook §3b, no runtime).

This test locks the markdown safety boundary in ``PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md``.
It must stay import-light and must not invoke subprocess/network.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path("docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md")
CONTRACT_FULL = REPO_ROOT / CONTRACT_PATH


def _read_contract_text() -> str:
    assert CONTRACT_FULL.is_file(), f"missing canonical runbook owner: {CONTRACT_PATH}"
    return CONTRACT_FULL.read_text(encoding="utf-8")


def _extract_boundary_section_v0(full: str) -> str:
    start = "## 3b. Shadow 24/7 Futures executable command template boundary"
    end = "## 4. Status model"
    assert start in full, "§3b heading missing — merge runbook boundary before widening contract"
    assert end in full, "## 4. Status model anchor missing — cannot extract §3b slab"
    i = full.index(start)
    j = full.index(end, i)
    return full[i:j]


def test_shadow_247_futures_executable_start_boundary_has_canonical_owner_path() -> None:
    """Canonical runbook owner must remain the preflight contract path."""
    assert CONTRACT_FULL.resolve().is_relative_to(REPO_ROOT.resolve())
    assert (
        CONTRACT_FULL
        == REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
    )


def test_shadow_247_futures_executable_command_template_boundary_contract_v0() -> None:
    """Offline assertions for §3b — future executable start-path safety (no daemon implied)."""
    slab = _extract_boundary_section_v0(_read_contract_text())

    # 10 — docs do not confer execution approval / activation authority.
    assert "keine Ausführungsfreigabe" in slab

    # 1 fail-closed / default-off scaffolding
    assert "`DO_NOT_RUN_YET`" in slab or "```DO_NOT_RUN_YET" in slab
    assert "exit 64" in slab
    assert "PLANNING SURFACE ONLY" in slab

    # 2 explicit no-live
    assert "**Kein Live**" in slab or "Kein Live" in slab
    assert "PT_LIVE_ENABLED" in slab

    # 3 explicit no-testnet unless separately gated
    assert "PT_TESTNET_ENABLED" in slab
    assert "separately approved gate" in slab

    # 4 no broker/private endpoint/order submission
    assert "PT_BROKER_ENABLED" in slab
    assert "PT_ORDER_SUBMISSION_ENABLED" in slab
    assert "PT_PRIVATE_EXCHANGE_ENDPOINTS_ENABLED" in slab

    # 5 Futures/perpetual scope placeholders
    assert "PLACEHOLDER_SHADOW_FUTURES_PERP_REVIEW_REQUIRED" in slab
    assert "Governance-definierter Job-Satz" in slab or "perpetual" in slab.lower()

    # 6 evidence under /tmp/peak_trade_*
    assert "/tmp/peak_trade_" in slab
    assert "PT_EVIDENCE_ROOT" in slab

    # 7 bounded supervisor / timeout surface
    assert "scripts&#47;ops&#47;run_with_timeout.py" in slab
    assert "PT_MAX_RUNTIME_SECONDS" in slab

    # 8 abort/stop criteria section
    assert "Abort / STOP-Kriterien" in slab

    # 9 explicit future operator confirmation / gate language
    assert "explizite Operator-Review" in slab
    assert "future operator execution gate" in slab
