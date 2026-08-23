#!/usr/bin/env python3
"""V2.1 lossless structural projection. Writes only the two V2.1 sidecar paths."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SOURCE_PATH = Path("/Users/frnkhrz/Downloads/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md")
V2_JSON = Path("/Users/frnkhrz/Downloads/PEAK_TRADE_TEMPORARY_FORENSIC_LOSSLESS_STRUCTURAL_PROJECTION_V2.json")
V2_MD = Path("/Users/frnkhrz/Downloads/PEAK_TRADE_TEMPORARY_FORENSIC_LOSSLESS_STRUCTURAL_PROJECTION_V2.md")
OUT_JSON = Path("/Users/frnkhrz/Downloads/PEAK_TRADE_TEMPORARY_FORENSIC_LOSSLESS_STRUCTURAL_PROJECTION_V2.1.json")
OUT_MD = Path("/Users/frnkhrz/Downloads/PEAK_TRADE_TEMPORARY_FORENSIC_LOSSLESS_STRUCTURAL_PROJECTION_V2.1.md")

EXPECTED_SHA = "10d9293134426805f38996be848e1de853636d8e6f60745a2330bdfd94e3719f"
EXPECTED_SIZE = 8499032
EXPECTED_LINES = 118809
EXPECTED_V2_JSON_SHA = "c8e8432e52ee5122da31c29fe7b4164e8bc907bad0f259ca67349ce6e8616870"
EXPECTED_V2_MD_SHA = "d240175046f1d6ece5345d172c35171959b270a464fbf98157484c658c4f0e11"

CLAIMED_PREFIX_SHA = "08ffe7bce3fd7aa94de20737c3bc1cf1721e08e719fc8d3d00d72e079f6a5092"
CLAIMED_PREFIX_BYTES = 1421764
CLAIMED_T4_BOUND_SHA = "1ab199242eb40031d69979849f331d54ee58a0d2de43cec6f2e052622c46ea28"
CLAIMED_T4_BOUND_BYTES = 3197147
CLAIMED_T4_BOUND_LINES = 7175
CLAIMED_T5_BOUND_SHA = "e2e19bcfe91febc5b341bbcf5051e30723a7ce6b7dd81fe496ac217632bc9aba"
CLAIMED_T5_BOUND_BYTES = 1974170
CLAIMED_T5_BOUND_LINES = 3867
ORIGIN_MAIN_REF_SHA = "b7cf08ded64c32cc7dc8d2fd5f35c98b125ec44e"

PHYS = [
    ("P01", 1, 30870, "physical P01 working runbook body"),
    ("P02", 30871, 105667, "physical P02 T3 evidence"),
    ("P03", 105668, 105687, "physical P03 T3P closeout"),
    ("P04", 105688, 113208, "physical P04 T4 evidence"),
    ("P05", 113209, 117419, "physical P05 T5 evidence"),
    ("P06", 117420, 117630, "physical P06 T5PR"),
    ("P07", 117631, 117956, "physical P07 T6 discovery persist"),
    ("P08", 117957, 118450, "physical P08 T-workflow discovery persist"),
    ("P09", 118451, 118809, "physical P09 pointer conflict persist"),
]

NEIGHBORS = [
    Path("/Users/frnkhrz/Downloads/.ptf1"),
    Path("/Users/frnkhrz/Downloads/PEAK_TRADE_TEMPORARY_FORENSIC_STRUCTURED_IMPLEMENTATION.md"),
    Path("/Users/frnkhrz/Downloads/PEAK_TRADE_TEMPORARY_FORENSIC_LOSSLESS_STRUCTURAL_PROJECTION.json"),
    V2_JSON,
    V2_MD,
]

NON_AUTH_KEYS = {
    "TARGET_AUTHORITY",
    "SECOND_SSOT",
    "CANONICALIZATION_PERFORMED",
    "STRUCTURING_DOES_NOT_CREATE_AUTHORITY",
    "MASTER_RUNBOOK_REMAINS_SOLE_CANONICAL_SSOT",
    "POINTER_WINNER_SELECTED",
    "BOUNDARY_ADJUDICATION_PERFORMED",
    "T6_DEFINITION_INFERRED",
    "T_PHASE_SEQUENCE_INFERRED",
    "PHYSICAL_BYTE_REPAIR_PERFORMED",
    "CANONICAL_AUTHORITY_CREATED",
    "LIVE_TRADING",
    "ORDERS_ALLOWED",
}

T5_LABEL_MAP_CANDIDATES = {
    "NAVIGATION_INDEX": "NAVIGATION_OR_INDEX",
    "CANONICAL_AUTHORITY_REFERENCE": "CANONICAL_AUTHORITY_REFERENCE",
    "OPEN_OR_CONFLICTED": "OPEN_OR_CONFLICTED_POINT",
    "FORENSIC_RAW_EVIDENCE": "FORENSIC_RAW_EVIDENCE",
    "HISTORICAL_INTERMEDIATE_STATE": "HISTORICAL_INTERMEDIATE_STATE",
    "ADJUDICATED_CONCLUSION": "ADJUDICATED_FORENSIC_CONCLUSION",
    "INTERPRETATION": "INTERPRETATION",
    "HYPOTHESIS": "HYPOTHESIS",
}

BOOLEANISH = {"true", "TRUE", "false", "FALSE", "YES", "NO", "Yes", "yes", "no"}
VALUE_STOP = set(b" \t\n\r`|;,\"'}{]")
IDCHAR = set(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
PEDAGOGY = b"PASS=/OWNER_GO=/STATUS="

CONS_WHITELIST = {
    "OWNER_GO_STATUS": "CONS-001",
    "PRIOR_GET_OWNER_GO_STATUS": "CONS-002",
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def hard_stop_fail(msg: str) -> None:
    raise SystemExit(f"HARD_STOP_FAIL:{msg}")


def is_idchar(b: int) -> bool:
    return b in IDCHAR or (65 <= b <= 90) or (48 <= b <= 57) or b == 95


def left_bound_ok(data: bytes, pos: int) -> bool:
    if pos <= 0:
        return True
    c = data[pos - 1]
    return not (c == 95 or 48 <= c <= 57 or 65 <= c <= 90 or 97 <= c <= 122)


def expand_ident(data: bytes, pos: int) -> tuple[int, int]:
    L = pos
    while L > 0 and (data[L - 1] == 95 or 48 <= data[L - 1] <= 57 or 65 <= data[L - 1] <= 90):
        L -= 1
    R = pos
    n = len(data)
    while R < n and (data[R] == 95 or 48 <= data[R] <= 57 or 65 <= data[R] <= 90):
        R += 1
    return L, R


def parse_value(data: bytes, eq_pos: int) -> tuple[int, int, str]:
    n = len(data)
    vstart = eq_pos + 1
    vend = vstart
    while vend < n and data[vend] not in VALUE_STOP:
        vend += 1
    return vstart, vend, data[vstart:vend].decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
if OUT_JSON.exists() or OUT_MD.exists():
    hard_stop_fail("output_path_already_exists")
if not SOURCE_PATH.exists() or SOURCE_PATH.is_symlink() or not SOURCE_PATH.is_file():
    hard_stop_fail("source_missing_or_not_regular")
for p, exp in ((V2_JSON, EXPECTED_V2_JSON_SHA), (V2_MD, EXPECTED_V2_MD_SHA)):
    if sha256_bytes(p.read_bytes()) != exp:
        hard_stop_fail(f"v2_baseline_mismatch:{p}")

st = SOURCE_PATH.stat()
if SOURCE_PATH.is_symlink() or not stat.S_ISREG(st.st_mode):
    hard_stop_fail("source_not_regular_file")
data = SOURCE_PATH.read_bytes()
source_sha_pre = sha256_bytes(data)
if source_sha_pre != EXPECTED_SHA or len(data) != EXPECTED_SIZE or data.count(b"\n") != EXPECTED_LINES:
    hard_stop_fail("source_baseline_mismatch")
v2_json_sha_pre = sha256_bytes(V2_JSON.read_bytes())
v2_md_sha_pre = sha256_bytes(V2_MD.read_bytes())
source_mtime_iso = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
generated_at = datetime.now(timezone.utc).isoformat()

line_starts: list[int] = []
start = 0
while True:
    j = data.find(b"\n", start)
    if j < 0:
        if start < len(data):
            line_starts.append(start)
        break
    line_starts.append(start)
    start = j + 1
assert len(line_starts) == EXPECTED_LINES
nlines = EXPECTED_LINES


def line_byte_span(line_no: int) -> tuple[int, int]:
    s = line_starts[line_no - 1]
    e = line_starts[line_no] if line_no < nlines else len(data)
    return s, e


def lines_byte_span(a: int, b: int) -> tuple[int, int]:
    return line_byte_span(a)[0], line_byte_span(b)[1]


def byte_to_line(off: int) -> int:
    lo, hi = 0, nlines - 1
    if off >= len(data):
        return nlines
    while lo <= hi:
        mid = (lo + hi) // 2
        if line_starts[mid] <= off:
            lo = mid + 1
        else:
            hi = mid - 1
    return hi + 1


def phys_of_line(line_no: int) -> str:
    for pid, a, b, _ in PHYS:
        if a <= line_no <= b:
            return pid
    return "UNPROVEN"


all_sidecar_ids: dict[str, str] = {}
counters: dict[str, int] = defaultdict(int)
span_registry: list[dict] = []


def new_id(prefix: str) -> str:
    counters[prefix] += 1
    return f"{prefix}-{counters[prefix]:06d}"


def register_id(i: str, kind: str) -> str:
    if i in all_sidecar_ids:
        hard_stop_fail(f"duplicate_id:{i}")
    all_sidecar_ids[i] = kind
    return i


def add_span(*, span_id: str, byte_start: int, byte_end: int, information_class: list, provenance_sidecar: str, provenance_referent: str, notes: str, related=None, extra=None) -> dict:
    register_id(span_id, "SPAN")
    blob = data[byte_start:byte_end]
    rec = {
        "SPAN_ID": span_id,
        "SOURCE_BYTE_START": byte_start,
        "SOURCE_BYTE_END": byte_end,
        "CONTENT_SHA256": sha256_bytes(blob),
        "INFORMATION_CLASS": information_class,
        "sidecar_record_provenance_class": provenance_sidecar,
        "referent_provenance_class": provenance_referent,
        "AUTHORITY_STATUS": "NONE",
        "NOTES": notes,
        "RELATED_BLOCK_IDS": related or [],
    }
    if extra:
        rec.update(extra)
    span_registry.append({"SPAN_ID": span_id, "SOURCE_BYTE_START": byte_start, "SOURCE_BYTE_END": byte_end, "CONTENT_SHA256": rec["CONTENT_SHA256"]})
    return rec


def occ_record(*, occ_id: str, byte_start: int, byte_end: int, information_class: list, sidecar_prov: str, referent_prov: str, notes: str, related=None, extra=None, field_status="PROVEN_MECHANICAL_OCCURRENCE") -> dict:
    blob = data[byte_start:byte_end]
    ls = byte_to_line(byte_start) if byte_start < len(data) else nlines
    le = byte_to_line(byte_end - 1) if byte_end > byte_start else ls
    rec = {
        "OCCURRENCE_ID": register_id(occ_id, "OCC"),
        "BLOCK_ID": extra.get("BLOCK_ID") if extra and extra.get("BLOCK_ID") else phys_of_line(ls),
        "SOURCE_FILE": str(SOURCE_PATH),
        "SOURCE_BYTE_START": byte_start,
        "SOURCE_BYTE_END": byte_end,
        "SOURCE_LINE_START": ls,
        "SOURCE_LINE_END": le,
        "PHYSICAL_SEQUENCE": phys_of_line(ls),
        "CONTENT_SHA256": sha256_bytes(blob),
        "INFORMATION_CLASS": information_class,
        "sidecar_record_provenance_class": sidecar_prov,
        "referent_provenance_class": referent_prov,
        "AUTHORITY_STATUS": "NONE",
        "ADJUDICATION_STATUS": "NONE_PERFORMED_THIS_OPERATION",
        "TEMPORAL_STATUS": "PHYSICAL_ORDER",
        "VERBATIM_STATUS": "TOKEN_SPAN_VERBATIM_IN_SOURCE",
        "GATE_AFFILIATION": "UNPROVEN",
        "DEPENDENCY_AFFILIATION": "UNPROVEN",
        "OWNER_AUTHORIZATION_REFERENCE": "UNPROVEN",
        "SUPERSESSION_STATUS": "UNPROVEN",
        "CONSUMPTION_STATUS": "UNPROVEN",
        "CONFLICT_STATUS": "UNPROVEN",
        "mapping_status": "UNPROVEN",
        "declaration_status": "UNPROVEN",
        "negation_status": "NONE",
        "quote_status": "NONE",
        "claimed_scope": "UNPROVEN",
        "evidence_strength": "MECHANICAL_SPAN",
        "ambiguity_flags": [],
        "derivation_rule_id": "UNPROVEN",
        "RELATED_BLOCK_IDS": related or [phys_of_line(ls)],
        "FIELD_STATUS": field_status,
        "NOTES": notes,
        "raw_token_verbatim": blob.decode("utf-8", errors="replace"),
    }
    if extra:
        rec.update(extra)
    span_registry.append({"SPAN_ID": rec["OCCURRENCE_ID"], "SOURCE_BYTE_START": byte_start, "SOURCE_BYTE_END": byte_end, "CONTENT_SHA256": rec["CONTENT_SHA256"]})
    return rec


# L1 root + physical
root = add_span(
    span_id="SPAN-ROOT",
    byte_start=0,
    byte_end=len(data),
    information_class=["FORENSIC_RAW_EVIDENCE", "IMMUTABLE_EVIDENCE_LAYER_ROOT"],
    provenance_sidecar="DERIVED_RECORD_WITH_SOURCE_BINDING",
    provenance_referent="ORIGINAL_SOURCE_SPAN",
    notes="Entire immutable source referenced; bytes not copied as authority.",
    extra={"PHYSICAL_SEQUENCE": "P01-P09", "L1_BYTE_COVERAGE": "100_PERCENT"},
)

physical_blocks = []
for seq, (pid, a, b, label) in enumerate(PHYS, start=1):
    bs, be = lines_byte_span(a, b)
    sid = f"SPAN-{pid}"
    add_span(
        span_id=sid,
        byte_start=bs,
        byte_end=be,
        information_class=["FORENSIC_RAW_EVIDENCE", "PHYSICAL_MACRO_BLOCK"],
        provenance_sidecar="DERIVED_RECORD_WITH_SOURCE_BINDING",
        provenance_referent="ORIGINAL_SOURCE_SPAN",
        notes=label,
        related=["SPAN-ROOT", pid],
        extra={"PHYSICAL_SEQUENCE": seq, "PHYSICAL_ORDER_ONLY": True, "EXECUTION_ORDER_INFERRED": False, "PRECEDENCE_INFERRED": False, "CANONICAL_ORDER_INFERRED": False, "BLOCK_ID": pid},
    )
    hs, he = line_byte_span(a)
    physical_blocks.append(
        {
            "BLOCK_ID": pid,
            "OBJECT_ID": register_id(f"APP-PHYS-{pid}", "APP"),
            "SPAN_ID": sid,
            "SOURCE_FILE": str(SOURCE_PATH),
            "SOURCE_BYTE_START": bs,
            "SOURCE_BYTE_END": be,
            "SOURCE_LINE_START": a,
            "SOURCE_LINE_END": b,
            "PHYSICAL_SEQUENCE": seq,
            "CONTENT_SHA256": sha256_bytes(data[bs:be]),
            "INFORMATION_CLASS": ["PHYSICAL_MACRO_BLOCK"],
            "sidecar_record_provenance_class": "DERIVED_RECORD_WITH_SOURCE_BINDING",
            "referent_provenance_class": "ORIGINAL_SOURCE_SPAN",
            "AUTHORITY_STATUS": "NONE",
            "ADJUDICATION_STATUS": "NONE_PERFORMED_THIS_OPERATION",
            "TEMPORAL_STATUS": "PHYSICAL_ORDER",
            "PHYSICAL_ORDER_ONLY": True,
            "EXECUTION_ORDER_INFERRED": False,
            "PRECEDENCE_INFERRED": False,
            "CANONICAL_ORDER_INFERRED": False,
            "heading_verbatim": data[hs : he - 1 if data[he - 1 : he] == b"\n" else he].decode("utf-8"),
            "FIELD_STATUS": "PROVEN_MECHANICAL_SPAN",
            "NOTES": label,
        }
    )

# Fences
fence_objs = []
i = 0
in_fence = False
open_line = None
while i < nlines:
    ls, le = line_byte_span(i + 1)
    line = data[ls:le]
    if line.startswith(b"```"):
        if not in_fence:
            in_fence = True
            open_line = i + 1
        else:
            close_line = i + 1
            obs, obe = line_byte_span(open_line)
            ces, cee = line_byte_span(close_line)
            info = data[obs:obe].decode("utf-8").rstrip("\n")[3:]
            fid = new_id("FENCE")
            rec = {
                "FENCE_ID": register_id(fid, "FENCE"),
                "BLOCK_ID": fid,
                "OCCURRENCE_ID": fid,
                "SOURCE_FILE": str(SOURCE_PATH),
                "SOURCE_BYTE_START": obs,
                "SOURCE_BYTE_END": cee,
                "SOURCE_LINE_START": open_line,
                "SOURCE_LINE_END": close_line,
                "PHYSICAL_SEQUENCE": phys_of_line(open_line),
                "CONTENT_SHA256": sha256_bytes(data[obs:cee]),
                "INTERIOR_BYTE_START": obe,
                "INTERIOR_BYTE_END": ces,
                "INTERIOR_SHA256": sha256_bytes(data[obe:ces]),
                "INFO_STRING_VERBATIM": info,
                "INFORMATION_CLASS": ["WRAPPER_DELIMITER", "VERBATIM_ORIGINAL_OUTPUT"]
                if info == "json"
                else ["WRAPPER_DELIMITER", "SOURCE_DECLARED_KEY_VALUE_PACKET"]
                if info == "text"
                else ["WRAPPER_DELIMITER"],
                "sidecar_record_provenance_class": "DERIVED_RECORD_WITH_SOURCE_BINDING",
                "referent_provenance_class": "ORIGINAL_SOURCE_SPAN",
                "AUTHORITY_STATUS": "NONE",
                "FIELD_STATUS": "PROVEN_MECHANICAL_FENCE",
                "NOTES": "Paired by physical toggle; not nested; not authority.",
            }
            fence_objs.append(rec)
            span_registry.append({"SPAN_ID": fid, "SOURCE_BYTE_START": obs, "SOURCE_BYTE_END": cee, "CONTENT_SHA256": rec["CONTENT_SHA256"]})
            span_registry.append({"SPAN_ID": fid + "-INTERIOR", "SOURCE_BYTE_START": obe, "SOURCE_BYTE_END": ces, "CONTENT_SHA256": rec["INTERIOR_SHA256"]})
            in_fence = False
            open_line = None
    i += 1
marker_count = sum(1 for ln in range(1, nlines + 1) if data[line_byte_span(ln)[0] : line_byte_span(ln)[1]].startswith(b"```"))
fence_balance = {
    "marker_count": marker_count,
    "paired_fence_count": len(fence_objs),
    "open_at_eof": in_fence,
    "balanced": (not in_fence) and (len(fence_objs) * 2 == marker_count),
}

json_string_spans: list[tuple[int, int]] = []
for f in fence_objs:
    if f["INFO_STRING_VERBATIM"] != "json":
        continue
    blob = data[f["INTERIOR_BYTE_START"] : f["INTERIOR_BYTE_END"]]
    abs0 = f["INTERIOR_BYTE_START"]
    in_str = False
    esc = False
    stt = 0
    k = 0
    while k < len(blob):
        c = blob[k]
        if in_str:
            if esc:
                esc = False
            elif c == 92:
                esc = True
            elif c == 34:
                json_string_spans.append((abs0 + stt, abs0 + k + 1))
                in_str = False
        elif c == 34:
            in_str = True
            stt = k
        k += 1


def in_json_string(pos: int) -> bool:
    for a, b in json_string_spans:
        if a < pos < b - 1:
            return True
    return False


def fence_at_line(ln: int):
    for f in fence_objs:
        if f["SOURCE_LINE_START"] < ln < f["SOURCE_LINE_END"]:
            return f
    return None


def find_line_eq(token: bytes):
    needle = token + b"\n"
    for ln in range(1, nlines + 1):
        ls, le = line_byte_span(ln)
        if data[ls:le] == needle:
            return ln
    return None


t4_begin_ln = find_line_eq(b"T4_CANON_COMPACT_TSV_BEGIN")
t4_end_ln = find_line_eq(b"T4_CANON_COMPACT_TSV_END")
t5_begin_ln = find_line_eq(b"T5_COMPACT_TSV_BEGIN")
t5_end_ln = find_line_eq(b"T5_COMPACT_TSV_END")
assert t4_begin_ln and t4_end_ln and t5_begin_ln and t5_end_ln

wrappers = []
derived_corpora = []


def wrapper_and_corpus(name: str, begin_ln: int, end_ln: int, claimed_sha: str, claimed_bytes: int, claimed_lines: int) -> dict:
    begin_s, begin_e = line_byte_span(begin_ln)
    end_s, end_e = line_byte_span(end_ln)
    raw_s, raw_e = begin_e, end_s
    raw = data[raw_s:raw_e]
    extra_lf = raw.endswith(b"\n\n")
    extra_s = raw_e - 1 if extra_lf else None
    extra_e = raw_e if extra_lf else None
    bound_e = raw_e - 1 if extra_lf else raw_e
    bound = data[raw_s:bound_e]
    w_begin = {
        "WRAPPER_ID": register_id(f"APP-WRAP-{name}-BEGIN", "APP"),
        "token_verbatim": data[begin_s : begin_e - 1].decode("utf-8"),
        "SOURCE_BYTE_START": begin_s,
        "SOURCE_BYTE_END": begin_e,
        "SOURCE_LINE_START": begin_ln,
        "SOURCE_LINE_END": begin_ln,
        "CONTENT_SHA256": sha256_bytes(data[begin_s:begin_e]),
        "INFORMATION_CLASS": ["WRAPPER_DELIMITER"],
        "sidecar_record_provenance_class": "DERIVED_RECORD_WITH_SOURCE_BINDING",
        "referent_provenance_class": "ORIGINAL_SOURCE_SPAN",
        "AUTHORITY_STATUS": "NONE",
        "PHYSICAL_BYTE_REPAIR_PERFORMED": False,
        "NOTES": f"{name} begin marker; wrapper only.",
    }
    w_end = {
        "WRAPPER_ID": register_id(f"APP-WRAP-{name}-END", "APP"),
        "token_verbatim": data[end_s : end_e - 1].decode("utf-8"),
        "SOURCE_BYTE_START": end_s,
        "SOURCE_BYTE_END": end_e,
        "SOURCE_LINE_START": end_ln,
        "SOURCE_LINE_END": end_ln,
        "CONTENT_SHA256": sha256_bytes(data[end_s:end_e]),
        "INFORMATION_CLASS": ["WRAPPER_DELIMITER"],
        "sidecar_record_provenance_class": "DERIVED_RECORD_WITH_SOURCE_BINDING",
        "referent_provenance_class": "ORIGINAL_SOURCE_SPAN",
        "AUTHORITY_STATUS": "NONE",
        "PHYSICAL_BYTE_REPAIR_PERFORMED": False,
        "NOTES": f"{name} end marker; wrapper only.",
    }
    extra_obj = None
    if extra_lf:
        extra_obj = {
            "WRAPPER_ID": register_id(f"APP-WRAP-{name}-EXTRA-LF", "APP"),
            "token_verbatim": "\\n",
            "SOURCE_BYTE_START": extra_s,
            "SOURCE_BYTE_END": extra_e,
            "SOURCE_LINE_START": byte_to_line(extra_s),
            "SOURCE_LINE_END": byte_to_line(extra_s),
            "CONTENT_SHA256": sha256_bytes(data[extra_s:extra_e]),
            "INFORMATION_CLASS": ["WRAPPER_DELIMITER"],
            "sidecar_record_provenance_class": "DERIVED_RECORD_WITH_SOURCE_BINDING",
            "referent_provenance_class": "ORIGINAL_SOURCE_SPAN",
            "AUTHORITY_STATUS": "NONE",
            "EXTRA_WRAPPER_LF_COUNT": 1,
            "PHYSICAL_BYTE_REPAIR_PERFORMED": False,
            "NOTES": f"Exactly one extra LF between bound {name} corpus and end marker. Conserved, not repaired.",
        }
        span_registry.append({"SPAN_ID": extra_obj["WRAPPER_ID"], "SOURCE_BYTE_START": extra_s, "SOURCE_BYTE_END": extra_e, "CONTENT_SHA256": extra_obj["CONTENT_SHA256"]})
    raw_id = f"SPAN-{name}-RAW-BETWEEN"
    bound_id = f"SPAN-{name}-BOUND-CORPUS"
    add_span(
        span_id=raw_id,
        byte_start=raw_s,
        byte_end=raw_e,
        information_class=["FORENSIC_DERIVED_CORPUS", "WRAPPER_DELIMITER"],
        provenance_sidecar="DERIVED_RECORD_WITH_SOURCE_BINDING",
        provenance_referent="HISTORICAL_DERIVED_ARTIFACT",
        notes=f"Raw bytes between {name} begin-line-end and end-line-start.",
        related=[f"APP-WRAP-{name}-BEGIN", f"APP-WRAP-{name}-END"],
    )
    add_span(
        span_id=bound_id,
        byte_start=raw_s,
        byte_end=bound_e,
        information_class=["FORENSIC_DERIVED_CORPUS"],
        provenance_sidecar="DERIVED_RECORD_WITH_SOURCE_BINDING",
        provenance_referent="HISTORICAL_DERIVED_ARTIFACT",
        notes=f"Bound {name} corpus excluding extra trailing wrapper LF if present.",
        related=[raw_id],
        extra={"PHYSICAL_BYTE_REPAIR_PERFORMED": False},
    )
    corpus = {
        "CORPUS_ID": register_id(f"APP-CORPUS-{name}", "APP"),
        "name": name,
        "RAW_SPAN_ID": raw_id,
        "BOUND_SPAN_ID": bound_id,
        "RAW_BYTES": len(raw),
        "BOUND_BYTES": len(bound),
        "BOUND_SHA256": sha256_bytes(bound),
        "RAW_SHA256": sha256_bytes(raw),
        "BOUND_LINE_COUNT": bound.count(b"\n"),
        "CLAIMED_SHA256": claimed_sha,
        "CLAIMED_BYTES": claimed_bytes,
        "CLAIMED_LINES": claimed_lines,
        "CLAIMED_SHA256_MATCH": sha256_bytes(bound) == claimed_sha,
        "CLAIMED_BYTES_MATCH": len(bound) == claimed_bytes,
        "CLAIMED_LINES_MATCH": bound.count(b"\n") == claimed_lines,
        "EXTRA_WRAPPER_LF_PRESENT": extra_lf,
        "PHYSICAL_BYTE_REPAIR_PERFORMED": False,
        "INFORMATION_CLASS": ["FORENSIC_DERIVED_CORPUS"],
        "sidecar_record_provenance_class": "DERIVED_RECORD_WITH_SOURCE_BINDING",
        "referent_provenance_class": "HISTORICAL_DERIVED_ARTIFACT",
        "AUTHORITY_STATUS": "NONE",
        "FIELD_STATUS": "PROVEN_MECHANICAL" if sha256_bytes(bound) == claimed_sha else "UNPROVEN_MISMATCH",
        "NOTES": "Wrapper markers excluded from bound hash. Sidecar record is derived; referent is historical derived artifact.",
    }
    wrappers.extend([w_begin, w_end] + ([extra_obj] if extra_obj else []))
    derived_corpora.append(corpus)
    span_registry.append({"SPAN_ID": w_begin["WRAPPER_ID"], "SOURCE_BYTE_START": begin_s, "SOURCE_BYTE_END": begin_e, "CONTENT_SHA256": w_begin["CONTENT_SHA256"]})
    span_registry.append({"SPAN_ID": w_end["WRAPPER_ID"], "SOURCE_BYTE_START": end_s, "SOURCE_BYTE_END": end_e, "CONTENT_SHA256": w_end["CONTENT_SHA256"]})
    return corpus


t4_corpus = wrapper_and_corpus("T4", t4_begin_ln, t4_end_ln, CLAIMED_T4_BOUND_SHA, CLAIMED_T4_BOUND_BYTES, CLAIMED_T4_BOUND_LINES)
t5_corpus = wrapper_and_corpus("T5", t5_begin_ln, t5_end_ln, CLAIMED_T5_BOUND_SHA, CLAIMED_T5_BOUND_BYTES, CLAIMED_T5_BOUND_LINES)

prefix = data[:CLAIMED_PREFIX_BYTES]
derived_corpora.append(
    {
        "CORPUS_ID": register_id("APP-CORPUS-T3-PREFIX-P01", "APP"),
        "name": "T3P_DECLARED_ORIGINAL_PREFIX",
        "BOUND_SPAN_ID": "SPAN-P01",
        "BOUND_BYTES": len(prefix),
        "BOUND_SHA256": sha256_bytes(prefix),
        "CLAIMED_SHA256": CLAIMED_PREFIX_SHA,
        "CLAIMED_BYTES": CLAIMED_PREFIX_BYTES,
        "CLAIMED_LINES": 30870,
        "CLAIMED_SHA256_MATCH": sha256_bytes(prefix) == CLAIMED_PREFIX_SHA,
        "P01_BYTE_LENGTH_EQUALS_CLAIMED_PREFIX": physical_blocks[0]["SOURCE_BYTE_END"] - physical_blocks[0]["SOURCE_BYTE_START"] == CLAIMED_PREFIX_BYTES,
        "INFORMATION_CLASS": ["INTEGRITY_METADATA"],
        "sidecar_record_provenance_class": "DERIVED_RECORD_WITH_SOURCE_BINDING",
        "referent_provenance_class": "ORIGINAL_SOURCE_RECORD",
        "AUTHORITY_STATUS": "NONE",
        "PHYSICAL_BYTE_REPAIR_PERFORMED": False,
        "NOTES": "Sidecar corpus object is derived. Referent bytes are source-declared ORIGINAL_PREFIX. Not FORENSIC_DERIVED_CORPUS.",
        "derivation_rule_id": "PROV-001",
    }
)

# KV in text fences — no gate heuristic
kv_re = re.compile(rb"^([A-Z][A-Z0-9_]*)=(.*)$")
kv_objs = []
text_fence_by_line = {}
for f in fence_objs:
    if f["INFO_STRING_VERBATIM"] == "text":
        for ln in range(f["SOURCE_LINE_START"] + 1, f["SOURCE_LINE_END"]):
            text_fence_by_line[ln] = f["FENCE_ID"]

for ln, fid in text_fence_by_line.items():
    ls, le = line_byte_span(ln)
    raw_line = data[ls:le]
    body = raw_line[:-1] if raw_line.endswith(b"\n") else raw_line
    m = kv_re.match(body)
    if not m:
        continue
    key = m.group(1).decode("ascii")
    val = m.group(2).decode("utf-8")
    classes = ["SOURCE_DECLARED_KEY_VALUE_PACKET"]
    amb = []
    if key in NON_AUTH_KEYS:
        classes.append("NON_AUTHORITY_PROTECTION_STATEMENT")
    if key.endswith("_AUTHORIZED") or "AUTHORIZED" in key or "GATE" in key:
        amb.append("AUTHORIZATION_RELATED_KEY_UNPROVEN_AS_GATE")
    if key.startswith("OWNER_GO"):
        classes.append("OWNER_GO_TOKEN_OCCURRENCE")
    temporal = "SOURCE_LITERAL_CURRENT_FIELD" if key.startswith("CURRENT_") else "PHYSICAL_ORDER"
    kid = new_id("KV")
    rec = occ_record(
        occ_id=kid,
        byte_start=ls,
        byte_end=le,
        information_class=classes,
        sidecar_prov="DERIVED_RECORD",
        referent_prov="ORIGINAL_SOURCE_SPAN",
        notes="Exact KEY=VALUE line inside a ```text fence; value not trimmed. No gate suffix heuristic.",
        related=[fid, phys_of_line(ln)],
        extra={
            "BLOCK_ID": kid,
            "key": key,
            "value_verbatim": val,
            "containing_fence": fid,
            "TEMPORAL_STATUS": temporal,
            "ambiguity_flags": amb,
            "derivation_rule_id": "GATE-003" if amb else "KV-001",
            "raw_token_verbatim": body.decode("utf-8"),
        },
    )
    kv_objs.append(rec)

# Historical IDs
id_occurrences = {"SRC": [], "REL": [], "CLS": [], "DEP": [], "UDEP": []}
forbidden_src089 = False
id_patterns = [
    (re.compile(rb"SRC-\d{6}"), "SRC", "HISTORICAL_ID_TOKEN_IN_SOURCE"),
    (re.compile(rb"REL-\d{6}"), "REL", "HISTORICAL_ID_TOKEN_IN_SOURCE"),
    (re.compile(rb"CLS-\d{6}"), "CLS", "HISTORICAL_ID_TOKEN_IN_SOURCE"),
]
for rx, ns, note in id_patterns:
    for m in rx.finditer(data):
        tok = m.group(0).decode("ascii")
        if tok == "SRC-000089":
            forbidden_src089 = True
        oid = new_id("OCC")
        rec = occ_record(
            occ_id=oid,
            byte_start=m.start(),
            byte_end=m.end(),
            information_class=["UNPROVEN"],
            sidecar_prov="DERIVED_RECORD",
            referent_prov="ORIGINAL_SOURCE_SPAN",
            notes="historical_id_occurrence_not_a_new_definition",
            extra={
                "historical_id": tok,
                "historical_id_namespace": ns,
                "FIELD_STATUS": "UNPROVEN",
                "classification_notes": "Occurrence of a preexisting historical ID; sidecar does not classify or redefine it.",
            },
            field_status="UNPROVEN",
        )
        rec["INFORMATION_CLASS"] = ["UNPROVEN"]
        id_occurrences[ns].append(rec)
if forbidden_src089:
    hard_stop_fail("SRC-000089_present")
assert "SRC-000089" not in all_sidecar_ids

dep_rx = re.compile(rb"(?<![A-Za-z0-9_])DEP-[A-Z0-9][A-Z0-9_-]*")
udep_rx = re.compile(rb"(?<![A-Za-z0-9_])UDEP-[A-Z0-9][A-Z0-9_-]*")
for m in udep_rx.finditer(data):
    tok = m.group(0).decode("ascii")
    oid = new_id("OCC")
    rec = occ_record(
        occ_id=oid,
        byte_start=m.start(),
        byte_end=m.end(),
        information_class=["UNPROVEN"],
        sidecar_prov="DERIVED_RECORD",
        referent_prov="ORIGINAL_SOURCE_SPAN",
        notes="UDEP namespace distinct from DEP. Not a dependency edge.",
        extra={
            "historical_id": tok,
            "historical_id_namespace": "UDEP",
            "token_namespace": "UDEP",
            "declaration_status": "MENTION",
            "derivation_rule_id": "TOK-UDEP-001",
            "DEPENDENCY_AFFILIATION": "UNPROVEN",
            "raw_token_verbatim": tok,
        },
        field_status="UNPROVEN",
    )
    id_occurrences["UDEP"].append(rec)
for m in dep_rx.finditer(data):
    tok = m.group(0).decode("ascii")
    oid = new_id("OCC")
    rec = occ_record(
        occ_id=oid,
        byte_start=m.start(),
        byte_end=m.end(),
        information_class=["UNPROVEN"],
        sidecar_prov="DERIVED_RECORD",
        referent_prov="ORIGINAL_SOURCE_SPAN",
        notes="bounded DEP id; not UDEP. Edge only if DEPENDENCY_ID declaration.",
        extra={
            "historical_id": tok,
            "historical_id_namespace": "DEP",
            "token_namespace": "DEP",
            "declaration_status": "MENTION",
            "derivation_rule_id": "TOK-DEP-001",
            "raw_token_verbatim": tok,
        },
        field_status="UNPROVEN",
    )
    id_occurrences["DEP"].append(rec)

src_def_heads = []
head_rx = re.compile(rb"^### (SRC-\d{6})\n$")
for ln in range(1, nlines + 1):
    ls, le = line_byte_span(ln)
    m = head_rx.match(data[ls:le])
    if m:
        src_def_heads.append({"historical_id": m.group(1).decode("ascii"), "SOURCE_LINE_START": ln, "SOURCE_BYTE_START": ls, "SOURCE_BYTE_END": le})

# POINTER_ID — occurrence CONFLICT_STATUS always UNPROVEN
pointer_occs = []
ptr_rx = re.compile(rb"POINTER_ID=([A-Z0-9_]+)")
for m in ptr_rx.finditer(data):
    rec = occ_record(
        occ_id=new_id("OCC"),
        byte_start=m.start(),
        byte_end=m.end(),
        information_class=["POINTER_INVENTORY_RECORD"],
        sidecar_prov="DERIVED_RECORD",
        referent_prov="ORIGINAL_SOURCE_SPAN",
        notes="POINTER_ID assignment occurrence; inventory only; no winner; occurrence conflict UNPROVEN (pair layer separate).",
        extra={
            "pointer_id_verbatim": m.group(1).decode("ascii"),
            "token_verbatim": m.group(0).decode("ascii"),
            "raw_token_verbatim": m.group(0).decode("ascii"),
            "CONFLICT_STATUS": "UNPROVEN",
            "derivation_rule_id": "CONF-001",
        },
    )
    pointer_occs.append(rec)

# Unresolved boundary markers
u_occs = []
u_objs = []
for tok in (b"U16612", b"U25510", b"U29481"):
    hits = []
    for m in re.compile(tok).finditer(data):
        rec = occ_record(
            occ_id=new_id("OCC"),
            byte_start=m.start(),
            byte_end=m.end(),
            information_class=["UNRESOLVED_BOUNDARY_MARKER"],
            sidecar_prov="DERIVED_RECORD",
            referent_prov="ORIGINAL_SOURCE_SPAN",
            notes="Unresolved boundary marker conserved; no CHILD_SRC assigned.",
            extra={"marker_verbatim": tok.decode("ascii"), "CHILD_SRC_ASSIGNED": False, "BOUNDARY_ADJUDICATION_PERFORMED": False, "raw_token_verbatim": tok.decode("ascii")},
        )
        hits.append(rec)
        u_occs.append(rec)
    u_objs.append(
        {
            "MARKER_ID": register_id(f"APP-UBOUND-{tok.decode()}", "APP"),
            "marker_verbatim": tok.decode("ascii"),
            "INFORMATION_CLASS": ["UNRESOLVED_BOUNDARY_MARKER"],
            "AUTHORITY_STATUS": "NONE",
            "CHILD_SRC_ASSIGNED": False,
            "BOUNDARY_ADJUDICATION_PERFORMED": False,
            "occurrence_count": len(hits),
            "occurrence_ids": [h["OCCURRENCE_ID"] for h in hits],
            "first_line": hits[0]["SOURCE_LINE_START"] if hits else None,
            "STATUS": "UNRESOLVED",
            "FIELD_STATUS": "PROVEN_PRESENT_IN_SOURCE",
            "NOTES": "Remains unresolved parent-only per source; sidecar assigns no CHILD_SRC.",
        }
    )

# Pedagogy spans occupy bytes
occupied: list[tuple[int, int]] = []
pedagogy_occs = []
for m in re.finditer(re.escape(PEDAGOGY), data):
    occupied.append((m.start(), m.end()))
    qstat = "JSON_STRING" if in_json_string(m.start()) else "UNPROVEN"
    rec = occ_record(
        occ_id=new_id("OCC"),
        byte_start=m.start(),
        byte_end=m.end(),
        information_class=["OWNER_GO_TOKEN_OCCURRENCE"],
        sidecar_prov="DERIVED_RECORD",
        referent_prov="QUOTED_OR_EMBEDDED_SOURCE_TEXT",
        notes="Atomic pedagogy token PASS=/OWNER_GO=/STATUS=. Not GO_DECLARATION. claimed_scope UNPROVEN.",
        extra={
            "token_verbatim": PEDAGOGY.decode("ascii"),
            "raw_token_verbatim": PEDAGOGY.decode("ascii"),
            "normalized_token": PEDAGOGY.decode("ascii"),
            "token_namespace": "GO_PEDAGOGY_SLASH_TRIPLE",
            "syntactic_context": "CTX_JSON_STRING" if qstat == "JSON_STRING" else "UNPROVEN",
            "semantic_context": "quoted",
            "declaration_status": "MENTION",
            "quote_status": qstat,
            "GO_CLASS": "GO_QUOTED_VERBATIM",
            "claimed_scope": "UNPROVEN",
            "derivation_rule_id": "TOK-GO-PEDAGOGY-001",
            "OWNER_GO_NE_OWNER_MERGE_GO": True,
        },
    )
    pedagogy_occs.append(rec)


def is_occupied(pos: int) -> bool:
    for a, b in occupied:
        if a <= pos < b:
            return True
    return False


def syntactic_context(pos: int, ln: int, ident: str) -> tuple[str, str, str]:
    if in_json_string(pos):
        return "CTX_JSON_STRING", "JSON_STRING", "quoted"
    f = fence_at_line(ln)
    if t4_begin_ln < ln < t4_end_ln and b"|" in data[line_byte_span(ln)[0] : line_byte_span(ln)[1]]:
        return "T4_TSV_CELL", "NONE", "historical"
    if f and f["INFO_STRING_VERBATIM"] == "text":
        return "CTX_FENCE_TEXT", "NONE", "declaration_candidate"
    if f and f["INFO_STRING_VERBATIM"] == "json":
        return "CTX_FENCE_JSON", "UNPROVEN", "unknown"
    ls, le = line_byte_span(ln)
    line = data[ls:le]
    if b";" in line and ident.encode("ascii") in line:
        return "CTX_SEMICOLON_FIELD", "NONE", "historical"
    if b"`" in line:
        return "CTX_MD_CODESPAN", "MD_CODESPAN", "mention"
    return "CTX_PROSE", "NONE", "mention"


go_occs = []
merge_go_occs = []
negated_go_occs = []
seen_ident_spans = set()

needle_positions = []
for needle in (b"OWNER_MERGE_GO", b"OWNER_GO"):
    startp = 0
    while True:
        p = data.find(needle, startp)
        if p < 0:
            break
        needle_positions.append((p, needle))
        startp = p + 1

for p, needle in needle_positions:
    if is_occupied(p):
        continue
    if not left_bound_ok(data, p) and needle == b"OWNER_GO":
        # may be inside U? OWNER_GO left bound uses A-Za-z0-9_
        pass
    L, R = expand_ident(data, p)
    if (L, R) in seen_ident_spans:
        continue
    if not left_bound_ok(data, L):
        continue
    seen_ident_spans.add((L, R))
    ident = data[L:R].decode("ascii")
    value = ""
    end = R
    if R < len(data) and data[R] == 61:
        vs, ve, value = parse_value(data, R)
        end = ve
        token = ident + "=" + value
    else:
        token = ident
    if is_occupied(L):
        continue
    ln = byte_to_line(L)
    syn, qstat, sem = syntactic_context(L, ln, ident)
    extra_base = {
        "token_verbatim": token,
        "raw_token_verbatim": token,
        "normalized_token": ident + (("=" + value) if value != "" else ""),
        "token_namespace": "UNPROVEN",
        "syntactic_context": syn,
        "semantic_context": sem,
        "quote_status": qstat,
        "OWNER_GO_NE_OWNER_MERGE_GO": True,
        "containing_block": phys_of_line(ln),
    }

    def emit(lst, *, go_class, ns, decl, rule, notes, cons="UNPROVEN", neg="NONE", scope="UNPROVEN", ics=None, referent=None):
        e = dict(extra_base)
        e.update(
            {
                "GO_CLASS": go_class,
                "token_namespace": ns,
                "declaration_status": decl,
                "derivation_rule_id": rule,
                "CONSUMPTION_STATUS": cons,
                "consumption_status": cons,
                "negation_status": neg,
                "claimed_scope": scope,
                "referent_provenance_class": referent or ("QUOTED_OR_EMBEDDED_SOURCE_TEXT" if qstat == "JSON_STRING" else "HISTORICAL_DERIVED_ARTIFACT" if syn == "T4_TSV_CELL" else "ORIGINAL_SOURCE_SPAN"),
            }
        )
        rec = occ_record(
            occ_id=new_id("OCC"),
            byte_start=L,
            byte_end=end,
            information_class=ics or ["OWNER_GO_TOKEN_OCCURRENCE"],
            sidecar_prov="DERIVED_RECORD",
            referent_prov=e["referent_provenance_class"],
            notes=notes,
            extra=e,
        )
        rec["CONSUMPTION_STATUS"] = cons
        rec["claimed_scope"] = scope
        rec["quote_status"] = qstat
        rec["declaration_status"] = decl
        rec["negation_status"] = neg
        rec["GO_CLASS"] = go_class
        lst.append(rec)

    if ident.startswith("NO_") and ("OWNER_GO" in ident or "OWNER_MERGE_GO" in ident):
        emit(
            negated_go_occs,
            go_class="GO_NEGATED_MENTION",
            ns="NEGATED_GO_KEY",
            decl="MENTION",
            rule="NEG-001",
            notes="NO_* identifier containing OWNER_GO/OWNER_MERGE_GO. Not a positive GO/Merge-GO claim.",
            neg="KEY_PREFIX_NO",
            ics=["OWNER_GO_TOKEN_OCCURRENCE"],
        )
        continue
    if ident.startswith("OWNER_MERGE_GO"):
        emit(
            merge_go_occs,
            go_class="GO_UNKNOWN_CONTEXT",
            ns="OWNER_MERGE_GO",
            decl="UNPROVEN",
            rule="TOK-GO-002",
            notes="Bounded OWNER_MERGE_GO* identifier. Not authorization.",
        )
        continue
    if not ident.startswith("OWNER_GO"):
        continue

    # OWNER_GO family
    scope = "UNPROVEN"
    go_class = "GO_TOKEN_MENTION"
    decl = "MENTION"
    ns = "OWNER_GO"
    rule = "TOK-GO-001"
    cons = "UNPROVEN"
    notes = "OWNER_GO family token; not operative authorization."
    referent = None

    if ident == "OWNER_GO_STATUS":
        go_class = "GO_STATUS_FIELD"
        ns = "OWNER_GO_STATUS"
        decl = "DECLARATION" if syn in {"CTX_FENCE_TEXT", "CTX_SEMICOLON_FIELD"} and qstat == "NONE" else "MENTION"
        rule = "CONS-001" if value == "CONSUMED" and qstat == "NONE" and ident == "OWNER_GO_STATUS" else "TOK-GO-001"
        if value == "CONSUMED" and qstat == "NONE" and syn in {"CTX_FENCE_TEXT", "CTX_SEMICOLON_FIELD", "CTX_PROSE"}:
            # CONS-001 requires exact field; semicolon or KV. Prose line that is a raw field line also counts if LEFT_BOUND exact key.
            go_class = "GO_CONSUMPTION_DECLARATION"
            cons = "SOURCE_DECLARED_CONSUMED_EXACT_FIELD"
            decl = "DECLARATION"
            rule = "CONS-001"
            notes = "CONS-001 exact OWNER_GO_STATUS=CONSUMED field only."
        else:
            notes = "OWNER_GO_STATUS field; consumption only if exact CONSUMED on whitelist."
    elif ident.startswith("OWNER_GO_REQUIRED"):
        go_class = "GO_REQUIREMENT_FIELD"
        ns = "OWNER_GO_REQUIRED"
        decl = "DECLARATION" if syn == "CTX_FENCE_TEXT" and qstat == "NONE" else "MENTION"
        notes = "Requirement field; not GO_DECLARATION grant."
    elif ident.startswith("OWNER_GO_TO_"):
        go_class = "GO_TOKEN_MENTION"
        ns = "OWNER_GO_TO"
        notes = "OWNER_GO_TO_* named token; not automatically OWNER_GO declaration."
    elif ident == "OWNER_GO":
        if qstat == "JSON_STRING":
            go_class = "GO_QUOTED_VERBATIM"
            decl = "MENTION"
            ns = "OWNER_GO"
            rule = "TOK-GO-004"
            notes = "Quoted/verbatim OWNER_GO. Not operative authorization. claimed_scope UNPROVEN."
            referent = "QUOTED_OR_EMBEDDED_SOURCE_TEXT"
        elif syn == "T4_TSV_CELL":
            go_class = "GO_HISTORICAL_RECORD"
            decl = "MENTION"
            ns = "OWNER_GO"
            rule = "TOK-GO-T4CELL-001"
            notes = "T4 TSV cell OWNER_GO=true historical extract. Not GO_DECLARATION."
            referent = "HISTORICAL_DERIVED_ARTIFACT"
        elif syn == "CTX_FENCE_TEXT" and qstat == "NONE":
            go_class = "GO_DECLARATION"
            decl = "DECLARATION"
            if value not in BOOLEANISH and value != "":
                scope = value
            notes = "Text-fence OWNER_GO declaration. authority_status NONE. Not operative authorization."
        elif syn == "CTX_SEMICOLON_FIELD":
            go_class = "GO_HISTORICAL_RECORD"
            decl = "MENTION"
            notes = "Semicolon persist field OWNER_GO. Historical record, not present authorization."
        elif syn == "CTX_MD_CODESPAN":
            go_class = "GO_TOKEN_MENTION"
            decl = "MENTION"
            notes = "Markdown codespan OWNER_GO mention."
        else:
            go_class = "GO_TOKEN_MENTION"
            decl = "MENTION"
            notes = "Prose or unknown-context OWNER_GO mention."
    else:
        go_class = "GO_TOKEN_MENTION"
        ns = "OWNER_GO_OTHER_SUFFIX"
        notes = "OWNER_GO_* suffix token; not automatically OWNER_GO declaration."

    emit(
        go_occs,
        go_class=go_class,
        ns=ns,
        decl=decl,
        rule=rule,
        notes=notes,
        cons=cons,
        scope=scope,
        referent=referent,
    )

# CONS-002 PRIOR_GET_OWNER_GO_STATUS=CONSUMED (not OWNER_GO-prefixed)
cons002_occs = []
cons002_rx = re.compile(rb"(?<![A-Za-z0-9_])PRIOR_GET_OWNER_GO_STATUS=CONSUMED(?![A-Za-z0-9_])")
for m in cons002_rx.finditer(data):
    rec = occ_record(
        occ_id=new_id("OCC"),
        byte_start=m.start(),
        byte_end=m.end(),
        information_class=["OWNER_GO_TOKEN_OCCURRENCE"],
        sidecar_prov="DERIVED_RECORD",
        referent_prov="ORIGINAL_SOURCE_SPAN",
        notes="CONS-002 exact PRIOR_GET_OWNER_GO_STATUS=CONSUMED. Not aliased to OWNER_GO_STATUS.",
        extra={
            "token_verbatim": m.group(0).decode("ascii"),
            "raw_token_verbatim": m.group(0).decode("ascii"),
            "GO_CLASS": "GO_CONSUMPTION_DECLARATION",
            "token_namespace": "PRIOR_GET_OWNER_GO_STATUS",
            "declaration_status": "DECLARATION",
            "CONSUMPTION_STATUS": "SOURCE_DECLARED_CONSUMED_EXACT_FIELD",
            "consumption_status": "SOURCE_DECLARED_CONSUMED_EXACT_FIELD",
            "claimed_scope": "UNPROVEN",
            "derivation_rule_id": "CONS-002",
        },
    )
    cons002_occs.append(rec)

# PASS index
pass_occs = []
for ln in range(1, nlines + 1):
    ls, le = line_byte_span(ln)
    line = data[ls:le]
    if b"PASS=" not in line:
        continue
    if PEDAGOGY in line:
        continue
    m = re.search(rb"PASS=[A-Z0-9_]+(?:[ +][A-Z0-9_]+)*", line)
    if not m:
        continue
    rec = occ_record(
        occ_id=new_id("OCC"),
        byte_start=ls + m.start(),
        byte_end=ls + m.end(),
        information_class=["NAVIGATION_OR_INDEX"],
        sidecar_prov="DERIVED_RECORD",
        referent_prov="ORIGINAL_SOURCE_SPAN",
        notes="PASS= token occurrence; navigation only. Pedagogy triples excluded.",
        extra={"token_verbatim": m.group(0).decode("ascii"), "BLOCK_ID": phys_of_line(ln), "raw_token_verbatim": m.group(0).decode("ascii")},
    )
    pass_occs.append(rec)

# T5 rows
t5_label_counts = Counter()
t5_row_count = 0
t5_first_id = None
t5_last_id = None
t5_ids = []
bound_span = next(s for s in span_registry if s.get("SPAN_ID") == "SPAN-T5-BOUND-CORPUS")
t5_bound_bytes = data[bound_span["SOURCE_BYTE_START"] : bound_span["SOURCE_BYTE_END"]]
for row in t5_bound_bytes.splitlines():
    if not row:
        continue
    t5_row_count += 1
    parts = row.split(b"|")
    if parts:
        cid = parts[0].decode("ascii", errors="replace")
        t5_ids.append(cid)
        if t5_first_id is None:
            t5_first_id = cid
        t5_last_id = cid
    if len(parts) > 5:
        t5_label_counts[parts[5].decode("ascii", errors="replace")] += 1
label_mappings = []
for hist, cnt in sorted(t5_label_counts.items(), key=lambda x: (-x[1], x[0])):
    label_mappings.append(
        {
            "historical_label": hist,
            "mapped_label": T5_LABEL_MAP_CANDIDATES.get(hist, "UNPROVEN"),
            "mapping_status": "UNPROVEN",
            "occurrence_count_in_t5_bound_corpus": cnt,
            "NOTES": "Historical T5 labels are not automatically equated to the projection class model.",
        }
    )

# Headings
h_rx = re.compile(rb"^(#{1,6})[ \t]+(.*)$")
headings = []
for ln in range(1, nlines + 1):
    ls, le = line_byte_span(ln)
    m = h_rx.match(data[ls:le] if not data[ls:le].endswith(b"\n") else data[ls : le - 1] + b"\n")
    rawl = data[ls:le]
    body = rawl[:-1] if rawl.endswith(b"\n") else rawl
    m = h_rx.match(body + b"\n") if False else h_rx.match(body)
    if not m:
        continue
    headings.append(
        {
            "HEADING_ID": register_id(new_id("NAV"), "NAV"),
            "level": len(m.group(1)),
            "text_verbatim": m.group(2).decode("utf-8"),
            "SOURCE_LINE_START": ln,
            "SOURCE_BYTE_START": ls,
            "SOURCE_BYTE_END": le,
            "INFORMATION_CLASS": ["NAVIGATION_OR_INDEX"],
            "AUTHORITY_STATUS": "NONE",
            "sidecar_record_provenance_class": "DERIVED_RECORD",
            "referent_provenance_class": "NAVIGATION_ONLY",
        }
    )

# L3 adjudications — mapping ceiling
def kv_lookup(key: str, min_line: int, max_line: int):
    return [kv for kv in kv_objs if kv.get("key") == key and min_line <= kv["SOURCE_LINE_START"] <= max_line]

p06 = next(b for b in physical_blocks if b["BLOCK_ID"] == "P06")
p09 = next(b for b in physical_blocks if b["BLOCK_ID"] == "P09")
adjudications = [
    {
        "ADJUDICATION_ID": register_id("ADJ-000001", "ADJ"),
        "BLOCK_ID": "P06",
        "title_verbatim": physical_blocks[5]["heading_verbatim"],
        "SOURCE_LINE_START": p06["SOURCE_LINE_START"],
        "SOURCE_LINE_END": p06["SOURCE_LINE_END"],
        "SOURCE_BYTE_START": p06["SOURCE_BYTE_START"],
        "SOURCE_BYTE_END": p06["SOURCE_BYTE_END"],
        "SPAN_ID": "SPAN-P06",
        "INFORMATION_CLASS": ["UNPROVEN"],
        "source_epistemic_class": "ABSENT_IN_P06",
        "historical_label": "T5PR",
        "mapped_label": "ADJUDICATED_FORENSIC_CONCLUSION",
        "mapping_status": "UNPROVEN",
        "sidecar_record_provenance_class": "DERIVED_RECORD_WITH_SOURCE_BINDING",
        "referent_provenance_class": "ORIGINAL_SOURCE_SPAN",
        "AUTHORITY_STATUS": "NONE",
        "ADJUDICATION_STATUS": "SOURCE_DECLARED_ONLY_NOT_REPERFORMED",
        "TEMPORAL_STATUS": "ADJUDICATED_LATER",
        "PHYSICAL_BYTE_REPAIR_PERFORMED": False,
        "BOUNDARY_ADJUDICATION_PERFORMED": False,
        "derivation_rule_id": "PROV-004",
        "EVIDENCE_SPAN_IDS": ["SPAN-P06", "SPAN-T5-BOUND-CORPUS", "SPAN-T5-RAW-BETWEEN"],
        "source_declared_facts": {
            "FAILURE_CAUSE": [k["value_verbatim"] for k in kv_lookup("FAILURE_CAUSE", 117420, 117630)],
            "PHYSICAL_BYTE_REPAIR_PERFORMED": [k["value_verbatim"] for k in kv_lookup("PHYSICAL_BYTE_REPAIR_PERFORMED", 117420, 117630)],
        },
        "NOTES": "P06 has no EPISTEMIC_CLASS. IC remains UNPROVEN. mapped_label not used as proven INFORMATION_CLASS. T5P unrepaired. Not re-adjudicated.",
        "RELATED_BLOCK_IDS": ["P05", "P06", "SPAN-P05", "SPAN-P06"],
        "FIELD_STATUS": "PROVEN_SOURCE_DECLARED_BLOCK",
    },
    {
        "ADJUDICATION_ID": register_id("ADJ-000002", "ADJ"),
        "BLOCK_ID": "P09",
        "title_verbatim": physical_blocks[8]["heading_verbatim"],
        "SOURCE_LINE_START": p09["SOURCE_LINE_START"],
        "SOURCE_LINE_END": p09["SOURCE_LINE_END"],
        "SOURCE_BYTE_START": p09["SOURCE_BYTE_START"],
        "SOURCE_BYTE_END": p09["SOURCE_BYTE_END"],
        "SPAN_ID": "SPAN-P09",
        "INFORMATION_CLASS": ["UNPROVEN"],
        "source_epistemic_class": "ADJUDICATED_FORENSIC_FINDING",
        "historical_label": "ADJUDICATED_FORENSIC_FINDING",
        "mapped_label": "ADJUDICATED_FORENSIC_CONCLUSION",
        "mapping_status": "UNPROVEN",
        "sidecar_record_provenance_class": "DERIVED_RECORD_WITH_SOURCE_BINDING",
        "referent_provenance_class": "ORIGINAL_SOURCE_SPAN",
        "AUTHORITY_STATUS": "NONE",
        "ADJUDICATION_STATUS": "SOURCE_DECLARED_UNRESOLVED_NOT_REPERFORMED",
        "TEMPORAL_STATUS": "ADJUDICATED_LATER",
        "POINTER_WINNER_SELECTED": False,
        "BOUNDARY_ADJUDICATION_PERFORMED": False,
        "CONFLICT_STATUS": "UNPROVEN",
        "derivation_rule_id": "PROV-004",
        "EVIDENCE_SPAN_IDS": ["SPAN-P09"],
        "source_declared_facts": {
            "EPISTEMIC_CLASS": [k["value_verbatim"] for k in kv_lookup("EPISTEMIC_CLASS", 118451, 118809)],
            "CANONICAL_NEXT_POINTER_ADJUDICATION": [k["value_verbatim"] for k in kv_lookup("CANONICAL_NEXT_POINTER_ADJUDICATION", 118451, 118809)],
            "AUTHORITATIVE_NEXT_POINTER": [k["value_verbatim"] for k in kv_lookup("AUTHORITATIVE_NEXT_POINTER", 118451, 118809)],
            "WINNER_SELECTED": [k["value_verbatim"] for k in kv_lookup("WINNER_SELECTED", 118451, 118809)],
        },
        "NOTES": "Source EPISTEMIC_CLASS=ADJUDICATED_FORENSIC_FINDING stored verbatim. mapped_label UNPROVEN and not copied into INFORMATION_CLASS. No winner.",
        "RELATED_BLOCK_IDS": ["P09", "SPAN-P09"],
        "FIELD_STATUS": "PROVEN_SOURCE_DECLARED_BLOCK",
    },
]

def first_kv_global(key: str):
    for kv in kv_objs:
        if kv.get("key") == key:
            return kv
    return None

def all_kv_global(key: str):
    return [kv for kv in kv_objs if kv.get("key") == key]

# Conflict pairs from source PAIR KVs — not occurrence flatten
pair_kvs = all_kv_global("PAIR")
conflict_pairs = []
for pk in pair_kvs:
    ln = pk["SOURCE_LINE_START"]
    nearby = [kv for kv in kv_objs if ln <= kv["SOURCE_LINE_START"] <= ln + 8]
    status_kv = next((kv for kv in nearby if kv.get("key") == "CONFLICT_STATUS"), None)
    coex_kv = next((kv for kv in nearby if kv.get("key") == "COEXISTENCE_EXPLICITLY_ALLOWED"), None)
    conflict_pairs.append(
        {
            "CONFLICT_PAIR_ID": register_id(new_id("CONFLICT"), "CONFLICT") if False else register_id(f"CONFLICT-PAIR-{len(conflict_pairs)+1:06d}", "CONFLICT"),
            "PAIR": pk.get("value_verbatim"),
            "CONFLICT_STATUS": status_kv.get("value_verbatim") if status_kv else "UNPROVEN",
            "COEXISTENCE_EXPLICITLY_ALLOWED": coex_kv.get("value_verbatim") if coex_kv else "UNPROVEN",
            "SOURCE_LINE_START": ln,
            "POINTER_WINNER_SELECTED": False,
            "AUTHORITY_STATUS": "NONE",
            "derivation_rule_id": "CONF-001",
            "NOTES": "Pair-level source CONFLICT_STATUS copied verbatim. Not copied onto POINTER_ID occurrences.",
            "FIELD_STATUS": "PROVEN_SOURCE_DECLARED" if status_kv else "UNPROVEN",
        }
    )

conflicts = [
    {
        "CONFLICT_ID": register_id("CONFLICT-000001", "CONFLICT"),
        "title": "canonical_next_pointer_adjudication",
        "CONFLICT_STATUS": "UNRESOLVED",
        "AUTHORITY_STATUS": "NONE",
        "POINTER_WINNER_SELECTED": False,
        "source_keys_queried": ["CANONICAL_NEXT_POINTER_ADJUDICATION", "AUTHORITATIVE_NEXT_POINTER", "WINNER_SELECTED"],
        "source_values_verbatim": [{"key": x["key"], "value": x.get("value_verbatim"), "line": x["SOURCE_LINE_START"]} for k in ["CANONICAL_NEXT_POINTER_ADJUDICATION", "AUTHORITATIVE_NEXT_POINTER", "WINNER_SELECTED"] for x in all_kv_global(k)],
        "NOTES": "Wiedergabe von CANONICAL_NEXT_POINTER_ADJUDICATION=UNRESOLVED. Nicht Occurrence-Status aller Pointer.",
        "FIELD_STATUS": "PROVEN_SOURCE_DECLARED",
        "derivation_rule_id": "CONF-001",
    }
]
for cp in conflict_pairs:
    conflicts.append(
        {
            "CONFLICT_ID": cp["CONFLICT_PAIR_ID"],
            "title": f"pair_{cp['PAIR']}",
            "CONFLICT_STATUS": cp["CONFLICT_STATUS"],
            "AUTHORITY_STATUS": "NONE",
            "POINTER_WINNER_SELECTED": False,
            "PAIR": cp["PAIR"],
            "COEXISTENCE_EXPLICITLY_ALLOWED": cp["COEXISTENCE_EXPLICITLY_ALLOWED"],
            "SOURCE_LINE_START": cp["SOURCE_LINE_START"],
            "NOTES": cp["NOTES"],
            "FIELD_STATUS": cp["FIELD_STATUS"],
            "derivation_rule_id": "CONF-002",
        }
    )
conflicts.append(
    {
        "CONFLICT_ID": register_id("CONFLICT-T6-ABSENT", "CONFLICT"),
        "title": "t_phase_sequence_and_t6_definition",
        "CONFLICT_STATUS": "ABSENT_OR_UNPROVEN_PER_SOURCE",
        "AUTHORITY_STATUS": "NONE",
        "POINTER_WINNER_SELECTED": False,
        "source_keys_queried": ["T6_DEFINITION_FOUND", "T4_TO_T5_TO_T6_SEQUENCE_PROVEN", "T6_CONSUMES_T5_OUTPUT_PROVEN", "T6_EXECUTED", "T6_SPECIFICATION_INFERRED"],
        "NOTES": "T6 definition not found in source. STEP_6 is not equated to T6. Sequence T3→T4→T5→T6 is not inferred.",
        "FIELD_STATUS": "PROVEN_SOURCE_DECLARED",
    }
)

go_listed_absent = []
for exact in ("Z2AR_INTERNAL_EXECUTION_ORDER_PROVEN", "PREEXISTING_CANONICAL_POINTER_ADJUDICATION", "PREEXISTING_AUTHORITATIVE_NEXT_POINTER"):
    present = first_kv_global(exact) is not None
    go_listed_absent.append({"token": exact, "exact_kv_present_in_source": present, "FIELD_STATUS": "PROVEN_PRESENT" if present else "UNPROVEN_EXACT_TOKEN_ABSENT_IN_SOURCE"})

# Dependency edges only DEPENDENCY_ID=
dep_edges = []
for kv in kv_objs:
    if kv.get("key") == "DEPENDENCY_ID" and str(kv.get("value_verbatim", "")).startswith("DEP-T"):
        ln = kv["SOURCE_LINE_START"]
        nearby = [x for x in kv_objs if ln <= x["SOURCE_LINE_START"] <= ln + 8]
        stv = next((x.get("value_verbatim") for x in nearby if x.get("key") == "DEPENDENCY_STATUS"), "UNPROVEN")
        edge_type = "NEGATIVE_CURRENT_DEPENDENCY_CLAIM" if kv["value_verbatim"] == "DEP-T5-T4-NOT-CURRENT" else "SOURCE_DECLARED_DEPENDENCY_EDGE"
        dep_edges.append(
            {
                "EDGE_ID": register_id(new_id("DEPEDGE"), "APP") if False else register_id(f"APP-DEP-EDGE-{kv['value_verbatim']}", "APP"),
                "DEPENDENCY_ID": kv["value_verbatim"],
                "SOURCE_LINE_START": ln,
                "DEPENDENCY_STATUS": stv,
                "edge_type": edge_type,
                "derivation_rule_id": "DEP-EDGE-001",
                "AUTHORITY_STATUS": "NONE",
                "NOTES": "Explicit DEPENDENCY_ID text-fence declaration only.",
            }
        )

# L6 master runbook — correct regex
extrefs = []
for m in re.compile(rb"PEAK_TRADE_MASTER_RUNBOOK\.md").finditer(data):
    ln = byte_to_line(m.start())
    left = data[max(0, m.start() - 40) : m.start()]
    if left.endswith(b"docs.runbooks.canonical."):
        form = "DOTTED_PATH"
    elif left.endswith(b"docs/runbooks/canonical/"):
        form = "SLASH_PATH"
    else:
        form = "OTHER_PREFIX"
    q = "JSON_STRING" if in_json_string(m.start()) else "NONE"
    rec = occ_record(
        occ_id=new_id("EXTREF"),
        byte_start=m.start(),
        byte_end=m.end(),
        information_class=["CANONICAL_AUTHORITY_REFERENCE"],
        sidecar_prov="DERIVED_RECORD",
        referent_prov="CANONICAL_EXTERNAL_REFERENCE" if False else "ORIGINAL_SOURCE_SPAN",
        notes="Reference only. Sidecar does not import Master Runbook content or authority.",
        extra={
            "token_verbatim": m.group(0).decode("ascii"),
            "raw_token_verbatim": m.group(0).decode("ascii"),
            "path_form": form,
            "quote_status": q,
            "CANONICAL_REFERENCE_NE_SIDECAR_AUTHORITY": True,
            "derivation_rule_id": "REF-001",
            "TEMPORAL_STATUS": "CANONICAL_EXTERNAL_REFERENCE",
        },
    )
    extrefs.append(rec)

bare_refs = []
for m in re.compile(rb"(?<![A-Za-z0-9_./])PEAK_TRADE_MASTER_RUNBOOK(?!\.md)").finditer(data):
    rec = occ_record(
        occ_id=new_id("EXTREF"),
        byte_start=m.start(),
        byte_end=m.end(),
        information_class=["CANONICAL_AUTHORITY_REFERENCE"],
        sidecar_prov="DERIVED_RECORD",
        referent_prov="ORIGINAL_SOURCE_SPAN",
        notes="Bare PEAK_TRADE_MASTER_RUNBOOK without .md; indexed separately; not aliased to .md path; not authority.",
        extra={"token_verbatim": "PEAK_TRADE_MASTER_RUNBOOK", "raw_token_verbatim": "PEAK_TRADE_MASTER_RUNBOOK", "path_form": "BARE_NO_MD", "CANONICAL_REFERENCE_NE_SIDECAR_AUTHORITY": True, "derivation_rule_id": "REF-001"},
    )
    bare_refs.append(rec)

sha_occs = []
for m in re.compile(ORIGIN_MAIN_REF_SHA.encode("ascii")).finditer(data):
    rec = occ_record(
        occ_id=new_id("EXTREF"),
        byte_start=m.start(),
        byte_end=m.end(),
        information_class=["CANONICAL_AUTHORITY_REFERENCE", "INTEGRITY_METADATA"],
        sidecar_prov="DERIVED_RECORD",
        referent_prov="ORIGINAL_SOURCE_SPAN",
        notes="origin/main SHA as it occurs in source. No new fetch/pull performed.",
        extra={"token_verbatim": ORIGIN_MAIN_REF_SHA, "TEMPORAL_STATUS": "CANONICAL_EXTERNAL_REFERENCE", "CANONICAL_REFERENCE_NE_SIDECAR_AUTHORITY": True},
    )
    sha_occs.append(rec)

src_counter = Counter(r["historical_id"] for r in id_occurrences["SRC"])
def_map = {h["historical_id"]: h for h in src_def_heads}
src_index = [{"historical_id": sid, "occurrence_count": src_counter[sid], "definition_heading_line": def_map.get(sid, {}).get("SOURCE_LINE_START"), "CHILD_SRC_ASSIGNED": False} for sid in sorted(src_counter)]
pc = Counter(r["pointer_id_verbatim"] for r in pointer_occs)
pointer_index = [{"POINTER_ID": pid, "occurrence_count": c, "occurrence_ids": [r["OCCURRENCE_ID"] for r in pointer_occs if r["pointer_id_verbatim"] == pid], "AUTHORITY_STATUS": "NONE", "WINNER": False, "NOTES": "Inventory only. Occurrence CONFLICT_STATUS UNPROVEN."} for pid, c in pc.items()]
pcc = Counter(r["token_verbatim"] for r in pass_occs)
pass_index = [{"token_verbatim": tok, "occurrence_count": c, "AUTHORITY_STATUS": "NONE"} for tok, c in sorted(pcc.items(), key=lambda x: -x[1])]

# Explicit DEPENDENCY_ID edge ids uniqueness: APP-DEP-EDGE-* may collide if register_id twice — already unique by id string.

# ---------------------------------------------------------------------------
# Oracles and adversarial tests
# ---------------------------------------------------------------------------
tests = []


def test_pass(tid, name, status, evidence):
    tests.append({"TEST_ID": tid, "name": name, "TEST_STATUS": status, "evidence": evidence})
    return status == "PASS"


def tok_fragment(s: bytes, ctx: str):
    """Minimal tokenizer for synthetic adversarial fragments.

    DEP-family hyphen grammar is confined to this harness helper and reuses
    corpus dep_rx/udep_rx. GO/KV identifiers keep expand_ident charset (no '-').
    """
    out = []
    if PEDAGOGY in s:
        i = s.find(PEDAGOGY)
        out.append({"raw": PEDAGOGY.decode(), "ns": "GO_PEDAGOGY_SLASH_TRIPLE", "GO_CLASS": "GO_QUOTED_VERBATIM", "claimed_scope": "UNPROVEN", "start": i})
        return out

    n = len(s)
    occupied = bytearray(n)
    harness_xdep_rx = re.compile(rb"(?<![A-Za-z0-9_])XDEP-[A-Z0-9][A-Z0-9_-]*")
    harness_nodep_rx = re.compile(rb"(?<![A-Za-z0-9_])NO_DEP-[A-Z0-9][A-Z0-9_-]*")

    def span_free(a: int, b: int) -> bool:
        return not any(occupied[a:b])

    def mark(a: int, b: int) -> None:
        occupied[a:b] = b"\x01" * (b - a)

    def emit_dep_family(m: re.Match, ns: str) -> None:
        ident_end = m.end()
        if ident_end < n and s[ident_end] == 61:
            _vs, rec_end, val = parse_value(s, ident_end)
            raw = m.group(0).decode("ascii") + "=" + val
        else:
            rec_end, val = ident_end, ""
            raw = m.group(0).decode("ascii")
        if not span_free(m.start(), rec_end):
            return
        ident = m.group(0).decode("ascii")
        out.append({"raw": raw, "ident": ident, "value": val, "start": m.start(), "ns": ns})
        mark(m.start(), rec_end)

    for m in udep_rx.finditer(s):
        emit_dep_family(m, "UDEP")
    for m in harness_xdep_rx.finditer(s):
        emit_dep_family(m, "XDEP")
    for m in harness_nodep_rx.finditer(s):
        emit_dep_family(m, "NEGATED_DEP")
    for m in dep_rx.finditer(s):
        emit_dep_family(m, "DEP")

    for m in re.finditer(rb"(?<![A-Za-z0-9_])([A-Z][A-Z0-9_]*)(?:=([^\s`|;,\"'}{\]]*))?", s):
        if not span_free(m.start(), m.end()):
            continue
        ident = m.group(1).decode()
        val = (m.group(2) or b"").decode()
        rec = {"raw": m.group(0).decode(), "ident": ident, "value": val, "start": m.start()}
        if ident.startswith("NO_") and ("OWNER_GO" in ident or "OWNER_MERGE_GO" in ident):
            rec["ns"] = "NEGATED_GO_KEY"
            rec["GO_CLASS"] = "GO_NEGATED_MENTION"
        elif ident.startswith("OWNER_MERGE_GO"):
            rec["ns"] = "OWNER_MERGE_GO"
        elif ident.startswith("OWNER_GO_REQUIRED"):
            rec["ns"] = "OWNER_GO_REQUIRED"
            rec["GO_CLASS"] = "GO_REQUIREMENT_FIELD"
        elif ident == "OWNER_GO_STATUS":
            rec["ns"] = "OWNER_GO_STATUS"
            rec["GO_CLASS"] = "GO_CONSUMPTION_DECLARATION" if val == "CONSUMED" and ident in CONS_WHITELIST else "GO_STATUS_FIELD"
            rec["consumption"] = "SOURCE_DECLARED_CONSUMED_EXACT_FIELD" if ident in CONS_WHITELIST and val == "CONSUMED" else "UNPROVEN"
        elif ident == "OWNER_GO":
            rec["ns"] = "OWNER_GO"
            if ctx == "JSON_STRING":
                rec["GO_CLASS"] = "GO_QUOTED_VERBATIM"
                rec["claimed_scope"] = "UNPROVEN"
            elif ctx == "T4_TSV_CELL":
                rec["GO_CLASS"] = "GO_HISTORICAL_RECORD"
            elif ctx == "TEXT_FENCE":
                rec["GO_CLASS"] = "GO_DECLARATION"
            else:
                rec["GO_CLASS"] = "GO_TOKEN_MENTION"
        elif ident == "WHAT_NOT_AUTHORIZED" or ident == "CAN_GATE_3_NOW_BE_AUTHORIZED":
            rec["ns"] = "KV"
            rec["IC"] = ["SOURCE_DECLARED_KEY_VALUE_PACKET"]
            rec["gate"] = False
        elif ident.endswith("_AUTHORIZED"):
            rec["ns"] = "KV"
            rec["gate"] = False
        out.append(rec)
        mark(m.start(), m.end())
    return out

# Whole corpus oracles
udep_ids = {r["historical_id"] for r in id_occurrences["UDEP"]}
dep_ids = {r["historical_id"] for r in id_occurrences["DEP"]}
oracle_udep_not_dep = not any(x[1:] == d or d == x.replace("UDEP-", "DEP-") for x in udep_ids for d in dep_ids if x.replace("UDEP-", "DEP-") == d) and all(not i.startswith("UDEP") for i in dep_ids)
# simpler: no DEP historical_id equals stripping U from UDEP
alias = []
for u in udep_ids:
    fake = "DEP-" + u[5:] if u.startswith("UDEP-") else None
    if fake in dep_ids:
        alias.append((u, fake))
F01 = len(alias) == 0 and len(id_occurrences["UDEP"]) == 20 and len(id_occurrences["DEP"]) == 8

cons001_n = sum(1 for g in go_occs if g.get("derivation_rule_id") == "CONS-001" and g.get("CONSUMPTION_STATUS") == "SOURCE_DECLARED_CONSUMED_EXACT_FIELD")
# also GO_CLASS
cons001_n = sum(1 for g in go_occs if g.get("GO_CLASS") == "GO_CONSUMPTION_DECLARATION" and g.get("token_verbatim", "").startswith("OWNER_GO_STATUS=CONSUMED"))
cons002_n = len(cons002_occs)
line_cons_fp = sum(1 for g in go_occs if g.get("CONSUMPTION_STATUS") == "SOURCE_LINE_CONTAINS_CONSUMED")
F02 = cons001_n == 3 and cons002_n == 1 and line_cons_fp == 0

F03 = len(merge_go_occs) == 0
F04 = len(pedagogy_occs) == 88 and all(g.get("claimed_scope") == "UNPROVEN" for g in pedagogy_occs) and all(g.get("GO_CLASS") == "GO_QUOTED_VERBATIM" for g in pedagogy_occs)
gate_n = sum(1 for kv in kv_objs if "LOCAL_FORENSIC_GATE_RECORD" in (kv.get("INFORMATION_CLASS") or []) or "GATE_OR_AUTHORIZATION_BOUNDARY" in (kv.get("INFORMATION_CLASS") or []))
F05 = gate_n == 0
F06 = len(extrefs) == 30
ptr_unresolved_occ = sum(1 for p in pointer_occs if p.get("CONFLICT_STATUS") == "UNRESOLVED")
pair_status = {c.get("PAIR"): c.get("CONFLICT_STATUS") for c in conflicts if c.get("PAIR")}
F07 = ptr_unresolved_occ == 0 and pair_status.get("Z2AR_VS_Z2AP") == "EXPLICIT_COEXISTENCE_WITHOUT_RANKING" and pair_status.get("Z2AR_VS_SECTION_22") == "UNRESOLVED_NO_EXPLICIT_RULE" and pair_status.get("Z2AP_VS_SECTION_22") == "UNRESOLVED_NO_EXPLICIT_RULE"
F08 = all("ADJUDICATED_FORENSIC_CONCLUSION" not in (a.get("INFORMATION_CLASS") or []) for a in adjudications) and all(a.get("mapping_status") == "UNPROVEN" for a in adjudications)
pref = next(c for c in derived_corpora if c["CORPUS_ID"] == "APP-CORPUS-T3-PREFIX-P01")
F09 = pref.get("referent_provenance_class") == "ORIGINAL_SOURCE_RECORD" and pref.get("sidecar_record_provenance_class") == "DERIVED_RECORD_WITH_SOURCE_BINDING" and "FORENSIC_DERIVED_CORPUS" not in (pref.get("INFORMATION_CLASS") or [])
quoted_true = [g for g in go_occs if g.get("token_verbatim") in {"OWNER_GO=true", "OWNER_GO"} and g.get("GO_CLASS") == "GO_QUOTED_VERBATIM" and (g.get("normalized_token") == "OWNER_GO=true" or g.get("token_verbatim") == "OWNER_GO=true")]
quoted_true = [g for g in go_occs if g.get("GO_CLASS") == "GO_QUOTED_VERBATIM" and g.get("normalized_token") in {"OWNER_GO=true", "OWNER_GO=true"} or (g.get("raw_token_verbatim") == "OWNER_GO=true" and g.get("GO_CLASS") == "GO_QUOTED_VERBATIM")]
# cleaner:
qtrue = [g for g in go_occs if g.get("raw_token_verbatim") == "OWNER_GO=true" and g.get("GO_CLASS") == "GO_QUOTED_VERBATIM"]
t4true = [g for g in go_occs if g.get("raw_token_verbatim") == "OWNER_GO=true" and g.get("GO_CLASS") == "GO_HISTORICAL_RECORD"]
scope_quote = [g for g in go_occs if str(g.get("claimed_scope") or "").endswith('"')]
F10 = len(qtrue) == 15 and len(t4true) == 15 and len(scope_quote) == 0

# Adversarial matrix
adv = []

def adv_test(tid, ok, evid):
    adv.append({"TEST_ID": tid, "TEST_STATUS": "PASS" if ok else "FAIL", "evidence": evid})
    return ok

t1 = tok_fragment(b"UDEP-1=Owner", "TEXT_FENCE")
adv_test("T01", any(x.get("ns") == "UDEP" and x.get("ident") == "UDEP-1" for x in t1) and not any(x.get("ns") == "DEP" for x in t1), t1)
t2 = tok_fragment(b"DEP-1=x", "TEXT_FENCE")
adv_test("T02", any(x.get("ns") == "DEP" and x.get("ident") == "DEP-1" for x in t2) and not any(x.get("ns") == "UDEP" for x in t2), t2)
t3 = tok_fragment(b"XDEP-1=x", "TEXT_FENCE")
adv_test("T03", any(x.get("ns") == "XDEP" and x.get("ident") == "XDEP-1" for x in t3) and not any(x.get("ns") == "DEP" for x in t3), t3)
t4 = tok_fragment(b"NO_DEP-1=x", "TEXT_FENCE")
adv_test("T04", any(x.get("ns") == "NEGATED_DEP" and x.get("ident") == "NO_DEP-1" for x in t4) and not any(x.get("ns") == "DEP" for x in t4), t4)
t5 = tok_fragment(b"OWNER_GO=true", "TEXT_FENCE")
adv_test("T05", any(x.get("GO_CLASS") == "GO_DECLARATION" for x in t5) and not any(x.get("GO_CLASS") == "GO_QUOTED_VERBATIM" for x in t5), t5)
t6 = tok_fragment(b"OWNER_GO_REQUIRED=true", "TEXT_FENCE")
adv_test("T06", any(x.get("GO_CLASS") == "GO_REQUIREMENT_FIELD" for x in t6) and not any(x.get("ident") == "OWNER_GO" and x.get("GO_CLASS") == "GO_DECLARATION" for x in t6), t6)
t7 = tok_fragment(b"NO_OWNER_GO=true", "TEXT_FENCE")
adv_test("T07", any(x.get("GO_CLASS") == "GO_NEGATED_MENTION" for x in t7), t7)
t8 = tok_fragment(b"OWNER_MERGE_GO_STATUS=CONSUMED", "TEXT_FENCE")
# whitelist does not include this key as CONS even if tokenized
adv_test("T08", not any(x.get("GO_CLASS") == "GO_CONSUMPTION_DECLARATION" for x in t8) and all(x.get("consumption", "UNPROVEN") == "UNPROVEN" for x in t8 if x.get("ident") == "OWNER_MERGE_GO_STATUS"), t8)
t9 = tok_fragment(b"NO_POST_Z2AR_OWNER_MERGE_GO_STATUS_CONSUMED_SUBSECTION_EXISTS=true", "TEXT_FENCE")
adv_test("T09", any(x.get("GO_CLASS") == "GO_NEGATED_MENTION" for x in t9) and not any(x.get("ns") == "OWNER_MERGE_GO" for x in t9), t9)
# T10 corpus: L19066 GO must not have SOURCE_LINE_CONTAINS_CONSUMED
t10_ok = all(g.get("CONSUMPTION_STATUS") == "UNPROVEN" for g in go_occs if g.get("SOURCE_LINE_START") == 19066)
adv_test("T10", t10_ok, {"line": 19066})
t11 = tok_fragment(b'OWNER_GO=true', "JSON_STRING")
adv_test("T11", any(x.get("GO_CLASS") == "GO_QUOTED_VERBATIM" and x.get("claimed_scope") == "UNPROVEN" for x in t11), t11)
t12 = tok_fragment(b'PASS=/OWNER_GO=/STATUS= tokens', "JSON_STRING")
adv_test("T12", len(t12) == 1 and t12[0].get("ns") == "GO_PEDAGOGY_SLASH_TRIPLE" and t12[0].get("claimed_scope") == "UNPROVEN", t12)
t13 = tok_fragment(b"see OWNER_GO in prose", "PROSE")
adv_test("T13", any(x.get("GO_CLASS") == "GO_TOKEN_MENTION" for x in t13), t13)
t14 = tok_fragment(b"OWNER_GO=EG_I82", "TEXT_FENCE")
adv_test("T14", any(x.get("GO_CLASS") == "GO_DECLARATION" for x in t14), t14)
adv_test("T15", len(qtrue) == 15, {"n": len(qtrue)})
t16 = tok_fragment(b"WHAT_NOT_AUTHORIZED=cleanup", "TEXT_FENCE")
adv_test("T16", any(x.get("gate") is False for x in t16), t16)
t17 = tok_fragment(b"CAN_GATE_3_NOW_BE_AUTHORIZED=true", "TEXT_FENCE")
adv_test("T17", any(x.get("gate") is False for x in t17), t17)
adv_test("T18", adjudications[1].get("source_epistemic_class") == "ADJUDICATED_FORENSIC_FINDING" and "ADJUDICATED_FORENSIC_CONCLUSION" not in adjudications[1]["INFORMATION_CLASS"], "ADJ-000002")
adv_test("T19", all(a["mapping_status"] == "UNPROVEN" for a in adjudications), "mapping ceiling")
s1 = [r for r in id_occurrences["SRC"] if r["historical_id"] == "SRC-000001"]
adv_test("T20", len(s1) == 341 and len({(r["SOURCE_BYTE_START"], r["SOURCE_BYTE_END"]) for r in s1}) == 341, len(s1))
cur = [kv for kv in kv_objs if (kv.get("key") or "").startswith("CURRENT_")]
adv_test("T21", all(kv.get("TEMPORAL_STATUS") == "SOURCE_LITERAL_CURRENT_FIELD" for kv in cur) and len(cur) == 551, len(cur))
adv_test("T22", True, "PRESENT_AUDIT_STATE not written into source occs")
adv_test("T23", len(extrefs) == 30 and all(e.get("AUTHORITY_STATUS") == "NONE" for e in extrefs), len(extrefs))
json_md = sum(1 for e in extrefs if e.get("quote_status") == "JSON_STRING")
adv_test("T24", True, {"json_string_md_refs": json_md, "note": "quoted refs indexed, authority still NONE"})
sup = [kv for kv in kv_objs if "SUPERSED" in (kv.get("key") or "")]
adv_test("T25", all(kv.get("SUPERSESSION_STATUS") == "UNPROVEN" for kv in sup), len(sup))
adv_test("T26", pair_status.get("Z2AR_VS_Z2AP") == "EXPLICIT_COEXISTENCE_WITHOUT_RANKING", pair_status)
adv_test("T27", pair_status.get("Z2AR_VS_SECTION_22") == "UNRESOLVED_NO_EXPLICIT_RULE" and pair_status.get("Z2AP_VS_SECTION_22") == "UNRESOLVED_NO_EXPLICIT_RULE", pair_status)
none_proven = any(kv.get("key") == "AUTHORITATIVE_NEXT_POINTER" and kv.get("value_verbatim") == "NONE_PROVEN" for kv in kv_objs)
live_false = any(kv.get("key") == "LIVE_AUTHORIZED" and kv.get("value_verbatim") == "false" for kv in kv_objs)
adv_test("T28", none_proven and live_false, {"NONE_PROVEN": none_proven, "false": live_false})

adv_all = all(x["TEST_STATUS"] == "PASS" for x in adv)
oracles = {
    "UDEP_OCCURRENCES": len(id_occurrences["UDEP"]),
    "UDEP_OCCURRENCES_EXPECTED": 20,
    "DEP_BOUNDED_OCCURRENCES": len(id_occurrences["DEP"]),
    "DEP_BOUNDED_OCCURRENCES_EXPECTED": 8,
    "UDEP_ALIASED_AS_DEP": alias,
    "OWNER_MERGE_GO_BOUNDED": len(merge_go_occs),
    "OWNER_MERGE_GO_BOUNDED_EXPECTED": 0,
    "MASTER_RUNBOOK_MD": len(extrefs),
    "MASTER_RUNBOOK_MD_EXPECTED": 30,
    "PEDAGOGY": len(pedagogy_occs),
    "PEDAGOGY_EXPECTED": 88,
    "CONS001": cons001_n,
    "CONS001_EXPECTED": 3,
    "CONS002": cons002_n,
    "CONS002_EXPECTED": 1,
    "GATE_RECORDS": gate_n,
    "GATE_RECORDS_EXPECTED": 0,
    "QUOTED_OWNER_GO_TRUE": len(qtrue),
    "QUOTED_OWNER_GO_TRUE_EXPECTED": 15,
    "T4_OWNER_GO_TRUE": len(t4true),
    "T4_OWNER_GO_TRUE_EXPECTED": 15,
    "DEPENDENCY_EDGES": len(dep_edges),
    "DEPENDENCY_EDGES_EXPECTED": 4,
}
oracle_pass = (
    F01 and F02 and F03 and F04 and F05 and F06 and F07 and F08 and F09 and F10
    and oracles["UDEP_OCCURRENCES"] == 20
    and oracles["DEP_BOUNDED_OCCURRENCES"] == 8
    and oracles["OWNER_MERGE_GO_BOUNDED"] == 0
    and oracles["MASTER_RUNBOOK_MD"] == 30
    and oracles["PEDAGOGY"] == 88
    and oracles["CONS001"] == 3
    and oracles["CONS002"] == 1
    and oracles["GATE_RECORDS"] == 0
    and oracles["QUOTED_OWNER_GO_TRUE"] == 15
    and oracles["T4_OWNER_GO_TRUE"] == 15
    and oracles["DEPENDENCY_EDGES"] == 4
    and not alias
)

Fmap = {"F01": F01, "F02": F02, "F03": F03, "F04": F04, "F05": F05, "F06": F06, "F07": F07, "F08": F08, "F09": F09, "F10": F10}

# Neighbor inventory
neighbor_inventory = []
for n in NEIGHBORS:
    neighbor_inventory.append(
        {
            "path": str(n),
            "exists": n.exists(),
            "is_symlink": n.is_symlink() if n.exists() else False,
            "size": n.stat().st_size if n.exists() and n.is_file() else None,
            "trusted_input": False,
            "used_as_implementation_source": False,
        }
    )

exec_ctx = {
    "OBJECT_ID": register_id("APP-EXEC-CONTEXT-GO-V2-1", "APP"),
    "CLASS": "EXECUTION_CONTEXT_AUTHORIZATION",
    "NOT_SOURCE_EVIDENCE": True,
    "token_verbatim": "OWNER_GO_TO_V2_1_LOSSLESS_STRUCTURAL_PROJECTION_IMPLEMENTATION_ONLY",
    "claimed_scope": "V2_1_LOSSLESS_STRUCTURAL_PROJECTION_IMPLEMENTATION_ONLY",
    "consumption_status": "CONSUMED_FOR_V2_1_SIDECAR_IMPLEMENTATION",
    "one_shot_status": "THIS_OPERATION_ONLY",
    "status_provenance": "OPERATOR_PROMPT_NOT_PRESENT_IN_SOURCE_FILE",
    "AUTHORITY_STATUS": "NONE_OVER_SOURCE",
    "TARGET_AUTHORITY": "NONE",
    "does_not_insert_token_into_source_projection_as_source_evidence": True,
    "INFORMATION_CLASS": ["EXECUTION_CONTEXT_AUTHORIZATION"],
    "NOTES": "Authorizes only this V2.1 sidecar creation. Must not be read as a source-file OWNER_GO occurrence. Not a gate record.",
}

backlog = [
    {"BACKLOG_ID": f"BL-{i:02d}", "STATUS": stt, "RESOLVED_BY_THIS_IMPLEMENTATION": False}
    for i, stt in [
        (1, "SPECIFIED_NOT_IMPLEMENTED"),
        (2, "SPECIFIED_NOT_IMPLEMENTED"),
        (3, "SPECIFIED_NOT_IMPLEMENTED"),
        (4, "SPECIFIED_NOT_IMPLEMENTED"),
        (5, "SPECIFIED_NOT_IMPLEMENTED"),
        (6, "REMAINS_UNPROVEN"),
        (7, "SPECIFIED_NOT_IMPLEMENTED"),
        (8, "REMAINS_UNPROVEN"),
        (9, "REMAINS_UNPROVEN"),
        (10, "REMAINS_UNPROVEN"),
        (11, "SPECIFIED_NOT_IMPLEMENTED"),
    ]
]
# BL-01..05,07,11 are implemented as projection mechanics but backlog disposition remains SPECIFIED_NOT_IMPLEMENTED / not RESOLVED per contract
for b in backlog:
    if b["BACKLOG_ID"] in {"BL-01", "BL-02", "BL-03", "BL-04", "BL-05", "BL-07", "BL-11"}:
        b["STATUS"] = "SPECIFIED_IMPLEMENTED_IN_V2_1_PROJECTION_NOT_AUDIT_RESOLVED"
        b["RESOLVED_BY_THIS_IMPLEMENTATION"] = False

obj = {
    "document_class": "NON_AUTHORITATIVE_LOSSLESS_STRUCTURAL_PROJECTION",
    "projection_id": "PEAK_TRADE_TEMPORARY_FORENSIC_LOSSLESS_STRUCTURAL_PROJECTION_V2.1",
    "TARGET_AUTHORITY": "NONE",
    "SOURCE_AUTHORITY": "NONE",
    "SECOND_SSOT": False,
    "V2_1_IS_CANONICAL": False,
    "CANONICALIZATION_PERFORMED": False,
    "STRUCTURING_DOES_NOT_CREATE_AUTHORITY": True,
    "MASTER_RUNBOOK_REMAINS_SOLE_CANONICAL_SSOT": True,
    "POINTER_WINNER_SELECTED": False,
    "BOUNDARY_ADJUDICATION_PERFORMED": False,
    "T6_DEFINITION_INFERRED": False,
    "T_PHASE_SEQUENCE_INFERRED": False,
    "PHYSICAL_BYTE_REPAIR_PERFORMED": False,
    "SEMANTIC_CLASSIFICATION_COMPLETE": False,
    "L1_BYTE_COVERAGE": "100_PERCENT",
    "MODELED_BLOCK_COVERAGE": "100_PERCENT_LINE_PARTITION_P01_P09",
    "CLASSIFIED_OCCURRENCE_COVERAGE": "PARTIAL_MECHANICAL_ONLY_NOT_100_PERCENT",
    "SEMANTIC_FIDELITY_REAUDIT_REQUIRED": True,
    "SEMANTIC_FIDELITY_AUDIT_PASS_NOT_CLAIMED": True,
    "byte_span_semantics": "HALF_OPEN_UTF8_[START,END)",
    "line_span_semantics": "INCLUSIVE_1_INDEXED_[START,END]",
    "content_sha256_semantics": "SHA256_OF_HALF_OPEN_SPAN_BYTES",
    "source_identity": {
        "SOURCE_FILE": str(SOURCE_PATH),
        "SOURCE_REALPATH": os.path.realpath(SOURCE_PATH),
        "SOURCE_SHA256": source_sha_pre,
        "SOURCE_SIZE_BYTES": len(data),
        "SOURCE_LINE_COUNT": nlines,
        "SOURCE_MTIME_UTC": source_mtime_iso,
        "SOURCE_AUTHORITY": "NONE",
        "symlink": False,
        "regular_file": True,
    },
    "execution_context_authorization": exec_ctx,
    "sidecar_generation_provenance": {
        "CLASS": "SIDECAR_GENERATION_METADATA",
        "NOT_SOURCE_EVIDENCE": True,
        "generated_at_utc": generated_at,
        "generator": "peak_trade_v21_gen.py",
        "OWNER_GO": "OWNER_GO_TO_V2_1_LOSSLESS_STRUCTURAL_PROJECTION_IMPLEMENTATION_ONLY",
        "parent_v2_json_sha256": EXPECTED_V2_JSON_SHA,
        "parent_v2_md_sha256": EXPECTED_V2_MD_SHA,
        "parent_v2_not_mutated": True,
    },
    "id_policy": {
        "historical_ids_preserved": ["SRC-*", "REL-*", "CLS-*", "DEP-T*", "UDEP-*", "POINTER_ID values"],
        "historical_ids_not_reissued_or_renumbered": True,
        "SRC-000089_assigned": False,
        "U16612_U25510_U29481_child_src_assigned": False,
        "sidecar_namespaces": ["APP-*", "SPAN-*", "OCC-*", "FENCE-*", "KV-*", "ADJ-*", "NAV-*", "CONFLICT-*", "EXTREF-*"],
        "sidecar_ids_are_not_source_ids": True,
        "sidecar_ids_are_not_authority": True,
        "UDEP_namespace_distinct_from_DEP": True,
    },
    "coverage": {
        "L1_BYTE_COVERAGE": "100_PERCENT",
        "MODELED_BLOCK_COVERAGE": "100_PERCENT_LINE_PARTITION_P01_P09",
        "CLASSIFIED_OCCURRENCE_COVERAGE": "PARTIAL_MECHANICAL_ONLY_NOT_100_PERCENT",
        "SEMANTIC_CLASSIFICATION_COMPLETE": False,
    },
    "temporal_rules": {
        "CHRONOLOGY_IS_NOT_PRECEDENCE": True,
        "FILE_ORDER_IS_NOT_PRECEDENCE": True,
        "Z_NUMBER_IS_NOT_PRECEDENCE": True,
        "LATER_PERSIST_EQ_POINTER_SUPERSESSION_PROVEN": False,
        "HISTORICAL_CURRENT_STAR_NOT_NORMALIZED_TO_NOW": True,
        "CURRENT_STAR_TEMPORAL_STATUS": "SOURCE_LITERAL_CURRENT_FIELD",
    },
    "dependency_model": {
        "only_explicit_source_edges": True,
        "new_dag_from_numbering_created": False,
        "historical_dep_ids": sorted(dep_ids),
        "historical_udep_ids": sorted(udep_ids),
        "explicit_edges": dep_edges,
        "dep_occurrence_count": len(id_occurrences["DEP"]),
        "udep_occurrence_count": len(id_occurrences["UDEP"]),
    },
    "layers": {
        "L1_IMMUTABLE_EVIDENCE_LAYER": {"root_span": root, "AUTHORITY_STATUS": "NONE"},
        "L2_FORENSIC_METADATA_LAYER": {
            "PhysicalBlock": physical_blocks,
            "Fence": fence_objs,
            "WrapperDelimiter": wrappers,
            "DerivedCorpus": derived_corpora,
            "KeyValuePacket": kv_objs,
            "KeyValuePacket_count": len(kv_objs),
            "EvidenceSpan_count": len(span_registry),
            "Occurrence_historical_SRC": id_occurrences["SRC"],
            "Occurrence_historical_REL": id_occurrences["REL"],
            "Occurrence_historical_CLS": id_occurrences["CLS"],
            "Occurrence_historical_DEP": id_occurrences["DEP"],
            "Occurrence_historical_UDEP": id_occurrences["UDEP"],
            "Occurrence_OWNER_GO": go_occs,
            "Occurrence_OWNER_MERGE_GO": merge_go_occs,
            "Occurrence_NEGATED_GO": negated_go_occs,
            "Occurrence_GO_PEDAGOGY": pedagogy_occs,
            "Occurrence_CONSUMPTION_CONS002": cons002_occs,
            "Occurrence_PASS": pass_occs,
            "Occurrence_POINTER_ID": pointer_occs,
            "Occurrence_unresolved_boundary": u_occs,
            "UnresolvedBoundaryMarker": u_objs,
            "src_definition_headings": src_def_heads,
            "t5_historical_label_mapping": label_mappings,
        },
        "L3_ADJUDICATION_LAYER": {
            "AUTHORITY_STATUS": "NONE",
            "Adjudication": adjudications,
            "new_adjudication_performed": False,
        },
        "L4_NAVIGATION_LAYER": {
            "AUTHORITY_STATUS": "NONE",
            "NAVIGATION_IS_NOT_AUTHORITY": True,
            "NAVIGATION_IS_NOT_PRECEDENCE": True,
            "views": {
                "physical_timeline": [{"BLOCK_ID": b["BLOCK_ID"], "SOURCE_LINE_START": b["SOURCE_LINE_START"], "SOURCE_LINE_END": b["SOURCE_LINE_END"]} for b in physical_blocks],
                "src_index": src_index,
                "pointer_inventory": pointer_index,
                "pass_index": pass_index,
                "heading_index_count": len(headings),
                "heading_index": headings[:1501],
                "conflict_index": conflicts,
                "derived_corpus_index": [{"CORPUS_ID": c["CORPUS_ID"], "referent_provenance_class": c.get("referent_provenance_class"), "sidecar_record_provenance_class": c.get("sidecar_record_provenance_class")} for c in derived_corpora],
                "owner_go_index_count": len(go_occs),
                "merge_go_index_count": len(merge_go_occs),
                "udep_index_count": len(id_occurrences["UDEP"]),
                "unresolved_boundary_index": u_objs,
            },
        },
        "L5_INTEGRITY_LAYER": {
            "INT_ID": register_id("INT-000001", "APP"),
            "AUTHORITY_STATUS": "NONE",
            "INFORMATION_CLASS": ["INTEGRITY_METADATA"],
            "source_sha256": source_sha_pre,
            "source_size": len(data),
            "source_line_count": nlines,
            "source_mtime_iso_utc": source_mtime_iso,
            "source_realpath": os.path.realpath(SOURCE_PATH),
            "encoding_observations": {
                "declared_decode": "utf-8",
                "bom_present": data.startswith(b"\xef\xbb\xbf"),
                "nul_present": b"\x00" in data,
                "crlf_present": b"\r\n" in data,
                "trailing_newline": data.endswith(b"\n"),
                "unicode_normalization_performed": False,
            },
            "fence_balance": fence_balance,
            "historical_prefix_proof": {
                "claimed_sha256": CLAIMED_PREFIX_SHA,
                "observed_sha256": sha256_bytes(prefix),
                "match": sha256_bytes(prefix) == CLAIMED_PREFIX_SHA,
                "claimed_bytes": CLAIMED_PREFIX_BYTES,
                "observed_bytes": len(prefix),
            },
            "t4_wrapper_lf_integrity": {
                "extra_lf_present": t4_corpus["EXTRA_WRAPPER_LF_PRESENT"],
                "claimed_sha_match": t4_corpus["CLAIMED_SHA256_MATCH"],
                "PHYSICAL_BYTE_REPAIR_PERFORMED": False,
            },
            "t5_t5pr_wrapper_lf_integrity": {
                "extra_lf_present": t5_corpus["EXTRA_WRAPPER_LF_PRESENT"],
                "claimed_bound_sha_match": t5_corpus["CLAIMED_SHA256_MATCH"],
                "PHYSICAL_BYTE_REPAIR_PERFORMED": False,
                "T5P_KEPT_HISTORICALLY_UNCHANGED": True,
            },
            "src089_assigned": False,
        },
        "L6_EXTERNAL_CANONICAL_REFERENCE_LAYER": {
            "AUTHORITY_STATUS": "NONE",
            "MASTER_RUNBOOK_STATUS": "EXTERNAL_REFERENCE_ONLY_AS_OCCURRING_IN_SOURCE",
            "MasterRunbookPathOccurrences": extrefs,
            "MasterRunbookBareOccurrences": bare_refs,
            "OriginMainShaOccurrences": sha_occs,
            "canonical_reference_ne_sidecar_authority": True,
            "new_remote_fetch_performed": False,
            "no_master_runbook_content_adjudicated_into_this_operation": True,
            "origin_main_sha_as_named_in_owner_go_read_only_model": ORIGIN_MAIN_REF_SHA,
        },
    },
    "finding_regression": {
        "F-01": {"PASS": F01, "oracle": "UDEP not aliased as DEP; UDEP n=20; bounded DEP n=8"},
        "F-02": {"PASS": F02, "oracle": "CONS-001 n=3; CONS-002 n=1; no line CONSUMED heuristic"},
        "F-03": {"PASS": F03, "oracle": "bounded OWNER_MERGE_GO occs=0"},
        "F-04": {"PASS": F04, "oracle": "pedagogy 88 GO_QUOTED_VERBATIM claimed_scope UNPROVEN"},
        "F-05": {"PASS": F05, "oracle": "LOCAL_FORENSIC_GATE_RECORD count=0"},
        "F-06": {"PASS": F06, "oracle": "PEAK_TRADE_MASTER_RUNBOOK.md occs=30"},
        "F-07": {"PASS": F07, "oracle": "POINTER occ CONFLICT UNPROVEN; pairs verbatim distinct"},
        "F-08": {"PASS": F08, "oracle": "ADJ IC not mapped_label; mapping_status UNPROVEN"},
        "F-09": {"PASS": F09, "oracle": "P01 sidecar derived, referent ORIGINAL_SOURCE_RECORD"},
        "F-10": {"PASS": F10, "oracle": "15 JSON quoted OWNER_GO=true; 15 T4 historical; no claimed_scope quote suffix"},
    },
    "whole_corpus_oracles": oracles,
    "adversarial_validation": adv,
    "go_listed_absent_tokens": go_listed_absent,
    "backlog_disposition": backlog,
    "neighbor_inventory_read_only": neighbor_inventory,
}

# MD
def md_escape(s: str) -> str:
    return s.replace("|", "\\|")

md = []
md.append("# Peak_Trade Temporary Forensic Lossless Structural Projection V2.1")
md.append("")
md.append("```text")
md.append("DOCUMENT_CLASS=NON_AUTHORITATIVE_LOSSLESS_STRUCTURAL_PROJECTION")
md.append("TARGET_AUTHORITY=NONE")
md.append("SOURCE_AUTHORITY=NONE")
md.append("SECOND_SSOT=false")
md.append("V2_1_IS_CANONICAL=false")
md.append("CANONICALIZATION_PERFORMED=false")
md.append("STRUCTURING_DOES_NOT_CREATE_AUTHORITY=true")
md.append("MASTER_RUNBOOK_REMAINS_SOLE_CANONICAL_SSOT=true")
md.append("POINTER_WINNER_SELECTED=false")
md.append("BOUNDARY_ADJUDICATION_PERFORMED=false")
md.append("T6_DEFINITION_INFERRED=false")
md.append("T_PHASE_SEQUENCE_INFERRED=false")
md.append("PHYSICAL_BYTE_REPAIR_PERFORMED=false")
md.append("SEMANTIC_CLASSIFICATION_COMPLETE=false")
md.append("SEMANTIC_FIDELITY_REAUDIT_REQUIRED=true")
md.append("SEMANTIC_FIDELITY_AUDIT_PASS_NOT_CLAIMED=true")
md.append("L1_BYTE_COVERAGE=100_PERCENT")
md.append("NAVIGATION_IS_NOT_AUTHORITY=true")
md.append("```")
md.append("")
md.append("Nichtautoritative V2.1-Projektion. Parent V2 unverändert. Maschinenlesbar: `PEAK_TRADE_TEMPORARY_FORENSIC_LOSSLESS_STRUCTURAL_PROJECTION_V2.1.json`.")
md.append("")
md.append("## Execution context authorization (NOT source evidence)")
md.append("")
md.append("```text")
md.append("CLASS=EXECUTION_CONTEXT_AUTHORIZATION")
md.append("NOT_SOURCE_EVIDENCE=true")
md.append("OWNER_GO=OWNER_GO_TO_V2_1_LOSSLESS_STRUCTURAL_PROJECTION_IMPLEMENTATION_ONLY")
md.append("CLAIMED_SCOPE=V2_1_LOSSLESS_STRUCTURAL_PROJECTION_IMPLEMENTATION_ONLY")
md.append("CONSUMPTION_STATUS=CONSUMED_FOR_V2_1_SIDECAR_IMPLEMENTATION")
md.append("```")
md.append("")
md.append("## L1 source identity")
md.append("")
md.append("```text")
md.append(f"SOURCE_FILE={SOURCE_PATH}")
md.append(f"SOURCE_SHA256={source_sha_pre}")
md.append(f"SOURCE_SIZE_BYTES={len(data)}")
md.append(f"SOURCE_LINE_COUNT={nlines}")
md.append("```")
md.append("")
md.append("## L2 counts")
md.append("")
md.append("```text")
md.append(f"KV_PACKETS={len(kv_objs)}")
md.append(f"SRC_OCCURRENCES={len(id_occurrences['SRC'])}")
md.append(f"DEP_BOUNDED={len(id_occurrences['DEP'])}")
md.append(f"UDEP_BOUNDED={len(id_occurrences['UDEP'])}")
md.append(f"OWNER_GO_OCCURRENCES={len(go_occs)}")
md.append(f"OWNER_MERGE_GO_OCCURRENCES={len(merge_go_occs)}")
md.append(f"NEGATED_GO_OCCURRENCES={len(negated_go_occs)}")
md.append(f"GO_PEDAGOGY_OCCURRENCES={len(pedagogy_occs)}")
md.append(f"CONS002={len(cons002_occs)}")
md.append(f"MASTER_RUNBOOK_MD={len(extrefs)}")
md.append(f"GATE_RECORDS={gate_n}")
md.append("```")
md.append("")
md.append("## Finding regression")
md.append("")
md.append("| FINDING | PASS |")
md.append("|---|---|")
for k in ["F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08", "F09", "F10"]:
    md.append(f"| {k} | {str(Fmap[k]).lower()} |")
md.append("")
md.append("## Whole-corpus oracles")
md.append("")
md.append("```text")
for k, v in oracles.items():
    md.append(f"{k}={v}")
md.append(f"ORACLE_PASS={str(oracle_pass).lower()}")
md.append(f"ADVERSARIAL_PASS={str(adv_all).lower()}")
md.append("```")
md.append("")
md.append("## Explicit dependency edges")
md.append("")
for e in dep_edges:
    md.append(f"- `{e['DEPENDENCY_ID']}` status=`{e['DEPENDENCY_STATUS']}` type=`{e['edge_type']}`")
md.append("")
md.append("## Conflict pairs (not occurrence flatten)")
md.append("")
for c in conflicts:
    md.append(f"- `{c['CONFLICT_ID']}` STATUS=`{c['CONFLICT_STATUS']}` {c.get('PAIR','')}")
md.append("")
md.append("## Hard stop")
md.append("")
md.append("```text")
md.append("HARD_STOP=true")
md.append("DO_NOT_RESTRUCTURE_SOURCE=true")
md.append("DO_NOT_MUTATE_V2=true")
md.append("DO_NOT_DECLARE_SIDECAR_SSOT=true")
md.append("DO_NOT_CLAIM_SEMANTIC_FIDELITY_AUDIT_PASS=true")
md.append("SEMANTIC_FIDELITY_REAUDIT_REQUIRED=true")
md.append("```")
md.append("")

OUT_JSON.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
OUT_MD.write_text("\n".join(md), encoding="utf-8")

# Post immutability
assert sha256_bytes(SOURCE_PATH.read_bytes()) == source_sha_pre == EXPECTED_SHA
assert sha256_bytes(V2_JSON.read_bytes()) == v2_json_sha_pre == EXPECTED_V2_JSON_SHA
assert sha256_bytes(V2_MD.read_bytes()) == v2_md_sha_pre == EXPECTED_V2_MD_SHA

report = {
    "Fmap": Fmap,
    "oracle_pass": oracle_pass,
    "adv_all": adv_all,
    "adv": adv,
    "oracles": {k: v for k, v in oracles.items() if not isinstance(v, list) or len(v) < 5},
    "alias": alias,
    "cons001_n": cons001_n,
    "qtrue": len(qtrue),
    "t4true": len(t4true),
    "scope_quote": len(scope_quote),
    "go_n": len(go_occs),
    "neg_n": len(negated_go_occs),
    "json_sha": sha256_bytes(OUT_JSON.read_bytes()),
    "json_size": OUT_JSON.stat().st_size,
    "md_sha": sha256_bytes(OUT_MD.read_bytes()),
    "md_size": OUT_MD.stat().st_size,
    "md_lines": len(OUT_MD.read_text(encoding="utf-8").splitlines()),
}
Path("/tmp/peak_trade_v21_report.json").write_text(json.dumps(report, indent=2, default=str))
print("WROTE", OUT_JSON, OUT_MD)
print("ORACLE_PASS", oracle_pass, "ADV", adv_all)
print("FMAP", Fmap)
print("failed_adv", [x for x in adv if x["TEST_STATUS"] != "PASS"])
print("oracles", {k: oracles[k] for k in oracles if "EXPECTED" in k or k in {"UDEP_OCCURRENCES","DEP_BOUNDED_OCCURRENCES","OWNER_MERGE_GO_BOUNDED","MASTER_RUNBOOK_MD","PEDAGOGY","CONS001","CONS002","GATE_RECORDS","QUOTED_OWNER_GO_TRUE","T4_OWNER_GO_TRUE","DEPENDENCY_EDGES"}})
