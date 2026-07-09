from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from research.linear_evidence.signal_orthogonality import (
    SignalOrthogonalityConfigV1,
    analyze_signal_orthogonality,
    evidence_to_dict,
    make_deterministic_signal_fixture,
)


def test_signal_orthogonality_fixture_reports_redundancy_without_authority() -> None:
    rows, features = make_deterministic_signal_fixture()
    evidence = analyze_signal_orthogonality(
        rows,
        features,
        config=SignalOrthogonalityConfigV1(correlation_threshold=0.80),
    )
    payload = evidence_to_dict(evidence)

    assert payload["status"] == "DIAGNOSTIC_ONLY"
    assert payload["authority_effect"] == "NONE"
    assert payload["runtime_effect"] == "NONE"
    assert payload["cost_policy_output"] == "diagnostic_only"
    assert payload["validation_policy"]["strategy_selection_effect"] is False
    assert "SIGNAL_REDUNDANCY_REPORTED" in payload["reason_codes"]
    assert payload["diagnostics"]["redundant_pairs"]


def test_signal_orthogonality_blocks_random_split_and_keeps_offline_policy() -> None:
    rows, features = make_deterministic_signal_fixture()
    evidence = analyze_signal_orthogonality(rows, features)
    payload = evidence_to_dict(evidence)

    assert payload["validation_policy"]["offline_only"] is True
    assert payload["validation_policy"]["random_split_allowed"] is False
    assert payload["validation_policy"]["lookahead_allowed"] is False


def test_signal_orthogonality_cli_writes_manifestable_report(tmp_path: Path) -> None:
    script = Path("scripts/research/offline_signal_orthogonality_diagnostics_v0.py")
    result = subprocess.run(
        [sys.executable, str(script), "--out", str(tmp_path)],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "VERDICT=OFFLINE_SIGNAL_ORTHOGONALITY_DIAGNOSTICS_V0_COLLECTED" in result.stdout
    payload = json.loads(
        (tmp_path / "signal_orthogonality_evidence_v1.json").read_text(encoding="utf-8")
    )
    assert payload["authority_effect"] == "NONE"
    assert payload["runtime_effect"] == "NONE"


def test_signal_orthogonality_source_has_no_runtime_order_or_scheduler_imports() -> None:
    source = Path("src/research/linear_evidence/signal_orthogonality.py").read_text(
        encoding="utf-8"
    )
    forbidden = [
        "src.live",
        "src.execution",
        "src.scheduler",
        "live.",
        "execution.",
        "scheduler.",
        "order_adapter",
        "submit_order",
        "cancel_order",
    ]
    assert not any(token in source for token in forbidden)
