from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ReadinessCheckV1:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class OnlineReadinessReportV1:
    version: str
    checks: List[ReadinessCheckV1]

    def to_dict(self) -> Dict:
        return {
            "version": self.version,
            "checks": [{"name": c.name, "ok": c.ok, "detail": c.detail} for c in self.checks],
        }


def build_online_readiness_report_v1(*, checks: List[ReadinessCheckV1]) -> OnlineReadinessReportV1:
    return OnlineReadinessReportV1(version="online_readiness_contract_v1", checks=checks)
