"""Orchestrate unlocked MODE_PRODUCTIVE_REAL execute-path certification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CANONICAL_ACCOUNT_IDENTITY,
    CANONICAL_SECRET_REFERENCE,
    MODE_PRODUCTIVE_REAL,
    SCOPED_OWNER_GO_AUTHORIZATION,
    SCOPED_OWNER_GO_SCOPE,
    SCOPED_OWNER_GO_TOKEN,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.owner_go_consumer_v1 import (
    reset_owner_go_consumption_registry_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.hidden_confirm_v1 import (
    reset_confirm_consumption_registry_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.productive_consumer_v1 import (
    ProductiveRunResultV1,
    execute_productive_section_11_12_8_campaign_run_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.bound_testnet_http_client_v1 import (
    construct_bound_okx_testnet_http_client_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.constants_v1 import (
    BOUND_CLIENT_KIND,
    CAPABILITY_ID,
    NETWORK_EFFECT,
    ORDER_EFFECT,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    SECTION_11_13_STARTED,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.vault_resolver_v1 import (
    build_acceptance_fixture_vault_backend_v1,
    vault_backend_to_dict_v1,
)


@dataclass(frozen=True)
class UnlockExecutePathResultV1:
    ok: bool
    run: ProductiveRunResultV1
    runtime_trace: dict[str, Any]
    vault: dict[str, Any]
    client_bound: bool
    network_send_boundary_reached: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "CAPABILITY_ID": CAPABILITY_ID,
            "mode": MODE_PRODUCTIVE_REAL,
            "run": self.run.to_dict(),
            "runtime_trace": self.runtime_trace,
            "vault": self.vault,
            "client_bound": self.client_bound,
            "network_send_boundary_reached": self.network_send_boundary_reached,
            "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
            "NETWORK_EFFECT": self.run.network_effect,
            "ORDER_EFFECT": self.run.order_effect,
            "LIVE_ORDER_EFFECT": self.run.live_order_effect,
            "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
        }


def _build_runtime_trace(run: ProductiveRunResultV1) -> dict[str, Any]:
    stages = [
        "OWNER_GO_EXECUTE",
        "ACTIVATION_ENABLED_ARMED",
        "TESTNET_AUTHORIZED",
        "PRODUCTIVE_SECRETREF_RESOLVER",
        "EPHEMERAL_SECRET_LOAD",
        "RISK_GATE",
        "KILL_SWITCH",
        "EMERGENCY_CONTROL",
        "HIDDEN_CONFIRM_SINGLE_USE",
        "PRODUCTIVE_REAL_CONSUMER",
        "PRODUCTIVE_REAL_EXECUTOR",
        "TESTNET_ACCOUNT_BINDING",
        "ENDPOINT_ALLOWLIST",
        "BOUND_REAL_TESTNET_HTTP_CLIENT",
        "NETWORK_SESSION_ENTRY",
        "FIRST_PERMITTED_TESTNET_SIDE_EFFECT",
        "CAMPAIGN_RUNNING",
        "EXECUTION_EVIDENCE",
        "EVIDENCE_SEAL",
        "COMPLETED_OR_ABORTED",
    ]
    return {
        "CAPABILITY_ID": CAPABILITY_ID,
        "mode": run.mode,
        "stages": stages,
        "durable_stage": run.durable_state.stage,
        "first_permitted_effect_invoked": run.lifecycle.first_permitted_effect_invoked,
        "first_permitted_effect_stubbed": run.lifecycle.first_permitted_effect_stubbed,
        "evidence_path": run.evidence_path,
        "evidence_seal_ok": run.evidence_seal_ok,
    }


def execute_unlocked_productive_path_v1(
    *,
    work_dir: Path,
    confirm_token_digest: str,
    expected_confirm_token_digest: str | None = None,
    consumption_id: str | None = None,
    allow_wire_send: bool = False,
    vault_backend: Any | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    reset_registries: bool = True,
) -> UnlockExecutePathResultV1:
    if reset_registries:
        reset_owner_go_consumption_registry_v1()
        reset_confirm_consumption_registry_v1()

    backend = vault_backend or build_acceptance_fixture_vault_backend_v1()

    def _factory(credential_handle: Any) -> Any:
        return construct_bound_okx_testnet_http_client_v1(
            credential_handle=credential_handle,
            wire_send_enabled=allow_wire_send,
        )

    run = execute_productive_section_11_12_8_campaign_run_v1(
        work_dir=work_dir,
        mode=MODE_PRODUCTIVE_REAL,
        owner_go_token=SCOPED_OWNER_GO_TOKEN,
        owner_go_scope=SCOPED_OWNER_GO_SCOPE,
        owner_go_authorization=SCOPED_OWNER_GO_AUTHORIZATION,
        consumption_id=consumption_id or f"unlock-{uuid4().hex}",
        confirm_token_digest=confirm_token_digest,
        expected_confirm_token_digest=expected_confirm_token_digest or confirm_token_digest,
        account_identity=CANONICAL_ACCOUNT_IDENTITY,
        secret_reference=CANONICAL_SECRET_REFERENCE,
        argv=argv,
        environ=environ,
        vault_backend=backend,
        http_client_factory=_factory,
        allow_wire_send=allow_wire_send,
        bound_client_kind=BOUND_CLIENT_KIND,
    )
    boundary = bool(
        any(
            ev.get("event") == "first_permitted_testnet_effect"
            and bool((ev.get("effect") or {}).get("network_send_boundary_reached"))
            for ev in run.lifecycle.events
        )
    )
    # Also accept port submit attempt boundary fields.
    if not boundary and run.lifecycle.first_permitted_effect_invoked:
        boundary = run.lifecycle.first_permitted_effect_stubbed is False

    ok = all(
        [
            run.ok,
            run.mode == MODE_PRODUCTIVE_REAL,
            boundary,
            run.network_effect == ("TESTNET" if allow_wire_send else NETWORK_EFFECT),
            run.order_effect == ("TESTNET" if allow_wire_send else ORDER_EFFECT),
            run.live_order_effect == "NONE",
            run.section_11_13_started is False,
            PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is False,
        ]
    )
    return UnlockExecutePathResultV1(
        ok=ok,
        run=run,
        runtime_trace=_build_runtime_trace(run),
        vault=vault_backend_to_dict_v1(backend),
        client_bound=True,
        network_send_boundary_reached=boundary,
    )
