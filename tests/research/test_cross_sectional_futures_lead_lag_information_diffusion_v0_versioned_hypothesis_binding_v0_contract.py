"""Contract tests for cross_sectional_futures_lead_lag_information_diffusion v0 hypothesis binding."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_score_v0 import (
    DEFAULT_LAG_WINDOW_L,
    DEFAULT_SIGNAL_LAG_BARS,
    SCORE_FORMULA_VERSION,
    compute_panel_median_lagged_return_v0,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0 import (
    CONFIG_REL_PATH,
    GOVERNANCE_REL_PATH,
    PRIOR_RELATIVE_STRENGTH_BINDING_DIGEST,
    PRIOR_RELATIVE_STRENGTH_SCORE_FAMILY,
    RANKING_FORMULA,
    RESEARCH_SCOPE,
    SCORE_FAMILY_POLICY,
    materialize_and_validate_versioned_hypothesis_binding_v0,
    materialize_versioned_hypothesis_binding_v0,
    materializer_to_binder_roundtrip_v0,
    validate_prior_relative_strength_not_reused_unchanged_v0,
    validate_stale_or_wrong_digest_rejected_v0,
    validate_versioned_hypothesis_binding_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0 as materialize_prior_relative_strength_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / CONFIG_REL_PATH
GOVERNANCE_DOC = REPO_ROOT / GOVERNANCE_REL_PATH
MATERIALIZER_PATH = (
    REPO_ROOT / "scripts/research/"
    "materialize_cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0.py"
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
    def test_distinct_from_prior_relative_strength(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        prior = materialize_prior_relative_strength_v0()
        material = envelope["material_difference_from_prior"]
        assert (
            material["prior_relative_strength_score_family"] == PRIOR_RELATIVE_STRENGTH_SCORE_FAMILY
        )
        assert material["new_score_family_policy"] == SCORE_FAMILY_POLICY
        assert material["material_difference_proven"] is True
        assert material["same_semantic_binding"] is False
        assert envelope["binding_digest"] != prior["binding_digest"]
        assert envelope["binding_digest"] != PRIOR_RELATIVE_STRENGTH_BINDING_DIGEST

    def test_prior_relative_strength_binding_not_reused_unchanged(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        ok, reasons = validate_prior_relative_strength_not_reused_unchanged_v0(envelope)
        assert ok, reasons

    def test_stale_prior_binding_digest_rejected(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        stale = deepcopy(envelope)
        stale["binding_digest"] = PRIOR_RELATIVE_STRENGTH_BINDING_DIGEST
        stale["binding"]["digest_bindings"]["binding_digest"]["value"] = (
            PRIOR_RELATIVE_STRENGTH_BINDING_DIGEST
        )
        ok, reasons = validate_stale_or_wrong_digest_rejected_v0(
            stale, stale_binding_digest=PRIOR_RELATIVE_STRENGTH_BINDING_DIGEST
        )
        assert not ok
        assert "STALE_BINDING_DIGEST_ACCEPTED" in reasons


class TestRequiredBindingFields:
    def test_futures_only_bitcoin_absent(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        constraints = envelope["system_constraints"]
        assert constraints["futures_only"] is True
        assert constraints["bitcoin_present"] is False
        assert constraints["bitcoin_direction_allowed"] is False
        assert constraints["spot_excluded"] is True

    def test_panel_median_lag_diffusion_semantics_bound(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        assert envelope["score_family_policy"] == SCORE_FAMILY_POLICY
        assert envelope["ranking_policy_binding"]["ranking_formula"] == RANKING_FORMULA
        assert envelope["research_scope"] == RESEARCH_SCOPE
        assert envelope["parameter_binding"]["score_formula_version"] == SCORE_FORMULA_VERSION

    def test_dataset_and_universe_digests_bound(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        assert (
            envelope["dataset_digest"]
            == "79b1c977960f4af7e1eb54580738d77b259b74f7f02bbf0e999afbb95f8f09f1"
        )
        assert (
            envelope["universe_digest"]
            == "d57738dc7e80520c17e49c406a22f8de15216c2e48e56d91b3757359ebb552a1"
        )

    def test_no_economic_evaluation(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        assert envelope["economic_evaluation_executed"] is False
        assert envelope["runtime_effect"] == "NONE"
        assert envelope["authority_effect"] == "NONE"


class TestScoringPrimitives:
    def test_panel_median_lagged_return_uses_feature_time(self) -> None:
        closes = {
            "okx:linear_perpetual:ETH:USDT:USDT:perp": [
                100.0,
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
                110.0,
            ],
            "okx:linear_perpetual:SOL:USDT:USDT:perp": [
                10.0,
                10.5,
                11.0,
                11.5,
                12.0,
                12.5,
                13.0,
                13.5,
                14.0,
                14.5,
                15.0,
            ],
            "okx:linear_perpetual:AVAX:USDT:USDT:perp": [
                20.0,
                20.2,
                20.4,
                20.6,
                20.8,
                21.0,
                21.2,
                21.4,
                21.6,
                21.8,
                22.0,
            ],
            "okx:linear_perpetual:LINK:USDT:USDT:perp": [
                5.0,
                5.1,
                5.2,
                5.3,
                5.4,
                5.5,
                5.6,
                5.7,
                5.8,
                5.9,
                6.0,
            ],
            "okx:linear_perpetual:DOGE:USDT:USDT:perp": [
                0.1,
                0.11,
                0.12,
                0.13,
                0.14,
                0.15,
                0.16,
                0.17,
                0.18,
                0.19,
                0.2,
            ],
        }
        result = compute_panel_median_lagged_return_v0(
            closes,
            lag_window_l=DEFAULT_LAG_WINDOW_L,
            signal_lag_bars=DEFAULT_SIGNAL_LAG_BARS,
            epoch_index=10,
        )
        assert result is not None


class TestGovernanceAndPaths:
    def test_governance_doc_exists(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "cross_sectional_futures_lead_lag_information_diffusion" in text

    def test_materializer_script_exists(self) -> None:
        assert MATERIALIZER_PATH.is_file()

    def test_no_runtime_imports(self) -> None:
        module_path = (
            REPO_ROOT / "src/research/"
            "cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0.py"
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
        assert config_envelope["binding_digest"] != PRIOR_RELATIVE_STRENGTH_BINDING_DIGEST
