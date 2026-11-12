"""Measure a declared later mark-price horizon for an observed F1/M9 application."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from src.learning.deterministic_decision_outcome_v0.independent_market_horizon_v1 import (
    build_independent_market_return_target_v1,
    validate_independent_market_horizon_v1,
)
from src.learning.deterministic_decision_outcome_v0.o4_n_bars_bar_evidence_bridge_contracts_v1 import (
    derive_o4_bar_spec_ref_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    instant_v1,
    seal_v1,
    strict_json_v1,
    validate_seal_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_recorded_market_replay_v1 import (
    RecordedMarkArchiveV1,
    measure_recorded_market_horizon_v1,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex
from src.ops.f1_m9_applied_offline_replay_v1 import read_f1_m9_applied_offline_replay_v1

_PLAN_SCHEMA = "f1_m9_applied_replay_market_outcome_plan_v1"
_MEASUREMENT_SCHEMA = "f1_m9_applied_replay_market_outcome_v1"
_COMPARISON_STATUS = "COMPARABLE_EXECUTION_EVIDENCE_REQUIRED"


def _publish(path: Path, payload: dict[str, Any]) -> None:
    data = bytes_v1(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, prefix=".outcome-", delete=False) as stream:
        staging = Path(stream.name)
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            try:
                os.link(staging, path)
            except FileExistsError:
                if path.read_bytes() != data:
                    raise ValueError("F1_M9_MARKET_OUTCOME_RECORD_CONFLICT") from None
        finally:
            staging.unlink()


def _plan(
    *,
    host_evidence_path: Path,
    host_evidence_sha256: str,
    market_request: Mapping[str, Any],
    declared_at_utc: str,
) -> dict[str, Any]:
    archived = read_f1_m9_applied_offline_replay_v1(
        evidence_path=host_evidence_path, expected_sha256=host_evidence_sha256
    )
    target = build_independent_market_return_target_v1(dict(market_request))
    request = target["market_request"]
    if request["source_kind"] != "RECORDED_PUBLIC_MD" or target[
        "bar_spec_ref"
    ] != derive_o4_bar_spec_ref_v1("PT1H"):
        raise ValueError("F1_M9_MARKET_OUTCOME_RECORDED_HOURLY_MARK_REQUIRED")
    host = archived["host"]
    observation = host["observation"]
    if target["instrument_ref"] != observation["instrument_id"]:
        raise ValueError("F1_M9_MARKET_OUTCOME_INSTRUMENT_MISMATCH")
    declared = instant_v1(declared_at_utc)
    if not (
        instant_v1(observation["submitted_decision_time"])
        <= instant_v1(archived["evidence"]["evaluation_time_utc"])
        <= declared
        <= instant_v1(target["horizon_start_time_utc"])
    ):
        raise ValueError("F1_M9_MARKET_OUTCOME_DECLARATION_TIME_MISMATCH")
    return seal_v1(
        {
            "schema_version": _PLAN_SCHEMA,
            "authority": "NONE",
            "host_evidence_sha256": host_evidence_sha256,
            "host_decision_evidence_digest": host["decision_evidence_digest"],
            "host_configuration_digest": observation["configuration_digest"],
            "host_seam_digest": observation["seam_digest"],
            "declared_at_utc": declared_at_utc,
            "market_target": target,
        }
    )


def declare_f1_m9_applied_replay_market_outcome_v1(
    *,
    store_root: Path,
    host_evidence_path: Path,
    host_evidence_sha256: str,
    market_request: Mapping[str, Any],
    declared_at_utc: str,
) -> dict[str, Any]:
    """Store the exact following market window before admitting its observations."""
    plan = _plan(
        host_evidence_path=host_evidence_path,
        host_evidence_sha256=host_evidence_sha256,
        market_request=market_request,
        declared_at_utc=declared_at_utc,
    )
    _publish(store_root / plan["exact_content_digest"] / "plan.json", plan)
    return plan


def _read_plan(store_root: Path, plan_digest: str, host_evidence_path: Path) -> dict[str, Any]:
    if not is_valid_sha256_hex(plan_digest):
        raise ValueError("F1_M9_MARKET_OUTCOME_PLAN_DIGEST_INVALID")
    path = store_root / plan_digest / "plan.json"
    plan = validate_seal_v1(strict_json_v1(path.read_bytes()), _PLAN_SCHEMA)
    if plan["exact_content_digest"] != plan_digest or plan != _plan(
        host_evidence_path=host_evidence_path,
        host_evidence_sha256=plan["host_evidence_sha256"],
        market_request=plan["market_target"]["market_request"],
        declared_at_utc=plan["declared_at_utc"],
    ):
        raise ValueError("F1_M9_MARKET_OUTCOME_PLAN_LINEAGE_MISMATCH")
    return plan


def measure_f1_m9_applied_replay_market_outcome_v1(
    *,
    store_root: Path,
    plan_digest: str,
    host_evidence_path: Path,
    archive: RecordedMarkArchiveV1,
    evaluated_at_utc: str,
) -> dict[str, Any]:
    """Run the recorded-mark supplier against the saved plan."""
    plan = _read_plan(store_root, plan_digest, host_evidence_path)
    observation = measure_recorded_market_horizon_v1(
        archive=archive,
        request=plan["market_target"]["market_request"],
        evaluated_at_utc=evaluated_at_utc,
    )
    record = seal_v1(
        {
            "schema_version": _MEASUREMENT_SCHEMA,
            "authority": "NONE",
            "plan_digest": plan_digest,
            "market_observation": observation,
            "economic_application_effect": None,
            "comparison_status": _COMPARISON_STATUS,
        }
    )
    _publish(store_root / plan_digest / "measurement.json", record)
    return record


def read_f1_m9_applied_replay_market_outcome_v1(
    *,
    store_root: Path,
    plan_digest: str,
    host_evidence_path: Path,
    expected_measurement_digest: str,
) -> dict[str, Any]:
    """Reopen the original host, plan and measured market context."""
    plan = _read_plan(store_root, plan_digest, host_evidence_path)
    path = store_root / plan_digest / "measurement.json"
    record = validate_seal_v1(strict_json_v1(path.read_bytes()), _MEASUREMENT_SCHEMA)
    if (
        record["exact_content_digest"] != expected_measurement_digest
        or record["plan_digest"] != plan_digest
        or record["economic_application_effect"] is not None
        or record["comparison_status"] != _COMPARISON_STATUS
    ):
        raise ValueError("F1_M9_MARKET_OUTCOME_MEASUREMENT_LINEAGE_MISMATCH")
    observation = validate_independent_market_horizon_v1(record["market_observation"])
    if observation["request"] != plan["market_target"]["market_request"]:
        raise ValueError("F1_M9_MARKET_OUTCOME_TARGET_MISMATCH")
    return record
