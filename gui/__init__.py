"""Polish user interface for a single selected cadastral parcel."""

from .dialog import (
    SelectedParcelDialog,
    SelectedParcelResult,
    calculate_selected_parcel,
)

__all__ = [
    "SelectedParcelDialog",
    "SelectedParcelResult",
    "calculate_selected_parcel",
]
