"""One-shot runner for §11.14 productive capture-owner and lifecycle-hook binding."""

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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_productive_capture_owner_and_lifecycle_hook_binding_execute_v1 import (  # noqa: E402
    execute_live_handoff_productive_capture_owner_and_lifecycle_hook_binding_v1,
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
    result = execute_live_handoff_productive_capture_owner_and_lifecycle_hook_binding_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_main_sha,
        repo_root=repo_root,
        run_id=CANONICAL_EVIDENCE_RUN_ID,
    )
    pack = Path(result["pack"])
    pack.mkdir(parents=True, exist_ok=True)
    documents = {
        "SUMMARY.json": dict(result["summary"]),
        "BASELINE.json": dict(result["baseline"]),
        "CHANGED_PATH_CENSUS.json": dict(result["changed_path_census"]),
        "PATH_GRAPH.json": dict(result["path_graph"]),
        "OWNER_CENSUS.json": dict(result["owner_census"]),
        "HOOK_CENSUS.json": dict(result["hook_census"]),
        "AUTHORIZATION_SURFACE_MATRIX.json": dict(result["authorization_surfaces"]),
        "PRODUCTIVE_BINDING_DECISION.json": dict(result["binding_decision"]),
        "COMPLETE_CAPTURE_SEAM_PREDICATE.json": dict(result["seam_predicate"]),
        "SAFETY.json": dict(result["safety"]),
        "claims.json": dict(result["claims"]),
        "ADJUDICATION.json": dict(result["adjudication"]),
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
    print(f"CASE_ADJUDICATION={summary.get('CASE_ADJUDICATION')}")
    print(f"BINDING_CASE={summary.get('BINDING_CASE')}")
    print(
        f"MINIMAL_FAIL_CLOSED_BINDING_ALLOWED={summary.get('MINIMAL_FAIL_CLOSED_BINDING_ALLOWED')}"
    )
    print(f"PRODUCTIVE_CAPTURE_OWNER_STATUS={summary.get('PRODUCTIVE_CAPTURE_OWNER_STATUS')}")
    print(f"PRODUCTIVE_LIFECYCLE_HOOK_STATUS={summary.get('PRODUCTIVE_LIFECYCLE_HOOK_STATUS')}")
    print(f"AUTHORIZED_RUNTIME_SURFACE={summary.get('AUTHORIZED_RUNTIME_SURFACE')}")
    print(f"COMPLETE_CAPTURE_SEAM={summary.get('COMPLETE_CAPTURE_SEAM')}")
    print(f"LIVE_RESTART_RECONSTRUCTED={summary.get('LIVE_RESTART_RECONSTRUCTED')}")
    print(f"IMPLEMENTATION_AUTHORIZED={summary.get('IMPLEMENTATION_AUTHORIZED')}")
    print(f"MANIFEST_VERIFY_RC={summary['MANIFEST_VERIFY_RC']}")
    return 0 if summary["MANIFEST_VERIFY_RC"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
