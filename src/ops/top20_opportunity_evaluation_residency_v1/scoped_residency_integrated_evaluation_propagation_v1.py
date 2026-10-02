"""Co-propagate scoped integrated evaluation config when completion is required.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.single_selected_future_policy_v1.residency_eligibility_gate_v1 import (
    Cap23ResidencyEligibilityGateConfigV1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.models_v1 import ResidencyRuntimeConfigV1
from src.ops.top20_opportunity_evaluation_residency_v1.scoped_productive_residency_evaluation_completion_v1 import (
    ScopedResidencyIntegratedEvaluationConfigV1,
    venue_native_for_canonical_v1,
)


@dataclass(frozen=True)
class ScopedResidencyIntegratedEvaluationCoalesceResultV1:
    config: ScopedResidencyIntegratedEvaluationConfigV1 | None
    failure_codes: tuple[str, ...] = ()
    derivation_used: bool = False
    dataset_root: Path | None = None
    primary_venue_native_id: str = ""


def is_scoped_residency_completion_required_v1(
    *,
    gate: Cap23ResidencyEligibilityGateConfigV1,
    residency_config: ResidencyRuntimeConfigV1,
) -> bool:
    if not bool(gate.enabled):
        return False
    if not bool(gate.scoped_productive_activation):
        return False
    if not bool(residency_config.enabled):
        return False
    return True


def _repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]


def iter_registered_offline_integrated_evaluation_dataset_roots_v1(
    *,
    repo_root: Path | None = None,
) -> tuple[Path, ...]:
    """Evidence-backed offline integrated datasets (newest first)."""

    root = repo_root or _repo_root_v1()
    out: list[Path] = []
    bases = (
        root / "evidence/ops/golden_happy_vector_instrumented_information_funnel_post6999_v1",
        root / "evidence/ops/combined_ghv_whole_cycle_canary_measurement_v1",
    )
    for base in bases:
        if not base.is_dir():
            continue
        for child in sorted(
            (p for p in base.iterdir() if p.is_dir()),
            key=lambda p: p.name,
            reverse=True,
        ):
            if (child / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").is_file():
                out.append(child)
    return tuple(out)


def dataset_root_supports_venue_native_v1(
    *,
    dataset_root: Path,
    venue_native_id: str,
) -> bool:
    native = str(venue_native_id or "").strip()
    if not native:
        return False
    jsonl = dataset_root / "natural_market_data_get_capture_v1.jsonl"
    if not jsonl.is_file():
        return False
    try:
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if (
                str(
                    row.get("native_id") or row.get("instId") or row.get("venue_native_id") or ""
                ).strip()
                == native
            ):
                return True
            payload = row.get("payload") or row.get("data")
            if isinstance(payload, Mapping):
                if str(payload.get("instId") or "").strip() == native:
                    return True
            if isinstance(payload, list):
                for item in payload:
                    if (
                        isinstance(item, Mapping)
                        and str(item.get("instId") or "").strip() == native
                    ):
                        return True
    except (OSError, json.JSONDecodeError):
        return False
    return False


def primary_ranked_canonical_instrument_id_v1(
    ranking_snapshot: Mapping[str, Any],
) -> str:
    ranked = ranking_snapshot.get("ranked_candidates") or ranking_snapshot.get("ranked") or ()
    for row in ranked:
        if not isinstance(row, Mapping):
            continue
        cid = str(row.get("canonical_instrument_id") or row.get("instrument_id") or "").strip()
        if cid:
            return cid
    return ""


def resolve_dataset_root_for_venue_native_v1(
    *,
    venue_native_id: str,
    repo_root: Path | None = None,
) -> Path | None:
    for candidate in iter_registered_offline_integrated_evaluation_dataset_roots_v1(
        repo_root=repo_root
    ):
        if dataset_root_supports_venue_native_v1(
            dataset_root=candidate, venue_native_id=venue_native_id
        ):
            return candidate
    return None


def integrated_evaluation_supports_venue_natives_v1(
    *,
    config: ScopedResidencyIntegratedEvaluationConfigV1,
    venue_native_ids: Sequence[str],
) -> tuple[bool, tuple[str, ...]]:
    jsonl = config.dataset_root / "natural_market_data_get_capture_v1.jsonl"
    if not jsonl.is_file():
        # Caller-supplied offline workspace (stub replay / tests): defer to completion.
        return True, ()
    missing: list[str] = []
    for native in venue_native_ids:
        n = str(native or "").strip()
        if not n:
            missing.append("EMPTY_VENUE_NATIVE")
            continue
        if not dataset_root_supports_venue_native_v1(
            dataset_root=config.dataset_root, venue_native_id=n
        ):
            missing.append(f"DATASET_IDENTITY_MISMATCH:{n}")
    return (len(missing) == 0, tuple(missing))


def coalesce_scoped_residency_integrated_evaluation_config_v1(
    *,
    gate: Cap23ResidencyEligibilityGateConfigV1,
    residency_config: ResidencyRuntimeConfigV1,
    caller_config: ScopedResidencyIntegratedEvaluationConfigV1 | None,
    repository_sha: str,
    universe_snapshot: Mapping[str, Any],
    ranking_snapshot: Mapping[str, Any],
    allow_derivation: bool = True,
    repo_root: Path | None = None,
) -> ScopedResidencyIntegratedEvaluationCoalesceResultV1:
    if not is_scoped_residency_completion_required_v1(gate=gate, residency_config=residency_config):
        return ScopedResidencyIntegratedEvaluationCoalesceResultV1(config=caller_config)

    primary_cid = primary_ranked_canonical_instrument_id_v1(ranking_snapshot)
    primary_native = venue_native_for_canonical_v1(
        universe_snapshot=universe_snapshot,
        canonical_instrument_id=primary_cid,
    )
    if not primary_native:
        return ScopedResidencyIntegratedEvaluationCoalesceResultV1(
            config=None,
            failure_codes=("INTEGRATED_EVALUATION_IDENTITY_UNRESOLVED",),
            primary_venue_native_id="",
        )

    if caller_config is not None:
        ok, codes = integrated_evaluation_supports_venue_natives_v1(
            config=caller_config,
            venue_native_ids=(primary_native,),
        )
        if not ok:
            return ScopedResidencyIntegratedEvaluationCoalesceResultV1(
                config=None,
                failure_codes=codes or ("INTEGRATED_EVALUATION_IDENTITY_MISMATCH",),
                primary_venue_native_id=primary_native,
            )
        return ScopedResidencyIntegratedEvaluationCoalesceResultV1(
            config=caller_config,
            primary_venue_native_id=primary_native,
            dataset_root=caller_config.dataset_root,
        )

    if not allow_derivation:
        return ScopedResidencyIntegratedEvaluationCoalesceResultV1(
            config=None,
            failure_codes=("INTEGRATED_EVALUATION_CONFIG_MISSING",),
            primary_venue_native_id=primary_native,
        )

    dataset_root = resolve_dataset_root_for_venue_native_v1(
        venue_native_id=primary_native,
        repo_root=repo_root,
    )
    if dataset_root is None:
        return ScopedResidencyIntegratedEvaluationCoalesceResultV1(
            config=None,
            failure_codes=("INTEGRATED_EVALUATION_CONFIG_MISSING",),
            primary_venue_native_id=primary_native,
        )

    return ScopedResidencyIntegratedEvaluationCoalesceResultV1(
        config=ScopedResidencyIntegratedEvaluationConfigV1(
            dataset_root=dataset_root,
            repository_sha=repository_sha,
        ),
        derivation_used=True,
        dataset_root=dataset_root,
        primary_venue_native_id=primary_native,
    )
