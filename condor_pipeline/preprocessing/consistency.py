"""
condor.preprocessing.consistency
=================================
Timestamp quality checks on a standardised actigraphy DataFrame.

Checks performed
----------------
- **Gaps**: intervals between consecutive timestamps longer than
  ``duration`` seconds.
- **Backward jumps**: timestamps that go backwards in time.
- **Epoch artefacts**: timestamps suspiciously close to Unix epoch
  (year 1970) or the year-2000 rollover, which indicate firmware bugs.
"""

from __future__ import annotations

import pandas as pd


_ARTEFACT_YEARS = {1970, 2000}


def consistency_check(
    df: pd.DataFrame,
    duration: float = 120.0,
    datetime_col: str = "datetime",
) -> pd.DataFrame:
    """Check a standardised DataFrame for timestamp issues.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain a ``datetime`` column (or the column named by
        *datetime_col*) with datetime64 dtype.
    duration : float, optional
        Gap threshold in seconds. Gaps longer than this are flagged.
        Default is 120 s (2 minutes).
    datetime_col : str, optional
        Name of the datetime column. Default is ``"datetime"``.

    Returns
    -------
    pd.DataFrame
        A DataFrame of detected issues with columns:
        ``index``, ``datetime``, ``issue``, ``detail``.
        Empty if no issues are found.
    """
    times = pd.to_datetime(df[datetime_col])
    issues = []

    # ── Gap detection ─────────────────────────────────────────────────────────
    deltas = times.diff().dt.total_seconds()
    gap_mask = deltas > duration
    for idx in df.index[gap_mask]:
        issues.append({
            "index":    idx,
            "datetime": times.iloc[idx],
            "issue":    "gap",
            "detail":   f"{deltas.iloc[idx]:.0f} s gap before this epoch",
        })

    # ── Backward jumps ────────────────────────────────────────────────────────
    backward_mask = deltas < 0
    for idx in df.index[backward_mask]:
        issues.append({
            "index":    idx,
            "datetime": times.iloc[idx],
            "issue":    "backward_jump",
            "detail":   f"timestamp went back {abs(deltas.iloc[idx]):.0f} s",
        })

    # ── Year artefacts ────────────────────────────────────────────────────────
    years = times.dt.year
    for year in _ARTEFACT_YEARS:
        art_mask = years == year
        for idx in df.index[art_mask]:
            issues.append({
                "index":    idx,
                "datetime": times.iloc[idx],
                "issue":    "year_artefact",
                "detail":   f"suspicious year {year} (likely firmware bug)",
            })

    if not issues:
        return pd.DataFrame(columns=["index", "datetime", "issue", "detail"])

    return pd.DataFrame(issues).sort_values("index").reset_index(drop=True)
