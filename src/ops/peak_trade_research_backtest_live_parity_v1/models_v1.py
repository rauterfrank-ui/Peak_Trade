"""DTOs for B09 research/backtest/shadow/productive ranking parity evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from src.ops.archive_sibling_export_contract_v1.canonical_digest import canonical_digest_v1


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class ModeParityWitnessV1:
    mode: str
    ok: bool
    feature_witness: tuple[Mapping[str, Any], ...]
    rank_witness: tuple[Mapping[str, Any], ...]
    config_identity: Mapping[str, Any]
    temporal_witness: tuple[Mapping[str, Any], ...]
    failure_codes: tuple[str, ...] = ()

    def comparable_payload(self) -> dict[str, Any]:
        return {
            "feature_witness": [dict(row) for row in self.feature_witness],
            "rank_witness": [dict(row) for row in self.rank_witness],
            "config_identity": dict(self.config_identity),
            "temporal_witness": [dict(row) for row in self.temporal_witness],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "ok": bool(self.ok),
            **self.comparable_payload(),
            "failure_codes": list(self.failure_codes),
        }


@dataclass(frozen=True)
class ParityProofV1:
    package_id: str
    parity_version: str
    repository_sha: str
    modes: tuple[ModeParityWitnessV1, ...]
    authority: Mapping[str, Any]
    path_classification: tuple[Mapping[str, str], ...]
    feature_formula_parity_proven: bool
    rank_order_parity_proven: bool
    config_version_parity_proven: bool
    temporal_no_lookahead_proven: bool
    productive_only_economic_formula_count: int
    duplicated_equivalent_path_count: int
    divergent_current_path_count: int
    legacy_not_current_path_count: int
    not_applicable_path_count: int
    integrity_digest: str = ""
    failure_codes: tuple[str, ...] = field(default_factory=tuple)

    def deterministic_payload_for_digest(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("integrity_digest", None)
        return payload

    def compute_integrity_digest(self) -> str:
        return canonical_digest_v1(self.deterministic_payload_for_digest())

    def with_integrity_digest(self) -> ParityProofV1:
        return ParityProofV1(
            package_id=self.package_id,
            parity_version=self.parity_version,
            repository_sha=self.repository_sha,
            modes=self.modes,
            authority=dict(self.authority),
            path_classification=self.path_classification,
            feature_formula_parity_proven=self.feature_formula_parity_proven,
            rank_order_parity_proven=self.rank_order_parity_proven,
            config_version_parity_proven=self.config_version_parity_proven,
            temporal_no_lookahead_proven=self.temporal_no_lookahead_proven,
            productive_only_economic_formula_count=self.productive_only_economic_formula_count,
            duplicated_equivalent_path_count=self.duplicated_equivalent_path_count,
            divergent_current_path_count=self.divergent_current_path_count,
            legacy_not_current_path_count=self.legacy_not_current_path_count,
            not_applicable_path_count=self.not_applicable_path_count,
            integrity_digest=self.compute_integrity_digest(),
            failure_codes=self.failure_codes,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "parity_version": self.parity_version,
            "repository_sha": self.repository_sha,
            "modes": [mode.to_dict() for mode in self.modes],
            "authority": dict(sorted(self.authority.items())),
            "path_classification": [dict(row) for row in self.path_classification],
            "feature_formula_parity_proven": bool(self.feature_formula_parity_proven),
            "rank_order_parity_proven": bool(self.rank_order_parity_proven),
            "config_version_parity_proven": bool(self.config_version_parity_proven),
            "temporal_no_lookahead_proven": bool(self.temporal_no_lookahead_proven),
            "productive_only_economic_formula_count": int(
                self.productive_only_economic_formula_count
            ),
            "duplicated_equivalent_path_count": int(self.duplicated_equivalent_path_count),
            "divergent_current_path_count": int(self.divergent_current_path_count),
            "legacy_not_current_path_count": int(self.legacy_not_current_path_count),
            "not_applicable_path_count": int(self.not_applicable_path_count),
            "integrity_digest": self.integrity_digest,
            "failure_codes": list(self.failure_codes),
        }
