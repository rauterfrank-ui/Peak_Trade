"""Fail-closed models for R5 realistic sim/replay semantics v1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class RealisticSimReplaySemanticsError(ValueError):
    """Fail-closed R5 sim/replay semantics error."""


class ModeClass(str, Enum):
    SIMULATION = "SIMULATION"
    PAPER = "PAPER"
    REPLAY = "REPLAY"
    SHADOW = "SHADOW"
    PRODUCTIVE_SHADOW = "PRODUCTIVE_SHADOW"
    PAPER_EXCHANGE = "PAPER_EXCHANGE"


class SurfaceId(str, Enum):
    CAP7_INTERNAL_SIM = "CAP7_INTERNAL_SIM"
    CAP7_OFFLINE_MD_REPLAY = "CAP7_OFFLINE_MD_REPLAY"
    I67_PAPER_SIM = "I67_PAPER_SIM"
    I79_REPLAY_PACK = "I79_REPLAY_PACK"
    I17_PRODUCTIVE_SHADOW = "I17_PRODUCTIVE_SHADOW"


class EquivalenceClass(str, Enum):
    DISTINCT = "DISTINCT"
    NOT_PROVEN = "NOT_PROVEN"
    FORBIDDEN_NAME_COLLISION = "FORBIDDEN_NAME_COLLISION"


@dataclass(frozen=True)
class ModeSemanticsRowV1:
    dimension: str
    cap7_internal_sim: str
    cap7_offline_md_replay: str
    i67_paper_sim: str
    i79_replay_pack: str
    i17_productive_shadow: str
    equivalence: EquivalenceClass

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "dimension": self.dimension,
                "cap7_internal_sim": self.cap7_internal_sim,
                "cap7_offline_md_replay": self.cap7_offline_md_replay,
                "i67_paper_sim": self.i67_paper_sim,
                "i79_replay_pack": self.i79_replay_pack,
                "i17_productive_shadow": self.i17_productive_shadow,
                "equivalence": self.equivalence.value,
            }
        )


@dataclass(frozen=True)
class ModeClassRowV1:
    mode: ModeClass
    meaning: str
    canonical_surface: str
    authority_effect: str
    promotion_eligible: bool
    order_effect: str

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "mode": self.mode.value,
                "meaning": self.meaning,
                "canonical_surface": self.canonical_surface,
                "authority_effect": self.authority_effect,
                "promotion_eligible": self.promotion_eligible,
                "order_effect": self.order_effect,
            }
        )
