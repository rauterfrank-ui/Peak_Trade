"""Explicit USDC→USDC identity conversion edge."""

from __future__ import annotations

from decimal import Decimal

from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
)
from src.ops.governed_productive_monetary_normalization_v1.constants_v1 import (
    AUTHORITY_SEMANTIC_IDENTITY,
    CANONICAL_INTERNAL_RISK_NUMERAIRE,
    FRESHNESS_POLICY,
    IDENTITY_RATE_UNIT,
    USDT_USDC_ENDPOINT,
    USDT_USDC_VENUE,
)
from src.ops.governed_productive_monetary_normalization_v1.contracts_v1 import ConversionEdgeV1


def build_usdc_identity_conversion_edge_v1(
    *,
    decision_epoch: str,
    observed_at: str,
    freshness_status: str | None = None,
    provenance_ref: str = "USDC_IDENTITY_EDGE_NO_NETWORK",
) -> ConversionEdgeV1:
    """Identity edge — no market GET; still explicit in normalization evidence."""
    status = str(freshness_status or FreshPretradeGetStatusV1.TRUSTED_PRESENT.value)
    epoch = str(decision_epoch or "").strip()
    observed = str(observed_at or epoch).strip()
    return ConversionEdgeV1(
        source_currency=CANONICAL_INTERNAL_RISK_NUMERAIRE,
        target_currency=CANONICAL_INTERNAL_RISK_NUMERAIRE,
        raw_rate=Decimal("1"),
        raw_rate_unit=IDENTITY_RATE_UNIT,
        normalized_rate=Decimal("1"),
        normalized_rate_unit=IDENTITY_RATE_UNIT,
        inversion_applied=False,
        venue=USDT_USDC_VENUE,
        endpoint=USDT_USDC_ENDPOINT,
        source_identity=f"{CANONICAL_INTERNAL_RISK_NUMERAIRE}-{CANONICAL_INTERNAL_RISK_NUMERAIRE}",
        source_field="IDENTITY",
        source_timestamp=observed,
        observed_at=observed,
        decision_epoch=epoch,
        freshness_status=status,
        payload_digest=provenance_ref,
        provenance_ref=provenance_ref,
        authority_semantic=AUTHORITY_SEMANTIC_IDENTITY,
    )
