"""One-shot runner for PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_FILL_OBSERVED_MAXIMUM_SAFE_LEVERAGE_V1."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (  # noqa: E402
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_execute_v1 import (  # noqa: E402
    execute_live_fill_observed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_gets_v1 import (  # noqa: E402
    EXPECTED_ORIGIN_MAIN_SHA,
    THIS_OWNER_GO,
)


def _origin_main_sha(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "origin/main"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    origin_main_sha = _origin_main_sha(repo_root)
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        print(
            f"ORIGIN_MAIN_SHA_MISMATCH actual={origin_main_sha} expected={EXPECTED_ORIGIN_MAIN_SHA}"
        )
        return 2
    result = execute_live_fill_observed_v1(
        owner_go=THIS_OWNER_GO,
        origin_main_sha=origin_main_sha,
        repo_root=repo_root,
    )
    pack = Path(result["pack"])
    pack.mkdir(parents=True, exist_ok=True)
    summary = dict(result["summary"])
    adjudication = dict(result["adjudication"])
    raw_exchanges = list(result["raw_exchanges"])
    write_json_v1(pack / "SUMMARY.json", summary)
    write_json_v1(pack / "FILL_OBSERVED_ADJUDICATION.json", adjudication)
    names = ["SUMMARY.json", "FILL_OBSERVED_ADJUDICATION.json"]
    for raw in raw_exchanges:
        role = str(raw.get("GET_ROLE") or "UNKNOWN")
        filename = f"GET_{role}.raw.json"
        write_json_v1(pack / filename, raw)
        names.append(filename)
    write_manifest_v1(pack, tuple(names))
    verified = verify_manifest_v1(pack)
    summary["MANIFEST_VERIFY_RC"] = int(verified.get("MANIFEST_VERIFY_RC", 1))
    write_json_v1(pack / "SUMMARY.json", summary)
    write_manifest_v1(pack, tuple(names))
    print(f"EVIDENCE_PACK={pack}")
    print(f"LIVE_FILL_OBSERVED={adjudication.get('LIVE_FILL_OBSERVED')}")
    print(f"NO_FILL_OBSERVED={adjudication.get('NO_FILL_OBSERVED')}")
    print(f"PARTIAL_FILL_OBSERVED={adjudication.get('PARTIAL_FILL_OBSERVED')}")
    print(f"FULL_FILL_OBSERVED={adjudication.get('FULL_FILL_OBSERVED')}")
    print(f"CASE_ADJUDICATION={adjudication.get('CASE_ADJUDICATION')}")
    print(f"LIVE_FILL_ADJUDICATION_REASON={adjudication.get('LIVE_FILL_ADJUDICATION_REASON')}")
    print(f"UNRESOLVED_REASON={adjudication.get('UNRESOLVED_REASON')}")
    print(f"RAW_FILL_ROW_COUNT={adjudication.get('RAW_FILL_ROW_COUNT')}")
    print(f"RAW_EXECUTED_QTY_IF_OBSERVED={adjudication.get('RAW_EXECUTED_QTY_IF_OBSERVED')}")
    print(f"RAW_ORDER_STATE_IF_OBSERVED={adjudication.get('RAW_ORDER_STATE_IF_OBSERVED')}")
    print(f"GET_REQUEST_COUNT={summary.get('GET_REQUEST_COUNT')}")
    print(f"MANIFEST_VERIFY_RC={summary.get('MANIFEST_VERIFY_RC')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
