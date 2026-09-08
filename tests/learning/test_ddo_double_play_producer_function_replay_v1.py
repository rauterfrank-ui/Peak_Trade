"""DDO Double-Play producer-function current-code replay v1 tests.

Offline in-memory A replay. Does not enable capture, bind a productive ledger,
send, or persist replay results.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Any

import pytest

from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    REPLAY_CAPTURE_ISOLATION_ENABLED,
    REPLAY_CAPTURE_ISOLATION_LEDGER_PATH,
    REPLAY_CAPTURE_ISOLATION_UNBOUND,
    DdoCaptureBindingV0,
    bind_capture_session_v0,
    ddo_replay_capture_disabled_isolation_is_pass_v0,
    ddo_replay_capture_disabled_isolation_reason_v0,
    reset_capture_session_v0,
)
from src.learning.deterministic_decision_outcome_v0.double_play_input_evidence_v1 import (
    CAPTURE_TIMING_BEFORE_PRODUCER_CALL,
    PRODUCER_FUNCTION_NAME,
    project_double_play_entry_exit_policy_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.double_play_observation_projection_v1 import (
    PRODUCER_CANONICAL_KEYS,
    build_double_play_entry_exit_observation_v1,
    project_entry_exit_policy_decision_v1,
)
from src.learning.deterministic_decision_outcome_v0.double_play_producer_function_replay_v1 import (
    HISTORICAL_CODE_PARITY_CLAIM,
    REPLAY_CLASS_LETTER,
    REPLAY_CLASS_OWNER_TOKEN,
    REPLAY_CLASS_SEMANTIC,
    REPLAY_TIMEOUT_POLICY,
    RESULT_DURABILITY,
    STATUS_MATCH,
    STATUS_MISMATCH,
    STATUS_REPLAY_BLOCKED,
    STATUS_REPLAY_INDETERMINATE,
    replay_double_play_producer_function_current_code_v1,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DoublePlayEntryExitPolicyV0,
    evaluate_double_play_entry_exit_policy_v0,
)
from tests.trading.master_v2.test_double_play_entry_exit_policy_v0 import _policy_input

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src" / "learning" / "deterministic_decision_outcome_v0"
REPLAY_PATH = PACKAGE_DIR / "double_play_producer_function_replay_v1.py"
CAPTURE_PATH = PACKAGE_DIR / "capture_v0.py"
EVENT_TIME = "2026-09-08T12:00:00Z"
CORR_ID = "ddo.corr.dp.fnreplay.v1"
CYCLE_ID = "cycle:dp:fnreplay:0001"
INPUT_RECORD_ID = "ddo.dpi.fnreplay.0001"
OUTPUT_RECORD_ID = "ddo.dpo.fnreplay.0001"
DECISION_REF = "ddo.dec.fnreplay.0001"

FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "src.live",
    "src.risk",
    "src.risk_layer",
    "src.governance.promotion",
    "src.ops",
    "requests",
    "httpx",
    "urllib",
)


def _isolation_binding(*, enabled: bool = False, ledger_path: Any = None) -> DdoCaptureBindingV0:
    return DdoCaptureBindingV0(enabled=enabled, ledger_path=ledger_path)


def _bind(binding: DdoCaptureBindingV0 | None) -> Any:
    return bind_capture_session_v0(binding)


def _typed_pair() -> tuple[Any, Any, Any]:
    inp = _policy_input()
    policy = DoublePlayEntryExitPolicyV0()
    decision = evaluate_double_play_entry_exit_policy_v0(inp, policy)
    evidence = project_double_play_entry_exit_policy_input_v1(
        inp,
        record_id=INPUT_RECORD_ID,
        event_time_utc=EVENT_TIME,
        correlation_id=CORR_ID,
        cycle_id=CYCLE_ID,
        decision_event_ref=DECISION_REF,
        typed_output_observation_ref=OUTPUT_RECORD_ID,
        producer_call_policy_version=str(policy.policy_version),
        capture_timing=CAPTURE_TIMING_BEFORE_PRODUCER_CALL,
    )
    observation = project_entry_exit_policy_decision_v1(
        decision,
        record_id=OUTPUT_RECORD_ID,
        event_time_utc=EVENT_TIME,
        correlation_id=CORR_ID,
        cycle_id=CYCLE_ID,
        decision_event_ref=DECISION_REF,
    )
    return evidence, observation, decision


def _replay_isolated(
    evidence: Any,
    observations: list[Any],
) -> Any:
    token = _bind(_isolation_binding())
    try:
        return replay_double_play_producer_function_current_code_v1(evidence, observations)
    finally:
        reset_capture_session_v0(token)


def _imported_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.add(node.module.split(".")[0])
    return names


def test_isolation_predicate_explicit_disabled_no_ledger_pass() -> None:
    binding = _isolation_binding(enabled=False, ledger_path=None)
    assert ddo_replay_capture_disabled_isolation_reason_v0(binding) is None
    assert ddo_replay_capture_disabled_isolation_is_pass_v0(binding) is True


def test_isolation_predicate_none_fail_closed() -> None:
    assert ddo_replay_capture_disabled_isolation_reason_v0(None) == (
        REPLAY_CAPTURE_ISOLATION_UNBOUND
    )
    assert ddo_replay_capture_disabled_isolation_is_pass_v0(None) is False


def test_isolation_predicate_enabled_fail_closed() -> None:
    binding = _isolation_binding(enabled=True, ledger_path=None)
    assert ddo_replay_capture_disabled_isolation_reason_v0(binding) == (
        REPLAY_CAPTURE_ISOLATION_ENABLED
    )


def test_isolation_predicate_disabled_with_ledger_path_fail_closed() -> None:
    binding = _isolation_binding(enabled=False, ledger_path="/tmp/ddo-fnreplay-forbidden.ndjson")
    assert ddo_replay_capture_disabled_isolation_reason_v0(binding) == (
        REPLAY_CAPTURE_ISOLATION_LEDGER_PATH
    )


def test_isolation_unbound_session_blocks_without_producer_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence, observation, _decision = _typed_pair()
    calls = {"n": 0}
    orig = evaluate_double_play_entry_exit_policy_v0

    def spy(*args: Any, **kwargs: Any) -> Any:
        calls["n"] += 1
        return orig(*args, **kwargs)

    monkeypatch.setattr(
        "trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0",
        spy,
    )
    result = replay_double_play_producer_function_current_code_v1(evidence, [observation])
    assert result["status"] == STATUS_REPLAY_BLOCKED
    assert result["producer_invocation_count"] == 0
    assert result["producer_function_invoked"] is False
    assert result["semantic_match"] is False
    assert "CAPTURE_ISOLATION_FAILED" in result["reason_codes"]
    assert REPLAY_CAPTURE_ISOLATION_UNBOUND in result["reason_codes"]
    assert calls["n"] == 0


def test_isolation_enabled_blocks_without_producer_call(monkeypatch: pytest.MonkeyPatch) -> None:
    evidence, observation, _decision = _typed_pair()
    calls = {"n": 0}
    orig = evaluate_double_play_entry_exit_policy_v0

    def spy(*args: Any, **kwargs: Any) -> Any:
        calls["n"] += 1
        return orig(*args, **kwargs)

    monkeypatch.setattr(
        "trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0",
        spy,
    )
    token = _bind(_isolation_binding(enabled=True, ledger_path=None))
    try:
        result = replay_double_play_producer_function_current_code_v1(evidence, [observation])
    finally:
        reset_capture_session_v0(token)
    assert result["status"] == STATUS_REPLAY_BLOCKED
    assert result["producer_invocation_count"] == 0
    assert calls["n"] == 0
    assert REPLAY_CAPTURE_ISOLATION_ENABLED in result["reason_codes"]


def test_isolation_disabled_with_ledger_path_blocks_without_producer_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence, observation, _decision = _typed_pair()
    calls = {"n": 0}
    orig = evaluate_double_play_entry_exit_policy_v0

    def spy(*args: Any, **kwargs: Any) -> Any:
        calls["n"] += 1
        return orig(*args, **kwargs)

    monkeypatch.setattr(
        "trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0",
        spy,
    )
    token = _bind(_isolation_binding(enabled=False, ledger_path="/tmp/ddo-fnreplay.ndjson"))
    try:
        result = replay_double_play_producer_function_current_code_v1(evidence, [observation])
    finally:
        reset_capture_session_v0(token)
    assert result["status"] == STATUS_REPLAY_BLOCKED
    assert result["producer_invocation_count"] == 0
    assert calls["n"] == 0
    assert REPLAY_CAPTURE_ISOLATION_LEDGER_PATH in result["reason_codes"]


def test_valid_immutable_evidence_match() -> None:
    evidence, observation, _decision = _typed_pair()
    binding = _isolation_binding()
    token = _bind(binding)
    try:
        result = replay_double_play_producer_function_current_code_v1(evidence, [observation])
        assert binding.captured_records == []
    finally:
        reset_capture_session_v0(token)
    assert result["status"] == STATUS_MATCH
    assert result["semantic_match"] is True
    assert result["producer_invocation_count"] == 1
    assert result["public_producer_symbol_used"] is True
    assert result["wrapped_bypass_used"] is False
    assert result["replay_class_letter"] == REPLAY_CLASS_LETTER
    assert result["replay_class_semantic"] == REPLAY_CLASS_SEMANTIC
    assert result["replay_class_owner_token"] == REPLAY_CLASS_OWNER_TOKEN
    assert result["historical_code_parity_claim"] is False
    assert result["stored_code_sha"] == UNKNOWN
    assert result["result_durability"] == RESULT_DURABILITY
    assert result["replay_timeout_policy"] == REPLAY_TIMEOUT_POLICY
    assert result["mismatch_fields"] == []
    assert "replay_class" not in result


def test_missing_required_field_replay_blocked() -> None:
    evidence, observation, _decision = _typed_pair()
    broken = dict(evidence)
    broken.pop("producer_call_policy_version")
    broken.pop("content_hash", None)
    result = _replay_isolated(broken, [observation])
    assert result["status"] == STATUS_REPLAY_BLOCKED
    assert result["producer_invocation_count"] == 0
    assert result["semantic_match"] is False


def test_wrong_schema_version_replay_blocked() -> None:
    evidence, observation, _decision = _typed_pair()
    broken = dict(evidence)
    broken["schema_version"] = "not_the_bound_schema"
    broken.pop("content_hash", None)
    result = _replay_isolated(broken, [observation])
    assert result["status"] == STATUS_REPLAY_BLOCKED
    assert result["producer_invocation_count"] == 0


def test_live_current_injection_path_not_available() -> None:
    sig = inspect.signature(replay_double_play_producer_function_current_code_v1)
    assert "later_information" not in sig.parameters
    assert "current_market" not in sig.parameters
    assert "current_account" not in sig.parameters
    assert "environment_injection" not in sig.parameters
    evidence, observation, _decision = _typed_pair()
    with pytest.raises(TypeError):
        replay_double_play_producer_function_current_code_v1(
            evidence,
            [observation],
            later_information={"later_price": 1},  # type: ignore[call-arg]
        )


def test_hindsight_key_on_input_replay_blocked() -> None:
    evidence, observation, _decision = _typed_pair()
    tainted = dict(evidence)
    tainted["later_price"] = "1"
    result = _replay_isolated(tainted, [observation])
    assert result["status"] == STATUS_REPLAY_BLOCKED
    assert result["producer_invocation_count"] == 0


def test_join_exact_ref_accepted() -> None:
    evidence, observation, _decision = _typed_pair()
    result = _replay_isolated(evidence, [observation])
    assert result["status"] == STATUS_MATCH
    assert evidence["typed_output_observation_ref"] == observation["record_id"]


def test_join_missing_ref_replay_blocked() -> None:
    inp = _policy_input()
    policy = DoublePlayEntryExitPolicyV0()
    decision = evaluate_double_play_entry_exit_policy_v0(inp, policy)
    evidence = project_double_play_entry_exit_policy_input_v1(
        inp,
        record_id=INPUT_RECORD_ID,
        event_time_utc=EVENT_TIME,
        correlation_id=CORR_ID,
        cycle_id=CYCLE_ID,
        decision_event_ref=DECISION_REF,
        typed_output_observation_ref=None,
        producer_call_policy_version=str(policy.policy_version),
        capture_timing=CAPTURE_TIMING_BEFORE_PRODUCER_CALL,
    )
    observation = project_entry_exit_policy_decision_v1(
        decision,
        record_id=OUTPUT_RECORD_ID,
        event_time_utc=EVENT_TIME,
        correlation_id=CORR_ID,
        cycle_id=CYCLE_ID,
        decision_event_ref=DECISION_REF,
    )
    result = _replay_isolated(evidence, [observation])
    assert result["status"] == STATUS_REPLAY_BLOCKED
    assert "TYPED_OUTPUT_OBSERVATION_REF_MISSING" in result["reason_codes"]
    assert result["producer_invocation_count"] == 0


def test_join_unresolved_ref_replay_blocked() -> None:
    evidence, observation, _decision = _typed_pair()
    other = dict(observation)
    other["record_id"] = "ddo.dpo.other.0001"
    other.pop("content_hash", None)
    rebuilt = build_double_play_entry_exit_observation_v1(other)
    result = _replay_isolated(evidence, [rebuilt])
    assert result["status"] == STATUS_REPLAY_BLOCKED
    assert "TYPED_OUTPUT_OBSERVATION_REF_UNRESOLVED" in result["reason_codes"]
    assert result["producer_invocation_count"] == 0


def test_join_ambiguous_ref_replay_blocked() -> None:
    evidence, observation, _decision = _typed_pair()
    result = _replay_isolated(evidence, [observation, observation])
    assert result["status"] == STATUS_REPLAY_BLOCKED
    assert "TYPED_OUTPUT_OBSERVATION_REF_AMBIGUOUS" in result["reason_codes"]
    assert result["producer_invocation_count"] == 0


def test_join_wrong_producer_identity_replay_blocked() -> None:
    evidence, observation, _decision = _typed_pair()
    broken = dict(observation)
    broken["producer_owner"] = "not.the.double_play.producer"
    broken.pop("content_hash", None)
    rebuilt = build_double_play_entry_exit_observation_v1(broken)
    result = _replay_isolated(evidence, [rebuilt])
    assert result["status"] == STATUS_REPLAY_BLOCKED
    assert "TYPED_OUTPUT_OBSERVATION_PRODUCER_IDENTITY_MISMATCH" in result["reason_codes"]
    assert result["producer_invocation_count"] == 0


def test_join_wrong_schema_replay_blocked() -> None:
    evidence, observation, _decision = _typed_pair()
    broken = dict(observation)
    broken["schema_name"] = "decision_event"
    broken.pop("content_hash", None)
    result = _replay_isolated(evidence, [broken])
    assert result["status"] == STATUS_REPLAY_BLOCKED
    assert result["producer_invocation_count"] == 0


def test_public_decorated_symbol_invoked_once_not_wrapped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence, observation, _decision = _typed_pair()
    orig = evaluate_double_play_entry_exit_policy_v0
    assert hasattr(orig, "__wrapped__")
    counts = {"public": 0}

    def public_spy(*args: Any, **kwargs: Any) -> Any:
        counts["public"] += 1
        return orig(*args, **kwargs)

    monkeypatch.setattr(
        "trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0",
        public_spy,
    )
    result = _replay_isolated(evidence, [observation])
    assert result["status"] == STATUS_MATCH
    assert counts["public"] == 1
    assert result["producer_invocation_count"] == 1
    assert result["wrapped_bypass_used"] is False
    source = REPLAY_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    wrapped_uses = [
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr == "__wrapped__"
    ]
    assert wrapped_uses == []


def test_mismatch_changed_deterministic_field() -> None:
    evidence, observation, _decision = _typed_pair()
    broken = dict(observation)
    payload = dict(broken["producer_canonical_payload"])
    payload["decision_outcome"] = "no_action"
    broken["producer_canonical_payload"] = payload
    broken.pop("content_hash", None)
    mutated = build_double_play_entry_exit_observation_v1(broken)
    first = _replay_isolated(evidence, [mutated])
    second = _replay_isolated(evidence, [mutated])
    assert first["status"] == STATUS_MISMATCH
    assert first["semantic_match"] is False
    assert first["mismatch_fields"][0] == "producer_canonical_payload"
    assert "decision_outcome" in first["mismatch_fields"]
    assert first["mismatch_fields"] == second["mismatch_fields"]
    payload_keys = [key for key in first["mismatch_fields"] if key in PRODUCER_CANONICAL_KEYS]
    assert payload_keys == sorted(payload_keys, key=PRODUCER_CANONICAL_KEYS.index)
    assert first["mismatch_fields"][:1] == ["producer_canonical_payload"]


def test_stored_code_sha_unknown_not_backfilled() -> None:
    evidence, observation, _decision = _typed_pair()
    assert evidence["code_sha"] == UNKNOWN
    assert observation["code_sha"] == UNKNOWN
    result = _replay_isolated(evidence, [observation])
    assert result["stored_code_sha"] == UNKNOWN
    assert result["historical_code_parity_claim"] is HISTORICAL_CODE_PARITY_CLAIM
    assert result["historical_code_parity_claim"] is False
    sha_keys = [key for key in result if "code_sha" in key]
    assert sha_keys == ["stored_code_sha"]
    assert "git" not in result
    assert "repository_sha" not in result
    assert "current_head" not in result


def test_producer_raise_replay_indeterminate_no_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence, observation, _decision = _typed_pair()
    calls = {"n": 0}

    def boom(*args: Any, **kwargs: Any) -> Any:
        calls["n"] += 1
        raise RuntimeError("producer_boom")

    monkeypatch.setattr(
        "trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0",
        boom,
    )
    result = _replay_isolated(evidence, [observation])
    assert result["status"] == STATUS_REPLAY_INDETERMINATE
    assert result["semantic_match"] is False
    assert calls["n"] == 1
    assert result["producer_invocation_count"] == 1
    assert "PRODUCER_INVOCATION_EXCEPTION" in result["reason_codes"]
    assert result["exception_class"] == "RuntimeError"


def test_serializer_raise_replay_indeterminate_no_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence, observation, _decision = _typed_pair()
    calls = {"n": 0}

    def boom(raw: Any, *args: Any, **kwargs: Any) -> Any:
        calls["n"] += 1
        raise RuntimeError("serializer_boom")

    monkeypatch.setattr(
        "src.learning.deterministic_decision_outcome_v0.double_play_producer_function_replay_v1.json.loads",
        boom,
    )
    result = _replay_isolated(evidence, [observation])
    assert result["status"] == STATUS_REPLAY_INDETERMINATE
    assert calls["n"] == 1
    assert result["producer_invocation_count"] == 1
    assert "SERIALIZATION_OR_DIGEST_OR_COMPARE_FAILURE" in result["reason_codes"]


def test_side_effects_no_capture_ledger_file_or_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence, observation, _decision = _typed_pair()
    appends = {"n": 0}
    writes = {"n": 0}
    orig_append = AppendOnlyDdoLedgerV0.append
    orig_write = Path.write_text

    def append_spy(self: Any, *args: Any, **kwargs: Any) -> Any:
        appends["n"] += 1
        return orig_append(self, *args, **kwargs)

    def write_spy(self: Path, *args: Any, **kwargs: Any) -> Any:
        writes["n"] += 1
        return orig_write(self, *args, **kwargs)

    monkeypatch.setattr(AppendOnlyDdoLedgerV0, "append", append_spy)
    monkeypatch.setattr(Path, "write_text", write_spy)
    binding = _isolation_binding()
    token = _bind(binding)
    try:
        result = replay_double_play_producer_function_current_code_v1(evidence, [observation])
        assert binding.captured_records == []
        assert binding.persisted_ids == []
    finally:
        reset_capture_session_v0(token)
    assert result["status"] == STATUS_MATCH
    assert appends["n"] == 0
    assert writes["n"] == 0
    assert result["trading_authority"] == "NONE"
    assert result["replay_productive_authority"] == "NONE"


def test_replay_module_has_no_forbidden_or_wrapped_imports() -> None:
    names = _imported_names(REPLAY_PATH)
    for prefix in FORBIDDEN_IMPORT_PREFIXES:
        assert all(not item.startswith(prefix) for item in names)
    source = REPLAY_PATH.read_text(encoding="utf-8")
    assert "__wrapped__" not in source
    assert "requests" not in names
    capture_names = _imported_names(CAPTURE_PATH)
    assert "src.execution" not in capture_names
    assert "src.live" not in capture_names


def test_function_name_constant_matches_public_symbol() -> None:
    assert PRODUCER_FUNCTION_NAME == "evaluate_double_play_entry_exit_policy_v0"
    assert evaluate_double_play_entry_exit_policy_v0.__name__ == PRODUCER_FUNCTION_NAME
    assert hasattr(evaluate_double_play_entry_exit_policy_v0, "__wrapped__")
