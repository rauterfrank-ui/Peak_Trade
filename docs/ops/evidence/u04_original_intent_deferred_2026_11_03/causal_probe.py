from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile

from src.ops.full_core_live_path_composition_root_v1 import current_productive_treasury_single_source_capital_handoff_v1 as handoff_module
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import FreshPretradeGetStatusV1, LiveAccountBoundStatusV1
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_models_v1 import CurrentProductiveU04ReservationTypedEvidenceV1
from tests.ops.test_full_core_treasury_single_source_capital_handoff_v1 import _minimal_margin_observation_v1
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import _host_enter_cycle, _join, _injected, _balance_payload
from src.learning.deterministic_decision_outcome_v0.capture_v0 import DdoCaptureBindingV0, bind_capture_session_v0, reset_capture_session_v0, bind_host_cycle_capture_context_v0
from unittest.mock import patch

root = Path(tempfile.mkdtemp(prefix='peaktrade-u04-causal-probe-'))
cases = []
original = handoff_module.join_treasury_observation_through_e4_into_productive_account_equity_host_v1
for amount in ('0', '25', '1001'):
    trace = []
    def observed_host(*args, **kwargs):
        out = original(*args, **kwargs)
        trace.append(out)
        return out
    witness = CurrentProductiveU04ReservationTypedEvidenceV1(
        reservation_value_raw=amount,
        empty_reservation_proven='true' if amount == '0' else 'false',
        witness_kind='EXPLICIT_SYNTHETIC_PROBE_NOT_ACCOUNT_EVIDENCE',
        witness_digest=hashlib.sha256(('u04-probe:' + amount).encode()).hexdigest(),
    )
    host_inputs = replace(handoff_module.build_default_full_core_u04_p01_eligibility_host_inputs_v1(raw_acct_lv='2'), u04_evidence=witness)
    observation = _minimal_margin_observation_v1()
    with patch.object(handoff_module, 'join_treasury_observation_through_e4_into_productive_account_equity_host_v1', observed_host):
        out = handoff_module.execute_current_productive_treasury_single_source_capital_handoff_v1(
            margin_observation=observation, instrument_id=observation.bound_instrument_identity if hasattr(observation, 'bound_instrument_identity') else 'SUI-USDC-SWAP',
            body_sha256='c' * 64,
            fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
            live_account_bound_status=LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
            u04_p01_host_inputs=host_inputs,
        )
    binding = trace[0].u04_p01_eligibility_binding
    cases.append({'synthetic_u04': amount, 'ct_output': binding.producer_output.value,
                  'ct_produced': binding.producer_output.produced,
                  'final_risk_output': out.producer_output.value,
                  'final_u04_applied': out.producer_output.u04_applied,
                  'final_provenance': out.producer_output.input_set_digest,
                  'handoff_fail_closed': out.fail_closed})

_, cycle, _ = _host_enter_cycle()
capture = DdoCaptureBindingV0(enabled=True, ledger_path=root / 'active_capture.jsonl')
bind_host_cycle_capture_context_v0(capture, event_ts_unix=1_700_000_120, session_id='u04-causal-probe', cycle_index=1, repository_sha='aadba02744b20de9fa2129765b53a8504933b757')
capture.capture_scope_config_hash = 'a' * 64
token = bind_capture_session_v0(capture)
try:
    result = _join(replay=cycle.replay, injected=_injected(payload=_balance_payload()))
finally:
    reset_capture_session_v0(token)
assert result.status == 'PASS', result.first_blocker
assert (root / 'active_capture.jsonl').exists(), (capture.last_error, capture.last_result)
before = (root / 'active_capture.jsonl').read_bytes()
inactive = _join(replay=cycle.replay, injected=_injected(payload=_balance_payload()))
assert inactive.status == 'PASS'
assert (root / 'active_capture.jsonl').read_bytes() == before
text = before.decode()
records = [json.loads(line)['payload'] for line in text.splitlines()]
summary = {'baseline_cases': cases,
    'capture_with_active_context': {'records': len(records),
        'producer_ids': [r.get('producer_id') for r in records],
        'risk_seam_present': any(r.get('producer_id') == 'capital_risk_sizing_v1' for r in records),
        'intent_seam_present': any(r.get('producer_id') == 'canonical_order_intent_v1' for r in records),
        'risk_snapshot_refs': [r.get('risk_snapshot_ref') for r in records],
        'decision_types': [r.get('decision_type') for r in records]},
    'join_after_context_reset_appends_to_same_capture': False,
    'raw_probe_dir': str(root),
    'scope': 'Injected synthetic branch sensitivity and explicit capture context; not account evidence or a learner/promotion run'}
(root / 'probe_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
