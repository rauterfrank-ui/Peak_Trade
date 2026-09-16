"""Schema/marker tests for Cap 6.3 tick/lot/ctVal/price-scale metadata authority v1."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = REPO_ROOT / "docs/ops/specs/CAP63_TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY_V1.md"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"


def _contract_text() -> str:
    return CONTRACT.read_text(encoding="utf-8")


def _runbook_text() -> str:
    return RUNBOOK.read_text(encoding="utf-8")


def test_metadata_authority_contract_file_exists() -> None:
    assert CONTRACT.is_file()


def test_owner_model_reuses_surfaces_without_inventing_owner() -> None:
    text = _contract_text()
    assert "OWNER_MODEL=REUSE_EXISTING_PRODUCER_SURFACES_WITHOUT_PARALLEL_SSOT" in text
    assert "OWNER_MODEL_PERSISTED=true" in text
    assert "TICK_LOT_CTVAL_PRICE_SCALE_METADATA_CONSUMER_OWNER=UNINVENTED" in text
    assert "TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY=AUTHORITY_MISSING" in text
    assert "PARALLEL_SSOT_CREATED=false" in text
    assert "VENUE_RAW_FACT_EQUALS_CAP63_AUTHORITY=false" in text
    assert "CAP21_NORMALIZATION_OR_ELIGIBILITY_EQUALS_CAP63_METADATA_OWNER=false" in text
    assert "CANARY_CONSUMPTION_EQUALS_CAP63_OWNER=false" in text
    assert "GOLDEN_VECTOR_EQUALS_METADATA_AUTHORITY=false" in text


def test_named_tokens_keep_later_bind_open() -> None:
    text = _contract_text()
    assert "TICKSZ_OQ_C1_C2=NOT_REQUIRED_FOR_CAP63" in text
    assert "TICKSZ_LATER_RUNTIME_BIND=OPEN" in text
    assert "TICKSZ_CAP63_CLASS=OPEN" in text
    assert "LOTSZ_OQ_C1_C2=NOT_REQUIRED_FOR_CAP63" in text
    assert "LOTSZ_LATER_RUNTIME_BIND=OPEN" in text
    assert "LOTSZ_CAP63_CLASS=OPEN" in text
    assert "CTVAL_OQ_C1_C2=NOT_REQUIRED_FOR_CAP63" in text
    assert "CTVAL_LATER_RUNTIME_BIND=OPEN" in text
    assert "CTVAL_CAP63_CLASS=OPEN" in text
    assert "PRICE_SCALE_OQ_C1_C2=NOT_REQUIRED_FOR_CAP63" in text
    assert "PRICE_SCALE_LATER_RUNTIME_BIND=OPEN" in text
    assert "PRICE_SCALE_CAP63_CLASS=OPEN" in text
    assert "PRICE_SCALE_FIELD_IDENTITY=OPEN" in text
    assert "PRICE_SCALE_EQUALS_TICKSZ=false" in text


def test_e_edges_are_not_silently_closed() -> None:
    text = _contract_text()
    assert "E1_STATUS=OWNER_MODEL_PERSISTED_CONSUMER_OWNER_UNINVENTED" in text
    assert "E2_STATUS=LATER_BIND_FIELD_SUBSET_OPEN" in text
    assert "E3_STATUS=PRICE_SCALE_FIELD_IDENTITY_OPEN" in text
    assert "E4_STATUS=DOWNSTREAM_OPEN_IDENTITY_BINDING_NOT_ADJUDICATED" in text
    assert "E5_STATUS=DOWNSTREAM_OPEN_FRESHNESS_POLICY_NOT_CHOSEN" in text
    assert "E6_STATUS=DOWNSTREAM_OPEN_ADMISSIBILITY_CONSUMER_CONTRACT_UNBOUND" in text
    assert "E7_STATUS=DOWNSTREAM_OPEN_NON_PROMOTION_MUST_REMAIN_IN_LATER_SLICES" in text


def test_implementation_and_model_c_remain_unauthorized() -> None:
    text = _contract_text()
    assert "TICK_LOT_CTVAL_PRICE_SCALE_IMPLEMENTATION_AUTHORIZED=false" in text
    assert "CURRENT_IMPLEMENTATION_AUTHORIZED=false" in text
    assert "MODEL_C_BOUND=false" in text
    assert "MODEL_C_RUNTIME_BIND_AUTHORIZED=false" in text
    assert "QUANTIZATION_RULE_AUTHORIZED=false" in text
    assert "ROUNDING_RULE_AUTHORIZED=false" in text
    assert "CONVERSION_FORMULA_AUTHORIZED=false" in text
    assert "CURRENT_CANONICAL_MODEL=MODEL_B" in text
    assert "up_distance=200.0" in text


def test_pr6547_is_merged_canonical_pre_metadata_validation() -> None:
    text = _contract_text()
    assert "PR6547_STATUS=MERGED_CANONICAL_PRE_METADATA_VALIDATION_PERSIST" in text
    assert "PR6547_ALTERED=false" in text
    assert "PR6547_MERGED=true" in text
    assert "CROSS_INSTRUMENT_VALIDATION_GO_CONSUMED_BY_THIS_PERSIST=false" in text
    assert "ORIGIN_MAIN_VALIDATION_GO_REMAINS_UNCONSUMED=false" in text


def test_runbook_persist_matches_contract_markers() -> None:
    text = _runbook_text()
    assert "### 9.2.9 Cap 6.3 tick/lot/ctVal/price-scale metadata authority owner contract" in text
    assert "### 9.2.8 Cap 6.3 dynamic derivation cross-instrument validation" in text
    assert (
        "OWNER_GO=OWNER_GO_BOUNDED_CAP63_TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY_OWNER_CONTRACT_PERSIST_DOCS_ONLY_V1"
        in text
    )
    assert "OWNER_MODEL=REUSE_EXISTING_PRODUCER_SURFACES_WITHOUT_PARALLEL_SSOT" in text
    assert "TICK_LOT_CTVAL_PRICE_SCALE_IMPLEMENTATION_AUTHORIZED=false" in text
    assert "MODEL_C_BOUND=false" in text
    assert (
        "EXACT_NEXT_OWNER_GO_TOKEN=OWNER_GO_BOUNDED_CAP63_TICK_LOT_CTVAL_PRICE_SCALE_METADATA_IDENTITY_BINDING_V1"
        in text
    )
    assert "NEXT_NAMED_OPEN_GATE=CAP63_METADATA_IDENTITY_BINDING_UNBOUND" in text
    assert "ORIGIN_MAIN_VALIDATION_GO_REMAINS_UNCONSUMED=false" in text
