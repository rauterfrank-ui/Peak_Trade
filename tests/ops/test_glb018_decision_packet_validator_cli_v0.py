"""CLI tests for the GLB-018 operator decision packet validator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("scripts/ops/validate_glb018_operator_decision_packet.py")

AUTHORITY_FLAGS = {
    "live_authorization": False,
    "bounded_pilot_approval": False,
    "closeout_approval": False,
    "gate_passage": False,
    "strategy_readiness": False,
    "autonomy_readiness": False,
    "external_authority_completion": False,
}


def canonical_packet() -> dict[str, object]:
    rows = [
        {
            "session_id": "session_20260319_152033_bounded_pilot_8e5f2c",
            "operator_decision": "closeout_path_required",
        },
        {
            "session_id": "session_20260319_151416_bounded_pilot_579507",
            "operator_decision": "closeout_path_required",
        },
        {
            "session_id": "session_20260318_154852_bounded_pilot_979b86",
            "operator_decision": "evidence_missing_review",
        },
        {
            "session_id": "session_20260318_122341_bounded_pilot_02c8eb",
            "operator_decision": "evidence_missing_review",
        },
        {
            "session_id": "session_20260318_122123_bounded_pilot_8c7be9",
            "operator_decision": "evidence_missing_review",
        },
    ]
    return {
        "contract": "operator_glb018_decision_packet_v0",
        "non_authorizing": True,
        "session_decisions": rows,
        "decision_counts": {
            "closeout_path_required": 2,
            "evidence_missing_review": 3,
        },
        "operator_decision_required": True,
        "authority_boundary": dict(AUTHORITY_FLAGS),
    }


def write_packet(tmp_path: Path, packet: dict[str, object]) -> Path:
    path = tmp_path / "packet.json"
    path.write_text(json.dumps(packet, sort_keys=True), encoding="utf-8")
    return path


def run_validator(packet_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--packet", str(packet_path), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )


def parse_stdout(proc: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return json.loads(proc.stdout)


def test_valid_packet_exits_zero_and_emits_ok_json(tmp_path: Path) -> None:
    proc = run_validator(write_packet(tmp_path, canonical_packet()))
    payload = parse_stdout(proc)

    assert proc.returncode == 0
    assert payload["contract"] == "glb018_decision_packet_validator_v0"
    assert payload["input_contract"] == "operator_glb018_decision_packet_v0"
    assert payload["ok"] is True
    assert payload["errors"] == []
    assert payload["non_authorizing"] is True
    assert payload["authority_boundary"] == AUTHORITY_FLAGS


def test_invalid_decision_exits_one(tmp_path: Path) -> None:
    packet = canonical_packet()
    rows = packet["session_decisions"]
    assert isinstance(rows, list)
    rows[0]["operator_decision"] = "approve_live"

    proc = run_validator(write_packet(tmp_path, packet))
    payload = parse_stdout(proc)

    assert proc.returncode == 1
    assert payload["ok"] is False
    assert "invalid_operator_decision" in payload["errors"]


def test_malformed_json_exits_two(tmp_path: Path) -> None:
    path = tmp_path / "packet.json"
    path.write_text("{not-json", encoding="utf-8")

    proc = run_validator(path)
    payload = parse_stdout(proc)

    assert proc.returncode == 2
    assert payload["ok"] is False
    assert payload["errors"] == ["packet_read_or_parse_failed"]
    assert payload["non_authorizing"] is True
    assert payload["authority_boundary"] == AUTHORITY_FLAGS


def test_missing_packet_exits_two(tmp_path: Path) -> None:
    proc = run_validator(tmp_path / "missing.json")
    payload = parse_stdout(proc)

    assert proc.returncode == 2
    assert payload["ok"] is False
    assert payload["errors"] == ["packet_read_or_parse_failed"]
    assert payload["non_authorizing"] is True


def test_true_authority_flag_exits_one(tmp_path: Path) -> None:
    packet = canonical_packet()
    packet["authority_boundary"] = {**AUTHORITY_FLAGS, "live_authorization": True}

    proc = run_validator(write_packet(tmp_path, packet))
    payload = parse_stdout(proc)

    assert proc.returncode == 1
    assert "authority_boundary_must_be_all_false" in payload["errors"]


def test_output_contains_no_unqualified_authority_claims(tmp_path: Path) -> None:
    proc = run_validator(write_packet(tmp_path, canonical_packet()))
    serialized = proc.stdout.lower()

    forbidden_claims = [
        "live authorization granted",
        "bounded pilot approved",
        "closeout approved",
        "signoff complete",
        "gate passed",
        "strategy ready",
        "autonomy ready",
        "externally authorized",
        "approved for live",
        "trade approved",
    ]

    for claim in forbidden_claims:
        assert claim not in serialized


def test_this_cli_test_does_not_read_real_artifact_locations() -> None:
    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "/".join(["reports", "experiments", "live_sessions"]),
        "/".join(["out", "ops"]),
        "/".join(["execution_events", "sessions"]),
        "_".join(["live", "session", "registry"]),
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source_text
