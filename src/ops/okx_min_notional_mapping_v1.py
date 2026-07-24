"""Sole owner: official OKX linear SWAP min-notional mapping (Decimal only).

Non-authorizing. Does not place orders, activate runtime, or invent missing units.
Inverse / ambiguous contract semantics fail closed.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "OKX_MIN_NOTIONAL_MAPPING_V1=true"
MAPPING_RATIFICATION_ID = "okx_min_notional_official_mapping_ratification_v1"
FORMULA_ID = "OKX_LINEAR_SWAP_MIN_QUOTE_NOTIONAL_FROM_MINSZ_CTVAL_MARKPX_V1"
FORMULA_VERSION = "v1"
MIN_NOTIONAL_KIND = "REFERENCE_PRICE_DERIVED_FROM_PROVIDER_AUTHENTIC_FIELDS"
REFERENCE_PRICE_TYPE = "okx_public_mark_price"
OFFICIAL_DOCUMENTATION_REFERENCE = (
    "https://www.okx.com/docs-v5/en/#public-data-rest-api-get-instruments"
)
CONFIG_RELATIVE_PATH = "config/ops/okx_min_notional_official_mapping_ratification_v1.json"

REASON_INVERSE_OR_AMBIGUOUS = "OKX_MIN_NOTIONAL_INVERSE_OR_AMBIGUOUS_REJECTED"
REASON_MISSING_REFERENCE_PRICE = "OKX_MIN_NOTIONAL_MISSING_REFERENCE_PRICE"
REASON_STALE_REFERENCE_PRICE = "OKX_MIN_NOTIONAL_STALE_REFERENCE_PRICE"
REASON_NON_POSITIVE_INPUT = "OKX_MIN_NOTIONAL_NON_POSITIVE_INPUT"
REASON_MISSING_PROVIDER_FIELD = "OKX_MIN_NOTIONAL_MISSING_PROVIDER_FIELD"
REASON_BTC_EXCLUDED = "OKX_MIN_NOTIONAL_BTC_EXCLUDED"
REASON_SPOT_EXCLUDED = "OKX_MIN_NOTIONAL_SPOT_EXCLUDED"
REASON_UNSUPPORTED_SETTLE = "OKX_MIN_NOTIONAL_UNSUPPORTED_SETTLE_CCY"


class OkxMinNotionalMappingError(ValueError):
    """Fail-closed mapping rejection."""


@dataclass(frozen=True)
class OkxMinNotionalMappingResultV1:
    eligible: bool
    min_notional_kind: str
    minimum_contract_quantity: str | None
    ct_val: str | None
    ct_val_ccy: str | None
    ct_type: str | None
    reference_price: str | None
    reference_price_type: str | None
    reference_price_captured_at: str | None
    computed_min_notional: str | None
    formula_id: str
    formula_version: str
    official_documentation_reference: str
    raw_capture_digest: str | None
    mapping_ratification_id: str
    reason_codes: tuple[str, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_mapping_ratification_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    root = repo_root or _repo_root()
    path = root / CONFIG_RELATIVE_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise OkxMinNotionalMappingError("ratification config must be object")
    if data.get("schema_id") != MAPPING_RATIFICATION_ID:
        raise OkxMinNotionalMappingError("ratification schema_id mismatch")
    if data.get("OKX_MIN_NOTIONAL_DIRECT_FIELD_AVAILABLE") is not False:
        raise OkxMinNotionalMappingError("direct field claim must remain false")
    if data.get("OKX_MIN_NOTIONAL_MAPPING_AUTHORIZED") is not True:
        raise OkxMinNotionalMappingError("mapping not authorized")
    return data


def _dec(value: Any, *, field: str) -> Decimal:
    if value is None or value == "":
        raise OkxMinNotionalMappingError(f"{REASON_MISSING_PROVIDER_FIELD}:{field}")
    if isinstance(value, float):
        raise OkxMinNotionalMappingError(f"FLOAT_MONEY_FORBIDDEN:{field}")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise OkxMinNotionalMappingError(f"{REASON_MISSING_PROVIDER_FIELD}:{field}") from exc
    if parsed <= 0:
        raise OkxMinNotionalMappingError(f"{REASON_NON_POSITIVE_INPUT}:{field}")
    return parsed


def _base_from_inst(inst: Mapping[str, Any]) -> str:
    uly = str(inst.get("uly") or "").strip().upper()
    if uly and "-" in uly:
        return uly.split("-", 1)[0]
    inst_id = str(inst.get("instId") or "").strip().upper()
    if inst_id and "-" in inst_id:
        return inst_id.split("-", 1)[0]
    return str(inst.get("baseCcy") or "").strip().upper()


def _is_btc(inst: Mapping[str, Any]) -> bool:
    tokens = (
        str(inst.get("instId") or ""),
        str(inst.get("uly") or ""),
        str(inst.get("baseCcy") or ""),
        str(inst.get("ctValCcy") or ""),
        _base_from_inst(inst),
    )
    for token in tokens:
        upper = token.upper()
        if upper in {"BTC", "XBT", "WBTC", "TBTC"} or upper.startswith("BTC-") or "-BTC-" in upper:
            return True
        if upper.endswith("-BTC") or upper.startswith("BTC"):
            # ETH-BTC-SWAP style / BTC-*
            parts = upper.replace("_", "-").split("-")
            if "BTC" in parts or "XBT" in parts:
                return True
    return False


def map_okx_linear_swap_min_notional_v1(
    *,
    instrument: Mapping[str, Any],
    reference_price: Any,
    reference_price_captured_at: str,
    raw_capture_digest: str | None,
    reference_price_fresh: bool = True,
) -> OkxMinNotionalMappingResultV1:
    """Map provider-authentic OKX fields to typed reference-price-derived min notional."""
    reasons: list[str] = []
    inst_type = str(instrument.get("instType") or "").strip().upper()
    ct_type = str(instrument.get("ctType") or "").strip().lower()
    settle = str(instrument.get("settleCcy") or "").strip().upper()
    ct_val_ccy = str(instrument.get("ctValCcy") or "").strip().upper()
    base = _base_from_inst(instrument)

    if inst_type == "SPOT" or str(instrument.get("instId") or "").upper().endswith("-SPOT"):
        reasons.append(REASON_SPOT_EXCLUDED)
    if _is_btc(instrument):
        reasons.append(REASON_BTC_EXCLUDED)
    if inst_type not in {"SWAP", "FUTURES"}:
        reasons.append(REASON_INVERSE_OR_AMBIGUOUS)
    if ct_type != "linear":
        reasons.append(REASON_INVERSE_OR_AMBIGUOUS)
    if settle != "USDT":
        reasons.append(REASON_UNSUPPORTED_SETTLE)
    if not ct_val_ccy or not base or ct_val_ccy != base:
        reasons.append(REASON_INVERSE_OR_AMBIGUOUS)
    if reference_price is None or reference_price == "":
        reasons.append(REASON_MISSING_REFERENCE_PRICE)
    if not reference_price_fresh:
        reasons.append(REASON_STALE_REFERENCE_PRICE)
    if not reference_price_captured_at:
        reasons.append(REASON_MISSING_REFERENCE_PRICE)

    if reasons:
        return OkxMinNotionalMappingResultV1(
            eligible=False,
            min_notional_kind=MIN_NOTIONAL_KIND,
            minimum_contract_quantity=None,
            ct_val=None,
            ct_val_ccy=ct_val_ccy or None,
            ct_type=ct_type or None,
            reference_price=None,
            reference_price_type=REFERENCE_PRICE_TYPE,
            reference_price_captured_at=reference_price_captured_at or None,
            computed_min_notional=None,
            formula_id=FORMULA_ID,
            formula_version=FORMULA_VERSION,
            official_documentation_reference=OFFICIAL_DOCUMENTATION_REFERENCE,
            raw_capture_digest=raw_capture_digest,
            mapping_ratification_id=MAPPING_RATIFICATION_ID,
            reason_codes=tuple(sorted(set(reasons))),
        )

    min_sz = _dec(instrument.get("minSz"), field="minSz")
    ct_val = _dec(instrument.get("ctVal"), field="ctVal")
    mark = _dec(reference_price, field="markPx")
    minimum_base = min_sz * ct_val
    computed = minimum_base * mark

    return OkxMinNotionalMappingResultV1(
        eligible=True,
        min_notional_kind=MIN_NOTIONAL_KIND,
        minimum_contract_quantity=format(min_sz, "f"),
        ct_val=format(ct_val, "f"),
        ct_val_ccy=ct_val_ccy,
        ct_type=ct_type,
        reference_price=format(mark, "f"),
        reference_price_type=REFERENCE_PRICE_TYPE,
        reference_price_captured_at=reference_price_captured_at,
        computed_min_notional=format(computed, "f"),
        formula_id=FORMULA_ID,
        formula_version=FORMULA_VERSION,
        official_documentation_reference=OFFICIAL_DOCUMENTATION_REFERENCE,
        raw_capture_digest=raw_capture_digest,
        mapping_ratification_id=MAPPING_RATIFICATION_ID,
        reason_codes=(),
    )


def assert_no_adhoc_min_notional_expression(source_text: str) -> None:
    """Static helper used by architecture guards — detect float-ish ad-hoc expressions."""
    banned = (
        "minSz * price",
        "min_sz * price",
        "float(minSz)",
        "float(min_sz)",
    )
    lowered = source_text.replace(" ", "")
    for token in banned:
        if token.replace(" ", "") in lowered:
            raise OkxMinNotionalMappingError(f"ADHOC_MIN_NOTIONAL_EXPRESSION:{token}")
