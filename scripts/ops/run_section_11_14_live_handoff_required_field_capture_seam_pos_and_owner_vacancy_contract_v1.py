"""One-shot runner for §11.14 required-field capture-seam and owner-vacancy contract."""

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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_required_field_capture_execute_v1 import (  # noqa: E402
    execute_live_handoff_required_field_capture_seam_pos_and_owner_vacancy_contract_v1,
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
    result = execute_live_handoff_required_field_capture_seam_pos_and_owner_vacancy_contract_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_main_sha,
        repo_root=repo_root,
        run_id=CANONICAL_EVIDENCE_RUN_ID,
    )
    pack = Path(result["pack"])
    pack.mkdir(parents=True, exist_ok=True)
    documents = {
        "SUMMARY.json": dict(result["summary"]),
        "REQUIRED_FIELD_CONTRACT.json": dict(result["field_contract"]),
        "CAPTURE_MOMENT_CENSUS.json": dict(result["timeline"]),
        "POS_PRODUCER_CENSUS.json": dict(result["pos_producer_census"]),
        "POS_DERIVATION_ADJUDICATION.json": dict(result["pos_derivation"]),
        "OWNER_VACANCY_CONTRACT.json": dict(result["owner_vacancy"]),
        "HANDOFF_OWNER_BIND.json": dict(result["owner_bind"]),
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
    print(f"OWNER_VACANCY_CONTRACT_STATUS={summary.get('OWNER_VACANCY_CONTRACT_STATUS')}")
    print(f"LIVE_RESTART_RECONSTRUCTED={summary.get('LIVE_RESTART_RECONSTRUCTED')}")
    print(f"GET_PERFORMED={summary.get('GET_PERFORMED')}")
    print(f"WIRE_SEND={summary.get('WIRE_SEND')}")
    print(f"MANIFEST_VERIFY_RC={summary.get('MANIFEST_VERIFY_RC')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
