"""Deterministic research execution runner and artifact writer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    AUTHORITY_SCOPE,
    BASELINE_CANDIDATE_ID,
    CAPABILITY_ID,
    CONCLUSION_SCHEMA_VERSION,
    DEFAULT_INPUT_LEDGER_RELATIVE_PATH,
    DEFAULT_OUTPUT_EVIDENCE_RELATIVE_ROOT,
    EXPECTED_PREREGISTRATION_DIGEST,
    HARD_STOP,
    INTEGRITY_SCHEMA_VERSION,
    NON_AUTHORITY_SCOPE,
    NUMERIC_THRESHOLD_SELECTED,
    PARAMETER_PROMOTED,
    RESEARCH_CONCLUSION_INSUFFICIENT,
    RESEARCH_CONCLUSION_NO_ROBUST,
    RESEARCH_CONCLUSION_REGION_PENDING,
    THRESHOLD_STATUS,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.contracts_v1 import (
    MaxAgeResearchExecutionError,
    assert_candidate_domain_immutable_v1,
    assert_candidates_not_config_authority_v1,
    bind_candidate_domain_v1,
    bind_hypothesis_contract_v1,
    bind_robustness_execution_contract_v1,
    bind_split_and_embargo_contract_v1,
    build_research_execution_manifest_shell_v1,
    verify_preregistration_digest_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evaluator_v1 import (
    apply_rejection_criteria_v1,
    evaluate_all_candidates_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evidence_loader_v1 import (
    ResearchEvidenceRecordV1,
    assert_restore_does_not_invent_estimate_evidence_v1,
    build_input_evidence_manifest_v1,
    coverage_summary_v1,
    empty_input_evidence_manifest_v1,
    load_research_evidence_from_payloads_v1,
    load_research_evidence_records_v1,
    stable_records_fingerprint_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.robustness_v1 import (
    block_bootstrap_confidence_v1,
    final_holdout_matrix_v1,
    monte_carlo_applicability_v1,
    neighborhood_perturbation_v1,
    regime_session_matrices_v1,
    stress_matrices_v1,
    walk_forward_matrix_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.serialization_v1 import (
    build_execution_id_v1,
    canonical_json_dumps,
    digest_excluding_keys,
    sha256_hex,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.split_engine_v1 import (
    build_purged_chronological_splits_v1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    build_ratified_max_age_research_design_contract_v1,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = canonical_json_dumps(dict(payload))
    path.write_text(text + "\n", encoding="utf-8")
    return sha256_hex(dict(payload))


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [canonical_json_dumps(dict(row)) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return sha256_hex({"rows": list(rows)})


def resolve_repository_sha_v1(repo_root: Path, *, repository_sha: Optional[str] = None) -> str:
    if repository_sha:
        return repository_sha
    head = repo_root / ".git" / "HEAD"
    if not head.exists():
        raise MaxAgeResearchExecutionError("repository_sha_unavailable")
    # Prefer explicit caller/git SHA; fallback is non-authoritative for formal runs.
    import subprocess

    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise MaxAgeResearchExecutionError("repository_sha_unavailable")
    return proc.stdout.strip()


def run_max_age_parameter_research_execution_v1(
    *,
    repo_root: Path,
    ledger_path: Optional[Path] = None,
    output_root: Optional[Path] = None,
    repository_sha: Optional[str] = None,
    records: Optional[Sequence[ResearchEvidenceRecordV1]] = None,
    created_at_utc: Optional[str] = None,
) -> dict[str, Any]:
    """Execute non-enforcing max-age parameter research and write evidence artifacts."""
    assert_architecture_guards_v1(repo_root=repo_root)
    created = created_at_utc or _utc_now_iso()
    sha = resolve_repository_sha_v1(repo_root, repository_sha=repository_sha)

    design = build_ratified_max_age_research_design_contract_v1()
    prereg_digest = design.preregistration_digest
    verify_preregistration_digest_v1(prereg_digest)

    # Placeholder execution id for pre-bind artifacts; replaced after digest chain.
    provisional_execution_id = "provisional_pending_digest_chain"
    candidate_domain = bind_candidate_domain_v1(
        repository_sha=sha,
        preregistration_digest=prereg_digest,
        execution_id=provisional_execution_id,
        created_at_utc=created,
    )
    assert_candidates_not_config_authority_v1(candidate_domain.to_dict())
    assert_candidate_domain_immutable_v1(
        candidate_domain,
        attempted_candidates=candidate_domain.candidate_max_age_seconds,
    )
    hypothesis = bind_hypothesis_contract_v1(
        repository_sha=sha,
        preregistration_digest=prereg_digest,
        execution_id=provisional_execution_id,
        created_at_utc=created,
    )
    split_contract = bind_split_and_embargo_contract_v1(
        repository_sha=sha,
        preregistration_digest=prereg_digest,
        execution_id=provisional_execution_id,
        created_at_utc=created,
    )
    robustness_contract = bind_robustness_execution_contract_v1(
        repository_sha=sha,
        preregistration_digest=prereg_digest,
        execution_id=provisional_execution_id,
        created_at_utc=created,
    )

    input_valid = True
    insufficient = False
    load_error: Optional[str] = None
    loaded_records: tuple[ResearchEvidenceRecordV1, ...] = ()

    if records is not None:
        loaded_records = tuple(records)
        input_manifest = build_input_evidence_manifest_v1(
            repository_sha=sha,
            preregistration_digest=prereg_digest,
            execution_id=provisional_execution_id,
            ledger_path=ledger_path,
            records=loaded_records,
            created_at_utc=created,
        )
    else:
        resolved_ledger = ledger_path or (repo_root / DEFAULT_INPUT_LEDGER_RELATIVE_PATH)
        try:
            loaded_records = load_research_evidence_records_v1(resolved_ledger)
            input_manifest = build_input_evidence_manifest_v1(
                repository_sha=sha,
                preregistration_digest=prereg_digest,
                execution_id=provisional_execution_id,
                ledger_path=resolved_ledger,
                records=loaded_records,
                created_at_utc=created,
            )
        except MaxAgeResearchExecutionError as exc:
            input_valid = False
            insufficient = True
            load_error = str(exc)
            input_manifest = empty_input_evidence_manifest_v1(
                repository_sha=sha,
                preregistration_digest=prereg_digest,
                execution_id=provisional_execution_id,
                created_at_utc=created,
                reason=load_error,
            )

    coverage = coverage_summary_v1(loaded_records)
    if not coverage.get("sufficient_for_research"):
        insufficient = True

    execution_id = build_execution_id_v1(
        repository_sha=sha,
        preregistration_digest=prereg_digest,
        candidate_domain_digest=candidate_domain.domain_digest,
        hypothesis_contract_digest=hypothesis.hypothesis_digest,
        split_contract_digest=split_contract.split_digest,
        robustness_contract_digest=robustness_contract.robustness_digest,
        input_evidence_manifest_digest=str(input_manifest["input_evidence_manifest_digest"]),
    )

    # Re-bind contracts with final execution_id (digests of body exclude execution_id?
    # Execution id is IN the body, so rebinding changes digests. Keep provisional digests
    # as identity inputs and stamp final execution_id on output copies.)
    candidate_domain_out = dict(candidate_domain.to_dict())
    candidate_domain_out["execution_id"] = execution_id
    hypothesis_out = dict(hypothesis.to_dict())
    hypothesis_out["execution_id"] = execution_id
    split_out = dict(split_contract.to_dict())
    split_out["execution_id"] = execution_id
    robustness_out = dict(robustness_contract.to_dict())
    robustness_out["execution_id"] = execution_id
    input_manifest_out = dict(input_manifest)
    input_manifest_out["execution_id"] = execution_id

    out_root = output_root or (repo_root / DEFAULT_OUTPUT_EVIDENCE_RELATIVE_ROOT / execution_id)
    out_root.mkdir(parents=True, exist_ok=True)

    artifact_digests: dict[str, str] = {}
    artifact_digests["candidate_domain.json"] = _write_json(
        out_root / "candidate_domain.json", candidate_domain_out
    )
    artifact_digests["hypothesis_contract.json"] = _write_json(
        out_root / "hypothesis_contract.json", hypothesis_out
    )
    artifact_digests["split_and_embargo_contract.json"] = _write_json(
        out_root / "split_and_embargo_contract.json", split_out
    )
    artifact_digests["robustness_execution_contract.json"] = _write_json(
        out_root / "robustness_execution_contract.json", robustness_out
    )
    artifact_digests["input_evidence_manifest.json"] = _write_json(
        out_root / "input_evidence_manifest.json", input_manifest_out
    )

    status = "BLOCKED" if insufficient or not input_valid else "PASS"
    candidate_results: list[dict[str, Any]] = []
    walk_forward: dict[str, Any] = {"executed": False}
    holdout: dict[str, Any] = {"executed": False}
    regime_results: dict[str, Any] = {"executed": False}
    session_results: dict[str, Any] = {"executed": False}
    robustness_results: dict[str, Any] = {"executed": False}
    rejection_rows: list[dict[str, Any]] = []
    research_conclusion = RESEARCH_CONCLUSION_INSUFFICIENT
    robust_region: Optional[list[int]] = None
    deterministic_reexec_pass = False
    ledger_resume_pass = False
    monte_carlo = {"executed": False, "monte_carlo_not_applicable_reason": "NOT_RUN"}

    if not insufficient and loaded_records:
        # Ledger reload / resume equivalence
        if ledger_path is not None and Path(ledger_path).exists():
            reloaded = load_research_evidence_records_v1(Path(ledger_path))
            assert_restore_does_not_invent_estimate_evidence_v1(
                before=loaded_records, after=reloaded
            )
            ledger_resume_pass = stable_records_fingerprint_v1(
                loaded_records
            ) == stable_records_fingerprint_v1(reloaded)
        else:
            # In-memory path: reload via payloads must be identical.
            payloads = [r.raw for r in loaded_records]
            reloaded = load_research_evidence_from_payloads_v1(payloads)
            assert_restore_does_not_invent_estimate_evidence_v1(
                before=loaded_records, after=reloaded
            )
            ledger_resume_pass = stable_records_fingerprint_v1(
                loaded_records
            ) == stable_records_fingerprint_v1(reloaded)

        sealed = build_purged_chronological_splits_v1(
            loaded_records,
            split_contract=split_contract,
            access_holdout=False,
        )
        researchable = sealed.train + sealed.validation
        candidate_results = evaluate_all_candidates_v1(
            researchable,
            candidate_max_age_seconds=candidate_domain.candidate_max_age_seconds,
        )
        # Deterministic re-execution check
        candidate_results_2 = evaluate_all_candidates_v1(
            researchable,
            candidate_max_age_seconds=candidate_domain.candidate_max_age_seconds,
        )
        deterministic_reexec_pass = candidate_results == candidate_results_2

        walk_forward = walk_forward_matrix_v1(
            loaded_records,
            split_contract=split_contract,
            candidate_seconds=candidate_domain.candidate_max_age_seconds,
        )
        holdout = final_holdout_matrix_v1(
            sealed,
            candidate_seconds=candidate_domain.candidate_max_age_seconds,
        )
        regime_results, session_results = regime_session_matrices_v1(
            researchable,
            candidate_seconds=candidate_domain.candidate_max_age_seconds,
        )
        neighborhood = neighborhood_perturbation_v1(
            researchable,
            candidate_seconds=candidate_domain.candidate_max_age_seconds,
        )
        bootstrap = block_bootstrap_confidence_v1(
            researchable,
            candidate_seconds=candidate_domain.candidate_max_age_seconds,
            repetitions=robustness_contract.bootstrap_repetitions,
            block_seconds=robustness_contract.bootstrap_block_seconds,
            seed=robustness_contract.bootstrap_seed,
        )
        stresses = stress_matrices_v1(
            researchable,
            candidate_seconds=candidate_domain.candidate_max_age_seconds,
        )
        monte_carlo = monte_carlo_applicability_v1(loaded_records)
        robustness_results = {
            "executed": True,
            "neighborhood_perturbation": neighborhood,
            "block_bootstrap": bootstrap,
            "stress": stresses,
            "monte_carlo": monte_carlo,
            "restart_resume_consistency": {
                "executed": True,
                "ledger_resume_equivalence_pass": ledger_resume_pass,
            },
            "ledger_reload_consistency": {
                "executed": True,
                "pass": ledger_resume_pass,
            },
        }

        baseline = next(r for r in candidate_results if r["candidate_id"] == BASELINE_CANDIDATE_ID)
        wf_stability = walk_forward.get("walk_forward_stability")
        accepted_region: list[int] = []
        for result in candidate_results:
            if result["candidate_id"] == BASELINE_CANDIDATE_ID:
                continue
            seconds = int(result["candidate_max_age_seconds_argument"])
            cand_id = result["candidate_id"]
            neigh = neighborhood.get("results", {}).get(cand_id, {}).get("neighborhood_sensitivity")
            holdout_row = holdout.get("results", {}).get(cand_id, {})
            baseline_holdout = holdout.get("results", {}).get(BASELINE_CANDIDATE_ID, {})
            holdout_degraded = False
            if holdout_row and baseline_holdout:
                holdout_degraded = float(holdout_row.get("decision_coverage") or 0.0) < (
                    float(baseline_holdout.get("decision_coverage") or 0.0) - 0.25
                )
            regime_slices = regime_results.get("slices", {})
            session_slices = session_results.get("slices", {})
            single_regime = len(regime_slices) <= 1
            single_session = len(session_slices) <= 1
            rejection = apply_rejection_criteria_v1(
                result,
                baseline_result=baseline,
                walk_forward_stability=(None if wf_stability is None else float(wf_stability)),
                neighborhood_sensitivity=None if neigh is None else float(neigh),
                holdout_degraded=holdout_degraded,
                single_session_only=single_session,
                single_regime_only=single_regime,
                leakage_or_digest_violation=False,
                restart_ledger_nondeterminism=not ledger_resume_pass,
            )
            rejection_rows.append(rejection)
            result["threshold_boundary_sensitivity"] = neigh
            result["walk_forward_stability"] = wf_stability
            result["final_holdout_result"] = {
                "decision_coverage": holdout_row.get("decision_coverage"),
                "evidence_count": holdout_row.get("evidence_count"),
            }
            result["parameter_stability"] = {
                "rejected": rejection["rejected"],
                "rejection_reasons": rejection["rejection_reasons"],
            }
            if not rejection["rejected"]:
                # Region membership requires non-worse stale exposure vs very open thresholds
                # without catastrophic coverage loss — still not a selection.
                if float(result.get("stale_rejection_rate") or 0.0) > 0.0:
                    accepted_region.append(seconds)

        # Contiguous robust region only; never promote a point threshold.
        if accepted_region:
            accepted_region = sorted(set(accepted_region))
            # Keep only contiguous runs; pick longest contiguous block as non-binding region.
            runs: list[list[int]] = []
            current: list[int] = []
            cand_set = list(candidate_domain.candidate_max_age_seconds)
            for value in cand_set:
                if value in accepted_region:
                    current.append(value)
                elif current:
                    runs.append(current)
                    current = []
            if current:
                runs.append(current)
            if runs:
                robust_region = max(runs, key=len)
                research_conclusion = RESEARCH_CONCLUSION_REGION_PENDING
            else:
                research_conclusion = RESEARCH_CONCLUSION_NO_ROBUST
        else:
            research_conclusion = RESEARCH_CONCLUSION_NO_ROBUST
            robust_region = None
    else:
        research_conclusion = RESEARCH_CONCLUSION_INSUFFICIENT
        status = "BLOCKED"

    conclusion = {
        "schema_version": CONCLUSION_SCHEMA_VERSION,
        "repository_sha": sha,
        "preregistration_digest": prereg_digest,
        "execution_id": execution_id,
        "created_at_utc": created,
        "authority_scope": AUTHORITY_SCOPE,
        "non_authority_scope": NON_AUTHORITY_SCOPE,
        "status": status,
        "research_conclusion": research_conclusion,
        "robust_candidate_region_identified": bool(robust_region),
        "robust_candidate_region": robust_region,
        "no_robust_numeric_max_age_established": research_conclusion
        in {RESEARCH_CONCLUSION_NO_ROBUST, RESEARCH_CONCLUSION_INSUFFICIENT},
        "insufficient_research_evidence": insufficient,
        "input_evidence_valid": input_valid,
        "load_error": load_error,
        "threshold_status": THRESHOLD_STATUS,
        "numeric_max_age_decided": False,
        "numeric_threshold_selected": NUMERIC_THRESHOLD_SELECTED,
        "parameter_promoted": PARAMETER_PROMOTED,
        "enforcement_applied": False,
        "alpha_mutation_occurred": False,
        "recommended_single_threshold": None,
        "hard_stop": HARD_STOP,
        "rejection_matrix": rejection_rows,
    }
    # Hard guarantee: conclusion cannot promote a threshold.
    if conclusion["numeric_threshold_selected"] or conclusion["parameter_promoted"]:
        raise MaxAgeResearchExecutionError("research_conclusion_must_not_promote_threshold")
    if conclusion.get("recommended_single_threshold") is not None:
        raise MaxAgeResearchExecutionError("research_conclusion_must_not_select_threshold")
    conclusion["conclusion_digest"] = digest_excluding_keys(
        conclusion, exclude={"conclusion_digest"}
    )

    artifact_digests["candidate_results.jsonl"] = _write_jsonl(
        out_root / "candidate_results.jsonl", candidate_results
    )
    artifact_digests["walk_forward_results.json"] = _write_json(
        out_root / "walk_forward_results.json", walk_forward
    )
    artifact_digests["holdout_results.json"] = _write_json(
        out_root / "holdout_results.json", holdout
    )
    artifact_digests["regime_results.json"] = _write_json(
        out_root / "regime_results.json", regime_results
    )
    artifact_digests["session_results.json"] = _write_json(
        out_root / "session_results.json", session_results
    )
    artifact_digests["robustness_results.json"] = _write_json(
        out_root / "robustness_results.json", robustness_results
    )
    artifact_digests["research_conclusion.json"] = _write_json(
        out_root / "research_conclusion.json", conclusion
    )

    manifest = build_research_execution_manifest_shell_v1(
        repository_sha=sha,
        preregistration_digest=prereg_digest,
        execution_id=execution_id,
        candidate_domain_digest=candidate_domain.domain_digest,
        hypothesis_contract_digest=hypothesis.hypothesis_digest,
        split_contract_digest=split_contract.split_digest,
        robustness_contract_digest=robustness_contract.robustness_digest,
        input_evidence_manifest_digest=str(input_manifest["input_evidence_manifest_digest"]),
        created_at_utc=created,
    )
    manifest["status"] = status
    manifest["research_conclusion"] = research_conclusion
    manifest["output_evidence_path"] = str(out_root)
    manifest["artifact_relative_paths"] = sorted(artifact_digests.keys()) + [
        "research_execution_manifest.json",
        "integrity_manifest.json",
    ]
    manifest["manifest_digest"] = digest_excluding_keys(manifest, exclude={"manifest_digest"})
    artifact_digests["research_execution_manifest.json"] = _write_json(
        out_root / "research_execution_manifest.json", manifest
    )

    integrity = {
        "schema_version": INTEGRITY_SCHEMA_VERSION,
        "repository_sha": sha,
        "preregistration_digest": prereg_digest,
        "execution_id": execution_id,
        "created_at_utc": created,
        "authority_scope": AUTHORITY_SCOPE,
        "non_authority_scope": NON_AUTHORITY_SCOPE,
        "artifacts": [
            {
                "relative_path": name,
                "sha256": digest,
                "schema_version_hint": CAPABILITY_ID,
                "execution_id": execution_id,
                "repository_sha": sha,
                "preregistration_digest": prereg_digest,
            }
            for name, digest in sorted(artifact_digests.items())
        ],
        "deterministic_reexecution_pass": deterministic_reexec_pass,
        "ledger_resume_equivalence_pass": ledger_resume_pass,
        "expected_preregistration_digest": EXPECTED_PREREGISTRATION_DIGEST,
        "preregistration_digest_match": prereg_digest == EXPECTED_PREREGISTRATION_DIGEST,
    }
    integrity["integrity_digest"] = digest_excluding_keys(integrity, exclude={"integrity_digest"})
    artifact_digests["integrity_manifest.json"] = _write_json(
        out_root / "integrity_manifest.json", integrity
    )
    # Rewrite integrity with self-inclusion of final digest map.
    integrity["artifacts"] = [
        {
            "relative_path": name,
            "sha256": digest,
            "schema_version_hint": CAPABILITY_ID,
            "execution_id": execution_id,
            "repository_sha": sha,
            "preregistration_digest": prereg_digest,
        }
        for name, digest in sorted(artifact_digests.items())
    ]
    integrity["integrity_digest"] = digest_excluding_keys(integrity, exclude={"integrity_digest"})
    _write_json(out_root / "integrity_manifest.json", integrity)

    return {
        "status": status,
        "execution_id": execution_id,
        "repository_sha": sha,
        "preregistration_digest": prereg_digest,
        "preregistration_digest_match": prereg_digest == EXPECTED_PREREGISTRATION_DIGEST,
        "candidate_domain_digest": candidate_domain.domain_digest,
        "hypothesis_contract_digest": hypothesis.hypothesis_digest,
        "split_contract_digest": split_contract.split_digest,
        "robustness_contract_digest": robustness_contract.robustness_digest,
        "input_evidence_manifest_digest": input_manifest["input_evidence_manifest_digest"],
        "output_evidence_path": str(out_root),
        "coverage": coverage,
        "input_evidence_valid": input_valid,
        "insufficient_research_evidence": insufficient,
        "research_conclusion": research_conclusion,
        "robust_candidate_region": robust_region,
        "walk_forward_executed": bool(walk_forward.get("executed")),
        "final_holdout_executed": bool(holdout.get("executed")),
        "regime_slices_executed": bool(regime_results.get("executed")),
        "session_slices_executed": bool(session_results.get("executed")),
        "parameter_perturbation_executed": bool(
            robustness_results.get("neighborhood_perturbation", {}).get("executed")
        ),
        "bootstrap_executed": bool(robustness_results.get("block_bootstrap", {}).get("executed")),
        "monte_carlo_executed": bool(monte_carlo.get("executed")),
        "monte_carlo_not_applicable_reason": monte_carlo.get("monte_carlo_not_applicable_reason"),
        "deterministic_reexecution_pass": deterministic_reexec_pass,
        "ledger_resume_equivalence_pass": ledger_resume_pass,
        "artifact_digests": artifact_digests,
        "numeric_threshold_selected": False,
        "parameter_promoted": False,
        "enforcement_applied": False,
        "threshold_status": THRESHOLD_STATUS,
        "hard_stop": HARD_STOP,
        "candidate_results": candidate_results,
        "rejection_matrix": rejection_rows,
        "conclusion": conclusion,
    }


def dumps_summary_v1(result: Mapping[str, Any]) -> str:
    return json.dumps(dict(result), sort_keys=True, indent=2, default=str)
