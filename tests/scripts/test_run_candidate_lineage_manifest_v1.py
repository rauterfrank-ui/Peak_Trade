"""CLI tests for Package F offline CandidateLineageManifest v1 producer."""

from __future__ import annotations

import json
import os
import stat
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.run_candidate_lineage_manifest_v1 import (
    EXIT_OK,
    EXIT_PRODUCER_ERROR,
    EXIT_USAGE_ERROR,
    main,
)
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    CandidateLineageManifestValidationError,
    deserialize_candidate_lineage_manifest_v1,
    validate_candidate_lineage_manifest_v1,
)


FIXED_NOW = datetime(2026, 6, 27, 17, 0, 0, tzinfo=timezone.utc)
LINEAGE_ID = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
CONTRACT_REF = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"


def _valid_input() -> dict:
    return {
        "lineage_manifest_id": LINEAGE_ID,
        "candidate_id": "candidate-cli-001",
        "candidate_type": "config_patch_bundle",
        "candidate_contract_ref": CONTRACT_REF,
        "refs": [
            {
                "ref_type": "experiment",
                "ref_id": "exp-cli-1",
                "relation": "sources",
                "owner_domain": "experiments/base",
                "required": True,
            }
        ],
        "created_at": FIXED_NOW.isoformat(),
    }


def test_cli_valid_run_produces_deterministic_output(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    input_path.write_text(json.dumps(_valid_input()), encoding="utf-8")

    rc = main(
        [
            "--input-path",
            str(input_path),
            "--output-path",
            str(output_path),
            "--created-at",
            FIXED_NOW.isoformat(),
        ]
    )
    assert rc == EXIT_OK
    assert output_path.is_file()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    valid, _, errors, _ = validate_candidate_lineage_manifest_v1(payload)
    assert valid is True, errors
    assert payload["lineage_manifest_id"] == LINEAGE_ID

    rc_second = main(
        [
            "--input-path",
            str(input_path),
            "--output-path",
            str(tmp_path / "output2.json"),
            "--created-at",
            FIXED_NOW.isoformat(),
        ]
    )
    assert rc_second == EXIT_OK
    assert output_path.read_text(encoding="utf-8") == (tmp_path / "output2.json").read_text(
        encoding="utf-8"
    )


def test_cli_missing_input_path_is_usage_error(tmp_path: Path) -> None:
    rc = main(
        [
            "--input-path",
            str(tmp_path / "missing.json"),
            "--output-path",
            str(tmp_path / "out.json"),
        ]
    )
    assert rc == EXIT_USAGE_ERROR
    assert not (tmp_path / "out.json").exists()


def test_cli_invalid_json_is_producer_error(tmp_path: Path, capsys) -> None:
    input_path = tmp_path / "bad.json"
    output_path = tmp_path / "out.json"
    input_path.write_text("{not-json", encoding="utf-8")

    rc = main(["--input-path", str(input_path), "--output-path", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()
    err = capsys.readouterr().err
    assert "ERROR:" in err
    assert "secret" not in err.lower()


def test_cli_contract_violation_is_producer_error(tmp_path: Path, capsys) -> None:
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "out.json"
    bad = _valid_input()
    bad["lineage_manifest_id"] = "not-a-uuid"
    input_path.write_text(json.dumps(bad), encoding="utf-8")

    rc = main(
        [
            "--input-path",
            str(input_path),
            "--output-path",
            str(output_path),
            "--created-at",
            FIXED_NOW.isoformat(),
        ]
    )
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()
    assert "ERROR:" in capsys.readouterr().err


def test_cli_no_partial_output_on_validation_failure(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "out.json"
    bad = _valid_input()
    bad["refs"] = []
    input_path.write_text(json.dumps(bad), encoding="utf-8")

    rc = main(
        [
            "--input-path",
            str(input_path),
            "--output-path",
            str(output_path),
            "--created-at",
            FIXED_NOW.isoformat(),
        ]
    )
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".tmp").exists()


def test_cli_existing_output_atomically_replaced(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "out.json"
    input_path.write_text(json.dumps(_valid_input()), encoding="utf-8")
    output_path.write_text('{"stale": true}', encoding="utf-8")

    rc = main(
        [
            "--input-path",
            str(input_path),
            "--output-path",
            str(output_path),
            "--created-at",
            FIXED_NOW.isoformat(),
        ]
    )
    assert rc == EXIT_OK
    manifest = deserialize_candidate_lineage_manifest_v1(
        json.loads(output_path.read_text(encoding="utf-8"))
    )
    assert manifest.lineage_manifest_id == LINEAGE_ID


def test_cli_non_writable_output_directory(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    output_dir = tmp_path / "readonly"
    output_dir.mkdir()
    output_path = output_dir / "out.json"
    input_path.write_text(json.dumps(_valid_input()), encoding="utf-8")
    os.chmod(output_dir, stat.S_IRUSR | stat.S_IXUSR)

    try:
        rc = main(
            [
                "--input-path",
                str(input_path),
                "--output-path",
                str(output_path),
                "--created-at",
                FIXED_NOW.isoformat(),
            ]
        )
    finally:
        os.chmod(output_dir, stat.S_IRWXU)

    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()


def test_cli_validation_error_reports_verdict_on_stderr(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "out.json"
    input_path.write_text(json.dumps(_valid_input()), encoding="utf-8")

    def _raise_validation(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise CandidateLineageManifestValidationError(
            "forced validation failure",
            phase=__import__(
                "src.meta.learning_loop.contract_safety_v1",
                fromlist=["ValidationPhase"],
            ).ValidationPhase.RESULT,
            errors=("forced",),
            verdict="FORCED_VERDICT",
        )

    monkeypatch.setattr(
        "scripts.run_candidate_lineage_manifest_v1.produce_candidate_lineage_manifest_v1_from_paths",
        _raise_validation,
    )

    rc = main(["--input-path", str(input_path), "--output-path", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    err = capsys.readouterr().err
    assert "VALIDATION_ERROR" in err
    assert "VERDICT=FORCED_VERDICT" in err
