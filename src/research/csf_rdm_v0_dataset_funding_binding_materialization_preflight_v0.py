"""CSF/RDM v0 dataset/funding binding materialization preflight (pre-evaluation gate only).

Deterministic, versioned, manifest-verifiable preflight that requires explicit dataset and
funding bindings before any offline economic evaluation may proceed. Does not execute
economic evaluation, runtime, fetch with credentials, or order effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_funding_rate_delta_momentum_v0_bound_panel_dataset_materialization_v0 import (
    BoundFundingPanelMaterializationResultV0,
    MaterializationTerminalStatus,
    materialization_result_to_dict,
    materialize_bound_funding_panel_dataset_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    FAIL_CLOSED_EXPECTED_ORIGIN_MAIN_SHA_BINDING_MISSING,
    FAIL_CLOSED_ORIGIN_MAIN_SHA_MISMATCH,
    ORIGIN_MAIN_SHA_BINDING_ENV_VAR,
    RUNTIME_EFFECT,
    OriginMainShaGuardResultV0,
    load_versioned_research_binding_v0,
    origin_main_sha_guard_to_dict,
    resolve_actual_repo_shas_v0,
    verify_origin_main_sha_guard_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (
    STRATEGY_ID,
    STRATEGY_VERSION,
    materialize_versioned_research_binding_v0,
)

PACKAGE_MARKER = "CSF_RDM_V0_DATASET_FUNDING_BINDING_MATERIALIZATION_PREFLIGHT_V0=true"
PREFLIGHT_VERSION = "csf_rdm_v0_dataset_funding_binding_materialization_preflight.v0"
GO_TOKEN = "GO_BOUNDED_CSF_RDM_V0_DATASET_FUNDING_BINDING_MATERIALIZATION_PREFLIGHT_V0"
BINDING_ORIGIN_MAIN_SHA_ENV_VAR = "BINDING_ORIGIN_MAIN_SHA"

REASON_DATASET_BINDING_MISSING = "DATASET_BINDING_MISSING"
REASON_DATASET_BINDING_INCOMPLETE = "DATASET_BINDING_INCOMPLETE"
REASON_FUNDING_BINDING_MISSING = "FUNDING_MODEL_BINDING_MISSING"
REASON_FUNDING_BINDING_INCOMPLETE = "FUNDING_MODEL_BINDING_INCOMPLETE"
REASON_STRATEGY_ID_MISSING = "STRATEGY_ID_MISSING"
REASON_CANDIDATE_ID_MISSING = "CANDIDATE_ID_MISSING"
REASON_BINDING_ORIGIN_MAIN_SHA_MISSING = "BINDING_ORIGIN_MAIN_SHA_MISSING"
REASON_BINDING_ORIGIN_MAIN_SHA_MISMATCH = "BINDING_ORIGIN_MAIN_SHA_MISMATCH"
REASON_BOUND_DATA_UNAVAILABLE = "BOUND_DATA_UNAVAILABLE"
REASON_FUNDING_DATA_UNAVAILABLE_NOT_MATERIALIZED = "FUNDING_DATA_UNAVAILABLE_NOT_MATERIALIZED"
REASON_DATA_DIGEST_MISMATCH = "DATA_DIGEST_MISMATCH"

_DATASET_REQUIRED_FIELDS = (
    "dataset_id",
    "dataset_extension",
    "panel_funding_dataset_manifest_ref",
    "panel_calendar_start_utc",
    "panel_calendar_end_utc",
)


class PreflightTerminalStatus(str, Enum):
    FAIL_CLOSED_SHA_GUARD = "FAIL_CLOSED_SHA_GUARD"
    FAIL_CLOSED_DATASET_BINDING = "FAIL_CLOSED_DATASET_BINDING"
    FAIL_CLOSED_FUNDING_BINDING = "FAIL_CLOSED_FUNDING_BINDING"
    FAIL_CLOSED_BINDING_ORIGIN_MAIN_SHA = "FAIL_CLOSED_BINDING_ORIGIN_MAIN_SHA"
    FAIL_CLOSED_BOUND_DATA_UNAVAILABLE = "FAIL_CLOSED_BOUND_DATA_UNAVAILABLE"
    FAIL_CLOSED_FUNDING_DATA_UNAVAILABLE = "FAIL_CLOSED_FUNDING_DATA_UNAVAILABLE"
    PREFLIGHT_GATE_PASS_READY_FOR_NEXT_PRE_EVALUATION_GATE = (
        "PREFLIGHT_GATE_PASS_READY_FOR_NEXT_PRE_EVALUATION_GATE"
    )


@dataclass(frozen=True)
class ExplicitBindingVerificationV0:
    strategy_id: str
    candidate_id: str
    dataset_binding: dict[str, Any]
    period_binding: dict[str, Any]
    instrument_binding: dict[str, Any]
    funding_model_binding: dict[str, Any]
    data_digest: str
    config_digest: str
    binding_origin_main_sha: str


@dataclass(frozen=True)
class DatasetFundingBindingMaterializationPreflightResultV0:
    status: PreflightTerminalStatus
    sha_guard: OriginMainShaGuardResultV0
    binding_verification: ExplicitBindingVerificationV0 | None
    dataset_materialization: BoundFundingPanelMaterializationResultV0 | None
    ready_for_next_pre_evaluation_gate: bool
    economic_evaluation_executed: bool
    economic_evaluation_blocked: bool
    reason_codes: tuple[str, ...]
    authority_effect: str
    runtime_effect: str


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def resolve_binding_origin_main_sha_v0(
    *,
    explicit_sha: str | None = None,
    env: Mapping[str, str] | None = None,
) -> tuple[str, str]:
    if explicit_sha and explicit_sha.strip():
        return explicit_sha.strip(), "cli_argument"
    import os

    env_map = env if env is not None else os.environ
    env_sha = str(env_map.get(BINDING_ORIGIN_MAIN_SHA_ENV_VAR, "")).strip()
    if env_sha:
        return env_sha, "environment_variable"
    return "", ""


def verify_dataset_binding_explicit_v0(
    *,
    dataset_binding: Mapping[str, Any] | None,
    data_digest: str,
    period_binding: Mapping[str, Any] | None,
    instrument_binding: Mapping[str, Any] | None,
    config_digest: str,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if not isinstance(dataset_binding, Mapping) or not dataset_binding:
        return False, (REASON_DATASET_BINDING_MISSING,)

    for field in _DATASET_REQUIRED_FIELDS:
        if not str(dataset_binding.get(field, "")).strip():
            reasons.append(f"{REASON_DATASET_BINDING_INCOMPLETE}:{field}")

    if (
        not isinstance(period_binding, Mapping)
        or not str(period_binding.get("period_binding_id", "")).strip()
    ):
        reasons.append(f"{REASON_DATASET_BINDING_INCOMPLETE}:period_binding")

    if not isinstance(instrument_binding, Mapping) or not instrument_binding:
        reasons.append(f"{REASON_DATASET_BINDING_INCOMPLETE}:instrument_binding")

    if not str(data_digest).strip() or len(str(data_digest).strip()) != 64:
        reasons.append(f"{REASON_DATASET_BINDING_INCOMPLETE}:data_digest")

    if not str(config_digest).strip() or len(str(config_digest).strip()) != 64:
        reasons.append(f"{REASON_DATASET_BINDING_INCOMPLETE}:config_digest")

    return not reasons, tuple(reasons)


def verify_funding_model_binding_explicit_v0(
    funding_model_binding: Mapping[str, Any] | None,
) -> tuple[bool, tuple[str, ...], str]:
    if not isinstance(funding_model_binding, Mapping) or not funding_model_binding:
        return False, (REASON_FUNDING_BINDING_MISSING,), "NOT_BOUND"

    reasons: list[str] = []
    if funding_model_binding.get("bind") is not True:
        reasons.append(f"{REASON_FUNDING_BINDING_INCOMPLETE}:bind")
    if not str(funding_model_binding.get("funding_model_version", "")).strip():
        reasons.append(f"{REASON_FUNDING_BINDING_INCOMPLETE}:funding_model_version")

    if reasons:
        return False, tuple(reasons), "NOT_BOUND"
    return True, (), "BOUND"


def verify_binding_origin_main_sha_v0(
    *,
    binding_origin_main_sha: str,
    actual_origin_main_sha: str,
) -> tuple[bool, tuple[str, ...]]:
    if not binding_origin_main_sha.strip():
        return False, (REASON_BINDING_ORIGIN_MAIN_SHA_MISSING,)
    if binding_origin_main_sha != actual_origin_main_sha:
        return False, (
            REASON_BINDING_ORIGIN_MAIN_SHA_MISMATCH,
            f"expected={binding_origin_main_sha}",
            f"actual={actual_origin_main_sha}",
        )
    return True, ()


def extract_explicit_bindings_v0(
    versioned_binding: Mapping[str, Any],
    *,
    binding_origin_main_sha: str,
) -> tuple[ExplicitBindingVerificationV0 | None, tuple[str, ...]]:
    reasons: list[str] = []
    strategy_id = str(versioned_binding.get("strategy_id", "")).strip()
    if not strategy_id:
        reasons.append(REASON_STRATEGY_ID_MISSING)

    candidate_id = f"{strategy_id}/{STRATEGY_VERSION}" if strategy_id else ""
    if not candidate_id or candidate_id.endswith("/"):
        reasons.append(REASON_CANDIDATE_ID_MISSING)

    dataset_binding = versioned_binding.get("panel_dataset_binding")
    period_binding = versioned_binding.get("period_binding")
    instrument_binding = versioned_binding.get("instrument_binding")
    data_digest = str(versioned_binding.get("data_digest", "")).strip()
    config_digest = str(versioned_binding.get("config_digest", "")).strip()

    dataset_ok, dataset_reasons = verify_dataset_binding_explicit_v0(
        dataset_binding=dataset_binding if isinstance(dataset_binding, Mapping) else None,
        data_digest=data_digest,
        period_binding=period_binding if isinstance(period_binding, Mapping) else None,
        instrument_binding=instrument_binding if isinstance(instrument_binding, Mapping) else None,
        config_digest=config_digest,
    )
    if not dataset_ok:
        reasons.extend(dataset_reasons)

    cost_binding = versioned_binding.get("cost_execution_binding", {})
    funding_binding = (
        cost_binding.get("funding_model_binding") if isinstance(cost_binding, Mapping) else None
    )
    funding_ok, funding_reasons, _ = verify_funding_model_binding_explicit_v0(
        funding_binding if isinstance(funding_binding, Mapping) else None
    )
    if not funding_ok:
        reasons.extend(funding_reasons)

    if reasons:
        return None, tuple(reasons)

    return (
        ExplicitBindingVerificationV0(
            strategy_id=strategy_id,
            candidate_id=candidate_id,
            dataset_binding=dict(dataset_binding),
            period_binding=dict(period_binding),
            instrument_binding=dict(instrument_binding),
            funding_model_binding=dict(funding_binding),
            data_digest=data_digest,
            config_digest=config_digest,
            binding_origin_main_sha=binding_origin_main_sha,
        ),
        (),
    )


def preflight_result_to_dict(
    result: DatasetFundingBindingMaterializationPreflightResultV0,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": PREFLIGHT_VERSION,
        "status": result.status.value,
        "sha_guard": origin_main_sha_guard_to_dict(result.sha_guard),
        "ready_for_next_pre_evaluation_gate": result.ready_for_next_pre_evaluation_gate,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "economic_evaluation_blocked": result.economic_evaluation_blocked,
        "reason_codes": list(result.reason_codes),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "go_token": GO_TOKEN,
        "package_marker": PACKAGE_MARKER,
    }
    if result.binding_verification is not None:
        binding = result.binding_verification
        payload["binding_verification"] = {
            "strategy_id": binding.strategy_id,
            "candidate_id": binding.candidate_id,
            "dataset_binding": binding.dataset_binding,
            "period_binding": binding.period_binding,
            "instrument_binding": binding.instrument_binding,
            "funding_model_binding": binding.funding_model_binding,
            "data_digest": binding.data_digest,
            "config_digest": binding.config_digest,
            "binding_origin_main_sha": binding.binding_origin_main_sha,
            "binding_digest": _stable_digest(
                {
                    "strategy_id": binding.strategy_id,
                    "candidate_id": binding.candidate_id,
                    "data_digest": binding.data_digest,
                    "config_digest": binding.config_digest,
                    "binding_origin_main_sha": binding.binding_origin_main_sha,
                }
            ),
        }
    if result.dataset_materialization is not None:
        payload["dataset_materialization"] = materialization_result_to_dict(
            result.dataset_materialization
        )
    payload["manifest_digest"] = _stable_digest(
        {key: value for key, value in payload.items() if key != "manifest_digest"}
    )
    return payload


def run_dataset_funding_binding_materialization_preflight_v0(
    *,
    repo_root: Path,
    staging_root: Path,
    expected_origin_main_sha: str | None = None,
    binding_origin_main_sha: str | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
    env: Mapping[str, str] | None = None,
) -> DatasetFundingBindingMaterializationPreflightResultV0:
    """Fail-closed pre-evaluation gate: SHA guard, explicit bindings, materialization preflight."""
    sha_guard = verify_origin_main_sha_guard_v0(
        repo_root=repo_root,
        expected_origin_main_sha=expected_origin_main_sha,
        env=env,
    )
    if not sha_guard.passed:
        return DatasetFundingBindingMaterializationPreflightResultV0(
            status=PreflightTerminalStatus.FAIL_CLOSED_SHA_GUARD,
            sha_guard=sha_guard,
            binding_verification=None,
            dataset_materialization=None,
            ready_for_next_pre_evaluation_gate=False,
            economic_evaluation_executed=False,
            economic_evaluation_blocked=True,
            reason_codes=sha_guard.fail_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    resolved_binding_sha, _ = resolve_binding_origin_main_sha_v0(
        explicit_sha=binding_origin_main_sha,
        env=env,
    )
    _, actual_origin_main = resolve_actual_repo_shas_v0(repo_root)
    binding_sha_ok, binding_sha_reasons = verify_binding_origin_main_sha_v0(
        binding_origin_main_sha=resolved_binding_sha,
        actual_origin_main_sha=actual_origin_main,
    )
    if not binding_sha_ok:
        return DatasetFundingBindingMaterializationPreflightResultV0(
            status=PreflightTerminalStatus.FAIL_CLOSED_BINDING_ORIGIN_MAIN_SHA,
            sha_guard=sha_guard,
            binding_verification=None,
            dataset_materialization=None,
            ready_for_next_pre_evaluation_gate=False,
            economic_evaluation_executed=False,
            economic_evaluation_blocked=True,
            reason_codes=binding_sha_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    envelope = dict(
        versioned_binding
        or load_versioned_research_binding_v0(repo_root)
        or materialize_versioned_research_binding_v0()
    )
    binding_verification, binding_reasons = extract_explicit_bindings_v0(
        envelope,
        binding_origin_main_sha=resolved_binding_sha,
    )
    if binding_verification is None:
        status = (
            PreflightTerminalStatus.FAIL_CLOSED_FUNDING_BINDING
            if any(code.startswith("FUNDING") for code in binding_reasons)
            else PreflightTerminalStatus.FAIL_CLOSED_DATASET_BINDING
        )
        return DatasetFundingBindingMaterializationPreflightResultV0(
            status=status,
            sha_guard=sha_guard,
            binding_verification=None,
            dataset_materialization=None,
            ready_for_next_pre_evaluation_gate=False,
            economic_evaluation_executed=False,
            economic_evaluation_blocked=True,
            reason_codes=binding_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    materialization = materialize_bound_funding_panel_dataset_v0(
        staging_root,
        period_binding=binding_verification.period_binding,
        expected_data_digest=binding_verification.data_digest,
    )

    if materialization.status is not MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE:
        reasons = list(materialization.reason_codes)
        reasons.append(REASON_BOUND_DATA_UNAVAILABLE)
        reasons.append(REASON_FUNDING_DATA_UNAVAILABLE_NOT_MATERIALIZED)
        return DatasetFundingBindingMaterializationPreflightResultV0(
            status=PreflightTerminalStatus.FAIL_CLOSED_BOUND_DATA_UNAVAILABLE,
            sha_guard=sha_guard,
            binding_verification=binding_verification,
            dataset_materialization=materialization,
            ready_for_next_pre_evaluation_gate=False,
            economic_evaluation_executed=False,
            economic_evaluation_blocked=True,
            reason_codes=tuple(reasons),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    if not materialization.data_digest_match:
        return DatasetFundingBindingMaterializationPreflightResultV0(
            status=PreflightTerminalStatus.FAIL_CLOSED_BOUND_DATA_UNAVAILABLE,
            sha_guard=sha_guard,
            binding_verification=binding_verification,
            dataset_materialization=materialization,
            ready_for_next_pre_evaluation_gate=False,
            economic_evaluation_executed=False,
            economic_evaluation_blocked=True,
            reason_codes=(REASON_DATA_DIGEST_MISMATCH,),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    if not materialization.funding_manifest_path:
        return DatasetFundingBindingMaterializationPreflightResultV0(
            status=PreflightTerminalStatus.FAIL_CLOSED_FUNDING_DATA_UNAVAILABLE,
            sha_guard=sha_guard,
            binding_verification=binding_verification,
            dataset_materialization=materialization,
            ready_for_next_pre_evaluation_gate=False,
            economic_evaluation_executed=False,
            economic_evaluation_blocked=True,
            reason_codes=(REASON_FUNDING_DATA_UNAVAILABLE_NOT_MATERIALIZED,),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    return DatasetFundingBindingMaterializationPreflightResultV0(
        status=PreflightTerminalStatus.PREFLIGHT_GATE_PASS_READY_FOR_NEXT_PRE_EVALUATION_GATE,
        sha_guard=sha_guard,
        binding_verification=binding_verification,
        dataset_materialization=materialization,
        ready_for_next_pre_evaluation_gate=True,
        economic_evaluation_executed=False,
        economic_evaluation_blocked=True,
        reason_codes=(),
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


__all__ = [
    "BINDING_ORIGIN_MAIN_SHA_ENV_VAR",
    "DatasetFundingBindingMaterializationPreflightResultV0",
    "ExplicitBindingVerificationV0",
    "FAIL_CLOSED_EXPECTED_ORIGIN_MAIN_SHA_BINDING_MISSING",
    "FAIL_CLOSED_ORIGIN_MAIN_SHA_MISMATCH",
    "GO_TOKEN",
    "ORIGIN_MAIN_SHA_BINDING_ENV_VAR",
    "PREFLIGHT_VERSION",
    "PreflightTerminalStatus",
    "extract_explicit_bindings_v0",
    "preflight_result_to_dict",
    "resolve_binding_origin_main_sha_v0",
    "run_dataset_funding_binding_materialization_preflight_v0",
    "verify_binding_origin_main_sha_v0",
    "verify_dataset_binding_explicit_v0",
    "verify_funding_model_binding_explicit_v0",
]
