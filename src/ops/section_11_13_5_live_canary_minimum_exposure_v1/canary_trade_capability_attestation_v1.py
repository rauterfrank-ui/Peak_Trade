"""§11.13.5.C LIVE canary trade-key attestation (metadata-only; fail-closed).

Proves or fail-closes the dedicated LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY
SecretRef binding without printing, hashing, or persisting secret material.
Does not submit orders, execute Canary, adopt Exchange-Truth, or clear
BLOCKS_NEW_ENTRY.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    BLOCKS_NEW_ENTRY,
    DEFAULT_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
    LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED,
    LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN,
    LIVE_RECONCILIATION_PROVEN,
    PRIOR_DRY_RUN_PERMISSION_ATTESTATION,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_ENTITY,
    REUSED_BINDING_REGION,
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
    SECRETREF_CANARY_PATH_MARKER,
    SECRETREF_CONVENTION_EXAMPLE,
    SECRETREF_FORBIDDEN_CROSS_PACKAGE_MARKERS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cybersecurity_canary_gate_v1 import (
    evaluate_live_canary_cybersecurity_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.trade_permission_forensic_v1 import (
    build_trade_permission_forensic_v1,
)

OWNER_GO_TRADE_KEY_ATTESTATION = "OWNER_GO_LIVE_CANARY_TRADE_KEY_ATTESTATION"
REQUIRED_SECRETREF_URI = SECRETREF_CONVENTION_EXAMPLE.replace("<venue>", "okx")
CANARY_VAULT_RELATIVE = "section_11_13_5_live_canary_minimum_exposure/secrets/secretref_vault.json"
PRIOR_PACKAGE_VAULTS: tuple[tuple[str, str], ...] = (
    (
        "section_11_13_2_live_private_read_only/secrets/secretref_vault.json",
        "secretref://vault/peak-trade/live-private-ro/okx",
    ),
    (
        "section_11_13_3_live_shadow_with_exchange_reconciliation/secrets/secretref_vault.json",
        "secretref://vault/peak-trade/live-shadow-recon/okx",
    ),
    (
        "section_11_13_4_live_dry_run_order_plan/secrets/secretref_vault.json",
        "secretref://vault/peak-trade/live-dry-run-order-plan/okx",
    ),
)

TERMINAL_PROVEN = "TRADE_KEY_ATTESTATION_PROVEN_AWAITING_EXCHANGE_TRUTH_ADOPTION"
TERMINAL_FAIL_CLOSED = "FAIL_CLOSED_TRADE_KEY_ATTESTATION_BLOCKED"


class LiveCanaryTradeKeyAttestationError(RuntimeError):
    """Fail-closed trade-key attestation violation."""


def _vault_key_names_only(path: Path) -> list[str]:
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LiveCanaryTradeKeyAttestationError(f"VAULT_NOT_OBJECT:{path}")
    return [str(k) for k in payload.keys()]


def _material_shape_meta(path: Path, uri: str) -> dict[str, Any] | None:
    """Return non-secret structural metadata for a vault URI, or None if absent.

    Never returns api_key/api_secret/passphrase values or digests of those values.
    """
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or uri not in payload:
        return None
    raw = payload[uri]
    if isinstance(raw, str):
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LiveCanaryTradeKeyAttestationError(f"VAULT_MATERIAL_NOT_JSON:{uri}") from exc
    elif isinstance(raw, dict):
        obj = raw
    else:
        raise LiveCanaryTradeKeyAttestationError(f"VAULT_MATERIAL_SHAPE_FORBIDDEN:{uri}")
    if not isinstance(obj, dict):
        raise LiveCanaryTradeKeyAttestationError(f"VAULT_MATERIAL_NOT_OBJECT:{uri}")
    fields = sorted(str(k) for k in obj.keys())
    # lengths only — never values
    lens = {
        f"{k}_len": len(str(obj.get(k, "")))
        for k in ("api_key", "api_secret", "passphrase")
        if k in obj
    }
    return {
        "uri": uri,
        "present": True,
        "top_fields": fields,
        "field_length_meta": lens,
        "secret_values_included": False,
    }


def _materials_equal_in_memory(path_a: Path, uri_a: str, path_b: Path, uri_b: str) -> bool:
    """Ephemeral equality check; result is boolean only (no material export)."""
    a = json.loads(path_a.read_text(encoding="utf-8"))[uri_a]
    b = json.loads(path_b.read_text(encoding="utf-8"))[uri_b]
    if isinstance(a, str):
        a = json.loads(a)
    if isinstance(b, str):
        b = json.loads(b)
    return (
        str(a.get("api_key", "")) == str(b.get("api_key", ""))
        and str(a.get("api_secret", "")) == str(b.get("api_secret", ""))
        and str(a.get("passphrase", "")) == str(b.get("passphrase", ""))
    )


def probe_local_canary_trade_key_secretref_v1(
    *,
    ops_local_root: Path | str,
) -> dict[str, Any]:
    """Inspect local `.ops_local` SecretRef bindings without secret export."""
    root = Path(ops_local_root)
    canary_vault = root / CANARY_VAULT_RELATIVE
    canary_keys = _vault_key_names_only(canary_vault)
    canary_uri_present = REQUIRED_SECRETREF_URI in canary_keys
    canary_meta = (
        _material_shape_meta(canary_vault, REQUIRED_SECRETREF_URI) if canary_uri_present else None
    )

    prior_present: list[dict[str, Any]] = []
    prior_paths: list[tuple[Path, str]] = []
    for rel, uri in PRIOR_PACKAGE_VAULTS:
        path = root / rel
        meta = _material_shape_meta(path, uri)
        prior_present.append(
            {
                "vault_relative": rel,
                "uri": uri,
                "present": meta is not None,
                "top_fields": None if meta is None else meta["top_fields"],
                "field_length_meta": None if meta is None else meta["field_length_meta"],
                "sealed_permission_attestation": dict(PRIOR_DRY_RUN_PERMISSION_ATTESTATION),
            }
        )
        if meta is not None:
            prior_paths.append((path, uri))

    prior_materials_identical: bool | None = None
    if len(prior_paths) >= 2:
        baseline = prior_paths[0]
        prior_materials_identical = all(
            _materials_equal_in_memory(baseline[0], baseline[1], p, u) for p, u in prior_paths[1:]
        )

    # Scan other vault json files for accidental canary URI placement (key names only).
    canary_uri_elsewhere: list[str] = []
    if root.is_dir():
        for path in root.rglob("secretref_vault.json"):
            if path.resolve() == canary_vault.resolve():
                continue
            if REQUIRED_SECRETREF_URI in _vault_key_names_only(path):
                canary_uri_elsewhere.append(str(path.relative_to(root)))

    cross_package_collision = any(
        marker in REQUIRED_SECRETREF_URI for marker in SECRETREF_FORBIDDEN_CROSS_PACKAGE_MARKERS
    )

    return {
        "DOCUMENT_CLASS": "SECTION_11_13_5_C_CANARY_TRADE_KEY_SECRETREF_PROBE_V1",
        "OPS_LOCAL_ROOT_PRESENT": root.is_dir(),
        "REQUIRED_SECRETREF_URI": REQUIRED_SECRETREF_URI,
        "REQUIRED_SECRETREF_PATH_MARKER": SECRETREF_CANARY_PATH_MARKER,
        "CANARY_VAULT_RELATIVE": CANARY_VAULT_RELATIVE,
        "CANARY_VAULT_PRESENT": canary_vault.is_file(),
        "CANARY_SECRETREF_URI_PRESENT": canary_uri_present,
        "CANARY_SECRETREF_SHAPE_META": canary_meta,
        "CANARY_SECRETREF_FOUND_ELSEWHERE": canary_uri_elsewhere,
        "PRIOR_PACKAGE_SECRETREFS": prior_present,
        "PRIOR_DRY_RUN_OR_RO_MATERIAL_PRESENT": any(p["present"] for p in prior_present),
        "PRIOR_PACKAGE_MATERIALS_IDENTICAL": prior_materials_identical,
        "CROSS_PACKAGE_URI_COLLISION_WITH_FORBIDDEN_MARKERS": cross_package_collision,
        "SECRET_VALUE_ACCESS": "NONE",
        "SECRET_VALUES_PERSISTED": False,
        "SECRET_DIGESTS_PERSISTED": False,
        "ok": True,
    }


def evaluate_live_canary_canary_trade_capability_attestation_v1(
    *,
    ops_local_root: Path | str,
    origin_main_sha: str,
    owner_go: str = OWNER_GO_TRADE_KEY_ATTESTATION,
    owner_permission_attestation: Mapping[str, Any] | None = None,
    productive_private_read_effect: str = "NONE",
    network_effect: str = "NONE",
) -> dict[str, Any]:
    """Prove or fail-close dedicated Canary trade-key attestation under this Owner-GO."""
    if str(owner_go or "").strip() != OWNER_GO_TRADE_KEY_ATTESTATION:
        raise LiveCanaryTradeKeyAttestationError("OWNER_GO_MISBOUND")
    if productive_private_read_effect not in {"NONE", "READ_ONLY"}:
        raise LiveCanaryTradeKeyAttestationError("PRIVATE_READ_EFFECT_FORBIDDEN")
    if network_effect not in {"NONE", "LIVE_PRIVATE_READ_ONLY"}:
        raise LiveCanaryTradeKeyAttestationError("NETWORK_EFFECT_FORBIDDEN")

    sealed = build_trade_permission_forensic_v1()
    probe = probe_local_canary_trade_key_secretref_v1(ops_local_root=ops_local_root)
    owner_perm = dict(owner_permission_attestation or {})
    required = dict(REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT)

    blockers: list[str] = []
    if not probe["CANARY_VAULT_PRESENT"]:
        blockers.append("CANARY_SECRETREF_VAULT_MISSING")
    if not probe["CANARY_SECRETREF_URI_PRESENT"]:
        blockers.append("CANARY_SECRETREF_URI_ABSENT")
    if probe["CANARY_SECRETREF_FOUND_ELSEWHERE"]:
        blockers.append("CANARY_SECRETREF_URI_AMBIGUOUS_ELSEWHERE")
    if probe["PRIOR_DRY_RUN_OR_RO_MATERIAL_PRESENT"] and not probe["CANARY_SECRETREF_URI_PRESENT"]:
        blockers.append("ONLY_AVAILABLE_KEY_IS_PRIOR_DRY_RUN_OR_RO_TRADE_FALSE")
    # Historical sealed dry-run TRADE=false is a blocker only while the dedicated
    # canary SecretRef is still absent (cannot substitute). Once a distinct canary
    # SecretRef is present and not reused, this is historical context only.
    if (
        sealed["PRIOR_PERMISSION_ATTESTATION"].get("TRADE") is False
        and not probe["CANARY_SECRETREF_URI_PRESENT"]
    ):
        blockers.append("SEALED_PRIOR_DRY_RUN_KEY_TRADE_FALSE_NOT_REUSABLE")

    # Positive TRADE/WITHDRAW proof requires either Owner attestation payload for the
    # dedicated canary key class + resolvable SecretRef, or a future read-only probe
    # against that SecretRef. Absence of SecretRef => cannot positively prove.
    owner_complete = (
        owner_perm.get("READ") is True
        and owner_perm.get("TRADE") is True
        and owner_perm.get("WITHDRAW") is False
        and str(owner_perm.get("credential_class") or "") == REQUIRED_CREDENTIAL_CLASS
        and str(owner_perm.get("secretref_uri") or "").strip() == REQUIRED_SECRETREF_URI
        and str(owner_perm.get("venue") or "") == REUSED_BINDING_VENUE
        and str(owner_perm.get("entity") or "") == REUSED_BINDING_ENTITY
        and str(owner_perm.get("region") or "") == REUSED_BINDING_REGION
        and str(owner_perm.get("rest_host") or "") == REUSED_BINDING_REST_HOST
        and str(owner_perm.get("account_scope") or "") == REUSED_BINDING_ACCOUNT_SCOPE
    )
    if owner_perm and not owner_complete:
        blockers.append("OWNER_PERMISSION_ATTESTATION_AMBIGUOUS_OR_INCOMPLETE")
    if not owner_perm:
        blockers.append("OWNER_TRADE_KEY_PERMISSION_ATTESTATION_ABSENT")
    if not probe["CANARY_SECRETREF_URI_PRESENT"]:
        blockers.append("TRADE_CAPABILITY_NOT_POSITIVELY_PROVEN")
        blockers.append("WITHDRAW_DISABLED_NOT_POSITIVELY_PROVEN_FOR_INTENDED_KEY")
        blockers.append("KEY_ACCOUNT_HOST_BINDING_AMBIGUOUS_WITHOUT_CANARY_SECRETREF")

    prior_dry_run_key_reused = False
    if probe["CANARY_SECRETREF_URI_PRESENT"] and probe["PRIOR_DRY_RUN_OR_RO_MATERIAL_PRESENT"]:
        # If canary URI exists, compare ephemerally to prior dry-run material.
        canary_vault = Path(ops_local_root) / CANARY_VAULT_RELATIVE
        dry_rel, dry_uri = PRIOR_PACKAGE_VAULTS[-1]
        dry_vault = Path(ops_local_root) / dry_rel
        if dry_vault.is_file() and canary_vault.is_file():
            try:
                if _materials_equal_in_memory(
                    canary_vault, REQUIRED_SECRETREF_URI, dry_vault, dry_uri
                ):
                    prior_dry_run_key_reused = True
                    blockers.append("PRIOR_DRY_RUN_KEY_REUSED_AS_CANARY_TRADE_KEY")
            except Exception:  # noqa: BLE001 - treat compare failure as ambiguity
                blockers.append("CANARY_VS_PRIOR_KEY_COMPARE_AMBIGUOUS")

    trade_attestation = bool(
        probe["CANARY_SECRETREF_URI_PRESENT"]
        and owner_complete
        and not prior_dry_run_key_reused
        and "TRADE_CAPABILITY_NOT_POSITIVELY_PROVEN" not in blockers
    )
    # WITHDRAW_ATTESTATION semantics: true means withdraw enabled (forbidden).
    withdraw_attestation = bool(owner_perm.get("WITHDRAW") is True)
    read_attestation = bool(
        (owner_perm.get("READ") is True)
        or sealed["PRIOR_PERMISSION_ATTESTATION"].get("READ") is True
    )
    if withdraw_attestation:
        blockers.append("WITHDRAW_ENABLED_FORBIDDEN")
        trade_attestation = False

    # Deduplicate blockers while preserving order.
    seen: set[str] = set()
    ordered_blockers: list[str] = []
    for b in blockers:
        if b not in seen:
            seen.add(b)
            ordered_blockers.append(b)

    if trade_attestation and ordered_blockers:
        trade_attestation = False

    terminal = TERMINAL_PROVEN if trade_attestation else TERMINAL_FAIL_CLOSED
    canary_binding = "PROVEN" if trade_attestation else "NOT_PROVEN_FAIL_CLOSED"

    gate = evaluate_live_canary_cybersecurity_gate_v1(
        productive_surface_merged_to_origin_main=True,
        trade_attestation=trade_attestation,
        withdraw_attestation=withdraw_attestation,
        read_attestation=read_attestation,
        permission_attestation={
            "READ": True if read_attestation else False,
            "TRADE": True if trade_attestation else False,
            "WITHDRAW": True if withdraw_attestation else False,
        },
    )

    earliest = (
        "OWNER_GO_EXCHANGE_TRUTH_ADOPTION"
        if trade_attestation
        else "OWNER_PROVISION_DEDICATED_LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY_AND_SECRETREF"
    )
    next_step = (
        "OWNER_GO_EXCHANGE_TRUTH_ADOPTION"
        if trade_attestation
        else (
            "OWNER_ACTIONS_CREATE_OR_SELECT_TRADE_CAPABLE_WITHDRAWAL_DISABLED_LIVE_API_KEY_"
            "STORE_UNDER_live-canary-minimum-exposure_SECRETREF_THEN_REISSUE_"
            "OWNER_GO_LIVE_CANARY_TRADE_KEY_ATTESTATION"
        )
    )

    return {
        "DOCUMENT_CLASS": "SECTION_11_13_5_C_LIVE_CANARY_TRADE_KEY_ATTESTATION_V1",
        "OWNER_GO_BOUND": OWNER_GO_TRADE_KEY_ATTESTATION,
        "OWNER_GO_STATUS": "CONSUMED",
        "ORIGIN_MAIN_SHA": origin_main_sha,
        "KEY_CLASS": REQUIRED_CREDENTIAL_CLASS,
        "VENUE": REUSED_BINDING_VENUE,
        "LEGAL_ENTITY": REUSED_BINDING_ENTITY,
        "REGION": REUSED_BINDING_REGION,
        "REST_HOST": REUSED_BINDING_REST_HOST,
        "ACCOUNT_SCOPE": REUSED_BINDING_ACCOUNT_SCOPE,
        "CANARY_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "REQUIRED_API_KEY_CAPABILITY": required,
        "SECRETREF_STATUS": (
            "RESOLVED" if probe["CANARY_SECRETREF_URI_PRESENT"] else "MISSING_FAIL_CLOSED"
        ),
        "SECRETREF_URI_CONTRACT": REQUIRED_SECRETREF_URI,
        "KEY_BINDING_STATUS": canary_binding,
        "CANARY_TRADE_KEY_BINDING": canary_binding,
        "READ_ATTESTATION": read_attestation,
        "TRADE_ATTESTATION": trade_attestation,
        "WITHDRAW_ATTESTATION": withdraw_attestation,
        "INTENDED_KEY_TRADE_CAPABLE_VERIFIED": trade_attestation,
        "INTENDED_KEY_WITHDRAWAL_DISABLED_VERIFIED": trade_attestation,
        "PRIOR_DRY_RUN_KEY_REUSED": prior_dry_run_key_reused,
        "PRIOR_DRY_RUN_PERMISSION_ATTESTATION_SEALED": dict(PRIOR_DRY_RUN_PERMISSION_ATTESTATION),
        "SECRETREF_PROBE": probe,
        "SEALED_PRIOR_PERMISSION_FORENSIC": sealed,
        "PRODUCTIVE_PRIVATE_READ_EFFECT": productive_private_read_effect,
        "NETWORK_EFFECT": network_effect,
        "ORDER_EFFECT": "NONE",
        "ACCOUNT_MUTATION_EFFECT": "NONE",
        "SECRET_VALUE_ACCESS": "NONE",
        "LIVE_CANARY_CYBERSECURITY_GATE": gate["LIVE_CANARY_CYBERSECURITY_GATE"],
        "LIVE_CANARY_CYBERSECURITY_GATE_EVAL": gate,
        "BLOCKS_NEW_ENTRY": BLOCKS_NEW_ENTRY,
        "LIVE_RECONCILIATION_PROVEN": LIVE_RECONCILIATION_PROVEN,
        "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED": LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED,
        "LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN": LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "EXCHANGE_TRUTH_ADOPTION_STATUS": "OWNER_POLICIES_REQUIRED_NOT_ADOPTED",
        "EXCHANGE_TRUTH_ADOPTION_AUTHORIZED_BY_THIS_GO": False,
        "PRIOR_CANARY_OWNER_GO_REUSED": False,
        "NEW_CANARY_OWNER_GO_GRANTED": False,
        "TERMINAL_STATE": terminal,
        "BLOCKERS": ordered_blockers,
        "EARLIEST_UNRESOLVED_DEPENDENCY": earliest,
        "CANONICAL_NEXT_STEP": next_step,
        "HARD_STOP_REASONS": ordered_blockers,
        "ok": True,
    }
