"""Offline parameter sensitivity productive input join materializer v0.

Deterministic, offline-only join of ratified final-research-fleet signal matrix rows
to parameter sensitivity inputs via the operator-ratified productive contract v0.
Reuses ``validate_productive_binding_batch_v0`` as the sole join owner. No OLS,
economic evaluation, runtime, order, scheduler, or authority effect.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.linear_evidence.parameter_sensitivity_productive_contract_v0 import (
    AUTHORITY_EFFECT,
    ALLOWED_CALIBRATABLE_PARAMETERS,
    ParameterSensitivityProductiveBindingV0,
    ParameterSensitivityProductiveProvenanceV0,
    ProductiveBindingValidationResultV0,
    RUNTIME_EFFECT,
    load_productive_parameter_grid_v0,
    stable_digest_v0,
    validate_productive_binding_batch_v0,
)
from src.research.linear_evidence.sensitivity import ParameterSensitivityInputV1
from src.research.linear_evidence.signal_matrix_productive_contract_v0 import (
    compute_signal_matrix_digest_v0,
)
from src.research.offline_final_research_fleet_signal_matrix_productive_input_join_materializer_v0 import (
    load_ratified_binding_completion_v0,
)

PACKAGE_MARKER = "OFFLINE_PARAMETER_SENSITIVITY_PRODUCTIVE_INPUT_JOIN_MATERIALIZER_V0=true"
SCHEMA_VERSION = "offline_parameter_sensitivity_productive_input_join_materializer.v0"
CANONICAL_CONTRACT_OWNER = (
    "src/research/linear_evidence/parameter_sensitivity_productive_contract_v0.py"
)
CANONICAL_GRID_OWNER = "src/backtest/parameter_sensitivity_v1.py"
IMPLEMENTATION_DIGEST = stable_digest_v0(
    {
        "contract": SCHEMA_VERSION,
        "join_owner": CANONICAL_CONTRACT_OWNER,
        "grid_owner": CANONICAL_GRID_OWNER,
        "allowed_parameters": list(ALLOWED_CALIBRATABLE_PARAMETERS),
    }
)


class MaterializationStatus(str, Enum):
    PASS = "PASS"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    TARGET_BINDING_MISSING = "TARGET_BINDING_MISSING"


@dataclass(frozen=True)
class MaterializationResultV0:
    status: MaterializationStatus
    records: tuple[ParameterSensitivityInputV1, ...]
    join_result: ProductiveBindingValidationResultV0
    provenance: ParameterSensitivityProductiveProvenanceV0
    materialization_digest: str
    output_digest: str
    productive_input_digest: str
    grid_digest: str
    source_binding_digest: str
    source_signal_matrix_digest: str
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


def load_signal_matrix_rows(path: Path) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    if path.suffix.lower() == ".jsonl":
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                raise ValueError("JSONL_ROW_NOT_OBJECT")
            rows.append(payload)
        return tuple(rows)
    if path.suffix.lower() == ".csv":
        import csv

        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                payload = {key: row[key] for key in row}
                for signal_key in ("bollinger_bands", "momentum_1h", "trend_following"):
                    if signal_key in payload:
                        payload[signal_key] = float(payload[signal_key])
                rows.append(payload)
        return tuple(rows)
    raise ValueError(f"UNSUPPORTED_SIGNAL_MATRIX_FORMAT:{path.suffix}")


def compute_source_rows_digest(rows: Sequence[Mapping[str, Any]]) -> str:
    ordered = sorted(
        rows,
        key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":"), default=str),
    )
    return stable_digest_v0({"rows": list(ordered), "schema": "offline_signal_matrix_rows_v0"})


def _serialize_records(records: Sequence[ParameterSensitivityInputV1]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for record in records:
        payload.append(
            {
                "instrument_id": record.instrument_id,
                "decision_time": record.decision_time,
                "feature_availability_time": record.feature_availability_time,
                "target": record.target,
                "features": dict(record.features),
            }
        )
    return payload


def build_productive_provenance_v0(
    *,
    join_result: ProductiveBindingValidationResultV0,
    source_binding_digest: str,
    source_signal_matrix_digest: str,
) -> ParameterSensitivityProductiveProvenanceV0:
    return ParameterSensitivityProductiveProvenanceV0(
        binding_digest=source_binding_digest,
        signal_matrix_digest=source_signal_matrix_digest,
        grid_digest=join_result.grid.grid_digest,
        strategy_id=join_result.binding.strategy_id,
        strategy_version=join_result.binding.strategy_version,
        row_count_before_filter=join_result.row_count_before_filter,
        row_count_after_filter=join_result.row_count_after_filter,
        dropped_rows_by_reason=dict(join_result.dropped_rows_by_reason),
        implementation_digest=IMPLEMENTATION_DIGEST,
    )


def materialize_offline_parameter_sensitivity_productive_inputs_v0(
    *,
    signal_matrix_rows: Sequence[Mapping[str, Any]],
    repo_root: Path,
    binding_completion: Mapping[str, Any] | None = None,
    strategy_id: str = "trend_following",
    source_binding_digest: str | None = None,
    source_signal_matrix_digest: str | None = None,
) -> MaterializationResultV0:
    binding_payload = binding_completion or load_ratified_binding_completion_v0(repo_root)
    binding_digest = source_binding_digest or str(binding_payload.get("completion_digest", ""))

    if not signal_matrix_rows:
        provenance = ParameterSensitivityProductiveProvenanceV0(
            binding_digest=binding_digest,
            implementation_digest=IMPLEMENTATION_DIGEST,
        )
        return MaterializationResultV0(
            status=MaterializationStatus.INSUFFICIENT_DATA,
            records=(),
            join_result=ProductiveBindingValidationResultV0(
                admissible_records=(),
                rejected=(),
                row_count_before_filter=0,
                row_count_after_filter=0,
                dropped_rows_by_reason={},
                binding=ParameterSensitivityProductiveBindingV0(binding_digest=binding_digest),
                grid=load_productive_parameter_grid_v0(
                    repo_root=repo_root,
                    strategy_id=strategy_id,
                    data_digest=str(
                        binding_payload.get("shared_bindings", {})
                        .get("dataset_binding", {})
                        .get("data_digest", "")
                    ),
                ),
                grid_specs=(),
            ),
            provenance=provenance,
            materialization_digest=stable_digest_v0(
                {"schema_version": SCHEMA_VERSION, "empty": True}
            ),
            output_digest=stable_digest_v0({"schema_version": SCHEMA_VERSION, "empty": True}),
            productive_input_digest=stable_digest_v0(
                {"schema_version": SCHEMA_VERSION, "empty": True}
            ),
            grid_digest="",
            source_binding_digest=binding_digest,
            source_signal_matrix_digest="",
        )

    signal_digest = source_signal_matrix_digest or compute_signal_matrix_digest_v0(
        signal_matrix_rows
    )

    join_result = validate_productive_binding_batch_v0(
        signal_matrix_rows=signal_matrix_rows,
        binding_completion=binding_payload,
        repo_root=repo_root,
        strategy_id=strategy_id,
        expected_binding_digest=binding_digest,
        expected_signal_matrix_digest=signal_digest,
    )
    records = join_result.admissible_records
    serialized = _serialize_records(records)
    productive_input_digest = stable_digest_v0(
        {
            "schema_version": SCHEMA_VERSION,
            "records": serialized,
        }
    )
    output_digest = stable_digest_v0(
        {
            "schema_version": SCHEMA_VERSION,
            "productive_input_digest": productive_input_digest,
            "grid_digest": join_result.grid.grid_digest,
            "row_count_after_filter": join_result.row_count_after_filter,
        }
    )
    materialization_digest = stable_digest_v0(
        {
            "schema_version": SCHEMA_VERSION,
            "output_digest": output_digest,
            "source_binding_digest": binding_digest,
            "source_signal_matrix_digest": signal_digest,
            "grid_digest": join_result.grid.grid_digest,
            "dropped_rows_by_reason": dict(join_result.dropped_rows_by_reason),
        }
    )
    provenance = build_productive_provenance_v0(
        join_result=join_result,
        source_binding_digest=binding_digest,
        source_signal_matrix_digest=signal_digest,
    )

    if not signal_matrix_rows:
        status = MaterializationStatus.INSUFFICIENT_DATA
    elif not records:
        status = MaterializationStatus.TARGET_BINDING_MISSING
    else:
        status = MaterializationStatus.PASS

    return MaterializationResultV0(
        status=status,
        records=records,
        join_result=join_result,
        provenance=provenance,
        materialization_digest=materialization_digest,
        output_digest=output_digest,
        productive_input_digest=productive_input_digest,
        grid_digest=join_result.grid.grid_digest,
        source_binding_digest=binding_digest,
        source_signal_matrix_digest=signal_digest,
    )


def materialize_from_manifest_paths_v0(
    *,
    repo_root: Path,
    signal_matrix_path: Path,
    binding_completion_path: Path | None = None,
    strategy_id: str = "trend_following",
) -> MaterializationResultV0:
    signal_rows = load_signal_matrix_rows(signal_matrix_path)
    binding_payload: Mapping[str, Any] | None = None
    if binding_completion_path is not None:
        binding_payload = json.loads(binding_completion_path.read_text(encoding="utf-8"))
    return materialize_offline_parameter_sensitivity_productive_inputs_v0(
        signal_matrix_rows=signal_rows,
        repo_root=repo_root,
        binding_completion=binding_payload,
        strategy_id=strategy_id,
    )


def serialize_materialized_productive_inputs_v0(
    records: Sequence[ParameterSensitivityInputV1],
) -> str:
    ordered = sorted(
        records,
        key=lambda record: (record.decision_time, record.instrument_id),
    )
    lines = [
        json.dumps(
            {
                "instrument_id": record.instrument_id,
                "decision_time": record.decision_time,
                "feature_availability_time": record.feature_availability_time,
                "target": record.target,
                "features": dict(record.features),
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        for record in ordered
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def materializer_to_contract_roundtrip_pass_v0(
    result: MaterializationResultV0,
) -> bool:
    if result.status != MaterializationStatus.PASS:
        return False
    if not result.records:
        return False
    for spec in result.join_result.grid_specs:
        if spec.parameter_name not in ALLOWED_CALIBRATABLE_PARAMETERS:
            return False
        if spec.scaled_feature_name != spec.parameter_name:
            return False
    return bool(result.join_result.binding.binding_digest)
