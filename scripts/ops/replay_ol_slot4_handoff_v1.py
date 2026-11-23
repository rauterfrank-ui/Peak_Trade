"""Offline-Prüfung des Entwurfs für Slot 4. Ausgabe ausschließlich auf stdout."""

import argparse
import fcntl
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ops.current_mf_member_to_pinned_cap23_n1_adapter_v1.adapter_v1 import (
    build_governed_cap23_pin_v1,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    load_completed_fixed_rank_publication_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    apply_isolated_lane_topology_v1,
    isolated_lane_topology_from_dict,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    eligible_prefix_from_cap22_snapshot,
    membership_context_artifact_from_dict,
    validate_membership_context_artifact_v1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    load_and_validate_ranking_snapshot_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import PortfolioTruthSnapshotV1
from src.ops.ranked_slot_run_source_v1 import read_ranked_run_slot_v1
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    prepare_lane_selection_v1,
    commit_prepared_lane_selection_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1 import (
    run_single_selected_future_runtime_binding_gate_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
)


def read(path):
    return json.loads(path.read_bytes())


def fingerprint(path):
    return dict(path=str(path), sha256=sha256(path.read_bytes()).hexdigest())


def epoch(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def protect(root):
    def check(event, args):
        if event in {
            "socket.connect",
            "socket.getaddrinfo",
            "socket.sendto",
            "urllib.Request",
            "subprocess.Popen",
        }:
            raise PermissionError("Nur lokale Quellen")
        if event == "open":
            if not args[2] & (os.O_CREAT | os.O_RDWR | os.O_WRONLY | os.O_TRUNC):
                return
            paths = args[:1]
        elif event in {
            "os.mkdir",
            "os.rename",
            "os.remove",
            "os.rmdir",
            "os.chmod",
            "os.utime",
            "os.link",
            "os.symlink",
        }:
            paths = args[:2] if event in {"os.rename", "os.link", "os.symlink"} else args[:1]
            # TemporaryDirectory entfernt seine eigenen Dateien auch relativ zu einem dir_fd.
            if (
                event in {"os.remove", "os.rmdir"}
                and len(args) > 1
                and isinstance(args[1], int)
                and args[1] >= 0
            ):
                parent = fcntl.fcntl(args[1], fcntl.F_GETPATH, bytes(1024)).split(b"\0", 1)[0]
                paths = (Path(os.fsdecode(parent)) / os.fsdecode(args[0]),)
        else:
            return
        for path in paths:
            if isinstance(path, int):
                path = fcntl.fcntl(path, fcntl.F_GETPATH, bytes(1024)).split(b"\0", 1)[0]
            if not isinstance(path, (str, bytes, os.PathLike)) or not (
                Path(os.fsdecode(path)).resolve() == root
                or Path(os.fsdecode(path)).resolve().is_relative_to(root)
            ):
                raise PermissionError(f"Schreibzugriff außerhalb der Testkopie: {event} {path}")

    sys.addaudithook(check)


def evaluate(draft_path, cfgpath, temp):
    cfg = read(cfgpath)
    draft = read(draft_path)
    profile = draft["vorgeschlagene_profilfelder"]
    src = cfg["n5_source"]
    base = Path(src["topology_root"])
    original = read_ranked_run_slot_v1(cfg)
    current = original.selection
    lane = original.lane_id
    target = profile["canonical_instrument_id"]
    native = profile["native_instrument_id"]
    require(
        (
            lane,
            profile["lane"],
            profile["surface"],
            profile["authority"],
            native,
            current.venue_native_id,
        )
        == ("LANE_4", "LANE_4", "SHADOW", "NONE", "OL-USDT-SWAP", "PIEVERSE-USDT-SWAP"),
        "Profil oder Vorgänger geändert",
    )
    require(
        original.reference()["selection_digest"] == draft["vorherige_bindung"]["selection_digest"],
        "Vorgänger-Digest geändert",
    )
    require(
        original.transition_id == draft["vorherige_bindung"]["transition_id"],
        "N5-Vorgänger geändert",
    )
    limit = Decimal(profile["shadow_entry_cost_limit_usdc"])
    policy = load_slot_entry_budget_v1(
        Path.cwd() / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V5.json"
    )
    require(
        limit.is_finite()
        and 0 < limit <= 10
        and limit <= policy.per_entry_notional_limit
        and policy.currency == "USDC",
        "Falsches Einstiegslimit",
    )
    rdir = Path(src["ranking_root"])
    udir = Path(src["universe_root"])
    rank = load_and_validate_ranking_snapshot_v1(
        rdir, expected_repository_sha=src["repository_sha"]
    )
    require(rank.ok, "Cap22-Integrität")
    snapshot = rank.snapshot.to_dict()
    receipt = load_completed_fixed_rank_publication_v1(base)
    topology = isolated_lane_topology_from_dict(receipt["topology"])
    membership_path = base / "membership" / (topology.membership_instance_id + ".json")
    membership = validate_membership_context_artifact_v1(
        membership_context_artifact_from_dict(read(membership_path))
    )
    prefix = eligible_prefix_from_cap22_snapshot(snapshot)
    rows = snapshot["ranked_candidates"]
    identities = {r["canonical_instrument_id"]: r["rank"] for r in rows}
    require(
        tuple(membership.ordered_instrument_ids) == prefix
        and len(prefix) == 5
        and target not in prefix
        and identities[target] == 6,
        "Unerwartete Ursprungsmitgliedschaft",
    )
    require(
        topology.instrument_to_lane()[current.instrument_id] == lane and current.selected_rank == 4,
        "Unerwartete Belegung",
    )
    try:
        apply_isolated_lane_topology_v1(
            membership=membership,
            ranking_snapshot=snapshot,
            topology_state_root_base=base,
            prior_topology=topology,
        )
    except ValueError as exc:
        freeze = str(exc)
        require(
            "LANE_FIXED_BINDINGS_ALREADY_PUBLISHED" in freeze,
            "Unerwartete Topologieablehnung: " + freeze,
        )
    else:
        raise ValueError("Fixierte Topologie wurde ersetzt")

    # Alle Cap23-Writer und Cap24-Consumer arbeiten nur an wegwerfbaren Kopien.
    before = temp / "vorher" / "LANE_4"
    before.mkdir(parents=True)
    for name in (
        "MANIFEST.sha256",
        "single_selected_future_selection_v1.json",
        "single_selected_future_selection_evidence_v1.json",
    ):
        shutil.copyfile(base / lane / name, before / name)
    empty = temp / "kontrolle" / "LANE_4"
    empty.mkdir(parents=True)
    check_time = epoch(current.selected_at_wall_time) + 1

    def assess(root, expected, opened=None, publish_control=False):
        pin = build_governed_cap23_pin_v1(
            canonical_instrument_id=target, ranking_snapshot=snapshot, lane_state_root=root
        )
        with prepare_lane_selection_v1(
            state_root=root,
            ranking_snapshot=snapshot,
            repository_sha=src["repository_sha"],
            producer_observed_at_unix=check_time,
            governed_pin=pin,
            expected_previous_instrument=expected,
            open_position_instrument_id=opened,
        ) as prepared:
            selected = (
                commit_prepared_lane_selection_v1(prepared)
                if publish_control
                else prepared.produced.selection
            )
            return dict(
                instrument=selected.venue_native_id,
                rank=selected.selected_rank,
                state=selected.state,
                previous_selection_id=selected.previous_selection_id,
                proposed_replacement=selected.replacement_venue_native_id,
                reasons=list(selected.reason_codes),
                selection_id=selected.selection_id,
                digest=selected.integrity_digest,
            )

    flat = assess(before, current.instrument_id)
    opened = assess(before, current.instrument_id, current.instrument_id)
    control = assess(empty, None, publish_control=True)
    require(
        flat["instrument"] == current.venue_native_id
        and "HYSTERESIS_BLOCKS_CHURN" in str(flat["reasons"]),
        "OL wurde unerwartet angenommen",
    )
    require(
        opened["state"] == "REPLACEMENT_PENDING"
        and opened["instrument"] == current.venue_native_id,
        "Offene Position verloren",
    )
    require(
        control["instrument"] == native
        and control["rank"] == 6
        and not control["previous_selection_id"],
        "Kontrollannahme abweichend",
    )
    require(opened["proposed_replacement"] == native, "Falscher vorgemerkter Ersatz")
    acqfile = base.parent / "universe-acquisition-2.json"
    (rawmark,) = [v for v in read(acqfile)["mark_price_payload"]["data"] if v["instId"] == native]

    def gate(name, root, digest, now):
        result = run_single_selected_future_runtime_binding_gate_v1(
            selection_state_root=root,
            ranking_state_root=rdir,
            universe_state_root=udir,
            repository_sha=src["repository_sha"],
            session_id="offline-kontrolle-" + name,
            now_unix=now,
            reconciliation_state_root=temp / "recon" / name,
            observed_portfolio=PortfolioTruthSnapshotV1(
                positions=(),
                event_time_unix=now,
                wall_time_unix=now,
                source_id="analytical_execution_state",
            ),
            expected_selection_integrity_digest=digest,
            mark_price_by_native_id={native: rawmark["markPx"]},
        )
        return dict(
            ok=result.ok,
            new_alpha_allowed=result.new_alpha_allowed,
            hard_stop=result.hard_stop,
            blockers=list(result.blockers),
            bound=result.bound.to_dict() if result.bound else None,
        )

    # Vergleich an derselben historischen Auswahlzeit, ohne Handelsentscheidung.
    foreign = gate("fremder-digest", before, control["digest"], check_time)
    admitted = gate("isolierter-kaltstart", empty, control["digest"], check_time)
    expired = gate("fenster-abgelaufen", empty, control["digest"], epoch(current.valid_until) + 60)
    require(
        not foreign["new_alpha_allowed"] and not expired["new_alpha_allowed"],
        "Cap24-Negativkontrolle",
    )
    require(
        admitted["ok"]
        and admitted["new_alpha_allowed"]
        and admitted["bound"]["venue_native_id"] == native
        and admitted["bound"]["selection_integrity_digest"] == control["digest"],
        "Cap24-Kontrollbindung",
    )
    require(
        admitted["bound"]["ranking_snapshot_id"] == snapshot["ranking_snapshot_id"]
        and admitted["bound"]["ranking_integrity_digest"] == snapshot["integrity_digest"]
        and admitted["bound"]["universe_snapshot_id"] == snapshot["universe_snapshot_id"]
        and admitted["bound"]["instrument_id"] == target
        and admitted["bound"]["selection_id"] == control["selection_id"],
        "Inkonsistente Cap24-Kontrollbindung",
    )
    return dict(
        status="BLOCKIERT_KEINE_N5_NACHFOLGEBINDUNG",
        aktiv=False,
        authority="NONE",
        origin=original.reference(),
        cap22=dict(
            id=snapshot["ranking_snapshot_id"],
            digest=snapshot["integrity_digest"],
            market_time=snapshot["event_time"],
            rank_ol=identities[target],
            rank_pieverse=identities[current.instrument_id],
            membership_ranks=[identities[x] for x in prefix],
            published_topology=freeze,
        ),
        cap23_mit_originalem_vorgaenger=dict(flat_kontrolle=flat, offene_position_kontrolle=opened),
        cap24_kontrollen=dict(
            fremder_digest=foreign,
            isolierter_kaltstart_cap23=control,
            isolierter_kaltstart_cap24=admitted,
            abgelaufene_auswahl=expired,
            historische_pruefzeit_utc=datetime.fromtimestamp(check_time, timezone.utc).isoformat(),
            einordnung="Wegwerfkopien, kontrollierter Portfoliozustand und historische Preise. Die positive Kontrolle beginnt ohne Vorgänger und belegt ausschließlich den Cap23/Cap24-Datenvertrag für OL auf Rang 6.",
        ),
        uebergabe=dict(
            profilfelder=profile,
            originalrang=6,
            grenze_einschliesslich_kosten_usdc=str(limit),
            gebuchte_menge=None,
            owner_zuordnung={
                "N5": "Geprüfte Mitgliedschaft und gezielte Nachfolge genau für Slot 4",
                "Cap23": "Wirksame Folgeauswahl mit echtem Vorgänger, Rang und Gültigkeitszeit",
                "Cap24": "Binden der geprüften Auswahl samt Reconciliation; keine Berechnung oder Reservierung des Budgets",
                "Risk Sizing und Slot-Budget-Owner": "Erst nach bestätigter Entscheidung native Kontrakte berechnen und Gesamtgegenwert mit Kosten gegen das Profil-Limit prüfen",
            },
            n5_nachfolger_transition=None,
            cap23_nachfolger_selection_id=None,
            cap23_nachfolger_digest=None,
            cap24_nachfolger_binding=None,
            erforderliche_pruefungen=[
                "Für einen finanziell begründeten Ersatz braucht die Mitgliedschaft eine slotbezogene Zulassungsregel: belegte Undurchführbarkeit des PIEVERSE-Mindestloses und belegte Durchführbarkeit des OL-Mindestloses mit beiden Handelsseiten, Finanzierung und Umrechnung zum selben Entscheidungsstand. Aus dem original geordneten Kandidatenfeld den ersten passenden, für diesen Slot freien Swap bestimmen. Den Cap22-Originalrang beider Instrumente erhalten. Dies ist ein fachlicher Vorschlag, keine vorhandene Ersatzfreigabe.",
                "Slotbelegung 1, 2 und 5 und die Reservierung des externen Slots 3 bewahren. Den Ersatz an Slot 4 adressieren. Freie-Slot-Verteilung allein würde Slot 3 vor Slot 4 wählen.",
                "Die bisherige Top-5-Mitgliedschaft und unveränderliche Erstpublikation, der Profilleser und die Archivverifikation müssen einen eigenständig belegten Nachfolger mit Rang 6 auf Slot 4 unterscheiden können. Die Erstpublikation selbst bleibt historisch unverändert.",
                "Den echten PIEVERSE-Vorgänger, aktuelle Portfolio-/Custody-Wahrheit und die zuständige Rotationsentscheidung erhalten. Eine neue Cap23-Regel müsste eine nachgewiesene Unzulässigkeit des bisherigen Instruments am Slot abbilden. Der bestehende reine Rangvergleich bremst den Wechsel 4 auf 6. Cap23 muss OL als aktive Folgeauswahl ausweisen.",
                "Cap24 erhält den OL-Auswahl-Digest, das passende Cap21/22-Paar, eine gültige Auswahlzeit, Session und beobachtetes Portfolio für Reconciliation. Die geprüfte Rückgabe muss exakt OL binden.",
                "Im Shadow-Profil maximal 10 USDC einschließlich modellierter Eröffnungs-, Schließungs- und nächster Fundingkosten. Mengen werden erst downstream durch Risk Sizing und Budget-Owner auf Basis zeitlich zulässiger Originaldaten gebunden.",
            ],
        ),
        quellen=[
            fingerprint(f)
            for f in (
                draft_path,
                cfgpath,
                membership_path,
                rdir / "productive_futures_ranking_snapshot_v1.json",
                udir / "governed_futures_universe_snapshot_v1.json",
                base / "durable_lane_assignment_v1" / "selection_publication_completed_v1.json",
                acqfile,
            )
        ],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slot-config", type=Path, required=True)
    parser.add_argument(
        "--draft",
        type=Path,
        default=Path(__file__).resolve().parents[2]
        / "docs/ops/evidence/UP_PAPER_SHADOW_PREPARATION_20261123.json",
    )
    args = parser.parse_args()
    draft = args.draft.resolve()
    with TemporaryDirectory(prefix="peaktrade-n5-cap23-cap24-") as folder:
        work = Path(folder).resolve()
        protect(work)
        result = evaluate(draft, args.slot_config.resolve(), work)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
