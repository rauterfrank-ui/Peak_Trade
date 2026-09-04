"""One-shot runner for the exhaustive offline LIVE_RESTART_RECONSTRUCTED census."""

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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (  # noqa: E402
    CANONICAL_EVIDENCE_RUN_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_exhaustive_execute_v1 import (  # noqa: E402
    execute_live_restart_reconstructed_exhaustive_census_v1,
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
    result = execute_live_restart_reconstructed_exhaustive_census_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_main_sha,
        repo_root=repo_root,
        run_id=CANONICAL_EVIDENCE_RUN_ID,
    )
    pack = Path(result["pack"])
    pack.mkdir(parents=True, exist_ok=True)
    summary = dict(result["summary"])
    adjudication = dict(result["adjudication"])
    census = dict(result["census"])
    code_path = dict(result["code_path_census"])
    future_go = dict(result["future_owner_go_contract"])
    validator_matrix = dict(result["validator_matrix"])
    write_json_v1(pack / "SUMMARY.json", summary)
    write_json_v1(pack / "RESTART_RECONSTRUCTED_ADJUDICATION.json", adjudication)
    write_json_v1(pack / "EXHAUSTIVE_CENSUS.json", census)
    write_json_v1(pack / "CODE_PATH_CENSUS.json", code_path)
    write_json_v1(pack / "FUTURE_OWNER_GO_CONTRACT.json", future_go)
    write_json_v1(pack / "VALIDATOR_MATRIX.json", validator_matrix)
    names = [
        "SUMMARY.json",
        "RESTART_RECONSTRUCTED_ADJUDICATION.json",
        "EXHAUSTIVE_CENSUS.json",
        "CODE_PATH_CENSUS.json",
        "FUTURE_OWNER_GO_CONTRACT.json",
        "VALIDATOR_MATRIX.json",
    ]
    write_manifest_v1(pack, tuple(names))
    verified = verify_manifest_v1(pack)
    summary["MANIFEST_VERIFY_RC"] = int(verified.get("MANIFEST_VERIFY_RC", 1))
    write_json_v1(pack / "SUMMARY.json", summary)
    write_manifest_v1(pack, tuple(names))
    print(f"EVIDENCE_PACK={pack}")
    print(f"LIVE_RESTART_RECONSTRUCTED={adjudication.get('LIVE_RESTART_RECONSTRUCTED')}")
    print(f"CASE_ADJUDICATION={adjudication.get('CASE_ADJUDICATION')}")
    print(f"EARLIEST_MISSING_FACT={adjudication.get('EARLIEST_MISSING_FACT')}")
    print(f"GET_PERFORMED={summary.get('GET_PERFORMED')}")
    print(f"RESTART_EXECUTION={summary.get('RESTART_EXECUTION')}")
    print(f"MANIFEST_VERIFY_RC={summary.get('MANIFEST_VERIFY_RC')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
