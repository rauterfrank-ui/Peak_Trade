"""Sanitized durable evidence for productive Treasury read-only observation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.treasury_productive_read_only_venue_observation_v1.constants_v1 import (
    OWNER_GO,
    SESSION_OWNER_GO,
    WP_ID,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.errors_v1 import (
    TreasuryProductiveReadOnlyVenueObservationError,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)

EVIDENCE_PACK_MANIFEST_FILES: tuple[str, ...] = (
    "adjudication.json",
    "capture_summary.json",
    "claims.json",
    "treasury_observation.sanitized.json",
)


def _utc_stamp_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _assert_no_secrets_v1(payload: Mapping[str, Any]) -> None:
    rendered = json.dumps(payload, sort_keys=True).lower()
    for marker in ("ok-access-", "apikey", "secretkey", "passphrase", "authorization"):
        if marker in rendered:
            raise TreasuryProductiveReadOnlyVenueObservationError("SECRET_MATERIAL_IN_EVIDENCE")


def persist_treasury_productive_observation_evidence_pack_v1(
    *,
    evidence_root: Path,
    origin_main_sha: str,
    capture_result: Mapping[str, Any],
) -> dict[str, Any]:
    if capture_result.get("disposition") != "PRODUCTIVE_OBSERVATION_COMPLETE":
        raise TreasuryProductiveReadOnlyVenueObservationError("CAPTURE_NOT_COMPLETE")

    sanitized = {
        "OBSERVATION_IDENTITY": capture_result.get("OBSERVATION_IDENTITY"),
        "OBSERVATION_PROVENANCE": capture_result.get("OBSERVATION_PROVENANCE"),
        "OBSERVATION_FRESHNESS": capture_result.get("OBSERVATION_FRESHNESS"),
        "OBSERVATION_AMBIGUITY": capture_result.get("OBSERVATION_AMBIGUITY"),
        "funding_observation_public": capture_result.get("funding_observation_public"),
        "treasury_venue_observation": capture_result.get("treasury_venue_observation"),
        "reconciliation_chain": capture_result.get("reconciliation_chain"),
        "TREASURY_SEPARATION_MATRIX": capture_result.get("TREASURY_SEPARATION_MATRIX"),
    }
    _assert_no_secrets_v1(sanitized)

    pack = evidence_root / _utc_stamp_v1()
    pack.mkdir(parents=True, exist_ok=False)

    write_json_v1(
        pack / "capture_summary.json",
        {
            "NETWORK_READ_ONLY_USED": capture_result.get("NETWORK_READ_ONLY_USED"),
            "NETWORK_REQUESTS_PERFORMED": capture_result.get("NETWORK_REQUESTS_PERFORMED"),
            "NETWORK_METHODS_USED": capture_result.get("NETWORK_METHODS_USED"),
            "pre_network_gate": capture_result.get("pre_network_gate"),
        },
    )
    write_json_v1(pack / "treasury_observation.sanitized.json", sanitized)
    write_json_v1(
        pack / "adjudication.json",
        {
            "ADJUDICATED_CONCLUSIONS": {
                "PRODUCTIVE_OBSERVATION_STATUS": "VENUE_FACT_OBSERVED",
                "RECONCILIATION_STATUS": capture_result.get("reconciliation_chain", {}).get(
                    "RECONCILIATION_STATUS"
                ),
                "EARLIEST_NEW_REAL_BLOCKER": capture_result.get("reconciliation_chain", {}).get(
                    "EARLIEST_NEW_REAL_BLOCKER"
                ),
            },
            "NAVIGATION": {
                "WP_ID": WP_ID,
                "OWNER_GO": OWNER_GO,
                "SESSION_OWNER_GO": SESSION_OWNER_GO,
                "ORIGIN_MAIN_SHA": origin_main_sha,
            },
        },
    )
    write_json_v1(
        pack / "claims.json",
        {
            "WP_ID": WP_ID,
            "OWNER_GO": OWNER_GO,
            "SESSION_OWNER_GO": SESSION_OWNER_GO,
            "HTTP_METHODS": ["GET"],
            "POST_REQUEST_COUNT": 0,
            "TREASURY_MUTATION_REQUEST_COUNT": 0,
            "SECRET_EXPOSURE": "NONE",
            "AUTHORITY_GRAPH_CHANGED": False,
            "RISK_ADMISSIBLE_MINT": False,
        },
    )
    write_manifest_v1(pack, EVIDENCE_PACK_MANIFEST_FILES)
    manifest_rc = verify_manifest_v1(pack)
    if int(manifest_rc.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise TreasuryProductiveReadOnlyVenueObservationError("MANIFEST_VERIFY_FAIL")
    return {
        "EVIDENCE_PACK_PATH": str(pack),
        "MANIFEST_VERIFY_RC": int(manifest_rc.get("MANIFEST_VERIFY_RC", 0)),
    }
