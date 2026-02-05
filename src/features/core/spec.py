from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Literal, Sequence, Mapping, Any
import pandas as pd

Freq = Literal["1m", "5m", "15m", "1h", "4h", "1d"]


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    version: str
    freq: Freq
    lookback: int
    warmup: int = 0
    allow_na: bool = False
    description: str = ""


FeatureFn = Callable[[pd.DataFrame, Mapping[str, Any]], pd.DataFrame]
