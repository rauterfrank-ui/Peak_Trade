"""D4/D5 genesis runtime orchestrator.

Captures one GENESIS_AS_OF, performs the authorized account-config GET,
and persists digest-stable D4 and D5 runtime instances. Does not reconstruct
the legacy chain. Does not POST. Does not execute observation S1-S5.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_contract_v1 import (
    PROVENANCE_GENESIS_FRESH_TYPED_BINDING,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    BoundAccountIdentityRuntimeBindingV1,
    persist_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_acquisition_contract_v1 import (
    FRESHNESS_EVIDENCE_STATUS,
    CheckpointObservationAcquisitionResultV1,
    acquire_checkpoint_observation_v1,
    bind_checkpoint_observation_to_checkpoint_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_window_binding_contract_v1 import (
    AS_OF_RELATION_GENESIS_EPOCH,
    BINDING_CLASS_GENESIS_EPOCH,
    WINDOW_DERIVATION_GENESIS_EPOCH,
    CheckpointObservationWindowBindingV1,
    bind_checkpoint_observation_window_v1,
    persist_checkpoint_observation_window_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    CONTINUE_OWNER_GO,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    D4D5GenesisRebaselineContractV1,
    build_d4_d5_genesis_rebaseline_contract_v1,
    persist_d4_d5_genesis_rebaseline_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_genesis_fresh_account_config_bootstrap_v1 import (
    D4GenesisFreshAccountConfigBootstrapError,
    execute_genesis_account_config_get_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_stock_checkpoint_contract_v1 import (
    build_equity_stock_checkpoint_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_s0_runtime_binding_gate_v1 import (
    assert_package_1_observation_s0_runtime_payloads_present_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryTransportV1,
)

SANITIZED_GET_FACTS_FILENAME = "d4_genesis_account_config_observed_facts_v1.json"
CLAIMS_FILENAME = "claims.json"


class D4D5GenesisRuntimeOrchestratorError(ValueError):
    """Fail-closed D4/D5 genesis runtime orchestration violation."""


@dataclass(frozen=True)
class D4D5GenesisRuntimeOrchestrationResultV1:
    genesis_id: str
    genesis_as_of: str
    account_config_get_performed: str
    additional_read_only_gets: str
    network_post_performed: str
    d4_bound_account_identity: str
    d4_bound_venue_identity: str
    d4_bound_td_mode: str
    d4_settlement_currency: str
    d4_runtime_instance_persisted: str
    d4_uid_corroborated: str
    d5_checkpoint_reference: str
    d5_observation_reference: str
    d5_window_start: str
    d5_window_end: str
    d5_runtime_instance_persisted: str
    historical_continuity_claimed: str
    historical_completeness_claimed: str
    pre_genesis_data_imported: str
    observation_s0_prerequisites_satisfied: str
    store_root: str
    genesis_contract: D4D5GenesisRebaselineContractV1
    d4_binding: BoundAccountIdentityRuntimeBindingV1
    d5_window: CheckpointObservationWindowBindingV1
    acquisition: CheckpointObservationAcquisitionResultV1


def capture_genesis_as_of_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def derive_genesis_id_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    genesis_as_of: str,
) -> str:
    material = f"{owner_go}|{origin_main_sha}|{genesis_as_of}"
    return "D4D5GENESIS" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def _canonical_json(payload: dict[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _persist_json(*, path: Path, payload: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def persist_manifest_sha256_v1(*, store_root: Path | str) -> Path:
    root = Path(store_root)
    lines: list[str] = []
    for path in sorted(p for p in root.iterdir() if p.is_file() and p.name != "MANIFEST.sha256"):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}")
    manifest = root / "MANIFEST.sha256"
    tmp = manifest.with_suffix(manifest.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp.replace(manifest)
    return manifest


def execute_d4_d5_genesis_runtime_orchestrator_v1(
    *,
    store_root: Path | str,
    owner_go: str = OWNER_GO,
    continue_owner_go: str = CONTINUE_OWNER_GO,
    origin_main_sha: str = EXPECTED_ORIGIN_MAIN_SHA,
    genesis_as_of: str | None = None,
    genesis_id: str | None = None,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> D4D5GenesisRuntimeOrchestrationResultV1:
    if continue_owner_go != CONTINUE_OWNER_GO:
        raise D4D5GenesisRuntimeOrchestratorError("CONTINUE_OWNER_GO_MISMATCH")
    as_of = genesis_as_of if genesis_as_of is not None else capture_genesis_as_of_v1()
    gid = (
        genesis_id
        if genesis_id is not None
        else derive_genesis_id_v1(
            owner_go=owner_go,
            origin_main_sha=origin_main_sha,
            genesis_as_of=as_of,
        )
    )
    try:
        contract = build_d4_d5_genesis_rebaseline_contract_v1(
            genesis_id=gid,
            genesis_as_of=as_of,
            owner_go=owner_go,
            bound_origin_main_sha=origin_main_sha,
            continue_owner_go=continue_owner_go,
        )
    except Exception as exc:
        raise D4D5GenesisRuntimeOrchestratorError(str(exc)) from exc
    persist_d4_d5_genesis_rebaseline_contract_v1(store_root=store_root, contract=contract)
    try:
        get_result = execute_genesis_account_config_get_v1(
            owner_go=owner_go,
            origin_main_sha=origin_main_sha,
            genesis_id=gid,
            genesis_as_of=as_of,
            vault_file=vault_file,
            transport=transport,
        )
    except D4GenesisFreshAccountConfigBootstrapError as exc:
        fail_code = str(exc)
        get_performed = (
            "true"
            if fail_code.startswith("D4_GENESIS_FIELD_FAIL_CLOSED:")
            or fail_code.startswith("ACCOUNT_CONFIG_")
            else "false"
        )
        _persist_json(
            path=Path(store_root) / CLAIMS_FILENAME,
            payload={
                "ACCOUNT_CONFIG_GET_PERFORMED": get_performed,
                "ADDITIONAL_READ_ONLY_GETS": "0",
                "D4_GENESIS_FIELD_FAIL_CLOSED": (
                    fail_code.split(":", 1)[1]
                    if fail_code.startswith("D4_GENESIS_FIELD_FAIL_CLOSED:")
                    else ""
                ),
                "D4_RUNTIME_INSTANCE_PRESENT": "false",
                "D5_RUNTIME_INSTANCE_PRESENT": "false",
                "GENESIS_AS_OF": as_of,
                "GENESIS_ID": gid,
                "HISTORICAL_COMPLETENESS_CLAIMED": "false",
                "HISTORICAL_CONTINUITY_CLAIMED": "false",
                "LEGACY_D4_D5_RUNTIME_CHAIN": "NOT_RECONSTRUCTED",
                "NETWORK_POST_PERFORMED": "false",
                "OBSERVATION_S0_PREREQUISITES_SATISFIED": "false",
                "POINT_WINDOW_DOES_NOT_ASSERT_ZERO_PRIOR_EVENTS": "true",
                "PRE_GENESIS_DATA_IMPORTED": "false",
            },
        )
        persist_manifest_sha256_v1(store_root=store_root)
        raise D4D5GenesisRuntimeOrchestratorError(str(exc)) from exc
    members = get_result["members"]
    observed = get_result["observed"]
    d4 = persist_bound_account_identity_runtime_binding_v1(
        store_root=store_root,
        identity_id=members.bound_account_identity,
        bound_account_identity=members.bound_account_identity,
        bound_venue_identity=members.bound_venue_identity,
        bound_td_mode=members.bound_td_mode,
        settlement_currency=members.settlement_currency,
        identity_provenance_class=PROVENANCE_GENESIS_FRESH_TYPED_BINDING,
        concrete_uid_corroborated="true",
    )
    schema_digest = contract.provenance_digest
    input_set_digest = _sha256_hex(f"{d4.identity_digest}|{as_of}|{gid}")
    checkpoint = build_equity_stock_checkpoint_contract_v1(
        checkpoint_id=f"CKPT{gid}",
        schema_digest=schema_digest,
        input_set_digest=input_set_digest,
        checkpoint_version="v1",
        bound_account_identity_ref=d4.identity_id,
        bound_account_identity_digest=d4.identity_digest,
    )
    acquisition = acquire_checkpoint_observation_v1(
        observation_id=f"OBS{gid}",
        source_observation_id=f"SRC{gid}",
        expected_bound_account_identity_ref=d4.identity_id,
        expected_bound_account_identity_digest=d4.identity_digest,
        bound_account_identity_ref=d4.identity_id,
        bound_account_identity_digest=d4.identity_digest,
        observed_at_as_of=as_of,
        acquired_at=as_of,
        component_completeness="COMPLETE",
        freshness_policy_status=FRESHNESS_EVIDENCE_STATUS,
    )
    checkpoint_binding = bind_checkpoint_observation_to_checkpoint_v1(
        binding_id=f"BIND{gid}",
        checkpoint=checkpoint,
        acquisition=acquisition,
    )
    window = bind_checkpoint_observation_window_v1(
        binding_id=f"WIN{gid}",
        checkpoint_id=checkpoint.checkpoint_id,
        acquisition=acquisition,
        checkpoint_binding=checkpoint_binding,
        checkpoint_window_start=as_of,
        checkpoint_window_end=as_of,
        binding_class=BINDING_CLASS_GENESIS_EPOCH,
        window_derivation_class=WINDOW_DERIVATION_GENESIS_EPOCH,
        observed_at_as_of_relation_class=AS_OF_RELATION_GENESIS_EPOCH,
        event_completeness_from_window="false",
    )
    persist_checkpoint_observation_window_binding_v1(store_root=store_root, binding=window)
    _persist_json(
        path=Path(store_root) / SANITIZED_GET_FACTS_FILENAME,
        payload={
            "http_status": str(get_result["http_status"]),
            "network_get_count": "1",
            "network_post_count": "0",
            "observed_uid": observed.observed_uid,
            "observed_td_mode": observed.observed_td_mode,
            "observed_settle_ccy": observed.observed_settle_ccy,
            "observed_field_names": ",".join(observed.observed_field_names),
            "d4_genesis_bootstrap_source": "FRESH_AUTHENTICATED_ACCOUNT_CONFIG",
            "bound_account_identity_source": members.bound_account_identity_source,
            "bound_venue_identity_source": members.bound_venue_identity_source,
            "bound_td_mode_source": members.bound_td_mode_source,
            "settlement_currency_source": members.settlement_currency_source,
        },
    )
    _persist_json(
        path=Path(store_root) / CLAIMS_FILENAME,
        payload={
            "D4_RUNTIME_INSTANCE_PRESENT": "true",
            "D5_RUNTIME_INSTANCE_PRESENT": "true",
            "HISTORICAL_CONTINUITY_CLAIMED": "false",
            "HISTORICAL_COMPLETENESS_CLAIMED": "false",
            "PRE_GENESIS_DATA_IMPORTED": "false",
            "NETWORK_POST_PERFORMED": "false",
            "ACCOUNT_CONFIG_GET_PERFORMED": "true",
            "ADDITIONAL_READ_ONLY_GETS": "0",
            "POINT_WINDOW_DOES_NOT_ASSERT_ZERO_PRIOR_EVENTS": "true",
            "LEGACY_D4_D5_RUNTIME_CHAIN": "NOT_RECONSTRUCTED",
        },
    )
    persist_manifest_sha256_v1(store_root=store_root)
    assert_package_1_observation_s0_runtime_payloads_present_v1(store_root=store_root)
    return D4D5GenesisRuntimeOrchestrationResultV1(
        genesis_id=gid,
        genesis_as_of=as_of,
        account_config_get_performed="true",
        additional_read_only_gets="0",
        network_post_performed="false",
        d4_bound_account_identity=d4.bound_account_identity,
        d4_bound_venue_identity=d4.bound_venue_identity,
        d4_bound_td_mode=d4.bound_td_mode,
        d4_settlement_currency=d4.settlement_currency,
        d4_runtime_instance_persisted="true",
        d4_uid_corroborated=d4.concrete_uid_corroborated,
        d5_checkpoint_reference=window.checkpoint_id,
        d5_observation_reference=window.checkpoint_observation_ref,
        d5_window_start=window.checkpoint_window_start,
        d5_window_end=window.checkpoint_window_end,
        d5_runtime_instance_persisted="true",
        historical_continuity_claimed="false",
        historical_completeness_claimed="false",
        pre_genesis_data_imported="false",
        observation_s0_prerequisites_satisfied="true",
        store_root=str(Path(store_root)),
        genesis_contract=contract,
        d4_binding=d4,
        d5_window=window,
        acquisition=acquisition,
    )
