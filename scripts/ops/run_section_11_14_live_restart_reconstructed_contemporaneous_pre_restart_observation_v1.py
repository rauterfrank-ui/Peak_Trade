"""One-shot runner for §11.14 contemporaneous pre-restart observability prove-or-refute."""

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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_contemporaneous_pre_restart_observation_execute_v1 import (  # noqa: E402
    execute_live_restart_reconstructed_contemporaneous_pre_restart_observation_v1,
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
    result = execute_live_restart_reconstructed_contemporaneous_pre_restart_observation_v1(
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
        "CAPTURE_TRIGGER_AND_PRODUCER.json": dict(result["trigger"]),
        "DURABLE_WRITE_POINT.json": dict(result["write_point"]),
        "RESTART_BOUNDARY.json": dict(result["restart_boundary"]),
        "OBSERVATION_PROTOCOL.json": dict(result["observation_protocol"]),
        "READ_BACK.json": dict(result["read_back"]),
        "OBSERVABILITY_ADJUDICATION.json": dict(result["observability_adjudication"]),
        "COMPLETE_CAPTURE_SEAM_PREDICATE.json": dict(result["seam_predicate"]),
        "READER_BINDING.json": dict(result["binding"]),
        "SAFETY.json": dict(result["safety"]),
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
    print(f"OBSERVATION_STATUS={summary.get('OBSERVATION_STATUS')}")
    print(f"READ_BACK_RESULT={summary.get('READ_BACK_RESULT')}")
    print(f"COMPLETE_CAPTURE_SEAM={summary.get('COMPLETE_CAPTURE_SEAM')}")
    print(f"LIVE_RESTART_RECONSTRUCTED={summary.get('LIVE_RESTART_RECONSTRUCTED')}")
    print(
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED="
        f"{summary.get('CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED')}"
    )
    print(
        "AUTHORIZED_NON_LIVE_RUNTIME_SURFACE_PRESENT="
        f"{summary.get('AUTHORIZED_NON_LIVE_RUNTIME_SURFACE_PRESENT')}"
    )
    print(f"IMPLEMENTATION_AUTHORIZED={summary.get('IMPLEMENTATION_AUTHORIZED')}")
    print(f"MANIFEST_VERIFY_RC={summary['MANIFEST_VERIFY_RC']}")
    return 0 if summary["MANIFEST_VERIFY_RC"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
