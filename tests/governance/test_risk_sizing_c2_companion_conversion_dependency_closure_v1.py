"""C2 Companion conversion dependency closure v1 governance tests."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLOSURE_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_c2_companion_conversion_dependency_closure_v1.json"
)
CONTRACT_JSON = REPO_ROOT / "config/governance/companion_fraction_to_units_contract_v1.json"
CANONICAL_C2_JSON = (
    REPO_ROOT / "config/governance/risk_sizing_c2_canonical_risk_sizing_authority_closure_v1.json"
)
PROVENANCE_JSON = (
    REPO_ROOT / "config/governance/risk_sizing_productive_input_provenance_binding_v1.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_dependency_closure_verdict_and_ready_gate() -> None:
    payload = _load(CLOSURE_JSON)
    assert payload["verdict"]["conversion_ready"] is True
    assert payload["verdict"]["owner_decision_required"] is False
    assert payload["verdict"]["runtime_conversion_implemented"] is False
    assert payload["equity_binding"]["equity_input_proven"] is True
    assert payload["reference_price_binding"]["reference_price_input_proven"] is True
    assert payload["instrument_metadata_binding"]["instrument_metadata_input_proven"] is True
    assert payload["reference_price_binding"]["candle_close_permitted"] is False
    inv = payload["authority_invariants"]
    assert inv["duplicate_capital_authority_count"] == 0
    assert inv["duplicate_price_authority_count"] == 0
    assert inv["c2_authority_added"] is False


def test_companion_fraction_to_units_contract_algebra() -> None:
    contract = _load(CONTRACT_JSON)
    assert contract["input_unit"] == "FRACTION_DECIMAL_0_1"
    assert contract["output_unit"] == "QUANTITY_BASE_UNITS"
    assert contract["reference_price_class"] == "mark_price"
    assert contract["leverage_role"] == "NONE"
    assert contract["authority_added"] is False
    assert "start_balance" in contract["forbidden_inputs"]


def test_canonical_c2_and_provenance_align_on_conversion_ready() -> None:
    c2 = _load(CANONICAL_C2_JSON)
    assert c2["verdict"]["conversion_ready"] is True
    assert c2["companion_c2"]["fraction_to_units_runtime_implemented"] is False
    prov = _load(PROVENANCE_JSON)
    assert prov["markers"]["CONVERSION_READY"] is True
    assert prov["companion_conversion_input_binding"]["conversion_ready"] is True
    assert prov["markers"]["COMPANION_RUNTIME_CONVERSION_PRESENT"] is False


def test_shadow_live_still_pass_fraction_unchanged() -> None:
    shadow = (REPO_ROOT / "src/live/shadow_session.py").read_text(encoding="utf-8")
    live = (REPO_ROOT / "src/execution/live_session.py").read_text(encoding="utf-8")
    assert "position_size = self._shadow_cfg.position_fraction" in shadow
    assert "position_size=self._config.position_fraction" in live
