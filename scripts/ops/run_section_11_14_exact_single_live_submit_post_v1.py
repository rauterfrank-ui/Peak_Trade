"""One-shot runner for PEAK_TRADE_OWNER_GO_SECTION_11_14_EXACT_SINGLE_LIVE_SUBMIT_POST_V1."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (  # noqa: E402
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.exact_single_live_submit_execute_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    THIS_OWNER_GO,
    execute_exact_single_live_submit_post_v1,
)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = (
        repo_root
        / "evidence"
        / "ops"
        / "section_11_14_live_order_and_economic_evidence_ladder_v1"
        / run_id
    )
    result = execute_exact_single_live_submit_post_v1(
        owner_go=THIS_OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    result["CANONICAL_EVIDENCE_RUN_ID"] = run_id
    pack.mkdir(parents=True, exist_ok=True)
    write_json_v1(pack / "SUMMARY.json", result)
    ack = dict(result.get("ack_adjudication") or {})
    write_json_v1(pack / "SUBMIT_ACK_OBSERVED_ADJUDICATION.json", ack)
    write_manifest_v1(pack, ("SUMMARY.json", "SUBMIT_ACK_OBSERVED_ADJUDICATION.json"))
    verified = verify_manifest_v1(pack)
    result["MANIFEST_VERIFY_RC"] = int(verified.get("MANIFEST_VERIFY_RC", 1))
    write_json_v1(pack / "SUMMARY.json", result)
    write_manifest_v1(pack, ("SUMMARY.json", "SUBMIT_ACK_OBSERVED_ADJUDICATION.json"))
    print(f"EVIDENCE_PACK={pack}")
    print(f"PRE_WIRE_STOP_REASON={result.get('PRE_WIRE_STOP_REASON')}")
    print(f"PRODUCTIVE_POST_ATTEMPTED={result.get('PRODUCTIVE_POST_ATTEMPTED')}")
    print(f"PRODUCTIVE_POST_ATTEMPT_COUNT={result.get('PRODUCTIVE_POST_ATTEMPT_COUNT')}")
    print(f"WIRE_SEND_ATTEMPTED={result.get('WIRE_SEND_ATTEMPTED')}")
    print(f"UNKNOWN_SUBMIT_STATE={result.get('UNKNOWN_SUBMIT_STATE')}")
    print(f"HTTP_STATUS={result.get('http_status')}")
    print(f"TOP_LEVEL_CODE={result.get('okx_code')}")
    print(f"SCODE={result.get('s_code')}")
    print(f"ORDID_PRESENT={bool(result.get('ord_id'))}")
    print(f"SENT_CLORDID={result.get('sent_clordid')}")
    print(f"RETURNED_CLORDID={result.get('returned_clordid')}")
    print(f"LIVE_SUBMIT_ACK_OBSERVED={result.get('LIVE_SUBMIT_ACK_OBSERVED')}")
    print(f"CANARY_RESULT={result.get('CANARY_RESULT')}")
    print(f"FRESH_PLAN_PRODUCED={result.get('FRESH_PLAN_PRODUCED')}")
    print(f"HISTORICAL_PLAN_REUSED={result.get('HISTORICAL_PLAN_REUSED')}")
    print(f"CURRENT_GATE_CONJUNCTION_STATUS={result.get('CURRENT_GATE_CONJUNCTION_STATUS')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
