"""CURRENT instrument MV2 offline CRS/COI boundary state-file materialization v1.

Materializes digest-pinned static boundary fields for the selected okx_eea instrument.
Per-bar reference_price and protective_stop_price are not materialized; they bind at
gate time via mv2_offline_boundary_dynamic_price_context_v1 (same semantics as integrated replay).

Non-authorizing; no runtime, orders, or external effects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

from src.governance.capital_risk_sizing_v1 import (
    CONTRACT_VERSION as CAPITAL_RISK_SIZING_CONTRACT_VERSION,
)
from src.governance.canonical_order_intent_v1 import (
    CONTRACT_VERSION as CANONICAL_ORDER_INTENT_CONTRACT_VERSION,
)
from trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0 import (
    CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    compute_backtest_state_file_digest_from_payload_v0 as crs_digest,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    default_offline_replay_capital_context_v0,
    default_offline_replay_instrument_v0,
)
from trading.master_v2.canonical_order_intent_boundary_backtest_state_file_binding_adapter_v0 import (
    CANONICAL_ORDER_INTENT_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    compute_backtest_state_file_digest_from_payload_v0 as coi_digest,
)
from trading.master_v2.mv2_offline_boundary_dynamic_price_context_v1 import (
    MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
)

CONTRACT_VERSION = "current_instrument_mv2_offline_boundary_materialization_v1"
CONTRACT_OWNER = "backtest.current_instrument_mv2_offline_boundary_materialization_v1"

# Scope/per-trade/total limits remain digest-pinned; daily_loss and maximum_quantity are
# never materialized on the CURRENT dynamic path (no historical 25/100 fixture authority).
STATIC_SCOPE_LIMIT_LINEAGE_REF_V1 = (
    "capital_risk_sizing_offline_replay_binding_adapter_v0."
    "default_offline_replay_capital_context_v0.scope_limits_only"
)
CURRENT_DYNAMIC_BOUNDARY_SCALAR_LINEAGE_REF_V1 = (
    "mv2_offline_boundary_dynamic_price_context_v1.build_mv2_dynamic_boundary_capital_context_v1"
)
STATIC_INSTRUMENT_CONSTRAINT_LINEAGE_MANIFEST_V1 = (
    "admissible_versioned_futures_dataset_v1.manifest.instrument_metadata"
)
STATIC_INSTRUMENT_CONSTRAINT_LINEAGE_ADAPTER_V1 = (
    "capital_risk_sizing_offline_replay_binding_adapter_v0.default_offline_replay_instrument_v0"
)


class CurrentInstrumentBoundaryMaterializationError(ValueError):
    """Fail-closed CURRENT boundary materialization error."""


@dataclass(frozen=True)
class CurrentInstrumentBoundaryMaterializationResultV1:
    output_dir: Path
    canonical_instrument_id: str
    capital_risk_sizing_path: Path
    capital_risk_sizing_digest_ref: str
    canonical_order_intent_path: Path
    canonical_order_intent_digest_ref: str
    static_scope_limit_lineage_ref: str
    current_dynamic_boundary_scalar_lineage_ref: str
    instrument_constraint_lineage_ref: str
    dynamic_price_context_binding_ref: str

    def mandatory_binding_overlay_v0(self) -> dict[str, Any]:
        return {
            "capital_risk_sizing": {
                "state_file_path": str(self.capital_risk_sizing_path),
                "expected_state_file_digest_ref": self.capital_risk_sizing_digest_ref,
            },
            "canonical_order_intent": {
                "state_file_path": str(self.canonical_order_intent_path),
                "expected_state_file_digest_ref": self.canonical_order_intent_digest_ref,
            },
        }


def _fail_closed(condition: bool, reason: str) -> None:
    if condition:
        raise CurrentInstrumentBoundaryMaterializationError(reason)


def _load_manifest_instrument_metadata(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.is_file():
        _fail_closed(True, "dataset_manifest_missing")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        _fail_closed(True, "dataset_manifest_invalid")
    metadata = payload.get("instrument_metadata")
    if not isinstance(metadata, dict):
        return {}
    return metadata


def _manifest_instrument_id(manifest_path: Path) -> str:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        for key in ("instrument_id", "canonical_instrument_id"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _instrument_constraints_from_manifest_or_adapter_v1(
    *,
    canonical_instrument_id: str,
    manifest_metadata: Mapping[str, Any],
) -> tuple[Any, str]:
    lot = manifest_metadata.get("lotSz") or manifest_metadata.get("lot_size")
    tick = manifest_metadata.get("tickSz") or manifest_metadata.get("tick_size")
    min_sz = manifest_metadata.get("minSz") or manifest_metadata.get("minimum_quantity")
    if lot and tick and min_sz:
        default_inst = default_offline_replay_instrument_v0(canonical_instrument_id)
        return (
            replace(
                default_inst,
                lot_size=Decimal(str(lot)),
                minimum_quantity=Decimal(str(min_sz)),
                tick_size=Decimal(str(tick)),
                maximum_quantity=None,
                instrument_metadata_version=STATIC_INSTRUMENT_CONSTRAINT_LINEAGE_MANIFEST_V1,
            ),
            STATIC_INSTRUMENT_CONSTRAINT_LINEAGE_MANIFEST_V1,
        )
    return (
        replace(
            default_offline_replay_instrument_v0(canonical_instrument_id),
            maximum_quantity=None,
        ),
        STATIC_INSTRUMENT_CONSTRAINT_LINEAGE_ADAPTER_V1,
    )


def _shared_static_payload_v1(
    *,
    canonical_instrument_id: str,
    account_equity: Decimal,
    capital_ctx: Any,
    instrument: Any,
    schema_version: str,
    owner_digest_ref: str,
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "instrument_id": canonical_instrument_id,
        "dynamic_price_context_binding_ref": MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
        "account_equity": str(account_equity),
        "scope_capital_limit": str(capital_ctx.scope_capital_limit),
        "per_trade_risk_limit": str(capital_ctx.per_trade_risk_limit),
        "total_capital_limit": str(capital_ctx.total_capital_limit),
        "current_reconciled_exposure": str(capital_ctx.current_reconciled_exposure),
        "lot_size": str(instrument.lot_size),
        "minimum_quantity": str(instrument.minimum_quantity),
        "minimum_notional": str(instrument.minimum_notional),
        "tick_size": str(instrument.tick_size),
        "owner_digest_ref": owner_digest_ref,
    }


def materialize_current_instrument_crs_coi_boundary_state_files_v1(
    *,
    canonical_instrument_id: str,
    dataset_manifest_path: Path,
    output_dir: Path,
    account_equity: Decimal | float | str,
) -> CurrentInstrumentBoundaryMaterializationResultV1:
    """Write CRS + COI boundary JSON for CURRENT instrument (dynamic price binding)."""
    canon = str(canonical_instrument_id or "").strip()
    _fail_closed(not canon.startswith("okx_eea:"), "canonical_instrument_id_not_okx_eea")
    manifest_id = _manifest_instrument_id(Path(dataset_manifest_path))
    if manifest_id:
        _fail_closed(manifest_id != canon, "dataset_manifest_instrument_identity_mismatch")

    manifest_metadata = _load_manifest_instrument_metadata(Path(dataset_manifest_path))
    instrument, constraint_lineage = _instrument_constraints_from_manifest_or_adapter_v1(
        canonical_instrument_id=canon,
        manifest_metadata=manifest_metadata,
    )
    capital_ctx = default_offline_replay_capital_context_v0(
        instrument_id=canon,
        reference_price=Decimal("1"),
        protective_stop_price=Decimal("0.99"),
    )
    equity = Decimal(str(account_equity))

    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    crs_base = _shared_static_payload_v1(
        canonical_instrument_id=canon,
        account_equity=equity,
        capital_ctx=capital_ctx,
        instrument=instrument,
        schema_version=CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        owner_digest_ref=CAPITAL_RISK_SIZING_CONTRACT_VERSION,
    )
    crs_base["capital_risk_sizing_owner_digest_ref"] = crs_base.pop("owner_digest_ref")
    crs_digest_ref = crs_digest(crs_base)
    crs_payload = {**crs_base, "state_file_digest_ref": crs_digest_ref}
    crs_path = out / "capital_risk_sizing.json"
    crs_path.write_text(json.dumps(crs_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    coi_base = _shared_static_payload_v1(
        canonical_instrument_id=canon,
        account_equity=equity,
        capital_ctx=capital_ctx,
        instrument=instrument,
        schema_version=CANONICAL_ORDER_INTENT_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        owner_digest_ref=CANONICAL_ORDER_INTENT_CONTRACT_VERSION,
    )
    coi_base["canonical_order_intent_owner_digest_ref"] = coi_base.pop("owner_digest_ref")
    coi_digest_ref = coi_digest(coi_base)
    coi_payload = {**coi_base, "state_file_digest_ref": coi_digest_ref}
    coi_path = out / "canonical_order_intent.json"
    coi_path.write_text(json.dumps(coi_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return CurrentInstrumentBoundaryMaterializationResultV1(
        output_dir=out,
        canonical_instrument_id=canon,
        capital_risk_sizing_path=crs_path,
        capital_risk_sizing_digest_ref=crs_digest_ref,
        canonical_order_intent_path=coi_path,
        canonical_order_intent_digest_ref=coi_digest_ref,
        static_scope_limit_lineage_ref=STATIC_SCOPE_LIMIT_LINEAGE_REF_V1,
        current_dynamic_boundary_scalar_lineage_ref=CURRENT_DYNAMIC_BOUNDARY_SCALAR_LINEAGE_REF_V1,
        instrument_constraint_lineage_ref=constraint_lineage,
        dynamic_price_context_binding_ref=MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
    )


def is_current_okx_eea_canonical_instrument_id_v1(instrument_id: str) -> bool:
    return str(instrument_id or "").strip().startswith("okx_eea:")
