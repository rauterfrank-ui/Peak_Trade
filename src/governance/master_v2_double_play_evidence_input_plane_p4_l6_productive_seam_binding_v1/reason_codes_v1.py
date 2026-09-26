"""Fail-closed reason codes for P4 productive L6 seam binding."""

from __future__ import annotations

from enum import Enum


class ProductiveL6SeamFailureCodeV1(str, Enum):
    REQUEST_MISSING = "productive_l6_seam_request_missing"
    GATE_NOT_AUTHORIZED = "productive_l6_binding_not_authorized"
    ADJUDICATION_NOT_ADMIT = "adjudication_not_admit"
    BINDING_NOT_BIND = "binding_not_bind"
    L6_ADMISSION_REJECT = "l6_admission_reject"
    INSTRUMENT_MISMATCH = "instrument_binding_mismatch"
    EPOCH_MISMATCH = "epoch_binding_mismatch"
    NULLLINE_EPOCH_MISMATCH = "nullline_provenance_epoch_mismatch"
    DUPLICATE_SEAM_DIVERGENT = "duplicate_seam_delivery_divergent"
    MECHANICAL_PROPOSED_D_T_FORBIDDEN_FROM_EVIDENCE = (
        "mechanical_proposed_d_t_must_not_be_sourced_from_evidence"
    )
