from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts/ops/build_public_rest_to_supervised_observer_bridge_v0.py"

_CONFIRM = "NO_NETWORK_NO_BROKER_NO_EXCHANGE_NO_ORDERS"
_PROVIDER = "binance_spot_market_data_only"

_FORBIDDEN_IN_SCRIPT = (
    "import requests",
    "import httpx",
    "import aiohttp",
    "websocket",
    "import socket",
    "from socket",
    "import subprocess",
    "subprocess.",
    "time.sleep",
    "while True",
    "datetime.now",
    "src.execution",
    "src.live",
    "src.scheduler",
    "src.runtime",
    "import ccxt",
    "click",
    "typer",
    "uvicorn",
    "dotenv",
    "create_order",
    "place_order",
    "send_order",
    "submit_order",
    "cancel_order",
)


def _load_mod() -> Any:
    spec = importlib.util.spec_from_file_location("_bridge_pub", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(args: List[str], *, cwd: Optional[Path] = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        cwd=cwd or _REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _canonical_write(path: Path, obj: Mapping[str, Any]) -> None:
    path.write_bytes(
        (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode(
            "utf-8"
        )
    )


def _base_normalized() -> Dict[str, Any]:
    return {
        "schema": "captured_realistic_snapshot_observation_input_v0",
        "source": "redacted_public_snapshot_static",
        "provenance": {
            "captured_by": "operator",
            "captured_at_utc": "2026-05-17T12:00:00Z",
            "redacted": True,
            "network_fetch_during_test": True,
            "contains_credentials": False,
            "contains_orders": False,
            "contains_fills": False,
            "source_class": "public_rest_snapshot_one_shot",
            "provider": _PROVIDER,
            "capture_method": "public_rest_one_shot_bounded",
            "last_source": "derived_midpoint",
            "volume_source": "not_available_book_ticker_v0",
            "raw_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        },
        "snapshots": [
            {
                "symbol": "BTCUSDT",
                "observed_at_utc": "2026-05-17T12:00:01Z",
                "payload": {
                    "bid": "100.00",
                    "ask": "100.10",
                    "last": "100.05",
                    "mid": "100.05",
                    "spread_bps": "9.99",
                    "volume": "0",
                    "source_state": "public_rest_snapshot_one_shot",
                    "sequence": "1",
                    "bid_qty": "1.0",
                    "ask_qty": "2.0",
                },
            }
        ],
    }


def _base_manifest(norm_sha: str) -> Dict[str, Any]:
    return {
        "schema": "public_rest_market_capture_package_manifest_v0",
        "provider": _PROVIDER,
        "source": "public_rest_snapshot_one_shot",
        "network_allowed": True,
        "auth_required": False,
        "symbol": "BTCUSDT",
        "raw_file": "raw/public_rest_book_ticker_raw.json",
        "normalized_file": "normalized/captured_realistic_snapshots.json",
        "supervised_timed_manifest_file": "manifest/supervised_timed_manifest.json",
        "raw_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "normalized_sha256": norm_sha,
        "snapshot_count": 1,
        "redacted": True,
        "contains_credentials": False,
        "contains_orders": False,
        "contains_fills": False,
    }


def write_valid_capture_pkg(root: Path) -> Path:
    root.mkdir(parents=True)
    norm_path = root / "normalized" / "captured_realistic_snapshots.json"
    norm_path.parent.mkdir(parents=True)
    norm_obj = _base_normalized()
    _canonical_write(norm_path, norm_obj)
    sha = hashlib.sha256(norm_path.read_bytes()).hexdigest()
    man_path = root / "manifest" / "capture_manifest.json"
    man_path.parent.mkdir(parents=True)
    _canonical_write(man_path, _base_manifest(sha))
    return root


@pytest.fixture
def mod() -> Any:
    return _load_mod()


def test_requires_capture_package_dir() -> None:
    cp = _run(
        [
            "--output-dir",
            "/tmp",
            "--bridge-id",
            "b.v0",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    out = (cp.stderr or "") + (cp.stdout or "")
    assert "capture-package-dir" in out.lower() or "required" in out.lower()


def test_requires_output_dir() -> None:
    cp = _run(
        [
            "--capture-package-dir",
            "/tmp",
            "--bridge-id",
            "b.v0",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    out = (cp.stderr or "") + (cp.stdout or "")
    assert "output-dir" in out.lower() or "required" in out.lower()


def test_requires_bridge_id() -> None:
    cp = _run(
        [
            "--capture-package-dir",
            "/tmp",
            "--output-dir",
            "/tmp",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    out = (cp.stderr or "") + (cp.stdout or "")
    assert "bridge-id" in out.lower() or "required" in out.lower()


def test_requires_exact_no_network_token(tmp_path: Path) -> None:
    pkg = write_valid_capture_pkg(tmp_path / "in")
    out = tmp_path / "out"
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(out),
            "--bridge-id",
            "bridge.v0",
            "--confirm-no-network",
            "WRONG_TOKEN",
        ]
    )
    assert cp.returncode != 0
    assert "ERR" in (cp.stderr or "") or "invalid choice" in (cp.stderr or "").lower()


def test_rejects_missing_capture_package_dir(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    out = tmp_path / "out"
    cp = _run(
        [
            "--capture-package-dir",
            str(missing),
            "--output-dir",
            str(out),
            "--bridge-id",
            "b.v0",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    assert "ERR" in (cp.stderr or "")


def test_rejects_capture_package_dir_as_file(tmp_path: Path) -> None:
    f = tmp_path / "notadir"
    f.write_text("x", encoding="utf-8")
    cp = _run(
        [
            "--capture-package-dir",
            str(f),
            "--output-dir",
            str(tmp_path / "out"),
            "--bridge-id",
            "b.v0",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    assert "directory" in (cp.stderr or "").lower()


def test_rejects_unsafe_bridge_id(tmp_path: Path) -> None:
    pkg = write_valid_capture_pkg(tmp_path / "in")
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(tmp_path / "out"),
            "--bridge-id",
            "../evil",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    assert "ERR" in (cp.stderr or "")


def test_rejects_missing_capture_manifest(tmp_path: Path) -> None:
    pkg = tmp_path / "in"
    pkg.mkdir()
    (pkg / "normalized").mkdir()
    norm = _base_normalized()
    _canonical_write(pkg / "normalized" / "captured_realistic_snapshots.json", norm)
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(tmp_path / "out"),
            "--bridge-id",
            "b.v0",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    assert "manifest" in (cp.stderr or "").lower()


def test_rejects_missing_normalized_file(tmp_path: Path) -> None:
    pkg = tmp_path / "in"
    pkg.mkdir()
    (pkg / "manifest").mkdir()
    _canonical_write(
        pkg / "manifest" / "capture_manifest.json",
        _base_manifest("0" * 64),
    )
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(tmp_path / "out"),
            "--bridge-id",
            "b.v0",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    assert "missing" in (cp.stderr or "").lower() or "ERR" in (cp.stderr or "")


def test_rejects_wrong_capture_manifest_schema(tmp_path: Path) -> None:
    pkg = write_valid_capture_pkg(tmp_path / "in")
    man = _base_manifest("deadbeef")
    man["schema"] = "wrong_schema"
    norm_path = pkg / "normalized" / "captured_realistic_snapshots.json"
    sha = hashlib.sha256(norm_path.read_bytes()).hexdigest()
    man["normalized_sha256"] = sha
    _canonical_write(pkg / "manifest" / "capture_manifest.json", man)
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(tmp_path / "out"),
            "--bridge-id",
            "b.v0",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_rejects_provider_other_than_binance(tmp_path: Path) -> None:
    pkg = write_valid_capture_pkg(tmp_path / "in")
    man = json.loads((pkg / "manifest" / "capture_manifest.json").read_text(encoding="utf-8"))
    man["provider"] = "other"
    norm_path = pkg / "normalized" / "captured_realistic_snapshots.json"
    sha = hashlib.sha256(norm_path.read_bytes()).hexdigest()
    man["normalized_sha256"] = sha
    _canonical_write(pkg / "manifest" / "capture_manifest.json", man)
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(tmp_path / "out"),
            "--bridge-id",
            "b.v0",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_rejects_network_allowed_false_in_upstream_manifest(tmp_path: Path) -> None:
    pkg = write_valid_capture_pkg(tmp_path / "in")
    man = json.loads((pkg / "manifest" / "capture_manifest.json").read_text(encoding="utf-8"))
    man["network_allowed"] = False
    norm_path = pkg / "normalized" / "captured_realistic_snapshots.json"
    sha = hashlib.sha256(norm_path.read_bytes()).hexdigest()
    man["normalized_sha256"] = sha
    _canonical_write(pkg / "manifest" / "capture_manifest.json", man)
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(tmp_path / "out"),
            "--bridge-id",
            "b.v0",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_rejects_upstream_snapshot_count_other_than_one(tmp_path: Path) -> None:
    pkg = write_valid_capture_pkg(tmp_path / "in")
    man = json.loads((pkg / "manifest" / "capture_manifest.json").read_text(encoding="utf-8"))
    man["snapshot_count"] = 2
    norm_path = pkg / "normalized" / "captured_realistic_snapshots.json"
    sha = hashlib.sha256(norm_path.read_bytes()).hexdigest()
    man["normalized_sha256"] = sha
    _canonical_write(pkg / "manifest" / "capture_manifest.json", man)
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(tmp_path / "out"),
            "--bridge-id",
            "b.v0",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_rejects_normalized_sha_mismatch(tmp_path: Path) -> None:
    pkg = write_valid_capture_pkg(tmp_path / "in")
    man = json.loads((pkg / "manifest" / "capture_manifest.json").read_text(encoding="utf-8"))
    man["normalized_sha256"] = "0" * 64
    _canonical_write(pkg / "manifest" / "capture_manifest.json", man)
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(tmp_path / "out"),
            "--bridge-id",
            "b.v0",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_rejects_normalized_provenance_network_fetch_false(tmp_path: Path) -> None:
    pkg = tmp_path / "in"
    norm_path = pkg / "normalized" / "captured_realistic_snapshots.json"
    norm_path.parent.mkdir(parents=True)
    norm = _base_normalized()
    norm["provenance"]["network_fetch_during_test"] = False
    _canonical_write(norm_path, norm)
    sha = hashlib.sha256(norm_path.read_bytes()).hexdigest()
    man_path = pkg / "manifest" / "capture_manifest.json"
    man_path.parent.mkdir(parents=True)
    _canonical_write(man_path, _base_manifest(sha))
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(tmp_path / "out"),
            "--bridge-id",
            "b.v0",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_rejects_normalized_with_snapshot_count_not_one(tmp_path: Path) -> None:
    pkg = tmp_path / "in"
    norm_path = pkg / "normalized" / "captured_realistic_snapshots.json"
    norm_path.parent.mkdir(parents=True)
    norm = _base_normalized()
    norm["snapshots"] = list(norm["snapshots"]) + list(norm["snapshots"])
    _canonical_write(norm_path, norm)
    sha = hashlib.sha256(norm_path.read_bytes()).hexdigest()
    man_path = pkg / "manifest" / "capture_manifest.json"
    man_path.parent.mkdir(parents=True)
    _canonical_write(man_path, _base_manifest(sha))
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(tmp_path / "out"),
            "--bridge-id",
            "b.v0",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_rejects_forbidden_private_nested_key(tmp_path: Path) -> None:
    pkg = tmp_path / "in"
    norm_path = pkg / "normalized" / "captured_realistic_snapshots.json"
    norm_path.parent.mkdir(parents=True)
    norm = _base_normalized()
    norm["extra"] = {"api_key_ref": "x"}
    _canonical_write(norm_path, norm)
    sha = hashlib.sha256(norm_path.read_bytes()).hexdigest()
    man_path = pkg / "manifest" / "capture_manifest.json"
    man_path.parent.mkdir(parents=True)
    _canonical_write(man_path, _base_manifest(sha))
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(tmp_path / "out"),
            "--bridge-id",
            "b.v0",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_happy_path_writes_expected_layout(tmp_path: Path) -> None:
    pkg = write_valid_capture_pkg(tmp_path / "in")
    out = tmp_path / "out"
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(out),
            "--bridge-id",
            "bridge.happy",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode == 0, cp.stderr
    br = out / "bridge.happy"
    assert br.is_dir()
    assert (br / "source" / "capture_manifest.json").is_file()
    assert (br / "source" / "captured_realistic_snapshots.json").is_file()
    assert (br / "normalized" / "captured_realistic_snapshots_bridge.json").is_file()
    assert (br / "manifest" / "bridge_manifest.json").is_file()
    assert (br / "manifest" / "supervised_timed_manifest.json").is_file()
    assert (br / "PUBLIC_REST_TO_SUPERVISED_OBSERVER_BRIDGE_CLOSEOUT.md").is_file()
    br.resolve().relative_to(out.resolve())


def test_bridge_normalized_has_three_snapshots(tmp_path: Path) -> None:
    pkg = write_valid_capture_pkg(tmp_path / "in")
    out = tmp_path / "out"
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(out),
            "--bridge-id",
            "b3",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode == 0
    bridge_norm = json.loads(
        (out / "b3" / "normalized" / "captured_realistic_snapshots_bridge.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(bridge_norm["snapshots"]) == 3


def test_bridge_provenance_flags(tmp_path: Path) -> None:
    pkg = write_valid_capture_pkg(tmp_path / "in")
    out = tmp_path / "out"
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(out),
            "--bridge-id",
            "bf",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode == 0
    bridge_norm = json.loads(
        (out / "bf" / "normalized" / "captured_realistic_snapshots_bridge.json").read_text(
            encoding="utf-8"
        )
    )
    prov = bridge_norm["provenance"]
    assert prov["network_fetch_during_test"] is False
    assert prov["upstream_network_fetch_during_test"] is True


def test_supervised_manifest_absolute_path_and_max_obs(tmp_path: Path) -> None:
    pkg = write_valid_capture_pkg(tmp_path / "in")
    out = tmp_path / "out"
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(out),
            "--bridge-id",
            "sup",
            "--confirm-no-network",
            _CONFIRM,
            "--cadence-seconds",
            "120",
        ]
    )
    assert cp.returncode == 0
    sm = json.loads(
        (out / "sup" / "manifest" / "supervised_timed_manifest.json").read_text(encoding="utf-8")
    )
    assert sm["max_observations"] == 3
    assert sm["cadence_seconds"] == 120
    p = Path(sm["inputs"][0]["input_file"])
    assert p.is_absolute()
    assert p.is_file()
    assert p.name == "captured_realistic_snapshots_bridge.json"


def test_closeout_contains_required_machine_lines(tmp_path: Path) -> None:
    pkg = write_valid_capture_pkg(tmp_path / "in")
    out = tmp_path / "out"
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(out),
            "--bridge-id",
            "co",
            "--confirm-no-network",
            _CONFIRM,
        ]
    )
    assert cp.returncode == 0
    text = (out / "co" / "PUBLIC_REST_TO_SUPERVISED_OBSERVER_BRIDGE_CLOSEOUT.md").read_text(
        encoding="utf-8"
    )
    for line in (
        "VERDICT=PUBLIC_REST_TO_SUPERVISED_OBSERVER_BRIDGE_V0_CREATED_NOT_APPROVED",
        "DECISION=not_approved",
        "NETWORK_ALLOWED=false",
        "PUBLIC_REST_TO_SUPERVISED_OBSERVER_COMPATIBILITY_BRIDGE_CREATED=true",
        "UPSTREAM_NETWORK_FETCH_DURING_TEST=true",
        "BRIDGE_NETWORK_FETCH_DURING_TEST=false",
        "UPSTREAM_SNAPSHOT_COUNT=1",
        "BRIDGE_SNAPSHOT_COUNT=3",
    ):
        assert line in text


def test_no_forbidden_imports_in_script() -> None:
    raw = _SCRIPT.read_text(encoding="utf-8")
    for frag in _FORBIDDEN_IN_SCRIPT:
        assert frag not in raw, frag


def test_outputs_stay_under_explicit_tmp_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    pkg = write_valid_capture_pkg(tmp_path / "in")
    out = tmp_path / "explicit_out"
    cp = _run(
        [
            "--capture-package-dir",
            str(pkg),
            "--output-dir",
            str(out),
            "--bridge-id",
            "stay",
            "--confirm-no-network",
            _CONFIRM,
        ],
        cwd=tmp_path,
    )
    assert cp.returncode == 0
    base = out.resolve()
    for p in (out / "stay").rglob("*"):
        if p.is_file():
            rp = p.resolve()
            rp.relative_to(base)
            assert str(rp).startswith(str(base))
