from condor_pipeline.io.base import AbstractReader, REQUIRED_COLUMNS
from condor_pipeline.io.acttrust import ActTrustReader
from condor_pipeline.io.actiwatch import ActiwatchReader

__all__ = [
    "AbstractReader",
    "REQUIRED_COLUMNS",
    "ActTrustReader",
    "ActiwatchReader",
]

# Registry — maps device name strings to reader classes.
# Add new brands here as their readers are implemented.
READERS: dict[str, type[AbstractReader]] = {
    "acttrust": ActTrustReader,
    "actiwatch": ActiwatchReader,
}


def get_reader(device: str) -> type[AbstractReader]:
    """Return the reader class for a given device name.

    Parameters
    ----------
    device : str
        Case-insensitive device identifier, e.g. ``"acttrust"``.

    Raises
    ------
    ValueError
        If no reader is registered for the given device name.
    """
    key = device.lower().strip()
    if key not in READERS:
        raise ValueError(
            f"No reader registered for device '{device}'. "
            f"Available: {list(READERS.keys())}"
        )
    return READERS[key]
