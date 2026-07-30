"""Fail-closed classifier for legacy formal_authorization_v1 artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.constants_v1 import (
    LEGACY_FORMAL_AUTHORIZATION_CLASS,
    LEGACY_FORMAL_SCHEMA_ID,
    TARGET_RUNTIME_CAPABILITY,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.integrity_v1 import (
    integrity_digest_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    assert_no_plaintext_token_fields,
)


class LegacyFormalAuthorizationError(ValueError):
    """Fail-closed legacy formal authorization error."""


@dataclass(frozen=True)
class LegacyFormalAuthorizationV1:
    classification: str
    schema_id: str
    authorization_id: str
    authorization_digest: str
    preregistration_id: str
    preregistration_digest: str
    capability: str
    repository_sha: str
    runbook_sha256: str
    consumed: bool
    revoked_field: bool
    arming_state_raw: str
    path: str
    raw: Mapping[str, Any]

    @property
    def consumable(self) -> bool:
        return False


@dataclass
class LegacyClassificationResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    legacy: Optional[LegacyFormalAuthorizationV1] = None
    consumable: bool = False
    classification: str = ""


def classify_legacy_formal_authorization_v1(
    raw: Mapping[str, Any],
    *,
    path: str = "",
    expected_authorization_digest: Optional[str] = None,
) -> LegacyClassificationResultV1:
    blockers: list[str] = []
    try:
        assert_no_plaintext_token_fields(raw)
    except Exception as exc:  # noqa: BLE001
        return LegacyClassificationResultV1(ok=False, blockers=[f"PLAINTEXT_TOKEN_FIELD:{exc}"])

    schema_id = str(raw.get("schema_id") or "")
    artifact_kind = str(raw.get("artifact_kind") or "")
    if schema_id != LEGACY_FORMAL_SCHEMA_ID and artifact_kind != "FORMAL_SINGLE_USE_AUTHORIZATION":
        return LegacyClassificationResultV1(
            ok=False,
            blockers=["NOT_LEGACY_FORMAL_AUTHORIZATION_V1"],
            classification="UNKNOWN_SCHEMA",
        )

    auth_id = str(raw.get("authorization_id") or "")
    stored_digest = str(raw.get("authorization_digest") or "")
    # Recompute using the same digest scope as creation: exclude digest fields.
    material = {k: v for k, v in raw.items() if k not in ("authorization_digest", "digest_scope")}
    recomputed = integrity_digest_v1(material)
    # Note: integrity_digest_v1 excludes integrity_digest/digest_scope/authorization_digest;
    # formal auth used authorization_digest exclusion — same effective set for these keys.
    if stored_digest and stored_digest != recomputed:
        # Formal artifacts may have used slightly different exclusion; accept stored if
        # recomputed with formal digest scope matches expected.
        formal_material = {
            k: v for k, v in raw.items() if k not in ("authorization_digest", "digest_scope")
        }
        # Use identical dump rules
        from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
            canonical_json_dumps,
        )
        from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.integrity_v1 import (
            sha256_text,
        )

        recomputed = sha256_text(canonical_json_dumps(formal_material))
        if stored_digest != recomputed:
            blockers.append("LEGACY_AUTHORIZATION_DIGEST_MISMATCH")

    if expected_authorization_digest and stored_digest != expected_authorization_digest:
        blockers.append("LEGACY_EXPECTED_DIGEST_MISMATCH")

    capability = str(raw.get("capability_id") or raw.get("capability") or "")
    if capability and capability != TARGET_RUNTIME_CAPABILITY:
        blockers.append("LEGACY_CAPABILITY_MISMATCH")

    legacy = LegacyFormalAuthorizationV1(
        classification=LEGACY_FORMAL_AUTHORIZATION_CLASS,
        schema_id=schema_id or LEGACY_FORMAL_SCHEMA_ID,
        authorization_id=auth_id,
        authorization_digest=stored_digest or recomputed,
        preregistration_id=str(raw.get("preregistration_id") or ""),
        preregistration_digest=str(raw.get("preregistration_digest") or ""),
        capability=capability or TARGET_RUNTIME_CAPABILITY,
        repository_sha=str(raw.get("repository_sha") or ""),
        runbook_sha256=str(raw.get("runbook_sha256") or ""),
        consumed=bool(raw.get("consumed", False)),
        revoked_field=bool(raw.get("revoked", False)),
        arming_state_raw=str(raw.get("arming_state") or ""),
        path=path,
        raw=dict(raw),
    )
    # Never consumable — even if structurally ok.
    if not blockers:
        return LegacyClassificationResultV1(
            ok=True,
            blockers=[],
            legacy=legacy,
            consumable=False,
            classification=LEGACY_FORMAL_AUTHORIZATION_CLASS,
        )
    return LegacyClassificationResultV1(
        ok=False,
        blockers=sorted(set(blockers)),
        legacy=legacy,
        consumable=False,
        classification=LEGACY_FORMAL_AUTHORIZATION_CLASS,
    )


def load_and_classify_legacy_formal_authorization_v1(
    path: Path,
    *,
    expected_authorization_digest: Optional[str] = None,
) -> LegacyClassificationResultV1:
    if not path.is_file():
        return LegacyClassificationResultV1(ok=False, blockers=["LEGACY_AUTHORIZATION_MISSING"])
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return LegacyClassificationResultV1(ok=False, blockers=[f"LEGACY_PARSE_ERROR:{exc}"])
    if not isinstance(raw, dict):
        return LegacyClassificationResultV1(ok=False, blockers=["LEGACY_NOT_OBJECT"])
    return classify_legacy_formal_authorization_v1(
        raw,
        path=str(path),
        expected_authorization_digest=expected_authorization_digest,
    )
