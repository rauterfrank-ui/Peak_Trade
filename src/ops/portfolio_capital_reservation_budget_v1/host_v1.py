"""N1 host lifecycle for the existing durable owner; no execution authority.

Private REST observations are account-bound before opening the store. Recovery
consumes the existing canonical capital producer only at the outer ENTRY seam.
Order/fill history is bounded observation, not reservation-to-fill resolution.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from threading import Lock
import time
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from src.ops.execution_reconciliation_get_provenance_v1 import (
        AuthenticatedExecutionReconciliationProofV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.slot_loss_budget_v1 import (
        SlotCapitalAllocationV1,
    )

from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    NUMERIC_EQUITY_TTL_SECONDS,
)
from src.ops.okx_eea_private_account_state_runtime_v1.rest_baseline_v1 import (
    collect_rest_baseline_v1,
    PrivateRestBaselineError,
)
from src.ops.okx_eea_private_account_state_runtime_v1.reconciliation_v1 import (
    reconcile_rest_baseline_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.local_commitment_readback_v1 import (
    LocalCapitalCommitmentReadbackV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.recovery_v1 import (
    reconcile_durable_budget_startup_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)


@dataclass(frozen=True)
class HostAccountObservationV1:
    account: str
    observed: PortfolioTruthSnapshotV1
    pending_orders: bool
    occupancy_payloads: dict
    pending_source: object | None = field(default=None, repr=False, compare=False)
    account_inventory_source: object | None = field(default=None, repr=False, compare=False)


@dataclass(frozen=True)
class FuturesFinancialCustodyV1:
    """Same-account inventory and local commitments for a financial reader."""

    local_commitments: LocalCapitalCommitmentReadbackV1 = field(repr=False)
    _host: "PortfolioBudgetHostV1" = field(repr=False, compare=False)
    _observation: HostAccountObservationV1 = field(repr=False)
    _bindings: tuple = field(repr=False)
    _read_count: int

    def read_v1(self):
        return self._host.inspect_futures_financial_custody_v1(self)

    def fetch_xperp_position_terms_v1(self, native_ids):
        self.read_v1()
        terms = self._observation.account_inventory_source.fetch_xperp_position_terms_v1(native_ids)
        self.read_v1()
        return terms


@dataclass(frozen=True)
class StandingStartupAccountObservationPortV1:
    """Deliver the original startup observation before account admission."""

    fetch: Callable
    reconcile: Callable[[HostAccountObservationV1], None]

    def __call__(self, path, query):
        return self.fetch(path, query)


def collect_host_account_observation_v1(
    *,
    private_rest_fetch,
    instrument_ids_by_native_id,
    session_id,
    clock=time.time,
    expected_account=None,
) -> HostAccountObservationV1:
    """Reuse host baseline checks before any budget-store or binding mutation.

    The scoped standing startup can consume the completed observation through
    its existing budget host before the startup gate uses it.
    """
    startup_port = None
    if type(private_rest_fetch) is StandingStartupAccountObservationPortV1:
        startup_port = private_rest_fetch
        private_rest_fetch = startup_port.fetch
    native = dict(instrument_ids_by_native_id)
    from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
        K1AccountObservationSourceV1,
    )

    inventory_source = None
    if (
        type(private_rest_fetch) is K1AccountObservationSourceV1
        and private_rest_fetch.account_inventory_guard
    ):
        inventory_source = private_rest_fetch
    # The legacy baseline observes SWAP. At standing startup, only the
    # guarded K1 source can provide account custody for a FUTURES selection.
    observed_product = (
        inventory_source.inventory_inst_type if inventory_source is not None else "SWAP"
    )
    if startup_port is not None or inventory_source is not None:
        from src.ops.execution_reconciliation_get_provenance_v1 import (
            resolve_reconciliation_query_options_v1,
        )

        try:
            bound_products = {
                resolve_reconciliation_query_options_v1(
                    instrument_id=instrument_id, native_id=native_id
                ).inst_type
                for native_id, instrument_id in native.items()
            }
        except ValueError as exc:
            raise ValueError("HOST_BUDGET_BOUND_PRODUCT_SCOPE_UNPROVEN") from exc
        if bound_products - {observed_product}:
            raise ValueError("HOST_BUDGET_BOUND_PRODUCT_SCOPE_UNPROVEN")
    started = clock()
    uids = set()
    pending = []
    occupancy = {}

    def fetch(path, params):
        # The budget needs account scope. K1 custody expands the position
        # and pending reads and selects the product for history and fills.
        query = {k: v for k, v in params.items() if k != "instId"}
        payload = private_rest_fetch(path, query)
        key = {
            "/api/v5/account/config": "CONFIG",
            "/api/v5/account/positions": "POSITIONS",
            "/api/v5/trade/orders-pending": "PENDING",
        }.get(path)
        if key is not None:
            occupancy[key] = payload
        if path in {"/api/v5/account/config", "/api/v5/account/balance"}:
            for row in payload.get("data", []):
                uid = row.get("uid")
                if uid is not None and str(uid).strip():
                    uids.add(str(uid).strip())
        if path == "/api/v5/trade/orders-pending":
            pending.extend(payload.get("data", []))
        return payload

    try:
        baseline = collect_rest_baseline_v1(
            fetch,
            captured_at=datetime.fromtimestamp(started, timezone.utc).isoformat(),
            recovery=True,
        )
    except PrivateRestBaselineError as exc:
        raise ValueError("HOST_BUDGET_PRIVATE_BASELINE_INVALID") from exc
    if len(uids) != 1:
        raise ValueError("HOST_BUDGET_PRIVATE_ACCOUNT_UNPROVEN")
    account = next(iter(uids))
    if expected_account is not None and account != expected_account:
        raise ValueError("HOST_BUDGET_PRIVATE_ACCOUNT_CHANGED")
    now = clock()
    position_max_age = POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS / 1000
    if not 0 <= now - started <= position_max_age:
        raise ValueError("HOST_BUDGET_PRIVATE_SNAPSHOT_STALE")
    if not reconcile_rest_baseline_v1(
        reconciliation_id=session_id,
        rest_baseline=baseline,
    ).trusted:
        raise ValueError("HOST_BUDGET_PRIVATE_RECONCILIATION_REQUIRED")
    source_id = f"host-private-rest-{observed_product.lower()}"
    positions = []
    seen = set()
    for p in baseline.positions:
        if p.inst_id not in native or p.inst_id in seen:
            raise ValueError("HOST_BUDGET_POSITION_SCOPE_UNPROVEN")
        seen.add(p.inst_id)
        quantity = Decimal(p.pos)
        if p.pos_side not in {"net", "long", "short"} or (p.pos_side != "net" and quantity < 0):
            raise ValueError("HOST_BUDGET_POSITION_SIDE_UNPROVEN")
        if p.pos_side == "short":
            quantity = -quantity
        positions.append(
            PositionTruthV1.from_signed(
                instrument_id=native[p.inst_id],
                signed_quantity=quantity,
                source_id=source_id,
                event_time_unix=started,
                wall_time_unix=now,
            )
        )
    observation = HostAccountObservationV1(
        account=account,
        pending_orders=bool(pending),
        occupancy_payloads=occupancy,
        account_inventory_source=inventory_source,
        observed=PortfolioTruthSnapshotV1(
            positions=tuple(positions),
            source_id=source_id,
            event_time_unix=started,
            wall_time_unix=now,
            max_age_seconds=position_max_age,
        ),
    )
    # Only the original concrete observer has the supported algo/credential/
    # session contract. A plain callback's empty rows are not that evidence.
    from src.ops.okx_eea_private_account_state_runtime_v1.startup_source_v1 import (
        is_original_account_observation_source_v1,
    )

    if inventory_source is None and is_original_account_observation_source_v1(private_rest_fetch):
        private_rest_fetch.bind_completed_host_observation_v1(observation)
        observation = replace(observation, pending_source=private_rest_fetch)
    if startup_port is not None:
        startup_port.reconcile(observation)
    return observation


@dataclass(frozen=True)
class AuthenticatedEntryEpisodeRequestV1:
    proof_root: Path
    proof: "AuthenticatedExecutionReconciliationProofV1"


@dataclass(frozen=True)
class HostBudgetRecoveryContextV1:
    host: "PortfolioBudgetHostV1"
    account: str
    observed: PortfolioTruthSnapshotV1
    pending_orders: bool
    occupancy_payloads: dict
    execution_reconciliation: dict = field(default_factory=dict)
    pending_source: object | None = field(default=None, repr=False, compare=False)
    account_inventory_source: object | None = field(default=None, repr=False, compare=False)
    authenticated_reconciliation: object | None = field(default=None, repr=False, compare=False)

    def recover_v1(self, owner, output):
        return self._recover_with_bindings_v1(owner, output, self.host.bindings)

    def _recover_with_bindings_v1(self, owner, output, bindings):
        from .test_phase_limits_v1 import BoundedSlotReconciliationScopeV1

        if owner is not self.host.owner:
            raise ValueError("HOST_BUDGET_OWNER_MISMATCH")
        owner.restart_fail_closed_v1()
        if any(
            not result.get("matched")
            or result.get("decision", {}).get("reconciliation_complete") is not True
            for result in self.execution_reconciliation.values()
        ):
            raise ValueError("HOST_BUDGET_EXECUTION_RECONCILIATION_UNRESOLVED")
        if self.pending_orders:
            raise ValueError("HOST_BUDGET_PENDING_ORDERS_UNRESOLVED")
        if output.bound_account_identity != self.account:
            raise ValueError("HOST_BUDGET_ACCOUNT_MISMATCH")
        authenticated_update = None
        if (
            self.host.execution_environment == "TESTNET"
            and self.authenticated_reconciliation is not None
        ):
            proofs = tuple(self.authenticated_reconciliation.evidence.values())
            if len(proofs) != 1:
                raise ValueError("TESTNET_RECOVERY_SINGLE_AUTHENTICATED_POSITION_REQUIRED")
            proof = proofs[0]
            row = self.execution_reconciliation[proof.reservation_id]
            authenticated_update = {
                "authenticated_net_reversal"
                if "net_reversal_booking_digest" in row
                else "authenticated_testnet_entry": (self, proof)
            }
        result = reconcile_durable_budget_startup_v1(
            owner,
            output=output,
            observed=self.observed,
            lane_bindings=bindings,
            reconciliation_state_root=self.host.root / "reconciliation",
            session_id=self.host.session_id,
            repository_sha=self.host.repository_sha,
            now_unix=self.host.clock(),
            capital_max_age_seconds=NUMERIC_EQUITY_TTL_SECONDS,
            authenticated_position_update=authenticated_update,
            **(
                {
                    "bounded_reconciliation_scope": BoundedSlotReconciliationScopeV1(
                        owner.entry_budget_policy_v1(),
                        tuple(sorted(bindings.items())),
                        self.host.execution_environment,
                    )
                }
                if owner.entry_budget_policy_v1() is not None
                else {}
            ),
        )
        if owner.budget_state_v1().recovery_required:
            raise ValueError("HOST_BUDGET_RECOVERY_BLOCKED:" + ",".join(result.reason_codes))

    def position_side_v1(self, bound):
        if self.host.closed or bound not in self.host.bindings.values():
            raise ValueError("HOST_BUDGET_POSITION_BINDING_MISMATCH")
        position = next(
            (p for p in self.observed.positions if p.instrument_id == bound.instrument_id), None
        )
        return position.side if position is not None else "FLAT"

    def inspect_current_authenticated_entry_v1(self, *, lane_id, proof):
        """Require the exact current observation and its durable entry revision."""
        from src.ops.execution_reconciliation_get_provenance_v1 import (
            AuthenticatedExecutionReconciliationProofV1,
        )
        from .execution_v1 import read_persisted_execution_reconciliation_v1

        host = self.host
        if (
            host.closed
            or host.execution_environment not in {"LIVE", "TESTNET"}
            or self.pending_orders
            or host.owner is None
            or host.owner.execution_environment_v1() != host.execution_environment
            or lane_id not in (host.bindings or {})
            or type(proof) is not AuthenticatedExecutionReconciliationProofV1
            or proof.session_id != host.session_id
            or proof.account != self.account
            or not proof.gets
            or not 0
            <= host.clock() - proof.gets[0].acquired_at.timestamp()
            <= POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS / 1000
        ):
            raise ValueError("HOST_AUTHENTICATED_ENTRY_OBSERVATION_UNPROVEN")
        result = self.execution_reconciliation.get(proof.reservation_id)
        if result and "net_reversal_booking_digest" in result:
            source = self.authenticated_reconciliation
            booking, _ = host.owner.read_current_net_reversal_obligation_v1(
                proof.reservation_id, revision_ref=proof.revision_ref
            )
            link = host.owner.execution_links_v1(active_only=True).get(proof.reservation_id)
            if (
                source is None
                or source.evidence.get(proof.reservation_id) != proof
                or source.transport is not host.reconciliation_transport
                or link is None
                or booking["slot_id"] != lane_id
                or booking["booking_digest"] != result["net_reversal_booking_digest"]
                or booking["envelope_digest"] != proof.identity_digest
                or result["portfolio_digest"] != self.observed.digest()
                or result["snapshot_digest"] != proof.snapshot_digest
                or result["reservation_released"] is not False
            ):
                raise ValueError("NET_REVERSAL_CURRENT_POSITION_RECEIPT_UNPROVEN")
            return {**link, "reconciliation": result}
        _, _, link = read_persisted_execution_reconciliation_v1(
            host.owner, proof.reservation_id, revision_ref=proof.revision_ref
        )
        result = link["reconciliation"]
        if (
            result != self.execution_reconciliation.get(proof.reservation_id)
            or result["portfolio_digest"] != self.observed.digest()
            or result["identity_digest"] != proof.identity_digest
            or result["snapshot_digest"] != proof.snapshot_digest
        ):
            raise ValueError("HOST_AUTHENTICATED_ENTRY_OBSERVATION_UNPROVEN")
        return link

    def bind_current_authenticated_entry_episode_v1(
        self, *, lane_id, proof_root, proof, config_digest, recover_only=False
    ):
        """Publish the observed entry through the original position-episode writer."""
        from src.ops.exit_policy_producer_binding_v1.authenticated_execution_entry_source_v1 import (
            open_position_episode_from_authenticated_execution_v1,
        )
        from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
            PositionEpisodeScopeV1,
        )

        link = self.inspect_current_authenticated_entry_v1(lane_id=lane_id, proof=proof)
        host = self.host
        if "net_reversal_booking_digest" in link["reconciliation"]:
            from src.ops.full_core_live_path_composition_root_v1.current_productive_net_reversal_reconciliation_v1 import (
                open_booked_net_position_episode_v1,
            )

            booking, _ = host.owner.read_current_net_reversal_obligation_v1(
                proof.reservation_id, revision_ref=proof.revision_ref
            )
            return open_booked_net_position_episode_v1(
                host=host,
                bound=host.bindings[lane_id],
                booking=booking,
                config_digest=config_digest,
                recover_only=recover_only,
            )
        state_root = host.root / "position-episodes" / proof.identity_digest
        args = dict(
            bound=host.bindings[lane_id],
            lane_id=lane_id,
            account_scope=PositionEpisodeScopeV1(self.account, host.execution_environment),
            proof_root=proof_root,
            budget_owner_root=host.root / "owner",
            source_session_id=proof.session_id,
            reservation_id=proof.reservation_id,
            revision_ref=proof.revision_ref,
            state_root=state_root,
            repository_sha=host.repository_sha,
            config_digest=config_digest,
            writer_session_id=host.session_id,
        )
        if recover_only:
            return open_position_episode_from_authenticated_execution_v1(**args, mode="recover")
        try:
            return open_position_episode_from_authenticated_execution_v1(**args, mode="create")
        except FileExistsError:
            return open_position_episode_from_authenticated_execution_v1(**args, mode="recover")

    def publish_authenticated_testnet_entry_c1_v1(
        self, *, lane_id, proof, episode, cursor_root, g17_producer
    ):
        """Join the confirmed original fill to the original Mark-to-C1 publisher."""
        from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
            load_current_productive_sidestate_confirmation_cursor_v1,
            parse_current_productive_sidestate_confirmation_cursor_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.current_core_entry_assessment_frame_v1 import (
            read_current_core_entry_assessment_frame_v1,
        )
        from src.ops.offline_first_entry_position_v2 import publish_confirmed_first_entry_c1_v2
        from src.ops.exit_policy_producer_binding_v1.current_cursor_recovery_v1 import (
            require_current_cursor_continuity_v1,
        )
        from src.ops.execution_reconciliation_proof_store_v1 import (
            read_authenticated_execution_reconciliation_source_v1,
        )

        host = self.host
        link = self.inspect_current_authenticated_entry_v1(lane_id=lane_id, proof=proof)
        source = link.get("plan_origin", {}).get("core_cursor_source", {})
        if (
            host.execution_environment != "TESTNET"
            or episode.identity.account_scope.execution_environment != "TESTNET"
            or source.get("cursor_root") != str(Path(cursor_root).resolve())
            or source.get("decision_id") != link["identity"]["canonical_decision_id"]
            or proof.identity_digest != episode.identity.episode_id
            or "net_reversal_booking_digest" in link["reconciliation"]
        ):
            raise ValueError("TESTNET_ENTRY_C1_ORIGINAL_SCOPE_REQUIRED")
        raw = load_current_productive_sidestate_confirmation_cursor_v1(Path(cursor_root))
        if raw is None:
            raise ValueError("TESTNET_ENTRY_C1_ORIGINAL_CURSOR_REQUIRED")
        if raw["entry_assessment_frame"] is None:
            require_current_cursor_continuity_v1(
                episode=episode, incoming=raw, store_root=Path(cursor_root)
            )
            return
        frame = read_current_core_entry_assessment_frame_v1(
            parse_current_productive_sidestate_confirmation_cursor_v1(raw)
        )
        if frame["parent"]["decision_id"] != source["decision_id"]:
            # A later occupied Core cycle has its own assessment frame. Its
            # original Exit-owned publication must match the current cursor;
            # never replay the opening handoff over that continued state.
            if episode.binding.current_cursor_publication is not None:
                require_current_cursor_continuity_v1(
                    episode=episode, incoming=raw, store_root=Path(cursor_root)
                )
                return
            raise ValueError("TESTNET_ENTRY_C1_ORIGINAL_DECISION_REQUIRED")

        def retain():
            original = read_authenticated_execution_reconciliation_source_v1(
                root=self.authenticated_reconciliation.proof_root,
                budget_owner_root=host.root / "owner",
                account=self.account,
                session_id=proof.session_id,
                reservation_id=proof.reservation_id,
                revision_ref=proof.revision_ref,
            )
            if original.proof != proof:
                raise ValueError("TESTNET_ENTRY_C1_ORIGINAL_FILL_CHANGED")
            return proof.snapshot_digest

        return publish_confirmed_first_entry_c1_v2(
            episode=episode,
            cursor_root=Path(cursor_root),
            g17_producer=g17_producer,
            writer_session_id=host.session_id,
            retain_opening=retain,
        )


class PortfolioBudgetHostV1:
    """One session, one writer, stable account scope outside lane/run roots."""

    def __init__(
        self,
        *,
        root: Path,
        private_rest_fetch,
        repository_sha: str,
        session_id: str,
        expected_account_identity: str,
        durable_mode: str = "recover",
        clock=time.time,
        retry_sleep=time.sleep,
        retry_interval_seconds=1,
        reconciliation_transport=None,
        execution_environment="LIVE",
        entry_budget_policy=None,
        execution_incident_state_path: Path | None = None,
        slot_capital_allocation: "SlotCapitalAllocationV1 | None" = None,
        live_slot_capital_allocation: "SlotCapitalAllocationV1 | None" = None,
        testnet_owner_contract: str | None = None,
    ):
        if (
            not isinstance(expected_account_identity, str)
            or not expected_account_identity
            or expected_account_identity != expected_account_identity.strip()
        ):
            raise ValueError("HOST_BUDGET_EXPECTED_ACCOUNT_REQUIRED")
        if durable_mode not in {"create", "recover"}:
            raise ValueError("HOST_BUDGET_DURABLE_MODE_INVALID")
        if not Path(root).is_absolute():
            raise ValueError("HOST_BUDGET_ABSOLUTE_ROOT_REQUIRED")
        self.root = Path(root).resolve()
        if durable_mode == "recover" and not self.root.exists():
            raise ValueError("DURABLE_BUDGET_STATE_MISSING")
        if durable_mode == "create" and self.root.exists():
            raise ValueError("HOST_BUDGET_BOOTSTRAP_SCOPE_ALREADY_EXISTS")
        self.durable_mode = durable_mode
        self.expected_account_identity = expected_account_identity
        self.fetch = private_rest_fetch
        self.repository_sha = repository_sha
        self.session_id = session_id
        self.clock = clock
        self.owner = None
        self.bindings = None
        self._futures_financial_lock = Lock()
        self._futures_financial_custody = None
        self.account = expected_account_identity
        self.closed = False
        self.retry_sleep = retry_sleep
        self.retry_interval_seconds = retry_interval_seconds
        self.transport_retry_count = 0
        self.reconciliation_transport = reconciliation_transport
        self.execution_environment = execution_environment
        self._testnet_owner_contract = testnet_owner_contract
        if testnet_owner_contract is not None:
            from src.ops.btc_demo_budget_owner_v3 import CONTRACT
            from .test_phase_limits_v1 import require_btc_testnet_slot_scope_v1

            if execution_environment != "TESTNET" or testnet_owner_contract != CONTRACT:
                raise ValueError("HOST_TESTNET_OWNER_CONTRACT_MISMATCH")
            require_btc_testnet_slot_scope_v1(entry_budget_policy)
        if execution_environment == "TESTNET" and entry_budget_policy is not None:
            from .test_phase_limits_v1 import require_btc_testnet_slot_scope_v1

            require_btc_testnet_slot_scope_v1(entry_budget_policy)
        self.execution_incident_state_path = execution_incident_state_path
        if execution_incident_state_path is not None and execution_environment not in {
            "LIVE",
            "TESTNET",
        }:
            raise ValueError("HOST_EXECUTION_INCIDENT_LIVE_SCOPE_REQUIRED")
        if entry_budget_policy is not None:
            from .test_phase_limits_v1 import (
                BoundedSlotEntryBudgetV1,
            )

            if type(entry_budget_policy) is not BoundedSlotEntryBudgetV1:
                raise ValueError("ENTRY_BUDGET_POLICY_TYPE_INVALID")
            entry_budget_policy.validate_v1()
        if (
            entry_budget_policy is not None
            and entry_budget_policy.per_slot_reserved_notional_limit is not None
            and execution_environment not in {"INTERNAL_SIMULATED_EXECUTION", "TESTNET"}
        ):
            raise ValueError("SLOT_TEST_BUDGET_REQUIRES_SIMULATED_HOST")
        if slot_capital_allocation is not None and (
            durable_mode != "create"
            or execution_environment not in {"INTERNAL_SIMULATED_EXECUTION", "TESTNET"}
            or entry_budget_policy is None
        ):
            raise ValueError("HOST_SLOT_CAPITAL_SIMULATED_BOOTSTRAP_REQUIRED")
        if live_slot_capital_allocation is not None and (
            durable_mode != "create"
            or execution_environment != "LIVE"
            or entry_budget_policy is not None
            or slot_capital_allocation is not None
        ):
            raise ValueError("HOST_SLOT_CAPITAL_LIVE_BOOTSTRAP_REQUIRED")
        self.entry_budget_policy = entry_budget_policy
        self._slot_capital_allocation = slot_capital_allocation
        self._live_slot_capital_allocation = live_slot_capital_allocation

    def observe_v1(self, bindings, *, required_execution_attempts=None):
        return self._observe_with_retry_v1(
            bindings, required_execution_attempts=required_execution_attempts
        )

    def _open_budget_owner_v1(self, *, account, bindings):
        if self.execution_environment == "TESTNET" and self.entry_budget_policy is not None:
            from .test_phase_limits_v1 import require_btc_testnet_slot_scope_v1

            require_btc_testnet_slot_scope_v1(self.entry_budget_policy, bindings)
        owner_args = dict(
            durable_root=self.root / "owner",
            durable_account_identity=account,
            durable_mode=self.durable_mode,
            durable_lane_bindings=bindings,
            execution_environment="TESTNET" if self.execution_environment == "TESTNET" else "LIVE",
            entry_budget_policy=self.entry_budget_policy,
            slot_capital_allocation=self._slot_capital_allocation
            if self.durable_mode == "create"
            else None,
            live_slot_capital_allocation=(
                self._live_slot_capital_allocation if self.durable_mode == "create" else None
            ),
        )
        if self._testnet_owner_contract is not None:
            from src.ops.btc_demo_budget_owner_v3 import BtcDemoBudgetOwnerV3

            # Explicit selection, no journal migration or fallback to a generic
            # owner. V3 also validates the existing isolated Demo root itself.
            del owner_args["execution_environment"]
            del owner_args["live_slot_capital_allocation"]
            owner = BtcDemoBudgetOwnerV3(**owner_args)
        else:
            owner = PortfolioCapitalReservationBudgetOwnerV1(**owner_args)
        restored_policy = owner.entry_budget_policy_v1()
        if (
            restored_policy is not None
            and restored_policy.per_slot_reserved_notional_limit is not None
            and self.execution_environment not in {"INTERNAL_SIMULATED_EXECUTION", "TESTNET"}
        ):
            owner.close()
            raise ValueError("SLOT_TEST_BUDGET_REQUIRES_SIMULATED_HOST")
        if owner.has_live_slot_capital_allocation_v1() and self.execution_environment != "LIVE":
            owner.close()
            raise ValueError("LIVE_SLOT_CAPITAL_HOST_SCOPE_MISMATCH")
        if self.execution_environment == "TESTNET" and restored_policy is not None:
            from .test_phase_limits_v1 import require_btc_testnet_slot_scope_v1

            try:
                require_btc_testnet_slot_scope_v1(restored_policy, bindings)
            except Exception:
                owner.close()
                raise
        return owner

    def recover_owner_for_l10_close_booking_v1(self, bindings):
        return self.recover_owner_for_occupied_execution_v1(bindings, operation="L10_CLOSE_BOOKING")

    def recover_owner_for_occupied_execution_v1(self, bindings, *, operation):
        """Open the original writer without reconciling or admitting new capital."""
        if (
            self.closed
            or self.execution_environment not in {"LIVE", "TESTNET"}
            or self.durable_mode != "recover"
        ):
            raise ValueError(f"{operation}_ORIGINAL_HOST_REQUIRED")
        if self.owner is None:
            self.owner = self._open_budget_owner_v1(
                account=self.expected_account_identity, bindings=bindings
            )
            self.bindings = dict(bindings)
        elif self.bindings != bindings:
            raise ValueError(f"{operation}_LANE_MISMATCH")
        return self.owner

    def capture_futures_financial_custody_v1(self, source):
        """Take a read-only sample with the original durable owner already open."""
        with self._futures_financial_lock:
            self._futures_financial_custody = None
            proof = self._capture_futures_financial_custody_v1(source)
            self._futures_financial_custody = proof
            return proof

    def _capture_futures_financial_custody_v1(self, source):
        from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
            FUTURES_INVENTORY_REQUEST_COUNT,
            K1AccountObservationSourceV1,
        )

        if self.closed or self.owner is None or not self.bindings:
            raise ValueError("FUTURES_FINANCIAL_ORIGINAL_OWNER_REQUIRED")
        if (
            type(source) is not K1AccountObservationSourceV1
            or source.closed
            or not source.account_inventory_guard
            or source.inventory_inst_type != "FUTURES"
            or source.expected_account_identity != self.account
        ):
            raise ValueError("FUTURES_FINANCIAL_ORIGINAL_K1_SCOPE_REQUIRED")
        local = self.owner.local_commitment_readback_v1()
        if not local.durable_state_enabled or local.account_identity != self.account:
            raise ValueError("FUTURES_FINANCIAL_DURABLE_ACCOUNT_REQUIRED")
        bindings = tuple(sorted(self.bindings.items()))
        transport = source.transport
        initial_reads = transport.read_count
        observation = collect_host_account_observation_v1(
            private_rest_fetch=source,
            instrument_ids_by_native_id={
                bound.venue_native_id: bound.instrument_id for _, bound in bindings
            },
            session_id=self.session_id,
            clock=self.clock,
            expected_account=self.account,
        )
        if transport.read_count - initial_reads != FUTURES_INVENTORY_REQUEST_COUNT:
            raise ValueError("FUTURES_FINANCIAL_INVENTORY_GET_COUNT_MISMATCH")
        proof = FuturesFinancialCustodyV1(local, self, observation, bindings, transport.read_count)
        self._inspect_futures_financial_custody_v1(proof)
        return proof

    def inspect_futures_financial_custody_v1(self, proof):
        """Read current sources and recheck the original local generation."""
        with self._futures_financial_lock:
            if proof is None or proof is not self._futures_financial_custody:
                raise ValueError("FUTURES_FINANCIAL_ORIGINAL_HOST_PROOF_REQUIRED")
            return self._inspect_futures_financial_custody_v1(proof)

    def _inspect_futures_financial_custody_v1(self, proof):
        if (
            self.closed
            or self.owner is not proof.local_commitments.source_owner
            or self.account != proof._observation.account
            or tuple(sorted(self.bindings.items())) != proof._bindings
        ):
            raise ValueError("FUTURES_FINANCIAL_HOST_SCOPE_CHANGED")
        inputs = proof._observation.account_inventory_source.inspect_futures_financial_gets_v1(
            proof._observation, read_count=proof._read_count
        )
        self.owner.require_local_commitment_readback_v1(
            proof.local_commitments, account_identity=self.account
        )
        return inputs

    def reconcile_standing_startup_observation_v1(
        self, bindings, observation, *, net_reversal_proof_root=None
    ):
        """Use the completed startup sample in the same owner used later by S5."""
        if (
            self.closed
            or (
                self.owner is not None
                and not (net_reversal_proof_root is not None and self.bindings == bindings)
            )
            or self.durable_mode != "recover"
            or self.execution_incident_state_path is None
            or type(observation) is not HostAccountObservationV1
            or observation.account != self.expected_account_identity
        ):
            raise ValueError("HOST_EXECUTION_STANDING_STARTUP_OBSERVATION_UNPROVEN")
        capture = None
        if net_reversal_proof_root is not None:
            from src.ops.execution_reconciliation_get_provenance_v1 import (
                AuthenticatedReconciliationGetV1,
            )

            capture = AuthenticatedReconciliationGetV1(
                self.reconciliation_transport,
                account=self.expected_account_identity,
                clock=self.clock,
                proof_root=net_reversal_proof_root,
            )
        self._bind_observation_v1(
            bindings,
            observation,
            capture=capture,
            deliver_authenticated_incidents=capture is not None,
        )

    def observe_execution_reconciliation_evidence_v1(self, bindings):
        """Expose original snapshots only for the explicit isolated SHADOW probe."""
        from src.ops.execution_incident_host_v1 import InjectedReconciliationGetV1

        if self.execution_environment != "SHADOW":
            raise ValueError("HOST_EXECUTION_EVIDENCE_SHADOW_REQUIRED")
        capture = InjectedReconciliationGetV1(self.reconciliation_transport)
        context = self._observe_with_retry_v1(bindings, capture=capture)
        return context, capture.evidence

    def observe_authenticated_execution_reconciliation_v1(
        self, bindings, *, proof_root=None, deliver_authenticated_incidents=False
    ):
        """Observe the original environment-bound chain with per-request GET proof."""
        from src.ops.execution_reconciliation_get_provenance_v1 import (
            AuthenticatedReconciliationGetV1,
        )

        if self.execution_environment not in {"LIVE", "TESTNET"}:
            raise ValueError("HOST_EXECUTION_EVIDENCE_LIVE_IDENTITY_REQUIRED")
        if self.execution_environment == "TESTNET":
            from .test_phase_limits_v1 import require_btc_testnet_slot_scope_v1

            require_btc_testnet_slot_scope_v1(self.entry_budget_policy, bindings)
        if deliver_authenticated_incidents and (
            proof_root is None or self.execution_incident_state_path is None
        ):
            raise ValueError("HOST_EXECUTION_SAFETY_AND_PROOF_SCOPE_REQUIRED")
        capture = AuthenticatedReconciliationGetV1(
            self.reconciliation_transport,
            account=self.expected_account_identity,
            clock=self.clock,
            proof_root=proof_root,
        )
        if self.reconciliation_transport.execution_environment != self.execution_environment:
            raise ValueError("HOST_AUTHENTICATED_GET_ENVIRONMENT_MISMATCH")
        context = self._observe_with_retry_v1(
            bindings,
            capture=capture,
            deliver_authenticated_incidents=deliver_authenticated_incidents,
        )
        capture.discard_response_bodies_v1()
        return replace(context, authenticated_reconciliation=capture), capture.evidence

    def _observe_with_retry_v1(
        self,
        bindings,
        *,
        capture=None,
        required_execution_attempts=None,
        deliver_authenticated_incidents=False,
    ):
        from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.recovery_v1 import (
            bounded_retry_policy_v1,
        )

        attempt = 0
        while True:
            if capture is not None:
                capture.reset_v1()
            try:
                return self._observe_once_v1(
                    bindings,
                    capture=capture,
                    required_execution_attempts=required_execution_attempts,
                    deliver_authenticated_incidents=deliver_authenticated_incidents,
                )
            except (TimeoutError, ConnectionError):
                if not bounded_retry_policy_v1(
                    attempt=attempt,
                    automatic_recovery_allowed=True,
                )["retry_allowed"]:
                    raise
                attempt += 1
                self.transport_retry_count += 1
                self.retry_sleep(self.retry_interval_seconds)

    def occupied_mark_pretrade_scope_v1(self, *, reservation_id, lane_id):
        """Identify advance GETs by the original occupied reservation and host session."""
        from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
            canonical_digest_v1,
        )

        return "n1-occupied:" + canonical_digest_v1(
            {"session_id": self.session_id, "reservation_id": reservation_id, "lane_id": lane_id}
        )

    def prepare_occupied_mark_account_read_v1(self, bindings, *, proof_root):
        """Capture the original execution revision before the worker starts GETs."""
        from src.ops.execution_reconciliation_get_provenance_v1 import (
            AuthenticatedReconciliationGetV1,
        )

        if (
            self.closed
            or self.owner is None
            or self.execution_environment not in {"LIVE", "TESTNET"}
            or self.bindings != bindings
            or len(bindings) != 1
            or proof_root is None
            or self.execution_incident_state_path is None
        ):
            raise ValueError("HOST_OCCUPIED_MARK_ACCOUNT_SCOPE_UNPROVEN")
        owner = self.owner
        submitted = self._submitted_executions_v1(include_reconciliation=False)
        if len(submitted) != 1:
            raise ValueError("HOST_OCCUPIED_MARK_ORIGINAL_EXECUTION_REQUIRED")
        booked = {rid: owner.read_current_net_reversal_obligation_v1(rid) for rid in submitted}

        def read():
            capture = AuthenticatedReconciliationGetV1(
                self.reconciliation_transport,
                account=self.expected_account_identity,
                clock=self.clock,
                proof_root=proof_root,
            )
            observation = self._collect_account_observation_v1(bindings)
            context = self._account_recovery_context_v1(observation)
            requests = self._execution_reconciliation_requests_v1(context, submitted, capture)
            reads = tuple(
                self._read_execution_reconciliation_v1(context, requests, capture, booked)
            )

            def admit():
                if (
                    self.closed
                    or self.owner is not owner
                    or self.bindings != bindings
                    or self._submitted_executions_v1(include_reconciliation=False) != submitted
                    or any(
                        owner.read_current_net_reversal_obligation_v1(rid) != revision
                        for rid, revision in booked.items()
                    )
                ):
                    raise ValueError("HOST_OCCUPIED_MARK_EXECUTION_REVISION_CHANGED")
                if (
                    not 0
                    <= self.clock() - context.observed.event_time_unix
                    <= context.observed.max_age_seconds
                ):
                    raise ValueError("HOST_BUDGET_PRIVATE_SNAPSHOT_STALE")
                owner.restart_fail_closed_v1()
                result = self._apply_execution_reconciliation_v1(
                    context, reads, capture, released=set(), deliver_incidents=True
                )
                capture.discard_response_bodies_v1()
                return replace(
                    context, execution_reconciliation=result, authenticated_reconciliation=capture
                ), capture.evidence

            return admit

        return next(iter(submitted)), read

    def prepare_simulated_double_play_reversal_v1(
        self, *, double_play, injected, decision_epoch, recovery
    ):
        """Continue the reconciled switch through its original 29P and 29Q owners."""
        from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
            STATUS_DOUBLE_PLAY_RESERVED,
            join_current_productive_enter_live_29p_before_venue_plan_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
            bind_current_productive_double_play_execution_plan_v1,
        )

        if (
            self.closed
            or self.owner is None
            or self.execution_environment != "INTERNAL_SIMULATED_EXECUTION"
            or type(recovery) is not HostBudgetRecoveryContextV1
            or recovery.host is not self
            or double_play.close_request.budget_owner is not self.owner
        ):
            raise ValueError("DOUBLE_PLAY_29P_ORIGINAL_SIMULATED_HOST_REQUIRED")
        continuation = double_play.continuation
        bound = continuation.bound_instrument
        decision_id = "l10:" + continuation.close_envelope_digest
        previous = self.owner.lookup_v1(
            slot_id=continuation.switch.episode.lane_id,
            decision_id=decision_id,
            cycle_id=decision_id,
            observation_id=self.owner.budget_state_v1().observation_id,
        )
        if previous is None:
            reserved = join_current_productive_enter_live_29p_before_venue_plan_v1(
                replay=None,
                bound_instrument=bound,
                injected=injected,
                decision_epoch=decision_epoch,
                portfolio_budget_owner=self.owner,
                host_budget_recovery=recovery,
                double_play=replace(double_play, reserve=True),
            )
            if reserved.status != STATUS_DOUBLE_PLAY_RESERVED:
                raise ValueError(reserved.first_blocker)
            reservation_id = reserved.portfolio_reservation_id
        else:
            reservation_id = str(previous.reservation_id)
        envelope = bind_current_productive_double_play_execution_plan_v1(
            reservation_id=reservation_id,
            double_play=double_play,
            bound_instrument=bound,
            injected=injected,
            decision_epoch=decision_epoch,
            host_budget_recovery=recovery,
        )
        return reservation_id, envelope

    def open_simulated_double_play_episode_v1(
        self, *, reservation_id, double_play, injected, decision_epoch, recovery, fill
    ):
        """Apply the exact simulated opening fill and retain the successor episode."""
        from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
            canonical_digest_v1,
        )
        from src.ops.exit_policy_producer_binding_v1.simulated_accounting_close_v1 import (
            create_successor_after_sealed_simulated_episode_v1,
            inspect_sealed_simulated_episode_v1,
        )
        from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
            _verify,
            bind_simulated_accounting_episode_identity_v1,
            recover_position_episode_from_simulated_accounting_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
            bind_current_productive_double_play_execution_plan_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
            FinalOrderEnvelopeV1,
        )
        from src.ops.portfolio_capital_reservation_budget_v1.slot_economic_source_v1 import (
            SlotCloseAccountingSourceV1,
            _fill,
        )
        from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
            ProductiveFuturesAccountingSessionV1,
        )
        from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import (
            SimulatedFillInputV1,
        )

        if (
            self.closed
            or self.owner is None
            or self.execution_environment != "INTERNAL_SIMULATED_EXECUTION"
            or type(recovery) is not HostBudgetRecoveryContextV1
            or recovery.host is not self
            or type(fill) is not SimulatedFillInputV1
        ):
            raise ValueError("DOUBLE_PLAY_ORIGINAL_SIMULATED_HOST_AND_FILL_REQUIRED")
        continuation = double_play.continuation
        close = double_play.close_request
        source = close.slot_accounting_source
        prior = continuation.switch.episode
        if (
            close.budget_owner is not self.owner
            or type(source) is not SlotCloseAccountingSourceV1
            or source.identity_v1() != prior
            or self.bindings.get(prior.lane_id) != continuation.bound_instrument
        ):
            raise ValueError("DOUBLE_PLAY_SIMULATED_FILL_CLOSE_SOURCE_MISMATCH")
        retained = self.owner.read_bound_double_play_execution_plan_v1(reservation_id)
        envelope = retained["envelope"]
        bound_fill = retained.get("simulated_fill_digest")
        if bound_fill is not None and bound_fill != fill.digest():
            raise ValueError("DOUBLE_PLAY_SIMULATED_FILL_ALREADY_BOUND")
        opening_epoch = datetime.fromisoformat(envelope["creation_epoch"].replace("Z", "+00:00"))
        if (
            retained["double_play"]["close_envelope_digest"] != continuation.close_envelope_digest
            or envelope["provenance_ref"] != continuation.switch.admission_ref_v1()
            or fill.fill_id != "original-plan:" + envelope["envelope_digest"]
            or fill.instrument_id != envelope["instrument_id"]
            or fill.side != envelope["side"].upper()
            or fill.quantity != Decimal(envelope["quantity"])
            or fill.reduce_only is not False
            or type(fill.event_time_unix) not in (float, int)
            or not opening_epoch.timestamp() <= fill.event_time_unix <= self.clock()
        ):
            raise ValueError("DOUBLE_PLAY_SIMULATED_FILL_ENVELOPE_MISMATCH")

        sealed = inspect_sealed_simulated_episode_v1(
            identity=prior,
            state_root=Path(source.state_root),
            repository_sha=source.repository_sha,
            config_digest=source.config_digest,
            expected_initial_source_ref=source.initial_source_ref,
        )
        flat = sealed["source_payload"]
        accounting = ProductiveFuturesAccountingSessionV1.from_durable_dict(
            flat["accounting_checkpoint"]
        )
        applied = accounting.apply_fill(fill)
        if applied.action_code != continuation.target_side.upper() + "_OPEN":
            raise ValueError("DOUBLE_PLAY_SIMULATED_FILL_DID_NOT_OPEN_TARGET_SIDE")
        fills = (*(_fill(row) for row in flat["fills"]), fill)
        identity = bind_simulated_accounting_episode_identity_v1(
            identity=replace(prior, position_side=continuation.target_side),
            opening_fill=fill,
        )
        root = self.root / "double_play_simulated_episodes" / reservation_id
        archive_root = root / "accounting"
        episode_args = {
            "identity": identity,
            "state_root": root / "position",
            "repository_sha": source.repository_sha,
            "config_digest": source.config_digest,
            "writer_session_id": self.session_id,
        }
        from hashlib import sha256
        from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
            bind_occupied_lane_governed_cycle_store_roots_v1,
            recover_occupied_scope_close_for_reconciliation_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
            CYCLE_EXCLUSION_LOCK_NAME,
            occupied_scope_mark_cycle_lock_v1,
        )
        from src.ops.portfolio_capital_reservation_budget_v1.core_cursor_source_v1 import (
            _read_original_cursor,
        )
        from trading.master_v2.double_play_state import SideState
        from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
            read_occupied_scope_mark_snapshot_v1,
        )

        pair = (double_play.lane, continuation.bound_instrument)
        cursor_root, lock_root, evidence_root = bind_occupied_lane_governed_cycle_store_roots_v1(
            {prior.lane_id: pair}
        )[prior.lane_id]
        if episode_args["state_root"].exists():
            if bound_fill is None:
                raise ValueError("DOUBLE_PLAY_SIMULATED_FILL_ALREADY_BOUND")
            if (Path(lock_root) / CYCLE_EXCLUSION_LOCK_NAME).exists():
                recover_occupied_scope_close_for_reconciliation_v1(
                    lane_id=prior.lane_id,
                    lane_pair=pair,
                    expected_scope=prior.account_scope,
                    sealed_accounting_source=source,
                )
            payload, _ = _verify(identity=identity, session=accounting, fills=fills)
            episode = recover_position_episode_from_simulated_accounting_v1(
                source_path=archive_root / (canonical_digest_v1(payload) + ".json"),
                **episode_args,
            )
        else:
            if bound_fill is None:
                current = bind_current_productive_double_play_execution_plan_v1(
                    reservation_id=reservation_id,
                    double_play=double_play,
                    bound_instrument=continuation.bound_instrument,
                    injected=injected,
                    decision_epoch=decision_epoch,
                    host_budget_recovery=recovery,
                )
            else:
                # This exact simulated fill was retained before the interruption.
                # Resume its accounting from the original plan and sealed flat.
                if (Path(lock_root) / CYCLE_EXCLUSION_LOCK_NAME).exists():
                    recover_occupied_scope_close_for_reconciliation_v1(
                        lane_id=prior.lane_id,
                        lane_pair=pair,
                        expected_scope=prior.account_scope,
                        sealed_accounting_source=source,
                    )
                current = FinalOrderEnvelopeV1(**envelope)
            if current.to_runtime_json_v1() != envelope:
                raise ValueError("DOUBLE_PLAY_SIMULATED_FILL_BOUND_PLAN_CHANGED")
            scope = read_occupied_scope_mark_snapshot_v1(Path(cursor_root))
            if scope is None or scope["digest"] != continuation.switch.scope_digest:
                raise ValueError("DOUBLE_PLAY_SIMULATED_FILL_CURRENT_SCOPE_CHANGED")
            suffix = f":{prior.lane_id}:{prior.lane_id}"
            cycle = scope["mark"]["cycle_id"]
            if not cycle.endswith(suffix) or not cycle.removesuffix(suffix):
                raise ValueError("OCCUPIED_SCOPE_CLOSE_CYCLE_ID_INVALID")
            attempt = sha256(cycle.removesuffix(suffix).encode()).hexdigest()
            lock = occupied_scope_mark_cycle_lock_v1(
                lock_root=Path(lock_root),
                evidence_root=Path(evidence_root) / "bounded_slot_attempts_v1" / attempt,
                native_id=envelope["instrument_id"],
            )
            lock.acquire()
            try:
                scope = read_occupied_scope_mark_snapshot_v1(Path(cursor_root))
                cursor, _, raw = _read_original_cursor(
                    cursor_root, instrument_id=prior.instrument_id, native_id=prior.venue_native_id
                )
                if (
                    scope is None
                    or scope["digest"] != continuation.switch.scope_digest
                    or cursor.side_state is SideState.KILL_ALL
                    or (raw.get("runtime_scope_state") or {}).get("chop_latched") is not False
                ):
                    raise ValueError("DOUBLE_PLAY_SIMULATED_FILL_CURRENT_SCOPE_CHANGED")
                if bound_fill is None:
                    double_play.mark.require_current_mark_clock_v1(observed_unix=self.clock())
                with self.owner.guard_bound_double_play_simulated_fill_v1(
                    reservation_id, current, fill_digest=fill.digest()
                ):
                    episode = create_successor_after_sealed_simulated_episode_v1(
                        prior_identity=prior,
                        prior_state_root=Path(source.state_root),
                        prior_repository_sha=source.repository_sha,
                        prior_config_digest=source.config_digest,
                        prior_initial_source_ref=source.initial_source_ref,
                        accounting_session=accounting,
                        fills=fills,
                        source_archive_root=archive_root,
                        **episode_args,
                    )
            finally:
                lock.release()
        return episode, accounting, fills

    def observe_after_bounded_slot_close_v1(self, bindings, *, request):
        """Refresh original account truth and rebind only a proven flat test slot."""
        if (
            self.owner is None
            or self.closed
            or self.execution_environment != "INTERNAL_SIMULATED_EXECUTION"
            or self.owner.entry_budget_policy_v1() is None
        ):
            raise ValueError("BOUNDED_CLOSE_ORIGINAL_SIMULATED_HOST_REQUIRED")
        proof = self.owner.inspect_bounded_slot_close_refresh_v1(request)
        slot = proof["slot_id"]
        if set(bindings) != set(self.bindings) or any(
            bindings[lane] != old for lane, old in self.bindings.items() if lane != slot
        ):
            raise ValueError("BOUNDED_CLOSE_FOREIGN_HOST_BINDING_CHANGED")
        return self._observe_once_v1(bindings, rebound_request=request)

    def _observe_once_v1(
        self,
        bindings,
        *,
        rebound_request=None,
        capture=None,
        required_execution_attempts=None,
        deliver_authenticated_incidents=False,
    ):
        if self.closed:
            raise ValueError("HOST_BUDGET_SESSION_CLOSED")
        if self.owner is None and self.durable_mode == "create" and self.root.exists():
            raise ValueError("HOST_BUDGET_BOOTSTRAP_SCOPE_ALREADY_EXISTS")
        # Fence before fetching: a failed refresh cannot retain old authority.
        if self.owner is not None:
            self.owner.restart_fail_closed_v1()
        observation = self._collect_account_observation_v1(bindings)
        return self._bind_observation_v1(
            bindings,
            observation,
            rebound_request=rebound_request,
            capture=capture,
            required_execution_attempts=required_execution_attempts,
            deliver_authenticated_incidents=deliver_authenticated_incidents,
        )

    def _collect_account_observation_v1(self, bindings):
        return collect_host_account_observation_v1(
            private_rest_fetch=self.fetch,
            instrument_ids_by_native_id={
                b.venue_native_id: b.instrument_id for b in bindings.values()
            },
            session_id=self.session_id,
            clock=self.clock,
            expected_account=self.expected_account_identity,
        )

    def _bind_observation_v1(
        self,
        bindings,
        observation,
        *,
        rebound_request=None,
        capture=None,
        required_execution_attempts=None,
        deliver_authenticated_incidents=False,
    ):
        account = observation.account
        if self.bindings is not None and self.bindings != bindings and rebound_request is None:
            raise ValueError("HOST_BUDGET_LANE_GENERATION_CHANGED")
        if self.owner is None:
            # Normal start/restart restores only. Missing/deleted state is not
            # evidence of a fresh account. Creation is an explicit bootstrap.
            self.owner = self._open_budget_owner_v1(account=account, bindings=bindings)
            self.account = account
            self.durable_mode = "recover"
            self.bindings = dict(bindings)
        context = self._account_recovery_context_v1(observation)
        context = replace(
            context,
            execution_reconciliation=self._reconcile_executions_v1(
                context,
                capture=capture,
                required_execution_attempts=required_execution_attempts,
                deliver_authenticated_incidents=deliver_authenticated_incidents,
            ),
        )
        if rebound_request is not None:
            slot = self.owner.inspect_bounded_slot_close_refresh_v1(rebound_request)["slot_id"]
            target = bindings[slot]
            if any(
                p.instrument_id
                in {target.instrument_id, rebound_request.bound_instrument.instrument_id}
                and p.signed_quantity != 0
                for p in context.observed.positions
            ):
                raise ValueError("BOUNDED_CLOSE_REBIND_POSITION_NOT_FLAT")
            context._recover_with_bindings_v1(
                self.owner, rebound_request.capital_handoff.producer_output, bindings
            )
            self.bindings = dict(bindings)
        return context

    def _account_recovery_context_v1(self, observation):
        return HostBudgetRecoveryContextV1(
            host=self,
            account=observation.account,
            pending_orders=observation.pending_orders,
            occupancy_payloads=observation.occupancy_payloads,
            pending_source=observation.pending_source,
            account_inventory_source=(
                observation.account_inventory_source
                if observation.account_inventory_source is self.fetch
                else None
            ),
            observed=observation.observed,
        )

    def _submitted_executions_v1(self, *, include_reconciliation=True):
        return {
            rid: (
                link
                if include_reconciliation
                else {key: value for key, value in link.items() if key != "reconciliation"}
            )
            for rid, link in self.owner.execution_links_v1(active_only=True).items()
            if link["phase"] == "SUBMIT_MAY_HAVE_OCCURRED"
        }

    def _reconcile_executions_v1(
        self,
        context,
        *,
        capture=None,
        required_execution_attempts=None,
        deliver_authenticated_incidents=False,
    ):
        from src.ops.execution_reconciliation_get_provenance_v1 import (
            AuthenticatedReconciliationGetV1,
        )
        from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
            parse_exchange_reconciliation_identity_v1,
        )

        submitted = self._submitted_executions_v1()
        released = set()
        if required_execution_attempts:
            retained = self.owner.execution_links_v1()
            for rid, expected_digest in required_execution_attempts.items():
                link = retained.get(rid)
                if (
                    link is None
                    or link["phase"] != "SUBMIT_MAY_HAVE_OCCURRED"
                    or parse_exchange_reconciliation_identity_v1(link["identity"]).identity_digest()
                    != expected_digest
                ):
                    raise ValueError("HOST_REQUIRED_EXECUTION_ATTEMPT_UNPROVEN")
                if rid not in submitted:
                    released.add(rid)
                    submitted[rid] = link
        if not submitted:
            return {}
        deliver_incidents = (
            capture is None or deliver_authenticated_incidents
        ) and self.execution_incident_state_path is not None
        if self.reconciliation_transport is None:
            if deliver_incidents:
                raise ValueError("HOST_EXECUTION_READ_PORT_MISSING")
            return {
                rid: {"matched": False, "reason_codes": ["HOST_EXECUTION_READ_PORT_MISSING"]}
                for rid in submitted
            }
        if deliver_incidents and capture is None:
            capture = AuthenticatedReconciliationGetV1(
                self.reconciliation_transport,
                account=self.account,
                clock=self.clock,
                retain_response_bodies=True,
            )
        requests = self._execution_reconciliation_requests_v1(context, submitted, capture)
        reads = self._read_execution_reconciliation_v1(context, requests, capture)
        return self._apply_execution_reconciliation_v1(
            context, reads, capture, released=released, deliver_incidents=deliver_incidents
        )

    def _execution_reconciliation_requests_v1(self, context, submitted, capture):
        from src.ops.execution_reconciliation_get_provenance_v1 import (
            AuthenticatedReconciliationGetV1,
            resolve_reconciliation_query_options_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
            PortfolioExecutionReconciliationIdentityV2,
            parse_exchange_reconciliation_identity_v1,
        )
        from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
            K1AccountObservationSourceV1,
        )

        inventory = context.account_inventory_source
        futures_custody = (
            type(inventory) is K1AccountObservationSourceV1
            and not inventory.closed
            and inventory.account_inventory_guard
            and inventory.inventory_inst_type == "FUTURES"
            and inventory.expected_account_identity == context.account
        )
        requests = []
        for rid, link in submitted.items():
            identity = parse_exchange_reconciliation_identity_v1(link["identity"])
            if identity.execution_environment != self.execution_environment:
                raise ValueError("HOST_EXECUTION_ENVIRONMENT_MISMATCH")
            options = None
            if type(identity) is PortfolioExecutionReconciliationIdentityV2:
                options = resolve_reconciliation_query_options_v1(
                    instrument_id=identity.instrument_id, native_id=identity.native_id
                )
            futures_order = options is not None and options.inst_type == "FUTURES"
            simulated_futures = (
                futures_order
                and futures_custody
                and self.execution_environment == "INTERNAL_SIMULATED_EXECUTION"
                and capture is None
                and self.reconciliation_transport is inventory.transport._transport
                and getattr(
                    self.owner.entry_budget_policy_v1(),
                    "require_original_public_movement_facts",
                    False,
                )
                and identity.send_authority_ref.startswith("futures-simulated-dispatch:")
            )
            if futures_order != futures_custody or (
                futures_order
                and not simulated_futures
                and type(capture) is not AuthenticatedReconciliationGetV1
            ):
                raise ValueError("HOST_EXECUTION_FUTURES_CUSTODY_UNPROVEN")
            requests.append((rid, identity, options))
        return requests

    def _read_execution_reconciliation_v1(self, context, requests, capture, booked_revisions=None):
        from src.ops.execution_reconciliation_get_provenance_v1 import (
            require_futures_reconciliation_product_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
            fetch_okx_read_only_reconciliation_snapshot_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
            GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )

        transport = self.reconciliation_transport if capture is None else capture
        config = transport.get(
            endpoint="/api/v5/account/config",
            auth_required=True,
            pretrade_decision_id=f"{self.session_id}:execution-recovery",
            get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )
        payload = config.payload
        if not (
            config.get_performed
            and config.method == "GET"
            and config.endpoint == "/api/v5/account/config"
            and config.auth_header_sent
            and not config.historical_reuse
            and config.http_status == 200
            and not config.error_class
            and isinstance(payload, dict)
            and payload.get("code") == "0"
            and isinstance(payload.get("data"), list)
            and len(payload["data"]) == 1
            and payload["data"][0].get("uid") == self.account
        ):
            raise ValueError("HOST_EXECUTION_READ_PORT_ACCOUNT_UNPROVEN")
        for rid, identity, options in requests:
            booked = (
                self.owner.read_current_net_reversal_obligation_v1(rid)
                if booked_revisions is None
                else booked_revisions[rid]
            )
            if booked is not None:
                from src.ops.full_core_live_path_composition_root_v1.current_productive_net_reversal_reconciliation_v1 import (
                    observe_booked_net_position_v1,
                )

                booking, revision_ref = booked
                result = observe_booked_net_position_v1(
                    source=capture,
                    booking=booking,
                    observed=context.observed,
                    occupancy_payloads=context.occupancy_payloads,
                    pending_orders=context.pending_orders,
                    session_id=self.session_id,
                    revision_ref=revision_ref,
                )
                yield rid, identity, None, None, result
                continue
            acquired = datetime.fromtimestamp(self.clock(), timezone.utc)
            snapshot = fetch_okx_read_only_reconciliation_snapshot_v1(
                identity=identity,
                options=options,
                read_only_get_transport=transport,
                pretrade_decision_id=f"{self.session_id}:{rid}",
                received_at=acquired.isoformat(),
            )
            if options is not None and options.inst_type == "FUTURES":
                require_futures_reconciliation_product_v1(snapshot)
            yield rid, identity, snapshot, acquired, None

    def _apply_execution_reconciliation_v1(
        self, context, reads, capture, *, released, deliver_incidents
    ):
        from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
            PortfolioExecutionReconciliationIdentityV2,
        )

        result = {}
        for rid, identity, snapshot, acquired, booked_result in reads:
            if snapshot is None:
                result[rid] = booked_result
                continue
            result[rid] = self.owner.reconcile_execution_v1(
                rid,
                snapshot=snapshot,
                observed=context.observed,
                account=context.account,
                now_unix=self.clock(),
                confirm_released_no_fill=rid in released,
            )
            if capture is not None and type(identity) is PortfolioExecutionReconciliationIdentityV2:
                capture.record_v1(
                    self,
                    rid,
                    identity,
                    snapshot,
                    acquired,
                    result[rid],
                    **({"publish_proof": False} if deliver_incidents else {}),
                )
                if deliver_incidents:
                    from src.ops.execution_incident_host_v1 import (
                        deliver_authenticated_host_execution_incident_v1,
                    )

                    deliver_authenticated_host_execution_incident_v1(
                        host=self,
                        capture=capture,
                        reservation_id=rid,
                        identity=identity,
                        snapshot=snapshot,
                        result=result[rid],
                        observed_at=acquired,
                    )
                    capture.publish_current_proof_v1(
                        identity=identity, snapshot=snapshot, observed_at=acquired
                    )
        if deliver_incidents and any(
            not item["matched"] or item["decision"]["reconciliation_complete"] is not True
            for item in result.values()
        ):
            raise ValueError("HOST_BUDGET_EXECUTION_RECONCILIATION_UNRESOLVED")
        return result

    def close(self):
        self.closed = True
        self._futures_financial_custody = None
        if self.owner is not None:
            self.owner.close()
