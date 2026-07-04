"""Final Research Fleet offline economic evaluation execution v0.

Deterministic, fail-closed offline execution of ratified economic evaluation for
trend_following/v1, bollinger_bands/v1, and momentum_1h/v1 using canonical
STEP29M/STEP31F owners. No runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.backtest.economic_validity_policy_v1 import EconomicValidityEvaluationStatus
from src.backtest.economic_viability_evidence_v1 import (
    ARTIFACT_FILENAME,
    EconomicViabilityEvidenceError,
    load_economic_viability_evidence_bundle_v1,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
    FLEET_ID,
    FLEET_VERSION,
    STEP31F_CONFIG_PATHS,
    load_step31f_evaluation_config_v0,
)
from src.research.final_research_fleet_offline_economic_evaluation_scope_ratification_v0 import (
    OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
    ValidationVerdict,
    materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0,
    validate_final_research_fleet_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    ValidationVerdict as BindingValidationVerdict,
    canonical_candidate_identifier,
    validate_final_research_fleet_versioned_binding_completion_v0,
)

PACKAGE_MARKER = "FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0=true"

SCHEMA_VERSION = "final_research_fleet_offline_economic_evaluation_execution.v0"
EXECUTION_ID = "final_research_fleet_offline_economic_evaluation_execution_v0"
EXECUTION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = "research_fleet_execution_canonical_json_v1"

GO_TOKEN = "GO_EXECUTE_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_V0"
GO_TOKEN_OPERATOR_ALIAS = (
    "GO_BOUNDED_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_FOR_VERSIONED_FINAL_RESEARCH_FLEET_V0"
)
ACCEPTED_GO_TOKENS: frozenset[str] = frozenset({GO_TOKEN, GO_TOKEN_OPERATOR_ALIAS})
PR4826_MERGE_COMMIT = "208ab96562f7750fb4dff43936b345a040d1cea4"
PR4832_MERGE_COMMIT = "ddce9c508158b89fa225c381436e2d1efced7328"
PR4833_MERGE_COMMIT = "4828168cd91c57aa72dcb3b40b47188eeb82fd32"
PR4834_MERGE_COMMIT = "0d23e662c4a0b8e0638a919ac879490e82e2ef41"
MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA = PR4832_MERGE_COMMIT
CURRENT_EXECUTION_ORIGIN_MAIN_SHA = PR4834_MERGE_COMMIT
EXPECTED_ORIGIN_MAIN_SHA = CURRENT_EXECUTION_ORIGIN_MAIN_SHA
ACCEPTED_ORIGIN_MAIN_SHAS: frozenset[str] = frozenset(
    {
        PR4826_MERGE_COMMIT,
        MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA,
        PR4833_MERGE_COMMIT,
        CURRENT_EXECUTION_ORIGIN_MAIN_SHA,
    }
)
REQUIRED_MERGED_PR_NUMBER = 4826
CLASS_D_BINDING_COMPLETION_ID = "final_research_fleet_class_d_versioned_binding_completion_v0"
CLASS_D_BINDING_COMPLETION_SCHEMA_VERSION = (
    "final_research_fleet_class_d_versioned_bindings_and_offline_economic_evaluation_scope.v0"
)
CLASS_D_BINDING_COMPLETION_DIGEST = (
    "0610afa34b347abde08768fb2fbfb30fd4bb19ae010f3b2042c67155fb6c0fc4"
)
CLASS_D_SCOPE_RATIFICATION_CONFIG_REL = "config/research/final_research_fleet_class_d_offline_economic_evaluation_scope_ratification_v0.json"
CLASS_D_RATIFIED_SCOPE_ID = (
    "FINAL_RESEARCH_FLEET_VERSIONED_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0"
)
DURABLE_EVIDENCE_SUBDIR = "research"
DURABLE_EVIDENCE_BUNDLE_PREFIX = "bounded_offline_economic_evaluation_final_research_fleet_v0"
LEGACY_DURABLE_EVIDENCE_SUBDIR = "implementation"
LEGACY_DURABLE_EVIDENCE_BUNDLE_PREFIX = (
    "bounded_final_research_fleet_offline_economic_evaluation_v0"
)
HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST = (
    "161d834e5153df78a0013b6e55c4c8bd4788c775811e3678f025104a307d78f1"
)
HISTORICAL_STEP31F_EXECUTION_EVIDENCE_CLASS = (
    "step31f_final_research_fleet_v0_offline_economic_validity_evaluation_v0"
)
PR4826_SCOPE_EVIDENCE_CLASS = "VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_V0"
PR4826_CREATES_NEW_EXECUTION_EVIDENCE_CLASS = False

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

RUNNER_OWNER = "scripts.ops.run_economic_viability_evidence_evaluation_v1"
RUNNER_SCRIPT = "scripts/ops/run_economic_viability_evidence_evaluation_v1.py"
CANDIDATE_RUN_TIMEOUT_SECONDS = 600

ALLOWED_EVALUATION_STAGES: tuple[str, ...] = (
    "OFFLINE_BACKTEST",
    "WALK_FORWARD",
    "MONTE_CARLO",
    "STRESS",
    "PARAMETER_SENSITIVITY",
    "ECONOMIC_VIABILITY_EVIDENCE_MATERIALIZATION",
)

REASON_START_STATE_INVALID = "START_STATE_INVALID"
REASON_ORIGIN_MAIN_MISMATCH = "ORIGIN_MAIN_SHA_MISMATCH"
REASON_RATIFICATION_MISSING = "RATIFICATION_CONTRACT_MISSING"
REASON_RATIFICATION_INVALID = "RATIFICATION_CONTRACT_INVALID"
REASON_BINDING_COMPLETION_INVALID = "BINDING_COMPLETION_INVALID"
REASON_SCOPE_NOT_RATIFIED = "OFFLINE_ECONOMIC_EVALUATION_SCOPE_NOT_RATIFIED"
REASON_EVALUATION_ALREADY_EXECUTED = "ECONOMIC_EVALUATION_ALREADY_EXECUTED"
REASON_GO_TOKEN_INVALID = "GO_TOKEN_INVALID"
REASON_CANDIDATE_RUN_FAILED = "CANDIDATE_RUN_FAILED"
REASON_CANDIDATE_RUN_TIMEOUT = "CANDIDATE_RUN_TIMEOUT"
REASON_CANDIDATE_EVIDENCE_MISSING = "CANDIDATE_EVIDENCE_MISSING"
REASON_MANIFEST_VERIFY_FAILED = "MANIFEST_VERIFY_FAILED"
REASON_BINDING_DIGEST_MISMATCH = "CANDIDATE_BINDING_DIGEST_MISMATCH"
REASON_UNMODIFIED_BINDING_RETRY_BLOCKED = "UNMODIFIED_BINDING_RETRY_BLOCKED"
REASON_NEW_EVIDENCE_CLASS_REQUIRED = "NEW_EVIDENCE_CLASS_REQUIRED_FOR_REEXECUTION"


class CandidateTerminalStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


class FleetTerminalStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class StartStateVerificationResultV0:
    valid: bool
    fail_reasons: tuple[str, ...]
    origin_main_sha: str
    ratification_digest: str
    fleet_binding_digest: str


@dataclass(frozen=True)
class CandidateExecutionResultV0:
    strategy_id: str
    strategy_version: str
    canonical_candidate_identifier: str
    config_path: str
    output_dir: str
    run_id: str
    terminal_status: CandidateTerminalStatus
    economic_validity_result: str
    economic_validity_offline_gate_pass: bool
    evidence_status: str
    manifest_verify_rc: int
    reason_codes: tuple[str, ...]
    stage_return_codes: dict[str, int]
    runner_execution_success: bool


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def dumps_execution_canonical_v1(obj: Mapping[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)


def compute_fleet_summary_digest_v0(summary_body: Mapping[str, Any]) -> str:
    body = dict(summary_body)
    body.pop("manifest_digest", None)
    body.pop("semantic_digest", None)
    return hashlib.sha256(dumps_execution_canonical_v1(body).encode("utf-8")).hexdigest()


def compute_fleet_semantic_digest_v0(summary_body: Mapping[str, Any]) -> str:
    payload = {
        "fleet_id": summary_body.get("fleet_id"),
        "fleet_version": summary_body.get("fleet_version"),
        "ratification_ref": summary_body.get("ratification_ref"),
        "candidate_results": summary_body.get("candidate_results"),
        "pass_count": summary_body.get("pass_count"),
        "fail_count": summary_body.get("fail_count"),
        "inconclusive_count": summary_body.get("inconclusive_count"),
        "fleet_status": summary_body.get("fleet_status"),
        "economic_validity_offline_gate_pass": summary_body.get(
            "economic_validity_offline_gate_pass"
        ),
    }
    return _stable_digest(payload)


def _resolve_origin_main_sha(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def is_accepted_go_token(token: str) -> bool:
    return token in ACCEPTED_GO_TOKENS


def is_accepted_origin_main_sha(origin_main_sha: str) -> bool:
    return origin_main_sha in ACCEPTED_ORIGIN_MAIN_SHAS


def is_class_d_binding_completion_v0(fleet_binding_completion: Mapping[str, Any]) -> bool:
    return (
        fleet_binding_completion.get("schema_version") == CLASS_D_BINDING_COMPLETION_SCHEMA_VERSION
        or fleet_binding_completion.get("completion_id") == CLASS_D_BINDING_COMPLETION_ID
        or fleet_binding_completion.get("ratification_class") == "D"
    )


def resolve_durable_evidence_bundle_dir_v0(
    *,
    durable_evidence_root: Path,
    timestamp_slug: str,
) -> Path:
    return (
        durable_evidence_root
        / DURABLE_EVIDENCE_SUBDIR
        / f"{DURABLE_EVIDENCE_BUNDLE_PREFIX}_{timestamp_slug}"
    )


def resolve_legacy_durable_evidence_bundle_dir_v0(
    *,
    durable_evidence_root: Path,
    timestamp_slug: str,
) -> Path:
    return (
        durable_evidence_root
        / LEGACY_DURABLE_EVIDENCE_SUBDIR
        / f"{LEGACY_DURABLE_EVIDENCE_BUNDLE_PREFIX}_{timestamp_slug}"
    )


def verify_origin_main_sha_for_binding_v0(
    *,
    origin_main_sha: str,
    fleet_binding_completion: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    if is_class_d_binding_completion_v0(fleet_binding_completion):
        if origin_main_sha != CURRENT_EXECUTION_ORIGIN_MAIN_SHA:
            return False, (
                f"{REASON_ORIGIN_MAIN_MISMATCH}:{origin_main_sha}!={CURRENT_EXECUTION_ORIGIN_MAIN_SHA}",
            )
        return True, ()
    if not is_accepted_origin_main_sha(origin_main_sha):
        return False, (f"{REASON_ORIGIN_MAIN_MISMATCH}:{origin_main_sha}",)
    return True, ()


def load_scope_ratification_for_execution_v0(
    *,
    repo_root: Path,
    fleet_binding_completion: Mapping[str, Any],
) -> dict[str, Any]:
    if is_class_d_binding_completion_v0(fleet_binding_completion):
        scope_path = repo_root / CLASS_D_SCOPE_RATIFICATION_CONFIG_REL
        if not scope_path.is_file():
            raise ValueError(f"missing_class_d_scope_ratification:{scope_path}")
        payload = json.loads(scope_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("class_d_scope_ratification_not_object")
        return payload
    return materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
        repo_root=repo_root,
        fleet_binding_completion=fleet_binding_completion,
    )


def validate_binding_completion_for_execution_v0(
    fleet_binding_completion: Mapping[str, Any],
    *,
    repo_root: Path,
    require_ready_for_eval: bool = True,
) -> tuple[bool, tuple[str, ...]]:
    if is_class_d_binding_completion_v0(fleet_binding_completion):
        from src.research.final_research_fleet_class_d_versioned_bindings_and_offline_economic_evaluation_scope_v0 import (  # noqa: PLC0415,E501
            validate_class_d_binding_completion_v0,
        )

        verdict, fail_reasons = validate_class_d_binding_completion_v0(
            fleet_binding_completion,
            repo_root=repo_root,
        )
        if verdict.value != "ACCEPTED":
            return False, fail_reasons
        return True, ()
    binding_validation = validate_final_research_fleet_versioned_binding_completion_v0(
        fleet_binding_completion,
        repo_root=repo_root,
        require_ready_for_eval=require_ready_for_eval,
    )
    if binding_validation.verdict != BindingValidationVerdict.ACCEPTED:
        return False, binding_validation.fail_reasons
    return True, ()


def validate_class_d_scope_ratification_for_execution_v0(
    ratification: Mapping[str, Any],
    *,
    fleet_binding_completion: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if ratification.get("schema_version") != CLASS_D_BINDING_COMPLETION_SCHEMA_VERSION:
        reasons.append("UNKNOWN_SCHEMA_VERSION")
    if ratification.get("ratified_scope_id") != CLASS_D_RATIFIED_SCOPE_ID:
        reasons.append("RATIFIED_SCOPE_ID_MISMATCH")
    if ratification.get("fleet_binding_digest") != fleet_binding_completion.get(
        "completion_digest"
    ):
        reasons.append(REASON_BINDING_DIGEST_MISMATCH)
    if ratification.get("offline_economic_evaluation_scope_ratified") is not True:
        reasons.append(REASON_SCOPE_NOT_RATIFIED)
    if ratification.get("economic_evaluation_executed") is not False:
        reasons.append(REASON_EVALUATION_ALREADY_EXECUTED)
    if ratification.get("economic_evaluation_authorized") is not False:
        reasons.append("ECONOMIC_EVALUATION_AUTHORIZED_MUST_BE_FALSE")
    for effect_field, expected in (
        ("authority_effect", AUTHORITY_EFFECT),
        ("runtime_effect", RUNTIME_EFFECT),
        ("order_effect", ORDER_EFFECT),
    ):
        if ratification.get(effect_field) != expected:
            reasons.append(f"EFFECT_NOT_NONE:{effect_field}")
    if ratification.get("runtime_rewire_admissible") is not False:
        reasons.append("RUNTIME_REWIRE_MUST_BE_FALSE")
    if ratification.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if ratification.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_BINDING_REJECTED")
    expected_refs = [
        canonical_candidate_identifier(strategy_id, version)
        for strategy_id, version in FLEET_CANDIDATES
    ]
    if sorted(ratification.get("candidate_refs") or []) != sorted(expected_refs):
        reasons.append("CANDIDATE_SET_MISMATCH")
    binding_digests = ratification.get("candidate_binding_digests")
    if isinstance(binding_digests, Mapping):
        for candidate in fleet_binding_completion.get("candidates", ()):
            if not isinstance(candidate, Mapping):
                continue
            ref = canonical_candidate_identifier(
                str(candidate["strategy_id"]), str(candidate["strategy_version"])
            )
            expected = str(candidate.get("binding_semantic_digest", ""))
            actual = binding_digests.get(ref)
            if actual != expected:
                reasons.append(f"{REASON_BINDING_DIGEST_MISMATCH}:{ref}")
    return not reasons, tuple(reasons)


def validate_scope_ratification_for_execution_v0(
    ratification: Mapping[str, Any],
    *,
    repo_root: Path,
    fleet_binding_completion: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    if is_class_d_binding_completion_v0(fleet_binding_completion):
        return validate_class_d_scope_ratification_for_execution_v0(
            ratification,
            fleet_binding_completion=fleet_binding_completion,
        )
    ratification_validation = (
        validate_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
            ratification,
            repo_root=repo_root,
            expected_fleet_binding_completion=fleet_binding_completion,
        )
    )
    if ratification_validation.verdict != ValidationVerdict.ACCEPTED:
        return False, ratification_validation.fail_reasons
    return True, ()


def canonical_go_token(token: str) -> str:
    if is_accepted_go_token(token):
        return GO_TOKEN
    raise ValueError(REASON_GO_TOKEN_INVALID)


def verify_unmodified_retry_admissibility_v0(
    *,
    fleet_binding_completion: Mapping[str, Any],
    requested_execution_evidence_class: str | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Fail closed when bindings match historical STEP31F terminal FAIL digest."""
    completion_digest = str(fleet_binding_completion.get("completion_digest", ""))
    if completion_digest != HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST:
        return True, ()
    if PR4826_CREATES_NEW_EXECUTION_EVIDENCE_CLASS and requested_execution_evidence_class:
        if requested_execution_evidence_class != HISTORICAL_STEP31F_EXECUTION_EVIDENCE_CLASS:
            return True, ()
    reasons = [REASON_UNMODIFIED_BINDING_RETRY_BLOCKED]
    if not PR4826_CREATES_NEW_EXECUTION_EVIDENCE_CLASS:
        reasons.append(REASON_NEW_EVIDENCE_CLASS_REQUIRED)
    return False, tuple(reasons)


def verify_execution_start_state_v0(
    *,
    repo_root: Path,
    ratification: Mapping[str, Any],
    fleet_binding_completion: Mapping[str, Any],
    origin_main_sha: str | None = None,
) -> StartStateVerificationResultV0:
    reasons: list[str] = []
    resolved_origin = origin_main_sha or _resolve_origin_main_sha(repo_root)
    origin_ok, origin_reasons = verify_origin_main_sha_for_binding_v0(
        origin_main_sha=resolved_origin,
        fleet_binding_completion=fleet_binding_completion,
    )
    if not origin_ok:
        reasons.extend(origin_reasons)

    binding_ok, binding_reasons = validate_binding_completion_for_execution_v0(
        fleet_binding_completion,
        repo_root=repo_root,
        require_ready_for_eval=True,
    )
    if not binding_ok:
        reasons.extend(binding_reasons)

    scope_ok, scope_reasons = validate_scope_ratification_for_execution_v0(
        ratification,
        repo_root=repo_root,
        fleet_binding_completion=fleet_binding_completion,
    )
    if not scope_ok:
        reasons.extend(scope_reasons)

    if ratification.get("offline_economic_evaluation_scope_ratified") is not True:
        reasons.append(REASON_SCOPE_NOT_RATIFIED)
    if ratification.get("economic_evaluation_executed") is not False:
        reasons.append(REASON_EVALUATION_ALREADY_EXECUTED)
    if not is_class_d_binding_completion_v0(fleet_binding_completion):
        if ratification.get("offline_economic_evaluation_scope_ratified") != (
            OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED
        ):
            reasons.append(REASON_SCOPE_NOT_RATIFIED)

    expected_refs = [
        canonical_candidate_identifier(strategy_id, version)
        for strategy_id, version in FLEET_CANDIDATES
    ]
    candidate_refs = ratification.get("candidate_refs")
    if sorted(candidate_refs or []) != sorted(expected_refs):
        reasons.append("CANDIDATE_SET_MISMATCH")

    binding_digests = ratification.get("candidate_binding_digests")
    if isinstance(binding_digests, Mapping):
        for candidate in fleet_binding_completion.get("candidates", ()):
            if not isinstance(candidate, Mapping):
                continue
            ref = canonical_candidate_identifier(
                str(candidate["strategy_id"]), str(candidate["strategy_version"])
            )
            expected = str(candidate.get("binding_semantic_digest", ""))
            actual = binding_digests.get(ref)
            if actual != expected:
                reasons.append(f"{REASON_BINDING_DIGEST_MISMATCH}:{ref}")

    retry_ok, retry_reasons = verify_unmodified_retry_admissibility_v0(
        fleet_binding_completion=fleet_binding_completion,
    )
    if not retry_ok:
        reasons.extend(retry_reasons)

    return StartStateVerificationResultV0(
        valid=not reasons,
        fail_reasons=tuple(reasons),
        origin_main_sha=resolved_origin,
        ratification_digest=str(ratification.get("ratification_digest", "")),
        fleet_binding_digest=str(ratification.get("fleet_binding_digest", "")),
    )


def extract_dataset_paths_from_config(cfg: Mapping[str, Any]) -> tuple[str, str]:
    binding = cfg.get("real_admissible_futures_evaluation_binding_v1")
    if not isinstance(binding, Mapping):
        raise ValueError("real_admissible_futures_evaluation_binding_v1_missing")
    dataset_path = str(binding.get("dataset_path", "")).strip()
    manifest_path = str(
        binding.get("dataset_manifest_path") or binding.get("expected_manifest_path") or ""
    ).strip()
    if not dataset_path:
        raise ValueError("dataset_path_missing")
    if not manifest_path:
        manifest_path = str(Path(dataset_path).parent / "dataset_manifest.json")
    return dataset_path, manifest_path


def map_candidate_terminal_status_v0(
    *,
    runner_execution_success: bool,
    economic_validity_result: str,
    economic_validity_offline_gate_pass: bool,
    evidence_status: str,
) -> CandidateTerminalStatus:
    if not runner_execution_success:
        return CandidateTerminalStatus.INCONCLUSIVE
    if economic_validity_result == EconomicValidityEvaluationStatus.PASS.value:
        if economic_validity_offline_gate_pass and evidence_status == "ECONOMICALLY_VIABLE_OFFLINE":
            return CandidateTerminalStatus.PASS
        return CandidateTerminalStatus.FAIL
    if economic_validity_result == EconomicValidityEvaluationStatus.FAIL.value:
        return CandidateTerminalStatus.FAIL
    if economic_validity_result == EconomicValidityEvaluationStatus.BLOCKED.value:
        return CandidateTerminalStatus.INCONCLUSIVE
    return CandidateTerminalStatus.FAIL


def resolve_fleet_terminal_status_v0(
    candidate_results: Sequence[CandidateExecutionResultV0],
) -> FleetTerminalStatus:
    if any(r.terminal_status is CandidateTerminalStatus.INCONCLUSIVE for r in candidate_results):
        return FleetTerminalStatus.INCONCLUSIVE
    if all(r.terminal_status is CandidateTerminalStatus.PASS for r in candidate_results):
        return FleetTerminalStatus.PASS
    return FleetTerminalStatus.FAIL


def run_candidate_economic_evaluation_v0(
    *,
    repo_root: Path,
    strategy_id: str,
    strategy_version: str,
    config_path: Path,
    output_dir: Path,
    timeout_seconds: int = CANDIDATE_RUN_TIMEOUT_SECONDS,
) -> CandidateExecutionResultV0:
    candidate_ref = canonical_candidate_identifier(strategy_id, strategy_version)
    cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
    dataset_path, manifest_path = extract_dataset_paths_from_config(cfg)

    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"output_dir_nonempty:{output_dir}")

    from scripts.ops.run_economic_viability_evidence_evaluation_v1 import (  # noqa: PLC0415
        RunnerError,
        build_arg_parser,
        execute_evaluation,
    )

    parser = build_arg_parser()
    args = parser.parse_args(
        [
            "--dataset-path",
            dataset_path,
            "--dataset-manifest-path",
            manifest_path,
            "--config-path",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--allow-existing-output",
            "--json",
        ]
    )
    stage_return_codes: dict[str, int] = {"economic_viability_runner": 0}
    try:
        outcome = execute_evaluation(args)
    except RunnerError:
        stage_return_codes["economic_viability_runner"] = 1
        return CandidateExecutionResultV0(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            canonical_candidate_identifier=candidate_ref,
            config_path=str(config_path.relative_to(repo_root)),
            output_dir=str(output_dir),
            run_id="",
            terminal_status=CandidateTerminalStatus.INCONCLUSIVE,
            economic_validity_result="BLOCKED",
            economic_validity_offline_gate_pass=False,
            evidence_status="",
            manifest_verify_rc=1,
            reason_codes=(REASON_CANDIDATE_RUN_FAILED,),
            stage_return_codes=stage_return_codes,
            runner_execution_success=False,
        )

    if not outcome.runner_execution_success:
        stage_return_codes["economic_viability_runner"] = 1
        return CandidateExecutionResultV0(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            canonical_candidate_identifier=candidate_ref,
            config_path=str(config_path.relative_to(repo_root)),
            output_dir=str(output_dir),
            run_id=outcome.run_id,
            terminal_status=CandidateTerminalStatus.INCONCLUSIVE,
            economic_validity_result=outcome.economic_validity_result,
            economic_validity_offline_gate_pass=False,
            evidence_status="",
            manifest_verify_rc=outcome.manifest_verify_rc,
            reason_codes=(REASON_CANDIDATE_RUN_FAILED,),
            stage_return_codes=stage_return_codes,
            runner_execution_success=False,
        )

    runner_payload = {
        "economic_validity_result": outcome.economic_validity_result,
        "economic_validity_offline_gate_pass": outcome.economic_validity_offline_gate_pass,
        "manifest_verify_rc": outcome.manifest_verify_rc,
    }

    economic_validity_result = str(runner_payload.get("economic_validity_result") or "BLOCKED")
    economic_validity_offline_gate_pass = bool(
        runner_payload.get("economic_validity_offline_gate_pass")
    )
    manifest_verify_rc = int(runner_payload.get("manifest_verify_rc", 1))

    run_id = outcome.run_id
    summary_path = output_dir / "run_summary.env"
    if summary_path.is_file():
        for line in summary_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("RUN_ID="):
                run_id = line.split("=", 1)[1].strip()
                break

    try:
        loaded = load_economic_viability_evidence_bundle_v1(output_dir)
        evidence_status = loaded.evidence.status.value
    except EconomicViabilityEvidenceError:
        return CandidateExecutionResultV0(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            canonical_candidate_identifier=candidate_ref,
            config_path=str(config_path.relative_to(repo_root)),
            output_dir=str(output_dir),
            run_id=run_id,
            terminal_status=CandidateTerminalStatus.INCONCLUSIVE,
            economic_validity_result=economic_validity_result,
            economic_validity_offline_gate_pass=False,
            evidence_status="",
            manifest_verify_rc=manifest_verify_rc,
            reason_codes=(REASON_CANDIDATE_EVIDENCE_MISSING,),
            stage_return_codes=stage_return_codes,
            runner_execution_success=False,
        )

    terminal_status = map_candidate_terminal_status_v0(
        runner_execution_success=True,
        economic_validity_result=economic_validity_result,
        economic_validity_offline_gate_pass=economic_validity_offline_gate_pass,
        evidence_status=evidence_status,
    )
    reason_codes: tuple[str, ...] = ()
    if manifest_verify_rc != 0:
        reason_codes = (REASON_MANIFEST_VERIFY_FAILED,)

    return CandidateExecutionResultV0(
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        canonical_candidate_identifier=candidate_ref,
        config_path=str(config_path.relative_to(repo_root)),
        output_dir=str(output_dir),
        run_id=run_id,
        terminal_status=terminal_status,
        economic_validity_result=economic_validity_result,
        economic_validity_offline_gate_pass=economic_validity_offline_gate_pass,
        evidence_status=evidence_status,
        manifest_verify_rc=manifest_verify_rc,
        reason_codes=reason_codes,
        stage_return_codes=stage_return_codes,
        runner_execution_success=True,
    )


def materialize_fleet_evaluation_summary_v0(
    *,
    ratification: Mapping[str, Any],
    candidate_results: Sequence[CandidateExecutionResultV0],
    execution_bundle_dir: str,
    origin_main_sha: str,
) -> dict[str, Any]:
    fleet_status = resolve_fleet_terminal_status_v0(candidate_results)
    pass_count = sum(
        1 for r in candidate_results if r.terminal_status is CandidateTerminalStatus.PASS
    )
    fail_count = sum(
        1 for r in candidate_results if r.terminal_status is CandidateTerminalStatus.FAIL
    )
    inconclusive_count = sum(
        1 for r in candidate_results if r.terminal_status is CandidateTerminalStatus.INCONCLUSIVE
    )
    economic_validity_offline_gate_pass = (
        fleet_status is FleetTerminalStatus.PASS and pass_count == len(FLEET_CANDIDATES)
    )
    promotion_candidates = [
        r.canonical_candidate_identifier
        for r in candidate_results
        if r.terminal_status is CandidateTerminalStatus.PASS
    ]

    candidate_summaries = []
    for result in candidate_results:
        candidate_summaries.append(
            {
                "strategy_id": result.strategy_id,
                "strategy_version": result.strategy_version,
                "canonical_candidate_identifier": result.canonical_candidate_identifier,
                "terminal_status": result.terminal_status.value,
                "economic_validity_result": result.economic_validity_result,
                "economic_validity_offline_gate_pass": result.economic_validity_offline_gate_pass,
                "evidence_status": result.evidence_status,
                "config_path": result.config_path,
                "output_dir": result.output_dir,
                "run_id": result.run_id,
                "manifest_verify_rc": result.manifest_verify_rc,
                "reason_codes": list(result.reason_codes),
                "stage_return_codes": dict(result.stage_return_codes),
                "runner_execution_success": result.runner_execution_success,
                "evidence_artifact": ARTIFACT_FILENAME,
            }
        )

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "execution_id": EXECUTION_ID,
        "execution_version": EXECUTION_VERSION,
        "fleet_id": FLEET_ID,
        "fleet_version": FLEET_VERSION,
        "ratification_ref": ratification.get("operator_scope_ratification_ref"),
        "ratification_digest": ratification.get("ratification_digest"),
        "fleet_binding_digest": ratification.get("fleet_binding_digest"),
        "origin_main_sha": origin_main_sha,
        "execution_bundle_dir": execution_bundle_dir,
        "candidate_results": candidate_summaries,
        "candidate_evidence_refs": [r.output_dir for r in candidate_results],
        "candidate_manifest_digests": {
            r.canonical_candidate_identifier: r.manifest_verify_rc for r in candidate_results
        },
        "pass_count": pass_count,
        "fail_count": fail_count,
        "inconclusive_count": inconclusive_count,
        "fleet_status": fleet_status.value,
        "fleet_reason_codes": []
        if fleet_status is FleetTerminalStatus.PASS
        else ["FLEET_NOT_FULL_PASS"],
        "comparable_policy_check": True,
        "comparable_dataset_period_check": True,
        "individual_failure_preservation": True,
        "economic_validity_offline_gate_pass": economic_validity_offline_gate_pass,
        "economic_evaluation_executed": True,
        "promotion_candidate_eligibility": bool(promotion_candidates),
        "promotion_candidates": promotion_candidates,
        "runtime_rewire_admissible": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "allowed_evaluation_stages_executed": list(ALLOWED_EVALUATION_STAGES),
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "digest_semantics": {
            "semantic_digest": "FLEET_EXECUTION_SUMMARY_SEMANTIC_PAYLOAD_v0",
            "manifest_digest": "FLEET_EXECUTION_SUMMARY_BODY_CANONICAL_JSON_v0",
        },
    }
    body["semantic_digest"] = compute_fleet_semantic_digest_v0(body)
    body["manifest_digest"] = compute_fleet_summary_digest_v0(body)
    return body
