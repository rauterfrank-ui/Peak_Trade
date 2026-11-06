"""Bounded tests for isolated MF selector and membership-diff rotation runtime."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from src.ops.mf_membership_context_artifact_contract_v1 import (
    CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH,
    CANONICAL_STORE_RELATIVE_ROOT,
    N_VALUE,
    REPO_ROOT,
    Cap22ProvenanceV1,
    MembershipContextArtifactError,
    build_membership_context_artifact_v1,
    cap22_provenance_from_snapshot_file,
    read_membership_context_artifact_v1,
    sha256_hex,
    write_membership_context_artifact_v1,
)
from src.ops.mf_membership_selector_and_rotation_runtime_contract_v1 import (
    CANARY_AUTHORITY_EFFECT,
    CAP23_REWIRED,
    CAP24_REWIRED,
    CHALLENGER_MARGIN_VALUE,
    EXECUTION_AUTHORITY_EFFECT,
    FULL_CORE_LIVE_AUTHORITY_EFFECT,
    G13_UNLOCK,
    HOLDING_STATE_DERIVABLE_FROM_EXISTING_ARTIFACTS,
    HOST_JOIN,
    MEMBERSHIP_DECISION_RUNTIME_IMPLEMENTED,
    MINIMUM_HOLDING_VALUE,
    NO_NEW_INSTANCE,
    ROTATION_CONTROLLER_ROLE,
    ROTATION_RUNTIME_IMPLEMENTED,
    RUNTIME_AUTHORIZED,
    SELECTOR_RUNTIME_IMPLEMENTED,
    STATUS_CHANGED,
    STATUS_UNCHANGED_NEW_OBSERVATION,
    STATUS_UNCHANGED_REPLAY,
    WRITE_NEW_OBSERVATION_INSTANCE,
    MfSelectorError,
    derive_holding_ages_v1,
    parse_eligible_cap22_top20,
    persist_selector_result_v1,
    run_isolated_selector_cycle_v1,
)

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "src/ops/mf_membership_selector_and_rotation_runtime_contract_v1.py"
)

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


def _run(
    store: Path,
    prior,
    snapshot: dict[str, Any],
    *,
    persist: bool = True,
):
    return run_isolated_selector_cycle_v1(
        snapshot=snapshot,
        cap22_provenance=_provenance(snapshot),
        prior=prior,
        store_root=store,
        persist=persist,
    )


def test_bootstrap_identical_top5_no_churn_replay(tmp_path: Path) -> None:
    snapshot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="d" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, snapshot)
    result = _run(tmp_path, prior, snapshot)
    assert result.decision_status == STATUS_UNCHANGED_REPLAY
    assert result.write_policy == NO_NEW_INSTANCE
    assert result.persisted_artifact is None
    assert [item.split(":")[2] for item in result.ordered_membership] == [
        "ADA",
        "APT",
        "ARB",
        "ATOM",
        "AVAX",
    ]
    assert list(tmp_path.glob("mca_*.json")) == [tmp_path / f"{prior.instance_id}.json"]


def test_forced_removal_bypasses_min_hold(tmp_path: Path) -> None:
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
        rows=_prefix_rows(["ADA", "APT", "ARB", "ATOM", "AVAX", "BCH"]),
    )
    nxt["ranked_candidates"][4]["eligibility_status"] = "INELIGIBLE"
    result = _run(tmp_path, prior, nxt)
    bases = [item.split(":")[2] for item in result.ordered_membership]
    assert "AVAX" not in bases
    assert "BCH" in bases
    assert result.decision_status == STATUS_CHANGED
    assert "AVAX" in [item.split(":")[2] for item in result.rotation_delta["exited"]]
    assert "BCH" in [item.split(":")[2] for item in result.rotation_delta["entered"]]


def test_underfill_skips_hysteresis(tmp_path: Path) -> None:
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
        rows=_prefix_rows(["ADA", "APT", "ARB", "BCH", "DOT"]),
    )
    result = _run(tmp_path, prior, nxt)
    bases = [item.split(":")[2] for item in result.ordered_membership]
    assert bases == ["ADA", "APT", "ARB", "BCH", "DOT"]
    assert result.holding_ages[_cid("ADA")] == 1


def test_min_hold_blocks_qualified_challenger(tmp_path: Path) -> None:
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
    result = _run(tmp_path, prior, nxt)
    bases = [item.split(":")[2] for item in result.ordered_membership]
    assert bases == ["ADA", "APT", "ARB", "ATOM", "AVAX"]
    assert "BCH" not in bases
    assert result.holding_ages[_cid("AVAX")] == 1
    assert result.holding_ages[_cid("AVAX")] < MINIMUM_HOLDING_VALUE


def test_post_hold_replacement_and_rank_margin(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, boot)
    hold = _snapshot(
        snapshot_id="snap-hold",
        event_time="2023-11-14T22:14:20Z",
        digest="b" * 64,
        rows=_prefix_rows(),
    )
    held = _run(tmp_path, prior, hold)
    assert held.decision_status == STATUS_UNCHANGED_NEW_OBSERVATION
    assert held.persisted_artifact is not None
    assert held.holding_ages[_cid("AVAX")] == 1
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
    replaced = _run(tmp_path, held.persisted_artifact, challenger)
    bases = [item.split(":")[2] for item in replaced.ordered_membership]
    assert bases == ["ADA", "APT", "ARB", "BCH", "ATOM"]
    assert replaced.rotation_delta["exited"] == [_cid("AVAX")]
    assert replaced.rotation_delta["entered"] == [_cid("BCH")]

    fail_margin = _snapshot(
        snapshot_id="snap-4",
        event_time="2023-11-14T22:16:20Z",
        digest="d" * 64,
        rows=[
            _row("ADA", 1),
            _row("APT", 2),
            _row("ARB", 3),
            _row("BCH", 4),
            _row("ATOM", 5),
            _row("DOT", 6),
        ],
    )
    blocked = _run(tmp_path, replaced.persisted_artifact, fail_margin)
    assert [item.split(":")[2] for item in blocked.ordered_membership] == [
        "ADA",
        "APT",
        "ARB",
        "BCH",
        "ATOM",
    ]
    assert CHALLENGER_MARGIN_VALUE == 1


def test_multi_replacement_and_order_preservation(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, boot)
    hold = _run(
        tmp_path,
        prior,
        _snapshot(
            snapshot_id="snap-hold",
            event_time="2023-11-14T22:14:20Z",
            digest="b" * 64,
            rows=_prefix_rows(),
        ),
    )
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
    result = _run(tmp_path, hold.persisted_artifact, nxt)
    bases = [item.split(":")[2] for item in result.ordered_membership]
    assert bases == ["ADA", "BCH", "DOT", "APT", "ARB"]
    assert set(item.split(":")[2] for item in result.rotation_delta["exited"]) == {
        "ATOM",
        "AVAX",
    }
    assert len(result.ordered_membership) <= N_VALUE


def test_no_padding_when_fewer_eligible(tmp_path: Path) -> None:
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
        rows=[_row("ADA", 1), _row("APT", 2), _row("ARB", 3)],
    )
    result = _run(tmp_path, prior, nxt)
    assert [item.split(":")[2] for item in result.ordered_membership] == ["ADA", "APT", "ARB"]
    assert len(result.ordered_membership) == 3


def test_replayed_snapshot_does_not_increment_age(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, boot)
    first = _run(tmp_path, prior, boot)
    second = _run(tmp_path, prior, boot)
    assert first.holding_ages == second.holding_ages
    assert first.holding_ages[_cid("ADA")] == 1
    assert first.write_policy == NO_NEW_INSTANCE
    assert len(list(tmp_path.glob("mca_*.json"))) == 1


def test_derived_rotation_delta_not_stored(tmp_path: Path) -> None:
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
        rows=_prefix_rows(["ADA", "APT", "ARB", "ATOM", "BCH"]),
    )
    result = _run(tmp_path, prior, nxt)
    assert result.persisted_artifact is not None
    payload = json.loads(
        (tmp_path / f"{result.persisted_artifact.instance_id}.json").read_text(encoding="utf-8")
    )
    assert "rotation_deltas" not in payload
    assert "entered" not in payload
    assert result.rotation_delta["entered"]
    assert result.rotation_delta["exited"]


def test_fail_closed_malformed_inputs(tmp_path: Path) -> None:
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, boot)
    bad_state = copy.deepcopy(boot)
    bad_state["snapshot_state"] = "INVALID"
    with pytest.raises(MfSelectorError) as invalid:
        _run(tmp_path, prior, bad_state)
    assert invalid.value.failure_code == "INVALID_CAP22_INPUT"

    duplicate = copy.deepcopy(boot)
    duplicate["ranked_candidates"].append(_row("ADA", 1))
    with pytest.raises(MfSelectorError) as dup:
        parse_eligible_cap22_top20(duplicate)
    assert dup.value.failure_code == "DUPLICATE_CAP22_INPUT"

    regression = copy.deepcopy(boot)
    regression["ranking_snapshot_id"] = "snap-old"
    regression["event_time"] = "2023-11-14T22:12:00Z"
    regression["integrity_digest"] = "c" * 64
    with pytest.raises(MfSelectorError) as temporal:
        _run(tmp_path, prior, regression)
    assert temporal.value.failure_code == "TEMPORAL_REGRESSION"

    with pytest.raises(MembershipContextArtifactError):
        read_membership_context_artifact_v1("mca_deadbeefdeadbeef", store_root=tmp_path)


def test_holding_state_from_artifact_chain(tmp_path: Path) -> None:
    assert HOLDING_STATE_DERIVABLE_FROM_EXISTING_ARTIFACTS is True
    boot = _snapshot(
        snapshot_id="snap-boot",
        event_time="2023-11-14T22:13:20Z",
        digest="a" * 64,
        rows=_prefix_rows(),
    )
    prior = _bootstrap(tmp_path, boot)
    ages = derive_holding_ages_v1((prior,))
    assert ages[_cid("ADA")] == 1
    held = _run(
        tmp_path,
        prior,
        _snapshot(
            snapshot_id="snap-hold",
            event_time="2023-11-14T22:14:20Z",
            digest="b" * 64,
            rows=_prefix_rows(),
        ),
    )
    chain_ages = derive_holding_ages_v1((prior, held.persisted_artifact))
    assert chain_ages[_cid("ADA")] == 2


def test_writer_reader_integration_at_most_one_new_artifact(tmp_path: Path) -> None:
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
        rows=_prefix_rows(),
    )
    selected = run_isolated_selector_cycle_v1(
        snapshot=nxt,
        cap22_provenance=_provenance(nxt),
        prior=prior,
        store_root=tmp_path,
        persist=False,
    )
    assert selected.write_policy == WRITE_NEW_OBSERVATION_INSTANCE
    assert selected.persisted_artifact is None
    persist_selector_result_v1(selected, store_root=tmp_path)
    persist_selector_result_v1(selected, store_root=tmp_path)
    assert len({path.name for path in tmp_path.glob("mca_*.json")}) == 2
    readback = read_membership_context_artifact_v1(
        selected.proposed_artifact.instance_id, store_root=tmp_path
    )
    assert readback.prior_membership_reference == prior.instance_id
    assert readback.bootstrap is False


def test_canonical_bootstrap_replay_does_not_write_second_instance() -> None:
    store = REPO_ROOT / CANONICAL_STORE_RELATIVE_ROOT
    snapshot_path = REPO_ROOT / CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    provenance, _loaded = cap22_provenance_from_snapshot_file(
        snapshot_path, source_relative_path=CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH
    )
    prior = read_membership_context_artifact_v1("mca_bf0255a6007432e2", store_root=store)
    before = sorted(path.name for path in store.glob("mca_*.json"))
    result = run_isolated_selector_cycle_v1(
        snapshot=snapshot,
        cap22_provenance=provenance,
        prior=prior,
        store_root=store,
        persist=True,
    )
    after = sorted(path.name for path in store.glob("mca_*.json"))
    assert result.decision_status == STATUS_UNCHANGED_REPLAY
    assert result.write_policy == NO_NEW_INSTANCE
    assert before == after == ["mca_bf0255a6007432e2.json"]
    assert [item.split(":")[2] for item in result.ordered_membership] == [
        "ADA",
        "APT",
        "ARB",
        "ATOM",
        "AVAX",
    ]


def test_no_execution_or_foreign_authority() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert SELECTOR_RUNTIME_IMPLEMENTED is True
    assert MEMBERSHIP_DECISION_RUNTIME_IMPLEMENTED is True
    assert ROTATION_RUNTIME_IMPLEMENTED is True
    assert ROTATION_CONTROLLER_ROLE == "MEMBERSHIP_DIFF_ONLY"
    assert RUNTIME_AUTHORIZED is False
    assert HOST_JOIN is False
    assert G13_UNLOCK is False
    assert CAP23_REWIRED is False
    assert CAP24_REWIRED is False
    assert EXECUTION_AUTHORITY_EFFECT == "NONE"
    assert FULL_CORE_LIVE_AUTHORITY_EFFECT == "NONE"
    assert CANARY_AUTHORITY_EFFECT == "NONE"
    for forbidden in (
        "produce_productive_futures_ranking_v1",
        "select_single_selected_future",
        "submit_order",
        "src.ops.productive_futures_ranking_producer_v1",
        "src.ops.single_selected_future_policy_v1",
        "src.execution",
        "src.trading.master_v2",
    ):
        assert forbidden not in source
