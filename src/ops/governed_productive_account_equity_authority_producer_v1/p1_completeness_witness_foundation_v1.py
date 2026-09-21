"""P1 completeness witness foundation (offline, fail-closed).

Six independent root witnesses, two derived predicates (TIME, PROVENANCE),
shared serialization/validation, and sealed-evidence composition.
Does not GET. Does not ratify kind sets. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    EMPTY_ROWS_PROVE_KIND_ABSENCE,
    EMPTY_ROWS_PROVE_ZERO_EVENTS,
    PAGINATION_EXHAUSTION_PROVES_COMPLETENESS,
    RAW_EQ_SOURCE_AUTHORITY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
    RATIFIED_CLASSIFIED_KIND_SET_RESOLVED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_s0_runtime_binding_gate_v1 import (
    resolve_canonical_d4_d5_genesis_runtime_store_root_v1,
)

CANONICAL_CD_PACK = (
    "evidence/ops/full_core_u05_primary_proof_bound_interest_accrued_get_acquisition_v1/"
    "2026-09-15T010500Z"
)
CANONICAL_USDC_P1_PACK = (
    "evidence/ops/full_core_u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1/"
    "2026-09-20T233000Z"
)
CANONICAL_U01_PACK = (
    "evidence/ops/full_core_current_productive_u01_account_mode_semantic_ratification_v1/"
    "20260915T113345Z"
)

SCHEMA_CLASS = "P1_COMPLETENESS_WITNESS_FOUNDATION_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
WP_ID = "FULL_CORE_P1_COMPLETENESS_WITNESS_FOUNDATION_MAX_OFFLINE_V1"

TRUE_TOKEN = "true"
FALSE_TOKEN = "false"

ROOT_CURRENCY_DOMAIN = "CURRENCY_DOMAIN_COMPLETE"
ROOT_LIABILITY_EVENT_CLASS = "LIABILITY_EVENT_CLASS_COMPLETE"
ROOT_PAGINATION = "PAGINATION_COMPLETE"
ROOT_EVENT_ORDERING = "EVENT_ORDERING_COMPLETE"
ROOT_OBSERVATION_FRESHNESS = "OBSERVATION_FRESHNESS_COMPLETE"
ROOT_RESTART_DURABILITY = "RESTART_DURABILITY_COMPLETE"

DERIVED_TIME_DOMAIN = "TIME_DOMAIN_COMPLETE"
DERIVED_PROVENANCE = "PROVENANCE_COMPLETE"

ROOT_WITNESS_ORDER: tuple[str, ...] = (
    ROOT_CURRENCY_DOMAIN,
    ROOT_LIABILITY_EVENT_CLASS,
    ROOT_PAGINATION,
    ROOT_EVENT_ORDERING,
    ROOT_OBSERVATION_FRESHNESS,
    ROOT_RESTART_DURABILITY,
)

WITNESS_COMPLETE = "COMPLETE"
WITNESS_UNKNOWN = "UNKNOWN"
WITNESS_INCOMPLETE = "INCOMPLETE"
WITNESS_CONFLICTED = "CONFLICTED"

BLOCKER_NONE = "NONE"
BLOCKER_EVIDENCE = "EVIDENCE"
BLOCKER_GOVERNANCE = "GOVERNANCE"
BLOCKER_NETWORK = "NETWORK"
BLOCKER_RUNTIME = "RUNTIME"
BLOCKER_RESTART = "RESTART"

PAGINATION_MODEL_LIMIT_ONLY = "limit_only_no_cursor_in_binding"


class P1CompletenessWitnessFoundationError(ValueError):
    """Fail-closed P1 completeness witness violation."""


@dataclass(frozen=True)
class P1RootWitnessEvaluationV1:
    root_id: str
    status: str
    complete: bool
    blocker_class: str
    missing_evidence: str
    detail: str
    network_required: bool
    governance_required: bool
    runtime_required: bool
    restart_required: bool


@dataclass(frozen=True)
class P1DerivedWitnessEvaluationV1:
    predicate_id: str
    status: str
    complete: bool
    derived_from: tuple[str, ...]
    blocker_class: str
    missing_evidence: str
    detail: str


@dataclass(frozen=True)
class P1SealedWitnessEvidenceV1:
    cd_claims: Mapping[str, Any]
    usdc_claims: Mapping[str, Any]
    reopen_adjudication: Mapping[str, Any]
    surface_binding: Mapping[str, Any]
    surface_discovery: Mapping[str, Any]
    offline_qualification: Mapping[str, Any]
    u01_claims: Mapping[str, Any]
    raw_http_capture: Mapping[str, Any]
    d5_event_completeness_from_window: str
    d5_binding_present: bool


@dataclass(frozen=True)
class P1CompletenessWitnessBundleV1:
    roots: tuple[P1RootWitnessEvaluationV1, ...]
    time_domain: P1DerivedWitnessEvaluationV1
    provenance: P1DerivedWitnessEvaluationV1
    bound_origin_main_sha: str


def _as_bool_token(value: object) -> bool:
    return str(value or "").lower() == TRUE_TOKEN


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _root_eval(
    *,
    root_id: str,
    status: str,
    blocker_class: str = BLOCKER_NONE,
    missing_evidence: str = "",
    detail: str = "",
    network_required: bool = False,
    governance_required: bool = False,
    runtime_required: bool = False,
    restart_required: bool = False,
) -> P1RootWitnessEvaluationV1:
    complete = status == WITNESS_COMPLETE
    return P1RootWitnessEvaluationV1(
        root_id=root_id,
        status=status,
        complete=complete,
        blocker_class=blocker_class if not complete else BLOCKER_NONE,
        missing_evidence=missing_evidence,
        detail=detail,
        network_required=network_required,
        governance_required=governance_required,
        runtime_required=runtime_required,
        restart_required=restart_required,
    )


def _derived_eval(
    *,
    predicate_id: str,
    status: str,
    derived_from: Sequence[str],
    blocker_class: str = BLOCKER_NONE,
    missing_evidence: str = "",
    detail: str = "",
) -> P1DerivedWitnessEvaluationV1:
    complete = status == WITNESS_COMPLETE
    return P1DerivedWitnessEvaluationV1(
        predicate_id=predicate_id,
        status=status,
        complete=complete,
        derived_from=tuple(derived_from),
        blocker_class=blocker_class if not complete else BLOCKER_NONE,
        missing_evidence=missing_evidence,
        detail=detail,
    )


def evaluate_currency_domain_witness_v1(
    evidence: P1SealedWitnessEvidenceV1,
) -> P1RootWitnessEvaluationV1:
    settlement = str(evidence.surface_binding.get("SETTLEMENT_CCY", ""))
    scoped_ccy = str(evidence.usdc_claims.get("EXACT_REQUEST", ""))
    if settlement == "USDC" and "ccy=USDC" in scoped_ccy:
        return _root_eval(
            root_id=ROOT_CURRENCY_DOMAIN,
            status=WITNESS_INCOMPLETE,
            blocker_class=BLOCKER_EVIDENCE,
            missing_evidence="APPLICABLE_LOAN_CURRENCY_DOMAIN_EXHAUSTION_WITNESS",
            detail=(
                "USDC settlement and ccy=USDC scope alone do not prove currency-domain "
                "completeness; applicable currency set not exhausted"
            ),
            network_required=True,
        )
    return _root_eval(
        root_id=ROOT_CURRENCY_DOMAIN,
        status=WITNESS_INCOMPLETE,
        blocker_class=BLOCKER_EVIDENCE,
        missing_evidence="EXPLICIT_CURRENCY_DOMAIN_COMPLETENESS_WITNESS",
        detail="Currency domain witness inputs absent or unbound",
        network_required=True,
    )


def evaluate_liability_event_class_witness_v1(
    evidence: P1SealedWitnessEvidenceV1,
) -> P1RootWitnessEvaluationV1:
    del evidence
    if RATIFIED_CLASSIFIED_KIND_SET and RATIFIED_CLASSIFIED_KIND_SET_RESOLVED:
        return _root_eval(
            root_id=ROOT_LIABILITY_EVENT_CLASS,
            status=WITNESS_COMPLETE,
            detail="Ratified classified kind set resolved",
        )
    return _root_eval(
        root_id=ROOT_LIABILITY_EVENT_CLASS,
        status=WITNESS_INCOMPLETE,
        blocker_class=BLOCKER_GOVERNANCE,
        missing_evidence="RATIFIED_CLASSIFIED_KIND_SET",
        detail=(
            "Liability event class completeness requires ratified classified kind set; "
            "seam present, ratification absent"
        ),
        governance_required=True,
    )


def evaluate_pagination_exhaustion_witness_v1(
    evidence: P1SealedWitnessEvidenceV1,
) -> P1RootWitnessEvaluationV1:
    exhaustion = _as_bool_token(evidence.reopen_adjudication.get("CD_EXHAUSTION_PROVEN"))
    max_pages = str(evidence.surface_binding.get("MAX_PAGES", ""))
    page_scope = str(evidence.reopen_adjudication.get("CD_PAGE_SCOPE", ""))
    if max_pages == "1":
        return _root_eval(
            root_id=ROOT_PAGINATION,
            status=WITNESS_INCOMPLETE,
            blocker_class=BLOCKER_EVIDENCE,
            missing_evidence="PAGINATION_EXHAUSTION_WITNESS",
            detail="MAX_PAGES=1 does not prove pagination exhaustion",
            network_required=True,
        )
    if not exhaustion:
        return _root_eval(
            root_id=ROOT_PAGINATION,
            status=WITNESS_INCOMPLETE,
            blocker_class=BLOCKER_NETWORK,
            missing_evidence="PAGINATION_TRAVERSAL_EXHAUSTION_PROOF",
            detail=f"CD_EXHAUSTION_PROVEN=false; page_scope={page_scope}",
            network_required=True,
        )
    if PAGINATION_EXHAUSTION_PROVES_COMPLETENESS is not True:
        return _root_eval(
            root_id=ROOT_PAGINATION,
            status=WITNESS_INCOMPLETE,
            blocker_class=BLOCKER_EVIDENCE,
            missing_evidence="PAGINATION_EXHAUSTION_DOES_NOT_PROVE_COMPLETENESS_LAW",
            detail="Repository law forbids treating pagination exhaustion as completeness",
        )
    return _root_eval(
        root_id=ROOT_PAGINATION,
        status=WITNESS_COMPLETE,
        detail="Pagination exhaustion proven under bound D6 rules",
    )


def evaluate_event_ordering_witness_v1(
    evidence: P1SealedWitnessEvidenceV1,
) -> P1RootWitnessEvaluationV1:
    row_count = int(str(evidence.offline_qualification.get("row_count", "0")))
    if row_count == 0 and (EMPTY_ROWS_PROVE_ZERO_EVENTS or EMPTY_ROWS_PROVE_KIND_ABSENCE):
        raise P1CompletenessWitnessFoundationError("ABSENCE_LAW_DRIFT")
    pagination_model = ""
    for record in evidence.surface_discovery.get("records", []):
        if not isinstance(record, Mapping):
            continue
        if str(record.get("STATUS", "")) == "CAPABLE_WITH_BOUNDED_BINDING":
            pagination_model = str(record.get("PAGINATION_MODEL", ""))
            break
    return _root_eval(
        root_id=ROOT_EVENT_ORDERING,
        status=WITNESS_INCOMPLETE,
        blocker_class=BLOCKER_EVIDENCE,
        missing_evidence="EVENT_ORDERING_COMPLETENESS_WITNESS",
        detail=(
            f"Zero rows and pagination_model={pagination_model} do not prove ordering "
            "completeness; explicit ordering witness required"
        ),
    )


def evaluate_observation_freshness_witness_v1(
    evidence: P1SealedWitnessEvidenceV1,
) -> P1RootWitnessEvaluationV1:
    if not evidence.d5_binding_present:
        return _root_eval(
            root_id=ROOT_OBSERVATION_FRESHNESS,
            status=WITNESS_INCOMPLETE,
            blocker_class=BLOCKER_RUNTIME,
            missing_evidence="D5_CHECKPOINT_WINDOW_BINDING_RUNTIME_INSTANCE",
            detail="D5 runtime binding absent for P1-bound freshness witness",
            runtime_required=True,
        )
    if _as_bool_token(evidence.d5_event_completeness_from_window):
        return _root_eval(
            root_id=ROOT_OBSERVATION_FRESHNESS,
            status=WITNESS_CONFLICTED,
            blocker_class=BLOCKER_EVIDENCE,
            missing_evidence="D5_EVENT_COMPLETENESS_FROM_WINDOW_MUST_BE_FALSE",
            detail="event_completeness_from_window=true contradicts P1 freshness law",
        )
    request_utc = str(evidence.raw_http_capture.get("request_utc", ""))
    if not request_utc:
        return _root_eval(
            root_id=ROOT_OBSERVATION_FRESHNESS,
            status=WITNESS_INCOMPLETE,
            blocker_class=BLOCKER_EVIDENCE,
            missing_evidence="P1_BOUND_OBSERVATION_FRESHNESS_WITNESS",
            detail="Observation timestamp present but P1-bound freshness witness absent",
        )
    return _root_eval(
        root_id=ROOT_OBSERVATION_FRESHNESS,
        status=WITNESS_INCOMPLETE,
        blocker_class=BLOCKER_EVIDENCE,
        missing_evidence="D5_CHECKPOINT_FRESHNESS_WITNESS_V1",
        detail=(
            "D5 binding present with event_completeness_from_window=false; "
            "P1-bound checkpoint freshness witness not proven"
        ),
    )


def evaluate_restart_durability_witness_v1(
    evidence: P1SealedWitnessEvidenceV1,
) -> P1RootWitnessEvaluationV1:
    del evidence
    return _root_eval(
        root_id=ROOT_RESTART_DURABILITY,
        status=WITNESS_INCOMPLETE,
        blocker_class=BLOCKER_RESTART,
        missing_evidence="OBSERVATION_RESTART_DURABILITY_WITNESS_V1",
        detail="Restart durability completeness requires restart-campaign proof; not persisted alone",
        restart_required=True,
    )


def derive_time_domain_witness_v1(
    *,
    pagination: P1RootWitnessEvaluationV1,
    evidence: P1SealedWitnessEvidenceV1,
) -> P1DerivedWitnessEvaluationV1:
    if not pagination.complete:
        return _derived_eval(
            predicate_id=DERIVED_TIME_DOMAIN,
            status=WITNESS_INCOMPLETE,
            derived_from=(ROOT_PAGINATION,),
            blocker_class=pagination.blocker_class,
            missing_evidence="PAGINATION_COMPLETE_REQUIRED_FOR_TIME_DOMAIN",
            detail="TIME_DOMAIN_COMPLETE derived from pagination + cursor semantics",
        )
    cursor_used = _as_bool_token(evidence.reopen_adjudication.get("CD_CURSOR_USED"))
    page_scope = str(evidence.reopen_adjudication.get("CD_PAGE_SCOPE", ""))
    time_scope = str(evidence.reopen_adjudication.get("CD_TIME_SCOPE", ""))
    if cursor_used:
        return _derived_eval(
            predicate_id=DERIVED_TIME_DOMAIN,
            status=WITNESS_INCOMPLETE,
            derived_from=(ROOT_PAGINATION,),
            blocker_class=BLOCKER_EVIDENCE,
            missing_evidence="CURSOR_TRAVERSAL_EXHAUSTION_WITNESS",
            detail="Cursor used without proven exhaustion under cursor semantics",
        )
    if page_scope == "single_page" and time_scope == "venue_default_past_year":
        return _derived_eval(
            predicate_id=DERIVED_TIME_DOMAIN,
            status=WITNESS_INCOMPLETE,
            derived_from=(ROOT_PAGINATION,),
            blocker_class=BLOCKER_NETWORK,
            missing_evidence="TIME_WINDOW_TRAVERSAL_EXHAUSTION_WITNESS",
            detail="Single-page observation does not prove venue past-year traversal",
        )
    return _derived_eval(
        predicate_id=DERIVED_TIME_DOMAIN,
        status=WITNESS_COMPLETE,
        derived_from=(ROOT_PAGINATION,),
        detail="Pagination complete and cursor/time scope semantics satisfied",
    )


def derive_provenance_witness_v1(
    *,
    evidence: P1SealedWitnessEvidenceV1,
    currency: P1RootWitnessEvaluationV1,
    time_domain: P1DerivedWitnessEvaluationV1,
    pagination: P1RootWitnessEvaluationV1,
) -> P1DerivedWitnessEvaluationV1:
    cd_raw = _as_bool_token(evidence.cd_claims.get("RAW_EVIDENCE_PERSISTED"))
    usdc_raw = _as_bool_token(evidence.usdc_claims.get("RAW_EVIDENCE_PERSISTED"))
    cd_sha = str(evidence.cd_claims.get("RAW_EVIDENCE_SHA256", ""))
    usdc_sha = str(evidence.usdc_claims.get("RAW_EVIDENCE_SHA256", ""))
    raw_chain_ok = cd_raw and usdc_raw and len(cd_sha) == 64 and len(usdc_sha) == 64
    if not raw_chain_ok:
        return _derived_eval(
            predicate_id=DERIVED_PROVENANCE,
            status=WITNESS_INCOMPLETE,
            derived_from=(ROOT_CURRENCY_DOMAIN, ROOT_PAGINATION, DERIVED_TIME_DOMAIN),
            blocker_class=BLOCKER_EVIDENCE,
            missing_evidence="SEALED_RAW_PROVENANCE_CHAIN",
            detail="Raw evidence persistence or digest incomplete",
        )
    if not (currency.complete and pagination.complete and time_domain.complete):
        missing = [
            name
            for name, ok in (
                (ROOT_CURRENCY_DOMAIN, currency.complete),
                (ROOT_PAGINATION, pagination.complete),
                (DERIVED_TIME_DOMAIN, time_domain.complete),
            )
            if not ok
        ]
        return _derived_eval(
            predicate_id=DERIVED_PROVENANCE,
            status=WITNESS_INCOMPLETE,
            derived_from=tuple(missing),
            blocker_class=BLOCKER_EVIDENCE,
            missing_evidence="REQUIRED_DOMAIN_CLOSURE_FOR_PROVENANCE",
            detail=f"Raw chain present; domain closure missing: {','.join(missing)}",
        )
    return _derived_eval(
        predicate_id=DERIVED_PROVENANCE,
        status=WITNESS_COMPLETE,
        derived_from=(ROOT_CURRENCY_DOMAIN, ROOT_PAGINATION, DERIVED_TIME_DOMAIN),
        detail="Raw provenance chain plus required domain closures proven",
    )


def load_sealed_p1_witness_evidence_v1(*, repo_root: Path | str) -> P1SealedWitnessEvidenceV1:
    root = Path(repo_root)
    usdc_pack = root / CANONICAL_USDC_P1_PACK
    raw_http_path = usdc_pack / "raw_http_capture_v1.json"
    raw_http: dict[str, Any] = {}
    if raw_http_path.is_file():
        raw_http = _read_json(raw_http_path)

    d5_present = False
    d5_event_completeness = FALSE_TOKEN
    genesis_root = resolve_canonical_d4_d5_genesis_runtime_store_root_v1(repo_root=root)
    if genesis_root is not None:
        d5_path = genesis_root / "d5_checkpoint_observation_window_binding_v1.json"
        if d5_path.is_file():
            d5_present = True
            d5_payload = _read_json(d5_path)
            d5_event_completeness = str(
                d5_payload.get("event_completeness_from_window", FALSE_TOKEN)
            )

    return P1SealedWitnessEvidenceV1(
        cd_claims=_read_json(root / CANONICAL_CD_PACK / "claims.json"),
        usdc_claims=_read_json(usdc_pack / "claims.json"),
        reopen_adjudication=_read_json(usdc_pack / "interest_accrued_reopen_adjudication_v1.json"),
        surface_binding=_read_json(usdc_pack / "p1_surface_binding_v1.json"),
        surface_discovery=_read_json(usdc_pack / "futures_p1_surface_discovery_v1.json"),
        offline_qualification=_read_json(usdc_pack / "p1_offline_qualification_v1.json"),
        u01_claims=_read_json(root / CANONICAL_U01_PACK / "claims.json"),
        raw_http_capture=raw_http,
        d5_event_completeness_from_window=d5_event_completeness,
        d5_binding_present=d5_present,
    )


def compose_p1_completeness_witness_bundle_v1(
    evidence: P1SealedWitnessEvidenceV1,
    *,
    bound_origin_main_sha: str = "",
) -> P1CompletenessWitnessBundleV1:
    currency = evaluate_currency_domain_witness_v1(evidence)
    liability = evaluate_liability_event_class_witness_v1(evidence)
    pagination = evaluate_pagination_exhaustion_witness_v1(evidence)
    ordering = evaluate_event_ordering_witness_v1(evidence)
    freshness = evaluate_observation_freshness_witness_v1(evidence)
    restart = evaluate_restart_durability_witness_v1(evidence)
    roots = (currency, liability, pagination, ordering, freshness, restart)
    time_domain = derive_time_domain_witness_v1(pagination=pagination, evidence=evidence)
    provenance = derive_provenance_witness_v1(
        evidence=evidence,
        currency=currency,
        time_domain=time_domain,
        pagination=pagination,
    )
    return P1CompletenessWitnessBundleV1(
        roots=roots,
        time_domain=time_domain,
        provenance=provenance,
        bound_origin_main_sha=bound_origin_main_sha,
    )


def evaluate_sealed_p1_completeness_witness_bundle_v1(
    *, repo_root: Path | str, bound_origin_main_sha: str = ""
) -> P1CompletenessWitnessBundleV1:
    evidence = load_sealed_p1_witness_evidence_v1(repo_root=repo_root)
    return compose_p1_completeness_witness_bundle_v1(
        evidence, bound_origin_main_sha=bound_origin_main_sha
    )


def root_by_id_v1(bundle: P1CompletenessWitnessBundleV1, root_id: str) -> P1RootWitnessEvaluationV1:
    for root in bundle.roots:
        if root.root_id == root_id:
            return root
    raise P1CompletenessWitnessFoundationError(f"ROOT_NOT_FOUND:{root_id}")


def witness_flags_for_p1_closeout_v1(
    bundle: P1CompletenessWitnessBundleV1,
    *,
    account_identity_bound: bool,
    account_mode_futures_ratified: bool,
    venue_binding_complete: bool,
    surface_coverage_complete: bool,
    independence_from_balance_snapshot: bool,
    independence_from_raw_eq: bool,
    qualifying_event_count: int,
    nonqualifying_event_count: int,
    cd_row_count: int,
    usdc_scoped_row_count: int,
) -> dict[str, bool]:
    """Map witness bundle to #6665 closeout input flags (authority-neutral)."""
    del qualifying_event_count, nonqualifying_event_count, cd_row_count, usdc_scoped_row_count
    return {
        "account_identity_bound": account_identity_bound,
        "account_mode_futures_ratified": account_mode_futures_ratified,
        "venue_binding_complete": venue_binding_complete,
        "currency_domain_complete": root_by_id_v1(bundle, ROOT_CURRENCY_DOMAIN).complete,
        "liability_event_class_complete": root_by_id_v1(
            bundle, ROOT_LIABILITY_EVENT_CLASS
        ).complete,
        "time_domain_complete": bundle.time_domain.complete,
        "surface_coverage_complete": surface_coverage_complete,
        "pagination_complete": root_by_id_v1(bundle, ROOT_PAGINATION).complete,
        "event_ordering_complete": root_by_id_v1(bundle, ROOT_EVENT_ORDERING).complete,
        "observation_freshness_complete": root_by_id_v1(
            bundle, ROOT_OBSERVATION_FRESHNESS
        ).complete,
        "restart_durability_complete": root_by_id_v1(bundle, ROOT_RESTART_DURABILITY).complete,
        "independence_from_balance_snapshot": independence_from_balance_snapshot,
        "independence_from_raw_eq": independence_from_raw_eq,
        "provenance_complete": bundle.provenance.complete,
    }


def validate_witness_bundle_v1(bundle: P1CompletenessWitnessBundleV1) -> None:
    seen: set[str] = set()
    for root in bundle.roots:
        if root.root_id in seen:
            raise P1CompletenessWitnessFoundationError(f"DUPLICATE_ROOT:{root.root_id}")
        seen.add(root.root_id)
        if root.complete and root.status != WITNESS_COMPLETE:
            raise P1CompletenessWitnessFoundationError(f"COMPLETE_STATUS_MISMATCH:{root.root_id}")
        if not root.complete and root.status == WITNESS_COMPLETE:
            raise P1CompletenessWitnessFoundationError(f"INCOMPLETE_STATUS_MISMATCH:{root.root_id}")
    for expected in ROOT_WITNESS_ORDER:
        if expected not in seen:
            raise P1CompletenessWitnessFoundationError(f"ROOT_MISSING:{expected}")
    if bundle.time_domain.predicate_id != DERIVED_TIME_DOMAIN:
        raise P1CompletenessWitnessFoundationError("DERIVED_TIME_ID_MISMATCH")
    if bundle.provenance.predicate_id != DERIVED_PROVENANCE:
        raise P1CompletenessWitnessFoundationError("DERIVED_PROVENANCE_ID_MISMATCH")


def witness_bundle_digest_v1(bundle: P1CompletenessWitnessBundleV1) -> str:
    payload = witness_bundle_to_mapping_v1(bundle)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def witness_bundle_to_mapping_v1(bundle: P1CompletenessWitnessBundleV1) -> dict[str, Any]:
    return {
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "WP_ID": WP_ID,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "BOUND_ORIGIN_MAIN_SHA": bundle.bound_origin_main_sha,
        "ROOT_WITNESSES": [
            {
                "ROOT_ID": r.root_id,
                "STATUS": r.status,
                "COMPLETE": r.complete,
                "BLOCKER_CLASS": r.blocker_class,
                "MISSING_EVIDENCE": r.missing_evidence,
                "DETAIL": r.detail,
                "NETWORK_REQUIRED": r.network_required,
                "GOVERNANCE_REQUIRED": r.governance_required,
                "RUNTIME_REQUIRED": r.runtime_required,
                "RESTART_REQUIRED": r.restart_required,
            }
            for r in bundle.roots
        ],
        "DERIVED_TIME_DOMAIN": {
            "PREDICATE_ID": bundle.time_domain.predicate_id,
            "STATUS": bundle.time_domain.status,
            "COMPLETE": bundle.time_domain.complete,
            "DERIVED_FROM": list(bundle.time_domain.derived_from),
            "BLOCKER_CLASS": bundle.time_domain.blocker_class,
            "MISSING_EVIDENCE": bundle.time_domain.missing_evidence,
            "DETAIL": bundle.time_domain.detail,
        },
        "DERIVED_PROVENANCE": {
            "PREDICATE_ID": bundle.provenance.predicate_id,
            "STATUS": bundle.provenance.status,
            "COMPLETE": bundle.provenance.complete,
            "DERIVED_FROM": list(bundle.provenance.derived_from),
            "BLOCKER_CLASS": bundle.provenance.blocker_class,
            "MISSING_EVIDENCE": bundle.provenance.missing_evidence,
            "DETAIL": bundle.provenance.detail,
        },
        "WITNESS_BUNDLE_DIGEST": "",
    }


def first_real_blocker_from_bundle_v1(
    bundle: P1CompletenessWitnessBundleV1,
) -> tuple[str, str, str]:
    """Return (root_or_derived_id, blocker_class, missing_evidence) for earliest gap."""
    for root in bundle.roots:
        if not root.complete:
            return root.root_id, root.blocker_class, root.missing_evidence
    if not bundle.time_domain.complete:
        return (
            DERIVED_TIME_DOMAIN,
            bundle.time_domain.blocker_class,
            bundle.time_domain.missing_evidence,
        )
    if not bundle.provenance.complete:
        return (
            DERIVED_PROVENANCE,
            bundle.provenance.blocker_class,
            bundle.provenance.missing_evidence,
        )
    return "", BLOCKER_NONE, ""


def p1_conjunction_status_from_bundle_v1(bundle: P1CompletenessWitnessBundleV1) -> str:
    if all(r.complete for r in bundle.roots) and bundle.time_domain.complete:
        return "ALL_ROOTS_AND_TIME_DERIVED_COMPLETE"
    return "UNKNOWN_INCOMPLETE"


__all__ = [
    "AUTHORITY_EFFECT",
    "BLOCKER_EVIDENCE",
    "BLOCKER_GOVERNANCE",
    "BLOCKER_NETWORK",
    "BLOCKER_NONE",
    "BLOCKER_RESTART",
    "BLOCKER_RUNTIME",
    "CONTRACT_VERSION",
    "DERIVED_PROVENANCE",
    "DERIVED_TIME_DOMAIN",
    "P1CompletenessWitnessBundleV1",
    "P1CompletenessWitnessFoundationError",
    "P1DerivedWitnessEvaluationV1",
    "P1RootWitnessEvaluationV1",
    "P1SealedWitnessEvidenceV1",
    "ROOT_CURRENCY_DOMAIN",
    "ROOT_EVENT_ORDERING",
    "ROOT_LIABILITY_EVENT_CLASS",
    "ROOT_OBSERVATION_FRESHNESS",
    "ROOT_PAGINATION",
    "ROOT_RESTART_DURABILITY",
    "ROOT_WITNESS_ORDER",
    "SCHEMA_CLASS",
    "WP_ID",
    "WITNESS_COMPLETE",
    "WITNESS_INCOMPLETE",
    "compose_p1_completeness_witness_bundle_v1",
    "derive_provenance_witness_v1",
    "derive_time_domain_witness_v1",
    "evaluate_currency_domain_witness_v1",
    "evaluate_event_ordering_witness_v1",
    "evaluate_liability_event_class_witness_v1",
    "evaluate_observation_freshness_witness_v1",
    "evaluate_pagination_exhaustion_witness_v1",
    "evaluate_restart_durability_witness_v1",
    "evaluate_sealed_p1_completeness_witness_bundle_v1",
    "first_real_blocker_from_bundle_v1",
    "load_sealed_p1_witness_evidence_v1",
    "p1_conjunction_status_from_bundle_v1",
    "root_by_id_v1",
    "validate_witness_bundle_v1",
    "witness_bundle_digest_v1",
    "witness_bundle_to_mapping_v1",
    "witness_flags_for_p1_closeout_v1",
]
