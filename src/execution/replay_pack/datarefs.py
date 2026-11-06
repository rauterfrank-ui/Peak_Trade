from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Mapping, Optional, Sequence, Tuple

from .canonical import write_json_canonical
from .contract import ContractViolationError, SchemaValidationError
from .hashing import sha256_file, write_sha256sums
from .schema import validate_market_data_refs_document_strict


RESOLVER_VERSION: Literal["1"] = "1"

ResolutionMode = Literal["best_effort", "strict"]
ResolutionStatus = Literal["RESOLVED", "MISSING", "HASH_MISMATCH"]


class MissingRequiredDataRefError(ContractViolationError):
    """
    Raised when mode is strict and a required dataref cannot be resolved.
    """


class DataRefHashMismatchError(ContractViolationError):
    """
    Raised when mode is strict and a resolved dataref sha256 mismatches sha256_hint.
    """


@dataclass(frozen=True)
class MarketDataLocator:
    namespace: str
    dataset: str
    partition: Optional[str] = None


@dataclass(frozen=True)
class MarketDataRef:
    ref_id: str
    kind: str
    symbol: str
    venue: Optional[str]
    timeframe: Optional[str]
    start_utc: str
    end_utc: str
    source: Literal["local_cache"]
    locator: MarketDataLocator
    sha256_hint: Optional[str]
    required: bool = False


@dataclass(frozen=True)
class ResolutionResult:
    ref_id: str
    status: ResolutionStatus
    path: Optional[str]
    bytes: Optional[int]
    sha256: Optional[str]
    note: Optional[str] = None


@dataclass(frozen=True)
class ResolutionSummary:
    total: int
    resolved: int
    missing: int
    hash_mismatch: int


@dataclass(frozen=True)
class ResolutionReport:
    meta: Dict[str, Any]
    results: List[ResolutionResult]
    summary: ResolutionSummary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meta": dict(self.meta),
            "results": [
                {
                    "ref_id": r.ref_id,
                    "status": r.status,
                    "path": r.path,
                    "bytes": r.bytes,
                    "sha256": r.sha256,
                    "note": r.note,
                }
                for r in self.results
            ],
            "summary": {
                "total": self.summary.total,
                "resolved": self.summary.resolved,
                "missing": self.summary.missing,
                "hash_mismatch": self.summary.hash_mismatch,
            },
        }


def _sorted_refs(refs: Sequence[MarketDataRef]) -> List[MarketDataRef]:
    return sorted(refs, key=lambda r: (r.kind, r.symbol, r.start_utc, r.end_utc, r.ref_id))


def _require_non_empty_str(d: Mapping[str, Any], key: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise SchemaValidationError(f"market_data_ref field must be non-empty string: {key}")
    return v


def _optional_str(d: Mapping[str, Any], key: str) -> Optional[str]:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, str):
        raise SchemaValidationError(f"market_data_ref field must be string or null: {key}")
    v = v.strip()
    return v or None


def _optional_bool(d: Mapping[str, Any], key: str, default: bool) -> bool:
    v = d.get(key, default)
    if isinstance(v, bool):
        return v
    raise SchemaValidationError(f"market_data_ref field must be bool: {key}")


def _parse_locator(x: Any) -> MarketDataLocator:
    if not isinstance(x, Mapping):
        raise SchemaValidationError("market_data_ref.locator must be an object")
    namespace = _require_non_empty_str(x, "namespace")
    dataset = _require_non_empty_str(x, "dataset")
    partition = _optional_str(x, "partition")
    return MarketDataLocator(namespace=namespace, dataset=dataset, partition=partition)


def _parse_market_data_ref(x: Any) -> MarketDataRef:
    if not isinstance(x, Mapping):
        raise SchemaValidationError("market_data_ref must be an object")
    ref_id = _require_non_empty_str(x, "ref_id")
    kind = _require_non_empty_str(x, "kind")
    symbol = _require_non_empty_str(x, "symbol")
    venue = _optional_str(x, "venue")
    timeframe = _optional_str(x, "timeframe")
    start_utc = _require_non_empty_str(x, "start_utc")
    end_utc = _require_non_empty_str(x, "end_utc")
    source = _require_non_empty_str(x, "source")
    if source != "local_cache":
        raise SchemaValidationError("market_data_ref.source must be 'local_cache'")
    locator = _parse_locator(x.get("locator"))
    sha256_hint = _optional_str(x, "sha256_hint")
    required = _optional_bool(x, "required", False)
    return MarketDataRef(
        ref_id=ref_id,
        kind=kind,
        symbol=symbol,
        venue=venue,
        timeframe=timeframe,
        start_utc=start_utc,
        end_utc=end_utc,
        source="local_cache",
        locator=locator,
        sha256_hint=sha256_hint,
        required=required,
    )


def parse_market_data_refs_document(doc: Mapping[str, Any] | Sequence[Any]) -> List[MarketDataRef]:
    """
    Parse and validate the refs document.

    Accepted top-level shapes:
    - list[ref]  (legacy/simple)
    - { "schema_version": "MARKET_DATA_REFS_V1", "refs": [ref, ...] }
    - { "market_data_refs": [ref, ...] }  (wrapper used by operators)
    """
    validate_market_data_refs_document_strict(doc)
    if isinstance(doc, list):
        items = doc
    else:
        if "market_data_refs" in doc:
            items = list(doc.get("market_data_refs") or [])
        else:
            items = list(doc.get("refs") or [])
    refs = [_parse_market_data_ref(it) for it in items]
    # Uniqueness of ref_id (strict).
    ref_ids = [r.ref_id for r in refs]
    if len(set(ref_ids)) != len(ref_ids):
        raise SchemaValidationError("market_data_refs ref_id must be unique")
    return refs


def _normalize_time_tag(s: str) -> str:
    """
    Make a filesystem-friendly tag while remaining deterministic.
    """
    return (
        s.strip()
        .replace(":", "")
        .replace("+", "")
        .replace("-", "")
        .replace(".", "")
        .replace("Z", "Z")
    )


def _candidate_relpaths_for_ref(r: MarketDataRef) -> List[str]:
    """
    Deterministic candidate list.

    Filename formats attempted (in this order):
      1) <symbol>.<kind>.<timeframe?>.<start>_<end>.parquet         (raw start/end)
      2) <symbol>.<kind>.<timeframe?>.<startTag>_<endTag>.parquet   (normalized tags)
    """
    parts = [r.symbol, r.kind]
    if r.timeframe:
        parts.append(r.timeframe)
    base = ".".join(parts)
    raw = f"{base}.{r.start_utc}_{r.end_utc}.parquet"
    norm = f"{base}.{_normalize_time_tag(r.start_utc)}_{_normalize_time_tag(r.end_utc)}.parquet"

    prefix_parts = [r.locator.namespace, r.locator.dataset]
    if r.locator.partition:
        prefix_parts.append(r.locator.partition)
    prefix = "/".join(prefix_parts)
    return [f"{prefix}/{raw}", f"{prefix}/{norm}"]


def resolve_market_data_refs(
    bundle_root: str | Path,
    refs: Sequence[Mapping[str, Any]] | Sequence[MarketDataRef],
    cache_root: str | Path,
    *,
    mode: ResolutionMode = "best_effort",
    bundle_id: Optional[str] = None,
    run_id: Optional[str] = None,
    generated_at_utc: Optional[str] = None,
    run_id_for_report: Optional[str] = None,
) -> ResolutionReport:
    """
    Resolve bundle market_data_refs to locally cached datasets (offline).

    Determinism:
    - refs are resolved in stable order: (kind, symbol, start_utc, end_utc, ref_id)
    - candidates are deterministic; if multiple exist, pick lexicographically smallest path
    """
    root = Path(bundle_root)
    cache = Path(cache_root)
    if mode not in ("best_effort", "strict"):
        raise ValueError("mode must be 'best_effort' or 'strict'")
    if not cache.exists() or not cache.is_dir():
        raise ContractViolationError("cache_root must be an existing directory")

    parsed: List[MarketDataRef]
    if refs and isinstance(refs[0], MarketDataRef):  # type: ignore[index]
        parsed = list(refs)  # type: ignore[assignment]
    else:
        parsed = [_parse_market_data_ref(r) for r in refs]  # type: ignore[arg-type]

    ordered = _sorted_refs(parsed)
    results: List[ResolutionResult] = []

    for r in ordered:
        candidates = [cache / rel for rel in _candidate_relpaths_for_ref(r)]
        existing = [p for p in candidates if p.exists() and p.is_file()]
        if not existing:
            results.append(
                ResolutionResult(
                    ref_id=r.ref_id,
                    status="MISSING",
                    path=None,
                    bytes=None,
                    sha256=None,
                    note="no candidate file found under cache_root",
                )
            )
            continue

        chosen = sorted({p.as_posix() for p in existing})[0]
        chosen_path = Path(chosen)
        digest = sha256_file(chosen_path)
        size = int(chosen_path.stat().st_size)

        if r.sha256_hint and digest != r.sha256_hint:
            results.append(
                ResolutionResult(
                    ref_id=r.ref_id,
                    status="HASH_MISMATCH",
                    path=chosen,
                    bytes=size,
                    sha256=digest,
                    note="sha256 differs from sha256_hint",
                )
            )
        else:
            note = None
            if len(existing) > 1:
                note = "multiple candidates; chose lexicographically smallest path"
            results.append(
                ResolutionResult(
                    ref_id=r.ref_id,
                    status="RESOLVED",
                    path=chosen,
                    bytes=size,
                    sha256=digest,
                    note=note,
                )
            )

    resolved = sum(1 for r in results if r.status == "RESOLVED")
    missing = sum(1 for r in results if r.status == "MISSING")
    mism = sum(1 for r in results if r.status == "HASH_MISMATCH")

    meta = {
        "bundle_id": bundle_id,
        "run_id": run_id_for_report or run_id,
        "generated_at_utc": generated_at_utc,
        "resolver_version": RESOLVER_VERSION,
        "mode": mode,
    }
    return ResolutionReport(
        meta=meta,
        results=results,
        summary=ResolutionSummary(
            total=len(results), resolved=resolved, missing=missing, hash_mismatch=mism
        ),
    )


def enforce_resolution_mode(
    *,
    mode: ResolutionMode,
    refs: Sequence[MarketDataRef],
    report: ResolutionReport,
) -> None:
    """
    Enforce STRICT semantics on a computed report.

    Rules:
    - STRICT: any HASH_MISMATCH => DataRefHashMismatchError
             any required ref with status MISSING => MissingRequiredDataRefError
    - BEST_EFFORT: no exception
    """
    if mode != "strict":
        return
    if any(r.status == "HASH_MISMATCH" for r in report.results):
        raise DataRefHashMismatchError("hash mismatch for market_data_refs (sha256_hint)")
    required_ids = {r.ref_id for r in refs if r.required}
    missing_required = [
        r.ref_id for r in report.results if r.ref_id in required_ids and r.status == "MISSING"
    ]
    if missing_required:
        raise MissingRequiredDataRefError(f"missing required market_data_refs: {missing_required}")


def read_market_data_refs_file(path: Path) -> List[MarketDataRef]:
    """
    Read and parse events/market_data_refs.json.
    """
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, (Mapping, list)):
        raise SchemaValidationError("market_data_refs document must be object or list")
    return parse_market_data_refs_document(doc)


def write_resolution_report_json(path: Path, report: ResolutionReport) -> None:
    write_json_canonical(path, report.to_dict())


def embed_resolution_report_into_bundle(
    *,
    bundle_root: Path,
    report: ResolutionReport,
    relpath: str = "meta/resolution_report.json",
) -> None:
    """
    Write report into the bundle AND update sha256sums accordingly.

    Note: we intentionally do NOT add the report to manifest.contents to avoid any
    bundle_id self-referential fixed-point issues (bundle_id computed from contents list).
    The report is still hash-protected via hashes/sha256sums.txt.
    """
    out_path = bundle_root / relpath
    write_resolution_report_json(out_path, report)

    # Update sha256sums to cover all files except itself.
    from .hashing import collect_files_for_hashing

    relpaths_for_hashing = collect_files_for_hashing(bundle_root)
    write_sha256sums(bundle_root, relpaths_for_hashing)
