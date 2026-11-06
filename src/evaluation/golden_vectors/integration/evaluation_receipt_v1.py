"""Durable exact GVEF result receipts and original numerical-owner evidence bytes."""

from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass, asdict
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
from .domain_result_binding_v1 import EvaluationBindingError, exact_bytes_v1, binding_digest_v1


@dataclass(frozen=True)
class EvaluationReceiptV1:
    schema_version: str
    plan_id: str
    domain: str
    legacy_bundle_digest: str | None
    complete_result_binding_digest: str
    permitted_claim: str


def evaluation_receipt_binding_v1(body):
    original = {k: v for k, v in body.items() if k != "evaluation_receipt"}
    record = body.get("record") or {}
    bundle = record.get("evidence_bundle") or {}
    return asdict(
        EvaluationReceiptV1(
            "evaluation_receipt.v1",
            body["plan_id"],
            body["requirement"]["domain"],
            bundle.get("evidence_digest"),
            binding_digest_v1("complete_domain_result.v1", original),
            "EXPLICIT_REPLAY_CONTRACTS_ONLY",
        )
    )


class EvaluationReceiptArchiveV1:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    def safe_path_v1(self, relative):
        relative = Path(relative)
        if relative.is_absolute() or ".." in relative.parts:
            raise EvaluationBindingError("RECEIPT_RELATIVE_PATH_REQUIRED")
        path = self.root / relative
        for part in (path, *path.parents):
            if part == self.root:
                break
            if part.is_symlink():
                raise EvaluationBindingError("RECEIPT_SYMLINK_FORBIDDEN")
        return path

    def publish_v1(self, path: Path, value):
        if path.is_absolute() or ".." in path.parts:
            raise EvaluationBindingError("RECEIPT_RELATIVE_PATH_REQUIRED")
        raw = exact_bytes_v1(value)
        path = self.safe_path_v1(path)
        if path.is_symlink():
            raise EvaluationBindingError("RECEIPT_SYMLINK_FORBIDDEN")
        if path.exists():
            if path.read_bytes() != raw:
                raise EvaluationBindingError("IMMUTABLE_EVALUATION_RECEIPT_CONFLICT")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".receipt-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(tmp, path)
            except FileExistsError:
                if path.read_bytes() != raw:
                    raise EvaluationBindingError("IMMUTABLE_EVALUATION_RECEIPT_CONFLICT")
            for parent in (path.parent, *path.parent.parents):
                handle = os.open(parent, os.O_RDONLY)
                try:
                    os.fsync(handle)
                finally:
                    os.close(handle)
        finally:
            os.unlink(tmp)

    def append_v1(self, kind, body):
        if kind not in {"domain", "system"}:
            raise EvaluationBindingError("UNKNOWN_RECEIPT_KIND")
        ident = binding_digest_v1(kind, body)
        self.publish_v1(
            Path("records") / kind / (ident + ".json"),
            {"kind": kind, "digest": ident, "body": body},
        )
        return ident

    def get_v1(self, kind, ident):
        if kind not in {"domain", "system"}:
            raise EvaluationBindingError("UNKNOWN_RECEIPT_KIND")
        if (
            not isinstance(ident, str)
            or len(ident) != 64
            or any(c not in "0123456789abcdef" for c in ident)
        ):
            raise EvaluationBindingError("RECEIPT_CONTENT_ADDRESS_REQUIRED")
        path = self.safe_path_v1(Path("records") / kind / (ident + ".json"))
        if path.is_symlink():
            raise EvaluationBindingError("RECEIPT_SYMLINK_FORBIDDEN")
        row = json.loads(path.read_bytes())
        if (
            set(row) != {"kind", "digest", "body"}
            or row["kind"] != kind
            or row["digest"] != ident
            or binding_digest_v1(kind, row["body"]) != ident
        ):
            raise EvaluationBindingError("FULL_RESULT_RECEIPT_DIGEST_MISMATCH")
        return row["body"]

    @contextmanager
    def lease_v1(self):
        self.root.mkdir(parents=True, exist_ok=True)
        p = self.root / ".fanout.lock"
        if p.is_symlink():
            raise EvaluationBindingError("RECEIPT_SYMLINK_FORBIDDEN")
        with p.open("a+b") as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise EvaluationBindingError("EVALUATION_ARCHIVE_WRITER_BUSY") from exc
            try:
                yield
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def retain_original_bytes_v1(self, raw):
        digest = hashlib.sha256(raw).hexdigest()
        # Encoding is lossless; the original JSON byte sequence has its own SHA,
        # separate from new receipt JSON and every historical GVEF digest.
        import base64

        self.publish_v1(
            Path("numeric") / (digest + ".json"),
            {"sha256": digest, "base64": base64.b64encode(raw).decode()},
        )
        return digest

    def numeric_bytes_v1(self, digest):
        import base64

        path = self.safe_path_v1(Path("numeric") / (digest + ".json"))
        if (
            len(digest) != 64
            or any(c not in "0123456789abcdef" for c in digest)
            or path.is_symlink()
        ):
            raise EvaluationBindingError("NUMERIC_CONTENT_ADDRESS_INVALID")
        row = json.loads(path.read_bytes())
        raw = base64.b64decode(row["base64"], validate=True)
        if row["sha256"] != digest or hashlib.sha256(raw).hexdigest() != digest:
            raise EvaluationBindingError("NUMERIC_ARCHIVE_BYTES_CHANGED")
        return raw


def retain_native_research_packet_v1(
    archive: EvaluationReceiptArchiveV1, *, owner_root: Path, artifact_id: str
):
    from src.experiments.canonical_native_research_session_v1 import (
        NativeResearchExecutionArchiveV1,
    )

    owner = NativeResearchExecutionArchiveV1(owner_root)
    executed = owner.get(artifact_id)
    raw = (owner.root / (artifact_id + ".json")).read_bytes()
    if hashlib.sha256(raw).hexdigest() != artifact_id:
        raise EvaluationBindingError("ORIGINAL_NUMERIC_PACKET_CHANGED")
    retained = archive.retain_original_bytes_v1(raw)
    return {
        "owner": "NativeResearchExecutionArchiveV1",
        "original_locator": str(owner.root / (artifact_id + ".json")),
        "original_artifact_id": artifact_id,
        "original_bytes_sha256": retained,
        "experiment_id": executed.next_meta_input.research_loop_record["selected_experiment_id"],
        "measurement_receipt_digest": json.loads(raw)["measurement_receipt"]["content_digest"],
    }


def validate_numeric_packet_v1(archive: EvaluationReceiptArchiveV1, ref):
    from src.experiments.canonical_search_candidate_research_execution_v1 import (
        read_research_execution_gvef_reference_v1,
    )
    from src.experiments.canonical_native_research_session_v1 import _validate_measurement

    raw = archive.numeric_bytes_v1(ref["original_bytes_sha256"])
    if ref["owner"] == "MiOfflineDurableEvidenceStoreV1":
        from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_record_v1 import (
            validate_mi_offline_durable_evidence_record_v1,
        )

        packet = validate_mi_offline_durable_evidence_record_v1(json.loads(raw))
        if (
            packet["durable_evidence_id"] != ref["original_artifact_id"]
            or packet["content_digest"] != ref["record_content_digest"]
        ):
            raise EvaluationBindingError("NUMERIC_OWNER_IDENTITY_MISMATCH")
        return dict(packet["calibration_evidence"]["calibration_result"])
    if (
        ref["owner"] != "NativeResearchExecutionArchiveV1"
        or hashlib.sha256(raw).hexdigest() != ref["original_artifact_id"]
    ):
        raise EvaluationBindingError("UNSUPPORTED_OR_CHANGED_NUMERIC_OWNER")
    packet = json.loads(raw)
    if packet["schema_version"] != "native_research_execution_archive_packet_v1":
        raise EvaluationBindingError("NUMERIC_OWNER_SCHEMA_MISMATCH")
    executed = read_research_execution_gvef_reference_v1(
        packet["gvef_reference"], artifact_bytes=packet["execution_utf8"].encode()
    )
    _validate_measurement(packet["measurement_receipt"], executed)
    if (
        ref["measurement_receipt_digest"] != packet["measurement_receipt"]["content_digest"]
        or ref["experiment_id"]
        != executed.next_meta_input.research_loop_record["selected_experiment_id"]
    ):
        raise EvaluationBindingError("NUMERIC_OWNER_IDENTITY_MISMATCH")
    return packet["measurement_receipt"]


def retain_mi_packet_v1(archive, *, owner_root, durable_evidence_id):
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_store_v1 import (
        MiOfflineDurableEvidenceStoreV1,
    )

    owner = MiOfflineDurableEvidenceStoreV1(owner_root)
    record = owner.get(durable_evidence_id)
    path = owner._record_path(durable_evidence_id)
    ref = {
        "owner": "MiOfflineDurableEvidenceStoreV1",
        "original_locator": str(path.resolve()),
        "original_artifact_id": durable_evidence_id,
        "original_bytes_sha256": archive.retain_original_bytes_v1(path.read_bytes()),
        "record_content_digest": record["content_digest"],
    }
    validate_numeric_packet_v1(archive, ref)
    return ref


def assess_economic_quality_v1(request):
    # No current owner establishes an independent natural economic comparison
    # with complete costs/funding/uncertainty. Caller labels cannot certify it.
    required = (
        "independent_comparison",
        "independent_market_data",
        "costs",
        "funding",
        "horizon",
        "uncertainty",
        "target_metric",
    )
    reasons = ["MISSING_" + k.upper() for k in required if not request.get(k)]
    reasons.append("ECONOMIC_QUALITY_CONTRACT_NOT_RATIFIED")
    return {
        "status": "BLOCKED",
        "reasons": reasons,
        "requested_claim": request.get("claim"),
        "profitability_established": False,
        "natural_learning_usefulness_established": False,
    }
