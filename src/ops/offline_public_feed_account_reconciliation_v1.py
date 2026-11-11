"""Join the stopped offline feed to the original FUTURES account and budget owners."""

from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.current_futures_simulated_dispatch_v1 import (
    SIMULATED_ENVIRONMENT,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    durable_consume_path_v1,
    load_external_effect_durable_consume_v1,
)
from src.ops.offline_public_feed_recovery_v1 import (
    OfflinePublicFeedRecoveryError,
    OfflinePublicFeedRecoveryV1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    FUTURES_INVENTORY_REQUEST_COUNT,
    K1AccountObservationSourceV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest
from src.ops.portfolio_capital_reservation_budget_v1.execution_v1 import (
    read_persisted_execution_reconciliation_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    BoundedSlotReconciliationScopeV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.classifier_v1 import (
    classify_productive_reconciliation_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    EVIDENCE_FILENAME,
    MANIFEST_FILENAME,
    PORTFOLIO_STATE_FILENAME,
)
from src.ops.productive_reconciliation_runtime_binding_v1.persistence_v1 import (
    config_digest_for_binding,
    detect_duplicate_portfolio_state,
    load_persisted_portfolio_state,
    verify_manifest,
)
from src.ops.productive_reconciliation_runtime_binding_v1.single_writer_v1 import (
    ProductivePortfolioSingleWriterV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.taxonomy_v1 import (
    ProductiveReconciliationClass,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


def _read_original_portfolio(host, root):
    paths = [
        root / name for name in (PORTFOLIO_STATE_FILENAME, EVIDENCE_FILENAME, MANIFEST_FILENAME)
    ]
    if detect_duplicate_portfolio_state(root) or any(
        path.resolve() != path or not path.is_file() for path in paths
    ):
        raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_PORTFOLIO_SCOPE_UNPROVEN")
    portfolio_path, evidence_path, manifest_path = paths
    manifest = manifest_path.read_text(encoding="utf-8")
    files = [line.split(None, 1)[-1] for line in manifest.splitlines() if line.strip()]
    if sorted(files) != sorted((portfolio_path.name, evidence_path.name)):
        raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_PORTFOLIO_MANIFEST_UNPROVEN")
    verify_manifest(root)
    persisted = load_persisted_portfolio_state(root, require_present=True)
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if (
        persisted.missing
        or evidence.get("post_state_digest") != persisted.digest()
        or evidence.get("config_digest")
        != config_digest_for_binding(repository_sha=host.repository_sha)
    ):
        raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_ORIGINAL_PORTFOLIO_UNPROVEN")
    return persisted, sha256(manifest.encode()).hexdigest()


def _read_owned_submit_barrier(link, *, scope_root):
    if "transport_store_root" not in link:
        return None
    root = Path(link["transport_store_root"])
    path = durable_consume_path_v1(root)
    if root.resolve() != root or not root.is_relative_to(scope_root) or path.resolve() != path:
        raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_ORIGINAL_SUBMIT_STORE_UNPROVEN")
    original = load_external_effect_durable_consume_v1(store_root=root)
    record = original["record"]
    if (
        not original["durable_consumed"]
        or not record
        or record.get("execution_identity") != link["identity"]
        or record["permit_id"] != link["external_effect_permit"]["permit_id"]
        or original["resubmit_allowed"] is not False
    ):
        raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_ORIGINAL_SUBMIT_BARRIER_UNPROVEN")
    return {
        "permit_id": record["permit_id"],
        "consume_state": record["durable_state"],
        "resubmit_allowed": False,
        "receipt_sha256": fact_digest(record),
    }


def capture_offline_feed_account_reconciliation_v1(
    repair: OfflinePublicFeedRecoveryV1, *, host: PortfolioBudgetHostV1, bindings: dict
) -> dict:
    """Capture current evidence under a pinned stop. The existing owners keep their writes."""
    if type(repair) is not OfflinePublicFeedRecoveryV1 or type(host) is not PortfolioBudgetHostV1:
        raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_ORIGINAL_HOST_REQUIRED")
    feed = repair.read_verified_repair_v1()

    def require_same_feed():
        if repair.read_verified_repair_v1() != feed:
            raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_MARK_CHANGED")

    result = _inspect_stopped_account(
        repair.incident,
        host=host,
        bindings=bindings,
        require_stop=require_same_feed,
        feed_verified_at=datetime.fromisoformat(feed["verified_at"]).timestamp(),
    )
    if result["execution_blocker"] is not None:
        raise OfflinePublicFeedRecoveryError(result["execution_blocker"])
    if result["portfolio_classification"] != ProductiveReconciliationClass.MATCH.value:
        raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_ORIGINAL_POSITION_NOT_MATCHED")
    return {
        **result,
        "schema": "offline_public_feed_account_reconciliation.v1",
        "feed_binding": feed["binding"],
        "feed_mark_fact_sha256": feed["mark"]["fact_sha256"],
        "feed_mark_event_ms": feed["mark"]["event_ms"],
        "feed_mark_captured_at": feed["mark"]["captured_at"],
        "feed_mark_row_sha256": feed["mark"]["event_id"].rsplit(":", 1)[1],
    }


def _inspect_stopped_account(incident, *, host, bindings, require_stop, feed_verified_at=None):
    """Read and reconcile through the original owners while the scoped stop is proven."""
    if type(host) is not PortfolioBudgetHostV1:
        raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_ORIGINAL_HOST_REQUIRED")
    if (
        host.execution_environment != SIMULATED_ENVIRONMENT
        or host.root != incident.root / "host"
        or host.session_id != incident.session_id
    ):
        raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_SIMULATED_SCOPE_UNPROVEN")
    if type(bindings) is not dict or len(bindings) != 1:
        raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_ORIGINAL_BINDING_REQUIRED")
    (bound,) = bindings.values()
    if (
        type(bound) is not BoundInstrumentV1
        or bound.venue_native_id != incident.instrument.venue_native_id
        or bound.instrument_id != incident.instrument.canonical_instrument_id
    ):
        raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_ORIGINAL_BINDING_REQUIRED")
    result = _inspect_original_futures_account(
        host=host,
        bindings=bindings,
        require_stop=require_stop,
        transport_scope=incident.root,
        feed_verified_at=feed_verified_at,
    )
    slot = next(iter(bindings))
    return {
        **result,
        "schema": "offline_stopped_account_observation.v1",
        "slot": slot,
        "selection_integrity_digest": bound.selection_integrity_digest,
    }


def _inspect_original_futures_account(
    *, host, bindings, require_stop, transport_scope, feed_verified_at=None
):
    source = host.fetch
    portfolio_root = host.root / "reconciliation"
    budget_root = host.root / "owner"
    database = budget_root / "reservations.sqlite3"
    if (
        host.closed
        or host.root.resolve() != host.root
        or host.durable_mode != "recover"
        or not portfolio_root.is_dir()
        or portfolio_root.resolve() != portfolio_root
        or not database.is_file()
        or any(
            path.resolve() != path
            for path in (
                database,
                budget_root / "writer.lock",
                database.with_suffix(".sqlite3-journal"),
            )
        )
        or type(source) is not K1AccountObservationSourceV1
        or source.closed
        or not source.account_inventory_guard
        or source.inventory_inst_type != "FUTURES"
        or source.session_id != host.session_id
        or source.expected_account_identity != host.expected_account_identity
        or host.reconciliation_transport is not source.transport._transport
    ):
        raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_SIMULATED_SCOPE_UNPROVEN")
    if (
        type(bindings) is not dict
        or not bindings
        or host.bindings not in (None, bindings)
        or any(type(bound) is not BoundInstrumentV1 for bound in bindings.values())
    ):
        raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_ORIGINAL_BINDING_REQUIRED")

    # This is the portfolio owner's existing writer exclusion. The comparison
    # below only reads its manifest and position state.
    writer = ProductivePortfolioSingleWriterV1(
        state_root=portfolio_root, session_id=host.session_id
    )
    writer.acquire(now_unix=host.clock())
    try:
        persisted, manifest_digest = _read_original_portfolio(host, portfolio_root)
        require_stop()
        initial_reads = source.transport.read_count
        context = host.observe_v1(bindings)
        observed = context.observed
        read_count = source.transport.read_count
        if (
            context.account_inventory_source is not source
            or read_count - initial_reads != FUTURES_INVENTORY_REQUEST_COUNT
            or (feed_verified_at is not None and observed.event_time_unix < feed_verified_at)
        ):
            raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_CURRENT_INVENTORY_UNPROVEN")

        owner = host.owner
        commitments = owner.local_commitment_readback_v1()
        results = {}
        execution_blocker = None
        for rid, result in context.execution_reconciliation.items():
            decision = result.get("decision")
            if decision is None:
                execution_blocker = "FEED_ACCOUNT_EXECUTION_UNRESOLVED"
                results[rid] = {"matched": False, "reason_codes": result["reason_codes"]}
                continue
            sequence, digest, link = read_persisted_execution_reconciliation_v1(owner, rid)
            if link["reconciliation"] != result or result["portfolio_digest"] != observed.digest():
                raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_EXECUTION_READBACK_MISMATCH")
            matched = result.get("matched") is True and decision["reconciliation_complete"] is True
            if not matched:
                execution_blocker = "FEED_ACCOUNT_EXECUTION_UNRESOLVED"
            results[rid] = {
                "identity_digest": result["identity_digest"],
                "order_and_fill_snapshot_digest": result["snapshot_digest"],
                "confirmed_filled_qty": decision["cumulative_filled_qty"],
                "outcome": decision["outcome"],
                "matched": matched,
                "reservation_released": result["reservation_released"],
                "budget_sequence": sequence,
                "budget_digest": digest,
                "original_submit_barrier": _read_owned_submit_barrier(
                    link, scope_root=transport_scope
                ),
            }
        active_submissions = {
            rid
            for rid, link in owner.execution_links_v1(active_only=True).items()
            if link["phase"] == "SUBMIT_MAY_HAVE_OCCURRED"
        }
        if active_submissions - results.keys():
            execution_blocker = "FEED_ACCOUNT_EXECUTION_COVERAGE_UNPROVEN"
        if context.pending_orders:
            execution_blocker = "STARTUP_PENDING_ORDERS_UNRESOLVED"

        scope = None
        if host.execution_environment == SIMULATED_ENVIRONMENT:
            scope = BoundedSlotReconciliationScopeV1(
                owner.entry_budget_policy_v1(), tuple(bindings.items()), host.execution_environment
            )
        classification, _, _ = classify_productive_reconciliation_v1(
            persisted=persisted,
            observed=observed,
            now_unix=host.clock(),
            bounded_reconciliation_scope=scope,
        )
        current = source.inspect_futures_financial_gets_v1(context, read_count=read_count)
        require_stop()
        owner.require_local_commitment_readback_v1(commitments, account_identity=context.account)
        budget = owner.budget_state_v1()
        if not budget.recovery_required or budget.admitted:
            raise OfflinePublicFeedRecoveryError("FEED_ACCOUNT_BUDGET_FENCE_UNPROVEN")
        writer.assert_held()
        return {
            "account": context.account,
            "host_root": str(host.root),
            "observed_portfolio_digest": observed.digest(),
            "persisted_portfolio_digest": persisted.digest(),
            "persisted_portfolio_manifest_sha256": manifest_digest,
            "account_inventory_digest": fact_digest(current.gets),
            "occupancy_payload_sha256": fact_digest(context.occupancy_payloads),
            "observed_at_unix": observed.event_time_unix,
            "account_inventory_completed_unix": observed.wall_time_unix,
            "account_inventory_max_age_seconds": observed.max_age_seconds,
            "local_commitment_generation": commitments.generation_digest,
            "durable_budget_head": owner.risk_snapshot_v1()["durable_head"],
            "active_local_commitment_usdc": str(commitments.active_commitment_sum),
            "execution_reconciliation": results,
            "execution_blocker": execution_blocker,
            "portfolio_classification": classification.value,
        }
    finally:
        writer.release()
