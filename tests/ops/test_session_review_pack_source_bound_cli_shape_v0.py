"""Synthetic source-bound SRP CLI shape tests.

These tests model future argv semantics without importing or changing the
production report parser. They do not invoke report code, read real registries,
or bind real sessions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


AUTHORITY_FLAGS = {
    "live_authorization": False,
    "closeout_approval": False,
    "gate_passage": False,
    "strategy_readiness": False,
    "autonomy_readiness": False,
    "external_authority_completion": False,
}


@dataclass(frozen=True)
class SyntheticCliShape:
    valid: bool
    mode: str | None
    session_id: str | None
    json_output: bool
    error: str | None
    missing_fields: tuple[str, ...]
    authority_boundary: dict[str, bool]


def parse_synthetic_source_bound_srp_argv(argv: list[str]) -> SyntheticCliShape:
    static_requested = "--session-review-pack" in argv
    source_bound_requested = "--session-review-pack-source-bound" in argv
    json_output = "--json" in argv

    session_values: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--session-id":
            if index + 1 >= len(argv):
                session_values.append("")
                index += 1
                continue
            session_values.append(argv[index + 1])
            index += 2
            continue
        index += 1

    if static_requested and source_bound_requested:
        return SyntheticCliShape(
            valid=False,
            mode=None,
            session_id=None,
            json_output=json_output,
            error="static_and_source_bound_modes_are_mutually_exclusive",
            missing_fields=(),
            authority_boundary=dict(AUTHORITY_FLAGS),
        )

    if session_values and not source_bound_requested:
        return SyntheticCliShape(
            valid=False,
            mode=None,
            session_id=None,
            json_output=json_output,
            error="session_id_requires_source_bound_mode",
            missing_fields=(),
            authority_boundary=dict(AUTHORITY_FLAGS),
        )

    if source_bound_requested:
        if not session_values or not session_values[0].strip():
            return SyntheticCliShape(
                valid=False,
                mode="source_bound",
                session_id=None,
                json_output=json_output,
                error="explicit_session_id_required",
                missing_fields=("selection.session_id",),
                authority_boundary=dict(AUTHORITY_FLAGS),
            )

        if len(session_values) != 1:
            return SyntheticCliShape(
                valid=False,
                mode="source_bound",
                session_id=None,
                json_output=json_output,
                error="multiple_session_id_values_not_allowed",
                missing_fields=("selection.session_id",),
                authority_boundary=dict(AUTHORITY_FLAGS),
            )

        return SyntheticCliShape(
            valid=True,
            mode="source_bound",
            session_id=session_values[0],
            json_output=json_output,
            error=None,
            missing_fields=(),
            authority_boundary=dict(AUTHORITY_FLAGS),
        )

    if static_requested:
        return SyntheticCliShape(
            valid=True,
            mode="static",
            session_id=None,
            json_output=json_output,
            error=None,
            missing_fields=(),
            authority_boundary=dict(AUTHORITY_FLAGS),
        )

    return SyntheticCliShape(
        valid=False,
        mode=None,
        session_id=None,
        json_output=json_output,
        error="no_session_review_pack_mode_selected",
        missing_fields=("mode",),
        authority_boundary=dict(AUTHORITY_FLAGS),
    )


def serialized_shape(shape: SyntheticCliShape) -> str:
    return json.dumps(
        {
            "valid": shape.valid,
            "mode": shape.mode,
            "session_id": shape.session_id,
            "json_output": shape.json_output,
            "error": shape.error,
            "missing_fields": list(shape.missing_fields),
            "authority_boundary": shape.authority_boundary,
            "non_authorizing": True,
        },
        sort_keys=True,
    )


def assert_non_authorizing(shape: SyntheticCliShape) -> None:
    assert shape.authority_boundary == AUTHORITY_FLAGS
    assert '"non_authorizing": true' in serialized_shape(shape)


def test_source_bound_session_id_json_shape_parses_valid() -> None:
    shape = parse_synthetic_source_bound_srp_argv(
        ["--session-review-pack-source-bound", "--session-id", "session_a", "--json"]
    )

    assert shape.valid is True
    assert shape.mode == "source_bound"
    assert shape.session_id == "session_a"
    assert shape.json_output is True
    assert shape.error is None
    assert shape.missing_fields == ()
    assert_non_authorizing(shape)


def test_source_bound_missing_session_id_fails_closed() -> None:
    shape = parse_synthetic_source_bound_srp_argv(["--session-review-pack-source-bound", "--json"])

    assert shape.valid is False
    assert shape.mode == "source_bound"
    assert shape.error == "explicit_session_id_required"
    assert shape.missing_fields == ("selection.session_id",)
    assert_non_authorizing(shape)


def test_source_bound_blank_session_id_fails_closed() -> None:
    shape = parse_synthetic_source_bound_srp_argv(
        ["--session-review-pack-source-bound", "--session-id", "   ", "--json"]
    )

    assert shape.valid is False
    assert shape.error == "explicit_session_id_required"
    assert shape.session_id is None
    assert shape.missing_fields == ("selection.session_id",)
    assert_non_authorizing(shape)


def test_static_and_source_bound_modes_are_mutually_exclusive() -> None:
    shape = parse_synthetic_source_bound_srp_argv(
        ["--session-review-pack", "--session-review-pack-source-bound", "--session-id", "session_a"]
    )

    assert shape.valid is False
    assert shape.mode is None
    assert shape.error == "static_and_source_bound_modes_are_mutually_exclusive"
    assert_non_authorizing(shape)


def test_session_id_without_source_bound_mode_fails_closed() -> None:
    shape = parse_synthetic_source_bound_srp_argv(["--session-id", "session_a", "--json"])

    assert shape.valid is False
    assert shape.error == "session_id_requires_source_bound_mode"
    assert shape.session_id is None
    assert_non_authorizing(shape)


def test_multiple_session_id_values_fail_closed() -> None:
    shape = parse_synthetic_source_bound_srp_argv(
        [
            "--session-review-pack-source-bound",
            "--session-id",
            "session_a",
            "--session-id",
            "session_b",
            "--json",
        ]
    )

    assert shape.valid is False
    assert shape.mode == "source_bound"
    assert shape.error == "multiple_session_id_values_not_allowed"
    assert shape.missing_fields == ("selection.session_id",)
    assert_non_authorizing(shape)


def test_no_auto_primacy_or_newest_fallback_is_represented() -> None:
    shape = parse_synthetic_source_bound_srp_argv(["--session-review-pack-source-bound", "--json"])
    serialized = serialized_shape(shape).lower()

    assert "newest" not in serialized
    assert "latest" not in serialized
    assert "auto_primacy" not in serialized
    assert "default_session" not in serialized
    assert shape.error == "explicit_session_id_required"


def test_serialized_output_contains_no_unqualified_authority_claims() -> None:
    shapes = [
        parse_synthetic_source_bound_srp_argv(
            ["--session-review-pack-source-bound", "--session-id", "session_a", "--json"]
        ),
        parse_synthetic_source_bound_srp_argv(["--session-review-pack-source-bound", "--json"]),
        parse_synthetic_source_bound_srp_argv(["--session-review-pack", "--json"]),
    ]

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

    for shape in shapes:
        serialized = serialized_shape(shape).lower()
        for claim in forbidden_claims:
            assert claim not in serialized


def test_this_cli_shape_test_does_not_read_real_artifact_locations() -> None:
    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "/".join(["reports", "experiments", "live_sessions"]),
        "/".join(["out", "ops"]),
        "/".join(["execution_events", "sessions"]),
        "_".join(["live", "session", "registry"]),
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source_text
