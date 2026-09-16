"""Schema/marker tests for Cap 6.3 cross-instrument validation protocol v1."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    REPO_ROOT / "docs/ops/specs/CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_PROTOCOL_V1.md"
)


def _text() -> str:
    return CONTRACT.read_text(encoding="utf-8")


def test_protocol_contract_file_exists() -> None:
    assert CONTRACT.is_file()


def test_protocol_owner_persisted_and_validation_not_performed() -> None:
    text = _text()
    assert "CROSS_INSTRUMENT_VALIDATION_PROTOCOL_OWNER=PERSISTED" in text
    assert "CROSS_INSTRUMENT_VALIDATION_PERFORMED=false" in text
    assert "CROSS_INSTRUMENT_VALIDATION_AUTHORIZED=false" in text
    assert "VALIDATION_EXECUTED=false" in text
    assert "VALIDATION_HARNESS_AUTHORIZED=false" in text
    assert "INSTRUMENT_GOLDEN_EVIDENCE_AUTHORIZED=false" in text


def test_selection_rule_references_cap23_and_defines_no_list() -> None:
    text = _text()
    assert "THIS_PROTOCOL_DEFINES_NO_INSTRUMENT_LIST=true" in text
    assert "SELECTION_OWNER=CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1" in text
    assert "CAP23_REMAINS_SOLE_PRODUCTIVE_SELECTION_OWNER=true" in text
    assert "NEW_INSTRUMENT_LIST_AUTHORIZED=false" in text
    assert "NEW_UNIVERSE_OWNER_AUTHORIZED=false" in text
    assert "CAP23_REWIRE_AUTHORIZED=false" in text


def test_band_provenance_reuses_runtime_scope_state() -> None:
    text = _text()
    assert (
        "BAND_FIELD_OWNER=trading.master_v2.double_play_state."
        "RuntimeScopeState.current_hysteresis_band" in text
    )
    assert "BAND_PRODUCER=trading.master_v2.double_play_state.update_dynamic_boundaries" in text
    assert "SYNTHETIC_BAND_SET_AS_PRODUCTIVE_AUTHORITY=FORBIDDEN" in text
    assert "GOLDEN_VECTORS_ARE_FORMULA_VECTORS_NOT_INSTRUMENT_UNIVERSE=true" in text


def test_pass_fail_is_pre_metadata_only() -> None:
    text = _text()
    assert "TICK_ALIGNMENT=NOT_IN_SCOPE" in text
    assert "LOT_ALIGNMENT=NOT_IN_SCOPE" in text
    assert "CTVAL_ALIGNMENT=NOT_IN_SCOPE" in text
    assert "PRICE_SCALE_ALIGNMENT=NOT_IN_SCOPE" in text
    assert "VENUE_EXECUTABILITY=NOT_IN_SCOPE" in text
    assert "METADATA_GATE_CONSUMED=false" in text
    assert "TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY=AUTHORITY_MISSING" in text
    assert "QUANTIZATION_RULE_AUTHORIZED=false" in text
    assert "ROUNDING_RULE_AUTHORIZED=false" in text


def test_evidence_is_not_trading_authority() -> None:
    text = _text()
    assert "EVIDENCE_AUTHORITY_EFFECT=NONE" in text
    assert "EVIDENCE_IS_NOT_TRADING_AUTHORITY=true" in text
    assert "THIS_PROTOCOL_PERSIST_CREATES_NO_VALIDATION_EVIDENCE=true" in text


def test_model_c_remains_unbound_and_next_go_token_unchanged() -> None:
    text = _text()
    assert "MODEL_C_BOUND=false" in text
    assert "MODEL_C_RUNTIME_BIND_AUTHORIZED=false" in text
    assert "DERIVATION_RUNTIME_BIND_AUTHORIZED=false" in text
    assert (
        "EXACT_NEXT_OWNER_GO_TOKEN=OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1"
        in text
    )
    assert "NEXT_OWNER_GO_CONSUMED=false" in text
    assert "TOKEN_RENAMED=false" in text
    assert "CURRENT_CANONICAL_MODEL=MODEL_B" in text
    assert "up_distance=200.0" in text
    assert "OD2_LAST_STEP=KEEP_BOUND_DESTINATION_PREFIX" in text
    assert "OD2_ARMED_RESIDUAL_MUTATION_AUTHORIZED=false" in text
