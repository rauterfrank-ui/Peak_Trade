import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
    load_apply_ledger_entries_v1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
    append_threshold_revocation_ledger_entry_v1,
    initialize_empty_threshold_revocation_ledger_v1,
    load_threshold_ledger_entries_v1,
)
from src.governance.governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1 import (
    GovernedF1M9RuntimeApplyStartRequestV1,
    run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1,
)
from src.ops.f1_m9_applied_offline_replay_v1 import (
    read_f1_m9_applied_offline_replay_v1,
    run_and_write_f1_m9_applied_offline_replay_v1,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _market_context,
    _replay_input,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
    evaluate_typed_volatility_binding_eligibility_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    build_canonical_volatility_estimate_v1,
)

ROOT = Path(__file__).resolve().parents[2]
APPLIED_AT = datetime(2026, 11, 12, 7, 30, tzinfo=timezone.utc)
MARKET_AT = APPLIED_AT + timedelta(minutes=10)
EVALUATED_AT = MARKET_AT + timedelta(minutes=10)


@pytest.fixture
def owner_state(tmp_path):
    ledgers = tmp_path / "owner-ledgers"
    ledgers.mkdir()
    applies = F1M9ProductiveApplyLedgerPathsV1(
        ledgers / "apply.jsonl", ledgers / "apply-revocation.jsonl"
    )
    thresholds = F1M9ThresholdValueAuthorizationLedgerPathsV1(
        ledgers / "threshold.jsonl", ledgers / "threshold-revocation.jsonl"
    )
    initialize_empty_revocation_ledger_v1(applies.revocation_ledger_path)
    initialize_empty_threshold_revocation_ledger_v1(thresholds.threshold_revocation_ledger_path)
    result = run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1(
        GovernedF1M9RuntimeApplyStartRequestV1(
            apply_ledger_paths=applies,
            threshold_ledger_paths=thresholds,
            repo_root=ROOT,
            evaluation_time_utc=APPLIED_AT,
        )
    )
    assert result.status == "CONTINUATION_COMPLETE", result.blocking_reasons
    assert result.productive_apply_occurred is True
    assert result.external_effect is False
    return ledgers, applies, thresholds, result.bound_seam_record


def _input(*, market_at=MARKET_AT):
    estimate = build_canonical_volatility_estimate_v1(
        value=0.004321,
        observation_count=61,
        as_of_event_time=market_at - timedelta(hours=2),
        fallback_used=False,
        source_digest="b" * 64,
    )
    context = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        _market_context(
            volatility_estimate=0.0,
            market_event_time=market_at.isoformat(),
            decision_time=(market_at + timedelta(seconds=1)).isoformat(),
        ),
        estimate,
    )
    return _replay_input(
        canonical_market_context=context,
        require_productive_typed_volatility_presence_gate=True,
        productive_typed_volatility_binding_eligibility=evaluate_typed_volatility_binding_eligibility_v1(
            context
        ),
    )


def _run(owner_state, out_dir, *, market_at=MARKET_AT, evaluation_time=EVALUATED_AT):
    _, applies, thresholds, _ = owner_state
    return run_and_write_f1_m9_applied_offline_replay_v1(
        repo_root=ROOT,
        apply_ledger_paths=applies,
        threshold_ledger_paths=thresholds,
        evaluation_time_utc=evaluation_time,
        replay_input=_input(market_at=market_at),
        out_dir=out_dir,
    )


def _snapshot(root):
    return {path.name: path.read_bytes() for path in root.iterdir()}


def test_original_applied_configuration_reaches_host_and_reads_back_in_new_process(
    owner_state, tmp_path
):
    root, applies, thresholds, seam = owner_state
    before = _snapshot(root)
    path, digest = _run(owner_state, tmp_path / "first")
    archive = read_f1_m9_applied_offline_replay_v1(evidence_path=path, expected_sha256=digest)
    evidence, host = archive["evidence"], archive["host"]
    [apply] = load_apply_ledger_entries_v1(applies.apply_ledger_path)
    [threshold] = load_threshold_ledger_entries_v1(thresholds.threshold_ledger_path)
    assert evidence["apply_ledger_entry"] == apply
    assert evidence["threshold_ledger_entry"] == threshold
    assert evidence["configuration_digest"] == seam["configuration_digest"]
    assert evidence["threshold_seconds"] == host["observation"]["threshold_seconds"] == 600.0
    assert (
        host["observation"]["owner_apply_record_digest"]
        == apply["owner_apply_authorization_record_digest"]
    )
    assert host["observation"]["seam_digest"] == seam["seam_digest"]
    assert host["observation"]["local_alpha_allowed"] is False
    assert host["observation"]["effective_host_alpha_allowed"] is True
    assert host["execution_eligible"] is False

    _, repeated_digest = _run(owner_state, tmp_path / "repeat")
    assert repeated_digest == digest
    assert _snapshot(root) == before
    code = """
import json, sys
from pathlib import Path
from src.ops.f1_m9_applied_offline_replay_v1 import read_f1_m9_applied_offline_replay_v1
print(json.dumps(read_f1_m9_applied_offline_replay_v1(
    evidence_path=Path(sys.argv[1]), expected_sha256=sys.argv[2]
)))
"""
    cold = subprocess.run(
        ["./scripts/pt", "-c", code, str(path), digest],
        cwd=ROOT,
        capture_output=True,
        check=True,
        text=True,
    )
    assert json.loads(cold.stdout.splitlines()[-1]) == archive


@pytest.mark.parametrize("change", ["missing", "duplicate", "revoked", "expired", "too_early"])
def test_owner_readback_refuses_ineligible_history_without_writing(owner_state, tmp_path, change):
    root, applies, thresholds, _ = owner_state
    market_at = MARKET_AT
    evaluation_time = EVALUATED_AT
    if change == "missing":
        thresholds.threshold_ledger_path.write_bytes(b"")
        expected = "REQUIRES_UNIQUE_OWNER_ENTRIES"
    elif change == "duplicate":
        content = applies.apply_ledger_path.read_bytes()
        applies.apply_ledger_path.write_bytes(content + content)
        expected = "REQUIRES_UNIQUE_OWNER_ENTRIES"
    elif change == "revoked":
        [entry] = load_threshold_ledger_entries_v1(thresholds.threshold_ledger_path)
        append_threshold_revocation_ledger_entry_v1(
            revocation_ledger_path=thresholds.threshold_revocation_ledger_path,
            threshold_value_authorization_record_digest=entry[
                "threshold_value_authorization_record_digest"
            ],
            configuration_digest=entry["configuration_digest"],
            reason="offline revocation test",
            operator_reference="offline test fixture",
            revoked_at=(APPLIED_AT + timedelta(minutes=1)).isoformat(),
        )
        expected = "threshold_value_authorization_revoked"
    elif change == "expired":
        evaluation_time = datetime(2027, 10, 1, tzinfo=timezone.utc)
        expected = "APPLY_EXPIRED"
    else:
        market_at = APPLIED_AT - timedelta(minutes=1)
        expected = "DECISION_TIME_MISMATCH"

    before = _snapshot(root)
    output = tmp_path / "rejected"
    with pytest.raises(ValueError, match=expected):
        _run(owner_state, output, market_at=market_at, evaluation_time=evaluation_time)
    assert not output.exists()
    assert _snapshot(root) == before
