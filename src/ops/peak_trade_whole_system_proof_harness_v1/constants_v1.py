"""Whole-System Proof Harness V1 — observational only; AUTHORITY=NONE."""

from __future__ import annotations

OWNER = "ops.peak_trade_whole_system_proof_harness_v1"
CONTRACT_VERSION = "peak_trade_whole_system_proof_harness.v1"
MANIFEST_SCHEMA_VERSION = "whole_system_proof_manifest.v1"

BASELINE_ORIGIN_MAIN_SHA = "2761aab69beb00564892d417818b7a35eb6794a7"

DEFAULT_OPERATION_SPEC_REL = (
    "config/ops/peak_trade_whole_system_proof_harness_v1/operations/"
    "policy_governed_live_c1_pre_external_v1.json"
)

PREVIOUS_CLOSURE_EVIDENCE_REL = (
    "evidence/research/whole_system_semantic_closure_ghv_startable_setting_v1/20261005T195200Z"
)

EVIDENCE_ROOT_REL = "evidence/research/peak_trade_whole_system_proof_harness_v1"

COVERAGE_RESULT_VALUES = frozenset(
    {"PROVEN", "PARTIALLY_PROVEN", "UNKNOWN", "CONFLICTING", "VIOLATED"}
)

EXCLUSION_CLASSIFICATIONS = frozenset(
    {"REQUIRED", "CONDITIONALLY_REQUIRED", "NOT_REQUIRED_WITH_PROOF", "UNKNOWN_RELEVANCE"}
)
