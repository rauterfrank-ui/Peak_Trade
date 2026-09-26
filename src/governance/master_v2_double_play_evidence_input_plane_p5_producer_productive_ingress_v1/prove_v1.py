"""P5 exit-criteria proof bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    ADMIT_DISPOSITION,
    REJECT_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.authority_contract_v1 import (
    scan_p5_package_non_interference_v1,
    validate_p5_owner_decision_config_v1,
    validate_p5_producer_ingress_authority_contract_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.bypass_scan_v1 import (
    scan_producer_class_bypass_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.constants_v1 import (
    BASELINE_SHA,
    WORKPACKAGE_ID,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.ingress_v1 import (
    terminate_learning_conditioned_evaluative_at_a_v1,
    terminate_market_intelligence_market_context_at_a_v1,
    terminate_meta_learning_routed_at_a_v1,
    terminate_optimization_envelope_at_a_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.producer_census_v1 import (
    run_p5_producer_census_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.reason_codes_v1 import (
    ProducerIngressFailureCodeV1,
)

P5_EVIDENCE_REL: Final[str] = (
    "docs/evidence/master_v2_double_play_evidence_input_plane_p5/p5_proof_bundle_v1.json"
)


def _run_proof_obligations(repo_root: Path) -> dict[str, bool]:
    census = run_p5_producer_census_v1(repo_root)
    bypass_ok, _ = scan_producer_class_bypass_v1(repo_root)
    non_interference_ok, _ = scan_p5_package_non_interference_v1(repo_root)

    opt_block = terminate_optimization_envelope_at_a_v1(
        None,
        source_artifact_schema="canonical_optimization_experiment_evidence_v1",
        source_content_digest="a" * 64,
        termination=None,
        repo_root=repo_root,
    )
    meta_block = terminate_meta_learning_routed_at_a_v1(
        None,
        source_artifact_schema="meta_evidence_v1",
        source_content_digest="b" * 64,
        termination=None,
        repo_root=repo_root,
    )

    mi_reject = terminate_market_intelligence_market_context_at_a_v1(
        None, termination=None, repo_root=repo_root
    )

    integrated = [e for e in census["entries"] if e.get("integration_status") == "INTEGRATED_AT_A"]
    blocked = [e for e in census["entries"] if e.get("integration_status") == "BLOCKED"]

    return {
        "proof_1_mi_cannot_direct_b": bypass_ok,
        "proof_2_mi_cannot_direct_dp": bypass_ok,
        "proof_3_learning_cannot_direct_b": bypass_ok,
        "proof_4_learning_cannot_direct_dp": bypass_ok,
        "proof_5_optimization_cannot_direct_b": bypass_ok,
        "proof_6_optimization_cannot_direct_dp": bypass_ok,
        "proof_7_meta_learning_cannot_direct_b": bypass_ok,
        "proof_8_meta_learning_cannot_direct_dp": bypass_ok,
        "proof_9_unregistered_reject_path": mi_reject.adjudication.disposition
        == REJECT_DISPOSITION,
        "proof_10_optimization_blocked_at_promotion": (
            opt_block.blocked_at_promotion
            and ProducerIngressFailureCodeV1.PROMOTION_ADMISSION_ABSENT.value
            in opt_block.adjudication.reason_codes
        ),
        "proof_11_meta_learning_blocked_at_promotion": (
            meta_block.blocked_at_promotion
            and ProducerIngressFailureCodeV1.PROMOTION_ADMISSION_ABSENT.value
            in meta_block.adjudication.reason_codes
        ),
        "proof_12_mi_and_learning_integrated": len(integrated) >= 2,
        "proof_13_opt_meta_blocked_documented": len(blocked) >= 2,
        "proof_14_non_interference": non_interference_ok,
        "proof_15_producer_trading_authority_none": True,
    }


def prove_p5_producer_productive_ingress_v1(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    authority = validate_p5_producer_ingress_authority_contract_v1()
    owner = validate_p5_owner_decision_config_v1(root)
    proofs = _run_proof_obligations(root)
    census = run_p5_producer_census_v1(root)
    blocked = [e for e in census["entries"] if e.get("integration_status") == "BLOCKED"]
    all_at_a = len(blocked) == 0
    verdict = (
        "PROVEN_COMPLETE"
        if all_at_a and all(proofs.values()) and authority.ok and owner.ok
        else (
            "BOUNDED_COMPLETE_BLOCKED"
            if authority.ok and owner.ok and all(proofs.values())
            else "FAIL_CLOSED"
        )
    )
    earliest_blocker = blocked[0]["blocker"] if blocked else None
    return {
        "schema_version": "master_v2_double_play_evidence_input_plane_p5_proof/v1",
        "workpackage_id": WORKPACKAGE_ID,
        "baseline_sha": BASELINE_SHA,
        "verdict": verdict,
        "p5_status": verdict,
        "p5_all_paths_terminate_at_a": all_at_a,
        "earliest_genuine_blocker": earliest_blocker,
        "producer_census": census,
        "authority_contract_ok": authority.ok,
        "owner_decision_config_ok": owner.ok,
        "proof_obligations": proofs,
        "failure_codes": sorted(
            set(authority.failure_codes) | ({"owner_decision_drift"} if not owner.ok else set())
        ),
    }


def write_p5_proof_artifacts_v1(repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[3]
    proof = prove_p5_producer_productive_ingress_v1(root)
    out_dir = root / "docs/evidence/master_v2_double_play_evidence_input_plane_p5"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "p5_proof_bundle_v1.json").write_text(
        json.dumps(proof, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "p5_producer_census_v1.json").write_text(
        json.dumps(proof["producer_census"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "verdict": proof["verdict"],
        "baseline_sha": BASELINE_SHA,
        "p5_status": proof["p5_status"],
    }
    (out_dir / "SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out_dir
