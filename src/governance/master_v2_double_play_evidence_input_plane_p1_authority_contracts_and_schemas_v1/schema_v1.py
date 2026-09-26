"""Canonical deterministic schema manifests for P1 contracts (immutable definitions)."""

from __future__ import annotations

import json
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.constants_v1 import (
    BINDING_SCHEMA_VERSION,
    ENVELOPE_SCHEMA_VERSION,
    L6_TYPED_INPUT_SCHEMA_VERSION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    ALLOWED_L6_EVIDENCE_KINDS_V1,
    ALLOWED_PRODUCER_FAMILIES_V1,
    P1_ALLOWED_B_TARGET_LAYERS_V1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

CANONICAL_MASTER_V2_EVIDENCE_ENVELOPE_V1: Final[Mapping[str, Any]] = MappingProxyType(
    {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "required_fields": (
            "envelope_id",
            "producer_family",
            "evidence_kind",
            "instrument",
            "market_observation_epoch",
            "observed_at_unix",
            "freshness_horizon_seconds",
            "source_evidence_digest",
            "typed_payload_digest",
            "provenance_refs",
            "trading_authority",
            "adjudication_path",
        ),
        "forbidden_fields": (
            "proposed_d_t",
            "d_t",
            "final_d_t",
            "computed_d_t",
            "formula_id",
        ),
        "allowed_producer_families": tuple(sorted(f.value for f in ALLOWED_PRODUCER_FAMILIES_V1)),
        "allowed_evidence_kinds": tuple(sorted(k.value for k in ALLOWED_L6_EVIDENCE_KINDS_V1)),
        "trading_authority_fixed": "NONE",
    }
)

CANONICAL_DP_LAYER_INPUT_BINDING_V1: Final[Mapping[str, Any]] = MappingProxyType(
    {
        "schema_version": BINDING_SCHEMA_VERSION,
        "required_fields": (
            "binding_id",
            "target_layer",
            "envelope_digest",
            "instrument",
            "market_observation_epoch",
            "nullline_provenance_epoch",
            "binding_evaluated_at_unix",
            "trading_authority",
            "dp_state_mutation_authority",
            "producer_to_b_direct",
        ),
        "forbidden_fields": (
            "proposed_d_t",
            "d_t",
            "final_d_t",
            "computed_d_t",
            "formula_id",
        ),
        "allowed_target_layers": tuple(sorted(l.value for l in P1_ALLOWED_B_TARGET_LAYERS_V1)),
        "trading_authority_fixed": "NONE",
        "dp_state_mutation_authority_fixed": "NONE",
        "b_may_compute_final_d_t": False,
        "b_may_select_d_t_formula": False,
        "b_may_collapse_to_proposed_d_t": False,
    }
)

L6_BOUNDED_TYPED_EXTERNAL_EVIDENCE_INPUT_V1: Final[Mapping[str, Any]] = MappingProxyType(
    {
        "schema_version": L6_TYPED_INPUT_SCHEMA_VERSION,
        "required_fields": (
            "input_id",
            "target_layer",
            "evidence_kind",
            "instrument",
            "market_observation_epoch",
            "nullline_provenance_epoch",
            "envelope_digest",
            "binding_digest",
            "source_evidence_digest",
            "typed_payload_digest",
            "provenance_refs",
            "interpretation_authority",
        ),
        "forbidden_fields": ("proposed_d_t", "d_t", "final_d_t", "computed_d_t"),
        "interpretation_authority_fixed": "L6_ONLY",
        "target_layer_fixed": "L6_DYNAMIC_SCOPE_GENERATOR",
    }
)


def canonical_schema_manifest_v1() -> dict[str, Any]:
    return {
        "canonical_dp_layer_input_binding_v1": dict(CANONICAL_DP_LAYER_INPUT_BINDING_V1),
        "canonical_master_v2_evidence_envelope_v1": dict(CANONICAL_MASTER_V2_EVIDENCE_ENVELOPE_V1),
        "l6_bounded_typed_external_evidence_input_v1": dict(
            L6_BOUNDED_TYPED_EXTERNAL_EVIDENCE_INPUT_V1
        ),
    }


def canonical_schema_manifest_digest_v1() -> str:
    payload = canonical_schema_manifest_v1()
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return compute_content_sha256({"canonical_json": canonical})
