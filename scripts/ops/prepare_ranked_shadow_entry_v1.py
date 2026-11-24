"""Bereitet eine neue Shadow-Einstiegszulassung aus den originalen Cap21–23-Belegen vor."""

import argparse
import json
from pathlib import Path
from time import time

from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    immutable_json_v1,
)
from src.ops.ranked_shadow_entry_selection_v1 import inspect_ranked_shadow_entry_selection_v1
from src.ops.ranked_slot_run_source_v1 import (
    read_ranked_run_slot_v1,
    read_shadow_entry_admission_v1,
)


def read(path):
    return json.loads(path.read_bytes())


def prepare(folder, source_root):
    """Bind one fresh Shadow admission and its producer to the same session."""
    config = read(folder / "slot.json")
    lane, session = config["lane"], config["session_id"]
    inputs = read(source_root / "zulassungspruefung.json")
    rows = [row for row in inputs["shadow_slots"] if row["zuweisung"]["lane_id"] == lane]
    if len(rows) != 1 or rows[0]["session"] != session or config["surface"] != "SHADOW":
        raise ValueError("SHADOW_SESSION_MISMATCH")
    row = rows[0]
    if row["status"] != "CAP23_ACTIVE":
        raise ValueError(row.get("reason") or row["status"])
    config["shadow_entry_admission"] = dict(
        occupancy=row["zuweisung"],
        selection_root=row["selection_root"],
        ranking_root=inputs["cap22_root"],
        universe_root=inputs["cap21_root"],
        selection_digest=row["selection_digest"],
    )
    assignment = read_ranked_run_slot_v1(config)
    admission = read_shadow_entry_admission_v1(config, assignment)
    admission.require_current_v1(time())
    path = source_root / "Shadowbindung" / session / "slot-gebunden.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    immutable_json_v1(path, config)
    check = inspect_ranked_shadow_entry_selection_v1(path, now=time())
    if check["blockers"] != ["SHADOW_ENTRY_CAP24_MISSING"]:
        raise ValueError(str(check["blockers"]))
    prepared = read(folder / "vorbereitung.json")
    if (prepared["sitzung"], prepared["instrument"], prepared["modus"]) != (
        session,
        assignment.instrument.venue_native_inst_id,
        "SHADOW",
    ):
        raise ValueError("SHADOW_PRODUCER_SCOPE_MISMATCH")
    producer = prepared["producer"]
    args = producer["arguments"]
    if args["--ranked-slot-config"] != str(folder / "slot.json"):
        raise ValueError("SHADOW_PRODUCER_SOURCE_MISMATCH")
    args["--ranked-slot-config"] = str(path)
    bound_producer = path.with_name("producer-gebunden.json")
    immutable_json_v1(bound_producer, producer)
    print(
        json.dumps(
            dict(
                slot=lane,
                session=session,
                profil=str(path),
                producer=str(bound_producer),
                auswahl_bis=admission.selection.valid_until,
                cap24="am ersten zugelassenen Entscheidungstick aus Originalportfolio und Markpreis",
                vorstart=check,
            ),
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slot-folder", required=True, type=Path)
    parser.add_argument("--selection-root", required=True, type=Path)
    args = parser.parse_args()
    prepare(args.slot_folder.resolve(strict=True), args.selection_root.resolve(strict=True))


if __name__ == "__main__":
    main()
