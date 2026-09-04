"""Offline adjudication of LIVE_EXECUTION_CODE_EXISTS and PATH_REACHABLE."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_SUBMIT_TRANSPORT_PATH,
    CANONICAL_RUNBOOK_PATH,
    CODE_PRESENCE_IS_NOT_LIVE_EXECUTION_CODE_EXISTS,
    CURRENTLY_REACHABLE_IS_NOT_LIVE_EXECUTION_PATH_REACHABLE,
    FLATTEN_EXECUTE_PATH,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_CODE_EXISTS,
    LIVE_EXECUTION_CODE_EXISTS_CANONICAL_DEFINITION,
    LIVE_EXECUTION_CODE_EXISTS_DOES_NOT_IMPLY_PATH_REACHABLE,
    SECTION_4_9_ANCHOR,
    SP01_PATH,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.static_execution_graph_v1 import (
    build_static_execution_graph_v1,
    evaluate_live_execution_code_exists_predicate_v1,
    file_presence_alone_v1,
)

_PROOF_KEYS = (
    "canonical_definition",
    "observed_repo_fact",
    "admissibility_rule",
    "evidence_paths",
    "contradiction_check",
    "adjudicated_value",
    "reason",
)


def _record(*, payload: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in _PROOF_KEYS if key not in payload]
    if missing:
        raise RuntimeError("STATIC_PROOF_KEYS_MISSING:" + ",".join(missing))
    return payload


def adjudicate_live_execution_code_exists_v1(*, repo_root: Path) -> dict[str, Any]:
    presence = file_presence_alone_v1(
        repo_root=repo_root,
        paths=(SP01_PATH, FLATTEN_EXECUTE_PATH, CANARY_SUBMIT_TRANSPORT_PATH),
    )
    graph = build_static_execution_graph_v1(repo_root=repo_root)
    predicate = evaluate_live_execution_code_exists_predicate_v1(
        repo_root=repo_root,
        source_kind="REPOSITORY_IMPLEMENTATION",
        graph=graph,
    )
    claim = bool(predicate["claim_value"] is True)
    observed = (
        f"FILE_PRESENCE_ALONE={str(presence['all_listed_files_exist']).lower()};"
        f"FILE_PRESENCE_ADMISSIBLE={str(presence['admissible_as_live_execution_code_exists']).lower()};"
        f"STATIC_GRAPH_STATUS={predicate['graph_status']};"
        f"REQUIRED_NODES_INTEGRATED={str(predicate['conjuncts']['REQUIRED_NODES_INTEGRATED']).lower()};"
        f"CHAIN_COMPLETE={str(predicate['conjuncts']['STATIC_EDGE_CHAIN_COMPLETE']).lower()}"
    )
    contradiction = (
        "NO_CONTRADICTION. Integrated current Live canary path satisfies the "
        "bound predicate. File presence remains supporting context only. "
        "Cap 11.7-11.11 remain contracts-only false and are not this field's "
        "SSOT. PATH_REACHABLE stays false. "
        "CODE_PRESENCE_IS_NOT_LIVE_EXECUTION_CODE_EXISTS="
        f"{str(CODE_PRESENCE_IS_NOT_LIVE_EXECUTION_CODE_EXISTS).lower()}."
    )
    if claim is not True:
        contradiction = (
            "NO_CONTRADICTION. Predicate unsatisfied; field remains false. "
            f"missing={predicate['missing_required_nodes']};"
            f"disallowed={predicate['disallowed_required_nodes']}"
        )
    reason = (
        "STATIC_INTEGRATED_PRODUCTIVE_PATH_PROVEN;"
        "CODE_PRESENCE_ALONE_INADMISSIBLE;"
        "PATH_REACHABLE_NOT_INFERRED;"
        "AUTHORIZATION_NOT_INFERRED;"
        "LATER_LADDER_FIELDS_NOT_PROMOTED;"
        "LIVE_EXECUTION_CODE_EXISTS=true"
        if claim
        else (
            "PREDICATE_UNSATISFIED;"
            + ",".join(predicate["missing_required_nodes"] or ["NONE"])
            + ";LIVE_EXECUTION_CODE_EXISTS=false"
        )
    )
    return _record(
        payload={
            "canonical_definition": LIVE_EXECUTION_CODE_EXISTS_CANONICAL_DEFINITION,
            "observed_repo_fact": observed,
            "admissibility_rule": predicate["admissibility_predicate"],
            "admissibility_predicate": predicate,
            "static_execution_graph": graph,
            "file_presence_alone": presence,
            "evidence_paths": [
                SP01_PATH,
                FLATTEN_EXECUTE_PATH,
                CANARY_SUBMIT_TRANSPORT_PATH,
                SECTION_4_9_ANCHOR,
                CANONICAL_RUNBOOK_PATH,
            ],
            "contradiction_check": contradiction,
            "adjudicated_value": claim,
            "reason": reason,
        }
    )


def adjudicate_live_execution_path_reachable_v1(
    *,
    repo_root: Path,
    credential_presence: Mapping[str, Any] | None = None,
    private_get_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.path_reachable_adjudication_v1 import (
        adjudicate_live_execution_path_reachable_v1 as _adjudicate,
    )

    proof = _adjudicate(
        repo_root=repo_root,
        credential_presence=credential_presence,
        private_get_evidence=private_get_evidence,
    )
    claim = bool(proof["adjudicated_value"] is True)
    observed = (
        f"CODE_EXISTS={str(LIVE_EXECUTION_CODE_EXISTS).lower()};"
        f"CONJUNCTION={proof['reason']};"
        f"PRIVATE_GET_PRESENT={str(proof['private_get_evidence_present']).lower()};"
        f"CREDENTIAL_AVAILABLE={str(proof['credential_presence'].get('available')).lower()};"
        f"LIVE_AUTHORIZED={str(LIVE_AUTHORIZED).lower()};"
        f"LIVE_EXECUTION_CODE_EXISTS_DOES_NOT_IMPLY_PATH_REACHABLE="
        f"{str(LIVE_EXECUTION_CODE_EXISTS_DOES_NOT_IMPLY_PATH_REACHABLE).lower()}."
    )
    return _record(
        payload={
            "canonical_definition": proof["canonical_definition"],
            "observed_repo_fact": observed,
            "admissibility_rule": proof["admissibility_predicate"],
            "evidence_paths": [
                SECTION_4_9_ANCHOR,
                CANONICAL_RUNBOOK_PATH,
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/constants_v1.py",
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/path_reachable_predicate_v1.py",
            ],
            "contradiction_check": (
                "NO_CONTRADICTION. Submit-authorization gates remain false and are "
                "not PATH_REACHABLE constituents. GET evidence does not promote "
                "LIVE_PRIVATE_READ_ONLY_PROVEN. "
                "CURRENTLY_REACHABLE_IS_NOT_LIVE_EXECUTION_PATH_REACHABLE="
                f"{str(CURRENTLY_REACHABLE_IS_NOT_LIVE_EXECUTION_PATH_REACHABLE).lower()}."
            ),
            "adjudicated_value": claim,
            "reason": proof["reason"],
            "constituent_values": proof["constituent_values"],
            "conjunction": proof["conjunction"],
            "credential_presence": proof["credential_presence"],
            "LIVE_PRIVATE_READ_ONLY_PROVEN": False,
        }
    )


def adjudicate_static_fields_v1(
    *,
    repo_root: Path,
    credential_presence: Mapping[str, Any] | None = None,
    private_get_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    code_exists = adjudicate_live_execution_code_exists_v1(repo_root=repo_root)
    path_reachable = adjudicate_live_execution_path_reachable_v1(
        repo_root=repo_root,
        credential_presence=credential_presence,
        private_get_evidence=private_get_evidence,
    )
    if (
        bool(path_reachable["adjudicated_value"]) is True
        and bool(code_exists["adjudicated_value"]) is not True
    ):
        raise RuntimeError("PATH_REACHABLE_WITHOUT_CODE_EXISTS")
    if bool(path_reachable["adjudicated_value"]) is True and private_get_evidence is None:
        raise RuntimeError("PATH_REACHABLE_TRUE_WITHOUT_FRESH_GET_EVIDENCE")
    return {
        "LIVE_EXECUTION_CODE_EXISTS": code_exists,
        "LIVE_EXECUTION_PATH_REACHABLE": path_reachable,
        "LIVE_EXECUTION_CODE_EXISTS_VALUE": bool(code_exists["adjudicated_value"]),
        "LIVE_EXECUTION_PATH_REACHABLE_VALUE": bool(path_reachable["adjudicated_value"]),
    }
