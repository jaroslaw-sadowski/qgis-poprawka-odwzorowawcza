"""QGIS plugin entry point."""


def classFactory(iface):
    """Create the plugin instance requested by QGIS."""

    from .plugin import EgibAreaPlugin

    return EgibAreaPlugin(iface)
