"""Evidence persist for the §11.14 flatten GET-only preflight. No POST."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    assert_no_plaintext_in_payload_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    ADJUDICATION_FILENAME,
    CANDIDATE_FILENAME,
    CLAIMS_FILENAME,
    ENVELOPE_FILENAME,
    FROZEN_ENVELOPE_REF_FILENAME,
    GET_LOG_FILENAME,
    HARNESS_FILENAME,
    LINEAGE_FILENAME,
    MANIFEST_FILENAME,
    NON_EXECUTION_FILENAME,
    SUMMARY_FILENAME,
)


class FlattenPersistError(RuntimeError):
    """Fail-closed flatten evidence persist violation."""


def persist_flatten_get_only_evidence_v1(
    *,
    persist_root: Path | str,
    summary: Mapping[str, Any],
    claims: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    gets: Mapping[str, Any],
    envelope: Mapping[str, Any] | None,
    lineage: Mapping[str, Any],
    non_execution: Mapping[str, Any],
) -> dict[str, Any]:
    root = Path(persist_root)
    root.mkdir(parents=True, exist_ok=True)
    files: dict[str, Mapping[str, Any]] = {
        SUMMARY_FILENAME: summary,
        CLAIMS_FILENAME: claims,
        ADJUDICATION_FILENAME: adjudication,
        GET_LOG_FILENAME: gets,
        LINEAGE_FILENAME: lineage,
        NON_EXECUTION_FILENAME: non_execution,
    }
    if envelope is not None:
        files[ENVELOPE_FILENAME] = envelope
    for name, payload in files.items():
        assert_no_plaintext_in_payload_v1(payload)
        write_json_v1(root / name, payload)
    rels = tuple(sorted(files))
    write_manifest_v1(root, rels)
    verified = verify_manifest_v1(root)
    if int(verified.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise FlattenPersistError("MANIFEST_VERIFY_FAILED")
    return {
        "persist_root": str(root),
        "MANIFEST_VERIFY_RC": 0,
        "manifest": MANIFEST_FILENAME,
        "files": list(rels),
    }


def persist_flatten_harness_evidence_v1(
    *,
    persist_root: Path | str,
    summary: Mapping[str, Any],
    claims: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    lineage: Mapping[str, Any],
    non_execution: Mapping[str, Any],
    harness: Mapping[str, Any],
    candidate: Mapping[str, Any] | None,
    frozen_ref: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Persist dry-run/harness evidence. Does not rewrite frozen GET-only packs."""
    root = Path(persist_root)
    root.mkdir(parents=True, exist_ok=True)
    files: dict[str, Mapping[str, Any]] = {
        SUMMARY_FILENAME: summary,
        CLAIMS_FILENAME: claims,
        ADJUDICATION_FILENAME: adjudication,
        LINEAGE_FILENAME: lineage,
        NON_EXECUTION_FILENAME: non_execution,
        HARNESS_FILENAME: harness,
    }
    if candidate is not None:
        files[CANDIDATE_FILENAME] = candidate
    if frozen_ref is not None:
        files[FROZEN_ENVELOPE_REF_FILENAME] = frozen_ref
    for name, payload in files.items():
        assert_no_plaintext_in_payload_v1(payload)
        write_json_v1(root / name, payload)
    rels = tuple(sorted(files))
    write_manifest_v1(root, rels)
    verified = verify_manifest_v1(root)
    if int(verified.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise FlattenPersistError("MANIFEST_VERIFY_FAILED")
    return {
        "persist_root": str(root),
        "MANIFEST_VERIFY_RC": 0,
        "manifest": MANIFEST_FILENAME,
        "files": list(rels),
    }
