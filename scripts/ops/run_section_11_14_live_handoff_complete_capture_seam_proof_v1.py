"""One-shot runner for §11.14 Live handoff complete-capture-seam proof."""

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
    HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_OWNER_GO,
    HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_RUN_ID,
    HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_SHA,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_capture_seam_proof_execute_v1 import (  # noqa: E402
    execute_live_handoff_complete_capture_seam_proof_v1,
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
    if origin_main_sha != HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_SHA:
        print(
            "ORIGIN_MAIN_SHA_MISMATCH actual="
            f"{origin_main_sha} expected={HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_SHA}"
        )
        return 2
    result = execute_live_handoff_complete_capture_seam_proof_v1(
        owner_go=HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_OWNER_GO,
        origin_main_sha=origin_main_sha,
        repo_root=repo_root,
        run_id=HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_RUN_ID,
    )
    pack = Path(result["pack"])
    pack.mkdir(parents=True, exist_ok=True)
    documents = {
        "SUMMARY.json": dict(result["summary"]),
        "COMPLETE_CAPTURE_SEAM_PROOF.json": dict(result["proof"]),
        "COMPLETE_CAPTURE_SEAM_PREDICATE.json": dict(result["predicate"]),
        "PRODUCER_RECENSUS.json": dict(result["producer_recensus"]),
        "CAPTURE_TRIGGER.json": dict(result["capture_trigger"]),
        "HANDOFF_RECORD_FIELD_MATRIX.json": dict(result["handoff_record"]),
        "STORAGE_OWNER_CENSUS.json": dict(result["storage_owner"]),
        "WRITER_READER_DATAFLOW.json": dict(result["writer_reader_dataflow"]),
        "FAILURE_MATRIX.json": dict(result["failure_matrix"]),
        "CRASH_BOUNDARY.json": dict(result["crash_boundary"]),
        "TEST_PLAN.json": dict(result["test_plan"]),
        "IMPLEMENTATION_WORKPACKAGE.json": dict(result["implementation_workpackage"]),
        "claims.json": dict(result["claims"]),
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
    print(f"COMPLETE_CAPTURE_SEAM={summary.get('COMPLETE_CAPTURE_SEAM')}")
    print(f"NEW_PRODUCER_IMPLEMENTED={summary.get('NEW_PRODUCER_IMPLEMENTED')}")
    print(f"STORAGE_OWNER_MINTED={summary.get('STORAGE_OWNER_MINTED')}")
    print(f"WRITER_BOUND={summary.get('WRITER_BOUND')}")
    print(f"READER_BOUND={summary.get('READER_BOUND')}")
    print(f"IMPLEMENTATION_AUTHORIZED={summary.get('IMPLEMENTATION_AUTHORIZED')}")
    print(f"MANIFEST_VERIFY_RC={summary['MANIFEST_VERIFY_RC']}")
    return 0 if summary["MANIFEST_VERIFY_RC"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
