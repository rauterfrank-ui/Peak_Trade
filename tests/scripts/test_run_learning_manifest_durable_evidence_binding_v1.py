"""CLI tests for Package G offline learning manifest durable evidence binding v1."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.run_learning_manifest_durable_evidence_binding_v1 import (
    EXIT_BINDING_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    build_candidate_lineage_manifest_v1_from_producer_input,
    write_candidate_lineage_manifest_v1_atomic,
)
from src.meta.learning_loop.config_patch_manifest_v1 import build_empty_config_patch_manifest_v1
from src.meta.learning_loop.manifest_bridge_v1 import write_config_patch_manifest_v1_atomic
from src.meta.learning_loop.manifest_durable_evidence_binding_v1 import INDEX_ARTIFACT_REL

FIXED_NOW = datetime(2026, 6, 27, 19, 0, 0, tzinfo=timezone.utc)
CONFIG_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
LINEAGE_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
CONTRACT_REF = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.manifest_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )


def _write_manifest_pair(tmp_path: Path) -> tuple[Path, Path, Path]:
    sources = tmp_path / "sources"
    sources.mkdir(exist_ok=True)
    config_path = sources / "config_patch.json"
    lineage_path = sources / "lineage.json"
    config = build_empty_config_patch_manifest_v1(
        manifest_id=CONFIG_ID,
        lineage_manifest_ref=LINEAGE_ID,
        generated_at=FIXED_NOW,
    )
    write_config_patch_manifest_v1_atomic(config, config_path)
    lineage = build_candidate_lineage_manifest_v1_from_producer_input(
        {
            "lineage_manifest_id": LINEAGE_ID,
            "candidate_id": "cli-candidate",
            "candidate_type": "config_patch_bundle",
            "candidate_contract_ref": CONTRACT_REF,
            "refs": [
                {
                    "ref_type": "experiment",
                    "ref_id": "exp-cli",
                    "relation": "sources",
                    "owner_domain": "experiments/base",
                    "required": True,
                }
            ],
            "created_at": FIXED_NOW.isoformat(),
        },
        created_at=FIXED_NOW,
    )
    write_candidate_lineage_manifest_v1_atomic(lineage, lineage_path)
    out_root = tmp_path / "evidence_root"
    out_root.mkdir(exist_ok=True)
    return config_path, lineage_path, out_root


def test_cli_successful_run(tmp_path: Path) -> None:
    config_path, lineage_path, out_root = _write_manifest_pair(tmp_path)
    out = out_root / "bundle_out"
    rc = main(
        [
            "--config-patch-manifest",
            str(config_path),
            "--candidate-lineage-manifest",
            str(lineage_path),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    assert (out / INDEX_ARTIFACT_REL).is_file()


def test_cli_requires_all_three_paths() -> None:
    with pytest.raises(SystemExit):
        main([])


def test_cli_missing_config_manifest_usage_error(tmp_path: Path) -> None:
    _, lineage_path, out_root = _write_manifest_pair(tmp_path)
    rc = main(
        [
            "--config-patch-manifest",
            str(tmp_path / "missing.json"),
            "--candidate-lineage-manifest",
            str(lineage_path),
            "--output-dir",
            str(out_root / "out"),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_missing_lineage_manifest_usage_error(tmp_path: Path) -> None:
    config_path, _, out_root = _write_manifest_pair(tmp_path)
    rc = main(
        [
            "--config-patch-manifest",
            str(config_path),
            "--candidate-lineage-manifest",
            str(tmp_path / "missing.json"),
            "--output-dir",
            str(out_root / "out"),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_invalid_json_binding_error(tmp_path: Path) -> None:
    config_path = tmp_path / "bad.json"
    config_path.write_text("{broken", encoding="utf-8")
    _, lineage_path, out_root = _write_manifest_pair(tmp_path)
    rc = main(
        [
            "--config-patch-manifest",
            str(config_path),
            "--candidate-lineage-manifest",
            str(lineage_path),
            "--output-dir",
            str(out_root / "out"),
        ]
    )
    assert rc == EXIT_BINDING_ERROR


def test_cli_ref_inconsistency_binding_error(tmp_path: Path) -> None:
    config_path, lineage_path, out_root = _write_manifest_pair(tmp_path)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["lineage_manifest_ref"] = "99999999-9999-4999-8999-999999999999"
    config_path.write_text(json.dumps(payload), encoding="utf-8")
    rc = main(
        [
            "--config-patch-manifest",
            str(config_path),
            "--candidate-lineage-manifest",
            str(lineage_path),
            "--output-dir",
            str(out_root / "out"),
        ]
    )
    assert rc == EXIT_BINDING_ERROR


def test_cli_existing_output_binding_error(tmp_path: Path) -> None:
    config_path, lineage_path, out_root = _write_manifest_pair(tmp_path)
    out = out_root / "exists"
    out.mkdir()
    rc = main(
        [
            "--config-patch-manifest",
            str(config_path),
            "--candidate-lineage-manifest",
            str(lineage_path),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_BINDING_ERROR


def test_cli_stderr_has_no_full_payload_dump(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path, lineage_path, out_root = _write_manifest_pair(tmp_path)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["lineage_manifest_ref"] = "99999999-9999-4999-8999-999999999999"
    config_path.write_text(json.dumps(payload), encoding="utf-8")
    rc = main(
        [
            "--config-patch-manifest",
            str(config_path),
            "--candidate-lineage-manifest",
            str(lineage_path),
            "--output-dir",
            str(out_root / "out"),
        ]
    )
    assert rc == EXIT_BINDING_ERROR
    err = capsys.readouterr().err
    assert "patches" not in err
    assert len(err) < 500


def test_cli_no_network_or_promotion_side_effects(tmp_path: Path) -> None:
    config_path, lineage_path, out_root = _write_manifest_pair(tmp_path)
    out = out_root / "bundle"
    with patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")):
        rc = main(
            [
                "--config-patch-manifest",
                str(config_path),
                "--candidate-lineage-manifest",
                str(lineage_path),
                "--output-dir",
                str(out),
            ]
        )
    assert rc == EXIT_OK


def test_cli_deterministic_output(tmp_path: Path) -> None:
    config_path, lineage_path, out_root = _write_manifest_pair(tmp_path)
    out1 = out_root / "bundle1"
    out2 = out_root / "bundle2"
    assert (
        main(
            [
                "--config-patch-manifest",
                str(config_path),
                "--candidate-lineage-manifest",
                str(lineage_path),
                "--output-dir",
                str(out1),
            ]
        )
        == EXIT_OK
    )
    assert (
        main(
            [
                "--config-patch-manifest",
                str(config_path),
                "--candidate-lineage-manifest",
                str(lineage_path),
                "--output-dir",
                str(out2),
            ]
        )
        == EXIT_OK
    )
    assert (out1 / INDEX_ARTIFACT_REL).read_bytes() == (out2 / INDEX_ARTIFACT_REL).read_bytes()
