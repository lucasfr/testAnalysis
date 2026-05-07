"""
condor.io.acttrust
==================
Reader for Condor Instruments ActTrust actigraph files.

ActTrust files are tab-delimited .txt exports with a variable-length
header block followed by epoch rows.  The header ends at the line that
begins with "DATE/TIME".

This reader uses the Condor vendor module `LogRead` (bundled under
condor/algorithms/vendor/condor/) to do the low-level parsing, then
maps the raw columns to the standardised schema defined in base.py.

Column mapping
--------------
Raw ActTrust column   →  Standard column
──────────────────────────────────────────
DATE/TIME             →  datetime
PIM                   →  activity
TEMPERATURE           →  int_temp
EXT TEMPERATURE       →  ext_temp
ZCMn                  →  ZCMn          (kept as-is)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from condor_pipeline.io.base import AbstractReader

# Resolve the vendor directory so LogRead can be imported
_VENDOR_DIR = Path(__file__).resolve().parents[1] / "algorithms" / "vendor" / "condor"


class ActTrustReader(AbstractReader):
    """Read a Condor ActTrust .txt file into a standardised DataFrame.

    Parameters
    ----------
    path : str or Path
        Path to the ActTrust export file.
    """

    # Mapping from raw ActTrust column names → standard names
    _COLUMN_MAP: dict[str, str] = {
        "DATE/TIME":       "datetime",
        "PIM":             "activity",
        "TEMPERATURE":     "int_temp",
        "EXT TEMPERATURE": "ext_temp",
        # ZCMn is kept with the same name
    }

    def read(self) -> pd.DataFrame:
        """Parse the ActTrust file and return a standardised DataFrame."""
        # Add vendor dir to path so LogRead can be imported
        vendor_str = str(_VENDOR_DIR)
        if vendor_str not in sys.path:
            sys.path.insert(0, vendor_str)

        try:
            from logread import LogRead as lr  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "Could not import LogRead from the Condor vendor directory. "
                f"Expected location: {_VENDOR_DIR}\n"
                "Run the setup script to download the vendor dependencies."
            ) from exc

        df: pd.DataFrame = lr(str(self.path)).data

        # LogRead sets DATE/TIME as both index and column — just drop the index
        if df.index.name == "DATE/TIME":
            df = df.reset_index(drop=True)

        # Rename to standard column names
        df = df.rename(columns=self._COLUMN_MAP)

        # Ensure datetime column is proper datetime dtype
        df["datetime"] = pd.to_datetime(df["datetime"])

        # ext_temp may be absent on some ActTrust firmware versions
        if "ext_temp" not in df.columns:
            df["ext_temp"] = np.nan

        # ZCMn may be absent on some firmware versions
        if "ZCMn" not in df.columns:
            df["ZCMn"] = np.nan

        return self._validate(df)
