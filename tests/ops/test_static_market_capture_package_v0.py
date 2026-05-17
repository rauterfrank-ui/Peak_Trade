from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Tuple, Union, cast

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts/ops/build_static_market_capture_package_v0.py"
_CONFIRM = "NO_NETWORK_NO_BROKER_NO_EXCHANGE_NO_ORDERS"

_RAW_SCHEMA = "operator_supplied_static_market_snapshot_raw_v0"
_RAW_SOURCE = "operator_supplied_export_static"

_FS_SCRIPT = _REPO_ROOT / "scripts" / "ops" / "run_shadow_observation_file_snapshot_v0.py"

_FORBIDDEN_IN_BUILDER_SCRIPT = (
    "import requests",
    "import httpx",
    "import aiohttp",
    "websocket",
    "import socket",
    "from socket",
    "import subprocess",
    "subprocess.",
    "time.sleep",
    "datetime.now",
    "while True",
    "src.execution",
    "src.live",
    "src.scheduler",
    "src.runtime",
    "import ccxt",
    " binance",
    " kraken",
    "click",
    "typer",
    "uvicorn",
    "create_order",
    "place_order",
    "send_order",
    "submit_order",
    "cancel_order",
)


def _load_snapshots() -> Callable[[Mapping[str, Any]], Any]:
    spec = importlib.util.spec_from_file_location("_snap_mod", _FS_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return cast(
        Callable[[Mapping[str, Any]], Any],
        getattr(mod, "load_snapshots_for_envelope"),
    )


def _run_builder(
    args: List[str], *, cwd: Union[Path, None] = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        cwd=cwd or _REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _valid_raw(snap_symbols: Tuple[str, str, str]) -> Dict[str, Any]:
    snaps = []
    for i, sym in enumerate(snap_symbols):
        snaps.append(
            {
                "symbol": sym,
                "observed_at_utc": f"2026-01-01T00:0{i}:00Z",
                "bid": str(100 + i),
                "ask": str(100 + i + 1),
                "last": str(100 + i + 2),
                "volume": str(50 + i),
            }
        )
    return {"schema": _RAW_SCHEMA, "source": _RAW_SOURCE, "snapshots": snaps}


@pytest.fixture
def isolated_out(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_requires_raw_input_file(isolated_out: Path) -> None:
    cp = _run_builder(
        [
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "pkg.safe",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    assert "raw-input-file" in (cp.stderr or "").lower()


def test_requires_output_dir(isolated_out: Path) -> None:
    rf = isolated_out / "in.json"
    rf.write_text(json.dumps(_valid_raw(("a", "b", "c"))), encoding="utf-8")
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--package-id",
            "pkg.safe",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    assert "--output-dir" in (cp.stderr or "").lower() or cp.returncode


def test_requires_package_id(isolated_out: Path) -> None:
    rf = isolated_out / "in.json"
    rf.write_text(json.dumps(_valid_raw(("a", "b", "c"))), encoding="utf-8")
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    assert "--package-id" in (cp.stderr or "").lower() or cp.returncode


def test_requires_exact_no_network_token(isolated_out: Path) -> None:
    rf = isolated_out / "in.json"
    rf.write_text(json.dumps(_valid_raw(("a", "b", "c"))), encoding="utf-8")
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "pkg.safe",
            "--confirm-no-network",
            "WRONG_TOKEN",
        ]
    )
    assert cp.returncode != 0


def test_rejects_missing_raw(isolated_out: Path) -> None:
    missing = isolated_out / "nope.json"
    cp = _run_builder(
        [
            "--raw-input-file",
            str(missing),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "pkg.safe",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    assert "not found" in (cp.stderr or "").lower()


def test_rejects_directory_raw_input(isolated_out: Path, tmp_path: Path) -> None:
    rf = isolated_out / "dir.json"
    rf.mkdir()
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "pkg.safe",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    assert "directory" in (cp.stderr or "").lower()


def test_rejects_glob_raw_input(isolated_out: Path) -> None:
    bogus = isolated_out / "*bad*.json"
    cp = _run_builder(
        [
            "--raw-input-file",
            str(bogus),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "pkg.safe",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    assert "glob" in (cp.stderr or "").lower()


@pytest.mark.parametrize(
    "bid_pkg",
    [
        "../evil",
        "a/b",
        "a\\\\b",
        "",
        "...",
        "!",
    ],
)
def test_rejects_unsafe_package_id(isolated_out: Path, bid_pkg: str) -> None:
    rf = isolated_out / "in.json"
    rf.write_text(json.dumps(_valid_raw(("x", "y", "z"))), encoding="utf-8")
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            bid_pkg,
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_rejects_wrong_raw_schema(isolated_out: Path) -> None:
    rf = isolated_out / "in.json"
    doc = _valid_raw(("a", "b", "c"))
    doc["schema"] = "wrong"
    rf.write_text(json.dumps(doc), encoding="utf-8")
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "ok.pkg",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    assert "schema" in (cp.stderr or "").lower()


def test_rejects_wrong_raw_source(isolated_out: Path) -> None:
    rf = isolated_out / "in.json"
    doc = _valid_raw(("a", "b", "c"))
    doc["source"] = "wrong_source"
    rf.write_text(json.dumps(doc), encoding="utf-8")
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "ok.pkg",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


@pytest.mark.parametrize("frag", ["order_id", "api_key"])
def test_rejects_forbidden_nested_keys(isolated_out: Path, frag: str) -> None:
    rf = isolated_out / "in.json"
    doc = _valid_raw(("a", "b", "c"))
    doc["meta"] = {frag: "x"}
    rf.write_text(json.dumps(doc), encoding="utf-8")
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "ok.pkg",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


@pytest.mark.parametrize("n", [0, 1, 2, 4, 10])
def test_rejects_snapshot_count_other_than_three(isolated_out: Path, n: int) -> None:
    rf = isolated_out / "in.json"
    snaps = [_valid_raw(("a", "b", "c"))["snapshots"][0]] * n if n > 0 else []
    rf.write_text(
        json.dumps({"schema": _RAW_SCHEMA, "source": _RAW_SOURCE, "snapshots": snaps}),
        encoding="utf-8",
    )
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "ok.pkg",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_rejects_missing_snapshot_field(isolated_out: Path) -> None:
    rf = isolated_out / "in.json"
    base = list(_valid_raw(("a", "b", "c"))["snapshots"])
    del base[0]["bid"]
    rf.write_text(
        json.dumps({"schema": _RAW_SCHEMA, "source": _RAW_SOURCE, "snapshots": base}),
        encoding="utf-8",
    )
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "ok.pkg",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_happy_path_writes_expected_layout(isolated_out: Path) -> None:
    rf = isolated_out / "in.json"
    rf.write_bytes(
        json.dumps(_valid_raw(("BTCUSDT", "BTCUSDT", "BTCUSDT")), sort_keys=True).encode() + b"\n"
    )
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "cap.pkg.v0",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode == 0, cp.stderr + cp.stdout
    root = isolated_out / "cap.pkg.v0"
    assert (root / "raw/operator_market_snapshot_raw.json").is_file()
    assert (root / "normalized/captured_realistic_snapshots.json").is_file()
    assert (root / "manifest/capture_manifest.json").is_file()
    assert (root / "manifest/supervised_timed_manifest.json").is_file()
    assert (root / "CAPTURE_PACKAGE_CLOSEOUT.md").is_file()


def test_raw_copy_matches_hash(isolated_out: Path) -> None:
    rf = isolated_out / "in.json"
    raw_bytes = json.dumps(_valid_raw(("S", "S", "S")), sort_keys=True).encode("utf-8") + b"\n"
    rf.write_bytes(raw_bytes)
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "samehash",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode == 0, cp.stderr
    written = isolated_out / "samehash/raw/operator_market_snapshot_raw.json"
    assert written.read_bytes() == raw_bytes


def test_normalized_passes_existing_loader(isolated_out: Path) -> None:
    rf = isolated_out / "in.json"
    rf.write_text(json.dumps(_valid_raw(("S", "S", "S"))), encoding="utf-8")
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "ldr",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode == 0, cp.stderr
    norm_path = isolated_out / "ldr/normalized/captured_realistic_snapshots.json"
    load = _load_snapshots()
    snaps, src = load(json.loads(norm_path.read_text(encoding="utf-8")))
    assert src == "operator_supplied_static"
    assert len(snaps) == 3


def test_capture_manifest_hashes_match(isolated_out: Path) -> None:
    import hashlib

    rf = isolated_out / "in.json"
    rf.write_text(json.dumps(_valid_raw(("S", "S", "S"))), encoding="utf-8")
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "mani",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode == 0, cp.stderr
    root = isolated_out / "mani"
    cap = json.loads((root / "manifest/capture_manifest.json").read_text())
    nr = root / "normalized/captured_realistic_snapshots.json"
    rr = root / "raw/operator_market_snapshot_raw.json"
    assert cap["raw_sha256"] == hashlib.sha256(rr.read_bytes()).hexdigest()
    assert cap["normalized_sha256"] == hashlib.sha256(nr.read_bytes()).hexdigest()


def test_supervised_manifest_absolute_normalized_path(isolated_out: Path) -> None:
    rf = isolated_out / "in.json"
    rf.write_text(json.dumps(_valid_raw(("S", "S", "S"))), encoding="utf-8")
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "sup.man",
            "--confirm-no-network",
            _CONFIRM,
            "--cadence-seconds",
            "90",
        ]
    )
    assert cp.returncode == 0, cp.stderr
    root = isolated_out / "sup.man"
    mf = json.loads((root / "manifest/supervised_timed_manifest.json").read_text())
    norm = isolated_out.resolve() / "sup.man/normalized/captured_realistic_snapshots.json"
    assert mf["inputs"][0]["input_file"] == str(norm.resolve())
    assert mf["max_observations"] == 3
    assert mf["cadence_seconds"] == 90


def test_closeout_machine_lines(isolated_out: Path) -> None:
    rf = isolated_out / "in.json"
    rf.write_text(json.dumps(_valid_raw(("S", "S", "S"))), encoding="utf-8")
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "clo",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode == 0, cp.stderr
    text = (isolated_out / "clo/CAPTURE_PACKAGE_CLOSEOUT.md").read_text()
    req = (
        "VERDICT=MARKET_CAPTURE_PACKAGE_V0_CREATED_NOT_APPROVED",
        "DECISION=not_approved",
        "NETWORK_ALLOWED=false",
        "ORDER_SUBMISSION_ALLOWED=false",
    )
    assert all(line in text for line in req)


def test_no_forbidden_tokens_in_builder_script() -> None:
    src = _SCRIPT.read_text(encoding="utf-8")
    lowered = src.lower()
    for frag in _FORBIDDEN_IN_BUILDER_SCRIPT:
        assert frag.lower() not in lowered, f"disallowed token {frag!r} appeared in builder"


def test_output_not_under_repo_package(isolated_out: Path) -> None:
    rf = isolated_out / "in.json"
    rf.write_text(json.dumps(_valid_raw(("T", "T", "T"))), encoding="utf-8")
    cp = _run_builder(
        [
            "--raw-input-file",
            str(rf),
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "not.in.repo",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode == 0, cp.stderr
    pkg_root = (isolated_out / "not.in.repo").resolve()
    repo_root = _REPO_ROOT.resolve()
    try:
        pkg_root.relative_to(repo_root)
        raises = False
    except ValueError:
        raises = True
    assert raises, "capture package produced under workspace unexpectedly"
