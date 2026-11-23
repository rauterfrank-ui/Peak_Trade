"""Publish the initial N5 assignment for the dedicated SOPH shadow deployment."""

import json
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    atomic_write_json,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    checkpoint_root_for,
    load_completed_selection_publication_v1,
    load_pending_selection_publication_v1,
    prior_durable_lane_assignment_commit_exists,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.soph_shadow_bootstrap_v1 import (
    SOPH_SHADOW_INITIAL_ASSIGNMENT_POLICY,
    SophShadowSlot2BootstrapV1,
)
from src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1.checked_publication_v1 import (
    CheckedLanePublicationV1,
    publish_checked_lane_selections_v1,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.composition_v1 import (
    Wp02ProductiveDefaultChainRequestV1,
    _load_prior_membership_v1,
    produce_wp02_ranking_inputs_v1,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.constants_v1 import (
    DEFAULT_MEMBERSHIP_SUBDIR,
    DEFAULT_RANKING_SUBDIR,
    DEFAULT_UNIVERSE_SUBDIR,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import MINIMUM_FINALIZED_PT1M_MARKS
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    load_and_validate_universe_snapshot_v1,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    build_bootstrap_membership_from_cap22_snapshot_v1,
    write_membership_context_artifact_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    SOPH_I17,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import SNAPSHOT_FILENAME
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    load_and_validate_ranking_snapshot_v1,
)


def publish_wp02_soph_shadow_bootstrap_v1(
    request: Wp02ProductiveDefaultChainRequestV1,
    *,
    scope: SophShadowSlot2BootstrapV1,
    publication_observed_at_unix: float,
) -> CheckedLanePublicationV1:
    """Create or replay one shadow genesis. Cap24 and the shadow session are separate owners."""
    base = Path(request.topology_state_root_base)
    scope.require_topology_root(base)
    state = Path(request.wp02_state_root)
    store = Path(request.public_store_root)
    window = request.bound_mark_window
    if (
        state != scope.deployment_root / "wp02_runtime"
        or store != scope.deployment_root / "public_facts"
        or state.is_symlink()
        or store.is_symlink()
        or window is None
        or request.venue_native_id != SOPH_I17.native_id
        or window.instrument_ref.canonical_instrument_id != SOPH_I17.canonical_id
        or window.instrument_ref.venue_native_id != SOPH_I17.native_id
        or len(window.fact_digests) != MINIMUM_FINALIZED_PT1M_MARKS
        or not all(
            isfinite(value)
            for value in (
                window.collection_started_at_unix,
                window.collection_completed_at_unix,
                publication_observed_at_unix,
            )
        )
        or not window.collection_started_at_unix
        <= window.collection_completed_at_unix
        <= publication_observed_at_unix
        or request.prior_membership is not None
        or request.lane_assignment_writer is not None
        or request.economic_md_public_source is not None
        or not request.persist_handoff
    ):
        raise ValueError("SOPH_SHADOW_BOOTSTRAP_REQUEST_MISMATCH")

    writer = DurableLaneAssignmentSingleWriterV1(checkpoint_root_for(base))
    writer.acquire(now_unix=publication_observed_at_unix)
    try:
        pending = load_pending_selection_publication_v1(base)
        completed = load_completed_selection_publication_v1(base)
        if prior_durable_lane_assignment_commit_exists(base) and not (pending or completed):
            raise ValueError("SOPH_SHADOW_BOOTSTRAP_UNPUBLISHED_CHECKPOINT")
        if (pending or completed) and not state.is_dir():
            raise ValueError("SOPH_SHADOW_BOOTSTRAP_ORIGINAL_SOURCES_MISSING")

        # Bind the first source build before its writers run. A retry can finish
        # partial input production, but cannot replace its inputs under the same root.
        inputs_path = state / "soph_shadow_bootstrap_inputs_v1.json"
        inputs = {
            "initial_assignment_policy": SOPH_SHADOW_INITIAL_ASSIGNMENT_POLICY,
            "repository_sha": request.repository_sha,
            "source_event_time": request.source_event_time,
            "universe_payload_digest": fact_digest(request.universe_source_payload),
            "mark_price_payload_digest": fact_digest(request.universe_mark_price_payload),
            "instrument_ref": window.instrument_ref.to_dict(),
            "fact_digests": sorted(window.fact_digests),
            "collection_started_at_unix": window.collection_started_at_unix,
            "collection_completed_at_unix": window.collection_completed_at_unix,
        }
        membership_root = base / DEFAULT_MEMBERSHIP_SUBDIR
        prior = _load_prior_membership_v1(membership_root)
        if (pending or completed) and prior is None:
            raise ValueError("SOPH_SHADOW_BOOTSTRAP_ORIGINAL_MEMBERSHIP_MISSING")
        if inputs_path.exists():
            if json.loads(inputs_path.read_bytes()) != inputs:
                raise ValueError("SOPH_SHADOW_BOOTSTRAP_INPUT_CONFLICT")
        else:
            if pending or completed or prior or (state.exists() and any(state.iterdir())):
                raise ValueError("SOPH_SHADOW_BOOTSTRAP_UNOWNED_STATE")
            atomic_write_json(path=inputs_path, payload=inputs)

        source = Path(DEFAULT_RANKING_SUBDIR) / SNAPSHOT_FILENAME
        if prior is None and not (pending or completed):
            ranked = produce_wp02_ranking_inputs_v1(request)
            if not ranked.ok:
                raise ValueError(ranked.failure_code)

        ranked_original = load_and_validate_ranking_snapshot_v1(
            state / DEFAULT_RANKING_SUBDIR,
            expected_repository_sha=request.repository_sha,
        )
        governed = load_and_validate_universe_snapshot_v1(
            state / DEFAULT_UNIVERSE_SUBDIR,
            expected_repository_sha=request.repository_sha,
        )
        if not ranked_original.ok or not governed.ok:
            raise ValueError("SOPH_SHADOW_BOOTSTRAP_ORIGINAL_SOURCES_MISSING")
        ranking = ranked_original.snapshot
        universe = governed.snapshot
        if (
            ranking.universe_snapshot_id != universe.snapshot_id
            or ranking.universe_payload_digest != universe.payload_digest
            or ranking.universe_source_digest != universe.source_digest
        ):
            raise ValueError("SOPH_SHADOW_BOOTSTRAP_ORIGINAL_SOURCE_CONFLICT")
        snapshot = ranking.to_dict()
        membership = build_bootstrap_membership_from_cap22_snapshot_v1(
            snapshot_path=state / source,
            source_relative_path=str(Path("wp02_runtime") / source),
        )
        if SOPH_I17.canonical_id not in membership.ordered_instrument_ids:
            raise ValueError("SOPH_SHADOW_ELIGIBLE_MEMBER_REQUIRED")
        if prior is not None and prior != membership:
            raise ValueError("SOPH_SHADOW_BOOTSTRAP_MEMBERSHIP_CONFLICT")
        if prior is None:
            # The membership and its manifest become visible together at genesis.
            with TemporaryDirectory(dir=base) as tmp:
                staged = Path(tmp) / DEFAULT_MEMBERSHIP_SUBDIR
                write_membership_context_artifact_v1(membership, store_root=staged)
                staged.rename(membership_root)
        return publish_checked_lane_selections_v1(
            membership=membership,
            ranking_snapshot=snapshot,
            topology_state_root_base=base,
            writer=writer,
            repository_sha=request.repository_sha,
            producer_observed_at_unix=publication_observed_at_unix,
            soph_shadow_bootstrap=scope,
        )
    finally:
        writer.release()
