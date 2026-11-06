"""
Resolve OBSE + AILIVE compose project names and -f compose file args.
Uses docker compose ls ConfigFiles when present; else fallback to known
base + override compose files on disk (so stacks can be started after a down).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List

REPO = Path.cwd()
BASE_DEFAULT = REPO / "docker/docker-compose.obs.yml"
PROMETHEUS_CONFIG_DEFAULT = REPO / ".local/prometheus/prometheus.docker.yml"
OVR_DIR = REPO / ".ops_local/compose_overrides"


def _compose_ls_json() -> list:
    try:
        out = subprocess.check_output(
            ["docker", "compose", "ls", "--format", "json"],
            text=True,
            cwd=REPO,
        )
        return json.loads(out) if out.strip() else []
    except Exception:
        return []


def _cfgfiles_from_ls(project: str, rows: list) -> List[str]:
    for r in rows:
        if (r.get("Name") or "").strip() != project:
            continue
        cfg = r.get("ConfigFiles") or r.get("ConfigFile")
        files: List[str] = []
        if isinstance(cfg, list):
            files = [str(x).strip() for x in cfg if str(x).strip()]
        elif isinstance(cfg, str):
            parts = [p.strip() for p in cfg.split(",")]
            files = [p for p in parts if p]
        return files
    return []


def _pick_project(rows: list, needles: List[str], fallback: str) -> str:
    for n in needles:
        for r in rows:
            name = (r.get("Name") or "").strip()
            if n in name:
                return name
    return fallback


def _exists(p: Path) -> bool:
    return p.exists() and p.is_file()


def _fallback_files(kind: str) -> List[Path]:
    """Return compose files for fallback. Prefer override-only (full compose in
    .ops_local) to avoid port list merge with base (which would add 9092)."""
    if kind == "obse":
        patterns = [
            "*observability*.yml",
            "*observability*.yaml",
            "*obse*.yml",
            "*obse*.yaml",
        ]
    else:
        patterns = [
            "*ai-live*.yml",
            "*ai-live*.yaml",
            "*ai_live*.yml",
            "*ai_live*.yaml",
        ]

    files: List[Path] = []
    if OVR_DIR.exists():
        seen = set()
        for pat in patterns:
            for p in sorted(OVR_DIR.glob(pat)):
                rp = str(p.resolve())
                if rp in seen:
                    continue
                seen.add(rp)
                files.append(p)
    if files:
        return files
    if _exists(BASE_DEFAULT):
        return [BASE_DEFAULT]
    return []


def _shell_f_args(paths: List[Path]) -> str:
    def q(s: str) -> str:
        return "'" + s.replace("'", "'\"'\"'") + "'"

    return " ".join("-f " + q(str(p)) for p in paths)


def resolve() -> dict:
    rows = _compose_ls_json()

    obse_proj = os.environ.get("OBSE_PROJECT") or _pick_project(
        rows, ["observability", "obse"], "peaktrade-observability"
    )
    ailive_proj = os.environ.get("AILIVE_PROJECT") or _pick_project(
        rows, ["ai-live"], "peaktrade-ai-live-ops"
    )

    obse_override = (os.environ.get("OBSE_COMPOSE") or "").strip()
    ailive_override = (os.environ.get("AILIVE_COMPOSE") or "").strip()

    if obse_override:
        obse_args = obse_override
    else:
        ls_files = _cfgfiles_from_ls(obse_proj, rows)
        if ls_files:
            obse_args = _shell_f_args([Path(f) for f in ls_files])
        else:
            obse_args = _shell_f_args(_fallback_files("obse"))

    if ailive_override:
        ailive_args = ailive_override
    else:
        ls_files = _cfgfiles_from_ls(ailive_proj, rows)
        if ls_files:
            ailive_args = _shell_f_args([Path(f) for f in ls_files])
        else:
            ailive_args = _shell_f_args(_fallback_files("ai-live"))

    return {
        "OBSE_PROJECT": obse_proj,
        "AILIVE_PROJECT": ailive_proj,
        "OBSE_COMPOSE_ARGS": obse_args.strip(),
        "AILIVE_COMPOSE_ARGS": ailive_args.strip(),
        "compose_ls_names": [(r.get("Name") or "").strip() for r in rows],
        "base_default_exists": str(_exists(BASE_DEFAULT)),
        "override_dir_exists": str(OVR_DIR.exists()),
    }


if __name__ == "__main__":
    print(json.dumps(resolve(), indent=2, sort_keys=True))
