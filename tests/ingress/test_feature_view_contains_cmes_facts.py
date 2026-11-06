"""Contract: FeatureView contains CMES 7 facts; pointer-only scan passes (Runbook K2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.risk.cmes import CMES_FACT_KEYS, default_cmes_facts
from src.ingress.views.feature_view_builder import build_feature_view_from_jsonl


FORBIDDEN_KEYS = frozenset(
    {"payload", "raw", "transcript", "api_key", "secret", "token", "content"}
)


def _scan_dict_forbidden(d: dict, path: str = "") -> list[str]:
    hits = []
    for k, v in d.items():
        key_lower = k.lower()
        if any(f in key_lower for f in FORBIDDEN_KEYS):
            hits.append(f"{path}.{k}" if path else k)
        if isinstance(v, dict):
            hits.extend(_scan_dict_forbidden(v, f"{path}.{k}" if path else k))
    return hits


def test_feature_view_has_cmes_facts_empty_input() -> None:
    v = build_feature_view_from_jsonl("", run_id="r1")
    out = v.to_dict()
    facts = out.get("facts", {})
    for k in CMES_FACT_KEYS:
        assert k in facts, f"missing CMES fact {k}"


def test_feature_view_pointer_only_scan() -> None:
    v = build_feature_view_from_jsonl("", run_id="r1")
    out = v.to_dict()
    hits = _scan_dict_forbidden(out)
    assert not hits, f"forbidden keys in FeatureView: {hits}"


def test_feature_view_from_jsonl_has_cmes_facts(tmp_path: Path) -> None:
    jsonl = tmp_path / "ev.jsonl"
    jsonl.write_text(
        '{"event_id":"e1","ts_ms":1000,"source":"s","kind":"k","scope":"sc","tags":[],"sensitivity":"internal"}\n'
    )
    v = build_feature_view_from_jsonl(str(jsonl), run_id="r1")
    facts = v.to_dict().get("facts", {})
    for k in CMES_FACT_KEYS:
        assert k in facts
