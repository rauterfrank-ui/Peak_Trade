"""Regression: GHV E2E must bind productive Closure from pre-decision cursor, not post-ENTER."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.ghv_e2e_productive_pre_external_tail_bind_v1 import (
    FORENSIC_LEGACY_POST_ENTER_ENV,
    ghv_e2e_forensic_legacy_post_enter_closure_entry_v1,
    resolve_ghv_e2e_closure_lane_entry_cursor_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class _CursorStub:
    def __init__(self, label: str) -> None:
        self.label = label
        self.side_state = label

    def to_persisted_payload_v1(self) -> dict[str, str]:
        return {"label": self.label}


def test_resolve_closure_entry_cursor_defaults_to_pre_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(FORENSIC_LEGACY_POST_ENTER_ENV, raising=False)
    pre = _CursorStub("pre")
    post = _CursorStub("post")
    assert (
        resolve_ghv_e2e_closure_lane_entry_cursor_v1(
            pre_decision_incoming_cursor=pre,
            post_enter_outgoing_cursor=post,
        )
        is pre
    )
    assert not ghv_e2e_forensic_legacy_post_enter_closure_entry_v1()


def test_forensic_legacy_env_selects_post_enter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(FORENSIC_LEGACY_POST_ENTER_ENV, "1")
    pre = _CursorStub("pre")
    post = _CursorStub("post")
    assert (
        resolve_ghv_e2e_closure_lane_entry_cursor_v1(
            pre_decision_incoming_cursor=pre,
            post_enter_outgoing_cursor=post,
        )
        is post
    )


def test_pre_and_post_decision_cursors_are_distinct_on_enter_cycle() -> None:
    """Representative GHV-F0068/c8 digests from slice-D forensics (read-only invariant)."""
    prior = (
        REPO_ROOT / "evidence/research/ghv_pre_external_tail_slice_d_lifecycle_forensics_v1/"
        "20261003T212408Z/representative_timeline.json"
    )
    if not prior.is_file():
        pytest.skip("slice-D representative timeline evidence not present")
    data = json.loads(prior.read_text(encoding="utf-8"))
    stage0 = data["stages"][0]
    pre_d = stage0["INPUT_CURSOR_DIGEST"]
    post_d = stage0["OUTPUT_CURSOR_DIGEST"]
    assert pre_d != post_d
    assert stage0["DECISION_CLASS"] in ("enter_long", "enter_short")


def test_durable_module_does_not_import_slice_scaffold() -> None:
    path = (
        REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1/"
        "ghv_e2e_productive_pre_external_tail_bind_v1.py"
    )
    text = path.read_text(encoding="utf-8")
    assert "GHV_SLICE_A" not in text
    assert "GHV_SLICE_B" not in text
    assert "GHV_SLICE_C" not in text
    assert "GHV_SLICE_D" not in text
    assert hashlib.sha256(text.encode()).hexdigest()[:12]
