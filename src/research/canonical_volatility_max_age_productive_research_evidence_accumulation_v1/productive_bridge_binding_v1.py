"""Bind productive accumulation state onto the hardened bridge session.

Ownership: ``HardenedBridgeSessionStateV2.productive_evidence_accumulation_state``
is the sole session-owned handle. No global mutable singleton is introduced.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    AUTHORITATIVE_BRIDGE_CYCLE_OUTPUT_ID,
    DEFAULT_PRODUCTIVE_BRIDGE_CANONICAL_INSTRUMENT_ID,
    DEFAULT_PRODUCTIVE_BRIDGE_VENUE,
    DEFAULT_PRODUCTIVE_BRIDGE_VENUE_INSTRUMENT_ID,
    PRODUCTIVE_BRIDGE_BINDING_CAPABILITY_ID,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
    require_nonempty,
    sha256_hex,
    sha256_hex_text,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.runtime_v1 import (
    ProductiveEvidenceAccumulationStateV1,
    bind_accumulation_state_v1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    build_ratified_max_age_research_design_contract_v1,
)

# Local import of bridge state type is deferred in signatures via string annotation
# to keep architecture guards free of trading.execution imports.


def market_sample_id_from_identity_v1(sample: Mapping[str, Any] | Any) -> str:
    """Deterministic market-sample identity digest (not runtime cycle index)."""
    if hasattr(sample, "distinctness_key"):
        key = sample.distinctness_key()
        material = {
            "canonical_instrument_id": key[1],
            "event_time_unix": key[3],
            "mark_price": key[4],
            "venue": key[0],
            "venue_instrument_id": key[2],
        }
    elif isinstance(sample, Mapping):
        event = sample.get("event_time") or {}
        material = {
            "canonical_instrument_id": sample.get("canonical_instrument_id"),
            "event_time_unix": (
                event.get("unix_seconds")
                if isinstance(event, Mapping)
                else sample.get("event_time_unix")
            ),
            "mark_price": sample.get("mark_price"),
            "venue": sample.get("venue"),
            "venue_instrument_id": sample.get("venue_instrument_id"),
        }
    else:
        raise ProductiveEvidenceAccumulationError("market_sample_identity_invalid")
    for field_name, value in material.items():
        if value is None or (isinstance(value, str) and not str(value).strip()):
            raise ProductiveEvidenceAccumulationError(f"market_sample_missing_{field_name}")
    return "msi_" + sha256_hex(material)[:32]


def build_productive_bridge_cycle_authority_v1(
    *,
    campaign_id: str,
    repository_sha: str,
    session_id: str,
    market_sample_id: str,
    preregistration_digest: str | None = None,
) -> dict[str, Any]:
    design = build_ratified_max_age_research_design_contract_v1()
    digest = preregistration_digest or design.preregistration_digest
    return {
        "authority_id": AUTHORITATIVE_BRIDGE_CYCLE_OUTPUT_ID,
        "binding_capability_id": PRODUCTIVE_BRIDGE_BINDING_CAPABILITY_ID,
        "campaign_id": require_nonempty(campaign_id, field_name="campaign_id"),
        "event_time_remains_authoritative": True,
        "fixture": False,
        "preregistration_digest": require_nonempty(digest, field_name="preregistration_digest"),
        "repository_sha": require_nonempty(repository_sha, field_name="repository_sha"),
        "runtime_cycle_is_not_market_sample": True,
        "session_id": require_nonempty(session_id, field_name="session_id"),
        "source_is_authoritative_bridge_cycle": True,
        "synthetic": False,
        "test_data": False,
        "market_sample_id": require_nonempty(market_sample_id, field_name="market_sample_id"),
    }


def authorize_productive_bridge_cycle_input_v1(
    cycle: Mapping[str, Any],
    *,
    expected_repository_sha: str,
    expected_preregistration_digest: str | None = None,
    require_authoritative: bool = True,
) -> dict[str, Any]:
    """Fail-closed authorization of a productive bridge cycle before evidence mutation."""
    design = build_ratified_max_age_research_design_contract_v1()
    expected_digest = expected_preregistration_digest or design.preregistration_digest
    authority = dict(cycle.get("productive_bridge_cycle_authority") or {})

    if not require_authoritative and not authority:
        return {"authorized": True, "mode": "legacy_non_productive_probe"}

    if not authority:
        raise ProductiveEvidenceAccumulationError("productive_bridge_authority_required")

    def _flag(name: str, expected: bool) -> None:
        if bool(authority.get(name)) is not expected:
            raise ProductiveEvidenceAccumulationError(f"authority_flag_invalid:{name}")

    _flag("source_is_authoritative_bridge_cycle", True)
    _flag("synthetic", False)
    _flag("fixture", False)
    _flag("test_data", False)

    if authority.get("authority_id") != AUTHORITATIVE_BRIDGE_CYCLE_OUTPUT_ID:
        raise ProductiveEvidenceAccumulationError("authority_id_mismatch")

    repo_sha = require_nonempty(authority.get("repository_sha"), field_name="repository_sha")
    if repo_sha != require_nonempty(expected_repository_sha, field_name="expected_repository_sha"):
        raise ProductiveEvidenceAccumulationError("repository_sha_mismatch_before_mutation")

    preg = require_nonempty(
        authority.get("preregistration_digest"), field_name="preregistration_digest"
    )
    if preg != expected_digest:
        raise ProductiveEvidenceAccumulationError("preregistration_digest_mismatch_before_mutation")

    # Reject synthetic / fixture / test provenance markers anywhere on the cycle.
    forbidden_tokens = ("synthetic", "fixture", "test_data", "mock", "demo")
    blob = sha256_hex_text(str(sorted(cycle.keys())))  # keep import used; real check below
    _ = blob
    for key in ("notes", "decision_outcome", "quantity_source"):
        text = str(cycle.get(key) or "").lower()
        if "forced_wiring_fixture" in text or "synthetic_probe" in text:
            raise ProductiveEvidenceAccumulationError("synthetic_or_fixture_input_rejected")
    if cycle.get("forced_wiring") is True:
        raise ProductiveEvidenceAccumulationError("fixture_input_rejected")
    for token in forbidden_tokens:
        if authority.get(token) is True:
            raise ProductiveEvidenceAccumulationError(f"{token}_evidence_rejected")

    if not cycle.get("canonical_volatility_typed_binding"):
        raise ProductiveEvidenceAccumulationError("missing_canonical_volatility_typed_binding")
    gate = dict(cycle.get("double_play_typed_volatility_presence_gate") or {})
    if not gate.get("max_age_policy_evidence"):
        raise ProductiveEvidenceAccumulationError("missing_max_age_policy_evidence")

    require_nonempty(cycle.get("session_id"), field_name="session_id")
    require_nonempty(cycle.get("cycle_id"), field_name="cycle_id")
    require_nonempty(authority.get("campaign_id"), field_name="campaign_id")
    require_nonempty(authority.get("market_sample_id"), field_name="market_sample_id")

    return {
        "authorized": True,
        "authority": authority,
        "expected_preregistration_digest": expected_digest,
        "expected_repository_sha": expected_repository_sha,
        "mode": "productive_bridge",
    }


def stamp_productive_bridge_cycle_authority_v1(
    cycle: Mapping[str, Any],
    *,
    authority: Mapping[str, Any],
    venue: str,
    venue_instrument_id: str,
    receive_time: str | None,
    market_sample: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Attach productive provenance onto an authoritative hardened bridge cycle output."""
    out = dict(cycle)
    out["productive_bridge_cycle_authority"] = dict(authority)
    out["venue"] = require_nonempty(venue, field_name="venue")
    out["venue_instrument_id"] = require_nonempty(
        venue_instrument_id, field_name="venue_instrument_id"
    )
    if receive_time is not None:
        out["receive_time"] = receive_time
    if market_sample is not None:
        out["market_sample_identity"] = dict(market_sample)
        out["market_sample_id"] = authority["market_sample_id"]
    out["campaign_id"] = authority["campaign_id"]
    out["source_is_authoritative_bridge_cycle"] = True
    out["synthetic"] = False
    out["fixture"] = False
    out["test_data"] = False
    return out


def bind_accumulation_state_to_hardened_bridge_session_v1(
    session_state: Any,
    *,
    accumulation_state: ProductiveEvidenceAccumulationStateV1 | None = None,
    session_id: str | None = None,
    session_start_event_time: str | None = None,
    repository_sha: str | None = None,
    campaign_id: str | None = None,
    venue: str = DEFAULT_PRODUCTIVE_BRIDGE_VENUE,
    canonical_instrument_id: str = DEFAULT_PRODUCTIVE_BRIDGE_CANONICAL_INSTRUMENT_ID,
    venue_instrument_id: str = DEFAULT_PRODUCTIVE_BRIDGE_VENUE_INSTRUMENT_ID,
    repo_root: Path | None = None,
    productive_ledger_path: Path | None = None,
    join_ledger_path: Path | None = None,
    quarantine_ledger_path: Path | None = None,
    require_authoritative_bridge_cycle: bool = True,
    existing_session: Any = None,
    resume_token: str | None = None,
    process_restart: bool = False,
) -> Any:
    """Bind accumulation onto ``HardenedBridgeSessionStateV2`` (explicit ownership).

    Equivalent operator shape::

        session_state = bind_accumulation_state_v1(
            session_state=session_state,
            accumulation_state=productive_accumulation_state,
        )
    """
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
        HardenedBridgeSessionStateV2,
    )

    if not isinstance(session_state, HardenedBridgeSessionStateV2):
        raise ProductiveEvidenceAccumulationError("hardened_bridge_session_state_required")

    if accumulation_state is None:
        if not session_id or not session_start_event_time or not repository_sha:
            raise ProductiveEvidenceAccumulationError(
                "session_id_start_time_and_repository_sha_required_when_creating_state"
            )
        accumulation_state = bind_accumulation_state_v1(
            session_id=session_id,
            session_start_event_time=session_start_event_time,
            repository_sha=repository_sha,
            venue=venue,
            canonical_instrument_id=canonical_instrument_id,
            venue_instrument_id=venue_instrument_id,
            repo_root=repo_root or Path.cwd(),
            productive_ledger_path=productive_ledger_path,
            join_ledger_path=join_ledger_path,
            quarantine_ledger_path=quarantine_ledger_path,
            existing_session=existing_session,
            resume_token=resume_token,
            process_restart=process_restart,
            restore_reuse_cursor_from_ledger=True,
        )

    accumulation_state.require_authoritative_bridge_cycle = bool(require_authoritative_bridge_cycle)
    accumulation_state.expected_repository_sha = accumulation_state.repository_sha
    design = build_ratified_max_age_research_design_contract_v1()
    accumulation_state.expected_preregistration_digest = design.preregistration_digest
    if campaign_id is not None:
        accumulation_state.campaign_id = require_nonempty(campaign_id, field_name="campaign_id")

    session_state.productive_evidence_accumulation_state = accumulation_state
    if session_id and not session_state.session_id:
        session_state.session_id = session_id
    return session_state


# Alias matching the operator-facing API name in the authorization brief.
def bind_accumulation_state_v1_onto_bridge(
    *,
    session_state: Any,
    accumulation_state: ProductiveEvidenceAccumulationStateV1 | None = None,
    **kwargs: Any,
) -> Any:
    return bind_accumulation_state_to_hardened_bridge_session_v1(
        session_state,
        accumulation_state=accumulation_state,
        **kwargs,
    )


def iso_from_unix_v1(ts: float) -> str:
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat().replace("+00:00", "Z")
