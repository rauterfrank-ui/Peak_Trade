"""Static contracts for OBL_B05 ENTRY_EXIT producer side-authority decision v1.

Inventory / classification / decision markers only.
No productive side emission; adapter must remain entry_side=NONE.
"""

from __future__ import annotations

import json
from pathlib import Path

import src.backtest.strategy_signal_suitability_agreement_adapter_v1 as adapter_mod
from src.backtest.strategy_signal_suitability_agreement_adapter_v1 import (
    normalize_strategy_signal_to_suitability_agreement_material_v1,
    resolve_strategy_signal_encoding_class_v1,
)
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyEntrySideCarrierV1,
    StrategySignalEncodingClassV1,
)
from tests.backtest.test_strategy_signal_suitability_agreement_adapter_v1 import (
    _binding,
    _provenance,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = (
    REPO_ROOT
    / "config"
    / "governance"
    / "obl_b05_entry_exit_producer_side_authority_decision_v1.json"
)
GOV_DOC = (
    REPO_ROOT / "docs" / "governance" / "OBL_B05_ENTRY_EXIT_PRODUCER_SIDE_AUTHORITY_DECISION_V1.md"
)
ADAPTER_SRC = REPO_ROOT / "src" / "backtest" / "strategy_signal_suitability_agreement_adapter_v1.py"

_ALLOWED_CLASSES = frozenset(
    {
        "CANONICAL_EXISTING_SIDE_AUTHORITY",
        "RATIFIABLE_PRODUCER_SEMANTICS",
        "EVENT_ONLY_NO_SIDE_AUTHORITY",
        "AMBIGUOUS_OR_CONTRADICTORY",
        "LEGACY_OR_SPECIALIST_ONLY",
    }
)


def _ssot() -> dict:
    return json.loads(SSOT_PATH.read_text(encoding="utf-8"))


def test_ssot_and_governance_doc_exist_with_decision_markers() -> None:
    assert SSOT_PATH.is_file()
    assert GOV_DOC.is_file()
    data = _ssot()
    body = GOV_DOC.read_text(encoding="utf-8")
    assert data["slice_id"] == "OBL_B05_ENTRY_EXIT_PRODUCER_SIDE_AUTHORITY_DECISION_V1"
    assert data["entry_exit_owner_set_closed"] is True
    assert data["productive_side_emission_changed"] is False
    assert data["bollinger_side_activated"] is False
    assert data["bollinger_entry_side_decision"] == "BLOCKED_AMBIGUITY"
    assert data["semantic_activation_requires_separate_go"] is True
    assert "PRODUCER_SIDE_AUTHORITY_AUDIT_COMPLETE" in body
    assert "BOLLINGER_ENTRY_SIDE_DECISION" in body
    assert "BLOCKED_AMBIGUITY" in body
    assert "DOCS_TOKEN_OBL_B05_ENTRY_EXIT_PRODUCER_SIDE_AUTHORITY_DECISION_V1" in body


def test_closed_owner_set_matches_adapter_frozenset() -> None:
    data = _ssot()
    ssot_owners = frozenset(data["closed_owner_set"])
    adapter_owners = frozenset(adapter_mod._ENTRY_EXIT_EVENT_OWNERS)
    assert ssot_owners == adapter_owners
    producer_ids = {row["producer_id"] for row in data["producers"]}
    assert producer_ids == adapter_owners
    assert len(adapter_owners) == 7


def test_every_owner_resolves_to_entry_exit_encoding() -> None:
    for producer_id in sorted(adapter_mod._ENTRY_EXIT_EVENT_OWNERS):
        assert (
            resolve_strategy_signal_encoding_class_v1(producer_id)
            is StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1
        )


def test_producer_rows_have_required_fields_and_allowed_classes() -> None:
    data = _ssot()
    required = {
        "producer_id",
        "encoding",
        "raw_output_domain",
        "meaning_plus_one",
        "meaning_minus_one",
        "meaning_zero",
        "entry_condition",
        "exit_condition",
        "short_entry_condition_present",
        "canonical_side_authority_present",
        "candidate_entry_side",
        "authority_source",
        "class",
        "confidence",
        "ambiguity_or_contradiction",
        "recommended_disposition",
    }
    for row in data["producers"]:
        missing = required - set(row)
        assert not missing, f"{row.get('producer_id')}: missing {sorted(missing)}"
        assert row["encoding"] == "ENTRY_EXIT_EVENT_V1"
        assert row["class"] in _ALLOWED_CLASSES
        assert row["canonical_side_authority_present"] is False
        assert row["authority_source"] == "NONE"
        assert row["short_entry_condition_present"] is False
        assert row["meaning_plus_one"] == "ENTRY_EVENT"
        assert row["meaning_minus_one"] == "EXIT_EVENT"
        assert "KEEP_NONE" in row["recommended_disposition"]


def test_bollinger_decision_blocked_ambiguity_and_not_activated() -> None:
    data = _ssot()
    assert data["bollinger_entry_side_decision"] == "BLOCKED_AMBIGUITY"
    bollinger = next(r for r in data["producers"] if r["producer_id"] == "bollinger_bands")
    assert bollinger["class"] == "AMBIGUOUS_OR_CONTRADICTORY"
    assert bollinger["activation_slice_eligible"] is False
    assert bollinger["recommended_disposition"] == "KEEP_NONE"
    assert data["bollinger_side_activated"] is False


def test_no_canonical_existing_side_authority_in_inventory() -> None:
    data = _ssot()
    assert all(row["class"] != "CANONICAL_EXISTING_SIDE_AUTHORITY" for row in data["producers"])


def test_adapter_source_does_not_emit_long_or_short_entry_side() -> None:
    source = ADAPTER_SRC.read_text(encoding="utf-8")
    assert "entry_side = StrategyEntrySideCarrierV1.NONE" in source
    assert "StrategyEntrySideCarrierV1.LONG" not in source
    assert "StrategyEntrySideCarrierV1.SHORT" not in source


def test_productive_adapter_still_defaults_bollinger_entry_side_none() -> None:
    material = normalize_strategy_signal_to_suitability_agreement_material_v1(
        _binding(
            [1, 0, -1],
            provenance=_provenance(
                configured_strategy_id="bollinger_bands",
                executed_strategy_id="bollinger_bands",
            ),
        ),
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=0,
    )
    assert material.encoding_class is StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1
    assert material.entry_side is StrategyEntrySideCarrierV1.NONE


def test_conflict_provenance_and_future_slices_present() -> None:
    data = _ssot()
    assert len(data["conflict_provenance"]) >= 5
    assert len(data["future_activation_slices"]) >= 4
    ids = {item["id"] for item in data["conflict_provenance"]}
    assert "CP02_BOLLINGER_CLASS_DOC_LONG_VS_METHOD_ENTRY" in ids
