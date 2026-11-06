"""Contract tests for OKX self-accumulated forward OI archive correction execution v0."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.research.okx_self_accumulated_forward_open_interest_archive_correction_and_executable_binding_v0 import (
    BOUND_EXECUTION_PLAN_SCHEMA_VERSION,
    CONFIRM_GO_EXECUTION,
    CORRECTED_OBSERVATIONS_JSONL_FILENAME,
    CORRECTION_ENTRY_POINT,
    SUPERSESSION_RECORDS_JSONL_FILENAME,
    CorrectionExecutionTerminalStatus,
    execute_archive_correction_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    COLLECTION_MODE_FORWARD_ONLY,
    InstrumentArchiveStateV0,
    append_forward_observation_v0,
    compute_observation_digest_v0,
    normalize_forward_open_interest_observation_v0,
    persist_archive_snapshot_v0,
    write_manifest_sha256_v0,
)
from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / CORRECTION_ENTRY_POINT
CONFIG_PATH = (
    REPO_ROOT
    / "config/research/okx_self_accumulated_forward_open_interest_archive_correction_and_executable_binding_v0.json"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
)


def _ms(utc: str) -> int:
    return int(
        datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000
    )


def _observation_row(ts_utc: str, oi: str, collected_at_utc: str = "2026-07-11T19:30:00Z") -> dict:
    payload = {
        "instrument_id": "okx:linear_perpetual:ETH:USDT:USDT:perp",
        "native_instrument_id": "ETH-USDT-SWAP",
        "venue_timestamp_ms": _ms(ts_utc),
        "venue_timestamp_utc": ts_utc,
        "collected_at_ms": _ms(collected_at_utc),
        "collected_at_utc": collected_at_utc,
        "open_interest_raw": oi,
        "open_interest_unit": "okx_native_contract_count",
        "bar_interval": "PT1H",
        "source_schema_version": "okx_rubik_open_interest_history.v0",
        "source_endpoint": "/api/v5/rubik/stat/contracts/open-interest-history",
        "source_record_key": f"ETH-USDT-SWAP:{_ms(ts_utc)}",
        "collection_mode": COLLECTION_MODE_FORWARD_ONLY,
    }
    payload["observation_digest"] = compute_observation_digest_v0(payload)
    return payload


def _write_fixture_archive(tmp_path: Path) -> tuple[Path, list[dict]]:
    snapshot_dir = tmp_path / "archive"
    state = InstrumentArchiveStateV0(
        instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
        native_instrument_id="ETH-USDT-SWAP",
    )
    rows: list[dict] = []
    for ts, oi in (
        ("2026-07-11T11:00:00Z", "1234.5"),
        ("2026-07-11T12:00:00Z", "1350.0"),
    ):
        row = [str(_ms(ts)), oi, "100.0", "2000000.0"]
        obs = normalize_forward_open_interest_observation_v0(
            row,
            instrument_id=state.instrument_id,
            native_instrument_id=state.native_instrument_id,
            collected_at_utc="2026-07-11T18:10:07Z",
        )
        assert obs is not None
        append_forward_observation_v0(state, obs, preconditions_checked=True)
        rows.append(
            {
                "instrument_id": obs.instrument_id,
                "native_instrument_id": obs.native_instrument_id,
                "venue_timestamp_ms": obs.venue_timestamp_ms,
                "venue_timestamp_utc": obs.venue_timestamp_utc,
                "collected_at_ms": obs.collected_at_ms,
                "collected_at_utc": obs.collected_at_utc,
                "open_interest_raw": obs.open_interest_raw,
                "open_interest_unit": obs.open_interest_unit,
                "bar_interval": obs.bar_interval,
                "source_schema_version": obs.source_schema_version,
                "source_endpoint": obs.source_endpoint,
                "source_record_key": obs.source_record_key,
                "collection_mode": obs.collection_mode,
                "observation_digest": obs.observation_digest,
            }
        )
    persist_archive_snapshot_v0([state], output_dir=snapshot_dir)
    write_manifest_sha256_v0(snapshot_dir)
    return snapshot_dir, rows


def _write_external_reference(tmp_path: Path) -> Path:
    ref_dir = tmp_path / "external_ref"
    ref_dir.mkdir(parents=True)
    rows = [
        _observation_row("2026-07-11T11:00:00Z", "7193416.080000025"),
        _observation_row("2026-07-11T12:00:00Z", "7211803.7800000251"),
    ]
    (ref_dir / "observations.jsonl").write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    return ref_dir


def _bound_plan(
    tmp_path: Path,
    archive_dir: Path,
    fixture_rows: list[dict],
    *,
    execution_authorized: bool = True,
    operator_go: str = CONFIRM_GO_EXECUTION,
    before_digest: str | None = None,
    external_ref: Path | None = None,
    self_source: str | None = None,
) -> Path:
    if before_digest is None:
        manifest = json.loads((archive_dir / "archive_manifest.json").read_text(encoding="utf-8"))
        before_digest = manifest["archive_digest"]
    corrected = [
        _observation_row("2026-07-11T11:00:00Z", "7193416.080000025"),
        _observation_row("2026-07-11T12:00:00Z", "7211803.7800000251"),
    ]
    if external_ref is None:
        external_ref = _write_external_reference(tmp_path)
    plan = {
        "schema_version": BOUND_EXECUTION_PLAN_SCHEMA_VERSION,
        "operator_go": operator_go,
        "execution_authorized": execution_authorized,
        "target_archive_path": str(archive_dir),
        "before_archive_digest": before_digest,
        "expected_after_archive_digest": f"{before_digest}:corrected_v0",
        "external_reference_input": str(external_ref),
        "external_reference_as_self_source_allowed": False,
        "self_observation_source": self_source,
        "fixture_observations_to_preserve": [row["observation_digest"] for row in fixture_rows],
        "corrected_observations": corrected,
        "collection_binding": {
            "enable_live_fetch": True,
            "fixture_source_used": False,
            "network_allowed": True,
        },
        "collection_execution_id": "exec-live-correction-1",
        "evidence_ref": str(tmp_path / "evidence"),
        "executable_binding": {
            "overwrite_allowed": False,
            "external_reference_usage": "VALIDATION_ONLY",
            "historical_evidence_preserved": True,
        },
        "supersession_records": [
            {
                "superseded_observation_ref": fixture_rows[0]["observation_digest"],
                "replacement_observation_ref": None,
                "supersession_reason": "FIXTURE_NON_PRODUCTION_REQUIRES_CORRECTED_GENERATION",
            },
            {
                "superseded_observation_ref": fixture_rows[1]["observation_digest"],
                "replacement_observation_ref": None,
                "supersession_reason": "FIXTURE_NON_PRODUCTION_REQUIRES_CORRECTED_GENERATION",
            },
        ],
        "generation_binding": {
            "generation_id": f"{before_digest}:corrected_v0",
            "parent_generation_id": before_digest,
            "generation_mode": "CORRECTION",
        },
    }
    plan_path = tmp_path / "bound_plan.json"
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return plan_path


def _run_cli(
    tmp_path: Path, archive_dir: Path, plan_path: Path, *extra: str
) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        str(CLI_PATH),
        "--confirm-go-token",
        CONFIRM_GO_EXECUTION,
        "--bound-plan",
        str(plan_path),
        "--target-archive",
        str(archive_dir),
        *extra,
    ]
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


class TestConfigAndImports:
    def test_config_binds_entry_point_and_go_token(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        assert config["correction_execution_entry_point"] == CORRECTION_ENTRY_POINT
        assert config["correction_execution_go_token"] == CONFIRM_GO_EXECUTION
        assert config["correction_execution_validate_only_default"] is True
        assert config["explicit_mutation_flag_required"] is True
        assert config["no_archive_correction_execution"] is True
        assert config["correction_execution_authorized"] is False

    def test_no_runtime_imports(self) -> None:
        module_path = REPO_ROOT / (
            "src/research/okx_self_accumulated_forward_open_interest_archive_correction_and_executable_binding_v0.py"
        )
        cli_source = CLI_PATH.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in module_path.read_text(encoding="utf-8")
            assert prefix not in cli_source


class TestAuthorityAndRejection:
    def test_missing_go_token_rejected(self, tmp_path: Path) -> None:
        archive_dir, fixture_rows = _write_fixture_archive(tmp_path)
        plan_path = _bound_plan(tmp_path, archive_dir, fixture_rows)
        result = subprocess.run(
            [
                sys.executable,
                str(CLI_PATH),
                "--bound-plan",
                str(plan_path),
                "--target-archive",
                str(archive_dir),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0

    def test_wrong_go_token_rejected(self, tmp_path: Path) -> None:
        archive_dir, fixture_rows = _write_fixture_archive(tmp_path)
        plan_path = _bound_plan(tmp_path, archive_dir, fixture_rows)
        result = _run_cli(tmp_path, archive_dir, plan_path, "--confirm-go-token", "GO_WRONG")
        assert result.returncode == 2

    def test_unbound_go_token_rejected(self, tmp_path: Path) -> None:
        archive_dir, fixture_rows = _write_fixture_archive(tmp_path)
        plan_path = _bound_plan(
            tmp_path,
            archive_dir,
            fixture_rows,
            operator_go="GO_UNBOUND_TOKEN",
        )
        result = execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=True,
            execute_mutation=False,
            enabled=False,
            bound_plan_path=plan_path,
            target_archive_path=archive_dir,
        )
        assert result.status == CorrectionExecutionTerminalStatus.FAIL_CLOSED_PLAN_BINDING
        assert "PLAN_OPERATOR_GO_MISMATCH" in result.reason_codes

    def test_plan_execution_authorized_false_rejected(self, tmp_path: Path) -> None:
        archive_dir, fixture_rows = _write_fixture_archive(tmp_path)
        plan_path = _bound_plan(
            tmp_path,
            archive_dir,
            fixture_rows,
            execution_authorized=False,
        )
        result = execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=True,
            execute_mutation=False,
            enabled=False,
            bound_plan_path=plan_path,
            target_archive_path=archive_dir,
        )
        assert result.status == CorrectionExecutionTerminalStatus.FAIL_CLOSED_PLAN_BINDING
        assert "PLAN_EXECUTION_NOT_AUTHORIZED" in result.reason_codes

    def test_validate_only_default_no_mutation(self, tmp_path: Path) -> None:
        archive_dir, fixture_rows = _write_fixture_archive(tmp_path)
        plan_path = _bound_plan(tmp_path, archive_dir, fixture_rows)
        before = (archive_dir / "observations.jsonl").read_bytes()
        result = _run_cli(tmp_path, archive_dir, plan_path)
        after = (archive_dir / "observations.jsonl").read_bytes()
        assert result.returncode == 0
        assert before == after
        assert not (archive_dir / CORRECTED_OBSERVATIONS_JSONL_FILENAME).exists()

    def test_explicit_mutation_flag_required(self, tmp_path: Path) -> None:
        archive_dir, fixture_rows = _write_fixture_archive(tmp_path)
        plan_path = _bound_plan(tmp_path, archive_dir, fixture_rows)
        result = _run_cli(
            tmp_path,
            archive_dir,
            plan_path,
            "--execute-mutation",
        )
        assert result.returncode != 0
        assert "EXECUTE_MUTATION_REQUIRES_ENABLED_FLAG" in result.stderr

    def test_source_manifest_failure_rejected(self, tmp_path: Path) -> None:
        archive_dir, fixture_rows = _write_fixture_archive(tmp_path)
        plan_path = _bound_plan(tmp_path, archive_dir, fixture_rows)
        bad_manifest_dir = tmp_path / "bad_manifest"
        bad_manifest_dir.mkdir()
        (bad_manifest_dir / "MANIFEST.sha256").write_text(
            "deadbeef  missing.txt\n", encoding="utf-8"
        )
        result = execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=True,
            execute_mutation=False,
            enabled=False,
            bound_plan_path=plan_path,
            target_archive_path=archive_dir,
            source_manifest_dirs=(bad_manifest_dir,),
        )
        assert result.status == CorrectionExecutionTerminalStatus.FAIL_CLOSED_PLAN_BINDING
        assert any("SOURCE_MANIFEST_VERIFY_FAIL" in code for code in result.reason_codes)

    def test_wrong_target_archive_rejected(self, tmp_path: Path) -> None:
        archive_dir, fixture_rows = _write_fixture_archive(tmp_path)
        other_dir, _ = _write_fixture_archive(tmp_path / "other")
        plan_path = _bound_plan(tmp_path, archive_dir, fixture_rows)
        result = execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=True,
            execute_mutation=False,
            enabled=False,
            bound_plan_path=plan_path,
            target_archive_path=other_dir,
        )
        assert result.status == CorrectionExecutionTerminalStatus.FAIL_CLOSED_PLAN_BINDING
        assert "TARGET_ARCHIVE_PATH_MISMATCH" in result.reason_codes

    def test_before_digest_mismatch_rejected(self, tmp_path: Path) -> None:
        archive_dir, fixture_rows = _write_fixture_archive(tmp_path)
        plan_path = _bound_plan(
            tmp_path,
            archive_dir,
            fixture_rows,
            before_digest="deadbeef",
        )
        result = execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=True,
            execute_mutation=False,
            enabled=False,
            bound_plan_path=plan_path,
            target_archive_path=archive_dir,
        )
        assert "BEFORE_ARCHIVE_DIGEST_MISMATCH" in result.reason_codes

    def test_external_reference_as_self_source_rejected(self, tmp_path: Path) -> None:
        archive_dir, fixture_rows = _write_fixture_archive(tmp_path)
        external_ref = _write_external_reference(tmp_path)
        plan_path = _bound_plan(
            tmp_path,
            archive_dir,
            fixture_rows,
            external_ref=external_ref,
            self_source=str(external_ref),
        )
        result = execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=True,
            execute_mutation=False,
            enabled=False,
            bound_plan_path=plan_path,
            target_archive_path=archive_dir,
        )
        assert "EXTERNAL_REFERENCE_AS_SELF_SOURCE_BLOCKED" in result.reason_codes


class TestIntegrationExecution:
    def test_real_entry_point_append_only_supersession_and_idempotency(
        self, tmp_path: Path
    ) -> None:
        archive_dir, fixture_rows = _write_fixture_archive(tmp_path)
        plan_path = _bound_plan(tmp_path, archive_dir, fixture_rows)
        before_obs = (archive_dir / "observations.jsonl").read_text(encoding="utf-8")

        result = _run_cli(
            tmp_path,
            archive_dir,
            plan_path,
            "--execute-mutation",
            "--enabled",
        )
        assert result.returncode == 0, result.stderr + result.stdout
        payload = json.loads(result.stdout)
        assert payload["status"] == CorrectionExecutionTerminalStatus.EXECUTION_COMPLETE.value
        assert payload["authority_effect"] == "NONE"
        assert payload["runtime_effect"] == "NONE"
        assert payload["economic_evaluation_executed"] is False
        assert (archive_dir / "observations.jsonl").read_text(encoding="utf-8") == before_obs
        assert (archive_dir / CORRECTED_OBSERVATIONS_JSONL_FILENAME).is_file()
        assert (archive_dir / SUPERSESSION_RECORDS_JSONL_FILENAME).is_file()
        supersession_rows = [
            json.loads(line)
            for line in (archive_dir / SUPERSESSION_RECORDS_JSONL_FILENAME)
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        assert len(supersession_rows) == 2
        assert all(row["historical_record_preserved"] for row in supersession_rows)
        assert all(row["replacement_observation_ref"] for row in supersession_rows)

        repeat = _run_cli(
            tmp_path,
            archive_dir,
            plan_path,
            "--execute-mutation",
            "--enabled",
        )
        assert repeat.returncode == 0
        repeat_payload = json.loads(repeat.stdout)
        assert (
            repeat_payload["status"] == CorrectionExecutionTerminalStatus.ALREADY_APPLIED_NOOP.value
        )

    def test_deterministic_second_validate_only_diff_empty(self, tmp_path: Path) -> None:
        archive_dir, fixture_rows = _write_fixture_archive(tmp_path)
        plan_path = _bound_plan(tmp_path, archive_dir, fixture_rows)
        first = execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=True,
            execute_mutation=False,
            enabled=False,
            bound_plan_path=plan_path,
            target_archive_path=archive_dir,
        )
        second = execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=True,
            execute_mutation=False,
            enabled=False,
            bound_plan_path=plan_path,
            target_archive_path=archive_dir,
        )
        assert json.dumps(
            {
                "status": first.status.value,
                "reason_codes": list(first.reason_codes),
                "expected": first.expected_mutation_set,
            },
            sort_keys=True,
        ) == json.dumps(
            {
                "status": second.status.value,
                "reason_codes": list(second.reason_codes),
                "expected": second.expected_mutation_set,
            },
            sort_keys=True,
        )

    def test_conflict_overwrite_rejected(self, tmp_path: Path) -> None:
        archive_dir, fixture_rows = _write_fixture_archive(tmp_path)
        plan_path = _bound_plan(tmp_path, archive_dir, fixture_rows)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["executable_binding"]["overwrite_allowed"] = True
        plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        result = execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=True,
            execute_mutation=False,
            enabled=False,
            bound_plan_path=plan_path,
            target_archive_path=archive_dir,
        )
        assert "OVERWRITE_NOT_ALLOWED" in result.reason_codes

    def test_production_path_not_derived_from_fixture(self, tmp_path: Path) -> None:
        archive_dir, fixture_rows = _write_fixture_archive(tmp_path)
        plan_path = _bound_plan(tmp_path, archive_dir, fixture_rows)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        assert "production_snapshot" not in plan["target_archive_path"]
        result = execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=True,
            execute_mutation=False,
            enabled=False,
            bound_plan_path=plan_path,
            target_archive_path=archive_dir,
        )
        assert result.status == CorrectionExecutionTerminalStatus.VALIDATE_ONLY_PASS

    def test_plan_manifest_failure_rejected(self, tmp_path: Path) -> None:
        archive_dir, fixture_rows = _write_fixture_archive(tmp_path)
        manifest_dir = tmp_path / "source_manifest"
        manifest_dir.mkdir()
        (manifest_dir / "proof.txt").write_text("proof\n", encoding="utf-8")
        write_manifest_sha256(manifest_dir)
        (manifest_dir / "proof.txt").write_text("mutated\n", encoding="utf-8")
        plan_path = _bound_plan(tmp_path, archive_dir, fixture_rows)
        result = execute_archive_correction_v0(
            confirm=CONFIRM_GO_EXECUTION,
            validate_only=True,
            execute_mutation=False,
            enabled=False,
            bound_plan_path=plan_path,
            target_archive_path=archive_dir,
            source_manifest_dirs=(manifest_dir,),
        )
        assert result.status == CorrectionExecutionTerminalStatus.FAIL_CLOSED_PLAN_BINDING
