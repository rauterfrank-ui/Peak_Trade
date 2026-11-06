"""Post-6943 scoped REAL_KEYCHAIN / credential material load perform (no K1, no POST)."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

WORKPACKAGE_ID: Final[str] = "POST_6943_REAL_KEYCHAIN_MATERIAL_LOAD_SCOPED_PERFORM_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/AUTHORITY_MAP_ATLAS_GUIDED_REAL_KEYCHAIN_MATERIAL_LOAD_SCOPED_PERFORM_FROM_POST_6943_MAIN_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/post_6943_real_keychain_material_load_scoped_perform_v1_decision_v1.json"
)
OWNER_GO_DECISION_CONFIG: Final[str] = (
    "config/governance/real_keychain_access_or_credential_material_load_owner_go_v1_decision.json"
)
OWNER_GO_TOKEN: Final[str] = "REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_OWNER_GO"
MAP_SOURCE_REL: Final[str] = (
    "config/governance/current_system_interaction_authority_map_v1/source_v1.json"
)
ATLAS_CENSUS_REL: Final[str] = "docs/system_atlas/census/census_meta.yaml"
K1_NEXT_OWNER_GO: Final[str] = (
    "OWNER_GO_CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1"
)


@dataclass(frozen=True)
class MaterialLoadPreconditionProbeV1:
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
) -> MaterialLoadPreconditionProbeV1:
    reasons: list[str] = []
    token = str(owner_go_token or "").strip()
    if token != OWNER_GO_TOKEN:
        reasons.append("SCOPED_OWNER_GO_TOKEN_MISMATCH_OR_MISSING")
    owner = load_json_v1(repo_root, OWNER_GO_DECISION_CONFIG)
    if owner.get("owner_go") is not True:
        reasons.append("OWNER_GO_DECISION_NOT_TRUE")
    if str(owner.get("owner_go_token") or "") != OWNER_GO_TOKEN:
        reasons.append("OWNER_GO_DECISION_TOKEN_DRIFT")
    if owner.get("real_keychain_access_or_credential_material_load_owner_go") is not True:
        reasons.append("MATERIAL_LOAD_OWNER_GO_NOT_AUTHORIZED_IN_DECISION")
    return MaterialLoadPreconditionProbeV1(ok=not reasons, reason_codes=tuple(reasons))


def probe_material_load_preconditions_v1(*, repo_root: Path) -> dict[str, Any]:
    from src.governance.real_keychain_access_or_credential_material_load_policy_v1 import (
        evaluate_real_keychain_access_or_credential_material_load_admission_v1,
        prove_material_load_does_not_authorize_post_v1,
        prove_material_load_does_not_authorize_request_signing_v1,
        prove_material_load_does_not_flip_standing_keychain_pins_v1,
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

    admission = evaluate_real_keychain_access_or_credential_material_load_admission_v1(
        repo_root=repo_root
    )
    reasons: list[str] = []
    if admission.material_load_policy_granted is not True:
        reasons.extend(list(admission.reason_codes) or ["MATERIAL_LOAD_ADMISSION_DENIED"])
    if not prove_material_load_does_not_flip_standing_keychain_pins_v1():
        reasons.append("STANDING_KEYCHAIN_PIN_DRIFT")
    if not prove_material_load_does_not_authorize_request_signing_v1():
        reasons.append("REQUEST_SIGNING_MUST_REMAIN_FALSE")
    if not prove_material_load_does_not_authorize_post_v1():
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
        "MATERIAL_LOAD_ADMISSION": {
            "granted": admission.material_load_policy_granted,
            "status": admission.admission_status,
            "reason_codes": list(admission.reason_codes),
        },
        "STANDING_PINS_OK": not any(
            r.startswith("STANDING_") or r.startswith("AUTONOMY_") for r in reasons
        ),
        "PRECONDITION_PROBE": MaterialLoadPreconditionProbeV1(
            ok=not reasons,
            reason_codes=tuple(dict.fromkeys(reasons)),
        ).to_dict(),
    }


def perform_scoped_material_load_v1(
    *,
    repo_root: Path,
    owner_go_token: str,
    use_productive_macos_backend: bool,
    backend: Any | None = None,
) -> dict[str, Any]:
    """Perform governed ephemeral acquisition. Opaque bytes never enter this dict."""

    from src.governance.real_keychain_access_governed_credential_material_acquisition_v1 import (
        attempt_governed_credential_material_acquisition_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
        MacosSecurityFrameworkLookupBackendV1,
        REAL_KEYCHAIN_ACCESS_AUTHORIZED,
        REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
    )

    owner_probe = validate_scoped_owner_go_v1(repo_root=repo_root, owner_go_token=owner_go_token)
    pre = probe_material_load_preconditions_v1(repo_root=repo_root)
    if not owner_probe.ok or not pre["PRECONDITION_PROBE"]["OK"]:
        return {
            "PERFORM_ATTEMPTED": False,
            "OWNER_GO_PROBE": owner_probe.to_dict(),
            "PRECONDITIONS": pre,
            "ACQUISITION": None,
            "FAIL_CLOSED": True,
        }

    chosen_backend = backend
    if use_productive_macos_backend:
        if sys.platform != "darwin":
            return {
                "PERFORM_ATTEMPTED": False,
                "OWNER_GO_PROBE": owner_probe.to_dict(),
                "PRECONDITIONS": pre,
                "ACQUISITION": {
                    "acquisition_performed": False,
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
            "ACQUISITION": {
                "acquisition_performed": False,
                "reason_codes": ["LOOKUP_BACKEND_REQUIRED"],
            },
            "FAIL_CLOSED": True,
        }

    result = attempt_governed_credential_material_acquisition_v1(
        repo_root=repo_root,
        backend=chosen_backend,
    )
    public = result.to_public_dict_v1()
    return {
        "PERFORM_ATTEMPTED": True,
        "OWNER_GO_PROBE": owner_probe.to_dict(),
        "PRECONDITIONS": pre,
        "ACQUISITION": public,
        "MATERIAL_LOAD_PERFORMED": result.acquisition_performed is True,
        "REAL_CREDENTIAL_ACCESS_PERFORMED": result.real_credential_access_performed is True,
        "SECRET_DISCLOSED": result.secret_disclosed is True,
        "SECRET_PERSISTED": result.secret_persisted is True,
        "STANDING_REAL_KEYCHAIN_ACCESS_AUTHORIZED_AFTER": REAL_KEYCHAIN_ACCESS_AUTHORIZED is True,
        "STANDING_REAL_KEYCHAIN_ACCESS_IMPLEMENTED_AFTER": REAL_KEYCHAIN_ACCESS_IMPLEMENTED is True,
        "FAIL_CLOSED": result.acquisition_performed is not True,
    }


def build_material_load_perform_report_v1(
    *,
    repo_root: Path,
    baseline_sha: str,
    owner_go_token: str,
    perform_payload: Mapping[str, Any],
    chain_6942_report: Mapping[str, Any] | None,
    map_sha256: str,
    atlas_sha256: str,
    e2e_run_id: str,
    evidence_root: str,
) -> dict[str, Any]:
    performed = bool(perform_payload.get("MATERIAL_LOAD_PERFORMED"))
    secret_exposed = bool(perform_payload.get("SECRET_DISCLOSED")) or bool(
        perform_payload.get("SECRET_PERSISTED")
    )
    pre_external = bool((chain_6942_report or {}).get("PRE_EXTERNAL_EFFECT_REACHED"))
    fixpoint = (
        performed
        and not secret_exposed
        and perform_payload.get("STANDING_REAL_KEYCHAIN_ACCESS_AUTHORIZED_AFTER") is False
        and pre_external
    )
    first_blocker = K1_NEXT_OWNER_GO if fixpoint else "EXTERNAL_EFFECT_AUTHORIZATION"
    blocker_class = (
        "K1_OPAQUE_SIGNING_HANDLE_OWNER_GO_REQUIRED" if fixpoint else "PRECONDITION_OR_LOAD"
    )
    return {
        "WP": WORKPACKAGE_ID,
        "BASELINE_SHA": baseline_sha,
        "MAP_SHA256": map_sha256,
        "ATLAS_SHA256": atlas_sha256,
        "E2E_RUN_ID": e2e_run_id,
        "EVIDENCE_ROOT": evidence_root,
        "CANONICAL_CREDENTIAL_AUTHORITY": (
            "governance.real_keychain_access_governed_credential_material_acquisition_v1"
        ),
        "CREDENTIAL_SOURCE_CLASS": "MACOS_KEYCHAIN_GENERIC_PASSWORD_OPAQUE",
        "MATERIAL_LOAD_ADMISSION": perform_payload.get("PRECONDITIONS", {}).get(
            "MATERIAL_LOAD_ADMISSION", {}
        ),
        "MATERIAL_LOAD_PERFORMED": performed,
        "SECRET_MATERIAL_EXPOSED": secret_exposed,
        "SCOPED_OWNER_GO_TOKEN": OWNER_GO_TOKEN,
        "OWNER_GO_CONSUMED_FOR_THIS_WP": owner_go_token == OWNER_GO_TOKEN,
        "PERFORM_PAYLOAD": dict(perform_payload),
        "CHAIN_6942_REFERENCE": {
            "PRE_EXTERNAL_EFFECT_REACHED": pre_external,
            "EVIDENCE_ROOT": (chain_6942_report or {}).get("EVIDENCE_ROOT"),
        },
        "ADJUDICATED_CONCLUSIONS": {
            "admission_distinct_from_perform_proven": True,
            "standing_keychain_pins_unchanged_after_perform": (
                perform_payload.get("STANDING_REAL_KEYCHAIN_ACCESS_AUTHORIZED_AFTER") is False
            ),
            "k1_not_started": True,
            "venue_post_not_started": True,
        },
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "K1_OWNER_GO_CONSUMED": False,
        "VENUE_POST_OWNER_GO_CONSUMED": False,
        "EXTERNAL_EFFECT_PERMIT_MINTED": False,
        "EXTERNAL_EFFECT_AUTHORIZED": False,
        "POST_ALLOWED": False,
        "REAL_EXTERNAL_EFFECT_COUNT": 0,
        "VENUE_POST_COUNT": 0,
        "FIXPOINT_REACHED": fixpoint,
        "NEXT_WP_ANCHOR": K1_NEXT_OWNER_GO
        if fixpoint
        else "RESOLVE_MATERIAL_LOAD_PRECONDITION_OR_KEYCHAIN_ITEM",
        "OPEN_CONFLICTS": [],
    }
