"""Input loading for comparison_ssot.v1 from comparison_metric_input manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.meta.learning_loop.comparison_metric_input_v1.constants import METRIC_KEYS
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.comparison_metric_input_v1.validation import (
    validate_comparison_metric_input_manifest_v1,
)
from src.meta.learning_loop.comparison_metric_input_v1.identity import (
    verify_manifest_identity_and_integrity,
)
from src.meta.learning_loop.comparison_ssot_v1.constants import (
    ALLOWED_SOURCE_DOMAINS,
    MAX_INPUT_COUNT,
    MIN_INPUT_COUNT,
)
from src.meta.learning_loop.comparison_ssot_v1.models import (
    ComparisonSsotError,
    InputRef,
    LoadedMetricInput,
)


def _input_ref_from_manifest(manifest: dict[str, Any]) -> InputRef:
    source_ref = manifest.get("source_ref")
    if not isinstance(source_ref, dict):
        raise ComparisonSsotError("source_ref must be object")
    return InputRef(
        owner_domain=str(source_ref["owner_domain"]),
        ref_type=str(source_ref["ref_type"]).upper(),
        ref_id=str(source_ref["ref_id"]),
        digest=str(source_ref["digest"]),
    )


def canonical_sort_inputs(inputs: list[LoadedMetricInput]) -> list[LoadedMetricInput]:
    return sorted(inputs, key=lambda item: item.source_ref.sort_key())


def load_metric_input_manifest(path: Path) -> LoadedMetricInput:
    manifest = read_manifest(path)
    validate_comparison_metric_input_manifest_v1(manifest)
    verify_manifest_identity_and_integrity(manifest)
    source_domain = str(manifest["source_domain"]).upper()
    if source_domain not in ALLOWED_SOURCE_DOMAINS:
        raise ComparisonSsotError(f"unsupported source_domain: {source_domain}")
    source_ref = _input_ref_from_manifest(manifest)
    expected_id = str(manifest["comparison_metric_input_id"])
    return LoadedMetricInput(
        manifest_path=path.resolve(),
        manifest=manifest,
        comparison_metric_input_id=expected_id,
        source_domain=source_domain,
        source_ref=source_ref,
        evaluation_slice_id=str(manifest["evaluation_slice_id"]),
        comparability_metadata=dict(manifest["comparability_metadata"]),
        metrics=dict(manifest["metrics"]),
    )


def load_and_validate_inputs(manifest_paths: list[Path]) -> list[LoadedMetricInput]:
    if len(manifest_paths) < MIN_INPUT_COUNT:
        raise ComparisonSsotError(
            f"at least {MIN_INPUT_COUNT} input manifests required, got {len(manifest_paths)}"
        )
    if len(manifest_paths) > MAX_INPUT_COUNT:
        raise ComparisonSsotError(
            f"at most {MAX_INPUT_COUNT} input manifests allowed, got {len(manifest_paths)}"
        )

    loaded: list[LoadedMetricInput] = []
    seen_paths: set[str] = set()
    seen_full_refs: set[tuple[str, str, str, str]] = set()
    seen_ref_ids: dict[str, str] = {}

    for path in manifest_paths:
        resolved = str(path.resolve())
        if resolved in seen_paths:
            raise ComparisonSsotError(f"duplicate manifest path (fail-closed): {path}")
        seen_paths.add(resolved)

        item = load_metric_input_manifest(path)
        ref_key = item.source_ref.sort_key()
        if ref_key in seen_full_refs:
            raise ComparisonSsotError(
                f"duplicate canonical input ref (fail-closed): {item.source_ref.ref_id}"
            )
        seen_full_refs.add(ref_key)

        prior_digest = seen_ref_ids.get(item.source_ref.ref_id)
        if prior_digest is not None and prior_digest != item.source_ref.digest:
            raise ComparisonSsotError(
                f"same ref_id with different digest (fail-closed): {item.source_ref.ref_id}"
            )
        seen_ref_ids[item.source_ref.ref_id] = item.source_ref.digest

        metrics = item.metrics
        for key in METRIC_KEYS:
            if key not in metrics:
                raise ComparisonSsotError(f"missing metric {key} in {path}")
        if set(metrics.keys()) != set(METRIC_KEYS):
            raise ComparisonSsotError(f"unexpected metric keys in {path}")

        loaded.append(item)

    domains = {item.source_domain for item in loaded}
    if len(domains) != 1:
        raise ComparisonSsotError(
            f"cross-domain inputs not allowed (fail-closed): {sorted(domains)}"
        )

    return canonical_sort_inputs(loaded)
