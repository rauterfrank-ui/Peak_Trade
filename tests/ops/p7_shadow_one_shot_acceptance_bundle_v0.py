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


def _validate_p7_fills(data: dict[str, Any]) -> None:
    assert data.get("schema_version") == "p7.fills.v0"
    fills = data.get("fills")
    assert isinstance(fills, list) and len(fills) >= 1


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


def validate_p7_shadow_one_shot_artifact_bundle(bundle_root: Path) -> None:
    """Raise AssertionError when the bundle does not satisfy the v0 acceptance contract."""
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
    _validate_p7_fills(_load_json(root / "p7_fills.json"))
    _validate_p7_fills(_load_json(root / "p7" / "fills.json"))
    _validate_p7_account(_load_json(root / "p7_account.json"))
    _validate_p7_account(_load_json(root / "p7" / "account.json"))
    _validate_root_evidence_manifest(_load_json(root / "evidence_manifest.json"))
    _validate_p7_evidence_manifest(_load_json(root / "p7" / "evidence_manifest.json"))
