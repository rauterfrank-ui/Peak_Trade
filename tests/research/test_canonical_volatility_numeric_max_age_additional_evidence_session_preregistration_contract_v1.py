"""Focused tests for additional evidence session preregistration contract v1."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.constants_v1 import (
    ARTIFACT_RELATIVE_PATH,
    BOUND_DESIGN_DIGEST,
    BOUND_REPOSITORY_SHA,
    BOUND_RUNBOOK_DIGEST,
    EXISTING_EXHAUSTED_SESSION_IDS,
    MINIMUM_MAXIMUM_CYCLES_PER_SESSION,
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
    mutated = copy.deepcopy(candidate)
    mutated["authorization_optional"] = True
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="authorization_optional_forbidden",
    ):
        validate_additional_evidence_session_preregistration_candidate_v1(mutated)
    mutated2 = copy.deepcopy(candidate)
    mutated2["authorization_reusable"] = True
    with pytest.raises(
        AdditionalEvidenceSessionPreregistrationContractError,
        match="authorization_reusable_forbidden",
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


def test_16_contract_artifact_verifies_and_operator_workflow() -> None:
    artifact = verify_additional_evidence_session_preregistration_contract_artifact_v1(
        repo_root=ROOT
    )
    assert artifact["minimum_additional_productive_sessions"] == 2
    assert list(artifact["target_age_buckets_seconds"]) == list(TARGET_AGE_BUCKETS_SECONDS)
    assert list(artifact["operator_workflow"]) == list(OPERATOR_WORKFLOW)
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
