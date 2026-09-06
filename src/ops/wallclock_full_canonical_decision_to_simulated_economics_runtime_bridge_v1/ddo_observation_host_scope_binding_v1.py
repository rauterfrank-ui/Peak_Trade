"""Explicit DDO observation-host scope input and durable ledger binding v1.

Consumes existing owners only. Resolves ledger_path solely from the frozen
scope tuple via resolve_ddo_durable_evidence_path_v1. Binds
AppendOnlyDdoLedgerV0 through DdoCaptureBindingV0. Does not invent
cwd/home/repo/tmp defaults, fixture account IDs, or credentials-as-identity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.a1_unattended_durability_policy_boundary_v1 import (
    a1_policy_observability_v1,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import DdoCaptureBindingV0
from src.learning.deterministic_decision_outcome_v0.durable_evidence_path_v0 import (
    DDO_EVIDENCE_ACCOUNT_OWNER,
    DDO_EVIDENCE_ENVIRONMENT_OWNER,
    DDO_EVIDENCE_ENVIRONMENT_TOKENS,
    DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN,
    LOGICAL_CONFIG_KEY_DDO_DURABLE_EVIDENCE_RUNTIME_STATE_ROOT,
    resolve_ddo_durable_evidence_path_v1,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoPathResolutionError
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.account_identity_boundary_v1 import (
    AccountIdentityRecordV1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.constants_v1 import (
    ACCOUNT_IDENTITY_BOUNDARY_OWNER,
)

SCOPE_INPUT_MISSING: Final[str] = "SCOPE_INPUT_MISSING"
SCOPE_INPUT_INVALID: Final[str] = "SCOPE_INPUT_INVALID"
SCOPE_INPUT_CONFLICT: Final[str] = "SCOPE_INPUT_CONFLICT"
PATH_BINDING_FAILURE: Final[str] = "PATH_BINDING_FAILURE"
DDO_LEDGER_PATH_UNRESOLVED: Final[str] = "DDO_LEDGER_PATH_UNRESOLVED"

RUNTIME_STATE_ROOT_OWNER: Final[str] = "DDO_DURABLE_EVIDENCE_STORAGE_OWNER"
ENVIRONMENT_OWNER: Final[str] = DDO_EVIDENCE_ENVIRONMENT_OWNER
ACCOUNT_SCOPE_OWNER: Final[str] = ACCOUNT_IDENTITY_BOUNDARY_OWNER
ACCOUNT_SCOPE_OWNER_LOGICAL: Final[str] = DDO_EVIDENCE_ACCOUNT_OWNER

_FORBIDDEN_FIXTURE_ACCOUNT_IDENTITIES: Final[frozenset[str]] = frozenset({"acct-uid-demo"})
_FORBIDDEN_FIXTURE_CREDENTIAL_REFS: Final[frozenset[str]] = frozenset({"cred-ref-demo"})
_ACCOUNT_IDENTITY_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9._-]+$")


class DdoHostScopeInputError(Exception):
    """Fail-closed DDO observation-host scope input error. Not trading authority."""

    error_code = "DDO_HOST_SCOPE_INPUT_ERROR"

    def __init__(self, failure_class: str, message: str) -> None:
        super().__init__(message)
        self.failure_class = failure_class


@dataclass(frozen=True)
class DdoObservationHostScopeInputsV1:
    """Frozen explicit host scope inputs. Not a trading authority."""

    runtime_state_root: str
    environment: ExecutionEnvironment
    account_identity: str
    runtime_state_root_owner: str = RUNTIME_STATE_ROOT_OWNER
    runtime_state_root_config_key: str = LOGICAL_CONFIG_KEY_DDO_DURABLE_EVIDENCE_RUNTIME_STATE_ROOT
    environment_owner: str = ENVIRONMENT_OWNER
    account_scope_owner: str = ACCOUNT_SCOPE_OWNER
    system_scope: str = DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN
    ledger_path_resolved: bool = False


def load_ddo_durable_evidence_runtime_state_root_v1(config: Mapping[str, Any]) -> Path:
    """Load the named logical config key. No filesystem fallback."""
    if config is None:
        raise DdoHostScopeInputError(SCOPE_INPUT_MISSING, "RUNTIME_STATE_ROOT_REQUIRED")
    raw = _extract_runtime_state_root_raw(config)
    if raw is None:
        raise DdoHostScopeInputError(SCOPE_INPUT_MISSING, "RUNTIME_STATE_ROOT_REQUIRED")
    return _validate_runtime_state_root(raw)


def maybe_bind_ddo_observation_host_scope_from_optional_inputs_v1(
    state: Any,
    *,
    runtime_state_root: str | Path | None = None,
    environment: ExecutionEnvironment | None = None,
    account_identity_record: AccountIdentityRecordV1 | None = None,
    runtime_state_root_config: Mapping[str, Any] | None = None,
) -> DdoObservationHostScopeInputsV1 | None:
    """Bind only when the caller supplies the complete existing-owner triple.

    Default host construction supplies none of these and remains unbound.
    """
    has_root = runtime_state_root is not None or runtime_state_root_config is not None
    has_environment = environment is not None
    has_account = account_identity_record is not None
    if not (has_root or has_environment or has_account):
        return None
    if not (has_root and has_environment and has_account):
        raise DdoHostScopeInputError(SCOPE_INPUT_MISSING, "HOST_SCOPE_INPUTS_MUST_BE_COMPLETE")
    return bind_ddo_observation_host_scope_v1(
        state,
        runtime_state_root=runtime_state_root,
        environment=environment,
        account_identity_record=account_identity_record,
        runtime_state_root_config=runtime_state_root_config,
    )


def bind_ddo_observation_host_scope_v1(
    state: Any,
    *,
    runtime_state_root: str | Path | None = None,
    environment: ExecutionEnvironment | None = None,
    account_identity_record: AccountIdentityRecordV1 | None = None,
    runtime_state_root_config: Mapping[str, Any] | None = None,
) -> DdoObservationHostScopeInputsV1:
    """Bind once from existing owners, then resolve and bind the durable ledger path."""
    resolved_root = _resolve_runtime_state_root_input(
        runtime_state_root=runtime_state_root,
        runtime_state_root_config=runtime_state_root_config,
    )
    resolved_environment = _validate_environment(environment)
    resolved_account = _project_account_identity(account_identity_record)
    incoming = DdoObservationHostScopeInputsV1(
        runtime_state_root=str(resolved_root),
        environment=resolved_environment,
        account_identity=resolved_account,
        ledger_path_resolved=True,
    )
    resolved_path = resolve_ddo_observation_host_durable_ledger_path_v1(incoming)
    existing = getattr(state, "ddo_observation_host_scope", None)
    if existing is not None:
        if existing != incoming:
            raise DdoHostScopeInputError(SCOPE_INPUT_CONFLICT, "HOST_SCOPE_REBIND_CONFLICT")
        _assert_host_scope_matches_frozen(state, existing)
        _bind_ledger_path_once(state, resolved_path)
        return existing
    _write_scope_onto_host(state, incoming)
    _bind_ledger_path_once(state, resolved_path)
    apply_ddo_observation_host_scope_to_capture_binding_v1(state)
    return incoming


def resolve_ddo_observation_host_durable_ledger_path_v1(
    scope: DdoObservationHostScopeInputsV1,
) -> Path:
    """Derive the ledger path from the frozen host scope. No fallback source."""
    try:
        return resolve_ddo_durable_evidence_path_v1(
            runtime_state_root=scope.runtime_state_root,
            environment=scope.environment.value,
            account_scope=scope.account_identity,
            system_scope=scope.system_scope,
        )
    except DdoPathResolutionError as exc:
        raise DdoHostScopeInputError(PATH_BINDING_FAILURE, str(exc)) from exc


def apply_ddo_observation_host_scope_to_capture_binding_v1(state: Any) -> None:
    """Copy bound scope onto capture fields and bind-once the scope-derived ledger path."""
    scope = getattr(state, "ddo_observation_host_scope", None)
    binding = getattr(state, "ddo_capture_binding", None)
    if scope is None or not isinstance(binding, DdoCaptureBindingV0):
        return
    binding.evidence_environment = scope.environment.value
    binding.evidence_account_scope = scope.account_identity
    binding.evidence_environment_binding_status = "BOUND"
    binding.evidence_account_binding_status = "BOUND"
    _bind_ledger_path_once(state, resolve_ddo_observation_host_durable_ledger_path_v1(scope))


def assert_ddo_observation_host_scope_stable_v1(state: Any) -> None:
    """Fail closed if bound scope fields or the bound ledger path were mutated mid-lifecycle."""
    scope = getattr(state, "ddo_observation_host_scope", None)
    if scope is None:
        return
    _assert_host_scope_matches_frozen(state, scope)
    resolved = resolve_ddo_observation_host_durable_ledger_path_v1(scope)
    _assert_ledger_path_matches(state, resolved)


def annotate_ddo_host_ledger_binding_on_capture_v1(state: Any) -> None:
    """Stamp path-binding observability onto last_ddo_capture. Never changes the cycle."""
    payload = dict(getattr(state, "last_ddo_capture") or {})
    binding = getattr(state, "ddo_capture_binding", None)
    ledger_bound = isinstance(binding, DdoCaptureBindingV0) and binding.ledger_path is not None
    payload["ledger_bound"] = bool(ledger_bound)
    payload["path_binding_state"] = "BOUND" if ledger_bound else "UNBOUND"
    payload["resolved_path_is_scope_derived"] = bool(
        ledger_bound and getattr(state, "ddo_observation_host_scope", None) is not None
    )
    if ledger_bound:
        payload.pop("ddo_ledger_path_unresolved", None)
    else:
        payload["ddo_ledger_path_unresolved"] = DDO_LEDGER_PATH_UNRESOLVED
    payload["environment_binding_status"] = getattr(
        state, "ddo_evidence_environment_binding_status", "UNBOUND"
    )
    payload["account_binding_status"] = getattr(
        state, "ddo_evidence_account_binding_status", "UNBOUND"
    )
    payload.update(a1_policy_observability_v1())
    state.last_ddo_capture = payload


def observe_ddo_host_scope_conflict_v1(state: Any, exc: DdoHostScopeInputError) -> None:
    """Record a scope conflict without changing the trading cycle return."""
    payload = dict(getattr(state, "last_ddo_capture") or {})
    payload["decision_unchanged"] = True
    payload["capture_failure_changes_current_decision"] = False
    payload["scope_input_failure_class"] = exc.failure_class
    payload["scope_input_error"] = f"{type(exc).__name__}:{exc}"
    state.last_ddo_capture = payload
    annotate_ddo_host_ledger_binding_on_capture_v1(state)


def _extract_runtime_state_root_raw(config: Mapping[str, Any]) -> Any:
    dotted = config.get(LOGICAL_CONFIG_KEY_DDO_DURABLE_EVIDENCE_RUNTIME_STATE_ROOT)
    if dotted is not None:
        return dotted
    nested = config.get("ddo")
    if isinstance(nested, Mapping):
        durable = nested.get("durable_evidence")
        if isinstance(durable, Mapping) and "runtime_state_root" in durable:
            return durable.get("runtime_state_root")
    return None


def _validate_runtime_state_root(raw: Any) -> Path:
    if raw is None or str(raw).strip() == "":
        raise DdoHostScopeInputError(SCOPE_INPUT_MISSING, "RUNTIME_STATE_ROOT_REQUIRED")
    path = Path(str(raw).strip())
    if not path.is_absolute():
        raise DdoHostScopeInputError(SCOPE_INPUT_INVALID, "RUNTIME_STATE_ROOT_MUST_BE_ABSOLUTE")
    if ".." in path.parts:
        raise DdoHostScopeInputError(SCOPE_INPUT_INVALID, "RUNTIME_STATE_ROOT_PATH_TRAVERSAL")
    return path


def _resolve_runtime_state_root_input(
    *,
    runtime_state_root: str | Path | None,
    runtime_state_root_config: Mapping[str, Any] | None,
) -> Path:
    loaded: Path | None = None
    if runtime_state_root_config is not None:
        loaded = load_ddo_durable_evidence_runtime_state_root_v1(runtime_state_root_config)
    if runtime_state_root is None:
        if loaded is None:
            raise DdoHostScopeInputError(SCOPE_INPUT_MISSING, "RUNTIME_STATE_ROOT_REQUIRED")
        return loaded
    explicit = _validate_runtime_state_root(runtime_state_root)
    if loaded is not None and loaded != explicit:
        raise DdoHostScopeInputError(SCOPE_INPUT_CONFLICT, "RUNTIME_STATE_ROOT_CONFIG_CONFLICT")
    return explicit


def _validate_environment(environment: ExecutionEnvironment | None) -> ExecutionEnvironment:
    if environment is None:
        raise DdoHostScopeInputError(SCOPE_INPUT_MISSING, "ENVIRONMENT_SCOPE_REQUIRED")
    if not isinstance(environment, ExecutionEnvironment):
        raise DdoHostScopeInputError(
            SCOPE_INPUT_INVALID, "ENVIRONMENT_MUST_BE_EXECUTION_ENVIRONMENT"
        )
    if environment.value not in DDO_EVIDENCE_ENVIRONMENT_TOKENS:
        raise DdoHostScopeInputError(SCOPE_INPUT_INVALID, "ENVIRONMENT_SCOPE_UNKNOWN")
    return environment


def _project_account_identity(record: AccountIdentityRecordV1 | None) -> str:
    if record is None:
        raise DdoHostScopeInputError(SCOPE_INPUT_MISSING, "ACCOUNT_SCOPE_REQUIRED")
    if not isinstance(record, AccountIdentityRecordV1):
        raise DdoHostScopeInputError(SCOPE_INPUT_INVALID, "ACCOUNT_IDENTITY_RECORD_REQUIRED")
    identity = str(record.account_identity).strip()
    if identity in _FORBIDDEN_FIXTURE_ACCOUNT_IDENTITIES:
        raise DdoHostScopeInputError(SCOPE_INPUT_INVALID, "FIXTURE_ACCOUNT_IDENTITY_FORBIDDEN")
    if str(record.credential_ref_id).strip() in _FORBIDDEN_FIXTURE_CREDENTIAL_REFS:
        raise DdoHostScopeInputError(SCOPE_INPUT_INVALID, "FIXTURE_CREDENTIAL_REF_FORBIDDEN")
    if identity in {".", ".."} or not _ACCOUNT_IDENTITY_RE.fullmatch(identity):
        raise DdoHostScopeInputError(SCOPE_INPUT_INVALID, "ACCOUNT_SCOPE_INVALID")
    if identity == str(record.credential_ref_id).strip():
        raise DdoHostScopeInputError(SCOPE_INPUT_INVALID, "CREDENTIAL_REF_IS_NOT_ACCOUNT_IDENTITY")
    return identity


def _write_scope_onto_host(state: Any, scope: DdoObservationHostScopeInputsV1) -> None:
    state.ddo_observation_host_scope = scope
    state.ddo_durable_evidence_runtime_state_root = scope.runtime_state_root
    state.ddo_evidence_environment = scope.environment.value
    state.ddo_evidence_account_scope = scope.account_identity
    state.ddo_evidence_environment_binding_status = "BOUND"
    state.ddo_evidence_account_binding_status = "BOUND"


def _bind_ledger_path_once(state: Any, resolved: Path) -> None:
    binding = getattr(state, "ddo_capture_binding", None)
    if not isinstance(binding, DdoCaptureBindingV0):
        raise DdoHostScopeInputError(PATH_BINDING_FAILURE, "CAPTURE_BINDING_REQUIRED")
    existing = binding.ledger_path
    if existing is not None and Path(existing) != resolved:
        raise DdoHostScopeInputError(SCOPE_INPUT_CONFLICT, "LEDGER_PATH_REBIND_CONFLICT")
    host_path = getattr(state, "ddo_durable_ledger_path", None)
    if host_path is not None and str(host_path) != str(resolved):
        raise DdoHostScopeInputError(SCOPE_INPUT_CONFLICT, "LEDGER_PATH_REBIND_CONFLICT")
    binding.ledger_path = resolved
    state.ddo_durable_ledger_path = str(resolved)


def _assert_ledger_path_matches(state: Any, resolved: Path) -> None:
    binding = getattr(state, "ddo_capture_binding", None)
    if not isinstance(binding, DdoCaptureBindingV0) or binding.ledger_path is None:
        raise DdoHostScopeInputError(SCOPE_INPUT_CONFLICT, "LEDGER_PATH_UNBOUND_AFTER_SCOPE")
    if Path(binding.ledger_path) != resolved:
        raise DdoHostScopeInputError(SCOPE_INPUT_CONFLICT, "LEDGER_PATH_REBIND_CONFLICT")
    host_path = getattr(state, "ddo_durable_ledger_path", None)
    if host_path is None or str(host_path) != str(resolved):
        raise DdoHostScopeInputError(SCOPE_INPUT_CONFLICT, "LEDGER_PATH_CONFLICT")


def _assert_host_scope_matches_frozen(state: Any, scope: DdoObservationHostScopeInputsV1) -> None:
    if (
        str(getattr(state, "ddo_durable_evidence_runtime_state_root", None))
        != scope.runtime_state_root
    ):
        raise DdoHostScopeInputError(SCOPE_INPUT_CONFLICT, "RUNTIME_STATE_ROOT_CONFLICT")
    if str(getattr(state, "ddo_evidence_environment", None)) != scope.environment.value:
        raise DdoHostScopeInputError(SCOPE_INPUT_CONFLICT, "ENVIRONMENT_CONFLICT")
    if str(getattr(state, "ddo_evidence_account_scope", None)) != scope.account_identity:
        raise DdoHostScopeInputError(SCOPE_INPUT_CONFLICT, "ACCOUNT_SCOPE_CONFLICT")
    if str(getattr(state, "ddo_evidence_environment_binding_status", None)) != "BOUND":
        raise DdoHostScopeInputError(SCOPE_INPUT_CONFLICT, "ENVIRONMENT_BINDING_STATUS_CONFLICT")
    if str(getattr(state, "ddo_evidence_account_binding_status", None)) != "BOUND":
        raise DdoHostScopeInputError(SCOPE_INPUT_CONFLICT, "ACCOUNT_BINDING_STATUS_CONFLICT")
    if scope.system_scope != DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN:
        raise DdoHostScopeInputError(SCOPE_INPUT_CONFLICT, "SYSTEM_SCOPE_CONFLICT")
