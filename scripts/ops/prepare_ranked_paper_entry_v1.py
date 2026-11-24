"""Eröffnungsbeobachtung des Paper-Accounts und Cap24 für eine bereits gebundene Lane."""

import argparse
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from time import time
from scripts.ops.run_zkp_lane1_paper_v1 import (
    REPO,
    _capture,
    _read_cap24_binding,
    load_paper_liquidity_policy_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1.paper_account_opening_v1 import (
    paper_account_opening_v1,
    read_paper_account_opening_v1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    exclusive_v1,
    immutable_json_v1,
)
from src.ops.ranked_slot_run_source_v1 import (
    read_paper_entry_admission_v1,
    read_ranked_paper_slot_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import PortfolioTruthSnapshotV1
from src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1 import (
    run_single_selected_future_runtime_binding_gate_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.persistence_v1 import (
    persist_binding_evidence_atomic_v1,
    verify_manifest,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import EVIDENCE_FILENAME
from src.ops.peak_trade_public_market_data_runtime_v1.freshness_v1 import (
    classify_live_mark_price_freshness_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import _fresh


def read(p):
    return json.loads(p.read_bytes())


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


def prepare(check, *, folder=None, evidence_base=None):
    if folder is None:
        raise ValueError("PAPER_ENTRY_SLOT_FOLDER_REQUIRED")
    cfg = read(folder / "slot.json")
    lane = cfg["lane"]
    expected = {"LANE_2": "UP-USD_UM_XPERP-310919", "LANE_5": "OL-USD_UM_XPERP-310912"}
    require(
        lane in expected
        and cfg["surface"] == "PAPER_EXCHANGE"
        and cfg["native_instrument_id"] == expected[lane],
        "RANKED_PAPER_SCOPE",
    )
    data = read(check / "zulassungspruefung.json")
    row = next(row for row in data["paper_slots"] if row["zuweisung"]["lane_id"] == lane)
    require(row["session"] == cfg["session_id"], "FOREIGN_CAP23_SESSION")
    require(row["status"] == "CAP23_ACTIVE", "NO_CAP23")
    source = dict(
        occupancy=row["zuweisung"],
        selection_root=row["selection_root"],
        ranking_root=data["cap22_root"],
        universe_root=data["cap21_root"],
        selection_digest=row["selection_digest"],
    )
    cfg["paper_entry_admission"] = source
    origin, slot = read_ranked_paper_slot_v1(cfg)
    if "repository_sha" in data:
        source.update(
            repository_sha=data["repository_sha"],
            original_repository_sha=origin.selection.repository_sha,
        )
    admission = read_paper_entry_admission_v1(cfg, origin)
    admission.require_current_v1(time())
    campaign = read(folder / "gvef-entwurf.json")
    session = cfg["session_id"]
    state = Path(campaign["state"]).parent
    require(state.name == session and state.is_dir(), "SESSION_ROOT")
    target = Path(campaign["paper_runs"]) / session
    require(
        campaign["slot"]["session_id"] == session
        and campaign["slot"]["venue_native_id"] == slot.native_id
        and Path(campaign["paper_runs"]) == state / "sources" / "paper",
        "GVEF_SESSION_ROOT",
    )
    # Zulassungsgenerationen haben getrennte Cap24- und Kontoeröffnungsbelege.
    # Bei der späteren Sitzung konsumiert der Runner exakt das gewählte Profil.
    binding_state = state
    if evidence_base is not None:
        binding_state = evidence_base.resolve(strict=True) / session
        binding_state.mkdir(mode=0o700, exist_ok=True)
    output = binding_state / "cap24" / lane
    account_file = binding_state / "paper-opening.json"
    pointer = binding_state / "paper-opening-source.json"
    with exclusive_v1(state / "prepare-entry.lock"):
        require(
            not target.exists() and not target.with_name(target.name + "-inputs").exists(),
            "SESSION_ALREADY_OBSERVED",
        )
        if (binding_state / "slot-gebunden.json").is_file():
            from scripts.ops.run_zkp_lane1_paper_v1 import _verify_renewed_paper_cap24

            existing = read(binding_state / "slot-gebunden.json")
            require(all(existing.get(k) == v for k, v in cfg.items()), "BINDING_GENERATION_CHANGED")
            bound = _read_cap24_binding(
                output, entry_repository_sha=admission.selection.repository_sha
            )
            admission.require_binding_v1(bound)
            _verify_renewed_paper_cap24(existing, output, origin, admission, bound)
            print(lane, slot.native_id, "Vorhandene Einstiegsbindung geprüft")
            return
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        capture = binding_state / ("opening-market-" + stamp)
        capture.mkdir(mode=0o700)
        market = _capture(
            load_paper_liquidity_policy_v1(REPO),
            label=session + "-opening-" + stamp,
            output=capture,
            slot=slot,
        )
        if not pointer.exists():
            if account_file.exists():
                old = read(account_file)
                candidates = [
                    x
                    for x in binding_state.glob("opening-market-*")
                    if (x / "usdc-index.json").is_file()
                    and sha256((x / "usdc-index.json").read_bytes()).hexdigest()
                    == old["fx_source_sha256"]
                    and (x / "receipts.json").is_file()
                ]
                require(len(candidates) == 1, "OPENING_RECEIPT_AMBIGUOUS")
                market_dir = candidates[0]
            else:
                old = paper_account_opening_v1(config=cfg, market=market)
                immutable_json_v1(account_file, old)
                market_dir = capture
            immutable_json_v1(
                pointer,
                dict(
                    path=str(account_file),
                    digest=canonical_digest_v1(old),
                    market_dir=str(market_dir),
                ),
            )
        cfg["paper_account_opening"] = read(pointer)
        initial = read_paper_account_opening_v1(cfg, market)
        portfolio = initial["portfolio"]
        require(
            not portfolio["positions"]
            and not portfolio["fill_count"]
            and not portfolio["applied_fill_ids"]
            and portfolio["equity"] == portfolio["initial_equity"],
            "PAPER_ACCOUNT_NOT_NEW",
        )
        # Fresh readback of this isolated unstarted account. Only flat genesis is admitted here.
        observed_at = time()
        observed = PortfolioTruthSnapshotV1(
            positions=(),
            cash=Decimal(portfolio["equity"]),
            source_id="PAPER_EXCHANGE:" + session + ":" + cfg["paper_account_opening"]["digest"],
            event_time_unix=initial["observed_at_unix"],
            wall_time_unix=observed_at,
        )
        recorded_marks = read(capture / "mark.json")["data"]
        receipt = read(capture / "receipts.json")["mark"]
        require(
            len(recorded_marks) == 1
            and recorded_marks[0]["instId"] == slot.native_id
            and Decimal(recorded_marks[0]["markPx"]) == market.mark,
            "MARK_ID",
        )
        _fresh(
            recorded_marks[0],
            datetime.fromisoformat(receipt["acquired_at_utc"]).timestamp(),
            observed_at,
            classify_live_mark_price_freshness_v1,
        )
        recon = binding_state / "reconciliation" / lane
        gate = run_single_selected_future_runtime_binding_gate_v1(
            selection_state_root=Path(source["selection_root"]),
            ranking_state_root=Path(source["ranking_root"]),
            universe_state_root=Path(source["universe_root"]),
            repository_sha=admission.selection.repository_sha,
            session_id=session,
            now_unix=observed_at,
            reconciliation_state_root=recon,
            observed_portfolio=observed,
            expected_selection_integrity_digest=source["selection_digest"],
            mark_price_by_native_id={slot.native_id: str(market.mark)},
        )
        require(gate.ok and gate.alpha_enabled and gate.bound is not None, str(gate.blockers))
        admission.require_binding_v1(gate.bound)
        result = dict(
            gate=gate.to_dict(),
            session_id=session,
            lane=lane,
            n5_assignment=origin.reference(),
            entry_admission=admission.reference(),
            paper_opening_digest=cfg["paper_account_opening"]["digest"],
            observed_portfolio=observed.to_dict(),
            mark_source=str(capture / "mark.json"),
            mark_body_sha256=market.source_hashes["mark"],
        )
        persist_binding_evidence_atomic_v1(
            evidence_root=output, evidence=gate.evidence.to_dict(), result=result
        )
        verify_manifest(output)
        admission.require_binding_v1(
            _read_cap24_binding(output, entry_repository_sha=admission.selection.repository_sha)
        )
        cfg["paper_cap24"] = {
            "root": str(output),
            "evidence_sha256": sha256((output / EVIDENCE_FILENAME).read_bytes()).hexdigest(),
            "result_digest": canonical_digest_v1(result),
        }
        from scripts.ops.run_zkp_lane1_paper_v1 import _verify_renewed_paper_cap24

        _verify_renewed_paper_cap24(cfg, output, origin, admission, gate.bound)
        admission.require_current_v1(time())
        immutable_json_v1(binding_state / "slot-gebunden.json", cfg)
        print(
            lane,
            slot.native_id,
            "Cap24 positiv",
            gate.reconciliation_result["classification"],
            admission.selection.valid_until,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prüft eine neue Cap23-Zulassung und bereitet den isolierten OL-Papereinstieg vor. Startet keinen Runner."
    )
    parser.add_argument("--zulassungsordner", type=Path, required=True)
    parser.add_argument("--slot-folder", type=Path, required=True)
    parser.add_argument(
        "--belegordner", type=Path, help="Eigener Ordner für eine zeitlich begrenzte Vorstartprobe"
    )
    args = parser.parse_args()
    prepare(
        args.zulassungsordner.resolve(strict=True),
        folder=args.slot_folder.resolve(strict=True),
        evidence_base=args.belegordner,
    )
