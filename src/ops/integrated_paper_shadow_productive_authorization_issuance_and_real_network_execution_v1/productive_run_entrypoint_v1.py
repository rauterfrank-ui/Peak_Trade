"""Productive wallclock run entrypoint: verify → consume → lock → then network."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Set

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1 import (
    WallclockRuntimeConfigV1,
    WallclockSessionResultV1,
    WallclockSessionRuntimeV1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.constants_v1 import (  # noqa: E501
    CANONICAL_HOST,
    CAPABILITY_ID,
    NETWORK_SCOPE,
    REAL_NETWORK_ENV,
    SESSION_EXECUTION_SCOPE,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    fingerprint_confirm_token,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.issuance_evidence_v1 import (
    write_issuance_runtime_evidence_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_authorization_verifier_v1 import (  # noqa: E501
    verify_productive_authorization_bundle_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.real_http_fetcher_v1 import (  # noqa: E501
    build_real_eea_public_md_transport_v1,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.authorization_artifact_v2 import (
    parse_authorization_artifact_v2,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZATION_SCHEMA_REJECTED_LEGACY,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.v1_quarantine_v1 import (
    classify_authorization_schema_for_wallclock_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1 import (
    AuthorizationArtifactV1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    OperatorGoContractV1,
    load_operator_go_contract_dict_v1,
    parse_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    SessionPreregistrationContractV1,
    load_preregistration_contract_dict_v1,
    parse_preregistration_contract_v1,
)


@dataclass
class ProductiveRunGateResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    network_opened: bool = False
    session_result: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _fingerprint_payload(payload: Mapping[str, Any]) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def assert_productive_run_preconditions_v1(
    *,
    prereg: SessionPreregistrationContractV1,
    go: OperatorGoContractV1,
    artifact: AuthorizationArtifactV1 | None = None,
    confirm_token: str = "",
    now_unix: float,
    expected_repository_sha: str,
    use_real_network: bool,
    environ: Mapping[str, str] | None = None,
    previously_seen_fingerprints: frozenset[str] | None = None,
    artifact_path: Path | None = None,
) -> list[str]:
    """Productive preconditions. AuthorizationArtifactV1 is never admissible."""
    blockers: list[str] = []
    if artifact is not None:
        return [AUTHORIZATION_SCHEMA_REJECTED_LEGACY]
    if artifact_path is None or not artifact_path.is_file():
        return ["AUTHORIZATION_ARTIFACT_MISSING"]
    try:
        raw = json.loads(artifact_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["AUTHORIZATION_PARSE_ERROR"]
    if not isinstance(raw, dict):
        return ["AUTHORIZATION_NOT_OBJECT"]
    kind, kind_blockers = classify_authorization_schema_for_wallclock_v1(raw)
    if kind != "v2":
        return sorted(set(kind_blockers or [AUTHORIZATION_SCHEMA_REJECTED_LEGACY]))
    try:
        v2 = parse_authorization_artifact_v2(raw)
    except Exception as exc:  # noqa: BLE001
        return [f"AUTHORIZATION_PARSE_FAILED:{type(exc).__name__}"]
    if v2.forced_wiring_fixture_mode:
        blockers.append("FIXTURE_AUTH_REJECTED_FOR_PRODUCTIVE_RUN")
    if prereg.fixture_non_authoritative or go.fixture_non_authoritative:
        blockers.append("FIXTURE_AUTH_REJECTED_FOR_PRODUCTIVE_RUN")
    if go.network_scope != NETWORK_SCOPE or go.session_execution_scope != SESSION_EXECUTION_SCOPE:
        blockers.append("SCOPE_BINDING_MISMATCH")
    if v2.repository_sha != expected_repository_sha:
        blockers.append("REPOSITORY_SHA_MISMATCH")
    if use_real_network:
        env = environ if environ is not None else os.environ
        if str(env.get(REAL_NETWORK_ENV) or "") != "1":
            blockers.append("REAL_NETWORK_ENV_REQUIRED_AS_ADDITIONAL_GATE")
        if blockers:
            blockers.append("REAL_NETWORK_REQUIRES_VERIFIED_PRODUCTIVE_AUTH")
        from src.ops.canonical_runtime_environment_contract_v1.preflight_v1 import (
            collect_proxy_no_proxy_blockers_v1,
        )

        # O1: proxy/NO_PROXY fail-closed BEFORE authorization consumption proceeds.
        blockers.extend(collect_proxy_no_proxy_blockers_v1(env))
    else:
        # Even offline productive gates must not carry proxy inheritance into later network bind.
        env = environ if environ is not None else {}
        if env:
            from src.ops.canonical_runtime_environment_contract_v1.preflight_v1 import (
                collect_proxy_no_proxy_blockers_v1,
            )

            blockers.extend(collect_proxy_no_proxy_blockers_v1(env))
    # Keep previously_seen_fingerprints for API compatibility; replay is enforced in gatekeeper.
    _ = (
        confirm_token,
        now_unix,
        previously_seen_fingerprints,
        verify_productive_authorization_bundle_v1,
    )
    return sorted(set(blockers))


def run_productive_wallclock_session_v1(
    *,
    prereg: SessionPreregistrationContractV1,
    go: OperatorGoContractV1,
    confirm_token: str,
    artifact_path: Path,
    evidence_root: Path,
    expected_repository_sha: str,
    fingerprint_ledger_path: Path,
    artifact: AuthorizationArtifactV1 | None = None,
    transport: Optional[EeaPublicMdTransportV1] = None,
    use_real_network: bool = False,
    runtime_config: WallclockRuntimeConfigV1 | None = None,
    clock_wall: Callable[[], float] | None = None,
    clock_mono: Callable[[], float] | None = None,
    sleep: Callable[[float], None] | None = None,
    repo_root: Path | None = None,
    known_session_ids: Optional[Set[str]] = None,
    environ: Mapping[str, str] | None = None,
    previously_seen_fingerprints: frozenset[str] | None = None,
    stop_flag: Optional[Callable[[], bool]] = None,
    runtime_overrides: Mapping[str, Any] | None = None,
) -> ProductiveRunGateResultV1:
    """Fail-closed productive run. Network only after canonical v2 consumption inside runtime."""
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "CONSUMPTION_BEFORE_NETWORK",
        "CANONICAL_AUTHORIZATION_ARTIFACT_V2_ONLY",
        "FIXTURES_REJECTED",
        f"HOST={CANONICAL_HOST}",
    ]
    now = float((clock_wall or time.time)())
    if artifact is not None:
        return ProductiveRunGateResultV1(
            ok=False, blockers=[AUTHORIZATION_SCHEMA_REJECTED_LEGACY], notes=notes
        )
    # O1 canonical environment preflight stage marker: before any auth consumption side effects.
    from src.ops.canonical_runtime_environment_contract_v1.preflight_v1 import (
        collect_proxy_no_proxy_blockers_v1,
    )

    pre_auth_env = environ if environ is not None else (os.environ if use_real_network else {})
    pre_auth_blockers = collect_proxy_no_proxy_blockers_v1(pre_auth_env) if pre_auth_env else []
    if pre_auth_blockers:
        return ProductiveRunGateResultV1(
            ok=False,
            blockers=sorted(set(pre_auth_blockers)),
            notes=notes + ["O1_PREFLIGHT_BEFORE_AUTHORIZATION_CONSUMPTION"],
        )
    notes.append("O1_PREFLIGHT_BEFORE_AUTHORIZATION_CONSUMPTION")
    blockers = assert_productive_run_preconditions_v1(
        prereg=prereg,
        go=go,
        artifact=None,
        confirm_token=confirm_token,
        now_unix=now,
        expected_repository_sha=expected_repository_sha,
        use_real_network=use_real_network,
        environ=environ,
        previously_seen_fingerprints=previously_seen_fingerprints,
        artifact_path=artifact_path,
    )
    blockers = [b for b in blockers if b]
    if blockers:
        return ProductiveRunGateResultV1(ok=False, blockers=blockers, notes=notes)

    if transport is None:
        if not use_real_network:
            return ProductiveRunGateResultV1(
                ok=False,
                blockers=["TRANSPORT_OR_REAL_NETWORK_REQUIRED"],
                notes=notes,
            )
        transport, _telemetry = build_real_eea_public_md_transport_v1(
            environ=environ if environ is not None else os.environ,
            sleep=sleep or time.sleep,
        )
        notes.append("REAL_PUBLIC_MD_TRANSPORT_BOUND")
    else:
        notes.append("INJECTED_TRANSPORT_BOUND")

    # Lazy-open transport: WallclockSessionRuntimeV1 opens only after consume+lock.
    # Wrap open to record ordering evidence.
    evidence_root.mkdir(parents=True, exist_ok=True)
    prereg_fp = _fingerprint_payload(prereg.to_dict())
    auth_raw = json.loads(artifact_path.read_text(encoding="utf-8"))
    auth_fp = _fingerprint_payload(auth_raw if isinstance(auth_raw, dict) else {})
    consumed_at_box: dict[str, float] = {}
    transport_open_at_box: dict[str, float] = {}

    original_open = transport.open

    def _tracked_open() -> None:
        # Consumption record must already exist (runtime writes it before open).
        consumption_path = evidence_root / "authorization_consumption_record.json"
        if not consumption_path.is_file():
            raise RuntimeError("TRANSPORT_OPEN_BEFORE_CONSUMPTION_RECORD")
        transport_open_at_box["ts"] = float((clock_wall or time.time)())
        if consumed_at_box and transport_open_at_box["ts"] < consumed_at_box["ts"]:
            raise RuntimeError("TRANSPORT_BEFORE_CONSUMPTION")
        original_open()
        write_issuance_runtime_evidence_v1(
            evidence_root=evidence_root,
            session_id=go.session_id,
            preregistration_fingerprint=prereg_fp,
            authorization_fingerprint=auth_fp,
            confirm_token_fingerprint=fingerprint_confirm_token(confirm_token),
            consumed_at=float(consumed_at_box.get("ts") or (clock_wall or time.time)()),
            transport_open_at=transport_open_at_box["ts"],
            host=CANONICAL_HOST,
            method="GET",
            paths=["/api/v5/market/ticker"],
        )

    transport.open = _tracked_open  # type: ignore[method-assign]

    # Patch evidence writer indirectly: capture consume time via pre-existing file poll
    # inside tracked open. Also write a pre-run gate attestation (no network).
    gate_path = evidence_root / "productive_run_gate.json"
    gate_path.write_text(
        json.dumps(
            {
                "ok": True,
                "fixture_rejected": True,
                "scopes": {
                    "network_scope": NETWORK_SCOPE,
                    "session_execution_scope": SESSION_EXECUTION_SCOPE,
                },
                "use_real_network": use_real_network,
                "env_alone_insufficient": True,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    runtime = WallclockSessionRuntimeV1(
        evidence_root=evidence_root,
        transport=transport,
        config=runtime_config,
        clock_wall=clock_wall,
        clock_mono=clock_mono,
        sleep=sleep,
        repo_root=repo_root,
        stop_flag=stop_flag,
    )

    # Monkey-patch consume timing: wrap run by observing consumption file mtime after return
    # from internal consume — instead hook via wrapping evidence writer after first consume.
    original_run = runtime.run

    def _run_with_consume_mark(**kwargs: Any) -> WallclockSessionResultV1:
        # Intercept by wrapping transport open already; set consumed_at when consumption file appears
        # via a thin wrapper around consume inside session runtime is not exposed — use side channel:
        # before run, install a proxy on evidence writer write_immutable_json.
        writer = runtime.writer
        orig_write = writer.write_immutable_json

        def _write(name: str, payload: Mapping[str, Any]) -> Path:
            path = orig_write(name, payload)
            if name == "authorization_consumption_record.json":
                consumed_at_box["ts"] = float(
                    payload.get("consumed_at") or (clock_wall or time.time)()
                )
            return path

        writer.write_immutable_json = _write  # type: ignore[method-assign]
        return original_run(**kwargs)

    result = _run_with_consume_mark(
        prereg=prereg,
        go=go,
        confirm_token=confirm_token,
        artifact_path=artifact_path,
        expected_repository_sha=expected_repository_sha,
        fingerprint_ledger_path=fingerprint_ledger_path,
        known_session_ids=known_session_ids,
        runtime_overrides=runtime_overrides,
        config_snapshot={
            "schema": "productive_wallclock_runtime_v1",
            "capability_id": CAPABILITY_ID,
            "use_real_network": use_real_network,
        },
    )
    return ProductiveRunGateResultV1(
        ok=result.terminal_verdict in {"PASS", "ABORT"} or result.consumed,
        blockers=list(result.blockers),
        notes=notes + list(result.notes),
        network_opened=bool(result.network_opened),
        session_result=result.to_dict(),
    )


def run_productive_wallclock_session_from_paths_v1(
    *,
    preregistration_path: Path,
    operator_go_path: Path,
    authorization_artifact_path: Path,
    confirm_token: str,
    evidence_root: Path,
    expected_repository_sha: str,
    fingerprint_ledger_path: Path,
    transport: Optional[EeaPublicMdTransportV1] = None,
    use_real_network: bool = False,
    runtime_config: WallclockRuntimeConfigV1 | None = None,
    clock_wall: Callable[[], float] | None = None,
    clock_mono: Callable[[], float] | None = None,
    sleep: Callable[[float], None] | None = None,
    repo_root: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> ProductiveRunGateResultV1:
    prereg = parse_preregistration_contract_v1(
        load_preregistration_contract_dict_v1(preregistration_path)
    )
    go = parse_operator_go_contract_v1(load_operator_go_contract_dict_v1(operator_go_path))
    return run_productive_wallclock_session_v1(
        prereg=prereg,
        go=go,
        artifact=None,
        confirm_token=confirm_token,
        artifact_path=authorization_artifact_path,
        evidence_root=evidence_root,
        expected_repository_sha=expected_repository_sha,
        fingerprint_ledger_path=fingerprint_ledger_path,
        transport=transport,
        use_real_network=use_real_network,
        runtime_config=runtime_config,
        clock_wall=clock_wall,
        clock_mono=clock_mono,
        sleep=sleep,
        repo_root=repo_root,
        environ=environ,
    )
