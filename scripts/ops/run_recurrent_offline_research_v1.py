#!/usr/bin/env python3
"""Process newly completed Paper and I17 evidence in bounded offline ticks."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from itertools import zip_longest
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from pydantic import BaseModel, ConfigDict, Field  # noqa: E402

from src.backtest.cost_config_v0 import resolve_effective_backtest_cost_config  # noqa: E402
from scripts.ops.paper_episode_learning_handoff_v1 import paper_episode_learning_handoff_v1  # noqa: E402
from scripts.ops.run_offline_ddo_learning_follow_up_v1 import load_offline_research_bars_v1  # noqa: E402
from scripts.ops.shadow_ddo_learning_handoff_v1 import shadow_ddo_learning_handoff_v1  # noqa: E402
from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (  # noqa: E402
    EvaluationReceiptArchiveV1,
)
from src.experiments.canonical_experiment_identity_v1 import inspect_code_provenance_v1  # noqa: E402
from src.experiments.canonical_native_research_session_v1 import NativeResearchExecutionArchiveV1  # noqa: E402
from src.experiments.canonical_research_prepared_execution_v1 import digest_v1, publish_v1, read_v1  # noqa: E402
from src.experiments.offline_ddo_research_cycle_v1 import (  # noqa: E402
    OfflineDdoResearchProfileV1,
    ResearchCycleTimesV1,
    ResearchFollowUpTimesV1,
    run_offline_paper_ddo_research_cycle_v1,
    run_offline_shadow_ddo_research_cycle_v1,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoError  # noqa: E402
from src.ops.bounded_peaktrade_system_composition_v1.paper_episode_outcome_v1 import (  # noqa: E402
    closed_paper_episode_ids_v1,
    paper_episode_fee_observation_v1,
)


class ResearchInputV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    template: Path
    bars: Path
    config: Path
    paper_fee_tolerance_bps: float | None = Field(default=None, ge=0, allow_inf_nan=False)


class ResearchCampaignV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    state: Path
    paper_runs: Path
    shadow_follow_ups: Path
    shadow_runs: Path
    research_inputs: dict[str, list[ResearchInputV1]]
    jobs_per_tick: int = Field(gt=0, strict=True)
    history_jobs: int = Field(gt=0, strict=True)
    retry_seconds: int = Field(gt=0, strict=True)


def _absolute(path: Path) -> Path:
    if not path.is_absolute() or path.resolve() != path:
        raise ValueError(f"RESEARCH_CANONICAL_ABSOLUTE_PATH_REQUIRED:{path}")
    return path


def _read_json(path: Path) -> dict:
    data = json.loads(_absolute(path).read_bytes())
    if not isinstance(data, dict):
        raise ValueError(f"RESEARCH_OBJECT_REQUIRED:{path}")
    return data


def _utc(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _discover_shadow(campaign: ResearchCampaignV1):
    for run in sorted(campaign.shadow_follow_ups.glob("*")):
        if run.is_symlink() or not (run / "completion.json").is_file():
            continue
        yield {"surface": "SHADOW", "run": str(run)}


def _read_source(workspace, source, campaign):
    if source["surface"] == "PAPER_EXCHANGE":
        archive = _absolute(Path(source["archive"]))
        output = workspace.safe_path_v1("paper-learning")
        relative = Path("paper-episodes") / source["episode"] / "result.json"
        handoff = paper_episode_learning_handoff_v1(
            archive_root=archive,
            episode_id=source["episode"],
            output_root=output,
            verify=EvaluationReceiptArchiveV1(output).safe_path_v1(relative).is_file(),
        )
        return handoff, {
            "paper_fee_observation": paper_episode_fee_observation_v1(
                archive, handoff["measurement"]
            )
        }
    run = _absolute(Path(source["run"]))
    plan = _read_json(run / "window-plan.json")
    archive = _absolute(Path(plan["shadow_archive"]))
    if not archive.is_relative_to(campaign.shadow_runs) or archive.name != "evidence":
        raise ValueError("SHADOW_RESEARCH_ARCHIVE_OUTSIDE_INTAKE")
    complete = _read_json(run / "completion.json")
    verified_receipts = []
    handoff = shadow_ddo_learning_handoff_v1(
        root=_absolute(run / "learning"),
        cycle_key="i17",
        evidence_root=archive,
        o4_mark_archive=_absolute(run / "o4"),
        outcome_receipt=_absolute(run / "shadow-outcome.json"),
        expected_digest=complete["handoff_digest"],
        verified_receipt_sink=verified_receipts,
    )
    if handoff != complete:
        raise ValueError("RESEARCH_SHADOW_COMPLETION_READBACK_MISMATCH")
    (receipt,) = verified_receipts
    return handoff, {"shadow_measurement": receipt}


def _history(workspace, instrument, strategy_id, strategy_version, as_of):
    prior = []
    for path in workspace.safe_path_v1("completed").glob("*.json"):
        row = read_v1(path)
        if (
            row["instrument_id"] == instrument
            and row["strategy_id"] == strategy_id
            and row["strategy_version"] == strategy_version
            and row["artifacts"]
            and row["completed_at_utc"] <= _utc(as_of)
        ):
            prior.append(row)
    prior.sort(key=lambda row: (row["completed_at_utc"], row["learning_digest"]))
    return prior


def _history_units(workspace, references, meta_digests, input_digest, surface):
    units = {}
    regions = {}
    for row in references:
        for_meta = row["learning_digest"] in meta_digests
        for_coverage = row["input_digest"] == input_digest and row["source"]["surface"] == surface
        if not for_meta and not for_coverage:
            continue
        result = read_v1(
            workspace.safe_path_v1(
                Path("offline-ddo-research") / row["learning_digest"] / "result.json"
            )
        )
        if digest_v1(result) != row["result_digest"]:
            raise ValueError("RESEARCH_CAMPAIGN_PRIOR_RESULT_MISMATCH")
        archive = NativeResearchExecutionArchiveV1(
            workspace.safe_path_v1(
                Path("offline-ddo-research") / row["learning_digest"] / "native-archive"
            )
        )
        if result["evaluation"] is not None:
            evidence_root = archive.root.parent / "gvef" / "evidence"
            evaluation = EvaluationReceiptArchiveV1(evidence_root).get_v1(
                "system", result["evaluation"]["receipt_id"]
            )
            if (
                evaluation["mechanism_status"] != result["evaluation"]["mechanism_status"]
                or evaluation["economic_quality"]["status"]
                != result["evaluation"]["economic_status"]
            ):
                raise ValueError("RESEARCH_CAMPAIGN_PRIOR_GVEF_MISMATCH")
        for artifact in row["artifacts"]:
            unit = archive.get(artifact).next_meta_input
            if for_meta:
                units[unit.research_loop_record["selected_experiment_id"]] = unit
            if for_coverage:
                region = dict(unit.research_loop_record["robustness_evidence"]["parameter_region"])
                regions[digest_v1(region)] = {
                    "artifact_id": artifact,
                    "parameter_region": region,
                    "input_digest": input_digest,
                }
    return tuple(units.values()), tuple(regions.values())


def _profile(template, source, now, has_history):
    """Bind logical phase ordering; the execution ledger records actual wall time."""
    clocks = list(ResearchCycleTimesV1.model_fields)
    ordered = iter(_utc(now + timedelta(microseconds=i + 1)) for i in range(len(clocks) + 4))
    campaign_meta = next(ordered) if has_history else None
    return OfflineDdoResearchProfileV1.model_validate(
        {
            **template,
            "observed_surface": source["surface"],
            "campaign_meta": campaign_meta,
            "times": {key: next(ordered) for key in clocks},
            "follow_up_times": {key: next(ordered) for key in ResearchFollowUpTimesV1.model_fields},
        }
    )


def _input_bundle(selected):
    bars = _absolute(selected.bars).read_bytes()
    config = _absolute(selected.config).read_bytes()
    template = _read_json(selected.template)
    contract_keys = {
        "schema_version",
        "instrument_id",
        "bars_csv_sha256",
        "backtest_json_sha256",
        "profile",
    }
    if set(template) != contract_keys or template["schema_version"] != "offline_research_input.v1":
        raise ValueError("RESEARCH_INPUT_DESCRIPTOR_INVALID")
    if (
        sha256(bars).hexdigest() != template["bars_csv_sha256"]
        or sha256(config).hexdigest() != template["backtest_json_sha256"]
        or template["profile"]["instrument_id"] != template["instrument_id"]
    ):
        raise ValueError("RESEARCH_INPUT_FILE_BINDING_MISMATCH")
    return (
        template["profile"],
        bars,
        config,
        digest_v1(
            {
                "descriptor": template,
                "paper_fee_tolerance_bps": selected.paper_fee_tolerance_bps,
            }
        ),
    )


def _run_one(workspace, source, handoff, source_measurements, campaign, code, now):
    evidence = handoff["learning_evidence"]
    digest = evidence["content_hash"]
    instrument = evidence["outcome_evidence_provenance"]["instrument_id"]
    receipt = workspace.safe_path_v1(Path("sources") / (digest_v1(source) + ".json"))
    done = workspace.safe_path_v1(Path("completed") / (digest + ".json"))
    if done.exists():
        _verify_completed(workspace, digest)
        publish_v1(receipt, {"source": source, "learning_digest": digest})
        return "ALREADY_COMPLETED"
    path = workspace.safe_path_v1(Path("jobs") / (digest + ".json"))
    if path.exists():
        packet = read_v1(path)
        selected = ResearchInputV1.model_validate(packet["input"])
    else:
        selected = _select_input(campaign, instrument, evidence, now)
        if selected is None:
            return "WAITING_FOR_RESEARCH_INPUT"
        packet = None
    template, bars, config, input_digest = _input_bundle(selected)
    if template["instrument_id"] != instrument:
        raise ValueError("RESEARCH_CAMPAIGN_INSTRUMENT_MISMATCH")
    if template["gap_dimensions"]:
        raise ValueError("RESEARCH_CAMPAIGN_GAP_REQUIRES_SOURCE_BOUND_MEASUREMENT")
    config = json.loads(config)
    fee = source_measurements.get("paper_fee_observation")
    tolerance = selected.paper_fee_tolerance_bps
    if fee is not None and tolerance is not None:
        policy = {
            "dimension": "fee",
            "scope": "SIMULATED_FILL_FEE_MODEL_PARITY",
            "threshold_bps": tolerance,
            "authority": "NONE",
        }
        template = {
            **template,
            "threshold_policy_digest": digest_v1(policy),
            "gap_dimensions": [
                {
                    "name": "fee",
                    "expected": resolve_effective_backtest_cost_config(config).taker_fee_bps,
                    "observed": float(fee["fee_basis_points"]),
                    "threshold": tolerance,
                    "unit": "bps",
                }
            ],
        }
        source_measurements = {"paper_fee_observation": {**fee, "threshold_policy": policy}}
    if packet is not None:
        if (packet["input_digest"], packet["source"], packet["code_sha"]) != (
            input_digest,
            source,
            code.git_sha,
        ):
            raise ValueError("RESEARCH_CAMPAIGN_ORIGINAL_JOB_CHANGED")
    else:
        # History is taken before the experiment and frozen for every retry.
        history = _history(
            workspace,
            instrument,
            template["strategy_id"],
            template["strategy_version"],
            now,
        )
        meta_digests = [row["learning_digest"] for row in history[-campaign.history_jobs :]]
        profile = _profile(template, source, now, bool(meta_digests))
        packet = {
            "source": source,
            "input": selected.model_dump(mode="json"),
            "input_digest": input_digest,
            "code_sha": code.git_sha,
            "profile": {
                **profile.model_dump(mode="json", exclude_none=True),
                "campaign_meta": profile.campaign_meta,
            },
            "history": history,
            "meta_digests": meta_digests,
        }
        publish_v1(path, packet)
    runner = (
        run_offline_paper_ddo_research_cycle_v1
        if source["surface"] == "PAPER_EXCHANGE"
        else run_offline_shadow_ddo_research_cycle_v1
    )
    prior_units, coverage = _history_units(
        workspace, packet["history"], packet["meta_digests"], input_digest, source["surface"]
    )
    result = runner(
        workspace.root,
        digest,
        handoff=handoff,
        request=OfflineDdoResearchProfileV1.model_validate(packet["profile"]),
        bars=load_offline_research_bars_v1(bars),
        cfg=config,
        code=code,
        campaign_history=prior_units,
        campaign_regions=coverage,
        **source_measurements,
    )
    if result["status"] == "MECHANISM_INCOMPLETE":
        return result["status"]
    publish_v1(
        done,
        {
            "authority": "NONE",
            "completed_at_utc": _utc(datetime.now(timezone.utc)),
            "instrument_id": instrument,
            "learning_digest": digest,
            "source": source,
            "result_digest": digest_v1(result),
            "input_digest": input_digest,
            "status": result["status"],
            "strategy_id": template["strategy_id"],
            "strategy_version": template["strategy_version"],
            "artifacts": [
                artifact
                for artifact in (
                    result["first_artifact_id"],
                    result["next_artifact_id"],
                    (result.get("follow_up") or {}).get("artifact_id"),
                )
                if artifact is not None
            ],
        },
    )
    publish_v1(receipt, {"source": source, "learning_digest": digest})
    return result["status"]


def _select_input(campaign, instrument, evidence, now):
    observed = datetime.fromisoformat(evidence["observed_at_utc"].replace("Z", "+00:00"))
    if observed >= now:
        return None
    available = {}
    for candidate in campaign.research_inputs.get(instrument, ()):
        profile = _read_json(candidate.template)["profile"]
        timestamp = datetime.fromisoformat(profile["bars_known_at"].replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("RESEARCH_DATASET_KNOWLEDGE_TIME_REQUIRES_TIMEZONE")
        if timestamp < now:
            if timestamp in available:
                raise ValueError("RESEARCH_CAMPAIGN_AMBIGUOUS_DATASET_VERSION")
            available[timestamp] = candidate
    return available[max(available)] if available else None


def _verify_completed(workspace, digest):
    result = read_v1(workspace.safe_path_v1(Path("offline-ddo-research") / digest / "result.json"))
    completed = read_v1(workspace.safe_path_v1(Path("completed") / (digest + ".json")))
    if (
        completed["learning_digest"] != digest
        or result["learning_evidence_digest"] != digest
        or digest_v1(result) != completed["result_digest"]
    ):
        raise ValueError("RESEARCH_CAMPAIGN_RESULT_MISMATCH")


def tick_research_campaign_v1(campaign: ResearchCampaignV1, *, code, now=None):
    from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
        atomic_write_json,
    )

    workspace = EvaluationReceiptArchiveV1(_absolute(campaign.state))
    sources = [
        _absolute(path)
        for path in (campaign.paper_runs, campaign.shadow_follow_ups, campaign.shadow_runs)
    ]
    if any(
        workspace.root.is_relative_to(path) or path.is_relative_to(workspace.root)
        for path in [REPO, *sources]
    ):
        raise ValueError("RESEARCH_CAMPAIGN_SEPARATE_WORKSPACE_REQUIRED")
    if any(not path.is_dir() for path in sources):
        raise ValueError("RESEARCH_CAMPAIGN_SOURCE_DIRECTORY_REQUIRED")
    if code.working_tree_status != "CLEAN":
        raise ValueError("RESEARCH_CAMPAIGN_CLEAN_CHECKOUT_REQUIRED")
    jobs = []
    attempted = 0
    clock = (lambda: now) if now is not None else (lambda: datetime.now(timezone.utc))
    with workspace.lease_v1():
        discovered = list(_discover_shadow(campaign))
        for archive in sorted(campaign.paper_runs.glob("*")):
            if archive.is_symlink() or not (archive / "MANIFEST.sha256").is_file():
                continue
            try:
                discovered.extend(
                    {"surface": "PAPER_EXCHANGE", "archive": str(archive), "episode": episode}
                    for episode in closed_paper_episode_ids_v1(archive)
                )
            except (OSError, ValueError, KeyError, TypeError) as exc:
                jobs.append({"source": str(archive), "status": "BLOCKED", "reason": str(exc)})
        # Interleave the two sources so a backlog cannot monopolize each tick.
        paper = iter(item for item in discovered if item["surface"] == "PAPER_EXCHANGE")
        shadow = iter(item for item in reversed(discovered) if item["surface"] == "SHADOW")
        scheduled = (
            item for pair in zip_longest(paper, shadow) for item in pair if item is not None
        )
        for source in scheduled:
            if attempted >= campaign.jobs_per_tick:
                break
            job_time = clock()
            source_id = digest_v1(source)
            receipt = workspace.safe_path_v1(Path("sources") / (source_id + ".json"))
            retry_path = workspace.safe_path_v1(Path("retry") / (source_id + ".json"))
            try:
                if retry_path.is_file():
                    retry = _read_json(retry_path)
                    if job_time < datetime.fromisoformat(
                        retry["retry_at_utc"].replace("Z", "+00:00")
                    ):
                        continue
                if receipt.is_file():
                    completed = read_v1(receipt)
                    if completed["source"] != source:
                        raise ValueError("RESEARCH_CAMPAIGN_SOURCE_MISMATCH")
                    _verify_completed(workspace, completed["learning_digest"])
                    continue
                handoff, measurements = _read_source(workspace, source, campaign)
                status = _run_one(
                    workspace, source, handoff, measurements, campaign, code, job_time
                )
                row = {"source": source, "status": status}
            except (OSError, ValueError, KeyError, TypeError, DdoError) as exc:
                status = "BLOCKED"
                row = {"source": source, "status": status, "reason": str(exc)}
            if status in {"BLOCKED", "MECHANISM_INCOMPLETE", "WAITING_FOR_RESEARCH_INPUT"}:
                atomic_write_json(
                    path=retry_path,
                    payload={
                        **row,
                        "retry_at_utc": _utc(clock() + timedelta(seconds=campaign.retry_seconds)),
                    },
                )
            jobs.append(row)
            attempted += 1
    return {"authority": "NONE", "jobs": jobs}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True, type=Path)
    args = parser.parse_args(argv)
    campaign = ResearchCampaignV1.model_validate(_read_json(args.campaign))
    try:
        result = tick_research_campaign_v1(campaign, code=inspect_code_provenance_v1(REPO))
    except (OSError, ValueError, KeyError, TypeError, DdoError) as exc:
        parser.exit(2, f"Offline research tick stopped: {exc}\n")
    print(json.dumps(result, sort_keys=True), flush=True)
    return 2 if any(row["status"] == "BLOCKED" for row in result["jobs"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
