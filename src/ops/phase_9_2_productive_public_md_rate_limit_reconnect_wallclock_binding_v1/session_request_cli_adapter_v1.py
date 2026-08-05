"""CLI/operator adapter: assemble canonical wallclock session_request from issuance artifacts.

Capability: PHASE_9_2_STEP_4_PRODUCTIVE_SESSION_REQUEST_CLI_OPERATOR_ADAPTER_V1

Reuses the existing session_request Mapping shape consumed by
``build_canonical_wallclock_runner_kwargs_v1`` / ``run_productive_wallclock_session_v1``.
Does not mint authorization, confirm tokens, or session GO. Does not start a network
session and does not consume authorization or confirm tokens.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    assert_no_plaintext_token_fields,
    fingerprint_confirm_token,
    validate_token_format,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    load_operator_go_contract_dict_v1,
    parse_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    load_preregistration_contract_dict_v1,
    parse_preregistration_contract_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.confirm_token_binding_v1 import (
    load_confirm_token_plaintext_canonical_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    SESSION_REQUEST_ADAPTER_CAPABILITY_ID,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.runner_invoke_binding_v1 import (
    REQUIRED_RUNNER_KWARGS,
    build_canonical_wallclock_runner_kwargs_v1,
    prove_runner_invoke_binding_v1,
)

# Canonical session_request domain shape = Mapping of runner kwargs (+ metadata).
# Owner: runner_invoke_binding_v1 + run_productive_wallclock_session_v1 signature.
CANONICAL_SESSION_REQUEST_OWNER = (
    "ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1."
    "runner_invoke_binding_v1.build_canonical_wallclock_runner_kwargs_v1"
)


@dataclass
class SessionRequestAdapterResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    session_request: Optional[dict[str, Any]] = None
    runner_kwargs_keys: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    confirm_token_fingerprint: str = ""
    field_source_map: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        # Never serialize plaintext confirm_token; stringify Paths for JSON hygiene.
        safe_request: dict[str, Any] | None = None
        if self.session_request is not None:
            safe_request = {}
            for k, v in self.session_request.items():
                if k == "confirm_token":
                    safe_request[k] = "[REDACTED]"
                elif isinstance(v, Path):
                    safe_request[k] = str(v)
                elif k in {"prereg", "go"}:
                    safe_request[k] = type(v).__name__
                else:
                    safe_request[k] = v
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "session_request": safe_request,
            "runner_kwargs_keys": list(self.runner_kwargs_keys),
            "claims": dict(self.claims),
            "confirm_token_fingerprint": self.confirm_token_fingerprint,
            "field_source_map": dict(self.field_source_map),
            "capability_id": SESSION_REQUEST_ADAPTER_CAPABILITY_ID,
            "canonical_session_request_owner": CANONICAL_SESSION_REQUEST_OWNER,
        }


def _require_file(path: Path | None, code: str, blockers: list[str]) -> Path | None:
    if path is None:
        blockers.append(f"{code}_MISSING")
        return None
    resolved = Path(path)
    if not resolved.is_file():
        blockers.append(f"{code}_NOT_A_FILE:{resolved}")
        return None
    return resolved


def _load_authorization_artifact_bindings_v1(
    path: Path,
    *,
    expected_session_id: str,
    expected_repository_sha: str,
) -> list[str]:
    blockers: list[str] = []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"AUTHORIZATION_ARTIFACT_PARSE_ERROR:{exc}"]
    if not isinstance(raw, dict):
        return ["AUTHORIZATION_ARTIFACT_NOT_OBJECT"]
    try:
        assert_no_plaintext_token_fields(raw)
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"AUTHORIZATION_ARTIFACT_PLAINTEXT_TOKEN:{type(exc).__name__}")
        return blockers

    prereg_id = str(raw.get("preregistration_id") or raw.get("session_id") or "")
    if not prereg_id:
        blockers.append("AUTHORIZATION_ARTIFACT_PREREGISTRATION_ID_MISSING")
    elif prereg_id != expected_session_id:
        blockers.append("AUTHORIZATION_ARTIFACT_PREREGISTRATION_ID_MISMATCH")

    art_sha = str(raw.get("repository_sha") or raw.get("expected_repository_sha") or "")
    if not art_sha:
        blockers.append("AUTHORIZATION_ARTIFACT_REPOSITORY_SHA_MISSING")
    elif art_sha != expected_repository_sha:
        blockers.append("AUTHORIZATION_ARTIFACT_REPOSITORY_SHA_MISMATCH")
    return blockers


def build_canonical_session_request_from_issuance_artifacts_v1(
    *,
    preregistration_path: Path | None,
    operator_go_path: Path | None,
    authorization_artifact_path: Path | None,
    confirm_token_file: Path | None,
    fingerprint_ledger_path: Path | None,
    expected_repository_sha: str | None = None,
    evidence_root_override: Path | None = None,
    permit_canonical_runner_invoke: bool = False,
    use_real_network: bool = False,
    environ: Mapping[str, str] | None = None,
) -> SessionRequestAdapterResultV1:
    """Assemble signature-compatible session_request from existing issuance artifacts."""
    blockers: list[str] = []
    notes = [
        f"SESSION_REQUEST_ADAPTER_CAPABILITY_ID={SESSION_REQUEST_ADAPTER_CAPABILITY_ID}",
        f"CANONICAL_SESSION_REQUEST_OWNER={CANONICAL_SESSION_REQUEST_OWNER}",
        "NO_AUTHORIZATION_ISSUANCE=true",
        "NO_CONFIRM_TOKEN_MINT=true",
        "NO_AUTHORIZATION_CONSUMPTION=true",
        "NO_CONFIRM_TOKEN_CONSUMPTION=true",
        "PARALLEL_SESSION_REQUEST_MODEL_CREATED=false",
    ]
    field_source_map: dict[str, str] = {}

    if use_real_network:
        blockers.append("ADAPTER_FORBIDS_USE_REAL_NETWORK")
    if not permit_canonical_runner_invoke:
        blockers.append("OWNER_SESSION_PERMIT_REQUIRED")

    prereg_path = _require_file(preregistration_path, "PREREGISTRATION_PATH", blockers)
    go_path = _require_file(operator_go_path, "OPERATOR_GO_PATH", blockers)
    art_path = _require_file(authorization_artifact_path, "AUTHORIZATION_ARTIFACT_PATH", blockers)
    token_path = _require_file(confirm_token_file, "CONFIRM_TOKEN_FILE", blockers)
    ledger_path = _require_file(fingerprint_ledger_path, "FINGERPRINT_LEDGER_PATH", blockers)

    if blockers:
        return SessionRequestAdapterResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["FAIL_CLOSED_BEFORE_ASSEMBLY=true"],
            claims={
                "CLI_SESSION_REQUEST_ADAPTER_EXISTS": True,
                "CANONICAL_SESSION_REQUEST_TYPE_REUSED": True,
                "PARALLEL_SESSION_REQUEST_MODEL_CREATED": False,
                "SESSION_REQUEST_REQUIRED_FIELDS_COMPLETE": False,
                "NETWORK_SESSION_STARTED": False,
                "AUTHORIZATION_CONSUMED": False,
                "CONFIRM_TOKEN_CONSUMED": False,
                "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            },
            field_source_map=field_source_map,
        )

    assert prereg_path is not None
    assert go_path is not None
    assert art_path is not None
    assert token_path is not None
    assert ledger_path is not None

    try:
        prereg = parse_preregistration_contract_v1(
            load_preregistration_contract_dict_v1(prereg_path)
        )
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"PREREGISTRATION_LOAD_FAILED:{type(exc).__name__}")
        prereg = None  # type: ignore[assignment]

    try:
        go = parse_operator_go_contract_v1(load_operator_go_contract_dict_v1(go_path))
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"OPERATOR_GO_LOAD_FAILED:{type(exc).__name__}")
        go = None  # type: ignore[assignment]

    if prereg is None or go is None:
        return SessionRequestAdapterResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["FAIL_CLOSED_CONTRACT_LOAD=true"],
            claims={
                "CLI_SESSION_REQUEST_ADAPTER_EXISTS": True,
                "CANONICAL_SESSION_REQUEST_TYPE_REUSED": True,
                "PARALLEL_SESSION_REQUEST_MODEL_CREATED": False,
                "SESSION_REQUEST_REQUIRED_FIELDS_COMPLETE": False,
                "PREREG_GO_CANONICALLY_SOURCED": False,
                "NETWORK_SESSION_STARTED": False,
                "AUTHORIZATION_CONSUMED": False,
                "CONFIRM_TOKEN_CONSUMED": False,
                "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            },
            field_source_map=field_source_map,
        )

    # SHA: sourced from prereg; CLI override must match exactly (no silent replace).
    prereg_sha = str(prereg.expected_repository_sha or "")
    go_sha = str(go.expected_repository_sha or "")
    if not prereg_sha:
        blockers.append("PREREG_EXPECTED_REPOSITORY_SHA_MISSING")
    if not go_sha:
        blockers.append("OPERATOR_GO_EXPECTED_REPOSITORY_SHA_MISSING")
    if prereg_sha and go_sha and prereg_sha != go_sha:
        blockers.append("PREREG_OPERATOR_GO_REPOSITORY_SHA_MISMATCH")
    if expected_repository_sha:
        if str(expected_repository_sha) != prereg_sha:
            blockers.append("CLI_EXPECTED_REPOSITORY_SHA_MISMATCH")
        bound_sha = str(expected_repository_sha)
        field_source_map["expected_repository_sha"] = (
            "cli.expected_repository_sha==prereg.expected_repository_sha"
        )
    else:
        bound_sha = prereg_sha
        field_source_map["expected_repository_sha"] = "prereg.expected_repository_sha"

    # evidence_root from prereg only; optional CLI path must match.
    prereg_evidence = Path(str(prereg.evidence_root))
    if evidence_root_override is not None:
        override = Path(evidence_root_override)
        if override.resolve() != prereg_evidence.resolve() and str(override) != str(
            prereg_evidence
        ):
            blockers.append("EVIDENCE_ROOT_OVERRIDE_MISMATCH")
        evidence_root = prereg_evidence
        field_source_map["evidence_root"] = "prereg.evidence_root==cli.evidence_root"
    else:
        evidence_root = prereg_evidence
        field_source_map["evidence_root"] = "prereg.evidence_root"

    if go.session_id != prereg.session_id:
        blockers.append("OPERATOR_GO_SESSION_ID_MISMATCH")
    if go.confirm_token_binding_sha256 != prereg.confirm_token_binding_sha256:
        blockers.append("CONFIRM_TOKEN_BINDING_SHA256_MISMATCH")

    art_blockers = _load_authorization_artifact_bindings_v1(
        art_path,
        expected_session_id=str(prereg.session_id),
        expected_repository_sha=bound_sha,
    )
    blockers.extend(art_blockers)

    token_plaintext, token_load_blockers = load_confirm_token_plaintext_canonical_v1(
        confirm_token_file=token_path,
        environ=environ,
    )
    blockers.extend(token_load_blockers)
    token_fp = ""
    if token_plaintext and not token_load_blockers:
        fmt_blockers = list(validate_token_format(token_plaintext))
        if fmt_blockers:
            blockers.extend(fmt_blockers)
            token_plaintext = ""
        else:
            token_fp = fingerprint_confirm_token(token_plaintext)

    field_source_map["prereg"] = f"issuance.preregistration:{prereg_path}"
    field_source_map["go"] = f"issuance.operator_go:{go_path}"
    field_source_map["confirm_token"] = f"issuance.confirm_token_file:{token_path}"
    field_source_map["artifact_path"] = f"issuance.authorization_artifact:{art_path}"
    field_source_map["fingerprint_ledger_path"] = f"cli.fingerprint_ledger:{ledger_path}"
    field_source_map["use_real_network"] = "adapter.constant_false"

    if blockers:
        # Drop any plaintext immediately on fail-closed.
        token_plaintext = ""
        return SessionRequestAdapterResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["FAIL_CLOSED_BEFORE_SESSION_REQUEST=true"],
            confirm_token_fingerprint=token_fp,
            claims={
                "CLI_SESSION_REQUEST_ADAPTER_EXISTS": True,
                "CANONICAL_SESSION_REQUEST_TYPE_REUSED": True,
                "PARALLEL_SESSION_REQUEST_MODEL_CREATED": False,
                "SESSION_REQUEST_REQUIRED_FIELDS_COMPLETE": False,
                "SESSION_REQUEST_ARTIFACT_BINDINGS_PROVEN": False,
                "EXPECTED_REPOSITORY_SHA_BOUND": bool(bound_sha),
                "FINGERPRINT_LEDGER_BOUND": True,
                "PREREG_GO_CANONICALLY_SOURCED": True,
                "CONFIRM_TOKEN_ARTIFACT_CANONICALLY_SOURCED": True,
                "CLI_OWNER_SESSION_PERMIT_EXPLICIT": bool(permit_canonical_runner_invoke),
                "NETWORK_SESSION_STARTED": False,
                "AUTHORIZATION_CONSUMED": False,
                "CONFIRM_TOKEN_CONSUMED": False,
                "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            },
            field_source_map=field_source_map,
        )

    session_request: dict[str, Any] = {
        "session_id": str(prereg.session_id),
        "capability_id": SESSION_REQUEST_ADAPTER_CAPABILITY_ID,
        "owner_session_permit": True,
        "prereg": prereg,
        "go": go,
        "confirm_token": token_plaintext,
        "artifact_path": art_path,
        "evidence_root": evidence_root,
        "expected_repository_sha": bound_sha,
        "fingerprint_ledger_path": ledger_path,
        "use_real_network": False,
    }
    # Clear local name after placement into request (still held in mapping for dry kwargs).
    token_plaintext = ""

    try:
        kwargs = build_canonical_wallclock_runner_kwargs_v1(session_request)
    except ValueError as exc:
        session_request["confirm_token"] = ""
        return SessionRequestAdapterResultV1(
            ok=False,
            blockers=sorted(set(blockers + [str(exc)])),
            notes=notes + ["RUNNER_INVOKE_BINDING_FAILED=true"],
            confirm_token_fingerprint=token_fp,
            claims={
                "CLI_SESSION_REQUEST_ADAPTER_EXISTS": True,
                "CANONICAL_SESSION_REQUEST_TYPE_REUSED": True,
                "PARALLEL_SESSION_REQUEST_MODEL_CREATED": False,
                "SESSION_REQUEST_REQUIRED_FIELDS_COMPLETE": False,
                "RUNNER_SIGNATURE_MATCH": False,
                "NETWORK_SESSION_STARTED": False,
                "AUTHORIZATION_CONSUMED": False,
                "CONFIRM_TOKEN_CONSUMED": False,
                "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            },
            field_source_map=field_source_map,
        )

    proof = prove_runner_invoke_binding_v1(session_request)
    missing = [k for k in REQUIRED_RUNNER_KWARGS if k not in kwargs]
    if missing:
        blockers.append("SESSION_REQUEST_REQUIRED_FIELDS_INCOMPLETE:" + ",".join(missing))

    ok = not blockers and bool(proof.get("ok"))
    return SessionRequestAdapterResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes
        + [
            "SESSION_REQUEST_ASSEMBLED_FROM_ISSUANCE_ARTIFACTS=true",
            "DRY_PROBE_USE_REAL_NETWORK_FALSE=true",
            f"TARGET_SESSION_ID_REFERENCE={TARGET_SESSION_ID}",
        ],
        session_request=session_request if ok else None,
        runner_kwargs_keys=sorted(kwargs.keys()),
        confirm_token_fingerprint=token_fp,
        field_source_map=field_source_map,
        claims={
            "CLI_SESSION_REQUEST_ADAPTER_EXISTS": True,
            "CANONICAL_SESSION_REQUEST_TYPE_REUSED": True,
            "PARALLEL_SESSION_REQUEST_MODEL_CREATED": False,
            "SESSION_REQUEST_REQUIRED_FIELDS_COMPLETE": ok and not missing,
            "SESSION_REQUEST_ARTIFACT_BINDINGS_PROVEN": ok,
            "EXPECTED_REPOSITORY_SHA_BOUND": True,
            "FINGERPRINT_LEDGER_BOUND": True,
            "PREREG_GO_CANONICALLY_SOURCED": True,
            "CONFIRM_TOKEN_ARTIFACT_CANONICALLY_SOURCED": True,
            "CLI_OWNER_SESSION_PERMIT_EXPLICIT": True,
            "RUNNER_SIGNATURE_MATCH": bool(proof.get("runner_signature_match")),
            "PRODUCTIVE_SESSION_PATH_STRUCTURALLY_RUNTIME_REACHABLE": bool(
                proof.get("productive_session_path_structurally_runtime_reachable")
            ),
            "PRODUCTIVE_SESSION_PATH_DRY_PROBE_REACHABLE": ok,
            "NETWORK_SESSION_STARTED": False,
            "PUBLIC_MARKET_DATA_REQUEST_OCCURRED": False,
            "AUTHORIZATION_ISSUED": False,
            "AUTHORIZATION_CONSUMED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
            "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            "CONFIRM_TOKEN_PERSISTED": False,
        },
    )
