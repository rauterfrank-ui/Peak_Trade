"""Final Research Fleet Class D versioned bindings and offline evaluation scope v0.

Deterministic, fail-closed materialization of NEW versioned bindings for
trend_following/v1, bollinger_bands/v1, and momentum_1h/v1 bound to the
extended_chronological_v1 panel, plus bounded offline-only economic evaluation
scope ratification. No economic evaluation execution, no runtime or order effect.

Operator ratification: RATIFICATION_CLASS=D / NEW_VERSIONED_RESEARCH_SCOPE
ECONOMIC_EVALUATION_AUTHORIZED=false for all candidates in this scope.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
    FLEET_ID,
    FLEET_VERSION,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
    FAILED_HISTORICAL_CANDIDATES,
    canonical_candidate_identifier,
    compute_binding_semantic_digest_v0,
    compute_completion_digest_v0,
)
from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
    AUTHORITY_EFFECT,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    FUTURES_ONLY,
    BITCOIN_DIRECTION_ALLOWED,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    SPOT_ALLOWED,
    SYNTHETIC_SPOT_ALLOWED,
    ValidationVerdict,
    _load_period_policy,
    build_runtime_step31f_config_v0,
    compute_funding_coverage_report_v0,
    load_panel_member_binding_v0,
    load_scope_config_v0,
    materialize_binding_completion_v0,
    materialize_narrow_evaluation_dataset_v0,
    resolve_staging_root,
    validate_binding_completion_v0,
)

PACKAGE_MARKER = (
    "FINAL_RESEARCH_FLEET_CLASS_D_VERSIONED_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0=true"
)

SCHEMA_VERSION = (
    "final_research_fleet_class_d_versioned_bindings_and_offline_economic_evaluation_scope.v0"
)
COMPLETION_ID = "final_research_fleet_class_d_versioned_binding_completion_v0"
SCOPE_RATIFICATION_ID = (
    "final_research_fleet_class_d_offline_economic_evaluation_scope_ratification_v0"
)
OPERATOR_RATIFICATION_ID = "final_research_fleet_class_d_operator_ratification_v0"
CONFIG_REL_PATH = (
    "config/research/final_research_fleet_class_d_versioned_binding_completion_v0.json"
)
SCOPE_CONFIG_REL_PATH = "config/research/final_research_fleet_class_d_offline_economic_evaluation_scope_ratification_v0.json"
OPERATOR_RATIFICATION_CONFIG_REL_PATH = (
    "config/research/final_research_fleet_class_d_operator_ratification_v0.json"
)
CANONICAL_SERIALIZATION_VERSION = "research_binding_completion_canonical_json_v1"

GO_TOKEN = (
    "GO_BOUNDED_FINAL_RESEARCH_FLEET_CLASS_D_VERSIONED_BINDINGS_AND_"
    "OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0"
)
SCOPE_CLASSIFICATION = (
    "BOUNDED_FINAL_RESEARCH_FLEET_CLASS_D_VERSIONED_BINDINGS_AND_"
    "OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0"
)
RATIFIED_SCOPE_ID = (
    "FINAL_RESEARCH_FLEET_VERSIONED_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0"
)
RATIFICATION_CLASS = "D"
RATIFICATION_CLASS_NAME = "NEW_VERSIONED_RESEARCH_SCOPE"
OPERATOR_RATIFICATION_REF = "final_research_fleet_class_d_operator_ratification_v0_20260704T205300Z"
HISTORICAL_BLOCKED_COMPLETION_DIGEST = (
    "161d834e5153df78a0013b6e55c4c8bd4788c775811e3678f025104a307d78f1"
)

ECONOMIC_EVALUATION_AUTHORIZED = False
ECONOMIC_EVALUATION_EXECUTED = False
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS = False
RUNTIME_REWIRE_ADMISSIBLE = False
OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED = True
FINAL_RESEARCH_FLEET_BINDING_READY = True

REASON_HISTORICAL_BINDING_RETRY_BLOCKED = "FAIL_CLOSED_HISTORICAL_BINDING_RETRY_BLOCKED"
REASON_EVALUATION_AUTHORIZED_TRUE = "FAIL_CLOSED_ECONOMIC_EVALUATION_AUTHORIZED_MUST_BE_FALSE"
REASON_STAGING_MISSING = "STAGING_MISSING"
REASON_FUNDING_COVERAGE_INCOMPLETE = "FAIL_CLOSED_DATASET_OR_FUNDING_COVERAGE_INCOMPLETE"


def _verify_panel_preconditions_v0(*, staging_root: Path) -> tuple[bool, tuple[str, ...], Any, Any]:
    reasons: list[str] = []
    panel_binding = None
    coverage = compute_funding_coverage_report_v0(staging_root)
    if not staging_root.is_dir():
        reasons.append(REASON_STAGING_MISSING)
    else:
        try:
            panel_binding = load_panel_member_binding_v0(staging_root)
        except FileNotFoundError as exc:
            reasons.append(str(exc))
        if coverage.coverage_ratio < 1.0 or coverage.missing_funding_count > 0:
            reasons.append(REASON_FUNDING_COVERAGE_INCOMPLETE)
    if panel_binding is None and REASON_STAGING_MISSING not in reasons:
        reasons.append(REASON_STAGING_MISSING)
    return not reasons, tuple(reasons), panel_binding, coverage


class ValidationVerdictEnum(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class ScopeMaterializationResultV0:
    binding_completion: dict[str, Any]
    scope_ratification: dict[str, Any]
    operator_ratification: dict[str, Any]
    evidence_root: Path
    manifest_verify_rc: int


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def materialize_operator_ratification_record_v0(*, repo_head_sha: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "ratification_id": OPERATOR_RATIFICATION_ID,
        "ratification_status": "RATIFIED_BY_OPERATOR",
        "ratification_class": RATIFICATION_CLASS,
        "ratification_class_name": RATIFICATION_CLASS_NAME,
        "ratified_scope_id": RATIFIED_SCOPE_ID,
        "operator_ratification_ref": OPERATOR_RATIFICATION_REF,
        "final_research_fleet": "trend_following,bollinger_bands,momentum_1h",
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "runtime_rewire_admissible": RUNTIME_REWIRE_ADMISSIBLE,
        "live_authorized": False,
        "historical_blocked_completion_digest": HISTORICAL_BLOCKED_COMPLETION_DIGEST,
        "repo_head_binding": repo_head_sha,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "generated_at_utc": _utc_now_z(),
    }


def _apply_class_d_binding_policy(completion: Mapping[str, Any]) -> dict[str, Any]:
    patched = deepcopy(dict(completion))
    patched["schema_version"] = SCHEMA_VERSION
    patched["completion_id"] = COMPLETION_ID
    patched["scope_classification"] = SCOPE_CLASSIFICATION
    patched["operator_ratification_ref"] = OPERATOR_RATIFICATION_REF
    patched["ratified_scope_id"] = RATIFIED_SCOPE_ID
    patched["ratification_class"] = RATIFICATION_CLASS
    patched["economic_evaluation_authorized"] = ECONOMIC_EVALUATION_AUTHORIZED
    patched["economic_evaluation_executed"] = ECONOMIC_EVALUATION_EXECUTED
    patched["runtime_rewire_admissible"] = RUNTIME_REWIRE_ADMISSIBLE
    patched["historical_blocked_completion_digest"] = HISTORICAL_BLOCKED_COMPLETION_DIGEST
    patched["binding_materialization_status"] = BINDING_STATUS_READY_FOR_EVAL_RATIFICATION
    patched.pop("go_token_consumed", None)
    patched.pop("expected_origin_main_sha", None)
    candidates = patched.get("candidates")
    if isinstance(candidates, list):
        for candidate in candidates:
            if isinstance(candidate, Mapping):
                candidate_dict = dict(candidate)
                candidate_dict["economic_evaluation_authorized"] = ECONOMIC_EVALUATION_AUTHORIZED
                candidate_dict["operator_ratification_ref"] = OPERATOR_RATIFICATION_REF
                candidate_dict["binding_semantic_digest"] = compute_binding_semantic_digest_v0(
                    candidate_dict
                )
                candidate.update(candidate_dict)
    patched["completion_digest"] = compute_completion_digest_v0(patched)
    return patched


def validate_class_d_binding_completion_v0(
    completion: Any,
    *,
    repo_root: Path,
) -> tuple[ValidationVerdictEnum, tuple[str, ...]]:
    reasons: list[str] = []
    if not isinstance(completion, Mapping):
        return ValidationVerdictEnum.REJECTED, ("COMPLETION_NOT_OBJECT",)
    if completion.get("schema_version") != SCHEMA_VERSION:
        reasons.append("UNKNOWN_SCHEMA_VERSION")
    if completion.get("completion_id") != COMPLETION_ID:
        reasons.append("UNKNOWN_COMPLETION_ID")
    if completion.get("ratified_scope_id") != RATIFIED_SCOPE_ID:
        reasons.append("RATIFIED_SCOPE_ID_MISMATCH")
    if completion.get("ratification_class") != RATIFICATION_CLASS:
        reasons.append("RATIFICATION_CLASS_MISMATCH")
    if completion.get("economic_evaluation_authorized") is not False:
        reasons.append(REASON_EVALUATION_AUTHORIZED_TRUE)
    if str(completion.get("completion_digest", "")) == HISTORICAL_BLOCKED_COMPLETION_DIGEST:
        reasons.append(REASON_HISTORICAL_BINDING_RETRY_BLOCKED)
    expected_ids = {canonical_candidate_identifier(s, v) for s, v in FLEET_CANDIDATES}
    seen: set[str] = set()
    candidates = completion.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != len(FLEET_CANDIDATES):
        reasons.append("MISSING_CANDIDATES")
        candidates = candidates or []
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            reasons.append("CANDIDATE_NOT_OBJECT")
            continue
        ref = str(candidate.get("canonical_candidate_identifier", ""))
        seen.add(ref)
        if candidate.get("economic_evaluation_authorized") is not False:
            reasons.append(f"{REASON_EVALUATION_AUTHORIZED_TRUE}:{ref}")
        for digest_field in ("implementation_digest", "config_digest", "data_digest"):
            if not candidate.get(digest_field):
                reasons.append(f"MISSING_DIGEST:{digest_field}:{ref}")
        expected_semantic = compute_binding_semantic_digest_v0(candidate)
        if str(candidate.get("binding_semantic_digest", "")) != expected_semantic:
            reasons.append(f"BINDING_SEMANTIC_DIGEST_MISMATCH:{ref}")
    if seen != expected_ids:
        reasons.extend(sorted(expected_ids - seen))
    expected_completion_digest = compute_completion_digest_v0(completion)
    if str(completion.get("completion_digest", "")) != expected_completion_digest:
        reasons.append("COMPLETION_DIGEST_MISMATCH")
    _ = repo_root
    verdict = ValidationVerdictEnum.ACCEPTED if not reasons else ValidationVerdictEnum.REJECTED
    return verdict, tuple(reasons)


def materialize_scope_ratification_v0(
    *,
    binding_completion: Mapping[str, Any],
) -> dict[str, Any]:
    candidates = list(binding_completion["candidates"])
    first = candidates[0]
    ratification = {
        "schema_version": SCHEMA_VERSION,
        "ratification_id": SCOPE_RATIFICATION_ID,
        "ratification_version": "v0",
        "scope_classification": SCOPE_CLASSIFICATION,
        "ratified_scope_id": RATIFIED_SCOPE_ID,
        "ratification_class": RATIFICATION_CLASS,
        "ratification_class_name": RATIFICATION_CLASS_NAME,
        "operator_ratification_ref": OPERATOR_RATIFICATION_REF,
        "fleet_binding_ref": {
            "completion_id": COMPLETION_ID,
            "completion_digest": binding_completion["completion_digest"],
            "fleet_id": FLEET_ID,
            "fleet_version": FLEET_VERSION,
            "schema_version": binding_completion.get("schema_version"),
        },
        "fleet_binding_digest": binding_completion["completion_digest"],
        "candidate_refs": [str(c["canonical_candidate_identifier"]) for c in candidates],
        "candidate_binding_digests": {
            str(c["canonical_candidate_identifier"]): str(c["binding_semantic_digest"])
            for c in candidates
        },
        "common_dataset_policy_ref": dict(first["dataset_binding"]),
        "common_period_policy_ref": dict(first["period_binding"]),
        "common_instrument_policy_ref": dict(first["instrument_binding"]),
        "fee_model_binding": dict(first["fee_model_binding"]),
        "slippage_model_binding": dict(first["slippage_model_binding"]),
        "funding_model_binding": dict(first["funding_model_binding"]),
        "execution_model_binding": dict(first["execution_model_binding"]),
        "economic_policy_binding": dict(first["economic_policy_binding"]),
        "economic_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "final_research_fleet_binding_ready": FINAL_RESEARCH_FLEET_BINDING_READY,
        "offline_economic_evaluation_scope_ratified": OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "economic_validity_offline_gate_pass": ECONOMIC_VALIDITY_OFFLINE_GATE_PASS,
        "runtime_rewire_admissible": RUNTIME_REWIRE_ADMISSIBLE,
        "evaluation_authorization_status": "NOT_AUTHORIZED_PENDING_SEPARATE_OFFLINE_EXECUTION_GO",
        "evaluation_execution_performed": False,
        "evaluation_modules_invoked": [],
        "allowed_after_this_ratification": False,
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
        "order_effect": ORDER_EFFECT,
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "spot_allowed": SPOT_ALLOWED,
        "synthetic_spot_allowed": SYNTHETIC_SPOT_ALLOWED,
        "historical_blocked_completion_digest": HISTORICAL_BLOCKED_COMPLETION_DIGEST,
        "prohibited_actions": [
            "ECONOMIC_EVALUATION_EXECUTION",
            "BACKTEST_EXECUTION",
            "WALK_FORWARD_EXECUTION",
            "MONTE_CARLO_EXECUTION",
            "STRESS_EXECUTION",
            "PARAMETER_SENSITIVITY_EXECUTION",
            "RUNTIME_REWIRE",
            "RUNTIME",
            "SCHEDULER",
            "SHADOW",
            "PAPER",
            "TESTNET",
            "CANARY",
            "LIVE",
            "FAILED_BINDING_RETRY",
            "POLICY_THRESHOLD_RETROFIT",
        ],
        "excluded_failed_historical_candidates": [
            {"strategy_id": sid, "strategy_version": ver, "retry_forbidden": True}
            for sid, ver in FAILED_HISTORICAL_CANDIDATES
        ],
        "implementation_digest": _stable_digest({"module": __name__}),
        "ratification_digest": _stable_digest(
            {
                "completion_digest": binding_completion["completion_digest"],
                "scope_classification": SCOPE_CLASSIFICATION,
                "ratified_scope_id": RATIFIED_SCOPE_ID,
                "ratification_class": RATIFICATION_CLASS,
                "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
            }
        ),
    }
    return ratification


def write_repo_artifacts_v0(
    *,
    repo_root: Path,
    binding_completion: Mapping[str, Any],
    scope_ratification: Mapping[str, Any],
    operator_ratification: Mapping[str, Any],
) -> tuple[Path, Path, Path]:
    binding_path = repo_root / CONFIG_REL_PATH
    scope_path = repo_root / SCOPE_CONFIG_REL_PATH
    operator_path = repo_root / OPERATOR_RATIFICATION_CONFIG_REL_PATH
    for path in (binding_path, scope_path, operator_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    binding_path.write_text(
        json.dumps(binding_completion, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    scope_path.write_text(
        json.dumps(scope_ratification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    operator_path.write_text(
        json.dumps(operator_ratification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return binding_path, scope_path, operator_path


def run_class_d_binding_materialization_v0(
    *,
    confirm: str,
    repo_root: Path,
    durable_evidence_root: Path,
    repo_head_sha: str,
    write_repo_config: bool = True,
) -> ScopeMaterializationResultV0:
    if confirm != GO_TOKEN:
        raise ValueError(f"GO_TOKEN_INVALID:{confirm}")

    scope_config = load_scope_config_v0(repo_root)
    staging_root = resolve_staging_root(
        durable_archive_root=durable_evidence_root,
        scope_config=scope_config,
    )
    ok, reasons, panel_binding, coverage = _verify_panel_preconditions_v0(
        staging_root=staging_root,
    )
    if not ok:
        raise ValueError(f"PRECONDITION_FAILED:{reasons}")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_root = (
        durable_evidence_root
        / "implementation"
        / f"bounded_final_research_fleet_class_d_versioned_bindings_and_offline_evaluation_scope_v0_{ts_slug}"
    )
    evidence_root.mkdir(parents=True, exist_ok=True)

    narrow_root = evidence_root / "narrow_evaluation_dataset" / "inst-eth-usdt-perp" / "v1"
    period_policy = _load_period_policy(repo_root)
    narrow_dataset = materialize_narrow_evaluation_dataset_v0(
        staging_root=staging_root,
        output_root=narrow_root,
        period_policy=period_policy,
    )

    runtime_config_paths: dict[str, Path] = {}
    config_dir = evidence_root / "RUNTIME_STEP31F_CONFIGS"
    for strategy_id, _strategy_version in FLEET_CANDIDATES:
        runtime_config_paths[strategy_id] = build_runtime_step31f_config_v0(
            repo_root=repo_root,
            strategy_id=strategy_id,
            narrow_dataset=narrow_dataset,
            output_path=config_dir / f"step31f_{strategy_id}_v1_economic_evaluation_v1.json",
        )

    raw_completion = materialize_binding_completion_v0(
        repo_root=repo_root,
        staging_root=staging_root,
        panel_binding=panel_binding,
        coverage=coverage,
        narrow_dataset=narrow_dataset,
        runtime_config_paths=runtime_config_paths,
    )
    raw_verdict = validate_binding_completion_v0(raw_completion, repo_root=repo_root)
    if raw_verdict.verdict is not ValidationVerdict.ACCEPTED:
        raise ValueError(f"RAW_BINDING_VALIDATION_FAILED:{raw_verdict.fail_reasons}")
    if str(raw_completion.get("completion_digest", "")) == HISTORICAL_BLOCKED_COMPLETION_DIGEST:
        raise ValueError(REASON_HISTORICAL_BINDING_RETRY_BLOCKED)

    binding_completion = _apply_class_d_binding_policy(raw_completion)
    verdict, fail_reasons = validate_class_d_binding_completion_v0(
        binding_completion,
        repo_root=repo_root,
    )
    if verdict is not ValidationVerdictEnum.ACCEPTED:
        raise ValueError(f"BINDING_VALIDATION_FAILED:{fail_reasons}")

    scope_ratification = materialize_scope_ratification_v0(
        binding_completion=binding_completion,
    )
    operator_ratification = materialize_operator_ratification_record_v0(
        repo_head_sha=repo_head_sha,
    )

    if write_repo_config:
        write_repo_artifacts_v0(
            repo_root=repo_root,
            binding_completion=binding_completion,
            scope_ratification=scope_ratification,
            operator_ratification=operator_ratification,
        )

    for name, payload in (
        ("FINAL_FLEET_BINDING.json", binding_completion),
        ("OFFLINE_EVALUATION_SCOPE_RATIFICATION.json", scope_ratification),
        ("OPERATOR_RATIFICATION_RECORD.json", operator_ratification),
    ):
        (evidence_root / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, _verify_msg = retention.finalize_durable_bundle_manifest(evidence_root)
    return ScopeMaterializationResultV0(
        binding_completion=binding_completion,
        scope_ratification=scope_ratification,
        operator_ratification=operator_ratification,
        evidence_root=evidence_root,
        manifest_verify_rc=rc,
    )
