"""Productive producer → typed adapter → Component A termination (no B/DP bypass)."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    EvidenceProducerFamilyV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.adjudicator_v1 import (
    adjudicate_evidence_intake_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.ledger_v1 import (
    AdjudicationLedgerV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.models_v1 import (
    EvidenceIntakeAdjudicationContextV1,
    EvidenceIntakeRecordV1,
    MasterV2EvidenceAdjudicationResultV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.registry_v1 import (
    load_producer_registry_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.adapters_v1 import (
    ProducerAdapterError,
    adapt_learning_conditioned_evaluative_v1,
    adapt_market_intelligence_market_context_v1,
    adapt_meta_learning_routed_evidence_v1,
    adapt_optimization_envelope_evidence_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.meta_learning_routed_evidence_v1 import (
    SCHEMA_VERSION as META_ROUTED_SCHEMA,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.optimization_envelope_evidence_v1 import (
    SCHEMA_VERSION as OPT_ENVELOPE_SCHEMA,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.constants_v1 import (
    LEARNING_PRODUCER_ID,
    META_LEARNING_PRODUCER_ID,
    MI_PRODUCER_ID,
    OPTIMIZATION_PRODUCER_ID,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.models_v1 import (
    ProducerArtifactV1,
    ProducerEvidenceTerminationContextV1,
    ProducerIngressProvenanceV1,
    ProducerIngressTerminationResultV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.promotion_admission_v1 import (
    load_promotion_admissions_v1,
    load_schema_binding_dispositions_v1,
    lookup_promotion_admission_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.reason_codes_v1 import (
    ProducerIngressFailureCodeV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    REJECT_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    BoundedL6EvidenceKindV1,
)


def _reject_at_ingress(
    *,
    producer_class: EvidenceProducerFamilyV1,
    producer_id: str,
    reason: str,
    delivery_id: str = "",
) -> ProducerIngressTerminationResultV1:
    adjudication = MasterV2EvidenceAdjudicationResultV1(
        delivery_id=delivery_id,
        disposition=REJECT_DISPOSITION,
        reason_codes=(reason,),
        adjudication_digest="",
        envelope=None,
        envelope_digest=None,
        dedup_replay=False,
    )
    return ProducerIngressTerminationResultV1(
        producer_class=producer_class,
        producer_id=producer_id,
        adjudication=adjudication,
        ingress_provenance=ProducerIngressProvenanceV1(
            adapter_id="p5_ingress_v1",
            source_schema_version="",
            source_content_digest="",
            producer_class=producer_class,
        ),
        blocked_at_promotion=reason
        == ProducerIngressFailureCodeV1.PROMOTION_ADMISSION_ABSENT.value,
        promotion_block_reason=reason
        if reason == ProducerIngressFailureCodeV1.PROMOTION_ADMISSION_ABSENT.value
        else None,
    )


def _adjudicate_intake(
    intake: EvidenceIntakeRecordV1,
    *,
    termination: ProducerEvidenceTerminationContextV1,
    repo_root: Path | None,
    ledger: AdjudicationLedgerV1 | None,
    provenance: ProducerIngressProvenanceV1,
) -> ProducerIngressTerminationResultV1:
    evaluated = termination.evaluated_at_unix
    if evaluated is None:
        evaluated = float(intake.observed_at_unix) + 1.0
    ctx = EvidenceIntakeAdjudicationContextV1(
        evaluated_at_unix=evaluated,
        expected_instrument=termination.instrument,
        expected_market_observation_epoch=termination.market_observation_epoch,
    )
    registry = load_producer_registry_v1(repo_root or Path(__file__).resolve().parents[3])
    result = adjudicate_evidence_intake_v1(
        intake,
        context=ctx,
        registry=registry,
        ledger=ledger or AdjudicationLedgerV1(),
    )
    return ProducerIngressTerminationResultV1(
        producer_class=intake.producer_family,
        producer_id=intake.producer_id,
        adjudication=result,
        ingress_provenance=provenance,
    )


def terminate_market_intelligence_market_context_at_a_v1(
    artifact: ProducerArtifactV1 | None,
    *,
    termination: ProducerEvidenceTerminationContextV1 | None,
    repo_root: Path | None = None,
    ledger: AdjudicationLedgerV1 | None = None,
) -> ProducerIngressTerminationResultV1:
    if artifact is None or termination is None:
        return _reject_at_ingress(
            producer_class=EvidenceProducerFamilyV1.MARKET_INTELLIGENCE,
            producer_id=MI_PRODUCER_ID if artifact is None else "",
            reason=ProducerIngressFailureCodeV1.TERMINATION_CONTEXT_MISSING.value
            if termination is None
            else ProducerIngressFailureCodeV1.ARTIFACT_MISSING.value,
        )
    try:
        intake = adapt_market_intelligence_market_context_v1(artifact, termination=termination)
    except ProducerAdapterError as exc:
        return _reject_at_ingress(
            producer_class=EvidenceProducerFamilyV1.MARKET_INTELLIGENCE,
            producer_id=MI_PRODUCER_ID,
            reason=str(exc),
        )
    provenance = ProducerIngressProvenanceV1(
        adapter_id="market_intelligence_market_context_v1",
        source_schema_version="market_context_v1",
        source_content_digest=intake.source_evidence_digest,
        producer_class=EvidenceProducerFamilyV1.MARKET_INTELLIGENCE,
    )
    return _adjudicate_intake(
        intake,
        termination=termination,
        repo_root=repo_root,
        ledger=ledger,
        provenance=provenance,
    )


def terminate_learning_conditioned_evaluative_at_a_v1(
    artifact: ProducerArtifactV1 | None,
    *,
    termination: ProducerEvidenceTerminationContextV1 | None,
    repo_root: Path | None = None,
    ledger: AdjudicationLedgerV1 | None = None,
) -> ProducerIngressTerminationResultV1:
    if artifact is None or termination is None:
        return _reject_at_ingress(
            producer_class=EvidenceProducerFamilyV1.LEARNING,
            producer_id=LEARNING_PRODUCER_ID,
            reason=ProducerIngressFailureCodeV1.TERMINATION_CONTEXT_MISSING.value
            if termination is None
            else ProducerIngressFailureCodeV1.ARTIFACT_MISSING.value,
        )
    try:
        intake = adapt_learning_conditioned_evaluative_v1(artifact, termination=termination)
    except ProducerAdapterError as exc:
        return _reject_at_ingress(
            producer_class=EvidenceProducerFamilyV1.LEARNING,
            producer_id=LEARNING_PRODUCER_ID,
            reason=str(exc),
        )
    provenance = ProducerIngressProvenanceV1(
        adapter_id="learning_conditioned_evaluative_v1",
        source_schema_version="mi_learning_evidence_record_v1",
        source_content_digest=intake.source_evidence_digest,
        producer_class=EvidenceProducerFamilyV1.LEARNING,
    )
    return _adjudicate_intake(
        intake,
        termination=termination,
        repo_root=repo_root,
        ledger=ledger,
        provenance=provenance,
    )


def terminate_optimization_envelope_at_a_v1(
    artifact: ProducerArtifactV1 | None,
    *,
    source_artifact_schema: str,
    source_content_digest: str,
    termination: ProducerEvidenceTerminationContextV1 | None,
    repo_root: Path | None = None,
    ledger: AdjudicationLedgerV1 | None = None,
) -> ProducerIngressTerminationResultV1:
    root = repo_root or Path(__file__).resolve().parents[3]
    admissions = load_promotion_admissions_v1(root)
    schema_bindings = load_schema_binding_dispositions_v1(root)
    ok, reason = lookup_promotion_admission_v1(
        producer_family=EvidenceProducerFamilyV1.OPTIMIZATION,
        source_artifact_schema=source_artifact_schema,
        source_content_digest=source_content_digest,
        promoted_evidence_kind=BoundedL6EvidenceKindV1.OPTIMIZATION_ENVELOPE_EVIDENCE_V1.value,
        admissions=admissions,
        schema_bindings=schema_bindings,
    )
    if not ok:
        return _reject_at_ingress(
            producer_class=EvidenceProducerFamilyV1.OPTIMIZATION,
            producer_id=OPTIMIZATION_PRODUCER_ID,
            reason=reason or ProducerIngressFailureCodeV1.PROMOTION_ADMISSION_ABSENT.value,
        )
    if artifact is None or termination is None:
        return _reject_at_ingress(
            producer_class=EvidenceProducerFamilyV1.OPTIMIZATION,
            producer_id=OPTIMIZATION_PRODUCER_ID,
            reason=ProducerIngressFailureCodeV1.ARTIFACT_MISSING.value
            if artifact is None
            else ProducerIngressFailureCodeV1.TERMINATION_CONTEXT_MISSING.value,
        )
    if str(artifact.get("schema_version") or "") != OPT_ENVELOPE_SCHEMA:
        return _reject_at_ingress(
            producer_class=EvidenceProducerFamilyV1.OPTIMIZATION,
            producer_id=OPTIMIZATION_PRODUCER_ID,
            reason=ProducerIngressFailureCodeV1.ARTIFACT_MALFORMED.value,
        )
    try:
        intake = adapt_optimization_envelope_evidence_v1(artifact, termination=termination)
    except ProducerAdapterError as exc:
        return _reject_at_ingress(
            producer_class=EvidenceProducerFamilyV1.OPTIMIZATION,
            producer_id=OPTIMIZATION_PRODUCER_ID,
            reason=str(exc),
        )
    provenance = ProducerIngressProvenanceV1(
        adapter_id="optimization_envelope_evidence_v1",
        source_schema_version=OPT_ENVELOPE_SCHEMA,
        source_content_digest=intake.source_evidence_digest,
        producer_class=EvidenceProducerFamilyV1.OPTIMIZATION,
    )
    return _adjudicate_intake(
        intake,
        termination=termination,
        repo_root=root,
        ledger=ledger,
        provenance=provenance,
    )


def terminate_meta_learning_routed_at_a_v1(
    artifact: ProducerArtifactV1 | None,
    *,
    source_artifact_schema: str,
    source_content_digest: str,
    termination: ProducerEvidenceTerminationContextV1 | None,
    repo_root: Path | None = None,
    ledger: AdjudicationLedgerV1 | None = None,
) -> ProducerIngressTerminationResultV1:
    root = repo_root or Path(__file__).resolve().parents[3]
    admissions = load_promotion_admissions_v1(root)
    schema_bindings = load_schema_binding_dispositions_v1(root)
    ok, reason = lookup_promotion_admission_v1(
        producer_family=EvidenceProducerFamilyV1.META_LEARNING,
        source_artifact_schema=source_artifact_schema,
        source_content_digest=source_content_digest,
        promoted_evidence_kind=BoundedL6EvidenceKindV1.META_LEARNING_ROUTED_EVIDENCE_V1.value,
        admissions=admissions,
        schema_bindings=schema_bindings,
    )
    if not ok:
        return _reject_at_ingress(
            producer_class=EvidenceProducerFamilyV1.META_LEARNING,
            producer_id=META_LEARNING_PRODUCER_ID,
            reason=reason or ProducerIngressFailureCodeV1.PROMOTION_ADMISSION_ABSENT.value,
        )
    if artifact is None or termination is None:
        return _reject_at_ingress(
            producer_class=EvidenceProducerFamilyV1.META_LEARNING,
            producer_id=META_LEARNING_PRODUCER_ID,
            reason=ProducerIngressFailureCodeV1.ARTIFACT_MISSING.value
            if artifact is None
            else ProducerIngressFailureCodeV1.TERMINATION_CONTEXT_MISSING.value,
        )
    if str(artifact.get("schema_version") or "") != META_ROUTED_SCHEMA:
        return _reject_at_ingress(
            producer_class=EvidenceProducerFamilyV1.META_LEARNING,
            producer_id=META_LEARNING_PRODUCER_ID,
            reason=ProducerIngressFailureCodeV1.ARTIFACT_MALFORMED.value,
        )
    try:
        intake = adapt_meta_learning_routed_evidence_v1(artifact, termination=termination)
    except ProducerAdapterError as exc:
        return _reject_at_ingress(
            producer_class=EvidenceProducerFamilyV1.META_LEARNING,
            producer_id=META_LEARNING_PRODUCER_ID,
            reason=str(exc),
        )
    provenance = ProducerIngressProvenanceV1(
        adapter_id="meta_learning_routed_evidence_v1",
        source_schema_version=META_ROUTED_SCHEMA,
        source_content_digest=intake.source_evidence_digest,
        producer_class=EvidenceProducerFamilyV1.META_LEARNING,
    )
    return _adjudicate_intake(
        intake,
        termination=termination,
        repo_root=root,
        ledger=ledger,
        provenance=provenance,
    )


def terminate_loop_a_conditioned_cycle_at_a_v1(
    *,
    market_context: Mapping[str, object] | None,
    mi_learning_evidence: Mapping[str, object] | None,
    termination: ProducerEvidenceTerminationContextV1 | None,
    repo_root: Path | None = None,
    ledger: AdjudicationLedgerV1 | None = None,
) -> dict[str, ProducerIngressTerminationResultV1]:
    ledger = ledger or AdjudicationLedgerV1()
    if termination is None and market_context is not None:
        from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.adapters_v1 import (
            default_termination_context_from_market_context_v1,
        )

        termination = default_termination_context_from_market_context_v1(
            market_context,
            market_observation_epoch=0,
        )
    return {
        "market_intelligence": terminate_market_intelligence_market_context_at_a_v1(
            market_context,
            termination=termination,
            repo_root=repo_root,
            ledger=ledger,
        ),
        "learning": terminate_learning_conditioned_evaluative_at_a_v1(
            mi_learning_evidence,
            termination=termination,
            repo_root=repo_root,
            ledger=ledger,
        ),
    }
