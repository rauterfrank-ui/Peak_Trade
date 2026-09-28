"""Post-6944 scoped K1 opaque signing handle PRE-POST perform (no venue POST)."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

WORKPACKAGE_ID: Final[str] = "POST_6944_K1_OPAQUE_SIGNING_HANDLE_PRE_POST_SCOPED_PERFORM_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/AUTHORITY_MAP_ATLAS_GUIDED_K1_OPAQUE_SIGNING_HANDLE_PRE_POST_SCOPED_PERFORM_FROM_POST_6944_MAIN_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/post_6944_k1_opaque_signing_handle_pre_post_scoped_perform_v1_decision_v1.json"
)
OWNER_GO_DECISION_CONFIG: Final[str] = (
    "config/governance/current_productive_k1_opaque_signing_handle_pre_post_owner_go_v1_decision.json"
)
OWNER_GO_TOKEN: Final[str] = (
    "OWNER_GO_CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1"
)
MAP_SOURCE_REL: Final[str] = (
    "config/governance/current_system_interaction_authority_map_v1/source_v1.json"
)
ATLAS_CENSUS_REL: Final[str] = "docs/system_atlas/census/census_meta.yaml"
VENUE_POST_NEXT_OWNER_GO: Final[str] = (
    "OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1"
)
CANONICAL_K1_AUTHORITY: Final[str] = (
    "governance.current_productive_k1_opaque_signing_handle_pre_post_policy_v1"
)
K1_HANDLE_CLASS: Final[str] = "FullCoreK1BoundVenueAuthHandleV1"


@dataclass(frozen=True)
class K1PrePostPreconditionProbeV1:
    ok: bool
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"OK": self.ok, "REASON_CODES": list(self.reason_codes)}


def load_json_v1(repo_root: Path, rel: str) -> dict[str, Any]:
    return json.loads((repo_root / rel).read_text(encoding="utf-8"))


def validate_scoped_owner_go_v1(
    *,
    repo_root: Path,
    owner_go_token: str | None,
) -> K1PrePostPreconditionProbeV1:
    reasons: list[str] = []
    token = str(owner_go_token or "").strip()
    if token != OWNER_GO_TOKEN:
        reasons.append("SCOPED_OWNER_GO_TOKEN_MISMATCH_OR_MISSING")
    owner = load_json_v1(repo_root, OWNER_GO_DECISION_CONFIG)
    if owner.get("owner_go") is not True:
        reasons.append("OWNER_GO_DECISION_NOT_TRUE")
    if str(owner.get("owner_go_token") or "") != OWNER_GO_TOKEN:
        reasons.append("OWNER_GO_DECISION_TOKEN_DRIFT")
    if owner.get("current_productive_k1_opaque_signing_handle_pre_post_owner_go") is not True:
        reasons.append("K1_PRE_POST_OWNER_GO_NOT_AUTHORIZED_IN_DECISION")
    return K1PrePostPreconditionProbeV1(ok=not reasons, reason_codes=tuple(reasons))


def build_pre_post_proof_envelope_v1():
    """Non-live envelope for PRE-POST signing proof only (no venue POST)."""

    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        bind_final_order_envelope_from_venue_plan_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1

    plan = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:BTC:USDT:USDT:btc-usdt-swap",
        side="buy",
        quantity="1",
        order_type="market",
        td_mode="cross",
        reduce_only=False,
        clordid="k1-pre-post-perform-proof-clord",
        venue_native_payload={
            "instId": "BTC-USDT-SWAP",
            "ordType": "market",
            "side": "buy",
            "sz": "1",
            "tdMode": "cross",
        },
        quantity_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        side_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        instrument_source="TEST_FIXTURE",
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
    )
    return bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="K1_PRE_POST_PERFORM_PROOF_ADMISSION_REF",
        provenance_ref="POST_6944_K1_PRE_POST_SCOPED_PERFORM_V1",
        creation_epoch="2026-09-28T00:00:00Z",
    )


def probe_k1_pre_post_preconditions_v1(*, repo_root: Path) -> dict[str, Any]:
    from src.governance.current_productive_k1_opaque_signing_handle_pre_post_policy_v1 import (
        evaluate_k1_opaque_signing_handle_pre_post_admission_v1,
        prove_k1_pre_post_does_not_authorize_post_v1,
        prove_k1_pre_post_does_not_flip_standing_keychain_pins_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
        EXTERNAL_EFFECT_AUTHORIZED,
        POST_ALLOWED,
        REAL_VENUE_POST_ALLOWED,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
        AUTONOMY_CAN_MINT_PERMIT,
        AUTONOMY_CAN_POST,
    )

    admission = evaluate_k1_opaque_signing_handle_pre_post_admission_v1(repo_root=repo_root)
    reasons: list[str] = []
    if admission.k1_pre_post_policy_granted is not True:
        reasons.extend(list(admission.reason_codes) or ["K1_PRE_POST_ADMISSION_DENIED"])
    if not prove_k1_pre_post_does_not_flip_standing_keychain_pins_v1():
        reasons.append("STANDING_KEYCHAIN_PIN_DRIFT")
    if not prove_k1_pre_post_does_not_authorize_post_v1():
        reasons.append("POST_AUTHORITY_MUST_REMAIN_FALSE")
    if (
        EXTERNAL_EFFECT_AUTHORIZED is True
        or POST_ALLOWED is True
        or REAL_VENUE_POST_ALLOWED is True
    ):
        reasons.append("STANDING_EXTERNAL_EFFECT_OR_POST_PINS_TRUE")
    if AUTONOMY_CAN_MINT_PERMIT is True or AUTONOMY_CAN_POST is True:
        reasons.append("AUTONOMY_CAN_MINT_OR_POST_TRUE")
    return {
        "K1_PRE_POST_ADMISSION": {
            "granted": admission.k1_pre_post_policy_granted,
            "status": admission.admission_status,
            "reason_codes": list(admission.reason_codes),
            "request_signing_authorized": admission.request_signing_authorized,
            "real_keychain_access_authorized": admission.real_keychain_access_authorized,
        },
        "STANDING_PINS_OK": not any(
            r.startswith("STANDING_") or r.startswith("AUTONOMY_") for r in reasons
        ),
        "PRECONDITION_PROBE": K1PrePostPreconditionProbeV1(
            ok=not reasons,
            reason_codes=tuple(dict.fromkeys(reasons)),
        ).to_dict(),
    }


def perform_scoped_k1_pre_post_boundary_v1(
    *,
    repo_root: Path,
    owner_go_token: str,
    use_productive_macos_backend: bool,
    backend: Any | None = None,
) -> dict[str, Any]:
    from src.governance.current_productive_k1_pre_post_productive_chain_v1 import (
        STATUS_CHAIN_STOPPED_POST_ADMISSION,
        attempt_governed_current_productive_k1_pre_post_productive_chain_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
        EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_K1_OPAQUE_SIGNING_HANDLE_PRE_POST,
        KEYCHAIN_ACCOUNT_ID,
        KEYCHAIN_ITEM_CLASS,
        KEYCHAIN_SERVICE_ID,
        MacosSecurityFrameworkLookupBackendV1,
        REAL_KEYCHAIN_ACCESS_AUTHORIZED,
        REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
    )

    owner_probe = validate_scoped_owner_go_v1(repo_root=repo_root, owner_go_token=owner_go_token)
    pre = probe_k1_pre_post_preconditions_v1(repo_root=repo_root)
    if not owner_probe.ok or not pre["PRECONDITION_PROBE"]["OK"]:
        return {
            "PERFORM_ATTEMPTED": False,
            "OWNER_GO_PROBE": owner_probe.to_dict(),
            "PRECONDITIONS": pre,
            "CHAIN": None,
            "FAIL_CLOSED": True,
        }

    chosen_backend = backend
    if use_productive_macos_backend:
        if sys.platform != "darwin":
            return {
                "PERFORM_ATTEMPTED": False,
                "OWNER_GO_PROBE": owner_probe.to_dict(),
                "PRECONDITIONS": pre,
                "CHAIN": {
                    "chain_status": "DENIED",
                    "reason_codes": ["NON_DARWIN_PRODUCTIVE_BACKEND_FORBIDDEN"],
                },
                "FAIL_CLOSED": True,
            }
        chosen_backend = MacosSecurityFrameworkLookupBackendV1()

    if chosen_backend is None:
        return {
            "PERFORM_ATTEMPTED": False,
            "OWNER_GO_PROBE": owner_probe.to_dict(),
            "PRECONDITIONS": pre,
            "CHAIN": {
                "chain_status": "DENIED",
                "reason_codes": ["LOOKUP_BACKEND_REQUIRED"],
            },
            "FAIL_CLOSED": True,
        }

    envelope = build_pre_post_proof_envelope_v1()
    chain = attempt_governed_current_productive_k1_pre_post_productive_chain_v1(
        repo_root=repo_root,
        owner_go=owner_go_token,
        envelope=envelope,
        k1_backend=chosen_backend,
        post_owner_go=None,
        one_shot_real_post=False,
    )
    public_chain = chain.to_public_dict_v1()
    handle_bindings = {
        "keychain_service_id": KEYCHAIN_SERVICE_ID,
        "keychain_account_id": KEYCHAIN_ACCOUNT_ID,
        "keychain_item_class": KEYCHAIN_ITEM_CLASS,
        "ephemeral_keychain_consumer": EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_K1_OPAQUE_SIGNING_HANDLE_PRE_POST,
        "envelope_id": envelope.envelope_id,
        "permit_id_public": chain.permit_id or "",
        "pre_post_digest": chain.pre_post_digest or "",
    }
    fixpoint_chain = chain.chain_status == STATUS_CHAIN_STOPPED_POST_ADMISSION
    return {
        "PERFORM_ATTEMPTED": True,
        "OWNER_GO_PROBE": owner_probe.to_dict(),
        "PRECONDITIONS": pre,
        "CHAIN": public_chain,
        "K1_HANDLE_CREATED": chain.opaque_signing_handle_constructed is True,
        "FRESH_MATERIAL_LOAD_REQUIRED": True,
        "FRESH_MATERIAL_LOAD_PERFORMED": chain.real_credential_access_performed is True,
        "SIGNING_WITHIN_K1_AUTHORITY": True,
        "SIGNING_PERFORMED": chain.request_signing_performed is True,
        "SECRET_DISCLOSED": chain.secret_disclosed is True,
        "SECRET_PERSISTED": chain.secret_persisted is True,
        "IN_MEMORY_PERMIT_FOR_PRE_POST_BINDING": chain.permit_mint_performed is True,
        "K1_HANDLE_BINDINGS": handle_bindings,
        "STANDING_REAL_KEYCHAIN_ACCESS_AUTHORIZED_AFTER": REAL_KEYCHAIN_ACCESS_AUTHORIZED is True,
        "STANDING_REAL_KEYCHAIN_ACCESS_IMPLEMENTED_AFTER": REAL_KEYCHAIN_ACCESS_IMPLEMENTED is True,
        "POST_ADMISSION_GRANTED": chain.post_admission.post_admission_granted is True,
        "FAIL_CLOSED": not fixpoint_chain,
    }


def build_k1_pre_post_perform_report_v1(
    *,
    repo_root: Path,
    baseline_sha: str,
    owner_go_token: str,
    perform_payload: Mapping[str, Any],
    chain_6942_report: Mapping[str, Any] | None,
    material_load_6943_report: Mapping[str, Any] | None,
    map_sha256: str,
    atlas_sha256: str,
    e2e_run_id: str,
    evidence_root: str,
) -> dict[str, Any]:
    chain = perform_payload.get("CHAIN") or {}
    handle_created = bool(perform_payload.get("K1_HANDLE_CREATED"))
    signing = bool(perform_payload.get("SIGNING_PERFORMED"))
    secret_exposed = bool(perform_payload.get("SECRET_DISCLOSED")) or bool(
        perform_payload.get("SECRET_PERSISTED")
    )
    pre_external = bool((chain_6942_report or {}).get("PRE_EXTERNAL_EFFECT_REACHED"))
    post_admission_granted = bool(perform_payload.get("POST_ADMISSION_GRANTED"))
    fixpoint = (
        handle_created
        and signing
        and not secret_exposed
        and not post_admission_granted
        and perform_payload.get("STANDING_REAL_KEYCHAIN_ACCESS_AUTHORIZED_AFTER") is False
        and chain.get("chain_status") == "K1_PRE_POST_CHAIN_STOPPED_AT_REAL_VENUE_POST_ADMISSION"
    )
    first_blocker = VENUE_POST_NEXT_OWNER_GO if fixpoint else "K1_PRE_POST_PRECONDITION_OR_PERFORM"
    blocker_class = (
        "ACTUAL_VENUE_POST_OWNER_GO_REQUIRED" if fixpoint else "PRECONDITION_OR_K1_CHAIN"
    )
    return {
        "WP": WORKPACKAGE_ID,
        "BASELINE_SHA": baseline_sha,
        "MAP_SHA256": map_sha256,
        "ATLAS_SHA256": atlas_sha256,
        "E2E_RUN_ID": e2e_run_id,
        "EVIDENCE_ROOT": evidence_root,
        "CANONICAL_K1_AUTHORITY": CANONICAL_K1_AUTHORITY,
        "K1_HANDLE_CLASS": K1_HANDLE_CLASS,
        "K1_PRE_POST_ADMISSION": perform_payload.get("PRECONDITIONS", {}).get(
            "K1_PRE_POST_ADMISSION", {}
        ),
        "K1_OWNER_GO_ADMISSION": perform_payload.get("OWNER_GO_PROBE", {}),
        "K1_OWNER_GO_CONSUMED": owner_go_token == OWNER_GO_TOKEN
        and handle_created
        and perform_payload.get("PERFORM_ATTEMPTED") is True,
        "FRESH_MATERIAL_LOAD_REQUIRED": perform_payload.get("FRESH_MATERIAL_LOAD_REQUIRED"),
        "FRESH_MATERIAL_LOAD_PERFORMED": perform_payload.get("FRESH_MATERIAL_LOAD_PERFORMED"),
        "K1_HANDLE_CREATED": handle_created,
        "K1_HANDLE_BINDINGS": perform_payload.get("K1_HANDLE_BINDINGS"),
        "SIGNING_WITHIN_K1_AUTHORITY": perform_payload.get("SIGNING_WITHIN_K1_AUTHORITY"),
        "SIGNING_PERFORMED": signing,
        "SECRET_MATERIAL_EXPOSED": secret_exposed,
        "SECRET_MATERIAL_PERSISTED": bool(perform_payload.get("SECRET_PERSISTED")),
        "IN_MEMORY_PERMIT_FOR_PRE_POST_BINDING_ONLY": perform_payload.get(
            "IN_MEMORY_PERMIT_FOR_PRE_POST_BINDING"
        ),
        "SCOPED_OWNER_GO_TOKEN": OWNER_GO_TOKEN,
        "PERFORM_PAYLOAD": dict(perform_payload),
        "CHAIN_6942_REFERENCE": {
            "PRE_EXTERNAL_EFFECT_REACHED": pre_external,
            "EVIDENCE_ROOT": (chain_6942_report or {}).get("EVIDENCE_ROOT"),
        },
        "CHAIN_6943_REFERENCE": {
            "MATERIAL_LOAD_PERFORMED_HISTORICAL": bool(
                (material_load_6943_report or {}).get("MATERIAL_LOAD_PERFORMED")
            ),
            "EVIDENCE_ROOT": (material_load_6943_report or {}).get("EVIDENCE_ROOT"),
            "NOT_REINTERPRETED_AS_PERSISTENT_SECRET": True,
        },
        "ADJUDICATED_CONCLUSIONS": {
            "k1_ephemeral_keychain_distinct_from_6943_material_load_consumer": True,
            "request_signing_within_k1_owner_go": True,
            "venue_post_not_started": True,
            "standing_keychain_pins_unchanged_after_perform": (
                perform_payload.get("STANDING_REAL_KEYCHAIN_ACCESS_AUTHORIZED_AFTER") is False
            ),
            "durable_external_effect_permit_not_minted": True,
        },
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "VENUE_POST_OWNER_GO_CONSUMED": False,
        "EXTERNAL_EFFECT_PERMIT_MINTED": False,
        "EXTERNAL_EFFECT_AUTHORIZED": False,
        "POST_ALLOWED": False,
        "REAL_EXTERNAL_EFFECT_COUNT": 0,
        "VENUE_POST_COUNT": 0,
        "FIXPOINT_REACHED": fixpoint,
        "NEXT_WP_ANCHOR": VENUE_POST_NEXT_OWNER_GO
        if fixpoint
        else "RESOLVE_K1_PRE_POST_PRECONDITION_OR_KEYCHAIN_ITEM",
        "OPEN_CONFLICTS": [],
    }
