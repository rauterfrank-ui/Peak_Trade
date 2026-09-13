"""D4/D5 genesis rebaseline authority contract.

Owner-selected new reconstruction epoch. Does not reconstruct the
legacy D4/D5 runtime chain. Does not claim historical continuity.
Does not mint identity from env, credential, default, or history.
AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    D4_D5_GENESIS_REBASELINE_CONTRACT_PRESENT,
    D4_GENESIS_ACCOUNT_CONFIG_GET_AUTHORIZED,
    D4_GENESIS_BOOTSTRAP_SOURCE,
    D4_POST_GENESIS_OBSERVATION_MUST_NOT_MINT_IDENTITY,
    GENESIS_REBASELINE_SELECTED_BY_OWNER,
    HISTORICAL_COMPLETENESS_CLAIMED,
    HISTORICAL_CONTINUITY_CLAIMED,
    LEGACY_D4_D5_RUNTIME_CHAIN_RECONSTRUCTED,
    NEW_CANONICAL_RUNTIME_CHAIN_STARTS_AT_GENESIS_AS_OF,
    POINT_WINDOW_DOES_NOT_ASSERT_ZERO_PRIOR_EVENTS,
    PRE_GENESIS_DATA_IMPORTED,
)

SCHEMA_CLASS = "D4_D5_GENESIS_REBASELINE_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
OWNER_GO = "OWNER_GO_D6_PATH_B_D4_D5_GENESIS_REBASELINE_V1"
CONTINUE_OWNER_GO = "OWNER_GO_D6_PATH_B_D4_D5_GENESIS_REBASELINE_CONTINUE_V1"
TD_MODE_RESOLUTION_OWNER_GO = "OWNER_GO_PR_6448_BOUND_TD_MODE_FRESH_POSITION_RESOLUTION_V1"
EXPECTED_ORIGIN_MAIN_SHA = "cf3aede3c115fc0b77253482af861f73614db877"
EXPECTED_GENESIS_ID = "D4D5GENESIS8d3f573ffc0c59b4"
EXPECTED_GENESIS_AS_OF = "2026-09-13T17:03:18Z"
GENESIS_EPOCH_SEMANTIC_CLASS = "NEW_CANONICAL_RECONSTRUCTION_EPOCH_STARTS_HERE"
PRIOR_PERIODS_SCOPE = "OUT_OF_SCOPE_FOR_NEW_CHAIN"
PRE_GENESIS_PERIOD = "OUT_OF_SCOPE_FOR_NEW_RUNTIME_CHAIN"
GENESIS_CONTRACT_FILENAME = "d4_d5_genesis_rebaseline_contract_v1.json"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
_ISO_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


class D4D5GenesisRebaselineContractError(ValueError):
    """Fail-closed D4/D5 genesis rebaseline contract violation."""


@dataclass(frozen=True)
class D4D5GenesisRebaselineContractV1:
    genesis_id: str
    genesis_as_of: str
    owner_go: str
    bound_origin_main_sha: str
    genesis_rebaseline_selected_by_owner: str
    legacy_d4_d5_runtime_chain: str
    historical_continuity_claimed: str
    genesis_epoch_semantic_class: str
    prior_periods_scope: str
    pre_genesis_period: str
    point_window_does_not_assert_zero_prior_events: str
    historical_completeness_claimed: str
    new_canonical_runtime_chain_starts_at_genesis_as_of: str
    pre_genesis_data_imported: str
    d4_genesis_bootstrap_source: str
    post_genesis_observation_must_not_mint_identity: str
    continue_owner_go: str
    authority_owner: str
    authority_effect: str
    provenance_digest: str


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_genesis_rebaseline_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise D4D5GenesisRebaselineContractError(f"GENESIS_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise D4D5GenesisRebaselineContractError(f"GENESIS_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise D4D5GenesisRebaselineContractError(f"GENESIS_FIELD_MISSING:{field}")
    return text


def _require_iso_z(*, field: str, raw: Any) -> str:
    text = _require_non_empty_str(field=field, raw=raw)
    if _ISO_Z.fullmatch(text) is None:
        raise D4D5GenesisRebaselineContractError(f"GENESIS_TIMESTAMP_NOT_ISO_Z:{field}")
    return text


def build_d4_d5_genesis_rebaseline_contract_v1(
    *,
    genesis_id: str,
    genesis_as_of: str,
    owner_go: str,
    bound_origin_main_sha: str,
    continue_owner_go: str = CONTINUE_OWNER_GO,
) -> D4D5GenesisRebaselineContractV1:
    if D4_D5_GENESIS_REBASELINE_CONTRACT_PRESENT is not True:
        raise D4D5GenesisRebaselineContractError("GENESIS_REBASELINE_CONTRACT_NOT_PRESENT")
    if GENESIS_REBASELINE_SELECTED_BY_OWNER is not True:
        raise D4D5GenesisRebaselineContractError("GENESIS_REBASELINE_NOT_OWNER_SELECTED")
    if LEGACY_D4_D5_RUNTIME_CHAIN_RECONSTRUCTED is not False:
        raise D4D5GenesisRebaselineContractError("LEGACY_D4_D5_RUNTIME_CHAIN_MUST_NOT_RECONSTRUCT")
    if HISTORICAL_CONTINUITY_CLAIMED is not False:
        raise D4D5GenesisRebaselineContractError("HISTORICAL_CONTINUITY_MUST_REMAIN_UNCLAIMED")
    if D4_GENESIS_BOOTSTRAP_SOURCE != "FRESH_AUTHENTICATED_ACCOUNT_CONFIG":
        raise D4D5GenesisRebaselineContractError("D4_GENESIS_BOOTSTRAP_SOURCE_DRIFT")
    if D4_GENESIS_ACCOUNT_CONFIG_GET_AUTHORIZED is not True:
        raise D4D5GenesisRebaselineContractError("D4_GENESIS_ACCOUNT_CONFIG_GET_NOT_AUTHORIZED")
    if D4_POST_GENESIS_OBSERVATION_MUST_NOT_MINT_IDENTITY is not True:
        raise D4D5GenesisRebaselineContractError(
            "D4_POST_GENESIS_OBSERVATION_MUST_NOT_MINT_IDENTITY"
        )
    if POINT_WINDOW_DOES_NOT_ASSERT_ZERO_PRIOR_EVENTS is not True:
        raise D4D5GenesisRebaselineContractError("POINT_WINDOW_MUST_NOT_ASSERT_ZERO_PRIOR_EVENTS")
    if HISTORICAL_COMPLETENESS_CLAIMED is not False:
        raise D4D5GenesisRebaselineContractError("HISTORICAL_COMPLETENESS_MUST_REMAIN_UNCLAIMED")
    if NEW_CANONICAL_RUNTIME_CHAIN_STARTS_AT_GENESIS_AS_OF is not True:
        raise D4D5GenesisRebaselineContractError(
            "NEW_CANONICAL_RUNTIME_CHAIN_MUST_START_AT_GENESIS_AS_OF"
        )
    if PRE_GENESIS_DATA_IMPORTED is not False:
        raise D4D5GenesisRebaselineContractError("PRE_GENESIS_DATA_MUST_NOT_BE_IMPORTED")
    owned = _require_non_empty_str(field="owner_go", raw=owner_go)
    if owned != OWNER_GO:
        raise D4D5GenesisRebaselineContractError("OWNER_GO_MISMATCH")
    sha = _require_non_empty_str(field="bound_origin_main_sha", raw=bound_origin_main_sha)
    if sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise D4D5GenesisRebaselineContractError("ORIGIN_MAIN_SHA_MISMATCH")
    if ACCOUNT_EQUITY_AUTHORITY_OWNER != (
        "ops.governed_productive_account_equity_authority_producer_v1"
    ):
        raise D4D5GenesisRebaselineContractError("GENESIS_AUTHORITY_OWNER_MUTATED")
    continued = _require_non_empty_str(field="continue_owner_go", raw=continue_owner_go)
    if continued != CONTINUE_OWNER_GO:
        raise D4D5GenesisRebaselineContractError("CONTINUE_OWNER_GO_MISMATCH")
    genesis = _require_non_empty_str(field="genesis_id", raw=genesis_id)
    as_of = _require_iso_z(field="genesis_as_of", raw=genesis_as_of)
    payload = {
        "genesis_id": genesis,
        "genesis_as_of": as_of,
        "owner_go": owned,
        "bound_origin_main_sha": sha,
        "genesis_rebaseline_selected_by_owner": TRUE_TOKEN,
        "legacy_d4_d5_runtime_chain": "NOT_RECONSTRUCTED",
        "historical_continuity_claimed": FALSE_TOKEN,
        "genesis_epoch_semantic_class": GENESIS_EPOCH_SEMANTIC_CLASS,
        "prior_periods_scope": PRIOR_PERIODS_SCOPE,
        "pre_genesis_period": PRE_GENESIS_PERIOD,
        "point_window_does_not_assert_zero_prior_events": TRUE_TOKEN,
        "historical_completeness_claimed": FALSE_TOKEN,
        "new_canonical_runtime_chain_starts_at_genesis_as_of": TRUE_TOKEN,
        "pre_genesis_data_imported": FALSE_TOKEN,
        "d4_genesis_bootstrap_source": D4_GENESIS_BOOTSTRAP_SOURCE,
        "post_genesis_observation_must_not_mint_identity": TRUE_TOKEN,
        "continue_owner_go": continued,
        "authority_owner": ACCOUNT_EQUITY_AUTHORITY_OWNER,
        "authority_effect": AUTHORITY_EFFECT,
    }
    digest = compute_genesis_rebaseline_digest_v1(payload)
    return D4D5GenesisRebaselineContractV1(**payload, provenance_digest=digest)


def genesis_contract_path_v1(*, store_root: Path | str) -> Path:
    return Path(store_root) / GENESIS_CONTRACT_FILENAME


def load_d4_d5_genesis_rebaseline_contract_v1(
    *,
    store_root: Path | str,
) -> D4D5GenesisRebaselineContractV1:
    path = genesis_contract_path_v1(store_root=store_root)
    if not path.is_file():
        raise D4D5GenesisRebaselineContractError("GENESIS_CONTRACT_ARTIFACT_ABSENT")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise D4D5GenesisRebaselineContractError("GENESIS_CONTRACT_NOT_JSON") from exc
    if not isinstance(payload, dict):
        raise D4D5GenesisRebaselineContractError("GENESIS_CONTRACT_NOT_OBJECT")
    contract = build_d4_d5_genesis_rebaseline_contract_v1(
        genesis_id=str(payload.get("genesis_id") or ""),
        genesis_as_of=str(payload.get("genesis_as_of") or ""),
        owner_go=str(payload.get("owner_go") or ""),
        bound_origin_main_sha=str(payload.get("bound_origin_main_sha") or ""),
        continue_owner_go=str(payload.get("continue_owner_go") or ""),
    )
    persisted_digest = str(payload.get("provenance_digest") or "").strip()
    if persisted_digest != contract.provenance_digest:
        raise D4D5GenesisRebaselineContractError("GENESIS_CONTRACT_DIGEST_MISMATCH")
    if contract.genesis_id != EXPECTED_GENESIS_ID:
        raise D4D5GenesisRebaselineContractError("GENESIS_ID_MUST_REMAIN_BOUND")
    if contract.genesis_as_of != EXPECTED_GENESIS_AS_OF:
        raise D4D5GenesisRebaselineContractError("GENESIS_AS_OF_MUST_REMAIN_BOUND")
    return contract


def persist_d4_d5_genesis_rebaseline_contract_v1(
    *,
    store_root: Path | str,
    contract: D4D5GenesisRebaselineContractV1,
) -> D4D5GenesisRebaselineContractV1:
    path = genesis_contract_path_v1(store_root=store_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "genesis_id": contract.genesis_id,
        "genesis_as_of": contract.genesis_as_of,
        "owner_go": contract.owner_go,
        "bound_origin_main_sha": contract.bound_origin_main_sha,
        "genesis_rebaseline_selected_by_owner": contract.genesis_rebaseline_selected_by_owner,
        "legacy_d4_d5_runtime_chain": contract.legacy_d4_d5_runtime_chain,
        "historical_continuity_claimed": contract.historical_continuity_claimed,
        "genesis_epoch_semantic_class": contract.genesis_epoch_semantic_class,
        "prior_periods_scope": contract.prior_periods_scope,
        "pre_genesis_period": contract.pre_genesis_period,
        "point_window_does_not_assert_zero_prior_events": (
            contract.point_window_does_not_assert_zero_prior_events
        ),
        "historical_completeness_claimed": contract.historical_completeness_claimed,
        "new_canonical_runtime_chain_starts_at_genesis_as_of": (
            contract.new_canonical_runtime_chain_starts_at_genesis_as_of
        ),
        "pre_genesis_data_imported": contract.pre_genesis_data_imported,
        "d4_genesis_bootstrap_source": contract.d4_genesis_bootstrap_source,
        "post_genesis_observation_must_not_mint_identity": (
            contract.post_genesis_observation_must_not_mint_identity
        ),
        "continue_owner_go": contract.continue_owner_go,
        "authority_owner": contract.authority_owner,
        "authority_effect": contract.authority_effect,
        "provenance_digest": contract.provenance_digest,
    }
    encoded = _canonical_json(payload) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(encoded, encoding="utf-8")
    tmp.replace(path)
    return contract
