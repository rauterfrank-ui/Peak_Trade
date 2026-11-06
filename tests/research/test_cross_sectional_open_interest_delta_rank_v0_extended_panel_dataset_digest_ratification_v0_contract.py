"""Contract tests for extended panel dataset digest ratification v0."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.research.cross_sectional_open_interest_delta_rank_v0_extended_panel_dataset_digest_ratification_v0 import (
    CONFIRM_GO,
    DEFAULT_MATERIALIZATION_MANIFEST,
    EXPECTED_RANKABLE_EPOCH_COUNT,
    HISTORY_DEPTH_AFTER,
    HISTORY_DEPTH_BEFORE,
    MINIMUM_REQUIRED_HISTORY_DEPTH,
    NEW_DATASET_DIGEST,
    OLD_BINDING_DIGEST,
    OLD_DATASET_DIGEST,
    RatificationTerminalStatus,
    build_before_after_field_diff_v0,
    build_ratification_config_v0,
    compare_ratification_envelopes_v0,
    execute_extended_panel_dataset_digest_ratification_v0,
    load_observed_dataset_identity_from_manifest_v0,
    materialize_extended_panel_ratified_versioned_binding_v0,
    ratification_roundtrip_contract_v0,
    validate_ratified_extended_binding_v0,
    verify_expected_extended_dataset_identity_v0,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    LOOKBACK_K,
    SIGNAL_LAG_BARS,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0 import (
    CONFIG_REL_PATH,
    PRIOR_BINDING_DIGEST,
    PRIOR_RATIFIED_PANEL_DATASET_DIGEST,
    RATIFIED_PANEL_DATASET_DIGEST,
    materialize_versioned_research_binding_v0,
    validate_stale_prior_binding_rejected_v0,
    validate_versioned_research_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    REPO_ROOT
    / "config/research/cross_sectional_open_interest_delta_rank_v0_extended_panel_dataset_digest_ratification_v0.json"
)
CLI_PATH = (
    REPO_ROOT
    / "scripts/ops/execute_cross_sectional_open_interest_delta_rank_v0_extended_panel_dataset_digest_ratification_v0.py"
)


class TestContractConfig:
    def test_config_matches_module(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        module_config = build_ratification_config_v0()
        assert config["go_token"] == CONFIRM_GO
        assert config["old_dataset_digest"] == OLD_DATASET_DIGEST
        assert config["new_dataset_digest"] == NEW_DATASET_DIGEST
        assert module_config["old_binding_digest"] == OLD_BINDING_DIGEST

    def test_cli_exists(self) -> None:
        assert CLI_PATH.is_file()


class TestDatasetIdentity:
    def test_manifest_identity_verification(self) -> None:
        observed = load_observed_dataset_identity_from_manifest_v0(DEFAULT_MATERIALIZATION_MANIFEST)
        ok, reasons = verify_expected_extended_dataset_identity_v0(observed)
        assert ok, reasons
        assert observed["history_depth_after"] >= MINIMUM_REQUIRED_HISTORY_DEPTH
        assert observed["panel_dataset_digest"] == NEW_DATASET_DIGEST

    def test_stale_dataset_digest_rejected(self) -> None:
        envelope = materialize_extended_panel_ratified_versioned_binding_v0()
        stale = deepcopy(envelope)
        stale["data_digest"] = OLD_DATASET_DIGEST
        stale["binding"]["digest_bindings"]["data_digest"]["value"] = OLD_DATASET_DIGEST
        ok, reasons = validate_ratified_extended_binding_v0(stale)
        assert not ok
        assert "STALE_DATASET_DIGEST_REJECTED" in reasons

    def test_stale_prior_binding_helper(self) -> None:
        stale = {
            "data_digest": PRIOR_RATIFIED_PANEL_DATASET_DIGEST,
            "binding_digest": PRIOR_BINDING_DIGEST,
        }
        ok, reasons = validate_stale_prior_binding_rejected_v0(stale)
        assert not ok
        assert reasons


class TestRatifiedBinding:
    def test_materialized_binding_accepts_validator(self) -> None:
        envelope = materialize_extended_panel_ratified_versioned_binding_v0()
        verdict, reasons = validate_versioned_research_binding_v0(envelope)
        assert verdict.value == "ACCEPTED_COMPLETE"
        assert reasons == ()
        assert envelope["data_digest"] == NEW_DATASET_DIGEST
        assert envelope["binding"]["parameter_binding"]["rank_lookback_k"] == LOOKBACK_K == 4
        assert envelope["binding"]["parameter_binding"]["signal_lag_bars"] == SIGNAL_LAG_BARS == 1

    def test_semantic_fields_unchanged_in_field_diff(self) -> None:
        old = json.loads((REPO_ROOT / CONFIG_REL_PATH).read_text(encoding="utf-8"))
        new = materialize_extended_panel_ratified_versioned_binding_v0()
        diff = build_before_after_field_diff_v0(old_binding=old, new_binding=new)
        unexpected = [row for row in diff if row["change_type"] == "UNEXPECTED_SEMANTIC_CHANGE"]
        assert unexpected == []
        assert all(row["field_class"] != "UNEXPECTED" for row in diff)

    def test_deterministic_double_ratification(self) -> None:
        first = materialize_extended_panel_ratified_versioned_binding_v0()
        second = materialize_extended_panel_ratified_versioned_binding_v0()
        diff_empty, _ = compare_ratification_envelopes_v0(first, second)
        assert diff_empty is True

    def test_ratification_roundtrip_pass(self) -> None:
        envelope = materialize_extended_panel_ratified_versioned_binding_v0()
        roundtrip = ratification_roundtrip_contract_v0(envelope)
        assert roundtrip["ratification_roundtrip_pass"] is True

    def test_execute_ratification_complete(self, tmp_path: Path) -> None:
        result = execute_extended_panel_dataset_digest_ratification_v0(
            confirm=CONFIRM_GO,
            enabled=True,
            manifest_path=DEFAULT_MATERIALIZATION_MANIFEST,
            write_repo_config=False,
            repo_root=REPO_ROOT,
        )
        assert result.status is RatificationTerminalStatus.RATIFICATION_COMPLETE
        assert result.new_dataset_digest == NEW_DATASET_DIGEST
        assert result.old_binding_digest == OLD_BINDING_DIGEST
        assert result.second_ratification_diff_empty is True
        assert result.unexpected_change_count == 0
        assert result.unclassified_changed_field_count == 0
        assert result.ratification_roundtrip_pass is True

    def test_history_and_rankable_epoch_counts(self) -> None:
        envelope = materialize_extended_panel_ratified_versioned_binding_v0()
        rat = envelope["extended_panel_dataset_ratification"]
        assert rat["history_depth_before"] == HISTORY_DEPTH_BEFORE
        assert rat["history_depth_after"] == HISTORY_DEPTH_AFTER
        assert rat["expected_rankable_epoch_count"] == EXPECTED_RANKABLE_EPOCH_COUNT
        assert rat["expected_rankable_epoch_count"] >= 50
