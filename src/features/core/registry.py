from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Mapping, Tuple
import pandas as pd
from .spec import FeatureSpec, FeatureFn

@dataclass
class RegisteredFeature:
    spec: FeatureSpec
    fn: FeatureFn
    default_params: Mapping[str, Any]

class FeatureRegistry:
    def __init__(self) -> None:
        self._items: Dict[Tuple[str,str], RegisteredFeature] = {}

    def register(self, spec: FeatureSpec, fn: FeatureFn, default_params: Mapping[str, Any] | None = None) -> None:
        key = (spec.name, spec.version)
        if key in self._items:
            raise ValueError(f"Feature already registered: {key}")
        self._items[key] = RegisteredFeature(spec=spec, fn=fn, default_params=default_params or {})

    def get(self, name: str, version: str) -> RegisteredFeature:
        return self._items[(name, version)]
