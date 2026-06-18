#!/usr/bin/env python3
"""Deterministic FULL-suite test sharding for CI (v1).

Partitions every ``tests/**/test_*.py`` file into exactly one shard using a
stable CRC32 bucket. Used by required PR matrix jobs and extended nightly runs.
"""

from __future__ import annotations

import argparse
import sys
import zlib
from pathlib import Path

DEFAULT_SHARD_COUNT = 8
MIN_SHARD_COUNT = 4
MAX_SHARD_COUNT = 12

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_ROOT = REPO_ROOT / "tests"


def enumerate_test_files(tests_root: Path = TESTS_ROOT) -> list[str]:
    files: list[str] = []
    for path in sorted(tests_root.rglob("test_*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        files.append(rel)
    return sorted(files, key=lambda item: item.encode("utf-8"))


def shard_index(path: str, shard_count: int) -> int:
    return zlib.crc32(path.encode("utf-8")) % shard_count


def partition_files(shard_count: int, tests_root: Path = TESTS_ROOT) -> dict[int, list[str]]:
    buckets: dict[int, list[str]] = {idx: [] for idx in range(shard_count)}
    for path in enumerate_test_files(tests_root):
        buckets[shard_index(path, shard_count)].append(path)
    return buckets


def verify_completeness(shard_count: int, tests_root: Path = TESTS_ROOT) -> None:
    all_files = enumerate_test_files(tests_root)
    buckets = partition_files(shard_count, tests_root)
    assigned: list[str] = []
    for idx in range(shard_count):
        assigned.extend(buckets[idx])
    if len(assigned) != len(all_files):
        raise SystemExit(
            f"shard completeness failed: assigned={len(assigned)} total={len(all_files)}"
        )
    if len(set(assigned)) != len(all_files):
        duplicates = len(assigned) - len(set(assigned))
        raise SystemExit(f"shard completeness failed: duplicate assignments={duplicates}")
    missing = sorted(set(all_files) - set(assigned))
    if missing:
        raise SystemExit(f"shard completeness failed: unassigned={missing[:5]}")
    empty = [idx for idx in range(shard_count) if not buckets[idx]]
    if empty:
        raise SystemExit(f"shard completeness failed: empty_shards={empty}")


def _validate_shard_count(shard_count: int) -> int:
    if not MIN_SHARD_COUNT <= shard_count <= MAX_SHARD_COUNT:
        raise SystemExit(
            f"shard_count must be in [{MIN_SHARD_COUNT}, {MAX_SHARD_COUNT}], got {shard_count}"
        )
    return shard_count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--shard-count",
        type=int,
        default=DEFAULT_SHARD_COUNT,
        help=f"Number of shards (default {DEFAULT_SHARD_COUNT})",
    )
    parser.add_argument(
        "--print-shard-count",
        action="store_true",
        help="Print shard count and exit",
    )
    parser.add_argument(
        "--emit-shard-files",
        type=int,
        metavar="SHARD_ID",
        help="Emit test file paths for the given shard id (one per line)",
    )
    parser.add_argument(
        "--verify-completeness",
        action="store_true",
        help="Fail unless every test file is assigned to exactly one shard",
    )
    parser.add_argument(
        "--print-shard-sizes",
        action="store_true",
        help="Print shard id and file count (for inventory tooling)",
    )
    args = parser.parse_args(argv)
    shard_count = _validate_shard_count(args.shard_count)

    if args.print_shard_count:
        print(shard_count)
        return 0

    if args.verify_completeness:
        verify_completeness(shard_count)
        return 0

    if args.print_shard_sizes:
        buckets = partition_files(shard_count)
        for idx in range(shard_count):
            print(f"{idx}\t{len(buckets[idx])}")
        return 0

    if args.emit_shard_files is not None:
        shard_id = args.emit_shard_files
        if not 0 <= shard_id < shard_count:
            raise SystemExit(f"shard id out of range: {shard_id}")
        for path in partition_files(shard_count)[shard_id]:
            print(path)
        return 0

    parser.error("no action requested")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
