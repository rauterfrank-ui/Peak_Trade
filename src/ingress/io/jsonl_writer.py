from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple

from ..normalized_event import NormalizedEvent
from ..validate import validate_normalized_event


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class JsonlWriteResult:
    path_jsonl: Path
    path_manifest: Path
    bytes_written: int
    records_written: int
    sha256_file: str
    sha256_chain_head: str


class JsonlEventWriter:
    """
    Append-only JSONL writer with sha256 chain.
    - Writes each line (NormalizedEvent.to_json_line()) to <path>.jsonl
    - Maintains <path>.manifest.json containing:
        {
          "algo":"sha256",
          "records": N,
          "bytes": B,
          "file_sha256": "...",
          "chain_head": "...",
          "chain": [{"i":1,"line_sha256":"...","chain":"..."}, ...]  # optional: can be elided later
        }
    NOTE: chain list can be truncated later; for now keep full for auditability.
    """
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.path_jsonl = self.base_path.with_suffix(".jsonl")
        self.path_manifest = self.base_path.with_suffix(".manifest.json")

    def append(self, events: Iterable[NormalizedEvent]) -> JsonlWriteResult:
        self.path_jsonl.parent.mkdir(parents=True, exist_ok=True)

        chain_head = "0" * 64
        records = 0
        bytes_written = 0
        chain_entries: list = []

        # If manifest exists, resume chain
        if self.path_manifest.exists() and self.path_jsonl.exists():
            m = json.loads(self.path_manifest.read_text(encoding="utf-8"))
            chain_head = m.get("chain_head", chain_head)
            records = int(m.get("records", 0))
            bytes_written = int(m.get("bytes", 0))
            chain_entries = list(m.get("chain", []))

        with self.path_jsonl.open("ab") as f:
            for ev in events:
                validate_normalized_event(ev)
                line = ev.to_json_line().encode("utf-8")
                line_sha = _sha256_hex(line)
                chain_head = _sha256_hex((chain_head + line_sha).encode("utf-8"))
                f.write(line)
                bytes_written += len(line)
                records += 1
                chain_entries.append({"i": records, "line_sha256": line_sha, "chain": chain_head})

        file_sha = _sha256_hex(self.path_jsonl.read_bytes())

        manifest = {
            "algo": "sha256",
            "records": records,
            "bytes": bytes_written,
            "file_sha256": file_sha,
            "chain_head": chain_head,
            "chain": chain_entries,
        }
        self.path_manifest.write_text(
            json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        return JsonlWriteResult(
            path_jsonl=self.path_jsonl,
            path_manifest=self.path_manifest,
            bytes_written=bytes_written,
            records_written=records,
            sha256_file=file_sha,
            sha256_chain_head=chain_head,
        )
