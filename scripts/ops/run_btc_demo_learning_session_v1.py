"""Prepare offline, or explicitly run the original bounded host and its DDO/GVEF tail."""

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import time

from scripts.ops.nonlive_gvef_companion_v1 import research_digest
from scripts.ops.run_btc_demo_bounded_host_v1 import (
    BtcDemoHostStartV1,
    BtcDemoRuntimeV1,
    macos_demo_signer_v1,
    prepare_btc_demo_host_v1,
    run_btc_demo_bounded_host_v1,
)
from scripts.ops.run_recurrent_offline_research_v1 import (
    ResearchCampaignV1,
    tick_research_campaign_v1,
)
from src.experiments.canonical_experiment_identity_v1 import inspect_code_provenance_v1
from src.ops.btc_demo_session_control_v1 import utc_v1
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    atomic_write_json,
)

REPO = Path(__file__).resolve().parents[2]


def campaign_for_host_v1(config, draft, *, started_at):
    """Use the registered one-hour trading window, not the two-hour draft window."""
    slot = draft["slot"]
    if (
        (
            slot["lane_id"],
            slot["surface"],
            slot["session_id"],
            slot["instrument_id"],
            slot["venue_native_id"],
        )
        != (
            "LANE_3",
            "TESTNET",
            config["session_id"],
            config["fixed_pin"]["canonical_instrument_id"],
            config["fixed_pin"]["native_instrument_id"],
        )
        or draft.get("testnet_root") != config["testnet_root"]
        or draft.get("testnet_source") != "BOUNDED_HOST_ENTRY"
        or (slot["starts_at"], slot["ends_at"]) != (None, None)
    ):
        raise ValueError("BTC_DDO_GVEF_ORIGINAL_SESSION_REQUIRED")
    campaign = ResearchCampaignV1.model_validate(
        {
            **draft,
            "slot": {**slot, "starts_at": started_at, "ends_at": started_at + timedelta(hours=1)},
        }
    )
    root = Path(config["testnet_root"])
    sources = (campaign.paper_runs, campaign.shadow_runs, campaign.shadow_follow_ups, root)
    if any(not p.is_absolute() or p.resolve() != p for p in (*sources, campaign.state)) or any(
        campaign.state.is_relative_to(p) or p.is_relative_to(campaign.state)
        for p in (*sources, REPO)
    ):
        raise ValueError("BTC_DDO_GVEF_SEPARATE_ORIGINAL_ROOTS_REQUIRED")
    for selected in campaign.research_inputs[slot["instrument_id"]]:
        research_digest(selected, slot["instrument_id"], "TESTNET", started_at.timestamp())
    if not campaign.research_inputs[slot["instrument_id"]]:
        raise ValueError("BTC_DDO_GVEF_RESEARCH_INPUT_REQUIRED")
    return campaign


def finish_btc_learning_v1(config, draft, registration, *, code, now=None, expected_inputs=None):
    """Read originals through the existing consumer; never change host custody or clocks."""
    registration.validate_v1()
    if (registration.session_id, registration.instrument_id, registration.native_id) != (
        config["session_id"],
        config["fixed_pin"]["canonical_instrument_id"],
        config["fixed_pin"]["native_instrument_id"],
    ):
        raise ValueError("BTC_DDO_GVEF_REGISTRATION_MISMATCH")
    campaign = campaign_for_host_v1(config, draft, started_at=utc_v1(registration.started_at_utc))
    inputs = [
        research_digest(
            selected, campaign.slot.instrument_id, "TESTNET", campaign.slot.starts_at.timestamp()
        )
        for selected in campaign.research_inputs[campaign.slot.instrument_id]
    ]
    prior_path = campaign.state.parent / "btc-learning-tail.json"
    if prior_path.is_file():
        prior = json.loads(prior_path.read_bytes())
        if (
            prior["registration_digest"] != registration.digest_v1()
            or prior["research_input_digests"] != inputs
        ):
            raise ValueError("BTC_DDO_GVEF_ORIGINAL_INPUT_CHANGED")
    if expected_inputs is not None and inputs != expected_inputs:
        raise ValueError("BTC_DDO_GVEF_ORIGINAL_INPUT_CHANGED")
    # One attempt for every retained original, not just jobs_per_tick=1.
    count = int((Path(config["testnet_root"]) / "original-entry-g17-c1.json").is_file())
    campaign = campaign.model_copy(update={"jobs_per_tick": max(1, count)})
    for path in (campaign.paper_runs, campaign.shadow_runs, campaign.shadow_follow_ups):
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    result = tick_research_campaign_v1(campaign, code=code, now=now)
    receipt = dict(
        schema="btc_demo_bounded_learning_tail.v1",
        authority="NONE",
        registration_digest=registration.digest_v1(),
        research_input_digests=inputs,
        original_first_fill_count=count,
        campaign=campaign.model_dump(mode="json", exclude_none=True),
        research=result,
        status="NO_CONFIRMED_ENTRY"
        if count == 0
        else "PROCESSED"
        if not any(
            row["status"] in {"BLOCKED", "MECHANISM_INCOMPLETE", "WAITING_FOR_RESEARCH_INPUT"}
            for row in result["jobs"]
        )
        and len(list((campaign.state / "sources").glob("*.json"))) == count
        else "FOLLOW_UP_OPEN",
    )
    atomic_write_json(path=campaign.state.parent / "btc-learning-tail.json", payload=receipt)
    return receipt


def run_session_v1(config, draft, start, *, runtime, code, clock=time.time, pause=time.sleep):
    initial = campaign_for_host_v1(
        config, draft, started_at=datetime.fromtimestamp(clock(), timezone.utc)
    )
    inputs = [
        research_digest(
            selected, initial.slot.instrument_id, "TESTNET", initial.slot.starts_at.timestamp()
        )
        for selected in initial.research_inputs[initial.slot.instrument_id]
    ]
    # A research failure is reported separately after the bounded host has
    # completed its close/reconciliation attempt; it cannot suppress that attempt.
    host = run_btc_demo_bounded_host_v1(
        runtime=runtime, operator_start=start, clock=clock, sleep=pause
    )
    try:
        learning = finish_btc_learning_v1(
            config, draft, runtime.registration, code=code, expected_inputs=inputs
        )
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        learning = dict(status="FOLLOW_UP_OPEN", reason=type(exc).__name__ + ":" + str(exc))
    return dict(host=host, learning=learning, authority="NONE")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--campaign-draft", required=True, type=Path)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--operator-start", type=Path)
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_bytes())
    draft = json.loads(args.campaign_draft.read_bytes())
    prepared = prepare_btc_demo_host_v1(config, require_integrated_source=args.run)
    campaign_for_host_v1(config, draft, started_at=datetime.now(timezone.utc))
    if not args.run:
        if args.operator_start:
            parser.error("--operator-start requires --run")
        print(json.dumps({**prepared, "learning_tail": "ORIGINAL_FIRST_FILL_DDO_AND_GVEF"}))
        return 0
    if not args.operator_start:
        parser.error("--run requires --operator-start")
    start = BtcDemoHostStartV1(**json.loads(args.operator_start.read_bytes()))
    if not (
        Path(config["testnet_root"]) / "testnet-state/budget-owner/owner/reservations.sqlite3"
    ).is_file():
        start.validate_v1(config=config, now_unix=time.time())
    code = inspect_code_provenance_v1(REPO)
    if code.working_tree_status != "CLEAN" or code.git_sha != config["repository_sha"]:
        raise ValueError("BTC_DDO_GVEF_CLEAN_PREPARED_REVISION_REQUIRED")
    with macos_demo_signer_v1(config) as handle:
        runtime = BtcDemoRuntimeV1(config=config, signing_handle=handle)
        try:
            result = run_session_v1(config, draft, start, runtime=runtime, code=code)
        finally:
            runtime.close()
    print(json.dumps(result, sort_keys=True))
    return (
        0
        if result["host"]["status"] in {"CONFIRMED_CLOSED", "CONFIRMED_NO_ENTRY"}
        and result["learning"]["status"] != "FOLLOW_UP_OPEN"
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
