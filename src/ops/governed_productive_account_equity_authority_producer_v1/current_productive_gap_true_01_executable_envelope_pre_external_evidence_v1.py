"""GAP-TRUE-01 bounded EXECUTABLE→Envelope→PRE_EXTERNAL evidence (transport-bound).

Composes WP-1 common epoch, Enter-Live-29P join, occupied-lane governed cycle, and
canonical envelope bind on the existing Full-Core closure executor. Does not POST,
mint permits, or authorize external effect.

Callers supply candles/market kwargs and lane state after any required natural ENTER
seed (see WP-2 composition proof tests). PRODUCTIVE_REAL_GET_PROVEN remains false
when using productive-class fresh GET transport doubles.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    CurrentProductive29PRuntimeIntegrityBackendV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    GAP_TRUE_01_OWNER_GO,
    CurrentProductiveFullCorePreExternalClosureResultV1,
    execute_current_productive_full_core_pre_external_closure_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1 import (
    _assert_no_secrets,
    _persist_json,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

OWNER_GO = GAP_TRUE_01_OWNER_GO
THIS_SLICE = "11.2.1.GAP-TRUE-01.EXECUTABLE_ENVELOPE_PRE_EXTERNAL_EVIDENCE"
EVIDENCE_DIRNAME = (
    "full_core_current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
_REPO_ROOT = Path(__file__).resolve().parents[3]


class CurrentProductiveGapTrue01EvidenceError(RuntimeError):
    """Fail-closed GAP-TRUE-01 evidence violation."""


@dataclass(frozen=True)
class CurrentProductiveGapTrue01EvidenceResultV1:
    store_root: str
    base_sha: str
    head_sha: str
    closure: CurrentProductiveFullCorePreExternalClosureResultV1
    gap_true_01_verdict: str
    manifest_verify_rc: int
    productive_real_get_proven: bool
    transport_bound_proof: bool


def _git_head_sha_v1() -> str:
    import subprocess

    return (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO_ROOT, text=True)
        .strip()
        .lower()
    )


def _validate_gap_true_01_closure_v1(
    result: CurrentProductiveFullCorePreExternalClosureResultV1,
) -> None:
    if result.wp1_status != "PASS" or result.wp2_status != "PASS":
        raise CurrentProductiveGapTrue01EvidenceError("WP1_OR_WP2_NOT_PASS")
    if result.terminal_disposition != DISPOSITION_PRE_EXTERNAL_EFFECT:
        raise CurrentProductiveGapTrue01EvidenceError("TERMINAL_NOT_PRE_EXTERNAL")
    if result.current_productive_decision_result != "EXECUTABLE_VENUE_PLAN_BOUND":
        raise CurrentProductiveGapTrue01EvidenceError("DECISION_NOT_EXECUTABLE")
    if result.decision_execution_eligible.lower() != "true":
        raise CurrentProductiveGapTrue01EvidenceError("DECISION_NOT_ELIGIBLE")
    if result.envelope_readiness.lower() != "true":
        raise CurrentProductiveGapTrue01EvidenceError("ENVELOPE_NOT_READY")
    if result.pre_external_effect_boundary_reached.lower() != "true":
        raise CurrentProductiveGapTrue01EvidenceError("PRE_EXTERNAL_NOT_REACHED")
    if result.capital_context_bound.lower() != "true":
        raise CurrentProductiveGapTrue01EvidenceError("CAPITAL_CONTEXT_NOT_BOUND")
    if result.mv2_capital_context_rebind_status != "PASS":
        raise CurrentProductiveGapTrue01EvidenceError("MV2_REBIND_NOT_PASS")
    if result.final_order_envelope_status != "PASS":
        raise CurrentProductiveGapTrue01EvidenceError("ENVELOPE_STATUS_NOT_PASS")
    if result.post_count != 0 or result.permit_created or result.external_effect_occurred:
        raise CurrentProductiveGapTrue01EvidenceError("EXTERNAL_EFFECT_OR_POST_LEAK")


def execute_current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    bound_instrument: BoundInstrumentV1,
    fresh_get_transport: FullCoreFreshPretradeGetTransportV1,
    lane_state_root: Path,
    candles_payload: Mapping[str, Any],
    market_kwargs: Mapping[str, Any],
    g17_typed_vol_producers: Mapping[str, object],
    evidence_root: Path | None = None,
    execution_integrity_backend: CurrentProductive29PRuntimeIntegrityBackendV1 | None = None,
) -> CurrentProductiveGapTrue01EvidenceResultV1:
    """Persist GAP-TRUE-01 closure evidence after caller-prepared natural ENTER inputs."""
    if owner_go != OWNER_GO:
        raise CurrentProductiveGapTrue01EvidenceError("OWNER_GO_MISMATCH")
    base_sha = str(origin_main_sha or "").strip().lower()
    if not base_sha:
        raise CurrentProductiveGapTrue01EvidenceError("ORIGIN_MAIN_SHA_MISSING")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    store = (
        Path(evidence_root)
        if evidence_root is not None
        else _REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME / run_id
    )
    store.mkdir(parents=True, exist_ok=True)

    closure = execute_current_productive_full_core_pre_external_closure_v1(
        owner_go=owner_go,
        origin_main_sha=base_sha,
        bound_instrument=bound_instrument,
        lane_state_root=lane_state_root,
        fresh_get_transport=fresh_get_transport,
        execute_network=False,
        evidence_root=store,
        candles_payload=dict(candles_payload),
        market_kwargs=dict(market_kwargs),
        g17_typed_vol_producers=g17_typed_vol_producers,
        execution_integrity_backend=execution_integrity_backend,
    )
    _validate_gap_true_01_closure_v1(closure)

    gap_claims: dict[str, Any] = {
        "OWNER_GO": owner_go,
        "THIS_SLICE": THIS_SLICE,
        "GAP_TRUE_01_VERDICT": "CLOSED",
        "BASE_SHA": base_sha,
        "HEAD_SHA": _git_head_sha_v1(),
        "PRODUCTIVE_REAL_GET_PROVEN": FALSE_TOKEN,
        "TRANSPORT_BOUND_PROOF": TRUE_TOKEN,
        "EXECUTABLE_DECISION_PROVEN": TRUE_TOKEN,
        "CAPITAL_CONTEXT_BOUND_PROVEN": TRUE_TOKEN,
        "ENVELOPE_READINESS_PROVEN": TRUE_TOKEN,
        "PRE_EXTERNAL_EFFECT_BOUNDARY_REACHED": TRUE_TOKEN,
        "POST_COUNT": str(closure.post_count),
        "VENUE_MUTATION_COUNT": "0",
        "EXTERNAL_EFFECT_OCCURRED": FALSE_TOKEN,
        "CLOSURE_STORE_ROOT": str(store),
    }
    _assert_no_secrets(gap_claims)
    _persist_json(path=store / "gap_true_01_verdict.json", payload=gap_claims)
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "OWNER_GO": owner_go,
            "THIS_SLICE": THIS_SLICE,
            "BASE_SHA": base_sha,
            "GAP_TRUE_01_TARGET": "EXECUTABLE_ENVELOPE_PRE_EXTERNAL",
        },
    )
    persist_manifest_sha256_v1(store_root=store)
    manifest_rc = verify_manifest_sha256_v1(store_root=store)
    if manifest_rc != 0:
        raise CurrentProductiveGapTrue01EvidenceError("MANIFEST_VERIFY_FAILED")

    return CurrentProductiveGapTrue01EvidenceResultV1(
        store_root=str(store),
        base_sha=base_sha,
        head_sha=_git_head_sha_v1(),
        closure=closure,
        gap_true_01_verdict="CLOSED",
        manifest_verify_rc=manifest_rc,
        productive_real_get_proven=False,
        transport_bound_proof=True,
    )


__all__ = [
    "EVIDENCE_DIRNAME",
    "OWNER_GO",
    "THIS_SLICE",
    "CurrentProductiveGapTrue01EvidenceError",
    "CurrentProductiveGapTrue01EvidenceResultV1",
    "execute_current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1",
]
