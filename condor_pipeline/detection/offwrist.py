"""
condor.detection.offwrist
==========================
Off-wrist detection using the Condor bimodal activity/temperature model.

Wraps the vendor ``offwrist_wrapper_acttrust`` module (bundled under
condor/algorithms/vendor/condor/) and provides a clean function interface
plus a CSV export compatible with pyActigraphy's mask format.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_VENDOR_DIR = Path(__file__).resolve().parents[1] / "algorithms" / "vendor" / "condor"


def detect_offwrist(df: pd.DataFrame) -> pd.DataFrame:
    """Run the Condor bimodal offwrist detector and update *df* in place.

    Off-wrist epochs are marked as ``state == 4``.  The ``offwrist``
    column is set to 0.25 for off-wrist epochs (scaled for actogram
    overlay plotting).

    Parameters
    ----------
    df : pd.DataFrame
        Prepared DataFrame from :func:`condor.preprocessing.prepare`.
        Must contain columns: ``datetime``, ``activity`` (PIM),
        ``int_temp``, ``ext_temp``, ``state``, ``offwrist``.

    Returns
    -------
    pd.DataFrame
        The same DataFrame with ``state`` and ``offwrist`` updated.
    """
    vendor_str = str(_VENDOR_DIR)
    if vendor_str not in sys.path:
        sys.path.insert(0, vendor_str)

    from bimodal_offwrist_wrapper_acttrust_without_prints import (  # noqa: PLC0415
        offwrist_wrapper_acttrust as _offwrist_wrapper,
    )

    # The vendor wrapper expects the original column names
    df_renamed = df.rename(columns={
        "datetime": "DATE/TIME",
        "int_temp": "TEMPERATURE",
        "ext_temp": "EXT TEMPERATURE",
        "activity": "PIM",
    })

    out = _offwrist_wrapper(df_renamed)
    df["state"]    = out
    df["offwrist"] = 0.25 * out
    return df


def export_offwrist_csv(
    df: pd.DataFrame,
    source_file: str | Path,
) -> Path:
    """Export detected off-wrist periods to a pyActigraphy-compatible CSV.

    Each contiguous off-wrist interval (``state == 4``) becomes one row
    with columns: ``Subject_id``, ``Start_time``, ``Stop_time``,
    ``Remarks``.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame after :func:`detect_offwrist` has been run.
    source_file : str or Path
        Path to the original input file — used to derive the subject ID
        and the output filename.

    Returns
    -------
    Path
        Path to the CSV file that was written (``<stem>_OffWrist.csv``
        next to *source_file*).
    """
    source_file = Path(source_file)
    file_stem   = source_file.stem

    _match     = re.search(r"([A-Za-z0-9]+)", file_stem)
    subject_id = _match.group(1) if _match else file_stem

    state_col     = df["state"]
    state_shifted = state_col.shift(1, fill_value=0)

    is_start = (state_col == 4) & (state_shifted != 4)
    is_end   = (state_col != 4) & (state_shifted == 4)

    start_times = df.index[is_start]
    end_times   = df.index[is_end]

    if len(start_times) > len(end_times):
        end_times = end_times.append(pd.Index([df.index[-1]]))

    intervals = [
        {
            "Subject_id": subject_id,
            "Start_time": df.loc[s, "datetime"],
            "Stop_time":  df.loc[e, "datetime"],
            "Remarks":    "OffWrist detected automatically by bimodal algorithm",
        }
        for s, e in zip(start_times, end_times)
    ]

    offwrist_df = pd.DataFrame(intervals)
    output_path = source_file.parent / f"{file_stem}_OffWrist.csv"
    offwrist_df.to_csv(output_path, index=False)

    return output_path
