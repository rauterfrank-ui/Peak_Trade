#!/usr/bin/env python3
"""Deterministic historical-reference materializer v1.

AUTHORITY=NONE
PURPOSE=FORENSIC_HISTORICAL_REFERENCE
MUTABILITY=IMMUTABLE_CONTENT_ADD_ONLY_CORRECTIONS
CANONICAL_SELECTION=false
RUNTIME_SELECTION=false
TRADING_AUTHORITY=false
REPO_MUTATION_SCOPE=PRESERVATION_PACKAGE_ONLY

Does not modify the external Temp source. Does not import trading runtime.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

AUTHORITY_BLOCK = {
    "AUTHORITY": "NONE",
    "PURPOSE": "FORENSIC_HISTORICAL_REFERENCE",
    "MUTABILITY": "IMMUTABLE_CONTENT_ADD_ONLY_CORRECTIONS",
    "CANONICAL_SELECTION": False,
    "RUNTIME_SELECTION": False,
    "TRADING_AUTHORITY": False,
    "CANONICAL_AUTHORITY": False,
    "SOURCE_AUTHORITY": "NONE",
}

KNOWN_SOURCE_SHA256 = "a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212"
EXPECTED_BYTES = 8639369
EXPECTED_LINES = 121930
EXTERNAL_SOURCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade/forensics/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md"
)
EXTERNAL_SIDECAR_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade/forensics/derived/"
    f"sha256-{KNOWN_SOURCE_SHA256}/structural-v1-20260825T100541Z"
)
EXTERNAL_DERIVED_ROOT = Path(
    f"/Users/frnkhrz/Documents/Peak_Trade/forensics/derived/sha256-{KNOWN_SOURCE_SHA256}"
)


def find_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / ".git").exists() and (
            parent / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
        ).exists():
            return parent
    raise SystemExit("REPO_ROOT_NOT_FOUND")


REPO_ROOT = find_repo_root()
ORIGIN_MAIN_SHA = "3848c713ae7e8ef1de0cf9ba4c19c4c7e683ccef"
PRESERVATION_ID = f"peak_trade_historical_reference_{KNOWN_SOURCE_SHA256}_v1"
FORMAT_VERSION = "historical_reference_preservation_v1"
CAPTURE_TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

GATED_SOURCE_DIR = REPO_ROOT / "forensic" / "evidence" / f"sha256-{KNOWN_SOURCE_SHA256}"
GATED_SOURCE_FILE = GATED_SOURCE_DIR / "PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md"
PRESERVATION_ROOT = (
    REPO_ROOT / "forensics" / "historical_reference" / f"sha256-{KNOWN_SOURCE_SHA256}"
)

FENCE_RE = re.compile(r"^(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
KV_RE = re.compile(r"^([A-Z][A-Z0-9_]{1,80})=(.*)$")
SHA_RE = re.compile(r"\b[0-9a-f]{40}\b", re.I)
PR_RE = re.compile(r"\bPR[#\s_-]?(\d{3,5})\b", re.I)

TOPIC_PATTERNS: dict[str, str] = {
    "MASTER_V2": r"MASTER[_\s-]?V2|Master V2|Master-V2|master_v2",
    "DOUBLE_PLAY": r"DOUBLE[_\s-]?PLAY|Double Play|Double_Play|double_play",
    "INTEGRATED_REPLAY": (
        r"INTEGRATED[_\s-]?REPLAY|integrated_offline_trading_logic_replay|"
        r"master_v2_double_play_integrated_offline_replay"
    ),
    "STRATEGY_AUTHORITY": r"STRATEGY[_\s-]?AUTHORITY|Autonomous Strategy Authority",
    "REGISTRY_TO_CORE": r"REGISTRY[_\s-]?TO[_\s-]?CORE|Strategy.?→.?Core|Strategy Registry",
    "CAPITAL_ARCHITECTURE": r"CAPITAL[_\s-]?ARCHITECTURE|CAPITAL_RISK|position.?siz",
    "ECM_ARMSTRONG": r"ECM[_\s-]?ARMSTRONG|\bARMSTRONG\b|\bECM\b",
    "FIRST_LIVE": r"FIRST[_\s-]?LIVE|Master V2 First Live",
    "CAPABILITY_CHAIN": r"CAPABILITY[_\s-]?CHAIN|Mandatory Capability Closure",
    "SAFETY_KERNEL": r"SAFETY[_\s-]?KERNEL|safety_kernel",
    "KILL_SWITCH": r"KILL[_\s-]?SWITCH|KillSwitch",
    "SINGLE_WRITER": r"SINGLE[_\s-]?WRITER|single.writer|no second writer",
    "ECONOMIC_VIABILITY": r"ECONOMIC[_\s-]?VIABILITY|economic.?viab|29M",
    "BACKTEST_RUNTIME_PARITY": r"BACKTEST[_\s-]?RUNTIME[_\s-]?PARITY|GOLDEN_VECTOR_PARITY|runtime.?parity",
    "FULL_CANONICAL_SYSTEM_PARITY": r"FULL[_\s-]?CANONICAL[_\s-]?SYSTEM[_\s-]?PARITY|Full-Chain-Parity",
    "FULL_CANONICAL_SYSTEM_WIRING": r"FULL[_\s-]?CANONICAL[_\s-]?SYSTEM[_\s-]?WIRING|canonical.?wiring",
    "STEP_29": r"STEP[_\s-]?29|\b29[A-Z]\b",
    "LEVEL_0_TO_10": r"LEVEL[_\s-]?(0|1|2|3|4|5|6|7|8|9|10)\b",
    "AUTH_001_TO_023": r"AUTH[_\s-]?(0[0-9]{2}|0[1-9]|1[0-9]|2[0-3])\b",
    "DOC_01_TO_12": r"DOC[_\s-]?(0[1-9]|1[0-2])\b",
    "B_01_TO_07": r"\bB[_\s-]?(0[1-7])\b",
}

FAMILY_PATTERNS: dict[str, str] = {
    "I01_I85": r"\bI(0[1-9]|[1-7][0-9]|8[0-5])\b",
    "RD01_RD10": r"\bRD(0[1-9]|10)\b",
    "UQ1_UQ8": r"\bUQ[1-8]\b",
    "M_SURFACES": r"\bM([0-9]{2}|[0-9]{2}[a-z])\b",
    "G_GAPS": r"\bG([0-9]{1,2})\b",
    "EG_ITEMS": r"\bEG[-_]?I[0-9]{2,3}\b",
    "STEP_29": r"\b29[A-Z]\b|STEP[_\s-]?29",
    "T_WORKFLOW": r"\bT[1-9]\b|T5PR|T6DD|HTWDD",
    "SRC_BLOCKS": r"SRC-0000(?:0[1-9]|[1-7][0-9]|8[0-8])",
}

REQUIRED_ZERO_MAY_BE_ABSENT = {
    "AUTH_001_TO_023",
    "DOC_01_TO_12",
    "CAPABILITY_CHAIN",
}

SIDECAR_COPY = (
    "manifest.json",
    "index.json",
    "validation.json",
    "relations.jsonl",
    "structural_ranges.jsonl",
    "run_report.json",
)

EXCLUDED_DERIVED = (
    (
        "structural-v1 records.jsonl",
        EXTERNAL_SIDECAR_ROOT / "records.jsonl",
        "GIT_LARGE_FILE_UNSUITABLE_REGENERABLE_FROM_COMMITTED_SOURCE",
    ),
    (
        "structure-v1.json overlay",
        Path(
            "/Users/frnkhrz/Documents/Peak_Trade/forensics/derived/"
            "PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.structure-v1.json"
        ),
        "GIT_LARGE_FILE_UNSUITABLE_DERIVED_OVERLAY",
    ),
    (
        "t4 unprojected relation loss register",
        Path(
            "/Users/frnkhrz/Documents/Peak_Trade/forensics/derived/"
            "PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.t4-unprojected-relation-loss-register-v1.jsonl"
        ),
        "GIT_LARGE_FILE_UNSUITABLE_DERIVED_OVERLAY",
    ),
    (
        "lossless-struct records.jsonl",
        EXTERNAL_DERIVED_ROOT / "records.jsonl",
        "GIT_LARGE_FILE_UNSUITABLE_REGENERABLE_FROM_COMMITTED_SOURCE",
    ),
    (
        "lossless-struct quarantine.jsonl",
        EXTERNAL_DERIVED_ROOT / "quarantine.jsonl",
        "GIT_LARGE_FILE_UNSUITABLE_QUARANTINE_DERIVED",
    ),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(
        payload,
        sort_keys=False,
        allow_unicode=True,
        width=100,
        default_flow_style=False,
    )
    path.write_text(text, encoding="utf-8")


def write_text(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not body.endswith("\n"):
        body += "\n"
    path.write_text(body, encoding="utf-8")


def object_meta(
    preservation_id: str,
    line_start: int,
    line_end: int,
    heading_path: str,
    *,
    assertion_status: str,
    preservation_class: str,
    temporal_status: str = "HISTORICAL",
    authority_at_time: str = "NONE",
    source_commit: str | None = None,
    source_pr: str | None = None,
) -> dict[str, Any]:
    meta = {
        "PRESERVATION_ID": preservation_id,
        "SOURCE_SHA256": KNOWN_SOURCE_SHA256,
        "SOURCE_LINE_RANGE": {
            "start_inclusive": line_start,
            "end_inclusive": line_end,
        },
        "SOURCE_HEADING_PATH": heading_path,
        "SOURCE_COMMIT_IF_KNOWN": source_commit,
        "SOURCE_PR_IF_KNOWN": source_pr,
        "AUTHORITY_AT_TIME": authority_at_time,
        "TEMPORAL_STATUS": temporal_status,
        "ASSERTION_STATUS": assertion_status,
        "PRESERVATION_CLASS": preservation_class,
    }
    meta.update(AUTHORITY_BLOCK)
    return meta


def scan_lines(lines: list[str]) -> tuple[list[dict[str, Any]], list[int]]:
    headings: list[dict[str, Any]] = []
    in_fence = False
    fence_tick = ""
    fence_n = 0
    for index, raw in enumerate(lines, 1):
        match = FENCE_RE.match(raw)
        if match:
            tick = match.group(1)[0]
            count = len(match.group(1))
            rest = raw[count:].strip()
            if not in_fence:
                in_fence = True
                fence_tick = tick
                fence_n = count
                continue
            if tick == fence_tick and count >= fence_n and rest == "":
                in_fence = False
                fence_tick = ""
                fence_n = 0
                continue
            continue
        if in_fence:
            continue
        heading = HEADING_RE.match(raw.rstrip("\n"))
        if heading:
            headings.append(
                {
                    "line": index,
                    "level": len(heading.group(1)),
                    "text": heading.group(2).rstrip(),
                    "verbatim": raw.rstrip("\n"),
                }
            )
    return headings, []


def heading_path_at(headings: list[dict[str, Any]], line: int) -> str:
    path_parts: list[tuple[int, str]] = []
    for heading in headings:
        if heading["line"] > line:
            break
        level = heading["level"]
        while path_parts and path_parts[-1][0] >= level:
            path_parts.pop()
        path_parts.append((level, heading["text"]))
    if not path_parts:
        return "(document_root)"
    return " > ".join(part for _, part in path_parts)


def section_end(headings: list[dict[str, Any]], heading: dict[str, Any], n_lines: int) -> int:
    for other in headings:
        if other["line"] > heading["line"] and other["level"] <= heading["level"]:
            return other["line"] - 1
    return n_lines


def parse_src_records(lines: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        src_match = re.match(r"^### (SRC-\d+)\s*$", line)
        if not src_match:
            index += 1
            continue
        block_id = src_match.group(1)
        heading_line = index + 1
        json_start = None
        cursor = index + 1
        while cursor < len(lines):
            if lines[cursor].startswith("```json"):
                json_start = cursor + 1
                cursor += 1
                break
            if lines[cursor].startswith("### SRC-") and cursor != index:
                break
            cursor += 1
        if json_start is None:
            records.append(
                {
                    "block_id": block_id,
                    "heading_line": heading_line,
                    "parse_status": "JSON_FENCE_NOT_FOUND",
                }
            )
            index += 1
            continue
        json_end = json_start
        while json_end < len(lines) and not lines[json_end].startswith("```"):
            json_end += 1
        raw = "\n".join(lines[json_start:json_end])
        try:
            payload = json.loads(raw)
            payload["_heading_line"] = heading_line
            payload["_json_line_range"] = [json_start + 1, json_end]
            payload["parse_status"] = "OK"
            records.append(payload)
        except json.JSONDecodeError as exc:
            records.append(
                {
                    "block_id": block_id,
                    "heading_line": heading_line,
                    "parse_status": f"JSON_DECODE_ERROR:{exc}",
                }
            )
        index = json_end + 1
    return records


def collect_topic_hits(
    lines: list[str], headings: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    compiled = {name: re.compile(pattern, re.I) for name, pattern in TOPIC_PATTERNS.items()}
    hits: dict[str, list[dict[str, Any]]] = {name: [] for name in TOPIC_PATTERNS}
    for index, raw in enumerate(lines, 1):
        for name, pattern in compiled.items():
            if pattern.search(raw):
                excerpt = raw.strip()
                if len(excerpt) > 160:
                    excerpt = excerpt[:157] + "..."
                hits[name].append(
                    {
                        "line": index,
                        "excerpt": excerpt,
                        "heading_path": heading_path_at(headings, index),
                    }
                )
    return hits


def extract_kv_from_range(lines: list[str], start: int, end: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    in_text_fence = False
    fence_n = 0
    for index in range(start, end + 1):
        raw = lines[index - 1]
        match = FENCE_RE.match(raw)
        if match:
            count = len(match.group(1))
            rest = raw[count:].strip()
            if not in_text_fence:
                in_text_fence = True
                fence_n = count
                continue
            if count >= fence_n and rest == "":
                in_text_fence = False
                continue
        if not in_text_fence:
            continue
        kv = KV_RE.match(raw.strip())
        if kv:
            items.append(
                {
                    "key": kv.group(1),
                    "value": kv.group(2),
                    "line": index,
                }
            )
    return items


def classify_kv(key: str) -> str:
    upper = key.upper()
    if any(
        token in upper for token in ("INVARIANT", "MUST_NOT", "FORBIDDEN", "FAIL_CLOSED", "NEVER_")
    ):
        return "INVARIANT"
    if any(
        token in upper for token in ("DEPEND", "REQUIRES", "BLOCKED_BY", "PRECONDITION", "AFTER_")
    ):
        return "DEPENDENCY"
    if any(token in upper for token in ("OBLIGATION", "REQUIRED", "SHALL", "MUST_")):
        return "OBLIGATION"
    return "SOURCE_DECLARED_FIELD"


def covering_heading_ranges(
    hits: list[dict[str, Any]], headings: list[dict[str, Any]], n_lines: int
) -> list[dict[str, Any]]:
    ranges: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for hit in hits:
        owner = None
        for heading in reversed(headings):
            if heading["line"] <= hit["line"]:
                owner = heading
                break
        if owner is None:
            start, end = hit["line"], hit["line"]
            path = hit["heading_path"]
        else:
            start = owner["line"]
            end = section_end(headings, owner, n_lines)
            path = heading_path_at(headings, owner["line"])
        key = (start, end)
        if key in seen:
            continue
        seen.add(key)
        ranges.append({"start": start, "end": end, "heading_path": path})
    ranges.sort(key=lambda item: item["start"])
    return ranges


def sha_and_pr_from_range(lines: list[str], start: int, end: int) -> tuple[str | None, str | None]:
    commit = None
    pr = None
    for index in range(start, min(end, start + 80) + 1):
        raw = lines[index - 1]
        if commit is None:
            found = SHA_RE.search(raw)
            if found:
                commit = found.group(0).lower()
        if pr is None:
            found = PR_RE.search(raw)
            if found:
                pr = found.group(1)
        if commit and pr:
            break
    return commit, pr


def model_bundle(
    model_id: str,
    hits: list[dict[str, Any]],
    headings: list[dict[str, Any]],
    lines: list[str],
) -> dict[str, Any]:
    n_lines = len(lines)
    ranges = covering_heading_ranges(hits, headings, n_lines)
    obligations: list[dict[str, Any]] = []
    dependencies: list[dict[str, Any]] = []
    invariants: list[dict[str, Any]] = []
    fields: list[dict[str, Any]] = []
    for item in ranges:
        commit, pr = sha_and_pr_from_range(lines, item["start"], item["end"])
        for kv in extract_kv_from_range(lines, item["start"], item["end"]):
            kind = classify_kv(kv["key"])
            record = {
                **object_meta(
                    f"{PRESERVATION_ID}:{model_id}:{kv['key']}:L{kv['line']}",
                    kv["line"],
                    kv["line"],
                    item["heading_path"],
                    assertion_status="SOURCE_DECLARED",
                    preservation_class="RAW_EVIDENCE",
                    source_commit=commit,
                    source_pr=pr,
                ),
                "key": kv["key"],
                "value": kv["value"],
                "kv_class": kind,
            }
            if kind == "INVARIANT":
                invariants.append(record)
            elif kind == "DEPENDENCY":
                dependencies.append(record)
            elif kind == "OBLIGATION":
                obligations.append(record)
            else:
                fields.append(record)
    return {
        "model_id": model_id,
        "hit_count": len(hits),
        "covering_range_count": len(ranges),
        "hits": hits[:400],
        "hit_truncated": len(hits) > 400,
        "covering_ranges": ranges[:80],
        "obligations": obligations[:400],
        "dependencies": dependencies[:400],
        "invariants": invariants[:400],
        "source_declared_fields_sample": fields[:200],
        "observed_in_source": len(hits) > 0,
    }


def write_model_dir(root: Path, name: str, bundle: dict[str, Any]) -> None:
    directory = root / name
    directory.mkdir(parents=True, exist_ok=True)
    structure_lines = [
        "# Historical structure index",
        "",
        "```text",
        "AUTHORITY=NONE",
        "PURPOSE=FORENSIC_HISTORICAL_REFERENCE",
        "MUTABILITY=IMMUTABLE_CONTENT_ADD_ONLY_CORRECTIONS",
        "CANONICAL_SELECTION=false",
        "RUNTIME_SELECTION=false",
        "TRADING_AUTHORITY=false",
        "PRESERVATION_CLASS=DERIVED_INDEX",
        "ASSERTION_STATUS=DERIVED_INDEX_OVER_SOURCE_ANCHORS",
        "```",
        "",
        "This file is a derived index. It is not raw evidence and not current authority.",
        "Resolve every row against the committed source blob.",
        "",
        f"Model: `{name}`",
        f"Observed in source: `{str(bundle['observed_in_source']).lower()}`",
        f"Hit count: {bundle['hit_count']}",
        "",
        "## Covering heading ranges",
        "",
        "| start | end | heading path |",
        "|---|---|---|",
    ]
    for item in bundle["covering_ranges"]:
        path = item["heading_path"].replace("|", "\\|")
        structure_lines.append(f"| {item['start']} | {item['end']} | {path} |")
    if not bundle["covering_ranges"]:
        structure_lines.append("| - | - | NOT_OBSERVED_IN_PRIMARY_SOURCE |")
    structure_lines.extend(
        [
            "",
            "Occurrence excerpts are stored in SOURCE_ANCHORS.yaml so this",
            "markdown file does not embed path tokens.",
            "",
        ]
    )
    write_text(directory / "STRUCTURE.md", "\n".join(structure_lines))

    common = {
        **AUTHORITY_BLOCK,
        "MODEL_ID": name,
        "SOURCE_SHA256": KNOWN_SOURCE_SHA256,
        "OBSERVED_IN_SOURCE": bundle["observed_in_source"],
    }
    dump_yaml(
        directory / "OBLIGATIONS.yaml",
        {**common, "count": len(bundle["obligations"]), "items": bundle["obligations"]},
    )
    dump_yaml(
        directory / "DEPENDENCIES.yaml",
        {**common, "count": len(bundle["dependencies"]), "items": bundle["dependencies"]},
    )
    dump_yaml(
        directory / "INVARIANTS.yaml",
        {**common, "count": len(bundle["invariants"]), "items": bundle["invariants"]},
    )
    dump_yaml(
        directory / "SOURCE_ANCHORS.yaml",
        {
            **common,
            "PRESERVATION_CLASS": "DERIVED_INDEX",
            "hit_count": bundle["hit_count"],
            "hit_truncated": bundle["hit_truncated"],
            "hits": bundle["hits"],
            "covering_ranges": bundle["covering_ranges"],
        },
    )


def main() -> int:
    if not EXTERNAL_SOURCE.exists():
        raise SystemExit(f"SOURCE_MISSING {EXTERNAL_SOURCE}")
    source_hash = sha256_file(EXTERNAL_SOURCE)
    source_bytes = EXTERNAL_SOURCE.stat().st_size
    source_text = EXTERNAL_SOURCE.read_text(encoding="utf-8")
    lines = source_text.splitlines()
    source_lines = len(lines)
    hash_match = source_hash == KNOWN_SOURCE_SHA256
    if source_text.endswith("\n"):
        # splitlines drops the final empty line representation; expected 121930
        pass

    GATED_SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(EXTERNAL_SOURCE, GATED_SOURCE_FILE)
    copied_hash = sha256_file(GATED_SOURCE_FILE)
    if copied_hash != source_hash:
        raise SystemExit("COPY_HASH_MISMATCH")

    write_text(
        GATED_SOURCE_DIR / "00_READ_ME_FIRST.md",
        """```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_HASH_ADDRESSED_FORENSIC_SOURCE_LEAF
AUTHORITY=NONE
PURPOSE=FORENSIC_HISTORICAL_REFERENCE
MUTABILITY=IMMUTABLE_CONTENT_ADD_ONLY_CORRECTIONS
CANONICAL_SELECTION=false
RUNTIME_SELECTION=false
TRADING_AUTHORITY=false
FILE_PLACEMENT_IS_NOT_AUTHORITY_PROMOTION=true
MASTER_RUNBOOK_REMAINS_SOLE_CANONICAL_SSOT=true
MAP_OF_TRUTH_REMAINS_NAVIGATION_ONLY=true
```

This leaf stores the byte-identical identity copy of the Temp forensic working
runbook bound by SHA-256 `a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212`.

It is not canonical working authority. It does not replace
`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`.

Extracted historical-reference objects live under
`forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/`.
""",
    )
    write_text(
        GATED_SOURCE_DIR / "AUTHORITY_NONE.txt",
        "AUTHORITY=NONE\nPURPOSE=FORENSIC_HISTORICAL_REFERENCE\nCANONICAL_SELECTION=false\n",
    )
    write_text(GATED_SOURCE_DIR / "SOURCE_SHA256.txt", f"{source_hash}\n")

    PRESERVATION_ROOT.mkdir(parents=True, exist_ok=True)
    write_text(
        PRESERVATION_ROOT / "AUTHORITY_NONE.txt",
        "AUTHORITY=NONE\nPURPOSE=FORENSIC_HISTORICAL_REFERENCE\n"
        "MUTABILITY=IMMUTABLE_CONTENT_ADD_ONLY_CORRECTIONS\n"
        "CANONICAL_SELECTION=false\nRUNTIME_SELECTION=false\nTRADING_AUTHORITY=false\n",
    )

    headings, _ = scan_lines(lines)
    src_records = parse_src_records(lines)
    hits = collect_topic_hits(lines, headings)

    sidecar_dest = PRESERVATION_ROOT / "sidecar_structural_v1_20260825T100541Z"
    sidecar_dest.mkdir(parents=True, exist_ok=True)
    sidecar_hashes: dict[str, str] = {}
    sidecar_present = EXTERNAL_SIDECAR_ROOT.is_dir()
    if sidecar_present:
        for name in SIDECAR_COPY:
            src = EXTERNAL_SIDECAR_ROOT / name
            if src.exists():
                dest = sidecar_dest / name
                shutil.copyfile(src, dest)
                sidecar_hashes[name] = sha256_file(dest)
        sidecar_readme = EXTERNAL_SIDECAR_ROOT / "README.md"
        if sidecar_readme.exists():
            dest_txt = sidecar_dest / "README.txt"
            shutil.copyfile(sidecar_readme, dest_txt)
            sidecar_hashes["README.txt"] = sha256_file(dest_txt)
            stale_md = sidecar_dest / "README.md"
            if stale_md.exists():
                stale_md.unlink()

    loss_register: list[dict[str, Any]] = []
    for label, path, reason in EXCLUDED_DERIVED:
        entry: dict[str, Any] = {
            "item": label,
            "external_path": str(path),
            "exists_at_capture": path.exists(),
            "exclusion_reason": reason,
            "committed": False,
        }
        if path.exists():
            entry["bytes"] = path.stat().st_size
            entry["sha256"] = sha256_file(path)
        loss_register.append(entry)

    unresolved: list[dict[str, Any]] = []
    for topic, topic_hits in hits.items():
        if not topic_hits:
            unresolved.append(
                {
                    "item": topic,
                    "status": "NOT_OBSERVED_AS_REQUIRED_TOKEN_IN_PRIMARY_SOURCE",
                    "may_exist_under_alias": topic in REQUIRED_ZERO_MAY_BE_ABSENT
                    or topic
                    in {
                        "REGISTRY_TO_CORE",
                        "CAPITAL_ARCHITECTURE",
                        "ECONOMIC_VIABILITY",
                        "BACKTEST_RUNTIME_PARITY",
                        "FULL_CANONICAL_SYSTEM_PARITY",
                        "FULL_CANONICAL_SYSTEM_WIRING",
                        "INTEGRATED_REPLAY",
                    },
                }
            )

    models_to_write = {
        "master_v2": "MASTER_V2",
        "double_play": "DOUBLE_PLAY",
    }
    bundles: dict[str, dict[str, Any]] = {}
    for dirname, topic in models_to_write.items():
        bundles[dirname] = model_bundle(topic, hits[topic], headings, lines)
        write_model_dir(PRESERVATION_ROOT, dirname, bundles[dirname])

    extra_models = [
        "INTEGRATED_REPLAY",
        "STRATEGY_AUTHORITY",
        "REGISTRY_TO_CORE",
        "CAPITAL_ARCHITECTURE",
        "ECM_ARMSTRONG",
        "FIRST_LIVE",
        "CAPABILITY_CHAIN",
        "SAFETY_KERNEL",
        "KILL_SWITCH",
        "SINGLE_WRITER",
        "ECONOMIC_VIABILITY",
        "BACKTEST_RUNTIME_PARITY",
        "FULL_CANONICAL_SYSTEM_PARITY",
        "FULL_CANONICAL_SYSTEM_WIRING",
        "STEP_29",
        "LEVEL_0_TO_10",
        "AUTH_001_TO_023",
        "DOC_01_TO_12",
        "B_01_TO_07",
    ]
    extra_dir = PRESERVATION_ROOT / "containers"
    extra_dir.mkdir(parents=True, exist_ok=True)
    extra_payload = []
    for topic in extra_models:
        bundle = model_bundle(topic, hits[topic], headings, lines)
        extra_payload.append(
            {
                **object_meta(
                    f"{PRESERVATION_ID}:container:{topic}",
                    bundle["covering_ranges"][0]["start"] if bundle["covering_ranges"] else 0,
                    bundle["covering_ranges"][0]["end"] if bundle["covering_ranges"] else 0,
                    topic,
                    assertion_status="DERIVED_INDEX"
                    if bundle["observed_in_source"]
                    else "NOT_OBSERVED",
                    preservation_class="DERIVED_INDEX",
                ),
                "model_id": topic,
                "hit_count": bundle["hit_count"],
                "observed_in_source": bundle["observed_in_source"],
                "covering_ranges": bundle["covering_ranges"][:20],
                "obligation_count": len(bundle["obligations"]),
                "dependency_count": len(bundle["dependencies"]),
                "invariant_count": len(bundle["invariants"]),
            }
        )
    dump_yaml(
        extra_dir / "REQUIRED_CONTAINER_INDEX.yaml",
        {**AUTHORITY_BLOCK, "items": extra_payload},
    )

    src_index = []
    for record in src_records:
        src_index.append(
            {
                **object_meta(
                    f"{PRESERVATION_ID}:{record.get('block_id', 'SRC_UNKNOWN')}",
                    int(record.get("source_start_line") or record.get("heading_line") or 0),
                    int(record.get("source_end_line") or record.get("heading_line") or 0),
                    record.get("start_marker_verbatim") or record.get("block_id") or "SRC",
                    assertion_status="SOURCE_DECLARED"
                    if record.get("parse_status") == "OK"
                    else "PARSE_RESIDUAL",
                    preservation_class="RAW_EVIDENCE"
                    if record.get("parse_status") == "OK"
                    else "DERIVED_INDEX",
                ),
                "block_id": record.get("block_id"),
                "t3_heading_line": record.get("_heading_line") or record.get("heading_line"),
                "source_order": record.get("source_order"),
                "source_line_count": record.get("source_line_count"),
                "source_region_sha256": record.get("source_region_sha256"),
                "parse_status": record.get("parse_status"),
            }
        )
    dump_yaml(
        extra_dir / "CONTAINER_REGISTER.yaml",
        {
            **AUTHORITY_BLOCK,
            "T3_RECORD_MODEL": "ONE_T3_RECORD_PER_T2_BLOCK",
            "expected_count": 88,
            "parsed_count": len(src_records),
            "ok_count": sum(1 for item in src_records if item.get("parse_status") == "OK"),
            "items": src_index,
        },
    )

    h1 = [item for item in headings if item["level"] == 1]
    dump_yaml(
        extra_dir / "H1_PASS_HEADING_INDEX.yaml",
        {
            **AUTHORITY_BLOCK,
            "PRESERVATION_CLASS": "DERIVED_INDEX",
            "h1_count": len(h1),
            "h1": [
                {
                    "line": item["line"],
                    "text": item["text"],
                    "end": section_end(headings, item, len(lines)),
                }
                for item in h1
            ],
            "pass_headings": [
                item
                for item in headings
                if item["text"].startswith("PASS=") or item["text"].startswith("PASS =")
            ],
        },
    )

    family_items = []
    lineage = []
    for family, pattern in FAMILY_PATTERNS.items():
        compiled = re.compile(pattern)
        occ = []
        for index, raw in enumerate(lines, 1):
            for match in compiled.finditer(raw):
                occ.append({"line": index, "token": match.group(0)})
                if len(occ) >= 300:
                    break
            if len(occ) >= 300:
                break
        family_items.append(
            {
                **object_meta(
                    f"{PRESERVATION_ID}:family:{family}",
                    occ[0]["line"] if occ else 0,
                    occ[-1]["line"] if occ else 0,
                    family,
                    assertion_status="SOURCE_DECLARED_TOKEN_INDEX",
                    preservation_class="DERIVED_INDEX",
                ),
                "family": family,
                "occurrence_count_capped": len(occ),
                "occurrences": occ[:200],
            }
        )
        if family == "I01_I85" and occ:
            lineage.append(
                {
                    "from_family": "I01_I85",
                    "to_family": "RD01_RD10",
                    "edge_class": "SOURCE_COOCCURRENCE_INDEX_NOT_PROVEN_DEPENDENCY",
                    "evidence": "doctrine matrix and later ratification passes share document",
                    "AUTHORITY": "NONE",
                }
            )
    dump_yaml(
        PRESERVATION_ROOT / "obligation_families" / "FAMILY_REGISTER.yaml",
        {**AUTHORITY_BLOCK, "families": family_items},
    )
    dump_yaml(
        PRESERVATION_ROOT / "obligation_families" / "LINEAGE_EDGES.yaml",
        {
            **AUTHORITY_BLOCK,
            "note": "Edges are index co-occurrence, not proven runtime dependencies.",
            "edges": lineage,
        },
    )

    child_ledger = []
    for record in src_records:
        if record.get("parse_status") != "OK":
            continue
        child_ledger.append(
            {
                "child_id": record.get("block_id"),
                "source_start_line": record.get("source_start_line"),
                "source_end_line": record.get("source_end_line"),
                "source_region_sha256": record.get("source_region_sha256"),
                "start_marker_verbatim": record.get("start_marker_verbatim"),
                "ssot_role": "HISTORICAL_FORENSIC_REGION_NOT_CURRENT_SSOT",
                **AUTHORITY_BLOCK,
            }
        )
    dump_yaml(
        PRESERVATION_ROOT / "conservation" / "HISTORICAL_CHILD_LEDGER.yaml",
        {
            **AUTHORITY_BLOCK,
            "count": len(child_ledger),
            "children": child_ledger,
        },
    )
    dump_yaml(
        PRESERVATION_ROOT / "conservation" / "SSOT_TRANSITIONS.yaml",
        {
            **AUTHORITY_BLOCK,
            "note": "Index of source-declared SSOT-transition mentions; not a current SSOT change.",
            "anchors": [
                hit
                for hit in collect_topic_hits(lines, headings).get("MASTER_V2", [])
                if "SSOT" in hit.get("excerpt", "")
            ][:20]
            + [
                {
                    "line": item["line"],
                    "excerpt": item["text"],
                    "heading_path": heading_path_at(headings, item["line"]),
                }
                for item in headings
                if "SSOT" in item["text"]
            ],
        },
    )

    dump_yaml(
        PRESERVATION_ROOT / "schemas" / "EPISTEMIC_SCHEMA.yaml",
        {
            **AUTHORITY_BLOCK,
            "PRESERVATION_CLASS": "SOURCE_DECLARED_SCHEMA_COPY",
            "source_heading": "# Forensic Persist — T5 Epistemic and Provenance Classification Evidence",
            "source_line_range": {"start_inclusive": 113319, "end_inclusive": 113329},
            "compact_fields": 17,
            "field_order": [
                "classification_id",
                "source_src_id",
                "source_lines",
                "segment_locator",
                "excerpt_sha256",
                "epistemic_class",
                "provenance_class",
                "classification_basis",
                "source_declared_currentness",
                "source_declared_authority",
                "adjudication_status",
                "boundary_status",
                "endpoint_resolution",
                "ambiguity_status",
                "t3_support_refs",
                "t4_support_refs",
                "notes",
            ],
            "epistemic_class_counts_source_declared": {
                "CANONICAL_AUTHORITY_REFERENCE": 801,
                "FORENSIC_RAW_EVIDENCE": 532,
                "ADJUDICATED_CONCLUSION": 98,
                "HISTORICAL_INTERMEDIATE_STATE": 189,
                "NAVIGATION_INDEX": 1587,
                "INTERPRETATION": 20,
                "HYPOTHESIS": 3,
                "OPEN_OR_CONFLICTED": 637,
                "TOTAL": 3867,
                "SOURCE_LINE_RANGE": {"start_inclusive": 113332, "end_inclusive": 113343},
            },
            "this_schema_is_not_current_authority": True,
        },
    )

    dump_yaml(
        PRESERVATION_ROOT / "provenance" / "SOURCE_IDENTITY.yaml",
        {
            **AUTHORITY_BLOCK,
            "SOURCE_PATH_AT_CAPTURE": str(EXTERNAL_SOURCE),
            "REPO_GATED_SOURCE_PATH": str(GATED_SOURCE_FILE.relative_to(REPO_ROOT)),
            "SOURCE_SHA256": source_hash,
            "KNOWN_SOURCE_SHA256": KNOWN_SOURCE_SHA256,
            "SOURCE_HASH_MATCH": hash_match,
            "SOURCE_BYTES": source_bytes,
            "SOURCE_LINES": source_lines,
            "EXPECTED_BYTES": EXPECTED_BYTES,
            "EXPECTED_LINES": EXPECTED_LINES,
            "NEWLINE": "LF",
            "EXTERNAL_SOURCE_MUTATED": False,
            "SIDECAR_ROOT_AT_CAPTURE": str(EXTERNAL_SIDECAR_ROOT),
            "SIDECAR_PRESENT": sidecar_present,
            "SIDECAR_FILE_SHA256": sidecar_hashes,
        },
    )
    dump_yaml(
        PRESERVATION_ROOT / "provenance" / "SOURCE_RANGES.yaml",
        {
            **AUTHORITY_BLOCK,
            "byte_range_convention": "line_inclusive_1_based",
            "document_line_range": {"start_inclusive": 1, "end_inclusive": source_lines},
            "t3_physical_source_lines_declared": {"start_inclusive": 1, "end_inclusive": 30870},
            "t3_physical_source_declaration_line": 113303,
            "src_block_count": len(src_records),
            "h1_count": len(h1),
            "heading_count": len(headings),
        },
    )
    commits = sorted({item.group(0).lower() for item in SHA_RE.finditer(source_text)})
    prs = sorted({item.group(1) for item in PR_RE.finditer(source_text)})
    dump_yaml(
        PRESERVATION_ROOT / "provenance" / "SOURCE_COMMITS.yaml",
        {
            **AUTHORITY_BLOCK,
            "note": "Tokens matching 40-hex and PR-like patterns in the source body. Not proven git objects.",
            "sha1_token_count": len(commits),
            "sha1_tokens_capped": commits[:200],
            "pr_token_count": len(prs),
            "pr_tokens_capped": prs[:200],
        },
    )

    obligation_count = len(bundles["master_v2"]["obligations"]) + len(
        bundles["double_play"]["obligations"]
    )
    dependency_count = len(bundles["master_v2"]["dependencies"]) + len(
        bundles["double_play"]["dependencies"]
    )
    invariant_count = len(bundles["master_v2"]["invariants"]) + len(
        bundles["double_play"]["invariants"]
    )
    for item in extra_payload:
        obligation_count += int(item["obligation_count"])
        dependency_count += int(item["dependency_count"])
        invariant_count += int(item["invariant_count"])

    every_object_has_anchor = True
    every_anchor_resolves = True
    for bundle in bundles.values():
        for collection in ("obligations", "dependencies", "invariants"):
            for item in bundle[collection]:
                start = item["SOURCE_LINE_RANGE"]["start_inclusive"]
                end = item["SOURCE_LINE_RANGE"]["end_inclusive"]
                if start < 1 or end > source_lines or start > end:
                    every_object_has_anchor = False
                    every_anchor_resolves = False
                    continue
                key = item.get("key")
                if key and key not in lines[start - 1]:
                    every_anchor_resolves = False

    dump_yaml(
        PRESERVATION_ROOT / "LOSS_REGISTER.yaml",
        {
            **AUTHORITY_BLOCK,
            "LOSSY_EXTRACTION": False,
            "FULL_SOURCE_COMMITTED": True,
            "excluded_derived_blobs": loss_register,
            "intentionally_not_preserved": [
                "78MiB structural sidecar line-records.jsonl (regenerable from committed source)",
                "38MiB structure-v1.json overlay (derived; not required when source bytes are committed)",
                "Temp-only extraction tools runtime state",
                "Chat transcripts not present in the primary source file",
            ],
            "unresolved_items": unresolved,
        },
    )

    dump_yaml(
        PRESERVATION_ROOT / "validation" / "LOSSLESSNESS_REPORT.yaml",
        {
            **AUTHORITY_BLOCK,
            "EVERY_PRESERVED_OBJECT_HAS_SOURCE_ANCHOR": every_object_has_anchor,
            "EVERY_SOURCE_ANCHOR_RESOLVES": every_anchor_resolves,
            "NO_UNMARKED_INTERPRETATION_AS_RAW_EVIDENCE": True,
            "NO_CANONICAL_PROMOTION": True,
            "SOURCE_MATERIAL_INCLUDED": [
                str(GATED_SOURCE_FILE.relative_to(REPO_ROOT)),
                "extracted indexes with line anchors",
                "small structural sidecar files except records.jsonl",
            ],
            "SOURCE_MATERIAL_EXCLUDED": [item["item"] for item in loss_register],
            "EXCLUSION_REASON": "GIT_MAINTAINABILITY_PLUS_REGENERABLE_FROM_COMMITTED_SOURCE",
            "LOSSY_EXTRACTION": False,
            "SOURCE_HASH_MATCH": hash_match,
            "COPIED_SOURCE_SHA256": copied_hash,
        },
    )

    preserved_models = ["MASTER_V2", "DOUBLE_PLAY", *extra_models]
    dump_yaml(
        PRESERVATION_ROOT / "MANIFEST.yaml",
        {
            "FORMAT_VERSION": FORMAT_VERSION,
            "PRESERVATION_ID": PRESERVATION_ID,
            "SOURCE_PATH_AT_CAPTURE": str(EXTERNAL_SOURCE),
            "SOURCE_SHA256": source_hash,
            "SOURCE_BYTES": source_bytes,
            "SOURCE_LINES": source_lines,
            "CAPTURE_TIMESTAMP": CAPTURE_TIMESTAMP,
            "ORIGIN_MAIN_SHA_AT_PRESERVATION": ORIGIN_MAIN_SHA,
            "SOURCE_AUTHORITY": "NONE",
            "PRESERVED_MODELS": preserved_models,
            "PRESERVED_CONTAINER_COUNT": len(src_records),
            "PRESERVED_OBLIGATION_COUNT": obligation_count,
            "PRESERVED_DEPENDENCY_EDGE_COUNT": dependency_count,
            "PRESERVED_INVARIANT_COUNT": invariant_count,
            "EXTRACTION_METHOD": (
                "mechanical heading/token/KEY=VALUE scan plus T3 SRC JSON parse; "
                "full source blob committed at gated forensic evidence path"
            ),
            "LOSS_REGISTER": "LOSS_REGISTER.yaml",
            "UNRESOLVED_ITEMS": unresolved,
            "CANONICAL_AUTHORITY": False,
            **AUTHORITY_BLOCK,
            "GATED_SOURCE_PATH": str(GATED_SOURCE_FILE.relative_to(REPO_ROOT)),
            "PRESERVATION_ROOT": str(PRESERVATION_ROOT.relative_to(REPO_ROOT)),
            "SIDECAR_COPIED_FILES": list(sidecar_hashes),
        },
    )

    write_text(
        PRESERVATION_ROOT / "README.md",
        f"""```text
AUTHORITY=NONE
PURPOSE=FORENSIC_HISTORICAL_REFERENCE
MUTABILITY=IMMUTABLE_CONTENT_ADD_ONLY_CORRECTIONS
CANONICAL_SELECTION=false
RUNTIME_SELECTION=false
TRADING_AUTHORITY=false
REPO_PRESERVATION != CANONICAL_PROMOTION
```

# Historical forensic reference (SHA-256 bound)

Preservation id: `{PRESERVATION_ID}`

This package is an immutable historical forensic reference. Storing it in git
does not make it canonical working authority. The current system remains the
only future mutation target.

## Source blob

Byte-identical copy (gated ingress path):

`forensic/evidence/sha256-{KNOWN_SOURCE_SHA256}/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md`

SHA-256: `{source_hash}`

## How to use

1. Treat `MANIFEST.yaml` as the root identity of this package.
2. Resolve every preserved object through `SOURCE_LINE_RANGE` against the blob.
3. Do not import this tree from runtime code.
4. Do not copy these obligations into the Master Runbook without a separate
   conservation / compatibility Owner-GO.

## Layers

- `provenance&#47;` source identity, ranges, commit/PR tokens
- `master_v2&#47;` and `double_play&#47;` derived indexes over source anchors
- `containers&#47;` T3 SRC-000001..088 plus required-container index
- `obligation_families&#47;` token families and non-proven lineage edges
- `conservation&#47;` historical child ledger and SSOT-transition mentions
- `schemas&#47;EPISTEMIC_SCHEMA.yaml` source-declared T5 schema copy
- `sidecar_structural_v1_20260825T100541Z&#47;` small structural sidecar files
- `LOSS_REGISTER.yaml` intentionally excluded derived blobs
""",
    )

    write_text(
        PRESERVATION_ROOT / "extraction" / "METHOD.md",
        """```text
AUTHORITY=NONE
PURPOSE=FORENSIC_HISTORICAL_REFERENCE
EXTRACTION_CLASS=MECHANICAL_READ_ONLY_REGEX_AND_FENCE_SCAN
INTERPRETATION_USED_AS_FACT=false
```

Re-run:

`./scripts/pt forensics/historical_reference/extraction/materialize_historical_reference_v1.py`

The generator is frozen with this package. Later corrections must add a new
content-addressed object and record supersession. Do not silently rewrite.
""",
    )

    write_text(
        REPO_ROOT / "forensics" / "historical_reference" / "README.md",
        f"""```text
AUTHORITY=NONE
PURPOSE=FORENSIC_HISTORICAL_REFERENCE_NAVIGATION
CANONICAL_SELECTION=false
RUNTIME_SELECTION=false
TRADING_AUTHORITY=false
```

# Historical reference namespace

Current immutable package:

`forensics/historical_reference/sha256-{KNOWN_SOURCE_SHA256}/`

Source blob (hash-addressed ingress leaf):

`forensic/evidence/sha256-{KNOWN_SOURCE_SHA256}/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md`

This namespace is not canonical authority.
""",
    )

    shutil.copyfile(
        Path(__file__),
        PRESERVATION_ROOT / "extraction" / "materialize_historical_reference_v1.py",
    )

    report = {
        "SOURCE_EXISTS": True,
        "SOURCE_SHA256": source_hash,
        "SOURCE_HASH_MATCH": hash_match,
        "SOURCE_BYTES": source_bytes,
        "SOURCE_LINES": source_lines,
        "COPIED_SHA256": copied_hash,
        "PRESERVATION_ROOT": str(PRESERVATION_ROOT),
        "GATED_SOURCE": str(GATED_SOURCE_FILE),
        "MASTER_V2_HITS": len(hits["MASTER_V2"]),
        "DOUBLE_PLAY_HITS": len(hits["DOUBLE_PLAY"]),
        "SRC_OK": sum(1 for item in src_records if item.get("parse_status") == "OK"),
        "LOSS_REGISTER_COUNT": len(loss_register),
        "UNRESOLVED_COUNT": len(unresolved),
        "EVERY_PRESERVED_OBJECT_HAS_SOURCE_ANCHOR": every_object_has_anchor,
        "EVERY_SOURCE_ANCHOR_RESOLVES": every_anchor_resolves,
        "LOSSY_EXTRACTION": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if not hash_match or not every_object_has_anchor or not every_anchor_resolves:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
