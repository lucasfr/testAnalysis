"""
condor_pipeline.pipeline
=========================
High-level orchestrator for the Circadia actigraphy sleep pipeline.

Usage — single file
-------------------
>>> from condor_pipeline.pipeline import SleepPipeline
>>> pipe = SleepPipeline("data/input1.txt", device="acttrust")
>>> results = pipe.run()
>>> print(results.nights)
>>> results.plot()

Usage — batch (folder)
-----------------------
>>> from condor_pipeline.pipeline import SleepPipeline
>>> results = SleepPipeline.batch("data/", device="acttrust", pattern="*.txt")
>>> for r in results:
...     print(r.subject_id, r.nights)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from condor_pipeline.io import get_reader
from condor_pipeline.preprocessing import prepare, consistency_check
from condor_pipeline.detection.offwrist import detect_offwrist, export_offwrist_csv
from condor_pipeline.detection.sleep_periods import detect_sleep_periods, detect_naps
from condor_pipeline.detection.waso import detect_waso
from condor_pipeline.viz.actogram import plot_actogram


@dataclass
class PipelineResult:
    """Container for all outputs from a single-subject pipeline run.

    Attributes
    ----------
    subject_id : str
        Derived from the input filename stem.
    source_file : Path
        Path to the raw input file.
    df : pd.DataFrame
        Final working DataFrame with all state columns populated.
    nights : pd.DataFrame
        Per-night sleep statistics table.
    issues : pd.DataFrame
        Timestamp consistency issues (empty if none).
    offwrist_csv : Path or None
        Path to the exported off-wrist CSV, if any off-wrist periods
        were detected.
    """

    subject_id:   str
    source_file:  Path
    df:           pd.DataFrame
    nights:       pd.DataFrame
    issues:       pd.DataFrame
    offwrist_csv: Path | None = None

    def plot(self, title: str | None = None, renderer: str = "iframe") -> object:
        """Plot the final actogram for this subject."""
        t = title or f"Final Actogram — {self.subject_id}"
        return plot_actogram(self.df, title=t, renderer=renderer)


class SleepPipeline:
    """Orchestrates the full actigraphy sleep analysis pipeline.

    Parameters
    ----------
    path : str or Path
        Path to the raw actigraph file.
    device : str
        Device type identifier, e.g. ``"acttrust"`` or ``"actiwatch"``.
    gap_threshold : float, optional
        Minimum gap (seconds) flagged by the consistency check. Default 120.
    wake_thresh : int, optional
        Passed to the WASO detector. Default 60.
    export_offwrist : bool, optional
        Whether to write the off-wrist CSV next to the input file.
        Default True.
    """

    def __init__(
        self,
        path: str | Path,
        device: str = "acttrust",
        gap_threshold: float = 120.0,
        wake_thresh: int = 60,
        export_offwrist: bool = True,
    ) -> None:
        self.path            = Path(path)
        self.device          = device
        self.gap_threshold   = gap_threshold
        self.wake_thresh     = wake_thresh
        self.export_offwrist = export_offwrist

    # ── Core run ──────────────────────────────────────────────────────────────

    def run(self) -> PipelineResult:
        """Execute the full pipeline for a single file.

        Returns
        -------
        PipelineResult
        """
        subject_id = self.path.stem

        # 1. Read
        reader = get_reader(self.device)(self.path)
        df     = reader.read()

        # 2. Consistency check
        issues = consistency_check(df, duration=self.gap_threshold)
        if len(issues) > 0:
            print(f"[{subject_id}] {len(issues)} timestamp issue(s) detected.")

        # 3. Prepare
        df = prepare(df)

        # 4. Off-wrist detection
        df = detect_offwrist(df)
        offwrist_csv = None
        if self.export_offwrist:
            offwrist_csv = export_offwrist_csv(df, self.path)

        # 5. Main sleep periods
        df = detect_sleep_periods(df)

        # 6. Naps
        df = detect_naps(df)

        # 7. WASO + nightly stats
        out = df["state"].to_numpy().copy()
        nights, df = detect_waso(df, out, wake_thresh=self.wake_thresh)

        return PipelineResult(
            subject_id=subject_id,
            source_file=self.path,
            df=df,
            nights=nights,
            issues=issues,
            offwrist_csv=offwrist_csv,
        )

    # ── Batch mode ────────────────────────────────────────────────────────────

    @classmethod
    def batch(
        cls,
        folder: str | Path,
        device: str = "acttrust",
        pattern: str = "*.txt",
        **kwargs,
    ) -> list[PipelineResult]:
        """Run the pipeline on all matching files in a folder.

        Parameters
        ----------
        folder : str or Path
            Directory containing raw actigraph files.
        device : str
            Device type, passed to each :class:`SleepPipeline` instance.
        pattern : str, optional
            Glob pattern for file discovery. Default ``"*.txt"``.
        **kwargs
            Additional keyword arguments forwarded to :class:`SleepPipeline`.

        Returns
        -------
        list of PipelineResult
            One result per file found.
        """
        folder = Path(folder)
        files  = sorted(folder.glob(pattern))

        if not files:
            print(f"No files matching '{pattern}' found in {folder}.")
            return []

        results = []
        for f in files:
            print(f"Processing: {f.name}")
            try:
                pipe   = cls(f, device=device, **kwargs)
                result = pipe.run()
                results.append(result)
                print(f"  ✓ {result.subject_id} — {len(result.nights)} night(s) detected.")
            except Exception as exc:  # noqa: BLE001
                print(f"  ✗ {f.name} failed: {exc}")

        return results
