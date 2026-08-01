"""Focused tests for additional evidence session preregistration contract hardening."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.constants_v1 import (
    ARTIFACT_RELATIVE_PATH,
    BOUND_DESIGN_DIGEST,
    BOUND_REPOSITORY_SHA,
    BOUND_RUNBOOK_DIGEST,
    CANDIDATE_SCHEMA_VERSION,
    CAPABILITY_VERSION,
    EXISTING_EXHAUSTED_CAMPAIGN_ID,
    EXISTING_EXHAUSTED_SESSION_IDS,
    EXPECTED_INSTRUMENT,
    EXPECTED_NETWORK_SCOPE,
    EXPECTED_SESSION_SCOPE,
    EXPECTED_VENUE,
    FORBIDDEN_AUTHORITY_FIELD_NAMES,
    HARDENING_CAPABILITY_ID,
    MINIMUM_MAXIMUM_CYCLES_PER_SESSION,
    MINIMUM_MAXIMUM_REQUESTS_PER_SESSION,
    MINIMUM_SESSION_DURATION_SECONDS,
    OPERATOR_WORKFLOW,
    TARGET_AGE_BUCKETS_SECONDS,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.contract_v1 import (
    build_additional_evidence_session_preregistration_contract_v1,
    build_example_additional_session_candidate_pair_v1,
    build_example_additional_session_candidate_v1,
    compute_candidate_preregistration_digest_v1,
    render_additional_evidence_session_preregistration_contract_v1,
    verify_additional_evidence_session_preregistration_contract_artifact_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.models_v1 import (
    AdditionalEvidenceSessionPreregistrationContractError,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.validate_v1 import (
    validate_additional_evidence_session_preregistration_candidate_v1,
)
from trading.master_v2.canonical_volatility_hot_path_contract_closure_v1 import (
    EXIT_PRECEDENCE_PRESERVED,
    REVERSAL_REDUCE_FIRST_PRESERVED,
)

ROOT = Path(__file__).resolve().parents[2]
EXISTING_PREREG_PATH = ROOT / (
    "config/research/"
    "canonical_volatility_numeric_max_age_productive_evidence_session_preregistration_v1.json"
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rehash(payload: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(payload)
    out.pop("preregistration_digest", None)
    out["preregistration_digest"] = compute_candidate_preregistration_digest_v1(out)
    return out


def _valid_payload() -> dict[str, Any]:
    return build_example_additional_session_candidate_v1().to_dict()


def test_01_two_new_unique_session_ids() -> None:
    a, b = build_example_additional_session_candidate_pair_v1()
    assert a.session_id != b.session_id
    assert a.session_id not in EXISTING_EXHAUSTED_SESSION_IDS
    assert b.session_id not in EXISTING_EXHAUSTED_SESSION_IDS
    validate_additional_evidence_session_preregistration_candidate_v1(a.to_dict())
    validate_additional_evidence_session_preregistration_candidate_v1(b.to_dict())


def test_02_s01_s02_reuse_rejected() -> None:
    for exhausted in EXISTING_EXHAUSTED_SESSION_IDS:
        with pytest.raises(
            AdditionalEvidenceSessionPreregistrationContractError,
            match="exhausted|terminal",
        ):
            candidate = build_example_additional_session_candidate_v1(
                session_id=exhausted,
            )
            validate_additional_evidence_session_preregistration_candidate_v1(candidate.to_dict())


def test_03_cycles_181_rejected_182_accepted() -> None:
    bad = build_example_additional_session_candidate_v1(
        maximum_cycles_per_session=181,
        maximum_requests_per_session=181,
    )
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="maximum_cycles_below_minimum_182",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())

    good = build_example_additional_session_candidate_v1(
        maximum_cycles_per_session=MINIMUM_MAXIMUM_CYCLES_PER_SESSION,
        maximum_requests_per_session=MINIMUM_MAXIMUM_CYCLES_PER_SESSION,
    )
    assert (
        validate_additional_evidence_session_preregistration_candidate_v1(good.to_dict())["valid"]
        is True
    )


def test_04_requests_lt_cycles_rejected() -> None:
    bad = build_example_additional_session_candidate_v1(
        maximum_cycles_per_session=200,
        maximum_requests_per_session=199,
    )
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="requests_must_be_gte_cycles",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())


def test_05_duration_10859_rejected_10860_accepted() -> None:
    bad = build_example_additional_session_candidate_v1(duration_seconds=10859)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="duration_below_minimum_10860",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())

    good = build_example_additional_session_candidate_v1(
        duration_seconds=MINIMUM_SESSION_DURATION_SECONDS
    )
    assert (
        validate_additional_evidence_session_preregistration_candidate_v1(good.to_dict())["valid"]
        is True
    )


def test_06_missing_7200_bucket_rejected() -> None:
    buckets = tuple(x for x in TARGET_AGE_BUCKETS_SECONDS if x != 7200)
    bad = build_example_additional_session_candidate_v1(target_age_buckets_seconds=buckets)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="target_age_buckets_mismatch|missing_age_7200",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())


def test_07_missing_recompute_contract_rejected() -> None:
    bad = build_example_additional_session_candidate_v1(recompute_after_age_floor_required=False)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="recompute_after_age_floor_required_required_true",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())


def test_08_missing_post_recompute_fresh_rejected() -> None:
    bad = build_example_additional_session_candidate_v1(
        post_recompute_fresh_observation_required=False
    )
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="post_recompute_fresh_observation_required_required_true",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())


def test_09_artificial_age_time_overrides_rejected() -> None:
    good = build_example_additional_session_candidate_v1().to_dict()
    for flag in (
        "ARTIFICIAL_DELAY_INJECTION",
        "SYNTHETIC_EVENT_TIME_ADVANCE",
        "AGE_OVERRIDE",
        "AS_OF_OVERRIDE",
        "RECOMPUTE_FORCE_FLAG",
    ):
        mutated = copy.deepcopy(good)
        mutated["forbidden_artificial_controls"][flag] = True
        with pytest.raises(
            AdditionalEvidenceSessionPreregistrationContractError,
            match="artificial_control_forbidden",
        ):
            validate_additional_evidence_session_preregistration_candidate_v1(mutated)


def test_10_repository_sha_binding() -> None:
    contract = build_additional_evidence_session_preregistration_contract_v1()
    assert contract.repository_sha == BOUND_REPOSITORY_SHA
    assert BOUND_REPOSITORY_SHA == "790065c2417a0006bef97b3496bfef30739e9ff3"
    accepted = build_example_additional_session_candidate_v1(repository_sha=BOUND_REPOSITORY_SHA)
    assert (
        validate_additional_evidence_session_preregistration_candidate_v1(accepted.to_dict())[
            "valid"
        ]
        is True
    )
    # Pre-rebase natural-age wiring SHA must remain rejected after rebase.
    legacy = build_example_additional_session_candidate_v1(
        repository_sha="bb5b1f4572deb451d238f890482254c690c164d2"
    )
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="repository_sha_mismatch",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(legacy.to_dict())
    bad = build_example_additional_session_candidate_v1(repository_sha="0" * 40)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="repository_sha_mismatch",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())


def test_11_digest_bindings() -> None:
    contract = build_additional_evidence_session_preregistration_contract_v1()
    assert contract.design_digest == BOUND_DESIGN_DIGEST
    assert contract.runbook_digest == BOUND_RUNBOOK_DIGEST
    bad_design = build_example_additional_session_candidate_v1(design_digest="0" * 64)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="design_digest_mismatch",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad_design.to_dict())
    bad_runbook = build_example_additional_session_candidate_v1(runbook_digest="1" * 64)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="runbook_digest_mismatch",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad_runbook.to_dict())


def test_12_authorization_per_session_binding() -> None:
    candidate = build_example_additional_session_candidate_v1().to_dict()
    binding = candidate["authorization_binding"]
    assert binding["maximum_session_count"] == 1
    assert binding["session_ids"] == [candidate["session_id"]]
    assert binding["single_use_authorization_required"] is True
    mutated = _rehash({**candidate, "authorization_optional": True})
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="unknown_candidate_fields:authorization_optional",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(mutated)
    mutated2 = _rehash({**candidate, "authorization_reusable": True})
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="unknown_candidate_fields:authorization_reusable",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(mutated2)


def test_13_deterministic_preregistration_digest() -> None:
    a = build_example_additional_session_candidate_v1(session_index=1)
    b = build_example_additional_session_candidate_v1(session_index=1)
    assert a.preregistration_digest == b.preregistration_digest
    assert a.preregistration_digest == compute_candidate_preregistration_digest_v1(a.to_dict())
    contract_a = render_additional_evidence_session_preregistration_contract_v1()
    contract_b = render_additional_evidence_session_preregistration_contract_v1()
    assert contract_a == contract_b
    assert contract_a["contract_digest"] == contract_b["contract_digest"]


def test_14_existing_s01_s02_fixtures_unchanged() -> None:
    before = _sha256_file(EXISTING_PREREG_PATH)
    _ = build_additional_evidence_session_preregistration_contract_v1()
    _ = build_example_additional_session_candidate_pair_v1()
    assert_architecture_guards_v1(repo_root=ROOT)
    after = _sha256_file(EXISTING_PREREG_PATH)
    assert before == after
    payload = json.loads(EXISTING_PREREG_PATH.read_text(encoding="utf-8"))
    ids = [s["session_id"] for s in payload["sessions"]]
    assert ids == list(EXISTING_EXHAUSTED_SESSION_IDS)


def test_15_master_v2_double_play_architecture_guards_unchanged() -> None:
    assert EXIT_PRECEDENCE_PRESERVED is True
    assert REVERSAL_REDUCE_FIRST_PRESERVED is True
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["SECOND_AGE_AUTHORITY_PRESENT"] is False
    assert guards["SECOND_DECISION_AUTHORITY_PRESENT"] is False
    assert guards["HARD_STOP"] is True
    assert guards["SESSION_PREREGISTRATION_CREATION_AUTHORIZED"] is False
    assert guards["candidate_schema_closed_world"] is True
    assert guards["hardening_capability_id"] == HARDENING_CAPABILITY_ID


def test_16_contract_artifact_verifies_and_operator_workflow() -> None:
    artifact = verify_additional_evidence_session_preregistration_contract_artifact_v1(
        repo_root=ROOT
    )
    assert artifact["minimum_additional_productive_sessions"] == 2
    assert list(artifact["target_age_buckets_seconds"]) == list(TARGET_AGE_BUCKETS_SECONDS)
    assert list(artifact["operator_workflow"]) == list(OPERATOR_WORKFLOW)
    assert artifact["candidate_schema_version"] == CANDIDATE_SCHEMA_VERSION
    assert artifact["expected_venue"] == EXPECTED_VENUE
    assert artifact["expected_instrument"] == EXPECTED_INSTRUMENT
    assert artifact["expected_network_scope"] == EXPECTED_NETWORK_SCOPE
    assert artifact["expected_session_scope"] == EXPECTED_SESSION_SCOPE
    assert artifact["candidate_schema_closed_world"] is True
    assert (ROOT / ARTIFACT_RELATIVE_PATH).is_file()


def test_17_post_first_produce_span_floor() -> None:
    bad = build_example_additional_session_candidate_v1(post_first_produce_event_span_seconds=7259)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="post_first_produce_span_below_minimum_7260",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())


def test_18_terminal_used_session_rejected() -> None:
    a = build_example_additional_session_candidate_v1(session_index=1)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="session_id_already_terminal_used",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(
            a.to_dict(),
            terminal_session_ids={a.session_id},
        )


def test_19_no_creation_or_execution_authorized_on_contract() -> None:
    contract = build_additional_evidence_session_preregistration_contract_v1()
    assert contract.session_preregistration_creation_authorized is False
    assert contract.authorization_issuance_authorized is False
    assert contract.authorization_consumption_authorized is False
    assert contract.network_access_authorized is False
    assert contract.productive_session_execution_authorized is False
    assert contract.numeric_max_age_selected is False
    assert contract.numeric_max_age_enforcing is False
    assert contract.hard_stop is True


# --- TEIL F positive hardening matrix ---


def test_f01_exact_valid_candidate_accepted() -> None:
    result = validate_additional_evidence_session_preregistration_candidate_v1(_valid_payload())
    assert result["valid"] is True
    assert result["schema_version"] == CANDIDATE_SCHEMA_VERSION


def test_f02_minimum_floors_at_boundary_accepted() -> None:
    good = build_example_additional_session_candidate_v1(
        duration_seconds=MINIMUM_SESSION_DURATION_SECONDS,
        maximum_cycles_per_session=MINIMUM_MAXIMUM_CYCLES_PER_SESSION,
        maximum_requests_per_session=MINIMUM_MAXIMUM_REQUESTS_PER_SESSION,
    )
    assert (
        validate_additional_evidence_session_preregistration_candidate_v1(good.to_dict())["valid"]
        is True
    )


def test_f03_maximum_requests_equals_maximum_cycles_accepted() -> None:
    good = build_example_additional_session_candidate_v1(
        maximum_cycles_per_session=200,
        maximum_requests_per_session=200,
    )
    assert (
        validate_additional_evidence_session_preregistration_candidate_v1(good.to_dict())["valid"]
        is True
    )


def test_f04_exact_target_age_buckets_accepted() -> None:
    good = build_example_additional_session_candidate_v1(
        target_age_buckets_seconds=TARGET_AGE_BUCKETS_SECONDS
    )
    assert (
        validate_additional_evidence_session_preregistration_candidate_v1(good.to_dict())["valid"]
        is True
    )


def test_f05_exact_venue_binding_accepted() -> None:
    payload = _valid_payload()
    assert payload["venue"] == EXPECTED_VENUE
    assert validate_additional_evidence_session_preregistration_candidate_v1(payload)["venue"] == (
        EXPECTED_VENUE
    )


def test_f06_exact_instrument_binding_accepted() -> None:
    payload = _valid_payload()
    assert payload["instrument"] == EXPECTED_INSTRUMENT
    assert (
        validate_additional_evidence_session_preregistration_candidate_v1(payload)["instrument"]
        == EXPECTED_INSTRUMENT
    )


def test_f07_exact_network_scope_accepted() -> None:
    payload = _valid_payload()
    assert payload["network_scope"] == EXPECTED_NETWORK_SCOPE
    assert (
        validate_additional_evidence_session_preregistration_candidate_v1(payload)["network_scope"]
        == EXPECTED_NETWORK_SCOPE
    )


def test_f08_exact_session_scope_accepted() -> None:
    payload = _valid_payload()
    assert payload["session_scope"] == EXPECTED_SESSION_SCOPE
    assert (
        validate_additional_evidence_session_preregistration_candidate_v1(payload)["session_scope"]
        == EXPECTED_SESSION_SCOPE
    )


def test_f09_exact_candidate_schema_version_accepted() -> None:
    payload = _valid_payload()
    assert payload["schema_version"] == CANDIDATE_SCHEMA_VERSION
    assert (
        validate_additional_evidence_session_preregistration_candidate_v1(payload)["schema_version"]
        == CANDIDATE_SCHEMA_VERSION
    )


def test_f10_deterministic_candidate_digest_accepted() -> None:
    a = _valid_payload()
    b = build_example_additional_session_candidate_v1(session_index=1).to_dict()
    assert a["preregistration_digest"] == b["preregistration_digest"]
    validate_additional_evidence_session_preregistration_candidate_v1(a)


def test_f11_contract_builder_matches_frozen_json() -> None:
    rendered = render_additional_evidence_session_preregistration_contract_v1()
    frozen = json.loads((ROOT / ARTIFACT_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert rendered == frozen
    verify_additional_evidence_session_preregistration_contract_artifact_v1(repo_root=ROOT)


# --- TEIL G negative hardening matrix ---


@pytest.mark.parametrize(
    ("mutate", "error"),
    [
        (lambda p: (p.pop("schema_version"), p)[1], "candidate_schema_version_mismatch"),
        (lambda p: {**p, "schema_version": None}, "candidate_schema_version_mismatch"),
        (lambda p: {**p, "schema_version": ""}, "candidate_schema_version_mismatch"),
        (lambda p: {**p, "schema_version": "v999"}, "candidate_schema_version_mismatch"),
        (
            lambda p: {**p, "schema_version": CAPABILITY_VERSION},
            "candidate_schema_version_mismatch",
        ),
        (
            lambda p: {**p, "schema_version": CANDIDATE_SCHEMA_VERSION.upper()},
            "candidate_schema_version_mismatch",
        ),
        (
            lambda p: {**p, "schema_version": f" {CANDIDATE_SCHEMA_VERSION} "},
            "candidate_schema_version_mismatch",
        ),
        (lambda p: {**p, "schema_version": 1}, "candidate_schema_version_mismatch"),
    ],
    ids=[
        "schema_missing",
        "schema_null",
        "schema_empty",
        "schema_v999",
        "schema_contract_version",
        "schema_case",
        "schema_whitespace",
        "schema_non_string",
    ],
)
def test_g_schema_version_fail_closed(mutate, error) -> None:
    payload = _rehash(mutate(_valid_payload()))
    with pytest.raises(AdditionalEvidenceSessionPreregistrationContractError, match=error):
        validate_additional_evidence_session_preregistration_candidate_v1(payload)


@pytest.mark.parametrize(
    ("mutate", "error"),
    [
        (lambda p: (p.pop("venue"), p)[1], "venue_binding_mismatch"),
        (lambda p: {**p, "venue": "BINANCE"}, "venue_binding_mismatch"),
        (lambda p: {**p, "venue": ""}, "venue_binding_mismatch"),
        (lambda p: {**p, "venue": "okx"}, "venue_binding_mismatch"),
        (lambda p: {**p, "venue": " OKX "}, "venue_binding_mismatch"),
        (lambda p: {**p, "venue": ["OKX"]}, "venue_binding_mismatch"),
    ],
    ids=[
        "venue_missing",
        "venue_wrong",
        "venue_empty",
        "venue_case",
        "venue_whitespace",
        "venue_list",
    ],
)
def test_g_venue_fail_closed(mutate, error) -> None:
    payload = _rehash(mutate(_valid_payload()))
    with pytest.raises(AdditionalEvidenceSessionPreregistrationContractError, match=error):
        validate_additional_evidence_session_preregistration_candidate_v1(payload)


@pytest.mark.parametrize(
    ("mutate", "error"),
    [
        (lambda p: (p.pop("instrument"), p)[1], "instrument_binding_mismatch"),
        (lambda p: {**p, "instrument": "BTC-USD_UM_XPERP"}, "instrument_binding_mismatch"),
        (lambda p: {**p, "instrument": ""}, "instrument_binding_mismatch"),
        (
            lambda p: {**p, "instrument": EXPECTED_INSTRUMENT.lower()},
            "instrument_binding_mismatch",
        ),
        (
            lambda p: {**p, "instrument": f" {EXPECTED_INSTRUMENT} "},
            "instrument_binding_mismatch",
        ),
        (lambda p: {**p, "instrument": [EXPECTED_INSTRUMENT]}, "instrument_binding_mismatch"),
    ],
    ids=[
        "instrument_missing",
        "instrument_wrong",
        "instrument_empty",
        "instrument_case",
        "instrument_whitespace",
        "instrument_list",
    ],
)
def test_g_instrument_fail_closed(mutate, error) -> None:
    payload = _rehash(mutate(_valid_payload()))
    with pytest.raises(AdditionalEvidenceSessionPreregistrationContractError, match=error):
        validate_additional_evidence_session_preregistration_candidate_v1(payload)


@pytest.mark.parametrize(
    ("mutate", "error"),
    [
        (lambda p: (p.pop("network_scope"), p)[1], "network_scope_binding_mismatch"),
        (lambda p: {**p, "network_scope": "PUBLIC"}, "network_scope_binding_mismatch"),
        (lambda p: {**p, "network_scope": ""}, "network_scope_binding_mismatch"),
        (
            lambda p: {**p, "network_scope": EXPECTED_NETWORK_SCOPE.lower()},
            "network_scope_binding_mismatch",
        ),
        (
            lambda p: {**p, "network_scope": f" {EXPECTED_NETWORK_SCOPE} "},
            "network_scope_binding_mismatch",
        ),
        (
            lambda p: {**p, "network_scope": [EXPECTED_NETWORK_SCOPE]},
            "network_scope_binding_mismatch",
        ),
    ],
    ids=[
        "network_missing",
        "network_wrong",
        "network_empty",
        "network_case",
        "network_whitespace",
        "network_list",
    ],
)
def test_g_network_scope_fail_closed(mutate, error) -> None:
    payload = _rehash(mutate(_valid_payload()))
    with pytest.raises(AdditionalEvidenceSessionPreregistrationContractError, match=error):
        validate_additional_evidence_session_preregistration_candidate_v1(payload)


@pytest.mark.parametrize(
    ("mutate", "error"),
    [
        (lambda p: (p.pop("session_scope"), p)[1], "session_scope_binding_mismatch"),
        (lambda p: {**p, "session_scope": "OTHER"}, "session_scope_binding_mismatch"),
        (lambda p: {**p, "session_scope": ""}, "session_scope_binding_mismatch"),
        (
            lambda p: {**p, "session_scope": EXPECTED_SESSION_SCOPE.lower()},
            "session_scope_binding_mismatch",
        ),
        (
            lambda p: {**p, "session_scope": f" {EXPECTED_SESSION_SCOPE} "},
            "session_scope_binding_mismatch",
        ),
        (
            lambda p: {**p, "session_scope": [EXPECTED_SESSION_SCOPE]},
            "session_scope_binding_mismatch",
        ),
    ],
    ids=[
        "session_missing",
        "session_wrong",
        "session_empty",
        "session_case",
        "session_whitespace",
        "session_list",
    ],
)
def test_g_session_scope_fail_closed(mutate, error) -> None:
    payload = _rehash(mutate(_valid_payload()))
    with pytest.raises(AdditionalEvidenceSessionPreregistrationContractError, match=error):
        validate_additional_evidence_session_preregistration_candidate_v1(payload)


def test_g33_unknown_neutral_field_rejected() -> None:
    payload = _rehash({**_valid_payload(), "forward_compat_note": "x"})
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="unknown_candidate_fields:forward_compat_note",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(payload)


@pytest.mark.parametrize("field", FORBIDDEN_AUTHORITY_FIELD_NAMES)
def test_g_authority_fields_true_rejected(field: str) -> None:
    payload = _rehash({**_valid_payload(), field: True})
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match=f"unknown_candidate_fields:{field}",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(payload)


def test_g35_trading_decision_authority_false_rejected() -> None:
    payload = _rehash({**_valid_payload(), "trading_decision_authority": False})
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="unknown_candidate_fields:trading_decision_authority",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(payload)


def test_g45_multiple_unknown_fields_rejected() -> None:
    payload = _rehash(
        {
            **_valid_payload(),
            "zzz_extra": 1,
            "aaa_extra": 2,
            "trading_decision_authority": True,
        }
    )
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match=("unknown_candidate_fields:aaa_extra,trading_decision_authority,zzz_extra"),
    ) as exc:
        validate_additional_evidence_session_preregistration_candidate_v1(payload)
    message = str(exc.value)
    keys = message.split("unknown_candidate_fields:", 1)[1].split(",")
    assert keys == sorted(keys)


def test_g46_unknown_fields_error_deterministically_sorted() -> None:
    payload = _rehash({**_valid_payload(), "m_field": 1, "b_field": 2, "a_field": 3})
    with pytest.raises(AdditionalEvidenceSessionPreregistrationContractError) as exc:
        validate_additional_evidence_session_preregistration_candidate_v1(payload)
    assert str(exc.value) == "unknown_candidate_fields:a_field,b_field,m_field"


def test_g47_unknown_nested_field_rejected() -> None:
    payload = _valid_payload()
    payload["authorization_binding"] = {
        **payload["authorization_binding"],
        "nested_extra_authority": True,
    }
    payload = _rehash(payload)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="unknown_candidate_fields:authorization_binding.nested_extra_authority",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(payload)


def test_g48_candidate_mutated_after_digest_rejected() -> None:
    payload = _valid_payload()
    payload["duration_seconds"] = MINIMUM_SESSION_DURATION_SECONDS + 1
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="preregistration_digest_mismatch",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(payload)


def test_g49_wrong_candidate_digest_rejected() -> None:
    payload = _valid_payload()
    payload["preregistration_digest"] = "0" * 64
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="preregistration_digest_mismatch",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(payload)


def test_g50_wrong_contract_digest_rejected(tmp_path: Path) -> None:
    rendered = render_additional_evidence_session_preregistration_contract_v1()
    rendered["contract_digest"] = "0" * 64
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(rendered, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="contract_digest_mismatch",
    ):
        verify_additional_evidence_session_preregistration_contract_artifact_v1(
            artifact_path=path,
            repo_root=ROOT,
        )


def test_g51_unknown_field_with_rehashed_digest_still_rejected() -> None:
    payload = _rehash({**_valid_payload(), "live_trading_authority": True})
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="unknown_candidate_fields:live_trading_authority",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(payload)


def test_g52_wrong_scope_with_rehashed_digest_still_rejected() -> None:
    payload = _rehash({**_valid_payload(), "venue": "BINANCE"})
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="venue_binding_mismatch",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(payload)


def test_g53_duration_10859_rejected() -> None:
    bad = build_example_additional_session_candidate_v1(duration_seconds=10859)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="duration_below_minimum_10860",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())


def test_g54_cycles_181_rejected() -> None:
    bad = build_example_additional_session_candidate_v1(
        maximum_cycles_per_session=181,
        maximum_requests_per_session=182,
    )
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="maximum_cycles_below_minimum_182",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())


def test_g55_requests_181_rejected() -> None:
    # cycles at floor, requests below independent request floor.
    payload = _valid_payload()
    payload["maximum_cycles_per_session"] = 182
    payload["maximum_requests_per_session"] = 181
    payload = _rehash(payload)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="maximum_requests_below_minimum_182",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(payload)


def test_g56_requests_lt_cycles_rejected() -> None:
    bad = build_example_additional_session_candidate_v1(
        maximum_cycles_per_session=200,
        maximum_requests_per_session=199,
    )
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="requests_must_be_gte_cycles",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())


def test_g57_bucket_missing_rejected() -> None:
    buckets = tuple(x for x in TARGET_AGE_BUCKETS_SECONDS if x != 600)
    bad = build_example_additional_session_candidate_v1(target_age_buckets_seconds=buckets)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="target_age_buckets_mismatch",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())


def test_g58_extra_bucket_rejected() -> None:
    buckets = TARGET_AGE_BUCKETS_SECONDS + (9999,)
    bad = build_example_additional_session_candidate_v1(target_age_buckets_seconds=buckets)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="target_age_buckets_mismatch",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())


def test_g59_age_7200_required_false_or_missing_rejected() -> None:
    bad = build_example_additional_session_candidate_v1(age_7200_observation_required=False)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="age_7200_observation_required_required_true",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())
    missing = _valid_payload()
    missing.pop("age_7200_observation_required")
    missing = _rehash(missing)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="age_7200_observation_required_required_true|missing_required_field",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(missing)


def test_g60_recompute_required_false_or_missing_rejected() -> None:
    bad = build_example_additional_session_candidate_v1(recompute_after_age_floor_required=False)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="recompute_after_age_floor_required_required_true",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())
    missing = _valid_payload()
    missing.pop("recompute_after_age_floor_required")
    missing = _rehash(missing)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="recompute_after_age_floor_required_required_true|missing_required_field",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(missing)


def test_g61_post_recompute_fresh_required_false_or_missing_rejected() -> None:
    bad = build_example_additional_session_candidate_v1(
        post_recompute_fresh_observation_required=False
    )
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="post_recompute_fresh_observation_required_required_true",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())
    missing = _valid_payload()
    missing.pop("post_recompute_fresh_observation_required")
    missing = _rehash(missing)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="post_recompute_fresh_observation_required_required_true|missing_required_field",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(missing)


def test_g62_s01_reuse_rejected() -> None:
    bad = build_example_additional_session_candidate_v1(
        session_id=EXISTING_EXHAUSTED_SESSION_IDS[0]
    )
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="exhausted|terminal",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())


def test_g63_s02_reuse_rejected() -> None:
    bad = build_example_additional_session_candidate_v1(
        session_id=EXISTING_EXHAUSTED_SESSION_IDS[1]
    )
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="exhausted|terminal",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(bad.to_dict())


def test_g64_campaign_namespace_reuse_rejected() -> None:
    payload = _valid_payload()
    payload["campaign_id"] = EXISTING_EXHAUSTED_CAMPAIGN_ID
    payload["authorization_binding"] = {
        **payload["authorization_binding"],
        "campaign_id": EXISTING_EXHAUSTED_CAMPAIGN_ID,
    }
    payload = _rehash(payload)
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="campaign_id_reuses_exhausted",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(payload)


def test_h_architecture_guards_hardening_semantics() -> None:
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["guards_pass"] is True
    assert guards["candidate_schema_closed_world"] is True
    assert guards["nested_objects_present"] is True
    assert guards["unknown_fields_rejected"] is True
    assert guards["unknown_authority_fields_rejected"] is True
    assert guards["candidate_schema_version"] == CANDIDATE_SCHEMA_VERSION
