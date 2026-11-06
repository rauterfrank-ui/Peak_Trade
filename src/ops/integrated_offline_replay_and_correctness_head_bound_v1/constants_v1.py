"""Constants for HEAD-bound integrated offline replay correctness proof v1."""

from __future__ import annotations

CAPABILITY_ID = "INTEGRATED_OFFLINE_REPLAY_AND_CORRECTNESS_HEAD_BOUND_V1"
PACKAGE_MARKER = "INTEGRATED_OFFLINE_REPLAY_AND_CORRECTNESS_HEAD_BOUND_V1=true"
PRODUCER_FAMILY = "ops.integrated_offline_replay_and_correctness_head_bound_v1"
SCHEMA_ID = PRODUCER_FAMILY
SCHEMA_VERSION = "v1"
AUTHORITY_EFFECT_NONE = "NONE"

CONFIG_RELPATH = "config/ops/integrated_offline_replay_and_correctness_head_bound_v1.toml"

PROOF_ARTIFACT_NAME = "INTEGRATED_OFFLINE_REPLAY_AND_CORRECTNESS_HEAD_BOUND_PROOF.json"
MANIFEST_NAME = "evidence_manifest.sha256"

INPUT_CLASS_CONTROLLED_FIXTURE = "CONTROLLED_FIXTURE_LIFECYCLE"
CRS_PROVENANCE = (
    "wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1."
    "simulated_economics_crs_boundary_binding_v1.build_simulated_economics_crs_boundary_state_file_v1"
)
