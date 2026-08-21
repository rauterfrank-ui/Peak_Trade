#!/usr/bin/env python3
"""One-shot authenticated SUI-USD_UM_XPERP trade-fee GET. No POST. No persist."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_fee_reserve_rates_rebind_get_path_v1 import (  # noqa: E402
    MAX_RETRIES,
    SECRETREF_URI,
    SUI_EXECUTE_OWNER_GO,
    SUI_INST_FAMILY,
    SUI_SEALED_QUERY,
    CoverUsdcFeeReserveRatesRebindGetPathError,
    collect_fee_reserve_rates_rebind_get_v1,
    extract_trade_fee_get_fields_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (  # noqa: E402
    LiveCanaryHttpError,
    UrllibLiveCanaryTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (  # noqa: E402
    build_file_secretref_vault_backend_v1,
    release_live_canary_ephemeral_material_v1,
    resolve_and_load_live_canary_secretref_ephemeral_v1,
)

REPO_ROOT = _REPO_ROOT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-go", required=True)
    parser.add_argument("--bound-origin-main-sha", required=True)
    parser.add_argument("--execute-trade-fee-get", action="store_true")
    parser.add_argument("--vault-file", default="")
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    if args.persist:
        print("PERSIST_FORBIDDEN_FOR_SUI_TRADE_FEE_GET", file=sys.stderr)
        return 2
    if args.owner_go != SUI_EXECUTE_OWNER_GO:
        print(f"OWNER_GO_MISMATCH:{args.owner_go}", file=sys.stderr)
        return 2
    if not args.execute_trade_fee_get:
        print("EXECUTE_FLAG_REQUIRED", file=sys.stderr)
        return 2
    vault_path = str(args.vault_file or "").strip()
    if not vault_path:
        print("VAULT_FILE_REQUIRED", file=sys.stderr)
        return 2
    if MAX_RETRIES != 0:
        print("RETRY_COUNT_MUST_BE_ZERO", file=sys.stderr)
        return 2
    handle = None
    try:
        backend = build_file_secretref_vault_backend_v1(vault_file=vault_path)
        handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
            secret_reference=SECRETREF_URI,
            vault_backend=backend,
        )
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
        snapshot, response = collect_fee_reserve_rates_rebind_get_v1(
            transport=transport,
            handle=handle,
            owner_go=args.owner_go,
            execute_trade_fee_get=True,
            inst_family=SUI_INST_FAMILY,
        )
    except (
        CoverUsdcFeeReserveRatesRebindGetPathError,
        LiveCanaryHttpError,
        TimeoutError,
        OSError,
        ValueError,
    ) as exc:
        print(f"FEE_GET_HARD_STOP:{type(exc).__name__}:{exc}", file=sys.stderr)
        return 3
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
    if response.method != "GET" or int(snapshot.get("POST_COUNT") or 0) != 0:
        print("POST_OR_NON_GET_DETECTED", file=sys.stderr)
        return 3
    if int(snapshot.get("GET_REQUEST_COUNT") or 0) != 1:
        print("GET_COUNT_NOT_ONE", file=sys.stderr)
        return 3
    if int(snapshot.get("RETRY_COUNT") or 0) != 0:
        print("RETRY_DETECTED", file=sys.stderr)
        return 3
    if int(response.status_code) != 200:
        print(f"HTTP_STATUS_HARD_STOP:{response.status_code}", file=sys.stderr)
        return 3
    payload = snapshot.get("payload")
    if not isinstance(payload, dict):
        print("PAYLOAD_NOT_OBJECT", file=sys.stderr)
        return 3
    try:
        fields = extract_trade_fee_get_fields_v1(
            payload=payload,
            request_inst_family=SUI_INST_FAMILY,
        )
    except CoverUsdcFeeReserveRatesRebindGetPathError as exc:
        print(f"FEE_GET_SCHEMA_HARD_STOP:{exc}", file=sys.stderr)
        return 3
    if fields["OKX_CODE"] != "0":
        print(f"OKX_CODE_HARD_STOP:{fields['OKX_CODE']}:{fields['OKX_MSG']}", file=sys.stderr)
        return 3
    result = {
        "BOUND_ORIGIN_MAIN_SHA": args.bound_origin_main_sha,
        "OWNER_GO": args.owner_go,
        "REQUEST_INST_FAMILY": SUI_INST_FAMILY,
        "REQUEST_QUERY": SUI_SEALED_QUERY,
        "HTTP_STATUS": int(response.status_code),
        "GET_REQUEST_COUNT": snapshot["GET_REQUEST_COUNT"],
        "POST_COUNT": snapshot["POST_COUNT"],
        "RETRY_COUNT": snapshot["RETRY_COUNT"],
        "LIVE_AUTHORIZED": False,
        "CANARY_INSTRUMENT_UNCHANGED": snapshot["CANARY_INSTRUMENT"],
        "fields": fields,
    }
    print("SUI_TRADE_FEE_GET=")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
