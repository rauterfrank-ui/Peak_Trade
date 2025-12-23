"""
Tests für NoopTracker
=====================
Stellt sicher dass NoopTracker keine Exceptions wirft.
"""

from src.core.tracking import NoopTracker


class TestNoopTracker:
    """Tests für NoopTracker."""

    def test_noop_tracker_all_methods(self):
        """NoopTracker: Alle Methoden werfen keine Exceptions."""
        tracker = NoopTracker()

        # Sollte alles durchlaufen ohne Fehler
        tracker.start_run("test_run", tags={"env": "test"})
        tracker.log_params({"foo": "bar", "num": 42})
        tracker.log_metrics({"sharpe": 1.8, "return": 0.25})
        tracker.log_artifact("/nonexistent/path.txt")
        tracker.end_run(status="FINISHED")

        # Kein Output, keine Exceptions → Success

    def test_noop_tracker_large_data(self):
        """NoopTracker: Kann große Daten verarbeiten."""
        tracker = NoopTracker()

        tracker.start_run("large_test")

        # Große Dicts
        large_params = {f"param_{i}": i for i in range(1000)}
        large_metrics = {f"metric_{i}": float(i) for i in range(1000)}

        tracker.log_params(large_params)
        tracker.log_metrics(large_metrics)
        tracker.end_run()

        # Sollte instant sein

    def test_noop_tracker_multiple_runs(self):
        """NoopTracker: Mehrere Runs hintereinander."""
        tracker = NoopTracker()

        for i in range(10):
            tracker.start_run(f"run_{i}")
            tracker.log_params({"iteration": i})
            tracker.log_metrics({"value": float(i)})
            tracker.end_run()

        # Sollte keine Probleme geben

