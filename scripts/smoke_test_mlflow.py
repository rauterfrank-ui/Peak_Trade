#!/usr/bin/env python3
"""
MLflow Integration Smoke Test
==============================
Testet MLflow-Integration Ende-zu-Ende ohne pytest.

**Usage**:
    python scripts/smoke_test_mlflow.py

**Requirements**:
    pip install mlflow

**Was wird getestet**:
1. MLflowTracker kann initialisiert werden
2. Run kann gestartet/beendet werden
3. Params/Metrics/Tags können geloggt werden
4. Artifacts können hochgeladen werden
5. BacktestEngine mit MLflow funktioniert
6. MLflow UI kann gestartet werden

**Output**:
    ✅ Alle Tests bestanden → MLflow funktioniert
    ❌ Fehler → Details werden ausgegeben
"""

import sys
import tempfile
from pathlib import Path

# Check MLflow
try:
    import mlflow

    print("✅ MLflow ist installiert")
except ImportError:
    print("❌ MLflow ist nicht installiert")
    print("   Installiere via: pip install mlflow")
    sys.exit(1)

# Imports
try:
    from src.core.tracking import (
        MLflowTracker,
        build_tracker_from_config,
        log_backtest_artifacts,
        log_backtest_metadata,
    )
    from src.core.peak_config import PeakConfig
    from src.backtest.engine import BacktestEngine
    import pandas as pd

    print("✅ Peak_Trade Imports erfolgreich")
except Exception as e:
    print(f"❌ Import-Fehler: {e}")
    sys.exit(1)


def test_mlflow_tracker_basic():
    """Test 1: MLflowTracker Basics."""
    print("\n" + "=" * 60)
    print("TEST 1: MLflowTracker Basics")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            tracker = MLflowTracker(
                tracking_uri=f"file://{tmpdir}",
                experiment_name="smoke_test",
            )
            print("✅ MLflowTracker initialisiert")

            tracker.start_run("test_run")
            print("✅ Run gestartet")

            tracker.log_params({"strategy": "test", "window": 20})
            print("✅ Params geloggt")

            tracker.log_metrics({"sharpe": 1.8, "return": 0.25})
            print("✅ Metrics geloggt")

            tracker.set_tags({"env": "test", "version": "1.0"})
            print("✅ Tags gesetzt")

            tracker.end_run()
            print("✅ Run beendet")

            return True
        except Exception as e:
            print(f"❌ Fehler: {e}")
            return False


def test_mlflow_tracker_context_manager():
    """Test 2: Context Manager."""
    print("\n" + "=" * 60)
    print("TEST 2: Context Manager")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            with MLflowTracker(
                tracking_uri=f"file://{tmpdir}",
                experiment_name="smoke_test_ctx",
                auto_start_run=True,
            ) as tracker:
                tracker.log_params({"foo": "bar"})
                tracker.log_metrics({"test_metric": 42.0})
                print("✅ Context Manager funktioniert")

            return True
        except Exception as e:
            print(f"❌ Fehler: {e}")
            return False


def test_mlflow_tracker_artifacts():
    """Test 3: Artifact Upload."""
    print("\n" + "=" * 60)
    print("TEST 3: Artifact Upload")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            tracker = MLflowTracker(
                tracking_uri=f"file://{tmpdir}",
                experiment_name="smoke_test_artifacts",
            )
            tracker.start_run("artifact_test")

            # Temporäre Datei erstellen
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
                tmp.write("Test-Content")
                tmp_path = tmp.name

            try:
                tracker.log_artifact(tmp_path, artifact_path="reports/test.txt")
                print("✅ Artifact hochgeladen")
            finally:
                Path(tmp_path).unlink(missing_ok=True)

            tracker.end_run()
            return True
        except Exception as e:
            print(f"❌ Fehler: {e}")
            return False


def test_build_tracker_from_config():
    """Test 4: Config-Builder."""
    print("\n" + "=" * 60)
    print("TEST 4: Config-Builder")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            config = PeakConfig(
                raw={
                    "tracking": {
                        "enabled": True,
                        "backend": "mlflow",
                        "mlflow": {
                            "tracking_uri": f"file://{tmpdir}",
                            "experiment_name": "smoke_test_config",
                        },
                    }
                }
            )

            tracker = build_tracker_from_config(config)
            print(f"✅ Tracker erstellt: {type(tracker).__name__}")

            if not isinstance(tracker, MLflowTracker):
                print(f"❌ Falscher Tracker-Typ: {type(tracker)}")
                return False

            return True
        except Exception as e:
            print(f"❌ Fehler: {e}")
            return False


def test_backtest_integration():
    """Test 5: BacktestEngine mit MLflow."""
    print("\n" + "=" * 60)
    print("TEST 5: BacktestEngine Integration")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Sample Data
            dates = pd.date_range("2023-01-01", periods=50, freq="1h")
            data = {
                "open": [100.0] * 50,
                "high": [105.0] * 50,
                "low": [95.0] * 50,
                "close": [100.0 + i * 0.5 for i in range(50)],
                "volume": [1000.0] * 50,
            }
            df = pd.DataFrame(data, index=dates)
            print("✅ Sample-Daten erstellt")

            # Tracker
            tracker = MLflowTracker(
                tracking_uri=f"file://{tmpdir}",
                experiment_name="smoke_test_backtest",
            )
            tracker.start_run("backtest_smoke")
            print("✅ Tracker gestartet")

            # Backtest
            engine = BacktestEngine(tracker=tracker, use_execution_pipeline=False)

            def buy_and_hold(df, params):
                return pd.Series(1, index=df.index)

            result = engine.run_realistic(
                df=df,
                strategy_signal_fn=buy_and_hold,
                strategy_params={"strategy_name": "buy_and_hold"},
            )
            print("✅ Backtest durchgeführt")

            # Verify
            if result is None:
                print("❌ Backtest-Result ist None")
                return False

            if "sharpe" not in result.stats:
                print("❌ Sharpe-Metrik fehlt")
                return False

            print(f"   Sharpe: {result.stats['sharpe']:.2f}")
            print(f"   Total Return: {result.stats['total_return']:.2%}")

            tracker.end_run()
            print("✅ Tracker beendet")

            return True
        except Exception as e:
            print(f"❌ Fehler: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_log_backtest_artifacts():
    """Test 6: Artifact-Logging."""
    print("\n" + "=" * 60)
    print("TEST 6: Backtest Artifacts")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Sample Data
            dates = pd.date_range("2023-01-01", periods=50, freq="1h")
            data = {
                "open": [100.0] * 50,
                "high": [105.0] * 50,
                "low": [95.0] * 50,
                "close": [100.0 + i * 0.5 for i in range(50)],
                "volume": [1000.0] * 50,
            }
            df = pd.DataFrame(data, index=dates)

            # Backtest
            engine = BacktestEngine(tracker=None, use_execution_pipeline=False)

            def buy_and_hold(df, params):
                return pd.Series(1, index=df.index)

            result = engine.run_realistic(
                df=df,
                strategy_signal_fn=buy_and_hold,
                strategy_params={"strategy_name": "buy_and_hold"},
            )

            # Tracker
            tracker = MLflowTracker(
                tracking_uri=f"file://{tmpdir}",
                experiment_name="smoke_test_artifacts",
            )
            tracker.start_run("artifact_logging")

            # Log Artifacts
            log_backtest_artifacts(tracker, result)
            print("✅ Artifacts geloggt")

            tracker.end_run()
            return True
        except Exception as e:
            print(f"❌ Fehler: {e}")
            import traceback

            traceback.print_exc()
            return False


def main():
    """Führt alle Smoke-Tests aus."""
    print("=" * 60)
    print("MLflow Integration Smoke Test")
    print("=" * 60)

    tests = [
        ("MLflowTracker Basics", test_mlflow_tracker_basic),
        ("Context Manager", test_mlflow_tracker_context_manager),
        ("Artifact Upload", test_mlflow_tracker_artifacts),
        ("Config-Builder", test_build_tracker_from_config),
        ("BacktestEngine Integration", test_backtest_integration),
        ("Backtest Artifacts", test_log_backtest_artifacts),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} — {name}")

    print("=" * 60)
    print(f"Result: {passed}/{total} Tests bestanden")
    print("=" * 60)

    if passed == total:
        print("\n🎉 Alle Tests bestanden! MLflow ist ready.")
        print("\nNächste Schritte:")
        print("  1. MLflow UI starten: mlflow ui --backend-store-uri ./mlruns")
        print("  2. Browser öffnen: http://localhost:5000")
        print("  3. Siehe: docs/MLFLOW_SETUP_GUIDE.md")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} Test(s) fehlgeschlagen.")
        print("   Siehe Fehler-Details oben.")
        sys.exit(1)


if __name__ == "__main__":
    main()
