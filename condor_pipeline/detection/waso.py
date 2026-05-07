"""
condor.detection.waso
======================
WASO and nightly sleep statistics using the Cole-Kripke algorithm.

Scores each epoch within a detected sleep period as wake or sleep,
then computes per-night statistics: TBT, TST, WASO, SOL, SOI,
number of awakenings, and sleep efficiency.

Metric definitions
------------------
TBT  — Total Bed Time      : total epochs from bed time to get-up time
TST  — Total Sleep Time    : TBT − WASO − SOL − SOI
WASO — Wake After Sleep Onset: wake epochs between sleep onset and final wake
SOL  — Sleep Onset Latency : epochs from bed time to first sleep epoch
SOI  — Sleep Offset Inertia: epochs of wake at end of sleep period
eff  — Sleep Efficiency    : TST / TBT
nw   — Number of Awakenings: count of wake-onset transitions
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from condor_pipeline.algorithms.cole_kripke import ColeKripke

_VENDOR_DIR = Path(__file__).resolve().parents[1] / "algorithms" / "vendor" / "condor"


def detect_waso(
    df: pd.DataFrame,
    out: np.ndarray,
    wake_thresh: int = 60,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Score WASO and compute nightly sleep statistics.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared DataFrame after nap detection.
    out : np.ndarray
        State array (length == len(df)) from the last detection step.
    wake_thresh : int, optional
        Minimum wake bout duration (epochs) for ``nights_df``.
        Default is 60.

    Returns
    -------
    nights_data : pd.DataFrame
        One row per night / nap with columns:
        ``bts``, ``gts``, ``bt``, ``gt``, ``nap``,
        ``tbt``, ``waso``, ``sol``, ``soi``, ``tst``, ``nw``, ``eff``.
    df : pd.DataFrame
        The input DataFrame with ``state`` and ``sleep`` updated with
        epoch-level wake/sleep scoring.
    """
    vendor_str = str(_VENDOR_DIR)
    if vendor_str not in sys.path:
        sys.path.insert(0, vendor_str)

    from nights_df import nights_df  # noqa: PLC0415

    onwrist = np.where(out == 4, False, True)

    stamps = df["datetime"].to_numpy()[onwrist]
    zcm    = df["ZCMn"].to_numpy()[onwrist]

    n           = len(zcm)
    state       = np.zeros(n, dtype=float)
    in_bed      = out[onwrist]

    nights_data = nights_df(stamps, in_bed, wake_thresh=wake_thresh, search_gap=False)
    num_nights  = len(nights_data)

    waso = np.full(num_nights, np.nan)
    tbt  = np.full(num_nights, np.nan)
    tst  = np.full(num_nights, np.nan)
    sol  = np.full(num_nights, np.nan)
    soi  = np.full(num_nights, np.nan)
    nw   = np.full(num_nights, np.nan)
    eff  = np.full(num_nights, np.nan)
    bts, gts = [], []

    for i in range(num_nights):
        bt  = nights_data.at[i, "bt"]
        gt  = nights_data.at[i, "gt"]
        nap = nights_data.at[i, "nap"]

        bts.append(stamps[bt])
        gts.append(stamps[gt])

        cole = ColeKripke(zcm[bt:gt])
        cole.model()
        cpred = cole.filtered_weighted   # 0 = sleep, 1 = wake

        # Sleep onset latency — leading wake epochs
        latency = 0
        while latency < len(cpred) and cpred[latency] > 0:
            latency += 1

        # Sleep offset inertia — trailing wake epochs
        inertia = len(cpred) - 1
        while inertia > 0 and cpred[inertia] > 0:
            inertia -= 1

        num_awake = int(np.sum(np.where(np.diff(cpred) > 0, 1, 0)))

        sol[i]  = latency
        soi[i]  = len(cpred) - 1 - inertia
        waso[i] = np.sum(cpred[latency:inertia])
        nw[i]   = num_awake
        tbt[i]  = gt - bt
        tst[i]  = tbt[i] - waso[i] - soi[i] - sol[i]
        eff[i]  = tst[i] / tbt[i] if tbt[i] > 0 else np.nan

        state[bt:gt] = 7 - 7 * cpred if nap else 1 - cpred

    nights_data["tbt"]  = tbt
    nights_data["waso"] = waso
    nights_data["sol"]  = sol
    nights_data["soi"]  = soi
    nights_data["tst"]  = tst
    nights_data["nw"]   = nw
    nights_data["eff"]  = eff
    nights_data.insert(0, "gts", gts)
    nights_data.insert(0, "bts", bts)

    out[onwrist]  = state
    df["state"]   = out
    sleep         = np.where(out == 4, 0, out)
    df["sleep"]   = np.where(sleep == 7, 1, sleep)

    return nights_data, df
