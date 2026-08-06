"""Derive network_allowed solely from validated issuance authorization bindings.

Reuse-before-new: Operator-GO + authorization artifact are the sole authority.
No silent CLI promotion of network_allowed. No parallel authorization model.

Scope layers (must not be string-compared across layers):
  - V2 artifact.network_scope = PUBLIC_MARKET_DATA_ONLY
    (canonical authorization_artifact_v2 / AUTHORIZED_NETWORK_SCOPE)
  - Operator-GO.network_scope = okx_eea_futures_public_md_observe_v1
    (venue/endpoint observe scope)

Config digest domains (compared only within the same domain):
  - wallclock_config_identity
  - productive_code_identity
  - effective_session_config
  - activation_config (single_future activation digest; not present on V2 artifacts)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.constants_v1 import (
    AUTHORIZATION_SCHEMA,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.states_v1 import (
    AuthorizationStateV2,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZED_NETWORK_SCOPE,
    EFFECTIVE_SESSION_CONFIG_DIGEST_KEY,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.mandatory_bindings_v1 import (
    MandatoryBindingError,
    validate_mandatory_session_config_digest_binding_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.constants_v1 import (
    PRODUCTIVE_CODE_IDENTITY,
    WALLCLOCK_CONFIG_IDENTITY,
)
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
    CONFIG_DIGEST_DOMAIN_ACTIVATION_CONFIG,
    CONFIG_DIGEST_DOMAIN_EFFECTIVE_SESSION_CONFIG,
    CONFIG_DIGEST_DOMAIN_PRODUCTIVE_CODE_IDENTITY,
    CONFIG_DIGEST_DOMAIN_WALLCLOCK_CONFIG_IDENTITY,
    GOVERNED_EXECUTION_BINDING_CAPABILITY_ID,
    GOVERNED_PUBLIC_MD_NETWORK_SCOPE,
    GOVERNED_PUBLIC_MD_SESSION_EXECUTION_SCOPE,
    NETWORK_ALLOWED_AUTHORITY_SOURCE,
    PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)

_KNOWN_CONFIG_DIGEST_DOMAINS = frozenset(
    {
        CONFIG_DIGEST_DOMAIN_WALLCLOCK_CONFIG_IDENTITY,
        CONFIG_DIGEST_DOMAIN_PRODUCTIVE_CODE_IDENTITY,
        CONFIG_DIGEST_DOMAIN_EFFECTIVE_SESSION_CONFIG,
        CONFIG_DIGEST_DOMAIN_ACTIVATION_CONFIG,
    }
)

# Fail-closed invariant: V2 artifact scope vocabulary must stay aligned with
# canonical AUTHORIZED_NETWORK_SCOPE (no silent drift / aliasing).
assert PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE == AUTHORIZED_NETWORK_SCOPE


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
    config_digest_domain: str = ""
    artifact_network_scope: str = ""
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
            "config_digest_domain": self.config_digest_domain,
            "artifact_network_scope": self.artifact_network_scope,
            "capability_id": self.capability_id,
            "claims": dict(self.claims),
        }


def _artifact_digest_v1(raw: Mapping[str, Any]) -> str:
    from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
        sha256_canonical_v1,
    )

    return sha256_canonical_v1(dict(raw))


def _sha256_utf8_v1(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compute_wallclock_config_identity_digest_v1() -> str:
    """Same producer formula as productive_operator_go_producer_v1."""
    return _sha256_utf8_v1(WALLCLOCK_CONFIG_IDENTITY)


def compute_productive_code_identity_digest_v1() -> str:
    """Same producer formula as productive_operator_go_producer_v1."""
    return _sha256_utf8_v1(PRODUCTIVE_CODE_IDENTITY)


def _activation_config_digest_v1() -> str:
    from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
        load_activation_config_v1,
    )
    from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
        repo_root_v1,
    )

    return str(
        load_activation_config_v1(
            config_path=repo_root_v1()
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


def _extract_artifact_config_digest_domains_v1(
    raw: Mapping[str, Any],
) -> dict[str, str]:
    out: dict[str, str] = {}
    cfg_block = raw.get("config_digests")
    if isinstance(cfg_block, Mapping):
        for key in (
            CONFIG_DIGEST_DOMAIN_WALLCLOCK_CONFIG_IDENTITY,
            CONFIG_DIGEST_DOMAIN_PRODUCTIVE_CODE_IDENTITY,
            EFFECTIVE_SESSION_CONFIG_DIGEST_KEY,
        ):
            value = cfg_block.get(key)
            if isinstance(value, str) and value:
                out[key] = value
    session_cfg = raw.get("session_config_digest")
    if isinstance(session_cfg, str) and session_cfg:
        out.setdefault(EFFECTIVE_SESSION_CONFIG_DIGEST_KEY, session_cfg)
    return out


def _bind_config_digest_domains_v1(
    *,
    raw: Mapping[str, Any],
    expected_config_digest: str,
    expected_config_digest_domain: str,
    blockers: list[str],
    notes: list[str],
) -> tuple[str, str]:
    """Return (bound_digest, bound_domain). Fail-closed on unknown/incompatible domains."""
    schema = str(raw.get("schema") or "").strip()
    is_v2 = schema == AUTHORIZATION_SCHEMA
    domain_values = _extract_artifact_config_digest_domains_v1(raw)
    expected = str(expected_config_digest or "").strip()
    domain = str(expected_config_digest_domain or "").strip()

    if is_v2:
        cfg_block = raw.get("config_digests")
        try:
            validate_mandatory_session_config_digest_binding_v1(
                session_config_digest=raw.get("session_config_digest"),
                config_digests=cfg_block if isinstance(cfg_block, Mapping) else {},
            )
            notes.append("V2_SESSION_CONFIG_DIGEST_INTEGRITY_OK=true")
        except MandatoryBindingError as exc:
            blockers.append(f"V2_CONFIG_DIGEST_INTEGRITY:{exc}")

        # Producer-parity checks for identities that productive issuance stamps.
        if CONFIG_DIGEST_DOMAIN_WALLCLOCK_CONFIG_IDENTITY in domain_values:
            recomputed = compute_wallclock_config_identity_digest_v1()
            if domain_values[CONFIG_DIGEST_DOMAIN_WALLCLOCK_CONFIG_IDENTITY] != recomputed:
                blockers.append("WALLCLOCK_CONFIG_IDENTITY_PRODUCER_MISMATCH")
        if CONFIG_DIGEST_DOMAIN_PRODUCTIVE_CODE_IDENTITY in domain_values:
            recomputed = compute_productive_code_identity_digest_v1()
            if domain_values[CONFIG_DIGEST_DOMAIN_PRODUCTIVE_CODE_IDENTITY] != recomputed:
                blockers.append("PRODUCTIVE_CODE_IDENTITY_PRODUCER_MISMATCH")

    if not expected and not domain:
        # No caller-expected cross-binding; V2 internal integrity above is the check.
        bound = domain_values.get(EFFECTIVE_SESSION_CONFIG_DIGEST_KEY, "")
        return bound, (CONFIG_DIGEST_DOMAIN_EFFECTIVE_SESSION_CONFIG if bound else "")

    if domain and domain not in _KNOWN_CONFIG_DIGEST_DOMAINS:
        blockers.append(f"CONFIG_DIGEST_DOMAIN_UNKNOWN:{domain}")
        return "", domain

    if domain == CONFIG_DIGEST_DOMAIN_ACTIVATION_CONFIG:
        blockers.append(
            "CONFIG_DIGEST_DOMAIN_INCOMPATIBLE:"
            "activation_config_not_present_on_authorization_artifact_v2"
        )
        return "", domain

    if domain and not expected:
        blockers.append("EXPECTED_CONFIG_DIGEST_MISSING_FOR_DOMAIN")
        return "", domain

    if domain and expected:
        if domain not in domain_values:
            blockers.append(f"CONFIG_DIGEST_DOMAIN_MISSING_IN_ARTIFACT:{domain}")
            return "", domain
        if domain_values[domain] != expected:
            blockers.append("AUTHORIZATION_CONFIG_MISMATCH")
            return expected, domain
        notes.append(f"CONFIG_DIGEST_DOMAIN_BOUND:{domain}")
        return expected, domain

    # expected without explicit domain → auto-detect by exact value equality only.
    matches = sorted(d for d, value in domain_values.items() if value == expected)
    if len(matches) == 1:
        notes.append(f"CONFIG_DIGEST_DOMAIN_AUTO:{matches[0]}")
        return expected, matches[0]
    if len(matches) > 1:
        blockers.append("CONFIG_DIGEST_DOMAIN_AMBIGUOUS:" + ",".join(matches))
        return "", ""

    # Exact activation-config detection (separate domain; never equate via hex length).
    try:
        activation_digest = _activation_config_digest_v1()
    except Exception:  # noqa: BLE001
        activation_digest = ""
    if activation_digest and expected == activation_digest:
        blockers.append("CONFIG_DIGEST_DOMAIN_INCOMPATIBLE:activation_config_vs_v2_config_digests")
        return "", CONFIG_DIGEST_DOMAIN_ACTIVATION_CONFIG

    blockers.append("CONFIG_DIGEST_DOMAIN_UNKNOWN")
    return "", ""


def derive_network_allowed_from_issuance_authorization_v1(
    *,
    operator_go: OperatorGoContractV1,
    authorization_artifact_path: Path,
    expected_repository_sha: str,
    expected_config_digest: str = "",
    expected_config_digest_domain: str = "",
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
        "CROSS_LAYER_SCOPE_STRING_EQUALITY_FORBIDDEN=true",
        "CROSS_SCHEMA_DIGEST_COMPARISON_FORBIDDEN=true",
        f"PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE={PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE}",
        f"GOVERNED_PUBLIC_MD_NETWORK_SCOPE={GOVERNED_PUBLIC_MD_NETWORK_SCOPE}",
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
    if not network_scope:
        blockers.append("OPERATOR_GO_NETWORK_SCOPE_MISSING")
    elif network_scope not in ALLOWED_NETWORK_SCOPES:
        blockers.append(f"NETWORK_SCOPE_MISMATCH:{network_scope}")
    if network_scope and network_scope != GOVERNED_PUBLIC_MD_NETWORK_SCOPE:
        blockers.append(f"GOVERNED_PUBLIC_MD_NETWORK_SCOPE_MISMATCH:{network_scope}")
    if not session_scope:
        blockers.append("OPERATOR_GO_SESSION_EXECUTION_SCOPE_MISSING")
    elif session_scope not in ALLOWED_SESSION_EXECUTION_SCOPES:
        blockers.append(f"SESSION_EXECUTION_SCOPE_MISMATCH:{session_scope}")
    if session_scope and session_scope != GOVERNED_PUBLIC_MD_SESSION_EXECUTION_SCOPE:
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

    # Layer A: V2 / issuance artifact network_scope (PUBLIC_MARKET_DATA_ONLY).
    art_network_scope = str(raw.get("network_scope") or "").strip()
    if not art_network_scope:
        blockers.append("ARTIFACT_NETWORK_SCOPE_MISSING")
    elif art_network_scope != PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE:
        # Exact equality only; no prefix/substring/normalization.
        blockers.append(f"ARTIFACT_NETWORK_SCOPE_MISMATCH:{art_network_scope}")

    # Optional explicit artifact flag (probe fixtures). V2 omits this field.
    if "network_authorized" in raw and not bool(raw.get("network_authorized")):
        blockers.append("AUTHORIZATION_ARTIFACT_NETWORK_NOT_AUTHORIZED")

    # Single-use / consume state (V2). Do not consume here.
    state_raw = str(raw.get("state") or "").strip()
    if state_raw == AuthorizationStateV2.CONSUMED.value or raw.get("consumed_at") is not None:
        blockers.append("AUTHORIZATION_ALREADY_CONSUMED")
    if state_raw in {
        AuthorizationStateV2.REVOKED.value,
        AuthorizationStateV2.INVALIDATED.value,
    }:
        blockers.append(f"AUTHORIZATION_STATE_NOT_CONSUMABLE:{state_raw}")

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
    authorization_digest = str(
        raw.get("authorization_digest") or raw.get("integrity_digest") or ""
    ).strip()
    if not authorization_digest and raw:
        authorization_digest = _artifact_digest_v1(raw)

    bound_digest, bound_domain = _bind_config_digest_domains_v1(
        raw=raw,
        expected_config_digest=expected_config_digest,
        expected_config_digest_domain=expected_config_digest_domain,
        blockers=blockers,
        notes=notes,
    )

    # Scope identity for Step-4 remains SESSION_SCOPE; network scope is separate.
    _ = expected_scope

    network_allowed = (
        not blockers
        and bool(go.network_authorized)
        and bool(go.session_execution_authorized)
        and network_scope == GOVERNED_PUBLIC_MD_NETWORK_SCOPE
        and art_network_scope == PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE
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
        config_digest=bound_digest,
        config_digest_domain=bound_domain,
        artifact_network_scope=art_network_scope,
        claims={
            "NETWORK_ALLOWED_FROM_AUTHORIZATION": network_allowed,
            "NETWORK_ALLOWED_AUTHORITY_SOURCE_BOUND": True,
            "PARALLEL_AUTHORIZATION_AUTHORITY_CREATED": False,
            "PUBLIC_MD_NETWORK_SCOPE_MATCH": network_scope == GOVERNED_PUBLIC_MD_NETWORK_SCOPE,
            "ARTIFACT_NETWORK_SCOPE_PUBLIC_MARKET_DATA_ONLY": (
                art_network_scope == PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE
            ),
            "CROSS_SCHEMA_DIGEST_COMPARISON_REMOVED": True,
            "AUTHORIZATION_CONSUMED": False,
            "ORDERS_AUTHORIZED": False,
            "LIVE_AUTHORIZED": False,
            "TESTNET_AUTHORIZED": False,
            "CREDENTIALS_AUTHORIZED": False,
        },
    )
