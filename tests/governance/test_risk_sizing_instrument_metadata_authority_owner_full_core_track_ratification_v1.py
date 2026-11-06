"""OWNER_GO ratification contract — Full-Core B05 instrument metadata authority owner."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

RATIFICATION_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_instrument_metadata_authority_owner_full_core_track_ratification_v1.json"
)
RATIFICATION_DOC = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "RISK_SIZING_INSTRUMENT_METADATA_AUTHORITY_OWNER_FULL_CORE_TRACK_RATIFICATION_V1.md"
)
AUTH_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_authority_decision_contract_freeze_v1.json"
)

OWNER = "ops.governed_productive_instrument_metadata_authority_producer_v1"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_owner_go_consumed_and_quantity_unit_semantics() -> None:
    payload = _load(RATIFICATION_JSON)
    decision = payload["decision_authority"]
    assert decision["owner_go_status"] == "CONSUMED"
    rat = payload["ratification"]
    assert rat["instrument_metadata_authority_owner"] == OWNER
    assert rat["scope_track"] == "FULL_CORE"
    assert rat["dimension_id"] == "COMPLETE_INSTRUMENT_QUANTITY_CONSTRAINT_METADATA"
    markers = payload["markers"]
    assert markers["INSTRUMENT_METADATA_AUTHORITY_OWNER"] == OWNER
    assert markers["FULL_CORE_INSTRUMENT_METADATA_AUTHORITY_OWNER_RATIFIED"] is True
    assert markers["QUANTITY_UNIT_SEMANTICS_CLASS_RATIFIED"] == "CONTRACTS_SZ_LOT_STEP"
    assert markers["GOVERNED_PRODUCER_CREATED"] is True
    assert markers["PRODUCER_IMPLEMENTATION_PRESENT"] is True
    assert markers["CONVERSION_READY"] is False
    assert markers["C2_INSTRUMENT_METADATA_DOMAIN_VERDICT"] == "PARTIAL"


def test_authority_freeze_binds_full_core_instrument_owner() -> None:
    auth = _load(AUTH_JSON)
    assert auth["markers"]["INSTRUMENT_METADATA_AUTHORITY_OWNER"] == OWNER
    assert auth["markers"]["FULL_CORE_INSTRUMENT_METADATA_AUTHORITY_OWNER_RATIFIED"] is True


def test_doc_markers_and_ssot_path() -> None:
    payload = _load(RATIFICATION_JSON)
    text = RATIFICATION_DOC.read_text(encoding="utf-8")
    assert payload["ssot_doc"] in text or "RISK_SIZING_INSTRUMENT_METADATA" in text
    assert "OWNER_GO_STATUS=CONSUMED" in text
    assert f"INSTRUMENT_METADATA_AUTHORITY_OWNER={OWNER}" in text
    assert "QUANTITY_UNIT_SEMANTICS_CLASS_RATIFIED=CONTRACTS_SZ_LOT_STEP" in text
