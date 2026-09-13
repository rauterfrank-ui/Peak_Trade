"""Typed D6 classified event-stream acquisition contract.

Acquires and binds classified equity-affecting events for exactly one
BoundAccountIdentity against a D5 checkpoint observation boundary.
Events are not reconstructed equity and cannot mutate EQUITY_STOCK.
Completeness is COMPLETE only when kind-set, source, range, ordering,
and provenance are proven. Absence of events is not zero events.
No venue GET. Not a reconstruction engine. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_contract_v1 import (
    BoundAccountIdentityContractError,
    assert_same_bound_account_identity_v1,
    require_bound_account_identity_ref_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_acquisition_contract_v1 import (
    CheckpointObservationAcquisitionResultV1,
    CheckpointObservationCheckpointBindingV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    C17_CREATED,
    CHECKPOINT_OBSERVATION_PROVEN,
    COMPLETE_EVENT_STREAM_PROVEN,
    EVENT_ACQUISITION_CREATED,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    SOURCE_SELECTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    CLASSIFICATION_STATUS_CLASSIFIED,
    CLASSIFICATION_STATUS_UNCLASSIFIED,
    CLASSIFICATION_STATUS_UNKNOWN,
    RATIFIED_CLASSIFIED_KIND_SET,
    RATIFIED_CLASSIFIED_KIND_SET_RESOLVED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_stock_checkpoint_contract_v1 import (
    EQUITY_MINT_STATUS_NOT_MINTED,
    EquityStockCheckpointContractV1,
    assert_checkpoint_cannot_mint_equity_v1,
)

SCHEMA_CLASS = "CLASSIFIED_EVENT_STREAM_ACQUISITION_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
NETWORK_METHOD_NONE = "NONE"
EQUITY_VALUE_STATE_ABSENT = "ABSENT"
EQUITY_MUTATION_NOT_MUTATED = "NOT_MUTATED"
COMPLETENESS_COMPLETE = "COMPLETE"
COMPLETENESS_UNPROVEN = "UNPROVEN"
COMPLETENESS_UNKNOWN = "UNKNOWN"
COMPLETENESS_INCOMPLETE = "INCOMPLETE"
SOURCE_STATUS_MISSING = "MISSING"
SOURCE_STATUS_PRESENT = "PRESENT"
FALSE_TOKEN = "false"
UNKNOWN_TOKEN = "UNKNOWN"
MISSING_COMPLETENESS_DEPENDENCY = (
    "RATIFIED_CLASSIFIED_EVENT_KIND_SET_AND_AUTHORIZED_EVENT_SOURCE_SEAM"
)
COVERAGE_BOUNDARY_CLASS = "CHECKPOINT_PRECEDES_SUBSEQUENT_CLASSIFIED_EVENTS"
REQUIRED_EVENT_FIELDS: Tuple[str, ...] = (
    "event_id",
    "source_event_id",
    "taxonomy_class",
    "event_semantic_class",
    "source_reference",
    "ordering_key",
    "replay_identity",
    "event_digest",
    "bound_account_identity_ref",
    "bound_account_identity_digest",
    "equity_stock_mutation_status",
    "claimed_equity_stock_value",
    "network_method",
)
REQUIRED_STREAM_FIELDS: Tuple[str, ...] = (
    "stream_id",
    "checkpoint_id",
    "checkpoint_observation_ref",
    "checkpoint_observation_digest",
    "coverage_boundary_class",
    "completeness_status",
    "source_status",
    "ordering_proven",
    "gap_detected",
    "complete_event_stream_proven",
    "missing_completeness_dependency",
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_FAIL_CLOSED_TOKENS: Tuple[str, ...] = (
    "UNKNOWN",
    "MISSING",
    "STALE",
    "PARTIAL",
    "UNCLASSIFIED",
    "UNPROVEN",
    "UNSPECIFIED",
    "INCOMPLETE",
    "IDENTITY_MISMATCH",
    "GAP",
)
_FORBIDDEN_EQUITY_CLAIM_MARKERS: Tuple[str, ...] = (
    "equity_stock",
    "running_account_equity",
    "available_for_sizing",
    "reconstructed_equity",
    "totaleq",
    "availeq",
    "adjeq",
    "availbal",
    "cashbal",
)
_SILENT_ZERO_MARKERS: Tuple[str, ...] = (
    "0",
    "0.0",
    "zero",
    "no-op",
    "noop",
    "ignore",
    "omit",
)
_FORBIDDEN_NETWORK_METHODS: Tuple[str, ...] = ("GET", "POST", "PUT", "PATCH", "DELETE")


class ClassifiedEventStreamAcquisitionContractError(ValueError):
    """Fail-closed classified event-stream acquisition contract violation."""


@dataclass(frozen=True)
class ClassifiedEventAcquisitionResultV1:
    event_id: str
    source_event_id: str
    taxonomy_class: str
    event_semantic_class: str
    source_reference: str
    ordering_key: str
    replay_identity: str
    event_digest: str
    bound_account_identity_ref: str
    bound_account_identity_digest: str
    equity_stock_mutation_status: str
    claimed_equity_stock_value: str
    reconstructed_equity_created: str
    network_method: str
    authority_effect: str
    provenance_digest: str


@dataclass(frozen=True)
class ClassifiedEventStreamBindingV1:
    stream_id: str
    stream_replay_identity: str
    checkpoint_id: str
    checkpoint_provenance_digest: str
    checkpoint_observation_ref: str
    checkpoint_observation_digest: str
    bound_account_identity_ref: str
    bound_account_identity_digest: str
    coverage_boundary_class: str
    completeness_status: str
    source_status: str
    event_count: str
    ordering_proven: str
    gap_detected: str
    complete_event_stream_proven: str
    missing_completeness_dependency: str
    reconstructed_equity_created: str
    reconstruction_engine_created: str
    eq_reconciliation_executed: str
    raw_eq_source_authority: str
    source_selected: str
    mapping_proven: str
    c17_created: str
    network_method: str
    authority_effect: str
    provenance_digest: str


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise ClassifiedEventStreamAcquisitionContractError(f"EVENT_STREAM_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise ClassifiedEventStreamAcquisitionContractError(
            f"EVENT_STREAM_FIELD_NOT_STRING:{field}"
        )
    text = raw.strip()
    if text == "" or text != raw:
        raise ClassifiedEventStreamAcquisitionContractError(f"EVENT_STREAM_FIELD_MISSING:{field}")
    return text


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_classified_event_stream_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _reject_fail_closed_token(*, field: str, raw: str) -> None:
    if raw in _FAIL_CLOSED_TOKENS:
        raise ClassifiedEventStreamAcquisitionContractError(
            f"EVENT_STREAM_{raw}_FAIL_CLOSED:{field}"
        )


def _reject_equity_claim(*, field: str, raw: str) -> None:
    lowered = raw.lower()
    if any(marker in lowered for marker in _FORBIDDEN_EQUITY_CLAIM_MARKERS):
        raise ClassifiedEventStreamAcquisitionContractError(
            f"EVENT_STREAM_EQUITY_CLAIM_FORBIDDEN:{field}"
        )
    if raw.strip().lower() in _SILENT_ZERO_MARKERS:
        raise ClassifiedEventStreamAcquisitionContractError(
            f"EVENT_STREAM_ABSENCE_IS_NOT_ZERO:{field}"
        )


def _assert_shared_pins() -> None:
    if EVENT_ACQUISITION_CREATED is not True:
        raise ClassifiedEventStreamAcquisitionContractError("EVENT_ACQUISITION_CREATED_NOT_TRUE")
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise ClassifiedEventStreamAcquisitionContractError(
            "COMPLETE_EVENT_STREAM_PROVEN_NOT_FALSE"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise ClassifiedEventStreamAcquisitionContractError(
            "EVENT_ACQUISITION_NETWORK_GET_NOT_UNAUTHORIZED"
        )
    if CHECKPOINT_OBSERVATION_PROVEN is not True:
        raise ClassifiedEventStreamAcquisitionContractError("D5_CHECKPOINT_OBSERVATION_NOT_PROVEN")
    if RECONSTRUCTION_ENGINE_CREATED is not False:
        raise ClassifiedEventStreamAcquisitionContractError(
            "RECONSTRUCTION_ENGINE_CREATED_NOT_FALSE"
        )
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise ClassifiedEventStreamAcquisitionContractError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if SOURCE_SELECTED is not False:
        raise ClassifiedEventStreamAcquisitionContractError("SOURCE_SELECTED_NOT_FALSE")
    if C17_CREATED is not False:
        raise ClassifiedEventStreamAcquisitionContractError("C17_CREATED_NOT_FALSE")
    if ACCOUNT_EQUITY_AUTHORITY_OWNER != (
        "ops.governed_productive_account_equity_authority_producer_v1"
    ):
        raise ClassifiedEventStreamAcquisitionContractError("EVENT_STREAM_AUTHORITY_OWNER_MUTATED")


def _assert_identity_pair(
    *,
    expected_ref: str,
    expected_digest: str,
    observed_ref: str,
    observed_digest: str,
) -> Tuple[str, str]:
    left_ref, left_digest = require_bound_account_identity_ref_v1(
        bound_account_identity_ref=expected_ref,
        bound_account_identity_digest=expected_digest,
    )
    right_ref, right_digest = require_bound_account_identity_ref_v1(
        bound_account_identity_ref=observed_ref,
        bound_account_identity_digest=observed_digest,
    )
    try:
        assert_same_bound_account_identity_v1(
            left_ref=left_ref,
            left_digest=left_digest,
            right_ref=right_ref,
            right_digest=right_digest,
        )
    except BoundAccountIdentityContractError as exc:
        raise ClassifiedEventStreamAcquisitionContractError(
            "EVENT_STREAM_IDENTITY_MISMATCH_CROSS_ACCOUNT"
        ) from exc
    return right_ref, right_digest


def acquire_classified_event_v1(
    *,
    event_id: str,
    source_event_id: str,
    taxonomy_class: str,
    event_semantic_class: str,
    source_reference: str,
    ordering_key: str,
    replay_identity: str,
    event_digest: str,
    expected_bound_account_identity_ref: str,
    expected_bound_account_identity_digest: str,
    bound_account_identity_ref: str,
    bound_account_identity_digest: str,
    equity_stock_mutation_status: str = EQUITY_MUTATION_NOT_MUTATED,
    claimed_equity_stock_value: str = EQUITY_VALUE_STATE_ABSENT,
    network_method: str = NETWORK_METHOD_NONE,
) -> ClassifiedEventAcquisitionResultV1:
    _assert_shared_pins()
    observed_ref, observed_digest = _assert_identity_pair(
        expected_ref=expected_bound_account_identity_ref,
        expected_digest=expected_bound_account_identity_digest,
        observed_ref=bound_account_identity_ref,
        observed_digest=bound_account_identity_digest,
    )
    event = _require_non_empty_str(field="event_id", raw=event_id)
    source_event = _require_non_empty_str(field="source_event_id", raw=source_event_id)
    taxonomy = _require_non_empty_str(field="taxonomy_class", raw=taxonomy_class)
    semantic = _require_non_empty_str(field="event_semantic_class", raw=event_semantic_class)
    source_ref = _require_non_empty_str(field="source_reference", raw=source_reference)
    order_key = _require_non_empty_str(field="ordering_key", raw=ordering_key)
    replay = _require_non_empty_str(field="replay_identity", raw=replay_identity)
    digest = _require_non_empty_str(field="event_digest", raw=event_digest)
    mutation = _require_non_empty_str(
        field="equity_stock_mutation_status", raw=equity_stock_mutation_status
    )
    claimed = _require_non_empty_str(
        field="claimed_equity_stock_value", raw=claimed_equity_stock_value
    )
    method = _require_non_empty_str(field="network_method", raw=network_method)
    for field, value in (
        ("event_id", event),
        ("source_event_id", source_event),
        ("source_reference", source_ref),
        ("ordering_key", order_key),
        ("replay_identity", replay),
    ):
        _reject_fail_closed_token(field=field, raw=value)
        _reject_equity_claim(field=field, raw=value)
    if not _SHA256_HEX.match(digest):
        raise ClassifiedEventStreamAcquisitionContractError("EVENT_DIGEST_NOT_SHA256")
    if not _SHA256_HEX.match(replay):
        raise ClassifiedEventStreamAcquisitionContractError("EVENT_REPLAY_IDENTITY_NOT_SHA256")
    if taxonomy in (CLASSIFICATION_STATUS_UNKNOWN, CLASSIFICATION_STATUS_UNCLASSIFIED):
        raise ClassifiedEventStreamAcquisitionContractError(
            f"EVENT_STREAM_{taxonomy}_FAIL_CLOSED:taxonomy_class"
        )
    if semantic in (CLASSIFICATION_STATUS_UNKNOWN, CLASSIFICATION_STATUS_UNCLASSIFIED):
        raise ClassifiedEventStreamAcquisitionContractError(
            f"EVENT_STREAM_{semantic}_FAIL_CLOSED:event_semantic_class"
        )
    if taxonomy != CLASSIFICATION_STATUS_CLASSIFIED:
        raise ClassifiedEventStreamAcquisitionContractError(
            "EVENT_STREAM_TAXONOMY_CLASS_NOT_CLASSIFIED"
        )
    if RATIFIED_CLASSIFIED_KIND_SET_RESOLVED is not True or semantic not in (
        RATIFIED_CLASSIFIED_KIND_SET
    ):
        raise ClassifiedEventStreamAcquisitionContractError("CLASSIFIED_KIND_NOT_RATIFIED")
    if source_ref == SOURCE_STATUS_MISSING:
        raise ClassifiedEventStreamAcquisitionContractError(
            "EVENT_STREAM_MISSING_SOURCE_FAIL_CLOSED"
        )
    if mutation != EQUITY_MUTATION_NOT_MUTATED:
        raise ClassifiedEventStreamAcquisitionContractError(
            "EVENT_STREAM_CANNOT_MUTATE_EQUITY_STOCK"
        )
    if claimed != EQUITY_VALUE_STATE_ABSENT:
        raise ClassifiedEventStreamAcquisitionContractError(
            "EVENT_STREAM_CANNOT_MINT_OR_OVERWRITE_EQUITY"
        )
    _reject_equity_claim(field="claimed_equity_stock_value", raw=claimed)
    if method in _FORBIDDEN_NETWORK_METHODS:
        raise ClassifiedEventStreamAcquisitionContractError(
            f"EVENT_STREAM_NETWORK_METHOD_FORBIDDEN:{method}"
        )
    if method != NETWORK_METHOD_NONE:
        raise ClassifiedEventStreamAcquisitionContractError(
            f"EVENT_STREAM_NETWORK_METHOD_NOT_NONE:{method}"
        )
    payload = {
        "event_id": event,
        "source_event_id": source_event,
        "taxonomy_class": taxonomy,
        "event_semantic_class": semantic,
        "source_reference": source_ref,
        "ordering_key": order_key,
        "replay_identity": replay,
        "event_digest": digest,
        "bound_account_identity_ref": observed_ref,
        "bound_account_identity_digest": observed_digest,
        "equity_stock_mutation_status": mutation,
        "claimed_equity_stock_value": claimed,
        "reconstructed_equity_created": FALSE_TOKEN,
        "network_method": method,
        "authority_effect": AUTHORITY_EFFECT,
    }
    provenance = compute_classified_event_stream_digest_v1(payload)
    return ClassifiedEventAcquisitionResultV1(
        **payload,
        provenance_digest=provenance,
    )


def adjudicate_classified_event_stream_completeness_v1(
    *,
    events: Sequence[ClassifiedEventAcquisitionResultV1],
    claimed_completeness_status: str,
    source_status: str,
) -> Tuple[str, str, str, str]:
    completeness = _require_non_empty_str(
        field="completeness_status", raw=claimed_completeness_status
    )
    source = _require_non_empty_str(field="source_status", raw=source_status)
    if completeness == COMPLETENESS_COMPLETE:
        raise ClassifiedEventStreamAcquisitionContractError(
            "EVENT_STREAM_COMPLETENESS_COMPLETE_NOT_PROVEN"
        )
    if completeness not in (COMPLETENESS_UNPROVEN, COMPLETENESS_UNKNOWN, COMPLETENESS_INCOMPLETE):
        raise ClassifiedEventStreamAcquisitionContractError(
            f"EVENT_STREAM_COMPLETENESS_STATUS_UNKNOWN_TOKEN:{completeness}"
        )
    if source == SOURCE_STATUS_PRESENT:
        raise ClassifiedEventStreamAcquisitionContractError(
            "EVENT_STREAM_SOURCE_PRESENT_NOT_PROVEN"
        )
    if source != SOURCE_STATUS_MISSING:
        raise ClassifiedEventStreamAcquisitionContractError(
            f"EVENT_STREAM_SOURCE_STATUS_UNKNOWN_TOKEN:{source}"
        )
    if RATIFIED_CLASSIFIED_KIND_SET_RESOLVED is True and RATIFIED_CLASSIFIED_KIND_SET:
        raise ClassifiedEventStreamAcquisitionContractError(
            "EVENT_STREAM_KIND_SET_RESOLVED_WITHOUT_SOURCE"
        )
    if completeness == COMPLETENESS_COMPLETE and not events:
        raise ClassifiedEventStreamAcquisitionContractError("EVENT_STREAM_ABSENCE_IS_NOT_ZERO")
    return (
        completeness,
        source,
        FALSE_TOKEN,
        MISSING_COMPLETENESS_DEPENDENCY,
    )


def bind_classified_event_stream_to_checkpoint_v1(
    *,
    stream_id: str,
    checkpoint: EquityStockCheckpointContractV1,
    observation: CheckpointObservationAcquisitionResultV1,
    observation_binding: CheckpointObservationCheckpointBindingV1,
    events: Sequence[ClassifiedEventAcquisitionResultV1],
    completeness_status: str,
    source_status: str = SOURCE_STATUS_MISSING,
    network_method: str = NETWORK_METHOD_NONE,
) -> ClassifiedEventStreamBindingV1:
    _assert_shared_pins()
    stream = _require_non_empty_str(field="stream_id", raw=stream_id)
    _reject_fail_closed_token(field="stream_id", raw=stream)
    _reject_equity_claim(field="stream_id", raw=stream)
    method = _require_non_empty_str(field="network_method", raw=network_method)
    if method in _FORBIDDEN_NETWORK_METHODS:
        raise ClassifiedEventStreamAcquisitionContractError(
            f"EVENT_STREAM_NETWORK_METHOD_FORBIDDEN:{method}"
        )
    if method != NETWORK_METHOD_NONE:
        raise ClassifiedEventStreamAcquisitionContractError(
            f"EVENT_STREAM_NETWORK_METHOD_NOT_NONE:{method}"
        )
    observed_ref, observed_digest = _assert_identity_pair(
        expected_ref=checkpoint.bound_account_identity_ref,
        expected_digest=checkpoint.bound_account_identity_digest,
        observed_ref=observation.bound_account_identity_ref,
        observed_digest=observation.bound_account_identity_digest,
    )
    _assert_identity_pair(
        expected_ref=observed_ref,
        expected_digest=observed_digest,
        observed_ref=observation_binding.bound_account_identity_ref,
        observed_digest=observation_binding.bound_account_identity_digest,
    )
    if observation_binding.checkpoint_id != checkpoint.checkpoint_id:
        raise ClassifiedEventStreamAcquisitionContractError(
            "EVENT_STREAM_CHECKPOINT_OBSERVATION_BINDING_MISMATCH"
        )
    if observation_binding.checkpoint_observation_ref != observation.observation_id:
        raise ClassifiedEventStreamAcquisitionContractError(
            "EVENT_STREAM_CHECKPOINT_OBSERVATION_REF_MISMATCH"
        )
    if observation_binding.checkpoint_observation_digest != observation.provenance_digest:
        raise ClassifiedEventStreamAcquisitionContractError(
            "EVENT_STREAM_CHECKPOINT_OBSERVATION_DIGEST_MISMATCH"
        )
    if not _SHA256_HEX.match(checkpoint.provenance_digest):
        raise ClassifiedEventStreamAcquisitionContractError(
            "CHECKPOINT_PROVENANCE_DIGEST_NOT_SHA256"
        )
    if not _SHA256_HEX.match(observation.provenance_digest):
        raise ClassifiedEventStreamAcquisitionContractError(
            "CHECKPOINT_OBSERVATION_DIGEST_NOT_SHA256"
        )
    assert_checkpoint_cannot_mint_equity_v1(
        equity_mint_status=checkpoint.equity_mint_status,
        running_equity_value_state=checkpoint.running_equity_value_state,
        claimed_equity_stock_value=checkpoint.claimed_equity_stock_value,
        observation_vs_authority_class=checkpoint.observation_vs_authority_class,
    )
    if checkpoint.equity_mint_status != EQUITY_MINT_STATUS_NOT_MINTED:
        raise ClassifiedEventStreamAcquisitionContractError(
            "EVENT_STREAM_CHECKPOINT_CANNOT_MINT_EQUITY"
        )
    replay_ids: set[str] = set()
    ordering_keys: list[str] = []
    for event in events:
        _assert_identity_pair(
            expected_ref=observed_ref,
            expected_digest=observed_digest,
            observed_ref=event.bound_account_identity_ref,
            observed_digest=event.bound_account_identity_digest,
        )
        if event.equity_stock_mutation_status != EQUITY_MUTATION_NOT_MUTATED:
            raise ClassifiedEventStreamAcquisitionContractError(
                "EVENT_STREAM_CANNOT_MUTATE_EQUITY_STOCK"
            )
        if event.claimed_equity_stock_value != EQUITY_VALUE_STATE_ABSENT:
            raise ClassifiedEventStreamAcquisitionContractError(
                "EVENT_STREAM_CANNOT_MINT_OR_OVERWRITE_EQUITY"
            )
        if event.replay_identity in replay_ids:
            raise ClassifiedEventStreamAcquisitionContractError(
                "EVENT_STREAM_DUPLICATE_REPLAY_IDENTITY_FAIL_CLOSED"
            )
        replay_ids.add(event.replay_identity)
        ordering_keys.append(event.ordering_key)
    if len(ordering_keys) != len(set(ordering_keys)):
        raise ClassifiedEventStreamAcquisitionContractError(
            "EVENT_STREAM_DUPLICATE_ORDERING_KEY_FAIL_CLOSED"
        )
    if ordering_keys != sorted(ordering_keys):
        raise ClassifiedEventStreamAcquisitionContractError(
            "EVENT_STREAM_ORDERING_AMBIGUITY_FAIL_CLOSED"
        )
    if len(ordering_keys) >= 2:
        for left, right in zip(ordering_keys, ordering_keys[1:]):
            if right <= left:
                raise ClassifiedEventStreamAcquisitionContractError(
                    "EVENT_STREAM_RANGE_GAP_FAIL_CLOSED"
                )
    for event in events:
        if event.taxonomy_class in (
            CLASSIFICATION_STATUS_UNKNOWN,
            CLASSIFICATION_STATUS_UNCLASSIFIED,
        ):
            raise ClassifiedEventStreamAcquisitionContractError(
                f"EVENT_STREAM_{event.taxonomy_class}_FAIL_CLOSED:taxonomy_class"
            )
        if event.taxonomy_class != CLASSIFICATION_STATUS_CLASSIFIED:
            raise ClassifiedEventStreamAcquisitionContractError(
                "EVENT_STREAM_TAXONOMY_CLASS_NOT_CLASSIFIED"
            )
        if RATIFIED_CLASSIFIED_KIND_SET_RESOLVED is not True or (
            event.event_semantic_class not in RATIFIED_CLASSIFIED_KIND_SET
        ):
            raise ClassifiedEventStreamAcquisitionContractError("CLASSIFIED_KIND_NOT_RATIFIED")
    completeness, source, complete_proven, missing = (
        adjudicate_classified_event_stream_completeness_v1(
            events=events,
            claimed_completeness_status=completeness_status,
            source_status=source_status,
        )
    )
    event_replay = ",".join(event.replay_identity for event in events)
    stream_replay_payload = {
        "stream_id": stream,
        "bound_account_identity_ref": observed_ref,
        "bound_account_identity_digest": observed_digest,
        "checkpoint_id": checkpoint.checkpoint_id,
        "checkpoint_observation_ref": observation.observation_id,
        "checkpoint_observation_digest": observation.provenance_digest,
        "event_replay_identities": event_replay,
    }
    stream_replay = compute_classified_event_stream_digest_v1(stream_replay_payload)
    payload = {
        "stream_id": stream,
        "stream_replay_identity": stream_replay,
        "checkpoint_id": checkpoint.checkpoint_id,
        "checkpoint_provenance_digest": checkpoint.provenance_digest,
        "checkpoint_observation_ref": observation.observation_id,
        "checkpoint_observation_digest": observation.provenance_digest,
        "bound_account_identity_ref": observed_ref,
        "bound_account_identity_digest": observed_digest,
        "coverage_boundary_class": COVERAGE_BOUNDARY_CLASS,
        "completeness_status": completeness,
        "source_status": source,
        "event_count": str(len(events)),
        "ordering_proven": FALSE_TOKEN,
        "gap_detected": UNKNOWN_TOKEN,
        "complete_event_stream_proven": complete_proven,
        "missing_completeness_dependency": missing,
        "reconstructed_equity_created": FALSE_TOKEN,
        "reconstruction_engine_created": FALSE_TOKEN,
        "eq_reconciliation_executed": FALSE_TOKEN,
        "raw_eq_source_authority": FALSE_TOKEN,
        "source_selected": FALSE_TOKEN,
        "mapping_proven": FALSE_TOKEN,
        "c17_created": FALSE_TOKEN,
        "network_method": method,
        "authority_effect": AUTHORITY_EFFECT,
    }
    digest = compute_classified_event_stream_digest_v1(payload)
    return ClassifiedEventStreamBindingV1(
        **payload,
        provenance_digest=digest,
    )
