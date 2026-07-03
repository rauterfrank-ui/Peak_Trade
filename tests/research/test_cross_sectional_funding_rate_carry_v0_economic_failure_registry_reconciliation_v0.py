"""Contract tests for funding-rate carry v0 economic failure registry reconciliation v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    load_registry,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BINDING_PATH = (
    REPO_ROOT
    / "config/research/cross_sectional_funding_rate_carry_v0_versioned_research_binding_v0.json"
)
SECTION_PREFIX = (
    "#### RUNBOOK_RESEARCH_LINE — Cross-Sectional Funding Rate Carry Non-Bitcoin Perpetuals v0"
)
ECONOMIC_EVIDENCE_REF = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/"
    "bounded_cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_re_run_v0_"
    "20260703T115048Z"
)
EXECUTION_INFRA_CLOSEOUT_REF = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/"
    "bounded_cross_sectional_funding_rate_carry_v0_execution_infrastructure_and_bound_"
    "funding_panel_recovery_squash_merge_closeout_v0_20260703T113900Z"
)
FULL_RUNNER_CLOSEOUT_REF = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/"
    "bounded_cross_sectional_funding_rate_carry_v0_full_offline_economic_evaluation_runner_"
    "mainline_integration_squash_merge_closeout_v0_20260703T140100Z"
)
EVIDENCE_REGISTRY_RECONCILIATION_CLOSEOUT_REF = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/"
    "bounded_cross_sectional_funding_rate_carry_v0_evidence_and_registry_reconciliation_"
    "squash_merge_closeout_v0_20260703T141600Z"
)


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _funding_carry_section(text: str) -> str:
    start = text.index(SECTION_PREFIX)
    end = text.index(
        "\n#### RUNBOOK_RESEARCH_LINE — Composite Breakout Confirmation Vol-Gated Donchian v1",
        start,
    )
    return text[start:end]


def _load_binding() -> dict:
    return json.loads(BINDING_PATH.read_text(encoding="utf-8"))


class TestFundingCarryBindingReconciliation:
    def test_terminal_fail_fields_on_persisted_binding(self) -> None:
        binding = _load_binding()
        assert binding["economic_evaluation_executed"] is True
        assert binding["economic_evaluation_status"] == "COMPLETE_FAIL"
        assert binding["economic_validity_offline_gate_pass"] is False
        assert binding["promotion_eligible"] is False
        assert binding["research_execution_infrastructure_status"] == "COMPLETE"
        assert binding["bound_funding_panel_status"] == "COMPLETE"
        assert binding["full_offline_evaluation_runner_status"] == "MAINLINE_AVAILABLE"
        assert binding["runtime_rewire_admissible"] is False
        assert binding["retry_unchanged_binding_allowed"] is False
        assert binding["policy_or_threshold_changed"] is False
        assert binding["binding_changed"] is False
        assert binding["historical_economic_result"] == "FAIL"
        assert binding["trade_count"] == 0
        assert binding["evaluation_authorized"] is False
        assert binding["re_evaluation_allowed"] is False

    def test_reason_codes_and_evidence_refs(self) -> None:
        binding = _load_binding()
        assert binding["economic_evaluation_reason_codes"] == [
            "TRADE_COUNT_BELOW_THRESHOLD",
            "PROFIT_FACTOR_BELOW_THRESHOLD",
            "MONTE_CARLO_FAILED",
        ]
        assert ECONOMIC_EVIDENCE_REF in binding["economic_viability_evidence_ref"]
        assert "MANIFEST_VERIFY_RC=0" in binding["economic_viability_evidence_ref"]
        assert ECONOMIC_EVIDENCE_REF in binding["durable_evidence_refs"]
        assert EXECUTION_INFRA_CLOSEOUT_REF in binding["durable_evidence_refs"]
        assert FULL_RUNNER_CLOSEOUT_REF in binding["durable_evidence_refs"]

    def test_binding_digests_unchanged(self) -> None:
        binding = _load_binding()
        assert (
            binding["config_digest"]
            == "e0d169f143e16bb60148a26c450a5e7abf0606253fe50c4fb2f8277e9f64a414"
        )
        assert (
            binding["data_digest"]
            == "0c4f26bfa044f82c3bda505906bcf59da3ff43ad4a63b1e8da6b97ce8b730224"
        )
        assert binding["implementation_digest"] == (
            "c8bdeaca4e26f111ce932e2c6e300d5d2b2a8bf175e3b7c4fa1c1205d6db538e"
        )
        assert binding["binding_digest"] == (
            "a98d40449cf32bc5415fadd4c26976e380d3be2880a03efebbc1e9149e809cd9"
        )


class TestFundingCarryProgressRegistryReconciliation:
    def test_global_metadata_terminal_fail(self) -> None:
        assert authoritative_field_value("LAST_VERIFIED_ORIGIN_MAIN") == (
            "1a6dac20003b1e9e84aed0f015a1cbb37601d467"
        )
        assert authoritative_field_value("CROSS_SECTIONAL_FUNDING_RATE_CARRY_V0_STATUS") == (
            "COMPLETE_FAIL"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_FUNDING_RATE_CARRY_V0_ECONOMIC_EVALUATION_STATUS"
            )
            == "COMPLETE_FAIL"
        )
        assert (
            authoritative_field_value("CROSS_SECTIONAL_FUNDING_RATE_CARRY_V0_PROMOTION_ELIGIBLE")
            == "false"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_FUNDING_RATE_CARRY_V0_RETRY_UNCHANGED_BINDING_ALLOWED"
            )
            == "false"
        )

    def test_research_line_section_terminal_fail(self) -> None:
        section = _funding_carry_section(read_registry())
        assert _field_value(section, "STATUS") == "COMPLETE_FAIL"
        assert _field_value(section, "ECONOMIC_EVALUATION_STATUS") == "COMPLETE_FAIL"
        assert _field_value(section, "PROMOTION_ELIGIBLE") == "false"
        assert _field_value(section, "RETRY_UNCHANGED_BINDING_ALLOWED") == "false"
        assert _field_value(section, "BINDING_CHANGED") == "false"
        assert _field_value(section, "POLICY_OR_THRESHOLD_CHANGED") == "false"
        assert _field_value(section, "TRADE_COUNT") == "0"
        assert _field_value(section, "FULL_OFFLINE_EVALUATION_RUNNER_STATUS") == (
            "MAINLINE_AVAILABLE"
        )
        assert _field_value(section, "RE_EVALUATION_ALLOWED") == "false"
        assert _field_value(section, "EVALUATION_AUTHORIZED") == "false"

    def test_durable_evidence_refs_present(self) -> None:
        section = _funding_carry_section(read_registry())
        refs = _field_value(section, "DURABLE_EVIDENCE_REFS")
        assert ECONOMIC_EVIDENCE_REF in refs
        assert EXECUTION_INFRA_CLOSEOUT_REF in refs
        assert FULL_RUNNER_CLOSEOUT_REF in refs
        assert "MANIFEST_VERIFY_RC=0" in refs

    def test_registry_resolver_loads_without_ambiguity(self) -> None:
        registry = load_registry()
        assert registry.authoritative_value("CROSS_SECTIONAL_FUNDING_RATE_CARRY_V0_STATUS") == (
            "COMPLETE_FAIL"
        )

    def test_evidence_registry_reconciliation_ref_bound(self) -> None:
        ref = authoritative_field_value(
            "CROSS_SECTIONAL_FUNDING_RATE_CARRY_V0_EVIDENCE_REGISTRY_RECONCILIATION_EVIDENCE_REF"
        )
        assert ref != "PENDING_POST_MERGE"
        assert EVIDENCE_REGISTRY_RECONCILIATION_CLOSEOUT_REF in ref
        assert "MANIFEST_VERIFY_RC=0" in ref
        assert "PR #4797" in ref
        assert "PR_HEAD=5e25c8115d3da8fea1b9b0479a93198c05ef03cc" in ref
        assert "squash d1eea783" in ref
        assert "ORIGIN_MAIN_AFTER=d1eea783e21ad3c968a5cde75abbf2ff865413f8" in ref

    def test_research_line_progress_registry_closeout_performed(self) -> None:
        section = _funding_carry_section(read_registry())
        assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
        assert _field_value(section, "NO_NEW_CANDIDATE_HOLD") == "REVOKED"

    def test_global_no_new_candidate_hold_revoked_and_next_step_reconciled(self) -> None:
        assert authoritative_field_value("NO_NEW_CANDIDATE_HOLD") == "REVOKED"
        assert (
            authoritative_field_value("NEXT_CANONICAL_ACTION")
            == "RATIFY_VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE"
        )
