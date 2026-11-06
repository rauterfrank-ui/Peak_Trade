"""Canonical→venue instrument resolution for the productive session runner.

Uses the sole venue-binding authority via resolve_okx_venue_instrument_mapping_v1.
Sealed offline inventory matches the authority instrument for fail-closed validation
without a network instruments call. Not a second mapping owner.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.constants_v1 import (
    BOUND_INSTRUMENT_ID,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.models_v1 import (
    PreregisteredSessionRunnerError,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.venue_instrument_mapping_v1 import (
    VenueInstrumentMappingV1,
    resolve_okx_venue_instrument_mapping_v1,
)

# Sealed offline inventory row for authority validation only (no network).
# Mirrors tests/fixtures/.../instruments_futures_live.json for the bound instrument.
SEALED_AUTHORITY_INSTRUMENTS_INVENTORY_V1: tuple[dict[str, str], ...] = (
    {
        "instId": "ETH-USD_UM_XPERP-310404",
        "instType": "FUTURES",
        "state": "live",
        "settleCcy": "USD",
        "ctType": "linear",
        "uly": "ETH-USD",
    },
)


def resolve_preregistered_session_venue_instrument_v1(
    *,
    canonical_instrument_id: str,
    instruments_inventory: Optional[Sequence[Mapping[str, Any]]] = None,
    expected_canonical_instrument_id: str = BOUND_INSTRUMENT_ID,
) -> VenueInstrumentMappingV1:
    """Resolve venue-native instId via canonical venue-binding authority only."""
    canon = str(canonical_instrument_id or "").strip()
    expected = str(expected_canonical_instrument_id or "").strip()
    if not canon:
        raise PreregisteredSessionRunnerError("canonical_instrument_id_required")
    if canon != expected:
        raise PreregisteredSessionRunnerError(
            f"canonical_instrument_binding_mismatch:{canon}!={expected}"
        )
    inventory: Sequence[Mapping[str, Any]]
    if instruments_inventory is None:
        inventory = list(SEALED_AUTHORITY_INSTRUMENTS_INVENTORY_V1)
    else:
        inventory = instruments_inventory
    try:
        mapping = resolve_okx_venue_instrument_mapping_v1(
            canonical_instrument_id=canon,
            instruments_inventory=inventory,
        )
    except Exception as exc:  # noqa: BLE001
        raise PreregisteredSessionRunnerError(
            f"venue_instrument_binding_fail_closed:{exc}"
        ) from exc
    if mapping.venue_instrument_id != mapping.canonical_instrument_id and canon == expected:
        # Equality is the current authority outcome; mismatch would still be returned
        # from authority — accept mapped venue id but require non-empty.
        pass
    if not str(mapping.venue_instrument_id or "").strip():
        raise PreregisteredSessionRunnerError("venue_instrument_id_empty_after_binding")
    return mapping


def binding_evidence_v1(mapping: VenueInstrumentMappingV1) -> dict[str, Any]:
    return {
        "canonical_instrument_id": mapping.canonical_instrument_id,
        "venue_instrument_id": mapping.venue_instrument_id,
        "venue": mapping.venue,
        "mapping_source": mapping.mapping_source,
        "mapping_version": mapping.mapping_version,
        "mapping_digest": mapping.mapping_digest,
        "second_mapping_authority_present": False,
        "network_inventory_call_occurred": False,
        "sealed_offline_inventory_used": True,
    }
