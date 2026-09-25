"""
Standardisierte Student-t-Innovationen (nur NumPy, NO-LIVE synthetische Pfade).

Konstruktion: Z ~ N(0,1), V ~ chi²(ν) unabhängig ⇒ Z/√(V/ν) ~ t(ν).
Skalierung mit √((ν−2)/ν) liefert Varianz 1 für ν > 2.
"""

from __future__ import annotations

import numpy as np


def sample_standardized_student_t(rng: np.random.Generator, nu: float) -> float:
    """
    Eine standardisierte Student-t-Ziehung mit Varianz 1.

    Args:
        rng: NumPy-Generator (reproduzierbar).
        nu: Freiheitsgrade (muss > 2 sein).

    Raises:
        ValueError: Wenn nu <= 2.
    """
    if nu <= 2:
        raise ValueError(f"nu must be > 2 for finite variance, got {nu}")
    z = rng.standard_normal()
    v = rng.chisquare(nu)
    t_raw = z / np.sqrt(v / nu)
    scale = np.sqrt((nu - 2) / nu)
    return float(t_raw * scale)
