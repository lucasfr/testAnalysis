"""
condor.algorithms.cole_kripke
==============================
Cole-Kripke sleep/wake scoring algorithm.

Scores each epoch as wake (1) or sleep (0) using a weighted sum of
surrounding zero-crossing mode (ZCM) activity counts.

Reference
---------
Cole, R. J., Kripke, D. F., Gruen, W., Mullaney, D. J., & Gillin, J. C.
(1992). Automatic sleep/wake identification from wrist activity.
*Sleep*, 15(5), 461–469. https://doi.org/10.1093/sleep/15.5.461
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


# Default weights from Cole et al. (1992), Table 2
_DEFAULT_WEIGHTS_BEFORE = np.array(
    [34.5, 133.0, 529.0, 375.0, 408.0, 400.5, 1074.0, 2048.5, 2424.5]
)
_DEFAULT_WEIGHTS_AFTER = np.array(
    [1920.0, 149.5, 257.5, 125.0, 111.5, 120.0, 69.0, 40.5]
)
_DEFAULT_P = 0.000464


class ColeKripke:
    """Score epochs as wake (1) or sleep (0) using the Cole-Kripke algorithm.

    Parameters
    ----------
    activity : array-like
        1-D array of ZCM activity counts, one value per epoch.
    P : float, optional
        Scaling factor. Default is 0.000464 (Cole et al., 1992).
    weights_before : array-like, optional
        Weights applied to the *P* epochs preceding each epoch.
        Default is the 9-element vector from Cole et al. (1992).
    weights_after : array-like, optional
        Weights applied to the *P* epochs following each epoch.
        Default is the 8-element vector from Cole et al. (1992).

    Attributes
    ----------
    filtered_weighted : np.ndarray or None
        Binary wake/sleep array (1 = wake, 0 = sleep) after calling
        :meth:`model`. ``None`` before the first call.

    Examples
    --------
    >>> ck = ColeKripke(zcm_array)
    >>> predictions = ck.model()   # 0 = sleep, 1 = wake
    """

    def __init__(
        self,
        activity: ArrayLike,
        P: float = _DEFAULT_P,
        weights_before: ArrayLike | None = None,
        weights_after: ArrayLike | None = None,
    ) -> None:
        self.activity = np.asarray(activity, dtype=float)
        self.P = P
        self.weights_before = (
            np.asarray(weights_before, dtype=float)
            if weights_before is not None
            else _DEFAULT_WEIGHTS_BEFORE.copy()
        )
        self.weights_after = (
            np.asarray(weights_after, dtype=float)
            if weights_after is not None
            else _DEFAULT_WEIGHTS_AFTER.copy()
        )
        self.filtered_weighted: np.ndarray | None = None

    def model(self, initial_state: ArrayLike | None = None) -> np.ndarray:
        """Run the Cole-Kripke scorer.

        Parameters
        ----------
        initial_state : array-like, optional
            Unused — kept for API compatibility with the original
            Condor notebook implementation.

        Returns
        -------
        np.ndarray
            Binary array of length ``len(activity)``; 1 = wake, 0 = sleep.
        """
        a  = self.activity
        nb = len(self.weights_before)
        n  = len(a)

        scores = np.zeros(n, dtype=float)

        # Contributions from epochs *before* the current epoch
        for i, w in enumerate(self.weights_before):
            offset = nb - i
            scores[offset:] += w * a[: n - offset]

        # Contributions from epochs *after* the current epoch
        for i, w in enumerate(self.weights_after):
            offset = i + 1
            scores[: n - offset] += w * a[offset:]

        scores *= self.P
        self.filtered_weighted = np.where(scores >= 1.0, 1.0, 0.0)
        return self.filtered_weighted
