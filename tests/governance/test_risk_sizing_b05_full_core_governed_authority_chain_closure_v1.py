"""B05 Full-Core governed authority-chain closure contract tests."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_JSON = (
    REPO_ROOT
    / "config/governance/risk_sizing_b05_full_core_governed_authority_chain_closure_v1.json"
)
CONTRACT_DOC = (
    REPO_ROOT / "docs/governance/RISK_SIZING_B05_FULL_CORE_GOVERNED_AUTHORITY_CHAIN_CLOSURE_V1.md"
)
AUTH_JSON = REPO_ROOT / "config/governance/risk_sizing_authority_decision_contract_freeze_v1.json"
ADAPTER_JSON = (
    REPO_ROOT
    / "config/governance/risk_sizing_governed_producer_observation_adapter_contract_v1.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_closure_contract_three_domains_closed_companion_untouched() -> None:
    payload = _load(CONTRACT_JSON)
    markers = payload["markers"]
    assert markers["B05_FULL_CORE_AUTHORITY_CHAIN_VERDICT"] == "CLOSED"
    assert markers["COMPANION_C2_TOUCHED"] is False
    assert markers["FRACTION_TO_UNITS_TOUCHED"] is False
    assert markers["ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED"] is True
    assert markers["REFERENCE_PRICE_AUTHORITY_CHAIN_CLOSED"] is True
    assert markers["INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED"] is True
    assert markers["AUTHORITY_BINDING_IMPLEMENTED"] is True
    for domain in ("ACCOUNT_EQUITY", "REFERENCE_PRICE", "INSTRUMENT_METADATA"):
        row = payload["domain_closures"][domain]
        assert row["authority_chain_closed"] is True
        assert row["authority_binding_implemented"] is True
        assert row["governed_producer_created"] is True


def test_authority_freeze_and_adapter_bind_closure_ref() -> None:
    closure_ref = (
        "config/governance/risk_sizing_b05_full_core_governed_authority_chain_closure_v1.json"
    )
    auth = _load(AUTH_JSON)
    assert auth["markers"]["B05_FULL_CORE_AUTHORITY_CHAIN_VERDICT"] == "CLOSED"
    assert auth["markers"]["EXPECTED_AUTHORITY_CHAIN_CLOSED_COUNT"] == 3
    assert auth["b05_full_core_authority_chain_closure_ref"] == closure_ref
    adapter = _load(ADAPTER_JSON)
    assert adapter["b05_full_core_authority_chain_closure_ref"] == closure_ref
    assert adapter["markers"]["EXPECTED_AUTHORITY_CHAIN_CLOSED_COUNT"] == 3


def test_doc_markers_present() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    assert "B05_FULL_CORE_AUTHORITY_CHAIN_VERDICT=CLOSED" in text
    assert "COMPANION_C2_STATUS=UNRESOLVED" in text
    assert "ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED=true" in text
    assert "CONVERSION_READY=false" in text
