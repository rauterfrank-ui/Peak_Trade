"""One-shot runner for PEAK_TRADE_OWNER_GO_SECTION_11_14_LIVE_ACCOUNTING_RECONSTRUCTED_MAXIMUM_SAFE_LEVERAGE_V1."""

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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.accounting_reconstructed_execute_v1 import (  # noqa: E402
    execute_live_accounting_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (  # noqa: E402
    CANONICAL_EVIDENCE_RUN_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
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
    result = execute_live_accounting_reconstructed_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_main_sha,
        repo_root=repo_root,
        run_id=CANONICAL_EVIDENCE_RUN_ID,
    )
    pack = Path(result["pack"])
    pack.mkdir(parents=True, exist_ok=True)
    summary = dict(result["summary"])
    adjudication = dict(result["adjudication"])
    identity = dict(result["identity"])
    source_references = dict(result["source_references"])
    write_json_v1(pack / "SUMMARY.json", summary)
    write_json_v1(pack / "ACCOUNTING_RECONSTRUCTED_ADJUDICATION.json", adjudication)
    write_json_v1(pack / "ACCOUNTING_IDENTITY.json", identity)
    write_json_v1(pack / "SOURCE_REFERENCES.json", source_references)
    names = [
        "SUMMARY.json",
        "ACCOUNTING_RECONSTRUCTED_ADJUDICATION.json",
        "ACCOUNTING_IDENTITY.json",
        "SOURCE_REFERENCES.json",
    ]
    write_manifest_v1(pack, tuple(names))
    verified = verify_manifest_v1(pack)
    summary["MANIFEST_VERIFY_RC"] = int(verified.get("MANIFEST_VERIFY_RC", 1))
    write_json_v1(pack / "SUMMARY.json", summary)
    write_manifest_v1(pack, tuple(names))
    print(f"EVIDENCE_PACK={pack}")
    print(f"LIVE_ACCOUNTING_RECONSTRUCTED={adjudication.get('LIVE_ACCOUNTING_RECONSTRUCTED')}")
    print(f"LIVE_RESTART_RECONSTRUCTED={adjudication.get('LIVE_RESTART_RECONSTRUCTED')}")
    print(f"CASE_ADJUDICATION={adjudication.get('CASE_ADJUDICATION')}")
    print(f"ACCOUNTING_RESULT={adjudication.get('ACCOUNTING_RESULT')}")
    print(f"ACCOUNTING_RESULT_UNIT={adjudication.get('ACCOUNTING_RESULT_UNIT')}")
    print(f"ACCOUNTING_RESIDUAL={adjudication.get('ACCOUNTING_RESIDUAL')}")
    print(f"ACCOUNTING_RESIDUAL_UNIT={adjudication.get('ACCOUNTING_RESIDUAL_UNIT')}")
    print(f"GET_PERFORMED={summary.get('GET_PERFORMED')}")
    print(f"CREDENTIAL_USE={summary.get('CREDENTIAL_USE')}")
    print(f"MANIFEST_VERIFY_RC={summary.get('MANIFEST_VERIFY_RC')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
