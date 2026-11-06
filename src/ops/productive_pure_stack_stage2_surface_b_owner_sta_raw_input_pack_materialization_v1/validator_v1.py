"""Fail-closed validator for Surface-B raw input-pack materialization execution v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    canonical_json_bytes,
)
from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_v1.materializer_v1 import (
    materialize_raw_input_observation_pack_v1,
)


class RawInputPackMaterializationExecutionErrorV1(ValueError):
    """Fail-closed materialization execution validation error."""


def _require_mapping(raw: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise RawInputPackMaterializationExecutionErrorV1(f"MAPPING_REQUIRED:{label}")
    return raw


def _assert_exact(value: Any, expected: Any, *, label: str) -> None:
    if value != expected:
        raise RawInputPackMaterializationExecutionErrorV1(f"VALUE_MISMATCH:{label}")


def _assert_false(value: Any, *, label: str) -> None:
    if value is True:
        raise RawInputPackMaterializationExecutionErrorV1(f"MUST_REMAIN_FALSE:{label}")
    if value not in (False, None) and bool(value):
        raise RawInputPackMaterializationExecutionErrorV1(f"MUST_REMAIN_FALSE:{label}")


def _assert_true(value: Any, *, label: str) -> None:
    if value is not True:
        raise RawInputPackMaterializationExecutionErrorV1(f"MUST_BE_TRUE:{label}")


def _assert_null(value: Any, *, label: str) -> None:
    if value is not None:
        raise RawInputPackMaterializationExecutionErrorV1(f"MUST_REMAIN_NULL:{label}")


def _assert_sha256_hex(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise RawInputPackMaterializationExecutionErrorV1(f"SHA256_HEX_REQUIRED:{label}")
    try:
        int(value, 16)
    except ValueError as exc:
        raise RawInputPackMaterializationExecutionErrorV1(f"SHA256_HEX_REQUIRED:{label}") from exc
    return value


def load_canonical_raw_input_pack_materialization_execution_manifest_v1(
    repo_root: Path,
) -> dict[str, Any]:
    path = Path(repo_root).resolve() / C.DECISIONS_MANIFEST_REL
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(_require_mapping(payload, label="execution_manifest"))


def validate_raw_input_pack_materialization_execution_manifest_v1(
    manifest: Mapping[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    _assert_exact(manifest.get("schema_version"), C.SCHEMA_VERSION, label="schema_version")
    _assert_exact(manifest.get("document_type"), C.DOCUMENT_TYPE, label="document_type")
    _assert_exact(manifest.get("capability_scope"), C.CAPABILITY_SCOPE, label="capability_scope")
    _assert_exact(manifest.get("status"), C.STATUS, label="status")
    _assert_exact(manifest.get("owner_go"), C.OWNER_GO, label="owner_go")
    _assert_exact(manifest.get("owner_go_base_sha"), C.OWNER_GO_BASE_SHA, label="owner_go_base_sha")
    _assert_exact(manifest.get("scope"), C.SCOPE, label="scope")
    _assert_exact(manifest.get("decision_id"), C.DECISION_ID, label="decision_id")
    _assert_exact(manifest.get("decision_status"), C.DECISION_STATUS, label="decision_status")
    _assert_exact(manifest.get("owner_value"), C.OWNER_VALUE, label="owner_value")

    _assert_true(manifest.get("pack_materialization"), label="pack_materialization")
    _assert_true(manifest.get("raw_input_pack_created"), label="raw_input_pack_created")
    _assert_true(
        manifest.get("raw_input_pack_materialization_authorized"),
        label="raw_input_pack_materialization_authorized",
    )
    _assert_true(
        manifest.get("use_recorded_instance_values"),
        label="use_recorded_instance_values",
    )
    _assert_false(manifest.get("campaign_start"), label="campaign_start")
    _assert_false(manifest.get("campaign_start_authorized"), label="campaign_start_authorized")
    _assert_false(manifest.get("campaign_started"), label="campaign_started")
    _assert_false(manifest.get("input_authority"), label="input_authority")
    _assert_false(manifest.get("runtime_implemented"), label="runtime_implemented")
    _assert_false(
        manifest.get("regime_coverage_producer_available"),
        label="regime_coverage_producer_available",
    )
    _assert_false(
        manifest.get("productive_thresholds_lookbacks"),
        label="productive_thresholds_lookbacks",
    )
    _assert_false(manifest.get("trading_logic_change"), label="trading_logic_change")
    _assert_false(manifest.get("orders_testnet_live"), label="orders_testnet_live")
    _assert_false(manifest.get("invented_values"), label="invented_values")
    _assert_false(manifest.get("silent_defaults"), label="silent_defaults")
    _assert_false(manifest.get("proposed_values"), label="proposed_values")
    _assert_exact(
        manifest.get("dashboard_authority_effect"),
        "NONE",
        label="dashboard_authority_effect",
    )
    _assert_exact(
        manifest.get("regime_coverage_status"),
        C.REGIME_COVERAGE_STATUS,
        label="regime_coverage_status",
    )
    if int(manifest.get("productive_numeric_values_set", -1)) != 0:
        raise RawInputPackMaterializationExecutionErrorV1(
            "PRODUCTIVE_NUMERIC_VALUES_MUST_REMAIN_ZERO"
        )

    proofs = _require_mapping(
        manifest.get("materialization_proofs"), label="materialization_proofs"
    )
    _assert_exact(proofs.get("dataset_id"), C.DATASET_ID, label="dataset_id")
    _assert_exact(proofs.get("scenario_id"), C.SCENARIO_ID, label="scenario_id")
    _assert_null(proofs.get("campaign_id"), label="campaign_id")
    _assert_exact(proofs.get("seed"), C.SEED, label="seed")
    _assert_exact(
        proofs.get("event_time_epoch_s"), C.EVENT_TIME_EPOCH_S, label="event_time_epoch_s"
    )
    _assert_exact(proofs.get("raw_source_digest"), C.RAW_SOURCE_DIGEST, label="raw_source_digest")
    _assert_sha256_hex(proofs.get("observation_pack_digest"), label="observation_pack_digest")
    _assert_exact(
        proofs.get("observation_pack_digest"),
        C.OBSERVATION_PACK_DIGEST,
        label="observation_pack_digest",
    )
    _assert_exact(proofs.get("config_digest"), C.CONFIG_DIGEST, label="config_digest")
    _assert_exact(proofs.get("repository_sha"), C.REPOSITORY_SHA, label="repository_sha")
    _assert_exact(proofs.get("bar_count"), C.BAR_COUNT, label="bar_count")
    _assert_null(proofs.get("regime_coverage_counts"), label="regime_coverage_counts")
    _assert_null(proofs.get("regime_coverage_instance"), label="regime_coverage_instance")

    binding = _require_mapping(proofs.get("instrument_binding"), label="instrument_binding")
    for key, expected in C.INSTRUMENT_BINDING.items():
        _assert_exact(binding.get(key), expected, label=f"instrument_binding.{key}")

    remaining = proofs.get("remaining_null_fields")
    if tuple(remaining or ()) != C.REMAINING_NULL_FIELDS:
        raise RawInputPackMaterializationExecutionErrorV1("REMAINING_NULL_FIELDS_MISMATCH")

    # Sealed artifacts exist and rebuild matches.
    pack_path = root / C.OBSERVATION_PACK_REL
    proof_path = root / C.MATERIALIZATION_PROOF_REL
    digest_txt = root / C.OBSERVATION_PACK_DIGEST_TXT_REL
    if not pack_path.is_file():
        raise RawInputPackMaterializationExecutionErrorV1("OBSERVATION_PACK_ARTIFACT_MISSING")
    if not proof_path.is_file():
        raise RawInputPackMaterializationExecutionErrorV1("MATERIALIZATION_PROOF_ARTIFACT_MISSING")
    if not digest_txt.is_file():
        raise RawInputPackMaterializationExecutionErrorV1("DIGEST_TXT_MISSING")
    if digest_txt.read_text(encoding="utf-8").strip() != C.OBSERVATION_PACK_DIGEST:
        raise RawInputPackMaterializationExecutionErrorV1("DIGEST_TXT_MISMATCH")

    sealed_pack = json.loads(pack_path.read_text(encoding="utf-8"))
    rebuilt = materialize_raw_input_observation_pack_v1(repo_root=root)
    if rebuilt.to_dict() != sealed_pack:
        raise RawInputPackMaterializationExecutionErrorV1("SEALED_PACK_REBUILD_MISMATCH")
    pack_bytes = canonical_json_bytes(sealed_pack)
    pack_sha = hashlib.sha256(pack_bytes).hexdigest()
    if pack_sha != C.OBSERVATION_PACK_CANONICAL_JSON_SHA256:
        raise RawInputPackMaterializationExecutionErrorV1("PACK_CANONICAL_JSON_SHA256_MISMATCH")

    sealed_proof = json.loads(proof_path.read_text(encoding="utf-8"))
    _assert_exact(
        sealed_proof.get("observation_pack_digest"),
        C.OBSERVATION_PACK_DIGEST,
        label="sealed_proof.observation_pack_digest",
    )
    _assert_true(
        sealed_proof.get("pack_materialization"), label="sealed_proof.pack_materialization"
    )
    _assert_true(
        sealed_proof.get("raw_input_pack_created"), label="sealed_proof.raw_input_pack_created"
    )
    _assert_false(sealed_proof.get("campaign_start"), label="sealed_proof.campaign_start")
    _assert_false(sealed_proof.get("input_authority"), label="sealed_proof.input_authority")
    _assert_false(sealed_proof.get("runtime_implemented"), label="sealed_proof.runtime_implemented")

    return {
        "ok": True,
        "owner_go": C.OWNER_GO,
        "status": C.STATUS,
        "decision_id": C.DECISION_ID,
        "observation_pack_digest": C.OBSERVATION_PACK_DIGEST,
        "raw_source_digest": C.RAW_SOURCE_DIGEST,
        "pack_materialization": True,
        "raw_input_pack_created": True,
        "raw_input_pack_materialization_authorized": True,
        "campaign_start": False,
        "input_authority": False,
        "runtime_implemented": False,
        "bar_count": C.BAR_COUNT,
        "remaining_null_fields": list(C.REMAINING_NULL_FIELDS),
    }


__all__ = [
    "RawInputPackMaterializationExecutionErrorV1",
    "load_canonical_raw_input_pack_materialization_execution_manifest_v1",
    "validate_raw_input_pack_materialization_execution_manifest_v1",
]
