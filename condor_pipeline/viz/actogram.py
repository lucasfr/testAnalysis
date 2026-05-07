"""
condor.viz.actogram
====================
Thin wrapper around the Condor vendor actogram function.

Keeps all plotting logic isolated from the analysis modules so that
notebooks can import only what they need.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_VENDOR_DIR = Path(__file__).resolve().parents[1] / "algorithms" / "vendor" / "condor"

# Default channels and overlay flags used across the pipeline
DEFAULT_CHANNELS = ["activity", "int_temp_", "ext_temp_", "sleep", "offwrist"]
DEFAULT_OVERLAYS  = [False, True, True, True, True]


def plot_actogram(
    df: pd.DataFrame,
    title: str = "Actogram",
    channels: list[str] | None = None,
    overlays: list[bool] | None = None,
    window: int = 12,
    renderer: str = "iframe",
) -> object:
    """Plot a double-plotted actogram.

    Parameters
    ----------
    df : pd.DataFrame
        Working DataFrame containing at least the columns in *channels*.
    title : str, optional
        Plot title.
    channels : list of str, optional
        Column names to plot. Defaults to
        ``["activity", "int_temp_", "ext_temp_", "sleep", "offwrist"]``.
    overlays : list of bool, optional
        Whether each channel is plotted as an overlay on the activity
        trace. Must be the same length as *channels*.
    window : int, optional
        Hours per row in the actogram. Default is 12.
    renderer : str, optional
        Plotly renderer. Use ``"iframe"`` for JupyterLab,
        ``"colab"`` for Google Colab, ``"browser"`` for a standalone
        browser window. Default is ``"iframe"``.

    Returns
    -------
    plotly.graph_objects.Figure
        The actogram figure (also displayed via ``fig.show()``).
    """
    vendor_str = str(_VENDOR_DIR)
    if vendor_str not in sys.path:
        sys.path.insert(0, vendor_str)

    from simple_actogram import actigraphy_single_plot_actogram  # noqa: PLC0415

    channels = channels or DEFAULT_CHANNELS
    overlays = overlays or DEFAULT_OVERLAYS

    fig = actigraphy_single_plot_actogram(
        df,
        channels,
        overlays,
        window,
        dt="datetime",
        title=title,
    )
    fig.show(renderer=renderer)
    return fig
