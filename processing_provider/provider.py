"""QGIS Processing provider registration object."""

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtCore import QCoreApplication

from .area_algorithm import CalculateEgibAreaAlgorithm


class EgibAreaProvider(QgsProcessingProvider):
    """Expose cadastral area algorithms in the Processing registry."""

    def loadAlgorithms(self) -> None:
        self.addAlgorithm(CalculateEgibAreaAlgorithm())

    def id(self) -> str:
        return "egib_area"

    def name(self) -> str:
        return self.tr("Powierzchnia działki EGiB")

    def longName(self) -> str:
        return self.name()

    @staticmethod
    def tr(message: str) -> str:
        return QCoreApplication.translate("EgibAreaProvider", message)
