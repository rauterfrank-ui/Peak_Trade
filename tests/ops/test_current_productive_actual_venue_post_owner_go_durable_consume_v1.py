"""Offline proofs of the actual-venue POST Owner-GO consumption boundary."""

import json
import stat
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, current_thread

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_actual_venue_post_owner_go_durable_consume_v1 as consume,
)


def _consume(store_root, baseline):
    return consume.persist_durable_post_owner_go_consume_v1(
        store_root=store_root,
        owner_go_token=consume.POST_OWNER_GO,
        baseline_origin_main_sha=baseline,
    )


def test_overlapping_consumers_cannot_replace_the_winner(tmp_path, monkeypatch):
    store_root = tmp_path / "durable" / "send"
    both_preparing = Barrier(2, timeout=10)
    first_finished = Event()
    clock = consume._utc_now_iso_v1

    def overlapping_clock():
        both_preparing.wait()
        if current_thread().name.startswith("second"):
            assert first_finished.wait(10)
        return clock()

    monkeypatch.setattr(consume, "_utc_now_iso_v1", overlapping_clock)
    with ThreadPoolExecutor(1, thread_name_prefix="first") as first:
        with ThreadPoolExecutor(1, thread_name_prefix="second") as second:
            winner = first.submit(_consume, store_root, "a" * 40)
            contender = second.submit(_consume, store_root, "b" * 40)
            try:
                record = winner.result(timeout=10)
            finally:
                first_finished.set()
            with pytest.raises(
                consume.CurrentProductiveActualVenuePostOwnerGoConsumeError,
                match="^POST_OWNER_GO_ALREADY_CONSUMED$",
            ):
                contender.result(timeout=10)

    loaded = consume.load_durable_post_owner_go_consume_v1(store_root=store_root)
    assert loaded["consumed"] is True
    assert loaded["record"] == record
    assert record["baseline_origin_main_sha"] == "a" * 40
    assert list(store_root.iterdir()) == [consume.durable_post_owner_go_path_v1(store_root)]


@pytest.mark.parametrize(
    ("consumed", "reason"),
    [(True, "POST_OWNER_GO_ALREADY_CONSUMED"), (False, "DURABLE_POST_GO_RECORD_CONFLICT")],
)
def test_existing_ledger_entry_is_never_replaced(tmp_path, consumed, reason):
    path = consume.durable_post_owner_go_path_v1(tmp_path)
    existing = json.dumps({"consumed": consumed, "owner_go_token": consume.POST_OWNER_GO})
    path.write_text(existing, encoding="utf-8")

    with pytest.raises(consume.CurrentProductiveActualVenuePostOwnerGoConsumeError, match=reason):
        _consume(tmp_path, "a" * 40)

    assert path.read_text(encoding="utf-8") == existing


def test_directory_sync_failure_fences_retry(tmp_path, monkeypatch):
    fsync = consume.os.fsync

    def fail_directory_sync(fd):
        if stat.S_ISDIR(consume.os.fstat(fd).st_mode):
            raise OSError("injected directory sync failure")
        fsync(fd)

    with monkeypatch.context() as failure:
        failure.setattr(consume.os, "fsync", fail_directory_sync)
        with pytest.raises(
            consume.CurrentProductiveActualVenuePostOwnerGoConsumeError,
            match="^DURABLE_POST_GO_PERSISTENCE_FAILED$",
        ):
            _consume(tmp_path, "a" * 40)

    with pytest.raises(
        consume.CurrentProductiveActualVenuePostOwnerGoConsumeError,
        match="^POST_OWNER_GO_ALREADY_CONSUMED$",
    ):
        _consume(tmp_path, "b" * 40)
    assert (
        consume.load_durable_post_owner_go_consume_v1(store_root=tmp_path)["record"][
            "baseline_origin_main_sha"
        ]
        == "a" * 40
    )
