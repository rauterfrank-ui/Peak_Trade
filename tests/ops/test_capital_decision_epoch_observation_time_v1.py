"""Decision scope and actual observation time survive the original Treasury join."""

from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
    build_default_full_core_u04_p01_eligibility_host_inputs_v1,
    execute_current_productive_treasury_single_source_capital_handoff_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_base_binding_v1 import (
    clear_current_productive_base_binding_state_v1,
)
from tests.ops.test_full_core_treasury_single_source_capital_handoff_v1 import (
    _minimal_margin_observation_v1,
    DEFAULT_INSTRUMENT_ID,
)


@pytest.fixture(autouse=True)
def isolated_original_base_owner():
    clear_current_productive_base_binding_state_v1()
    yield
    clear_current_productive_base_binding_state_v1()


def _later(epoch):
    return (datetime.fromisoformat(epoch.replace("Z", "+00:00")) + timedelta(seconds=1)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _handoff(observation):
    return execute_current_productive_treasury_single_source_capital_handoff_v1(
        margin_observation=observation,
        instrument_id=DEFAULT_INSTRUMENT_ID,
        body_sha256=observation.provenance_digest,
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        live_account_bound_status="TRUSTED_PRESENT",
        u04_p01_host_inputs=build_default_full_core_u04_p01_eligibility_host_inputs_v1(
            raw_acct_lv="2"
        ),
    )


def test_observation_after_decision_keeps_original_scope_without_changing_capital():
    original = _minimal_margin_observation_v1()
    baseline = _handoff(original)
    assert not baseline.fail_closed
    later = replace(original, observed_at_as_of=_later(original.decision_epoch))
    result = _handoff(later)
    assert not result.fail_closed, result.reason_codes
    assert result.producer_output.value == baseline.producer_output.value
    assert result.p01_fact.decision_epoch == original.decision_epoch
    assert result.p01_fact.observed_at_as_of == later.observed_at_as_of
    assert result.eligibility_fact.decision_epoch == original.decision_epoch


@pytest.mark.parametrize("age", ["999", "NaN", "-1"])
def test_separate_capture_time_does_not_relax_freshness(age):
    original = _minimal_margin_observation_v1()
    changed = replace(original, observed_at_as_of=_later(original.decision_epoch), age_seconds=age)
    result = _handoff(changed)
    assert result.fail_closed


def test_duplicate_observation_advances_known_time_without_extra_capital():
    original = _minimal_margin_observation_v1()
    assert not _handoff(original).fail_closed
    later = replace(original, observed_at_as_of=_later(_later(original.decision_epoch)))
    repeated = _handoff(later)
    assert not repeated.fail_closed
    assert repeated.producer_output.value == original.value
    assert repeated.p01_fact.observed_at_as_of == later.observed_at_as_of
    older_different = replace(
        original,
        observed_at_as_of=_later(original.decision_epoch),
        value="1001",
        provenance_digest="d" * 64,
    )
    denied = _handoff(older_different)
    assert denied.fail_closed
    assert "OLD_REPLAY_AFTER_NEWER_STATE_FAIL_CLOSED" in denied.reason_codes


def test_identical_acquisition_keeps_elapsed_age_in_derived_peer_facts():
    original = _minimal_margin_observation_v1()
    assert not _handoff(original).fail_closed
    repeated = _handoff(replace(original, age_seconds="3"))
    assert not repeated.fail_closed
    assert repeated.p01_fact.age_seconds == "3"
    assert repeated.p01_fact.observed_at_as_of == original.observed_at_as_of
    assert repeated.producer_output.value == original.value


def test_identical_fingerprint_cannot_introduce_a_different_capital_amount():
    original = _minimal_margin_observation_v1()
    assert not _handoff(original).fail_closed
    changed = _handoff(replace(original, value="1001"))
    assert changed.fail_closed
    assert "EVIDENCE_FINGERPRINT_CONTENT_MISMATCH" in changed.reason_codes


@pytest.mark.parametrize(
    "peer,field",
    [
        ("u04", "decision_epoch"),
        ("u04", "observed_at_as_of"),
        ("p01", "decision_epoch"),
        ("p01", "observed_at_as_of"),
    ],
)
def test_peer_decision_scope_and_capture_time_still_must_match(peer, field):
    from tests.ops.test_full_core_current_productive_available_for_sizing_producer_v1 import (
        _base,
        _u04,
        _p01,
        _eligibility,
        EPOCH,
        produce_current_productive_available_for_sizing_v1,
    )

    later = _later(_minimal_margin_observation_v1().observed_at_as_of)
    base = _base(observed_at_as_of=later)
    u04 = _u04(observed_at_as_of=later)
    p01 = _p01(observed_at_as_of=later)
    ok = produce_current_productive_available_for_sizing_v1(
        base=base, u04=u04, p01=p01, eligibility=_eligibility()
    )
    assert ok.produced == "true"
    wrong = {field: _later(later)}
    if peer == "u04":
        u04 = replace(u04, **wrong)
    else:
        p01 = replace(p01, **wrong)
    denied = produce_current_productive_available_for_sizing_v1(
        base=base, u04=u04, p01=p01, eligibility=_eligibility()
    )
    assert denied.produced == "false"
    assert f"{peer.upper()}_EPOCH_MISMATCH" in denied.reason_codes
