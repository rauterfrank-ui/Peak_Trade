"""Inspect SecretRef presence without disclosing secret values."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)

DEFAULT_VAULT_RELATIVE = "section_11_13_5_live_canary_minimum_exposure/secrets/secretref_vault.json"


def default_vault_path_v1(*, repo_root: Path) -> Path:
    return Path(repo_root) / ".ops_local" / DEFAULT_VAULT_RELATIVE


def inspect_credential_material_presence_v1(*, vault_file: Path) -> dict[str, Any]:
    """Return presence/completeness only. Never returns secret values."""

    path = Path(vault_file)
    if not path.is_file():
        return {
            "VAULT_FILE_PRESENT": False,
            "SECRETREF_URI_BOUND": False,
            "CREDENTIAL_FIELDS_COMPLETE": False,
            "SECRETREF_URI": REQUIRED_SECRETREF_URI,
            "CREDENTIAL_CLASS": REQUIRED_CREDENTIAL_CLASS,
            "VALUES_INCLUDED": False,
            "available": False,
            "reason": "VAULT_FILE_MISSING",
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Section1114OfflineSurfaceError("VAULT_FILE_NOT_JSON") from exc
    if not isinstance(payload, Mapping):
        raise Section1114OfflineSurfaceError("VAULT_FILE_NOT_OBJECT")
    bound = REQUIRED_SECRETREF_URI in payload
    complete = False
    if bound:
        raw = payload[REQUIRED_SECRETREF_URI]
        material: Mapping[str, Any]
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise Section1114OfflineSurfaceError("SECRETREF_MATERIAL_NOT_JSON") from exc
            if not isinstance(parsed, Mapping):
                raise Section1114OfflineSurfaceError("SECRETREF_MATERIAL_NOT_OBJECT")
            material = parsed
        elif isinstance(raw, Mapping):
            material = raw
        else:
            raise Section1114OfflineSurfaceError("SECRETREF_MATERIAL_TYPE_FORBIDDEN")
        key_ok = bool(str(material.get("api_key") or "").strip())
        secret_ok = bool(str(material.get("api_secret") or "").strip())
        phrase_ok = bool(str(material.get("passphrase") or "").strip())
        complete = key_ok and secret_ok and phrase_ok
        del material
    available = bound and complete
    return {
        "VAULT_FILE_PRESENT": True,
        "SECRETREF_URI_BOUND": bound,
        "CREDENTIAL_FIELDS_COMPLETE": complete,
        "SECRETREF_URI": REQUIRED_SECRETREF_URI,
        "CREDENTIAL_CLASS": REQUIRED_CREDENTIAL_CLASS,
        "VALUES_INCLUDED": False,
        "available": available,
        "reason": "CREDENTIAL_MATERIAL_AVAILABLE"
        if available
        else "CREDENTIAL_MATERIAL_INCOMPLETE",
    }
