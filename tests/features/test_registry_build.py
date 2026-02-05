import pandas as pd
from src.features.core.spec import FeatureSpec
from src.features.core.registry import FeatureRegistry
from src.features.builders.build import build_features


def test_build_features_smoke():
    df = pd.DataFrame({"close": [1, 2, 3]}, index=pd.RangeIndex(3))
    reg = FeatureRegistry()

    def f(in_df, params):
        return pd.DataFrame({"ret": in_df["close"].pct_change()}, index=in_df.index)

    reg.register(FeatureSpec(name="ret", version="1", freq="1d", lookback=1), f)
    feats, manifest = build_features(df, reg, [{"name": "ret", "version": "1"}])
    assert "ret" in feats.columns
    assert "hash" in manifest
