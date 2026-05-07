"""
condor.detection.sleep_periods
================================
Main sleep period and nap detection using the Condor Crespo algorithm.

Wraps the vendor modules ``cspd_wrapper`` and ``nap_wrapper`` (bundled
under condor/algorithms/vendor/condor/).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_VENDOR_DIR = Path(__file__).resolve().parents[1] / "algorithms" / "vendor" / "condor"


def _ensure_vendor() -> None:
    vendor_str = str(_VENDOR_DIR)
    if vendor_str not in sys.path:
        sys.path.insert(0, vendor_str)


def detect_sleep_periods(df: pd.DataFrame) -> pd.DataFrame:
    """Detect main sleep periods using the Crespo algorithm.

    Updates ``df["state"]`` and ``df["sleep"]`` in place.
    Off-wrist epochs (state == 4) are excluded from the sleep column.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared DataFrame after off-wrist detection.

    Returns
    -------
    pd.DataFrame
        The same DataFrame with ``state`` and ``sleep`` updated.
    """
    _ensure_vendor()
    from cspd_wrapper_without_prints import cspd_wrapper  # noqa: PLC0415

    out          = cspd_wrapper(df)
    df["state"]  = out
    df["sleep"]  = np.where(out == 4, 0, out)   # exclude off-wrist
    return df


def detect_naps(df: pd.DataFrame) -> pd.DataFrame:
    """Detect secondary sleep periods (naps) using the Crespo nap algorithm.

    Runs after :func:`detect_sleep_periods`.  Nap epochs (state == 7)
    are merged into the ``sleep`` column as value 1.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame after main sleep period detection.

    Returns
    -------
    pd.DataFrame
        The same DataFrame with ``state`` and ``sleep`` updated.
    """
    _ensure_vendor()
    from nap_wrapper_without_prints import nap_wrapper  # noqa: PLC0415

    out          = nap_wrapper(df)
    df["state"]  = out
    df["sleep"]  = np.where(out == 7, 1, df["sleep"].to_numpy())
    return df
