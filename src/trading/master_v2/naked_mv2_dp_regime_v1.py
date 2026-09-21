"""Shared naked MV2+DP regime identity (BULL/BEAR)."""

from __future__ import annotations

from enum import Enum


class NakedRegimeV1(str, Enum):
    BULL = "bull"
    BEAR = "bear"


__all__ = ["NakedRegimeV1"]
