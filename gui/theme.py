"""Shared visual tokens for the plugin dialogs."""

from qgis.PyQt.QtGui import QFont
from qgis.PyQt.QtWidgets import QWidget

MONOSPACE_FONT_STACK = (
    '"DejaVu Sans Mono", Consolas, Menlo, "Liberation Mono", monospace'
)
_FONT_STYLE_HINT_ENUM = getattr(QFont, "StyleHint", QFont)


def technical_font(point_size: int = 9) -> QFont:
    """Return the fixed-pitch font used by every plugin widget."""

    font = QFont("DejaVu Sans Mono", point_size)
    font.setStyleHint(_FONT_STYLE_HINT_ENUM.Monospace)
    font.setFixedPitch(True)
    return font


def theme_colors(widget: QWidget) -> dict:
    """Return an accessible light or dark palette derived from QGIS."""

    is_dark = widget.palette().window().color().lightness() < 128
    if is_dark:
        return {
            "window": "#1d252c",
            "surface": "#252f38",
            "surface_alt": "#2d3943",
            "text": "#edf3f7",
            "muted": "#adbac5",
            "border": "#44515d",
            "accent": "#63b3d4",
            "accent_hover": "#7bc1de",
            "accent_soft": "#243f4c",
            "success": "#65c59b",
            "success_soft": "#243e35",
            "warning": "#efbd68",
            "warning_soft": "#453922",
            "error": "#ee817c",
            "error_soft": "#482d2e",
        }
    return {
        "window": "#f2f5f7",
        "surface": "#ffffff",
        "surface_alt": "#eaf0f3",
        "text": "#17242d",
        "muted": "#5e6d77",
        "border": "#d3dde3",
        "accent": "#176b8b",
        "accent_hover": "#0f5874",
        "accent_soft": "#e1f0f5",
        "success": "#247253",
        "success_soft": "#e1f1e9",
        "warning": "#946116",
        "warning_soft": "#fbefd8",
        "error": "#a43d3a",
        "error_soft": "#f8e5e4",
    }
