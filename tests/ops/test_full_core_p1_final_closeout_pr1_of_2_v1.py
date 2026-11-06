"""P1 final closeout PR 1/2 witness and closeout tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.governed_productive_account_equity_authority_producer_v1.p1_completeness_witness_foundation_v1 import (
    ROOT_OBSERVATION_FRESHNESS,
    ROOT_RESTART_DURABILITY,
    DERIVED_PROVENANCE,
    DERIVED_TIME_DOMAIN,
    WITNESS_COMPLETE,
    evaluate_sealed_p1_completeness_witness_bundle_v1,
    load_sealed_p1_witness_evidence_v1,
    root_by_id_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_d5_checkpoint_freshness_witness_v1 import (
    P1D5CheckpointFreshnessWitnessError,
    build_p1_d5_checkpoint_freshness_witness_adjudication_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_final_closeout_pr1_of_2_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    WP_ID,
    execute_p1_final_closeout_pr1_of_2_v1,
    verify_canonical_p1_final_closeout_pr1_pack_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_negative_completeness_closeout_contract_v1 import (
    P1_CLOSEOUT_PROVEN_NEGATIVE,
    P1_CLOSEOUT_UNKNOWN,
    evaluate_sealed_interest_accrued_p1_closeout_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_observation_restart_durability_witness_v1 import (
    prove_offline_observation_restart_durability_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_CLOSEOUT_PACK = (
    REPO_ROOT / "evidence/ops/full_core_p1_final_closeout_pr1_of_2_v1/2026-09-21T050000Z"
)


def test_freshness_adjudication_proven_on_sealed_repo() -> None:
    adj = build_p1_d5_checkpoint_freshness_witness_adjudication_v1(
        repo_root=REPO_ROOT,
        traversal_pagination_proven=True,
    )
    assert adj["P1_OBSERVATION_FRESHNESS_COMPLETENESS_PROVEN"] == "true"
    assert adj["CHECKPOINT_BINDING_ID"] == "WIND4D5GENESIS8d3f573ffc0c59b4"
    assert len(adj.get("BOUND_OBSERVATION_IDS", [])) == 2


def test_freshness_fail_closed_without_pagination() -> None:
    adj = build_p1_d5_checkpoint_freshness_witness_adjudication_v1(
        repo_root=REPO_ROOT,
        traversal_pagination_proven=False,
    )
    assert adj["P1_OBSERVATION_FRESHNESS_COMPLETENESS_PROVEN"] == "false"


def test_offline_restart_proof_on_sealed_repo(tmp_path: Path) -> None:
    proof = prove_offline_observation_restart_durability_v1(
        repo_root=REPO_ROOT,
        reload_store=tmp_path / "reload",
    )
    assert proof.proven is True
    assert proof.d4_digest_stable is True
    assert proof.d5_digest_stable is True


def test_execute_persist_and_manifest_verify(tmp_path: Path) -> None:
    result = execute_p1_final_closeout_pr1_of_2_v1(
        repo_root=REPO_ROOT,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        owner_go=WP_ID,
        persist_as_of="2026-09-21T05:00:00Z",
        skip_persist=False,
        offline_reload_store=tmp_path / "offline_reload",
    )
    assert result.observation_freshness_proven == "true"
    assert result.time_domain_proven == "true"
    assert result.restart_durability_proven == "true"
    assert verify_canonical_p1_final_closeout_pr1_pack_v1(repo_root=REPO_ROOT) == 0


def test_witness_bundle_and_closeout_after_canonical_pack() -> None:
    if not (_CLOSEOUT_PACK / "MANIFEST.sha256").is_file():
        pytest.skip("canonical closeout pack not persisted yet")
    bundle = evaluate_sealed_p1_completeness_witness_bundle_v1(repo_root=REPO_ROOT)
    freshness = root_by_id_v1(bundle, ROOT_OBSERVATION_FRESHNESS)
    restart = root_by_id_v1(bundle, ROOT_RESTART_DURABILITY)
    assert freshness.complete is True
    assert freshness.status == WITNESS_COMPLETE
    assert restart.complete is True
    assert bundle.time_domain.complete is True
    assert bundle.provenance.complete is True
    closeout = evaluate_sealed_interest_accrued_p1_closeout_v1(repo_root=REPO_ROOT)
    assert closeout.closeout_decision == P1_CLOSEOUT_PROVEN_NEGATIVE
    assert closeout.p1_status_after == "PROVEN_FALSE"


def test_malformed_raw_http_fails_freshness(tmp_path: Path) -> None:
    evidence = load_sealed_p1_witness_evidence_v1(repo_root=REPO_ROOT)
    bad_raw = dict(evidence.raw_http_capture)
    bad_raw["request_utc"] = ""
    with pytest.raises(P1D5CheckpointFreshnessWitnessError):
        from src.ops.governed_productive_account_equity_authority_producer_v1.p1_d5_checkpoint_freshness_witness_v1 import (
            _capture_from_raw_http,
        )

        _capture_from_raw_http(pack_label="BAD", raw_http=bad_raw)


def test_stale_transport_breaks_freshness_logic() -> None:
    evidence = load_sealed_p1_witness_evidence_v1(repo_root=REPO_ROOT)
    stale = dict(evidence.raw_http_capture)
    stale["response_utc"] = "2030-01-01T00:00:00Z"
    from src.ops.governed_productive_account_equity_authority_producer_v1.p1_d5_checkpoint_freshness_witness_v1 import (
        _capture_from_raw_http,
        _validate_capture_against_checkpoint_v1,
    )

    capture = _capture_from_raw_http(pack_label="STALE", raw_http=stale)
    err = _validate_capture_against_checkpoint_v1(
        capture=capture,
        checkpoint_id="CKPT",
        checkpoint_binding_id=str(stale.get("d5_binding_id", "")),
        checkpoint_observed_at="2026-09-13T17:03:18Z",
        bound_identity_digest=str(stale.get("d4_identity_digest", "")),
        claims_raw_persisted=True,
        claims_raw_sha256=str(stale.get("payload_sha256", "")),
    )
    assert err is not None
    assert "STALE" in err or "TRANSPORT" in err
