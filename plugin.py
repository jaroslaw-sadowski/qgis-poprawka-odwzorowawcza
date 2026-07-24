"""QGIS plugin lifecycle and selected-parcel action."""

from pathlib import Path
from typing import Optional

from qgis.core import Qgis, QgsApplication, QgsProject, QgsVectorLayer
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMessageBox

if __package__:
    from .compat import QAction, execute_dialog
    from .gui import AboutDialog, SelectedParcelDialog
    from .processing_provider import EgibAreaProvider
else:
    from compat import QAction, execute_dialog
    from gui import AboutDialog, SelectedParcelDialog
    from processing_provider import EgibAreaProvider


class EgibAreaPlugin:
    """Register Processing and open a dialog for one selected polygon."""

    MENU_NAME = "&Poprawka odwzorowawcza"
    ACTION_TEXT = "Oblicz powierzchnię zaznaczonej działki"
    ABOUT_ACTION_TEXT = "O wtyczce…"

    def __init__(self, iface: object) -> None:
        self.iface = iface
        self.action: Optional[object] = None
        self.about_action: Optional[object] = None
        self.provider: Optional[EgibAreaProvider] = None
        self.dialog: Optional[SelectedParcelDialog] = None
        self.about_dialog: Optional[AboutDialog] = None

    def initGui(self) -> None:
        """Register Processing and the calculator and information actions."""

        if self.provider is None:
            provider = EgibAreaProvider()
            if not QgsApplication.processingRegistry().addProvider(provider):
                raise RuntimeError(
                    "Nie można zarejestrować providera Processing."
                )
            self.provider = provider

        if self.action is None:
            icon_path = (
                Path(__file__).resolve().parent / "resources" / "icon.svg"
            )
            action = QAction(
                QIcon(str(icon_path)),
                self.ACTION_TEXT,
                self.iface.mainWindow(),
            )
            action.setObjectName("egibSelectedParcelAction")
            action.triggered.connect(self.run)
            self.iface.addPluginToVectorMenu(self.MENU_NAME, action)
            self.iface.addVectorToolBarIcon(action)
            self.action = action

        if self.about_action is None:
            about_action = QAction(
                self.ABOUT_ACTION_TEXT,
                self.iface.mainWindow(),
            )
            about_action.setObjectName("egibAboutAction")
            about_action.triggered.connect(self.show_about)
            self.iface.addPluginToVectorMenu(self.MENU_NAME, about_action)
            self.about_action = about_action

    def unload(self) -> None:
        """Remove all UI and Processing registrations owned by the plugin."""

        if self.action is not None:
            action = self.action
            self.iface.removePluginVectorMenu(self.MENU_NAME, action)
            self.iface.removeVectorToolBarIcon(action)
            action.triggered.disconnect(self.run)
            action.deleteLater()
            self.action = None

        if self.about_action is not None:
            about_action = self.about_action
            self.iface.removePluginVectorMenu(self.MENU_NAME, about_action)
            about_action.triggered.disconnect(self.show_about)
            about_action.deleteLater()
            self.about_action = None

        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None

        self.dialog = None
        self.about_dialog = None

    def run(self) -> None:
        """Open the calculator for exactly one selected polygon."""

        layer = self.iface.activeLayer()
        if not isinstance(layer, QgsVectorLayer):
            self._warn("Aktywuj warstwę wektorową zawierającą działki.")
            return
        if layer.geometryType() != Qgis.GeometryType.Polygon:
            self._warn("Aktywna warstwa musi mieć geometrię poligonową.")
            return

        if layer.selectedFeatureCount() != 1:
            self._warn("Zaznacz dokładnie jedną działkę na aktywnej warstwie.")
            return
        selected_feature = next(layer.getSelectedFeatures(), None)
        if selected_feature is None:
            self._warn("Nie można odczytać zaznaczonej działki.")
            return

        dialog = SelectedParcelDialog(
            layer,
            selected_feature,
            QgsProject.instance().transformContext(),
            self.iface.mainWindow(),
        )
        self.dialog = dialog
        try:
            execute_dialog(dialog)
        finally:
            self.dialog = None

    def show_about(self) -> None:
        """Open release, privacy and authorship information."""

        dialog = AboutDialog(self.iface.mainWindow())
        self.about_dialog = dialog
        try:
            execute_dialog(dialog)
        finally:
            self.about_dialog = None

    def _warn(self, message: str) -> None:
        QMessageBox.warning(
            self.iface.mainWindow(),
            "Poprawka odwzorowawcza",
            message,
        )
