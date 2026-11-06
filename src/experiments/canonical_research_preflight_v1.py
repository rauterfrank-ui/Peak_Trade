"""Identity lookup before native measurement; original stores remain authoritative."""

from __future__ import annotations
from pathlib import Path
from src.experiments.canonical_advanced_search_v1 import canonical_record_payload_v1
from src.experiments.canonical_research_prepared_execution_v1 import (
    ResearchRecoveryError,
    read_v1,
    digest_v1,
    verify_owner_records_v1,
)


def research_preflight_v1(*, candidate, context, archive, step_path: Path, retest_reason):
    matches = []
    for path in sorted(archive.root.glob("*.json")):
        executed = archive.get(path.stem)
        loop = executed.next_meta_input.research_loop_record
        if loop["selected_experiment_id"] == candidate["experiment_id"]:
            if canonical_record_payload_v1(
                loop["experiment_record"]["experiment_identity"]
            ) != canonical_record_payload_v1(candidate["experiment_identity"]):
                raise ResearchRecoveryError("RESEARCH_IDENTITY_CONFLICT")
            verify_owner_records_v1(executed, context)
            matches.append((path.stem, executed))
    if len(matches) > 1:
        raise ResearchRecoveryError("MULTIPLE_ORIGINAL_PACKETS_FOR_IDENTITY")
    if matches:
        if retest_reason:
            raise ResearchRecoveryError("REPLICATION_NOT_SUPPORTED_V1")
        if (step_path / "prepared.json").exists():
            p = read_v1(step_path / "prepared.json")
            if (step_path / "ack.json").exists():
                ack = read_v1(step_path / "ack.json")
                if ack != {"artifact_id": matches[0][0], "prepared_digest": digest_v1(p)}:
                    raise ResearchRecoveryError("RESEARCH_ARCHIVE_ACK_MISMATCH")
            else:
                return "RESUME_INCOMPLETE", None
        return "REUSE_ARCHIVED", matches[0]
    if step_path.exists():
        if (step_path / "ack.json").exists():
            raise ResearchRecoveryError("RESEARCH_ACK_ARCHIVE_MISSING")
        if (step_path / "prepared.json").exists():
            return "RESUME_INCOMPLETE", None
        raise ResearchRecoveryError("MEASUREMENT_UNCERTAIN_ORIGINAL_REQUEST_MISSING")
    if (
        context.experiment_memory_store.store_root / candidate["experiment_id"]
    ).exists() or context.experiment_memory_store.exists(candidate["experiment_id"]):
        raise ResearchRecoveryError("ORIGINAL_MEASUREMENT_OR_ARCHIVE_MISSING")
    return "EXECUTE_NEW", None
