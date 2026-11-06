"""Historical schema expectations must come from source literals, never today's models."""

from pathlib import Path
import json

import pytest

from scripts.ops.reconstruct_gvef_contract_schema_manifest_v1 import (
    SOURCE_ROOT,
    OUTPUT_ROOT,
    reconstruct_contract_schema_manifest_v1,
)


def _sources():
    return (
        (SOURCE_ROOT / "gvef_builder.reconstructed.py.txt").read_text(),
        (SOURCE_ROOT / "gvef_closure.reconstructed.py.txt").read_text(),
    )


def test_reconstruction_reproduces_the_committed_independent_sixteen_contracts():
    payload, provenance = reconstruct_contract_schema_manifest_v1(*_sources())
    assert payload == json.loads((OUTPUT_ROOT / "contract_schema_manifest.json").read_text())
    assert provenance["schema_count"] == 16
    assert provenance["field_count"] == 111
    assert provenance["original_generated_output_bytes_recovered"] is False
    assert len(payload["digest_model"]["protected_domains"]) == 12


def test_source_field_change_is_not_silently_corrected_to_the_current_model():
    from src.evaluation.golden_vectors.contracts.models import RunManifestV1

    builder, closure = _sources()
    changed = builder.replace(
        '("run_id", "string", True, False, "uuid_v4"',
        '("run_id", "string", False, True, "uuid_v4"',
        1,
    )
    assert changed != builder
    payload, _ = reconstruct_contract_schema_manifest_v1(changed, closure)
    assert payload["schemas"]["RunManifest"][0]["REQUIRED"] is False
    assert RunManifestV1.model_fields["run_id"].is_required() is True


def test_schema_expression_is_rejected_without_executing_historical_code(tmp_path: Path):
    builder, closure = _sources()
    marker = tmp_path / "must_not_be_written"
    inserted = f'__import__("pathlib").Path({str(marker)!r}).write_text("executed"), '
    changed = builder.replace('"RunManifest": fields(', '"RunManifest": fields(' + inserted, 1)
    assert changed != builder
    with pytest.raises(ValueError):
        reconstruct_contract_schema_manifest_v1(changed, closure)
    assert not marker.exists()
