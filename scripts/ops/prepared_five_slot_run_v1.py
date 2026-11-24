"""Prepare the fixed staggered five-slot procedure offline; start only with a later bundle.

Preparation neither assigns T0 nor writes any session root. Fresh entry files
are consumed at each offset through their original owners, never relabelled.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import time

from scripts.ops.nonlive_gvef_companion_v1 import research_digest
from scripts.ops.run_btc_demo_learning_session_v1 import campaign_for_host_v1
from scripts.ops.run_btc_demo_bounded_host_v1 import prepare_btc_demo_host_v1
from scripts.ops.run_recurrent_offline_research_v1 import (
    ResearchCampaignV1,
    tick_research_campaign_v1,
)
from src.experiments.canonical_experiment_identity_v1 import inspect_code_provenance_v1
from src.experiments.canonical_research_prepared_execution_v1 import digest_v1
from src.ops.bounded_peaktrade_system_composition_v1.paper_episode_outcome_v1 import (
    closed_paper_episode_ids_v1,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    atomic_write_json,
)
from src.ops.ranked_slot_run_source_v1 import (
    read_ranked_run_slot_v1,
    read_paper_entry_admission_v1,
    read_shadow_entry_admission_v1,
)

REPO = Path(__file__).resolve().parents[2]
SLOTS = (
    (1, "UP-USDT-SWAP", "SHADOW", 0, 120),
    (2, "UP-USD_UM_XPERP-310919", "PAPER_EXCHANGE", 20, 120),
    (3, "BTC-USD_UM_XPERP-310328", "TESTNET", 40, 60),
    (4, "PIEVERSE-USDT-SWAP", "SHADOW", 60, 120),
    (5, "OL-USD_UM_XPERP-310912", "PAPER_EXCHANGE", 80, 60),
)
MODULES = {
    "SHADOW": "scripts.ops.run_i17_shadow_learning_companion_v1",
    "PAPER_EXCHANGE": "scripts.ops.run_zkp_lane1_paper_v1",
    "TESTNET": "scripts.ops.run_btc_demo_learning_session_v1",
}


def read(path):
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path:
        raise ValueError("FIVE_SLOT_CANONICAL_PATH_REQUIRED")
    return json.loads(path.read_bytes())


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def command(module, arguments, mode=None):
    result = [str(REPO / "scripts/pt"), "-m", module]
    if mode:
        result.append(mode)
    for name, value in arguments.items():
        result.append(name)
        if value is not None:
            result.append(str(value))
    return result


def prepare_v1(folder, *, now=None):
    folder = folder.resolve(strict=True)
    now = now or datetime.now(timezone.utc)
    code = inspect_code_provenance_v1(REPO)
    slots, hashes = [], {}

    def retain(path):
        path = Path(path)
        read(path) if path.suffix == ".json" else path.read_bytes()
        hashes[str(path)] = sha256(path.read_bytes()).hexdigest()

    for number, native, surface, offset, minutes in SLOTS:
        lane = folder / f"LANE_{number}"
        prepared = read(lane / "vorbereitung.json")
        producer = prepared["producer"]
        draft_path = lane / (
            "gvef-host-PR7418-entwurf.json" if number == 3 else "gvef-entwurf.json"
        )
        draft = read(draft_path)
        scope = draft["slot"]
        require(
            (
                prepared["slot"],
                prepared["instrument"],
                prepared["modus"],
                prepared["versatz_min"],
                prepared["laufzeit_min"],
                prepared["startzeit"],
            )
            == (number, native, surface, offset, minutes, None),
            "FIVE_SLOT_FIXED_PLAN_CHANGED",
        )
        require(producer and producer["module"] == MODULES[surface], "FIVE_SLOT_PRODUCER_UNBOUND")
        require(
            (
                scope["lane_id"],
                scope["surface"],
                scope["session_id"],
                scope["venue_native_id"],
                scope["starts_at"],
                scope["ends_at"],
            )
            == (f"LANE_{number}", surface, prepared["sitzung"], native, None, None),
            "FIVE_SLOT_CAMPAIGN_SCOPE_MISMATCH",
        )
        args = producer["arguments"]
        if number == 3:
            config_path = Path(args["--config"])
            config = read(config_path)
            require(config["repository_sha"] == code.git_sha, "FIVE_SLOT_DEMO_REVISION_CHANGED")
            host = prepare_btc_demo_host_v1(config)
            require(not host["source_blockers"], "FIVE_SLOT_DEMO_SOURCE_BLOCKED")
            require(args["--campaign-draft"] == str(draft_path), "FIVE_SLOT_DEMO_DRAFT_CHANGED")
            campaign = campaign_for_host_v1(config, draft, started_at=now)
            retain(config_path)
            retain(config["fixed_pin"]["instrument_source"])
            retain(config["entry_budget_policy_path"])
        else:
            config_path = Path(
                args["--ranked-slot-config"] if surface == "SHADOW" else args["--slot-config"]
            )
            # The producer template points at the future admission, but its
            # original assignment stays in the existing unarmed slot template.
            config = read(lane / "slot.json")
            original = read_ranked_run_slot_v1(config)
            require(
                (original.instrument.venue_native_inst_id, config["session_id"])
                == (native, prepared["sitzung"]),
                "FIVE_SLOT_ORIGINAL_ASSIGNMENT_CHANGED",
            )
            require(
                config_path == lane / "slot.json" or config_path.name == "slot-gebunden.json",
                "FIVE_SLOT_FRESH_ENTRY_PATH_REQUIRED",
            )
            args["--ranked-slot-config" if surface == "SHADOW" else "--slot-config"] = str(
                Path(draft["state"]).parent / "slot-gebunden.json"
            )
            scoped = {**scope, "starts_at": now, "ends_at": now + timedelta(minutes=minutes)}
            if surface == "PAPER_EXCHANGE":
                scoped["n5_selection_digest"] = original.selection.integrity_digest
                require(
                    int(args["--duration-seconds"]) == minutes * 60,
                    "FIVE_SLOT_PAPER_DURATION_CHANGED",
                )
                require(
                    Path(args["--run-root"]) == Path(draft["paper_runs"]) / config["session_id"],
                    "FIVE_SLOT_PAPER_SOURCE_CHANGED",
                )
            else:
                require(
                    args["--expected-repository-sha"] == code.git_sha,
                    "FIVE_SLOT_SHADOW_REVISION_CHANGED",
                )
                require(
                    Path(args["--companion-root"])
                    == Path(draft["shadow_follow_ups"]) / config["session_id"]
                    and Path(args["--evidence-root"])
                    == Path(draft["shadow_runs"]) / config["session_id"] / "evidence",
                    "FIVE_SLOT_SHADOW_SOURCE_CHANGED",
                )
                binding = read(args["--o4-instrument-binding"])
                require(
                    binding["n5_assignment"] == original.reference(), "FIVE_SLOT_SHADOW_O4_CHANGED"
                )
                retain(args["--o4-instrument-binding"])
                prereg = read(lane / "vorregistrierung-entwurf.json")
                require(
                    not prereg["armed"]
                    and not prereg["enabled"]
                    and prereg["fixture_non_authoritative"]
                    and prereg["planned_duration_seconds"] == minutes * 60
                    and prereg["earliest_start"] == prereg["expires_at"] == 0,
                    "FIVE_SLOT_DRAFT_MUST_REMAIN_UNARMED",
                )
                retain(lane / "vorregistrierung-entwurf.json")
            campaign = ResearchCampaignV1.model_validate({**draft, "slot": scoped})
            retain(lane / "slot.json")
        require(
            set(campaign.research_inputs) == {scope["instrument_id"]}
            and bool(campaign.research_inputs[scope["instrument_id"]]),
            "FIVE_SLOT_RESEARCH_REQUIRED",
        )
        input_digests = []
        for item in campaign.research_inputs[scope["instrument_id"]]:
            input_digests.append(
                research_digest(item, scope["instrument_id"], surface, now.timestamp())
            )
            for path in (item.template, item.bars, item.config):
                retain(path)
        for path in (lane / "vorbereitung.json", draft_path):
            retain(path)
        slots.append(
            dict(
                number=number,
                lane_id=f"LANE_{number}",
                session_id=prepared["sitzung"],
                native_id=native,
                surface=surface,
                offset_seconds=offset * 60,
                duration_seconds=minutes * 60,
                producer=producer,
                campaign_draft=str(draft_path),
                research_input_digests=input_digests,
                entry_input=str(Path(draft["state"]).parent / "authorization/start-inputs.json"),
                prepared=str(lane / "vorbereitung.json"),
            )
        )
    roots = [str(Path(read(s["campaign_draft"])["state"]).parent) for s in slots]
    require(
        len(set(roots)) == len(set(s["session_id"] for s in slots)) == 5,
        "FIVE_SLOT_SESSION_ISOLATION_REQUIRED",
    )
    result = dict(
        schema="prepared_five_slot_run.v1",
        authority="NONE",
        status="PREPARED_NO_START"
        if code.working_tree_status == "CLEAN"
        else "SOURCE_INTEGRATION_PENDING",
        code_status=code.working_tree_status,
        repository_sha=code.git_sha,
        checkout=str(REPO),
        t0=None,
        session_started=False,
        credentials_accessed=False,
        orders_sent=0,
        slots=slots,
        input_sha256=hashes,
        fresh_inputs=[
            "current Cap21/22/23 per entry, original fixed N5 occupancy retained",
            "Paper opening account, public USDC conversion and Cap24",
            "Shadow time-bound original preregistration, GO and confirmation; tick Cap24 and G17",
            "BTC original explicit start, existing signer, account and public data at runtime",
        ],
        follow_up="Shadow O4 waits for two final hourly bars after its decision; Paper closed simulated episodes; BTC confirmed first fill IMMEDIATE_POST_EVENT. GVEF follows each original handoff; economic BLOCKED stays BLOCKED.",
    )
    result["plan_digest"] = digest_v1(result)
    return result


def verify_input_files_v1(plan):
    for path, expected in plan.get("input_sha256", {}).items():
        require(
            sha256(Path(path).read_bytes()).hexdigest() == expected,
            "FIVE_SLOT_INPUT_CHANGED:" + path,
        )


def verify_plan_v1(plan, *, code):
    require(
        plan["plan_digest"] == digest_v1({k: v for k, v in plan.items() if k != "plan_digest"}),
        "FIVE_SLOT_PLAN_DIGEST_CHANGED",
    )
    require(
        code.git_sha == plan["repository_sha"] and code.working_tree_status == "CLEAN",
        "FIVE_SLOT_CLEAN_PREPARED_REVISION_REQUIRED",
    )
    require(
        len(plan["slots"]) == 5
        and all(
            (
                slot["number"],
                slot["native_id"],
                slot["surface"],
                slot["offset_seconds"],
                slot["duration_seconds"],
                slot["producer"]["module"],
            )
            == (n, native, surface, offset * 60, minutes * 60, MODULES[surface])
            for slot, (n, native, surface, offset, minutes) in zip(plan["slots"], SLOTS)
        ),
        "FIVE_SLOT_FIXED_PLAN_CHANGED",
    )
    verify_input_files_v1(plan)


def _run_command(argv, output):
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with output.open("xb") as stream:
        return subprocess.run(
            argv,
            cwd=REPO,
            env=dict(os.environ, GIT_WORK_TREE=str(REPO)),
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
        ).returncode


def admit_entry_v1(plan, slot, entry, *, now):
    require(
        (entry["plan_digest"], entry["lane_id"], entry["session_id"])
        == (plan["plan_digest"], slot["lane_id"], slot["session_id"]),
        "FIVE_SLOT_FOREIGN_ENTRY",
    )
    args = dict(slot["producer"]["arguments"])
    if slot["surface"] == "TESTNET":
        from src.ops.btc_demo_bounded_host_v1 import BtcDemoHostStartV1

        config = read(args["--config"])
        start = BtcDemoHostStartV1(**read(entry["operator_start"]))
        start.validate_v1(config=config, now_unix=now)
        args.update({"--run": None, "--operator-start": entry["operator_start"]})
        return args, None
    config_path = Path(entry["slot_config"])
    config = read(config_path)
    original = read_ranked_run_slot_v1(config)
    require(
        (config["lane"], config["session_id"], config["native_instrument_id"], config["surface"])
        == (slot["lane_id"], slot["session_id"], slot["native_id"], slot["surface"]),
        "FIVE_SLOT_ENTRY_SCOPE_CHANGED",
    )
    template_path = Path(slot["prepared"]).parent / "slot.json"
    template = read(template_path)
    require(
        all(config.get(k) == v for k, v in template.items()), "FIVE_SLOT_ORIGINAL_OCCUPANCY_CHANGED"
    )
    if slot["surface"] == "SHADOW":
        admission = read_shadow_entry_admission_v1(config, original)
        args["--ranked-slot-config"] = str(config_path)
    else:
        from scripts.ops.run_zkp_lane1_paper_v1 import (
            _read_cap24_binding,
            _verify_renewed_paper_cap24,
        )

        admission = read_paper_entry_admission_v1(config, original)
        cap = Path(config["paper_cap24"]["root"])
        bound = _read_cap24_binding(cap, entry_repository_sha=admission.selection.repository_sha)
        admission.require_binding_v1(bound)
        _verify_renewed_paper_cap24(config, cap, original, admission, bound)
        args.update({"--slot-config": str(config_path), "--card-cap24-evidence-root": str(cap)})
    admission.require_current_v1(now)
    require(
        admission.selection.repository_sha == plan["repository_sha"],
        "FIVE_SLOT_CURRENT_ENTRY_REVISION_REQUIRED",
    )
    return args, original


def run_slot_v1(plan, slot, *, wait_until, clock=time.time, pause=time.sleep, execute=_run_command):
    verify_input_files_v1(plan)
    while True:
        try:
            entry = read(slot["entry_input"])
            args, original = admit_entry_v1(plan, slot, entry, now=clock())
            break
        except (FileNotFoundError, ValueError, KeyError) as exc:
            if clock() >= wait_until:
                return dict(lane_id=slot["lane_id"], status="ENTRY_NOT_ADMITTED", reason=str(exc))
            pause(min(5, wait_until - clock()))
    draft = read(slot["campaign_draft"])
    state = Path(draft["state"]).parent
    if slot["surface"] == "SHADOW":
        start = datetime.fromtimestamp(clock(), timezone.utc)
        campaign = ResearchCampaignV1.model_validate(
            {
                **draft,
                "slot": {
                    **draft["slot"],
                    "starts_at": start,
                    "ends_at": start + timedelta(seconds=slot["duration_seconds"]),
                    "n5_selection_digest": original.selection.integrity_digest,
                },
            }
        )
        path = Path(args["--gvef-campaign"])
        require(not path.exists(), "FIVE_SLOT_CAMPAIGN_ALREADY_EXISTS")
        atomic_write_json(path=path, payload=campaign.model_dump(mode="json", exclude_none=True))
    rc = execute(
        command(slot["producer"]["module"], args, slot["producer"].get("mode")),
        state / "producer.log",
    )
    verify_input_files_v1(plan)
    research = None
    if slot["surface"] == "PAPER_EXCHANGE":
        archive = Path(args["--run-root"])
        window = read(archive / "window.json")
        require(
            window["duration_seconds"] == slot["duration_seconds"],
            "FIVE_SLOT_ORIGINAL_WINDOW_CHANGED",
        )
        start = datetime.fromtimestamp(window["started_at"], timezone.utc)
        count = len(closed_paper_episode_ids_v1(archive))
        campaign = ResearchCampaignV1.model_validate(
            {
                **draft,
                "jobs_per_tick": max(1, count),
                "slot": {
                    **draft["slot"],
                    "starts_at": start,
                    "ends_at": start + timedelta(seconds=window["duration_seconds"]),
                    "n5_selection_digest": original.selection.integrity_digest,
                },
            }
        )
        for path in (campaign.paper_runs, campaign.shadow_runs, campaign.shadow_follow_ups):
            path.mkdir(mode=0o700, parents=True, exist_ok=True)
        research = tick_research_campaign_v1(campaign, code=inspect_code_provenance_v1(REPO))
        atomic_write_json(path=state / "paper-learning-tail.json", payload=research)
    if slot["surface"] == "TESTNET":
        research = read(state / "btc-learning-tail.json")
        learning_ok = research["status"] in {"PROCESSED", "NO_CONFIRMED_ENTRY"}
    elif slot["surface"] == "SHADOW":
        research = read(Path(args["--companion-root"]) / "gvef/closeout.json")
        learning_ok = not any(
            row["status"] in {"BLOCKED", "MECHANISM_INCOMPLETE", "WAITING_FOR_RESEARCH_INPUT"}
            for row in research["jobs"]
        )
    else:
        learning_ok = not any(
            row["status"] in {"BLOCKED", "MECHANISM_INCOMPLETE", "WAITING_FOR_RESEARCH_INPUT"}
            for row in research["jobs"]
        )
    return dict(
        lane_id=slot["lane_id"],
        status="COMPLETED" if rc == 0 and learning_ok else "FOLLOW_UP_OR_PRODUCER_OPEN",
        producer_exit_code=rc,
        research=research,
    )


def run_five_slots_v1(plan, bundle, *, clock=time.time, pause=time.sleep, run_slot=run_slot_v1):
    verify_plan_v1(plan, code=inspect_code_provenance_v1(REPO))
    require(
        bundle["action"] == "START_PREPARED_FIVE_SLOT_RUN"
        and bundle["plan_digest"] == plan["plan_digest"],
        "FIVE_SLOT_EXPLICIT_BOUND_START_REQUIRED",
    )
    t0 = datetime.fromisoformat(bundle["t0"].replace("Z", "+00:00"))
    expires = datetime.fromisoformat(bundle["expires_at_utc"].replace("Z", "+00:00"))
    until = datetime.fromisoformat(bundle["admission_wait_until_utc"].replace("Z", "+00:00"))
    require(
        all(t.utcoffset() is not None for t in (t0, expires, until))
        and clock() <= t0.timestamp() < expires.timestamp()
        and t0.timestamp() + 4800 < until.timestamp(),
        "FIVE_SLOT_FRESH_START_WINDOW_REQUIRED",
    )

    def drive(slot):
        scheduled = t0.timestamp() + slot["offset_seconds"]
        while clock() < scheduled:
            pause(min(5, scheduled - clock()))
        try:
            result = run_slot(plan, slot, wait_until=until.timestamp())
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
            result = dict(lane_id=slot["lane_id"], status="FAILED", reason=str(exc))
        return {**result, "scheduled_at_unix": scheduled}

    # Process preparation never enters this branch. These five workers are
    # bounded session sequencing only, with each original owner still gating.
    with ThreadPoolExecutor(max_workers=5, thread_name_prefix="five-slot") as worker:
        futures = [worker.submit(drive, slot) for slot in plan["slots"]]
        results = [future.result() for future in futures]
    return dict(authority="NONE", slots=results)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation-folder", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--start-bundle", type=Path)
    args = parser.parse_args(argv)
    if args.run:
        if not args.plan or not args.start_bundle or args.preparation_folder:
            parser.error("--run requires --plan and --start-bundle")
        result = run_five_slots_v1(read(args.plan), read(args.start_bundle))
    else:
        if not args.preparation_folder or args.plan or args.start_bundle:
            parser.error("offline preparation requires only --preparation-folder")
        result = prepare_v1(args.preparation_folder)
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
    return 2 if args.run and any(slot["status"] != "COMPLETED" for slot in result["slots"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
