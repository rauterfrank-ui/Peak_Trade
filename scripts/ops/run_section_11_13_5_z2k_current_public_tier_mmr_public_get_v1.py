#!/usr/bin/env python3
"""One-shot §11.13.5.Z2K public position-tiers GET. No POST. No credentials."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (  # noqa: E402
    DEFAULT_INSTRUMENT_ID,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_current_public_tier_mmr_productive_evidence_v1 import (  # noqa: E402
    CANARY_INST_FAMILY,
    EVIDENCE_DIRNAME,
    OWNER_GO,
    classify_current_public_tier_mmr_evidence_surface_v1,
    collect_current_public_tier_mmr_public_get_v1,
    persist_current_public_tier_mmr_public_get_evidence_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (  # noqa: E402
    UrllibLiveCanaryTransportV1,
)

REPO_ROOT = _REPO_ROOT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-public-position-tiers-get", action="store_true")
    parser.add_argument("--owner-go", required=True)
    parser.add_argument("--bound-origin-main-sha", required=True)
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    if args.owner_go != OWNER_GO:
        print(f"OWNER_GO_MISMATCH:{args.owner_go}", file=sys.stderr)
        return 2
    if not args.execute_public_position_tiers_get:
        print("EXECUTE_FLAG_REQUIRED", file=sys.stderr)
        return 2
    classification = classify_current_public_tier_mmr_evidence_surface_v1()
    print("EVIDENCE_SURFACE_CLASSIFICATION=")
    print(json.dumps(classification, indent=2, sort_keys=True))
    transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    receive_ts = f"{time.time():.3f}"
    adjudication, snapshot, response = collect_current_public_tier_mmr_public_get_v1(
        transport=transport,
        receive_ts_unix=receive_ts,
        owner_go=args.owner_go,
        instrument_id=DEFAULT_INSTRUMENT_ID,
        inst_family=CANARY_INST_FAMILY,
        rest_host=REUSED_BINDING_REST_HOST,
    )
    if response.method != "GET" or adjudication.post_count != 0:
        print("POST_OR_NON_GET_DETECTED", file=sys.stderr)
        return 3
    result = {
        "MMR_PUBLIC_TIER_QTY_ONE_CURRENT_VALUE": (
            adjudication.mmr_public_tier_qty_one_current_value
        ),
        "MMR_TERM_STATUS": adjudication.mmr_term_status,
        "TIER_CURRENT_VALUE": adjudication.tier_current_value,
        "IMR_PUBLIC_TIER_QTY_ONE_OBSERVED": (adjudication.imr_public_tier_qty_one_observed),
        "MM_LIQ_BUFFER_NUMERIC_STATUS": (adjudication.mm_liq_buffer_numeric_status),
        "PROVIDER_TS_MS": adjudication.provider_ts_ms,
        "RECEIVE_TS_UNIX": adjudication.receive_ts_unix,
        "HTTP_STATUS": adjudication.http_status,
        "OKX_CODE": adjudication.okx_code,
        "COVER_USDC_STATUS": adjudication.cover_usdc_status,
        "GET_REQUEST_COUNT": adjudication.get_request_count,
        "POST_COUNT": adjudication.post_count,
        "LIVE_AUTHORIZED": adjudication.live_authorized,
    }
    print("ADJUDICATION=")
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.persist:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        evidence_root = REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME / run_id
        persistence = persist_current_public_tier_mmr_public_get_evidence_v1(
            evidence_root=evidence_root,
            run_id=run_id,
            bound_origin_main_sha=args.bound_origin_main_sha,
            adjudication=adjudication,
            snapshot=snapshot,
        )
        print("PERSISTENCE=")
        print(json.dumps(persistence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
