"""Read a closed Paper episode from its original sealed archive."""

from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import re

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.experiments.canonical_research_prepared_execution_v1 import digest_v1
from src.governance.canonical_order_intent_v1 import (
    canonical_order_intent_from_dict,
    canonical_order_intent_to_semantic_dict,
)
from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    COMMIT_MARKER_FILENAME,
    EXIT_STATE_FILENAME,
    MANIFEST_FILENAME,
)
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    IDENTITY_FILENAME,
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_close_v1 import (
    inspect_sealed_simulated_episode_v1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    economic_journal_events_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import (
    SimulatedFillInputV1,
)

SCHEMA = "paper_episode_outcome.v1"
PAPER_PROFILE = "bounded_single_instrument_paper_profile.v1"
SIMULATION = "INTERNAL_SIMULATED_EXECUTION"
FILL_LEDGER = "accounting/productive_fill_ledger_v1.jsonl"
EPISODE_ID = re.compile(r"simulated-accounting:[0-9a-f]{64}")


def closed_paper_episode_ids_v1(root: Path) -> tuple[str, ...]:
    """Select sealed simulated closes from a finalized Paper archive."""
    if root != root.resolve():
        raise ValueError("PAPER_OUTCOME_ARCHIVE_OR_EPISODE_INVALID")
    closeout = json.loads((root / "paper-closeout.json").read_bytes())
    if closeout["status"] not in {"WINDOW_ENDED", "STOPPED"} or closeout["error"] is not None:
        return ()
    episodes = root / "episodes"
    if not episodes.is_dir():
        return ()
    closed = []
    for folder in sorted(episodes.iterdir()):
        if not EPISODE_ID.fullmatch(folder.name) or not folder.is_dir():
            continue
        path = folder / EXIT_STATE_FILENAME
        if path.resolve() != path:
            raise ValueError("PAPER_OUTCOME_SYMLINK_FORBIDDEN")
        state = json.loads(path.read_bytes())
        if isinstance(state.get("simulated_accounting_close"), dict):
            closed.append(folder.name)
    return tuple(closed)


def paper_episode_fee_observation_v1(root: Path, measurement: dict) -> dict:
    """Read modeled quote fees and fill notional for the already verified episode."""
    ledger = _index(root / "paper-fills.jsonl", lambda row: row["fill"]["fill_id"])
    fills = [ledger[binding["fill_id"]]["fill"] for binding in measurement["fill_bindings"]]
    fees = sum(Decimal(fill["fee"]) for fill in fills)
    notional = sum(abs(Decimal(fill["notional"])) for fill in fills)
    if (
        fees != Decimal(measurement["fees"])
        or notional <= 0
        or sha256((root / MANIFEST_FILENAME).read_bytes()).hexdigest()
        != measurement["archive_manifest_sha256"]
    ):
        raise ValueError("PAPER_FEE_OBSERVATION_MISMATCH")
    return {
        "currency": measurement["currency"],
        "fees": str(fees),
        "notional": str(notional),
        "fee_basis_points": str(fees * 10_000 / notional),
    }


def _index(path, key):
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        identity = key(row)
        if identity in rows:
            raise ValueError(f"PAPER_OUTCOME_DUPLICATE_RECORD:{path.name}:{identity}")
        rows[identity] = row
    return rows


def _source_path(root, reference, pins):
    _, _, source = reference.split(":", 2)
    path = Path(source)
    if path.parent != root / "episode-sources" or path.relative_to(root).as_posix() not in pins:
        raise ValueError("PAPER_OUTCOME_SOURCE_OUTSIDE_MANIFEST")
    return path


def _utc(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z")


def _read_episode(root, state_root, profile, pins, expected_lane_id):
    entry = json.loads((state_root / IDENTITY_FILENAME).read_bytes())
    state = json.loads((state_root / EXIT_STATE_FILENAME).read_bytes())
    fields = dict(entry["identity"])
    fields["account_scope"] = PositionEpisodeScopeV1(**fields["account_scope"])
    identity = PositionEpisodeIdentityV1(**fields)
    binding = profile["instrument_binding"]
    if (
        identity.episode_id != state_root.name
        or (expected_lane_id is not None and identity.lane_id != expected_lane_id)
        or identity.account_scope.execution_environment != SIMULATION
        or identity.account_scope.account_identity != root.name
        or identity.instrument_id != binding["instrument_id"]
        or identity.venue_native_id != binding["venue_native_id"]
    ):
        raise ValueError("PAPER_OUTCOME_EPISODE_SCOPE_MISMATCH")
    initial_ref = entry["entry_source_ref"]
    initial = _source_path(root, initial_ref, pins)
    closure_ref = state["simulated_accounting_close"]["closure_ref"]
    closure = json.loads(_source_path(root, closure_ref, pins).read_bytes())["payload"]
    _source_path(root, closure["flat_source_ref"], pins)
    progress = closure["prior_exit_state"].get("simulated_accounting_progress")
    if progress is not None:
        for field in ("initial_source_ref", "previous_source_ref", "current_source_ref"):
            _source_path(root, progress[field], pins)
    sealed = inspect_sealed_simulated_episode_v1(
        identity=identity,
        state_root=state_root,
        repository_sha=profile["repository_sha"],
        config_digest=state["config_digest"],
        expected_initial_source_ref=initial_ref,
    )
    opening = json.loads(initial.read_bytes())["payload"]["fills"][-1]
    if sealed["source_payload"]["accounting_checkpoint"]["contract"] != profile["contract"]:
        raise ValueError("PAPER_OUTCOME_CONTRACT_MISMATCH")
    return sealed, opening, initial_ref, closure["observed_unix"]


def _bind_fill(fill, account, fills, decisions, executions, ledger):
    fill_id = fill["fill_id"]
    recorded = fills[fill_id]
    cycle = recorded["cycle_id"]
    decision_row = decisions[cycle]
    decision = json.loads(decision_row["decision"])
    execution = executions[cycle]
    original = account.applied_fill_results[fill_id]
    intent = canonical_order_intent_from_dict(execution["intent"])
    side = "BUY" if (intent.side == "LONG") != intent.reduce_only else "SELL"
    decision_time = decision_row["observed_unix"]
    fill_time = fill["event_time_unix"]
    if (
        recorded["fill"] != fill
        or execution["modeled_fill"] != fill
        or canonical_order_intent_to_semantic_dict(intent) != execution["intent"]
        or fill_id != f"paper:{intent.semantic_digest}"
        or intent.submission_authorized
        or intent.execution_eligible
        or intent.adapter_compatible
        or intent.decision_id != decision["decision_id"]
        or intent.trading_epoch != str(decision["trading_epoch"])
        or intent.instrument_id != decision["instrument_id"]
        or intent.instrument_id != fill["instrument_id"]
        or intent.side not in {"LONG", "SHORT"}
        or side != fill["side"]
        or intent.reduce_only != fill["reduce_only"]
        or intent.quantity != Decimal(fill["quantity"])
        or decision["decision_outcome"] != decision_row["decision_outcome"]
        or not (isfinite(decision_time) and 0 < decision_time <= fill_time)
        or ledger[fill_id]
        != {
            "fill_id": fill_id,
            "action_code": original.action_code,
            "fill_input_digest": original.fill_input_digest,
            "accounting_output_digest": original.accounting_output_digest,
        }
    ):
        raise ValueError(f"PAPER_OUTCOME_FILL_LINEAGE_MISMATCH:{fill_id}")
    return {
        "decision_id": decision["decision_id"],
        "decision_sha256": sha256(decision_row["decision"].encode()).hexdigest(),
        "cycle_id": cycle,
        "decision_observed_at_utc": _utc(decision_time),
        "decision_outcome": decision["decision_outcome"],
        "decision_config_sha256": decision["config_digest"],
        "trading_epoch": str(decision["trading_epoch"]),
        "intent_id": intent.intent_id,
        "intent_digest": intent.semantic_digest,
        "fill_id": fill_id,
        "fill_event_at_utc": _utc(fill_time),
        "accounting_output_digest": original.accounting_output_digest,
    }


def _accounting_before_open(payload, account, opening_fill_id):
    replay = ProductiveFuturesAccountingSessionV1(
        contract=account.contract,
        initial_equity=account.initial_equity,
        writer_identity=account.writer_identity,
    )
    monetary = {"quantity", "mark_price", "fill_price", "fee", "slippage_cost", "notional"}
    for event in economic_journal_events_v1(payload):
        row = event["value"]
        if event["kind"] == "FUNDING":
            replay.apply_funding_observation_v1(
                event_id=event["event_id"],
                amount=row["amount"],
                currency=row["currency"],
                instrument_id=row["instrument_id"],
                event_time_unix=row["event_time_unix"],
            )
        else:
            if row["fill_id"] == opening_fill_id:
                return replay.portfolio_state().to_dict()
            replay.apply_fill(
                SimulatedFillInputV1(
                    **{
                        key: Decimal(value) if key in monetary else value
                        for key, value in row.items()
                    }
                )
            )
    raise ValueError("PAPER_OUTCOME_OPENING_FILL_MISSING")


def read_paper_episode_outcome_v1(
    root: Path, episode_id: str, *, expected_lane_id: str | None = None
) -> dict:
    """Recompute a simulated net outcome for an explicitly selected episode."""
    root = root.absolute()
    if root.resolve() != root or not EPISODE_ID.fullmatch(episode_id):
        raise ValueError("PAPER_OUTCOME_ARCHIVE_OR_EPISODE_INVALID")
    state_root = root / "episodes" / episode_id
    state_files = (
        IDENTITY_FILENAME,
        EXIT_STATE_FILENAME,
        COMMIT_MARKER_FILENAME,
        MANIFEST_FILENAME,
    )
    required = (
        "paper-profile.json",
        "paper-closeout.json",
        "paper-decisions.jsonl",
        "paper-execution-decisions.jsonl",
        "paper-fills.jsonl",
        FILL_LEDGER,
        *((state_root / name).relative_to(root).as_posix() for name in state_files),
    )
    manifest = root / MANIFEST_FILENAME
    manifest_before = manifest.read_bytes()
    ok, reason = verify_manifest_sha256(root, required_rel_paths=required)
    if not ok:
        raise ValueError(f"PAPER_OUTCOME_MANIFEST_INVALID:{reason}")
    pins = {
        line.split(None, 1)[1] for line in manifest_before.decode().splitlines() if line.strip()
    }
    profile = json.loads((root / "paper-profile.json").read_bytes())
    closeout = json.loads((root / "paper-closeout.json").read_bytes())
    if (
        profile["schema"] != PAPER_PROFILE
        or profile["execution_environment"] != SIMULATION
        or profile["venue_order_transport"] is not False
        or not re.fullmatch(r"[0-9a-f]{40}", profile["repository_sha"])
        or not re.fullmatch(r"[0-9a-f]{64}", profile["source_tree_sha256"])
        or closeout["status"] not in {"WINDOW_ENDED", "STOPPED"}
        or closeout["error"] is not None
    ):
        raise ValueError("PAPER_OUTCOME_COMPLETED_SIMULATION_REQUIRED")

    sealed, opening, initial_ref, observed_unix = _read_episode(
        root, state_root, profile, pins, expected_lane_id
    )
    payload = sealed["source_payload"]
    account = ProductiveFuturesAccountingSessionV1.from_durable_dict(
        payload["accounting_checkpoint"]
    )
    fills = _index(root / "paper-fills.jsonl", lambda row: row["fill"]["fill_id"])
    decisions = _index(root / "paper-decisions.jsonl", lambda row: row["cycle_id"])
    executions = _index(root / "paper-execution-decisions.jsonl", lambda row: row["cycle_id"])
    ledger = _index(root / FILL_LEDGER, lambda row: row["fill_id"])
    if fills.keys() != ledger.keys() or len(fills) != closeout["simulated_fills"]:
        raise ValueError("PAPER_OUTCOME_ARCHIVE_FILL_COUNT_MISMATCH")
    opening_index = account.fill_order.index(opening["fill_id"])
    episode_fills = payload["fills"][opening_index:]
    if (
        len(episode_fills) < 2
        or opening["reduce_only"]
        or not episode_fills[-1]["reduce_only"]
        or fills[opening["fill_id"]]["episode_id"] != episode_id
    ):
        raise ValueError("PAPER_OUTCOME_EPISODE_FILL_RANGE_INVALID")
    bindings = [
        _bind_fill(fill, account, fills, decisions, executions, ledger) for fill in episode_fills
    ]
    before = _accounting_before_open(payload, account, opening["fill_id"])
    after = account.portfolio_state().to_dict()
    if (
        before["positions"]
        or after["positions"]
        or before != decisions[bindings[0]["cycle_id"]]["accounting_before_fill"]
        or after != fills[episode_fills[-1]["fill_id"]]["accounting"]
        or Decimal(after["initial_equity"]) != Decimal(profile["initial_equity_usd"])
    ):
        raise ValueError("PAPER_OUTCOME_FLAT_ACCOUNTING_BOUNDARY_REQUIRED")
    realized = Decimal(after["realized_pnl"]) - Decimal(before["realized_pnl"])
    fees = Decimal(after["cumulative_fees"]) - Decimal(before["cumulative_fees"])
    funding = Decimal(after["funding_pnl"]) - Decimal(before["funding_pnl"])
    slippage = Decimal(after["cumulative_slippage"]) - Decimal(before["cumulative_slippage"])
    net = Decimal(after["equity"]) - Decimal(before["equity"])
    if net != realized + funding - fees or fees < 0 or slippage < 0:
        raise ValueError("PAPER_OUTCOME_ACCOUNTING_DELTA_MISMATCH")
    if manifest.read_bytes() != manifest_before:
        raise ValueError("PAPER_OUTCOME_MANIFEST_CHANGED")

    body = {
        "schema": SCHEMA,
        "authority": "NONE",
        "execution_environment": SIMULATION,
        "archive_manifest_sha256": sha256(manifest_before).hexdigest(),
        "repository_sha": profile["repository_sha"],
        "source_tree_sha256": profile["source_tree_sha256"],
        "episode_id": episode_id,
        "session_id": root.name,
        "instrument_id": profile["instrument_binding"]["instrument_id"],
        "venue_native_id": profile["instrument_binding"]["venue_native_id"],
        "currency": account.contract.quote_currency,
        "observed_at_utc": _utc(observed_unix),
        "entry_source_ref": initial_ref,
        "closure_ref": sealed["closure_ref"],
        "fill_bindings": bindings,
        "realized_pnl": str(realized),
        "fees": str(fees),
        "funding_pnl": str(funding),
        "slippage_already_reflected_in_fill_prices": str(slippage),
        "simulated_net_pnl": str(net),
    }
    return {**body, "outcome_digest": digest_v1(body)}
