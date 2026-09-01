"""Offline DDO WP-FA-01/WP-FA-02 contract, hash, lineage and ledger tests."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    LEARNING_PRODUCTIVE_AUTHORITY,
    PROMOTION_AUTHORITY_EFFECT,
    RUNTIME_EFFECT,
    SECTION_11_13_5_DEPENDENCY,
)
from src.learning.deterministic_decision_outcome_v0.contract_registry_v0 import (
    CONTRACT_REGISTRY_V0,
    get_schema_contract_v0,
    hash_scope_fields_v0,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    DdoDuplicateConflictError,
    DdoIntegrityError,
    DdoLedgerCorruptionError,
    DdoLineageError,
    DdoMalformedRecordError,
    DdoUnsupportedSchemaVersionError,
    DdoValidationError,
)
from src.learning.deterministic_decision_outcome_v0.incident_record_v0 import (
    build_incident_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import (
    AppendOnlyDdoLedgerV0,
    canonical_json_dumps_v0,
    compute_content_hash_v0,
    validate_canonical_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.outcome_v0 import (
    build_outcome_record_v0,
    validate_outcome_ref_v0,
)
from src.learning.deterministic_decision_outcome_v0.reason_codes_v0 import (
    BLUEPRINT_HARD_BLOCK_TAXONOMY_ID,
    BLUEPRINT_REASON_TAXONOMY_ID,
    EXISTING_OPAQUE_TAXONOMY_ID,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    CANONICAL_JSON_ALGORITHM_ID,
    LEARNING_LOOP_ENSURE_ASCII_FALSE_DIALECT_IMPORTED,
    hash_scope_payload_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src" / "learning" / "deterministic_decision_outcome_v0"

FORBIDDEN_IMPORT_PREFIXES = (
    "src.trading",
    "src.execution",
    "src.live",
    "src.risk",
    "src.risk_layer",
    "src.governance.promotion",
    "src.meta.learning_loop",
    "src.ops",
    "urllib",
    "requests",
    "httpx",
    "aiohttp",
    "socket",
    "http.client",
)

FORBIDDEN_SUBSTRINGS = (
    "11.13.5",
    "section_11_13_5",
    "testnet",
    "canary",
)


def _reason(code: str = UNKNOWN) -> dict[str, str | None]:
    return {
        "taxonomy_id": BLUEPRINT_REASON_TAXONOMY_ID,
        "code": code,
        "source_taxonomy_ref": None,
    }


def _hard_block(code: str = UNKNOWN) -> dict[str, str | None]:
    return {
        "taxonomy_id": BLUEPRINT_HARD_BLOCK_TAXONOMY_ID,
        "code": code,
        "source_taxonomy_ref": None,
    }


def _decision(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_name": "decision_event",
        "schema_version": "decision_event_v0",
        "record_id": "dec-0001",
        "event_id": "evt-0001",
        "correlation_id": "cor-0001",
        "cycle_id": None,
        "event_time_utc": "2026-09-01T12:00:00Z",
        "decision_type": "NO_ENTRY",
        "decision_result": "NO_ACTION",
        "reason_codes": [_reason("NO_ENTRY")],
        "hard_block_reasons": [],
        "decision_time_information_set_ref": None,
        "market_snapshot_ref": None,
        "feature_snapshot_ref": None,
        "data_quality_ref": None,
        "risk_snapshot_ref": None,
        "position_snapshot_ref": None,
        "selected_instrument_ref": None,
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
        "authority_owner": UNKNOWN,
        "producer_id": "offline-test-producer",
        "evidence_hash": UNKNOWN,
        "causal_parent_ids": [],
        "evidence_source_refs": ["src-evidence-1"],
    }
    payload.update(overrides)
    return payload


def _incident(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_name": "incident_record",
        "schema_version": "incident_record_v0",
        "record_id": "inc-0001",
        "incident_id": "incd-0001",
        "correlation_id": "cor-0001",
        "cycle_id": None,
        "event_time_utc": "2026-09-01T12:00:01Z",
        "incident_class": "STALE",
        "reason_codes": [_reason("STALE_BLOCK")],
        "hard_block_reasons": [_hard_block("STALE_BLOCK")],
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
        "authority_owner": UNKNOWN,
        "producer_id": "offline-test-producer",
        "evidence_hash": UNKNOWN,
        "causal_parent_ids": ["dec-0001"],
        "evidence_source_refs": ["src-evidence-1"],
    }
    payload.update(overrides)
    return payload


def _outcome(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_name": "outcome_record",
        "schema_version": "outcome_record_v0",
        "record_id": "out-0001",
        "decision_event_ref": "dec-0001",
        "evaluation_horizon": UNKNOWN,
        "actual_outcome_ref": UNKNOWN,
        "counterfactual_admissibility": "UNAVAILABLE",
        "event_time_utc": "2026-09-01T12:00:02Z",
        "correlation_id": "cor-0001",
        "cycle_id": None,
        "causal_parent_ids": ["dec-0001"],
        "producer_id": "offline-test-producer",
        "authority_owner": UNKNOWN,
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
        "evidence_hash": UNKNOWN,
        "evidence_source_refs": ["src-evidence-1"],
    }
    payload.update(overrides)
    return payload


def test_runtime_effect_remains_none() -> None:
    assert RUNTIME_EFFECT == "NONE"
    assert PROMOTION_AUTHORITY_EFFECT == "NONE"
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert SECTION_11_13_5_DEPENDENCY == "NONE"
    assert CONTRACT_REGISTRY_V0["runtime_effect"] == "NONE"
    assert LEARNING_LOOP_ENSURE_ASCII_FALSE_DIALECT_IMPORTED is False
    assert CANONICAL_JSON_ALGORITHM_ID.endswith("ensure_ascii_true")


def test_schema_validation_and_explicit_nullability() -> None:
    record = build_decision_event_v0(_decision())
    assert record["cycle_id"] is None
    assert record["market_snapshot_ref"] is None
    assert record["reason_codes"][0]["code"] == "NO_ENTRY"
    omitted = _decision()
    omitted.pop("cycle_id")
    omitted.pop("plan_ref", None)
    canonical_omitted = build_decision_event_v0(omitted)
    assert canonical_omitted["cycle_id"] is None
    assert canonical_omitted["plan_ref"] is None
    assert canonical_omitted["content_hash"] == record["content_hash"]


def test_unknown_is_first_class_semantics() -> None:
    record = build_decision_event_v0(
        _decision(decision_type=UNKNOWN, decision_result=UNKNOWN, reason_codes=[_reason(UNKNOWN)])
    )
    assert record["decision_type"] == UNKNOWN
    assert record["code_sha"] == UNKNOWN
    with pytest.raises(DdoValidationError, match="INVALID_SHA256_OR_UNKNOWN"):
        build_decision_event_v0(_decision(code_sha="not-a-hash"))


def test_enum_and_version_handling() -> None:
    with pytest.raises(DdoValidationError, match="UNKNOWN_ENUM_VALUE"):
        build_decision_event_v0(_decision(decision_type="TRADE_ENTRY"))
    with pytest.raises(DdoUnsupportedSchemaVersionError):
        build_decision_event_v0(_decision(schema_version="decision_event_v1"))
    get_schema_contract_v0("decision_event", "decision_event_v0")
    with pytest.raises(DdoUnsupportedSchemaVersionError):
        get_schema_contract_v0("decision_event", "decision_event_v9")


def test_canonical_roundtrip_and_stable_serialization() -> None:
    first = build_decision_event_v0(_decision())
    encoded = canonical_json_dumps_v0(first)
    decoded = json.loads(encoded)
    second = build_decision_event_v0(decoded)
    assert dict(first) == dict(second)
    assert encoded == canonical_json_dumps_v0(second)
    assert encoded == canonical_json_dumps_v0(json.loads(encoded))


def test_stable_content_hash_and_semantic_difference() -> None:
    a = build_decision_event_v0(_decision())
    b = build_decision_event_v0(_decision())
    assert a["content_hash"] == b["content_hash"]
    changed = build_decision_event_v0(
        _decision(decision_type="NO_EXIT", reason_codes=[_reason("NO_EXIT")])
    )
    assert a["content_hash"] != changed["content_hash"]
    recomputed = compute_content_hash_v0(a)
    assert recomputed == a["content_hash"]


def test_hash_scope_excludes_volatile_envelope_metadata() -> None:
    record = build_decision_event_v0(_decision())
    scoped = hash_scope_payload_v0({**dict(record), "ingested_at_utc": "2026-09-01T99:00:00Z"})
    assert "ingested_at_utc" not in scoped
    assert "content_hash" not in scoped
    assert "sequence" not in hash_scope_fields_v0("decision_event", "decision_event_v0")
    same = compute_content_hash_v0({**dict(record), "ingested_at_utc": "2099-01-01T00:00:00Z"})
    assert same == record["content_hash"]


def test_float_and_malformed_record_rejection() -> None:
    with pytest.raises(DdoValidationError, match="UNEXPECTED_FIELD"):
        build_decision_event_v0(_decision(extra_field="nope"))
    with pytest.raises(DdoValidationError, match="FLOAT_FORBIDDEN"):
        canonical_json_dumps_v0({"a": 1.5})
    with pytest.raises(DdoValidationError, match="decision_event_MUST_BE_OBJECT"):
        build_decision_event_v0("not-an-object")  # type: ignore[arg-type]


def test_existing_reason_code_namespace_is_not_normalized() -> None:
    opaque = {
        "taxonomy_id": EXISTING_OPAQUE_TAXONOMY_ID,
        "code": "LIMIT_BREACH",
        "source_taxonomy_ref": "src/risk/cmes/reason_codes.py",
    }
    record = build_decision_event_v0(_decision(reason_codes=[opaque]))
    assert record["reason_codes"][0]["code"] == "LIMIT_BREACH"
    assert record["reason_codes"][0]["taxonomy_id"] == EXISTING_OPAQUE_TAXONOMY_ID
    with pytest.raises(DdoValidationError, match="EXISTING_REASON_CODE_REQUIRES_BOUND_SOURCE"):
        build_decision_event_v0(
            _decision(
                reason_codes=[
                    {
                        "taxonomy_id": EXISTING_OPAQUE_TAXONOMY_ID,
                        "code": "LIMIT_BREACH",
                        "source_taxonomy_ref": None,
                    }
                ]
            )
        )


def test_outcome_ref_nullability() -> None:
    absent = validate_outcome_ref_v0(
        {
            "schema_name": "outcome_ref",
            "schema_version": "outcome_ref_v0",
            "link_status": "ABSENT",
            "outcome_record_id": None,
        }
    )
    assert absent["outcome_record_id"] is None
    with pytest.raises(DdoValidationError, match="OUTCOME_REF_ABSENT_MUST_HAVE_NULL_ID"):
        validate_outcome_ref_v0(
            {
                "schema_name": "outcome_ref",
                "schema_version": "outcome_ref_v0",
                "link_status": "ABSENT",
                "outcome_record_id": "out-0001",
            }
        )


def test_forward_lineage_refs_require_existing_typed_records(tmp_path: Path) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "ddo_ledger_v0.jsonl")
    ledger.append(_decision())
    with pytest.raises(DdoLineageError, match="ATTRIBUTION_REFS_MISSING"):
        ledger.append(
            _decision(
                record_id="dec-0002",
                event_id="evt-0002",
                causal_parent_ids=["dec-0001"],
                attribution_refs=["attr-missing"],
            )
        )


def test_append_read_idempotent_and_conflict(tmp_path: Path) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "ddo_ledger_v0.jsonl")
    first = ledger.append(_decision())
    assert first.status == "APPENDED"
    replay = ledger.append(_decision())
    assert replay.status == "IDEMPOTENT_REPLAY"
    assert replay.sequence == first.sequence
    assert len(ledger.read_all()) == 1
    with pytest.raises(DdoDuplicateConflictError):
        ledger.append(_decision(decision_type="STALE_BLOCK", reason_codes=[_reason("STALE_BLOCK")]))
    loaded = ledger.get("dec-0001")
    assert loaded["content_hash"] == first.content_hash


def test_supersedes_corrects_and_invalid_lineage(tmp_path: Path) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "ddo_ledger_v0.jsonl")
    ledger.append(_decision())
    ledger.append(_incident())
    successor = ledger.append(
        _decision(
            record_id="dec-0002",
            event_id="evt-0002",
            supersedes_id="dec-0001",
            causal_parent_ids=["dec-0001"],
        )
    )
    assert successor.status == "APPENDED"
    with pytest.raises(DdoLineageError, match="LINEAGE_TARGET_MISSING"):
        ledger.append(
            _decision(record_id="dec-0003", event_id="evt-0003", corrects_id="dec-missing")
        )
    with pytest.raises(DdoLineageError, match="CAUSAL_PARENT_MISSING"):
        ledger.append(
            _decision(record_id="dec-0004", event_id="evt-0004", causal_parent_ids=["no-parent"])
        )
    with pytest.raises(DdoLineageError, match="OUTCOME_DECISION_REF_MISSING"):
        orphan = AppendOnlyDdoLedgerV0(tmp_path / "orphan.jsonl")
        orphan.append(_outcome(causal_parent_ids=[]))
    outcome = ledger.append(
        _outcome(causal_parent_ids=["dec-0001", "inc-0001"], incident_record_ref="inc-0001")
    )
    assert outcome.status == "APPENDED"
    rows = ledger.read_all()
    assert [row["record_id"] for row in rows] == ["dec-0001", "inc-0001", "dec-0002", "out-0001"]


def test_self_supersession_rejected() -> None:
    with pytest.raises(DdoLineageError, match="SELF_LINEAGE_FORBIDDEN"):
        from src.learning.deterministic_decision_outcome_v0.lineage_v0 import (
            validate_record_lineage_v0,
        )

        record = build_decision_event_v0(_decision(supersedes_id="dec-0001"))
        validate_record_lineage_v0(record, existing_by_id={})


def test_corruption_and_hash_mismatch_detection(tmp_path: Path) -> None:
    path = tmp_path / "ddo_ledger_v0.jsonl"
    ledger = AppendOnlyDdoLedgerV0(path)
    ledger.append(_decision())
    raw = path.read_text(encoding="utf-8")
    tampered = json.loads(raw)
    tampered["payload"]["decision_type"] = "KILL_SWITCH"
    path.write_text(canonical_json_dumps_v0(tampered) + "\n", encoding="utf-8")
    with pytest.raises((DdoIntegrityError, DdoLedgerCorruptionError)):
        ledger.verify_integrity()
    path.write_text("{not json\n", encoding="utf-8")
    with pytest.raises(DdoMalformedRecordError):
        AppendOnlyDdoLedgerV0(path).verify_integrity()


def test_unsupported_schema_version_on_ledger_append(tmp_path: Path) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "ddo_ledger_v0.jsonl")
    with pytest.raises(DdoUnsupportedSchemaVersionError):
        ledger.append(_decision(schema_version="decision_event_v99"))


def test_deterministic_repeated_runs(tmp_path: Path) -> None:
    hashes: list[str] = []
    for index in range(3):
        ledger = AppendOnlyDdoLedgerV0(tmp_path / f"run-{index}.jsonl")
        result = ledger.append(_decision(), ingested_at_utc="2026-09-01T15:00:00Z")
        hashes.append(result.content_hash)
        again = ledger.append(_decision(), ingested_at_utc="2099-01-01T00:00:00Z")
        assert again.status == "IDEMPOTENT_REPLAY"
        assert again.content_hash == result.content_hash
    assert hashes[0] == hashes[1] == hashes[2]


def test_ingestion_timestamp_does_not_change_content_identity(tmp_path: Path) -> None:
    left = AppendOnlyDdoLedgerV0(tmp_path / "left.jsonl")
    right = AppendOnlyDdoLedgerV0(tmp_path / "right.jsonl")
    a = left.append(_decision(), ingested_at_utc="2026-01-01T00:00:00Z")
    b = right.append(_decision(), ingested_at_utc="2026-12-31T23:59:59Z")
    assert a.content_hash == b.content_hash


def test_incident_and_outcome_structural_schemas() -> None:
    incident = build_incident_record_v0(
        _incident(
            causal_parent_ids=[],
            stale_root_cause="CLOCK_SKEW",
            kill_switch_correctness=UNKNOWN,
            kill_switch_timing_label=UNKNOWN,
        )
    )
    assert incident["incident_class"] == "STALE"
    assert incident["stale_root_cause"] == "CLOCK_SKEW"
    outcome = build_outcome_record_v0(_outcome(causal_parent_ids=[]))
    assert outcome["counterfactual_admissibility"] == "UNAVAILABLE"
    assert outcome["safety_score"] is None


def test_no_forbidden_imports_or_network_or_section_dependency() -> None:
    hits: list[str] = []
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for name in names:
                if any(
                    name == prefix or name.startswith(prefix + ".")
                    for prefix in FORBIDDEN_IMPORT_PREFIXES
                ):
                    hits.append(f"{path.name}:{name}")
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for token in FORBIDDEN_SUBSTRINGS:
            if token in lowered and "SECTION_11_13_5_DEPENDENCY" not in text:
                if token == "11.13.5" or token == "section_11_13_5":
                    hits.append(f"{path.name}:{token}")
                if (
                    token in {"testnet", "canary"}
                    and "TESTNET_EFFECT" not in text
                    and "CANARY_EFFECT" not in text
                ):
                    hits.append(f"{path.name}:{token}")
    assert hits == []


def test_package_does_not_import_trading_or_execution_at_runtime() -> None:
    import sys

    before = set(sys.modules)
    validate_canonical_record_v0(_decision())
    imported = set(sys.modules) - before
    leaked = [
        name
        for name in imported
        if name.startswith(
            (
                "src.trading",
                "src.execution",
                "src.live",
                "src.meta.learning_loop",
                "src.governance.promotion",
                "src.ops",
            )
        )
    ]
    assert leaked == []


def test_registry_exposes_hash_scope_and_existing_taxonomies() -> None:
    fields = hash_scope_fields_v0("incident_record", "incident_record_v0")
    assert "record_id" in fields
    assert "content_hash" not in fields
    refs = CONTRACT_REGISTRY_V0["existing_source_taxonomy_refs"]
    assert any(item["source_path"] == "src/risk/cmes/reason_codes.py" for item in refs)
    assert all(item["codes_copied"] == "false" for item in refs)
    assert CONTRACT_REGISTRY_V0["open_unbound_enums"]
