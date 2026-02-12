# tests/reporting/test_quadrant_2x2_heatmap.py
"""
Tests für src/reporting/plots.py render_standard_2x2_heatmap_template.

Unit-Tests: callable, schreibt PNG, lehnt non-2x2 ab, deterministische Bildgröße.
Kein Netzwerk, keine externen Tools.
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("matplotlib")

from src.reporting.plots import (
    render_standard_2x2_heatmap_template,
    QUADRANT_2X2_FIGSIZE,
    DEFAULT_DPI,
)


class TestRenderStandard2x2HeatmapTemplate:
    """Tests für render_standard_2x2_heatmap_template()."""

    def test_callable_and_writes_png(self):
        """Funktion ist aufrufbar und schreibt eine PNG-Datei."""
        matrix = [[1.0, 2.0], [3.0, 4.0]]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "quadrant.png"
            result = render_standard_2x2_heatmap_template(matrix, out)
            assert result == str(out)
            assert out.exists()
            assert out.suffix == ".png"

    def test_rejects_non_2x2_input_1x1(self):
        """Lehnt 1x1 Matrix ab."""
        matrix = [[1.0]]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "q.png"
            with pytest.raises(ValueError, match="2x2"):
                render_standard_2x2_heatmap_template(matrix, out)
            assert not out.exists()

    def test_rejects_non_2x2_input_3x3(self):
        """Lehnt 3x3 Matrix ab."""
        matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "q.png"
            with pytest.raises(ValueError, match="2x2"):
                render_standard_2x2_heatmap_template(matrix, out)
            assert not out.exists()

    def test_rejects_non_2x2_input_2x3(self):
        """Lehnt 2x3 Matrix ab."""
        matrix = [[1, 2, 3], [4, 5, 6]]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "q.png"
            with pytest.raises(ValueError, match="2x2"):
                render_standard_2x2_heatmap_template(matrix, out)
            assert not out.exists()

    def test_deterministic_output_size(self):
        """Bildgröße ist deterministisch (Pixel-Dimensionen)."""
        matrix = [[0.5, 0.5], [0.5, 0.5]]
        with tempfile.TemporaryDirectory() as tmp:
            out1 = Path(tmp) / "q1.png"
            out2 = Path(tmp) / "q2.png"
            render_standard_2x2_heatmap_template(matrix, out1)
            render_standard_2x2_heatmap_template(matrix, out2)
            # PNG-Größe: figsize * dpi
            size1 = out1.stat().st_size
            size2 = out2.stat().st_size
            assert size1 == size2

    def test_accepts_numpy_array(self):
        """Akzeptiert numpy Array."""
        matrix = np.array([[1.0, 2.0], [3.0, 4.0]])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "q.png"
            render_standard_2x2_heatmap_template(matrix, out)
            assert out.exists()

    def test_quadrant_labels_optional(self):
        """Quadrant-Labels sind optional."""
        matrix = [[1.0, 2.0], [3.0, 4.0]]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "q.png"
            render_standard_2x2_heatmap_template(
                matrix,
                out,
                quadrant_labels=("TL", "TR", "BL", "BR"),
            )
            assert out.exists()
