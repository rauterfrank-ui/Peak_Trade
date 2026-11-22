"""Bounded BTC Demo budget/reconciliation host over the original owners.

No transport construction, credentials, submits, retries or capital conversion.
This is the GET/recovery side of a host, not a new entry/reversal order engine.
A public USD/USDC index valuation never certifies account settlement or sizing.
"""

from copy import deepcopy
from datetime import datetime
from decimal import Decimal
import json
import math
from pathlib import Path

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import NUMERIC_EQUITY_TTL_SECONDS
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    PortfolioExecutionReconciliationIdentityV2,
    parse_exchange_reconciliation_identity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    exclusive_v1,
    immutable_json_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    CurrentProductive29PRiskCapitalOutputV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
    require_budget_head_read_only_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def _number(value):
    _need(type(value) in (int, float) and math.isfinite(value), "BTC_DEMO_HOST_CLOCK_INVALID")
    return value


def validate_btc_demo_coverage_v1(report, *, account, now):
    """Reproduce the original reader result; this is local consistency, not authenticity."""
    _number(now)
    body = deepcopy(report)
    checksum = body.pop("coverage_digest", None)
    _need(checksum == canonical_digest_v1(body), "BTC_DEMO_COVERAGE_DIGEST_MISMATCH")
    _need(
        body.get("schema") == "btc_demo_coverage.v1"
        and body.get("account_identity") == account
        and body.get("venue") == demo._DEMO.venue
        and body.get("execution_environment") == "TESTNET"
        and body.get("trading_authority") == "NONE"
        and body.get("usd_usdc_account_settlement_proven") is False,
        "BTC_DEMO_COVERAGE_SCOPE_MISMATCH",
    )
    rows = body.get("source_observations")
    _need(type(rows) is list and len(rows) == 5, "BTC_DEMO_COVERAGE_ORIGINALS_REQUIRED")
    captured = demo.BtcDemoObservationsV1(None)
    captured.rows = deepcopy(rows)
    rebuilt = demo.read_btc_demo_coverage_v2(reads=captured.replay_v1(), expected_uid=account)
    _need(rebuilt == report, "BTC_DEMO_COVERAGE_ORIGINAL_BODY_MISMATCH")
    receipts = [datetime.fromisoformat(row["acquired_at"]) for row in rows]
    _need(
        all(
            stamp.utcoffset() is not None
            and 0 <= now - stamp.timestamp() <= NUMERIC_EQUITY_TTL_SECONDS
            for stamp in receipts
        ),
        "BTC_DEMO_COVERAGE_STALE_OR_FUTURE",
    )
    return rebuilt


class BtcDemoBudgetReconciliationHostV1:
    """Join exact Demo observations to the existing durable budget writer.

    Constructor and budget admission do not submit or grant trading authority.
    Missing native USD sizing/settlement evidence remains its original gate.
    """

    def __init__(self, *, owner, bound, account, testnet_root):
        _need(
            type(owner) is PortfolioCapitalReservationBudgetOwnerV1,
            "BTC_DEMO_ORIGINAL_BUDGET_OWNER_REQUIRED",
        )
        lane = demo._demo_lane_root(testnet_root)
        scope = owner.durable_scope_identity_v1()
        _need(
            scope == {"root": str(lane.parent / "budget-owner" / "owner"), "account": account},
            "BTC_DEMO_BUDGET_OWNER_SCOPE_MISMATCH",
        )
        _need(bound.venue_native_id == demo._NATIVE, "BTC_DEMO_INSTRUMENT_SCOPE_MISMATCH")
        state = owner.risk_snapshot_v1()["state"]
        _need(
            set(state["lane_bindings"]) == {"LANE_3"}
            and state["lane_bindings"]["LANE_3"]["bound"] == bound.to_dict(),
            "BTC_DEMO_ORIGINAL_LANE_BINDING_REQUIRED",
        )
        self.owner, self.bound, self.account, self.root = owner, bound, account, Path(testnet_root)

    def budget_revision_ref_v1(self):
        """Read the actual original journal under its existing owner's lock.

        The sealed owner/store stay unchanged. Its original snapshot rejects
        closed/failed sources; its original revision reader validates the row;
        its read-only head gate binds the same account and actual disk head.
        """
        scope = self.owner.durable_scope_identity_v1()
        with self.owner._lock:
            snapshot = self.owner._risk_snapshot_locked()
            store = self.owner._store
            revision = store.read_revision_v1(store.sequence, snapshot["durable_head"])
            require_budget_head_read_only_v1(
                Path(scope["root"]),
                account_identity=self.account,
                expected_digest=revision["digest"],
            )
            return revision["sequence"], revision["digest"]

    def _fence_budget_v1(self):
        state = self.owner.budget_state_v1()
        if state.admitted or not state.recovery_required:
            self.owner.restart_fail_closed_v1()

    def admit_budget_v1(self, *, coverage, output, observed, reconciliation, now):
        """Feed typed USDC capital to the original recovery gate; do not mint it."""
        self._fence_budget_v1()
        report = validate_btc_demo_coverage_v1(coverage, account=self.account, now=now)
        _need(report["position_mode"] == "net_mode", "BTC_DEMO_NET_POSITION_MODE_REQUIRED")
        _need(
            type(output) is CurrentProductive29PRiskCapitalOutputV1,
            "BTC_DEMO_CANONICAL_CAPITAL_PRODUCER_REQUIRED",
        )
        _need(
            output.bound_account_identity == self.account
            and output.bound_venue_identity == "okx"
            and output.settlement_currency == "USDC"
            and output.value is not None,
            "BTC_DEMO_CANONICAL_CAPITAL_SCOPE_MISMATCH",
        )
        # Account-USDC margin is its own source. Neither USD balance nor public
        # FX valuation can be substituted into the existing capital producer.
        available = report["available_equity"].get("USDC")
        _need(
            available is not None and 0 < Decimal(output.value) <= Decimal(available),
            "BTC_DEMO_OBSERVED_USDC_CAPITAL_UNPROVEN",
        )
        policy = self.owner.entry_budget_policy_v1()
        _need(
            policy is not None
            and "LANE_3" in policy.allowed_slot_ids
            and policy.per_slot_reserved_notional_limit is not None
            and policy.per_slot_reserved_notional_limit <= demo._BUDGET_USDC
            and policy.per_entry_notional_limit <= demo._BUDGET_USDC
            and policy.require_opening_execution_costs
            and policy.require_closing_execution_costs
            and policy.require_next_funding_costs,
            "BTC_DEMO_ORIGINAL_BOUNDED_COST_POLICY_REQUIRED",
        )
        return self.owner.recover_automatically_v1(
            output=output,
            observed=observed,
            reconciliation=reconciliation,
            lane_bindings={"LANE_3": self.bound},
            now_unix=now,
            capital_max_age_seconds=NUMERIC_EQUITY_TTL_SECONDS,
        )

    def reconcile_attempt_v1(self, *, reads, reservation_id, clock):
        """Persist exact exchange reconciliation before any V2 first-fill handoff."""
        self._fence_budget_v1()
        revision = self.budget_revision_ref_v1()
        identity, _, _ = demo._read_original_attempt(
            demo._demo_lane_root(self.root), self.account, reservation_id, revision
        )
        _need(
            type(identity) is PortfolioExecutionReconciliationIdentityV2,
            "BTC_DEMO_ORIGINAL_ATTEMPT_REQUIRED",
        )
        snapshot, _, _, acquired, originals = demo.collect_btc_demo_execution_observation_v1(
            reads, identity
        )
        now = _number(clock())
        _need(
            all(
                0
                <= now - datetime.fromisoformat(row["acquired_at"]).timestamp()
                <= NUMERIC_EQUITY_TTL_SECONDS
                for row in originals.rows
            ),
            "BTC_DEMO_RECONCILIATION_STALE_OR_FUTURE",
        )
        positions = []
        for row in snapshot.positions_observation["response"]["data"]:
            _need(
                row.get("instId") == demo._NATIVE and row.get("posSide") == "net",
                "BTC_DEMO_POSITION_SCOPE_UNPROVEN",
            )
            quantity = demo._money(row.get("pos"))
            positions.append(
                PositionTruthV1.from_signed(
                    instrument_id=identity.instrument_id,
                    signed_quantity=quantity,
                    source_id="OKX_EEA_DEMO_PRIVATE_GET",
                    event_time_unix=acquired.timestamp(),
                    wall_time_unix=now,
                )
            )
        observed = PortfolioTruthSnapshotV1(
            positions=tuple(positions),
            source_id="OKX_EEA_DEMO_PRIVATE_GET",
            event_time_unix=acquired.timestamp(),
            wall_time_unix=now,
            max_age_seconds=NUMERIC_EQUITY_TTL_SECONDS,
        )
        # Source/submit revisions belong to the original writer, not this host.
        _need(self.budget_revision_ref_v1() == revision, "BTC_DEMO_BUDGET_HEAD_CHANGED")
        from hashlib import sha256

        old = self.owner.execution_links_v1()[reservation_id].get("reconciliation")
        digest = sha256(json.dumps(snapshot.to_dict(), sort_keys=True).encode()).hexdigest()
        if (
            old is not None
            and old["snapshot_digest"] == digest
            and old["portfolio_digest"] == observed.digest()
        ):
            evidence = old
        else:
            evidence = self.owner.reconcile_execution_v1(
                reservation_id,
                snapshot=snapshot,
                observed=observed,
                account=self.account,
                now_unix=now,
            )
        return {
            "authority": "NONE",
            "identity": identity.to_dict(),
            "budget_revision": list(self.budget_revision_ref_v1()),
            "reconciliation": evidence,
            "source_observations": deepcopy(originals.rows),
        }

    def bind_confirmed_entry_v1(
        self,
        *,
        reconciliation,
        repository_sha,
        config_digest,
        writer_session_id,
        g17_producer,
        cursor_store_root=None,
    ):
        """Use precisely the reconciled response batch, never a fresh mixed snapshot."""
        identity = parse_exchange_reconciliation_identity_v1(reconciliation["identity"])
        rid = identity.portfolio_reservation_id
        original = self.owner.execution_links_v1().get(rid)
        evidence = reconciliation["reconciliation"]
        _need(
            original is not None
            and original["identity"] == identity.to_dict()
            and original["reconciliation"] == evidence
            and evidence["matched"] is True
            and evidence["reservation_released"] is False
            and Decimal(evidence["decision"]["cumulative_filled_qty"]) > 0,
            "BTC_DEMO_ORIGINAL_MATCHED_FILL_RECONCILIATION_REQUIRED",
        )
        revision = tuple(reconciliation["budget_revision"])
        _need(revision == self.budget_revision_ref_v1(), "BTC_DEMO_BUDGET_HEAD_CHANGED")
        captured = demo.BtcDemoObservationsV1(None)
        captured.rows = deepcopy(reconciliation["source_observations"])
        # The native first-fill reader rechecks quantity, position, fees and
        # terminal status. The stored snapshot digest binds the supplied batch.
        snapshot, _, _, _, _ = demo.collect_btc_demo_execution_observation_v1(
            captured.replay_v1(), identity
        )
        from hashlib import sha256

        checksum = sha256(json.dumps(snapshot.to_dict(), sort_keys=True).encode()).hexdigest()
        _need(checksum == evidence["snapshot_digest"], "BTC_DEMO_RECONCILED_SOURCE_CHANGED")
        require_budget_head_read_only_v1(
            Path(self.owner.durable_scope_identity_v1()["root"]),
            account_identity=self.account,
            expected_digest=revision[1],
        )
        return demo.bind_btc_demo_first_fill_to_v2(
            reads=captured.replay_v1(),
            testnet_root=self.root,
            expected_uid=self.account,
            reservation_id=rid,
            revision_ref=revision,
            repository_sha=repository_sha,
            config_digest=config_digest,
            writer_session_id=writer_session_id,
            g17_producer=g17_producer,
            cursor_store_root=cursor_store_root,
        )

    def supervise_reconciliation_v1(
        self, *, state_root, started_at, reads, clock, pause, poll_seconds=5
    ):
        """Bound the GET/recovery side to one original hour; no trading loop.

        The absolute window is retained across process re-entry. At expiry or
        STOP, all uncertain/filled holds remain with the original budget owner.
        Fresh entry, reversal and order sends are outside this supervisor.
        """
        _number(started_at)
        _need(
            started_at > 0
            and type(poll_seconds) in (int, float)
            and math.isfinite(poll_seconds)
            and poll_seconds > 0,
            "BTC_DEMO_HOST_WINDOW_INVALID",
        )
        root = Path(state_root)
        protected = (
            demo._demo_lane_root(self.root),
            Path(self.owner.durable_scope_identity_v1()["root"]),
        )
        _need(
            root.is_absolute()
            and root == root.resolve()
            and root.is_relative_to(self.root)
            and all(
                not root.is_relative_to(path) and not path.is_relative_to(root)
                for path in protected
            ),
            "BTC_DEMO_HOST_STATE_SCOPE_MISMATCH",
        )
        window = {
            "schema": "btc_demo_reconciliation_host_window.v1",
            "authority": "NONE",
            "account": self.account,
            "bound": self.bound.to_dict(),
            "budget_owner": self.owner.durable_scope_identity_v1(),
            "started_at": started_at,
            "deadline": started_at + 3600,
        }
        root.mkdir(parents=True, exist_ok=True)
        with exclusive_v1(root / ".host.lock"):
            immutable_json_v1(root / "window.json", window)
            self._fence_budget_v1()
            closed = root / "closeout.json"
            if closed.exists():
                _need(closed.resolve() == closed, "BTC_DEMO_HOST_STATE_SCOPE_MISMATCH")
                receipt = json.loads(closed.read_bytes())
                _need(
                    receipt.get("window") == window
                    and receipt.get("authority") == "NONE"
                    and receipt.get("orders_sent") == 0
                    and receipt.get("status") in {"STOPPED", "WINDOW_ENDED"},
                    "BTC_DEMO_HOST_CLOSEOUT_MISMATCH",
                )
                return receipt
            index = len(list(root.glob("observation-*.json")))
            previous_time = started_at
            while True:
                now = _number(clock())
                _need(now >= previous_time, "BTC_DEMO_HOST_CLOCK_REGRESSED")
                previous_time = now
                if now >= window["deadline"] or (root / "STOP").exists():
                    break
                for rid, link in self.owner.execution_links_v1(active_only=True).items():
                    if link["phase"] != "SUBMIT_MAY_HAVE_OCCURRED":
                        continue
                    # No retry of a submit. A failing read leaves the original
                    # obligation untouched and ends this invocation visibly.
                    result = self.reconcile_attempt_v1(reads=reads, reservation_id=rid, clock=clock)
                    immutable_json_v1(root / f"observation-{index:08d}.json", result)
                    index += 1
                now = _number(clock())
                _need(now >= previous_time, "BTC_DEMO_HOST_CLOCK_REGRESSED")
                previous_time = now
                if now < window["deadline"]:
                    pause(min(poll_seconds, window["deadline"] - now))
            result = {
                "status": "STOPPED" if (root / "STOP").exists() else "WINDOW_ENDED",
                "authority": "NONE",
                "window": window,
                "observations": index,
                "orders_sent": 0,
                "held_capital": str(self.owner.active_sum_v1()),
            }
            immutable_json_v1(root / "closeout.json", result)
            return result
