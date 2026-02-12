from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .db import (
    DEFAULT_DB_PATH,
    DEFAULT_EVENTS_PATH,
    apply_schema,
    connect,
    make_run_id,
    stable_config_hash,
    utc_now_iso,
)
from .runner import (
    collect_and_persist,
    normalize_and_persist,
    risk_and_persist,
    score_and_persist,
)


@dataclass(frozen=True)
class RunResult:
    ok: bool
    run_id: str
    config_hash: str
    steps: list[str]
    outputs: dict[str, Any]
    manifest_path: str


def run_pipeline(
    *,
    cfg: Mapping[str, Any],
    out_dir: Path,
    db_path: Path = DEFAULT_DB_PATH,
    events_path: Path = DEFAULT_EVENTS_PATH,
    steps: list[str] | None = None,
) -> RunResult:
    """
    P6: Orchestrator-lite (deterministic).
    steps default: ["init","collect","normalize","risk","score"]
    Writes a run manifest JSON to out_dir/run_manifest_<run_id>.json (append-only by new run_id).
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg_hash = stable_config_hash(cfg)
    run_id = make_run_id(prefix="nl", config_hash8=cfg_hash[:8])

    steps_to_run = steps or ["init", "collect", "normalize", "risk", "score"]
    outputs: dict[str, Any] = {
        "ts_utc": utc_now_iso(),
        "db": str(db_path),
        "events": str(events_path),
    }

    # init schema (safe to run repeatedly)
    con = connect(db_path)
    apply_schema(con)
    outputs["init"] = {"ok": True}

    if "collect" in steps_to_run:
        outputs["collect"] = collect_and_persist(cfg=cfg, db_path=db_path, events_path=events_path)
    if "normalize" in steps_to_run:
        outputs["normalize"] = normalize_and_persist(
            cfg=cfg, db_path=db_path, events_path=events_path
        )
    if "risk" in steps_to_run:
        outputs["risk"] = risk_and_persist(cfg=cfg, db_path=db_path, events_path=events_path)
    if "score" in steps_to_run:
        outputs["score"] = score_and_persist(cfg=cfg, db_path=db_path, events_path=events_path)

    manifest = {
        "ok": True,
        "run_id": run_id,
        "config_hash": cfg_hash,
        "steps": steps_to_run,
        "outputs": outputs,
    }
    manifest_path = out_dir / f"run_manifest_{run_id}.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return RunResult(
        ok=True,
        run_id=run_id,
        config_hash=cfg_hash,
        steps=steps_to_run,
        outputs=outputs,
        manifest_path=str(manifest_path),
    )
