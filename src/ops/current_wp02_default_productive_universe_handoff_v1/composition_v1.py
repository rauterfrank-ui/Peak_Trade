"""Orchestrate Cap21 refresh → real B05 → Cap22 → hard-facts MF-N5 handoff (existing owners only)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    SOURCE_KIND,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.constants_v1 import (
    DEFAULT_MEMBERSHIP_SUBDIR,
    DEFAULT_RANKING_SUBDIR,
    DEFAULT_UNIVERSE_SUBDIR,
    MINIMUM_ECONOMIC_MD_MARKS,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.errors_v1 import (
    Wp02ProductiveDefaultChainError,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.time_alignment_v1 import (
    producer_observed_at_unix_from_source_event_v1,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    run_governed_futures_universe_producer_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap21_to_cap23_productive_persistence_v1 import (
    assert_current_productive_cap22_ranking_policy_binding_v1,
    build_cap22_feature_production_snapshot_for_cap21_universe_only_v1,
)
from src.ops.hard_facts_system_closure_v1.cap22_productive_real_gate_v1 import (
    assert_cap22_productive_real_ranking_v1,
)
from src.ops.hard_facts_system_closure_v1.productive_mf_n5_handoff_join_v1 import (
    HardFactsCap22MembershipHandoffRequestV1,
    HardFactsMfN5HandoffResultV1,
    execute_hard_facts_cap22_to_mf_n5_handoff_v1,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    MembershipContextArtifactV1,
    read_membership_context_artifact_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_runtime_economic_md_adapter_v1 import (
    PublicRuntimeEconomicMdPublicSourceV1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    run_productive_futures_ranking_producer_v1,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import EconomicMdPublicSourceV1


@dataclass(frozen=True)
class Wp02ProductiveDefaultChainRequestV1:
    wp02_state_root: Path
    public_store_root: Path
    venue_native_id: str
    repository_sha: str
    universe_source_payload: Mapping[str, Any]
    universe_mark_price_payload: Mapping[str, Any]
    source_event_time: str
    topology_state_root_base: Path
    producer_observed_at_unix: float | None = None
    session_id_prefix: str = "wp02-default"
    lane_assignment_writer: Any = None
    prior_membership: MembershipContextArtifactV1 | None = None
    economic_md_public_source: EconomicMdPublicSourceV1 | None = None
    persist_handoff: bool = True


@dataclass(frozen=True)
class Wp02ProductiveDefaultChainResultV1:
    ok: bool
    cap21_refresh_invoked: bool
    economic_md_source_canonical: bool
    real_b05_built: bool
    cap22_productive_real_assertion: bool
    hard_facts_handoff_invoked: bool
    membership_persisted: bool
    topology_persisted: bool
    ranking_snapshot: Mapping[str, Any] | None
    handoff: HardFactsMfN5HandoffResultV1 | None
    failure_code: str = ""


def _load_prior_membership_v1(store: Path) -> MembershipContextArtifactV1 | None:
    if not store.is_dir():
        return None
    candidates = [
        p
        for p in store.glob("*.json")
        if p.name != "cap22_snapshot.json" and p.name != "MANIFEST.sha256"
    ]
    if not candidates:
        return None
    latest = max(candidates, key=lambda path: path.stat().st_mtime)
    instance_id = latest.stem
    try:
        return read_membership_context_artifact_v1(instance_id, store_root=store)
    except Exception:  # noqa: BLE001
        return None


def run_wp02_productive_default_chain_v1(
    request: Wp02ProductiveDefaultChainRequestV1,
) -> Wp02ProductiveDefaultChainResultV1:
    assert_current_productive_cap22_ranking_policy_binding_v1()
    observed = (
        request.producer_observed_at_unix
        if request.producer_observed_at_unix is not None
        else producer_observed_at_unix_from_source_event_v1(request.source_event_time)
    )
    state = Path(request.wp02_state_root)
    uni_root = state / DEFAULT_UNIVERSE_SUBDIR
    rank_root = state / DEFAULT_RANKING_SUBDIR
    membership_root = Path(request.topology_state_root_base) / DEFAULT_MEMBERSHIP_SUBDIR
    for path in (uni_root, rank_root, membership_root):
        path.mkdir(parents=True, exist_ok=True)

    uni = run_governed_futures_universe_producer_v1(
        state_root=uni_root,
        source_payload=request.universe_source_payload,
        mark_price_payload=request.universe_mark_price_payload,
        repository_sha=request.repository_sha,
        producer_observed_at_unix=observed,
        source_event_time=request.source_event_time,
        source_kind=SOURCE_KIND,
        session_id=f"{request.session_id_prefix}-cap21",
    )
    if uni.get("ok") is not True:
        return Wp02ProductiveDefaultChainResultV1(
            ok=False,
            cap21_refresh_invoked=True,
            economic_md_source_canonical=False,
            real_b05_built=False,
            cap22_productive_real_assertion=False,
            hard_facts_handoff_invoked=False,
            membership_persisted=False,
            topology_persisted=False,
            ranking_snapshot=None,
            handoff=None,
            failure_code="CAP21_REFRESH_FAIL_CLOSED",
        )
    uni_snap = uni.get("snapshot")
    if not isinstance(uni_snap, Mapping):
        return Wp02ProductiveDefaultChainResultV1(
            ok=False,
            cap21_refresh_invoked=True,
            economic_md_source_canonical=False,
            real_b05_built=False,
            cap22_productive_real_assertion=False,
            hard_facts_handoff_invoked=False,
            membership_persisted=False,
            topology_persisted=False,
            ranking_snapshot=None,
            handoff=None,
            failure_code="CAP21_SNAPSHOT_MISSING",
        )

    if request.economic_md_public_source is not None:
        md_source = request.economic_md_public_source
    else:
        md_source = PublicRuntimeEconomicMdPublicSourceV1(store_root=request.public_store_root)
    bundle = md_source.collect_instrument_raw_input_v1(venue_native_id=request.venue_native_id)
    if len(bundle.marks) < MINIMUM_ECONOMIC_MD_MARKS or bundle.failure_codes:
        return Wp02ProductiveDefaultChainResultV1(
            ok=False,
            cap21_refresh_invoked=True,
            economic_md_source_canonical=False,
            real_b05_built=False,
            cap22_productive_real_assertion=False,
            hard_facts_handoff_invoked=False,
            membership_persisted=False,
            topology_persisted=False,
            ranking_snapshot=None,
            handoff=None,
            failure_code="ECONOMIC_MD_FAIL_CLOSED",
        )

    collection_started = observed - 1.0
    feature_snap = build_cap22_feature_production_snapshot_for_cap21_universe_only_v1(
        universe_snapshot=uni_snap,
        public_md_source=md_source,
        collection_started_at_unix=collection_started,
        collection_completed_at_unix=observed,
    )
    ranking_run = run_productive_futures_ranking_producer_v1(
        state_root=rank_root,
        universe_snapshot=uni_snap,
        repository_sha=request.repository_sha,
        producer_observed_at_unix=observed,
        session_id=f"{request.session_id_prefix}-cap22",
        feature_production_snapshot=feature_snap,
    )
    if ranking_run.get("ok") is not True:
        return Wp02ProductiveDefaultChainResultV1(
            ok=False,
            cap21_refresh_invoked=True,
            economic_md_source_canonical=True,
            real_b05_built=True,
            cap22_productive_real_assertion=False,
            hard_facts_handoff_invoked=False,
            membership_persisted=False,
            topology_persisted=False,
            ranking_snapshot=None,
            handoff=None,
            failure_code="CAP22_RANKING_FAIL_CLOSED",
        )
    ranking_snap = ranking_run.get("snapshot")
    if not isinstance(ranking_snap, Mapping):
        return Wp02ProductiveDefaultChainResultV1(
            ok=False,
            cap21_refresh_invoked=True,
            economic_md_source_canonical=True,
            real_b05_built=True,
            cap22_productive_real_assertion=False,
            hard_facts_handoff_invoked=False,
            membership_persisted=False,
            topology_persisted=False,
            ranking_snapshot=None,
            handoff=None,
            failure_code="CAP22_SNAPSHOT_MISSING",
        )

    assert_cap22_productive_real_ranking_v1(ranking_snap)

    prior = request.prior_membership
    if prior is None and request.persist_handoff:
        prior = _load_prior_membership_v1(membership_root)

    handoff_req = HardFactsCap22MembershipHandoffRequestV1(
        ranking_snapshot=dict(ranking_snap),
        membership_store_root=membership_root,
        topology_state_root_base=Path(request.topology_state_root_base),
    )
    handoff = execute_hard_facts_cap22_to_mf_n5_handoff_v1(
        handoff_req,
        prior=prior,
        lane_assignment_writer=request.lane_assignment_writer,
    )
    return Wp02ProductiveDefaultChainResultV1(
        ok=True,
        cap21_refresh_invoked=True,
        economic_md_source_canonical=True,
        real_b05_built=True,
        cap22_productive_real_assertion=True,
        hard_facts_handoff_invoked=True,
        membership_persisted=handoff.membership is not None,
        topology_persisted=handoff.topology is not None,
        ranking_snapshot=dict(ranking_snap),
        handoff=handoff,
    )
