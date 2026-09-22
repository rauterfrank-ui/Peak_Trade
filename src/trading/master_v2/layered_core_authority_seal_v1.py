"""Immutable LayeredCoreAuthoritySealV1 — P5.1 delegated-replay capability only.

Does not authorize productive cutover, P4 productive binding, or external effects.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple

from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
    AUTHORITY_CUTOVER_OCCURRED,
    PRODUCTIVE_BINDING_AUTHORIZED,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import (
    EXPLICIT_LAYERED_CORE_VERSION,
)
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1

SEAL_CONTRACT_VERSION = "layered_core_authority_seal.v1"
SEAL_OWNER = "trading.master_v2.layered_core_authority_seal_v1"

P5_AUTHORITY_CUTOVER_AUTHORIZED = False
P4_PRODUCTIVE_BINDING = False
NUMERIC_FORMULA_AUTHORITY = "NONE"
EXTERNAL_EFFECT_AUTHORIZED = False
OPTIMIZER_PRODUCTIVE_AUTHORITY = "NONE"
MULTI_FUTURE_RUNTIME_AUTHORIZED = False

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


class LayeredCoreAuthoritySealError(ValueError):
    """Fail-closed seal validation or construction violation."""


@dataclass(frozen=True)
class LayeredCoreAuthoritySealV1:
    seal_contract_version: str
    seal_id: str
    core_version: str
    instrument_id: str
    episode_snapshot_id: str
    store_manifest_digest: str
    regime_pre: str
    regime_post: str
    nullline_price: float
    d_t: float
    r_t: float
    cm_t: float
    switch_condition_met: bool
    mechanical_step_count: int
    cz4_delegation_active: bool
    seal_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "seal_contract_version": self.seal_contract_version,
            "seal_id": self.seal_id,
            "core_version": self.core_version,
            "instrument_id": self.instrument_id,
            "episode_snapshot_id": self.episode_snapshot_id,
            "store_manifest_digest": self.store_manifest_digest,
            "regime_pre": self.regime_pre,
            "regime_post": self.regime_post,
            "nullline_price": self.nullline_price,
            "d_t": self.d_t,
            "r_t": self.r_t,
            "cm_t": self.cm_t,
            "switch_condition_met": self.switch_condition_met,
            "mechanical_step_count": self.mechanical_step_count,
            "cz4_delegation_active": self.cz4_delegation_active,
            "seal_digest": self.seal_digest,
            "p5_authority_cutover_authorized": P5_AUTHORITY_CUTOVER_AUTHORIZED,
            "p4_productive_binding": P4_PRODUCTIVE_BINDING,
            "authority_cutover_occurred": AUTHORITY_CUTOVER_OCCURRED,
            "productive_binding_authorized": PRODUCTIVE_BINDING_AUTHORIZED,
        }


@dataclass(frozen=True)
class LayeredCoreAuthoritySealValidationResultV1:
    ok: bool
    failure_codes: Tuple[str, ...]


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _finite_positive(value: object) -> bool:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return number == number and number not in (float("inf"), float("-inf")) and number > 0.0


def _finite_non_negative(value: object) -> bool:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return number == number and number not in (float("inf"), float("-inf")) and number >= 0.0


def compute_seal_digest_material_v1(
    *,
    seal_contract_version: str,
    seal_id: str,
    core_version: str,
    instrument_id: str,
    episode_snapshot_id: str,
    store_manifest_digest: str,
    regime_pre: str,
    regime_post: str,
    nullline_price: float,
    d_t: float,
    r_t: float,
    cm_t: float,
    switch_condition_met: bool,
    mechanical_step_count: int,
) -> str:
    material = {
        "seal_contract_version": seal_contract_version,
        "seal_id": seal_id,
        "core_version": core_version,
        "instrument_id": instrument_id,
        "episode_snapshot_id": episode_snapshot_id,
        "store_manifest_digest": store_manifest_digest,
        "regime_pre": regime_pre,
        "regime_post": regime_post,
        "nullline_price": float(nullline_price),
        "d_t": float(d_t),
        "r_t": float(r_t),
        "cm_t": float(cm_t),
        "switch_condition_met": bool(switch_condition_met),
        "mechanical_step_count": int(mechanical_step_count),
    }
    return hashlib.sha256(_canonical_json(material).encode("utf-8")).hexdigest()


def build_layered_core_authority_seal_v1(
    *,
    seal_id: str,
    instrument_id: str,
    episode_snapshot_id: str,
    store_manifest_digest: str,
    regime_pre: NakedRegimeV1,
    regime_post: NakedRegimeV1,
    nullline_price: float,
    d_t: float,
    r_t: float,
    cm_t: float,
    switch_condition_met: bool,
    mechanical_step_count: int,
    cz4_delegation_active: bool = True,
) -> LayeredCoreAuthoritySealV1:
    digest = compute_seal_digest_material_v1(
        seal_contract_version=SEAL_CONTRACT_VERSION,
        seal_id=seal_id,
        core_version=EXPLICIT_LAYERED_CORE_VERSION,
        instrument_id=instrument_id,
        episode_snapshot_id=episode_snapshot_id,
        store_manifest_digest=store_manifest_digest,
        regime_pre=regime_pre.value,
        regime_post=regime_post.value,
        nullline_price=nullline_price,
        d_t=d_t,
        r_t=r_t,
        cm_t=cm_t,
        switch_condition_met=switch_condition_met,
        mechanical_step_count=mechanical_step_count,
    )
    return LayeredCoreAuthoritySealV1(
        seal_contract_version=SEAL_CONTRACT_VERSION,
        seal_id=seal_id,
        core_version=EXPLICIT_LAYERED_CORE_VERSION,
        instrument_id=instrument_id,
        episode_snapshot_id=episode_snapshot_id,
        store_manifest_digest=store_manifest_digest,
        regime_pre=regime_pre.value,
        regime_post=regime_post.value,
        nullline_price=float(nullline_price),
        d_t=float(d_t),
        r_t=float(r_t),
        cm_t=float(cm_t),
        switch_condition_met=bool(switch_condition_met),
        mechanical_step_count=int(mechanical_step_count),
        cz4_delegation_active=bool(cz4_delegation_active),
        seal_digest=digest,
    )


def validate_layered_core_authority_seal_v1(
    seal: Optional[LayeredCoreAuthoritySealV1],
    *,
    instrument_id: str,
) -> LayeredCoreAuthoritySealValidationResultV1:
    if seal is None:
        return LayeredCoreAuthoritySealValidationResultV1(ok=False, failure_codes=("seal_missing",))
    failures: list[str] = []
    if seal.seal_contract_version != SEAL_CONTRACT_VERSION:
        failures.append("seal_contract_version_mismatch")
    if seal.core_version != EXPLICIT_LAYERED_CORE_VERSION:
        failures.append("core_version_mismatch")
    if not seal.seal_id.strip():
        failures.append("seal_id_missing")
    if not seal.instrument_id.strip():
        failures.append("instrument_id_missing")
    elif seal.instrument_id != instrument_id:
        failures.append("instrument_id_mismatch")
    if not _SHA256_HEX.match(seal.episode_snapshot_id or ""):
        failures.append("episode_snapshot_id_invalid")
    if not _SHA256_HEX.match(seal.store_manifest_digest or ""):
        failures.append("store_manifest_digest_invalid")
    if seal.regime_pre not in (NakedRegimeV1.BULL.value, NakedRegimeV1.BEAR.value):
        failures.append("regime_pre_invalid")
    if seal.regime_post not in (NakedRegimeV1.BULL.value, NakedRegimeV1.BEAR.value):
        failures.append("regime_post_invalid")
    if not _finite_positive(seal.nullline_price):
        failures.append("nullline_price_invalid")
    if not _finite_positive(seal.d_t):
        failures.append("d_t_invalid")
    if not _finite_non_negative(seal.r_t):
        failures.append("r_t_invalid")
    if not _finite_non_negative(seal.cm_t):
        failures.append("cm_t_invalid")
    if seal.mechanical_step_count < 0:
        failures.append("mechanical_step_count_invalid")
    if not seal.cz4_delegation_active:
        failures.append("cz4_delegation_not_active")
    expected_digest = compute_seal_digest_material_v1(
        seal_contract_version=seal.seal_contract_version,
        seal_id=seal.seal_id,
        core_version=seal.core_version,
        instrument_id=seal.instrument_id,
        episode_snapshot_id=seal.episode_snapshot_id,
        store_manifest_digest=seal.store_manifest_digest,
        regime_pre=seal.regime_pre,
        regime_post=seal.regime_post,
        nullline_price=seal.nullline_price,
        d_t=seal.d_t,
        r_t=seal.r_t,
        cm_t=seal.cm_t,
        switch_condition_met=seal.switch_condition_met,
        mechanical_step_count=seal.mechanical_step_count,
    )
    if seal.seal_digest != expected_digest:
        failures.append("seal_digest_mismatch")
    if P5_AUTHORITY_CUTOVER_AUTHORIZED:
        failures.append("p5_cutover_not_authorized_in_v1")
    if P4_PRODUCTIVE_BINDING:
        failures.append("p4_productive_binding_forbidden")
    return LayeredCoreAuthoritySealValidationResultV1(
        ok=not failures,
        failure_codes=tuple(failures),
    )


__all__ = [
    "EXTERNAL_EFFECT_AUTHORIZED",
    "LayeredCoreAuthoritySealError",
    "LayeredCoreAuthoritySealV1",
    "LayeredCoreAuthoritySealValidationResultV1",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "NUMERIC_FORMULA_AUTHORITY",
    "OPTIMIZER_PRODUCTIVE_AUTHORITY",
    "P4_PRODUCTIVE_BINDING",
    "P5_AUTHORITY_CUTOVER_AUTHORIZED",
    "SEAL_CONTRACT_VERSION",
    "SEAL_OWNER",
    "build_layered_core_authority_seal_v1",
    "compute_seal_digest_material_v1",
    "validate_layered_core_authority_seal_v1",
]
