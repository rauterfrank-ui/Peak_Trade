"""Fail-closed skeleton for a future universe-refresh epoch.

WP-P1 never authorizes a refresh. WP-P2 accounts one in-memory acquisition on
the existing SelectionNetworkBudgetV1 class. WP-P3 names the existing
Cap-2.1→2.3 composition and does not call it. WP-P4 reads a committed
ranking snapshot through the existing Top-20 admission readers and does not
write residency, start a scheduler, or select for trading. None of these
steps calls a producer, opens a transport, publishes a snapshot, or mutates
selection. WP-P5 records selection continuity and does not call the
selection policy. WP-P6 describes Natural Enter isolation and does not
start, stop, reset, or rebind that runtime. WP-P8 uses the canonical
selection-budget class and does not release a refresh call. WP-P9
prepares an explicit previous-selection handoff and does not invoke it.
WP-P12 records data-completion evidence and does not release a residency slot.
"""

from __future__ import annotations

import sys
import types
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

REFRESH_ACTIVATION_ALLOWED: bool = False
CAP21_TO_CAP23_BINDING_INVOCATION_ALLOWED: bool = False
RUNTIME_AUTHORIZATION_EFFECT: str = "NONE"
CAP21_TO_CAP23_COMPOSITION_SYMBOL = "run_cap21_to_cap23_persist_productive_v1"
CAP21_TO_CAP23_COMPOSITION_MODULE = (
    "src.ops.governed_productive_account_equity_authority_producer_v1."
    "current_productive_cap21_to_cap23_productive_persistence_v1"
)
EXISTING_STATE_ROOTS_V1 = (
    "runtime_state/universe",
    "runtime_state/ranking",
    "runtime_state/selection",
)
EXISTING_UNIVERSE_WRITER_SYMBOL = "GovernedUniverseSingleWriterV1"
RANKING_VOLATILITY_OWNER = "population_sigma_log_returns_v1"
G17_VOLATILITY_OWNER = "CanonicalVolatilityTypedRuntimeProducerScaffoldV1"
TOP20_SNAPSHOT_READ_ALLOWED = False
NATURAL_ENTER_ISOLATION_INVOCATION_ALLOWED = False
NATURAL_ENTER_ENTRY_SYMBOL = (
    "run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1"
)
NATURAL_ENTER_ENTRY_MODULE = (
    "src.ops.full_core_live_path_composition_root_v1."
    "current_productive_persistent_natural_enter_convergence_v1"
)
_RANKING_STAGING_MARKER = ".productive_futures_ranking_staging_"
_OPS_ROOT = Path(__file__).resolve().parent
_WP_P4_RANKING_CONSTANTS = "_wp_p4_ranking_constants_v1"
_WP_P4_SELECTION_CONSTANTS = "_wp_p4_selection_constants_v1"
_WP_P4_TOP20_CONSTANTS = "_wp_p4_top20_constants_v1"
_WP_P4_RANKING_MODELS = "_wp_p4_ranking_models_v1"
_WP_P4_TOP20_ADMISSION = "_wp_p4_top20_admission_v1"
_WP_P12_ECONOMIC_MD_CONSTANTS = "_wp_p12_economic_md_constants_v1"
_WP_P12_FEATURE_CONSTANTS = "_wp_p12_feature_constants_v1"
CANONICAL_SELECTION_BUDGET_MODULE = (
    "src.ops.governed_productive_account_equity_authority_producer_v1."
    "current_productive_selection_network_budget_v1"
)
_BUDGET_FILE = (
    Path(__file__).resolve().parent
    / "governed_productive_account_equity_authority_producer_v1"
    / "current_productive_selection_network_budget_v1.py"
)


class UniverseRefreshEpochStatusV1(str, Enum):
    REFRESH_NOT_AUTHORIZED = "REFRESH_NOT_AUTHORIZED"


class UniverseRefreshNaturalEnterIsolationStatusV1(str, Enum):
    NATURAL_ENTER_ISOLATION_UNPROVEN = "NATURAL_ENTER_ISOLATION_UNPROVEN"
    NATURAL_ENTER_ISOLATION_HELD = "NATURAL_ENTER_ISOLATION_HELD"


class UniverseRefreshSelectionContinuityStatusV1(str, Enum):
    SELECTION_CONTINUITY_UNPROVEN = "SELECTION_CONTINUITY_UNPROVEN"
    SELECTION_CONTINUITY_HELD = "SELECTION_CONTINUITY_HELD"


class UniverseRefreshTop20SnapshotStatusV1(str, Enum):
    TOP20_SNAPSHOT_NOT_READY = "TOP20_SNAPSHOT_NOT_READY"
    TOP20_HYPOTHETICAL_ADMISSION = "TOP20_HYPOTHETICAL_ADMISSION"


class UniverseRefreshCap21BindingStatusV1(str, Enum):
    CAP21_TO_CAP23_BINDING_NOT_INVOKED = "CAP21_TO_CAP23_BINDING_NOT_INVOKED"


class UniverseRefreshReleasePreflightStatusV1(str, Enum):
    PREFLIGHT_BUDGET_REJECTED = "PREFLIGHT_BUDGET_REJECTED"
    PREFLIGHT_CONTINUITY_UNPROVEN = "PREFLIGHT_CONTINUITY_UNPROVEN"
    PREFLIGHT_HANDOFF_PREPARED_NOT_INVOKED = "PREFLIGHT_HANDOFF_PREPARED_NOT_INVOKED"


class UniverseRefreshSelectionHandoffStatusV1(str, Enum):
    HANDOFF_BUDGET_REJECTED = "HANDOFF_BUDGET_REJECTED"
    HANDOFF_CONTINUITY_UNPROVEN = "HANDOFF_CONTINUITY_UNPROVEN"
    HANDOFF_PREPARED_NOT_INVOKED = "HANDOFF_PREPARED_NOT_INVOKED"


class DataCompletionStatusV1(str, Enum):
    DATA_COMPLETION_UNPROVEN = "DATA_COMPLETION_UNPROVEN"
    DATA_COMPLETION_PROVEN = "DATA_COMPLETION_PROVEN"


class UniverseRefreshBudgetEpochStatusV1(str, Enum):
    BUDGET_NOT_AUTHORIZED = "BUDGET_NOT_AUTHORIZED"
    BUDGET_CEILING_INVALID = "BUDGET_CEILING_INVALID"
    BUDGET_INSUFFICIENT = "BUDGET_INSUFFICIENT"
    INVALID_ELIGIBLE_COUNT = "INVALID_ELIGIBLE_COUNT"
    BUDGET_ACCOUNTED = "BUDGET_ACCOUNTED"


@dataclass(frozen=True, slots=True)
class UniverseRefreshEpochRequestV1:
    epoch_id: str


@dataclass(frozen=True, slots=True)
class UniverseRefreshEpochResultV1:
    epoch_id: str
    status: UniverseRefreshEpochStatusV1
    refresh_activation_allowed: bool
    producer_executed: bool
    snapshot_published: bool
    selection_mutated: bool
    network_requested: bool
    file_write_attempted: bool


@dataclass(frozen=True, slots=True)
class UniverseRefreshNaturalEnterIsolationRequestV1:
    epoch_id: str
    natural_enter_binding: str = "UNKNOWN"
    bound_instrument_id: str = ""
    trading_epoch_id: str = ""
    ranking_favorite_id: str = ""
    selection_continuity_status: str = "SELECTION_CONTINUITY_UNPROVEN"


@dataclass(frozen=True, slots=True)
class UniverseRefreshNaturalEnterIsolationResultV1:
    epoch_id: str
    status: UniverseRefreshNaturalEnterIsolationStatusV1
    entry_symbol: str
    entry_module: str
    natural_enter_binding: str
    bound_instrument_id: str
    trading_epoch_id: str
    ranking_favorite_id: str
    ranking_favorite_changed: bool
    selection_continuity_proven: bool
    isolation_describes_only: bool
    runtime_control_performed: bool
    natural_enter_invoked: bool
    natural_enter_restarted: bool
    natural_enter_interrupted: bool
    natural_enter_reset: bool
    instrument_rebound: bool
    trading_epoch_created: bool
    trading_epoch_reset: bool
    position_closed: bool
    direction_switch_authorized: bool
    master_v2_invoked: bool
    double_play_invoked: bool
    selection_mutated: bool
    snapshot_write_attempted: bool
    state_write_attempted: bool
    network_requested: bool
    http_get_performed: bool
    http_post_performed: bool
    public_websocket_connected: bool
    private_websocket_connected: bool
    subscription_opened: bool


@dataclass(frozen=True, slots=True)
class UniverseRefreshSelectionContinuityRequestV1:
    epoch_id: str
    previous_selection: object = None
    state_provenance_proven: bool = False
    position_truth: str = "UNKNOWN"
    open_position_instrument_id: str = ""
    holding_elapsed_seconds: float | None = None
    ranking_favorite_id: str = ""


@dataclass(frozen=True, slots=True)
class UniverseRefreshSelectionContinuityResultV1:
    epoch_id: str
    status: UniverseRefreshSelectionContinuityStatusV1
    selection_owner: str
    retained_instrument_id: str
    previous_selection_supplied: bool
    previous_selection_forced_none: bool
    load_previous_from_state: bool
    state_provenance_proven: bool
    position_truth: str
    unknown_position_treated_as_flat: bool
    open_position_present: bool
    open_position_blocks_switch: bool
    holding_period_active: bool
    min_holding_period_seconds: float
    ranking_favorite_id: str
    ranking_favorite_changed: bool
    switch_authorized: bool
    new_selection_created: bool
    selection_policy_invoked: bool
    selection_mutated: bool
    state_write_attempted: bool
    second_selection_authority: bool
    natural_enter_started: bool
    trading_epoch_created: bool
    master_v2_invoked: bool
    double_play_invoked: bool
    network_requested: bool
    http_get_performed: bool
    public_websocket_connected: bool
    private_websocket_connected: bool


@dataclass(frozen=True, slots=True)
class UniverseRefreshTop20RankObservationV1:
    canonical_instrument_id: str
    rank: int | None
    in_top20: bool


@dataclass(frozen=True, slots=True)
class UniverseRefreshTop20SnapshotRequestV1:
    epoch_id: str
    snapshot: object = None
    snapshot_committed: bool = False
    prior_canonical_ids: tuple[str, ...] = ()
    observed_at_unix: float = 0.0


@dataclass(frozen=True, slots=True)
class UniverseRefreshTop20SnapshotResultV1:
    epoch_id: str
    status: UniverseRefreshTop20SnapshotStatusV1
    ranking_snapshot_owner: str
    top20_role: str
    hypothetical_new: tuple[str, ...]
    hypothetical_departed: tuple[str, ...]
    hypothetical_unchanged: tuple[str, ...]
    rank_observations: tuple[UniverseRefreshTop20RankObservationV1, ...]
    orchestrator_owns_ranking_state: bool
    orchestrator_owns_residency_state: bool
    residency_write_performed: bool
    scheduler_tick_performed: bool
    admission_mutated: bool
    productive_admission: bool
    selection_mutated: bool
    producer_executed: bool
    snapshot_published: bool
    network_requested: bool
    http_get_performed: bool
    public_websocket_connected: bool
    private_websocket_connected: bool
    file_write_attempted: bool
    second_writer_claimed: bool


@dataclass(frozen=True, slots=True)
class UniverseRefreshCap21BindingRequestV1:
    epoch_id: str


@dataclass(frozen=True, slots=True)
class UniverseRefreshCap21BindingResultV1:
    epoch_id: str
    status: UniverseRefreshCap21BindingStatusV1
    composition_symbol: str
    composition_module: str
    state_roots: tuple[str, ...]
    existing_universe_writer_symbol: str
    ranking_volatility_owner: str
    g17_volatility_owner: str
    invocation_performed: bool
    producer_executed: bool
    snapshot_published: bool
    selection_mutated: bool
    network_requested: bool
    http_get_performed: bool
    public_websocket_connected: bool
    private_websocket_connected: bool
    public_websocket_equated_with_http_get: bool
    binding_owns_state: bool
    second_writer_claimed: bool
    shared_volatility_epoch_enforced: bool
    market_data_redirected: bool
    hold_semantics_changed: bool
    file_write_attempted: bool


@dataclass(frozen=True, slots=True)
class DataCompletionEvidenceV1:
    instrument_id: str
    economic_md_ok: bool = False
    economic_input_snapshot_id: str = ""
    economic_instrument_id: str = ""
    economic_raw_input_eligible: bool = False
    economic_raw_input_digest: str = ""
    economic_mark_count: int = 0
    feature_production_snapshot_id: str = ""
    feature_production_digest: str = ""
    feature_instrument_id: str = ""
    feature_production_ready: bool = False
    feature_mark_count: int = 0
    feature_economic_md_raw_input_digest: str = ""
    ranking_snapshot_id: str = ""
    ranking_snapshot_state: str = ""
    ranking_instrument_id: str = ""
    ranking_feature_production_snapshot_id: str = ""
    ranking_feature_production_digest: str = ""
    residency_epoch_id: str = ""
    bound_residency_epoch_id: str = ""
    slot_already_released: bool = False
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DataCompletionSlotReleaseResultV1:
    instrument_id: str
    status: DataCompletionStatusV1
    residency_epoch_id: str
    hypothetical_slot_release: bool
    slot_already_released: bool
    slot_release_performed: bool
    admission_performed: bool
    residency_write_attempted: bool
    scheduler_tick_performed: bool
    replay_witness_created: bool
    timeout_completion: bool
    positive_negative_evaluation: bool
    ranking_authority: bool
    selection_authority: bool
    trading_authority: bool
    network_requested: bool
    http_get_performed: bool
    http_post_performed: bool
    public_websocket_connected: bool
    private_websocket_connected: bool


@dataclass(frozen=True, slots=True)
class UniverseRefreshBudgetEpochRequestV1:
    epoch_id: str
    max_total_attempts: object = None
    eligible_count: object = None


@dataclass(frozen=True, slots=True)
class UniverseRefreshSelectionHandoffRequestV1:
    epoch_id: str
    budget: object = None
    continuity: object = None
    previous_selection: object = None
    open_position_instrument_id: str = ""


@dataclass(frozen=True, slots=True)
class UniverseRefreshSelectionHandoffResultV1:
    epoch_id: str
    status: UniverseRefreshSelectionHandoffStatusV1
    previous_selection: object
    load_previous_from_state: bool
    open_position_instrument_id: str | None
    position_truth: str
    unknown_position_treated_as_flat: bool
    holding_period_active: bool
    holding_argument_supplied: bool
    budget_rejected_before_producer: bool
    invocation_performed: bool
    producer_executed: bool
    cap21_invoked: bool
    selection_policy_invoked: bool
    selection_mutated: bool
    state_write_attempted: bool
    network_requested: bool
    http_get_performed: bool
    http_post_performed: bool
    public_websocket_connected: bool
    private_websocket_connected: bool
    master_v2_invoked: bool
    double_play_invoked: bool
    natural_enter_invoked: bool


@dataclass(frozen=True, slots=True)
class UniverseRefreshReleasePreflightRequestV1:
    epoch_id: str
    budget: object = None
    continuity: object = None


@dataclass(frozen=True, slots=True)
class UniverseRefreshReleasePreflightResultV1:
    epoch_id: str
    status: UniverseRefreshReleasePreflightStatusV1
    budget_identity_canonical: bool
    continuity_proven: bool
    selection_handoff_supported: bool
    previous_selection_passed_as_none: bool
    release_performed: bool
    producer_executed: bool
    cap21_invoked: bool
    selection_mutated: bool
    state_write_attempted: bool
    network_requested: bool
    http_get_performed: bool
    http_post_performed: bool
    public_websocket_connected: bool
    private_websocket_connected: bool
    master_v2_invoked: bool
    double_play_invoked: bool
    natural_enter_invoked: bool


@dataclass(frozen=True, slots=True)
class UniverseRefreshBudgetEpochResultV1:
    epoch_id: str
    status: UniverseRefreshBudgetEpochStatusV1
    max_total_attempts: object
    attempts_accounted: int
    refresh_activation_allowed: bool
    producer_executed: bool
    snapshot_published: bool
    selection_mutated: bool
    network_requested: bool
    file_write_attempted: bool
    ceiling_unchanged: bool


def _load_selection_network_budget_v1():
    """Load the canonical budget module without importing its package.

    The budget file imports only the standard library. Registering it under
    its canonical module name keeps one class identity and does not execute
    the package initializer.
    """

    if CANONICAL_SELECTION_BUDGET_MODULE in sys.modules:
        existing = sys.modules[CANONICAL_SELECTION_BUDGET_MODULE]
        if not hasattr(existing, "SelectionNetworkBudgetV1"):
            raise RuntimeError("SELECTION_NETWORK_BUDGET_MODULE_UNAVAILABLE")
        return existing
    spec = spec_from_file_location(CANONICAL_SELECTION_BUDGET_MODULE, _BUDGET_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError("SELECTION_NETWORK_BUDGET_MODULE_UNAVAILABLE")
    module = module_from_spec(spec)
    sys.modules[CANONICAL_SELECTION_BUDGET_MODULE] = module
    spec.loader.exec_module(module)
    return module


_SELECTION_NETWORK_BUDGET_V1 = _load_selection_network_budget_v1()


def _epoch_identity(epoch_id: object) -> str:
    if isinstance(epoch_id, str):
        return epoch_id
    return ""


def _not_authorized(epoch_id: str) -> UniverseRefreshEpochResultV1:
    return UniverseRefreshEpochResultV1(
        epoch_id=epoch_id,
        status=UniverseRefreshEpochStatusV1.REFRESH_NOT_AUTHORIZED,
        refresh_activation_allowed=False,
        producer_executed=False,
        snapshot_published=False,
        selection_mutated=False,
        network_requested=False,
        file_write_attempted=False,
    )


def _budget_result(
    *,
    epoch_id: str,
    status: UniverseRefreshBudgetEpochStatusV1,
    max_total_attempts: object,
    attempts_accounted: int,
    supplied_ceiling: object,
) -> UniverseRefreshBudgetEpochResultV1:
    return UniverseRefreshBudgetEpochResultV1(
        epoch_id=epoch_id,
        status=status,
        max_total_attempts=max_total_attempts,
        attempts_accounted=attempts_accounted,
        refresh_activation_allowed=False,
        producer_executed=False,
        snapshot_published=False,
        selection_mutated=False,
        network_requested=False,
        file_write_attempted=False,
        ceiling_unchanged=max_total_attempts == supplied_ceiling,
    )


def _account_acquisition(budget: object, eligible_count: object) -> None:
    """Count one acquisition with the existing budget class.

    ``require_complete_economic_md_collection`` is the fit gate. The following
    loop only records attempts that gate already accepted, using the class
    constants. The ceiling attribute is never assigned.
    """

    budget_module = _SELECTION_NETWORK_BUDGET_V1
    for _ in range(budget_module.SELECTION_INVENTORY_GETS):
        budget.before_http_attempt()
    budget.require_complete_economic_md_collection(eligible_count=eligible_count)
    attempts_per_get = budget_module.SELECTION_ECONOMIC_MD_MAX_RETRIES + 1
    economic_attempts = (
        eligible_count * budget_module.SELECTION_ECONOMIC_MD_GETS_PER_INSTRUMENT * attempts_per_get
    )
    for _ in range(economic_attempts):
        budget.before_http_attempt()


def run_universe_refresh_epoch_v1(
    request: UniverseRefreshEpochRequestV1,
) -> UniverseRefreshEpochResultV1:
    """Return a deterministic unauthorized epoch result.

    No grant, constant, or caller flag can enable producer, snapshot,
    selection, network, or file effects in this skeleton.
    """

    return _not_authorized(_epoch_identity(request.epoch_id))


def run_universe_refresh_budget_epoch_v1(
    request: UniverseRefreshBudgetEpochRequestV1,
) -> UniverseRefreshBudgetEpochResultV1:
    """Account one finite acquisition offline.

    A missing ceiling is not authority. A fitting ceiling is still not a
    refresh activation, a GET, or a snapshot publication.
    """

    epoch_id = _epoch_identity(request.epoch_id)
    ceiling = request.max_total_attempts
    if ceiling is None:
        return _budget_result(
            epoch_id=epoch_id,
            status=UniverseRefreshBudgetEpochStatusV1.BUDGET_NOT_AUTHORIZED,
            max_total_attempts=None,
            attempts_accounted=0,
            supplied_ceiling=None,
        )

    budget_module = _SELECTION_NETWORK_BUDGET_V1
    try:
        budget = budget_module.SelectionNetworkBudgetV1(max_total_attempts=ceiling)
    except budget_module.SelectionNetworkBudgetError:
        return _budget_result(
            epoch_id=epoch_id,
            status=UniverseRefreshBudgetEpochStatusV1.BUDGET_CEILING_INVALID,
            max_total_attempts=ceiling,
            attempts_accounted=0,
            supplied_ceiling=ceiling,
        )

    try:
        _account_acquisition(budget, request.eligible_count)
    except budget_module.SelectionNetworkBudgetExceeded:
        return _budget_result(
            epoch_id=epoch_id,
            status=UniverseRefreshBudgetEpochStatusV1.BUDGET_INSUFFICIENT,
            max_total_attempts=budget.max_total_attempts,
            attempts_accounted=budget.attempts,
            supplied_ceiling=ceiling,
        )
    except budget_module.SelectionNetworkBudgetError as exc:
        if str(exc).startswith("SELECTION_ELIGIBLE_COUNT_INVALID"):
            status = UniverseRefreshBudgetEpochStatusV1.INVALID_ELIGIBLE_COUNT
        else:
            status = UniverseRefreshBudgetEpochStatusV1.BUDGET_CEILING_INVALID
        return _budget_result(
            epoch_id=epoch_id,
            status=status,
            max_total_attempts=budget.max_total_attempts,
            attempts_accounted=budget.attempts,
            supplied_ceiling=ceiling,
        )

    status = UniverseRefreshBudgetEpochStatusV1.BUDGET_ACCOUNTED
    if budget.max_total_attempts != ceiling:
        status = UniverseRefreshBudgetEpochStatusV1.BUDGET_CEILING_INVALID
    return _budget_result(
        epoch_id=epoch_id,
        status=status,
        max_total_attempts=budget.max_total_attempts,
        attempts_accounted=budget.attempts,
        supplied_ceiling=ceiling,
    )


def bind_universe_refresh_to_cap21_to_cap23_v1(
    request: UniverseRefreshCap21BindingRequestV1,
) -> UniverseRefreshCap21BindingResultV1:
    """Describe the existing Cap-2.1→2.3 composition without calling it.

    The invocation constant is not a switch. Public WebSocket, private
    WebSocket, and HTTP GET stay untouched and are not treated as the same path.
    """

    return UniverseRefreshCap21BindingResultV1(
        epoch_id=_epoch_identity(request.epoch_id),
        status=UniverseRefreshCap21BindingStatusV1.CAP21_TO_CAP23_BINDING_NOT_INVOKED,
        composition_symbol=CAP21_TO_CAP23_COMPOSITION_SYMBOL,
        composition_module=CAP21_TO_CAP23_COMPOSITION_MODULE,
        state_roots=EXISTING_STATE_ROOTS_V1,
        existing_universe_writer_symbol=EXISTING_UNIVERSE_WRITER_SYMBOL,
        ranking_volatility_owner=RANKING_VOLATILITY_OWNER,
        g17_volatility_owner=G17_VOLATILITY_OWNER,
        invocation_performed=False,
        producer_executed=False,
        snapshot_published=False,
        selection_mutated=False,
        network_requested=False,
        http_get_performed=False,
        public_websocket_connected=False,
        private_websocket_connected=False,
        public_websocket_equated_with_http_get=False,
        binding_owns_state=False,
        second_writer_claimed=False,
        shared_volatility_epoch_enforced=False,
        market_data_redirected=False,
        hold_semantics_changed=False,
        file_write_attempted=False,
    )


def _exec_isolated_module(name: str, path: Path, source: str) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def _load_top20_admission_v1() -> types.ModuleType:
    """Load the existing admission readers without the Top-20 package init.

    The package init imports the scheduler and the selection producer and
    currently cycles. The function bodies stay the on-disk source.
    """

    ranking_constants = _OPS_ROOT / "productive_futures_ranking_producer_v1" / "constants_v1.py"
    selection_constants = _OPS_ROOT / "single_selected_future_policy_v1" / "constants_v1.py"
    top20_constants = _OPS_ROOT / "top20_opportunity_evaluation_residency_v1" / "constants_v1.py"
    ranking_models = _OPS_ROOT / "productive_futures_ranking_producer_v1" / "models_v1.py"
    admission = _OPS_ROOT / "top20_opportunity_evaluation_residency_v1" / "admission_v1.py"
    _exec_isolated_module(
        _WP_P4_RANKING_CONSTANTS,
        ranking_constants,
        ranking_constants.read_text(encoding="utf-8"),
    )
    _exec_isolated_module(
        _WP_P4_SELECTION_CONSTANTS,
        selection_constants,
        selection_constants.read_text(encoding="utf-8"),
    )
    _exec_isolated_module(
        _WP_P4_TOP20_CONSTANTS,
        top20_constants,
        top20_constants.read_text(encoding="utf-8"),
    )
    models_source = ranking_models.read_text(encoding="utf-8").replace(
        "src.ops.productive_futures_ranking_producer_v1.constants_v1",
        _WP_P4_RANKING_CONSTANTS,
    )
    _exec_isolated_module(_WP_P4_RANKING_MODELS, ranking_models, models_source)
    admission_source = admission.read_text(encoding="utf-8")
    for original, private in (
        (
            "src.ops.productive_futures_ranking_producer_v1.constants_v1",
            _WP_P4_RANKING_CONSTANTS,
        ),
        (
            "src.ops.single_selected_future_policy_v1.constants_v1",
            _WP_P4_SELECTION_CONSTANTS,
        ),
        (
            "src.ops.top20_opportunity_evaluation_residency_v1.constants_v1",
            _WP_P4_TOP20_CONSTANTS,
        ),
        (
            "src.ops.productive_futures_ranking_producer_v1.models_v1",
            _WP_P4_RANKING_MODELS,
        ),
    ):
        admission_source = admission_source.replace(original, private)
    return _exec_isolated_module(_WP_P4_TOP20_ADMISSION, admission, admission_source)


_TOP20_ADMISSION = _load_top20_admission_v1()


def _top20_closed(
    epoch_id: str,
    *,
    status: UniverseRefreshTop20SnapshotStatusV1,
    new: tuple[str, ...] = (),
    departed: tuple[str, ...] = (),
    unchanged: tuple[str, ...] = (),
    observations: tuple[UniverseRefreshTop20RankObservationV1, ...] = (),
) -> UniverseRefreshTop20SnapshotResultV1:
    return UniverseRefreshTop20SnapshotResultV1(
        epoch_id=epoch_id,
        status=status,
        ranking_snapshot_owner="ops.productive_futures_ranking_producer_v1",
        top20_role="reader",
        hypothetical_new=new,
        hypothetical_departed=departed,
        hypothetical_unchanged=unchanged,
        rank_observations=observations,
        orchestrator_owns_ranking_state=False,
        orchestrator_owns_residency_state=False,
        residency_write_performed=False,
        scheduler_tick_performed=False,
        admission_mutated=False,
        productive_admission=False,
        selection_mutated=False,
        producer_executed=False,
        snapshot_published=False,
        network_requested=False,
        http_get_performed=False,
        public_websocket_connected=False,
        private_websocket_connected=False,
        file_write_attempted=False,
        second_writer_claimed=False,
    )


def _snapshot_is_staging(snapshot: Mapping[str, object]) -> bool:
    for key in ("ranking_snapshot_id", "source_path", "snapshot_path"):
        if key not in snapshot:
            continue
        if _RANKING_STAGING_MARKER in str(snapshot[key]):
            return True
    return False


def bind_universe_refresh_top20_snapshot_v1(
    request: UniverseRefreshTop20SnapshotRequestV1,
) -> UniverseRefreshTop20SnapshotResultV1:
    """Read one committed ranking snapshot through the existing Top-20 readers.

    Results are hypothetical. Residency, the scheduler, selection, and both
    WebSocket paths stay unused. ``TOP20_SNAPSHOT_READ_ALLOWED`` is not a switch.
    """

    epoch_id = _epoch_identity(request.epoch_id)
    snapshot = request.snapshot
    if request.snapshot_committed is not True or not isinstance(snapshot, Mapping):
        return _top20_closed(
            epoch_id,
            status=UniverseRefreshTop20SnapshotStatusV1.TOP20_SNAPSHOT_NOT_READY,
        )
    if _snapshot_is_staging(snapshot):
        return _top20_closed(
            epoch_id,
            status=UniverseRefreshTop20SnapshotStatusV1.TOP20_SNAPSHOT_NOT_READY,
        )

    admission = _TOP20_ADMISSION
    try:
        eligible = admission.eligible_top20_candidates_v1(snapshot)
        universe_id = ""
        if "universe_snapshot_id" in snapshot:
            universe_id = str(snapshot["universe_snapshot_id"])
        already_admitted = tuple(
            (universe_id, canonical) for canonical in request.prior_canonical_ids
        )
        events = admission.admission_events_from_valid_snapshot_v1(
            snapshot,
            already_admitted=already_admitted,
        )
    except admission.ResidencyAdmissionError:
        return _top20_closed(
            epoch_id,
            status=UniverseRefreshTop20SnapshotStatusV1.TOP20_SNAPSHOT_NOT_READY,
        )

    current_ids = {canonical for canonical, _rank, _row in eligible}
    prior_ids = tuple(dict.fromkeys(request.prior_canonical_ids))
    new_ids = tuple(canonical for canonical, _rank, _row in events)
    unchanged_ids = tuple(canonical for canonical in prior_ids if canonical in current_ids)
    departed_ids = tuple(canonical for canonical in prior_ids if canonical not in current_ids)
    observed: list[UniverseRefreshTop20RankObservationV1] = []
    for canonical in (*new_ids, *unchanged_ids, *departed_ids):
        rank, in_top20 = admission.current_rank_observation_for_instrument_v1(
            snapshot,
            canonical_instrument_id=canonical,
            observed_at_unix=request.observed_at_unix,
        )
        observed.append(
            UniverseRefreshTop20RankObservationV1(
                canonical_instrument_id=canonical,
                rank=rank,
                in_top20=in_top20,
            )
        )
    return _top20_closed(
        epoch_id,
        status=UniverseRefreshTop20SnapshotStatusV1.TOP20_HYPOTHETICAL_ADMISSION,
        new=new_ids,
        departed=departed_ids,
        unchanged=unchanged_ids,
        observations=tuple(observed),
    )


def _selection_constants() -> types.ModuleType:
    return sys.modules[_WP_P4_SELECTION_CONSTANTS]


def _previous_instrument_id(previous_selection: object) -> str:
    constants = _selection_constants()
    if not isinstance(previous_selection, Mapping):
        return ""
    required = ("selection_id", "instrument_id", "integrity_digest", "state")
    if any(key not in previous_selection for key in required):
        return ""
    state = str(previous_selection["state"])
    if state not in constants.SELECTION_STATES or state == constants.STATE_NO_SELECTION:
        return ""
    instrument_id = str(previous_selection["instrument_id"]).strip()
    selection_id = str(previous_selection["selection_id"]).strip()
    digest = str(previous_selection["integrity_digest"]).strip()
    if instrument_id == "" or selection_id == "" or digest == "":
        return ""
    return instrument_id


def bind_universe_refresh_selection_continuity_v1(
    request: UniverseRefreshSelectionContinuityRequestV1,
) -> UniverseRefreshSelectionContinuityResultV1:
    """Hold the previous selection unless continuity is proven.

    This does not call ``run_single_selected_future_policy_v1`` and never
    supplies an implicit ``previous_selection=None``. Holding and the open
    position block stay the existing constants and reason token.
    """

    constants = _selection_constants()
    min_holding = float(constants.DEFAULT_MIN_HOLDING_PERIOD_SECONDS)
    retained = _previous_instrument_id(request.previous_selection)
    previous_supplied = retained != ""
    position_truth = str(request.position_truth or "UNKNOWN")
    favorite = str(request.ranking_favorite_id or "").strip()
    favorite_changed = previous_supplied and favorite != "" and favorite != retained
    elapsed = request.holding_elapsed_seconds
    holding_active = previous_supplied and elapsed is not None and float(elapsed) < min_holding
    open_present = position_truth == "OPEN" and bool(
        str(request.open_position_instrument_id).strip()
    )
    open_matches = open_present and str(request.open_position_instrument_id).strip() == retained
    blocks_switch = bool(open_matches and favorite_changed)
    provenance_proven = request.state_provenance_proven is True
    position_known = position_truth in {"OPEN", "FLAT"}
    holding_known = elapsed is not None and float(elapsed) >= 0.0
    open_position_coherent = position_truth != "OPEN" or open_matches
    continuity_proven = (
        previous_supplied
        and provenance_proven
        and position_known
        and holding_known
        and open_position_coherent
    )
    status = (
        UniverseRefreshSelectionContinuityStatusV1.SELECTION_CONTINUITY_HELD
        if continuity_proven
        else UniverseRefreshSelectionContinuityStatusV1.SELECTION_CONTINUITY_UNPROVEN
    )
    return UniverseRefreshSelectionContinuityResultV1(
        epoch_id=_epoch_identity(request.epoch_id),
        status=status,
        selection_owner="ops.single_selected_future_policy_v1",
        retained_instrument_id=retained if previous_supplied else "",
        previous_selection_supplied=previous_supplied,
        previous_selection_forced_none=False,
        load_previous_from_state=provenance_proven and previous_supplied,
        state_provenance_proven=provenance_proven,
        position_truth=position_truth,
        unknown_position_treated_as_flat=False,
        open_position_present=open_present,
        open_position_blocks_switch=blocks_switch,
        holding_period_active=holding_active,
        min_holding_period_seconds=min_holding,
        ranking_favorite_id=favorite,
        ranking_favorite_changed=favorite_changed,
        switch_authorized=False,
        new_selection_created=False,
        selection_policy_invoked=False,
        selection_mutated=False,
        state_write_attempted=False,
        second_selection_authority=False,
        natural_enter_started=False,
        trading_epoch_created=False,
        master_v2_invoked=False,
        double_play_invoked=False,
        network_requested=False,
        http_get_performed=False,
        public_websocket_connected=False,
        private_websocket_connected=False,
    )


def bind_universe_refresh_natural_enter_isolation_v1(
    request: UniverseRefreshNaturalEnterIsolationRequestV1,
) -> UniverseRefreshNaturalEnterIsolationResultV1:
    """Describe whether a refresh stays outside the existing Natural Enter entry.

    The entry symbol is recorded and never called. A ranking change does not
    restart, rebind, or mutate a trading epoch.
    """

    binding = str(request.natural_enter_binding or "UNKNOWN")
    instrument = str(request.bound_instrument_id or "").strip()
    trading_epoch = str(request.trading_epoch_id or "").strip()
    favorite = str(request.ranking_favorite_id or "").strip()
    continuity_proven = (
        request.selection_continuity_status
        == UniverseRefreshSelectionContinuityStatusV1.SELECTION_CONTINUITY_HELD.value
    )
    inactive = binding == "INACTIVE" and instrument == "" and trading_epoch == ""
    bound = binding == "BOUND" and instrument != "" and trading_epoch != ""
    favorite_changed = bound and favorite != "" and favorite != instrument
    proven = continuity_proven and (inactive or bound)
    status = (
        UniverseRefreshNaturalEnterIsolationStatusV1.NATURAL_ENTER_ISOLATION_HELD
        if proven
        else UniverseRefreshNaturalEnterIsolationStatusV1.NATURAL_ENTER_ISOLATION_UNPROVEN
    )
    return UniverseRefreshNaturalEnterIsolationResultV1(
        epoch_id=_epoch_identity(request.epoch_id),
        status=status,
        entry_symbol=NATURAL_ENTER_ENTRY_SYMBOL,
        entry_module=NATURAL_ENTER_ENTRY_MODULE,
        natural_enter_binding=binding,
        bound_instrument_id=instrument,
        trading_epoch_id=trading_epoch,
        ranking_favorite_id=favorite,
        ranking_favorite_changed=favorite_changed,
        selection_continuity_proven=continuity_proven,
        isolation_describes_only=True,
        runtime_control_performed=False,
        natural_enter_invoked=False,
        natural_enter_restarted=False,
        natural_enter_interrupted=False,
        natural_enter_reset=False,
        instrument_rebound=False,
        trading_epoch_created=False,
        trading_epoch_reset=False,
        position_closed=False,
        direction_switch_authorized=False,
        master_v2_invoked=False,
        double_play_invoked=False,
        selection_mutated=False,
        snapshot_write_attempted=False,
        state_write_attempted=False,
        network_requested=False,
        http_get_performed=False,
        http_post_performed=False,
        public_websocket_connected=False,
        private_websocket_connected=False,
        subscription_opened=False,
    )


def _preflight_closed(
    *,
    epoch_id: str,
    status: UniverseRefreshReleasePreflightStatusV1,
    budget_identity_canonical: bool,
    continuity_proven: bool,
    selection_handoff_supported: bool = False,
) -> UniverseRefreshReleasePreflightResultV1:
    return UniverseRefreshReleasePreflightResultV1(
        epoch_id=epoch_id,
        status=status,
        budget_identity_canonical=budget_identity_canonical,
        continuity_proven=continuity_proven,
        selection_handoff_supported=selection_handoff_supported,
        previous_selection_passed_as_none=False,
        release_performed=False,
        producer_executed=False,
        cap21_invoked=False,
        selection_mutated=False,
        state_write_attempted=False,
        network_requested=False,
        http_get_performed=False,
        http_post_performed=False,
        public_websocket_connected=False,
        private_websocket_connected=False,
        master_v2_invoked=False,
        double_play_invoked=False,
        natural_enter_invoked=False,
    )


def preflight_universe_refresh_release_v1(
    request: UniverseRefreshReleasePreflightRequestV1,
) -> UniverseRefreshReleasePreflightResultV1:
    """Refuse a refresh release before any producer runs.

    Budget identity is the canonical class. A prepared handoff still does not
    call Cap 2.1.
    """

    epoch_id = _epoch_identity(request.epoch_id)
    canonical_budget = _SELECTION_NETWORK_BUDGET_V1.SelectionNetworkBudgetV1
    budget_ok = isinstance(request.budget, canonical_budget)
    if not budget_ok:
        return _preflight_closed(
            epoch_id=epoch_id,
            status=UniverseRefreshReleasePreflightStatusV1.PREFLIGHT_BUDGET_REJECTED,
            budget_identity_canonical=False,
            continuity_proven=False,
        )
    continuity = request.continuity
    continuity_ok = (
        isinstance(continuity, UniverseRefreshSelectionContinuityResultV1)
        and continuity.status
        is UniverseRefreshSelectionContinuityStatusV1.SELECTION_CONTINUITY_HELD
        and continuity.previous_selection_supplied is True
        and continuity.previous_selection_forced_none is False
        and continuity.selection_policy_invoked is False
    )
    if not continuity_ok:
        return _preflight_closed(
            epoch_id=epoch_id,
            status=UniverseRefreshReleasePreflightStatusV1.PREFLIGHT_CONTINUITY_UNPROVEN,
            budget_identity_canonical=True,
            continuity_proven=False,
        )
    return _preflight_closed(
        epoch_id=epoch_id,
        status=UniverseRefreshReleasePreflightStatusV1.PREFLIGHT_HANDOFF_PREPARED_NOT_INVOKED,
        budget_identity_canonical=True,
        continuity_proven=True,
        selection_handoff_supported=True,
    )


def _handoff_closed(
    *,
    epoch_id: str,
    status: UniverseRefreshSelectionHandoffStatusV1,
    previous_selection: object = None,
    open_position_instrument_id: str | None = None,
    position_truth: str = "UNKNOWN",
    holding_period_active: bool = False,
    budget_rejected_before_producer: bool = False,
) -> UniverseRefreshSelectionHandoffResultV1:
    return UniverseRefreshSelectionHandoffResultV1(
        epoch_id=epoch_id,
        status=status,
        previous_selection=previous_selection,
        load_previous_from_state=False,
        open_position_instrument_id=open_position_instrument_id,
        position_truth=position_truth,
        unknown_position_treated_as_flat=False,
        holding_period_active=holding_period_active,
        holding_argument_supplied=False,
        budget_rejected_before_producer=budget_rejected_before_producer,
        invocation_performed=False,
        producer_executed=False,
        cap21_invoked=False,
        selection_policy_invoked=False,
        selection_mutated=False,
        state_write_attempted=False,
        network_requested=False,
        http_get_performed=False,
        http_post_performed=False,
        public_websocket_connected=False,
        private_websocket_connected=False,
        master_v2_invoked=False,
        double_play_invoked=False,
        natural_enter_invoked=False,
    )


def prepare_universe_refresh_selection_handoff_v1(
    request: UniverseRefreshSelectionHandoffRequestV1,
) -> UniverseRefreshSelectionHandoffResultV1:
    """Prepare an explicit previous selection without calling Cap 2.1.

    An invalid budget is rejected before any producer. Existing state is not
    loaded. Holding and the open-position block stay in the selection policy.
    """

    epoch_id = _epoch_identity(request.epoch_id)
    canonical_budget = _SELECTION_NETWORK_BUDGET_V1.SelectionNetworkBudgetV1
    if not isinstance(request.budget, canonical_budget):
        return _handoff_closed(
            epoch_id=epoch_id,
            status=UniverseRefreshSelectionHandoffStatusV1.HANDOFF_BUDGET_REJECTED,
            budget_rejected_before_producer=True,
        )
    continuity = request.continuity
    retained = _previous_instrument_id(request.previous_selection)
    open_id = str(request.open_position_instrument_id or "").strip()
    continuity_ok = (
        isinstance(continuity, UniverseRefreshSelectionContinuityResultV1)
        and continuity.status
        is UniverseRefreshSelectionContinuityStatusV1.SELECTION_CONTINUITY_HELD
        and continuity.previous_selection_supplied is True
        and continuity.previous_selection_forced_none is False
        and continuity.state_provenance_proven is True
        and continuity.selection_policy_invoked is False
        and continuity.unknown_position_treated_as_flat is False
        and continuity.position_truth in {"OPEN", "FLAT"}
        and retained != ""
        and continuity.retained_instrument_id == retained
    )
    if not continuity_ok or not isinstance(continuity, UniverseRefreshSelectionContinuityResultV1):
        return _handoff_closed(
            epoch_id=epoch_id,
            status=UniverseRefreshSelectionHandoffStatusV1.HANDOFF_CONTINUITY_UNPROVEN,
            position_truth=str(getattr(continuity, "position_truth", "UNKNOWN")),
        )
    if continuity.position_truth == "OPEN":
        if continuity.open_position_present is not True or open_id != retained:
            return _handoff_closed(
                epoch_id=epoch_id,
                status=UniverseRefreshSelectionHandoffStatusV1.HANDOFF_CONTINUITY_UNPROVEN,
                position_truth="OPEN",
            )
        forwarded_open_id: str | None = open_id
    elif open_id != "" or continuity.open_position_present is True:
        return _handoff_closed(
            epoch_id=epoch_id,
            status=UniverseRefreshSelectionHandoffStatusV1.HANDOFF_CONTINUITY_UNPROVEN,
            position_truth=continuity.position_truth,
        )
    else:
        forwarded_open_id = None
    return _handoff_closed(
        epoch_id=epoch_id,
        status=UniverseRefreshSelectionHandoffStatusV1.HANDOFF_PREPARED_NOT_INVOKED,
        previous_selection=request.previous_selection,
        open_position_instrument_id=forwarded_open_id,
        position_truth=continuity.position_truth,
        holding_period_active=continuity.holding_period_active,
    )


def _load_data_completion_constants_v1() -> None:
    economic = _OPS_ROOT / "economic_md_input_producer_v1" / "constants_v1.py"
    feature = _OPS_ROOT / "peak_trade_ranking_feature_production_v1" / "constants_v1.py"
    _exec_isolated_module(
        _WP_P12_ECONOMIC_MD_CONSTANTS,
        economic,
        economic.read_text(encoding="utf-8"),
    )
    _exec_isolated_module(
        _WP_P12_FEATURE_CONSTANTS,
        feature,
        feature.read_text(encoding="utf-8"),
    )


_load_data_completion_constants_v1()


def _completion_closed(
    evidence: DataCompletionEvidenceV1,
    *,
    status: DataCompletionStatusV1,
    hypothetical_slot_release: bool,
) -> DataCompletionSlotReleaseResultV1:
    return DataCompletionSlotReleaseResultV1(
        instrument_id=evidence.instrument_id,
        status=status,
        residency_epoch_id=evidence.bound_residency_epoch_id,
        hypothetical_slot_release=hypothetical_slot_release,
        slot_already_released=evidence.slot_already_released is True,
        slot_release_performed=False,
        admission_performed=False,
        residency_write_attempted=False,
        scheduler_tick_performed=False,
        replay_witness_created=False,
        timeout_completion=False,
        positive_negative_evaluation=False,
        ranking_authority=False,
        selection_authority=False,
        trading_authority=False,
        network_requested=False,
        http_get_performed=False,
        http_post_performed=False,
        public_websocket_connected=False,
        private_websocket_connected=False,
    )


def _text(value: object) -> str:
    return str(value or "").strip()


def _mark_count(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _staging_refs(evidence: DataCompletionEvidenceV1) -> tuple[str, ...]:
    return (
        evidence.economic_input_snapshot_id,
        evidence.feature_production_snapshot_id,
        evidence.ranking_snapshot_id,
        *evidence.source_refs,
    )


def assess_data_completion_slot_release_v1(
    evidence: DataCompletionEvidenceV1,
) -> DataCompletionSlotReleaseResultV1:
    """Record whether one instrument's existing data chain is complete.

    This does not create an evaluation witness, release a slot, or admit
    the next pending candidate.
    """

    economic = sys.modules[_WP_P12_ECONOMIC_MD_CONSTANTS]
    feature = sys.modules[_WP_P12_FEATURE_CONSTANTS]
    ranking = sys.modules[_WP_P4_RANKING_CONSTANTS]
    required_marks = int(feature.MARK_COUNT)
    marks_agree = required_marks == int(economic.MINIMUM_FINALIZED_PT1M_MARKS)
    instrument = _text(evidence.instrument_id)
    epoch = _text(evidence.residency_epoch_id)
    bound_epoch = _text(evidence.bound_residency_epoch_id)
    economic_digest = _text(evidence.economic_raw_input_digest)
    feature_digest = _text(evidence.feature_production_digest)
    feature_id = _text(evidence.feature_production_snapshot_id)
    economic_marks = _mark_count(evidence.economic_mark_count)
    feature_marks = _mark_count(evidence.feature_mark_count)
    staging_markers = (
        str(ranking.STAGING_DIRNAME_PREFIX),
        str(economic.STAGING_DIRNAME_PREFIX),
    )
    staged = any(
        marker in ref for ref in _staging_refs(evidence) for marker in staging_markers if marker
    )
    same_instrument = (
        instrument != ""
        and _text(evidence.economic_instrument_id) == instrument
        and _text(evidence.feature_instrument_id) == instrument
        and _text(evidence.ranking_instrument_id) == instrument
    )
    provenance_joined = (
        economic_digest != ""
        and _text(evidence.feature_economic_md_raw_input_digest) == economic_digest
        and feature_id != ""
        and _text(evidence.ranking_feature_production_snapshot_id) == feature_id
        and feature_digest != ""
        and _text(evidence.ranking_feature_production_digest) == feature_digest
        and _text(evidence.economic_input_snapshot_id) not in {"", feature_id}
        and _text(evidence.ranking_snapshot_id) not in {"", feature_id}
    )
    complete = (
        marks_agree
        and not staged
        and same_instrument
        and provenance_joined
        and evidence.economic_md_ok is True
        and evidence.economic_raw_input_eligible is True
        and economic_marks == required_marks
        and evidence.feature_production_ready is True
        and feature_marks == required_marks
        and _text(evidence.ranking_snapshot_state) == str(ranking.SNAPSHOT_STATE_VALID)
        and epoch != ""
        and epoch == bound_epoch
    )
    if not complete:
        return _completion_closed(
            evidence,
            status=DataCompletionStatusV1.DATA_COMPLETION_UNPROVEN,
            hypothetical_slot_release=False,
        )
    return _completion_closed(
        evidence,
        status=DataCompletionStatusV1.DATA_COMPLETION_PROVEN,
        hypothetical_slot_release=evidence.slot_already_released is not True,
    )
