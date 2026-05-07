"""
condor.preprocessing.prepare
=============================
Transforms a raw standardised DataFrame (output of any AbstractReader)
into the working DataFrame expected by all detection modules.

Steps performed
---------------
1. Add state columns — ``state``, ``offwrist``, ``sleep`` — initialised to 0.
2. Clamp ``int_temp`` and ``ext_temp`` to the physiological range [0, 42] °C.
3. Add min-max scaled temperature columns ``int_temp_`` and ``ext_temp_``
   for plotting (range [0, 1]).

None of these steps modify the index or the original activity / datetime
columns.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* with state columns and scaled temperatures added.

    Parameters
    ----------
    df : pd.DataFrame
        Standardised DataFrame from any ``AbstractReader.read()`` call.
        Must contain ``int_temp`` and ``ext_temp`` columns.

    Returns
    -------
    pd.DataFrame
        New DataFrame (original is not modified) with additional columns:
        ``state``, ``offwrist``, ``sleep``, ``int_temp_``, ``ext_temp_``.
    """
    df = df.copy()

    # ── State columns ─────────────────────────────────────────────────────────
    df["state"]    = np.zeros(len(df), dtype=float)
    df["offwrist"] = np.zeros(len(df), dtype=float)
    df["sleep"]    = np.zeros(len(df), dtype=float)

    # ── Temperature clamping ─────────────────────────────────────────────────
    int_temp = np.clip(df["int_temp"].to_numpy(dtype=float), 0.0, 42.0)
    ext_temp = np.clip(df["ext_temp"].fillna(0).to_numpy(dtype=float), 0.0, 42.0)

    df["int_temp"] = int_temp
    df["ext_temp"] = ext_temp

    # ── Min-max scaling for plotting ─────────────────────────────────────────
    scale = max(int_temp.max(), ext_temp.max())
    if scale > 0:
        df["int_temp_"] = int_temp / scale
        df["ext_temp_"] = ext_temp / scale
    else:
        df["int_temp_"] = int_temp
        df["ext_temp_"] = ext_temp

    return df
