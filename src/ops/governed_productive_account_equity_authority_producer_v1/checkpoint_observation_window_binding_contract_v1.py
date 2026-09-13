"""D5 checkpoint/observation window-binding contract.

Explicit fail-closed window binding for one D5 checkpoint observation.
Does not derive start/end from now, lookback, bills, balance, venue
history, or fixtures. Does not imply event completeness. Does not
silently equate window_end with observed_at_as_of. No venue GET.
AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_contract_v1 import (
    BoundAccountIdentityContractError,
    assert_same_bound_account_identity_v1,
    require_bound_account_identity_ref_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_acquisition_contract_v1 import (
    CheckpointObservationAcquisitionResultV1,
    CheckpointObservationCheckpointBindingV1,
    NETWORK_METHOD_NONE,
    compute_checkpoint_observation_digest_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    CHECKPOINT_OBSERVATION_NETWORK_GET_AUTHORIZED,
    D5_WINDOW_BINDING_CONTRACT_PRESENT,
    D5_WINDOW_END_EQUALS_OBSERVED_AT_AS_OF_RELATION_AUTHORITY_PRESENT,
    EVENT_ACQUISITION_CREATED,
)

SCHEMA_CLASS = "CHECKPOINT_OBSERVATION_WINDOW_BINDING_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
BINDING_CLASS_EXPLICIT = "EXPLICIT_TYPED_WINDOW_BINDING"
BINDING_CLASS_GENESIS_EPOCH = "GENESIS_EPOCH_POINT_WINDOW_BINDING"
AS_OF_RELATION_UNPROVEN = "UNPROVEN_NO_IMPLIED_EQUALITY"
AS_OF_RELATION_GENESIS_EPOCH = "GENESIS_EPOCH_COINCIDENT_NOT_COMPLETENESS"
WINDOW_DERIVATION_GENESIS_EPOCH = "GENESIS_EPOCH_POINT"
WINDOW_RUNTIME_INSTANCE_FILENAME = "d5_checkpoint_observation_window_binding_v1.json"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
CONTRACT_STATUS_PROVEN = "CONTRACT_PROVEN"
_ISO_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_WINDOW_DERIVATION_CLASSES: Tuple[str, ...] = (
    "IMPLICIT_NOW",
    "CURRENT_TIME",
    "NOW",
    "LOOKBACK",
    "IMPLICIT_LOOKBACK",
    "BILLS_HISTORY",
    "BALANCE_HISTORY",
    "VENUE_HISTORY",
    "FIXTURE_DEFAULT",
    "FIXTURE",
    "DEFAULT",
    "HISTORY",
)
_FORBIDDEN_WINDOW_MARKERS: Tuple[str, ...] = (
    "now",
    "utcnow",
    "lookback",
    "datetime.now",
    "fixture",
    "bills-history",
    "balance-history",
    "venue-history",
)
FORBIDDEN_AS_OF_RELATION_CLAIMS: Tuple[str, ...] = (
    "IMPLIED_EQUAL",
    "WINDOW_END_EQUALS_OBSERVED_AT_AS_OF",
    "DERIVED_FROM_AS_OF",
    "EXPLICITLY_BOUND_EQUAL",
    "IMPLICIT_EQUAL",
)


class CheckpointObservationWindowBindingContractError(ValueError):
    """Fail-closed D5 window-binding contract violation."""


@dataclass(frozen=True)
class CheckpointObservationWindowBindingV1:
    binding_id: str
    binding_class: str
    checkpoint_id: str
    checkpoint_observation_ref: str
    checkpoint_observation_digest: str
    bound_account_identity_ref: str
    bound_account_identity_digest: str
    observed_at_as_of: str
    checkpoint_window_start: str
    checkpoint_window_end: str
    observed_at_as_of_relation_class: str
    window_derivation_class: str
    event_completeness_from_window: str
    network_method: str
    contract_status: str
    runtime_instance_present: str
    authority_effect: str
    provenance_digest: str


@dataclass(frozen=True)
class CheckpointObservationWindowBindingStatusV1:
    contract_status: str
    runtime_instance_present: str
    artifact_present: str
    event_completeness_from_window: str


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_checkpoint_window_binding_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise CheckpointObservationWindowBindingContractError(f"D5_WINDOW_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise CheckpointObservationWindowBindingContractError(f"D5_WINDOW_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise CheckpointObservationWindowBindingContractError(f"D5_WINDOW_FIELD_MISSING:{field}")
    return text


def _require_iso_z(*, field: str, raw: Any) -> str:
    text = _require_non_empty_str(field=field, raw=raw)
    if _ISO_Z.fullmatch(text) is None:
        raise CheckpointObservationWindowBindingContractError(
            f"D5_WINDOW_TIMESTAMP_NOT_ISO_Z:{field}"
        )
    lowered = text.lower()
    if any(marker in lowered for marker in _FORBIDDEN_WINDOW_MARKERS):
        raise CheckpointObservationWindowBindingContractError(
            f"D5_WINDOW_IMPLICIT_NOW_OR_LOOKBACK_FORBIDDEN:{field}"
        )
    return text


def _parse_iso_z(raw: str) -> datetime:
    body = raw[:-1]
    if "." in body:
        parsed = datetime.strptime(body, "%Y-%m-%dT%H:%M:%S.%f")
    else:
        parsed = datetime.strptime(body, "%Y-%m-%dT%H:%M:%S")
    return parsed.replace(tzinfo=timezone.utc)


def d5_window_binding_path_v1(*, store_root: Path | str) -> Path:
    return Path(store_root) / WINDOW_RUNTIME_INSTANCE_FILENAME


def _assert_window_pins() -> None:
    if D5_WINDOW_BINDING_CONTRACT_PRESENT is not True:
        raise CheckpointObservationWindowBindingContractError(
            "D5_WINDOW_BINDING_CONTRACT_NOT_PRESENT"
        )
    if D5_WINDOW_END_EQUALS_OBSERVED_AT_AS_OF_RELATION_AUTHORITY_PRESENT is not False:
        raise CheckpointObservationWindowBindingContractError(
            "D5_WINDOW_AS_OF_EQUALITY_AUTHORITY_MUST_REMAIN_ABSENT"
        )
    if CHECKPOINT_OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise CheckpointObservationWindowBindingContractError(
            "CHECKPOINT_OBSERVATION_NETWORK_GET_NOT_UNAUTHORIZED"
        )
    if ACCOUNT_EQUITY_AUTHORITY_OWNER != (
        "ops.governed_productive_account_equity_authority_producer_v1"
    ):
        raise CheckpointObservationWindowBindingContractError("D5_WINDOW_AUTHORITY_OWNER_MUTATED")


def bind_checkpoint_observation_window_v1(
    *,
    binding_id: str,
    checkpoint_id: str,
    acquisition: CheckpointObservationAcquisitionResultV1,
    checkpoint_binding: CheckpointObservationCheckpointBindingV1,
    checkpoint_window_start: str,
    checkpoint_window_end: str,
    binding_class: str = BINDING_CLASS_EXPLICIT,
    window_derivation_class: str = BINDING_CLASS_EXPLICIT,
    observed_at_as_of_relation_class: str = AS_OF_RELATION_UNPROVEN,
    event_completeness_from_window: str = FALSE_TOKEN,
) -> CheckpointObservationWindowBindingV1:
    _assert_window_pins()
    binding = _require_non_empty_str(field="binding_id", raw=binding_id)
    checkpoint = _require_non_empty_str(field="checkpoint_id", raw=checkpoint_id)
    cls = _require_non_empty_str(field="binding_class", raw=binding_class)
    derivation = _require_non_empty_str(
        field="window_derivation_class", raw=window_derivation_class
    )
    relation = _require_non_empty_str(
        field="observed_at_as_of_relation_class", raw=observed_at_as_of_relation_class
    )
    completeness = _require_non_empty_str(
        field="event_completeness_from_window", raw=event_completeness_from_window
    )
    start = _require_iso_z(field="checkpoint_window_start", raw=checkpoint_window_start)
    end = _require_iso_z(field="checkpoint_window_end", raw=checkpoint_window_end)
    observed_at = _require_iso_z(field="observed_at_as_of", raw=acquisition.observed_at_as_of)
    if derivation in FORBIDDEN_WINDOW_DERIVATION_CLASSES:
        raise CheckpointObservationWindowBindingContractError(
            f"D5_WINDOW_IMPLICIT_NOW_OR_LOOKBACK_FORBIDDEN:{derivation}"
        )
    if relation in FORBIDDEN_AS_OF_RELATION_CLAIMS:
        raise CheckpointObservationWindowBindingContractError(
            f"D5_WINDOW_AS_OF_RELATION_AUTHORITY_ABSENT:{relation}"
        )
    if cls == BINDING_CLASS_GENESIS_EPOCH:
        if derivation != WINDOW_DERIVATION_GENESIS_EPOCH:
            raise CheckpointObservationWindowBindingContractError(
                f"D5_WINDOW_GENESIS_DERIVATION_REQUIRED:{derivation}"
            )
        if relation != AS_OF_RELATION_GENESIS_EPOCH:
            raise CheckpointObservationWindowBindingContractError(
                f"D5_WINDOW_GENESIS_RELATION_REQUIRED:{relation}"
            )
        if start != end or start != observed_at:
            raise CheckpointObservationWindowBindingContractError(
                "D5_WINDOW_GENESIS_START_END_AS_OF_MUST_COINCIDE"
            )
    elif cls == BINDING_CLASS_EXPLICIT:
        if derivation != BINDING_CLASS_EXPLICIT:
            raise CheckpointObservationWindowBindingContractError(
                f"D5_WINDOW_DERIVATION_NOT_EXPLICIT:{derivation}"
            )
        if relation != AS_OF_RELATION_UNPROVEN:
            raise CheckpointObservationWindowBindingContractError(
                f"D5_WINDOW_AS_OF_RELATION_NOT_EXPLICITLY_UNPROVEN:{relation}"
            )
    else:
        raise CheckpointObservationWindowBindingContractError(
            f"D5_WINDOW_BINDING_CLASS_NOT_EXPLICIT:{cls}"
        )
    if completeness != FALSE_TOKEN:
        raise CheckpointObservationWindowBindingContractError(
            "D5_WINDOW_CANNOT_PROVE_EVENT_COMPLETENESS"
        )
    if _parse_iso_z(start) > _parse_iso_z(end):
        raise CheckpointObservationWindowBindingContractError("D5_WINDOW_RANGE_INVALID")
    try:
        require_bound_account_identity_ref_v1(
            bound_account_identity_ref=acquisition.bound_account_identity_ref,
            bound_account_identity_digest=acquisition.bound_account_identity_digest,
        )
        assert_same_bound_account_identity_v1(
            left_ref=acquisition.bound_account_identity_ref,
            left_digest=acquisition.bound_account_identity_digest,
            right_ref=checkpoint_binding.bound_account_identity_ref,
            right_digest=checkpoint_binding.bound_account_identity_digest,
        )
    except BoundAccountIdentityContractError as exc:
        raise CheckpointObservationWindowBindingContractError(
            "D5_WINDOW_IDENTITY_MISMATCH_CROSS_ACCOUNT"
        ) from exc
    if checkpoint_binding.checkpoint_id != checkpoint:
        raise CheckpointObservationWindowBindingContractError("D5_WINDOW_CHECKPOINT_REF_MISMATCH")
    if checkpoint_binding.checkpoint_observation_ref != acquisition.observation_id:
        raise CheckpointObservationWindowBindingContractError("D5_WINDOW_OBSERVATION_REF_MISMATCH")
    if checkpoint_binding.checkpoint_observation_digest != acquisition.provenance_digest:
        raise CheckpointObservationWindowBindingContractError(
            "D5_WINDOW_OBSERVATION_DIGEST_MISMATCH"
        )
    if acquisition.network_method != NETWORK_METHOD_NONE:
        raise CheckpointObservationWindowBindingContractError("D5_WINDOW_NETWORK_METHOD_NOT_NONE")
    if EVENT_ACQUISITION_CREATED is True and completeness == TRUE_TOKEN:
        raise CheckpointObservationWindowBindingContractError(
            "D5_WINDOW_CANNOT_PROVE_EVENT_COMPLETENESS"
        )
    recomputed = compute_checkpoint_observation_digest_v1(
        {
            "observation_id": acquisition.observation_id,
            "source_observation_id": acquisition.source_observation_id,
            "observation_semantic_class": acquisition.observation_semantic_class,
            "authority_owner": acquisition.authority_owner,
            "bound_account_identity_ref": acquisition.bound_account_identity_ref,
            "bound_account_identity_digest": acquisition.bound_account_identity_digest,
            "observed_at_as_of": acquisition.observed_at_as_of,
            "acquired_at": acquisition.acquired_at,
            "component_completeness": acquisition.component_completeness,
            "freshness_policy_status": acquisition.freshness_policy_status,
            "observation_vs_authority_class": acquisition.observation_vs_authority_class,
            "network_method": acquisition.network_method,
            "claimed_equity_stock_value": acquisition.claimed_equity_stock_value,
            "reconstructed_equity_created": acquisition.reconstructed_equity_created,
            "event_stream_acquisition_created": acquisition.event_stream_acquisition_created,
            "eq_reconciliation_executed": acquisition.eq_reconciliation_executed,
            "raw_eq_source_authority": acquisition.raw_eq_source_authority,
            "source_selected": acquisition.source_selected,
            "mapping_proven": acquisition.mapping_proven,
            "c17_created": acquisition.c17_created,
            "authority_effect": acquisition.authority_effect,
        }
    )
    if recomputed != acquisition.provenance_digest:
        raise CheckpointObservationWindowBindingContractError(
            "D5_WINDOW_OBSERVATION_DIGEST_NOT_STABLE"
        )
    if not _SHA256_HEX.match(acquisition.provenance_digest):
        raise CheckpointObservationWindowBindingContractError(
            "D5_WINDOW_OBSERVATION_DIGEST_NOT_SHA256"
        )
    payload = {
        "binding_id": binding,
        "binding_class": cls,
        "checkpoint_id": checkpoint,
        "checkpoint_observation_ref": acquisition.observation_id,
        "checkpoint_observation_digest": acquisition.provenance_digest,
        "bound_account_identity_ref": acquisition.bound_account_identity_ref,
        "bound_account_identity_digest": acquisition.bound_account_identity_digest,
        "observed_at_as_of": observed_at,
        "checkpoint_window_start": start,
        "checkpoint_window_end": end,
        "observed_at_as_of_relation_class": relation,
        "window_derivation_class": derivation,
        "event_completeness_from_window": FALSE_TOKEN,
        "network_method": NETWORK_METHOD_NONE,
        "contract_status": CONTRACT_STATUS_PROVEN,
        "runtime_instance_present": TRUE_TOKEN,
        "authority_effect": AUTHORITY_EFFECT,
    }
    digest = compute_checkpoint_window_binding_digest_v1(payload)
    return CheckpointObservationWindowBindingV1(
        **payload,
        provenance_digest=digest,
    )


def persist_checkpoint_observation_window_binding_v1(
    *,
    store_root: Path | str,
    binding: CheckpointObservationWindowBindingV1,
) -> CheckpointObservationWindowBindingV1:
    _assert_window_pins()
    if binding.runtime_instance_present != TRUE_TOKEN:
        raise CheckpointObservationWindowBindingContractError(
            "D5_WINDOW_RUNTIME_INSTANCE_PRESENT_TOKEN_INVALID"
        )
    if binding.event_completeness_from_window != FALSE_TOKEN:
        raise CheckpointObservationWindowBindingContractError(
            "D5_WINDOW_CANNOT_PROVE_EVENT_COMPLETENESS"
        )
    path = d5_window_binding_path_v1(store_root=store_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "binding_id": binding.binding_id,
        "binding_class": binding.binding_class,
        "checkpoint_id": binding.checkpoint_id,
        "checkpoint_observation_ref": binding.checkpoint_observation_ref,
        "checkpoint_observation_digest": binding.checkpoint_observation_digest,
        "bound_account_identity_ref": binding.bound_account_identity_ref,
        "bound_account_identity_digest": binding.bound_account_identity_digest,
        "observed_at_as_of": binding.observed_at_as_of,
        "checkpoint_window_start": binding.checkpoint_window_start,
        "checkpoint_window_end": binding.checkpoint_window_end,
        "observed_at_as_of_relation_class": binding.observed_at_as_of_relation_class,
        "window_derivation_class": binding.window_derivation_class,
        "event_completeness_from_window": binding.event_completeness_from_window,
        "network_method": binding.network_method,
        "contract_status": binding.contract_status,
        "runtime_instance_present": binding.runtime_instance_present,
        "authority_effect": binding.authority_effect,
        "provenance_digest": binding.provenance_digest,
    }
    encoded = _canonical_json(payload) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(encoded, encoding="utf-8")
    tmp.replace(path)
    return binding


def load_checkpoint_observation_window_binding_v1(
    *,
    store_root: Path | str | None,
) -> CheckpointObservationWindowBindingV1:
    _assert_window_pins()
    if store_root is None:
        raise CheckpointObservationWindowBindingContractError("D5_WINDOW_RUNTIME_INSTANCE_ABSENT")
    path = d5_window_binding_path_v1(store_root=store_root)
    if not path.is_file():
        raise CheckpointObservationWindowBindingContractError("D5_WINDOW_RUNTIME_INSTANCE_ABSENT")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise CheckpointObservationWindowBindingContractError(
            "D5_WINDOW_RUNTIME_INSTANCE_MALFORMED"
        )
    fields = (
        "binding_id",
        "binding_class",
        "checkpoint_id",
        "checkpoint_observation_ref",
        "checkpoint_observation_digest",
        "bound_account_identity_ref",
        "bound_account_identity_digest",
        "observed_at_as_of",
        "checkpoint_window_start",
        "checkpoint_window_end",
        "observed_at_as_of_relation_class",
        "window_derivation_class",
        "event_completeness_from_window",
        "network_method",
        "contract_status",
        "runtime_instance_present",
        "authority_effect",
        "provenance_digest",
    )
    payload = {key: _require_non_empty_str(field=key, raw=raw.get(key)) for key in fields}
    digest_payload = {key: payload[key] for key in payload if key != "provenance_digest"}
    expected = compute_checkpoint_window_binding_digest_v1(digest_payload)
    if payload["provenance_digest"] != expected:
        raise CheckpointObservationWindowBindingContractError("D5_WINDOW_DIGEST_MISMATCH")
    if payload["event_completeness_from_window"] != FALSE_TOKEN:
        raise CheckpointObservationWindowBindingContractError(
            "D5_WINDOW_CANNOT_PROVE_EVENT_COMPLETENESS"
        )
    if payload["observed_at_as_of_relation_class"] not in {
        AS_OF_RELATION_UNPROVEN,
        AS_OF_RELATION_GENESIS_EPOCH,
    }:
        raise CheckpointObservationWindowBindingContractError(
            "D5_WINDOW_AS_OF_RELATION_AUTHORITY_ABSENT:"
            f"{payload['observed_at_as_of_relation_class']}"
        )
    if (
        payload["observed_at_as_of_relation_class"] == AS_OF_RELATION_GENESIS_EPOCH
        and payload["binding_class"] != BINDING_CLASS_GENESIS_EPOCH
    ):
        raise CheckpointObservationWindowBindingContractError(
            "D5_WINDOW_GENESIS_RELATION_REQUIRES_GENESIS_BINDING_CLASS"
        )
    if payload["window_derivation_class"] in FORBIDDEN_WINDOW_DERIVATION_CLASSES:
        raise CheckpointObservationWindowBindingContractError(
            f"D5_WINDOW_IMPLICIT_NOW_OR_LOOKBACK_FORBIDDEN:{payload['window_derivation_class']}"
        )
    return CheckpointObservationWindowBindingV1(**payload)


def inspect_checkpoint_observation_window_binding_status_v1(
    *,
    store_root: Path | str | None = None,
) -> CheckpointObservationWindowBindingStatusV1:
    _assert_window_pins()
    if store_root is None:
        return CheckpointObservationWindowBindingStatusV1(
            contract_status=CONTRACT_STATUS_PROVEN,
            runtime_instance_present=FALSE_TOKEN,
            artifact_present=FALSE_TOKEN,
            event_completeness_from_window=FALSE_TOKEN,
        )
    path = d5_window_binding_path_v1(store_root=store_root)
    if not path.is_file():
        return CheckpointObservationWindowBindingStatusV1(
            contract_status=CONTRACT_STATUS_PROVEN,
            runtime_instance_present=FALSE_TOKEN,
            artifact_present=FALSE_TOKEN,
            event_completeness_from_window=FALSE_TOKEN,
        )
    loaded = load_checkpoint_observation_window_binding_v1(store_root=store_root)
    return CheckpointObservationWindowBindingStatusV1(
        contract_status=loaded.contract_status,
        runtime_instance_present=loaded.runtime_instance_present,
        artifact_present=TRUE_TOKEN,
        event_completeness_from_window=FALSE_TOKEN,
    )


def reject_implicit_now_or_lookback_window_v1(*, window_derivation_class: str) -> None:
    derivation = _require_non_empty_str(
        field="window_derivation_class", raw=window_derivation_class
    )
    if derivation in FORBIDDEN_WINDOW_DERIVATION_CLASSES:
        raise CheckpointObservationWindowBindingContractError(
            f"D5_WINDOW_IMPLICIT_NOW_OR_LOOKBACK_FORBIDDEN:{derivation}"
        )
    raise CheckpointObservationWindowBindingContractError(
        f"D5_WINDOW_DERIVATION_NOT_EXPLICIT:{derivation}"
    )
