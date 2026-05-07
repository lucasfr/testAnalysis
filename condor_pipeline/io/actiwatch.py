"""
condor.io.actiwatch
===================
Reader stub for Philips Respironics / Philips Actiwatch files.

Actiwatch exports come in several formats depending on firmware and
software version (Actiware .AWD, .CSV exports, Actiwatch Spectrum CSV).
This module is a placeholder — implement `read()` once sample files
are available.
"""

from __future__ import annotations

import pandas as pd

from condor_pipeline.io.base import AbstractReader


class ActiwatchReader(AbstractReader):
    """Read a Philips Actiwatch file into a standardised DataFrame.

    Not yet implemented — raise NotImplementedError until a concrete
    format is confirmed.
    """

    def read(self) -> pd.DataFrame:
        raise NotImplementedError(
            "ActiwatchReader is not yet implemented. "
            "Contribute a parser at condor/io/actiwatch.py."
        )
