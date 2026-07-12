"""Contract tests for cross_sectional_open_interest_zscore_reversion v0 hypothesis binding."""

from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path

import pytest

from src.research.cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0 import (
    PRIOR_BINDING_DIGEST as DELTA_PRIOR_BINDING_DIGEST,
    materialize_versioned_research_binding_v0 as materialize_prior_delta_binding_v0,
)
from src.research.cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0 import (
    materialize_versioned_hypothesis_binding_v0 as materialize_prior_level_rank_binding_v0,
)
from src.research.cross_sectional_open_interest_zscore_reversion_scoring_v0 import (
    MIN_ELIGIBLE_MEMBERS,
    OpenInterestZscoreLeg,
    OpenInterestZscoreScoreResultV0,
    OpenInterestZscoreScoreStatusV0,
    compute_instrument_open_interest_zscore_score_v0,
    compute_panel_oi_dispersion_snapshot_v0,
    select_open_interest_zscore_extreme_single_leg_v0,
)
from src.research.cross_sectional_open_interest_zscore_reversion_v0_pit_semantics_contract_v0 import (
    CONTRACT_VERSION,
    OPEN_INTEREST_LEVEL_DEFINITION,
    RESEARCH_SCOPE,
    ZSCORE_NORMALIZATION,
    ZERO_DISPERSION_POLICY,
)
from src.research.cross_sectional_open_interest_zscore_reversion_v0_versioned_hypothesis_binding_v0 import (
    CONFIG_REL_PATH,
    GOVERNANCE_REL_PATH,
    PRIOR_DELTA_RANK_BINDING_DIGEST,
    PRIOR_LEVEL_RANK_BINDING_DIGEST,
    RANKING_FORMULA,
    materialize_and_validate_versioned_hypothesis_binding_v0,
    materialize_versioned_hypothesis_binding_v0,
    materializer_to_binder_roundtrip_v0,
    validate_prior_level_rank_and_delta_not_reused_unchanged_v0,
    validate_stale_or_wrong_digest_rejected_v0,
    validate_versioned_hypothesis_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / CONFIG_REL_PATH
GOVERNANCE_DOC = REPO_ROOT / GOVERNANCE_REL_PATH
MATERIALIZER_PATH = (
    REPO_ROOT / "scripts/research/"
    "materialize_cross_sectional_open_interest_zscore_reversion_v0_versioned_hypothesis_binding_v0.py"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
)


def _panel_levels(values: dict[str, float | None]) -> tuple[tuple[str, float | None], ...]:
    return tuple((iid, values[iid]) for iid in sorted(values))


class TestHypothesisBindingMaterialization:
    def test_materialization_complete(self) -> None:
        result = materialize_and_validate_versioned_hypothesis_binding_v0()
        assert result.verdict.value == "COMPLETE"
        assert result.validation_verdict.value == "ACCEPTED_COMPLETE"
        assert result.fail_reasons == ()

    def test_deterministic_double_materialization(self) -> None:
        first = materialize_versioned_hypothesis_binding_v0()
        second = materialize_versioned_hypothesis_binding_v0()
        assert first == second

    def test_materializer_to_binder_roundtrip_pass(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        roundtrip = materializer_to_binder_roundtrip_v0(envelope)
        assert roundtrip["materializer_to_binder_roundtrip_pass"] is True


class TestMaterialDifference:
    def test_distinct_from_prior_level_rank(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        prior = materialize_prior_level_rank_binding_v0()
        material = envelope["material_difference_from_prior_open_interest_rank_hypotheses_v0"]
        assert material["prior_level_rank_feature"] == "point_in_time_open_interest_level"
        assert (
            material["new_feature"] == "cross_sectional_open_interest_zscore_at_lagged_observation"
        )
        assert material["distinct_hypothesis"] is True
        assert envelope["binding_digest"] != prior["binding_digest"]
        assert envelope["binding_digest"] != PRIOR_LEVEL_RANK_BINDING_DIGEST

    def test_distinct_from_prior_delta_rank(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        prior = materialize_prior_delta_binding_v0()
        material = envelope["material_difference_from_prior_open_interest_rank_hypotheses_v0"]
        assert material["prior_delta_rank_feature"] == "delta_or_change_in_open_interest"
        assert material["distinct_hypothesis"] is True
        assert envelope["binding_digest"] != prior["binding_digest"]
        assert envelope["binding_digest"] != PRIOR_DELTA_RANK_BINDING_DIGEST

    def test_prior_bindings_not_reused_unchanged(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        ok, reasons = validate_prior_level_rank_and_delta_not_reused_unchanged_v0(envelope)
        assert ok, reasons

    def test_stale_prior_binding_digest_rejected(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        for stale_digest in (
            PRIOR_LEVEL_RANK_BINDING_DIGEST,
            PRIOR_DELTA_RANK_BINDING_DIGEST,
            DELTA_PRIOR_BINDING_DIGEST,
        ):
            stale = deepcopy(envelope)
            stale["binding_digest"] = stale_digest
            stale["binding"]["digest_bindings"]["binding_digest"]["value"] = stale_digest
            ok, reasons = validate_stale_or_wrong_digest_rejected_v0(
                stale, stale_binding_digest=stale_digest
            )
            assert not ok
            assert "STALE_BINDING_DIGEST_ACCEPTED" in reasons


class TestRequiredBindingFields:
    def test_futures_only_bitcoin_absent(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        assert envelope["futures_only"] is True
        assert envelope["bitcoin_present"] is False
        assert envelope["system_constraints"]["bitcoin_direction_allowed"] is False

    def test_ranking_and_pit_semantics_bound(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        assert envelope["ranking_formula"] == RANKING_FORMULA
        assert envelope["open_interest_level_definition"] == OPEN_INTEREST_LEVEL_DEFINITION
        assert envelope["zscore_normalization"] == ZSCORE_NORMALIZATION
        assert envelope["zero_dispersion_policy"] == ZERO_DISPERSION_POLICY
        assert envelope["finalized_bar_only"] is True
        assert envelope["research_scope"] == RESEARCH_SCOPE
        assert envelope["pit_semantics_contract"]["contract_version"] == CONTRACT_VERSION

    def test_no_economic_evaluation(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        assert envelope["economic_evaluation_executed"] is False
        assert envelope["runtime_effect"] == "NONE"
        assert envelope["authority_effect"] == "NONE"

    def test_historical_evidence_preserved(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        lineage = envelope["binding"]["prior_hypothesis_lineage"]
        assert lineage["historical_evidence_preserved"] is True
        assert lineage["unchanged_retry_blocked"] is True


class TestScoringPrimitives:
    def test_zero_dispersion_fail_closed(self) -> None:
        snapshot = compute_panel_oi_dispersion_snapshot_v0(
            _panel_levels(
                {
                    "a": 100.0,
                    "b": 100.0,
                    "c": 100.0,
                    "d": 100.0,
                    "e": 100.0,
                }
            )
        )
        assert snapshot is not None
        assert snapshot.panel_std == 0.0
        assert snapshot.dispersion_gate_passes is False

        panel = _panel_levels(
            {
                "a": 100.0,
                "b": 100.0,
                "c": 100.0,
                "d": 100.0,
                "e": 100.0,
            }
        )
        score = compute_instrument_open_interest_zscore_score_v0("a", panel, epoch_index=1)
        assert score is not None
        assert score.score_status is OpenInterestZscoreScoreStatusV0.INSUFFICIENT_PANEL_DISPERSION
        assert not score.signal_eligible
        assert math.isnan(score.z_score)

        selection = select_open_interest_zscore_extreme_single_leg_v0(
            (),
            panel_dispersion_gate_passes=False,
        )
        assert selection.leg is OpenInterestZscoreLeg.FLAT

    def test_mirrored_long_min_and_short_max(self) -> None:
        panel = _panel_levels(
            {
                "inst_a": 50.0,
                "inst_b": 100.0,
                "inst_c": 75.0,
                "inst_d": 80.0,
                "inst_e": 90.0,
            }
        )
        scores = [
            score
            for iid, _ in panel
            if (
                score := compute_instrument_open_interest_zscore_score_v0(iid, panel, epoch_index=1)
            )
            is not None
            and score.signal_eligible
        ]
        assert len(scores) == 5
        selection = select_open_interest_zscore_extreme_single_leg_v0(
            scores,
            panel_dispersion_gate_passes=True,
        )
        assert selection.leg in {
            OpenInterestZscoreLeg.LONG_MIN_ZSCORE,
            OpenInterestZscoreLeg.SHORT_MAX_ZSCORE,
        }
        assert selection.min_zscore_instrument_id == "inst_a"
        assert selection.max_zscore_instrument_id == "inst_b"

    def test_tied_values_break_by_instrument_id_asc(self) -> None:
        scores = (
            OpenInterestZscoreScoreResultV0("b", 100.0, 100.0, 10.0, -1.5, True),
            OpenInterestZscoreScoreResultV0("a", 50.0, 100.0, 10.0, -1.5, True),
            OpenInterestZscoreScoreResultV0("c", 150.0, 100.0, 10.0, 1.5, True),
        )
        selection = select_open_interest_zscore_extreme_single_leg_v0(
            scores,
            min_abs_zscore_for_entry=1.0,
            panel_dispersion_gate_passes=True,
        )
        assert selection.min_zscore_instrument_id == "a"
        assert selection.leg is OpenInterestZscoreLeg.LONG_MIN_ZSCORE
        assert selection.instrument_id == "a"

    def test_missing_instrument_excluded(self) -> None:
        panel = _panel_levels(
            {
                "inst_a": None,
                "inst_b": 100.0,
                "inst_c": 75.0,
                "inst_d": 80.0,
                "inst_e": 90.0,
            }
        )
        score = compute_instrument_open_interest_zscore_score_v0("inst_a", panel, epoch_index=1)
        assert score is not None
        assert score.score_status is OpenInterestZscoreScoreStatusV0.MISSING_REQUIRED_OPEN_INTEREST
        assert not score.signal_eligible

    def test_minimum_universe_enforced_in_binding(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        assert envelope["minimum_rankable_instrument_count"] >= MIN_ELIGIBLE_MEMBERS


class TestGovernanceAndPaths:
    def test_governance_doc_exists(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "cross_sectional_open_interest_zscore_reversion/v0" in text
        assert "NO_ECONOMIC_EVALUATION" in text or "no economic evaluation" in text.lower()

    def test_materializer_script_exists(self) -> None:
        assert MATERIALIZER_PATH.is_file()

    def test_no_runtime_imports(self) -> None:
        module_path = (
            REPO_ROOT / "src/research/"
            "cross_sectional_open_interest_zscore_reversion_v0_versioned_hypothesis_binding_v0.py"
        )
        source = module_path.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source


class TestConfigArtifact:
    @pytest.fixture(scope="class")
    def config_envelope(self) -> dict:
        if CONFIG_PATH.is_file():
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return materialize_versioned_hypothesis_binding_v0()

    def test_config_matches_materializer_when_present(self, config_envelope: dict) -> None:
        materialized = materialize_versioned_hypothesis_binding_v0()
        if CONFIG_PATH.is_file():
            assert config_envelope["binding_digest"] == materialized["binding_digest"]
        verdict, reasons = validate_versioned_hypothesis_binding_v0(config_envelope)
        assert verdict.value == "ACCEPTED_COMPLETE", reasons
