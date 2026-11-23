"""Opt-in I17 Shadow runner with a bounded O4-to-DDO follow-up."""

from __future__ import annotations

import argparse
from datetime import timedelta
from hashlib import sha256
from http.client import HTTPException
import json
import os
from pathlib import Path
import re
from time import sleep, time

from scripts.ops.capture_offline_learning_mark_window_v1 import capture_public_mark_window_v1
from scripts.ops.run_integrated_paper_shadow_observation_wallclock_session_v1 import (
    _shadow_outcome_receipt,
    shadow_o4_window_start_v1,
)
from scripts.ops.run_integrated_paper_shadow_productive_authorization_issuance_and_real_network_v1 import (
    _load_token,
)
from scripts.ops.shadow_ddo_learning_handoff_v1 import shadow_ddo_learning_handoff_v1
from src.experiments.canonical_research_prepared_execution_v1 import digest_v1, publish_v1, read_v1
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    strict_json_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    durable_bytes_v1,
    exclusive_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (
    verify_wallclock_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.constants_v1 import (
    CANONICAL_PRODUCTIVE_DURATION_SECONDS,
    REAL_NETWORK_ENV,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    SOPH_I17,
    require_i17_shadow_instrument_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_run_entrypoint_v1 import (
    run_productive_wallclock_session_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    load_operator_go_contract_dict_v1,
    parse_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    load_preregistration_contract_dict_v1,
    parse_preregistration_contract_v1,
)
from src.research.offline_recorded_mark_horizon_source_v1 import (
    recorded_mark_price_unit_v1,
    utc_seconds,
)

REPO = Path(__file__).resolve().parents[2]
_HOURS = 2
_POLL_SECONDS = 15
_MAX_END_AGE_SECONDS = 600
_PROFILE = "i17_shadow_learning_companion.v1"


def _isolated(path: Path) -> Path:
    if (
        not path.is_absolute()
        or path != path.resolve()
        or path.is_relative_to(REPO)
        or path.is_relative_to(Path.home() / ".local/state/peak_trade/deployments")
    ):
        raise ValueError("I17_COMPANION_ISOLATED_PATH_REQUIRED")
    return path


def _source_roots(root, evidence):
    _isolated(root)
    _isolated(evidence)
    if root.is_relative_to(evidence) or evidence.is_relative_to(root):
        raise ValueError("I17_COMPANION_SHADOW_AND_LEARNING_ROOTS_MUST_BE_SEPARATE")


def _load_prereg(path):
    return parse_preregistration_contract_v1(load_preregistration_contract_dict_v1(path))


def _instrument_binding(data, *, instrument):
    binding = strict_json_v1(data)
    if not isinstance(binding, dict):
        raise ValueError("I17_COMPANION_O4_INSTRUMENT_BINDING_REQUIRED")
    recorded_mark_price_unit_v1(
        instrument_binding=binding,
        canonical_instrument_id=instrument.canonical_id,
        native_instrument_id=instrument.native_id,
    )
    return binding


def prepare_companion_v1(*, root, evidence, prereg, binding_path):
    """Pin the future observation and keep its follow-up outside the source archive."""
    _source_roots(root, evidence)
    instrument = require_i17_shadow_instrument_v1(prereg.instrument_allowlist)
    if prereg.planned_duration_seconds != CANONICAL_PRODUCTIVE_DURATION_SECONDS or not re.fullmatch(
        r"[0-9a-f]{40}", prereg.expected_repository_sha
    ):
        raise ValueError("I17_COMPANION_CANONICAL_PREREGISTRATION_REQUIRED")
    data = binding_path.read_bytes()
    _instrument_binding(data, instrument=instrument)
    root.mkdir(mode=0o700)
    durable_bytes_v1(root / "instrument-binding.json", data)
    publish_v1(
        root / "companion.json",
        {
            "schema": _PROFILE,
            "authority": "NONE",
            "evidence_root": str(evidence),
            "session_id": prereg.session_id,
            "repository_sha": prereg.expected_repository_sha,
            "preregistration_digest": digest_v1(prereg.to_dict()),
            "fixture_non_authoritative": prereg.fixture_non_authoritative,
            "instrument_binding_sha256": sha256(data).hexdigest(),
        },
    )


def _verified_plan(root, profile):
    evidence = Path(profile["evidence_root"])
    _source_roots(root, evidence)
    verification = verify_wallclock_evidence_bundle_v1(
        evidence_root=evidence, select_first_typed_shadow_decision=True
    )
    selected = verification.selected_shadow_decision
    if not verification.typed_ddo_requirement_met or selected is None:
        raise ValueError("I17_COMPANION_COMPLETE_TYPED_SHADOW_EVIDENCE_REQUIRED")
    if (
        selected["session_id"] != profile["session_id"]
        or selected["repository_sha"] != profile["repository_sha"]
    ):
        raise ValueError("I17_COMPANION_ORIGINAL_SESSION_MISMATCH")

    manifest = (evidence / "evidence_manifest.sha256").read_bytes()
    if sha256(manifest).hexdigest() != selected["shadow_manifest_sha256"]:
        raise ValueError("I17_COMPANION_SHADOW_MANIFEST_CHANGED")
    pins = {
        name: digest
        for digest, name in (line.split("  ", 1) for line in manifest.decode().splitlines() if line)
    }

    def pinned(name):
        path = evidence / name
        raw = path.read_bytes()
        if path.is_symlink() or sha256(raw).hexdigest() != pins.get(name):
            raise ValueError(f"I17_COMPANION_SOURCE_UNPROVEN:{name}")
        return strict_json_v1(raw)

    prereg = parse_preregistration_contract_v1(pinned("prereg.json"))
    instrument = require_i17_shadow_instrument_v1(prereg.instrument_allowlist)
    if (
        digest_v1(prereg.to_dict()) != profile["preregistration_digest"]
        or prereg.fixture_non_authoritative is not profile["fixture_non_authoritative"]
    ):
        raise ValueError("I17_COMPANION_PREREGISTRATION_MISMATCH")
    if (
        selected["canonical_instrument_id"] != instrument.canonical_id
        or selected["venue_instrument_id"] != instrument.native_id
        or selected.get("lane_id") != instrument.lane_id
    ):
        raise ValueError("I17_COMPANION_ORIGINAL_SESSION_MISMATCH")
    if not profile["fixture_non_authoritative"]:
        config = pinned("config_snapshot.json")
        if (
            config.get("schema") != "productive_wallclock_runtime_v1"
            or config.get("use_real_network") is not True
        ):
            raise ValueError("I17_COMPANION_RECORDED_PUBLIC_SHADOW_REQUIRED")
    binding_path = root / "instrument-binding.json"
    data = binding_path.read_bytes()
    if (
        binding_path.is_symlink()
        or sha256(data).hexdigest() != profile["instrument_binding_sha256"]
    ):
        raise ValueError("I17_COMPANION_INSTRUMENT_BINDING_CHANGED")
    if (
        _instrument_binding(data, instrument=instrument)["mapping_digest"]
        != selected["mapping_digest"]
    ):
        raise ValueError("I17_COMPANION_SHADOW_O4_MAPPING_MISMATCH")

    start = shadow_o4_window_start_v1(selected["decision_event_time_utc"])
    plan = {
        "authority": "NONE",
        "profile_digest": digest_v1(profile),
        "shadow_decision": selected,
        "n_bars": _HOURS,
        "window_start_utc": start.isoformat() + "Z",
        "window_end_utc": (start + timedelta(hours=_HOURS)).isoformat() + "Z",
    }
    publish_v1(root / "window-plan.json", plan)
    return evidence, plan


def _capture_o4(root, profile, plan, *, clock, pause, capture):
    archive = root / "o4"
    if archive.is_symlink():
        raise ValueError("I17_COMPANION_O4_ARCHIVE_SYMLINK_FORBIDDEN")
    end = utc_seconds(plan["window_end_utc"])
    deadline = end + _MAX_END_AGE_SECONDS
    while not archive.exists():
        remaining = end + _POLL_SECONDS - clock()
        if remaining <= 0:
            break
        pause(min(_POLL_SECONDS, remaining))

    latest_error = None
    while archive.exists() or clock() < deadline:
        existing = archive.exists()
        try:
            return capture(
                output=archive,
                start_utc=plan["window_start_utc"],
                hours=plan["n_bars"],
                binding_path=root / "instrument-binding.json",
                binding_sha256=profile["instrument_binding_sha256"],
                repository_sha=profile["repository_sha"],
            )
        except (OSError, HTTPException, ValueError) as exc:
            transient = isinstance(exc, (OSError, HTTPException)) or (
                str(exc)
                in {
                    "UNFINALIZED_SOURCE_MINUTE",
                    "INCOMPLETE_ORIGINAL_MINUTE_COVERAGE",
                    "PUBLIC_MARK_HTTP_429",
                }
                or re.fullmatch(r"PUBLIC_MARK_HTTP_5\d\d", str(exc))
            )
            if existing or not transient:
                raise
            latest_error = exc
            remaining = deadline - clock()
            if remaining > 0:
                pause(min(_POLL_SECONDS, remaining))
    raise ValueError("I17_COMPANION_O4_CAPTURE_DEADLINE_REACHED") from latest_error


def finish_companion_v1(*, root, clock=time, pause=sleep, capture=capture_public_mark_window_v1):
    """Resume from the sealed original, and verify the LearningState after ingestion."""
    _isolated(root)
    if not root.is_dir():
        raise ValueError("I17_COMPANION_ORIGINAL_ROOT_REQUIRED")
    with exclusive_v1(root / ".companion.lock"):
        profile = read_v1(root / "companion.json")
        if profile["schema"] != _PROFILE or profile["authority"] != "NONE":
            raise ValueError("I17_COMPANION_ORIGINAL_PROFILE_REQUIRED")
        evidence, plan = _verified_plan(root, profile)
        captured = _capture_o4(root, profile, plan, clock=clock, pause=pause, capture=capture)
        outcome_path = root / "shadow-outcome.json"
        receipt = _shadow_outcome_receipt(
            argparse.Namespace(
                evidence_root=evidence,
                o4_mark_archive=root / "o4",
                decision_event_ref=plan["shadow_decision"]["decision_event_ref"],
                n_bars=plan["n_bars"],
                max_end_age_seconds=_MAX_END_AGE_SECONDS,
                evaluated_at_utc=captured["available_at_utc"],
                verify_outcome_receipt=None,
                outcome_receipt_out=outcome_path,
            )
        )
        if receipt["shadow_decision"] != plan["shadow_decision"]:
            raise ValueError("I17_COMPANION_OUTCOME_SOURCE_MISMATCH")
        completion = root / "completion.json"
        existing = read_v1(completion) if completion.exists() or completion.is_symlink() else None
        handoff = shadow_ddo_learning_handoff_v1(
            root=root / "learning",
            cycle_key="i17",
            evidence_root=evidence,
            o4_mark_archive=root / "o4",
            outcome_receipt=outcome_path,
            expected_digest=existing["handoff_digest"] if existing else None,
        )
        publish_v1(completion, handoff)
        return handoff


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    run = modes.add_parser("run", help="Run an explicitly authorized I17 Shadow and its follow-up")
    resume = modes.add_parser("resume", help="Continue the DDO follow-up of a sealed Shadow only")
    for mode in (run, resume):
        mode.add_argument("--companion-root", type=Path, required=True)
    run.add_argument("--preregistration", type=Path, required=True)
    run.add_argument("--operator-go", type=Path, required=True)
    run.add_argument("--authorization-artifact", type=Path, required=True)
    run.add_argument("--confirm-token-file", type=Path)
    run.add_argument("--evidence-root", type=Path, required=True)
    run.add_argument("--fingerprint-ledger", type=Path, required=True)
    run.add_argument("--expected-repository-sha", required=True)
    run.add_argument("--o4-instrument-binding", type=Path, required=True)
    run.add_argument(
        "--card-cap24-evidence-root",
        type=Path,
        help="Carry an existing verified Cap24 selection into the SOPH card",
    )
    run.add_argument(
        "--card-selection-root",
        type=Path,
        help="Canonical published Cap21/22/23 state for the SOPH simulated first purchase",
    )
    run.add_argument(
        "--card-lane-sources",
        nargs=3,
        type=Path,
        metavar=("TOPOLOGY", "RANKING", "UNIVERSE"),
        help="Read the committed N5 slot assignment and its original ranking and universe",
    )
    args = parser.parse_args(argv)
    try:
        if os.environ.get(REAL_NETWORK_ENV) != "1":
            raise ValueError("I17_COMPANION_REAL_PUBLIC_MD_OPT_IN_REQUIRED")
        root = _isolated(args.companion_root)
        if args.mode == "run":
            prereg = _load_prereg(args.preregistration)
            card_bound = None
            selection_source = args.card_selection_root
            if args.card_lane_sources is not None:
                from src.ops.soph_slot_assignment_v1 import SophSlotSourcesV1

                if (
                    selection_source is not None
                    or require_i17_shadow_instrument_v1(prereg.instrument_allowlist) != SOPH_I17
                ):
                    raise ValueError("I17_CARD_SOPH_LANE_SOURCE_CONFLICT")
                selection_source = SophSlotSourcesV1(*args.card_lane_sources)
            if args.card_selection_root is not None and args.card_cap24_evidence_root is None:
                raise ValueError("I17_CARD_CAP24_EVIDENCE_REQUIRED")
            if args.card_cap24_evidence_root is not None:
                from scripts.ops.run_zkp_lane1_paper_v1 import _read_cap24_binding

                card_bound = _read_cap24_binding(
                    args.card_cap24_evidence_root,
                    entry_repository_sha=args.expected_repository_sha
                    if selection_source is not None
                    else None,
                )
                instrument = require_i17_shadow_instrument_v1(prereg.instrument_allowlist)
                if instrument.lane_id != "LANE_5" or (
                    card_bound.instrument_id,
                    card_bound.venue_native_id,
                ) != (instrument.canonical_id, instrument.native_id):
                    raise ValueError("I17_CARD_CAP24_INSTRUMENT_MISMATCH")
            if args.card_lane_sources is not None:
                assignment = selection_source.inspect(args.expected_repository_sha)
                if card_bound is not None:
                    assignment.require_matching_binding(card_bound)
            if (
                prereg.fixture_non_authoritative
                or prereg.expected_repository_sha != args.expected_repository_sha
                or Path(prereg.evidence_root) != args.evidence_root
                or args.evidence_root.exists()
            ):
                raise ValueError("I17_COMPANION_AUTHORIZED_NEW_SHADOW_SOURCE_REQUIRED")
            token = _load_token(args)
            go = parse_operator_go_contract_v1(load_operator_go_contract_dict_v1(args.operator_go))
            prepare_companion_v1(
                root=root,
                evidence=args.evidence_root,
                prereg=prereg,
                binding_path=args.o4_instrument_binding,
            )
            result = run_productive_wallclock_session_v1(
                prereg=prereg,
                go=go,
                confirm_token=token,
                artifact_path=args.authorization_artifact,
                evidence_root=args.evidence_root,
                expected_repository_sha=args.expected_repository_sha,
                fingerprint_ledger_path=args.fingerprint_ledger,
                use_real_network=True,
                repo_root=REPO,
                environ=os.environ,
                instrument_card_ranking_bound=card_bound,
                instrument_card_selection_root=selection_source,
            )
            if not result.ok:
                raise ValueError("I17_COMPANION_OBSERVATION_FAILED:" + ",".join(result.blockers))
        elif read_v1(root / "companion.json")["fixture_non_authoritative"] is not False:
            raise ValueError("I17_COMPANION_RECORDED_PUBLIC_SHADOW_REQUIRED")
        handoff = finish_companion_v1(root=root)
    except (OSError, HTTPException, ValueError, TypeError, KeyError, RuntimeError) as exc:
        parser.exit(2, f"I17 Shadow companion stopped: {exc}\n")
    print(json.dumps(handoff, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
