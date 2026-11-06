"""Contract tests for R&D strategy status grammar v0 (DRIFT_B02)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.governance.rd_strategy_status_grammar_v0 import (
    CANONICAL_STATUSES,
    CONTRACT_ID,
    RdStrategyStatusGrammarError,
    assert_fehlende_features_consumes_grammar_v0,
    clear_rd_strategy_status_grammar_cache_v0,
    get_rd_strategy_status_grammar_v0,
    iter_rd_strategy_status_rows_v0,
    list_canonical_rd_strategy_statuses_v0,
    normalize_rd_strategy_status_v0,
    serialize_rd_strategy_status_inventory_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FEHLENDE = REPO_ROOT / "docs/features/FEHLENDE_FEATURES_PEAK_TRADE.md"
CONTRACT = REPO_ROOT / "docs/features/rd_strategy_status_grammar_v0.json"
OWNER_MODULE = REPO_ROOT / "src/governance/rd_strategy_status_grammar_v0.py"


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_rd_strategy_status_grammar_cache_v0()
    yield
    clear_rd_strategy_status_grammar_cache_v0()


def test_canonical_status_set_complete_and_ordered():
    assert list_canonical_rd_strategy_statuses_v0() == ("missing", "research-only", "stub")
    assert CANONICAL_STATUSES == {"stub", "research-only", "missing"}


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("stub", "stub"),
        ("research-only", "research-only"),
        ("missing", "missing"),
        ("research_only", "research-only"),
        ("RESEARCH ONLY", "research-only"),
        ("r_and_d", "research-only"),
        ("r&d", "research-only"),
        ("placeholder", "stub"),
        ("scaffold", "stub"),
        ("fehlt", "missing"),
        ("absent", "missing"),
        ("not_present", "missing"),
    ],
)
def test_legacy_alias_normalization(raw, expected):
    assert normalize_rd_strategy_status_v0(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "TODO",
        "todo",
        "NotImplemented",
        "NotImplementedError",
        "not implemented",
        "unknown-status",
        "implemented",
        "",
        "   ",
        None,
        123,
    ],
)
def test_ambiguous_empty_unknown_fail_closed(raw):
    with pytest.raises(RdStrategyStatusGrammarError):
        normalize_rd_strategy_status_v0(raw)  # type: ignore[arg-type]


def test_deterministic_serialization_stable():
    a = serialize_rd_strategy_status_inventory_v0()
    b = serialize_rd_strategy_status_inventory_v0()
    assert a == b
    assert a == (
        '[{"module_path":"src/strategies/bouchaud/bouchaud_microstructure_strategy.py",'
        '"registry_key":"bouchaud_microstructure","status":"research-only",'
        '"strategy_id":"bouchaud_microstructure"},'
        '{"module_path":"src/strategies/ehlers/ehlers_cycle_filter_strategy.py",'
        '"registry_key":"ehlers_cycle_filter","status":"research-only",'
        '"strategy_id":"ehlers_cycle_filter"},'
        '{"module_path":"src/strategies/lopez_de_prado/meta_labeling_strategy.py",'
        '"registry_key":"meta_labeling","status":"research-only",'
        '"strategy_id":"meta_labeling"},'
        '{"module_path":"src/strategies/gatheral_cont/vol_regime_overlay_strategy.py",'
        '"registry_key":"vol_regime_overlay","status":"research-only",'
        '"strategy_id":"vol_regime_overlay"}]'
    )


def test_producer_rows_all_research_only_and_modules_exist():
    rows = iter_rd_strategy_status_rows_v0()
    assert {r["strategy_id"] for r in rows} == {
        "ehlers_cycle_filter",
        "bouchaud_microstructure",
        "vol_regime_overlay",
        "meta_labeling",
    }
    for row in rows:
        assert row["status"] == "research-only"
        assert (REPO_ROOT / row["module_path"]).is_file()
        text = (REPO_ROOT / row["module_path"]).read_text(encoding="utf-8")
        assert "NotImplementedError" not in text


def test_fehlende_consumer_parity_and_no_stale_drift():
    text = FEHLENDE.read_text(encoding="utf-8")
    assert_fehlende_features_consumes_grammar_v0(text)
    assert "TODO/NotImplementedError (z. B. Ehlers" not in text
    assert "gibt Nullen zurück" not in text
    assert "gibt leeres DataFrame zurück" not in text


def test_single_canonical_owner_surfaces():
    payload = get_rd_strategy_status_grammar_v0()
    assert payload["contract_id"] == CONTRACT_ID
    assert payload["canonical_owner_module"].endswith("rd_strategy_status_grammar_v0.py")
    assert OWNER_MODULE.is_file()
    assert CONTRACT.is_file()
    # No second mapping table in owner module beyond loading the JSON SSOT.
    owner_src = OWNER_MODULE.read_text(encoding="utf-8")
    assert owner_src.count("legacy_aliases") <= 3


def test_no_direct_drift_mappings_in_fehlende_for_named_strategies():
    text = FEHLENDE.read_text(encoding="utf-8")
    # Direct drift mappings that B02 removed.
    assert "Einige Research-Strategien: TODO/NotImplementedError" not in text
