"""Offline adjudication of LIVE_EXECUTION_CODE_EXISTS and PATH_REACHABLE."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_SUBMIT_TRANSPORT_PATH,
    CANONICAL_RUNBOOK_PATH,
    CANONICAL_SECTION_HEADING,
    CODE_PRESENCE_IS_NOT_LIVE_EXECUTION_CODE_EXISTS,
    CURRENTLY_REACHABLE_IS_NOT_LIVE_EXECUTION_PATH_REACHABLE,
    FLATTEN_EXECUTE_PATH,
    LIVE_EXECUTION_CODE_EXISTS,
    LIVE_EXECUTION_PATH_REACHABLE,
    SECTION_4_9_ANCHOR,
    SP01_PATH,
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


def _path_exists(repo_root: Path, rel: str) -> bool:
    return (repo_root / rel).is_file()


def adjudicate_live_execution_code_exists_v1(*, repo_root: Path) -> dict[str, Any]:
    sp01_exists = _path_exists(repo_root, SP01_PATH)
    flatten_exists = _path_exists(repo_root, FLATTEN_EXECUTE_PATH)
    transport_exists = _path_exists(repo_root, CANARY_SUBMIT_TRANSPORT_PATH)
    observed = (
        f"SP01_FILE_EXISTS={str(sp01_exists).lower()};"
        f"FLATTEN_EXECUTE_FILE_EXISTS={str(flatten_exists).lower()};"
        f"SUBMIT_TRANSPORT_FILE_EXISTS={str(transport_exists).lower()}"
    )
    return _record(
        payload={
            "canonical_definition": (
                f"{CANONICAL_RUNBOOK_PATH} {CANONICAL_SECTION_HEADING} "
                "lists LIVE_EXECUTION_CODE_EXISTS as the first Live proof-claim "
                "field. The runbook does not define a proof criterion beyond the "
                "field name. Cap 11.7-11.11 keep the same field false as a "
                "contracts-only overclaim guard."
            ),
            "observed_repo_fact": observed,
            "admissibility_rule": (
                "This GO forbids binding the field true merely because code is "
                "present. Unresolved semantic mapping fails closed. Repository "
                "file presence is supporting context, not the Live proof claim."
            ),
            "evidence_paths": [
                SP01_PATH,
                FLATTEN_EXECUTE_PATH,
                CANARY_SUBMIT_TRANSPORT_PATH,
                SECTION_4_9_ANCHOR,
                CANONICAL_RUNBOOK_PATH,
            ],
            "contradiction_check": (
                "NO_CONTRADICTION. Files exist and Cap/Section contracts still "
                "refuse the Live proof claim. CODE_PRESENCE_IS_NOT_LIVE_EXECUTION_"
                f"CODE_EXISTS={str(CODE_PRESENCE_IS_NOT_LIVE_EXECUTION_CODE_EXISTS).lower()}."
            ),
            "adjudicated_value": LIVE_EXECUTION_CODE_EXISTS,
            "reason": (
                "FAIL_CLOSED_UNRESOLVED_SEMANTIC_MAPPING;"
                "CODE_PRESENCE_ALONE_INADMISSIBLE;"
                "LIVE_EXECUTION_CODE_EXISTS=false"
            ),
        }
    )


def adjudicate_live_execution_path_reachable_v1(*, repo_root: Path) -> dict[str, Any]:
    del repo_root
    return _record(
        payload={
            "canonical_definition": (
                f"{CANONICAL_RUNBOOK_PATH} {CANONICAL_SECTION_HEADING} lists "
                "LIVE_EXECUTION_PATH_REACHABLE as the second Live proof-claim "
                "field. The runbook does not equate it with §4.9 "
                "CURRENTLY_REACHABLE."
            ),
            "observed_repo_fact": (
                "§4.9 SP-01 CURRENTLY_REACHABLE=true means the Python surface is "
                "constructible. CAN_SUBMIT_ORDER_TODAY=false. Standing gates "
                "LIVE_ENABLED=false LIVE_ARMED=false SUBMIT_UNLOCKED=false "
                "LIVE_AUTHORIZED=false. Credential, venue, and runtime permit "
                "state are NOT_OBSERVED in this offline GO."
            ),
            "admissibility_rule": (
                "Reachable as a §11.14 Live proof claim cannot be proven if it "
                "entails a runtime gate, authorization state, credential state, "
                "venue condition, or any other fact not provable offline. "
                "CURRENTLY_REACHABLE is not proven semantically identical."
            ),
            "evidence_paths": [
                SECTION_4_9_ANCHOR,
                CANONICAL_RUNBOOK_PATH,
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/constants_v1.py",
            ],
            "contradiction_check": (
                "NO_CONTRADICTION. Constructible code plus fail-closed gates is "
                "exactly the distinction this field must preserve. "
                "CURRENTLY_REACHABLE_IS_NOT_LIVE_EXECUTION_PATH_REACHABLE="
                f"{str(CURRENTLY_REACHABLE_IS_NOT_LIVE_EXECUTION_PATH_REACHABLE).lower()}."
            ),
            "adjudicated_value": LIVE_EXECUTION_PATH_REACHABLE,
            "reason": (
                "FAIL_CLOSED_RUNTIME_GATES_AUTHORIZATION_CREDENTIALS_VENUE_UNOBSERVED;"
                "NOT_EQUATED_WITH_SECTION_4_9_CURRENTLY_REACHABLE;"
                "LIVE_EXECUTION_PATH_REACHABLE=false"
            ),
        }
    )


def adjudicate_static_fields_v1(*, repo_root: Path) -> dict[str, Any]:
    code_exists = adjudicate_live_execution_code_exists_v1(repo_root=repo_root)
    path_reachable = adjudicate_live_execution_path_reachable_v1(repo_root=repo_root)
    return {
        "LIVE_EXECUTION_CODE_EXISTS": code_exists,
        "LIVE_EXECUTION_PATH_REACHABLE": path_reachable,
        "LIVE_EXECUTION_CODE_EXISTS_VALUE": bool(code_exists["adjudicated_value"]),
        "LIVE_EXECUTION_PATH_REACHABLE_VALUE": bool(path_reachable["adjudicated_value"]),
    }
