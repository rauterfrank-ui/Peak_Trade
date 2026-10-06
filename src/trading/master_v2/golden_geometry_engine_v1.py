"""Golden Geometry Engine V1 — sole productive owner of market-derived base geometry magnitude.

Computes CanonicalBaseGeometryMagnitudeV1: deterministic positive finite distance in the
same price unit as the canonical mark, from canonical mark price and resolved volatility only.
Does not depend on Scope state, side, position, or downstream trading semantics.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from trading.master_v2.canonical_market_context_v1 import CanonicalMarketContextV1

GGE_OWNER = "trading.master_v2.golden_geometry_engine_v1"
GGE_MODEL_VERSION = "golden_geometry_engine.v1"
GGE_MODEL_ID = "gge_v1_volatility_times_mark_price"
GGE_OUTPUT_UNIT = "canonical_mark_price_unit"
GGE_OUTPUT_SEMANTIC = "CanonicalBaseGeometryMagnitudeV1"

PRODUCTIVE_BASE_GEOMETRY_PRODUCER_ID = (
    "trading.master_v2.golden_geometry_engine_v1/gge_v1_volatility_times_mark_price/v1"
)

CURRENT_CONTROL_FORMULA_ID = "current_control_volatility_times_mark_price"
CURRENT_CONTROL_FORMULA = "D = volatility_estimate × mark_price"


@dataclass(frozen=True)
class CanonicalGeometryInputV1:
    """Minimum productive market inputs at the geometry seam."""

    instrument_id: str
    mark_price: float
    volatility_estimate: float
    observation_lineage_id: str = ""
    reference_timestamp: str = ""


@dataclass(frozen=True)
class CanonicalBaseGeometryMagnitudeV1:
    magnitude: float
    unit_semantic: str
    model_id: str
    model_version: str
    instrument_id: str
    input_digest: str
    mark_price: float
    volatility_estimate: float
    observation_lineage_id: str
    reference_timestamp: str


@dataclass(frozen=True)
class GoldenGeometryEngineResultV1:
    ok: bool
    output: CanonicalBaseGeometryMagnitudeV1 | None
    failure_codes: Tuple[str, ...]


def _positive_finite(value: object) -> bool:
    if not isinstance(value, (int, float)):
        return False
    f = float(value)
    return math.isfinite(f) and f > 0.0


def _productive_instrument_id(raw: str) -> str | None:
    inst = str(raw or "").strip()
    return inst if inst else None


def _input_digest_material(inp: CanonicalGeometryInputV1) -> str:
    inst = _productive_instrument_id(inp.instrument_id)
    if inst is None:
        inst = "unspecified"
    payload = {
        "instrument_id": inst,
        "mark_price": float(inp.mark_price),
        "volatility_estimate": float(inp.volatility_estimate),
        "model_id": GGE_MODEL_ID,
        "model_version": GGE_MODEL_VERSION,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_current_control_base_geometry_magnitude_v1(
    *,
    mark_price: float,
    volatility_estimate: float,
) -> float | None:
    """Non-authoritative σ×P reference for evaluation harnesses (AUTHORITY=NONE)."""
    if not _positive_finite(mark_price) or not _positive_finite(volatility_estimate):
        return None
    magnitude = float(volatility_estimate) * float(mark_price)
    if not _positive_finite(magnitude):
        return None
    return magnitude


class GoldenGeometryEngineV1:
    """Stateless GGE V1 — adjudicated model: volatility_estimate × mark_price."""

    model_id: str = GGE_MODEL_ID
    model_version: str = GGE_MODEL_VERSION

    @staticmethod
    def compute_base_geometry_magnitude_v1(
        inp: CanonicalGeometryInputV1,
    ) -> GoldenGeometryEngineResultV1:
        failures: list[str] = []
        if _productive_instrument_id(inp.instrument_id) is None:
            failures.append("instrument_id_blank")
        if not _positive_finite(inp.mark_price):
            failures.append("mark_price_non_positive")
        if not _positive_finite(inp.volatility_estimate):
            failures.append("volatility_non_positive")
        if failures:
            return GoldenGeometryEngineResultV1(
                ok=False,
                output=None,
                failure_codes=tuple(failures),
            )

        mark_price = float(inp.mark_price)
        volatility_estimate = float(inp.volatility_estimate)
        magnitude = volatility_estimate * mark_price
        if not _positive_finite(magnitude):
            return GoldenGeometryEngineResultV1(
                ok=False,
                output=None,
                failure_codes=("base_geometry_magnitude_invalid",),
            )

        digest = _input_digest_material(inp)
        output = CanonicalBaseGeometryMagnitudeV1(
            magnitude=magnitude,
            unit_semantic=GGE_OUTPUT_UNIT,
            model_id=GGE_MODEL_ID,
            model_version=GGE_MODEL_VERSION,
            instrument_id=str(_productive_instrument_id(inp.instrument_id) or ""),
            input_digest=digest,
            mark_price=mark_price,
            volatility_estimate=volatility_estimate,
            observation_lineage_id=str(inp.observation_lineage_id or ""),
            reference_timestamp=str(inp.reference_timestamp or ""),
        )
        return GoldenGeometryEngineResultV1(ok=True, output=output, failure_codes=())


def compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
    *,
    instrument_id: str,
    mark_price: float,
    volatility_estimate: float,
    observation_lineage_id: str = "",
    reference_timestamp: str = "",
) -> GoldenGeometryEngineResultV1:
    return GoldenGeometryEngineV1.compute_base_geometry_magnitude_v1(
        CanonicalGeometryInputV1(
            instrument_id=instrument_id,
            mark_price=mark_price,
            volatility_estimate=volatility_estimate,
            observation_lineage_id=observation_lineage_id,
            reference_timestamp=reference_timestamp,
        )
    )


def compute_canonical_base_geometry_magnitude_from_market_context_v1(
    market_context: CanonicalMarketContextV1,
) -> GoldenGeometryEngineResultV1:
    from trading.master_v2.canonical_geometry_volatility_v1 import (
        CanonicalGeometryVolatilityError,
        resolve_canonical_geometry_volatility_v1,
    )
    from trading.master_v2.canonical_market_context_v1 import CanonicalMarketContextV1

    if not isinstance(market_context, CanonicalMarketContextV1):
        return GoldenGeometryEngineResultV1(
            ok=False,
            output=None,
            failure_codes=("market_context_invalid",),
        )

    if _productive_instrument_id(market_context.instrument_id) is None:
        return GoldenGeometryEngineResultV1(
            ok=False,
            output=None,
            failure_codes=("instrument_id_blank",),
        )

    if not _positive_finite(market_context.mark_price):
        return GoldenGeometryEngineResultV1(
            ok=False,
            output=None,
            failure_codes=("mark_price_non_positive",),
        )

    try:
        geom_vol = resolve_canonical_geometry_volatility_v1(market_context)
        vol = float(geom_vol.value)
    except CanonicalGeometryVolatilityError as exc:
        code = exc.code.value.lower()
        return GoldenGeometryEngineResultV1(
            ok=False,
            output=None,
            failure_codes=(f"geometry_volatility_{code}",),
        )
    except Exception:
        return GoldenGeometryEngineResultV1(
            ok=False,
            output=None,
            failure_codes=("volatility_unavailable",),
        )

    lineage = str(market_context.input_digest or market_context.context_id or "")
    return compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id=str(market_context.instrument_id).strip(),
        mark_price=float(market_context.mark_price),
        volatility_estimate=vol,
        observation_lineage_id=lineage,
        reference_timestamp=str(market_context.decision_time or market_context.market_event_time),
    )


__all__ = [
    "CURRENT_CONTROL_FORMULA",
    "CURRENT_CONTROL_FORMULA_ID",
    "CanonicalBaseGeometryMagnitudeV1",
    "CanonicalGeometryInputV1",
    "GGE_MODEL_ID",
    "GGE_MODEL_VERSION",
    "GGE_OWNER",
    "GGE_OUTPUT_SEMANTIC",
    "GGE_OUTPUT_UNIT",
    "GoldenGeometryEngineResultV1",
    "GoldenGeometryEngineV1",
    "PRODUCTIVE_BASE_GEOMETRY_PRODUCER_ID",
    "compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1",
    "compute_canonical_base_geometry_magnitude_from_market_context_v1",
    "compute_current_control_base_geometry_magnitude_v1",
]
