"""Shared visual tokens for the plugin dialogs."""

from qgis.PyQt.QtWidgets import QWidget

UI_FONT_STACK = (
    '"Noto Sans", "Segoe UI", "SF Pro Text", "DejaVu Sans", sans-serif'
)
MONOSPACE_FONT_STACK = (
    '"DejaVu Sans Mono", Consolas, Menlo, "Liberation Mono", monospace'
)


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
