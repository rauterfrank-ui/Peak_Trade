"""Bounded tests for isolated MF previous-to-current deterministic replay."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.ops.mf_membership_context_artifact_contract_v1 import (
    CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH,
    CANONICAL_STORE_RELATIVE_ROOT,
    POLICY_IDENTITY_V1,
    REPO_ROOT,
    Cap22ProvenanceV1,
    build_membership_context_artifact_v1,
    cap22_provenance_from_snapshot_file,
    read_membership_context_artifact_v1,
    sha256_hex,
    write_membership_context_artifact_v1,
)
from src.ops.mf_membership_previous_to_current_replay_contract_v1 import (
    CANARY_AUTHORITY_EFFECT,
    CAP23_REWIRED,
    CAP24_REWIRED,
    DETERMINISTIC_PREVIOUS_TO_CURRENT_REPLAY_IMPLEMENTED,
    EXECUTION_AUTHORITY_EFFECT,
    FULL_CORE_LIVE_AUTHORITY_EFFECT,
    G13_UNLOCK,
    HOST_JOIN,
    ISOLATED_MF_TARGET_COMPLETE,
    MF_DETERMINISTIC_REPLAY_PROVEN,
    PRODUCTIVE_MF_INTEGRATION_COMPLETE,
    REPLAY_CANONICAL_MUTATION_FORBIDDEN,
    RUNTIME_AUTHORIZED,
    canonical_store_inventory_v1,
    replay_canonical_bootstrap_v1,
    replay_previous_to_current_v1,
)
from src.ops.mf_membership_selector_and_rotation_runtime_contract_v1 import (
    NO_NEW_INSTANCE,
    STATUS_CHANGED,
    STATUS_UNCHANGED_NEW_OBSERVATION,
    STATUS_UNCHANGED_REPLAY,
    WRITE_NEW_OBSERVATION_INSTANCE,
    run_isolated_selector_cycle_v1,
)

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "src/ops/mf_membership_previous_to_current_replay_contract_v1.py"
)
CANONICAL_STORE = REPO_ROOT / CANONICAL_STORE_RELATIVE_ROOT

BASES = [
    "ADA",
    "APT",
    "ARB",
    "ATOM",
    "AVAX",
    "BCH",
    "DOT",
    "ETH",
    "FIL",
    "INJ",
]


def _cid(base: str) -> str:
    return f"okx_eea:linear_perpetual:{base}:USDT:USDT:{base.lower()}-usdt-swap"


def _row(base: str, rank: int, eligible: bool = True) -> dict[str, Any]:
    return {
        "canonical_instrument_id": _cid(base),
        "eligibility_status": "ELIGIBLE" if eligible else "INELIGIBLE",
        "rank": rank,
    }


def _snapshot(
    *,
    snapshot_id: str,
    event_time: str,
    digest: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "snapshot_state": "VALID",
        "ranking_snapshot_id": snapshot_id,
        "schema_version": "productive_futures_ranking_snapshot.v1",
        "integrity_digest": digest,
        "event_time": event_time,
        "universe_snapshot_id": "gfu_fixture",
        "ranking_policy_id": "productive_futures_universe_structural_ranking_v1",
        "ranking_policy_version": "v1",
        "top20_candidate_context_limit": 20,
        "ranked_candidates": rows,
    }


def _provenance(snapshot: dict[str, Any]) -> Cap22ProvenanceV1:
    raw = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return Cap22ProvenanceV1(
        ranking_snapshot_id=str(snapshot["ranking_snapshot_id"]),
        ranking_schema_version=str(snapshot["schema_version"]),
        ranking_integrity_digest=str(snapshot["integrity_digest"]),
        ranking_event_time=str(snapshot["event_time"]),
        universe_snapshot_id=str(snapshot["universe_snapshot_id"]),
        ranking_policy_id=str(snapshot["ranking_policy_id"]),
        ranking_policy_version=str(snapshot["ranking_policy_version"]),
        source_relative_path="fixture://cap22",
        source_file_sha256=sha256_hex(raw),
        snapshot_state=str(snapshot["snapshot_state"]),
        top20_candidate_context_limit=int(snapshot["top20_candidate_context_limit"]),
    )


def _prefix_rows(bases: list[str] | None = None) -> list[dict[str, Any]]:
    chosen = bases if bases is not None else BASES
    return [_row(base, index + 1) for index, base in enumerate(chosen)]


def _bootstrap(store: Path, snapshot: dict[str, Any]):
    artifact = build_membership_context_artifact_v1(
        ordered_instrument_ids=[_cid(base) for base in ("ADA", "APT", "ARB", "ATOM", "AVAX")],
        cap22_provenance=_provenance(snapshot),
        bootstrap=True,
        prior_membership_reference=None,
    )
    return write_membership_context_artifact_v1(artifact, store_root=store)


def _replay(store: Path, prior_id: str, snapshot: dict[str, Any], **kwargs: Any):
    return replay_previous_to_current_v1(
        snapshot=snapshot,
        cap22_provenance=_provenance(snapshot),
        prior_instance_id=prior_id,
        store_root=store,
        **kwargs,
    )


def _bases(membership: tuple[str, ...]) -> list[str]:
    return [item.split(":")[2] for item in membership]


def _persist_selector(store: Path, prior, snapshot: dict[str, Any]):
    return run_isolated_selector_cycle_v1(
        snapshot=snapshot,
        cap22_provenance=_provenance(snapshot),
        prior=prior,
        store_root=store,
        persist=True,
    )


@pytest.fixture(autouse=True)
def _canonical_store_immutable() -> Any:
    before = canonical_store_inventory_v1(CANONICAL_STORE)
    yield
    after = canonical_store_inventory_v1(CANONICAL_STORE)
    assert before == after


def test_same_input_twice_identical_digest(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, boot)
    first = _replay(tmp_path, prior.instance_id, boot)
    second = _replay(
        tmp_path,
        prior.instance_id,
        boot,
        expected_result={
            "current_ordered_membership": list(first.current_ordered_membership),
            "membership_decision_status": first.membership_decision_status,
            "replay_result_digest": first.replay_result_digest,
        },
    )
    assert first.replay_result_digest == second.replay_result_digest
    assert first.replay_input_identity == second.replay_input_identity
    assert first.current_ordered_membership == second.current_ordered_membership
    assert first.entered == second.entered
    assert first.exited == second.exited
    assert first.retained == second.retained
    assert first.membership_decision_status == second.membership_decision_status
    assert first.replay_mutation_performed is False
    assert second.replay_mutation_performed is False
    assert first.selector_result.persisted_artifact is None
    assert list(tmp_path.glob("mca_*.json")) == [tmp_path / f"{prior.instance_id}.json"]


def test_bootstrap_replay_canonical_no_churn() -> None:
    snapshot_path = REPO_ROOT / CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH
    provenance, snapshot = cap22_provenance_from_snapshot_file(
        snapshot_path, source_relative_path=CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH
    )
    before = canonical_store_inventory_v1(CANONICAL_STORE)
    result = replay_canonical_bootstrap_v1(snapshot=snapshot, cap22_provenance=provenance)
    after = canonical_store_inventory_v1(CANONICAL_STORE)
    assert before == after
    assert _bases(result.current_ordered_membership) == ["ADA", "APT", "ARB", "ATOM", "AVAX"]
    assert result.membership_decision_status == STATUS_UNCHANGED_REPLAY
    assert result.write_policy == NO_NEW_INSTANCE
    assert result.entered == ()
    assert result.exited == ()
    assert result.replay_mutation_performed is False
    assert result.selector_result.persisted_artifact is None
    assert list(CANONICAL_STORE.glob("mca_*.json")) == [
        CANONICAL_STORE / "mca_bf0255a6007432e2.json"
    ]


def test_distinct_snapshot_age_advances_once(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, boot)
    first = _replay(tmp_path, prior.instance_id, boot)
    assert first.incumbent_observation_ages[_cid("ADA")] == 1
    hold = _snapshot(
        snapshot_id="snap-hold",
        event_time="2023-11-14T22:14:20Z",
        digest="b" * 64,
        rows=_prefix_rows(),
    )
    held = _persist_selector(tmp_path, prior, hold)
    assert held.persisted_artifact is not None
    replay_hold = _replay(tmp_path, prior.instance_id, hold)
    assert replay_hold.incumbent_observation_ages[_cid("ADA")] == 1
    assert replay_hold.membership_decision_status == STATUS_UNCHANGED_NEW_OBSERVATION
    replay_after = _replay(tmp_path, held.persisted_artifact.instance_id, hold)
    nxt = _snapshot(
        snapshot_id="snap-3",
        event_time="2023-11-14T22:15:20Z",
        digest="c" * 64,
        rows=_prefix_rows(),
    )
    advanced = _replay(tmp_path, held.persisted_artifact.instance_id, nxt)
    assert replay_after.incumbent_observation_ages[_cid("ADA")] == 2
    assert advanced.incumbent_observation_ages[_cid("ADA")] == 2
    assert (
        advanced.incumbent_observation_ages[_cid("ADA")]
        - first.incumbent_observation_ages[_cid("ADA")]
        == 1
    )


def test_duplicate_snapshot_idempotent(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, boot)
    first = _replay(tmp_path, prior.instance_id, boot)
    second = _replay(tmp_path, prior.instance_id, boot)
    assert first.incumbent_observation_ages == second.incumbent_observation_ages
    assert first.replay_result_digest == second.replay_result_digest
    assert first.membership_decision_status == STATUS_UNCHANGED_REPLAY
    assert list(tmp_path.glob("mca_*.json")) == [tmp_path / f"{prior.instance_id}.json"]


def test_min_hold_reconstructed(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, boot)
    nxt = _snapshot(
        snapshot_id="snap-2",
        event_time="2023-11-14T22:14:20Z",
        digest="b" * 64,
        rows=[
            _row("ADA", 1),
            _row("APT", 2),
            _row("ARB", 3),
            _row("BCH", 4),
            _row("ATOM", 5),
            _row("AVAX", 6),
        ],
    )
    result = _replay(tmp_path, prior.instance_id, nxt)
    assert _bases(result.current_ordered_membership) == ["ADA", "APT", "ARB", "ATOM", "AVAX"]
    assert "BCH" not in _bases(result.current_ordered_membership)
    assert result.incumbent_observation_ages[_cid("AVAX")] == 1


def test_post_hold_replacement(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, boot)
    held = _persist_selector(
        tmp_path,
        prior,
        _snapshot(
            snapshot_id="snap-hold",
            event_time="2023-11-14T22:14:20Z",
            digest="b" * 64,
            rows=_prefix_rows(),
        ),
    )
    assert held.persisted_artifact is not None
    challenger = _snapshot(
        snapshot_id="snap-3",
        event_time="2023-11-14T22:15:20Z",
        digest="c" * 64,
        rows=[
            _row("ADA", 1),
            _row("APT", 2),
            _row("ARB", 3),
            _row("BCH", 4),
            _row("ATOM", 5),
            _row("AVAX", 6),
        ],
    )
    result = _replay(tmp_path, held.persisted_artifact.instance_id, challenger)
    assert _bases(result.current_ordered_membership) == ["ADA", "APT", "ARB", "BCH", "ATOM"]
    assert result.exited == (_cid("AVAX"),)
    assert result.entered == (_cid("BCH"),)
    assert result.membership_decision_status == STATUS_CHANGED
    assert result.write_policy == WRITE_NEW_OBSERVATION_INSTANCE
    assert result.selector_result.persisted_artifact is None


def test_forced_removal(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, boot)
    nxt = _snapshot(
        snapshot_id="snap-2",
        event_time="2023-11-14T22:14:20Z",
        digest="b" * 64,
        rows=[
            _row("ADA", 1),
            _row("APT", 2),
            _row("ARB", 3),
            _row("ATOM", 4),
            _row("BCH", 5),
            _row("AVAX", 6, eligible=False),
        ],
    )
    result = _replay(tmp_path, prior.instance_id, nxt)
    assert "AVAX" not in _bases(result.current_ordered_membership)
    assert "BCH" in _bases(result.current_ordered_membership)
    assert result.incumbent_observation_ages[_cid("AVAX")] == 1


def test_underfill_no_padding(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(["ADA", "APT"]),
    )
    artifact = build_membership_context_artifact_v1(
        ordered_instrument_ids=[_cid("ADA"), _cid("APT")],
        cap22_provenance=_provenance(boot),
        bootstrap=True,
        prior_membership_reference=None,
    )
    prior = write_membership_context_artifact_v1(artifact, store_root=tmp_path)
    nxt = _snapshot(
        snapshot_id="snap-2",
        event_time="2023-11-14T22:14:20Z",
        digest="b" * 64,
        rows=[_row("ADA", 1), _row("APT", 2), _row("BCH", 3), _row("DOT", 4)],
    )
    result = _replay(tmp_path, prior.instance_id, nxt)
    assert _bases(result.current_ordered_membership) == ["ADA", "APT", "BCH", "DOT"]
    assert len(result.current_ordered_membership) < 5
    assert result.entered == (_cid("BCH"), _cid("DOT"))


def test_multi_replacement_and_order(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, boot)
    held = _persist_selector(
        tmp_path,
        prior,
        _snapshot(
            snapshot_id="snap-hold",
            event_time="2023-11-14T22:14:20Z",
            digest="b" * 64,
            rows=_prefix_rows(),
        ),
    )
    assert held.persisted_artifact is not None
    nxt = _snapshot(
        snapshot_id="snap-3",
        event_time="2023-11-14T22:15:20Z",
        digest="c" * 64,
        rows=[
            _row("ADA", 1),
            _row("BCH", 2),
            _row("DOT", 3),
            _row("APT", 4),
            _row("ARB", 5),
            _row("ATOM", 6),
            _row("AVAX", 7),
        ],
    )
    result = _replay(tmp_path, held.persisted_artifact.instance_id, nxt)
    bases = _bases(result.current_ordered_membership)
    assert bases == ["ADA", "BCH", "DOT", "APT", "ARB"]
    assert len(bases) <= 5
    assert result.current_ordered_membership == tuple(_cid(base) for base in bases)


def test_broken_prior_fail_closed(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    child = build_membership_context_artifact_v1(
        ordered_instrument_ids=[_cid(base) for base in ("ADA", "APT", "ARB", "ATOM", "AVAX")],
        cap22_provenance=_provenance(boot),
        bootstrap=False,
        prior_membership_reference="mca_deadbeefdeadbeef",
    )
    written = write_membership_context_artifact_v1(child, store_root=tmp_path)
    with pytest.raises(Exception) as exc:
        _replay(tmp_path, written.instance_id, boot)
    assert "ARTIFACT_MISSING" in str(exc.value) or "OBSERVATION_CHAIN" in str(exc.value)


def test_provenance_mismatch_fail_closed(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, boot)
    other = _snapshot(
        snapshot_id="snap-other",
        event_time="2023-11-14T22:14:20Z",
        digest="b" * 64,
        rows=_prefix_rows(),
    )
    with pytest.raises(Exception) as exc:
        replay_previous_to_current_v1(
            snapshot=boot,
            cap22_provenance=_provenance(other),
            prior_instance_id=prior.instance_id,
            store_root=tmp_path,
        )
    assert "PROVENANCE_MISMATCH" in str(exc.value)


def test_policy_mismatch_fail_closed(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, boot)
    wrong = dict(POLICY_IDENTITY_V1)
    wrong["anti_churn_policy"] = "POLICY_NOT_A"
    with pytest.raises(Exception) as exc:
        _replay(tmp_path, prior.instance_id, boot, policy_identity=wrong)
    assert "POLICY_IDENTITY_MISMATCH" in str(exc.value)


def test_malformed_artifact_fail_closed(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    (tmp_path / "MANIFEST.sha256").write_text(
        f"{'0' * 64}  mca_ffffffffffffffff.json\n", encoding="utf-8"
    )
    (tmp_path / "mca_ffffffffffffffff.json").write_text("{not-json", encoding="utf-8")
    with pytest.raises(Exception):
        _replay(tmp_path, "mca_ffffffffffffffff", boot)
    with pytest.raises(Exception):
        _replay(tmp_path, "not-an-id", boot)


def test_selector_equivalence_and_derived_delta(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, boot)
    nxt = _snapshot(
        snapshot_id="snap-2",
        event_time="2023-11-14T22:14:20Z",
        digest="b" * 64,
        rows=[
            _row("ADA", 1),
            _row("APT", 2),
            _row("ARB", 3),
            _row("ATOM", 4),
            _row("BCH", 5),
            _row("AVAX", 6, eligible=False),
        ],
    )
    selector = run_isolated_selector_cycle_v1(
        snapshot=nxt,
        cap22_provenance=_provenance(nxt),
        prior=prior,
        store_root=tmp_path,
        persist=False,
    )
    replay = _replay(tmp_path, prior.instance_id, nxt)
    assert replay.current_ordered_membership == selector.ordered_membership
    assert replay.membership_decision_status == selector.decision_status
    assert replay.entered == tuple(selector.rotation_delta["entered"])
    assert replay.exited == tuple(selector.rotation_delta["exited"])
    assert replay.retained == tuple(selector.rotation_delta["retained"])
    assert replay.policy_trace == selector.policy_trace
    assert selector.persisted_artifact is None
    assert replay.replay_mutation_performed is False


def test_canonical_store_immutable_inventory() -> None:
    before = canonical_store_inventory_v1(CANONICAL_STORE)
    snapshot_path = REPO_ROOT / CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH
    provenance, snapshot = cap22_provenance_from_snapshot_file(
        snapshot_path, source_relative_path=CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH
    )
    replay_canonical_bootstrap_v1(snapshot=snapshot, cap22_provenance=provenance)
    after = canonical_store_inventory_v1(CANONICAL_STORE)
    assert before == after
    assert set(before) == {"MANIFEST.sha256", "mca_bf0255a6007432e2.json"}
    readback = read_membership_context_artifact_v1(
        "mca_bf0255a6007432e2", store_root=CANONICAL_STORE
    )
    assert readback.instance_id == "mca_bf0255a6007432e2"


def test_no_writer_or_foreign_authority() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert DETERMINISTIC_PREVIOUS_TO_CURRENT_REPLAY_IMPLEMENTED is True
    assert MF_DETERMINISTIC_REPLAY_PROVEN is True
    assert ISOLATED_MF_TARGET_COMPLETE is True
    assert PRODUCTIVE_MF_INTEGRATION_COMPLETE is False
    assert REPLAY_CANONICAL_MUTATION_FORBIDDEN is True
    assert RUNTIME_AUTHORIZED is False
    assert HOST_JOIN is False
    assert G13_UNLOCK is False
    assert CAP23_REWIRED is False
    assert CAP24_REWIRED is False
    assert EXECUTION_AUTHORITY_EFFECT == "NONE"
    assert FULL_CORE_LIVE_AUTHORITY_EFFECT == "NONE"
    assert CANARY_AUTHORITY_EFFECT == "NONE"
    for forbidden in (
        "write_membership_context_artifact_v1",
        "persist_selector_result_v1",
        "run_isolated_selector_cycle_v1",
        "produce_productive_futures_ranking_v1",
        "select_single_selected_future",
        "submit_order",
        "src.execution",
        "src.trading.master_v2",
        "datetime",
        "time.time",
        "random",
        "uuid",
    ):
        assert forbidden not in source
