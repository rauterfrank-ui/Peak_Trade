"""Non-selecting Demo environment validation for Cap24-bound instrument identity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.constants_v1 import (
    BOUND_INSTRUMENT_OWNER,
    SELECTED_INSTRUMENT_OWNER,
    TESTNET_INSTRUMENT_MAPPING_ALLOWED,
    TESTNET_INSTRUMENT_SUBSTITUTION_ALLOWED,
    TESTNET_SECONDARY_SELECTION_ALLOWED,
)


class GhvTestnetEnvironmentValidationError(RuntimeError):
    """Fail-closed environment validation violation."""


@dataclass(frozen=True)
class GhvTestnetEnvironmentValidationInputV1:
    cap23_selected_native_id: str
    cap24_bound_native_id: str
    validation_native_id: str


@dataclass(frozen=True)
class GhvTestnetEnvironmentValidationResultV1:
    status: str
    fail_closed: bool
    reason_codes: tuple[str, ...]
    cap23_selected_native_id: str
    cap24_bound_native_id: str
    testnet_selected_native_id: str


def evaluate_ghv_testnet_environment_validation_v1(
    *,
    input_v1: GhvTestnetEnvironmentValidationInputV1,
    demo_public_instruments_payload: Mapping[str, Any] | None = None,
) -> GhvTestnetEnvironmentValidationResultV1:
    cap23 = str(input_v1.cap23_selected_native_id or "").strip()
    cap24 = str(input_v1.cap24_bound_native_id or "").strip()
    probe = str(input_v1.validation_native_id or "").strip()
    reasons: list[str] = []

    if TESTNET_INSTRUMENT_SUBSTITUTION_ALLOWED or TESTNET_INSTRUMENT_MAPPING_ALLOWED:
        reasons.append("TESTNET_INSTRUMENT_SUBSTITUTION_CONTRACT_VIOLATION")
    if TESTNET_SECONDARY_SELECTION_ALLOWED:
        reasons.append("TESTNET_SECONDARY_SELECTION_CONTRACT_VIOLATION")

    if not cap24:
        reasons.append("CAP24_BOUND_NATIVE_ID_MISSING")
    if not cap23:
        reasons.append("CAP23_SELECTED_NATIVE_ID_MISSING")
    if cap23 and cap24 and cap23 != cap24:
        reasons.append("CAP23_CAP24_NATIVE_ID_MISMATCH")
    if probe and cap24 and probe != cap24:
        reasons.append("TESTNET_INSTRUMENT_MISMATCH")
    if not probe:
        reasons.append("VALIDATION_NATIVE_ID_MISSING")

    if demo_public_instruments_payload is not None:
        inst_ids = _extract_inst_ids_v1(demo_public_instruments_payload)
        if cap24 and inst_ids and cap24 not in inst_ids:
            reasons.append("DEMO_ENVIRONMENT_INSTRUMENT_NOT_LISTED")

    fail_closed = bool(reasons)
    status = "FAIL_CLOSED" if fail_closed else "PASS"
    return GhvTestnetEnvironmentValidationResultV1(
        status=status,
        fail_closed=fail_closed,
        reason_codes=tuple(reasons),
        cap23_selected_native_id=cap23,
        cap24_bound_native_id=cap24,
        testnet_selected_native_id=cap24 if cap24 else probe,
    )


def assert_ghv_testnet_environment_validation_pass_v1(
    result: GhvTestnetEnvironmentValidationResultV1,
) -> None:
    if result.fail_closed or result.status != "PASS":
        raise GhvTestnetEnvironmentValidationError(
            "TESTNET_ENVIRONMENT_VALIDATION_FAIL_CLOSED:"
            + (result.reason_codes[0] if result.reason_codes else "UNKNOWN")
        )


def prove_instrument_identity_owners_unchanged_v1() -> dict[str, str]:
    return {
        "SELECTED_INSTRUMENT_OWNER": SELECTED_INSTRUMENT_OWNER,
        "BOUND_INSTRUMENT_OWNER": BOUND_INSTRUMENT_OWNER,
        "TESTNET_INSTRUMENT_SUBSTITUTION_ALLOWED": "false",
        "TESTNET_SECONDARY_SELECTION_ALLOWED": "false",
    }


def _extract_inst_ids_v1(payload: Mapping[str, Any]) -> frozenset[str]:
    data = payload.get("data")
    if not isinstance(data, Sequence):
        return frozenset()
    out: set[str] = set()
    for row in data:
        if isinstance(row, Mapping):
            inst = row.get("instId")
            if isinstance(inst, str) and inst.strip():
                out.add(inst.strip())
    return frozenset(out)
