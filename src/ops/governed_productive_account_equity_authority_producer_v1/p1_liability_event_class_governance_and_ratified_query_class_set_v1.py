"""P1 liability event-class governance and ratified query-class set (offline).

Consumes Owner-GO FULL_CORE_P1_LIABILITY_GOVERNANCE_AND_MAX_CLOSEOUT_TO_NEXT_
REAL_BLOCKER_V1. Ratifies the P1-scoped interest-accrued Market-loan query class
from sealed surface binding and venue specification. Does not mutate global
D6 EQUITY_STOCK RATIFIED_CLASSIFIED_KIND_SET or KIND_SET_RESOLVED.
AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    KIND_SET_RESOLVED,
    U05_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
    RATIFIED_CLASSIFIED_KIND_SET_RESOLVED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_completeness_witness_foundation_v1 import (
    DERIVED_PROVENANCE,
    DERIVED_TIME_DOMAIN,
    ROOT_CURRENCY_DOMAIN,
    ROOT_EVENT_ORDERING,
    ROOT_LIABILITY_EVENT_CLASS,
    ROOT_OBSERVATION_FRESHNESS,
    ROOT_PAGINATION,
    ROOT_RESTART_DURABILITY,
    evaluate_sealed_p1_completeness_witness_bundle_v1,
    first_real_blocker_from_bundle_v1,
    root_by_id_v1,
    witness_bundle_to_mapping_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_negative_completeness_closeout_contract_v1 import (
    evaluate_sealed_interest_accrued_p1_closeout_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_independent_liability_event_surface_or_embedding_witness_qualification_v1 import (
    LOAN_TYPE_MARKET,
    SELECTED_SURFACE_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_primary_proof_bound_interest_accrued_get_acquisition_v1 import (
    AUTHORIZED_QUERY as CD_AUTHORIZED_QUERY,
    CANONICAL_PACK_RELPATH as CANONICAL_CD_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_USDC_P1_PACK_ROOT,
)

CANONICAL_USDC_P1_PACK_RELPATH = f"{CANONICAL_USDC_P1_PACK_ROOT}/2026-09-20T233000Z"

WP_ID = "FULL_CORE_P1_LIABILITY_GOVERNANCE_AND_MAX_CLOSEOUT_TO_NEXT_REAL_BLOCKER_V1"
OWNER_GO = WP_ID
ALLOWED_OWNER_GOS = frozenset({OWNER_GO, f"OWNER_GO_{OWNER_GO}", "OWNER_GO=true"})
EXPECTED_ORIGIN_MAIN_SHA = "eb5857ffd1694d8a45e06ccfb771f261010ae242"
CANONICAL_PACK_RELPATH = "evidence/ops/full_core_p1_liability_event_class_governance_witness_v1"
CANONICAL_PACK_AS_OF_FOLDER = "2026-09-21T040000Z"
SCHEMA_CLASS = "P1_LIABILITY_EVENT_CLASS_GOVERNANCE_WITNESS_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"

RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET: tuple[str, ...] = (SELECTED_SURFACE_ID,)
RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET_RESOLVED = True
GLOBAL_EQUITY_STOCK_KIND_SET_UPLIFT = False

AUTHORIZED_CD_QUERY = CD_AUTHORIZED_QUERY
AUTHORIZED_USDC_P1_QUERY = "type=2&limit=100&ccy=USDC"
INTEREST_ACCRUED_TYPE_ALIGNMENT = f"type={LOAN_TYPE_MARKET}"

_REPO_ROOT = Path(__file__).resolve().parents[3]


class P1LiabilityEventClassGovernanceError(ValueError):
    """Fail-closed P1 liability event-class governance violation."""


@dataclass(frozen=True)
class P1LiabilityEventClassGovernanceResultV1:
    wp_id: str
    origin_main_sha: str
    persist_as_of: str
    store_root: str
    network_used: str
    p1_liability_event_class_completeness_proven: str
    ratified_query_class_count: str
    global_kind_set_unchanged: str
    p1_status_after: str
    first_real_blocker: str
    blocker_class: str
    missing_fact_or_authority: str
    closeout_decision: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise P1LiabilityEventClassGovernanceError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _assert_global_kind_set_pins_unchanged() -> None:
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise P1LiabilityEventClassGovernanceError("GLOBAL_RATIFIED_CLASSIFIED_KIND_SET_NON_EMPTY")
    if RATIFIED_CLASSIFIED_KIND_SET_RESOLVED is not False:
        raise P1LiabilityEventClassGovernanceError("GLOBAL_KIND_SET_RESOLVED_MUST_REMAIN_FALSE")
    if KIND_SET_RESOLVED is not False:
        raise P1LiabilityEventClassGovernanceError("KIND_SET_RESOLVED_MUST_REMAIN_FALSE")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise P1LiabilityEventClassGovernanceError(
            "U05_EQUITY_STOCK_KIND_DECISION_MUST_REMAIN_UNKNOWN"
        )
    if GLOBAL_EQUITY_STOCK_KIND_SET_UPLIFT is not False:
        raise P1LiabilityEventClassGovernanceError("GLOBAL_KIND_SET_UPLIFT_FORBIDDEN")


def build_p1_liability_query_class_authority_binding_v1() -> dict[str, Any]:
    """Pinned authority chain for P1-scoped query-class ratification."""
    return {
        "layer": "CANONICAL_AUTHORITY",
        "wp_id": WP_ID,
        "global_equity_stock_kind_set_uplift": FALSE_TOKEN,
        "global_ratified_classified_kind_set": "EMPTY_FAIL_CLOSED",
        "global_kind_set_resolved": FALSE_TOKEN,
        "u05_equity_stock_kind_decision": DECISION_REMAIN_UNKNOWN,
        "ratified_p1_liability_event_query_class_set": list(
            RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET
        ),
        "ratified_p1_liability_event_query_class_set_resolved": TRUE_TOKEN,
        "selected_surface_id": SELECTED_SURFACE_ID,
        "loan_type_market": LOAN_TYPE_MARKET,
        "interest_accrued_type_alignment": INTEREST_ACCRUED_TYPE_ALIGNMENT,
        "authorized_cd_query": AUTHORIZED_CD_QUERY,
        "authorized_usdc_p1_query": AUTHORIZED_USDC_P1_QUERY,
        "venue_spec_excerpt_ids": (
            "INTEREST_ACCRUED_IDENTITY",
            "INTEREST_ACCRUED_LOAN_TYPE",
            "INTEREST_ACCRUED_FIELDS",
        ),
        "sealed_surface_binding_pack": CANONICAL_USDC_P1_PACK_RELPATH,
        "sealed_cd_pack": CANONICAL_CD_PACK_RELPATH,
        "sealed_u05_surface_qualification": (
            "evidence/ops/full_core_u05_independent_liability_event_surface_or_"
            "embedding_witness_qualification_v1/2026-09-15T003000Z"
        ),
        "semantic_scope": (
            "P1_INDEPENDENT_LIABILITY_EVENT_QUERY_CLASS_NOT_EQUITY_STOCK_KIND_RATIFICATION"
        ),
    }


def build_p1_liability_event_class_witness_adjudication_v1(
    *,
    surface_binding: Mapping[str, Any],
    surface_discovery: Mapping[str, Any],
    cd_claims: Mapping[str, Any],
    usdc_claims: Mapping[str, Any],
) -> dict[str, Any]:
    """Offline fail-closed adjudication for P1 liability event-class completeness."""
    _assert_global_kind_set_pins_unchanged()

    missing = NONE_TOKEN
    proven = False

    p1_surface = str(surface_binding.get("P1_EVENT_SURFACE", ""))
    account_mode = str(surface_binding.get("ACCOUNT_MODE", ""))
    authorized_query = str(surface_binding.get("AUTHORIZED_QUERY", ""))
    cd_http = str(cd_claims.get("HTTP_STATUS", ""))
    usdc_http = str(usdc_claims.get("HTTP_STATUS", ""))

    if p1_surface != SELECTED_SURFACE_ID:
        missing = f"P1_EVENT_SURFACE_MISMATCH:{p1_surface}"
    elif account_mode != "FUTURES_MODE":
        missing = f"ACCOUNT_MODE_NOT_FUTURES:{account_mode}"
    elif LOAN_TYPE_MARKET not in authorized_query:
        missing = "AUTHORIZED_QUERY_MISSING_MARKET_LOAN_TYPE_2"
    elif cd_http != "200" or usdc_http != "200":
        missing = "SEALED_INTEREST_ACCRUED_GET_NOT_BOTH_HTTP_200"
    else:
        capable_ok = False
        for record in surface_discovery.get("records", []):
            if not isinstance(record, Mapping):
                continue
            if str(record.get("SURFACE_ID", "")) != SELECTED_SURFACE_ID:
                continue
            if str(record.get("STATUS", "")) != "CAPABLE_WITH_BOUNDED_BINDING":
                missing = "SELECTED_SURFACE_NOT_CAPABLE_WITH_BOUNDED_BINDING"
                break
            consumed = str(record.get("PREVIOUSLY_CONSUMED", ""))
            if "CD_UNSCOPED" not in consumed or "P1_USDC_SCOPE_NEW" not in consumed:
                missing = "BOUND_QUERY_VARIANTS_NOT_BOTH_CONSUMED"
                break
            capable_ok = True
        else:
            if not capable_ok:
                missing = "SELECTED_SURFACE_RECORD_MISSING"
            elif not RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET:
                missing = "RATIFIED_P1_QUERY_CLASS_SET_EMPTY"
            elif not RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET_RESOLVED:
                missing = "RATIFIED_P1_QUERY_CLASS_SET_UNRESOLVED"
            else:
                proven = True
                missing = NONE_TOKEN

    return {
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "WP_ID": WP_ID,
        "layer": "CANONICAL_AUTHORITY",
        "P1_LIABILITY_EVENT_CLASS_COMPLETENESS_PROVEN": TRUE_TOKEN if proven else FALSE_TOKEN,
        "RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET": list(
            RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET
        ),
        "RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET_RESOLVED": (
            TRUE_TOKEN if RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET_RESOLVED else FALSE_TOKEN
        ),
        "GLOBAL_KIND_SET_UNCHANGED": TRUE_TOKEN,
        "INTEREST_ACCRUED_TYPE_ALIGNMENT": INTEREST_ACCRUED_TYPE_ALIGNMENT,
        "LIABILITY_EVENT_CLASS_MISSING_FACT": missing,
        "NOT_EQUITY_STOCK_U05_KIND_RATIFICATION": TRUE_TOKEN,
    }


def execute_p1_liability_event_class_governance_witness_v1(
    *,
    repo_root: Path | str,
    origin_main_sha: str,
    owner_go: str,
    persist_as_of: str,
    skip_persist: bool = False,
) -> P1LiabilityEventClassGovernanceResultV1:
    if owner_go not in ALLOWED_OWNER_GOS:
        raise P1LiabilityEventClassGovernanceError(f"OWNER_GO_NOT_AUTHORIZED:{owner_go}")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P1LiabilityEventClassGovernanceError("ORIGIN_MAIN_SHA_MISMATCH")

    repo = Path(repo_root)
    usdc_pack = repo / CANONICAL_USDC_P1_PACK_RELPATH
    cd_pack = repo / CANONICAL_CD_PACK_RELPATH
    binding = _load_json_object(path=usdc_pack / "p1_surface_binding_v1.json")
    discovery = _load_json_object(path=usdc_pack / "futures_p1_surface_discovery_v1.json")
    cd_claims = _load_json_object(path=cd_pack / "claims.json")
    usdc_claims = _load_json_object(path=usdc_pack / "claims.json")

    authority = build_p1_liability_query_class_authority_binding_v1()
    adjudication = build_p1_liability_event_class_witness_adjudication_v1(
        surface_binding=binding,
        surface_discovery=discovery,
        cd_claims=cd_claims,
        usdc_claims=usdc_claims,
    )

    folder = persist_as_of.replace(":", "")
    store = repo / CANONICAL_PACK_RELPATH / folder
    if not skip_persist:
        _persist_json(
            path=store / "p1_liability_query_class_authority_binding_v1.json", payload=authority
        )
        _persist_json(
            path=store / "p1_liability_event_class_witness_adjudication_v1.json",
            payload=adjudication,
        )
        _persist_json(
            path=store / "claims.json",
            payload={
                "SCHEMA_CLASS": SCHEMA_CLASS,
                "CONTRACT_VERSION": CONTRACT_VERSION,
                "WP_ID": WP_ID,
                "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
                "ORIGIN_MAIN_SHA": origin_main_sha,
                "PERSIST_AS_OF": persist_as_of,
                "NETWORK_USED": FALSE_TOKEN,
                "AUTHORIZED_GET_COUNT": "0",
                "ACTUAL_GET_COUNT": "0",
                "RATIFIED_QUERY_CLASS_COUNT": str(len(RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET)),
                "CD_PACK_CONSUMED": str(cd_pack.relative_to(repo)),
                "USDC_P1_PACK_CONSUMED": str(usdc_pack.relative_to(repo)),
                "GENESIS_ID": EXPECTED_GENESIS_ID,
                "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
            },
        )
        persist_manifest_sha256_v1(store_root=store)

    bundle = evaluate_sealed_p1_completeness_witness_bundle_v1(
        repo_root=repo, bound_origin_main_sha=origin_main_sha
    )
    closeout = evaluate_sealed_interest_accrued_p1_closeout_v1(repo_root=repo)
    blocker_id, blocker_class, missing = first_real_blocker_from_bundle_v1(bundle)
    liability = root_by_id_v1(bundle, ROOT_LIABILITY_EVENT_CLASS)

    if not skip_persist:
        _persist_json(
            path=store / "p1_liability_governance_closeout_report_v1.json",
            payload={
                "WP_ID": WP_ID,
                "ORIGIN_MAIN_SHA": origin_main_sha,
                "WITNESS_BUNDLE": witness_bundle_to_mapping_v1(bundle),
                "CLOSEOUT_DECISION": closeout.closeout_decision,
                "P1_STATUS_AFTER": closeout.p1_status_after,
                "FIRST_REAL_BLOCKER": blocker_id,
                "BLOCKER_CLASS": blocker_class,
                "MISSING_FACT_OR_AUTHORITY": missing,
                "ROOTS_PROVEN": {
                    ROOT_CURRENCY_DOMAIN: root_by_id_v1(bundle, ROOT_CURRENCY_DOMAIN).complete,
                    ROOT_LIABILITY_EVENT_CLASS: liability.complete,
                    ROOT_PAGINATION: root_by_id_v1(bundle, ROOT_PAGINATION).complete,
                    ROOT_EVENT_ORDERING: root_by_id_v1(bundle, ROOT_EVENT_ORDERING).complete,
                    ROOT_OBSERVATION_FRESHNESS: root_by_id_v1(
                        bundle, ROOT_OBSERVATION_FRESHNESS
                    ).complete,
                    ROOT_RESTART_DURABILITY: root_by_id_v1(
                        bundle, ROOT_RESTART_DURABILITY
                    ).complete,
                    DERIVED_TIME_DOMAIN: bundle.time_domain.complete,
                    DERIVED_PROVENANCE: bundle.provenance.complete,
                },
            },
        )
        persist_manifest_sha256_v1(store_root=store)

    return P1LiabilityEventClassGovernanceResultV1(
        wp_id=WP_ID,
        origin_main_sha=origin_main_sha,
        persist_as_of=persist_as_of,
        store_root=str(store),
        network_used=FALSE_TOKEN,
        p1_liability_event_class_completeness_proven=adjudication[
            "P1_LIABILITY_EVENT_CLASS_COMPLETENESS_PROVEN"
        ],
        ratified_query_class_count=str(len(RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET)),
        global_kind_set_unchanged=TRUE_TOKEN,
        p1_status_after=closeout.p1_status_after,
        first_real_blocker=blocker_id,
        blocker_class=blocker_class,
        missing_fact_or_authority=missing,
        closeout_decision=closeout.closeout_decision,
    )


def verify_canonical_p1_liability_governance_pack_v1(*, repo_root: Path | str) -> int:
    store = Path(repo_root) / CANONICAL_PACK_RELPATH / CANONICAL_PACK_AS_OF_FOLDER
    return verify_manifest_sha256_v1(store_root=store)


__all__ = [
    "ALLOWED_OWNER_GOS",
    "AUTHORITY_EFFECT",
    "CANONICAL_PACK_AS_OF_FOLDER",
    "CANONICAL_PACK_RELPATH",
    "CONTRACT_VERSION",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "GLOBAL_EQUITY_STOCK_KIND_SET_UPLIFT",
    "INTEREST_ACCRUED_TYPE_ALIGNMENT",
    "OWNER_GO",
    "P1LiabilityEventClassGovernanceError",
    "P1LiabilityEventClassGovernanceResultV1",
    "RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET",
    "RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET_RESOLVED",
    "SCHEMA_CLASS",
    "WP_ID",
    "build_p1_liability_event_class_witness_adjudication_v1",
    "build_p1_liability_query_class_authority_binding_v1",
    "execute_p1_liability_event_class_governance_witness_v1",
    "verify_canonical_p1_liability_governance_pack_v1",
]
