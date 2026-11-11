"""N1 host lifecycle for the existing durable owner; no execution authority.

Private REST observations are account-bound before opening the store. Recovery
consumes the existing canonical capital producer only at the outer ENTRY seam.
Order/fill history is bounded observation, not reservation-to-fill resolution.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import time

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


def collect_host_account_observation_v1(
    *,
    private_rest_fetch,
    instrument_ids_by_native_id,
    session_id,
    clock=time.time,
    expected_account=None,
) -> HostAccountObservationV1:
    """Reuse host baseline checks before any budget-store or binding mutation.

    The caller supplies its existing private read capability. This collector
    does not create a budget owner, reconcile persisted state or grant alpha.
    """
    started = clock()
    uids = set()
    pending = []
    occupancy = {}

    def fetch(path, params):
        # Baseline defaults filter orders by one instrument. The shared
        # budget must observe the account's SWAP scope instead.
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
    native = dict(instrument_ids_by_native_id)
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
                source_id="host-private-rest-swap",
                event_time_unix=started,
                wall_time_unix=now,
            )
        )
    observation = HostAccountObservationV1(
        account=account,
        pending_orders=bool(pending),
        occupancy_payloads=occupancy,
        observed=PortfolioTruthSnapshotV1(
            positions=tuple(positions),
            source_id="host-private-rest-swap",
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

    if is_original_account_observation_source_v1(private_rest_fetch):
        private_rest_fetch.bind_completed_host_observation_v1(observation)
        observation = replace(observation, pending_source=private_rest_fetch)
    return observation


@dataclass(frozen=True)
class HostBudgetRecoveryContextV1:
    host: "PortfolioBudgetHostV1"
    account: str
    observed: PortfolioTruthSnapshotV1
    pending_orders: bool
    occupancy_payloads: dict
    execution_reconciliation: dict = field(default_factory=dict)
    pending_source: object | None = field(default=None, repr=False, compare=False)

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
        self.account = expected_account_identity
        self.closed = False
        self.retry_sleep = retry_sleep
        self.retry_interval_seconds = retry_interval_seconds
        self.transport_retry_count = 0
        self.reconciliation_transport = reconciliation_transport
        self.execution_environment = execution_environment
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
            and execution_environment != "INTERNAL_SIMULATED_EXECUTION"
        ):
            raise ValueError("SLOT_TEST_BUDGET_REQUIRES_SIMULATED_HOST")
        self.entry_budget_policy = entry_budget_policy

    def observe_v1(self, bindings):
        return self._observe_with_retry_v1(bindings)

    def observe_execution_reconciliation_evidence_v1(self, bindings):
        """Expose original snapshots only for the explicit isolated SHADOW probe."""
        from src.ops.execution_incident_host_v1 import InjectedReconciliationGetV1

        if self.execution_environment != "SHADOW":
            raise ValueError("HOST_EXECUTION_EVIDENCE_SHADOW_REQUIRED")
        capture = InjectedReconciliationGetV1(self.reconciliation_transport)
        context = self._observe_with_retry_v1(bindings, capture=capture)
        return context, capture.evidence

    def observe_authenticated_execution_reconciliation_v1(self, bindings, *, proof_root=None):
        """Observe the original LIVE chain with a per-request GET proof and no Safety delivery."""
        from src.ops.execution_reconciliation_get_provenance_v1 import (
            AuthenticatedReconciliationGetV1,
        )

        if self.execution_environment != "LIVE":
            raise ValueError("HOST_EXECUTION_EVIDENCE_LIVE_IDENTITY_REQUIRED")
        capture = AuthenticatedReconciliationGetV1(
            self.reconciliation_transport,
            account=self.expected_account_identity,
            clock=self.clock,
            proof_root=proof_root,
        )
        context = self._observe_with_retry_v1(bindings, capture=capture)
        return context, capture.evidence

    def _observe_with_retry_v1(self, bindings, *, capture=None):
        from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.recovery_v1 import (
            bounded_retry_policy_v1,
        )

        attempt = 0
        while True:
            if capture is not None:
                capture.reset_v1()
            try:
                return self._observe_once_v1(bindings, capture=capture)
            except (TimeoutError, ConnectionError):
                if not bounded_retry_policy_v1(
                    attempt=attempt,
                    automatic_recovery_allowed=True,
                )["retry_allowed"]:
                    raise
                attempt += 1
                self.transport_retry_count += 1
                self.retry_sleep(self.retry_interval_seconds)

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

    def _observe_once_v1(self, bindings, *, rebound_request=None, capture=None):
        if self.closed:
            raise ValueError("HOST_BUDGET_SESSION_CLOSED")
        if self.owner is None and self.durable_mode == "create" and self.root.exists():
            raise ValueError("HOST_BUDGET_BOOTSTRAP_SCOPE_ALREADY_EXISTS")
        # Fence before fetching: a failed refresh cannot retain old authority.
        if self.owner is not None:
            self.owner.restart_fail_closed_v1()
        observation = collect_host_account_observation_v1(
            private_rest_fetch=self.fetch,
            instrument_ids_by_native_id={
                b.venue_native_id: b.instrument_id for b in bindings.values()
            },
            session_id=self.session_id,
            clock=self.clock,
            expected_account=self.expected_account_identity,
        )
        account = observation.account
        if self.bindings is not None and self.bindings != bindings and rebound_request is None:
            raise ValueError("HOST_BUDGET_LANE_GENERATION_CHANGED")
        if self.owner is None:
            # Normal start/restart restores only. Missing/deleted state is not
            # evidence of a fresh account. Creation is an explicit bootstrap.
            store = self.root / "owner"
            self.owner = PortfolioCapitalReservationBudgetOwnerV1(
                durable_root=store,
                durable_account_identity=account,
                durable_mode=self.durable_mode,
                durable_lane_bindings=bindings,
                entry_budget_policy=self.entry_budget_policy,
            )
            restored_policy = self.owner.entry_budget_policy_v1()
            if (
                restored_policy is not None
                and restored_policy.per_slot_reserved_notional_limit is not None
                and self.execution_environment != "INTERNAL_SIMULATED_EXECUTION"
            ):
                self.owner.close()
                raise ValueError("SLOT_TEST_BUDGET_REQUIRES_SIMULATED_HOST")
            self.account = account
            self.durable_mode = "recover"
            self.bindings = dict(bindings)
        context = HostBudgetRecoveryContextV1(
            host=self,
            account=account,
            pending_orders=observation.pending_orders,
            occupancy_payloads=observation.occupancy_payloads,
            pending_source=observation.pending_source,
            observed=observation.observed,
        )
        context = replace(
            context,
            execution_reconciliation=self._reconcile_executions_v1(context, capture=capture),
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

    def _reconcile_executions_v1(self, context, *, capture=None):
        from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
            PortfolioExecutionReconciliationIdentityV2,
            parse_exchange_reconciliation_identity_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
            fetch_okx_read_only_reconciliation_snapshot_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
            GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )

        submitted = {
            rid: link
            for rid, link in self.owner.execution_links_v1(active_only=True).items()
            if link["phase"] == "SUBMIT_MAY_HAVE_OCCURRED"
        }
        if not submitted:
            return {}
        if self.reconciliation_transport is None:
            return {
                rid: {"matched": False, "reason_codes": ["HOST_EXECUTION_READ_PORT_MISSING"]}
                for rid in submitted
            }
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
        result = {}
        for rid, link in submitted.items():
            identity = parse_exchange_reconciliation_identity_v1(link["identity"])
            if identity.execution_environment != self.execution_environment:
                raise ValueError("HOST_EXECUTION_ENVIRONMENT_MISMATCH")
            acquired = datetime.fromtimestamp(self.clock(), timezone.utc)
            snapshot = fetch_okx_read_only_reconciliation_snapshot_v1(
                identity=identity,
                read_only_get_transport=transport,
                pretrade_decision_id=f"{self.session_id}:{rid}",
                received_at=acquired.isoformat(),
            )
            result[rid] = self.owner.reconcile_execution_v1(
                rid,
                snapshot=snapshot,
                observed=context.observed,
                account=context.account,
                now_unix=self.clock(),
            )
            if capture is not None and type(identity) is PortfolioExecutionReconciliationIdentityV2:
                capture.record_v1(self, rid, identity, snapshot, acquired, result[rid])
        return result

    def close(self):
        self.closed = True
        if self.owner is not None:
            self.owner.close()
