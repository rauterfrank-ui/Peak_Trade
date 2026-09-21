"""Build archive-sibling Economic Summary fields from one explicit STEP29M bundle only.

Loads ``EconomicViabilityEvidenceV1`` via ``load_economic_viability_evidence_bundle_v1``
with manifest verification. No registry, latest, or filesystem discovery.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.backtest.economic_viability_evidence_v1 import (
    ARTIFACT_FILENAME,
    ECONOMIC_VIABILITY_EVIDENCE_LAYER_VERSION,
    ECONOMIC_VIABILITY_EVIDENCE_OWNER,
    EconomicViabilityEvidenceError,
    load_economic_viability_evidence_bundle_v1,
)
from src.ops.economic_summary_archive_sibling_exporter_v1.constants_v1 import (
    ERROR_BUNDLE_DIR_MISSING,
    ERROR_CONTRACT_VERSION_MISMATCH,
    ERROR_CROSS_SECTIONAL_SHAPE,
    ERROR_EVIDENCE_ARTIFACT_MISSING,
    ERROR_MANIFEST_OR_CONTRACT_FAIL,
    ERROR_OWNER_MISMATCH,
    ERROR_SOURCE_CORRUPT,
    ERROR_SOURCE_INVALID,
)


def _metric_mapping(raw: object) -> dict[str, Any]:
    if hasattr(raw, "to_dict") and callable(raw.to_dict):
        return dict(raw.to_dict())
    raise TypeError("metric fields must expose to_dict")


def build_economic_summary_sibling_payload_from_explicit_bundle_v1(
    *,
    economic_viability_evidence_bundle_path: str | Path,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Map manifest-verified STEP29M bundle evidence into sibling export shape."""
    bundle_dir = Path(economic_viability_evidence_bundle_path).expanduser().resolve()
    if not bundle_dir.is_dir():
        return None, (ERROR_BUNDLE_DIR_MISSING,)

    artifact_path = bundle_dir / ARTIFACT_FILENAME
    if not artifact_path.is_file():
        return None, (ERROR_EVIDENCE_ARTIFACT_MISSING,)

    try:
        raw_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, (ERROR_SOURCE_CORRUPT,)

    if not isinstance(raw_payload, dict):
        return None, (ERROR_SOURCE_INVALID,)

    schema_version = raw_payload.get("schema_version")
    if isinstance(schema_version, str) and "cross_sectional" in schema_version.lower():
        return None, (ERROR_CROSS_SECTIONAL_SHAPE,)

    try:
        loaded = load_economic_viability_evidence_bundle_v1(bundle_dir, verify_manifest=True)
    except EconomicViabilityEvidenceError as exc:
        return None, (ERROR_MANIFEST_OR_CONTRACT_FAIL, str(exc))

    evidence = loaded.evidence
    if evidence.owner != ECONOMIC_VIABILITY_EVIDENCE_OWNER:
        return None, (ERROR_OWNER_MISMATCH,)
    if evidence.contract_version != ECONOMIC_VIABILITY_EVIDENCE_LAYER_VERSION:
        return None, (ERROR_CONTRACT_VERSION_MISMATCH,)

    status_value = (
        evidence.status.value if hasattr(evidence.status, "value") else str(evidence.status)
    )
    raw_fields: dict[str, Any] = {
        "status": status_value,
        "economic_validity_proven": evidence.economic_validity_proven,
        "profitability_claim_allowed": evidence.profitability_claim_allowed,
        "policy_threshold_status": evidence.policy_threshold_status,
        "policy_version": evidence.policy_version,
        "authority_effect": evidence.authority_effect,
        "runtime_effect": evidence.runtime_effect,
        "order_effect": evidence.order_effect,
        "reason_codes": list(evidence.reason_codes),
        "profit_factor": _metric_mapping(evidence.profit_factor),
        "net_return": _metric_mapping(evidence.net_return),
        "max_drawdown": _metric_mapping(evidence.max_drawdown),
        "sharpe": _metric_mapping(evidence.sharpe),
        "trade_count": _metric_mapping(evidence.trade_count),
        "funding_drag": _metric_mapping(evidence.funding_drag),
        "contract_version": evidence.contract_version,
        "owner": evidence.owner,
        "strategy_id": evidence.strategy_id,
        "strategy_version": evidence.strategy_version,
        "config_digest": evidence.config_digest,
        "implementation_digest": evidence.implementation_digest,
        "data_digest": evidence.data_digest,
        "manifest_digest": evidence.manifest_digest,
        "wiring_chain_digest": evidence.wiring_chain_digest,
        "policy_digest": evidence.policy_digest,
        "evidence_digest": evidence.manifest_digest,
    }

    from src.ops.economic_summary_archive_sibling_exporter_v1.exporter_v1 import (
        coerce_economic_summary_fields_export_payload_v1,
    )

    coerced, error = coerce_economic_summary_fields_export_payload_v1(raw_fields)
    if coerced is None:
        return None, (error or ERROR_SOURCE_INVALID,)
    return coerced, ()
