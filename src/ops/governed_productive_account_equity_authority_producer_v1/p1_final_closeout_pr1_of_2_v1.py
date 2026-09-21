"""P1 final closeout PR 1/2: freshness, time, provenance, restart, #6665 re-eval.

Consumes sealed P1 witness packs through D5 checkpoint freshness, bound time
domain, offline restart durability, and negative closeout. No GET unless
future scoped authorization adds network (this WP: offline only).
AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_bounded_query_traversal_completeness_witness_v1 import (
    CANONICAL_PACK_AS_OF_FOLDER as TRAVERSAL_PACK_FOLDER,
    CANONICAL_PACK_RELPATH as TRAVERSAL_PACK_RELPATH,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_d5_checkpoint_freshness_witness_v1 import (
    build_p1_d5_checkpoint_freshness_witness_adjudication_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_negative_completeness_closeout_contract_v1 import (
    evaluate_sealed_interest_accrued_p1_closeout_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_observation_restart_durability_witness_v1 import (
    build_p1_observation_restart_durability_witness_adjudication_v1,
    prove_offline_observation_restart_durability_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_time_domain_completeness_witness_v1 import (
    build_p1_time_domain_completeness_witness_adjudication_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_d5_checkpoint_freshness_witness_v1 import (
    CANONICAL_CD_PACK,
    CANONICAL_USDC_P1_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

WP_ID = "FULL_CORE_P1_FINAL_CLOSEOUT_PR1_OF_2_V1"
OWNER_GO = WP_ID
ALLOWED_OWNER_GOS = frozenset({OWNER_GO, f"OWNER_GO_{OWNER_GO}", "OWNER_GO=true"})
EXPECTED_ORIGIN_MAIN_SHA = "4230a9f1a3e29ac4c84ee28ec4b5a880b1e030ed"
CANONICAL_PACK_RELPATH = "evidence/ops/full_core_p1_final_closeout_pr1_of_2_v1"
CANONICAL_PACK_AS_OF_FOLDER = "2026-09-21T050000Z"
SCHEMA_CLASS = "P1_FINAL_CLOSEOUT_PR1_OF_2_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"


class P1FinalCloseoutPr1Error(ValueError):
    """Fail-closed P1 final closeout PR1 violation."""


@dataclass(frozen=True)
class P1FinalCloseoutPr1ResultV1:
    wp_id: str
    origin_main_sha: str
    persist_as_of: str
    store_root: str
    network_used: str
    observation_freshness_proven: str
    time_domain_proven: str
    provenance_proven: str
    restart_durability_proven: str
    p1_status_after: str
    closeout_decision: str
    first_real_blocker: str
    blocker_class: str
    missing_fact_or_authority: str
    p1_closed_in_this_pr: str


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
        raise P1FinalCloseoutPr1Error(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _as_bool_token(value: object) -> bool:
    return str(value or "").lower() == TRUE_TOKEN


def execute_p1_final_closeout_pr1_of_2_v1(
    *,
    repo_root: Path | str,
    origin_main_sha: str,
    owner_go: str,
    persist_as_of: str,
    skip_persist: bool = False,
    offline_reload_store: Path | str | None = None,
) -> P1FinalCloseoutPr1ResultV1:
    if owner_go not in ALLOWED_OWNER_GOS:
        raise P1FinalCloseoutPr1Error(f"OWNER_GO_NOT_AUTHORIZED:{owner_go}")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P1FinalCloseoutPr1Error("ORIGIN_MAIN_SHA_MISMATCH")

    repo = Path(repo_root)
    traversal_pack = repo / TRAVERSAL_PACK_RELPATH / TRAVERSAL_PACK_FOLDER
    if verify_manifest_sha256_v1(store_root=traversal_pack) != 0:
        raise P1FinalCloseoutPr1Error("TRAVERSAL_WITNESS_PACK_INVALID")

    traversal_adj = _load_json_object(
        path=traversal_pack / "p1_bounded_query_traversal_witness_adjudication_v1.json"
    )
    usdc_pack = repo / CANONICAL_USDC_P1_PACK_RELPATH
    cd_pack = repo / CANONICAL_CD_PACK
    cd_claims = _load_json_object(path=cd_pack / "claims.json")
    usdc_claims = _load_json_object(path=usdc_pack / "claims.json")
    reopen = _load_json_object(path=usdc_pack / "interest_accrued_reopen_adjudication_v1.json")

    pagination_proven = _as_bool_token(
        traversal_adj.get("P1_PAGINATION_QUERY_TRAVERSAL_EXHAUSTION_PROVEN")
    )

    freshness_adj = build_p1_d5_checkpoint_freshness_witness_adjudication_v1(
        repo_root=repo,
        traversal_pagination_proven=pagination_proven,
    )
    time_adj = build_p1_time_domain_completeness_witness_adjudication_v1(
        traversal_adjudication=traversal_adj,
        cd_claims=cd_claims,
        usdc_claims=usdc_claims,
        reopen_adjudication=reopen,
    )

    reload_root = (
        Path(offline_reload_store)
        if offline_reload_store is not None
        else repo / ".p1_offline_restart_reload_tmp"
    )
    offline_proof = prove_offline_observation_restart_durability_v1(
        repo_root=repo,
        reload_store=reload_root,
    )
    restart_adj = build_p1_observation_restart_durability_witness_adjudication_v1(
        offline_proof=offline_proof,
    )

    folder = persist_as_of.replace(":", "")
    store = repo / CANONICAL_PACK_RELPATH / folder
    if not skip_persist:
        _persist_json(
            path=store / "p1_d5_checkpoint_freshness_witness_adjudication_v1.json",
            payload=freshness_adj,
        )
        _persist_json(
            path=store / "p1_time_domain_completeness_witness_adjudication_v1.json",
            payload=time_adj,
        )
        _persist_json(
            path=store / "p1_observation_restart_durability_witness_adjudication_v1.json",
            payload=restart_adj,
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
                "TRAVERSAL_PACK_CONSUMED": str(traversal_pack.relative_to(repo)),
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

    p1_closed = (
        TRUE_TOKEN
        if closeout.p1_status_after == "PROVEN_FALSE"
        and closeout.closeout_decision == "PROVEN_NEGATIVE"
        else FALSE_TOKEN
    )

    if not skip_persist:
        _persist_json(
            path=store / "p1_final_closeout_report_v1.json",
            payload={
                "WP_ID": WP_ID,
                "ORIGIN_MAIN_SHA": origin_main_sha,
                "WITNESS_BUNDLE": witness_bundle_to_mapping_v1(bundle),
                "CLOSEOUT_DECISION": closeout.closeout_decision,
                "P1_STATUS_AFTER": closeout.p1_status_after,
                "FIRST_REAL_BLOCKER": blocker_id,
                "BLOCKER_CLASS": blocker_class,
                "MISSING_FACT_OR_AUTHORITY": missing,
                "P1_CLOSED_IN_THIS_PR": p1_closed,
                "ROOTS_PROVEN": {
                    ROOT_CURRENCY_DOMAIN: root_by_id_v1(bundle, ROOT_CURRENCY_DOMAIN).complete,
                    ROOT_LIABILITY_EVENT_CLASS: root_by_id_v1(
                        bundle, ROOT_LIABILITY_EVENT_CLASS
                    ).complete,
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

    return P1FinalCloseoutPr1ResultV1(
        wp_id=WP_ID,
        origin_main_sha=origin_main_sha,
        persist_as_of=persist_as_of,
        store_root=str(store),
        network_used=FALSE_TOKEN,
        observation_freshness_proven=freshness_adj["P1_OBSERVATION_FRESHNESS_COMPLETENESS_PROVEN"],
        time_domain_proven=time_adj["P1_TIME_DOMAIN_EXHAUSTION_PROVEN"],
        provenance_proven=TRUE_TOKEN if bundle.provenance.complete else FALSE_TOKEN,
        restart_durability_proven=restart_adj["P1_RESTART_DURABILITY_COMPLETENESS_PROVEN"],
        p1_status_after=closeout.p1_status_after,
        closeout_decision=closeout.closeout_decision,
        first_real_blocker=blocker_id,
        blocker_class=blocker_class,
        missing_fact_or_authority=missing,
        p1_closed_in_this_pr=p1_closed,
    )


def verify_canonical_p1_final_closeout_pr1_pack_v1(*, repo_root: Path | str) -> int:
    store = Path(repo_root) / CANONICAL_PACK_RELPATH / CANONICAL_PACK_AS_OF_FOLDER
    return verify_manifest_sha256_v1(store_root=store)


__all__ = [
    "ALLOWED_OWNER_GOS",
    "AUTHORITY_EFFECT",
    "CANONICAL_PACK_AS_OF_FOLDER",
    "CANONICAL_PACK_RELPATH",
    "CONTRACT_VERSION",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "OWNER_GO",
    "P1FinalCloseoutPr1Error",
    "P1FinalCloseoutPr1ResultV1",
    "SCHEMA_CLASS",
    "WP_ID",
    "execute_p1_final_closeout_pr1_of_2_v1",
    "verify_canonical_p1_final_closeout_pr1_pack_v1",
]
