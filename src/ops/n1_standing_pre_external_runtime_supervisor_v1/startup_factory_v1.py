"""Prepare an occupied-slot N1 request and open its existing GET-only ports on admission."""

from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import asdict
from functools import lru_cache, partial
from hashlib import sha256
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
    _cursor_floor_or_zero,
)
from src.ops.execution_reconciliation_proof_store_v1 import require_private_proof_root_v1
from src.ops.full_core_live_path_composition_root_v1.current_productive_bounded_continuous_get_budget_contract_v1 import (
    compute_productive_policy_governed_live_c1_shared_transport_max_request_count_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    RUNTIME_OWNER_GO,
    _validate_authorization,
    mint_continuous_run_id_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_live_c1_get_only_fresh_pretrade_transport_bind_v1 import (
    open_governed_live_c1_get_only_fresh_pretrade_transport_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    build_s8_occupied_lane_pairs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_s6_live_fresh_c1_continuous_observation_source_v1 import (
    LiveFreshC1ContinuousObservationSourceV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.session_integration_v1 import (
    wrap_observation_source_for_pending_outcome_advance_v1,
)
from src.ops.gates.risk_gate import canonical_kill_switch_state_path
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    assert_current_productive_29p_execution_identity_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

from .constants_v1 import TRANSPORT_SCOPE_SCOPED_READONLY_GET
from .supervisor_v1 import StandingSupervisorConfigV1, budget_owner_root_for_config_v1
from .unattended_v1 import PreparedN1RequestV1, UnattendedHostBoundsV1, unattended_request_digest_v1


_REPO = Path(__file__).resolve().parents[3]
_ROOT_FIELDS = {
    "public_store_root",
    "private_store_root",
    "lane_state_root",
    "lock_root",
    "cap24_productivity_root",
    "f1_m9_ledger_root",
    "occupied_mark_proof_root",
}
_AUTH_FIELDS = {
    "max_cycles_per_run",
    "max_run_duration_seconds",
    "wait_interval_seconds",
    "max_wait_for_next_c1_seconds",
    "stall_seconds",
}
_STARTER = (
    "scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py"
)


class _LaneG17(Mapping):
    """Defer normal market-data acquisition until N1 has checked the original position."""

    def __init__(self, load_producer):
        self._load_producer = load_producer

    def __getitem__(self, lane):
        if lane != "LANE_1":
            raise KeyError(lane)
        return self._load_producer()

    def __iter__(self):
        return iter(("LANE_1",))

    def __len__(self):
        return 1


def _fresh_rest(transport, auth_required, path, params):
    endpoint = f"{path}?{urlencode(params)}" if params else path
    result = transport.get(
        endpoint=endpoint,
        auth_required=auth_required,
        pretrade_decision_id="N1_STANDING_BASELINE",
        get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )
    if (
        result.get_performed is not True
        or result.method != "GET"
        or result.endpoint != endpoint
        or result.auth_header_sent is not auth_required
        or result.historical_reuse
        or result.venue_live_contact is not True
        or result.http_status != 200
        or not isinstance(result.payload, dict)
        or result.payload.get("code") != "0"
        or not isinstance(result.payload.get("data"), list)
    ):
        raise ValueError("N1_STANDING_FRESH_GET_UNPROVEN")
    return result.payload


@contextmanager
def _open_ports(authorization, *, config, bound, cursor, ledger_root, repository_sha):
    from scripts.ops.run_current_productive_policy_governed_live_c1_pre_external_convergence_v1 import (
        _build_f1_m9_evaluator,
        _resolve_g17_producer,
    )

    max_requests = compute_productive_policy_governed_live_c1_shared_transport_max_request_count_v1(
        authorization
    )
    with open_governed_live_c1_get_only_fresh_pretrade_transport_v1(
        max_request_count=max_requests
    ) as (transport, _):

        @lru_cache(maxsize=1)
        def g17():
            return _resolve_g17_producer(
                bound=bound,
                transport=transport,
                evidence_store=config.evidence_root / "g17_hot_path",
                observed_unix=time.time(),
            )["LANE_1"]

        producers = _LaneG17(g17)

        @lru_cache(maxsize=1)
        def evaluator():
            return _build_f1_m9_evaluator(
                ledger_root=ledger_root,
                g17_producers=producers,
                bound=bound,
                initialize_revocations=False,
            )

        source = LiveFreshC1ContinuousObservationSourceV1(
            cursor_store_root=cursor,
            evidence_root=config.evidence_root,
            run_id=mint_continuous_run_id_v1(authorization),
            native_id=bound.venue_native_id,
            transport=transport,
        )
        yield {
            "observation_source": wrap_observation_source_for_pending_outcome_advance_v1(
                source,
                lane_state_root=config.lane_state_root,
                evidence_root=config.evidence_root,
                canonical_instrument_id=bound.instrument_id,
                native_id=bound.venue_native_id,
                repository_sha=repository_sha,
            ),
            "g17_producers": producers,
            "f1_m9_cycle_evaluator": lambda cycle: evaluator()(cycle),
            "public_rest_fetch": partial(_fresh_rest, transport, False),
            "private_rest_fetch": partial(_fresh_rest, transport, True),
            "pretrade_transport": transport,
        }


def prepare_occupied_n1_request_v1(*, attempt_index, evidence_root, runtime_config):
    """Prepare an admitted checkout's request before the host opens its ports."""
    prepared = _prepare_occupied_n1_request(
        attempt_index=attempt_index, evidence_root=evidence_root, runtime_config=runtime_config
    )
    assert_current_productive_29p_execution_identity_v1(
        declared_origin_main_sha=prepared.request["origin_main_sha"]
    )
    return prepared


def _prepare_occupied_n1_request(*, attempt_index, evidence_root, runtime_config):
    """Load explicit startup inputs without opening credentials, sockets or a writer."""
    if type(attempt_index) is not int or attempt_index < 1:
        raise ValueError("N1_STANDING_ATTEMPT_INVALID")
    if not isinstance(runtime_config, dict) or runtime_config.keys() != {
        "repository_sha",
        "roots",
        "expected_account_identity",
        "bound",
        "authorization",
    }:
        raise ValueError("N1_STANDING_CONFIG_SHAPE_INVALID")
    revision = runtime_config["repository_sha"]
    account = runtime_config["expected_account_identity"]
    root_values = runtime_config["roots"]
    limits = runtime_config["authorization"]
    if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("N1_STANDING_REVISION_INVALID")
    if not isinstance(account, str) or not account or account != account.strip():
        raise ValueError("N1_STANDING_ACCOUNT_IDENTITY_REQUIRED")
    if not isinstance(root_values, dict) or root_values.keys() != _ROOT_FIELDS:
        raise ValueError("N1_STANDING_EXPLICIT_ROOTS_REQUIRED")
    if not isinstance(limits, dict) or limits.keys() != _AUTH_FIELDS:
        raise ValueError("N1_STANDING_EXPLICIT_BOUNDS_REQUIRED")
    roots = {name: Path(value) for name, value in root_values.items()}
    if any(
        not path.is_absolute() or path != path.resolve() or not path.is_dir()
        for path in roots.values()
    ):
        raise ValueError("N1_STANDING_EXISTING_CANONICAL_ROOTS_REQUIRED")
    if len(set(roots.values())) != len(roots):
        raise ValueError("N1_STANDING_DISTINCT_ROOTS_REQUIRED")
    proof_root = require_private_proof_root_v1(roots.pop("occupied_mark_proof_root"))
    ledger_root = roots.pop("f1_m9_ledger_root")
    if not all(
        (ledger_root / name).is_file()
        for name in ("apply.jsonl", "apply_rev.jsonl", "threshold.jsonl", "threshold_rev.jsonl")
    ):
        raise ValueError("N1_STANDING_ORIGINAL_F1_M9_LEDGERS_REQUIRED")
    # Recovery reads the original persisted binding, including its selection
    # state. The supervisor separately admits current selection after recovery.
    bound = BoundInstrumentV1(**runtime_config["bound"])
    if not bound.instrument_id or not bound.venue_native_id or not bound.selection_id:
        raise ValueError("N1_STANDING_ORIGINAL_INSTRUMENT_BINDING_REQUIRED")
    config = StandingSupervisorConfigV1(
        **roots,
        evidence_root=Path(evidence_root).resolve(),
        expected_account_identity=account,
        venue_native_id=bound.venue_native_id,
        canonical_instrument_id=bound.instrument_id,
        kill_switch_state_path=str(Path(canonical_kill_switch_state_path()).resolve()),
        transport_scope=TRANSPORT_SCOPE_SCOPED_READONLY_GET,
        require_pretrade_collection=True,
    )
    budget_root = budget_owner_root_for_config_v1(config)
    if not (budget_root / "owner" / "reservations.sqlite3").is_file():
        raise ValueError("N1_STANDING_ORIGINAL_BUDGET_STORE_REQUIRED")
    pair = build_s8_occupied_lane_pairs_v1(lane_state_root=config.lane_state_root, bound=bound)[
        "LANE_1"
    ]
    cursor = Path(pair[0].lane_state_root)
    authorization = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=RUNTIME_OWNER_GO,
        native_id=bound.venue_native_id,
        bar="1m",
        expected_cursor_floor=_cursor_floor_or_zero(cursor),
        **limits,
    )
    _validate_authorization(authorization)
    request = dict(
        config=config,
        origin_main_sha=revision,
        bound=bound,
        authorization=authorization,
        repo_root=_REPO,
        occupied_mark_proof_root=proof_root,
    )
    digest = sha256(json.dumps(runtime_config, sort_keys=True, allow_nan=False).encode())
    digest.update((_REPO / _STARTER).read_bytes())
    return PreparedN1RequestV1(
        request=request,
        runtime_config_digest=digest.hexdigest(),
        open_ports=partial(
            _open_ports,
            config=config,
            bound=bound,
            cursor=cursor,
            ledger_root=ledger_root,
            repository_sha=revision,
        ),
    )


def build_occupied_n1_manifest_v1(*, host_id, state_root, expires_at_unix, runtime_config):
    """Build the manifest data from the checked original roots without activating it."""
    state = Path(state_root)
    if not state.is_absolute() or state != state.resolve():
        raise ValueError("HOST_SERVICE_CANONICAL_PATH_REQUIRED")
    prepared = _prepare_occupied_n1_request(
        attempt_index=1, evidence_root=state / "attempts" / "1", runtime_config=runtime_config
    )
    auth = prepared.request["authorization"]
    bounds = UnattendedHostBoundsV1(
        host_id=host_id,
        repository_sha=prepared.request["origin_main_sha"],
        runtime_config_digest=unattended_request_digest_v1(prepared),
        expires_at_unix=expires_at_unix,
        max_total_cycles=auth.max_cycles_per_run,
        max_total_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=auth.wait_interval_seconds,
    )
    bounds.validate_v1()
    return {
        "schema": "n1_unattended_host_service.v1",
        "bounds": asdict(bounds),
        "state_root": str(state),
        "repository_root": str(_REPO),
        "runtime_factory": f"{__name__}:prepare_occupied_n1_request_v1",
        "runtime_request_config": runtime_config,
    }
