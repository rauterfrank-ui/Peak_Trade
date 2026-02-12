"""Governance: generated artifacts must not contain forbidden keys (Runbook K4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ingress.orchestrator import OrchestratorConfig, run_ingress


FORBIDDEN_KEYS = frozenset(
    {"payload", "raw", "transcript", "api_key", "secret", "token", "content"}
)


def _keys_deep(obj, prefix: str = "") -> list[str]:
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key_lower = k.lower()
            if any(f in key_lower for f in FORBIDDEN_KEYS):
                hits.append(f"{prefix}.{k}" if prefix else k)
            hits.extend(_keys_deep(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            hits.extend(_keys_deep(item, f"{prefix}[{i}]"))
    return hits


def test_ingress_artifacts_no_forbidden_keys(tmp_path: Path) -> None:
    config = OrchestratorConfig(base_dir=tmp_path / "ops", run_id="gov_cmes", input_jsonl_path="")
    fv_path, cap_path = run_ingress(config)
    for p in (fv_path, cap_path):
        data = json.loads(p.read_text(encoding="utf-8"))
        hits = _keys_deep(data)
        assert not hits, f"forbidden keys in {p.name}: {hits}"
