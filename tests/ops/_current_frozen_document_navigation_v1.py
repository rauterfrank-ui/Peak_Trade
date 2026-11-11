"""Verify dated document/catalog binding without treating it as runtime admission."""

from pathlib import Path
import gzip
import hashlib
import json

import yaml


def assert_current_frozen_document_navigation(
    root: Path, *, spec: Path, owners=(), expected_spec_identifier: str | None = None
):
    model = json.loads((root / "docs/system_atlas/source/current-model.json").read_bytes())
    runbook = (root / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md").read_text()
    mapping = (root / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md").read_text()
    atlas = (root / "docs/system_atlas/generated/SYSTEM_ATLAS.md").read_text()
    assert "DOCUMENT_CLASS=CANONICAL_MASTER_RUNBOOK" in runbook
    assert "RUNTIME_AUTHORIZATION_EFFECT=NONE" in runbook
    assert "NO_PARALLEL_SEMANTIC_MODEL=true" in runbook
    assert "MAP_OF_TRUTH_AUTHORITY=NAVIGATION_ONLY" in mapping
    assert "ATLAS_ROLE=CURRENT_FROZEN_SYSTEM_DESCRIPTION" in atlas
    for key, value in [
        ("SOURCE_COMMIT", model["source_commit"]),
        ("SOURCE_TAG", model["source_tag"]),
        ("SYSTEM_FREEZE_TAG", model["system_freeze_tag"]),
    ]:
        for text in [runbook, mapping, atlas]:
            assert f"{key}={value}" in text
    assert "../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md" in mapping
    assert "../system_atlas/generated/SYSTEM_ATLAS.md" in mapping
    assert "current-files.jsonl.gz" in atlas
    inventory = [
        json.loads(line)
        for line in gzip.decompress(
            (root / "docs/system_atlas/source/current-files.jsonl.gz").read_bytes()
        ).splitlines()
    ]
    development = json.loads(
        (root / "docs/system_atlas/source/development-binding-v1.json").read_text()
    )
    assert development["frozen_source_commit"] == model["source_commit"]
    for path in (spec, *owners):
        relative = path.relative_to(root).as_posix()
        original = [row for row in inventory if row["path"] == relative]
        assert len(original) == 1, relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != original[0]["sha256"]:
            later = [row for row in development["files"] if row["path"] == relative]
            assert len(later) == 1 and later[0]["sha256"] == actual, relative
            assert later[0]["before_sha256"] == original[0]["sha256"], relative
    if expected_spec_identifier is not None:
        opening, _, rest = spec.read_text(encoding="utf-8").partition("\n")
        frontmatter, closing, _ = rest.partition("\n---\n")
        assert opening == "---" and closing, spec
        assert yaml.safe_load(frontmatter)["docs_token"] == expected_spec_identifier, spec
    return model["source_commit"]
