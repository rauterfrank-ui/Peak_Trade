"""OWNER_GO ratification contract — Full-Core B05 reference price authority owner."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

RATIFICATION_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_reference_price_authority_owner_full_core_track_ratification_v1.json"
)
RATIFICATION_DOC = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "RISK_SIZING_REFERENCE_PRICE_AUTHORITY_OWNER_FULL_CORE_TRACK_RATIFICATION_V1.md"
)
AUTH_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_authority_decision_contract_freeze_v1.json"
)

OWNER = "ops.governed_productive_reference_price_authority_producer_v1"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_owner_go_consumed_and_mark_price_semantics() -> None:
    payload = _load(RATIFICATION_JSON)
    decision = payload["decision_authority"]
    assert decision["owner_go_status"] == "CONSUMED"
    rat = payload["ratification"]
    assert rat["reference_price_authority_owner"] == OWNER
    assert rat["scope_track"] == "FULL_CORE"
    assert rat["price_semantics_class"] == "mark_price"
    assert rat["dimension_id"] == "INSTRUMENT_VENUE_TIME_BOUND_CONVERSION_REFERENCE_PRICE"
    markers = payload["markers"]
    assert markers["REFERENCE_PRICE_AUTHORITY_OWNER"] == OWNER
    assert markers["FULL_CORE_REFERENCE_PRICE_AUTHORITY_OWNER_RATIFIED"] is True
    assert markers["PRICE_SEMANTICS_CLASS_RATIFIED"] == "mark_price"
    assert markers["GOVERNED_PRODUCER_CREATED"] is False
    assert markers["INDEX_PX_NOT_REFERENCE_PRICE_AUTHORITY"] is True
    assert markers["CONVERSION_READY"] is False
    assert markers["C2_REFERENCE_PRICE_DOMAIN_VERDICT"] == "PARTIAL"


def test_authority_freeze_binds_full_core_reference_owner() -> None:
    auth = _load(AUTH_JSON)
    assert auth["markers"]["REFERENCE_PRICE_AUTHORITY_OWNER"] == OWNER
    assert auth["markers"]["FULL_CORE_REFERENCE_PRICE_AUTHORITY_OWNER_RATIFIED"] is True
    assert auth["markers"]["REFERENCE_PRICE_SEMANTICS_CLASS_RATIFIED"] == "mark_price"


def test_doc_markers_and_ssot_path() -> None:
    payload = _load(RATIFICATION_JSON)
    text = RATIFICATION_DOC.read_text(encoding="utf-8")
    assert payload["ssot_doc"] in text or "RISK_SIZING_REFERENCE_PRICE" in text
    assert "OWNER_GO_STATUS=CONSUMED" in text
    assert f"REFERENCE_PRICE_AUTHORITY_OWNER={OWNER}" in text
    assert "PRICE_SEMANTICS_CLASS_RATIFIED=mark_price" in text
