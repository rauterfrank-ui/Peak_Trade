"""Static acceptance checks for a P7 Shadow one-shot dry-run artifact bundle (fixtures only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Normalized relpaths (posix) under the bundle root — matches
# tests/fixtures/p7_shadow_one_shot_acceptance_v0/ from a successful local dry-run.
EXPECTED_RELATIVE_JSON_FILES: frozenset[str] = frozenset(
    {
        "evidence_manifest.json",
        "p4c/l2_market_outlook.json",
        "p4c/market_outlook.json",
        "p5a/l3_trade_plan_advisory.json",
        "p7/account.json",
        "p7/evidence_manifest.json",
        "p7/fills.json",
        "p7_account.json",
        "p7_evidence_manifest.json",
        "p7_fills.json",
        "shadow_session_summary.json",
    }
)

# Case-insensitive substring deny-list for bundled JSON *content* (heuristic; not a security gate).
FORBIDDEN_SUBSTRINGS: tuple[str, ...] = (
    "testnet",
    "broker",
    "exchange",
    "api_key",
    "apikey",
    "https://",
    "wss://",
    "-----begin",
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _all_paths_portable(bundle_root: Path) -> None:
    """Reject absolute-looking path strings inside any JSON value."""
    root = bundle_root.resolve()

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for x in obj:
                walk(x)
        elif isinstance(obj, str):
            if obj.startswith("/"):
                raise AssertionError(
                    f"non-portable absolute path string in bundle under {root}: {obj!r}"
                )

    for rel in sorted(EXPECTED_RELATIVE_JSON_FILES):
        walk(_load_json(root / rel))


def _forbidden_scan(bundle_root: Path) -> None:
    root = bundle_root.resolve()
    blob_parts: list[str] = []
    for rel in sorted(EXPECTED_RELATIVE_JSON_FILES):
        data = _load_json(root / rel)
        blob_parts.append(json.dumps(data, sort_keys=True))
    blob = "\n".join(blob_parts).lower()
    for token in FORBIDDEN_SUBSTRINGS:
        if token.lower() in blob:
            raise AssertionError(
                f"forbidden substring {token!r} found in bundled JSON under {root}"
            )


def _validate_shadow_session_summary(data: dict[str, Any]) -> None:
    for key in (
        "run_id",
        "schema_version",
        "steps",
        "notes",
        "outputs",
        "p7_outputs",
        "p7_account_summary",
        "asof_utc",
        "no_trade",
    ):
        assert key in data, f"shadow_session_summary.json missing {key!r}"
    notes = data["notes"]
    assert isinstance(notes, list) and "dry_run_only" in notes and "no_execution" in notes
    outs = data["outputs"]
    assert isinstance(outs, dict)
    assert outs.get("p4c_out", "").startswith("p4c/")
    assert outs.get("p5a_out", "").startswith("p5a/")
    steps = data["steps"]
    assert isinstance(steps, list) and len(steps) >= 3


def _validate_p7_fills(data: dict[str, Any], *, fills_may_be_empty: bool) -> None:
    fills = data.get("fills")
    assert isinstance(fills, list), "fills must be a list"

    if fills_may_be_empty and len(fills) == 0:
        return

    if not fills_may_be_empty and len(fills) < 1:
        raise AssertionError("expected at least one fill")

    assert data.get("schema_version") == "p7.fills.v0"
    assert len(fills) >= 1


def _validate_p7_account(data: dict[str, Any]) -> None:
    assert data.get("schema_version") == "p7.account.v0"
    assert "cash" in data and isinstance(data["cash"], (int, float))
    pos = data.get("positions")
    assert isinstance(pos, dict)


def _validate_root_evidence_manifest(data: dict[str, Any]) -> None:
    meta = data.get("meta") or {}
    assert meta.get("kind") == "p6_shadow_session_manifest"
    files = data.get("files")
    assert isinstance(files, list) and len(files) == 6


def _validate_p7_evidence_manifest(data: dict[str, Any]) -> None:
    meta = data.get("meta") or {}
    assert meta.get("kind") == "p7_paper_manifest"
    files = data.get("files")
    assert isinstance(files, list) and len(files) == 2


def validate_p7_shadow_one_shot_artifact_bundle(
    bundle_root: Path, *, profile_name: str = "baseline"
) -> None:
    """Raise AssertionError when the bundle does not satisfy the v0 acceptance contract."""
    profile = _profile_config_v0(profile_name)
    root = bundle_root.resolve()
    if not root.is_dir():
        raise AssertionError(f"bundle root is not a directory: {root}")

    present: set[str] = set()
    for path in root.rglob("*.json"):
        present.add(str(path.relative_to(root).as_posix()))

    assert present == set(EXPECTED_RELATIVE_JSON_FILES), (
        f"json path mismatch: extra={present - EXPECTED_RELATIVE_JSON_FILES} missing={EXPECTED_RELATIVE_JSON_FILES - present}"
    )

    _all_paths_portable(root)
    _forbidden_scan(root)

    _validate_shadow_session_summary(_load_json(root / "shadow_session_summary.json"))
    allow_empty = profile["fills_may_be_empty"]
    _validate_p7_fills(_load_json(root / "p7_fills.json"), fills_may_be_empty=allow_empty)
    _validate_p7_fills(_load_json(root / "p7" / "fills.json"), fills_may_be_empty=allow_empty)
    _validate_p7_account(_load_json(root / "p7_account.json"))
    _validate_p7_account(_load_json(root / "p7" / "account.json"))
    _validate_root_evidence_manifest(_load_json(root / "evidence_manifest.json"))
    _validate_p7_evidence_manifest(_load_json(root / "p7" / "evidence_manifest.json"))


VOLATILE_REPEATED_RUN_KEYS_V0: frozenset[str] = frozenset(
    {
        "created_at",
        "created_at_utc",
        "generated_at",
        "timestamp",
        "ts",
        "started_at",
        "completed_at",
        "run_started_at",
        "run_completed_at",
        "sha256",
        "digest",
        "hash",
        "path",
        "paths",
        "outdir",
        "output_dir",
        "output_path",
    }
)

VOLATILE_REPEATED_RUN_PATH_PARTS_V0: frozenset[str] = frozenset(
    {
        "run_001",
        "run_002",
        "run_003",
        "peak_trade_manual_p7_shadow_repeated_campaign_scope_20260505T162028Z",
    }
)

STABLE_REPEATED_RUN_ARTIFACTS_V0: frozenset[str] = frozenset(
    {
        "shadow_session_summary.json",
        "p5a/l3_trade_plan_advisory.json",
        "p7/fills.json",
        "p7/account.json",
        "p7_fills.json",
        "p7_account.json",
    }
)


def normalize_p7_shadow_repeated_run_value_v0(value: Any) -> Any:
    """Normalize expected run-local volatility for repeated-run stability checks."""
    if isinstance(value, dict):
        return {
            key: normalize_p7_shadow_repeated_run_value_v0(item)
            for key, item in sorted(value.items())
            if key not in VOLATILE_REPEATED_RUN_KEYS_V0
        }

    if isinstance(value, list):
        return [normalize_p7_shadow_repeated_run_value_v0(item) for item in value]

    if isinstance(value, str):
        normalized = value
        for part in VOLATILE_REPEATED_RUN_PATH_PARTS_V0:
            normalized = normalized.replace(part, "<RUN_LOCAL>")
        return normalized

    return value


def stable_repeated_run_artifact_paths_v0() -> frozenset[str]:
    """Return artifact paths that must remain stable across repeated one-shot runs."""
    return STABLE_REPEATED_RUN_ARTIFACTS_V0


def assert_p7_shadow_repeated_run_stability_v0(
    run_payloads_by_relpath: dict[str, dict[str, Any]],
) -> None:
    """Assert normalized stable artifacts are identical across repeated runs.

    The input shape is:
    {
        "run_001": {"relative/artifact.json": parsed_json, ...},
        "run_002": {"relative/artifact.json": parsed_json, ...},
        ...
    }
    """
    run_names = sorted(run_payloads_by_relpath)
    assert run_names, "at least one run is required"

    baseline = run_names[0]
    baseline_payloads = run_payloads_by_relpath[baseline]

    for relpath in STABLE_REPEATED_RUN_ARTIFACTS_V0:
        assert relpath in baseline_payloads, f"missing stable artifact in {baseline}: {relpath}"
        expected = normalize_p7_shadow_repeated_run_value_v0(baseline_payloads[relpath])

        for run_name in run_names[1:]:
            run_payloads = run_payloads_by_relpath[run_name]
            assert relpath in run_payloads, f"missing stable artifact in {run_name}: {relpath}"
            actual = normalize_p7_shadow_repeated_run_value_v0(run_payloads[relpath])
            assert actual == expected, f"stable artifact drifted after normalization: {relpath}"


P7_SHADOW_ACCEPTANCE_FIXTURE_PROFILES_V0 = {
    "baseline": {
        "fixture_dir": "tests/fixtures/p7_shadow_one_shot_acceptance_v0",
        "expected_scenario": None,
        "expected_decision": None,
        "fills_may_be_empty": False,
    },
    "high_vol_no_trade": {
        "fixture_dir": "tests/fixtures/p7_shadow_one_shot_acceptance_high_vol_no_trade_v0",
        "expected_scenario": "high_vol_no_trade",
        "expected_decision": "NO_TRADE",
        "fills_may_be_empty": True,
    },
}


def _profile_config_v0(profile_name: str) -> dict[str, Any]:
    try:
        return P7_SHADOW_ACCEPTANCE_FIXTURE_PROFILES_V0[profile_name]
    except KeyError as exc:
        raise AssertionError(
            f"unknown P7 Shadow acceptance fixture profile: {profile_name}"
        ) from exc


def p7_shadow_acceptance_fixture_profiles_v0():
    """Return supported offline P7 Shadow acceptance fixture profiles."""

    return P7_SHADOW_ACCEPTANCE_FIXTURE_PROFILES_V0
