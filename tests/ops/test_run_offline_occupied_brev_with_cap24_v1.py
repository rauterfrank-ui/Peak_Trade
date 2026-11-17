from contextlib import nullcontext
from datetime import datetime
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

from scripts.ops import run_offline_occupied_brev_with_cap24_v1 as replay


def write(path, value):
    raw = json.dumps(value).encode()
    path.write_bytes(raw)
    return sha256(raw).hexdigest()


@pytest.fixture
def occupied_replay(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    fresh_root = root / "fresh"
    fresh_root.mkdir()
    publication = fresh_root / replay.CAP24_PUBLISH_MANIFEST_FILENAME
    publication_digest = write(
        publication, {"selection": "new", "decision_epoch": "2026-11-17T18:04:51Z"}
    )
    lock = root / replay.LOCK_NAME
    state = root / "occupied-n1-v2"
    initial = state / "attempts/1"
    initial.mkdir(parents=True)
    claim = {
        "owner": "n1_occupied_scope_recovery_v2",
        "recovery_context": {"binding": "original", "state_root": str(state), "attempt": 1},
    }
    lock_digest = write(lock, claim)
    bound_data = {"instrument_id": "BREV-canonical", "venue_native_id": "BREV-USDT-SWAP"}
    bound = SimpleNamespace(**bound_data, selection_id="held", to_dict=lambda: bound_data)
    budget_root = root / "budget"
    store_dir = budget_root / "owner"
    store_dir.mkdir(parents=True)
    store = store_dir / "reservations.sqlite3"
    store.touch()
    stamp = store.stat()
    wait = {"cursor_sha256": "original-cursor"}
    checkpoint = initial / replay.CHECKPOINT_FILENAME
    write(
        checkpoint,
        {
            "schema": claim["owner"],
            "binding": "original",
            "repository_sha": "held-revision",
            "outer_lock_sha256": lock_digest,
            "store_identity": [stamp.st_dev, stamp.st_ino],
            "native_wait": wait,
            "scope": {
                "budget_revision": [24, "original-head"],
                "position": {"bound": bound_data, "reservation_id": "original-hold"},
            },
        },
    )
    runtime_config = {"repository_sha": "held-revision"}
    cfg = SimpleNamespace(
        cap24_productivity_root=root / "held",
        lock_root=root,
        lane_state_root=root / "lane",
        expected_account_identity="offline",
    )
    prepared = SimpleNamespace(
        request={"config": cfg, "bound": bound, "origin_main_sha": "held-revision"}
    )
    selection = SimpleNamespace(
        **bound_data, selection_id="new", valid_until="2026-11-17T19:00:00Z"
    )
    monkeypatch.setattr(replay, "_prepare_occupied_n1_request", lambda **_: prepared)
    monkeypatch.setattr(replay, "unattended_request_digest_v1", lambda _: "original")
    monkeypatch.setattr(replay, "budget_owner_root_for_config_v1", lambda _: budget_root)
    monkeypatch.setattr(
        replay, "inspect_selection_v1", lambda **_: SimpleNamespace(selection=selection)
    )
    monkeypatch.setattr(replay, "_native_wait", lambda *_, **__: wait)
    monkeypatch.setattr(replay, "verify_occupied_wait_checkpoint_v1", lambda *_, **__: True)
    ports = []

    def open_ports(authorization):
        ports.append(authorization)
        return nullcontext()

    args = {
        "sandbox_root": root,
        "runtime_config": runtime_config,
        "expires_at_unix": 123.0,
        "cap24_productivity_root": fresh_root,
        "cap24_repository_sha": "a" * 40,
        "cap24_publication_sha256": publication_digest,
        "open_fixture_ports": open_ports,
        "replay_clock": lambda: datetime.fromisoformat("2026-11-17T18:22:00+00:00").timestamp(),
    }
    return args, ports, lock, claim, publication, selection


def test_confirmation_delegates_the_original_runtime_request(occupied_replay, monkeypatch):
    args, ports, lock, claim, _, _ = occupied_replay

    def run_original(**kwargs):
        assert kwargs["runtime_config"] is args["runtime_config"]
        assert kwargs["replay_clock"] is args["replay_clock"]
        assert kwargs["sandbox_root"] == args["sandbox_root"]
        claim["recovery_context"]["attempt"] = 2
        write(lock, claim)
        with kwargs["open_fixture_ports"]("original-authorization"):
            return {"status": "FINISHED", "result": "original-result"}

    monkeypatch.setattr(replay, "run_offline_occupied_n1_v2", run_original)
    result = replay.run_offline_occupied_brev_with_cap24_v1(**args)
    assert result["status"] == "FINISHED"
    assert result["result"] == "original-result"
    assert ports == ["original-authorization"]
    confirmation = result["cap24_confirmation"]
    assert confirmation["publication_sha256"] == args["cap24_publication_sha256"]
    assert confirmation["selection_id"] == "new"
    assert confirmation["occupied_selection_id"] == "held"
    assert confirmation["occupied_reservation_id"] == "original-hold"
    assert confirmation["occupied_cursor_sha256"] == "original-cursor"


def test_different_instrument_cannot_resume_the_occupied_lane(occupied_replay, monkeypatch):
    args, ports, _, _, _, selected = occupied_replay
    selected.venue_native_id = "MMT-USDT-SWAP"
    monkeypatch.setattr(
        replay,
        "run_offline_occupied_n1_v2",
        lambda **_: pytest.fail("a foreign selection reached the original runtime"),
    )
    assert replay.run_offline_occupied_brev_with_cap24_v1(**args) == {
        "status": "RECOVERY_CHECKPOINT_REQUIRED",
        "reason": "BREV_CAP24_FOREIGN_INSTRUMENT",
    }
    assert not ports


@pytest.mark.parametrize("changed", ["publication", "claim"])
def test_rechecks_publication_and_occupied_claim_before_ports(
    occupied_replay, monkeypatch, changed
):
    args, ports, lock, claim, publication, _ = occupied_replay

    def run_original(**kwargs):
        claim["recovery_context"]["attempt"] = 2 if changed == "publication" else 3
        write(lock, claim)
        if changed == "publication":
            write(publication, {"selection": "replaced"})
        with kwargs["open_fixture_ports"]("original-authorization"):
            pytest.fail("the invalid claim opened ports")

    monkeypatch.setattr(replay, "run_offline_occupied_n1_v2", run_original)
    result = replay.run_offline_occupied_brev_with_cap24_v1(**args)
    assert not ports
    assert result["status"] == "RECOVERY_CHECKPOINT_REQUIRED"
    assert result["reason"] == (
        "BREV_CAP24_PUBLICATION_CHANGED"
        if changed == "publication"
        else "BREV_CAP24_OCCUPIED_CHECKPOINT_CHANGED"
    )
