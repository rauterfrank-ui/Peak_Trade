"""Phase 3 dataset materialization closeout for CS MA-crossover panel rank-rotation v0.

Registers bounded OKX lifecycle source + PT1H panel dataset materialization for the
ratified research scope. No economic evaluation, no binding ratification, no runtime
authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_research_scope_ratification_v1 import (
    PHASE3_GO_TOKEN_TO_REGISTER_ONLY,
    RECOMMENDED_SCOPE_ID,
    STRATEGY_ID,
    STRATEGY_VERSION,
    UNDERLYING_SIGNAL_BINDING,
    materialize_ma_crossover_panel_rank_rotation_research_scope_ratification_v1,
    materialize_panel_universe_dataset_binding_v0,
)
from src.research.okx_production_instrument_lifecycle_source_v1 import SOURCE_ID
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    BAR_GRANULARITY,
    PANEL_DATASET_VERSION,
    PANEL_ID,
    InstrumentPanelSeriesV1,
    PanelBarV1,
    compute_series_digest,
    validate_panel_series_v1,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_PHASE3_DATASET_MATERIALIZATION_V1=true"
)
SCHEMA_VERSION = (
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_dataset_materialization.v1"
)
CLOSEOUT_ID = (
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_dataset_materialization_v1"
)
CLOSEOUT_VERSION = "v1"
OPERATOR_GO_PHASE3 = PHASE3_GO_TOKEN_TO_REGISTER_ONLY
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_dataset_materialization_v1.json"
)
PHASE3_PRECONDITION_CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_precondition_contract_v0.json"
)
RATIFICATION_CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_research_scope_ratification_v1.json"
)
PANEL_BINDING_CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_panel_universe_dataset_binding_v0.json"
)
DEFAULT_STAGING_REL = "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_pt1h_panel/v2"
BITCOIN_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin"})


class ValidationVerdictEnum(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class Phase3CloseoutValidationResultV1:
    verdict: ValidationVerdictEnum
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _instrument_contains_bitcoin(token: str) -> bool:
    lowered = token.lower()
    return any(substr in lowered for substr in BITCOIN_SUBSTRINGS)


def verify_bitcoin_absent_v1(instruments: Sequence[str]) -> tuple[bool, tuple[str, ...]]:
    blocked = tuple(inst for inst in instruments if _instrument_contains_bitcoin(inst))
    return not blocked, blocked


def _row_counts_by_instrument(
    panel_series: Sequence[Any],
) -> dict[str, int]:
    return {series.instrument_id: len(series.bars) for series in panel_series}


def _load_panel_series_from_staging_root(
    panel_staging_root: Path,
) -> tuple[tuple[InstrumentPanelSeriesV1, ...], str]:
    panel_dir = panel_staging_root / "panel"
    manifest = _load_json(panel_dir / "panel_dataset_manifest.json")
    rows = json.loads((panel_dir / "normalized_panel_bars.json").read_text(encoding="utf-8"))
    grouped: dict[str, list[PanelBarV1]] = {}
    native_by_id = dict(zip(manifest["instrument_ids"], manifest["native_instrument_ids"]))
    for row in rows:
        bar = PanelBarV1(
            instrument_id=str(row["instrument_id"]),
            timestamp_utc=str(row["timestamp_utc"]),
            open=str(row["open"]),
            high=str(row["high"]),
            low=str(row["low"]),
            close=str(row["close"]),
            volume=str(row["volume"]),
            is_final=bool(row.get("is_final", True)),
        )
        grouped.setdefault(bar.instrument_id, []).append(bar)
    series_list: list[InstrumentPanelSeriesV1] = []
    for instrument_id, bars in grouped.items():
        ordered = tuple(sorted(bars, key=lambda item: item.timestamp_utc))
        series = InstrumentPanelSeriesV1(
            instrument_id=instrument_id,
            native_instrument_id=str(native_by_id.get(instrument_id, instrument_id)),
            bars=ordered,
            series_digest="0" * 64,
        )
        series_list.append(
            InstrumentPanelSeriesV1(
                instrument_id=series.instrument_id,
                native_instrument_id=series.native_instrument_id,
                bars=series.bars,
                series_digest=compute_series_digest(series),
            )
        )
    return tuple(sorted(series_list, key=lambda item: item.instrument_id)), str(
        manifest.get("normalized_panel_digest", "")
    )


def load_okx_materialization_result_v1(evidence_dir: Path) -> dict[str, Any]:
    path = evidence_dir / "MATERIALIZATION_RESULT.json"
    if not path.is_file():
        raise FileNotFoundError(f"missing_materialization_result:{path}")
    return _load_json(path)


def materialize_phase3_precondition_contract_post_materialization_v0(
    *,
    materialization_evidence_path: str,
    panel_staging_root: str,
    panel_data_digest: str,
    lifecycle_data_digest: str,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": (
            "cross_sectional_ma_crossover_panel_rank_rotation_phase3_precondition.v0"
        ),
        "phase3_go_token_to_register_only": PHASE3_GO_TOKEN_TO_REGISTER_ONLY,
        "phase3_go_token_consumed": True,
        "dataset_materialization_authorized": True,
        "dataset_materialized": True,
        "network_ingest_authorized": True,
        "network_ingest_executed": True,
        "economic_evaluation_authorized": False,
        "required_preconditions": [
            "RESEARCH_SCOPE_RATIFIED=true",
            "PHASE3_GO_TOKEN_CONSUMED=true",
            "DATASET_MATERIALIZED=true",
            "VERSIONED_BINDING_RATIFICATION_REQUIRES_SEPARATE_GO",
            "ECONOMIC_EVALUATION_REQUIRES_SEPARATE_GO",
        ],
        "reuse_first_owners": [
            "scripts/ops/materialize_okx_production_lifecycle_and_pt1h_panel_v1.py",
            "src/research/pit_okx_pt1h_panel_ohlcv_dataset_v1",
            "src/research/cross_sectional_panel_economic_evaluation_wiring_v0",
            "src/research/cross_sectional_single_slot_backtest_wiring_v0",
        ],
        "next_action_after_dataset_materialization": (
            "VERSIONED_BINDING_RATIFICATION_REQUIRES_SEPARATE_OPERATOR_GO"
        ),
        "panel_staging_root": panel_staging_root,
        "panel_data_digest": panel_data_digest,
        "lifecycle_data_digest": lifecycle_data_digest,
        "materialization_evidence_path": materialization_evidence_path,
    }
    body["precondition_digest"] = _stable_digest(
        {k: v for k, v in body.items() if k != "precondition_digest"}
    )
    return body


def materialize_panel_binding_post_materialization_v0(
    *,
    panel_staging_root: str,
    panel_data_digest: str,
    lifecycle_data_digest: str,
    panel_dataset_ref: str,
) -> dict[str, Any]:
    binding = materialize_panel_universe_dataset_binding_v0()
    binding["binding_status"] = "DATASET_MATERIALIZED_BINDING_NOT_RATIFIED"
    binding["panel_staging_root"] = panel_staging_root
    binding["panel_data_digest"] = panel_data_digest
    binding["lifecycle_data_digest"] = lifecycle_data_digest
    binding["panel_dataset_ref"] = panel_dataset_ref
    binding["binding_digest"] = _stable_digest(
        {k: v for k, v in binding.items() if k != "binding_digest"}
    )
    return binding


def materialize_phase3_dataset_materialization_closeout_v1(
    *,
    repo_root: Path,
    durable_archive_root: Path,
    okx_materialization_evidence_dir: Path,
    panel_staging_root: Path,
    operator: str,
    pre_head: str,
) -> dict[str, Any]:
    materialization = load_okx_materialization_result_v1(okx_materialization_evidence_dir)
    if materialization.get("manifest_verify_rc") != 0:
        raise ValueError("MANIFEST_VERIFY_RC_NOT_ZERO")

    panel_series, _panel_digest = _load_panel_series_from_staging_root(panel_staging_root)
    panel_validation = validate_panel_series_v1(panel_series, min_instruments=5)
    if not panel_validation.valid:
        raise ValueError(f"PANEL_VALIDATION_FAILED:{panel_validation.error_codes}")

    instruments = [series.instrument_id for series in panel_series]
    bitcoin_ok, blocked = verify_bitcoin_absent_v1(instruments)
    if not bitcoin_ok:
        raise ValueError(f"BITCOIN_INSTRUMENT_PRESENT:{blocked}")

    row_counts = _row_counts_by_instrument(panel_series)
    row_count_total = sum(row_counts.values())
    panel_manifest = _load_json(panel_staging_root / "panel/panel_dataset_manifest.json")
    period_binding = _load_json(panel_staging_root / "reports/PERIOD_BINDING.json")

    scope_ratification = (
        materialize_ma_crossover_panel_rank_rotation_research_scope_ratification_v1(
            repo_root=repo_root,
        )
    )
    scope_ratification["dataset_materialized"] = True
    scope_ratification["phase3_precondition_contract"] = (
        materialize_phase3_precondition_contract_post_materialization_v0(
            materialization_evidence_path=str(okx_materialization_evidence_dir),
            panel_staging_root=str(panel_staging_root),
            panel_data_digest=str(materialization["panel_data_digest"]),
            lifecycle_data_digest=str(materialization["lifecycle_data_digest"]),
        )
    )
    scope_ratification["panel_universe_dataset_binding"] = (
        materialize_panel_binding_post_materialization_v0(
            panel_staging_root=str(panel_staging_root),
            panel_data_digest=str(materialization["panel_data_digest"]),
            lifecycle_data_digest=str(materialization["lifecycle_data_digest"]),
            panel_dataset_ref=str(materialization["panel_dataset_ref"]),
        )
    )
    scope_ratification["panel_staging_root"] = str(panel_staging_root)
    scope_ratification["panel_data_digest"] = materialization["panel_data_digest"]
    scope_ratification["lifecycle_data_digest"] = materialization["lifecycle_data_digest"]
    scope_ratification["panel_dataset_ref"] = materialization["panel_dataset_ref"]
    scope_ratification["ratification_digest"] = _stable_digest(
        {k: v for k, v in scope_ratification.items() if k != "ratification_digest"}
    )

    closeout: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "closeout_id": CLOSEOUT_ID,
        "closeout_version": CLOSEOUT_VERSION,
        "operator_go_token": OPERATOR_GO_PHASE3,
        "operator_go_token_consumed": True,
        "operator": operator,
        "pre_head": pre_head,
        "recommended_scope_id": RECOMMENDED_SCOPE_ID,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "underlying_signal_binding": UNDERLYING_SIGNAL_BINDING,
        "research_scope_ratified": True,
        "binding_ratified": False,
        "dataset_materialized": True,
        "economic_evaluation_authorized": False,
        "economic_evaluation_executed": False,
        "runtime_effect": "NONE",
        "authority_effect": "NONE",
        "production_lifecycle_source_id": SOURCE_ID,
        "production_lifecycle_source_bound": materialization["production_lifecycle_source_bound"],
        "lifecycle_registry_snapshot_materialized": materialization[
            "lifecycle_registry_snapshot_materialized"
        ],
        "panel_dataset_manifest_materialized": materialization[
            "panel_dataset_manifest_materialized"
        ],
        "dataset_id": PANEL_ID,
        "dataset_version": PANEL_DATASET_VERSION,
        "panel_staging_root": str(panel_staging_root),
        "panel_dataset_ref": materialization["panel_dataset_ref"],
        "panel_data_digest": materialization["panel_data_digest"],
        "lifecycle_data_digest": materialization["lifecycle_data_digest"],
        "raw_instruments_digest": materialization.get("registry_snapshot", {}).get(
            "approved_snapshot_digests", [""]
        ),
        "instrument_count": len(instruments),
        "instruments": sorted(instruments),
        "bitcoin_present": False,
        "window_start_utc": materialization["panel_period_start"],
        "window_end_utc": materialization["panel_period_end"],
        "bar_granularity": BAR_GRANULARITY,
        "row_count_total": row_count_total,
        "row_count_by_instrument": row_counts,
        "data_quality_status": "PASS",
        "panel_validation": materialization.get("panel_validation", {}),
        "period_binding": period_binding,
        "panel_manifest_digest": panel_manifest.get("manifest_digest"),
        "normalized_panel_digest": panel_manifest.get("normalized_panel_digest"),
        "network_surface": "okx_public_rest_api_v5_public_get_only",
        "okx_materialization_evidence_path": str(okx_materialization_evidence_dir),
        "manifest_verify_rc": materialization["manifest_verify_rc"],
        "next_action": "VERSIONED_BINDING_RATIFICATION_REQUIRES_SEPARATE_OPERATOR_GO",
        "ratification_digest": scope_ratification["ratification_digest"],
        "scope_ratification": scope_ratification,
    }
    closeout["closeout_digest"] = _stable_digest(
        {k: v for k, v in closeout.items() if k not in {"closeout_digest", "scope_ratification"}}
    )
    return closeout


def validate_phase3_dataset_materialization_closeout_v1(
    closeout: Mapping[str, Any],
) -> Phase3CloseoutValidationResultV1:
    reasons: list[str] = []
    if closeout.get("schema_version") != SCHEMA_VERSION:
        reasons.append("UNKNOWN_SCHEMA_VERSION")
    if closeout.get("operator_go_token") != OPERATOR_GO_PHASE3:
        reasons.append("PHASE3_GO_TOKEN_MISMATCH")
    if closeout.get("operator_go_token_consumed") is not True:
        reasons.append("PHASE3_GO_TOKEN_NOT_CONSUMED")
    if closeout.get("dataset_materialized") is not True:
        reasons.append("DATASET_NOT_MATERIALIZED")
    if closeout.get("economic_evaluation_authorized") is not False:
        reasons.append("ECONOMIC_EVALUATION_AUTHORIZED_MUST_BE_FALSE")
    if closeout.get("economic_evaluation_executed") is not False:
        reasons.append("ECONOMIC_EVALUATION_EXECUTED_MUST_BE_FALSE")
    if closeout.get("binding_ratified") is not False:
        reasons.append("BINDING_RATIFIED_MUST_BE_FALSE")
    if closeout.get("bitcoin_present") is not False:
        reasons.append("BITCOIN_PRESENT")
    if int(closeout.get("instrument_count", 0)) < 5:
        reasons.append("INSUFFICIENT_INSTRUMENT_COUNT")
    if closeout.get("runtime_effect") != "NONE":
        reasons.append("RUNTIME_EFFECT_NOT_NONE")
    if closeout.get("authority_effect") != "NONE":
        reasons.append("AUTHORITY_EFFECT_NOT_NONE")
    if closeout.get("manifest_verify_rc") != 0:
        reasons.append("MANIFEST_VERIFY_RC_NOT_ZERO")
    if closeout.get("data_quality_status") != "PASS":
        reasons.append("DATA_QUALITY_NOT_PASS")
    if closeout.get("dataset_id") != PANEL_ID:
        reasons.append("DATASET_ID_MISMATCH")
    if closeout.get("bar_granularity") != BAR_GRANULARITY:
        reasons.append("BAR_GRANULARITY_MISMATCH")

    instruments = closeout.get("instruments", [])
    if isinstance(instruments, list):
        bitcoin_ok, blocked = verify_bitcoin_absent_v1([str(item) for item in instruments])
        if not bitcoin_ok:
            reasons.append(f"BITCOIN_INSTRUMENT_IN_LIST:{blocked}")

    verdict = ValidationVerdictEnum.ACCEPTED if not reasons else ValidationVerdictEnum.REJECTED
    return Phase3CloseoutValidationResultV1(verdict=verdict, fail_reasons=tuple(reasons))


def serialize_closeout_canonical_v1(closeout: Mapping[str, Any]) -> str:
    return json.dumps(closeout, indent=2, sort_keys=True, default=str) + "\n"
