"""Keep a scoped offline research worker with its producer until the original is closed."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

from scripts.ops.run_recurrent_offline_research_v1 import (
    REPO,
    ResearchCampaignV1,
    ResearchInputV1,
    _input_bundle,
)


def verified_input(path, instrument, surface, now):
    selected = ResearchInputV1.model_validate_json(path.read_bytes())
    return selected, research_digest(selected, instrument, surface, now)


def research_digest(selected, instrument, surface, now):
    profile, _, _, digest = _input_bundle(selected)
    known = datetime.fromisoformat(profile["bars_known_at"].replace("Z", "+00:00"))
    if (
        known.utcoffset() is None
        or profile["instrument_id"] != instrument
        or profile["observed_surface"] != surface
        or known > datetime.fromtimestamp(now, timezone.utc)
    ):
        raise ValueError("GVEF_RESEARCH_INPUT_SCOPE_OR_KNOWLEDGE_TIME_MISMATCH")
    return digest


def _tick(campaign, output, phase):
    path = output / (phase + "-campaign.json")
    with path.open("x") as stream:
        stream.write(campaign.model_dump_json(indent=2, exclude_none=True) + "\n")
    result = subprocess.run(
        [
            str(REPO / "scripts/pt"),
            "-m",
            "scripts.ops.run_recurrent_offline_research_v1",
            "--campaign",
            str(path),
        ],
        cwd=REPO,
        env=dict(os.environ, GIT_WORK_TREE=str(REPO)),
        capture_output=True,
        text=True,
    )
    (output / (phase + ".stderr")).write_text(result.stderr)
    (output / (phase + ".json")).write_text(result.stdout)
    result.check_returncode()
    return json.loads(result.stdout)


@contextmanager
def paired_gvef(campaign: ResearchCampaignV1, output: Path, *, final_campaign=None):
    if campaign.slot is None or campaign.slot.surface not in {"PAPER_EXCHANGE", "SHADOW"}:
        raise ValueError("PAPER_OR_SHADOW_GVEF_SCOPE_REQUIRED")
    output.mkdir(mode=0o700)
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="gvef") as worker:
        worker.submit(_tick, campaign, output, "start").result()
        yield
        final = final_campaign() if final_campaign else campaign
        worker.submit(_tick, final, output, "closeout").result()
