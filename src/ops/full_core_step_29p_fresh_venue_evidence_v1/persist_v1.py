"""Persist STEP-29P fresh GET evidence. No secrets. No POST."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CLAIMS_FILENAME,
    MANIFEST_FILENAME,
    SUMMARY_FILENAME,
)

SNAPSHOT_FILENAME = "SNAPSHOT.json"
REQUIREMENT_MATRIX_FILENAME = "REQUIREMENT_MATRIX.json"
GETS_FILENAME = "GETS.json"


def persist_step_29p_fresh_venue_evidence_v1(
    *,
    pack: Path,
    snapshot: Mapping[str, Any],
    summary: Mapping[str, Any],
    claims: Mapping[str, Any],
    requirement_matrix: Mapping[str, Any],
    gets: Mapping[str, Any],
) -> dict[str, Any]:
    pack.mkdir(parents=True, exist_ok=True)
    write_json_v1(pack / SNAPSHOT_FILENAME, snapshot)
    write_json_v1(pack / SUMMARY_FILENAME, summary)
    write_json_v1(pack / CLAIMS_FILENAME, claims)
    write_json_v1(pack / REQUIREMENT_MATRIX_FILENAME, requirement_matrix)
    write_json_v1(pack / GETS_FILENAME, gets)
    relative = (
        SNAPSHOT_FILENAME,
        SUMMARY_FILENAME,
        CLAIMS_FILENAME,
        REQUIREMENT_MATRIX_FILENAME,
        GETS_FILENAME,
    )
    manifest_sha = write_manifest_v1(pack, relative)
    verify = verify_manifest_v1(pack)
    return {
        "EVIDENCE_PACK": str(pack),
        "MANIFEST_SHA256": manifest_sha,
        "MANIFEST_FILENAME": MANIFEST_FILENAME,
        "MANIFEST_VERIFY_RC": int(verify.get("MANIFEST_VERIFY_RC", 1)),
        "SECRET_VALUES_INCLUDED": False,
    }
