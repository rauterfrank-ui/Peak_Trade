#!/usr/bin/env bash
# NO-LIVE: Offline-Demo der Forward-Pipeline (dummy OHLCV) — Generate → CSV-Anpassung
# (as_of nicht auf letzter Bar, damit Evaluate einen Entry hat) → Evaluate.
# Siehe RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md — Stufe J / Forward-Pipeline.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
OUT="${ROOT}/.ops_local/forward_dummy_pipeline_demo"
RUN_NAME="forward_dummy_pipeline_demo"
CSV="${OUT}/${RUN_NAME}_signals.csv"

mkdir -p "$OUT"

echo "==> generate_forward_signals (dummy, ma_crossover, BTC/EUR)"
python3 scripts/generate_forward_signals.py \
  --strategy ma_crossover \
  --symbols BTC/EUR \
  --run-name "$RUN_NAME" \
  --output-dir "$OUT" \
  --ohlcv-source dummy \
  --n-bars 200

echo "==> as_of für auswertbare Signale setzen (mittelbar in der Serie, nicht letzte Bar)"
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('scripts').resolve()))
import pandas as pd
from _shared_ohlcv_loader import load_dummy_ohlcv
from generate_forward_signals import format_as_of_iso_utc

csv_path = Path(sys.argv[1])
df = pd.read_csv(csv_path)
df_price = load_dummy_ohlcv('BTC/EUR', n_bars=200)
# Genügend Bars nach as_of für horizon_bars=1 (vgl. Smoke-Test)
df.loc[0, 'as_of'] = format_as_of_iso_utc(df_price.index[-40])
df.to_csv(csv_path, index=False)
" "$CSV"

echo "==> evaluate_forward_signals"
python3 scripts/evaluate_forward_signals.py "$CSV" \
  --output-dir "$OUT" \
  --ohlcv-source dummy \
  --n-bars 200

echo "OK — Artefakte unter: $OUT"
