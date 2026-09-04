"""Orchestrate fill GETs, adjudication, and evidence packaging. No POST."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryTransportV1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.credential_presence_v1 import (
    default_vault_path_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_adjudication_v1 import (
    adjudicate_live_fill_observed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_gets_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    THIS_OWNER_GO,
    execute_fill_observed_gets_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_ACK_EVIDENCE_RUN_ID,
    BOUND_ACK_SOURCE_KIND,
    BOUND_CLORDID,
    BOUND_INSTID,
    BOUND_ORDID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.persist_v1 import (
    assert_no_secrets_in_payload_v1,
)

EVIDENCE_DIRNAME = "section_11_14_live_order_and_economic_evidence_ladder_v1"


def _utc_now_compact_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def execute_live_fill_observed_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    vault_file: Path | None = None,
    transport: LiveCanaryTransportV1 | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    if str(owner_go or "").strip() != THIS_OWNER_GO:
        raise Section1114OfflineSurfaceError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    productive = transport is None
    resolved_vault = vault_file
    if productive and resolved_vault is None:
        resolved_vault = default_vault_path_v1(repo_root=Path(repo_root))
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack_run_id = str(run_id or _utc_now_compact_v1())
    gets = execute_fill_observed_gets_v1(
        owner_go=owner_go,
        origin_main_sha=origin_main_sha,
        vault_file=resolved_vault,
        transport=transport,
    )
    assert_no_secrets_in_payload_v1(gets)
    adjudication = adjudicate_live_fill_observed_v1(fill_evidence=gets)
    assert_no_secrets_in_payload_v1(adjudication)
    ended = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary = {
        "OWNER_GO": THIS_OWNER_GO,
        "CANONICAL_EVIDENCE_RUN_ID": pack_run_id,
        "ORIGIN_MAIN_SHA": origin_main_sha,
        "STARTED_AT_UTC": started,
        "ENDED_AT_UTC": ended,
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_CLORDID": BOUND_CLORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "BOUND_ACK_SOURCE_KIND": BOUND_ACK_SOURCE_KIND,
        "BOUND_ACK_EVIDENCE_RUN_ID": BOUND_ACK_EVIDENCE_RUN_ID,
        "GET_PERFORMED": True,
        "PRIVATE_GET_USED": True,
        "PUBLIC_GET_USED": False,
        "CREDENTIAL_USE": bool(gets.get("CREDENTIAL_USE")),
        "GET_REQUEST_COUNT": gets.get("GET_REQUEST_COUNT"),
        "READ_ENDPOINTS_USED": list(gets.get("ENDPOINTS") or []),
        "POST_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "RETRY_USED": False,
        "SECOND_SUBMIT_USED": False,
        "FLATTEN_EXECUTE_USED": False,
        "FUNDING_USED": False,
        "LIVE_SUBMIT_ACK_OBSERVED": True,
        "LIVE_FILL_OBSERVED": adjudication.get("LIVE_FILL_OBSERVED"),
        "LIVE_FEE_OBSERVED": False,
        "LIVE_POSITION_RECONCILED": False,
        "SECTION_11_14_COMPLETE": False,
        "SECTION_11_14_AUTHORIZED": False,
        "NO_FILL_OBSERVED": adjudication.get("NO_FILL_OBSERVED"),
        "PARTIAL_FILL_OBSERVED": adjudication.get("PARTIAL_FILL_OBSERVED"),
        "FULL_FILL_OBSERVED": adjudication.get("FULL_FILL_OBSERVED"),
        "CASE_ADJUDICATION": adjudication.get("CASE_ADJUDICATION"),
        "LIVE_FILL_ADJUDICATION_REASON": adjudication.get("LIVE_FILL_ADJUDICATION_REASON"),
        "UNRESOLVED_REASON": adjudication.get("UNRESOLVED_REASON"),
        "SECRET_VALUES_INCLUDED": False,
        "GET_ERROR": gets.get("GET_ERROR"),
        "fill_adjudication": adjudication,
        "get_pack": {
            "ENDPOINTS": gets.get("ENDPOINTS"),
            "HOST": gets.get("HOST"),
            "VENUE_REQUESTS": gets.get("VENUE_REQUESTS"),
            "GET_ERROR": gets.get("GET_ERROR"),
            "OBSERVATIONS": gets.get("OBSERVATIONS"),
        },
    }
    assert_no_secrets_in_payload_v1(summary)
    pack = Path(repo_root) / "evidence" / "ops" / EVIDENCE_DIRNAME / pack_run_id
    return {
        "pack": pack,
        "run_id": pack_run_id,
        "summary": summary,
        "adjudication": adjudication,
        "gets": gets,
        "raw_exchanges": list(gets.get("RAW_EXCHANGES") or []),
    }
