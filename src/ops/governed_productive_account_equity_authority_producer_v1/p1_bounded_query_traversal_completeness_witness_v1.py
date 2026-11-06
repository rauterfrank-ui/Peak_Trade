"""P1 bounded query traversal, ordering, and related root witnesses (offline).

Consumes sealed CD and USDC P1 interest-accrued GET packs plus currency-domain
and liability governance witnesses. Proves P1 pagination query traversal and
vacuous event ordering for zero-row bound queries. Does not mint time-domain
exhaustion from zero rows or genesis-point D5 freshness. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    PAGINATION_EXHAUSTION_PROVES_COMPLETENESS,
    PAGINATION_EXHAUSTION_PROVES_QUERY_TRAVERSAL_COMPLETED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_completeness_witness_foundation_v1 import (
    evaluate_sealed_p1_completeness_witness_bundle_v1,
    first_real_blocker_from_bundle_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_liability_event_class_governance_and_ratified_query_class_set_v1 import (
    CANONICAL_PACK_RELPATH as LIABILITY_PACK_RELPATH,
    CANONICAL_PACK_AS_OF_FOLDER as LIABILITY_PACK_FOLDER,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_negative_completeness_closeout_contract_v1 import (
    evaluate_sealed_interest_accrued_p1_closeout_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_independent_liability_event_surface_or_embedding_witness_qualification_v1 import (
    SELECTED_SURFACE_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_primary_proof_bound_interest_accrued_get_acquisition_v1 import (
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
CANONICAL_PACK_RELPATH = "evidence/ops/full_core_p1_bounded_query_traversal_completeness_witness_v1"
CANONICAL_PACK_AS_OF_FOLDER = "2026-09-21T040500Z"
SCHEMA_CLASS = "P1_BOUNDED_QUERY_TRAVERSAL_COMPLETENESS_WITNESS_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
PAGINATION_MODEL = "limit_only_no_cursor_in_binding"


class P1BoundedQueryTraversalCompletenessWitnessError(ValueError):
    """Fail-closed P1 bounded query traversal witness violation."""


@dataclass(frozen=True)
class P1BoundedQueryTraversalCompletenessWitnessResultV1:
    wp_id: str
    origin_main_sha: str
    persist_as_of: str
    store_root: str
    pagination_proven: str
    event_ordering_proven: str
    observation_freshness_proven: str
    time_domain_proven: str
    first_real_blocker: str
    blocker_class: str
    missing_fact_or_authority: str


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
        raise P1BoundedQueryTraversalCompletenessWitnessError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _as_bool_token(value: object) -> bool:
    return str(value or "").lower() == TRUE_TOKEN


def _row_count_from_offline(*, offline: Mapping[str, Any]) -> int:
    return int(str(offline.get("row_count", "0")))


def build_p1_bounded_query_traversal_witness_adjudication_v1(
    *,
    surface_binding: Mapping[str, Any],
    surface_discovery: Mapping[str, Any],
    cd_claims: Mapping[str, Any],
    usdc_claims: Mapping[str, Any],
    usdc_offline: Mapping[str, Any],
    liability_adjudication: Mapping[str, Any],
    currency_adjudication: Mapping[str, Any],
    d5_event_completeness_from_window: str,
    d5_binding_present: bool,
) -> dict[str, Any]:
    if PAGINATION_EXHAUSTION_PROVES_COMPLETENESS is not False:
        raise P1BoundedQueryTraversalCompletenessWitnessError(
            "PAGINATION_EXHAUSTION_MUST_NOT_PROVE_COMPLETENESS"
        )
    if PAGINATION_EXHAUSTION_PROVES_QUERY_TRAVERSAL_COMPLETED is not True:
        raise P1BoundedQueryTraversalCompletenessWitnessError("QUERY_TRAVERSAL_PIN_DRIFT")

    missing_pagination = NONE_TOKEN
    pagination_proven = False
    ordering_proven = False
    freshness_proven = False
    time_proven = False

    if not _as_bool_token(
        liability_adjudication.get("P1_LIABILITY_EVENT_CLASS_COMPLETENESS_PROVEN")
    ):
        missing_pagination = "LIABILITY_EVENT_CLASS_COMPLETE_REQUIRED_FIRST"
    elif not _as_bool_token(currency_adjudication.get("P1_CURRENCY_DOMAIN_COMPLETENESS_PROVEN")):
        missing_pagination = "CURRENCY_DOMAIN_COMPLETE_REQUIRED_FIRST"
    elif str(surface_binding.get("P1_EVENT_SURFACE", "")) != SELECTED_SURFACE_ID:
        missing_pagination = "P1_SURFACE_BINDING_MISMATCH"
    elif str(surface_binding.get("MAX_PAGES", "")) != "1":
        missing_pagination = "MAX_PAGES_NOT_ONE_BOUND_QUERY"
    elif (
        str(cd_claims.get("HTTP_STATUS", "")) != "200"
        or str(usdc_claims.get("HTTP_STATUS", "")) != "200"
    ):
        missing_pagination = "SEALED_GET_NOT_BOTH_HTTP_200"
    else:
        pagination_model = ""
        for record in surface_discovery.get("records", []):
            if not isinstance(record, Mapping):
                continue
            if str(record.get("SURFACE_ID", "")) != SELECTED_SURFACE_ID:
                continue
            pagination_model = str(record.get("PAGINATION_MODEL", ""))
            break
        if pagination_model != PAGINATION_MODEL:
            missing_pagination = f"PAGINATION_MODEL_NOT_BOUND:{pagination_model}"
        else:
            pagination_proven = True
            missing_pagination = NONE_TOKEN
            cd_rows = int(
                str(
                    cd_claims.get(
                        "QUALIFYING_LIABILITY_ROWS",
                        cd_claims.get("ROW_COUNT", "0"),
                    )
                )
            )
            combined_rows = _row_count_from_offline(offline=usdc_offline) + cd_rows
            if combined_rows == 0:
                ordering_proven = True
            else:
                missing_pagination = (
                    "NONZERO_ROWS_REQUIRE_EXPLICIT_ORDERING_WITNESS_NOT_IN_THIS_PACK"
                )
                pagination_proven = False

    freshness_missing = "GENESIS_POINT_D5_WINDOW_NOT_P1_FRESHNESS_COMPLETE"
    if d5_binding_present and d5_event_completeness_from_window.lower() == FALSE_TOKEN:
        freshness_missing = (
            "D5_GENESIS_POINT_WINDOW_BINDING_PRESENT_BUT_OBSERVATION_FRESHNESS_"
            "REQUIRES_P1_BOUND_CHECKPOINT_FRESHNESS_WITNESS_NOT_GENESIS_POINT_ALONE"
        )

    time_missing = "VENUE_PAST_YEAR_TIME_DOMAIN_NOT_PROVEN_FROM_ZERO_ROWS_OR_SINGLE_PAGE_ALONE"

    return {
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "WP_ID": WP_ID,
        "layer": "CANONICAL_AUTHORITY",
        "P1_PAGINATION_QUERY_TRAVERSAL_EXHAUSTION_PROVEN": (
            TRUE_TOKEN if pagination_proven else FALSE_TOKEN
        ),
        "P1_PAGINATION_DETAIL": (
            "Both sealed bound interest-accrued queries executed under limit-only "
            "no-cursor binding; query traversal complete, not domain completeness"
            if pagination_proven
            else missing_pagination
        ),
        "P1_EVENT_ORDERING_COMPLETENESS_PROVEN": TRUE_TOKEN if ordering_proven else FALSE_TOKEN,
        "P1_EVENT_ORDERING_DETAIL": (
            "Zero qualifying rows under bound queries; vacuous ordering complete with "
            "venue ts semantics bound for non-empty cases"
            if ordering_proven
            else "ORDERING_NOT_PROVEN"
        ),
        "P1_OBSERVATION_FRESHNESS_COMPLETENESS_PROVEN": (
            TRUE_TOKEN if freshness_proven else FALSE_TOKEN
        ),
        "P1_OBSERVATION_FRESHNESS_DETAIL": freshness_missing,
        "P1_TIME_DOMAIN_EXHAUSTION_PROVEN": TRUE_TOKEN if time_proven else FALSE_TOKEN,
        "P1_TIME_DOMAIN_DETAIL": time_missing,
        "PAGINATION_DOMAIN_COMPLETENESS_CLAIMED": FALSE_TOKEN,
        "BOUNDED_TRAVERSAL_MISSING_FACT": missing_pagination,
    }


def execute_p1_bounded_query_traversal_completeness_witness_v1(
    *,
    repo_root: Path | str,
    origin_main_sha: str,
    owner_go: str,
    persist_as_of: str,
    skip_persist: bool = False,
) -> P1BoundedQueryTraversalCompletenessWitnessResultV1:
    if owner_go not in ALLOWED_OWNER_GOS:
        raise P1BoundedQueryTraversalCompletenessWitnessError(f"OWNER_GO_NOT_AUTHORIZED:{owner_go}")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P1BoundedQueryTraversalCompletenessWitnessError("ORIGIN_MAIN_SHA_MISMATCH")

    repo = Path(repo_root)
    liability_pack = repo / LIABILITY_PACK_RELPATH / LIABILITY_PACK_FOLDER
    if verify_manifest_sha256_v1(store_root=liability_pack) != 0:
        raise P1BoundedQueryTraversalCompletenessWitnessError("LIABILITY_WITNESS_PACK_INVALID")

    currency_pack = repo / (
        "evidence/ops/full_core_p1_currency_domain_completeness_witness_v1/2026-09-21T031500Z"
    )
    usdc_pack = repo / CANONICAL_USDC_P1_PACK_RELPATH
    cd_pack = repo / CANONICAL_CD_PACK_RELPATH

    liability_adj = _load_json_object(
        path=liability_pack / "p1_liability_event_class_witness_adjudication_v1.json"
    )
    currency_adj = _load_json_object(
        path=currency_pack / "p1_currency_domain_witness_adjudication_v1.json"
    )
    binding = _load_json_object(path=usdc_pack / "p1_surface_binding_v1.json")
    discovery = _load_json_object(path=usdc_pack / "futures_p1_surface_discovery_v1.json")
    cd_claims = _load_json_object(path=cd_pack / "claims.json")
    usdc_claims = _load_json_object(path=usdc_pack / "claims.json")
    usdc_offline = _load_json_object(path=usdc_pack / "p1_offline_qualification_v1.json")

    d5_present = False
    d5_event_completeness = FALSE_TOKEN
    from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_s0_runtime_binding_gate_v1 import (
        resolve_canonical_d4_d5_genesis_runtime_store_root_v1,
    )

    genesis_root = resolve_canonical_d4_d5_genesis_runtime_store_root_v1(repo_root=repo)
    if genesis_root is not None:
        d5_path = genesis_root / "d5_checkpoint_observation_window_binding_v1.json"
        if d5_path.is_file():
            d5_present = True
            d5_payload = _load_json_object(path=d5_path)
            d5_event_completeness = str(
                d5_payload.get("event_completeness_from_window", FALSE_TOKEN)
            )

    adjudication = build_p1_bounded_query_traversal_witness_adjudication_v1(
        surface_binding=binding,
        surface_discovery=discovery,
        cd_claims=cd_claims,
        usdc_claims=usdc_claims,
        usdc_offline=usdc_offline,
        liability_adjudication=liability_adj,
        currency_adjudication=currency_adj,
        d5_event_completeness_from_window=d5_event_completeness,
        d5_binding_present=d5_present,
    )

    folder = persist_as_of.replace(":", "")
    store = repo / CANONICAL_PACK_RELPATH / folder
    if not skip_persist:
        _persist_json(
            path=store / "p1_bounded_query_traversal_witness_adjudication_v1.json",
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
                "LIABILITY_PACK_CONSUMED": str(liability_pack.relative_to(repo)),
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

    return P1BoundedQueryTraversalCompletenessWitnessResultV1(
        wp_id=WP_ID,
        origin_main_sha=origin_main_sha,
        persist_as_of=persist_as_of,
        store_root=str(store),
        pagination_proven=adjudication["P1_PAGINATION_QUERY_TRAVERSAL_EXHAUSTION_PROVEN"],
        event_ordering_proven=adjudication["P1_EVENT_ORDERING_COMPLETENESS_PROVEN"],
        observation_freshness_proven=adjudication["P1_OBSERVATION_FRESHNESS_COMPLETENESS_PROVEN"],
        time_domain_proven=adjudication["P1_TIME_DOMAIN_EXHAUSTION_PROVEN"],
        first_real_blocker=blocker_id,
        blocker_class=blocker_class,
        missing_fact_or_authority=missing,
    )


__all__ = [
    "ALLOWED_OWNER_GOS",
    "AUTHORITY_EFFECT",
    "CANONICAL_PACK_AS_OF_FOLDER",
    "CANONICAL_PACK_RELPATH",
    "CONTRACT_VERSION",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "OWNER_GO",
    "P1BoundedQueryTraversalCompletenessWitnessError",
    "P1BoundedQueryTraversalCompletenessWitnessResultV1",
    "SCHEMA_CLASS",
    "WP_ID",
    "build_p1_bounded_query_traversal_witness_adjudication_v1",
    "execute_p1_bounded_query_traversal_completeness_witness_v1",
]
