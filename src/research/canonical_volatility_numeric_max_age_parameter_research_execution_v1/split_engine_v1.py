"""Purged chronological splits with event-time embargo and sealed holdout."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.contracts_v1 import (
    MaxAgeResearchExecutionError,
    SplitAndEmbargoContractV1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evidence_loader_v1 import (
    ResearchEvidenceRecordV1,
)


@dataclass(frozen=True)
class SplitAssignmentV1:
    train: tuple[ResearchEvidenceRecordV1, ...]
    validation: tuple[ResearchEvidenceRecordV1, ...]
    holdout: tuple[ResearchEvidenceRecordV1, ...]
    embargo_seconds: int
    holdout_accessed: bool
    fold_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "embargo_seconds": self.embargo_seconds,
            "fold_id": self.fold_id,
            "holdout_accessed": self.holdout_accessed,
            "holdout_count": len(self.holdout),
            "train_count": len(self.train),
            "validation_count": len(self.validation),
        }


def _require_event_times(
    records: Sequence[ResearchEvidenceRecordV1],
) -> list[ResearchEvidenceRecordV1]:
    ordered: list[ResearchEvidenceRecordV1] = []
    for record in records:
        if record.event_time_epoch_seconds is None:
            raise MaxAgeResearchExecutionError("incomplete_event_time_reference")
        ordered.append(record)
    ordered.sort(key=lambda r: (float(r.event_time_epoch_seconds), r.cycle_id, r.join_digest))
    return ordered


def _purge_with_embargo(
    left: Sequence[ResearchEvidenceRecordV1],
    right: Sequence[ResearchEvidenceRecordV1],
    *,
    embargo_seconds: int,
) -> tuple[tuple[ResearchEvidenceRecordV1, ...], tuple[ResearchEvidenceRecordV1, ...]]:
    if not left or not right:
        return tuple(left), tuple(right)
    left_max = max(float(r.event_time_epoch_seconds or 0.0) for r in left)
    right_min = min(float(r.event_time_epoch_seconds or 0.0) for r in right)
    # Purge overlapping windows within embargo of the boundary.
    purged_left = tuple(
        r
        for r in left
        if float(r.event_time_epoch_seconds or 0.0) <= (right_min - float(embargo_seconds))
    )
    purged_right = tuple(
        r
        for r in right
        if float(r.event_time_epoch_seconds or 0.0) >= (left_max + float(embargo_seconds))
        or float(r.event_time_epoch_seconds or 0.0) >= right_min
    )
    # Keep right side chronologically after left + embargo when both nonempty.
    if purged_left and purged_right:
        boundary = max(float(r.event_time_epoch_seconds or 0.0) for r in purged_left)
        purged_right = tuple(
            r
            for r in purged_right
            if float(r.event_time_epoch_seconds or 0.0) >= boundary + float(embargo_seconds)
        )
    return purged_left, purged_right


def build_purged_chronological_splits_v1(
    records: Sequence[ResearchEvidenceRecordV1],
    *,
    split_contract: SplitAndEmbargoContractV1,
    access_holdout: bool = False,
) -> SplitAssignmentV1:
    ordered = _require_event_times(records)
    n = len(ordered)
    if n == 0:
        return SplitAssignmentV1(
            train=(),
            validation=(),
            holdout=(),
            embargo_seconds=split_contract.embargo_seconds,
            holdout_accessed=False,
            fold_id="empty",
        )

    holdout_n = max(1, int(round(n * split_contract.holdout_fraction))) if n >= 5 else 0
    if holdout_n >= n:
        holdout_n = max(0, n // 5)
    non_holdout = ordered[: n - holdout_n] if holdout_n else ordered
    holdout = tuple(ordered[n - holdout_n :]) if holdout_n else ()

    if holdout and non_holdout:
        non_holdout_t, holdout = _purge_with_embargo(
            non_holdout,
            holdout,
            embargo_seconds=split_contract.embargo_seconds,
        )
        non_holdout = list(non_holdout_t)

    train_n = int(len(non_holdout) * split_contract.train_fraction_within_non_holdout)
    train = tuple(non_holdout[:train_n])
    validation = tuple(non_holdout[train_n:])
    if train and validation:
        train, validation = _purge_with_embargo(
            train,
            validation,
            embargo_seconds=split_contract.embargo_seconds,
        )

    if access_holdout is False:
        # Seal holdout identities until final evaluation.
        sealed_holdout = holdout
        holdout_accessed = False
    else:
        sealed_holdout = holdout
        holdout_accessed = True

    _assert_chronological(train, validation, sealed_holdout if holdout_accessed else ())
    _assert_embargo(
        train,
        validation,
        sealed_holdout if holdout_accessed else (),
        embargo_seconds=split_contract.embargo_seconds,
    )

    return SplitAssignmentV1(
        train=train,
        validation=validation,
        holdout=sealed_holdout,
        embargo_seconds=split_contract.embargo_seconds,
        holdout_accessed=holdout_accessed,
        fold_id="primary_purged_split",
    )


def build_walk_forward_folds_v1(
    records: Sequence[ResearchEvidenceRecordV1],
    *,
    split_contract: SplitAndEmbargoContractV1,
) -> tuple[SplitAssignmentV1, ...]:
    ordered = _require_event_times(records)
    n = len(ordered)
    folds = split_contract.walk_forward_folds
    if n < folds + 2:
        primary = build_purged_chronological_splits_v1(
            ordered, split_contract=split_contract, access_holdout=False
        )
        return (primary,)

    holdout_n = max(1, int(round(n * split_contract.holdout_fraction)))
    researchable = ordered[: n - holdout_n]
    holdout = tuple(ordered[n - holdout_n :])
    out: list[SplitAssignmentV1] = []
    for fold_idx in range(folds):
        # Anchored expanding walk-forward on researchable segment only.
        cut = int(len(researchable) * ((fold_idx + 1) / (folds + 1)))
        if cut < 1 or cut >= len(researchable):
            continue
        train_raw = tuple(researchable[:cut])
        val_raw = tuple(researchable[cut:])
        train, validation = _purge_with_embargo(
            train_raw,
            val_raw,
            embargo_seconds=split_contract.embargo_seconds,
        )
        out.append(
            SplitAssignmentV1(
                train=train,
                validation=validation,
                holdout=holdout,
                embargo_seconds=split_contract.embargo_seconds,
                holdout_accessed=False,
                fold_id=f"walk_forward_{fold_idx + 1}",
            )
        )
    if not out:
        return (
            build_purged_chronological_splits_v1(
                ordered, split_contract=split_contract, access_holdout=False
            ),
        )
    return tuple(out)


def access_final_holdout_v1(
    sealed: SplitAssignmentV1,
) -> SplitAssignmentV1:
    """Explicit final-holdout access — only for terminal evaluation."""
    return SplitAssignmentV1(
        train=sealed.train,
        validation=sealed.validation,
        holdout=sealed.holdout,
        embargo_seconds=sealed.embargo_seconds,
        holdout_accessed=True,
        fold_id=f"{sealed.fold_id}_final_holdout",
    )


def _assert_chronological(
    train: Sequence[ResearchEvidenceRecordV1],
    validation: Sequence[ResearchEvidenceRecordV1],
    holdout: Sequence[ResearchEvidenceRecordV1],
) -> None:
    def _times(rows: Sequence[ResearchEvidenceRecordV1]) -> list[float]:
        return [float(r.event_time_epoch_seconds or 0.0) for r in rows]

    for rows in (train, validation, holdout):
        ts = _times(rows)
        if ts != sorted(ts):
            raise MaxAgeResearchExecutionError("split_not_chronological")
    if train and validation and max(_times(train)) > min(_times(validation)):
        raise MaxAgeResearchExecutionError("split_train_validation_overlap")
    if validation and holdout and max(_times(validation)) > min(_times(holdout)):
        raise MaxAgeResearchExecutionError("split_validation_holdout_overlap")
    if train and holdout and max(_times(train)) > min(_times(holdout)):
        raise MaxAgeResearchExecutionError("split_train_holdout_overlap")


def _assert_embargo(
    train: Sequence[ResearchEvidenceRecordV1],
    validation: Sequence[ResearchEvidenceRecordV1],
    holdout: Sequence[ResearchEvidenceRecordV1],
    *,
    embargo_seconds: int,
) -> None:
    def _gap_ok(
        left: Sequence[ResearchEvidenceRecordV1],
        right: Sequence[ResearchEvidenceRecordV1],
    ) -> bool:
        if not left or not right:
            return True
        return (
            min(float(r.event_time_epoch_seconds or 0.0) for r in right)
            - max(float(r.event_time_epoch_seconds or 0.0) for r in left)
        ) >= float(embargo_seconds)

    if not _gap_ok(train, validation):
        raise MaxAgeResearchExecutionError("embargo_violation_train_validation")
    if not _gap_ok(validation, holdout):
        raise MaxAgeResearchExecutionError("embargo_violation_validation_holdout")
    if not _gap_ok(train, holdout):
        raise MaxAgeResearchExecutionError("embargo_violation_train_holdout")
