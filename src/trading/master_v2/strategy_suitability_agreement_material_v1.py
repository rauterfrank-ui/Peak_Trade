# src/trading/master_v2/strategy_suitability_agreement_material_v1.py
"""
Master-V2-native Strategy Suitability Agreement Material v1.

Family-scoped normalized agreement input for evaluate_suitability_binding_v1.
Does not import backtest StrategySignalBindingResultV1 or other backtest types.

OBL_B05_ENTRY_EXIT_OPTIONAL_SIDE_CARRIER_CONTRACT_V1:
optional explicit ``entry_side`` ∈ {LONG, SHORT, NONE} for ENTRY_EXIT_EVENT_V1.
Default NONE; never derived from cycle_signal_value sign, band-cross, or suitability.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, Mapping, Optional

STRATEGY_SUITABILITY_AGREEMENT_MATERIAL_LAYER_VERSION = "v1"
STRATEGY_SUITABILITY_AGREEMENT_MATERIAL_OWNER = (
    "trading.master_v2.strategy_suitability_agreement_material_v1"
)


class StrategySignalEncodingClassV1(str, Enum):
    POSITIONAL_LS_STATE_V1 = "POSITIONAL_LS_STATE_V1"
    POSITIONAL_LONG01_STATE_V1 = "POSITIONAL_LONG01_STATE_V1"
    ENTRY_EXIT_EVENT_V1 = "ENTRY_EXIT_EVENT_V1"
    FILTER_MASK01_V1 = "FILTER_MASK01_V1"
    UNKNOWN_OR_STUB_V1 = "UNKNOWN_OR_STUB_V1"


class StrategySideAgreementV1(str, Enum):
    AGREE = "AGREE"
    DISAGREE = "DISAGREE"
    NEUTRAL = "NEUTRAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class StrategyAgreementEventKindV1(str, Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    NONE = "NONE"


class StrategyEntrySideCarrierV1(str, Enum):
    """Explicit ENTRY side carrier for ENTRY_EXIT_EVENT_V1 only.

    NONE is the fail-closed default for all legacy producers. LONG/SHORT are
    never inferred from cycle_signal_value (+1/-1), band-cross, or suitability.
    """

    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


class StrategySuitabilityAgreementErrorV1(ValueError):
    """Fail-closed strategy suitability agreement material error."""


def _valid_sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def compute_strategy_suitability_agreement_material_digest_v1(
    *,
    encoding_class: StrategySignalEncodingClassV1,
    configured_strategy_id: str,
    executed_strategy_id: str,
    strategy_version: str,
    strategy_params_digest: str,
    strategy_signal_digest: str,
    instrument_id: str,
    trading_epoch: int,
    cycle_signal_value: int,
    side_agreement: StrategySideAgreementV1,
    filter_pass: Optional[bool],
    event_kind: Optional[StrategyAgreementEventKindV1],
    entry_side: StrategyEntrySideCarrierV1 = StrategyEntrySideCarrierV1.NONE,
) -> str:
    payload = {
        "configured_strategy_id": configured_strategy_id,
        "cycle_signal_value": cycle_signal_value,
        "encoding_class": encoding_class.value,
        "entry_side": entry_side.value,
        "event_kind": None if event_kind is None else event_kind.value,
        "executed_strategy_id": executed_strategy_id,
        "filter_pass": filter_pass,
        "instrument_id": instrument_id,
        "layer_version": STRATEGY_SUITABILITY_AGREEMENT_MATERIAL_LAYER_VERSION,
        "owner": STRATEGY_SUITABILITY_AGREEMENT_MATERIAL_OWNER,
        "side_agreement": side_agreement.value,
        "strategy_params_digest": strategy_params_digest,
        "strategy_signal_digest": strategy_signal_digest,
        "strategy_version": strategy_version,
        "trading_epoch": trading_epoch,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class StrategySuitabilityAgreementMaterialV1:
    encoding_class: StrategySignalEncodingClassV1
    configured_strategy_id: str
    executed_strategy_id: str
    strategy_version: str
    strategy_params_digest: str
    strategy_signal_digest: str
    instrument_id: str
    trading_epoch: int
    cycle_signal_value: Literal[-1, 0, 1]
    side_agreement: StrategySideAgreementV1
    filter_pass: Optional[bool]
    event_kind: Optional[StrategyAgreementEventKindV1]
    material_digest: str
    entry_side: StrategyEntrySideCarrierV1 = StrategyEntrySideCarrierV1.NONE

    def __post_init__(self) -> None:
        if self.encoding_class is StrategySignalEncodingClassV1.UNKNOWN_OR_STUB_V1:
            raise StrategySuitabilityAgreementErrorV1("stub_or_unknown_strategy_semantics")
        if self.cycle_signal_value not in (-1, 0, 1):
            raise StrategySuitabilityAgreementErrorV1("cycle_signal_value_invalid")
        if not self.configured_strategy_id or not self.executed_strategy_id:
            raise StrategySuitabilityAgreementErrorV1("strategy_identity_mismatch")
        if not self.strategy_version:
            raise StrategySuitabilityAgreementErrorV1("strategy_version_mismatch")
        if not _valid_sha256_hex(self.strategy_params_digest):
            raise StrategySuitabilityAgreementErrorV1("strategy_params_digest_mismatch")
        if not _valid_sha256_hex(self.strategy_signal_digest):
            raise StrategySuitabilityAgreementErrorV1("strategy_signal_digest_mismatch")
        if not self.instrument_id:
            raise StrategySuitabilityAgreementErrorV1("instrument_mismatch")
        if not isinstance(self.trading_epoch, int) or isinstance(self.trading_epoch, bool):
            raise StrategySuitabilityAgreementErrorV1("trading_epoch_mismatch")
        if not _valid_sha256_hex(self.material_digest):
            raise StrategySuitabilityAgreementErrorV1("material_digest_invalid")
        if (
            self.encoding_class is StrategySignalEncodingClassV1.POSITIONAL_LONG01_STATE_V1
            and self.cycle_signal_value == -1
        ):
            raise StrategySuitabilityAgreementErrorV1("stub_or_unknown_strategy_semantics")
        if not isinstance(self.entry_side, StrategyEntrySideCarrierV1):
            raise StrategySuitabilityAgreementErrorV1("entry_side_invalid")
        if self.entry_side is not StrategyEntrySideCarrierV1.NONE:
            if self.encoding_class is not StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1:
                raise StrategySuitabilityAgreementErrorV1("entry_side_encoding_mismatch")
            if self.event_kind is not StrategyAgreementEventKindV1.ENTRY:
                raise StrategySuitabilityAgreementErrorV1("entry_side_event_kind_mismatch")


def serialize_strategy_suitability_agreement_material_v1(
    material: StrategySuitabilityAgreementMaterialV1,
) -> dict[str, Any]:
    """Canonical JSON-ready mapping; preserves ``entry_side`` losslessly."""
    return {
        "configured_strategy_id": material.configured_strategy_id,
        "cycle_signal_value": material.cycle_signal_value,
        "encoding_class": material.encoding_class.value,
        "entry_side": material.entry_side.value,
        "event_kind": None if material.event_kind is None else material.event_kind.value,
        "executed_strategy_id": material.executed_strategy_id,
        "filter_pass": material.filter_pass,
        "instrument_id": material.instrument_id,
        "material_digest": material.material_digest,
        "side_agreement": material.side_agreement.value,
        "strategy_params_digest": material.strategy_params_digest,
        "strategy_signal_digest": material.strategy_signal_digest,
        "strategy_version": material.strategy_version,
        "trading_epoch": material.trading_epoch,
    }


def deserialize_strategy_suitability_agreement_material_v1(
    payload: Mapping[str, Any],
) -> StrategySuitabilityAgreementMaterialV1:
    """Rebuild material from a mapping. Missing ``entry_side`` → NONE (legacy)."""
    try:
        encoding_class = StrategySignalEncodingClassV1(str(payload["encoding_class"]))
        side_agreement = StrategySideAgreementV1(str(payload["side_agreement"]))
        raw_event = payload.get("event_kind")
        event_kind = None if raw_event is None else StrategyAgreementEventKindV1(str(raw_event))
        raw_side = payload.get("entry_side", StrategyEntrySideCarrierV1.NONE.value)
        if raw_side is None:
            entry_side = StrategyEntrySideCarrierV1.NONE
        else:
            entry_side = StrategyEntrySideCarrierV1(str(raw_side))
        cycle = int(payload["cycle_signal_value"])
        if cycle not in (-1, 0, 1):
            raise StrategySuitabilityAgreementErrorV1("cycle_signal_value_invalid")
        return StrategySuitabilityAgreementMaterialV1(
            encoding_class=encoding_class,
            configured_strategy_id=str(payload["configured_strategy_id"]),
            executed_strategy_id=str(payload["executed_strategy_id"]),
            strategy_version=str(payload["strategy_version"]),
            strategy_params_digest=str(payload["strategy_params_digest"]),
            strategy_signal_digest=str(payload["strategy_signal_digest"]),
            instrument_id=str(payload["instrument_id"]),
            trading_epoch=int(payload["trading_epoch"]),
            cycle_signal_value=cycle,  # type: ignore[arg-type]
            side_agreement=side_agreement,
            filter_pass=payload.get("filter_pass"),
            event_kind=event_kind,
            material_digest=str(payload["material_digest"]),
            entry_side=entry_side,
        )
    except StrategySuitabilityAgreementErrorV1:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise StrategySuitabilityAgreementErrorV1("material_deserialize_invalid") from exc


def fold_strategy_suitability_agreement_into_input_digest_v1(
    base_input_digest: str,
    material: Optional[StrategySuitabilityAgreementMaterialV1],
) -> str:
    """Fold agreement material into a base input digest. None leaves digest unchanged."""
    if material is None:
        return base_input_digest
    if not _valid_sha256_hex(base_input_digest) and base_input_digest:
        raise StrategySuitabilityAgreementErrorV1("input_digest_invalid")
    payload = {
        "base_input_digest": base_input_digest,
        "cycle_signal_value": material.cycle_signal_value,
        "encoding_class": material.encoding_class.value,
        "entry_side": material.entry_side.value,
        "material_digest": material.material_digest,
        "owner": STRATEGY_SUITABILITY_AGREEMENT_MATERIAL_OWNER,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = [
    "STRATEGY_SUITABILITY_AGREEMENT_MATERIAL_LAYER_VERSION",
    "STRATEGY_SUITABILITY_AGREEMENT_MATERIAL_OWNER",
    "StrategyAgreementEventKindV1",
    "StrategyEntrySideCarrierV1",
    "StrategySideAgreementV1",
    "StrategySignalEncodingClassV1",
    "StrategySuitabilityAgreementErrorV1",
    "StrategySuitabilityAgreementMaterialV1",
    "compute_strategy_suitability_agreement_material_digest_v1",
    "deserialize_strategy_suitability_agreement_material_v1",
    "fold_strategy_suitability_agreement_into_input_digest_v1",
    "serialize_strategy_suitability_agreement_material_v1",
]
