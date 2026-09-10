"""Bounded tests for MF membership-context artifact schema, writer, and reader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.mf_membership_context_artifact_contract_v1 import (
    ARTIFACT_SCHEMA_VERSION,
    ARTIFACT_TYPE,
    CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH,
    CANONICAL_STORE_RELATIVE_ROOT,
    EXECUTION_AUTHORITY_EFFECT,
    G13_UNLOCK,
    MANIFEST_FILENAME,
    N_VALUE,
    POLICY_IDENTITY_V1,
    REPO_ROOT,
    ROTATION_RUNTIME_IMPLEMENTED,
    RUNTIME_AUTHORIZED,
    SELECTOR_RUNTIME_IMPLEMENTED,
    Cap22ProvenanceV1,
    MembershipContextArtifactError,
    build_bootstrap_membership_from_cap22_snapshot_v1,
    build_membership_context_artifact_v1,
    canonical_json_dumps,
    derive_rotation_delta_v1,
    eligible_prefix_from_cap22_snapshot,
    materialize_canonical_bootstrap_instance_v1,
    membership_context_artifact_from_dict,
    read_membership_context_artifact_v1,
    sha256_hex,
    write_membership_context_artifact_v1,
)

SOURCE = (
    Path(__file__).resolve().parents[1] / "src/ops/mf_membership_context_artifact_contract_v1.py"
)


def _provenance(**overrides: object) -> Cap22ProvenanceV1:
    payload = {
        "ranking_event_time": "2023-11-14T22:13:20Z",
        "ranking_integrity_digest": "65c6ae446d9b55b095f236271329392bd6d8e747caba1b145cd55f7fd49f3a9f",
        "ranking_policy_id": "productive_futures_universe_structural_ranking_v1",
        "ranking_policy_version": "v1",
        "ranking_schema_version": "productive_futures_ranking_snapshot.v1",
        "ranking_snapshot_id": "pfr_evidence_cap22_v1",
        "snapshot_state": "VALID",
        "source_file_sha256": "abc" * 21 + "abcd",
        "source_relative_path": CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH,
        "top20_candidate_context_limit": 20,
        "universe_snapshot_id": "gfu_21fc493c5de33aca",
    }
    payload.update(overrides)
    return Cap22ProvenanceV1.from_dict(payload)


def _artifact(
    *, instruments: list[str] | None = None, bootstrap: bool = True, prior: str | None = None
):
    return build_membership_context_artifact_v1(
        ordered_instrument_ids=instruments
        if instruments is not None
        else ["okx_eea:ada", "okx_eea:apt"],
        cap22_provenance=_provenance(),
        bootstrap=bootstrap,
        prior_membership_reference=prior,
    )


def test_schema_valid_instance() -> None:
    artifact = _artifact()
    loaded = membership_context_artifact_from_dict(artifact.to_dict())
    assert loaded.schema_version == ARTIFACT_SCHEMA_VERSION
    assert loaded.artifact_type == ARTIFACT_TYPE
    assert loaded.bootstrap is True
    assert loaded.prior_membership_reference is None
    assert "rotation_deltas" not in loaded.to_dict()


def test_cardinality_over_n_rejected() -> None:
    with pytest.raises(MembershipContextArtifactError) as exc:
        _artifact(instruments=[f"id-{i}" for i in range(N_VALUE + 1)])
    assert exc.value.failure_code == "CARDINALITY_EXCEEDS_N"


def test_duplicates_rejected() -> None:
    with pytest.raises(MembershipContextArtifactError) as exc:
        _artifact(instruments=["okx_eea:ada", "okx_eea:ada"])
    assert exc.value.failure_code == "DUPLICATE_INSTRUMENT_ID"


def test_malformed_identity_rejected() -> None:
    artifact = _artifact()
    payload = artifact.to_dict()
    payload["instance_id"] = "not-an-id"
    with pytest.raises(MembershipContextArtifactError) as exc:
        membership_context_artifact_from_dict(payload)
    assert exc.value.failure_code == "MALFORMED_IDENTITY"


def test_invalid_provenance_rejected() -> None:
    with pytest.raises(MembershipContextArtifactError) as exc:
        _provenance(ranking_snapshot_id="")
    assert exc.value.failure_code == "INVALID_PROVENANCE"


def test_non_bootstrap_missing_prior_rejected() -> None:
    with pytest.raises(MembershipContextArtifactError) as exc:
        _artifact(bootstrap=False, prior=None)
    assert exc.value.failure_code == "MISSING_PRIOR_REFERENCE"


def test_bootstrap_null_prior_accepted() -> None:
    artifact = _artifact(bootstrap=True, prior=None)
    assert artifact.prior_membership_reference is None
    assert artifact.bootstrap is True


def test_writer_does_not_mutate_or_rerank_input(tmp_path: Path) -> None:
    decided_order = ["okx_eea:zzz", "okx_eea:aaa", "okx_eea:mmm"]
    artifact = _artifact(instruments=decided_order)
    written = write_membership_context_artifact_v1(artifact, store_root=tmp_path)
    assert list(written.ordered_instrument_ids) == decided_order
    readback = read_membership_context_artifact_v1(written.instance_id, store_root=tmp_path)
    assert list(readback.ordered_instrument_ids) == decided_order


def test_reader_fail_closed_malformed_and_partial(tmp_path: Path) -> None:
    artifact = _artifact()
    write_membership_context_artifact_v1(artifact, store_root=tmp_path)
    path = tmp_path / f"{artifact.instance_id}.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(MembershipContextArtifactError) as malformed:
        read_membership_context_artifact_v1(artifact.instance_id, store_root=tmp_path)
    assert malformed.value.failure_code in {"INVALID_SCHEMA", "INTEGRITY_FAILURE"}

    other = tmp_path / "orphan"
    other.mkdir()
    (other / f"{artifact.instance_id}.json").write_text(
        canonical_json_dumps(artifact.to_dict()) + "\n", encoding="utf-8"
    )
    with pytest.raises(MembershipContextArtifactError) as partial:
        read_membership_context_artifact_v1(artifact.instance_id, store_root=other)
    assert partial.value.failure_code == "PARTIAL_WRITE"


def test_empty_placeholder_rejected(tmp_path: Path) -> None:
    artifact = _artifact()
    write_membership_context_artifact_v1(artifact, store_root=tmp_path)
    (tmp_path / f"{artifact.instance_id}.json").write_text("", encoding="utf-8")
    with pytest.raises(MembershipContextArtifactError) as exc:
        read_membership_context_artifact_v1(artifact.instance_id, store_root=tmp_path)
    assert exc.value.failure_code in {"PLACEHOLDER_OR_EMPTY", "INTEGRITY_FAILURE", "PARTIAL_WRITE"}


def test_atomic_durable_persistence_and_manifest(tmp_path: Path) -> None:
    artifact = _artifact()
    written = write_membership_context_artifact_v1(artifact, store_root=tmp_path)
    manifest = tmp_path / MANIFEST_FILENAME
    assert manifest.is_file()
    body = manifest.read_text(encoding="utf-8")
    filename = f"{written.instance_id}.json"
    expected = sha256_hex((tmp_path / filename).read_bytes())
    assert f"{expected}  {filename}" in body
    readback = read_membership_context_artifact_v1(written.instance_id, store_root=tmp_path)
    assert readback.integrity_digest == written.integrity_digest


def test_rotation_deltas_not_persisted(tmp_path: Path) -> None:
    artifact = _artifact()
    write_membership_context_artifact_v1(artifact, store_root=tmp_path)
    payload = json.loads((tmp_path / f"{artifact.instance_id}.json").read_text(encoding="utf-8"))
    assert "rotation_deltas" not in payload
    assert "entered" not in payload
    assert "exited" not in payload
    assert "retained" not in payload
    with pytest.raises(MembershipContextArtifactError) as exc:
        membership_context_artifact_from_dict({**payload, "rotation_deltas": {"entered": []}})
    assert exc.value.failure_code == "ROTATION_DELTAS_CANONICAL_FORBIDDEN"


def test_derived_bootstrap_delta() -> None:
    artifact = _artifact()
    delta = derive_rotation_delta_v1(artifact, None)
    assert delta["entered"] == list(artifact.ordered_instrument_ids)
    assert delta["exited"] == []
    assert delta["retained"] == []


def test_reader_does_not_invent_prior(tmp_path: Path) -> None:
    artifact = _artifact()
    write_membership_context_artifact_v1(artifact, store_root=tmp_path)
    readback = read_membership_context_artifact_v1(artifact.instance_id, store_root=tmp_path)
    assert readback.prior_membership_reference is None
    with pytest.raises(MembershipContextArtifactError) as exc:
        derive_rotation_delta_v1(
            build_membership_context_artifact_v1(
                ordered_instrument_ids=["okx_eea:ada"],
                cap22_provenance=_provenance(),
                bootstrap=False,
                prior_membership_reference=artifact.instance_id,
            ),
            None,
        )
    assert exc.value.failure_code == "PRIOR_UNAVAILABLE"


def test_bootstrap_from_canonical_cap22_prefix_fill() -> None:
    snapshot_path = REPO_ROOT / CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH
    artifact = build_bootstrap_membership_from_cap22_snapshot_v1(
        snapshot_path=snapshot_path,
        source_relative_path=CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH,
    )
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    expected = eligible_prefix_from_cap22_snapshot(snapshot)
    assert artifact.ordered_instrument_ids == expected
    assert len(artifact.ordered_instrument_ids) == 5
    assert len(set(artifact.ordered_instrument_ids)) == 5
    assert artifact.bootstrap is True
    assert artifact.prior_membership_reference is None
    assert artifact.cap22_provenance.ranking_snapshot_id == "pfr_evidence_cap22_v1"
    assert artifact.temporal_identity.cap22_event_time == snapshot["event_time"]


def test_materialize_isolated_root_then_readback(tmp_path: Path) -> None:
    src = REPO_ROOT / CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH
    dest = tmp_path / CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())
    written = materialize_canonical_bootstrap_instance_v1(repo_root=tmp_path)
    readback = read_membership_context_artifact_v1(
        written.instance_id,
        store_root=tmp_path / CANONICAL_STORE_RELATIVE_ROOT,
    )
    assert readback.to_dict() == written.to_dict()
    assert readback.bootstrap is True


def test_canonical_bootstrap_readback_and_no_padding() -> None:
    store = REPO_ROOT / CANONICAL_STORE_RELATIVE_ROOT
    snapshot_path = REPO_ROOT / CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH
    expected = build_bootstrap_membership_from_cap22_snapshot_v1(
        snapshot_path=snapshot_path,
        source_relative_path=CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH,
    )
    readback = read_membership_context_artifact_v1(expected.instance_id, store_root=store)
    assert readback.instance_id == expected.instance_id
    assert list(readback.ordered_instrument_ids) == list(expected.ordered_instrument_ids)
    assert len(readback.ordered_instrument_ids) == 5
    assert len(readback.ordered_instrument_ids) <= N_VALUE
    assert readback.policy_identity == POLICY_IDENTITY_V1
    assert readback.prior_membership_reference is None
    delta = derive_rotation_delta_v1(readback, None)
    assert delta["entered"] == list(readback.ordered_instrument_ids)
    assert delta["exited"] == []
    assert delta["retained"] == []


def test_no_selector_runtime_or_execution_authority_introduced() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert SELECTOR_RUNTIME_IMPLEMENTED is False
    assert ROTATION_RUNTIME_IMPLEMENTED is False
    assert RUNTIME_AUTHORIZED is False
    assert G13_UNLOCK is False
    assert EXECUTION_AUTHORITY_EFFECT == "NONE"
    for forbidden in (
        "produce_productive_futures_ranking_v1",
        "select_single_selected_future",
        "challenger_margin",
        "submit_order",
        "src.ops.productive_futures_ranking_producer_v1",
        "src.ops.single_selected_future_policy_v1",
        "src.execution",
    ):
        assert forbidden not in source
    assert "eligible_prefix_from_cap22_snapshot" in source
