"""B05 preselection-only semantic boundary enforcement (Cap 2.2 → Full-Core handoff)."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, fields
from pathlib import Path

import pytest

from src.governance.capital_risk_sizing_v1 import CapitalRiskSizingDecisionV1
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from src.ops.ranking_universe_to_full_core_ssf_handoff_contract_v1 import (
    RankingUniverseToFullCoreSsfHandoffError,
    assert_handoff_invariants_v1,
    validate_replay_drops_handoff_provenance_v1,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
)
from src.ops.single_selected_future_policy_v1.selection_v1 import (
    produce_single_selected_future_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import (
    BoundInstrumentV1,
)
from src.ops.peak_trade_economic_ranking_runtime_v1.synthesize_ready_features_v1 import (
    synthesize_ready_feature_production_snapshot_v1,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    ScopeConfirmationStateV1,
)
from trading.master_v2.directional_assessment_v1 import (
    DirectionalAssessmentV1,
    DirectionalConfirmationStateV1,
)
from trading.master_v2.double_play_composition_matrix_v1 import DoublePlayCompositionPolicyV1
from trading.master_v2.double_play_entry_exit_policy_v0 import DoublePlayEntryExitPolicyV0
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SELECTION_V1_SOURCE = REPO_ROOT / "src/ops/single_selected_future_policy_v1/selection_v1.py"

REPO_SHA = "ff5a533bd1733f5b9e3bcc4e186194ff88ef401d"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"


def _perp(inst_id: str = "ETH-USDT-SWAP", **extra: object) -> dict:
    row = {
        "instId": inst_id,
        "instType": "SWAP",
        "state": "live",
        "baseCcy": "ETH",
        "quoteCcy": "USDT",
        "settleCcy": "USDT",
        "ctType": "linear",
        "ctVal": "0.01",
        "ctValCcy": "ETH",
        "tickSz": "0.01",
        "lotSz": "1",
        "minSz": "1",
        "uly": "ETH-USDT",
        "expTime": "",
    }
    row.update(extra)
    return row


def _ranking_snapshot() -> dict:
    rows = [
        _perp("SOL-USDT-SWAP", baseCcy="SOL", ctValCcy="SOL"),
        _perp("ETH-USDT-SWAP"),
        _perp("ADA-USDT-SWAP", baseCcy="ADA", ctValCcy="ADA"),
    ]
    uni = produce_governed_futures_universe_v1(
        source_payload={"code": "0", "msg": "", "data": rows},
        mark_price_payload={
            "code": "0",
            "msg": "",
            "data": [{"instId": r["instId"], "markPx": "100.5"} for r in rows],
        },
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    ).snapshot.to_dict()
    return produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        feature_production_snapshot=synthesize_ready_feature_production_snapshot_v1(uni),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    ).snapshot.to_dict()


def _selection_from_ranking(ranking: dict) -> SingleSelectedFutureSelectionV1:
    produced = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert produced.ok is True
    assert produced.selection is not None
    return produced.selection


def _bound_from_selection(
    selection: SingleSelectedFutureSelectionV1,
    *,
    universe_snapshot_id: str,
) -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id=selection.instrument_id,
        venue_native_id=selection.venue_native_id,
        ranking_snapshot_id=selection.ranking_snapshot_id,
        ranking_integrity_digest=selection.ranking_integrity_digest,
        universe_snapshot_id=universe_snapshot_id,
        selection_id=selection.selection_id,
        selection_integrity_digest=selection.integrity_digest,
        selection_state=selection.state,
        ranking_policy_id=selection.ranking_policy_id,
        ranking_policy_version=selection.ranking_policy_version,
        upstream_rank_order_witness=selection.upstream_rank_order_witness,
    )


def test_b05_movement_values_accepted_by_cap22_ranking() -> None:
    ranking = _ranking_snapshot()
    assert ranking["ranked_candidates"]
    first = ranking["ranked_candidates"][0]
    assert "total_score" in first
    assert "tie_break_values" in first


def test_cap23_consumes_ranking_order_without_rescore() -> None:
    ranking = _ranking_snapshot()
    selection = _selection_from_ranking(ranking)
    assert selection.instrument_id
    assert selection.ranking_snapshot_id == ranking["ranking_snapshot_id"]
    source = SELECTION_V1_SOURCE.read_text(encoding="utf-8")
    assert "build_balanced_movement_scores_v1" not in source
    assert "produce_raw_ranking_features_for_instrument_v1" not in source


# Check the actual score and tie-break fields from the producer against DTOs
# consumed downstream. No claim of a current runtime alias/key validator.
@pytest.mark.parametrize(
    "dto_type",
    [
        BoundInstrumentV1,
        IntegratedOfflineReplayInputV1,
        DirectionalAssessmentV1,
        DirectionalConfirmationStateV1,
        ScopeConfirmationStateV1,
        DoublePlayCompositionPolicyV1,
        DoublePlayEntryExitPolicyV0,
        CapitalRiskSizingDecisionV1,
    ],
)
def test_ranking_features_are_not_fields_on_trading_dtos(dto_type) -> None:
    top = _ranking_snapshot()["ranked_candidates"][0]
    # The IDs may legitimately survive as instrument identity. Exclude them
    # from the numeric score, tie-break and membership signals under test.
    ranking_fields = {"total_score", "tie_break_values", *top["tie_break_values"]} - {
        "canonical_instrument_id",
        "venue_native_id",
    }
    assert ranking_fields.isdisjoint(field.name for field in fields(dto_type))


def test_replay_validator_rejects_selection_provenance_as_runtime_input() -> None:
    @dataclass
    class ReplayWithLeakedRank:
        instrument_id: str
        ranking_snapshot_id: str

    validate_replay_drops_handoff_provenance_v1(IntegratedOfflineReplayInputV1)
    with pytest.raises(
        RankingUniverseToFullCoreSsfHandoffError, match="HANDOFF_PROVENANCE_LEAKED_INTO_REPLAY"
    ):
        validate_replay_drops_handoff_provenance_v1(ReplayWithLeakedRank)


def test_handoff_chain_behavioral_equivalence_fixture() -> None:
    ranking = _ranking_snapshot()
    selection_a = _selection_from_ranking(ranking)
    selection_b = _selection_from_ranking(ranking)
    assert selection_a.instrument_id == selection_b.instrument_id
    assert selection_a.selection_id == selection_b.selection_id
    universe_id = ranking["universe_snapshot_id"]
    bound = _bound_from_selection(selection_a, universe_snapshot_id=universe_id)
    assert_handoff_invariants_v1(
        selection_a,
        bound,
        ranking_snapshot_id=ranking["ranking_snapshot_id"],
        ranking_universe_snapshot_id=universe_id,
        universe_snapshot_id=universe_id,
    )


def test_cap23_selection_authority_unchanged() -> None:
    sig = inspect.signature(produce_single_selected_future_v1)
    assert "ranking_snapshot" in sig.parameters
