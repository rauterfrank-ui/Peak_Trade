"""CURRENT-WP-02: default productive universe → Cap22 → POLICY_A handoff."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.hard_facts_system_closure_v1.productive_mf_n5_handoff_join_v1 import (
    resolve_membership_via_hard_facts_handoff_v1,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    build_bootstrap_membership_from_cap22_snapshot_v1,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.composition_v1 import (
    Wp02ProductiveDefaultChainRequestV1,
    run_wp02_productive_default_chain_v1,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.default_handoff_v1 import (
    resolve_default_hard_facts_cap22_handoff_v1,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.evidence_v1 import (
    write_current_wp02_closure_evidence_v1,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.errors_v1 import (
    Wp02ProductiveDefaultChainError,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import (
    MINIMUM_FINALIZED_PT1M_MARKS,
    PT1M_STEP_MS,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.hard_facts_system_closure_v1.cap22_productive_real_gate_v1 import (
    Cap22ProductiveRealGateError,
)
from src.ops.hard_facts_system_closure_v1.position_aware_rotation_v1 import (
    RotationPhase,
    evaluate_position_aware_rotation_v1,
)
from src.ops.hard_facts_system_closure_v1.productive_mf_n5_handoff_join_v1 import (
    execute_hard_facts_cap22_to_mf_n5_handoff_v1,
    HardFactsCap22MembershipHandoffRequestV1,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    read_membership_context_artifact_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.wp02_insertion_v1 import (
    Wp02InsertionContextV1,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.wp02_hook_v1 import (
    Wp02HookBindingV1,
    build_default_wp02_hook_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    append_fact_v1,
    default_store_paths_v1,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    CAPABILITY_ID,
    PRODUCER_VERSION,
    RANKING_POLICY_PROVENANCE,
    SNAPSHOT_STATE_VALID,
)
from tests.ops._wp02_universe_fixture_v1 import (
    wp02_eth_only_mark_price_payload_v1,
    wp02_eth_only_universe_source_payload_v1,
)
from tests.ops.test_current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1 import (
    OBSERVED_UNIX,
    REPO_SHA,
    _five_rows,
    _held_writer,
    _persist_universe_and_ranking,
)

REPO = Path(__file__).resolve().parents[2]
BASELINE_SHA = "287bd8fd882f367b0a68b3f7d7321406a2534d5b"
BASE_TS = 1_757_631_540_000


def _tested_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()


def _seed_public_marks(store_root: Path, *, n: int = MINIMUM_FINALIZED_PT1M_MARKS) -> None:
    paths = default_store_paths_v1(store_root)
    store_root.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        append_fact_v1(
            paths,
            {
                "fact_kind": "FinalizedPt1mMarkFactV1",
                "interval_start_ms": BASE_TS + i * PT1M_STEP_MS,
                "mark_px": str(100 + i),
                "confirm": "1",
                "captured_at": "2026-09-26T00:00:00Z",
                "instrument": {"venue_native_id": "ETH-USDT-SWAP"},
            },
        )


def _chain_request(
    tmp_path: Path, *, writer=None, session: str = "t"
) -> Wp02ProductiveDefaultChainRequestV1:
    public = tmp_path / "public"
    _seed_public_marks(public)
    topo = tmp_path / "topology"
    return Wp02ProductiveDefaultChainRequestV1(
        wp02_state_root=tmp_path / "wp02",
        public_store_root=public,
        venue_native_id="ETH-USDT-SWAP",
        repository_sha=REPO_SHA,
        universe_source_payload=wp02_eth_only_universe_source_payload_v1(),
        universe_mark_price_payload=wp02_eth_only_mark_price_payload_v1(),
        source_event_time="1700000000000",
        topology_state_root_base=topo,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id_prefix=session,
        lane_assignment_writer=writer,
    )


def test_t_plus_chain_cap21_real_b05_cap22_handoff(tmp_path: Path) -> None:
    writer = _held_writer(tmp_path / "topology")
    result = run_wp02_productive_default_chain_v1(_chain_request(tmp_path, writer=writer))
    assert result.ok is True
    assert result.cap21_refresh_invoked is True
    assert result.economic_md_source_canonical is True
    assert result.real_b05_built is True
    assert result.cap22_productive_real_assertion is True
    assert result.hard_facts_handoff_invoked is True
    assert result.membership_persisted is True
    assert result.topology_persisted is True
    assert result.ranking_snapshot is not None


def test_t_plus_supervisor_hook_invoked(tmp_path: Path) -> None:
    writer = _held_writer(tmp_path / "topology")
    public = tmp_path / "public"
    _seed_public_marks(public)
    binding = Wp02HookBindingV1(
        wp02_state_root=tmp_path / "wp02",
        topology_state_root_base=tmp_path / "topology",
        repository_sha=REPO_SHA,
        universe_source_payload=wp02_eth_only_universe_source_payload_v1(),
        universe_mark_price_payload=wp02_eth_only_mark_price_payload_v1(),
        source_event_time="1700000000000",
        lane_assignment_writer=writer,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    hook = build_default_wp02_hook_v1(binding)
    sink: dict = {}
    hook(
        Wp02InsertionContextV1(
            public_store_root=public,
            venue_native_id="ETH-USDT-SWAP",
            canonical_instrument_id="inst-eth",
            economic_md_mark_count=MINIMUM_FINALIZED_PT1M_MARKS,
            tick_index=0,
            wp02_result_sink=sink,
        )
    )
    assert sink["chain_result"].ok is True


def test_two_ranking_observations_membership_persisted(tmp_path: Path) -> None:
    writer = _held_writer(tmp_path / "topology1")
    req1 = _chain_request(tmp_path, writer=writer, session="o1").__dict__.copy()
    req1["topology_state_root_base"] = tmp_path / "topology1"
    first = run_wp02_productive_default_chain_v1(Wp02ProductiveDefaultChainRequestV1(**req1))
    assert first.handoff is not None
    writer2 = _held_writer(tmp_path / "topology2")
    req2d = _chain_request(tmp_path, writer=writer2, session="o2").__dict__.copy()
    req2d["prior_membership"] = first.handoff.membership
    req2d["topology_state_root_base"] = tmp_path / "topology2"
    second = run_wp02_productive_default_chain_v1(Wp02ProductiveDefaultChainRequestV1(**req2d))
    assert first.ok and second.ok
    assert first.handoff is not None and second.handoff is not None
    m1 = first.handoff.membership.instance_id
    m2 = second.handoff.membership.instance_id
    assert m1 and m2


def test_restart_replay_same_ranking_no_forced_rotation(tmp_path: Path) -> None:
    writer = _held_writer(tmp_path / "topology1")
    req1 = _chain_request(tmp_path, writer=writer, session="r1").__dict__.copy()
    req1["topology_state_root_base"] = tmp_path / "topology1"
    first = run_wp02_productive_default_chain_v1(Wp02ProductiveDefaultChainRequestV1(**req1))
    assert first.handoff is not None
    prior_id = first.handoff.membership.instance_id
    membership_root = tmp_path / "topology1" / "membership"
    ranking = dict(first.ranking_snapshot or {})
    writer2 = _held_writer(tmp_path / "topology2")
    handoff = execute_hard_facts_cap22_to_mf_n5_handoff_v1(
        HardFactsCap22MembershipHandoffRequestV1(
            ranking_snapshot=ranking,
            membership_store_root=membership_root,
            topology_state_root_base=tmp_path / "topology2",
        ),
        prior=read_membership_context_artifact_v1(prior_id, store_root=membership_root),
        lane_assignment_writer=writer2,
    )
    assert handoff.membership.instance_id == prior_id


def test_missing_economic_md_fail_closed(tmp_path: Path) -> None:
    writer = _held_writer(tmp_path / "topology")
    req = _chain_request(tmp_path, writer=writer)
    req = Wp02ProductiveDefaultChainRequestV1(
        **{**req.__dict__, "public_store_root": tmp_path / "empty_public"}
    )
    result = run_wp02_productive_default_chain_v1(req)
    assert result.ok is False
    assert result.failure_code == "ECONOMIC_MD_FAIL_CLOSED"
    assert result.membership_persisted is False


def test_synthetic_ranking_rejected(tmp_path: Path) -> None:
    snap = {
        "capability_id": CAPABILITY_ID,
        "producer_version": PRODUCER_VERSION,
        "snapshot_state": SNAPSHOT_STATE_VALID,
        "ranking_policy_provenance": "synthetic test fixture",
        "ranking_snapshot_id": "x",
        "integrity_digest": "abc",
    }
    assert (
        resolve_default_hard_facts_cap22_handoff_v1(
            ranking_snapshot=snap,
            explicit_handoff=None,
            topology_state_root_base=tmp_path,
        )
        is None
    )
    with pytest.raises(Cap22ProductiveRealGateError):
        execute_hard_facts_cap22_to_mf_n5_handoff_v1(
            HardFactsCap22MembershipHandoffRequestV1(
                ranking_snapshot=snap,
                membership_store_root=tmp_path / "mca",
                topology_state_root_base=tmp_path / "topo",
            ),
        )


def test_control_plane_opt_in_default_handoff_without_explicit_inject(tmp_path: Path) -> None:
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    ranking = chain["ranking"]
    topo = tmp_path / "topo"
    resolved = resolve_default_hard_facts_cap22_handoff_v1(
        ranking_snapshot=ranking,
        explicit_handoff=None,
        topology_state_root_base=topo,
    )
    assert resolved is not None
    writer = _held_writer(topo)
    snap_file = tmp_path / "cap22.json"
    snap_file.write_text(json.dumps(ranking), encoding="utf-8")
    bootstrap = build_bootstrap_membership_from_cap22_snapshot_v1(
        snapshot_path=snap_file,
        source_relative_path="runtime/test/cap22.json",
    )
    updated = resolve_membership_via_hard_facts_handoff_v1(
        membership=bootstrap,
        handoff=resolved,
        lane_assignment_writer=writer,
    )
    assert updated.ordered_instrument_ids


def test_open_position_replacement_blocked() -> None:
    rot = evaluate_position_aware_rotation_v1(
        phase=RotationPhase.COMMIT,
        venue_flat=False,
        reconciled=True,
        pending_external_custody=False,
        pending_pre_external_custody=False,
        lane_health_allows_replacement=True,
    )
    assert rot.allowed is False


def test_post_pins_unreachable() -> None:
    assert POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False


def test_wp02_closure_evidence_artifact(tmp_path: Path) -> None:
    writer = _held_writer(tmp_path / "topology1")
    req1 = _chain_request(tmp_path, writer=writer, session="e1").__dict__.copy()
    req1["topology_state_root_base"] = tmp_path / "topology1"
    first = run_wp02_productive_default_chain_v1(Wp02ProductiveDefaultChainRequestV1(**req1))
    assert first.handoff is not None
    writer2 = _held_writer(tmp_path / "topology2")
    req2d = _chain_request(tmp_path, writer=writer2, session="e2").__dict__.copy()
    req2d["prior_membership"] = first.handoff.membership
    req2d["topology_state_root_base"] = tmp_path / "topology2"
    run_wp02_productive_default_chain_v1(Wp02ProductiveDefaultChainRequestV1(**req2d))
    path = write_current_wp02_closure_evidence_v1(
        repo_root=tmp_path,
        baseline_sha=BASELINE_SHA,
        tested_code_sha=_tested_sha(),
        chain_flags={
            "ok": True,
            "cap21_refresh_invoked": True,
            "economic_md_source_canonical": True,
            "real_b05_built": True,
            "cap22_productive_real_assertion": True,
            "hard_facts_handoff_invoked": True,
            "membership_persisted": True,
            "topology_persisted": True,
            "restart_mca_restored": True,
            "synthetic_b05_rejected": True,
            "open_position_replacement_blocked": True,
        },
        ranking_observations=2,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["external_ranking_inject_required"] is False
    assert payload["external_membership_inject_required"] is False
    assert payload["POST_COUNT"] == 0
