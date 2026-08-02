"""Cap 5.2 one-time public-MD shadow authorization consumption (no orders)."""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_SCHEMA,
    CAPABILITY_ID,
    CONSUMPTION_LEDGER_FILENAME,
    LIVE_AUTHORIZED,
    ORDERS_AUTHORIZED,
    PAPER_ORDER_EXECUTION_ALLOWED,
    PUBLIC_MARKET_DATA_ONLY,
    TESTNET_AUTHORIZED,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.models_v1 import (
    canonical_json_dumps,
    sha256_hex,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.reason_codes_v1 import (
    PublicMdShadowFailureCodeV1,
)


class AuthorizationConsumptionError(RuntimeError):
    """Fail-closed Cap 5.2 authorization consumption error."""


def _as_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return default


def validate_public_md_shadow_authorization_artifact_v1(
    *,
    authorization_artifact: Mapping[str, Any],
    repository_sha: str,
) -> dict[str, Any]:
    if not AUTHORIZATION_CONSUMPTION_ALLOWED:
        raise AuthorizationConsumptionError(
            PublicMdShadowFailureCodeV1.AUTHORIZATION_CONSUMPTION_REQUIRED.value
        )
    artifact = dict(authorization_artifact or {})
    blockers: list[str] = []
    if str(artifact.get("schema") or "") != AUTHORIZATION_SCHEMA:
        blockers.append("SCHEMA_MISMATCH")
    if str(artifact.get("capability_id") or "") != CAPABILITY_ID:
        blockers.append("CAPABILITY_ID_MISMATCH")
    auth_id = str(artifact.get("authorization_id") or "").strip()
    if not auth_id:
        blockers.append("AUTHORIZATION_ID_MISSING")
    if str(artifact.get("network_scope") or "") != "PUBLIC_MARKET_DATA_ONLY":
        blockers.append("NETWORK_SCOPE_MISMATCH")
    if _as_bool(artifact.get("orders_authorized")) or ORDERS_AUTHORIZED:
        blockers.append("ORDERS_AUTHORIZED_FORBIDDEN")
    if _as_bool(artifact.get("live_authorized")) or LIVE_AUTHORIZED:
        blockers.append("LIVE_AUTHORIZED_FORBIDDEN")
    if _as_bool(artifact.get("testnet_authorized")) or TESTNET_AUTHORIZED:
        blockers.append("TESTNET_AUTHORIZED_FORBIDDEN")
    if _as_bool(artifact.get("paper_order_execution_authorized")) or PAPER_ORDER_EXECUTION_ALLOWED:
        blockers.append("PAPER_ORDER_EXECUTION_FORBIDDEN")
    if not _as_bool(artifact.get("public_market_data_only"), default=True) or (
        not PUBLIC_MARKET_DATA_ONLY
    ):
        blockers.append("PUBLIC_MARKET_DATA_ONLY_REQUIRED")
    if not _as_bool(artifact.get("authorization_consumption_allowed"), default=True):
        blockers.append("CONSUMPTION_NOT_ALLOWED_IN_ARTIFACT")
    if _as_bool(artifact.get("multi_future_runtime_authorized")):
        blockers.append("MULTI_FUTURE_FORBIDDEN")
    if _as_bool(artifact.get("vol_max_age_enforcement_enabled")):
        blockers.append("VOL_MAX_AGE_ENFORCEMENT_FORBIDDEN")
    if _as_bool(artifact.get("runtime_activated")):
        blockers.append("RUNTIME_ACTIVATION_FORBIDDEN")
    expected_sha = str(artifact.get("repository_sha") or "").strip()
    if expected_sha and expected_sha != repository_sha:
        blockers.append("REPOSITORY_SHA_MISMATCH")
    if not _as_bool(artifact.get("one_time_use"), default=True):
        blockers.append("ONE_TIME_USE_REQUIRED")
    if blockers:
        raise AuthorizationConsumptionError(
            PublicMdShadowFailureCodeV1.AUTHORIZATION_INVALID.value + ":" + ",".join(blockers)
        )
    return {
        "ok": True,
        "schema": AUTHORIZATION_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "authorization_id": auth_id,
        "network_scope": "PUBLIC_MARKET_DATA_ONLY",
        "public_market_data_only": True,
        "orders_authorized": False,
        "live_authorized": False,
        "testnet_authorized": False,
        "paper_order_execution_authorized": False,
        "one_time_use": True,
        "repository_sha": repository_sha,
        "authorization_consumed": False,
        "step": "authorization_contract_validation_and_consumption",
    }


def _ledger_path(store: Path) -> Path:
    return Path(store) / CONSUMPTION_LEDGER_FILENAME


def _already_consumed(*, store: Path, authorization_id: str) -> bool:
    marker = Path(store) / f"{authorization_id}.consumed.json"
    if marker.is_file():
        return True
    ledger = _ledger_path(store)
    if not ledger.is_file():
        return False
    for line in ledger.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(row.get("authorization_id") or "") == authorization_id:
            return True
    return False


def consume_public_md_shadow_authorization_v1(
    *,
    authorization_artifact: Mapping[str, Any],
    consumption_store: Path,
    repository_sha: str,
    session_id: str,
    now_unix: Optional[float] = None,
) -> dict[str, Any]:
    """Validate and one-time-consume Cap 5.2 public-MD shadow authorization."""
    validated = validate_public_md_shadow_authorization_artifact_v1(
        authorization_artifact=authorization_artifact,
        repository_sha=repository_sha,
    )
    store = Path(consumption_store)
    store.mkdir(parents=True, exist_ok=True)
    auth_id = str(validated["authorization_id"])
    if _already_consumed(store=store, authorization_id=auth_id):
        raise AuthorizationConsumptionError(
            PublicMdShadowFailureCodeV1.AUTHORIZATION_ALREADY_CONSUMED.value
        )
    consumed_at = float(time.time() if now_unix is None else now_unix)
    payload = {
        "authorization_id": auth_id,
        "capability_id": CAPABILITY_ID,
        "schema": AUTHORIZATION_SCHEMA,
        "session_id": session_id,
        "repository_sha": repository_sha,
        "consumed_at_unix": consumed_at,
        "network_scope": "PUBLIC_MARKET_DATA_ONLY",
        "public_market_data_only": True,
        "orders_authorized": False,
        "live_authorized": False,
        "testnet_authorized": False,
        "paper_order_execution_authorized": False,
        "one_time_use": True,
        "revocation_state": "CONSUMED",
        "step": "authorization_contract_validation_and_consumption",
    }
    text = canonical_json_dumps(payload)
    marker = store / f"{auth_id}.consumed.json"
    fd, tmp = tempfile.mkstemp(dir=str(store), prefix=".tmp_cap52_consume_", suffix=".partial")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, marker)
    except Exception:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
        raise
    ledger = _ledger_path(store)
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return {
        **validated,
        "authorization_consumed": True,
        "consumed_at_unix": consumed_at,
        "consumption_marker_path": str(marker),
        "consumption_ledger_path": str(ledger),
        "consumption_digest": sha256_hex(text),
        "ok": True,
    }
