"""Phase 12 optimization productive lineage registry — census, disposition, replayable chain.

Closes typed lineage semantics for Phase-11 authorized research surfaces. Does not
authorize promotion, runtime apply, optimizer direct write, or external effects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID as F2_SURFACE_ID,
)
from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
    SURFACE_ID as F5_FRESH_SURFACE_ID,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as F1_SURFACE_ID,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    OptimizableEnvelopeResolveRequestV1,
    resolve_optimizable_envelope_v1,
)
from src.experiments.canonical_optimization_surface_portfolio_registry_v1 import (
    PortfolioClassification,
    list_authorized_research_surface_ids_v1,
    list_research_active_surface_ids_v1,
    resolve_optimization_surface_portfolio_v1,
)
from src.governance.governed_productive_configuration_v1 import runtime_apply_possible_v1
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    OPTIMIZATION_SURFACE_ID as M9_PRODUCTIVE_TARGET_SURFACE_ID,
    PRODUCTIVE_TARGET_ID,
    build_productive_target_contract_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    PROMOTION_AUTHORITY,
    direct_productive_write_possible_v1,
)
from src.governance.pdf_v3_3_topic_completion_composition_v1 import (
    prove_pdf_v3_3_productive_consumer_bindings_v1,
    prove_pdf_v3_3_productive_parameter_lineage_chain_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "canonical_optimization_productive_lineage_registry_v1"
WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_12_PRODUCTIVE_LINEAGE_CLOSURE_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_12_PRODUCTIVE_LINEAGE_CLOSURE_NORMATIVE_V1.md"
)
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_12_productive_lineage_closure_v1.json"
)
CONSUMER_BINDING_REGISTRY: Final[str] = (
    "config/governance/pdf_v3_3_productive_consumer_binding_registry_v1.json"
)

RESEARCH_AUTHORIZATION_IMPLIES_PRODUCTIVE_AUTHORIZATION: Final[bool] = False
CANDIDATE_IMPLIES_PRODUCTIVE_CONFIGURATION: Final[bool] = False
PROPOSAL_IMPLIES_AUTHORIZATION: Final[bool] = False
EVIDENCE_IMPLIES_AUTHORIZATION: Final[bool] = False
CONFIGURATION_IMPLIES_RUNTIME_APPLY: Final[bool] = False
OPTIMIZATION_PROMOTION_AUTHORITY: Final[str] = PROMOTION_AUTHORITY
OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE: Final[bool] = direct_productive_write_possible_v1()
NO_SELF_DEPLOY: Final[bool] = True
RISK_IS_HARD_BOUNDARY: Final[bool] = True

REASON_RESEARCH_ONLY: Final[str] = "RESEARCH_ONLY_NO_PRODUCTIVE_LINEAGE"
REASON_PRODUCTIVE_LINEAGE_PROVEN: Final[str] = "PRODUCTIVE_LINEAGE_PROVEN_BOUND"
REASON_FAIL_CLOSED: Final[str] = "PRODUCTIVE_LINEAGE_FAIL_CLOSED"
REASON_UNKNOWN_DISPOSITION: Final[str] = "PRODUCTIVE_RELEVANCE_UNKNOWN"
DISPOSITION_PROPOSAL_ONLY_REF: Final[str] = "PROPOSAL_ONLY"

_REPO_ROOT = Path(__file__).resolve().parents[2]


class ProductiveRelevanceDisposition(str, Enum):
    PRODUCTIVE_RELEVANT = "PRODUCTIVE_RELEVANT"
    RESEARCH_ONLY_NO_CURRENT_PRODUCTIVE_TARGET = "RESEARCH_ONLY_NO_CURRENT_PRODUCTIVE_TARGET"
    PRODUCTIVE_RELEVANCE_UNKNOWN = "PRODUCTIVE_RELEVANCE_UNKNOWN"


class LineageLinkStatus(str, Enum):
    PROVEN_BOUND = "PROVEN_BOUND"
    NOT_APPLICABLE_RESEARCH_ONLY = "NOT_APPLICABLE_RESEARCH_ONLY"
    ABSENT_FAIL_CLOSED = "ABSENT_FAIL_CLOSED"


@dataclass(frozen=True)
class ProductiveLineageLinkV1:
    link_id: str
    status: LineageLinkStatus
    owner_ref: str | None
    evidence_ref: str | None


@dataclass(frozen=True)
class ProductiveLineageSurfaceRecordV1:
    surface_id: str
    family_gate_id: str
    disposition: ProductiveRelevanceDisposition
    productive_target_id: str | None
    current_consumer_module: str | None
    lineage_links: tuple[ProductiveLineageLinkV1, ...]
    lineage_complete: bool
    research_only_productive_apply_forbidden: bool
    disposition_reason: str


def _load_consumer_registry() -> dict[str, Any]:
    return json.loads((_REPO_ROOT / CONSUMER_BINDING_REGISTRY).read_text(encoding="utf-8"))


def _binding_by_surface(surface_id: str) -> Mapping[str, Any] | None:
    reg = _load_consumer_registry()
    for row in reg.get("bindings") or ():
        if isinstance(row, dict) and row.get("surface_id") == surface_id:
            return row
    for row in reg.get("non_productive_surfaces") or ():
        if isinstance(row, dict) and row.get("surface_id") == surface_id:
            return row
    return None


def _family_gate_for_surface(surface_id: str) -> str:
    resolution = resolve_optimization_surface_portfolio_v1(surface_id=surface_id)
    return str(resolution.get("family_gate_id") or "UNKNOWN")


def _f1_lineage_links(binding: Mapping[str, Any]) -> tuple[ProductiveLineageLinkV1, ...]:
    return (
        ProductiveLineageLinkV1(
            link_id="surface_identity",
            status=LineageLinkStatus.PROVEN_BOUND,
            owner_ref="src/experiments/canonical_m9_volatility_numeric_max_age_optimizable_surface_v1.py",
            evidence_ref=str(binding.get("surface_id")),
        ),
        ProductiveLineageLinkV1(
            link_id="candidate_parameter",
            status=LineageLinkStatus.PROVEN_BOUND,
            owner_ref="src/governance/m9_volatility_numeric_max_age_numeric_productive_target_v1.py",
            evidence_ref=str(binding.get("source_candidate_parameter")),
        ),
        ProductiveLineageLinkV1(
            link_id="evidence_and_proposal",
            status=LineageLinkStatus.PROVEN_BOUND,
            owner_ref="src/governance/optimization_proposal_governance_ingress_v1.py",
            evidence_ref=DISPOSITION_PROPOSAL_ONLY_REF,
        ),
        ProductiveLineageLinkV1(
            link_id="governance_risk_admission",
            status=LineageLinkStatus.PROVEN_BOUND,
            owner_ref="src/governance/f1_m9_post_real_campaign_optimization_governance_ingress_v1.py",
            evidence_ref="governance_review_admission",
        ),
        ProductiveLineageLinkV1(
            link_id="explicit_productive_authorization",
            status=LineageLinkStatus.PROVEN_BOUND,
            owner_ref="src/governance/explicit_productive_authorization_v1.py",
            evidence_ref="explicit_productive_authorization_v1.evaluate",
        ),
        ProductiveLineageLinkV1(
            link_id="governed_configuration",
            status=LineageLinkStatus.PROVEN_BOUND,
            owner_ref="src/governance/governed_productive_configuration_v1.py",
            evidence_ref="materialize_governed_productive_configuration_v1",
        ),
        ProductiveLineageLinkV1(
            link_id="authorized_seam",
            status=LineageLinkStatus.PROVEN_BOUND,
            owner_ref=str(binding.get("authorized_seam_module")),
            evidence_ref=str(binding.get("authorized_seam_symbol")),
        ),
        ProductiveLineageLinkV1(
            link_id="productive_consumer",
            status=LineageLinkStatus.PROVEN_BOUND,
            owner_ref=str(binding.get("current_consumer_module")),
            evidence_ref=str(binding.get("trading_decision_consumer_module")),
        ),
    )


def _research_only_lineage_links(surface_id: str) -> tuple[ProductiveLineageLinkV1, ...]:
    return (
        ProductiveLineageLinkV1(
            link_id="surface_identity",
            status=LineageLinkStatus.PROVEN_BOUND,
            owner_ref="phase_11_portfolio_registry",
            evidence_ref=surface_id,
        ),
        ProductiveLineageLinkV1(
            link_id="productive_target",
            status=LineageLinkStatus.NOT_APPLICABLE_RESEARCH_ONLY,
            owner_ref=None,
            evidence_ref=REASON_RESEARCH_ONLY,
        ),
        ProductiveLineageLinkV1(
            link_id="productive_consumer",
            status=LineageLinkStatus.NOT_APPLICABLE_RESEARCH_ONLY,
            owner_ref=None,
            evidence_ref=REASON_RESEARCH_ONLY,
        ),
    )


def _disposition_for_surface(surface_id: str) -> ProductiveRelevanceDisposition:
    binding = _binding_by_surface(surface_id)
    if binding is None:
        return ProductiveRelevanceDisposition.PRODUCTIVE_RELEVANCE_UNKNOWN
    if surface_id in (F1_SURFACE_ID, M9_PRODUCTIVE_TARGET_SURFACE_ID):
        if binding.get("productive_target_id") and binding.get("current_consumer_module"):
            return ProductiveRelevanceDisposition.PRODUCTIVE_RELEVANT
    rel = str(binding.get("productive_relevance") or "")
    if rel in ("RESEARCH_EVIDENCE_ONLY", "SHADOW_RESEARCH_ONLY"):
        return ProductiveRelevanceDisposition.RESEARCH_ONLY_NO_CURRENT_PRODUCTIVE_TARGET
    if binding.get("consumer_binding_required") is False and surface_id != F1_SURFACE_ID:
        return ProductiveRelevanceDisposition.RESEARCH_ONLY_NO_CURRENT_PRODUCTIVE_TARGET
    return ProductiveRelevanceDisposition.PRODUCTIVE_RELEVANCE_UNKNOWN


def build_productive_lineage_surface_records_v1() -> tuple[ProductiveLineageSurfaceRecordV1, ...]:
    records: list[ProductiveLineageSurfaceRecordV1] = []
    for surface_id in list_authorized_research_surface_ids_v1():
        disposition = _disposition_for_surface(surface_id)
        binding = _binding_by_surface(surface_id)
        gate = _family_gate_for_surface(surface_id)
        if disposition == ProductiveRelevanceDisposition.PRODUCTIVE_RELEVANT and binding:
            links = _f1_lineage_links(binding)
            complete = True
            reason = REASON_PRODUCTIVE_LINEAGE_PROVEN
            target_id = str(binding.get("productive_target_id"))
            consumer = str(binding.get("current_consumer_module"))
        elif (
            disposition == ProductiveRelevanceDisposition.RESEARCH_ONLY_NO_CURRENT_PRODUCTIVE_TARGET
        ):
            links = _research_only_lineage_links(surface_id)
            complete = True
            reason = REASON_RESEARCH_ONLY
            target_id = None
            consumer = None
        else:
            links = (
                ProductiveLineageLinkV1(
                    link_id="disposition",
                    status=LineageLinkStatus.ABSENT_FAIL_CLOSED,
                    owner_ref=None,
                    evidence_ref=REASON_UNKNOWN_DISPOSITION,
                ),
            )
            complete = False
            reason = REASON_UNKNOWN_DISPOSITION
            target_id = None
            consumer = None
        records.append(
            ProductiveLineageSurfaceRecordV1(
                surface_id=surface_id,
                family_gate_id=gate,
                disposition=disposition,
                productive_target_id=target_id,
                current_consumer_module=consumer,
                lineage_links=links,
                lineage_complete=complete,
                research_only_productive_apply_forbidden=(
                    disposition
                    == ProductiveRelevanceDisposition.RESEARCH_ONLY_NO_CURRENT_PRODUCTIVE_TARGET
                ),
                disposition_reason=reason,
            )
        )
    return tuple(records)


def build_productive_lineage_registry_v1() -> MappingProxyType[str, Any]:
    records = build_productive_lineage_surface_records_v1()
    rows = []
    for record in records:
        rows.append(
            {
                "surface_id": record.surface_id,
                "family_gate_id": record.family_gate_id,
                "disposition": record.disposition.value,
                "productive_target_id": record.productive_target_id,
                "current_consumer_module": record.current_consumer_module,
                "lineage_complete": record.lineage_complete,
                "lineage_link_count": len(record.lineage_links),
                "research_only_productive_apply_forbidden": (
                    record.research_only_productive_apply_forbidden
                ),
                "disposition_reason": record.disposition_reason,
            }
        )
    body = {
        "schema_version": SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_research_surface_ids": list(list_authorized_research_surface_ids_v1()),
        "research_active_surface_ids": list(list_research_active_surface_ids_v1()),
        "research_authorization_implies_productive_authorization": (
            RESEARCH_AUTHORIZATION_IMPLIES_PRODUCTIVE_AUTHORIZATION
        ),
        "candidate_implies_productive_configuration": CANDIDATE_IMPLIES_PRODUCTIVE_CONFIGURATION,
        "optimization_promotion_authority": OPTIMIZATION_PROMOTION_AUTHORITY,
        "optimization_direct_productive_write": OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE,
        "surfaces": rows,
    }
    body["registry_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "registry_digest"}
    )
    return MappingProxyType(body)


def derive_lineage_record_digest_v1(record: ProductiveLineageSurfaceRecordV1) -> str:
    body = {
        "surface_id": record.surface_id,
        "disposition": record.disposition.value,
        "lineage_links": tuple(
            (link.link_id, link.status.value, link.owner_ref, link.evidence_ref)
            for link in record.lineage_links
        ),
    }
    return compute_content_sha256(body)


def resolve_productive_lineage_v1(*, surface_id: str) -> MappingProxyType[str, Any]:
    record = next(
        (r for r in build_productive_lineage_surface_records_v1() if r.surface_id == surface_id),
        None,
    )
    if record is None:
        payload = {
            "resolution": "NOT_IN_PHASE_12_CENSUS",
            "reason": REASON_FAIL_CLOSED,
            "productive_apply_allowed": False,
        }
        payload["result_digest"] = compute_content_sha256(payload)
        return MappingProxyType(payload)
    lineage_chain_proven = (
        record.disposition == ProductiveRelevanceDisposition.PRODUCTIVE_RELEVANT
        and record.lineage_complete
        and prove_f1_productive_lineage_chain_on_current_v1()
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "resolution": "LINEAGE_RECORD",
        "surface_id": record.surface_id,
        "disposition": record.disposition.value,
        "lineage_complete": record.lineage_complete,
        "lineage_chain_proven": lineage_chain_proven,
        "productive_apply_allowed": False,
        "runtime_apply_possible": runtime_apply_possible_v1(),
        "research_only_productive_apply_forbidden": (
            record.research_only_productive_apply_forbidden
        ),
        "lineage_record_digest": derive_lineage_record_digest_v1(record),
    }
    payload["result_digest"] = compute_content_sha256(
        {key: value for key, value in payload.items() if key != "result_digest"}
    )
    return MappingProxyType(payload)


def assert_research_only_cannot_productive_apply_v1(*, surface_id: str) -> None:
    resolution = resolve_productive_lineage_v1(surface_id=surface_id)
    if resolution.get("research_only_productive_apply_forbidden") is not True:
        raise ValueError(f"expected_research_only_forbidden:{surface_id}")
    if resolution.get("lineage_chain_proven") is True:
        raise ValueError(f"research_only_must_not_proven_lineage:{surface_id}")
    if resolution.get("productive_apply_allowed") is not False:
        raise ValueError(f"productive_apply_must_remain_false:{surface_id}")


def prove_f1_productive_lineage_chain_on_current_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    if not prove_pdf_v3_3_productive_consumer_bindings_v1(repo_root=root):
        return False
    if not prove_pdf_v3_3_productive_parameter_lineage_chain_v1(repo_root=root):
        return False
    contract = build_productive_target_contract_v1()
    if contract.get("optimization_surface_id") != F1_SURFACE_ID:
        return False
    if contract.get("productive_target_id") != PRODUCTIVE_TARGET_ID:
        return False
    envelope = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=F1_SURFACE_ID)
    )
    if envelope.get("resolution") != RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION:
        return False
    portfolio = resolve_optimization_surface_portfolio_v1(surface_id=F1_SURFACE_ID)
    if (
        portfolio.get("portfolio_classification")
        != PortfolioClassification.AUTHORIZED_RESEARCH_SURFACE.value
    ):
        return False
    return True


def list_productive_relevance_unknown_surface_ids_v1() -> tuple[str, ...]:
    return tuple(
        record.surface_id
        for record in build_productive_lineage_surface_records_v1()
        if record.disposition == ProductiveRelevanceDisposition.PRODUCTIVE_RELEVANCE_UNKNOWN
    )


def assert_phase_12_census_closed_v1() -> None:
    unknowns = list_productive_relevance_unknown_surface_ids_v1()
    if unknowns:
        raise ValueError(f"productive_relevance_unknown:{','.join(unknowns)}")
    for sid in (F2_SURFACE_ID, F5_FRESH_SURFACE_ID):
        assert_research_only_cannot_productive_apply_v1(surface_id=sid)
    if not prove_f1_productive_lineage_chain_on_current_v1():
        raise ValueError("f1_productive_lineage_chain_not_proven")
    if runtime_apply_possible_v1() is not False:
        raise ValueError("runtime_apply_must_remain_impossible")
    if OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE:
        raise ValueError("optimizer_direct_write_forbidden")


def prove_phase_12_productive_lineage_closure_v1(*, repo_root: Path | None = None) -> bool:
    del repo_root
    try:
        assert_phase_12_census_closed_v1()
    except ValueError:
        return False
    first = build_productive_lineage_registry_v1()
    second = build_productive_lineage_registry_v1()
    if first.get("registry_digest") != second.get("registry_digest"):
        return False
    f1_a = resolve_productive_lineage_v1(surface_id=F1_SURFACE_ID)
    f1_b = resolve_productive_lineage_v1(surface_id=F1_SURFACE_ID)
    if f1_a.get("result_digest") != f1_b.get("result_digest"):
        return False
    return True


__all__ = [
    "CANDIDATE_IMPLIES_PRODUCTIVE_CONFIGURATION",
    "CONSUMER_BINDING_REGISTRY",
    "INTEGRATION_CONFIG",
    "LineageLinkStatus",
    "NO_SELF_DEPLOY",
    "NORMATIVE_SPEC",
    "OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE",
    "OPTIMIZATION_PROMOTION_AUTHORITY",
    "ProductiveLineageLinkV1",
    "ProductiveLineageSurfaceRecordV1",
    "ProductiveRelevanceDisposition",
    "RESEARCH_AUTHORIZATION_IMPLIES_PRODUCTIVE_AUTHORIZATION",
    "RISK_IS_HARD_BOUNDARY",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "assert_phase_12_census_closed_v1",
    "assert_research_only_cannot_productive_apply_v1",
    "build_productive_lineage_registry_v1",
    "build_productive_lineage_surface_records_v1",
    "derive_lineage_record_digest_v1",
    "list_productive_relevance_unknown_surface_ids_v1",
    "prove_f1_productive_lineage_chain_on_current_v1",
    "prove_phase_12_productive_lineage_closure_v1",
    "resolve_productive_lineage_v1",
]
