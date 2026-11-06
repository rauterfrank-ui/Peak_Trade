"""Contract tests for OKX self-accumulated forward OI archive correction and executable binding v0."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    COLLECTION_MODE_FORWARD_ONLY,
    InstrumentArchiveStateV0,
    append_forward_observation_v0,
    compute_observation_digest_v0,
    normalize_forward_open_interest_observation_v0,
    persist_archive_snapshot_v0,
    write_manifest_sha256_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_correction_and_executable_binding_v0 import (
    ARCHIVE_OWNER,
    CONFIRM_GO,
    EXTERNAL_REFERENCE_OWNER,
    FORBIDDEN_EXTERNAL_REFERENCE_AS_SELF_SOURCE,
    MODULE_VERSION,
    PERMITTED_COLLECTOR_ENTRY_POINT,
    PERMITTED_OVERLAP_ENTRY_POINT,
    ArchiveObservationAdmissibilityV0,
    BindingValidationVerdict,
    ExternalReferenceUsageV0,
    GenerationModeV0,
    MaterializationTerminalStatus,
    SourceModeV0,
    assess_observation_admissibility_v0,
    build_contract_config_v0,
    build_correction_execution_plan_v0,
    build_executable_binding_v0,
    build_generation_binding_v0,
    build_observation_provenance_v0,
    build_supersession_record_v0,
    classify_admissibility_v0,
    compute_executable_binding_digest_v0,
    compute_generation_digest_v0,
    compute_implementation_digest_v0,
    compute_provenance_digest_v0,
    compute_supersession_digest_v0,
    executable_binding_eligible_v0,
    materialize_contract_bundle_v0,
    materialization_result_to_dict_v0,
    production_snapshot_path_claims_authority,
    validate_executable_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    REPO_ROOT / "config/research/"
    "okx_self_accumulated_forward_open_interest_archive_correction_and_executable_binding_v0.json"
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


def _observation_row(ts_utc: str, oi: str = "1234.5") -> dict[str, str | int]:
    payload = {
        "instrument_id": "okx:linear_perpetual:ETH:USDT:USDT:perp",
        "native_instrument_id": "ETH-USDT-SWAP",
        "venue_timestamp_ms": _ms(ts_utc),
        "venue_timestamp_utc": ts_utc,
        "collected_at_ms": _ms("2026-07-11T18:01:17Z"),
        "collected_at_utc": "2026-07-11T18:01:17Z",
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


def _fixture_binding(tmp_path: Path) -> dict[str, object]:
    fixture_path = tmp_path / "fixture.json"
    fixture_path.write_text(
        json.dumps({"code": "0", "data": [[str(_ms("2026-07-11T11:00:00Z")), "1234.5", "1", "2"]]}),
        encoding="utf-8",
    )
    return {
        "enable_live_fetch": False,
        "fixture_response": str(fixture_path),
        "mode": "collect-once",
        "network_allowed": False,
    }


class TestConfigAndDigests:
    def test_config_matches_module(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        module_config = build_contract_config_v0()
        assert config["go_token"] == CONFIRM_GO
        assert config["archive_owner"] == ARCHIVE_OWNER
        assert config["external_reference_owner"] == EXTERNAL_REFERENCE_OWNER
        assert config["append_only"] is True
        assert config["conflict_overwrite_allowed"] is False
        assert config["correction_execution_authorized"] is False
        assert module_config["implementation_digest"] == compute_implementation_digest_v0()

    def test_implementation_digest_deterministic(self) -> None:
        assert compute_implementation_digest_v0() == compute_implementation_digest_v0()

    def test_no_runtime_or_scheduler_imports(self) -> None:
        module_path = (
            REPO_ROOT / "src/research/"
            "okx_self_accumulated_forward_open_interest_archive_correction_and_executable_binding_v0.py"
        )
        source = module_path.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source


class TestAdmissibilityAndProvenance:
    def test_fixture_observation_rejected_as_production_admissible(self, tmp_path: Path) -> None:
        row = _observation_row("2026-07-11T11:00:00Z")
        assessment = assess_observation_admissibility_v0(
            row,
            collection_binding=_fixture_binding(tmp_path),
            evidence_ref="/tmp/evidence",
            collection_execution_id="exec-fixture-1",
            snapshot_path="/datasets/production_snapshot",
        )
        assert (
            assessment.admissibility
            == ArchiveObservationAdmissibilityV0.FIXTURE_NON_PRODUCTION.value
        )
        assert assessment.executable_binding_eligible is False

    def test_production_snapshot_path_name_does_not_override_fixture_provenance(self) -> None:
        assert production_snapshot_path_claims_authority("/datasets/production_snapshot") is False

    def test_unknown_provenance_blocks_executable_binding(self) -> None:
        provenance = build_observation_provenance_v0(
            _observation_row("2026-07-11T11:00:00Z"),
            collection_binding={"enable_live_fetch": False},
            evidence_ref=None,
            collection_execution_id="exec-unknown",
        )
        assert (
            classify_admissibility_v0(provenance)
            == ArchiveObservationAdmissibilityV0.UNKNOWN_BLOCKED.value
        )
        assert executable_binding_eligible_v0(classify_admissibility_v0(provenance)) is False

    def test_live_fetch_production_admissible(self) -> None:
        provenance = build_observation_provenance_v0(
            _observation_row("2026-07-11T11:00:00Z", "7193416.08"),
            collection_binding={"enable_live_fetch": True, "fixture_source_used": False},
            evidence_ref=None,
            collection_execution_id="exec-live-1",
        )
        assert (
            classify_admissibility_v0(provenance)
            == ArchiveObservationAdmissibilityV0.PRODUCTION_ADMISSIBLE.value
        )
        assert executable_binding_eligible_v0(classify_admissibility_v0(provenance)) is True

    def test_provenance_digest_stable(self, tmp_path: Path) -> None:
        provenance = build_observation_provenance_v0(
            _observation_row("2026-07-11T11:00:00Z"),
            collection_binding=_fixture_binding(tmp_path),
            evidence_ref="/tmp/evidence",
            collection_execution_id="exec-fixture-1",
        )
        assert compute_provenance_digest_v0(provenance) == compute_provenance_digest_v0(provenance)


class TestGenerationSupersessionAndBinding:
    def test_generation_and_supersession_digests_stable(self) -> None:
        generation = build_generation_binding_v0(
            generation_id="gen-1",
            parent_generation_id=None,
            generation_mode=GenerationModeV0.CORRECTION.value,
            source_observation_refs=("obs-1",),
            excluded_observation_refs=("obs-1",),
            supersession_record_refs=("sup-1",),
            created_by_owner=MODULE_VERSION,
            created_at_utc="2026-07-11T19:00:00Z",
        )
        assert generation.generation_digest == compute_generation_digest_v0(generation)
        record = build_supersession_record_v0(
            superseded_observation_ref="obs-1",
            replacement_observation_ref=None,
            supersession_reason="FIXTURE_NON_PRODUCTION_REQUIRES_CORRECTED_GENERATION",
        )
        assert record.historical_record_preserved is True
        assert record.in_place_mutation is False
        assert record.supersession_digest == compute_supersession_digest_v0(record)

    def test_executable_binding_rejects_external_reference_as_self_source(
        self, tmp_path: Path
    ) -> None:
        row = _observation_row("2026-07-11T11:00:00Z")
        assessment = assess_observation_admissibility_v0(
            row,
            collection_binding=_fixture_binding(tmp_path),
            evidence_ref="/tmp/evidence",
            collection_execution_id="exec-fixture-1",
        )
        binding = build_executable_binding_v0(
            input_archive_generation_id="gen-input",
            output_archive_generation_id="gen-output",
        )
        result = validate_executable_binding_v0(
            binding,
            admissibility_assessments=(assessment,),
            external_reference_owner=FORBIDDEN_EXTERNAL_REFERENCE_AS_SELF_SOURCE,
        )
        assert result.verdict == BindingValidationVerdict.PASS
        assert binding.external_reference_usage == ExternalReferenceUsageV0.VALIDATION_ONLY.value
        assert binding.overwrite_allowed is False
        assert binding.historical_evidence_preserved is True

    def test_stale_binding_digest_rejected(self) -> None:
        binding = build_executable_binding_v0(
            input_archive_generation_id="gen-input",
            output_archive_generation_id="gen-output",
        )
        stale_binding = type(binding)(
            permitted_entry_point=binding.permitted_entry_point,
            allowed_source_modes=binding.allowed_source_modes,
            required_provenance_fields=binding.required_provenance_fields,
            required_admissibility=binding.required_admissibility,
            input_archive_generation_id=binding.input_archive_generation_id,
            output_archive_generation_id=binding.output_archive_generation_id,
            external_reference_usage=binding.external_reference_usage,
            overwrite_allowed=binding.overwrite_allowed,
            historical_evidence_preserved=binding.historical_evidence_preserved,
            expected_overlap_policy=binding.expected_overlap_policy,
            expected_deterministic_second_run=binding.expected_deterministic_second_run,
            executable_binding_digest="deadbeef",
        )
        result = validate_executable_binding_v0(stale_binding, admissibility_assessments=())
        assert result.verdict == BindingValidationVerdict.FAIL
        assert "EXECUTABLE_BINDING_DIGEST_MISMATCH" in result.reason_codes
        assert binding.executable_binding_digest == compute_executable_binding_digest_v0(binding)


class TestMaterializationAndExecutionPlan:
    def _write_snapshot(self, tmp_path: Path) -> Path:
        snapshot_dir = tmp_path / "production_snapshot"
        state = InstrumentArchiveStateV0(
            instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
            native_instrument_id="ETH-USDT-SWAP",
        )
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
        persist_archive_snapshot_v0([state], output_dir=snapshot_dir)
        write_manifest_sha256_v0(snapshot_dir)
        return snapshot_dir

    def test_materialize_fixture_snapshot_complete(self, tmp_path: Path) -> None:
        snapshot_dir = self._write_snapshot(tmp_path)
        binding_path = tmp_path / "collection_binding.json"
        binding_path.write_text(json.dumps(_fixture_binding(tmp_path)), encoding="utf-8")
        result = materialize_contract_bundle_v0(
            confirm=CONFIRM_GO,
            enabled=True,
            source_snapshot_dir=snapshot_dir,
            collection_binding_path=binding_path,
            evidence_ref="/tmp/evidence",
            collection_execution_id="exec-fixture-1",
            created_at_utc="2026-07-11T19:00:00Z",
            external_reference_input="/tmp/external_ref",
        )
        assert result.status == MaterializationTerminalStatus.COMPLETE
        assert result.authority_effect == "NONE"
        assert result.runtime_effect == "NONE"
        assert len(result.supersession_records) == 2
        assert result.correction_execution_plan["execution_authorized"] is False
        assert (
            result.correction_execution_plan["validation_entry_point"]
            == PERMITTED_OVERLAP_ENTRY_POINT
        )
        assert (
            result.correction_execution_plan["permitted_entry_point"]
            == PERMITTED_COLLECTOR_ENTRY_POINT
        )
        assert (
            result.correction_execution_plan["external_reference_usage"]
            == ExternalReferenceUsageV0.VALIDATION_ONLY.value
        )

    def test_deterministic_materialization_second_run_diff_empty(self, tmp_path: Path) -> None:
        snapshot_dir = self._write_snapshot(tmp_path)
        binding_path = tmp_path / "collection_binding.json"
        binding_path.write_text(json.dumps(_fixture_binding(tmp_path)), encoding="utf-8")
        kwargs = dict(
            confirm=CONFIRM_GO,
            enabled=True,
            source_snapshot_dir=snapshot_dir,
            collection_binding_path=binding_path,
            evidence_ref="/tmp/evidence",
            collection_execution_id="exec-fixture-1",
            created_at_utc="2026-07-11T19:00:00Z",
            external_reference_input="/tmp/external_ref",
        )
        comparable_first = materialization_result_to_dict_v0(
            materialize_contract_bundle_v0(**kwargs)
        )
        comparable_second = materialization_result_to_dict_v0(
            materialize_contract_bundle_v0(**kwargs)
        )
        assert json.dumps(comparable_first, sort_keys=True) == json.dumps(
            comparable_second, sort_keys=True
        )

    def test_default_off_fail_closed(self, tmp_path: Path) -> None:
        result = materialize_contract_bundle_v0(
            confirm=CONFIRM_GO,
            enabled=False,
            source_snapshot_dir=tmp_path,
            collection_binding_path=tmp_path / "missing.json",
            evidence_ref=None,
            collection_execution_id="exec-off",
            created_at_utc="2026-07-11T19:00:00Z",
        )
        assert result.status == MaterializationTerminalStatus.FAIL_CLOSED_DEFAULT_OFF

    def test_correction_plan_not_authorized(self, tmp_path: Path) -> None:
        generation = build_generation_binding_v0(
            generation_id="gen-1",
            parent_generation_id=None,
            generation_mode=GenerationModeV0.CORRECTION.value,
            source_observation_refs=("obs-1", "obs-2"),
            excluded_observation_refs=("obs-1", "obs-2"),
            supersession_record_refs=("sup-1", "sup-2"),
            created_by_owner=MODULE_VERSION,
            created_at_utc="2026-07-11T19:00:00Z",
        )
        assessment = assess_observation_admissibility_v0(
            _observation_row("2026-07-11T11:00:00Z"),
            collection_binding=_fixture_binding(tmp_path),
            evidence_ref="/tmp/evidence",
            collection_execution_id="exec-fixture-1",
        )
        binding = build_executable_binding_v0(
            input_archive_generation_id="gen-1",
            output_archive_generation_id="gen-1:corrected_v0",
        )
        plan = build_correction_execution_plan_v0(
            source_generation=generation,
            admissibility_assessments=(assessment,),
            executable_binding=binding,
            external_reference_input="/tmp/external_ref",
        )
        assert plan["execution_authorized"] is False
        assert plan["historical_evidence_preservation"] is True

    def test_append_only_no_overwrite_invariant(self) -> None:
        config = build_contract_config_v0()
        assert config["append_only"] is True
        assert config["conflict_overwrite_allowed"] is False
        assert config["historical_evidence_preserved"] is True

    def test_external_reference_allowed_only_for_validation(self) -> None:
        config = build_contract_config_v0()
        assert config["external_reference_usage"] == ExternalReferenceUsageV0.VALIDATION_ONLY.value

    def test_unknown_source_mode_classification(self) -> None:
        provenance = build_observation_provenance_v0(
            _observation_row("2026-07-11T11:00:00Z"),
            collection_binding={"enable_live_fetch": False},
            evidence_ref=None,
            collection_execution_id="exec-unknown",
        )
        assert provenance.source_mode == SourceModeV0.UNKNOWN.value
