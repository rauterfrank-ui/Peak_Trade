from __future__ import annotations
import hashlib
import json
from typing import Any, Mapping, Sequence
import pandas as pd
from ..core.registry import FeatureRegistry


def stable_hash(obj: Any) -> str:
    b = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b).hexdigest()[:16]


def build_features(
    df: pd.DataFrame,
    registry: FeatureRegistry,
    requested: Sequence[Mapping[str, Any]],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    manifest = {"requested": requested}
    out = pd.DataFrame(index=df.index)
    for req in requested:
        rf = registry.get(req["name"], req["version"])
        params = {**rf.default_params, **req.get("params", {})}
        feat_df = rf.fn(df, params)
        if not isinstance(feat_df, pd.DataFrame):
            raise TypeError("feature fn must return DataFrame")
        out = out.join(feat_df, how="left")
    manifest["hash"] = stable_hash(manifest)
    return out, manifest
