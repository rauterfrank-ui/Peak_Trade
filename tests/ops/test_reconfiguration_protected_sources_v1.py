"""The revised source guard still rejects new/unreviewed source changes."""

import json

import pytest

from tests.ops._reconfiguration_protected_sources_v1 import (
    MANIFEST,
    assert_approved_reconfiguration_sources_v1,
)


def test_new_source_edit_is_rejected(tmp_path):
    name = next(iter(json.loads(MANIFEST.read_text())["sha256"]))
    path = tmp_path / name
    path.parent.mkdir(parents=True)
    path.write_text("unapproved source replacement\n")
    with pytest.raises(AssertionError, match="PROTECTED_SOURCE_CHANGED_AFTER_APPROVAL"):
        assert_approved_reconfiguration_sources_v1(tmp_path, [name])


def test_unreviewed_protected_path_is_not_exempted(tmp_path):
    with pytest.raises(AssertionError, match="UNREVIEWED_PROTECTED_SOURCE"):
        assert_approved_reconfiguration_sources_v1(tmp_path, ["src/unreviewed.py"])
