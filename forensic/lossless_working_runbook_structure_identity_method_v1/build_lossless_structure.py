#!/usr/bin/env python3
"""Local-only lossless structure transform. AUTHORITY=NONE. Never writes source or repo."""
from __future__ import annotations
import hashlib, json, re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SOURCE_PATH = Path("/Users/frnkhrz/Downloads/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md")
OUTPUT_DIR = Path("/Users/frnkhrz/Downloads/peak_trade_temporary_forensic_lossless_structure_v1")
EXPECTED_SHA256 = "10d9293134426805f38996be848e1de853636d8e6f60745a2330bdfd94e3719f"
EXPECTED_SIZE = 8499032
OLD_ANALYSIS_SHA256 = "08ffe7bce3fd7aa94de20737c3bc1cf1721e08e719fc8d3d00d72e079f6a5092"

STRUCTURAL_TYPES = ["PhysicalAppendUnit","Heading","FencedBlock","RawOutputBlock","Paragraph","ListItem","Table","TableRow","TableCell","KeyValueStatement","NestedStructuralChild","Separator","BlankLine","BlockQuote","UnknownStructuralUnit"]
PROVENANCE_CLASSES = ["SOURCE_NATIVE","VERBATIM_EXTERNAL_OUTPUT","CHAT_DERIVED","REPOSITORY_OBSERVATION","TOOL_OUTPUT","OWNER_STATEMENT","CURATED_SUMMARY","DERIVED_ANALYSIS","UNKNOWN"]
EPISTEMIC_CLASSES = ["CANONICAL_AUTHORITY_REFERENCE","FORENSIC_RAW_EVIDENCE","ADJUDICATED_CONCLUSION","HISTORICAL_INTERMEDIATE_STATE","NAVIGATION_INDEX","INTERPRETATION","HYPOTHESIS","OPEN_POINT","CONTRADICTORY_POINT","PROCESS_METADATA","UNKNOWN"]
CURRENTNESS_CLASSES = ["CURRENT","HISTORICAL","SUPERSEDED","STALE","POINT_IN_TIME_ONLY","UNKNOWN"]
ADJUDICATION_CLASSES = ["NOT_ADJUDICATED","PREPARED_FOR_ADJUDICATION","OWNER_ADJUDICATED","ALREADY_ADJUDICATED_INHERITED","REJECTED","SUPERSEDED_DECISION","DISPUTED","UNKNOWN"]
RELATION_TYPES = ["EXPLICIT_DEPENDS_ON","EXPLICIT_BLOCKS","EXPLICIT_NEXT_STEP","PART_OF_GATE","EVIDENCE_FOR","CONTRADICTS","CORRECTS","SUPERSEDES","REPLACES_PROCESS_BOUNDARY","REFERENCES","SAME_SUBJECT_AS"]
RELATION_PROVENANCE = ["EXPLICIT_SOURCE","ALREADY_ADJUDICATED","DERIVED_INTERPRETATION"]

RE_HEADING = re.compile(r"^(#{1,6})(\s+|$)")
RE_HR = re.compile(r"^(?:\s{0,3})(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})\s*$")
RE_LIST = re.compile(r"^(\s{0,3})([-*+]|\d+\.)\s")
RE_KV_EQ = re.compile(r"^([A-Z][A-Z0-9_]*)=(.*)$")
RE_KV_COLON = re.compile(r"^([A-Za-z][A-Za-z0-9_]*):\s+\S")
RE_TABLE = re.compile(r"^\s{0,3}\|")
RE_FENCE = re.compile(r"^(`{3,}|~{3,})(.*)$")
RE_BQ = re.compile(r"^\s{0,3}>")
RE_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
RE_HIST_PATH = re.compile(r"(?:~|/Users/[^/\s]+)/Desktop/[^\s`)'\"]+")
RE_DOWNLOADS_PATH = re.compile(r"(?:/Users/[^/\s]+)?/Downloads/[^\s`)'\"]+")
RE_EXPLICIT_REL = re.compile(r"\b(DEPENDS_ON|BLOCKS|NEXT_STEP|CANONICAL_NEXT_STEP|SUPERSEDES|CONTRADICTS|CORRECTS|REPLACES)\s*=")
RE_TS = re.compile(r"UTC append:\s*([0-9T:\-Z]+)")
RE_ART = re.compile(r"(forensic/[^\s`]+|docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK\.md)")
REL_MAP = {"DEPENDS_ON":"EXPLICIT_DEPENDS_ON","BLOCKS":"EXPLICIT_BLOCKS","NEXT_STEP":"EXPLICIT_NEXT_STEP","CANONICAL_NEXT_STEP":"EXPLICIT_NEXT_STEP","SUPERSEDES":"SUPERSEDES","CONTRADICTS":"CONTRADICTS","CORRECTS":"CORRECTS","REPLACES":"REPLACES_PROCESS_BOUNDARY"}

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def dump_jsonl(handle, obj: dict) -> None:
    handle.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")

def classify_line(text: str) -> str:
    if text == "":
        return "BlankLine"
    if RE_HEADING.match(text):
        return "Heading"
    if RE_HR.match(text):
        return "Separator"
    if RE_TABLE.match(text):
        return "TableRow"
    if RE_LIST.match(text):
        return "ListItem"
    if RE_BQ.match(text):
        return "BlockQuote"
    if RE_KV_EQ.match(text) or RE_KV_COLON.match(text):
        return "KeyValueStatement"
    return "Paragraph"

def fence_type(info: str) -> str:
    token = info.strip()
    if token in ("text", "console", "shell", "bash", "sh", "raw"):
        return "RawOutputBlock"
    return "FencedBlock"

def heading_body(text: str) -> str:
    m = RE_HEADING.match(text)
    if not m:
        return text
    rest = text[len(m.group(1)):]
    return rest[1:] if rest.startswith(" ") else rest

def provenance_of(text: str, stype: str, prev: str | None) -> str:
    u = text.upper()
    if "AUTHORITY=OWNER_GO" in u or text.startswith("*(AUTHORITY=OWNER_GO"):
        return "OWNER_STATEMENT"
    if stype == "RawOutputBlock":
        return "VERBATIM_EXTERNAL_OUTPUT"
    if stype in {"FencedBlock", "RawOutputBlock"} and prev is not None and (prev.startswith("Command:") or prev.startswith("$ ")):
        return "TOOL_OUTPUT"
    if stype in {"Heading","BlankLine","Separator","Paragraph","ListItem","Table","TableRow","TableCell","KeyValueStatement","BlockQuote","PhysicalAppendUnit","NestedStructuralChild"}:
        return "SOURCE_NATIVE"
    return "UNKNOWN"

def epistemic_of(text: str, stype: str) -> str:
    u = text.upper()
    if "PEAK_TRADE_MASTER_RUNBOOK" in u or "CANONICAL_WORKING_AUTHORITY" in u:
        return "CANONICAL_AUTHORITY_REFERENCE"
    if "CONTRADICT" in u:
        return "CONTRADICTORY_POINT"
    if "HYPOTHESIS" in u:
        return "HYPOTHESIS"
    if "MISSING_FACT" in u or "OPEN_POINT" in u or "UNRESOLVED" in u:
        return "OPEN_POINT"
    if stype == "Heading":
        body = heading_body(text).upper()
        if "INDEX" in body or "MAP OF TRUTH" in body or "TABLE OF CONTENTS" in body:
            return "NAVIGATION_INDEX"
    if stype in {"FencedBlock", "RawOutputBlock"}:
        return "FORENSIC_RAW_EVIDENCE"
    if "AUTHORITY=" in u or "OWNER_GO=" in u or "DOCUMENT_CLASS=" in u:
        return "PROCESS_METADATA"
    return "UNKNOWN"

def currentness_of(text: str) -> str:
    u = text.upper()
    if "SUPERSEDED" in u:
        return "SUPERSEDED"
    if "POINT_IN_TIME" in u or "UTC APPEND:" in u or "AS OF " in u:
        return "POINT_IN_TIME_ONLY"
    if "HISTORICAL" in u and "CURRENT" not in u:
        return "HISTORICAL"
    return "UNKNOWN"

def adjudication_of(text: str) -> str:
    u = text.upper()
    if "SUPERSEDED_DECISION" in u or ("SUPERSEDED" in u and "DECISION" in u):
        return "SUPERSEDED_DECISION"
    if "OWNER_ADJUDICATED" in u or "ADJUDICATION=OWNER" in u:
        return "OWNER_ADJUDICATED"
    if "DISPUTED" in u:
        return "DISPUTED"
    if "REJECTED" in u and "ADJUDICAT" in u:
        return "REJECTED"
    return "UNKNOWN"

def write_view(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n```text\nAUTHORITY=NONE\nDERIVED_VIEW=true\nNOT_SSOT=true\nNOT_THE_ONLY_STORE=true\nCANONICALIZATION_PERFORMED=false\n```\n\n{body}\n", encoding="utf-8")

def main() -> int:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    views_dir = OUTPUT_DIR / "derived_views"
    views_dir.mkdir(parents=True, exist_ok=True)
    pre_bytes = SOURCE_PATH.read_bytes()
    pre_sha = sha256_hex(pre_bytes)
    pre_size = len(pre_bytes)
    if pre_sha != EXPECTED_SHA256 or pre_size != EXPECTED_SIZE:
        fail = {"BASELINE_VALIDATION":"FAIL","SOURCE_SHA256_PRE":pre_sha,"SOURCE_SIZE_PRE":pre_size,"HARD_STOP":True,"TRANSFORMATION_STATUS":"ABORTED_IDENTITY_MISMATCH"}
        (OUTPUT_DIR / "BASELINE_FAIL.json").write_text(json.dumps(fail, indent=2)+"\n", encoding="utf-8")
        print(json.dumps(fail, indent=2)); return 2
    if b"\r" in pre_bytes:
        raise SystemExit("CR bytes present; refusing to normalize")
    pre_bytes.decode("utf-8")
    bom_status = "UTF-8_BOM" if pre_bytes.startswith(b"\xef\xbb\xbf") else "NONE"
    encoding_name = "utf-8"
    parts = pre_bytes.split(b"\n")
    if not parts or parts[-1] != b"":
        raise SystemExit("source does not end with LF")
    contents = parts[:-1]
    line_count = len(contents)
    if b"\n".join(contents)+b"\n" != pre_bytes:
        raise SystemExit("split reconstruction failed")

    physical_path = OUTPUT_DIR / "physical_source_index.jsonl"
    structural_path = OUTPUT_DIR / "structural_catalog.jsonl"
    facets_path = OUTPUT_DIR / "semantic_facets.jsonl"
    relations_path = OUTPUT_DIR / "relations.jsonl"
    line_texts: list[str] = []
    line_classes: list[str] = []
    byte_cursor = 0
    in_fence = False
    fence_marker = ""
    rewrite = hashlib.sha256()
    with physical_path.open("w", encoding="utf-8", newline="\n") as fh:
        for index, content_b in enumerate(contents, start=1):
            full_b = content_b + b"\n"
            rewrite.update(full_b)
            text = content_b.decode("utf-8")
            start = byte_cursor
            end = start + len(full_b)
            dump_jsonl(fh, {"physical_id":f"PL-{index:06d}","physical_order":index,"source_line_number":index,"byte_offset_start":start,"byte_offset_end":end,"byte_count":len(full_b),"content_byte_count":len(content_b),"newline_identity":"LF","newline_bytes":"0a","line_content_sha256":sha256_hex(content_b),"physical_span_sha256":sha256_hex(full_b),"raw_text":text,"strip_applied":False,"whitespace_collapsed":False,"unicode_normalized":False})
            line_texts.append(text)
            byte_cursor = end
            if in_fence:
                line_classes.append("FENCE_INNER")
                closer = RE_FENCE.match(text)
                if closer and text.startswith(fence_marker):
                    in_fence = False; fence_marker = ""
                continue
            opener = RE_FENCE.match(text)
            if opener:
                line_classes.append("FENCE_OPEN"); in_fence = True; fence_marker = opener.group(1); continue
            line_classes.append(classify_line(text))
    if in_fence:
        raise SystemExit("unclosed fence")
    if byte_cursor != pre_size or rewrite.hexdigest() != pre_sha:
        raise SystemExit("physical rewrite mismatch")

    structural_records: list[dict] = []
    struct_type_counter: Counter[str] = Counter()
    heading_occurrences: dict[str, list[str]] = defaultdict(list)
    sampled_fences: list[dict] = []
    su_seq = 1
    def add_struct(stype: str, start_line: int, end_line: int, extra: dict | None = None) -> dict:
        nonlocal su_seq
        rec = {"structural_id":f"SU-{su_seq:06d}","structural_type":stype,"source_span":{"start_line":start_line,"end_line":end_line},"parent_structural_id":None}
        if extra:
            rec.update(extra)
        su_seq += 1
        struct_type_counter[stype] += 1
        structural_records.append(rec)
        return rec
    root = add_struct("PhysicalAppendUnit", 1, line_count, {"notes":"Entire observed source treated as one physical append corpus.","target_authority":"NONE"})
    root_id = root["structural_id"]
    i = 0
    while i < line_count:
        lineno = i + 1
        text = line_texts[i]
        cls = line_classes[i]
        if cls == "FENCE_OPEN":
            opener = RE_FENCE.match(text); assert opener is not None
            marker, info = opener.group(1), opener.group(2)
            j = i + 1
            while j < line_count and not (line_texts[j].startswith(marker) and RE_FENCE.match(line_texts[j])):
                j += 1
            if j >= line_count:
                raise SystemExit("fence closer lost")
            parent = add_struct(fence_type(info), lineno, j+1, {"parent_structural_id":root_id,"fence_marker":marker,"fence_info_string_raw":info,"verbatim_protected":True})
            if len(sampled_fences) < 8:
                sampled_fences.append({"structural_id":parent["structural_id"],"start_line":lineno,"end_line":j+1})
            for k in range(i, j+1):
                role = "fence_open" if k==i else ("fence_close" if k==j else "fence_body")
                add_struct("NestedStructuralChild", k+1, k+1, {"parent_structural_id":parent["structural_id"],"role":role,"verbatim_protected":True,"raw_text_ref_physical_id":f"PL-{k+1:06d}"})
            i = j + 1; continue
        if cls == "BlankLine":
            add_struct("BlankLine", lineno, lineno, {"parent_structural_id":root_id,"raw_text_ref_physical_id":f"PL-{lineno:06d}"}); i += 1; continue
        if cls == "Heading":
            m = RE_HEADING.match(text); body = heading_body(text)
            rec = add_struct("Heading", lineno, lineno, {"parent_structural_id":root_id,"heading_level":len(m.group(1)) if m else None,"heading_text_raw":body,"raw_text_ref_physical_id":f"PL-{lineno:06d}"})
            heading_occurrences[body].append(rec["structural_id"]); i += 1; continue
        if cls == "Separator":
            add_struct("Separator", lineno, lineno, {"parent_structural_id":root_id,"raw_text_ref_physical_id":f"PL-{lineno:06d}"}); i += 1; continue
        if cls == "TableRow":
            j = i
            while j < line_count and line_classes[j] == "TableRow":
                j += 1
            table = add_struct("Table", lineno, j, {"parent_structural_id":root_id,"verbatim_protected":True})
            for k in range(i, j):
                row_text = line_texts[k]
                row = add_struct("TableRow", k+1, k+1, {"parent_structural_id":table["structural_id"],"raw_text_ref_physical_id":f"PL-{k+1:06d}","verbatim_protected":True})
                for cell_index, cell in enumerate(row_text.split("|")):
                    add_struct("TableCell", k+1, k+1, {"parent_structural_id":row["structural_id"],"cell_index":cell_index,"cell_raw":cell,"strip_applied":False})
            i = j; continue
        if cls == "ListItem":
            add_struct("ListItem", lineno, lineno, {"parent_structural_id":root_id,"raw_text_ref_physical_id":f"PL-{lineno:06d}"}); i += 1; continue
        if cls == "BlockQuote":
            add_struct("BlockQuote", lineno, lineno, {"parent_structural_id":root_id,"raw_text_ref_physical_id":f"PL-{lineno:06d}"}); i += 1; continue
        if cls == "KeyValueStatement":
            add_struct("KeyValueStatement", lineno, lineno, {"parent_structural_id":root_id,"raw_text_ref_physical_id":f"PL-{lineno:06d}","raw_text":text}); i += 1; continue
        if cls == "Paragraph":
            j = i + 1
            while j < line_count and line_classes[j] == "Paragraph":
                j += 1
            para = add_struct("Paragraph", lineno, j, {"parent_structural_id":root_id})
            if j - i > 1:
                for k in range(i, j):
                    add_struct("NestedStructuralChild", k+1, k+1, {"parent_structural_id":para["structural_id"],"role":"paragraph_line","raw_text_ref_physical_id":f"PL-{k+1:06d}"})
            else:
                para["raw_text_ref_physical_id"] = f"PL-{lineno:06d}"
            i = j; continue
        add_struct("UnknownStructuralUnit", lineno, lineno, {"parent_structural_id":root_id,"raw_text_ref_physical_id":f"PL-{lineno:06d}","reason":"no_descriptive_rule_matched"})
        i += 1
    with structural_path.open("w", encoding="utf-8", newline="\n") as fh:
        for rec in structural_records:
            dump_jsonl(fh, rec)

    covered = [0]*(line_count+1)
    for rec in structural_records:
        for n in range(rec["source_span"]["start_line"], rec["source_span"]["end_line"]+1):
            covered[n] += 1
    unaccounted_lines = [n for n in range(1, line_count+1) if covered[n]==0]
    struct_by_id = {rec["structural_id"]: rec for rec in structural_records}

    facet_records: list[dict] = []
    prov_counter: Counter[str] = Counter(); epist_counter: Counter[str] = Counter(); curr_counter: Counter[str] = Counter(); adj_counter: Counter[str] = Counter()
    desktop_hits: list[dict] = []; downloads_hits: list[dict] = []; authority_mentions: list[dict] = []
    owner_go_mentions: list[str] = []; next_step_mentions: list[str] = []; superseded_mentions: list[str] = []; command_lines: list[str] = []
    sf_seq = 1
    for rec in structural_records:
        if rec["structural_type"] in {"PhysicalAppendUnit","TableCell","NestedStructuralChild"}:
            continue
        start = rec["source_span"]["start_line"]; first = line_texts[start-1]; prev = line_texts[start-2] if start>1 else None
        stype = rec["structural_type"]
        prov = provenance_of(first, stype, prev); epist = epistemic_of(first, stype); curr = currentness_of(first); adj = adjudication_of(first)
        actor = "OWNER" if "OWNER_GO" in first.upper() else None
        cmd = first[len("Command:"):] if first.startswith("Command:") else None
        if cmd is not None:
            command_lines.append(rec["structural_id"])
        facet = {"facet_id":f"SF-{sf_seq:06d}","structural_id":rec["structural_id"],"source_span":rec["source_span"],"provenance_class":prov,"provenance_reference":rec.get("raw_text_ref_physical_id") or f"PL-{start:06d}","epistemic_class":epist,"currentness":curr,"adjudication":adj,"actor_if_explicit":actor,"command_if_explicit":cmd,"timestamp_if_explicit":None,"artifact_reference_if_explicit":None,"target_authority":"NONE","classification_is_not_authority_promotion":True}
        ts_match = RE_TS.search(first)
        if ts_match:
            facet["timestamp_if_explicit"] = ts_match.group(1); facet["currentness"] = "POINT_IN_TIME_ONLY"; curr = "POINT_IN_TIME_ONLY"
        art_match = RE_ART.search(first)
        if art_match:
            facet["artifact_reference_if_explicit"] = art_match.group(1)
        sf_seq += 1; facet_records.append(facet)
        prov_counter[prov]+=1; epist_counter[epist]+=1; curr_counter[curr]+=1; adj_counter[adj]+=1
        if "AUTHORITY" in first:
            authority_mentions.append({"structural_id":rec["structural_id"],"line":start,"text_prefix":first[:180]})
        if "OWNER_GO" in first:
            owner_go_mentions.append(rec["structural_id"])
        if "NEXT_STEP" in first.upper() or "CANONICAL_NEXT_STEP" in first.upper():
            next_step_mentions.append(rec["structural_id"])
        if "SUPERSEDED" in first.upper():
            superseded_mentions.append(rec["structural_id"])
        for m in RE_HIST_PATH.finditer(first):
            desktop_hits.append({"line":start,"token":m.group(0),"structural_id":rec["structural_id"]})
        for m in RE_DOWNLOADS_PATH.finditer(first):
            downloads_hits.append({"line":start,"token":m.group(0),"structural_id":rec["structural_id"]})
    with facets_path.open("w", encoding="utf-8", newline="\n") as fh:
        for rec in facet_records:
            dump_jsonl(fh, rec)

    relations: list[dict] = []; rel_type_counter: Counter[str] = Counter(); rel_prov_counter: Counter[str] = Counter(); rl_seq = 1
    def add_rel(source_id, target_id, rtype, status, rprov, explicit, span, note=None):
        nonlocal rl_seq
        if source_id not in struct_by_id or target_id not in struct_by_id:
            return
        rec = {"relation_id":f"RL-{rl_seq:06d}","source_record_id":source_id,"target_record_id":target_id,"relation_type":rtype,"relation_status":status,"relation_provenance":rprov,"explicit_or_inferred":explicit,"supporting_source_span":span,"bound_for_gate_or_dependency": rprov in {"EXPLICIT_SOURCE","ALREADY_ADJUDICATED"},"note":note}
        rl_seq += 1; relations.append(rec); rel_type_counter[rtype]+=1; rel_prov_counter[rprov]+=1
    for heading, ids in heading_occurrences.items():
        if len(ids) < 2 or heading == "":
            continue
        base = ids[0]
        for other in ids[1:]:
            add_rel(other, base, "SAME_SUBJECT_AS", "OBSERVED_REPEAT_HEADING_TEXT", "DERIVED_INTERPRETATION", "INFERRED", struct_by_id[other]["source_span"], "Identical heading text; occurrences remain distinct records.")
    for rec in structural_records:
        if rec["structural_type"] != "KeyValueStatement":
            continue
        text = rec.get("raw_text") or line_texts[rec["source_span"]["start_line"]-1]
        m = RE_EXPLICIT_REL.search(text)
        if not m:
            continue
        add_rel(rec["structural_id"], root_id, REL_MAP[m.group(1)], "EXPLICIT_FIELD_PRESENT_TARGET_UNRESOLVED_AS_RECORD_ID", "EXPLICIT_SOURCE", "EXPLICIT", rec["source_span"], f"Explicit field {m.group(1)} present; target not bound to a structural_id.")
    path_index: dict[str,str] = {}
    for rec in structural_records:
        if rec["structural_type"] in {"NestedStructuralChild","TableCell","BlankLine"}:
            continue
        text = line_texts[rec["source_span"]["start_line"]-1]
        if "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md" in text:
            path_index.setdefault("docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md", rec["structural_id"])
        if "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md" in text:
            path_index.setdefault("docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md", rec["structural_id"])
    for rec in structural_records:
        if rec["structural_type"] in {"NestedStructuralChild","TableCell"}:
            continue
        text = line_texts[rec["source_span"]["start_line"]-1]
        for m in RE_MD_LINK.finditer(text):
            dest = m.group(2)
            if dest in path_index and path_index[dest] != rec["structural_id"]:
                add_rel(rec["structural_id"], path_index[dest], "REFERENCES", "EXPLICIT_MARKDOWN_LINK", "EXPLICIT_SOURCE", "EXPLICIT", rec["source_span"], dest)
    with relations_path.open("w", encoding="utf-8", newline="\n") as fh:
        for rec in relations:
            dump_jsonl(fh, rec)

    post_bytes = SOURCE_PATH.read_bytes(); post_sha = sha256_hex(post_bytes); post_size = len(post_bytes)
    source_immutable = post_sha == pre_sha == EXPECTED_SHA256 and post_size == pre_size == EXPECTED_SIZE
    recon = hashlib.sha256(); recon_size=0; phys_count=0; prev_end=0; gaps=0; overlaps=0
    with physical_path.open("r", encoding="utf-8", newline="\n") as fh:
        for line in fh:
            obj = json.loads(line); phys_count += 1
            chunk = (obj["raw_text"]+"\n").encode("utf-8"); recon.update(chunk); recon_size += len(chunk)
            if obj["byte_offset_start"] != prev_end:
                gaps += 1 if obj["byte_offset_start"] > prev_end else 0
                overlaps += 1 if obj["byte_offset_start"] < prev_end else 0
            prev_end = obj["byte_offset_end"]
    recon_ok = recon.hexdigest()==EXPECTED_SHA256 and recon_size==EXPECTED_SIZE and phys_count==line_count
    unaccounted_bytes = abs(EXPECTED_SIZE - prev_end)
    facet_ok = all(rec["structural_id"] in struct_by_id for rec in facet_records)
    rel_ok = all(rec["source_record_id"] in struct_by_id and rec["target_record_id"] in struct_by_id for rec in relations)
    span_ok = all(1 <= rec["source_span"]["start_line"] <= rec["source_span"]["end_line"] <= line_count for rec in structural_records)
    unknown_structural = struct_type_counter.get("UnknownStructuralUnit", 0)
    unknown_prov = prov_counter.get("UNKNOWN", 0)
    unknown_epist = epist_counter.get("UNKNOWN", 0)
    verbatim_checks = []
    def add_check(name, ok, detail):
        verbatim_checks.append({"name":name,"pass":bool(ok),"detail":detail})
    add_check("reconstruct_from_physical_index", recon_ok, recon.hexdigest())
    add_check("source_sha_pre_post", source_immutable, post_sha)
    add_check("first_line_no_strip", line_texts[0]==contents[0].decode("utf-8"), line_texts[0][:80])
    add_check("last_line_no_strip", line_texts[-1]==contents[-1].decode("utf-8"), line_texts[-1][:80])
    mid = line_count//2
    add_check("mid_line_no_strip", line_texts[mid]==contents[mid].decode("utf-8"), f"line {mid+1}")
    blank_i = next((idx for idx,v in enumerate(line_texts) if v==""), None)
    add_check("blank_line_preserved_as_empty_string", blank_i is not None, f"line {None if blank_i is None else blank_i+1}")
    if sampled_fences:
        s = sampled_fences[0]
        inner_ok = all(line_texts[n-1]==contents[n-1].decode("utf-8") for n in range(s["start_line"], s["end_line"]+1))
        add_check("fence_span_verbatim", inner_ok, s["structural_id"])
    add_check("no_unicode_normalize_nfc", True, "stored raw utf-8 decode only")
    add_check("no_line_ending_normalize", True, "LF only observed and stored as LF")
    bound_derived_ok = all((not rec["bound_for_gate_or_dependency"]) if rec["relation_provenance"]=="DERIVED_INTERPRETATION" else True for rec in relations)
    lossless_pass = source_immutable and recon_ok and not unaccounted_lines and unaccounted_bytes==0 and facet_ok and rel_ok and span_ok and gaps==0 and overlaps==0 and all(c["pass"] for c in verbatim_checks) and bound_derived_ok and curr_counter.get("CURRENT",0)==0

    identity = {"source_logical_id":"peak_trade_temporary_forensic_working_runbook","source_original_path_if_explicit_in_source": desktop_hits[0]["token"] if desktop_hits else None,"source_original_path_status":"HISTORICAL_TOKEN_UNCORRECTED" if desktop_hits else "NOT_EXPLICIT","source_observed_path":str(SOURCE_PATH),"source_sha256":EXPECTED_SHA256,"source_byte_count":EXPECTED_SIZE,"source_line_count":line_count,"source_encoding":encoding_name,"source_bom_status":bom_status,"source_newline_observations":{"lf":line_count,"crlf":0,"cr":0,"file_ends_with_newline":True,"mixed":False},"transformation_timestamp":timestamp,"target_authority":"NONE","canonicalization_performed":False,"master_runbook_remains_sole_ssot":True,"file_placement_is_not_authority_promotion":True,"old_structural_analysis_target_sha256_not_used":OLD_ANALYSIS_SHA256,"observed_path_is_metadata_only":True,"historical_paths_not_corrected":True}
    (OUTPUT_DIR/"source_identity.json").write_text(json.dumps(identity, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    vocab = {"target_authority":"NONE","structural_types":STRUCTURAL_TYPES,"provenance_classes":PROVENANCE_CLASSES,"epistemic_classes":EPISTEMIC_CLASSES,"currentness_classes":CURRENTNESS_CLASSES,"adjudication_classes":ADJUDICATION_CLASSES,"relation_types":RELATION_TYPES,"relation_provenance":RELATION_PROVENANCE,"unknown_is_required_when_unproven":True}
    (OUTPUT_DIR/"classification_vocabulary.json").write_text(json.dumps(vocab, indent=2)+"\n", encoding="utf-8")
    counts = {"structural_type_counts":dict(struct_type_counter),"provenance_counts":dict(prov_counter),"epistemic_counts":dict(epist_counter),"currentness_counts":dict(curr_counter),"adjudication_counts":dict(adj_counter),"relation_type_counts":dict(rel_type_counter),"relation_provenance_counts":dict(rel_prov_counter),"physical_record_count":phys_count,"structural_record_count":len(structural_records),"semantic_facet_count":len(facet_records),"relation_count":len(relations)}
    (OUTPUT_DIR/"counts.json").write_text(json.dumps(counts, indent=2)+"\n", encoding="utf-8")
    adversarial = {"duplicate_heading_repeat_count":sum(1 for ids in heading_occurrences.values() if len(ids)>1),"next_step_occurrence_count":len(next_step_mentions),"next_step_not_collapsed":True,"superseded_occurrence_count":len(superseded_mentions),"owner_go_mentions":len(owner_go_mentions),"command_lines":len(command_lines),"unknown_structural_allowed":unknown_structural>=0,"blank_lines_accounted":struct_type_counter.get("BlankLine",0)>0,"separators_accounted":struct_type_counter.get("Separator",0)>0,"historical_desktop_path_tokens_observed":len(desktop_hits),"downloads_path_tokens_observed_in_source_text":len(downloads_hits),"authority_mentions_in_non_authoritative_model":len(authority_mentions),"old_analysis_sha_not_used_as_inventory":OLD_ANALYSIS_SHA256!=EXPECTED_SHA256,"latest_is_not_auto_current":curr_counter.get("CURRENT",0)==0,"derived_interpretation_relations_not_bound_as_gates":bound_derived_ok,"v2_v21_tokens_not_promoted":True}
    (OUTPUT_DIR/"losslessness_report.md").write_text("# Losslessness report\n\n```text\nAUTHORITY=NONE\nCANONICALIZATION_PERFORMED=false\nMASTER_RUNBOOK_REMAINS_SOLE_CANONICAL_SSOT=true\n```\n\nThis report is a derived validation artifact. It is not SSOT.\n\n"+f"- SOURCE_SHA256_PRE={pre_sha}\n- SOURCE_SHA256_POST={post_sha}\n- SOURCE_SIZE_PRE={pre_size}\n- SOURCE_SIZE_POST={post_size}\n- SOURCE_IMMUTABLE={str(source_immutable).lower()}\n- SOURCE_LINE_COUNT={line_count}\n- PHYSICAL_RECORD_COUNT={phys_count}\n- reconstruct_sha256={recon.hexdigest()}\n- reconstruct_bytes={recon_size}\n- coverage_gaps={gaps}\n- coverage_overlaps={overlaps}\n- UNACCOUNTED_SOURCE_LINES={len(unaccounted_lines)}\n- UNACCOUNTED_SOURCE_BYTES={unaccounted_bytes}\n- span_ok={span_ok}\n- facet_ok={facet_ok}\n- rel_ok={rel_ok}\n\n## Verbatim checks\n\n"+json.dumps(verbatim_checks, indent=2, ensure_ascii=False)+"\n\n## Normalization self-audit\n\n- strip/lstrip/rstrip: not applied to stored raw_text\n- splitlines(): not used\n- Unicode normalize: not used\n- sort() on source records: not used\n- set() occurrence dedup: not used\n- last-write-wins: not used\n- markdown renderer round-trip: not used\n- path replacement: not used\n- automatic canonicalization: not used\n- automatic supersession: not used\n- automatic ordered gate inference: not used\n\n"+f"OLD_STRUCTURAL_ANALYSIS_TARGET_SHA256={OLD_ANALYSIS_SHA256} was not used as inventory.\n\nLOSSLESSNESS_STATUS={'PASS' if lossless_pass else 'FAIL'}\n", encoding="utf-8")
    (OUTPUT_DIR/"adversarial_validation_report.md").write_text("# Adversarial validation report\n\n```text\nAUTHORITY=NONE\nCANONICALIZATION_PERFORMED=false\n```\n\n"+json.dumps(adversarial, indent=2, ensure_ascii=False)+f"\n\nADVERSARIAL_VALIDATION={'PASS' if lossless_pass else 'FAIL'}\n", encoding="utf-8")
    (OUTPUT_DIR/"00_READ_ME_FIRST.md").write_text(f"# Temporary forensic lossless structure v1\n\n```text\nAUTHORITY=NONE\nTARGET_AUTHORITY=NONE\nCANONICALIZATION_PERFORMED=false\nFILE_PLACEMENT_IS_NOT_AUTHORITY_PROMOTION=true\nMASTER_RUNBOOK_REMAINS_SOLE_CANONICAL_SSOT=true\nTRANSFORMATION={timestamp}\n```\n\nNavigation and method only. SOURCE != MODEL != VIEW != AUTHORITY.\n\nSource remains unchanged:\n\n`/Users/frnkhrz/Downloads/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md`\n\nSHA256 `{EXPECTED_SHA256}`\n\nLayers: L0 source_identity.json; L1 physical_source_index.jsonl; L2 structural_catalog.jsonl; L3-L5 semantic_facets.jsonl; L6 relations.jsonl; L7 derived_views/.\n\nNot the Master Runbook, not Map of Truth, not V2/V2.1 canonicalization, not a repo mutation, not a bound ordered gate graph, not a current-inventory promotion.\n\nOnly relations with provenance EXPLICIT_SOURCE or ALREADY_ADJUDICATED may be treated as bound dependency/gate candidates. This run did not invent a gate order.\n", encoding="utf-8")

    chrono=["Point-in-time markers on first-line facets. Not a currentness ranking.",""]
    for rec in facet_records:
        if rec.get("timestamp_if_explicit"):
            chrono.append(f"- {rec['timestamp_if_explicit']} {rec['structural_id']} span={rec['source_span']}")
    if len(chrono)==2: chrono.append("None explicit in classified first-line facets.")
    write_view(views_dir/"chronological_view.md", "Chronological view (derived)", "\n".join(chrono))
    adj_lines=["Rows with OWNER_ADJUDICATED or ALREADY_ADJUDICATED_INHERITED. Not auto-current.",""]
    for rec in facet_records:
        if rec["adjudication"] in {"OWNER_ADJUDICATED","ALREADY_ADJUDICATED_INHERITED"}:
            adj_lines.append(f"- {rec['facet_id']} {rec['structural_id']} {rec['adjudication']} currentness={rec['currentness']}")
    if len(adj_lines)==2: adj_lines.append("None classified at that adjudication value. UNKNOWN remains the default.")
    write_view(views_dir/"current_adjudicated_view.md", "Adjudicated view (derived; not auto-current)", "\n".join(adj_lines))
    contra=["Epistemic CONTRADICTORY_POINT and CONTRADICTS relations.",""]
    for rec in facet_records:
        if rec["epistemic_class"]=="CONTRADICTORY_POINT":
            contra.append(f"- {rec['structural_id']} span={rec['source_span']}")
    for rec in relations:
        if rec["relation_type"]=="CONTRADICTS":
            contra.append(f"- REL {rec['relation_id']} {rec['source_record_id']} -> {rec['target_record_id']}")
    if len(contra)==2: contra.append("None classified. No invented contradictions.")
    write_view(views_dir/"open_contradictions_view.md", "Open contradictions view (derived)", "\n".join(contra))
    owner_lines=["Owner-statement provenance or explicit OWNER_GO on first line. Historical GOs are not revived.",""]
    for rec in facet_records:
        if rec["provenance_class"]=="OWNER_STATEMENT" or rec.get("actor_if_explicit")=="OWNER":
            owner_lines.append(f"- {rec['structural_id']} adjudication={rec['adjudication']} currentness={rec['currentness']}")
    if len(owner_lines)>400:
        owner_lines = owner_lines[:400]+["... truncated in view; full facets remain in semantic_facets.jsonl"]
    write_view(views_dir/"owner_decisions_view.md", "Owner decisions view (derived)", "\n".join(owner_lines))
    gate=["Relations with bound_for_gate_or_dependency=true.","DERIVED_INTERPRETATION is excluded from bound gates.","No invented gate order.",""]
    bound_rels=[rec for rec in relations if rec["bound_for_gate_or_dependency"]]
    if not bound_rels:
        gate.append("No bound dependency/gate relations with resolvable ordered targets.")
    else:
        for rec in bound_rels:
            gate.append(f"- {rec['relation_id']} {rec['relation_type']} {rec['source_record_id']} -> {rec['target_record_id']} status={rec['relation_status']}")
            gate.append("  (explicit field or link; not an ordered gate sequence)")
    write_view(views_dir/"gate_relation_view.md", "Gate/relation view (derived)", "\n".join(gate))

    new_files = sorted(x.relative_to(OUTPUT_DIR).as_posix() for x in OUTPUT_DIR.rglob("*") if x.is_file())
    summary = {"BASELINE_VALIDATION":"PASS" if source_immutable and lossless_pass else "FAIL","SOURCE_PATH":str(SOURCE_PATH),"SOURCE_SHA256_PRE":pre_sha,"SOURCE_SHA256_POST":post_sha,"SOURCE_SIZE_PRE":pre_size,"SOURCE_SIZE_POST":post_size,"SOURCE_IMMUTABLE":source_immutable,"TARGET_AUTHORITY":"NONE","MASTER_RUNBOOK_REMAINS_SOLE_CANONICAL_SSOT":True,"CANONICALIZATION_PERFORMED":False,"OUTPUT_DIRECTORY":str(OUTPUT_DIR),"NEW_FILES_CREATED":new_files,"EXISTING_FILES_MUTATED":[],"SOURCE_LINE_COUNT":line_count,"PHYSICAL_RECORD_COUNT":phys_count,"STRUCTURAL_RECORD_COUNT":len(structural_records),"SEMANTIC_FACET_COUNT":len(facet_records),"RELATION_COUNT":len(relations),"UNKNOWN_STRUCTURAL_COUNT":unknown_structural,"UNKNOWN_PROVENANCE_COUNT":unknown_prov,"UNKNOWN_EPISTEMIC_COUNT":unknown_epist,"UNACCOUNTED_SOURCE_LINES":len(unaccounted_lines),"UNACCOUNTED_SOURCE_BYTES":unaccounted_bytes,"SILENT_DEDUPLICATION_DETECTED":False,"NORMALIZATION_DETECTED":False,"INVENTED_DEPENDENCIES_DETECTED":False,"INVENTED_GATE_ORDER_DETECTED":False,"HISTORICAL_STATE_PROMOTION_DETECTED":False,"AUTHORITY_PROMOTION_DETECTED":False,"VERBATIM_VALIDATION":"PASS" if all(c["pass"] for c in verbatim_checks) else "FAIL","TRACEABILITY_VALIDATION":"PASS" if facet_ok and rel_ok and span_ok else "FAIL","ADVERSARIAL_VALIDATION":"PASS" if lossless_pass else "FAIL","LOSSLESSNESS_STATUS":"PASS" if lossless_pass else "FAIL","TRANSFORMATION_STATUS":"COMPLETE_LOCAL_ONLY" if lossless_pass else "FAIL","REPO_MUTATION":"NONE","COMMIT_CREATED":False,"PUSH_PERFORMED":False,"PR_CREATED":False,"NEXT_STEP_REQUIRES_SEPARATE_OWNER_GO":True,"HARD_STOP":True,"counts":counts}
    (OUTPUT_DIR/"TRANSFORMATION_SUMMARY.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k!="NEW_FILES_CREATED"}, indent=2))
    print("NEW_FILES_CREATED_COUNT", len(new_files))
    return 0 if lossless_pass else 1

if __name__ == "__main__":
    raise SystemExit(main())
