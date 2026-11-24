"""Erzeugt den Cap22-Vergleich und slotgebundene Cap23-Folgeauswahlen eines neuen öffentlichen Snapshots."""

import argparse

import gzip
import json
from datetime import datetime, timezone
from pathlib import Path
from time import time
from src.ops.current_mf_member_to_pinned_cap23_n1_adapter_v1.adapter_v1 import (
    build_governed_cap23_pin_v1,
    GovernedCap23PinAdapterError,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
    InjectedEconomicMdPublicSourceV1,
    InstrumentPublicMdBundleV1,
    RawMarkCandleV1,
    RawTickerQuoteV1,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    load_and_validate_universe_snapshot_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap21_to_cap23_productive_persistence_v1 import (
    assert_current_productive_cap22_ranking_policy_binding_v1,
    build_cap22_feature_production_snapshot_for_cap21_universe_only_v1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    load_and_validate_ranking_snapshot_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    run_productive_futures_ranking_producer_v1,
)
from src.ops.ranked_slot_run_source_v1 import read_ranked_run_slot_v1
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    run_single_selected_future_policy_v1,
)
from src.ops.single_selected_future_policy_v1.persistence_v1 import load_and_validate_selection_v1

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--preparation-folder", required=True, type=Path)
parser.add_argument("--quellordner", required=True, type=Path)
args = parser.parse_args()
base = args.preparation_folder.resolve(strict=True)
root = args.quellordner.resolve(strict=True)


def read(path):
    return json.loads(path.read_bytes())


def save(path, data):
    with path.open("x") as out:
        json.dump(data, out, ensure_ascii=False, indent=2, allow_nan=False)
        out.write("\n")


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


capture = read(root / "market-capture.json")
revision = capture["revision"]
from src.experiments.canonical_experiment_identity_v1 import inspect_code_provenance_v1

code = inspect_code_provenance_v1(Path(__file__).resolve().parents[2])
require(
    code.git_sha == revision and code.working_tree_status == "CLEAN",
    "CURRENT_CLEAN_CAPTURE_REQUIRED",
)
require(
    not capture["missing_collections"]
    and not any(capture[x] for x in ("private_gets", "orders_sent", "permits_created")),
    "CAPTURE_SCOPE",
)
universe_root = root / f"cap21-{capture['final_cap21_round']}"
universe = load_and_validate_universe_snapshot_v1(universe_root, expected_repository_sha=revision)
require(universe.ok, "CAP21_INTEGRITY")
ranking_root = root / "ranking"
if not ranking_root.exists():
    with gzip.open(root / "economic-md-bundles.json.gz", "rt") as f:
        raw = json.load(f)
    require(set(capture["final_cap21_native_ids"]) <= raw.keys(), "UNIVERSE_SCOPE")
    source = InjectedEconomicMdPublicSourceV1(
        {
            key: InstrumentPublicMdBundleV1(
                venue_native_id=key,
                marks=tuple(RawMarkCandleV1(**m) for m in row["marks"]),
                ticker=RawTickerQuoteV1(**row["ticker"]) if row["ticker"] else None,
                failure_codes=tuple(row["failure_codes"]),
            )
            for key, row in raw.items()
        }
    )
    assert_current_productive_cap22_ranking_policy_binding_v1()
    features = build_cap22_feature_production_snapshot_for_cap21_universe_only_v1(
        universe_snapshot=universe.snapshot.to_dict(),
        public_md_source=source,
        collection_started_at_unix=datetime.fromisoformat(capture["started_at_utc"]).timestamp(),
        collection_completed_at_unix=capture["final_observed_unix"],
    )
    save(root / "features.json", features.to_dict())
    result = run_productive_futures_ranking_producer_v1(
        state_root=ranking_root,
        universe_state_root=universe_root,
        feature_production_snapshot=features,
        repository_sha=revision,
        producer_observed_at_unix=capture["final_observed_unix"],
        session_id=root.name,
    )
    require(result["ok"] and not result["hard_stop"], str(result["failure_codes"]))
loaded = load_and_validate_ranking_snapshot_v1(ranking_root, expected_repository_sha=revision)
require(loaded.ok, "CAP22_INTEGRITY")
rank = loaded.snapshot
u = universe.snapshot
require(
    (rank.universe_snapshot_id, rank.universe_source_digest, rank.universe_payload_digest)
    == (u.snapshot_id, u.source_digest, u.payload_digest),
    "CAP21_CAP22_REFERENZ",
)
findings = {
    "repository_sha": revision,
    "ranking_event_utc": rank.event_time,
    "ranking_snapshot_id": rank.ranking_snapshot_id,
    "ranking_digest": rank.integrity_digest,
    "universe_snapshot_id": u.snapshot_id,
    "cap21_root": str(universe_root),
    "cap22_root": str(ranking_root),
    "ranked_count": len(rank.ranked_candidates),
    "paper_slots": [],
    "shadow_slots": [],
}
for lane in ("LANE_1", "LANE_2", "LANE_4", "LANE_5"):
    cfg = read(base / lane / "slot.json")
    assignment = read_ranked_run_slot_v1(cfg)
    orig = assignment.selection
    croot = root / "cap23" / cfg["session_id"] / lane
    require(
        cfg["surface"] == ("SHADOW" if lane in ("LANE_1", "LANE_4") else "PAPER_EXCHANGE"),
        "SLOT_SCOPE",
    )
    entry = {
        "zuweisung": assignment.reference(),
        "session": cfg["session_id"],
        "current_rank": None,
        "cap21_eligible": any(
            (i.canonical_instrument_id, i.venue_native_inst_id, i.eligibility)
            == (orig.instrument_id, orig.venue_native_id, True)
            for i in u.instruments
        ),
    }
    candidates = [
        c.rank
        for c in rank.ranked_candidates
        if (c.canonical_instrument_id, c.venue_native_id)
        == (orig.instrument_id, orig.venue_native_id)
    ]
    if candidates:
        require(len(candidates) == 1, "DUPLICATE_RANK")
        entry["current_rank"] = candidates[0]
    try:
        pin = build_governed_cap23_pin_v1(
            canonical_instrument_id=orig.instrument_id,
            ranking_snapshot=rank.to_dict(),
            lane_state_root=croot,
        )
    except GovernedCap23PinAdapterError as exc:
        entry.update(status="PIN_DENIED", reason=str(exc))
    else:
        require(
            pin.resolved_venue_native_id == orig.venue_native_id and entry["cap21_eligible"],
            "NATIVE_ID_OR_ELIGIBILITY",
        )
        require(not croot.exists(), "NEW_GENERATION_REQUIRED")
        product = run_single_selected_future_policy_v1(
            state_root=croot,
            ranking_state_root=ranking_root,
            repository_sha=revision,
            producer_observed_at_unix=time(),
            session_id=cfg["session_id"],
            previous_selection=orig.to_dict(),
            load_previous_from_state=False,
            governed_pin=pin,
        )
        checked = load_and_validate_selection_v1(croot, expected_repository_sha=revision)
        require(checked.ok, "CAP23_INTEGRITY")
        s = checked.selection
        active = (
            product["ok"]
            and not product["hard_stop"]
            and s.state == "SELECTED_ACTIVE"
            and s.instrument_id == orig.instrument_id
            and s.venue_native_id == orig.venue_native_id
            and s.selected_rank == entry["current_rank"]
            and s.previous_selection_id == orig.selection_id
            and s.ranking_integrity_digest == rank.integrity_digest
            and s.selected_at_event_time == orig.selected_at_event_time
            and datetime.fromisoformat(s.valid_until).timestamp() > time()
        )
        entry.update(
            status="CAP23_ACTIVE" if active else "CAP23_DENIED",
            selection_root=str(croot),
            selection_digest=s.integrity_digest,
            selection_id=s.selection_id,
            valid_until=s.valid_until,
            reasons=s.reason_codes,
        )
    findings["shadow_slots" if cfg["surface"] == "SHADOW" else "paper_slots"].append(entry)
save(root / "zulassungspruefung.json", findings)
print(json.dumps(findings, ensure_ascii=False))
