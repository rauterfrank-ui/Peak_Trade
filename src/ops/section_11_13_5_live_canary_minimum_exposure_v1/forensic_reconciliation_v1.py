"""Forensic classification of sealed §11.13.3/§11.13.4 HARD_STOP_OWNER_REVIEW layers.

Authoring-only. No exchange/account mutation. No productive network by default —
classifies from sealed evidence digests unless a separate LIVE RO GO is supplied.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    FORENSIC_CLASSIFICATION_CODES,
    HARD_STOP_OWNER_REVIEW_LAYERS,
    POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1,
    POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1,
    POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1,
    REUSED_SECTION_11_13_3_BINDING_SOURCE,
    REUSED_SECTION_11_13_4_BINDING_SOURCE,
)


class LiveCanaryForensicError(RuntimeError):
    """Fail-closed forensic classification violation."""


@dataclass(frozen=True)
class LayerForensicRecordV1:
    layer: str
    local_status: str
    local_digest: str
    exchange_status: str
    exchange_digest: str
    prior_outcome: str
    classification_codes: tuple[str, ...]
    classification_primary: str
    rationale: str
    resolution_policy_id: str
    clears_blocks_new_entry_automatically: bool
    requires_owner_adoption_policy: bool
    productive_network_refresh_required: bool
    units: str
    currency: str | None
    contract_multiplier: str | None
    instrument_identity: str | None
    account_mode: str
    normalization_path: str
    freshness_source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "local_status": self.local_status,
            "local_digest": self.local_digest,
            "exchange_status": self.exchange_status,
            "exchange_digest": self.exchange_digest,
            "prior_outcome": self.prior_outcome,
            "classification_codes": list(self.classification_codes),
            "classification_primary": self.classification_primary,
            "rationale": self.rationale,
            "resolution_policy_id": self.resolution_policy_id,
            "clears_blocks_new_entry_automatically": (self.clears_blocks_new_entry_automatically),
            "requires_owner_adoption_policy": self.requires_owner_adoption_policy,
            "productive_network_refresh_required": (self.productive_network_refresh_required),
            "units": self.units,
            "currency": self.currency,
            "contract_multiplier": self.contract_multiplier,
            "instrument_identity": self.instrument_identity,
            "account_mode": self.account_mode,
            "normalization_path": self.normalization_path,
            "freshness_source": self.freshness_source,
        }


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LiveCanaryForensicError(f"JSON_OBJECT_REQUIRED:{path}")
    return payload


def _layer_view(snapshot: Mapping[str, Any], layer: str) -> dict[str, Any]:
    layers = snapshot.get("layers")
    if not isinstance(layers, Mapping):
        raise LiveCanaryForensicError("SNAPSHOT_LAYERS_MISSING")
    view = layers.get(layer)
    if not isinstance(view, Mapping):
        raise LiveCanaryForensicError(f"LAYER_MISSING:{layer}")
    return dict(view)


def classify_hard_stop_layers_from_sealed_snapshots_v1(
    *,
    local_expected_state: Mapping[str, Any],
    exchange_snapshot: Mapping[str, Any],
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    freshness_source: str = REUSED_SECTION_11_13_3_BINDING_SOURCE,
) -> tuple[LayerForensicRecordV1, ...]:
    """Deterministic forensic classification; does not mutate SSOT gates."""
    records: list[LayerForensicRecordV1] = []
    for layer in HARD_STOP_OWNER_REVIEW_LAYERS:
        local = _layer_view(local_expected_state, layer)
        exchange = _layer_view(exchange_snapshot, layer)
        local_status = str(local.get("status", ""))
        exchange_status = str(exchange.get("status", ""))
        local_digest = str(local.get("digest", ""))
        exchange_digest = str(exchange.get("digest", ""))

        if layer == "venue_instrument_and_contract_metadata":
            if local_status == "flat_or_empty" and exchange_status == "observed":
                codes = (
                    "B_SEMANTIC_OR_UNIT_MISMATCH",
                    "C_EXPECTED_BENIGN_OPERATIONAL_DIFFERENCE",
                )
                primary = "C_EXPECTED_BENIGN_OPERATIONAL_DIFFERENCE"
                rationale = (
                    "Local shadow expected state carries no instrument/metadata catalog "
                    "(flat_or_empty by design for pre-trading GET-only shadow). Exchange "
                    "snapshot observes account/config metadata. Open positions and open "
                    "orders layers MATCH; this is not a position/PnL economic conflict."
                )
                policy = POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1
                units = "metadata_digest"
                currency = None
                multiplier = None
            else:
                codes = ("D_REAL_UNRESOLVED_ECONOMIC_DIVERGENCE",)
                primary = "D_REAL_UNRESOLVED_ECONOMIC_DIVERGENCE"
                rationale = "Unexpected venue-metadata shape; Owner review required."
                policy = POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1
                units = "metadata_digest"
                currency = None
                multiplier = None
        elif layer == "balances_equity_and_available_margin":
            if local_status == "flat_or_empty" and exchange_status == "observed":
                codes = ("A_STALE_OR_LOCAL_DATA_MISMATCH",)
                primary = "A_STALE_OR_LOCAL_DATA_MISMATCH"
                rationale = (
                    "Local LIVE portfolio ledger was never seeded (flat_or_empty). "
                    "Exchange observes funded balances/equity. Positions layer MATCH "
                    "(flat). Divergence is local baseline absence vs exchange cash, not "
                    "conflicting open positions. Still blocks new entry until Owner "
                    "adopts exchange balance baseline via explicit policy."
                )
                policy = POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1
                units = "equity_digest"
                currency = "USDC_ACCOUNT_TRUTH_OR_ACCOUNT_EQ_AS_OBSERVED"
                multiplier = None
            else:
                codes = ("D_REAL_UNRESOLVED_ECONOMIC_DIVERGENCE",)
                primary = "D_REAL_UNRESOLVED_ECONOMIC_DIVERGENCE"
                rationale = "Unexpected balance-layer shape; treat as unresolved economic."
                policy = POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1
                units = "equity_digest"
                currency = "USDC_ACCOUNT_TRUTH_OR_ACCOUNT_EQ_AS_OBSERVED"
                multiplier = None
        elif layer == "local_portfolio_and_accounting":
            if local_status == "flat_or_empty" and exchange_status == "observed":
                codes = (
                    "A_STALE_OR_LOCAL_DATA_MISMATCH",
                    "E_IMPLEMENTATION_DEFECT",
                )
                primary = "A_STALE_OR_LOCAL_DATA_MISMATCH"
                rationale = (
                    "Exchange snapshot builder mirrors balances_equity digest into "
                    "local_portfolio_and_accounting when balances are observed, while "
                    "local expected remains flat. Primary issue is local LIVE accounting "
                    "baseline absence (A). Secondary note (E): layer aliasing amplifies "
                    "the same balance observation as a second HARD_STOP without an "
                    "independent portfolio book comparison."
                )
                policy = POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1
                units = "portfolio_digest_aliased_from_balances"
                currency = "USDC_ACCOUNT_TRUTH_OR_ACCOUNT_EQ_AS_OBSERVED"
                multiplier = None
            else:
                codes = ("D_REAL_UNRESOLVED_ECONOMIC_DIVERGENCE",)
                primary = "D_REAL_UNRESOLVED_ECONOMIC_DIVERGENCE"
                rationale = "Unexpected local-portfolio shape; Owner review required."
                policy = POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1
                units = "portfolio_digest"
                currency = "USDC_ACCOUNT_TRUTH_OR_ACCOUNT_EQ_AS_OBSERVED"
                multiplier = None
        else:
            raise LiveCanaryForensicError(f"UNSUPPORTED_FORENSIC_LAYER:{layer}")

        for code in codes:
            if code not in FORENSIC_CLASSIFICATION_CODES:
                raise LiveCanaryForensicError(f"UNKNOWN_CLASSIFICATION_CODE:{code}")

        records.append(
            LayerForensicRecordV1(
                layer=layer,
                local_status=local_status,
                local_digest=local_digest,
                exchange_status=exchange_status,
                exchange_digest=exchange_digest,
                prior_outcome="HARD_STOP_OWNER_REVIEW",
                classification_codes=codes,
                classification_primary=primary,
                rationale=rationale,
                resolution_policy_id=policy,
                clears_blocks_new_entry_automatically=False,
                requires_owner_adoption_policy=True,
                productive_network_refresh_required=False,
                units=units,
                currency=currency,
                contract_multiplier=multiplier,
                instrument_identity=instrument_id,
                account_mode="LIVE_PRE_TRADING_SHADOW_BASELINE",
                normalization_path=(
                    "digest_compare(local_expected_state.layers[layer], "
                    "exchange_snapshot.layers[layer]) "
                    "via section_11_13_3 reconciliation_v1 without adoption policy"
                ),
                freshness_source=freshness_source,
            )
        )
    return tuple(records)


def classify_from_sealed_evidence_roots_v1(
    *,
    repo_root: Path | str,
    shadow_evidence_rel: str = REUSED_SECTION_11_13_3_BINDING_SOURCE,
) -> dict[str, Any]:
    root = Path(repo_root)
    shadow = root / shadow_evidence_rel
    local = _load_json(shadow / "LOCAL_EXPECTED_STATE.sanitized.json")
    exchange = _load_json(shadow / "EXCHANGE_SNAPSHOT.sanitized.json")
    records = classify_hard_stop_layers_from_sealed_snapshots_v1(
        local_expected_state=local,
        exchange_snapshot=exchange,
        freshness_source=shadow_evidence_rel,
    )
    primary_codes = {r.classification_primary for r in records}
    any_real_d = any(
        "D_REAL_UNRESOLVED_ECONOMIC_DIVERGENCE" in r.classification_codes for r in records
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_13_5_FORENSIC_LAYER_CLASSIFICATION_V1",
        "SOURCE_SHADOW_EVIDENCE": shadow_evidence_rel,
        "SOURCE_DRY_RUN_EVIDENCE": REUSED_SECTION_11_13_4_BINDING_SOURCE,
        "PRODUCTIVE_NETWORK_USED": False,
        "PRODUCTIVE_NETWORK_AUTHORIZATION": ("MISSING_SEPARATE_LIVE_RO_GO_FOR_FORENSIC_REFRESH"),
        "ACCOUNT_MUTATION_EFFECT": "NONE",
        "ORDER_EFFECT": "NONE",
        "SECRET_VALUE_ACCESS": "NONE",
        "LIVE_RECONCILIATION_PROVEN_CLEARED": False,
        "BLOCKS_NEW_ENTRY_CLEARED": False,
        "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY": True,
        "ANY_LAYER_CLASSIFIED_AS_REAL_ECONOMIC_DIVERGENCE_D": any_real_d,
        "PRIMARY_CLASSIFICATION_CODES": sorted(primary_codes),
        "OWNER_ADOPTION_POLICIES_REQUIRED": sorted({r.resolution_policy_id for r in records}),
        "layers": [r.to_dict() for r in records],
        "ok": True,
    }


def prove_forensic_classification_contract_v1(*, repo_root: Path | str) -> dict[str, Any]:
    result = classify_from_sealed_evidence_roots_v1(repo_root=repo_root)
    layers = {item["layer"]: item for item in result["layers"]}
    ok = all(
        [
            result["PRODUCTIVE_NETWORK_USED"] is False,
            result["BLOCKS_NEW_ENTRY_CLEARED"] is False,
            result["LIVE_RECONCILIATION_PROVEN_CLEARED"] is False,
            result["ANY_LAYER_CLASSIFIED_AS_REAL_ECONOMIC_DIVERGENCE_D"] is False,
            layers["venue_instrument_and_contract_metadata"]["classification_primary"]
            == "C_EXPECTED_BENIGN_OPERATIONAL_DIFFERENCE",
            layers["balances_equity_and_available_margin"]["classification_primary"]
            == "A_STALE_OR_LOCAL_DATA_MISMATCH",
            layers["local_portfolio_and_accounting"]["classification_primary"]
            == "A_STALE_OR_LOCAL_DATA_MISMATCH",
            all(not item["clears_blocks_new_entry_automatically"] for item in result["layers"]),
        ]
    )
    result["contract_ok"] = ok
    if not ok:
        raise LiveCanaryForensicError("FORENSIC_CLASSIFICATION_CONTRACT_FAIL")
    return result
