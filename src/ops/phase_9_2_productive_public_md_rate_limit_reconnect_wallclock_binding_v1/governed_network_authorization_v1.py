"""Derive network_allowed solely from validated issuance authorization bindings.

Reuse-before-new: Operator-GO + authorization artifact are the sole authority.
No silent CLI promotion of network_allowed. No parallel authorization model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    assert_no_plaintext_token_fields,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.constants_v1 import (
    ALLOWED_NETWORK_SCOPES,
    ALLOWED_SESSION_EXECUTION_SCOPES,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    OperatorGoContractV1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    GOVERNED_EXECUTION_BINDING_CAPABILITY_ID,
    GOVERNED_PUBLIC_MD_NETWORK_SCOPE,
    GOVERNED_PUBLIC_MD_SESSION_EXECUTION_SCOPE,
    NETWORK_ALLOWED_AUTHORITY_SOURCE,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)


@dataclass
class GovernedNetworkAuthorizationResultV1:
    ok: bool
    network_allowed: bool = False
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    authority_source: str = NETWORK_ALLOWED_AUTHORITY_SOURCE
    authorization_id: str = ""
    authorization_digest: str = ""
    network_scope: str = ""
    session_execution_scope: str = ""
    repository_sha: str = ""
    config_digest: str = ""
    capability_id: str = GOVERNED_EXECUTION_BINDING_CAPABILITY_ID
    claims: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "network_allowed": self.network_allowed,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "authority_source": self.authority_source,
            "authorization_id": self.authorization_id,
            "authorization_digest": self.authorization_digest,
            "network_scope": self.network_scope,
            "session_execution_scope": self.session_execution_scope,
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "capability_id": self.capability_id,
            "claims": dict(self.claims),
        }


def _artifact_digest_v1(raw: Mapping[str, Any]) -> str:
    from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
        sha256_canonical_v1,
    )

    return sha256_canonical_v1(dict(raw))


def derive_network_allowed_from_issuance_authorization_v1(
    *,
    operator_go: OperatorGoContractV1,
    authorization_artifact_path: Path,
    expected_repository_sha: str,
    expected_config_digest: str = "",
    expected_session_id: str = TARGET_SESSION_ID,
    expected_capability_id: str = GOVERNED_EXECUTION_BINDING_CAPABILITY_ID,
    expected_scope: str = SESSION_SCOPE,
    cli_network_session_allowed: bool = False,
) -> GovernedNetworkAuthorizationResultV1:
    """Fail-closed derivation: network_allowed only when issuance authorizes public MD."""
    blockers: list[str] = []
    notes = [
        f"GOVERNED_EXECUTION_BINDING_CAPABILITY_ID={GOVERNED_EXECUTION_BINDING_CAPABILITY_ID}",
        f"NETWORK_ALLOWED_AUTHORITY_SOURCE={NETWORK_ALLOWED_AUTHORITY_SOURCE}",
        "NO_SILENT_CLI_NETWORK_PROMOTION=true",
        "PARALLEL_AUTHORIZATION_AUTHORITY_CREATED=false",
    ]

    if not cli_network_session_allowed:
        blockers.append("CLI_NETWORK_SESSION_ALLOWED_REQUIRED_FOR_GOVERNED_MODE")

    go = operator_go
    if bool(go.orders_authorized):
        blockers.append("ORDERS_AUTHORIZED_FORBIDDEN")
    if bool(go.live_authorized):
        blockers.append("LIVE_AUTHORIZED_FORBIDDEN")
    if bool(go.testnet_authorized):
        blockers.append("TESTNET_AUTHORIZED_FORBIDDEN")
    if bool(go.paper_execution_authorized):
        blockers.append("PAPER_EXECUTION_AUTHORIZED_FORBIDDEN")
    if bool(go.credentials_authorized):
        blockers.append("CREDENTIALS_AUTHORIZED_FORBIDDEN")
    if bool(go.broker_writes_authorized):
        blockers.append("BROKER_WRITES_AUTHORIZED_FORBIDDEN")

    if not bool(go.network_authorized):
        blockers.append("OPERATOR_GO_NETWORK_NOT_AUTHORIZED")
    if not bool(go.session_execution_authorized):
        blockers.append("OPERATOR_GO_SESSION_EXECUTION_NOT_AUTHORIZED")

    network_scope = str(go.network_scope or "").strip()
    session_scope = str(go.session_execution_scope or "").strip()
    if network_scope not in ALLOWED_NETWORK_SCOPES:
        blockers.append(f"NETWORK_SCOPE_MISMATCH:{network_scope or 'missing'}")
    if network_scope != GOVERNED_PUBLIC_MD_NETWORK_SCOPE:
        blockers.append(f"GOVERNED_PUBLIC_MD_NETWORK_SCOPE_MISMATCH:{network_scope}")
    if session_scope not in ALLOWED_SESSION_EXECUTION_SCOPES:
        blockers.append(f"SESSION_EXECUTION_SCOPE_MISMATCH:{session_scope or 'missing'}")
    if session_scope != GOVERNED_PUBLIC_MD_SESSION_EXECUTION_SCOPE:
        blockers.append(f"GOVERNED_SESSION_EXECUTION_SCOPE_MISMATCH:{session_scope}")

    go_sha = str(go.expected_repository_sha or "").strip()
    if not go_sha:
        blockers.append("OPERATOR_GO_EXPECTED_REPOSITORY_SHA_MISSING")
    elif go_sha != str(expected_repository_sha):
        blockers.append("AUTHORIZATION_SHA_MISMATCH")

    if str(go.session_id) and expected_session_id not in {
        TARGET_SESSION_ID,
        str(go.session_id),
    }:
        blockers.append("AUTHORIZATION_SESSION_ID_MISMATCH")

    art_path = Path(authorization_artifact_path)
    if not art_path.is_file():
        blockers.append(f"AUTHORIZATION_ARTIFACT_PATH_NOT_A_FILE:{art_path}")
        return GovernedNetworkAuthorizationResultV1(
            ok=False,
            network_allowed=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["FAIL_CLOSED_BEFORE_ARTIFACT_LOAD=true"],
            claims={
                "NETWORK_ALLOWED_FROM_AUTHORIZATION": False,
                "NETWORK_ALLOWED_AUTHORITY_SOURCE_BOUND": True,
                "PARALLEL_AUTHORIZATION_AUTHORITY_CREATED": False,
            },
        )

    try:
        raw = json.loads(art_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        blockers.append(f"AUTHORIZATION_ARTIFACT_PARSE_ERROR:{exc}")
        raw = {}
    if not isinstance(raw, dict):
        blockers.append("AUTHORIZATION_ARTIFACT_NOT_OBJECT")
        raw = {}
    else:
        try:
            assert_no_plaintext_token_fields(raw)
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"AUTHORIZATION_ARTIFACT_PLAINTEXT_TOKEN:{type(exc).__name__}")

    art_session = str(raw.get("preregistration_id") or raw.get("session_id") or "")
    if not art_session:
        blockers.append("AUTHORIZATION_ARTIFACT_PREREGISTRATION_ID_MISSING")
    elif art_session != str(go.session_id):
        blockers.append("AUTHORIZATION_ARTIFACT_PREREGISTRATION_ID_MISMATCH")

    art_sha = str(raw.get("repository_sha") or raw.get("expected_repository_sha") or "")
    if not art_sha:
        blockers.append("AUTHORIZATION_ARTIFACT_REPOSITORY_SHA_MISSING")
    elif art_sha != str(expected_repository_sha):
        blockers.append("AUTHORIZATION_SHA_MISMATCH")

    art_network_scope = str(raw.get("network_scope") or "").strip()
    if art_network_scope:
        if art_network_scope != GOVERNED_PUBLIC_MD_NETWORK_SCOPE:
            blockers.append(f"ARTIFACT_NETWORK_SCOPE_MISMATCH:{art_network_scope}")
    # Prefer explicit artifact network_authorized when present.
    if "network_authorized" in raw and not bool(raw.get("network_authorized")):
        blockers.append("AUTHORIZATION_ARTIFACT_NETWORK_NOT_AUTHORIZED")

    art_capability = str(raw.get("capability") or raw.get("capability_id") or "").strip()
    # Artifact may bind to productive issuance capability; Step-4 binding capability
    # is the consumer. Reject only explicit mismatched Step-4 capability claims.
    if (
        art_capability
        and art_capability.startswith("PHASE_9_2_STEP_4_")
        and (art_capability != expected_capability_id and art_capability != SESSION_SCOPE)
    ):
        blockers.append(f"CAPABILITY_ID_MISMATCH:{art_capability}")

    authorization_id = str(raw.get("authorization_id") or raw.get("preregistration_id") or "")
    if not authorization_id:
        blockers.append("AUTHORIZATION_ID_MISSING")
    authorization_digest = str(raw.get("authorization_digest") or "").strip()
    if not authorization_digest and raw:
        authorization_digest = _artifact_digest_v1(raw)

    config_digest = ""
    cfg_block = raw.get("config_digests")
    if isinstance(cfg_block, Mapping):
        config_digest = str(
            cfg_block.get("wallclock_config_identity") or cfg_block.get("config_digest") or ""
        )
    if not config_digest:
        config_digest = str(raw.get("config_digest") or go.config_identity or "")
    if expected_config_digest and config_digest and config_digest != expected_config_digest:
        # Allow identity string vs hash: only fail when both look like digests.
        if len(expected_config_digest) == 64 and len(config_digest) == 64:
            blockers.append("AUTHORIZATION_CONFIG_MISMATCH")

    # Scope identity for Step-4 remains SESSION_SCOPE; network scope is separate.
    _ = expected_scope

    network_allowed = (
        not blockers
        and bool(go.network_authorized)
        and bool(go.session_execution_authorized)
        and network_scope == GOVERNED_PUBLIC_MD_NETWORK_SCOPE
        and bool(cli_network_session_allowed)
    )
    ok = network_allowed and not blockers
    return GovernedNetworkAuthorizationResultV1(
        ok=ok,
        network_allowed=network_allowed,
        blockers=sorted(set(blockers)),
        notes=notes
        + [
            "NETWORK_ALLOWED_DERIVED_FROM_ISSUANCE=true"
            if network_allowed
            else "NETWORK_ALLOWED_DENIED=true"
        ],
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        network_scope=network_scope,
        session_execution_scope=session_scope,
        repository_sha=str(expected_repository_sha),
        config_digest=config_digest or expected_config_digest,
        claims={
            "NETWORK_ALLOWED_FROM_AUTHORIZATION": network_allowed,
            "NETWORK_ALLOWED_AUTHORITY_SOURCE_BOUND": True,
            "PARALLEL_AUTHORIZATION_AUTHORITY_CREATED": False,
            "PUBLIC_MD_NETWORK_SCOPE_MATCH": network_scope == GOVERNED_PUBLIC_MD_NETWORK_SCOPE,
            "ORDERS_AUTHORIZED": False,
            "LIVE_AUTHORIZED": False,
            "TESTNET_AUTHORIZED": False,
            "CREDENTIALS_AUTHORIZED": False,
        },
    )
