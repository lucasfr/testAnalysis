"""
condor.io.base
==============
Abstract base class for all actigraph file readers.

Every brand-specific reader must subclass AbstractReader and implement
the `read()` method, returning a standardised pandas DataFrame with at
least the columns listed in REQUIRED_COLUMNS.

Required output columns
-----------------------
datetime    : datetime64[ns]  — epoch timestamp (timezone-naive)
activity    : float64         — activity count for the epoch
int_temp    : float64         — internal (on-body) temperature, °C
ext_temp    : float64         — external (ambient) temperature, °C  (NaN if unavailable)
ZCMn        : float64         — zero-crossing mode count            (NaN if unavailable)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"datetime", "activity", "int_temp", "ext_temp", "ZCMn"}


class AbstractReader(ABC):
    """Base class for actigraph file readers.

    Parameters
    ----------
    path : str or Path
        Path to the raw actigraph data file.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")

    @abstractmethod
    def read(self) -> pd.DataFrame:
        """Parse the file and return a standardised DataFrame.

        Returns
        -------
        pd.DataFrame
            Must contain at minimum all columns in REQUIRED_COLUMNS.
            Index should be a default RangeIndex; datetime lives in a column.
        """
        ...

    def _validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Check that all required columns are present after reading."""
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(
                f"{self.__class__.__name__}.read() is missing required columns: {missing}"
            )
        return df
