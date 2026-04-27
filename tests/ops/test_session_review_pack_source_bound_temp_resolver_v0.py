"""Synthetic temp-fixture resolver tests for future source-bound SRP.

These tests model source resolution against tmp_path fixtures only. They do not
import production report code, read real registries, read generated artifacts, or
bind real sessions.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


CONTRACT = "synthetic.session_review_pack_source_bound_temp_resolver_v0"

AUTHORITY_FLAGS = {
    "live_authorization": False,
    "closeout_approval": False,
    "gate_passage": False,
    "strategy_readiness": False,
    "autonomy_readiness": False,
    "external_authority_completion": False,
}


@dataclass(frozen=True)
class TempResolverBases:
    registry_dir: Path
    events_dir: Path


def write_registry_record(
    registry_dir: Path,
    *,
    filename: str,
    session_id: str,
    status: str = "started",
    extra: dict[str, Any] | None = None,
) -> Path:
    registry_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "session_id": session_id,
        "status": status,
        "config": {"bounded_pilot": True, "dry_run": True},
        "metrics": {},
    }
    if extra:
        payload.update(extra)
    path = registry_dir / filename
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def write_event_file(events_dir: Path, *, session_id: str) -> Path:
    path = events_dir / "sessions" / session_id / "execution_events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '{"event_type":"order_submit","session_id":"' + session_id + '"}\n',
        encoding="utf-8",
    )
    return path


def fail_closed(error: str, *, missing_fields: list[str] | None = None) -> dict[str, Any]:
    return {
        "contract": CONTRACT,
        "valid": False,
        "non_authorizing": True,
        "error": error,
        "missing_fields": sorted(missing_fields or []),
        "authority_boundary": dict(AUTHORITY_FLAGS),
    }


def resolve_temp_source_bound_session(
    *,
    bases: TempResolverBases,
    selected_session_id: str,
) -> dict[str, Any]:
    registry_files = sorted(bases.registry_dir.glob("*.json"))
    if not registry_files:
        return fail_closed(
            "registry_source_missing", missing_fields=["source.registry_session_record"]
        )

    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in registry_files:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return fail_closed(
                "registry_json_malformed", missing_fields=["source.registry_session_record"]
            )

        if not isinstance(record, dict) or not isinstance(record.get("session_id"), str):
            return fail_closed(
                "registry_record_malformed", missing_fields=["source.registry_session_record"]
            )

        if record["session_id"] == selected_session_id:
            matches.append((path, record))

    if len(matches) != 1:
        return fail_closed(
            "selected_session_id_not_found_or_not_unique",
            missing_fields=["source.registry_session_record"],
        )

    path, record = matches[0]
    events_path = bases.events_dir / "sessions" / selected_session_id / "execution_events.jsonl"
    events_present = events_path.exists()
    missing_fields: list[str] = []
    if events_present:
        event_pointer = {
            "source_class": "scoped_execution_events_pointer",
            "present": True,
            "review_state": "reference_candidate",
            "authority": dict(AUTHORITY_FLAGS),
        }
    else:
        missing_fields.append("references.execution_events_session_jsonl")
        event_pointer = {
            "source_class": "scoped_execution_events_pointer",
            "present": False,
            "review_state": "needs_review",
            "authority": dict(AUTHORITY_FLAGS),
        }

    return {
        "contract": CONTRACT,
        "valid": True,
        "non_authorizing": True,
        "selection": {"mode": "explicit_session_id", "session_id": selected_session_id},
        "registry_session_record": {
            "source_class": "registry_session_record",
            "registry_file": path.name,
            "session_id": record["session_id"],
            "status": record.get("status"),
            "authority": dict(AUTHORITY_FLAGS),
        },
        "references": {
            "execution_events_session_jsonl": event_pointer,
        },
        "missing_fields": sorted(missing_fields),
        "authority_boundary": dict(AUTHORITY_FLAGS),
    }


def assert_authority_false(payload: dict[str, Any]) -> None:
    assert payload["authority_boundary"] == AUTHORITY_FLAGS
    if "registry_session_record" in payload:
        assert payload["registry_session_record"]["authority"] == AUTHORITY_FLAGS
    for reference in payload.get("references", {}).values():
        assert reference["authority"] == AUTHORITY_FLAGS


def test_selected_session_id_resolves_exactly_one_temp_registry_record(tmp_path: Path) -> None:
    bases = TempResolverBases(registry_dir=tmp_path / "registry", events_dir=tmp_path / "events")
    write_registry_record(bases.registry_dir, filename="a.json", session_id="session_a")
    write_registry_record(bases.registry_dir, filename="b.json", session_id="session_b")

    payload = resolve_temp_source_bound_session(bases=bases, selected_session_id="session_b")

    assert payload["valid"] is True
    assert payload["selection"] == {"mode": "explicit_session_id", "session_id": "session_b"}
    assert payload["registry_session_record"]["registry_file"] == "b.json"
    assert payload["registry_session_record"]["session_id"] == "session_b"
    assert_authority_false(payload)


def test_missing_selected_session_id_fails_closed(tmp_path: Path) -> None:
    bases = TempResolverBases(registry_dir=tmp_path / "registry", events_dir=tmp_path / "events")
    write_registry_record(bases.registry_dir, filename="a.json", session_id="session_a")

    payload = resolve_temp_source_bound_session(bases=bases, selected_session_id="session_missing")

    assert payload["valid"] is False
    assert payload["error"] == "selected_session_id_not_found_or_not_unique"
    assert payload["missing_fields"] == ["source.registry_session_record"]
    assert_authority_false(payload)


def test_duplicate_selected_session_id_fails_closed(tmp_path: Path) -> None:
    bases = TempResolverBases(registry_dir=tmp_path / "registry", events_dir=tmp_path / "events")
    write_registry_record(bases.registry_dir, filename="a.json", session_id="session_duplicate")
    write_registry_record(bases.registry_dir, filename="b.json", session_id="session_duplicate")

    payload = resolve_temp_source_bound_session(
        bases=bases, selected_session_id="session_duplicate"
    )

    assert payload["valid"] is False
    assert payload["error"] == "selected_session_id_not_found_or_not_unique"
    assert payload["missing_fields"] == ["source.registry_session_record"]
    assert_authority_false(payload)


def test_malformed_registry_json_fails_closed(tmp_path: Path) -> None:
    bases = TempResolverBases(registry_dir=tmp_path / "registry", events_dir=tmp_path / "events")
    bases.registry_dir.mkdir(parents=True)
    (bases.registry_dir / "bad.json").write_text("{not-json", encoding="utf-8")

    payload = resolve_temp_source_bound_session(bases=bases, selected_session_id="session_a")

    assert payload["valid"] is False
    assert payload["error"] == "registry_json_malformed"
    assert payload["missing_fields"] == ["source.registry_session_record"]
    assert_authority_false(payload)


def test_malformed_registry_record_non_string_session_id_fails_closed(tmp_path: Path) -> None:
    bases = TempResolverBases(registry_dir=tmp_path / "registry", events_dir=tmp_path / "events")
    bases.registry_dir.mkdir(parents=True)
    (bases.registry_dir / "bad_record.json").write_text(
        json.dumps({"session_id": 123, "status": "started"}, sort_keys=True),
        encoding="utf-8",
    )

    payload = resolve_temp_source_bound_session(bases=bases, selected_session_id="session_a")

    assert payload["valid"] is False
    assert payload["error"] == "registry_record_malformed"
    assert payload["missing_fields"] == ["source.registry_session_record"]
    assert_authority_false(payload)


def test_events_present_true_is_reference_candidate_only(tmp_path: Path) -> None:
    bases = TempResolverBases(registry_dir=tmp_path / "registry", events_dir=tmp_path / "events")
    write_registry_record(bases.registry_dir, filename="a.json", session_id="session_a")
    write_event_file(bases.events_dir, session_id="session_a")

    payload = resolve_temp_source_bound_session(bases=bases, selected_session_id="session_a")

    pointer = payload["references"]["execution_events_session_jsonl"]
    assert payload["valid"] is True
    assert pointer["present"] is True
    assert pointer["review_state"] == "reference_candidate"
    assert payload["missing_fields"] == []
    assert_authority_false(payload)


def test_events_present_false_is_needs_review_missing_field(tmp_path: Path) -> None:
    bases = TempResolverBases(registry_dir=tmp_path / "registry", events_dir=tmp_path / "events")
    write_registry_record(bases.registry_dir, filename="a.json", session_id="session_a")

    payload = resolve_temp_source_bound_session(bases=bases, selected_session_id="session_a")

    pointer = payload["references"]["execution_events_session_jsonl"]
    assert payload["valid"] is True
    assert pointer["present"] is False
    assert pointer["review_state"] == "needs_review"
    assert payload["missing_fields"] == ["references.execution_events_session_jsonl"]
    assert_authority_false(payload)


def test_empty_registry_directory_fails_closed(tmp_path: Path) -> None:
    bases = TempResolverBases(registry_dir=tmp_path / "registry", events_dir=tmp_path / "events")
    bases.registry_dir.mkdir(parents=True)

    payload = resolve_temp_source_bound_session(bases=bases, selected_session_id="session_a")

    assert payload["valid"] is False
    assert payload["error"] == "registry_source_missing"
    assert payload["missing_fields"] == ["source.registry_session_record"]
    assert_authority_false(payload)


def test_serialized_temp_resolver_output_contains_no_authority_claims(tmp_path: Path) -> None:
    bases = TempResolverBases(registry_dir=tmp_path / "registry", events_dir=tmp_path / "events")
    write_registry_record(bases.registry_dir, filename="a.json", session_id="session_a")
    payload = resolve_temp_source_bound_session(bases=bases, selected_session_id="session_a")
    serialized = json.dumps(payload, sort_keys=True).lower()

    forbidden_claims = [
        "live authorization granted",
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


def test_this_temp_resolver_test_does_not_read_real_artifact_locations() -> None:
    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "/".join(["reports", "experiments", "live_sessions"]),
        "/".join(["out", "ops"]),
        "/".join(["execution_events", "sessions"]),
        "_".join(["live", "session", "registry"]),
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source_text
