from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def test_prepare_bounded_scope_runner_materializes_ratified_candidates(tmp_path: Path) -> None:
    repo = Path.cwd()
    source = tmp_path / "source"
    evidence = tmp_path / "evidence"
    source.mkdir()
    payload = {
        "candidates": [
            {
                "candidate": "trend_following",
                "ratified": True,
                "non_retry_provenance_digest": "a" * 64,
            },
            {
                "candidate": "bollinger_bands",
                "ratified": True,
                "non_retry_provenance_digest": "b" * 64,
            },
            {
                "candidate": "momentum_1h",
                "ratified": True,
                "non_retry_provenance_digest": "c" * 64,
            },
        ]
    }
    p = source / "ratified_bindings.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    (source / "MANIFEST.sha256").write_text(
        f"{digest}  ./ratified_bindings.json\n", encoding="utf-8"
    )

    env = os.environ.copy()
    env.update(
        {
            "PEAK_TRADE_SOURCE_EVIDENCE": str(source),
            "PEAK_TRADE_EVIDENCE_DIR": str(evidence),
            "PEAK_TRADE_LIVE_AUTHORIZED": "false",
            "PEAK_TRADE_ORDERS_ALLOWED": "false",
            "PEAK_TRADE_SCHEDULER_RUNTIME_ALLOWED": "false",
            "PEAK_TRADE_EVALUATION_EXECUTED": "false",
            "PEAK_TRADE_UNMODIFIED_BINDING_RETRY_ALLOWED": "false",
        }
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/research/prepare_bounded_offline_evaluation_scope_from_ratified_new_versioned_bindings_no_retry_v0.py",
        ],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    out = json.loads(
        (
            evidence
            / "prepared_bounded_offline_evaluation_scope_from_ratified_new_versioned_bindings_no_retry_v0.json"
        ).read_text()
    )
    assert out["scope_status"] == "PREPARED_FOR_SEPARATE_BOUNDED_OFFLINE_EVALUATION"
    assert out["economic_evaluation_executed"] is False
    assert out["unmodified_binding_retry_allowed"] is False
    assert out["orders_allowed"] is False
    assert out["live_authorized"] is False
    assert [c["candidate"] for c in out["candidates"]] == [
        "trend_following",
        "bollinger_bands",
        "momentum_1h",
    ]


def test_prepare_bounded_scope_runner_blocks_runtime_authority(tmp_path: Path) -> None:
    repo = Path.cwd()
    source = tmp_path / "source"
    evidence = tmp_path / "evidence"
    source.mkdir()
    p = source / "ratified_bindings.json"
    p.write_text(
        json.dumps(
            {
                "candidates": [
                    {"candidate": "trend_following", "ratified": True},
                    {"candidate": "bollinger_bands", "ratified": True},
                    {"candidate": "momentum_1h", "ratified": True},
                ]
            }
        ),
        encoding="utf-8",
    )
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    (source / "MANIFEST.sha256").write_text(
        f"{digest}  ./ratified_bindings.json\n", encoding="utf-8"
    )

    env = os.environ.copy()
    env.update(
        {
            "PEAK_TRADE_SOURCE_EVIDENCE": str(source),
            "PEAK_TRADE_EVIDENCE_DIR": str(evidence),
            "PEAK_TRADE_LIVE_AUTHORIZED": "true",
            "PEAK_TRADE_ORDERS_ALLOWED": "false",
            "PEAK_TRADE_SCHEDULER_RUNTIME_ALLOWED": "false",
            "PEAK_TRADE_EVALUATION_EXECUTED": "false",
            "PEAK_TRADE_UNMODIFIED_BINDING_RETRY_ALLOWED": "false",
        }
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/research/prepare_bounded_offline_evaluation_scope_from_ratified_new_versioned_bindings_no_retry_v0.py",
        ],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "LIVE_AUTHORIZED_TRUE" in result.stdout
