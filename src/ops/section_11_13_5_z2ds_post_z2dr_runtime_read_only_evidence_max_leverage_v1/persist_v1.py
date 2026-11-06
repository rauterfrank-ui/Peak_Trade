"""Sanitized evidence persist for the Z2DS runtime read-only GET package."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1.redaction_v1 import (
    Z2DSRedactionError,
    assert_no_secrets_in_payload_v1,
)


class Z2DSPersistError(RuntimeError):
    """Fail-closed evidence persist violation."""


def persist_z2ds_runtime_read_only_evidence_v1(
    *,
    pack: Path,
    origin_main_sha: str,
    snapshot: Mapping[str, Any],
    summary: Mapping[str, Any],
    adjudication: Mapping[str, Any],
) -> dict[str, Any]:
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise Z2DSPersistError("ORIGIN_MAIN_SHA_MISMATCH")
    try:
        assert_no_secrets_in_payload_v1(snapshot)
        assert_no_secrets_in_payload_v1(summary)
        assert_no_secrets_in_payload_v1(adjudication)
        assert_no_secrets_in_payload_v1(CLAIMS)
    except Z2DSRedactionError as exc:
        raise Z2DSPersistError(str(exc)) from exc
    pack.mkdir(parents=True, exist_ok=False)
    write_json_v1(pack / "GET_SNAPSHOT.sanitized.json", snapshot)
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
            "GET_SNAPSHOT.sanitized.json",
            "SUMMARY.json",
            "ADJUDICATION.json",
            "claims.json",
        ),
    )
    verified = verify_manifest_v1(pack)
    if int(verified.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise Z2DSPersistError("MANIFEST_VERIFY_FAILED")
    return verified
