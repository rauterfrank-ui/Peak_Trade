#!/usr/bin/env python3
"""Append DONE token to local JSONL registry (append-only, untracked)."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


@dataclass(frozen=True)
class DoneRecord:
    kind: str
    ts_utc: str
    ops_status_exit: int
    prbi_decision: str
    prbi_score: int
    prbg_status: str
    prbg_sample_size: int
    prbg_anomaly_count: int
    prbg_error_count: int
    evidence_dir: str
    sha256_ok: bool
    done_path: str
    appended_at_utc: str

    def to_json(self) -> str:
        return json.dumps(
            {
                "kind": self.kind,
                "ts_utc": self.ts_utc,
                "ops_status_exit": self.ops_status_exit,
                "prbi_decision": self.prbi_decision,
                "prbi_score": self.prbi_score,
                "prbg_status": self.prbg_status,
                "prbg_sample_size": self.prbg_sample_size,
                "prbg_anomaly_count": self.prbg_anomaly_count,
                "prbg_error_count": self.prbg_error_count,
                "evidence_dir": self.evidence_dir,
                "sha256_ok": self.sha256_ok,
                "done_path": self.done_path,
                "appended_at_utc": self.appended_at_utc,
            },
            sort_keys=True,
        )


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_int(v: str, default: int = -1) -> int:
    try:
        return int(v.strip())
    except Exception:
        return default


def parse_done_token(path: Path) -> Dict[str, str]:
    kv: Dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or ":" not in line:
            continue
        k, v = line.split(":", 1)
        kv[k.strip()] = v.strip()
    return kv


def append_registry(
    done_path: Path,
    registry_jsonl: Path,
    sha256_ok: bool,
) -> DoneRecord:
    kv = parse_done_token(done_path)

    rec = DoneRecord(
        kind=kv.get("DONE", "unknown"),
        ts_utc=kv.get("ts_utc", "__MISSING__"),
        ops_status_exit=_parse_int(kv.get("ops_status_exit", "-1")),
        prbi_decision=kv.get("prbi_decision", "__MISSING__"),
        prbi_score=_parse_int(kv.get("prbi_score", "-1")),
        prbg_status=kv.get("prbg_status", "__MISSING__"),
        prbg_sample_size=_parse_int(kv.get("prbg_sample_size", "-1")),
        prbg_anomaly_count=_parse_int(kv.get("prbg_anomaly_count", "-1")),
        prbg_error_count=_parse_int(kv.get("prbg_error_count", "-1")),
        evidence_dir=kv.get("evidence_dir", "__MISSING__"),
        sha256_ok=bool(sha256_ok),
        done_path=str(done_path),
        appended_at_utc=_now_utc_iso(),
    )

    registry_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with registry_jsonl.open("a", encoding="utf-8") as f:
        f.write(rec.to_json() + "\n")

    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--done", required=True, help="Path to MORNING_ONE_SHOT_DONE_*.txt")
    ap.add_argument(
        "--registry",
        default="out/ops/registry/morning_one_shot_done_registry.jsonl",
        help="Append-only JSONL registry path (untracked)",
    )
    ap.add_argument(
        "--sha256-ok",
        default="unknown",
        choices=["true", "false", "unknown"],
        help="Whether the done .sha256 verification succeeded (best-effort)",
    )
    args = ap.parse_args()

    done_path = Path(args.done)
    if not done_path.exists():
        raise FileNotFoundError(done_path)

    sha_ok = {"true": True, "false": False, "unknown": False}[args.sha256_ok]
    reg = Path(args.registry)

    rec = append_registry(done_path, reg, sha_ok)
    print(rec.to_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
