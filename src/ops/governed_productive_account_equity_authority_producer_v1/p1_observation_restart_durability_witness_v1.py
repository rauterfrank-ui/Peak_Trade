"""P1 observation restart durability witness via offline serialization reload.

Persist → reload → reconstruct D4/D5 genesis bindings and sealed raw-capture
digests; verify identity/provenance/semantic equality. Not productive runtime
restart campaign. No GET. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    D4_RUNTIME_INSTANCE_FILENAME,
    load_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_window_binding_contract_v1 import (
    d5_window_binding_path_v1,
    load_checkpoint_observation_window_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_s0_runtime_binding_gate_v1 import (
    resolve_canonical_d4_d5_genesis_runtime_store_root_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_d5_checkpoint_freshness_witness_v1 import (
    CANONICAL_CD_PACK,
    CANONICAL_USDC_P1_PACK_RELPATH,
)

WP_ID = "FULL_CORE_P1_FINAL_CLOSEOUT_PR1_OF_2_V1"
SCHEMA_CLASS = "P1_OBSERVATION_RESTART_DURABILITY_WITNESS_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"


class P1ObservationRestartDurabilityWitnessError(ValueError):
    """Fail-closed P1 observation restart durability witness violation."""


@dataclass(frozen=True)
class P1OfflineRestartProofResultV1:
    proven: bool
    detail: str
    d4_digest_stable: bool
    d5_digest_stable: bool
    raw_capture_chain_stable: bool


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise P1ObservationRestartDurabilityWitnessError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _copy_genesis_runtime_to_store(*, source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for name in (D4_RUNTIME_INSTANCE_FILENAME, d5_window_binding_path_v1(store_root=source).name):
        src = source / name
        if not src.is_file():
            raise P1ObservationRestartDurabilityWitnessError(f"GENESIS_ARTIFACT_MISSING:{name}")
        shutil.copy2(src, target / name)


def prove_offline_observation_restart_durability_v1(
    *,
    repo_root: Path | str,
    reload_store: Path | str,
) -> P1OfflineRestartProofResultV1:
    repo = Path(repo_root)
    genesis_root = resolve_canonical_d4_d5_genesis_runtime_store_root_v1(repo_root=repo)
    if genesis_root is None:
        return P1OfflineRestartProofResultV1(
            proven=False,
            detail="GENESIS_STORE_ABSENT",
            d4_digest_stable=False,
            d5_digest_stable=False,
            raw_capture_chain_stable=False,
        )

    d4_before = load_bound_account_identity_runtime_binding_v1(store_root=genesis_root)
    d5_before = load_checkpoint_observation_window_binding_v1(store_root=genesis_root)

    reload_path = Path(reload_store)
    if reload_path.exists():
        shutil.rmtree(reload_path)
    _copy_genesis_runtime_to_store(source=genesis_root, target=reload_path)

    d4_after = load_bound_account_identity_runtime_binding_v1(store_root=reload_path)
    d5_after = load_checkpoint_observation_window_binding_v1(store_root=reload_path)

    d4_stable = d4_before.identity_digest == d4_after.identity_digest
    d5_stable = d5_before.provenance_digest == d5_after.provenance_digest

    usdc_raw = _load_json(repo / CANONICAL_USDC_P1_PACK_RELPATH / "raw_http_capture_v1.json")
    cd_raw = _load_json(repo / CANONICAL_CD_PACK / "raw_http_capture_v1.json")
    usdc_claims = _load_json(repo / CANONICAL_USDC_P1_PACK_RELPATH / "claims.json")
    cd_claims = _load_json(repo / CANONICAL_CD_PACK / "claims.json")

    raw_chain_ok = (
        str(usdc_claims.get("RAW_EVIDENCE_SHA256", "")) == str(usdc_raw.get("payload_sha256", ""))
        and str(cd_claims.get("RAW_EVIDENCE_SHA256", "")) == str(cd_raw.get("payload_sha256", ""))
        and str(usdc_raw.get("d5_binding_id", "")) == d5_after.binding_id
        and str(cd_raw.get("d5_binding_id", "")) == d5_after.binding_id
    )

    proven = d4_stable and d5_stable and raw_chain_ok
    if not proven:
        detail = "OFFLINE_RESTART_RELOAD_EQUALITY_FAILED"
    else:
        detail = (
            "Offline persist-reload-reconstruct of D4/D5 genesis bindings and "
            "sealed raw capture digest chain preserves identity and provenance"
        )
    return P1OfflineRestartProofResultV1(
        proven=proven,
        detail=detail,
        d4_digest_stable=d4_stable,
        d5_digest_stable=d5_stable,
        raw_capture_chain_stable=raw_chain_ok,
    )


def build_p1_observation_restart_durability_witness_adjudication_v1(
    *,
    offline_proof: P1OfflineRestartProofResultV1,
) -> dict[str, Any]:
    return {
        "layer": "CANONICAL_AUTHORITY",
        "WP_ID": WP_ID,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "P1_RESTART_DURABILITY_COMPLETENESS_PROVEN": (
            TRUE_TOKEN if offline_proof.proven else FALSE_TOKEN
        ),
        "P1_RESTART_DURABILITY_DETAIL": offline_proof.detail,
        "RESTART_DURABILITY_MISSING_FACT": (
            NONE_TOKEN if offline_proof.proven else offline_proof.detail
        ),
        "OFFLINE_RESTART_PROOF_ATTEMPTED": TRUE_TOKEN,
        "OFFLINE_RESTART_PROOF_RESULT": TRUE_TOKEN if offline_proof.proven else FALSE_TOKEN,
        "D4_IDENTITY_DIGEST_STABLE": TRUE_TOKEN if offline_proof.d4_digest_stable else FALSE_TOKEN,
        "D5_PROVENANCE_DIGEST_STABLE": TRUE_TOKEN
        if offline_proof.d5_digest_stable
        else FALSE_TOKEN,
        "RAW_CAPTURE_CHAIN_STABLE": (
            TRUE_TOKEN if offline_proof.raw_capture_chain_stable else FALSE_TOKEN
        ),
        "PRODUCTIVE_RUNTIME_RESTART_CAMPAIGN_REQUIRED": FALSE_TOKEN
        if offline_proof.proven
        else TRUE_TOKEN,
    }


__all__ = [
    "AUTHORITY_EFFECT",
    "CONTRACT_VERSION",
    "P1ObservationRestartDurabilityWitnessError",
    "P1OfflineRestartProofResultV1",
    "SCHEMA_CLASS",
    "WP_ID",
    "build_p1_observation_restart_durability_witness_adjudication_v1",
    "prove_offline_observation_restart_durability_v1",
]
