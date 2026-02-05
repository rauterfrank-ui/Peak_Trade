import pandas as pd

from src.strategies.lopez_de_prado.meta_labeling_strategy import MetaLabelingStrategy


def test_meta_labeling_strategy_extract_features_uses_feature_engine():
    df = pd.DataFrame({"close": [100, 101, 102]}, index=pd.RangeIndex(3))

    s = MetaLabelingStrategy(
        config={
            "features": {
                "requested": [{"name": "ret_1", "version": "1", "params": {"col": "close"}}]
            }
        }
    )
    feats = s._extract_features(df)
    assert "ret_1" in feats.columns
