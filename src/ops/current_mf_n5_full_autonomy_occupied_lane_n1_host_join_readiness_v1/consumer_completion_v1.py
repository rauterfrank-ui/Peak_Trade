"""Durable evidence of the original N1 consumer's completed, pre-external output.

This receipt acknowledges historical consumption only. It cannot authorize a
new cycle, restore an account admission, or replace a cursor or execution ledger.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile


SCHEMA = "occupied_lane_n1_consumer_completion.v1"
PRODUCER = "compose_occupied_lane_n1_host_join_readiness_v1"
DIRECTORY = "n1_consumer_completions_v1"
SUCCESS_DISPOSITIONS = frozenset({"PRE_EXTERNAL_EFFECT", "HOLD_CLOSED", "COMPLETED"})


class N1ConsumerCompletionError(ValueError):
    pass


class N1ConsumerCompletionPublicationError(N1ConsumerCompletionError):
    pass


def _digest(body):
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _is_digest(value):
    return (
        isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
    )


def validate_consumer_completion_request_v1(binding_digest, lane_ids):
    if not _is_digest(binding_digest) or len(lane_ids) != 1:
        raise N1ConsumerCompletionError("N1_COMPLETION_REQUEST_INVALID")


def _path(lane_state_root, binding_digest):
    if not _is_digest(binding_digest):
        raise N1ConsumerCompletionError("N1_COMPLETION_BINDING_INVALID")
    return Path(lane_state_root).resolve() / DIRECTORY / (binding_digest + ".json")


def _validate(
    record, *, binding_digest, lane_state_root, lane_id, bound, cycle_prefix, origin_main_sha
):
    if not isinstance(record, dict):
        raise N1ConsumerCompletionError("N1_COMPLETION_RECORD_INVALID")
    body = {k: v for k, v in record.items() if k != "content_digest"}
    if record.get("content_digest") != _digest(body):
        raise N1ConsumerCompletionError("N1_COMPLETION_INTEGRITY_INVALID")
    expected = {
        "schema": SCHEMA,
        "producer": PRODUCER,
        "binding_digest": binding_digest,
        "lane_state_root": str(Path(lane_state_root).resolve()),
        "lane_id": lane_id,
        "bound_instrument": bound,
        "cycle_prefix": cycle_prefix,
        "origin_main_sha": origin_main_sha,
        "execution_authority_effect": "NONE",
    }
    if any(record.get(key) != value for key, value in expected.items()):
        raise N1ConsumerCompletionError("N1_COMPLETION_IDENTITY_MISMATCH")
    consumed = record.get("consumed")
    if (
        not isinstance(consumed, dict)
        or consumed.get("instrument_id") != bound["instrument_id"]
        or consumed.get("native_id") != bound["venue_native_id"]
        # The original lane dispatch adds one lane suffix; S7 adds the second.
        # The cold-start bootstrap has only one and cannot acknowledge this call.
        or consumed.get("cycle_id") != f"{cycle_prefix}:{lane_id}:{lane_id}"
        or not _is_digest(consumed.get("input_digest"))
        or not isinstance(consumed.get("decision_outcome"), str)
        or not consumed["decision_outcome"].strip()
    ):
        raise N1ConsumerCompletionError("N1_COMPLETION_CORE_OUTPUT_INVALID")
    if (
        record.get("disposition") not in SUCCESS_DISPOSITIONS
        or type(record.get("post_count")) is not int
        or record["post_count"] != 0
        or record.get("permit_created") is not False
        or type(record.get("external_effect_count")) is not int
        or record["external_effect_count"] != 0
    ):
        raise N1ConsumerCompletionError("N1_COMPLETION_BOUNDARY_INVALID")


def read_n1_consumer_completion_v1(
    *, lane_state_root, binding_digest, lane_id, bound, cycle_prefix, origin_main_sha
):
    """Read exact original output; absence, conflicts and partial writes stay fenced."""
    try:
        record = json.loads(_path(lane_state_root, binding_digest).read_text())
        _validate(
            record,
            binding_digest=binding_digest,
            lane_state_root=lane_state_root,
            lane_id=lane_id,
            bound=bound,
            cycle_prefix=cycle_prefix,
            origin_main_sha=origin_main_sha,
        )
    except (OSError, TypeError, ValueError, KeyError) as exc:
        raise N1ConsumerCompletionError("N1_COMPLETION_READBACK_REQUIRED:" + str(exc)) from exc
    return record


def _sync_directories(path):
    for directory in (path.parent, path.parent.parent):
        fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _read_prepared(path, expected):
    try:
        record = json.loads(path.read_text())
        _validate(record, **expected)
        return record
    except (OSError, TypeError, ValueError, KeyError) as exc:
        raise N1ConsumerCompletionError(
            "N1_COMPLETION_PREPARED_READBACK_REQUIRED:" + str(exc)
        ) from exc


def _finish_publication(path, pending, expected):
    record = _read_prepared(pending, expected)
    try:
        os.link(pending, path)
    except FileExistsError:
        if read_n1_consumer_completion_v1(**expected) != record:
            raise N1ConsumerCompletionError("N1_COMPLETION_IMMUTABLE_OUTPUT_CONFLICT")
    _sync_directories(path)
    pending.unlink(missing_ok=True)
    _sync_directories(path)
    return record


def recover_n1_consumer_completion_v1(**expected):
    """Finish only an original durable prepared output; never rerun its consumer."""
    path = _path(expected["lane_state_root"], expected["binding_digest"])
    if path.exists():
        # An invalid final record is a conflict, not permission to overwrite it.
        return read_n1_consumer_completion_v1(**expected)
    pending = path.with_suffix(".pending.json")
    # Validate original output before distinguishing a retriable publication
    # failure from a genuinely missing or conflicting consumer outcome.
    _read_prepared(pending, expected)
    try:
        return _finish_publication(path, pending, expected)
    except OSError as exc:
        raise N1ConsumerCompletionPublicationError(
            "N1_COMPLETION_PUBLICATION_RETRY_REQUIRED:" + str(exc)
        ) from exc


def persist_n1_consumer_completion_v1(
    projections, *, binding_digest, cycle_prefix, origin_main_sha
):
    """Publish only after original consumption and all readiness boundary checks."""
    validate_consumer_completion_request_v1(binding_digest, projections)
    lane_id, projection = next(iter(projections.items()))
    invocation = projection.n1_consumer_result.s7_invocation
    if (
        invocation is None
        or invocation.persist_enabled is not True
        or invocation.bound_instrument != projection.bound_instrument
        or Path(invocation.store_root).resolve() != Path(projection.lane_state_root).resolve()
        or invocation.cap61_state_root_bound is not False
    ):
        raise N1ConsumerCompletionError("N1_COMPLETION_ORIGINAL_CONSUMER_UNPROVEN")
    core = invocation.cycle_result
    body = {
        "schema": SCHEMA,
        "producer": PRODUCER,
        "binding_digest": binding_digest,
        "lane_id": lane_id,
        "lane_state_root": str(Path(projection.lane_state_root).resolve()),
        "bound_instrument": projection.bound_instrument.to_dict(),
        "cycle_prefix": cycle_prefix,
        "origin_main_sha": origin_main_sha,
        "consumed": {
            "instrument_id": projection.instrument_id,
            "native_id": projection.native_id,
            "cycle_id": core.cycle_id,
            "input_digest": core.input_digest,
            "decision_outcome": core.decision_outcome,
        },
        "disposition": projection.disposition,
        "post_count": projection.post_count,
        "permit_created": projection.permit_created,
        "external_effect_count": projection.external_effect_count,
        "execution_authority_effect": "NONE",
    }
    record = {**body, "content_digest": _digest(body)}
    expected = dict(
        binding_digest=binding_digest,
        lane_state_root=projection.lane_state_root,
        lane_id=lane_id,
        bound=projection.bound_instrument.to_dict(),
        cycle_prefix=cycle_prefix,
        origin_main_sha=origin_main_sha,
    )
    _validate(record, **expected)
    path = _path(projection.lane_state_root, binding_digest)
    pending = path.with_suffix(".pending.json")
    if path.exists():
        if read_n1_consumer_completion_v1(**expected) != record:
            raise N1ConsumerCompletionError("N1_COMPLETION_IMMUTABLE_OUTPUT_CONFLICT")
        return record
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            # Commit original output before final publication. Preserve this
            # prepared record if publication fails so restart can finish it.
            os.link(temporary, pending)
        except FileExistsError:
            if _read_prepared(pending, expected) != record:
                raise N1ConsumerCompletionError("N1_COMPLETION_IMMUTABLE_OUTPUT_CONFLICT")
        _sync_directories(path)
        _finish_publication(path, pending, expected)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return record
