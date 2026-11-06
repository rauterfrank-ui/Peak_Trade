"""Caller-bounded measured research with durable feedback, never productive apply.

Additive composition of original master sections 3.1/15/22 and existing Phase1-12
owners. New implementation, not recovered historical executable bytes. Each call
performs at most one explicit experiment. Data, gap truth and all policies remain
caller-owned; there is no service, market loader or autonomous champion swap.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping, Sequence

import pandas as pd

from src.experiments.canonical_advanced_search_v1 import (
    CanonicalAdvancedSearchRequestV1,
    build_canonical_advanced_search_v1,
    canonical_record_payload_v1,
)
from src.experiments.canonical_comparison_ssot_v1 import ComparisonCandidateV1
from src.experiments.canonical_experiment_identity_v1 import domain_separated_digest
from src.experiments.canonical_failure_memory_v1 import derive_hypothesis_fingerprint_v1
from src.experiments.canonical_meta_learning_v1 import MetaLearningPolicyV1
from src.experiments.canonical_native_research_measurements_v1 import (
    NativeResearchExperimentProviderV1,
    NativeResearchMeasurementsV1,
    measure_native_research_candidate_v1,
    native_research_input_hashes_v1,
)
from src.experiments.canonical_robustness_suite_v1 import (
    CanonicalRobustnessSuiteRequestV1,
    build_canonical_robustness_evidence_v1,
    derive_robustness_policy_digest_v1,
)
from src.experiments.canonical_search_candidate_research_execution_v1 import (
    ExecutedSearchResearchV1,
    build_research_execution_gvef_reference_v1,
    read_research_execution_gvef_reference_v1,
    run_search_candidate_research_execution_v1,
)
from src.experiments.canonical_research_result_to_meta_input_v1 import (
    run_research_result_meta_search_feedback_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from src.backtest.mv2_research_wiring_v1 import (
    STEP29L_INSTRUMENT_ADMISSION_LEGACY_RESEARCH_SINGLETON_V0,
    _ensure_supported_instrument,
)


class NativeResearchSessionError(ValueError):
    """No evidence, context or durable identity is silently substituted."""


def _plain(value: Any) -> Any:
    return canonical_record_payload_v1(value)


def _bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _validate_measurement(receipt: Mapping[str, Any], executed: ExecutedSearchResearchV1) -> None:
    body = _plain(receipt)
    if body.get("content_digest") != compute_content_sha256(
        {k: v for k, v in body.items() if k != "content_digest"}
    ):
        raise NativeResearchSessionError("MEASUREMENT_DIGEST_MISMATCH")
    loop = executed.next_meta_input.research_loop_record
    if (body.get("experiment_id"), body.get("identity_digest")) != (
        loop["selected_experiment_id"],
        loop["experiment_record"]["experiment_identity"]["identity_digest"],
    ):
        raise NativeResearchSessionError("MEASUREMENT_EXECUTION_IDENTITY_MISMATCH")
    if body.get("source_authenticated") is not False:
        raise NativeResearchSessionError("SOURCE_AUTHENTICATION_NOT_ESTABLISHED")
    _ensure_supported_instrument(
        body["instrument_id"],
        admission_mode=body.get(
            "instrument_admission_mode", STEP29L_INSTRUMENT_ADMISSION_LEGACY_RESEARCH_SINGLETON_V0
        ),
    )
    identity = loop["experiment_record"]["experiment_identity"]
    if identity["strategy_params_digest"] != domain_separated_digest(
        "strategy_params", body["parameters"]
    ) or identity["dataset_digest"] != domain_separated_digest(
        "dataset", {"source_digest": body["source_hashes"]["dataset_sha256"]}
    ):
        raise NativeResearchSessionError("MEASUREMENT_INPUT_IDENTITY_MISMATCH")
    runs = {row["split"]: row for row in body["runs"]}
    if body["engine_invocations"] != 4 or set(runs) != {"full", "train", "validation", "holdout"}:
        raise NativeResearchSessionError("FOUR_ACTUAL_MEASUREMENTS_REQUIRED")
    for split, name in (
        ("full", "engine_pre_funding_sharpe"),
        ("holdout", "engine_pre_funding_oos_sharpe"),
    ):
        stat = runs[split]["statistics"]["sharpe"]
        if (
            stat["status"] != "COMPUTED"
            or loop["experiment_record"]["metrics"].get(name) != stat["value"]
        ):
            raise NativeResearchSessionError("MEASUREMENT_METRIC_BINDING_MISMATCH")


@dataclass(frozen=True)
class MeasuredNativeResearchChampionV1:
    candidate: ComparisonCandidateV1
    measurements: NativeResearchMeasurementsV1
    robustness_evidence: Mapping[str, Any]


def measure_native_research_champion_v1(
    *,
    candidate: Mapping[str, Any],
    bars: pd.DataFrame,
    cfg: Mapping[str, Any],
    strategy_id: str,
    strategy_version: str,
    instrument_id: str,
    time_horizon: Mapping[str, str],
    market_universe: Sequence[str],
    robustness_policy: Mapping[str, Any],
    created_at: str,
    instrument_admission_mode: str = STEP29L_INSTRUMENT_ADMISSION_LEGACY_RESEARCH_SINGLETON_V0,
) -> MeasuredNativeResearchChampionV1:
    """Measure an explicitly named research baseline and evaluate its real observations.

    A BLOCKED/FAIL robustness verdict is retained. Version declarations in the
    comparison candidate come from the actual Phase4 output, not missing defaults.
    """
    if (
        set(time_horizon) != {"start", "end"}
        or bars.empty
        or (
            pd.Timestamp(time_horizon["start"]) != bars.index[0]
            or pd.Timestamp(time_horizon["end"]) != bars.index[-1]
        )
    ):
        raise NativeResearchSessionError("CHAMPION_BAR_HORIZON_MISMATCH")
    identity = candidate["experiment_identity"]
    fingerprint = derive_hypothesis_fingerprint_v1(
        identity_digest=identity["identity_digest"],
        hypothesis_id=candidate["hypothesis_id"],
        parameter_region=candidate["parameter_region"],
        regime=candidate["offline_experiment_request"]["regime"],
        robustness_policy_digest=derive_robustness_policy_digest_v1(robustness_policy),
        parent_lineage_ref=identity["parent_lineage"]["parent_lineage_ref"],
    )
    if fingerprint != candidate["hypothesis_fingerprint"]:
        raise NativeResearchSessionError("CHAMPION_SEARCH_POLICY_FINGERPRINT_MISMATCH")
    hashes = native_research_input_hashes_v1(bars, cfg)
    measured = measure_native_research_candidate_v1(
        candidate=candidate,
        bars=bars,
        cfg=cfg,
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        instrument_id=instrument_id,
        instrument_admission_mode=instrument_admission_mode,
        expected_dataset_sha256=hashes["dataset_sha256"],
        expected_config_sha256=hashes["config_sha256"],
    )

    def ref(field: str) -> dict[str, str]:
        return {"kind": "IDENTITY_DIGEST_BOUND", "digest": identity[field]}

    robustness = build_canonical_robustness_evidence_v1(
        CanonicalRobustnessSuiteRequestV1(
            experiment_identity=identity,
            candidate_ref=candidate["candidate_ref"],
            dataset_ref=ref("dataset_digest"),
            split_policy_ref=ref("split_policy_digest"),
            cost_model_ref=ref("cost_model_digest"),
            risk_policy_ref=ref("risk_policy_digest"),
            seed=identity["seed"],
            created_at=created_at,
            robustness_policy=robustness_policy,
            observations=measured.observations.robustness_observations,
            hypothesis_id=candidate["hypothesis_id"],
            regime=candidate["offline_experiment_request"]["regime"],
            parameter_region=candidate["parameter_region"],
            experiment_id=candidate["experiment_id"],
            promotion_intent="FORBIDDEN",
        )
    )
    return MeasuredNativeResearchChampionV1(
        ComparisonCandidateV1(
            experiment_identity=identity,
            robustness_suite_version=robustness["robustness_suite_version"],
            metric_definitions=robustness["metric_definition_version"],
            time_horizon=dict(time_horizon),
            market_universe=tuple(market_universe),
            experiment_id=candidate["experiment_id"],
            evidence_refs=(
                {
                    "kind": "ROBUSTNESS_EVIDENCE",
                    "ref": candidate["candidate_ref"],
                    "digest": robustness["integrity"]["content_sha256"],
                },
            ),
        ),
        measured,
        robustness,
    )


class NativeResearchExecutionArchiveV1:
    """Atomic append-only packets: exact numeric execution plus measured provenance.

    Single-packet creation is atomic. Existing Phase2/3/7 stores are independent
    owners; this archive does not claim a distributed transaction across them.
    """

    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()
        if self.root.exists() and not self.root.is_dir():
            raise NativeResearchSessionError("ARCHIVE_DIRECTORY_REQUIRED")

    def _path(self, artifact_id: str) -> Path:
        if not isinstance(artifact_id, str) or not re.fullmatch(r"[0-9a-f]{64}", artifact_id):
            raise NativeResearchSessionError("CONTENT_ADDRESS_REQUIRED")
        path = self.root / (artifact_id + ".json")
        if path.is_symlink():
            raise NativeResearchSessionError("ARCHIVE_SYMLINK_FORBIDDEN")
        return path

    def append(
        self, executed: ExecutedSearchResearchV1, measurement_receipt: Mapping[str, Any]
    ) -> str:
        _validate_measurement(measurement_receipt, executed)
        reference = build_research_execution_gvef_reference_v1(
            executed, artifact_ref="execution.json"
        )
        body = {
            "schema_version": "native_research_execution_archive_packet_v1",
            "gvef_reference": _plain(reference.learning_artifact),
            "execution_utf8": reference.artifact_bytes.decode(),
            "measurement_receipt": _plain(measurement_receipt),
        }
        raw = _bytes(body)
        artifact_id = hashlib.sha256(raw).hexdigest()
        path = self._path(artifact_id)
        self.root.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".packet-", dir=self.root)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, path)
            except FileExistsError:
                if path.read_bytes() != raw:
                    raise NativeResearchSessionError("ARCHIVE_CONTENT_CONFLICT")
            directory_fd = os.open(self.root, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            os.unlink(temporary)
        self.get(artifact_id)
        return artifact_id

    def get(self, artifact_id: str) -> ExecutedSearchResearchV1:
        raw = self._path(artifact_id).read_bytes()
        if hashlib.sha256(raw).hexdigest() != artifact_id:
            raise NativeResearchSessionError("ARCHIVE_BYTE_DIGEST_MISMATCH")
        body = json.loads(raw)
        if body.get("schema_version") != "native_research_execution_archive_packet_v1":
            raise NativeResearchSessionError("ARCHIVE_SCHEMA_MISMATCH")
        executed = read_research_execution_gvef_reference_v1(
            body["gvef_reference"], artifact_bytes=body["execution_utf8"].encode()
        )
        _validate_measurement(body["measurement_receipt"], executed)
        return executed


@dataclass(frozen=True)
class NativeResearchSessionStepV1:
    search_record: Mapping[str, Any]
    feedback_record: Mapping[str, Any] | None
    execution: ExecutedSearchResearchV1 | None
    artifact_id: str | None
    status: str


def run_native_research_session_step_v1(
    *,
    search_request: CanonicalAdvancedSearchRequestV1,
    provider: NativeResearchExperimentProviderV1,
    archive: NativeResearchExecutionArchiveV1,
    prior_artifact_ids: Sequence[str],
    provider_ref: str,
    evidence_source_class: str,
    meta_created_at: str | None = None,
    meta_policy: MetaLearningPolicyV1 | None = None,
) -> NativeResearchSessionStepV1:
    """One explicit measured/reused/resumed trial, with a shared existing-memory lease."""
    kwargs = dict(
        search_request=search_request,
        provider=provider,
        archive=archive,
        prior_artifact_ids=prior_artifact_ids,
        provider_ref=provider_ref,
        evidence_source_class=evidence_source_class,
        meta_created_at=meta_created_at,
        meta_policy=meta_policy,
    )
    from src.experiments.canonical_research_prepared_execution_v1 import research_step_lease_v1

    ctx = kwargs["provider"].context
    _ensure_supported_instrument(
        provider.instrument_id, admission_mode=ctx.instrument_admission_mode
    )
    if any(
        getattr(ctx, n) is None
        for n in ("experiment_memory_store", "failure_memory_store", "reality_gap_store")
    ):
        raise NativeResearchSessionError("EXPLICIT_EXISTING_MEMORY_STORES_REQUIRED")
    with research_step_lease_v1(ctx):
        return _run_native_research_session_step_locked_v1(**kwargs)


def _run_native_research_session_step_locked_v1(
    *,
    search_request: CanonicalAdvancedSearchRequestV1,
    provider: NativeResearchExperimentProviderV1,
    archive: NativeResearchExecutionArchiveV1,
    prior_artifact_ids: Sequence[str],
    provider_ref: str,
    evidence_source_class: str,
    meta_created_at: str | None = None,
    meta_policy: MetaLearningPolicyV1 | None = None,
) -> NativeResearchSessionStepV1:
    """Resume explicit measured packets and read current Failure/Gap owners before Search.

    At most one candidate executes. Exhaustion is a result, not forced retesting.
    An explicit retest follows existing Search/Phase10 policy. No clocks, implicit
    gap values, automatic champion replacement or ongoing background loop.
    """
    if search_request.budget != 1:
        raise NativeResearchSessionError("EXPLICIT_SINGLE_ATTEMPT_BUDGET_REQUIRED")
    ctx = provider.context
    if any(
        store is None
        for store in (ctx.experiment_memory_store, ctx.failure_memory_store, ctx.reality_gap_store)
    ):
        raise NativeResearchSessionError("EXPLICIT_EXISTING_MEMORY_STORES_REQUIRED")
    if len(set(prior_artifact_ids)) != len(prior_artifact_ids):
        raise NativeResearchSessionError("DUPLICATE_PRIOR_ARTIFACT_FORBIDDEN")
    # Do not permit a second policy/identity under the provider's exact template.
    if search_request.identity_template != ctx.identity_template:
        raise NativeResearchSessionError("SEARCH_PROVIDER_TEMPLATE_MISMATCH")
    if search_request.retest_reason != ctx.retest_reason:
        raise NativeResearchSessionError("SEARCH_PROVIDER_RETEST_REASON_MISMATCH")
    from src.experiments.canonical_research_prepared_execution_v1 import (
        journal_root_v1,
        intent_digest_v1,
        read_v1,
        finish_prepared_v1,
        publish_v1,
        encode_request_value_v1,
        digest_v1,
        verify_owner_records_v1,
        ResearchRecoveryError,
    )
    from src.experiments.canonical_research_preflight_v1 import research_preflight_v1

    intent = intent_digest_v1(
        search_request, prior_artifact_ids, provider_ref, evidence_source_class, meta_policy
    )
    context_digest = digest_v1(
        encode_request_value_v1(
            replace(ctx, created_at="ORIGINAL_CLOCK_RETAINED", existing_failure_records=())
        )
    )
    request_key = digest_v1(
        {
            "intent": intent,
            "search_created_at": search_request.created_at,
            "execution_created_at": ctx.created_at,
            "meta_created_at": meta_created_at,
        }
    )
    incomplete = []
    for path in sorted(journal_root_v1(ctx).glob("*/started.json")):
        started = read_v1(path)
        if (path.parent / "ack.json").exists() and started["request_key"] == request_key:
            if started["context_digest"] != context_digest:
                raise ResearchRecoveryError("PREPARED_ORIGINAL_CONTEXT_CONFLICT")
            original = finish_prepared_v1(path.parent, archive, ctx)
            candidate = next(
                c
                for c in started["search"]["candidates"]
                if c["experiment_id"] == started["experiment_id"]
            )
            _require_reuse_inputs_v1(provider, candidate, archive, original.artifact_id)
            return original
        if not (path.parent / "ack.json").exists():
            if started["intent_digest"] == intent:
                if started["context_digest"] != context_digest:
                    raise ResearchRecoveryError("PREPARED_ORIGINAL_CONTEXT_CONFLICT")
                incomplete.append(path.parent)
    if len(incomplete) > 1:
        raise ResearchRecoveryError("MULTIPLE_INCOMPLETE_RESEARCH_STEPS")
    if incomplete:
        if not (incomplete[0] / "prepared.json").exists():
            raise ResearchRecoveryError("MEASUREMENT_UNCERTAIN_ORIGINAL_REQUEST_MISSING")
        return finish_prepared_v1(incomplete[0], archive, ctx)
    failures = ctx.failure_memory_store.list_records()
    gaps = ctx.reality_gap_store.list_records()
    # Caller-supplied lists are accepted only if identical to the durable owners.
    for supplied, stored in (
        (search_request.failure_records, failures),
        (ctx.existing_failure_records, failures),
        (search_request.reality_gap_records, gaps),
    ):
        if supplied and _plain(supplied) != _plain(stored):
            raise NativeResearchSessionError("DURABLE_MEMORY_CONTEXT_MISMATCH")
    request = replace(
        search_request, failure_records=tuple(failures), reality_gap_records=tuple(gaps)
    )
    feedback = None
    if prior_artifact_ids:
        if meta_created_at is None or meta_policy is None:
            raise NativeResearchSessionError("EXPLICIT_META_CONTEXT_REQUIRED")
        inputs = [archive.get(key).next_meta_input for key in prior_artifact_ids]
        feedback = run_research_result_meta_search_feedback_v1(
            inputs,
            created_at=meta_created_at,
            policy=meta_policy,
            next_search_request=request,
            compatibility_contract=ctx.compatibility_contract,
        )
        search = feedback["next_search_record"]
    else:
        if meta_created_at is not None or meta_policy is not None:
            raise NativeResearchSessionError("META_WITHOUT_PRIOR_EVIDENCE_FORBIDDEN")
        search = build_canonical_advanced_search_v1(request)
    proposed = [row for row in search["candidates"] if row["status"] == "PROPOSED"]
    if not proposed:
        return NativeResearchSessionStepV1(search, feedback, None, None, "NO_PROPOSED_CANDIDATE")
    if len(proposed) != 1:
        raise NativeResearchSessionError("SINGLE_PROPOSED_CANDIDATE_REQUIRED")
    selected = proposed[0]
    step_path = journal_root_v1(ctx) / selected["experiment_id"]
    disposition, reused = research_preflight_v1(
        candidate=selected,
        context=ctx,
        archive=archive,
        step_path=step_path,
        retest_reason=search_request.retest_reason,
    )
    if disposition == "REUSE_ARCHIVED":
        key, original = reused
        if (
            original.evidence["provider_ref"],
            original.evidence["declared_evidence_source_class"],
        ) != (provider_ref, evidence_source_class):
            raise ResearchRecoveryError("RESEARCH_PROVIDER_OR_SOURCE_CONFLICT")
        _require_reuse_inputs_v1(provider, selected, archive, key)
        return NativeResearchSessionStepV1(
            original.next_meta_input.search_record, None, original, key, disposition
        )
    if disposition == "RESUME_INCOMPLETE":
        return finish_prepared_v1(step_path, archive, ctx)
    started = {
        "schema_version": "research_started.v1",
        "intent_digest": intent,
        "context_digest": context_digest,
        "request_key": request_key,
        "experiment_id": selected["experiment_id"],
        "search": _plain(search),
        "feedback": _plain(feedback),
        "provider_ref": provider_ref,
        "source_class": evidence_source_class,
    }
    publish_v1(step_path / "started.json", started)
    captured = []
    observer = provider.measurement_observer

    def collect(measurement: NativeResearchMeasurementsV1) -> None:
        captured.append(_plain(measurement.receipt))
        if observer is not None:
            observer(measurement)

    bound_provider = replace(
        provider,
        context=replace(ctx, existing_failure_records=tuple(failures)),
        measurement_observer=collect,
    )

    def prepare(original_request):
        if len(captured) != 1:
            raise NativeResearchSessionError("EXACTLY_ONE_MEASUREMENT_RECEIPT_REQUIRED")
        dry = replace(
            original_request,
            experiment_memory_store=None,
            failure_memory_store=None,
            reality_gap_store=None,
        )
        validated = run_search_candidate_research_execution_v1(
            search_record=search,
            experiment_id=selected["experiment_id"],
            created_at=original_request.created_at,
            experiment_provider=lambda candidate: dry,
            provider_ref=provider_ref,
            evidence_source_class=evidence_source_class,
        )
        _validate_measurement(captured[0], validated)
        publish_v1(
            step_path / "prepared.json",
            {
                "schema_version": "research_prepared_execution.v1",
                "started_digest": digest_v1(started),
                "archive_root": str(archive.root),
                "request": encode_request_value_v1(original_request),
                "receipt": captured[0],
            },
        )

    executed = run_search_candidate_research_execution_v1(
        search_record=search,
        experiment_id=proposed[0]["experiment_id"],
        created_at=ctx.created_at,
        experiment_provider=bound_provider,
        prepared_request_hook=prepare,
        provider_ref=provider_ref,
        evidence_source_class=evidence_source_class,
    )
    if len(captured) != 1:
        raise NativeResearchSessionError("EXACTLY_ONE_MEASUREMENT_RECEIPT_REQUIRED")
    key = archive.append(executed, captured[0])
    verify_owner_records_v1(archive.get(key), ctx)
    publish_v1(
        step_path / "ack.json",
        {"artifact_id": key, "prepared_digest": digest_v1(read_v1(step_path / "prepared.json"))},
    )
    return NativeResearchSessionStepV1(search, feedback, executed, key, "EXECUTED_AND_ARCHIVED")


def _require_reuse_inputs_v1(provider, selected, archive, key):
    from src.experiments.canonical_research_prepared_execution_v1 import ResearchRecoveryError

    ctx = provider.context
    receipt = json.loads((archive.root / (key + ".json")).read_bytes())["measurement_receipt"]
    if (
        receipt.get(
            "instrument_admission_mode", STEP29L_INSTRUMENT_ADMISSION_LEGACY_RESEARCH_SINGLETON_V0
        )
        != ctx.instrument_admission_mode
    ):
        raise ResearchRecoveryError("RESEARCH_REUSE_INSTRUMENT_ADMISSION_CONFLICT")
    cfg = _plain(provider.base_cfg)
    cfg["economic_evaluation_v1"]["strategy_params"] = {
        **dict(ctx.identity_template.strategy_params),
        **dict(selected["parameter_region"]),
    }
    if native_research_input_hashes_v1(provider.bars, cfg) != receipt["source_hashes"] or (
        provider.strategy_id,
        provider.strategy_version,
        provider.instrument_id,
    ) != (receipt["strategy_id"], receipt["strategy_version"], receipt["instrument_id"]):
        raise ResearchRecoveryError("RESEARCH_REUSE_INPUT_CONFLICT")
