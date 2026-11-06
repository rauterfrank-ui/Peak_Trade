"""Durable handoff of an original Phase10 request, not another scientific memory.

Safe explicit dataclass codec and exact owner locators; no pickle/dynamic import,
new measurement, timestamp replacement, deletion or productive authority.
"""

from __future__ import annotations
from contextlib import contextmanager
from dataclasses import fields, is_dataclass, replace
import fcntl
import hashlib
import json
import os
import tempfile
from typing import Mapping

from src.experiments.canonical_automated_offline_research_loop_v1 import (
    CanonicalAutomatedOfflineResearchLoopRequestV1,
    ResearchHypothesisCandidateV1,
    OfflineExperimentObservationsV1,
)
from src.experiments.canonical_experiment_identity_v1 import CanonicalExperimentIdentityRequestV1
from src.experiments.canonical_comparison_ssot_v1 import (
    ComparisonCandidateV1,
    ComparisonCompatibilityContractV1,
    CompatibilityRuleV1,
)
from src.experiments.canonical_reality_gap_store_v1 import RealityGapDimensionV1
from src.experiments.canonical_advanced_search_v1 import canonical_record_payload_v1


class ResearchRecoveryError(ValueError):
    pass


_TYPES = {
    c.__name__: c
    for c in (
        CanonicalAutomatedOfflineResearchLoopRequestV1,
        ResearchHypothesisCandidateV1,
        OfflineExperimentObservationsV1,
        CanonicalExperimentIdentityRequestV1,
        ComparisonCandidateV1,
        ComparisonCompatibilityContractV1,
        CompatibilityRuleV1,
        RealityGapDimensionV1,
    )
}
_STORE_FIELDS = ("experiment_memory_store", "failure_memory_store", "reality_gap_store")


def encode_request_value_v1(value):
    if hasattr(value, "store_root"):
        return {"store_type": type(value).__name__, "root": str(value.store_root.resolve())}
    if is_dataclass(value):
        return {
            "dataclass": type(value).__name__,
            "fields": {
                f.name: encode_request_value_v1(getattr(value, f.name)) for f in fields(value)
            },
        }
    if isinstance(value, Mapping):
        return {"mapping": {k: encode_request_value_v1(v) for k, v in value.items()}}
    if isinstance(value, (list, tuple)):
        return [encode_request_value_v1(v) for v in value]
    if value is None or isinstance(value, (bool, str, int, float)):
        return value
    raise ResearchRecoveryError("PREPARED_UNSUPPORTED_TYPE:" + type(value).__name__)


def decode_request_value_v1(value, owners):
    if isinstance(value, list):
        return [decode_request_value_v1(v, owners) for v in value]
    if isinstance(value, dict):
        if set(value) == {"store_type", "root"}:
            matches = [o for o in owners if encode_request_value_v1(o) == value]
            if len(matches) != 1:
                raise ResearchRecoveryError("PREPARED_OWNER_LOCATOR_MISMATCH")
            return matches[0]
        if set(value) == {"mapping"}:
            return {k: decode_request_value_v1(v, owners) for k, v in value["mapping"].items()}
        if set(value) == {"dataclass", "fields"} and value["dataclass"] in _TYPES:
            cls = _TYPES[value["dataclass"]]
            if set(value["fields"]) != {f.name for f in fields(cls)}:
                raise ResearchRecoveryError("PREPARED_DATACLASS_FIELDS_MISMATCH")
            return cls(
                **{k: decode_request_value_v1(v, owners) for k, v in value["fields"].items()}
            )
        raise ResearchRecoveryError("PREPARED_CODEC_MISMATCH")
    return value


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest_v1(value):
    return hashlib.sha256(_bytes(value)).hexdigest()


def _sync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def publish_v1(path, body):
    envelope = {"body": body, "sha256": digest_v1(body)}
    raw = _bytes(envelope)
    if path.is_symlink():
        raise ResearchRecoveryError("RESEARCH_SYMLINK_FORBIDDEN")
    if path.exists():
        if path.read_bytes() != raw:
            raise ResearchRecoveryError("RESEARCH_IMMUTABLE_CONFLICT")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".prepared-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != raw:
                raise ResearchRecoveryError("RESEARCH_IMMUTABLE_CONFLICT")
        for p in (path.parent, *path.parent.parents):
            _sync_dir(p)
    finally:
        os.unlink(temporary)


def read_v1(path):
    if path.is_symlink():
        raise ResearchRecoveryError("RESEARCH_SYMLINK_FORBIDDEN")
    value = json.loads(path.read_bytes())
    if set(value) != {"body", "sha256"} or value["sha256"] != digest_v1(value["body"]):
        raise ResearchRecoveryError("RESEARCH_PACKET_DIGEST_MISMATCH")
    return value["body"]


@contextmanager
def research_step_lease_v1(context):
    path = context.experiment_memory_store.store_root.resolve() / ".research_step_v1.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ResearchRecoveryError("RESEARCH_SYMLINK_FORBIDDEN")
    with path.open("a+b") as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ResearchRecoveryError("RESEARCH_STEP_BUSY") from exc
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def journal_root_v1(context):
    return context.experiment_memory_store.store_root.resolve() / ".research_steps_v1"


def intent_digest_v1(request, prior_ids, provider_ref, source_class, meta_policy=None):
    # Caller clocks may advance at resume. Scientific identity/seed/config and
    # explicit input context do not change to evade an already charged trial.
    value = encode_request_value_v1(replace(request, created_at="ORIGINAL_CLOCK_RETAINED"))
    return digest_v1(
        {
            "request": value,
            "prior_ids": list(prior_ids),
            "provider_ref": provider_ref,
            "source_class": source_class,
            "meta_policy": encode_request_value_v1(meta_policy),
        }
    )


def verify_owner_records_v1(executed, context):
    loop = executed.next_meta_input.research_loop_record
    rows = [
        (context.experiment_memory_store, loop["experiment_record"], "experiment_id"),
        (context.reality_gap_store, loop["reality_gap_record"], "reality_gap_record_id"),
    ]
    rows += [
        (context.failure_memory_store, r, "failure_record_id") for r in loop["failure_records"]
    ]
    for owner, expected, key in rows:
        actual = owner.get(expected[key])
        if canonical_record_payload_v1(actual) != canonical_record_payload_v1(expected):
            raise ResearchRecoveryError("RESEARCH_ORIGINAL_OWNER_READBACK_MISMATCH")


def finish_prepared_v1(path, archive, context):
    from src.experiments.canonical_native_research_session_v1 import (
        _validate_measurement,
        NativeResearchSessionStepV1,
    )
    from src.experiments.canonical_search_candidate_research_execution_v1 import (
        run_search_candidate_research_execution_v1,
    )

    prepared = read_v1(path / "prepared.json")
    started = read_v1(path / "started.json")
    if (
        prepared.get("schema_version") != "research_prepared_execution.v1"
        or started.get("schema_version") != "research_started.v1"
        or started.get("experiment_id") != path.name
    ):
        raise ResearchRecoveryError("RESEARCH_PREPARED_SCHEMA_OR_IDENTITY_MISMATCH")
    if prepared["started_digest"] != digest_v1(started):
        raise ResearchRecoveryError("PREPARED_STARTED_MISMATCH")
    if prepared["archive_root"] != str(archive.root):
        raise ResearchRecoveryError("PREPARED_ARCHIVE_LOCATOR_MISMATCH")
    request = decode_request_value_v1(
        prepared["request"], [getattr(context, n) for n in _STORE_FIELDS]
    )
    if not isinstance(request, CanonicalAutomatedOfflineResearchLoopRequestV1):
        raise ResearchRecoveryError("PREPARED_PHASE10_REQUEST_REQUIRED")
    if (path / "ack.json").exists():
        ack = read_v1(path / "ack.json")
        if set(ack) != {"artifact_id", "prepared_digest"} or ack["prepared_digest"] != digest_v1(
            prepared
        ):
            raise ResearchRecoveryError("RESEARCH_ARCHIVE_ACK_MISMATCH")
        original = archive.get(ack["artifact_id"])
        _validate_measurement(prepared["receipt"], original)
        verify_owner_records_v1(original, context)
        return NativeResearchSessionStepV1(
            started["search"], started["feedback"], original, ack["artifact_id"], "REUSE_ARCHIVED"
        )
    dry = replace(
        request, experiment_memory_store=None, failure_memory_store=None, reality_gap_store=None
    )
    validated = run_search_candidate_research_execution_v1(
        search_record=started["search"],
        experiment_id=started["experiment_id"],
        created_at=request.created_at,
        experiment_provider=lambda candidate: dry,
        provider_ref=started["provider_ref"],
        evidence_source_class=started["source_class"],
    )
    _validate_measurement(prepared["receipt"], validated)
    executed = run_search_candidate_research_execution_v1(
        search_record=started["search"],
        experiment_id=started["experiment_id"],
        created_at=request.created_at,
        experiment_provider=lambda candidate: request,
        provider_ref=started["provider_ref"],
        evidence_source_class=started["source_class"],
    )
    _validate_measurement(prepared["receipt"], executed)
    key = archive.append(executed, prepared["receipt"])
    verify_owner_records_v1(archive.get(key), context)
    publish_v1(path / "ack.json", {"artifact_id": key, "prepared_digest": digest_v1(prepared)})
    return NativeResearchSessionStepV1(
        started["search"], started["feedback"], executed, key, "RESUMED_AND_ARCHIVED"
    )
