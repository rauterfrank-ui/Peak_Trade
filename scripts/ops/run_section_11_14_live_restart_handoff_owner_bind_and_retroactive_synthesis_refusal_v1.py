"""One-shot runner for Live restart handoff owner-bind and retroactive-synthesis refusal."""

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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_bind_execute_v1 import (  # noqa: E402
    execute_live_restart_handoff_owner_bind_and_retroactive_synthesis_refusal_v1,
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
    result = execute_live_restart_handoff_owner_bind_and_retroactive_synthesis_refusal_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_main_sha,
        repo_root=repo_root,
        run_id=CANONICAL_EVIDENCE_RUN_ID,
    )
    pack = Path(result["pack"])
    pack.mkdir(parents=True, exist_ok=True)
    documents = {
        "SUMMARY.json": dict(result["summary"]),
        "RESTART_RECONSTRUCTED_ADJUDICATION.json": dict(result["adjudication"]),
        "EXHAUSTIVE_CENSUS.json": dict(result["census"]),
        "ADDITIVE_CENSUS_PERSIST.json": dict(result["census_persist"]),
        "HANDOFF_OWNER_BIND.json": dict(result["owner_bind"]),
        "OWNER_CENSUS_MATRIX.json": dict(result["owner_matrix"]),
        "RETROACTIVE_SYNTHESIS_REFUSAL.json": dict(result["synthesis_refusal"]),
        "HISTORICAL_UNPROVABILITY_BIND.json": dict(result["historical_unprovability"]),
        "CODE_PATH_CENSUS.json": dict(result["code_path_census"]),
        "FUTURE_OWNER_GO_CONTRACT.json": dict(result["future_owner_go_contract"]),
        "VALIDATOR_MATRIX.json": dict(result["validator_matrix"]),
    }
    names = sorted(documents)
    for name, payload in documents.items():
        write_json_v1(pack / name, payload)
    write_manifest_v1(pack, tuple(names))
    verified = verify_manifest_v1(pack)
    summary = dict(result["summary"])
    summary["MANIFEST_VERIFY_RC"] = int(verified.get("MANIFEST_VERIFY_RC", 1))
    write_json_v1(pack / "SUMMARY.json", summary)
    write_manifest_v1(pack, tuple(names))
    print(f"EVIDENCE_PACK={pack}")
    print(f"LIVE_RESTART_RECONSTRUCTED={result['adjudication'].get('LIVE_RESTART_RECONSTRUCTED')}")
    print(
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT="
        f"{result['owner_bind'].get('SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT')}"
    )
    print(
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED="
        f"{result['synthesis_refusal'].get('RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED')}"
    )
    print(f"GET_PERFORMED={summary.get('GET_PERFORMED')}")
    print(f"RESTART_EXECUTION={summary.get('RESTART_EXECUTION')}")
    print(f"MANIFEST_VERIFY_RC={summary.get('MANIFEST_VERIFY_RC')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
