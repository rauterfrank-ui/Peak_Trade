"""Regression matrix for GHOSV execution lifecycle adjudication."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    LEDGER_FILENAME,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persisted_reconciliation_disposition_v1 import (
    CONTRACT_ID as G004_CONTRACT_ID,
    attempt_digest_v1,
)
from src.ops.ghosv_bounded_context_v1.execution_bounded_offline_observer_v1 import (
    ExecutionOfflineObserverPathsV1,
    run_execution_bounded_offline_observer_v1,
)
from src.ops.ghosv_bounded_context_v1.execution_lifecycle_adjudication_v1 import (
    adjudicate_confirmed_venue_post_submission_v1,
    venue_post_outcome_from_attempt_payload_v1,
)
from src.ops.ghosv_bounded_context_v1.types_v1 import GhosvEvidenceKind
from src.ops.ghosv_bounded_context_v1.s01_evidence_ingest_v1 import normalize_evidence_record_v1

REPO = Path(__file__).resolve().parents[2]
PRIMARY_REPO = Path("/Users/frnkhrz/Peak_Trade")
PRE_EXTERNAL_FIXTURE = (
    REPO
    / "tests/fixtures/current_productive_golden_happy_vector_post_7065_reference_v1/PRE_EXTERNAL_CONVERGENCE_REPORT.json"
)
CAP11_FIXTURE = (
    REPO
    / "docs/evidence/capability_1_1_productive_reconciliation_runtime_binding_v1/clean_start_match"
)
L10_RUN = PRIMARY_REPO / (
    "runtime/current_productive/natural_evidence_accumulation_v1/runs/"
    "20261012T190205Z_ghv_l10_integrated_natural_enter_pre_external_v1"
)
L10_CYCLE = L10_RUN / "cycles/48cf857337ef5f1f8249146ff607c24787afe0ec2124b406b6cb4321801c4cd5/s5"
L10_RECON = (
    PRIMARY_REPO
    / "runtime/current_productive/natural_evidence_accumulation_v1/productivity/runtime_state/recon"
)


def _write_cycle_dir(
    tmp_path: Path, *, ledger: dict, transitions: list[dict] | None = None
) -> Path:
    root = tmp_path / "cycle"
    root.mkdir(parents=True)
    (root / LEDGER_FILENAME).write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    if transitions:
        lines = [json.dumps(row, sort_keys=True) for row in transitions]
        (root / "transitions.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root


def _base_ledger(**extra: object) -> dict:
    payload = {
        "state": "COMPLETED",
        "binding_digest": "digest-a",
        "cycle_owner_go": "OWNER_GO_CURRENT_PRODUCTIVE_GOVERNED_CYCLE_ORCHESTRATOR_V1",
        "native_id": "BTC-USDT-SWAP",
        "POST_COUNT": "0",
        "PERMIT_CREATED": "false",
    }
    payload.update(extra)
    return payload


def _run_observer(tmp_path: Path, **kwargs: object) -> dict:
    out = tmp_path / "observer_out"
    paths = ExecutionOfflineObserverPathsV1(
        trade_id=str(kwargs.get("trade_id", "observer-test")),
        output_dir=out,
        recon_dir=kwargs.get("recon_dir"),
        pre_external_report=kwargs.get("pre_external_report"),
        final_order_envelope=kwargs.get("final_order_envelope"),
        governed_cycle_evidence_dir=kwargs.get("governed_cycle_evidence_dir"),
        g004_post_attempt_store_root=kwargs.get("g004_post_attempt_store_root"),
        repository_root=kwargs.get("repository_root"),
    )
    return run_execution_bounded_offline_observer_v1(paths)


def test_a_pre_external_post_count_zero(tmp_path: Path):
    if not PRE_EXTERNAL_FIXTURE.is_file():
        pytest.skip("fixture missing")
    report = _run_observer(tmp_path, pre_external_report=PRE_EXTERNAL_FIXTURE)
    assert report["execution_lifecycle_completeness"] == "PRE_EXTERNAL_ONLY"


def test_b_post_submission_witness_flag_without_post_occurred(tmp_path: Path):
    assert (
        venue_post_outcome_from_attempt_payload_v1(
            {"post_submission_witness": True, "post_occurred": False}
        )
        is False
    )
    root = _write_cycle_dir(tmp_path, ledger=_base_ledger(POST_COUNT="0"))
    report = _run_observer(tmp_path, governed_cycle_evidence_dir=root)
    assert report["lifecycle_adjudication"]["confirmed_venue_post_submission"] is False


def test_c_execution_attempt_without_venue_submission(tmp_path: Path):
    record = normalize_evidence_record_v1(
        {
            "kind": GhosvEvidenceKind.EXECUTION_ATTEMPT.value,
            "source_module": "test",
            "source_contract": "pre_external_convergence_report.v1",
            "trade_id": "t1",
            "instrument_id": "BTC-USDT-SWAP",
            "payload": {"post_occurred": False, "post_count": 0, "post_count_known": True},
        }
    )
    confirmed, conflict = adjudicate_confirmed_venue_post_submission_v1((record,))
    assert confirmed is False
    assert conflict is False


def test_d_confirmed_post_witness_post_count_one(tmp_path: Path):
    root = _write_cycle_dir(
        tmp_path,
        ledger=_base_ledger(POST_COUNT="1"),
        transitions=[
            _base_ledger(state="IN_PROGRESS", POST_COUNT="1"),
            _base_ledger(POST_COUNT="1"),
        ],
    )
    report = _run_observer(tmp_path, governed_cycle_evidence_dir=root)
    assert report["execution_lifecycle_completeness"] == "POST_SUBMISSION_WITNESSED"
    assert report["lifecycle_adjudication"]["confirmed_venue_post_submission"] is True


def test_e_missing_post_count_unknown(tmp_path: Path):
    ledger = _base_ledger()
    del ledger["POST_COUNT"]
    root = _write_cycle_dir(tmp_path, ledger=ledger)
    report = _run_observer(tmp_path, governed_cycle_evidence_dir=root)
    assert report["lifecycle_adjudication"]["confirmed_venue_post_submission"] is False


def test_f_post_count_contradicts_post_occurred(tmp_path: Path):
    sources = tmp_path / "sources"
    sources.mkdir()
    pre = sources / "pre.json"
    pre.write_text(
        json.dumps(
            {
                "NATIVE_ID": "BTC-USDT-SWAP",
                "RUN_ID": "run-1",
                "POST_COUNT": 1,
                "PRE_EXTERNAL_REACHED": "true",
                "TERMINAL_DISPOSITION": "PRE_EXTERNAL_EFFECT",
            }
        ),
        encoding="utf-8",
    )
    root = _write_cycle_dir(sources, ledger=_base_ledger(POST_COUNT="0", native_id="BTC-USDT-SWAP"))
    report = run_execution_bounded_offline_observer_v1(
        ExecutionOfflineObserverPathsV1(
            trade_id="conflict-test",
            output_dir=tmp_path / "observer_out",
            pre_external_report=pre,
            governed_cycle_evidence_dir=root,
        )
    )
    assert report["lifecycle_adjudication"]["post_witness_conflict"] is True
    assert report["execution_lifecycle_completeness"] == "INCONSISTENT_SOURCES"


def test_g_cross_file_native_id_mismatch(tmp_path: Path):
    if not PRE_EXTERNAL_FIXTURE.is_file():
        pytest.skip("fixture missing")
    root = _write_cycle_dir(tmp_path, ledger=_base_ledger(native_id="ETH-USDT-SWAP"))
    report = _run_observer(
        tmp_path,
        pre_external_report=PRE_EXTERNAL_FIXTURE,
        governed_cycle_evidence_dir=root,
    )
    assert report["execution_lifecycle_completeness"] == "INCONSISTENT_SOURCES"


def test_h_local_stop_not_venue_cancel(tmp_path: Path):
    root = _write_cycle_dir(
        tmp_path,
        ledger=_base_ledger(state="CANCELLED_STOP", reason_code="CANCELLED"),
    )
    report = _run_observer(tmp_path, governed_cycle_evidence_dir=root)
    assert report["execution_lifecycle_completeness"] != "VENUE_ACK_WITNESSED"
    assert (
        "FULL_FILL" in report["missing_evidence_classes"]
        or "FILL" in report["missing_evidence_classes"]
    )


def test_i_g004_confirmed_filled_not_full_fill_lifecycle(tmp_path: Path):
    store = tmp_path / "g004_ok"
    store.mkdir()
    submit_attempt_id = "attempt-1"
    envelope_digest = "env-digest"
    record = {
        "contract_id": G004_CONTRACT_ID,
        "submit_attempt_id": submit_attempt_id,
        "clordid": "cl-1",
        "envelope_digest": envelope_digest,
        "attempt_digest": attempt_digest_v1(
            submit_attempt_id=submit_attempt_id,
            envelope_digest=envelope_digest,
        ),
        "native_id": "BTC-USDT-SWAP",
        "reconciliation_outcome": "CONFIRMED_FILLED",
        "typed_post_submit_outcome": "ACKNOWLEDGED",
        "local_submit_outcome": "SUBMITTED",
        "ack_is_not_fill": True,
    }
    (store / "full_core_post_attempt_exchange_reconciliation_disposition_v1.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    report = _run_observer(tmp_path, g004_post_attempt_store_root=store, recon_dir=CAP11_FIXTURE)
    assert report["execution_lifecycle_completeness"] == "VENUE_ACK_WITNESSED"
    assert report["execution_lifecycle_completeness"] != "FILL_WITNESSED"


def test_j_missing_ack_fill_stays_below_ack(tmp_path: Path):
    report = _run_observer(tmp_path, recon_dir=CAP11_FIXTURE)
    assert report["execution_lifecycle_completeness"] not in {
        "VENUE_ACK_WITNESSED",
        "FILL_WITNESSED",
    }


def test_k_pre_external_only_fixture(tmp_path: Path):
    if not PRE_EXTERNAL_FIXTURE.is_file():
        pytest.skip("fixture missing")
    report = _run_observer(tmp_path, pre_external_report=PRE_EXTERNAL_FIXTURE)
    assert report["execution_lifecycle_completeness"] == "PRE_EXTERNAL_ONLY"
    assert "POST_SUBMISSION_WITNESS" in report["missing_evidence_classes"]


def test_l_current_productive_run_20261012_l10(tmp_path: Path):
    if not (L10_RUN / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").is_file():
        pytest.skip("productive L10 run not available on this machine")
    if not L10_CYCLE.is_dir():
        pytest.skip("productive L10 cycle dir missing")
    report = _run_observer(
        tmp_path,
        trade_id="e0ac0f0955d15a0b",
        pre_external_report=L10_RUN / "PRE_EXTERNAL_CONVERGENCE_REPORT.json",
        governed_cycle_evidence_dir=L10_CYCLE,
        recon_dir=L10_RECON,
        repository_root=PRIMARY_REPO,
    )
    assert report["observer_run_success"] is True
    assert report["execution_lifecycle_completeness"] == "PRE_EXTERNAL_ONLY"
    assert report["lifecycle_adjudication"]["confirmed_venue_post_submission"] is False
    assert report["ghosv_traffic_light"] == "YELLOW"
