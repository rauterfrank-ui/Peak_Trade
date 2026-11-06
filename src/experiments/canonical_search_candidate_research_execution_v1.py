"""Explicit bounded Search -> offline provider -> Phase10 -> subsequent Meta input.

New composition of existing owners, derived from original learning master sections
3.1/15/22. Not recovered historical executable bytes, a scheduler, or authority.
A provider's invocation proves neither measurement authenticity nor usefulness.
"""

from __future__ import annotations

import re
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence

from src.experiments.canonical_advanced_search_v1 import (
    CanonicalAdvancedSearchRequestV1,
    canonical_record_payload_v1,
    validate_canonical_advanced_search_v1,
)
from src.experiments.canonical_automated_offline_research_loop_v1 import (
    CanonicalAutomatedOfflineResearchLoopRequestV1,
    run_canonical_automated_offline_research_loop_v1,
    validate_canonical_automated_offline_research_loop_v1,
)
from src.experiments.canonical_comparison_ssot_v1 import ComparisonCompatibilityContractV1
from src.experiments.canonical_experiment_identity_v1 import build_canonical_experiment_identity_v1
from src.experiments.canonical_meta_learning_v1 import MetaLearningPolicyV1
from src.experiments.canonical_research_result_to_meta_input_v1 import (
    ResearchResultMetaInputV1,
    run_research_result_meta_search_feedback_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

ExperimentProviderV1 = Callable[[Mapping[str, Any]], CanonicalAutomatedOfflineResearchLoopRequestV1]


class SearchResearchExecutionError(ValueError):
    """Reject an unbound candidate before Phase10 can write to its stores."""


@dataclass(frozen=True)
class ExecutedSearchResearchV1:
    evidence: Mapping[str, Any]
    next_meta_input: ResearchResultMetaInputV1


class _ReadOnlyList(list):
    """Preserve existing owners' JSON-list contract while rejecting ordinary edits."""

    def _reject(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("execution evidence lists are read-only")

    __setitem__ = __delitem__ = append = clear = extend = insert = pop = remove = _reject
    reverse = sort = __iadd__ = __imul__ = _reject


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return _ReadOnlyList(_freeze(item) for item in value)
    return value


def _time_key(value: str) -> tuple[datetime, int]:
    # Exact nanoseconds and calendar validation at the pre-provider boundary.
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z", value
    ):
        raise SearchResearchExecutionError("EXPLICIT_UTC_TIME_REQUIRED")
    whole, _, fraction = value[:-1].partition(".")
    try:
        return datetime.strptime(whole, "%Y-%m-%dT%H:%M:%S"), int(fraction.ljust(9, "0"))
    except ValueError as exc:
        raise SearchResearchExecutionError("INVALID_CALENDAR_TIME") from exc


def _equal(actual: Any, expected: Any, field: str) -> None:
    if actual != expected:
        raise SearchResearchExecutionError(f"SEARCH_EXECUTION_BINDING_MISMATCH:{field}")


def run_search_candidate_research_execution_v1(
    *,
    search_record: Mapping[str, Any],
    experiment_id: str,
    created_at: str,
    experiment_provider: ExperimentProviderV1,
    provider_ref: str,
    evidence_source_class: str,
    prepared_request_hook: Callable[[CanonicalAutomatedOfflineResearchLoopRequestV1], None]
    | None = None,
) -> ExecutedSearchResearchV1:
    """Invoke one explicit caller-owned offline provider, then the existing loop.

    The provider receives an immutable candidate and must return a complete
    existing Phase10 request containing its actual observations and explicit
    comparison/gap context. It owns source applicability and metric conventions.
    This function does not normalize parameter names, metrics or source classes.
    It is not a sandbox for arbitrary provider code and installs no service.
    """
    search = canonical_record_payload_v1(search_record)
    validate_canonical_advanced_search_v1(search)
    if _time_key(created_at) < _time_key(search["created_at"]):
        raise SearchResearchExecutionError("EXECUTION_PRECEDES_SEARCH")
    for field, value in (
        ("provider_ref", provider_ref),
        ("evidence_source_class", evidence_source_class),
    ):
        if not isinstance(value, str) or not value.strip():
            raise SearchResearchExecutionError(f"EXPLICIT_{field.upper()}_REQUIRED")
    selected = [row for row in search["candidates"] if row["experiment_id"] == experiment_id]
    if len(selected) != 1 or selected[0]["status"] != "PROPOSED":
        raise SearchResearchExecutionError("EXACT_PROPOSED_CANDIDATE_REQUIRED")
    candidate = selected[0]
    request = experiment_provider(_freeze(candidate))
    if not isinstance(request, CanonicalAutomatedOfflineResearchLoopRequestV1):
        raise SearchResearchExecutionError("PHASE10_REQUEST_REQUIRED")
    _equal(request.created_at, created_at, "created_at")
    _equal(request.selected_hypothesis_id, candidate["hypothesis_id"], "selected_hypothesis_id")
    if len(request.hypotheses) != 1:
        raise SearchResearchExecutionError("SINGLE_EXECUTED_HYPOTHESIS_REQUIRED")
    hypothesis = request.hypotheses[0]
    _equal(hypothesis.hypothesis_id, candidate["hypothesis_id"], "hypothesis_id")
    identity = build_canonical_experiment_identity_v1(hypothesis.identity_request)
    _equal(canonical_record_payload_v1(identity), candidate["experiment_identity"], "identity")
    for field in ("parameter_region", "strategy_family", "candidate_ref"):
        _equal(getattr(hypothesis, field), candidate[field], field)
    _equal(hypothesis.regime, candidate["offline_experiment_request"]["regime"], "regime")
    if prepared_request_hook is not None:
        from src.experiments.canonical_research_prepared_execution_v1 import encode_request_value_v1

        original_request = encode_request_value_v1(request)
        prepared_request_hook(request)
        if encode_request_value_v1(request) != original_request:
            raise SearchResearchExecutionError("PREPARED_HOOK_MUTATED_ORIGINAL_REQUEST")
    # All candidate bindings are checked before this owner may persist evidence.
    loop = canonical_record_payload_v1(run_canonical_automated_offline_research_loop_v1(request))
    _equal(loop["selected_experiment_id"], experiment_id, "result.experiment_id")
    frozen_search, frozen_loop = _freeze(search), _freeze(loop)
    body = {
        "schema_version": "canonical_search_candidate_research_execution_v1",
        "search_record": search,
        "research_loop_record": loop,
        "provider_ref": provider_ref,
        "declared_evidence_source_class": evidence_source_class,
        "source_class_authenticated": False,
        "provider_invocations": 1,
        "phase10_invocations": 1,
        "created_at": created_at,
        "experiment_id": experiment_id,
        "hypothesis_id": hypothesis.hypothesis_id,
        "time_horizon": dict(hypothesis.time_horizon),
        "market_universe": list(hypothesis.market_universe),
        "search_identity": search["search_identity"],
        "search_content_sha256": search["integrity"]["content_sha256"],
        "loop_identity": loop["loop_identity"],
        "loop_content_sha256": loop["integrity"]["content_sha256"],
        "productive_apply_authorized": False,
        "scheduler_installed": False,
    }
    body["content_digest"] = compute_content_sha256(body)
    return ExecutedSearchResearchV1(
        evidence=_freeze(body),
        next_meta_input=ResearchResultMetaInputV1(
            frozen_search,
            frozen_loop,
            _freeze(hypothesis.time_horizon),
            tuple(hypothesis.market_universe),
        ),
    )


def run_research_feedback_next_execution_v1(
    inputs: Sequence[ResearchResultMetaInputV1],
    *,
    created_at: str,
    policy: MetaLearningPolicyV1,
    next_search_request: CanonicalAdvancedSearchRequestV1,
    execution_created_at: str,
    experiment_provider: ExperimentProviderV1,
    provider_ref: str,
    evidence_source_class: str,
    compatibility_contract: ComparisonCompatibilityContractV1 | None = None,
) -> ExecutedSearchResearchV1:
    """One feedback step and exactly one proposed candidate; no recursive schedule."""
    if next_search_request.budget != 1:
        raise SearchResearchExecutionError("EXPLICIT_SINGLE_CANDIDATE_BUDGET_REQUIRED")
    if _time_key(execution_created_at) < _time_key(next_search_request.created_at):
        raise SearchResearchExecutionError("EXECUTION_PRECEDES_SEARCH")
    feedback = run_research_result_meta_search_feedback_v1(
        inputs,
        created_at=created_at,
        policy=policy,
        next_search_request=next_search_request,
        compatibility_contract=compatibility_contract,
    )
    search = feedback["next_search_record"]
    proposed = [row for row in search["candidates"] if row["status"] == "PROPOSED"]
    if len(proposed) != 1:
        raise SearchResearchExecutionError("EXACTLY_ONE_PROPOSED_CANDIDATE_REQUIRED")
    executed = run_search_candidate_research_execution_v1(
        search_record=search,
        experiment_id=proposed[0]["experiment_id"],
        created_at=execution_created_at,
        experiment_provider=experiment_provider,
        provider_ref=provider_ref,
        evidence_source_class=evidence_source_class,
    )
    body = {
        "schema_version": "canonical_research_feedback_next_execution_v1",
        "meta_search_feedback": canonical_record_payload_v1(feedback),
        "executed_research": canonical_record_payload_v1(executed.evidence),
        "productive_apply_authorized": False,
    }
    body["content_digest"] = compute_content_sha256(body)
    return ExecutedSearchResearchV1(_freeze(body), executed.next_meta_input)


@dataclass(frozen=True)
class ResearchExecutionGvefReferenceV1:
    artifact_bytes: bytes
    learning_artifact: Mapping[str, Any]


def build_research_execution_gvef_reference_v1(
    executed: ExecutedSearchResearchV1, *, artifact_ref: str
) -> ResearchExecutionGvefReferenceV1:
    """Keep numeric JSON intact; give float-free GVEF a byte-bound reference.

    This does not make GVEF load or judge the numeric artifact. Its existing
    artifact-digest evaluator judges this reference, not learning usefulness.
    """
    if (
        not isinstance(artifact_ref, str)
        or not artifact_ref
        or any(ord(char) < 32 or ord(char) == 127 for char in artifact_ref)
        or "\\" in artifact_ref
        or ":" in artifact_ref
        or artifact_ref.startswith(("/", "~"))
        or any(part in {"", ".", ".."} for part in artifact_ref.split("/"))
        or PurePosixPath(artifact_ref).suffix != ".json"
    ):
        raise SearchResearchExecutionError("RELATIVE_JSON_ARTIFACT_REF_REQUIRED")
    payload = canonical_record_payload_v1(executed.evidence)
    schema = payload.get("schema_version")
    if schema == "canonical_research_feedback_next_execution_v1":
        inner = payload["executed_research"]
    elif schema == "canonical_search_candidate_research_execution_v1":
        inner = payload
    else:
        raise SearchResearchExecutionError("EXECUTION_SCHEMA_REQUIRED")
    for record in (payload, inner):
        expected = compute_content_sha256(
            {k: v for k, v in record.items() if k != "content_digest"}
        )
        if record.get("content_digest") != expected:
            raise SearchResearchExecutionError("EXECUTION_CONTENT_DIGEST_MISMATCH")
    _equal(
        canonical_record_payload_v1(executed.next_meta_input.search_record),
        inner["search_record"],
        "next_meta_input.search_record",
    )
    _equal(
        canonical_record_payload_v1(executed.next_meta_input.research_loop_record),
        inner["research_loop_record"],
        "next_meta_input.research_loop_record",
    )
    _equal(
        dict(executed.next_meta_input.time_horizon),
        inner["time_horizon"],
        "next_meta_input.time_horizon",
    )
    _equal(
        list(executed.next_meta_input.market_universe),
        inner["market_universe"],
        "next_meta_input.market_universe",
    )
    artifact_bytes = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    reference = {
        "schema_version": "research_execution_gvef_reference_v1",
        "artifact_ref": artifact_ref,
        "payload_encoding": "UTF8_JSON_NUMBERS_PRESERVED",
        "payload_sha256": hashlib.sha256(artifact_bytes).hexdigest(),
        "execution_content_digest": payload["content_digest"],
        "experiment_id": inner["experiment_id"],
        "loop_identity": inner["loop_identity"],
        "search_identity": inner["search_identity"],
        "declared_evidence_source_class": inner["declared_evidence_source_class"],
        "source_class_authenticated": False,
        "TEST_ONLY_SYNTHETIC": inner["declared_evidence_source_class"] == "TEST_ONLY_SYNTHETIC",
        "gvef_scope": "REFERENCE_ARTIFACT_BINDING_NOT_NUMERIC_QUALITY_EVALUATION",
        "productive_apply_authorized": False,
    }
    return ResearchExecutionGvefReferenceV1(artifact_bytes, _freeze(reference))


def read_research_execution_gvef_reference_v1(
    reference: Mapping[str, Any], *, artifact_bytes: bytes
) -> ExecutedSearchResearchV1:
    """Verify exact bytes and existing owner contracts before later Meta reuse.

    No path resolution or IO; caller supplies bytes from its chosen artifact
    store. GVEF reference validity is never treated as data authentication.
    """
    if hashlib.sha256(artifact_bytes).hexdigest() != reference.get("payload_sha256"):
        raise SearchResearchExecutionError("GVEF_PAYLOAD_BYTE_DIGEST_MISMATCH")
    try:
        payload = json.loads(artifact_bytes.decode("utf-8"))
        if payload["schema_version"] == "canonical_research_feedback_next_execution_v1":
            inner = payload["executed_research"]
        else:
            inner = payload
        result = ExecutedSearchResearchV1(
            _freeze(payload),
            ResearchResultMetaInputV1(
                _freeze(inner["search_record"]),
                _freeze(inner["research_loop_record"]),
                _freeze(inner["time_horizon"]),
                tuple(inner["market_universe"]),
            ),
        )
    except (ValueError, KeyError, TypeError, UnicodeError) as exc:
        raise SearchResearchExecutionError("INVALID_EXECUTION_ARTIFACT") from exc
    rebuilt = build_research_execution_gvef_reference_v1(
        result, artifact_ref=reference.get("artifact_ref")
    )
    _equal(artifact_bytes, rebuilt.artifact_bytes, "canonical_artifact_bytes")
    _equal(
        canonical_record_payload_v1(reference),
        canonical_record_payload_v1(rebuilt.learning_artifact),
        "gvef_reference",
    )
    validate_canonical_advanced_search_v1(result.next_meta_input.search_record)
    validate_canonical_automated_offline_research_loop_v1(
        result.next_meta_input.research_loop_record
    )
    _equal(inner["search_identity"], inner["search_record"]["search_identity"], "search_identity")
    _equal(inner["loop_identity"], inner["research_loop_record"]["loop_identity"], "loop_identity")
    _equal(
        inner["experiment_id"],
        inner["research_loop_record"]["selected_experiment_id"],
        "experiment_id",
    )
    return result
