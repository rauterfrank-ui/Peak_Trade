from __future__ import annotations

from pathlib import Path

from src.execution.replay_pack.canonical import write_jsonl_canonical


def test_jsonl_canonicalization_sorted_keys_and_lf(tmp_path: Path) -> None:
    p = tmp_path / "x.jsonl"
    write_jsonl_canonical(
        p,
        [
            {"b": 2, "a": 1},
            {"z": 1, "m": {"b": 1, "a": 2}},
        ],
    )

    raw = p.read_bytes()
    assert b"\r\n" not in raw
    lines = raw.decode("utf-8").splitlines()
    assert lines[0] == '{"a":1,"b":2}'
    assert lines[1] == '{"m":{"a":2,"b":1},"z":1}'
