"""One-shot runner for §11.14 Live handoff owner/capture architecture adjudication."""

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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_architecture_adjudication_execute_v1 import (  # noqa: E402
    execute_live_durable_pre_restart_handoff_owner_and_capture_architecture_adjudication_v1,
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
    result = (
        execute_live_durable_pre_restart_handoff_owner_and_capture_architecture_adjudication_v1(
            owner_go=OWNER_GO,
            origin_main_sha=origin_main_sha,
            repo_root=repo_root,
            run_id=CANONICAL_EVIDENCE_RUN_ID,
        )
    )
    pack = Path(result["pack"])
    pack.mkdir(parents=True, exist_ok=True)
    documents = {
        "SUMMARY.json": dict(result["summary"]),
        "ARCHITECTURE_ADJUDICATION.json": dict(result["architecture"]),
        "OWNER_CONTRACT.json": dict(result["owner"]),
        "POS_SEMANTICS_ADJUDICATION.json": dict(result["pos"]),
        "CAPTURE_SEAM_GRAPH_CENSUS.json": dict(result["seams"]),
        "DURABILITY_CONTRACT.json": dict(result["durability"]),
        "WRITER_READER_CONTRACT.json": dict(result["writer_reader"]),
        "RESTART_ADMISSION_PREDICATE.json": dict(result["admission"]),
        "STEP_29P_HANDOFF_RELATION.json": dict(result["step_29p"]),
        "SLICE_SEQUENCE.json": dict(result["sequence"]),
        "RESTART_RECONSTRUCTED_ADJUDICATION.json": dict(result["adjudication"]),
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
    print(f"POS_SEMANTICS={summary.get('POS_SEMANTICS')}")
    print(f"COMPLETE_CAPTURE_SEAM={summary.get('COMPLETE_CAPTURE_SEAM')}")
    print(
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT="
        f"{summary.get('SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT')}"
    )
    print(f"PROPOSED_FIRST_OWNER_ADJUDICATION={summary.get('PROPOSED_FIRST_OWNER_ADJUDICATION')}")
    print(f"STEP_29P_HANDOFF_RELATION={summary.get('STEP_29P_HANDOFF_RELATION')}")
    print(f"ARCHITECTURE_ADJUDICATION_COMPLETE={summary.get('ARCHITECTURE_ADJUDICATION_COMPLETE')}")
    print(f"IMPLEMENTATION_AUTHORIZED={summary.get('IMPLEMENTATION_AUTHORIZED')}")
    print(f"LIVE_RESTART_RECONSTRUCTED={summary.get('LIVE_RESTART_RECONSTRUCTED')}")
    print(f"GET_PERFORMED={summary.get('GET_PERFORMED')}")
    print(f"WIRE_SEND={summary.get('WIRE_SEND')}")
    print(f"MANIFEST_VERIFY_RC={summary.get('MANIFEST_VERIFY_RC')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
