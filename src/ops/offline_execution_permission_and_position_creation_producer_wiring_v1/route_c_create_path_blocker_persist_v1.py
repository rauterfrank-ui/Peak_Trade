"""Offline evidence persist for post-Z2DQ Route-C create-path blocker census."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_create_path_blocker_constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_create_path_blocker_persist_claims_v1 import (
    CLAIMS,
)


class Z2DRPersistError(RuntimeError):
    """Fail-closed evidence persist violation."""


def persist_route_c_create_path_blocker_evidence_v1(
    *,
    pack: Path,
    origin_main_sha: str,
    census: Mapping[str, Any],
    summary: Mapping[str, Any],
    adjudication: Mapping[str, Any],
) -> dict[str, Any]:
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise Z2DRPersistError("ORIGIN_MAIN_SHA_MISMATCH")
    pack.mkdir(parents=True, exist_ok=False)
    write_json_v1(pack / "CENSUS.json", census)
    write_json_v1(pack / "SUMMARY.json", summary)
    write_json_v1(pack / "ADJUDICATION.json", adjudication)
    write_json_v1(
        pack / "claims.json",
        {
            **CLAIMS,
            "OWNER_GO": OWNER_GO,
            "THIS_SLICE": THIS_SLICE,
            "WORKPACKAGE_ID": WORKPACKAGE_ID,
            "SECRET_VALUES_INCLUDED": False,
        },
    )
    write_manifest_v1(
        pack,
        (
            "CENSUS.json",
            "SUMMARY.json",
            "ADJUDICATION.json",
            "claims.json",
        ),
    )
    verified = verify_manifest_v1(pack)
    if int(verified.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise Z2DRPersistError("MANIFEST_VERIFY_FAILED")
    return verified
