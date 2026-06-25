"""GLB-019 and Master-V2 state event stream validators for durable completion proof binding."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from src.ops.durable_completion_validation.identity import sorted_unique, valid_sha256_digest
from src.ops.durable_completion_validation.models import ValidationContext, ValidationResult

BOUNDARY_OWNER = "glb019_event_stream_static_boundary_v0"
CONTRACT_VERSION = "v0"
HASH_ALGORITHM = "sha256"

REQUIRED_EVENT_CLASSES: tuple[str, ...] = (
    "state_transition",
    "gate_blocker_decision",
    "risk_killswitch_abort_closeout",
    "evidence_manifest_validation",
    "promotion_readiness_visibility",
)


@dataclass(frozen=True)
class EventStreamRecord:
    event_class: str
    event_id: str
    sequence: int
    timestamp_utc: str
    source: str
    correlation_id: str
    schema_version: str
    present: bool


@dataclass(frozen=True)
class Glb019EventStreamValidationInput:
    boundary_owner: str
    source_revision: str
    completion_identity_digest: str
    manifest_identity_digest: str
    run_identity_digest: str
    correlation_id: str
    events: tuple[EventStreamRecord, ...]


@dataclass(frozen=True)
class Glb019EventStreamProofBinding:
    boundary_owner: str
    source_revision: str
    validation_input_digest: str
    validation_result_digest: str
    glb019_validation_pass: bool
    event_stream_boundary_satisfied: bool
    durable_completion_event_stream_bound: bool
    incomplete_event_stream_fail_closed: bool
    event_stream_non_authorizing: bool
    completion_identity_digest: str
    manifest_identity_digest: str
    run_identity_digest: str
    correlation_id: str
    event_stream_identity: str


def _record_dict(record: EventStreamRecord) -> dict[str, Any]:
    return asdict(record)


def _validation_input_dict(validation_input: Glb019EventStreamValidationInput) -> dict[str, Any]:
    return {
        "boundary_owner": validation_input.boundary_owner,
        "completion_identity_digest": validation_input.completion_identity_digest,
        "contract_version": CONTRACT_VERSION,
        "correlation_id": validation_input.correlation_id,
        "events": [_record_dict(record) for record in validation_input.events],
        "hash_algorithm": HASH_ALGORITHM,
        "manifest_identity_digest": validation_input.manifest_identity_digest,
        "run_identity_digest": validation_input.run_identity_digest,
        "source_revision": validation_input.source_revision,
    }


def compute_validation_input_digest(validation_input: Glb019EventStreamValidationInput) -> str:
    return hashlib.sha256(
        json.dumps(
            _validation_input_dict(validation_input), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def compute_event_stream_identity(
    validation_input: Glb019EventStreamValidationInput,
    *,
    validation_pass: bool,
) -> str:
    payload = {
        "correlation_id": validation_input.correlation_id,
        "hash_algorithm": HASH_ALGORITHM,
        "required_event_classes": list(REQUIRED_EVENT_CLASSES),
        "validation_input_digest": compute_validation_input_digest(validation_input),
        "validation_pass": validation_pass,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def compute_validation_result_digest(
    validation_input: Glb019EventStreamValidationInput,
    *,
    validation_pass: bool,
    fail_reasons: tuple[str, ...],
) -> str:
    payload = {
        "boundary_owner": BOUNDARY_OWNER,
        "event_stream_identity": compute_event_stream_identity(
            validation_input,
            validation_pass=validation_pass,
        ),
        "fail_reasons": list(fail_reasons),
        "hash_algorithm": HASH_ALGORITHM,
        "validation_input_digest": compute_validation_input_digest(validation_input),
        "validation_pass": validation_pass,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def validate_glb019_event_stream_validation_input(
    validation_input: Glb019EventStreamValidationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    prefix = "glb019_event_stream_input"

    if validation_input.boundary_owner != BOUNDARY_OWNER:
        fail_reasons.append(f"{prefix}: boundary_owner must be {BOUNDARY_OWNER!r}")
    if not validation_input.source_revision:
        fail_reasons.append(f"{prefix}: source_revision required")

    for field_name in (
        "completion_identity_digest",
        "manifest_identity_digest",
        "run_identity_digest",
    ):
        value = getattr(validation_input, field_name)
        if not value:
            fail_reasons.append(f"{prefix}: {field_name} required")
        elif not valid_sha256_digest(value):
            fail_reasons.append(f"{prefix}: {field_name} must be 64-char lowercase sha256 hex")

    if not validation_input.correlation_id:
        fail_reasons.append(f"{prefix}: correlation_id required")

    if not validation_input.events:
        fail_reasons.append(f"{prefix}: events required")

    seen_ids: set[str] = set()
    seen_sequences: set[int] = set()
    for index, record in enumerate(validation_input.events):
        rec_prefix = f"{prefix}: events[{index}]"
        if not record.event_class:
            fail_reasons.append(f"{rec_prefix}: event_class required")
        if not record.event_id:
            fail_reasons.append(f"{rec_prefix}: event_id required")
        elif record.event_id in seen_ids:
            fail_reasons.append(f"{rec_prefix}: duplicate event_id")
        else:
            seen_ids.add(record.event_id)

        if record.sequence in seen_sequences:
            fail_reasons.append(f"{rec_prefix}: duplicate sequence")
        else:
            seen_sequences.add(record.sequence)

        if not record.timestamp_utc:
            fail_reasons.append(f"{rec_prefix}: timestamp_utc required")
        if not record.source:
            fail_reasons.append(f"{rec_prefix}: source required")
        if not record.schema_version:
            fail_reasons.append(f"{rec_prefix}: schema_version required")
        if record.correlation_id != validation_input.correlation_id:
            fail_reasons.append(f"{rec_prefix}: correlation_id mismatch with validation input")

    return sorted_unique(fail_reasons)


def evaluate_glb019_event_stream_validation(
    validation_input: Glb019EventStreamValidationInput,
) -> dict[str, Any]:
    """Canonical offline GLB-019 event stream validation — explicit input only."""
    fail_reasons = validate_glb019_event_stream_validation_input(validation_input)

    present_by_class: dict[str, list[EventStreamRecord]] = {}
    for record in validation_input.events:
        present_by_class.setdefault(record.event_class, []).append(record)

    for event_class in REQUIRED_EVENT_CLASSES:
        records = present_by_class.get(event_class, [])
        if not records:
            fail_reasons.append(
                f"glb019_event_stream: missing mandatory event class {event_class!r}"
            )
            continue
        if not any(record.present for record in records):
            fail_reasons.append(
                f"glb019_event_stream: mandatory event class {event_class!r} not present"
            )

    for event_class, records in present_by_class.items():
        if event_class not in REQUIRED_EVENT_CLASSES:
            fail_reasons.append(
                f"glb019_event_stream: unknown event class {event_class!r} not in GLB-019 SSOT"
            )
        for record in records:
            if record.present and not all(
                (
                    record.event_id,
                    record.timestamp_utc,
                    record.source,
                    record.correlation_id,
                    record.schema_version,
                )
            ):
                fail_reasons.append(
                    f"glb019_event_stream: incomplete identity fields for {event_class!r}"
                )

    sequences = sorted(record.sequence for record in validation_input.events)
    if sequences != list(range(len(sequences))):
        fail_reasons.append(
            "glb019_event_stream: contradictory or non-contiguous sequence ordering"
        )

    fail_reasons = sorted_unique(fail_reasons)
    validation_pass = not fail_reasons
    event_stream_identity = compute_event_stream_identity(
        validation_input,
        validation_pass=validation_pass,
    )
    validation_result_digest = compute_validation_result_digest(
        validation_input,
        validation_pass=validation_pass,
        fail_reasons=tuple(fail_reasons),
    )

    return {
        "boundary_owner": BOUNDARY_OWNER,
        "validation_pass": validation_pass,
        "event_stream_boundary_satisfied": validation_pass,
        "incomplete_event_stream_fail_closed": not validation_pass,
        "event_stream_non_authorizing": True,
        "validation_input_digest": compute_validation_input_digest(validation_input),
        "validation_result_digest": validation_result_digest,
        "event_stream_identity": event_stream_identity,
        "fail_reasons": fail_reasons,
    }


def validate_glb019_event_stream_proof(context: ValidationContext) -> ValidationResult:
    """Bind canonical GLB-019 validation result into durable completion proof graph."""
    if context.glb019_result is None:
        return ValidationResult(
            fail_reasons=(
                "glb019_event_stream_validation: glb019_result required in validation context",
            )
        )
    fail_reasons: list[str] = []
    integration_input = context.integration_input
    glb019_result = context.glb019_result
    proof = integration_input.glb019_event_stream_proof
    validation_input = integration_input.glb019_event_stream_validation_input
    prefix = "glb019_proof"

    if proof.boundary_owner != BOUNDARY_OWNER:
        fail_reasons.append(f"{prefix}: boundary_owner must be {BOUNDARY_OWNER!r}")
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append(f"{prefix}: source_revision mismatch")

    if not proof.validation_input_digest:
        fail_reasons.append(f"{prefix}: validation_input_digest required")
    elif not valid_sha256_digest(proof.validation_input_digest):
        fail_reasons.append(
            f"{prefix}: validation_input_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.validation_input_digest != compute_validation_input_digest(validation_input):
        fail_reasons.append(f"{prefix}: validation_input_digest mismatch")

    if not proof.validation_result_digest:
        fail_reasons.append(f"{prefix}: validation_result_digest required")
    elif not valid_sha256_digest(proof.validation_result_digest):
        fail_reasons.append(
            f"{prefix}: validation_result_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.validation_result_digest != glb019_result.get("validation_result_digest"):
        fail_reasons.append(
            f"{prefix}: validation_result_digest mismatch with canonical evaluation"
        )

    identity_fields = (
        ("completion_identity_digest", proof.completion_identity_digest),
        ("manifest_identity_digest", proof.manifest_identity_digest),
        ("run_identity_digest", proof.run_identity_digest),
        ("correlation_id", proof.correlation_id),
        ("event_stream_identity", proof.event_stream_identity),
    )
    for field_name, value in identity_fields:
        if not value:
            fail_reasons.append(f"{prefix}: {field_name} required")
        elif field_name != "correlation_id" and not valid_sha256_digest(value):
            fail_reasons.append(f"{prefix}: {field_name} must be 64-char lowercase sha256 hex")

    if proof.completion_identity_digest != validation_input.completion_identity_digest:
        fail_reasons.append(f"{prefix}: completion_identity_digest drift")
    if proof.manifest_identity_digest != validation_input.manifest_identity_digest:
        fail_reasons.append(f"{prefix}: manifest_identity_digest drift")
    if proof.run_identity_digest != validation_input.run_identity_digest:
        fail_reasons.append(f"{prefix}: run_identity_digest drift")
    if proof.correlation_id != validation_input.correlation_id:
        fail_reasons.append(f"{prefix}: correlation_id drift")

    required_flags = (
        ("glb019_validation_pass", True),
        ("event_stream_boundary_satisfied", True),
        ("durable_completion_event_stream_bound", True),
        ("incomplete_event_stream_fail_closed", False),
        ("event_stream_non_authorizing", True),
    )
    for field_name, expected in required_flags:
        if getattr(proof, field_name) is not expected:
            fail_reasons.append(f"{prefix}: {field_name} must be {expected}")

    if not glb019_result.get("validation_pass"):
        fail_reasons.append("glb019_event_stream_validation: canonical evaluation failed")
        fail_reasons.extend(
            f"glb019_event_stream_validation: {reason}"
            for reason in glb019_result.get("fail_reasons", [])
        )
    elif proof.event_stream_identity != glb019_result.get("event_stream_identity"):
        fail_reasons.append(f"{prefix}: event_stream_identity mismatch with canonical evaluation")

    if proof.validation_result_digest and glb019_result.get("validation_result_digest"):
        if proof.validation_result_digest != glb019_result["validation_result_digest"]:
            fail_reasons.append(f"{prefix}: stale or superseded validation_result_digest")

    return ValidationResult(fail_reasons=tuple(sorted_unique(fail_reasons)))


def default_minimal_event_stream_records(*, correlation_id: str) -> tuple[EventStreamRecord, ...]:
    return tuple(
        EventStreamRecord(
            event_class=event_class,
            event_id=f"{event_class}-001",
            sequence=index,
            timestamp_utc="2026-06-23T00:00:00Z",
            source="bounded_futures_testnet_durable_completion_offline_v0",
            correlation_id=correlation_id,
            schema_version=CONTRACT_VERSION,
            present=True,
        )
        for index, event_class in enumerate(REQUIRED_EVENT_CLASSES)
    )


def default_minimal_glb019_validation_input(
    *,
    source_revision: str,
    completion_identity_digest: str,
    manifest_identity_digest: str,
    run_identity_digest: str,
    correlation_id: str,
) -> Glb019EventStreamValidationInput:
    return Glb019EventStreamValidationInput(
        boundary_owner=BOUNDARY_OWNER,
        source_revision=source_revision,
        completion_identity_digest=completion_identity_digest,
        manifest_identity_digest=manifest_identity_digest,
        run_identity_digest=run_identity_digest,
        correlation_id=correlation_id,
        events=default_minimal_event_stream_records(correlation_id=correlation_id),
    )


def default_minimal_glb019_proof_binding(
    validation_input: Glb019EventStreamValidationInput,
    glb019_result: dict[str, Any],
) -> Glb019EventStreamProofBinding:
    if not glb019_result.get("validation_pass"):
        raise ValueError("GLB-019 validation must pass for default minimal proof")
    return Glb019EventStreamProofBinding(
        boundary_owner=BOUNDARY_OWNER,
        source_revision=validation_input.source_revision,
        validation_input_digest=glb019_result["validation_input_digest"],
        validation_result_digest=glb019_result["validation_result_digest"],
        glb019_validation_pass=True,
        event_stream_boundary_satisfied=True,
        durable_completion_event_stream_bound=True,
        incomplete_event_stream_fail_closed=False,
        event_stream_non_authorizing=True,
        completion_identity_digest=validation_input.completion_identity_digest,
        manifest_identity_digest=validation_input.manifest_identity_digest,
        run_identity_digest=validation_input.run_identity_digest,
        correlation_id=validation_input.correlation_id,
        event_stream_identity=glb019_result["event_stream_identity"],
    )


MASTER_V2_STATE_EVENT_BOUNDARY_OWNER = (
    "master_v2_kill_all_state_switch_event_stream_static_boundary_v0"
)
MASTER_V2_STATE_EVENT_CONTRACT_VERSION = "v0"

MASTER_V2_SEMANTIC_EVENT_CLASSES: tuple[str, ...] = (
    "dynamic_scope",
    "state_switch",
    "chop_guard",
    "kill_all_terminal",
)

MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH = "state_switch_coherent_v0"
MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL = "kill_all_terminal_v0"

_SUPPORTED_EVIDENCE_CHAIN_PROFILES: frozenset[str] = frozenset(
    {
        MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH,
        MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL,
    }
)

_OFFLINE_SOURCE = "bounded_futures_testnet_durable_completion_offline_v0"
_DEFAULT_TIMESTAMP_UTC = "2026-06-25T12:00:00Z"


@dataclass(frozen=True)
class MasterV2StateEventRecord:
    semantic_event_class: str
    event_id: str
    sequence: int
    timestamp_utc: str
    source: str
    correlation_id: str
    schema_version: str
    scope_event: str
    side_state_before: str
    side_state_after: str
    scope_state_digest: str
    transition_allowed: bool
    present: bool
    claims_live_authority: bool = False
    claims_execution_authority: bool = False


@dataclass(frozen=True)
class MasterV2StateEventStreamValidationInput:
    boundary_owner: str
    source_revision: str
    completion_identity_digest: str
    manifest_identity_digest: str
    run_identity_digest: str
    correlation_id: str
    evidence_chain_profile: str
    bound_dynamic_scope_state_digest: str | None
    events: tuple[MasterV2StateEventRecord, ...]


@dataclass(frozen=True)
class MasterV2StateEventStreamProofBinding:
    boundary_owner: str
    source_revision: str
    validation_input_digest: str
    validation_result_digest: str
    master_v2_state_event_validation_pass: bool
    event_stream_boundary_satisfied: bool
    durable_completion_master_v2_state_event_bound: bool
    incomplete_event_stream_fail_closed: bool
    event_stream_non_authorizing: bool
    completion_identity_digest: str
    manifest_identity_digest: str
    run_identity_digest: str
    correlation_id: str
    state_event_stream_identity: str
    evidence_chain_profile: str


def _master_v2_state_event_record_dict(record: MasterV2StateEventRecord) -> dict[str, Any]:
    return asdict(record)


def _master_v2_validation_input_dict(
    validation_input: MasterV2StateEventStreamValidationInput,
) -> dict[str, Any]:
    return {
        "boundary_owner": validation_input.boundary_owner,
        "bound_dynamic_scope_state_digest": validation_input.bound_dynamic_scope_state_digest,
        "completion_identity_digest": validation_input.completion_identity_digest,
        "contract_version": MASTER_V2_STATE_EVENT_CONTRACT_VERSION,
        "correlation_id": validation_input.correlation_id,
        "evidence_chain_profile": validation_input.evidence_chain_profile,
        "events": [
            _master_v2_state_event_record_dict(record) for record in validation_input.events
        ],
        "hash_algorithm": HASH_ALGORITHM,
        "manifest_identity_digest": validation_input.manifest_identity_digest,
        "run_identity_digest": validation_input.run_identity_digest,
        "source_revision": validation_input.source_revision,
    }


def compute_master_v2_scope_state_evidence_digest(*, scope_state: dict[str, Any]) -> str:
    payload = {
        "component": "dynamic_scope",
        "hash_algorithm": HASH_ALGORITHM,
        "state": dict(scope_state),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def compute_master_v2_state_event_validation_input_digest(
    validation_input: MasterV2StateEventStreamValidationInput,
) -> str:
    return hashlib.sha256(
        json.dumps(
            _master_v2_validation_input_dict(validation_input),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def compute_master_v2_state_event_stream_identity(
    validation_input: MasterV2StateEventStreamValidationInput,
    *,
    validation_pass: bool,
) -> str:
    payload = {
        "correlation_id": validation_input.correlation_id,
        "evidence_chain_profile": validation_input.evidence_chain_profile,
        "hash_algorithm": HASH_ALGORITHM,
        "required_semantic_event_classes": list(MASTER_V2_SEMANTIC_EVENT_CLASSES),
        "validation_input_digest": compute_master_v2_state_event_validation_input_digest(
            validation_input
        ),
        "validation_pass": validation_pass,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def compute_master_v2_state_event_validation_result_digest(
    validation_input: MasterV2StateEventStreamValidationInput,
    *,
    validation_pass: bool,
    fail_reasons: tuple[str, ...],
) -> str:
    payload = {
        "boundary_owner": MASTER_V2_STATE_EVENT_BOUNDARY_OWNER,
        "fail_reasons": list(fail_reasons),
        "hash_algorithm": HASH_ALGORITHM,
        "state_event_stream_identity": compute_master_v2_state_event_stream_identity(
            validation_input,
            validation_pass=validation_pass,
        ),
        "validation_input_digest": compute_master_v2_state_event_validation_input_digest(
            validation_input
        ),
        "validation_pass": validation_pass,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _default_offline_scope_state() -> dict[str, Any]:
    return {
        "anchor_price": 100.0,
        "chop_latched": False,
        "current_downscope_boundary": 95.0,
        "current_hysteresis_band": 2.0,
        "current_upscope_boundary": 105.0,
        "last_completed_side_switch_tick": -1_000_000,
        "last_switch_tick": -1_000_000,
        "now_tick": 0,
        "scope_stability_ticks": 0,
        "switches_in_window": 0,
        "window_start_tick": 0,
    }


def build_master_v2_state_event_record(
    *,
    semantic_event_class: str,
    event_id: str,
    sequence: int,
    correlation_id: str,
    scope_event: str,
    side_state_before: str,
    side_state_after: str,
    scope_state_digest: str,
    transition_allowed: bool,
    present: bool = True,
    timestamp_utc: str | None = None,
) -> MasterV2StateEventRecord:
    """Canonical builder for offline Master-V2 state event records (non-authorizing)."""
    return MasterV2StateEventRecord(
        semantic_event_class=semantic_event_class,
        event_id=event_id,
        sequence=sequence,
        timestamp_utc=timestamp_utc or _DEFAULT_TIMESTAMP_UTC,
        source=_OFFLINE_SOURCE,
        correlation_id=correlation_id,
        schema_version=MASTER_V2_STATE_EVENT_CONTRACT_VERSION,
        scope_event=scope_event,
        side_state_before=side_state_before,
        side_state_after=side_state_after,
        scope_state_digest=scope_state_digest,
        transition_allowed=transition_allowed,
        present=present,
        claims_live_authority=False,
        claims_execution_authority=False,
    )


def _master_v2_state_event_record(
    *,
    semantic_event_class: str,
    event_id: str,
    sequence: int,
    correlation_id: str,
    scope_event: str,
    side_state_before: str,
    side_state_after: str,
    scope_state_digest: str,
    transition_allowed: bool,
    present: bool = True,
) -> MasterV2StateEventRecord:
    return build_master_v2_state_event_record(
        semantic_event_class=semantic_event_class,
        event_id=event_id,
        sequence=sequence,
        correlation_id=correlation_id,
        scope_event=scope_event,
        side_state_before=side_state_before,
        side_state_after=side_state_after,
        scope_state_digest=scope_state_digest,
        transition_allowed=transition_allowed,
        present=present,
    )


def default_minimal_master_v2_state_switch_event_records(
    *,
    correlation_id: str,
    scope_state_digest: str,
) -> tuple[MasterV2StateEventRecord, ...]:
    from src.trading.master_v2.double_play_state import ScopeEvent, SideState

    return (
        _master_v2_state_event_record(
            semantic_event_class="dynamic_scope",
            event_id="mv2-dynamic-scope-001",
            sequence=0,
            correlation_id=correlation_id,
            scope_event=ScopeEvent.UPSCOPE_CANDIDATE.value,
            side_state_before=SideState.LONG_ACTIVE.value,
            side_state_after=SideState.LONG_ACTIVE.value,
            scope_state_digest=scope_state_digest,
            transition_allowed=True,
        ),
        _master_v2_state_event_record(
            semantic_event_class="state_switch",
            event_id="mv2-state-switch-001",
            sequence=1,
            correlation_id=correlation_id,
            scope_event=ScopeEvent.DOWNSCOPE_CONFIRMED.value,
            side_state_before=SideState.LONG_ACTIVE.value,
            side_state_after=SideState.SWITCH_LONG_TO_SHORT_PENDING.value,
            scope_state_digest=scope_state_digest,
            transition_allowed=True,
        ),
        _master_v2_state_event_record(
            semantic_event_class="chop_guard",
            event_id="mv2-chop-guard-001",
            sequence=2,
            correlation_id=correlation_id,
            scope_event=ScopeEvent.CHOP_DETECTED.value,
            side_state_before=SideState.LONG_ACTIVE.value,
            side_state_after=SideState.LONG_ACTIVE.value,
            scope_state_digest=scope_state_digest,
            transition_allowed=False,
        ),
    )


def default_minimal_master_v2_kill_all_event_records(
    *,
    correlation_id: str,
    scope_state_digest: str,
) -> tuple[MasterV2StateEventRecord, ...]:
    from src.trading.master_v2.double_play_state import ScopeEvent, SideState

    return (
        _master_v2_state_event_record(
            semantic_event_class="kill_all_terminal",
            event_id="mv2-kill-all-001",
            sequence=0,
            correlation_id=correlation_id,
            scope_event=ScopeEvent.KILL_ALL_REQUIRED.value,
            side_state_before=SideState.LONG_ACTIVE.value,
            side_state_after=SideState.KILL_ALL.value,
            scope_state_digest=scope_state_digest,
            transition_allowed=True,
        ),
    )


def validate_master_v2_state_event_stream_validation_input(
    validation_input: MasterV2StateEventStreamValidationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    prefix = "master_v2_state_event_stream_input"

    if validation_input.boundary_owner != MASTER_V2_STATE_EVENT_BOUNDARY_OWNER:
        fail_reasons.append(
            f"{prefix}: boundary_owner must be {MASTER_V2_STATE_EVENT_BOUNDARY_OWNER!r}"
        )
    if not validation_input.source_revision:
        fail_reasons.append(f"{prefix}: source_revision required")
    if validation_input.evidence_chain_profile not in _SUPPORTED_EVIDENCE_CHAIN_PROFILES:
        fail_reasons.append(f"{prefix}: unsupported evidence_chain_profile")

    for field_name in (
        "completion_identity_digest",
        "manifest_identity_digest",
        "run_identity_digest",
    ):
        value = getattr(validation_input, field_name)
        if not value:
            fail_reasons.append(f"{prefix}: {field_name} required")
        elif not valid_sha256_digest(value):
            fail_reasons.append(f"{prefix}: {field_name} must be 64-char lowercase sha256 hex")

    if validation_input.bound_dynamic_scope_state_digest is not None and not valid_sha256_digest(
        validation_input.bound_dynamic_scope_state_digest
    ):
        fail_reasons.append(
            f"{prefix}: bound_dynamic_scope_state_digest must be 64-char lowercase sha256 hex"
        )

    if not validation_input.correlation_id:
        fail_reasons.append(f"{prefix}: correlation_id required")
    if not validation_input.events:
        fail_reasons.append(f"{prefix}: events required")

    seen_ids: set[str] = set()
    seen_sequences: set[int] = set()
    for index, record in enumerate(validation_input.events):
        rec_prefix = f"{prefix}: events[{index}]"
        if record.semantic_event_class not in MASTER_V2_SEMANTIC_EVENT_CLASSES:
            fail_reasons.append(f"{rec_prefix}: unknown semantic_event_class")
        if not record.event_id:
            fail_reasons.append(f"{rec_prefix}: event_id required")
        elif record.event_id in seen_ids:
            fail_reasons.append(f"{rec_prefix}: duplicate event_id")
        else:
            seen_ids.add(record.event_id)
        if record.sequence in seen_sequences:
            fail_reasons.append(f"{rec_prefix}: duplicate sequence")
        else:
            seen_sequences.add(record.sequence)
        if not record.timestamp_utc:
            fail_reasons.append(f"{rec_prefix}: timestamp_utc required")
        if not record.source:
            fail_reasons.append(f"{rec_prefix}: source required")
        if not record.schema_version:
            fail_reasons.append(f"{rec_prefix}: schema_version required")
        if record.correlation_id != validation_input.correlation_id:
            fail_reasons.append(f"{rec_prefix}: correlation_id mismatch with validation input")
        if record.present and not valid_sha256_digest(record.scope_state_digest):
            fail_reasons.append(
                f"{rec_prefix}: scope_state_digest must be 64-char lowercase sha256 hex"
            )
        if record.claims_live_authority or record.claims_execution_authority:
            fail_reasons.append(f"{rec_prefix}: authority claims forbidden in evidence-only stream")

    return sorted_unique(fail_reasons)


def _validate_master_v2_transition_semantics(
    validation_input: MasterV2StateEventStreamValidationInput,
) -> list[str]:
    from src.trading.master_v2.double_play_state import (
        DynamicScopeRules,
        RuntimeEnvelope,
        RuntimeScopeState,
        ScopeEvent,
        SideState,
        StaticHardLimits,
        transition_state,
    )

    fail_reasons: list[str] = []
    prefix = "master_v2_state_event_stream"
    envelope = RuntimeEnvelope(static=StaticHardLimits(), live_authorization=False)
    rules = DynamicScopeRules(
        downscope_band_multiplier=1.0,
        upscope_band_multiplier=1.0,
        min_band_width=0.5,
        max_band_width=100.0,
        min_switch_cooldown_ticks=0,
        max_switches_per_window=10,
    )
    scope_state = RuntimeScopeState(**_default_offline_scope_state())
    transition_keys: set[tuple[str, str, int]] = set()
    kill_all_terminal_seen = False

    present_records = sorted(
        (record for record in validation_input.events if record.present),
        key=lambda record: record.sequence,
    )

    for index, record in enumerate(present_records):
        rec_prefix = f"{prefix}: events[{index}]"
        try:
            side_before = SideState(record.side_state_before)
            scope_event = ScopeEvent(record.scope_event)
        except ValueError:
            fail_reasons.append(f"{rec_prefix}: invalid canonical scope_event or side_state_before")
            continue

        transition_key = (record.scope_event, record.side_state_before)
        if transition_key in transition_keys:
            fail_reasons.append(f"{rec_prefix}: duplicate transition event")
        else:
            transition_keys.add(transition_key)

        if kill_all_terminal_seen:
            fail_reasons.append(f"{rec_prefix}: transition after kill_all_terminal forbidden")
            continue

        if (
            validation_input.bound_dynamic_scope_state_digest is not None
            and record.scope_state_digest != validation_input.bound_dynamic_scope_state_digest
        ):
            fail_reasons.append(f"{rec_prefix}: scope_state_digest drift from bound dynamic scope")

        side_after, _, decision = transition_state(
            side_state=side_before,
            event=scope_event,
            scope_state=scope_state,
            rules=rules,
            envelope=envelope,
            now_tick=record.sequence + 1,
        )
        expected_after = side_after.value
        if record.side_state_after != expected_after:
            fail_reasons.append(
                f"{rec_prefix}: side_state_after mismatch with canonical transition semantics"
            )
        if record.transition_allowed != decision.allowed:
            fail_reasons.append(
                f"{rec_prefix}: transition_allowed mismatch with canonical semantics"
            )

        if (
            record.semantic_event_class == "chop_guard"
            and expected_after == SideState.KILL_ALL.value
        ):
            fail_reasons.append(f"{rec_prefix}: chop_guard must not escalate to kill_all")

        if record.semantic_event_class == "kill_all_terminal":
            if scope_event != ScopeEvent.KILL_ALL_REQUIRED:
                fail_reasons.append(f"{rec_prefix}: kill_all_terminal requires KILL_ALL_REQUIRED")
            if expected_after != SideState.KILL_ALL.value:
                fail_reasons.append(
                    f"{rec_prefix}: kill_all_terminal must end in kill_all side state"
                )
            kill_all_terminal_seen = True

    return fail_reasons


def _validate_master_v2_profile_requirements(
    validation_input: MasterV2StateEventStreamValidationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    prefix = "master_v2_state_event_stream"
    present_by_class: dict[str, list[MasterV2StateEventRecord]] = {}
    for record in validation_input.events:
        if record.present:
            present_by_class.setdefault(record.semantic_event_class, []).append(record)

    profile = validation_input.evidence_chain_profile
    if profile == MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH:
        for event_class in ("dynamic_scope", "state_switch"):
            if event_class not in present_by_class:
                fail_reasons.append(f"{prefix}: missing required event class {event_class!r}")
        if "kill_all_terminal" in present_by_class:
            fail_reasons.append(f"{prefix}: kill_all_terminal forbidden in state_switch profile")
        if "chop_guard" in present_by_class:
            for record in present_by_class["chop_guard"]:
                if record.side_state_after == "kill_all":
                    fail_reasons.append(f"{prefix}: chop_guard escalated to kill_all")
    elif profile == MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL:
        if "kill_all_terminal" not in present_by_class:
            fail_reasons.append(f"{prefix}: missing required event class 'kill_all_terminal'")
        if "state_switch" in present_by_class:
            fail_reasons.append(f"{prefix}: state_switch forbidden after kill_all profile binding")

    sequences = sorted(record.sequence for record in validation_input.events if record.present)
    if sequences and sequences != list(range(sequences[0], sequences[0] + len(sequences))):
        fail_reasons.append(f"{prefix}: contradictory or non-contiguous sequence ordering")

    return fail_reasons


def evaluate_master_v2_state_event_stream_validation(
    validation_input: MasterV2StateEventStreamValidationInput,
) -> dict[str, Any]:
    """Canonical offline Master-V2 Kill-All/State-Switch event stream validation."""
    fail_reasons = validate_master_v2_state_event_stream_validation_input(validation_input)
    if not fail_reasons:
        fail_reasons.extend(_validate_master_v2_profile_requirements(validation_input))
    if not fail_reasons:
        fail_reasons.extend(_validate_master_v2_transition_semantics(validation_input))

    fail_reasons = sorted_unique(fail_reasons)
    validation_pass = not fail_reasons
    state_event_stream_identity = compute_master_v2_state_event_stream_identity(
        validation_input,
        validation_pass=validation_pass,
    )
    validation_result_digest = compute_master_v2_state_event_validation_result_digest(
        validation_input,
        validation_pass=validation_pass,
        fail_reasons=tuple(fail_reasons),
    )
    return {
        "boundary_owner": MASTER_V2_STATE_EVENT_BOUNDARY_OWNER,
        "validation_pass": validation_pass,
        "event_stream_boundary_satisfied": validation_pass,
        "incomplete_event_stream_fail_closed": not validation_pass,
        "event_stream_non_authorizing": True,
        "validation_input_digest": compute_master_v2_state_event_validation_input_digest(
            validation_input
        ),
        "validation_result_digest": validation_result_digest,
        "state_event_stream_identity": state_event_stream_identity,
        "evidence_chain_profile": validation_input.evidence_chain_profile,
        "fail_reasons": fail_reasons,
    }


def default_minimal_master_v2_state_event_validation_input(
    *,
    source_revision: str,
    completion_identity_digest: str,
    manifest_identity_digest: str,
    run_identity_digest: str,
    correlation_id: str,
    evidence_chain_profile: str = MASTER_V2_EVIDENCE_CHAIN_PROFILE_STATE_SWITCH,
    bound_dynamic_scope_state_digest: str | None = None,
) -> MasterV2StateEventStreamValidationInput:
    scope_state_digest = (
        bound_dynamic_scope_state_digest
        or compute_master_v2_scope_state_evidence_digest(scope_state=_default_offline_scope_state())
    )
    if evidence_chain_profile == MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL:
        events = default_minimal_master_v2_kill_all_event_records(
            correlation_id=correlation_id,
            scope_state_digest=scope_state_digest,
        )
    else:
        events = default_minimal_master_v2_state_switch_event_records(
            correlation_id=correlation_id,
            scope_state_digest=scope_state_digest,
        )
    return MasterV2StateEventStreamValidationInput(
        boundary_owner=MASTER_V2_STATE_EVENT_BOUNDARY_OWNER,
        source_revision=source_revision,
        completion_identity_digest=completion_identity_digest,
        manifest_identity_digest=manifest_identity_digest,
        run_identity_digest=run_identity_digest,
        correlation_id=correlation_id,
        evidence_chain_profile=evidence_chain_profile,
        bound_dynamic_scope_state_digest=bound_dynamic_scope_state_digest,
        events=events,
    )


def default_minimal_master_v2_state_event_proof_binding(
    validation_input: MasterV2StateEventStreamValidationInput,
    master_v2_result: dict[str, Any],
) -> MasterV2StateEventStreamProofBinding:
    if not master_v2_result.get("validation_pass"):
        raise ValueError("Master-V2 state event validation must pass for default minimal proof")
    return MasterV2StateEventStreamProofBinding(
        boundary_owner=MASTER_V2_STATE_EVENT_BOUNDARY_OWNER,
        source_revision=validation_input.source_revision,
        validation_input_digest=master_v2_result["validation_input_digest"],
        validation_result_digest=master_v2_result["validation_result_digest"],
        master_v2_state_event_validation_pass=True,
        event_stream_boundary_satisfied=True,
        durable_completion_master_v2_state_event_bound=True,
        incomplete_event_stream_fail_closed=False,
        event_stream_non_authorizing=True,
        completion_identity_digest=validation_input.completion_identity_digest,
        manifest_identity_digest=validation_input.manifest_identity_digest,
        run_identity_digest=validation_input.run_identity_digest,
        correlation_id=validation_input.correlation_id,
        state_event_stream_identity=master_v2_result["state_event_stream_identity"],
        evidence_chain_profile=validation_input.evidence_chain_profile,
    )
