"""P1 exit-criteria proof bundle (contract/schema only; AUTHORITY=NONE)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.authority_contract_v1 import (
    scan_runtime_ab_implementation_v1,
    validate_component_a_authority_contract_v1,
    validate_component_b_authority_contract_v1,
    validate_p1_owner_decision_config_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.constants_v1 import (
    BASELINE_SHA,
    WORKPACKAGE_ID,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.schema_v1 import (
    canonical_schema_manifest_digest_v1,
    canonical_schema_manifest_v1,
)

P1_EVIDENCE_REL: Final[str] = (
    "docs/evidence/master_v2_double_play_evidence_input_plane_p1/p1_proof_bundle_v1.json"
)


def prove_p1_authority_contracts_and_schemas_v1(
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    a = validate_component_a_authority_contract_v1()
    b = validate_component_b_authority_contract_v1()
    owner = validate_p1_owner_decision_config_v1(root)
    runtime_present, runtime_hits = scan_runtime_ab_implementation_v1(root)
    ok = a.ok and b.ok and owner.ok and not runtime_present
    return {
        "schema_version": "master_v2_double_play_evidence_input_plane_p1_proof/v1",
        "workpackage_id": WORKPACKAGE_ID,
        "baseline_sha": BASELINE_SHA,
        "verdict": "PROVEN_COMPLETE" if ok else "FAIL_CLOSED",
        "component_a_authority_contract_ok": a.ok,
        "component_b_authority_contract_ok": b.ok,
        "owner_decision_config_ok": owner.ok,
        "runtime_ab_implementation_detected": runtime_present,
        "runtime_ab_implementation_hits": list(runtime_hits),
        "canonical_schema_manifest_digest": canonical_schema_manifest_digest_v1(),
        "canonical_schema_manifest": canonical_schema_manifest_v1(),
        "failure_codes": sorted(
            set(a.failure_codes) | set(b.failure_codes) | set(owner.failure_codes)
        ),
    }


def write_p1_proof_artifacts_v1(repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[3]
    proof = prove_p1_authority_contracts_and_schemas_v1(root)
    out_dir = root / "docs/evidence/master_v2_double_play_evidence_input_plane_p1"
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "p1_proof_bundle_v1.json"
    target.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "verdict": proof["verdict"],
        "baseline_sha": BASELINE_SHA,
    }
    (out_dir / "SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out_dir
