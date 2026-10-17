"""Offline fixtures for CURRENT productive POST-path safety gates (tests only).

Kill-switch evidence is produced by writing a real state file under ``tmp_path``
and reading it through the CURRENT reader; nothing fabricates TRUSTED_PRESENT.
Global ledgers live under ``tmp_path``; the canonical per-user ledger root is
refused under pytest.
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_global_venue_effect_authority_ledger_v1 import (
    GlobalVenueEffectAuthorityLedgerV1,
    GlobalVenueEffectClaimV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    POST_OWNER_GO,
    build_global_venue_effect_identity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_path_kill_switch_gate_v1 import (
    PostPathKillSwitchEvidenceV1,
    read_post_path_kill_switch_evidence_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_risk_reduction_venue_proof_v1 import (
    RiskReductionVenueProofV1,
    prove_risk_reduction_from_venue_evidence_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    expected_permit_identity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
)
from src.ops.gates import risk_gate
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState

KILL_SWITCH_ENV = "PEAK_KILL_SWITCH_STATE_PATH"
KILL_SWITCH_ENV_ALT = "PEAKTRADE_KILL_SWITCH_STATE_PATH"
TEST_BASELINE_SHA = "ab" * 20


def write_kill_switch_state_v1(
    path: Path, *, state: str = "ACTIVE", raw: str | None = None
) -> Path:
    """Valid enum states go through the CURRENT ``StatePersistence`` writer."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        path.write_text(raw, encoding="utf-8")
    elif state in KillSwitchState.__members__:
        StatePersistence(str(path), backup_dir=str(path.parent / "backups")).save(
            KillSwitchState[state]
        )
    else:
        path.write_text(json.dumps({"state": state}) + "\n", encoding="utf-8")
    return path


def isolate_kill_switch_state_root_v1(monkeypatch: pytest.MonkeyPatch, root: Path) -> Path:
    """Explicitly re-anchor the canonical kill-switch path under ``root`` for this test.

    Writer and every reader keep resolving through ``canonical_kill_switch_state_path``;
    nothing outside this in-process injection (env, pytest import) can redirect it.
    """
    monkeypatch.delenv(KILL_SWITCH_ENV, raising=False)
    monkeypatch.delenv(KILL_SWITCH_ENV_ALT, raising=False)
    monkeypatch.setattr(risk_gate, "_KILL_SWITCH_STATE_ROOT", root.resolve())
    return Path(risk_gate.canonical_kill_switch_state_path())


def activate_isolated_kill_switch_state_v1(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    state: str = "ACTIVE",
) -> Path:
    path = isolate_kill_switch_state_root_v1(monkeypatch, tmp_path / "kill_switch_fixture")
    return write_kill_switch_state_v1(path, state=state)


def kill_switch_evidence_from_state_v1(
    tmp_path: Path, *, state: str = "ACTIVE"
) -> PostPathKillSwitchEvidenceV1:
    path = write_kill_switch_state_v1(
        tmp_path / "kill_switch_evidence_fixture" / f"{state.lower()}.json", state=state
    )
    return read_post_path_kill_switch_evidence_v1(state_path=path)


def trusted_active_kill_switch_evidence_v1(tmp_path: Path) -> PostPathKillSwitchEvidenceV1:
    evidence = kill_switch_evidence_from_state_v1(tmp_path, state="ACTIVE")
    assert evidence.evidence_status == "TRUSTED_PRESENT", evidence
    assert evidence.blocked is False
    return evidence


def fresh_trusted_active_kill_switch_evidence_v1() -> PostPathKillSwitchEvidenceV1:
    """Fresh real read of an ACTIVE state file in a new private temp dir."""
    return trusted_active_kill_switch_evidence_v1(Path(tempfile.mkdtemp(prefix="pt_ks_fixture_")))


def isolated_global_ledger_v1(tmp_path: Path) -> GlobalVenueEffectAuthorityLedgerV1:
    return GlobalVenueEffectAuthorityLedgerV1(root=tmp_path / "global_venue_effect_ledger")


def claim_for_join_v1(
    ledger: GlobalVenueEffectAuthorityLedgerV1,
    envelope: FinalOrderEnvelopeV1,
    *,
    owner_go: str = POST_OWNER_GO,
    baseline_origin_main_sha: str = TEST_BASELINE_SHA,
) -> GlobalVenueEffectClaimV1:
    identity = build_global_venue_effect_identity_v1(
        ledger=ledger,
        envelope=envelope,
        permit_id=expected_permit_identity_v1(envelope, authority_ref=owner_go).permit_id,
        post_owner_go=owner_go,
        baseline_origin_main_sha=baseline_origin_main_sha,
    )
    return ledger.claim_v1(identity)


def rr_venue_payloads_v1(
    envelope: FinalOrderEnvelopeV1,
    *,
    pos_mode: str = "net_mode",
    pos: str | None = None,
    pos_side: str | None = None,
    extra_position_rows: list[dict[str, Any]] | None = None,
    pending_rows: list[dict[str, Any]] | None = None,
    uid: str = "fixture-uid-0001",
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Venue payloads in which ``envelope`` strictly reduces the open position."""
    side = str(envelope.side).lower()
    qty = str(envelope.quantity)
    if pos_mode == "net_mode":
        signed = pos if pos is not None else (qty if side == "sell" else f"-{qty}")
        row_side = pos_side if pos_side is not None else "net"
    else:
        signed = pos if pos is not None else qty
        row_side = pos_side if pos_side is not None else str(envelope.pos_side or "long")
    rows: list[dict[str, Any]] = [
        {
            "instId": envelope.instrument_id,
            "pos": signed,
            "posSide": row_side,
            "mgnMode": envelope.td_mode,
        }
    ]
    rows.extend(extra_position_rows or [])
    config = {"code": "0", "data": [{"posMode": pos_mode, "uid": uid}]}
    positions = {"code": "0", "data": rows}
    pending = {"code": "0", "data": list(pending_rows or [])}
    return config, positions, pending


def risk_reduction_proof_for_envelope_v1(
    envelope: FinalOrderEnvelopeV1,
    *,
    observed_at_epoch_s: float | None = None,
    **payload_kw: Any,
) -> RiskReductionVenueProofV1:
    config, positions, pending = rr_venue_payloads_v1(envelope, **payload_kw)
    return prove_risk_reduction_from_venue_evidence_v1(
        envelope=envelope,
        config_payload=config,
        positions_payload=positions,
        pending_orders_payload=pending,
        observed_at_epoch_s=time.time() if observed_at_epoch_s is None else observed_at_epoch_s,
    )


def isolated_join_safety_kwargs_v1(
    envelope: FinalOrderEnvelopeV1,
    *,
    ledger: GlobalVenueEffectAuthorityLedgerV1 | None = None,
    owner_go: str = POST_OWNER_GO,
) -> dict[str, Any]:
    """Join safety kwargs on a private ledger (one global identity per call)."""
    use = (
        ledger
        if ledger is not None
        else isolated_global_ledger_v1(Path(tempfile.mkdtemp(prefix="pt_join_ledger_")))
    )
    return {
        "global_authority_ledger": use,
        "global_claim": claim_for_join_v1(use, envelope, owner_go=owner_go),
        "risk_reduction_proof": (
            risk_reduction_proof_for_envelope_v1(envelope) if envelope.reduce_only else None
        ),
    }


def join_with_isolated_post_path_safety_v1(join_fn: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap the one-shot join so legacy test calls supply ledger/claim/RR proof explicitly."""

    def _call(**kwargs: Any) -> Any:
        if "global_authority_ledger" not in kwargs:
            kwargs.update(
                isolated_join_safety_kwargs_v1(
                    kwargs["envelope"], owner_go=str(kwargs.get("post_owner_go") or POST_OWNER_GO)
                )
            )
        return join_fn(**kwargs)

    return _call


def execute_with_isolated_global_ledger_v1(execute_fn: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap execute so each legacy test call uses a private global ledger root."""

    def _call(*args: Any, **kwargs: Any) -> Any:
        if kwargs.get("global_authority_ledger") is None:
            kwargs["global_authority_ledger"] = isolated_global_ledger_v1(
                Path(tempfile.mkdtemp(prefix="pt_execute_ledger_"))
            )
        return execute_fn(*args, **kwargs)

    return _call


__all__ = [
    "KILL_SWITCH_ENV",
    "TEST_BASELINE_SHA",
    "activate_isolated_kill_switch_state_v1",
    "claim_for_join_v1",
    "execute_with_isolated_global_ledger_v1",
    "isolated_join_safety_kwargs_v1",
    "join_with_isolated_post_path_safety_v1",
    "fresh_trusted_active_kill_switch_evidence_v1",
    "isolate_kill_switch_state_root_v1",
    "isolated_global_ledger_v1",
    "kill_switch_evidence_from_state_v1",
    "risk_reduction_proof_for_envelope_v1",
    "rr_venue_payloads_v1",
    "trusted_active_kill_switch_evidence_v1",
    "write_kill_switch_state_v1",
]
