"""Additive exact-result bindings; historical GVEF hash domains are unchanged."""

from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from src.evaluation.golden_vectors.contracts.enums import EvaluationDomain
from src.evaluation.golden_vectors.contracts.models import DomainEvaluationResultV1


class EvaluationBindingError(ValueError):
    pass


def exact_bytes_v1(value: Any) -> bytes:
    # Separate domain from float-free GVEF V1: original numeric artifacts are
    # retained as original bytes, never rounded to enter the old schema.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def binding_digest_v1(kind: str, value: Any) -> str:
    return hashlib.sha256(
        exact_bytes_v1({"domain": "peaktrade.evaluation." + kind, "body": value})
    ).hexdigest()


def source_tree_digest_v1() -> str:
    root = Path(__file__).resolve().parents[4]
    digest = hashlib.sha256()
    for path in sorted((root / "src").rglob("*.py")):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


# These are deliberately narrow existing-evaluator contracts, not universal
# economic/domain quality requirements or a replacement authority taxonomy.
CONTRACTS = {
    "ranking_universe": (
        "RU_MEMBERSHIP_AND_SELECTION_BOUNDARY",
        ("ru.not_selection",),
        ("ru.membership_count", "ru.digest"),
    ),
    "productive_trading_path": (
        "PTP_ORDER_AND_PRE_EXTERNAL_BOUNDARY",
        ("ptp.pre_external_terminal",),
        ("ptp.stage_count", "ptp.trace_digest"),
    ),
    "self_learning": (
        "SL_ARTIFACT_AND_NO_WRITEBACK",
        ("sl.no_productive_writeback", "sl.baseline_candidate_bound"),
        ("sl.artifact_digest",),
    ),
    "optimization_universe": (
        "OPT_PARAMETER_AND_NO_APPLY",
        ("opt.no_productive_apply",),
        ("opt.param_count", "opt.digest"),
    ),
    "market_intelligence": (
        "MI_CONTEXT_AND_AUTHORITY_BOUNDARY",
        ("mi.no_productive_materialization", "mi.leakage_check"),
        ("mi.bundle_digest", "mi.freshness_token"),
    ),
}


@dataclass(frozen=True)
class DomainRequirementV1:
    domain: str
    requirement_id: str
    vector_id: str
    context_digest: str
    dependency_digest: str
    numeric_evidence_digest: str

    def validate_v1(self):
        if (
            self.domain not in CONTRACTS
            or self.requirement_id != CONTRACTS[self.domain][0]
            or not self.vector_id
        ):
            raise EvaluationBindingError("UNSUPPORTED_OR_EMPTY_DOMAIN_REQUIREMENT")
        for token in (self.context_digest, self.dependency_digest, self.numeric_evidence_digest):
            if len(token) != 64 or any(c not in "0123456789abcdef" for c in token):
                raise EvaluationBindingError("EXPLICIT_DOMAIN_BINDING_REQUIRED")


@dataclass(frozen=True)
class DomainExclusionV1:
    domain: str
    impact_reason: str
    consumer_edges: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationPlanV1:
    change_id: str
    source_tree_digest: str
    affected_consumer_edges: tuple[str, ...]
    required: tuple[DomainRequirementV1, ...]
    not_required: tuple[DomainExclusionV1, ...] = ()
    schema_version: str = "bounded_required_domain_evaluation_plan.v1"
    claim_scope: str = "EXPLICIT_REPLAY_CONTRACTS_ONLY"

    def to_dict_v1(self):
        return json.loads(exact_bytes_v1(asdict(self)))

    def validate_v1(self):
        if (
            self.schema_version != "bounded_required_domain_evaluation_plan.v1"
            or self.claim_scope != "EXPLICIT_REPLAY_CONTRACTS_ONLY"
            or not self.change_id.strip()
            or not self.affected_consumer_edges
            or not self.required
        ):
            raise EvaluationBindingError("EXPLICIT_EVALUATION_PLAN_REQUIRED")
        domains = [r.domain for r in self.required] + [r.domain for r in self.not_required]
        if len(domains) != len(set(domains)) or set(domains) != {d.value for d in EvaluationDomain}:
            raise EvaluationBindingError("ALL_DOMAINS_REQUIRE_EXPLICIT_IMPACT_DISPOSITION")
        for r in self.required:
            r.validate_v1()
        for e in self.not_required:
            if (
                not e.impact_reason.strip()
                or e.impact_reason.strip().upper() in {"UNKNOWN", "NONE", "N/A", "NOT_REQUIRED"}
                or not e.consumer_edges
            ):
                raise EvaluationBindingError("NOT_REQUIRED_NEEDS_IMPACT_REASON_AND_EDGES")
        if self.source_tree_digest != source_tree_digest_v1():
            raise EvaluationBindingError("EVALUATION_SOURCE_GENERATION_MISMATCH")


def require_result_coverage_v1(requirement: DomainRequirementV1, result: dict):
    row = DomainEvaluationResultV1.model_validate(result)
    if row.domain.value != requirement.domain or row.verdict.value != "PASS":
        raise EvaluationBindingError("DOMAIN_RESULT_NOT_PASS")
    inv = {i.invariant_id: i.pass_ for i in row.invariants}
    metrics = [m.metric_id for m in row.metrics]
    if (
        len(inv) != len(row.invariants)
        or len(metrics) != len(set(metrics))
        or not all(inv.values())
        or any(not b.pass_ for b in row.boundary_results)
        or not set(CONTRACTS[requirement.domain][1]) <= set(inv)
        or not set(CONTRACTS[requirement.domain][2]) <= set(metrics)
    ):
        raise EvaluationBindingError("REQUIRED_RESULT_FIELDS_OR_INVARIANTS_MISSING")
