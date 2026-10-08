"""Shared B2 fixture builders for integrated offline economic evidence tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.backtest.admissible_versioned_futures_dataset_v1 import TIMESTAMP_SEMANTICS
from src.ops.integrated_offline_economic_evidence_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    COMPARISON_CLASS_PRODUCTIVE_CURRENT,
    DECISION_EQUIVALENCE_SCHEMA_ID,
    DECISION_EQUIVALENCE_SCHEMA_VERSION,
    DECISION_EQUIVALENCE_VERIFIER_ID,
    MD_BRIDGE_CONTRACT_ID,
    MD_BRIDGE_SCHEMA_ID,
    MD_BRIDGE_SCHEMA_VERSION,
    MD_BRIDGE_VERIFIER_ID,
    OFFLINE_DATASET_OWNER,
)
from src.ops.integrated_offline_economic_evidence_v1.decision_input_fingerprint_v1 import (
    compute_decision_input_fingerprint_digest_sha256_v1,
    compute_productive_gate_bindings_digest_sha256_v1,
)

FIXTURE_PREFIX = "tests/fixtures/ops/integrated_offline_economic_evidence_b2_v1/minimal_productive"


def _d(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def shared_md_semantics_v1() -> dict[str, str]:
    return {
        "canonical_instrument_id": "ETH-USD_UM_XPERP-310404",
        "venue": "okx_eea",
        "venue_native_id": "ETH-USD_UM_XPERP-310404",
        "market_type": "linear_perpetual",
        "contract_type": "um_xperp",
        "timeframe": "1m",
        "bar_construction_policy": "utc_close_ohlcv_v1",
        "timestamp_semantics": TIMESTAMP_SEMANTICS,
        "price_basis": "mark_price",
        "volume_semantics": "base_volume",
        "spread_l1_assumptions": "OBSERVED_HISTORICAL_L1",
        "funding_input_semantics": "bar_funding_rate",
        "missing_data_policy": "FAIL_CLOSED_ON_REQUIRED_FIELD_MISSING",
        "warmup_policy": "NO_WARMUP_SKIP",
        "normalization_policy": "NONE",
    }


def build_md_bridge_document_v1(*, dataset_digest: str, mapping_digest: str) -> dict[str, Any]:
    semantics = shared_md_semantics_v1()
    return {
        "schema_id": MD_BRIDGE_SCHEMA_ID,
        "schema_version": MD_BRIDGE_SCHEMA_VERSION,
        "authority_effect": AUTHORITY_EFFECT_NONE,
        "verifier_id": MD_BRIDGE_VERIFIER_ID,
        "bridge_contract_id": MD_BRIDGE_CONTRACT_ID,
        "offline_dataset_owner": OFFLINE_DATASET_OWNER,
        "dataset_version": "v1",
        "dataset_content_digest_sha256": dataset_digest,
        "instrument_mapping_digest_sha256": mapping_digest,
        "current_offline_md_semantics_v1": dict(semantics),
        "offline_dataset_semantics_v1": dict(semantics),
        "time_range_coverage_v1": {
            "required_start_time": "2026-01-01T00:00:00Z",
            "required_end_time": "2026-01-02T00:00:00Z",
            "dataset_start_time": "2026-01-01T00:00:00Z",
            "dataset_end_time": "2026-01-03T00:00:00Z",
        },
    }


def build_decision_equivalence_document_v1(
    *,
    md_attestation_digest: str,
    decision_config_digest: str,
    registry_digest: str,
    capital_digest: str,
) -> dict[str, Any]:
    gate_binding = {
        "g17_typed_volatility_binding_mode": "MUST_RECONSTRUCT",
        "cap61_observation_acceptance_binding_mode": "MUST_REPLAY",
        "confirmation_progression_binding_mode": "MUST_REPLAY",
    }
    gate_digest = compute_productive_gate_bindings_digest_sha256_v1(
        productive_gate_binding_v1=gate_binding
    )
    input_binding = {
        "canonical_instrument_id": "ETH-USD_UM_XPERP-310404",
        "decision_config_digest_sha256": decision_config_digest,
        "strategy_registry_snapshot_digest_sha256": registry_digest,
        "market_data_bridge_attestation_digest_sha256": md_attestation_digest,
        "productive_gate_bindings_digest_sha256": gate_digest,
        "component_version_digest_sha256": _d("components"),
        "policy_version_digest_sha256": _d("policies"),
        "capital_context_digest_sha256": capital_digest,
    }
    fingerprint = compute_decision_input_fingerprint_digest_sha256_v1(binding=input_binding)
    decision_fields = {
        "decision": "ENTER_LONG",
        "side": "long",
        "selected_strategy_ref": "double_play:v0",
        "scope_gge_outcome": "ALLOW",
        "suitability_ranking_outcome": "SELECTED",
        "double_play_transition": "ARMED_TO_ENTER",
        "risk_result": "ALLOW",
        "sizing_result": "SIZED",
        "canonical_order_intent_present": False,
    }
    return {
        "schema_id": DECISION_EQUIVALENCE_SCHEMA_ID,
        "schema_version": DECISION_EQUIVALENCE_SCHEMA_VERSION,
        "authority_effect": AUTHORITY_EFFECT_NONE,
        "verifier_id": DECISION_EQUIVALENCE_VERIFIER_ID,
        "equivalence_class": COMPARISON_CLASS_PRODUCTIVE_CURRENT,
        "productive_gate_binding_v1": gate_binding,
        "comparison_rows": [
            {
                "row_id": "row-0",
                "required": True,
                "canonical_instrument_id": "ETH-USD_UM_XPERP-310404",
                "observation_id": "obs-1",
                "epoch_id": "epoch-1",
                "decision_input_fingerprint_digest_sha256": fingerprint,
                "decision_input_binding_v1": input_binding,
                "current_decision_v1": dict(decision_fields),
                "offline_decision_v1": dict(decision_fields),
            }
        ],
    }


def write_minimal_productive_b2_fixtures(repo_root: Path) -> dict[str, str]:
    """Materialize canonical B2 fixture artifacts; returns relpath -> sha256 map."""
    base = repo_root / FIXTURE_PREFIX
    base.mkdir(parents=True, exist_ok=True)
    dataset_digest = _d("dataset")
    mapping_digest = _d("map")
    md_doc = build_md_bridge_document_v1(
        dataset_digest=dataset_digest,
        mapping_digest=mapping_digest,
    )
    md_path = base / "CURRENT_OFFLINE_MD_BRIDGE_V1.json"
    md_path.write_text(json.dumps(md_doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_digest = hashlib.sha256(md_path.read_bytes()).hexdigest()
    de_doc = build_decision_equivalence_document_v1(
        md_attestation_digest=md_digest,
        decision_config_digest=_d("decision_cfg"),
        registry_digest=_d("registry"),
        capital_digest=_d("capital"),
    )
    de_path = base / "CURRENT_OFFLINE_DECISION_EQUIVALENCE_V1.json"
    de_path.write_text(json.dumps(de_doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    de_digest = hashlib.sha256(de_path.read_bytes()).hexdigest()
    return {
        "md_relpath": f"{FIXTURE_PREFIX}/CURRENT_OFFLINE_MD_BRIDGE_V1.json",
        "md_digest": md_digest,
        "de_relpath": f"{FIXTURE_PREFIX}/CURRENT_OFFLINE_DECISION_EQUIVALENCE_V1.json",
        "de_digest": de_digest,
        "dataset_digest": dataset_digest,
        "mapping_digest": mapping_digest,
    }
