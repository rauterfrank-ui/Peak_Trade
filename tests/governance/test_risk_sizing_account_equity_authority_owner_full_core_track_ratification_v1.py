"""OWNER_GO ratification contract — Full-Core B05 account equity authority owner."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

RATIFICATION_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_account_equity_authority_owner_full_core_track_ratification_v1.json"
)
RATIFICATION_DOC = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "RISK_SIZING_ACCOUNT_EQUITY_AUTHORITY_OWNER_FULL_CORE_TRACK_RATIFICATION_V1.md"
)

OWNER = "ops.governed_productive_account_equity_authority_producer_v1"


def _load() -> dict:
    return json.loads(RATIFICATION_JSON.read_text(encoding="utf-8"))


def test_owner_go_consumed_and_single_ratified_owner() -> None:
    payload = _load()
    decision = payload["decision_authority"]
    assert decision["owner_go_status"] == "CONSUMED"
    rat = payload["ratification"]
    assert rat["account_equity_authority_owner"] == OWNER
    assert rat["scope_track"] == "FULL_CORE"
    assert rat["dimension_id"] == "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
    assert rat["prior_b05_pin_superseded"] == "UNRESOLVED"
    markers = payload["markers"]
    assert markers["ACCOUNT_EQUITY_AUTHORITY_OWNER"] == OWNER
    assert markers["FULL_CORE_ACCOUNT_EQUITY_AUTHORITY_OWNER_RATIFIED"] is True
    assert markers["GOVERNED_PRODUCER_CREATED"] is True
    assert markers["PRODUCER_IMPLEMENTATION_PRESENT"] is True
    assert markers["ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED"] is True
    assert markers["CONVERSION_READY"] is False
    assert markers["C2_EQUITY_DOMAIN_VERDICT"] == "PARTIAL"
    assert markers["COMPANION_HANDOFF_STATUS"] == "NO_CONVERSION_HANDOFF_ON_COMPANION_PATH"


def test_doc_markers_and_ssot_path() -> None:
    payload = _load()
    assert payload["ssot_doc"] == (
        "docs/governance/RISK_SIZING_ACCOUNT_EQUITY_AUTHORITY_OWNER_FULL_CORE_TRACK_RATIFICATION_V1.md"
    )
    text = RATIFICATION_DOC.read_text(encoding="utf-8")
    assert "OWNER_GO_STATUS=CONSUMED" in text
    assert f"ACCOUNT_EQUITY_AUTHORITY_OWNER={OWNER}" in text
    assert "GOVERNED_PRODUCER_CREATED=false" in text
