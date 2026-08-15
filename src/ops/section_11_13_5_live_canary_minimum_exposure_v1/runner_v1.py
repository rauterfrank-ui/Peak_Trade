"""Runner for §11.13.5 LIVE_CANARY_MINIMUM_EXPOSURE (authoring/preflight; gated execute)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authorization_v1 import (
    LiveCanaryAuthorizationError,
    default_authorization_is_false_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.config_v1 import (
    LiveCanaryConfigError,
    example_incomplete_config_dict_v1,
    load_live_canary_config_v1,
)
from src.core.environment import LIVE_CONFIRM_TOKEN
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    BLOCKS_NEW_ENTRY,
    CANARY_SUBMIT_TRANSPORT_IMPLEMENTED,
    CANARY_SUBMIT_TRANSPORT_SCOPE,
    CAPABILITY_11_9_LIVE_CANARY_ACTIVATED,
    CAPABILITY_11_9_REMAINS_FIXTURE_ONLY,
    GENERAL_LIVE_SUBMIT_UNLOCKED,
    LIVE_AUTHORIZED,
    LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED,
    LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN,
    LIVE_RECONCILIATION_PROVEN,
    OWNER_GO_AUTHORING,
    OWNER_GO_EXECUTE,
    PACKAGE_MARKER,
    PREPARATION_SURFACE_READY,
    PRODUCTIVE_EXECUTE_PATH_READY,
    SUBMIT_UNLOCKED,
    TRANSPORT_CLASS_FORENSIC_SEALED_ONLY,
    TRANSPORT_CLASS_PREFLIGHT_NO_NETWORK,
    UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    seal_authoring_forensic_evidence_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.forensic_reconciliation_v1 import (
    classify_from_sealed_evidence_roots_v1,
    prove_forensic_classification_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    LiveCanaryCredentialError,
    build_file_secretref_vault_backend_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.lifecycle_v1 import (
    build_lifecycle_and_closeout_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_gates_v1 import (
    evaluate_canary_submit_gates_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_transport_v1 import (
    LiveCanarySubmitTransportError,
    run_canary_submit_transport_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.trade_permission_forensic_v1 import (
    build_trade_permission_forensic_v1,
)


class LiveCanaryRunnerError(RuntimeError):
    """Fail-closed runner violation."""


@dataclass(frozen=True)
class LiveCanaryRunnerResultV1:
    ok: bool
    mode: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        out = dict(self.payload)
        out["ok"] = self.ok
        out["mode"] = self.mode
        out["PACKAGE_MARKER"] = PACKAGE_MARKER
        return out


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_section_11_13_5_live_canary_minimum_exposure_v1(
    *,
    mode: str,
    config_payload: Mapping[str, Any] | None = None,
    origin_main_sha: str,
    executed_code_sha: str | None = None,
    owner_go: str | None = None,
    live_canary_authorized: bool | None = None,
    evidence_run_root: str | None = None,
    permission_attestation: Mapping[str, Any] | None = None,
    live_enabled: bool = False,
    live_armed: bool = False,
    confirm_token: str | None = None,
    owner_go_consumed: bool = False,
    seal_forensic_evidence: bool = False,
    transport: Any = None,
    allow_productive_wire_send: bool = False,
    vault_backend: Any = None,
    vault_file: str | None = None,
    live_canary_cybersecurity_gate: str = "PASS",
) -> LiveCanaryRunnerResultV1:
    mode_norm = str(mode or "").strip().lower()
    if mode_norm not in {"preflight", "forensic", "execute"}:
        raise LiveCanaryRunnerError(f"UNKNOWN_MODE:{mode}")

    if CAPABILITY_11_9_LIVE_CANARY_ACTIVATED or not CAPABILITY_11_9_REMAINS_FIXTURE_ONLY:
        raise LiveCanaryRunnerError("CAPABILITY_11_9_MUST_REMAIN_FIXTURE_ONLY")
    if LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN or LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED:
        raise LiveCanaryRunnerError("PACKAGE_PROVEN_EXECUTED_FLAGS_MUST_REMAIN_FALSE")
    if LIVE_AUTHORIZED:
        raise LiveCanaryRunnerError("LIVE_AUTHORIZED_MUST_REMAIN_FALSE")
    if GENERAL_LIVE_SUBMIT_UNLOCKED or SUBMIT_UNLOCKED:
        raise LiveCanaryRunnerError("GENERAL_LIVE_SUBMIT_UNLOCK_FORBIDDEN")
    if not CANARY_SUBMIT_TRANSPORT_IMPLEMENTED:
        raise LiveCanaryRunnerError("CANARY_SUBMIT_TRANSPORT_NOT_IMPLEMENTED")
    if CANARY_SUBMIT_TRANSPORT_SCOPE != "SECTION_11_13_5_LIVE_CANARY_MINIMUM_EXPOSURE_ONLY":
        raise LiveCanaryRunnerError("CANARY_SUBMIT_TRANSPORT_SCOPE_DRIFT")
    if not PREPARATION_SURFACE_READY or not PRODUCTIVE_EXECUTE_PATH_READY:
        raise LiveCanaryRunnerError("PREPARATION_OR_EXECUTE_PATH_NOT_READY")
    if not default_authorization_is_false_v1():
        raise LiveCanaryRunnerError("DEFAULT_AUTHORIZATION_MUST_BE_FALSE")

    cfg_payload = dict(config_payload or example_incomplete_config_dict_v1())
    try:
        cfg = load_live_canary_config_v1(
            cfg_payload,
            require_execute_fields=(mode_norm == "execute"),
        )
    except LiveCanaryConfigError as exc:
        raise LiveCanaryRunnerError(str(exc)) from exc

    repo = _repo_root()
    forensic = prove_forensic_classification_contract_v1(repo_root=repo)
    trade = build_trade_permission_forensic_v1()
    lifecycle = build_lifecycle_and_closeout_contract_v1()

    # Standing gates remain blocking until Owner adoption + TRADE attestation + execute GO.
    gate = evaluate_canary_submit_gates_v1(
        owner_go=owner_go,
        owner_go_consumed=owner_go_consumed,
        authorization_scope=AUTHORIZATION_SCOPE if owner_go else None,
        bound_origin_main_sha=origin_main_sha,
        expected_origin_main_sha=origin_main_sha,
        live_canary_authorized=bool(live_canary_authorized),
        live_enabled=live_enabled,
        live_armed=live_armed,
        confirm_token=confirm_token,
        blocks_new_entry=BLOCKS_NEW_ENTRY,
        unresolved_economic_divergence=UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY,
        live_reconciliation_proven=LIVE_RECONCILIATION_PROVEN,
        permission_attestation=permission_attestation or trade["PRIOR_PERMISSION_ATTESTATION"],
        environment=str(cfg.payload.get("environment") or "LIVE"),
        fixture_or_demo_or_testnet=False,
        max_notional=str(cfg.payload.get("max_notional") or "") or None,
        min_executable_notional=None,
        order_count=1,
        position_count=0,
        exposure_above_minimum_bound=False,
    )

    if mode_norm == "execute":
        if str(owner_go or "") == OWNER_GO_AUTHORING:
            raise LiveCanaryRunnerError("AUTHORING_GO_CANNOT_EXECUTE_CANARY")
        backend = vault_backend
        if backend is None:
            if not str(vault_file or "").strip():
                raise LiveCanaryRunnerError("EXECUTE_REQUIRES_VAULT_FILE")
            try:
                backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
            except LiveCanaryCredentialError as exc:
                raise LiveCanaryRunnerError(str(exc)) from exc
        try:
            execute_payload = run_canary_submit_transport_v1(
                cfg=cfg,
                origin_main_sha=origin_main_sha,
                owner_go=owner_go,
                live_canary_authorized=bool(live_canary_authorized),
                live_enabled=live_enabled,
                live_armed=live_armed,
                confirm_token=confirm_token,
                owner_go_consumed=owner_go_consumed,
                permission_attestation=permission_attestation
                or trade["PRIOR_PERMISSION_ATTESTATION"],
                transport=transport,
                allow_productive_wire_send=allow_productive_wire_send,
                live_canary_cybersecurity_gate=live_canary_cybersecurity_gate,
                vault_backend=backend,
            )
        except (LiveCanarySubmitTransportError, Exception) as exc:  # noqa: BLE001
            raise LiveCanaryRunnerError(str(exc)) from exc
        execute_payload["forensic"] = forensic
        execute_payload["trade_permission_forensic"] = trade
        execute_payload["lifecycle_contract"] = lifecycle
        execute_payload["LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN"] = False
        execute_payload["LIVE_AUTHORIZED"] = False
        execute_payload["OWNER_GO_CONSUMED"] = False
        return LiveCanaryRunnerResultV1(
            ok=bool(execute_payload.get("ok")),
            mode=mode_norm,
            payload=execute_payload,
        )

    claims = {
        "mode": mode_norm,
        "LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN": False,
        "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED": False,
        "LIVE_AUTHORIZED": False,
        "LIVE_RECONCILIATION_PROVEN": False,
        "BLOCKS_NEW_ENTRY": True,
        "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY": True,
        "TRADE_ATTESTATION": False,
        "PRODUCTIVE_CANARY_SURFACE_READY": True,
        "PREPARATION_SURFACE_READY": True,
        "PRODUCTIVE_EXECUTE_PATH_READY": True,
        "CAPABILITY_11_9_REMAINS_FIXTURE_ONLY": True,
        "ORDER_EFFECT": "NONE",
        "ACCOUNT_MUTATION_EFFECT": "NONE",
        "NETWORK_EFFECT": (
            TRANSPORT_CLASS_FORENSIC_SEALED_ONLY
            if mode_norm == "forensic"
            else TRANSPORT_CLASS_PREFLIGHT_NO_NETWORK
        ),
        "SECRET_VALUE_ACCESS": "NONE",
        "WRITE_REQUEST_COUNT": 0,
        "ORDER_REQUEST_COUNT": 0,
        "origin_main_sha": origin_main_sha,
        "executed_code_sha": executed_code_sha or origin_main_sha,
        "owner_go_observed": owner_go,
        "OWNER_GO_EXECUTE": OWNER_GO_EXECUTE,
        "OWNER_GO_AUTHORING": OWNER_GO_AUTHORING,
        "SUBMIT_ALLOWED": gate.submit_allowed,
        "SUBMIT_BLOCK_REASONS": list(gate.reasons),
    }
    summary = {
        "PACKAGE_MARKER": PACKAGE_MARKER,
        "FORENSIC_OK": True,
        "TRADE_ATTESTATION": False,
        "PRODUCTIVE_CANARY_SURFACE_READY": True,
        "LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN": False,
        "LIVE_RECONCILIATION_PROVEN": False,
        "BLOCKS_NEW_ENTRY": True,
    }

    sealed = None
    if seal_forensic_evidence:
        if not evidence_run_root:
            raise LiveCanaryRunnerError("EVIDENCE_ROOT_REQUIRED_TO_SEAL")
        sealed = seal_authoring_forensic_evidence_v1(
            evidence_root=evidence_run_root,
            forensic=forensic,
            trade_forensic=trade,
            submit_gate=gate.to_dict(),
            claims=claims,
            summary=summary,
            config_digest={
                "config_digest": cfg.digest(),
                "config_version": cfg.payload.get("config_version"),
            },
        )

    return LiveCanaryRunnerResultV1(
        ok=True,
        mode=mode_norm,
        payload={
            "forensic": forensic,
            "trade_permission_forensic": trade,
            "lifecycle_contract": lifecycle,
            "submit_gate": gate.to_dict(),
            "claims": claims,
            "summary": summary,
            "sealed_evidence": sealed,
            "config_digest": cfg.digest(),
            "classify_helper_ok": bool(
                classify_from_sealed_evidence_roots_v1(repo_root=repo).get("ok")
            ),
        },
    )


def assert_execute_refuses_authoring_go_v1() -> None:
    try:
        run_section_11_13_5_live_canary_minimum_exposure_v1(
            mode="execute",
            origin_main_sha="0f21b53e001e94085941c774a43a27562a1743fe",
            owner_go=OWNER_GO_AUTHORING,
            live_canary_authorized=True,
            permission_attestation={"READ": True, "TRADE": True, "WITHDRAW": False},
            live_enabled=True,
            live_armed=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
    except LiveCanaryRunnerError as exc:
        text = str(exc)
        if any(
            marker in text
            for marker in (
                "AUTHORING_GO",
                "CANARY_SUBMIT_HARD_BLOCKED",
                "EXECUTE_FIELD_REQUIRED",
            )
        ):
            return
        raise
    raise LiveCanaryRunnerError("AUTHORING_GO_EXECUTE_SHOULD_HAVE_FAILED")


__all__ = [
    "LiveCanaryRunnerError",
    "LiveCanaryRunnerResultV1",
    "LiveCanaryAuthorizationError",
    "assert_execute_refuses_authoring_go_v1",
    "run_section_11_13_5_live_canary_minimum_exposure_v1",
]
