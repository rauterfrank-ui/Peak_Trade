"""Z2N generic non-SSOT contract for untracked marketing fee-page dumps.

Read-only regression contract. Does not adopt fee rates, create a fee
SSOT, authorize Live, Testnet, Canary execute, funding, orders, or
COVER_USDC instantiation. Does not commit, push, or track the dumps.
Does not bind FND-012 or Master Runbook §4.13.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
Z2N_EVIDENCE_ROOT = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_z2m_fee_reserve_rates_rebind_get_v1"
    / "20260819T102325Z"
)
DUMP_FILES = (
    REPO_ROOT / "okx-en-eu-fees.yml",
    REPO_ROOT / "okx-en-eu-fees-futures.yml",
)
DUMP_NAMES = {path.name for path in DUMP_FILES}
Z2N_HEADING = "### 11.13.5.Z2N Fresh authenticated fee-reserve rates rebind GET evidence persist"
DIRTY_SECTION_4_13_FND012_HEADING = (
    "## 4.13 Untracked OKX Europe fee-page YAML dumps are non-SSOT (FND-012)"
)
OPERATIVE_SURFACES = ("src", "scripts", "config")


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2n_section(text: str) -> str:
    start = text.find(Z2N_HEADING)
    assert start >= 0, "missing §11.13.5.Z2N heading"
    end = text.find("## 11.14 Live order and economic evidence ladder", start)
    assert end > start, "missing §11.14 boundary after Z2N"
    return text[start:end]


def _git_ls_files(path: Path) -> str:
    result = subprocess.run(
        ["git", "ls-files", "--", path.name],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _operational_references() -> set[Path]:
    hits: set[Path] = set()
    this_file = Path(__file__).resolve()
    for surface in OPERATIVE_SURFACES:
        root = REPO_ROOT / surface
        if not root.exists():
            continue
        for candidate in root.rglob("*"):
            if not candidate.is_file():
                continue
            if candidate.resolve() == this_file:
                continue
            text = candidate.read_text(encoding="utf-8", errors="replace")
            if any(name in text for name in DUMP_NAMES):
                hits.add(candidate.resolve())
    return hits


def test_dirty_fnd_012_section_is_not_canon_owner() -> None:
    text = _read(MASTER_RUNBOOK)
    assert DIRTY_SECTION_4_13_FND012_HEADING not in text
    assert "FND_012_STATUS=RESOLVED" not in text
    assert "SURFACE_ID=OF-01-OKX-EN-EU-FEES-YML" not in text
    assert "SURFACE_ID=OF-02-OKX-EN-EU-FEES-FUTURES-YML" not in text
    assert "## 4.13 Phase-17 LIVE-unimplemented header superseded (FND-015)" in text


def test_root_okx_fee_ymls_remain_untracked_unimported_and_non_operative() -> None:
    for path in DUMP_FILES:
        assert _git_ls_files(path) == ""
        if path.exists():
            text = _read(path)
            assert text.lstrip().startswith("- generic")
            assert "[ref=" in text
            assert "/en-eu/fees" in text
            assert "maker_fee:" not in text
            assert "taker_fee:" not in text
            assert "makerFee:" not in text
            assert "takerFee:" not in text
    assert _operational_references() == set()


def test_z2n_persisted_trade_fee_pack_remains_fee_rate_ssot() -> None:
    section = _z2n_section(_read(MASTER_RUNBOOK))
    assert "FEE_RESERVE_RATES_REBIND_GET_EVIDENCE_BOUND=true" in section
    assert "FEE_RESERVE_RATES_ADJUDICATION=PROVEN" in section
    assert "LIVE_AUTHORIZED=false" in section
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in section
    assert "NUMERIC_FEE_RESERVE_STATUS=UNINSTANTIATED" in section
    assert "LIVE_AUTHORIZED=true" not in section
    snapshot = _read(Z2N_EVIDENCE_ROOT / "GET_SNAPSHOT.sanitized.json")
    assert '"takerUSDC": "-0.0005"' in snapshot
    assert '"makerUSDC": "-0.0002"' in snapshot
    for path in DUMP_FILES:
        assert path.resolve() != Z2N_EVIDENCE_ROOT.resolve()
        assert path.name not in snapshot
