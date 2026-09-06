"""One-shot runner for §11.14 Live handoff pos producer semantics and contract."""

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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_execute_v1 import (  # noqa: E402
    execute_live_handoff_pos_producer_semantics_and_contract_v1,
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
    result = execute_live_handoff_pos_producer_semantics_and_contract_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_main_sha,
        repo_root=repo_root,
        run_id=CANONICAL_EVIDENCE_RUN_ID,
    )
    pack = Path(result["pack"])
    pack.mkdir(parents=True, exist_ok=True)
    documents = {
        "SUMMARY.json": dict(result["summary"]),
        "POS_PRODUCER_SEMANTICS_AND_CONTRACT.json": dict(result["binding"]),
        "POS_MEANING_CANDIDATE_MATRIX.json": dict(result["meaning_candidates"]),
        "POS_WHAT_RESTART_RECONSTRUCTS.json": dict(result["what_restart_reconstructs"]),
        "POS_UNIT_PROOF.json": dict(result["unit_adjudication"]),
        "POS_SIGN_PROOF.json": dict(result["sign_adjudication"]),
        "POS_ACCOUNT_MODE_PROOF.json": dict(result["account_mode_adjudication"]),
        "POS_PRODUCER_CONTRACT.json": dict(result["producer_contract"]),
        "HANDOFF_SCHEMA_VERSION.json": dict(result["schema_version"]),
        "POS_DOWNSTREAM_EFFECT.json": dict(result["downstream"]),
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
    print(f"POS_SEMANTICS={summary.get('POS_SEMANTICS')}")
    print(f"SELECTED_SEMANTIC_ID={summary.get('SELECTED_SEMANTIC_ID')}")
    print(f"NEW_PRODUCER_CONTRACT_DEFINED={summary.get('NEW_PRODUCER_CONTRACT_DEFINED')}")
    print(f"NEW_PRODUCER_IMPLEMENTED={summary.get('NEW_PRODUCER_IMPLEMENTED')}")
    print(f"IMPLEMENTATION_AUTHORIZED={summary.get('IMPLEMENTATION_AUTHORIZED')}")
    print(f"WIRE_SEND={summary.get('WIRE_SEND')}")
    print(f"LIVE_ACTION={summary.get('LIVE_ACTION')}")
    print(f"MANIFEST_VERIFY_RC={summary.get('MANIFEST_VERIFY_RC')}")
    return 0 if int(summary.get("MANIFEST_VERIFY_RC", 1)) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
