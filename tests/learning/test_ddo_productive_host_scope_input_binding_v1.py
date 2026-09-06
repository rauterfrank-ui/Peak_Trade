"""DDO productive observation-host scope input binding v1.

Consumes existing owners only. No productive ledger_path. No trading authority.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Any

import pytest

from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTHORITY_OWNER,
    LEARNING_PRODUCTIVE_AUTHORITY,
    SECOND_EXECUTION_AUTHORITY_CREATED,
    SECOND_TRADING_AUTHORITY_CREATED,
)
from src.learning.deterministic_decision_outcome_v0.durable_evidence_path_v0 import (
    DDO_EVIDENCE_ACCOUNT_OWNER,
    DDO_EVIDENCE_ENVIRONMENT_OWNER,
    LOGICAL_CONFIG_KEY_DDO_DURABLE_EVIDENCE_RUNTIME_STATE_ROOT,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.account_identity_boundary_v1 import (
    AccountIdentityRecordV1,
    build_account_identity_record_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.constants_v1 import (
    ACCOUNT_IDENTITY_BOUNDARY_OWNER,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_observation_host_scope_binding_v1 import (
    ACCOUNT_SCOPE_OWNER,
    ACCOUNT_SCOPE_OWNER_LOGICAL,
    DDO_LEDGER_PATH_UNRESOLVED,
    ENVIRONMENT_OWNER,
    RUNTIME_STATE_ROOT_OWNER,
    SCOPE_INPUT_CONFLICT,
    SCOPE_INPUT_INVALID,
    SCOPE_INPUT_MISSING,
    DdoHostScopeInputError,
    DdoObservationHostScopeInputsV1,
    bind_ddo_observation_host_scope_v1,
    load_ddo_durable_evidence_runtime_state_root_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    BridgeSessionStateV1,
    run_bridge_cycle_v1,
    run_bridge_cycles_from_mids_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HOST_PATH = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "decision_economics_cycle_bridge_v1.py"
)
BINDING_PATH = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "ddo_observation_host_scope_binding_v1.py"
)
BINDING_PACKAGE = REPO_ROOT / "src/learning/deterministic_decision_outcome_v0"
ACCOUNT_TEST_IDENTITY = "acct-uid-test-scope-binding"
ACCOUNT_TEST_CREDENTIAL_REF = "cred-ref-test-scope-binding"


def _account_record(*, identity: str = ACCOUNT_TEST_IDENTITY) -> AccountIdentityRecordV1:
    return build_account_identity_record_v1(
        account_identity=identity,
        venue="OKX",
        credential_ref_id=ACCOUNT_TEST_CREDENTIAL_REF,
        account_scope="trading-only",
        expected_uid=identity,
    )


def _bind(
    state: BridgeSessionStateV1,
    tmp_path: Path,
    *,
    environment: ExecutionEnvironment = ExecutionEnvironment.DEV,
    account: AccountIdentityRecordV1 | None = None,
) -> DdoObservationHostScopeInputsV1:
    return bind_ddo_observation_host_scope_v1(
        state,
        runtime_state_root=tmp_path,
        environment=environment,
        account_identity_record=account if account is not None else _account_record(),
    )


def _call_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def test_runtime_state_root_environment_and_account_owners_reused(tmp_path: Path) -> None:
    state = BridgeSessionStateV1(require_selection_binding=False)
    bound = _bind(state, tmp_path)
    assert RUNTIME_STATE_ROOT_OWNER == "DDO_DURABLE_EVIDENCE_STORAGE_OWNER"
    assert ENVIRONMENT_OWNER == DDO_EVIDENCE_ENVIRONMENT_OWNER
    assert ENVIRONMENT_OWNER == "EXISTING_GOVERNANCE_EXECUTION_ENVIRONMENT"
    assert ACCOUNT_SCOPE_OWNER == ACCOUNT_IDENTITY_BOUNDARY_OWNER
    assert ACCOUNT_SCOPE_OWNER_LOGICAL == DDO_EVIDENCE_ACCOUNT_OWNER
    assert bound.runtime_state_root_owner == RUNTIME_STATE_ROOT_OWNER
    assert bound.environment_owner == ENVIRONMENT_OWNER
    assert bound.account_scope_owner == ACCOUNT_SCOPE_OWNER
    assert bound.environment is ExecutionEnvironment.DEV
    assert isinstance(bound.environment, ExecutionEnvironment)
    assert bound.account_identity == ACCOUNT_TEST_IDENTITY
    assert bound.runtime_state_root_config_key == (
        LOGICAL_CONFIG_KEY_DDO_DURABLE_EVIDENCE_RUNTIME_STATE_ROOT
    )


def test_no_new_ddo_environment_account_or_storage_root_authority() -> None:
    source = BINDING_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert "DDOEnvironment" not in class_names
    assert "DdoEnvironment" not in class_names
    assert "DdoAccountIdentity" not in class_names
    assert "class ExecutionEnvironment" not in source
    assert "class AccountIdentityRecordV1" not in source
    assert "LiveModeGate" not in source
    assert "acct-uid-demo" not in source.split("_FORBIDDEN_FIXTURE_ACCOUNT_IDENTITIES")[0]
    imports = [
        ast.dump(node) for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    joined = "\n".join(imports)
    assert "live_mode_gate" in joined
    assert "account_identity_boundary_v1" in joined
    assert "durable_evidence_path_v0" in joined


def test_host_scope_fields_explicit_after_injection(tmp_path: Path) -> None:
    state, _cycles = run_bridge_cycles_from_mids_v1(
        [3500.0],
        session_id="ddo-scope-bound",
        require_selection_binding=False,
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.SHADOW,
        ddo_account_identity_record=_account_record(),
    )
    assert state.ddo_observation_host_scope is not None
    assert state.ddo_durable_evidence_runtime_state_root == str(tmp_path)
    assert state.ddo_evidence_environment == ExecutionEnvironment.SHADOW.value
    assert state.ddo_evidence_account_scope == ACCOUNT_TEST_IDENTITY
    assert state.ddo_evidence_environment_binding_status == "BOUND"
    assert state.ddo_evidence_account_binding_status == "BOUND"
    assert state.ddo_capture_binding.evidence_environment == "shadow"
    assert state.ddo_capture_binding.evidence_account_scope == ACCOUNT_TEST_IDENTITY
    assert state.ddo_capture_binding.ledger_path is None
    assert state.last_ddo_capture is not None
    assert state.last_ddo_capture["path_binding_state"] == "UNBOUND"
    assert state.last_ddo_capture["ddo_ledger_path_unresolved"] == DDO_LEDGER_PATH_UNRESOLVED
    assert state.last_ddo_capture["ledger_bound"] is False


def test_missing_each_scope_input_fails_closed(tmp_path: Path) -> None:
    state = BridgeSessionStateV1(require_selection_binding=False)
    with pytest.raises(DdoHostScopeInputError) as missing_root:
        bind_ddo_observation_host_scope_v1(
            state,
            environment=ExecutionEnvironment.DEV,
            account_identity_record=_account_record(),
        )
    assert missing_root.value.failure_class == SCOPE_INPUT_MISSING
    with pytest.raises(DdoHostScopeInputError) as missing_env:
        bind_ddo_observation_host_scope_v1(
            state,
            runtime_state_root=tmp_path,
            account_identity_record=_account_record(),
        )
    assert missing_env.value.failure_class == SCOPE_INPUT_MISSING
    with pytest.raises(DdoHostScopeInputError) as missing_account:
        bind_ddo_observation_host_scope_v1(
            state,
            runtime_state_root=tmp_path,
            environment=ExecutionEnvironment.DEV,
        )
    assert missing_account.value.failure_class == SCOPE_INPUT_MISSING
    with pytest.raises(DdoHostScopeInputError) as partial:
        run_bridge_cycles_from_mids_v1(
            [3500.0],
            session_id="ddo-scope-partial",
            require_selection_binding=False,
            ddo_evidence_environment=ExecutionEnvironment.DEV,
        )
    assert partial.value.failure_class == SCOPE_INPUT_MISSING


def test_no_cwd_home_repo_tmp_or_identity_fallbacks(tmp_path: Path, monkeypatch: Any) -> None:
    source = BINDING_PATH.read_text(encoding="utf-8")
    assert "Path.cwd" not in source
    assert "Path.home" not in source
    assert "os.getcwd" not in source
    assert "tempfile" not in source
    assert "mkdtemp" not in source
    assert "acct-uid-demo" in source
    assert "FIXTURE_ACCOUNT_IDENTITY_FORBIDDEN" in source
    assert "CREDENTIAL_REF_IS_NOT_ACCOUNT_IDENTITY" in source

    def _boom_cwd() -> Path:
        raise AssertionError("CWD_FALLBACK_FORBIDDEN")

    def _boom_home() -> Path:
        raise AssertionError("HOME_FALLBACK_FORBIDDEN")

    monkeypatch.setattr(Path, "cwd", classmethod(lambda cls: _boom_cwd()))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: _boom_home()))
    state = BridgeSessionStateV1(require_selection_binding=False)
    bound = _bind(state, tmp_path)
    assert bound.runtime_state_root == str(tmp_path)
    with pytest.raises(DdoHostScopeInputError) as relative:
        bind_ddo_observation_host_scope_v1(
            BridgeSessionStateV1(require_selection_binding=False),
            runtime_state_root="relative/root",
            environment=ExecutionEnvironment.DEV,
            account_identity_record=_account_record(),
        )
    assert relative.value.failure_class == SCOPE_INPUT_INVALID
    with pytest.raises(DdoHostScopeInputError) as fixture_account:
        bind_ddo_observation_host_scope_v1(
            BridgeSessionStateV1(require_selection_binding=False),
            runtime_state_root=tmp_path,
            environment=ExecutionEnvironment.DEV,
            account_identity_record=_account_record(identity="acct-uid-demo"),
        )
    assert fixture_account.value.failure_class == SCOPE_INPUT_INVALID
    credential_as_identity = build_account_identity_record_v1(
        account_identity="same-secret-token",
        venue="OKX",
        credential_ref_id="same-secret-token",
        account_scope="trading-only",
        expected_uid="same-secret-token",
    )
    with pytest.raises(DdoHostScopeInputError) as cred:
        bind_ddo_observation_host_scope_v1(
            BridgeSessionStateV1(require_selection_binding=False),
            runtime_state_root=tmp_path,
            environment=ExecutionEnvironment.DEV,
            account_identity_record=credential_as_identity,
        )
    assert cred.value.failure_class == SCOPE_INPUT_INVALID
    with pytest.raises(DdoHostScopeInputError) as missing_config:
        load_ddo_durable_evidence_runtime_state_root_v1({})
    assert missing_config.value.failure_class == SCOPE_INPUT_MISSING
    loaded = load_ddo_durable_evidence_runtime_state_root_v1(
        {LOGICAL_CONFIG_KEY_DDO_DURABLE_EVIDENCE_RUNTIME_STATE_ROOT: str(tmp_path)}
    )
    assert loaded == tmp_path


def test_host_scope_immutable_or_conflict_explicit(tmp_path: Path) -> None:
    state = BridgeSessionStateV1(require_selection_binding=False)
    first = _bind(state, tmp_path, environment=ExecutionEnvironment.DEV)
    same = _bind(state, tmp_path, environment=ExecutionEnvironment.DEV)
    assert same is first
    with pytest.raises(DdoHostScopeInputError) as conflict:
        _bind(state, tmp_path, environment=ExecutionEnvironment.PROD)
    assert conflict.value.failure_class == SCOPE_INPUT_CONFLICT
    assert state.ddo_evidence_environment == "dev"
    mutated = BridgeSessionStateV1(require_selection_binding=False)
    _bind(mutated, tmp_path)
    mutated.ddo_evidence_environment = "prod"
    baseline_state, baseline = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id="ddo-scope-conflict", require_selection_binding=False
    )
    cycle = run_bridge_cycle_v1(
        mutated,
        mid_price=3500.0,
        event_ts_unix=1_700_000_000.0,
        session_id="ddo-scope-conflict",
    )
    assert cycle.to_dict() == baseline[0].to_dict()
    assert mutated.last_ddo_capture is not None
    assert mutated.last_ddo_capture["scope_input_failure_class"] == SCOPE_INPUT_CONFLICT
    assert mutated.last_ddo_capture["decision_unchanged"] is True
    _ = baseline_state


def test_productive_host_ledger_still_unbound_and_resolver_not_consumed(
    tmp_path: Path,
) -> None:
    default_state, _ = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id="ddo-scope-default", require_selection_binding=False
    )
    bound_state, _ = run_bridge_cycles_from_mids_v1(
        [3500.0],
        session_id="ddo-scope-default",
        require_selection_binding=False,
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.DEV,
        ddo_account_identity_record=_account_record(),
    )
    for state in (default_state, bound_state):
        assert state.ddo_capture_binding.ledger_path is None
        assert state.last_ddo_capture is not None
        assert state.last_ddo_capture["ledger_bound"] is False
        assert state.last_ddo_capture["path_binding_state"] == "UNBOUND"
        assert state.last_ddo_capture["ddo_ledger_path_unresolved"] == DDO_LEDGER_PATH_UNRESOLVED
        assert list(tmp_path.glob("**/*.jsonl")) == []
    assert default_state.ddo_observation_host_scope is None
    assert default_state.ddo_durable_evidence_runtime_state_root is None
    assert default_state.ddo_evidence_environment is None
    assert default_state.ddo_evidence_account_scope is None
    assert "resolve_ddo_durable_evidence_path_v1" not in _call_names(HOST_PATH)
    assert "resolve_ddo_durable_evidence_path_v1" not in _call_names(BINDING_PATH)
    host = HOST_PATH.read_text(encoding="utf-8")
    binding = BINDING_PATH.read_text(encoding="utf-8")
    assert "resolve_ddo_durable_evidence_path_v1(" not in host
    assert "resolve_ddo_durable_evidence_path_v1(" not in binding
    assert "ledger_path=resolver" not in host
    assert (
        inspect.signature(BridgeSessionStateV1.__init__)
        .parameters["ddo_durable_evidence_runtime_state_root"]
        .default
        is None
    )


def test_trading_decision_and_authority_unchanged_with_bound_scope(tmp_path: Path) -> None:
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0, 3510.0],
        session_id="ddo-scope-authority",
        require_selection_binding=False,
    )
    bound_state, bound = run_bridge_cycles_from_mids_v1(
        [3500.0, 3510.0],
        session_id="ddo-scope-authority",
        require_selection_binding=False,
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.TESTNET,
        ddo_account_identity_record=_account_record(),
    )
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    assert AUTHORITY_OWNER == "NONE"
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert SECOND_TRADING_AUTHORITY_CREATED is False
    assert SECOND_EXECUTION_AUTHORITY_CREATED is False
    assert unbound_state.last_ddo_capture is not None
    assert bound_state.last_ddo_capture is not None
    assert unbound_state.last_ddo_capture["decision_unchanged"] is True
    assert bound_state.last_ddo_capture["decision_unchanged"] is True
    assert bound_state.ddo_observation_host_scope is not None
    assert bound_state.ddo_observation_host_scope.ledger_path_resolved is False
    assert ACCOUNT_TEST_IDENTITY != "acct-uid-demo"
    _ = BINDING_PACKAGE
