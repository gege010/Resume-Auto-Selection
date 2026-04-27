"""
Simple Additive Weighting (SAW) — benefit-type normalization.

  r_ij = x_ij / max(x_j)          (benefit)
  score_i = Σ w_j × r_ij
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def run_saw(
    decision_matrix: pd.DataFrame,
    weights: list[float],
) -> pd.Series:
    """
    Compute SAW scores.

    Args:
        decision_matrix: rows = candidates, columns = criteria (all benefit).
        weights: list of weights summing to ~1, matching column order.

    Returns:
        pd.Series of scores indexed like decision_matrix.
    """
    dm = decision_matrix.values.astype(float)
    w  = np.array(weights, dtype=float)
    w  = w / w.sum()                       # ensure sums to 1

    col_max = dm.max(axis=0)
    col_max = np.where(col_max == 0, 1, col_max)   # avoid div-by-zero
    r = dm / col_max                                 # normalized matrix

    scores = (r * w).sum(axis=1)
    return pd.Series(scores, index=decision_matrix.index, name="SAW")
