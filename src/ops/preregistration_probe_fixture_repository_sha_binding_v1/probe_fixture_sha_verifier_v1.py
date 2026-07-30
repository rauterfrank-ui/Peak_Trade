"""Fail-closed repository SHA binding verifier for probe/fixture evidence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.ops.preregistration_probe_fixture_repository_sha_binding_v1.constants_v1 import (
    BRIDGED_CAPABILITY,
    CAPABILITY_ID,
    OWNER,
    PROBE_TYPE_CANONICAL,
    PROBE_TYPE_FORCED_FIXTURE,
)
from src.ops.preregistration_probe_fixture_repository_sha_binding_v1.repository_sha_source_v1 import (
    RepositoryShaResolutionErrorV1,
    assert_valid_repository_sha_v1,
)

VERIFIER_ID = f"{OWNER}.probe_fixture_sha_verifier_v1"
# Fail-closed isolation invariant (must remain false; do not import hardening package here).
_FORCED_FIXTURE_WALLCLOCK_REACHABLE_REQUIRED = False


@dataclass
class ProbeFixtureShaBindingResultV1:
    ok: bool
    verifier_id: str
    capability_id: str
    probe_type: str
    sha_bound: bool
    repository_sha: str
    expected_sha: str
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    forced_fixture_wallclock_reachable: bool | None = None
    forced_fixture_economic_metrics_excluded: bool | None = None
    forced_fixture_can_consume_productive_authorization: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(str(path))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return payload


def _extract_sha(payload: Mapping[str, Any], *, field: str = "repository_sha") -> str | None:
    value = payload.get(field)
    if value is None:
        return None
    return str(value)


def verify_probe_fixture_repository_sha_binding_v1(
    *,
    evidence_root: Path,
    expected_repository_sha: str,
    expected_probe_type: str,
) -> ProbeFixtureShaBindingResultV1:
    """Verify probe/fixture evidence is bound to the expected full git SHA."""
    blockers: list[str] = []
    notes: list[str] = []
    root = Path(evidence_root)

    try:
        expected = assert_valid_repository_sha_v1(
            expected_repository_sha, field="expected_repository_sha"
        )
    except RepositoryShaResolutionErrorV1 as exc:
        return ProbeFixtureShaBindingResultV1(
            ok=False,
            verifier_id=VERIFIER_ID,
            capability_id=CAPABILITY_ID,
            probe_type=str(expected_probe_type),
            sha_bound=False,
            repository_sha="",
            expected_sha=str(expected_repository_sha or ""),
            blockers=[str(exc)],
        )

    if expected_probe_type not in {PROBE_TYPE_CANONICAL, PROBE_TYPE_FORCED_FIXTURE}:
        blockers.append(f"UNKNOWN_PROBE_TYPE:{expected_probe_type}")

    try:
        manifest = _load_json(root / "session_manifest.json")
        completion = _load_json(root / "completion_verdict.json")
        integrity = _load_json(root / "integrity_manifest.json")
    except (OSError, ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        return ProbeFixtureShaBindingResultV1(
            ok=False,
            verifier_id=VERIFIER_ID,
            capability_id=CAPABILITY_ID,
            probe_type=str(expected_probe_type),
            sha_bound=False,
            repository_sha="",
            expected_sha=expected,
            blockers=[f"EVIDENCE_LOAD_FAILED:{exc}"],
        )

    probe_type = str(manifest.get("probe_type") or "")
    if probe_type != expected_probe_type:
        blockers.append(f"PROBE_TYPE_MISMATCH:{probe_type}!={expected_probe_type}")

    capability = str(manifest.get("capability") or "")
    if capability != BRIDGED_CAPABILITY:
        blockers.append(f"CAPABILITY_MISMATCH:{capability}!={BRIDGED_CAPABILITY}")

    required_manifest = (
        "repository_sha",
        "capability",
        "probe_type",
        "session_id",
        "created_at_utc",
        "config_digest",
        "evidence_schema_version",
    )
    for key in required_manifest:
        if key not in manifest or manifest.get(key) in (None, ""):
            blockers.append(f"MANIFEST_FIELD_MISSING:{key}")

    sha_fields: dict[str, str | None] = {
        "session_manifest": _extract_sha(manifest),
        "completion_verdict": _extract_sha(completion),
        "integrity_manifest": _extract_sha(integrity),
    }
    summary_path = root / "probe_summary.json"
    if summary_path.is_file():
        try:
            summary = _load_json(summary_path)
            sha_fields["probe_summary"] = _extract_sha(summary)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            blockers.append(f"PROBE_SUMMARY_LOAD_FAILED:{exc}")

    embedded = ""
    for label, raw in sha_fields.items():
        if raw is None:
            blockers.append(f"REPOSITORY_SHA_MISSING:{label}")
            continue
        try:
            validated = assert_valid_repository_sha_v1(raw, field=f"{label}.repository_sha")
        except RepositoryShaResolutionErrorV1 as exc:
            blockers.append(f"{label}:{exc}")
            continue
        if not embedded:
            embedded = validated
        elif validated != embedded:
            blockers.append(
                f"REPOSITORY_SHA_CROSS_ARTIFACT_CONFLICT:{label}:{validated}!={embedded}"
            )

    if embedded and embedded != expected:
        blockers.append(f"REPOSITORY_SHA_MISMATCH:{embedded}!={expected}")

    fixture_wallclock = None
    fixture_excluded = None
    fixture_auth = None
    if expected_probe_type == PROBE_TYPE_FORCED_FIXTURE:
        fixture_wallclock = bool(_FORCED_FIXTURE_WALLCLOCK_REACHABLE_REQUIRED)
        if fixture_wallclock:
            blockers.append("FORCED_FIXTURE_WALLCLOCK_REACHABLE_TRUE")
        metrics = {}
        try:
            metrics = _load_json(root / "economic_metrics.json")
        except (OSError, ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
            blockers.append(f"ECONOMIC_METRICS_LOAD_FAILED:{exc}")
        fixture_excluded = bool(
            metrics.get("excluded") is True or manifest.get("exclude_from_economic_metrics") is True
        )
        if not fixture_excluded:
            blockers.append("FORCED_FIXTURE_ECONOMIC_METRICS_NOT_EXCLUDED")
        try:
            auth = _load_json(root / "authorization_consumption.json")
        except (OSError, ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
            blockers.append(f"AUTHORIZATION_LOAD_FAILED:{exc}")
            auth = {}
        consumed = bool(auth.get("consumed"))
        productive = bool(auth.get("productive_authorization"))
        fixture_auth = bool(consumed or productive)
        if fixture_auth:
            blockers.append("FORCED_FIXTURE_CONSUMED_OR_CLAIMED_PRODUCTIVE_AUTHORIZATION")
        notes.append("FORCED_FIXTURE_ISOLATION_CHECKED")

    # Substitution guard: canonical evidence must not claim forced fixture mode and vice versa.
    mode = str(manifest.get("mode") or "")
    if expected_probe_type == PROBE_TYPE_CANONICAL and (
        mode == PROBE_TYPE_FORCED_FIXTURE or probe_type == PROBE_TYPE_FORCED_FIXTURE
    ):
        blockers.append("PROBE_FIXTURE_SUBSTITUTION_CANONICAL_AS_FORCED")
    if expected_probe_type == PROBE_TYPE_FORCED_FIXTURE and (
        mode == PROBE_TYPE_CANONICAL or probe_type == PROBE_TYPE_CANONICAL
    ):
        blockers.append("PROBE_FIXTURE_SUBSTITUTION_FORCED_AS_CANONICAL")

    sha_bound = (
        bool(embedded)
        and embedded == expected
        and not any(
            b.startswith("REPOSITORY_SHA_")
            or b.endswith("_MISSING")
            or "INVALID" in b
            or "EMPTY" in b
            or "NOT_LOWERCASE" in b
            or "MISMATCH" in b
            or "CONFLICT" in b
            for b in blockers
        )
    )
    ok = not blockers and sha_bound
    if ok:
        notes.append("REPOSITORY_SHA_BOUND")
    return ProbeFixtureShaBindingResultV1(
        ok=ok,
        verifier_id=VERIFIER_ID,
        capability_id=CAPABILITY_ID,
        probe_type=str(expected_probe_type),
        sha_bound=sha_bound,
        repository_sha=embedded,
        expected_sha=expected,
        blockers=blockers,
        notes=notes,
        forced_fixture_wallclock_reachable=fixture_wallclock,
        forced_fixture_economic_metrics_excluded=fixture_excluded,
        forced_fixture_can_consume_productive_authorization=fixture_auth,
    )
