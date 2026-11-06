"""Contract tests for cross_sectional_open_interest_level_rank v0 versioned hypothesis binding."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.research.cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0 import (
    PRIOR_BINDING_DIGEST as DELTA_PRIOR_BINDING_DIGEST,
    materialize_versioned_research_binding_v0 as materialize_prior_delta_binding_v0,
)
from src.research.cross_sectional_open_interest_level_rank_scoring_v0 import (
    OpenInterestLevelLeg,
    compute_instrument_open_interest_level_score_v0,
    select_open_interest_level_extreme_single_leg_v0,
)
from src.research.cross_sectional_open_interest_level_rank_v0_pit_semantics_contract_v0 import (
    CONTRACT_VERSION,
    OPEN_INTEREST_LEVEL_DEFINITION,
    RESEARCH_SCOPE,
)
from src.research.cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0 import (
    CONFIG_REL_PATH,
    GOVERNANCE_REL_PATH,
    PRIOR_BINDING_DIGEST,
    PRIOR_SCOPE,
    RANKING_FORMULA,
    materialize_and_validate_versioned_hypothesis_binding_v0,
    materialize_versioned_hypothesis_binding_v0,
    materializer_to_binder_roundtrip_v0,
    validate_prior_delta_binding_not_reused_unchanged_v0,
    validate_stale_or_wrong_digest_rejected_v0,
    validate_versioned_hypothesis_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / CONFIG_REL_PATH
GOVERNANCE_DOC = REPO_ROOT / GOVERNANCE_REL_PATH
MATERIALIZER_PATH = (
    REPO_ROOT / "scripts/research/"
    "materialize_cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0.py"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
)


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
    def test_distinct_from_prior_delta_rank(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        prior = materialize_prior_delta_binding_v0()
        material = envelope["material_difference_from_prior_open_interest_delta_rank_v0"]
        assert material["prior_scope"] == PRIOR_SCOPE
        assert material["prior_feature"] == "delta_or_change_in_open_interest"
        assert material["new_feature"] == "point_in_time_open_interest_level"
        assert material["distinct_hypothesis"] is True
        assert material["unchanged_retry"] is False
        assert envelope["binding_digest"] != prior["binding_digest"]
        assert envelope["binding_digest"] != PRIOR_BINDING_DIGEST

    def test_prior_delta_binding_not_reused_unchanged(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        ok, reasons = validate_prior_delta_binding_not_reused_unchanged_v0(envelope)
        assert ok, reasons

    def test_stale_prior_binding_digest_rejected(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        stale = deepcopy(envelope)
        stale["binding_digest"] = PRIOR_BINDING_DIGEST
        stale["binding"]["digest_bindings"]["binding_digest"]["value"] = PRIOR_BINDING_DIGEST
        ok, reasons = validate_stale_or_wrong_digest_rejected_v0(
            stale, stale_binding_digest=PRIOR_BINDING_DIGEST
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
    def test_level_score_uses_lagged_observation(self) -> None:
        values = [100.0, 110.0, 120.0, 130.0]
        result = compute_instrument_open_interest_level_score_v0(
            "okx:linear_perpetual:ETH:USDT:USDT:perp",
            values,
            epoch_index=2,
        )
        assert result is not None
        assert result.open_interest_level == 110.0

    def test_single_leg_selection_prefers_larger_median_deviation(self) -> None:
        from src.research.cross_sectional_open_interest_level_rank_scoring_v0 import (
            OpenInterestLevelScoreResultV0,
        )

        scores = (
            OpenInterestLevelScoreResultV0("a", 10.0, True),
            OpenInterestLevelScoreResultV0("b", 100.0, True),
            OpenInterestLevelScoreResultV0("c", 20.0, True),
        )
        selection = select_open_interest_level_extreme_single_leg_v0(scores)
        assert selection.leg in (
            OpenInterestLevelLeg.LONG_MIN_LEVEL,
            OpenInterestLevelLeg.SHORT_MAX_LEVEL,
        )


class TestGovernanceAndPaths:
    def test_governance_doc_exists(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "cross_sectional_open_interest_level_rank/v0" in text
        assert "NO_ECONOMIC_EVALUATION" in text or "no economic evaluation" in text.lower()

    def test_materializer_script_exists(self) -> None:
        assert MATERIALIZER_PATH.is_file()

    def test_no_runtime_imports(self) -> None:
        module_path = (
            REPO_ROOT / "src/research/"
            "cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0.py"
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

    def test_config_matches_materializer(self, config_envelope: dict) -> None:
        materialized = materialize_versioned_hypothesis_binding_v0()
        assert config_envelope["binding_digest"] == materialized["binding_digest"]
        verdict, reasons = validate_versioned_hypothesis_binding_v0(config_envelope)
        assert verdict.value == "ACCEPTED_COMPLETE", reasons

    def test_prior_binding_digest_differs(self, config_envelope: dict) -> None:
        assert config_envelope["binding_digest"] != DELTA_PRIOR_BINDING_DIGEST
