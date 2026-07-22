import configparser
import importlib
from pathlib import Path
from zipfile import ZipFile

from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsVectorLayer
from qgis.PyQt.QtWidgets import QWidget

import plugin as plugin_module
from plugin import EgibAreaPlugin
from scripts.build_plugin_zip import PLUGIN_PACKAGE_NAME, build_plugin_zip


class FakeIface:
    def __init__(self) -> None:
        self.window = QWidget()
        self.layer = None
        self.menu_actions = []
        self.toolbar_actions = []
        self.removed_menu_actions = []
        self.removed_toolbar_actions = []

    def mainWindow(self):
        return self.window

    def activeLayer(self):
        return self.layer

    def addPluginToVectorMenu(self, menu_name, action) -> None:
        self.menu_actions.append((menu_name, action))

    def addVectorToolBarIcon(self, action) -> None:
        self.toolbar_actions.append(action)

    def removePluginVectorMenu(self, menu_name, action) -> None:
        self.removed_menu_actions.append((menu_name, action))

    def removeVectorToolBarIcon(self, action) -> None:
        self.removed_toolbar_actions.append(action)


def _selected_layer() -> QgsVectorLayer:
    layer = QgsVectorLayer("MultiPolygon?crs=EPSG:2178", "Działki", "memory")
    feature = QgsFeature(layer.fields())
    feature.setGeometry(
        QgsGeometry.fromWkt(
            "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
            "7500050 5800050,7499950 5800050,7499950 5799950)))"
        )
    )
    layer.dataProvider().addFeature(feature)
    layer.selectByIds([next(layer.getFeatures()).id()])
    return layer


def test_plugin_registers_action_provider_and_unloads(monkeypatch) -> None:
    iface = FakeIface()
    plugin = EgibAreaPlugin(iface)
    registry = QgsApplication.processingRegistry()
    opened_dialogs = []

    monkeypatch.setattr(
        plugin_module,
        "execute_dialog",
        lambda dialog: opened_dialogs.append(dialog) or 0,
    )

    plugin.initGui()
    try:
        assert plugin.action is not None
        assert plugin.action.objectName() == "egibSelectedParcelAction"
        assert plugin.action.icon().isNull() is False
        assert iface.menu_actions == [(plugin.MENU_NAME, plugin.action)]
        assert iface.toolbar_actions == [plugin.action]
        assert registry.algorithmById("egib_area:calculate_egib_area") is not None

        iface.layer = _selected_layer()
        plugin.action.trigger()
        assert len(opened_dialogs) == 1
        assert opened_dialogs[0].windowTitle().startswith("Poprawka odwzorowawcza")
        assert plugin.dialog is None
    finally:
        action = plugin.action
        plugin.unload()

    assert registry.algorithmById("egib_area:calculate_egib_area") is None
    assert iface.removed_menu_actions == [(plugin.MENU_NAME, action)]
    assert iface.removed_toolbar_actions == [action]
    assert plugin.action is None
    assert plugin.provider is None


def test_plugin_action_warns_when_selection_is_missing(monkeypatch) -> None:
    iface = FakeIface()
    plugin = EgibAreaPlugin(iface)
    messages = []

    class FakeMessageBox:
        @staticmethod
        def warning(parent, title, message):
            del parent, title
            messages.append(message)

    monkeypatch.setattr(plugin_module, "QMessageBox", FakeMessageBox)
    iface.layer = _selected_layer()
    iface.layer.removeSelection()

    plugin.run()

    assert messages == ["Zaznacz dokładnie jedną działkę na aktywnej warstwie."]


def test_qgis_class_factory_imports_plugin_as_a_package(monkeypatch) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    monkeypatch.syspath_prepend(str(repository_root.parent))
    package = importlib.import_module(repository_root.name)

    instance = package.classFactory(FakeIface())

    assert instance.__class__.__name__ == "EgibAreaPlugin"


def test_metadata_is_processing_enabled_but_not_yet_marked_for_qgis4() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    metadata_path = repository_root / "metadata.txt"
    parser = configparser.ConfigParser()
    parser.read(metadata_path, encoding="utf-8")

    metadata = parser["general"]
    assert metadata["qgisminimumversion"] == "3.44"
    assert metadata["qgismaximumversion"] == "3.99"
    assert metadata["hasprocessingprovider"] == "yes"
    assert metadata["email"] == "jaroslaw-sadowski@users.noreply.github.com"
    assert "supportsQt6" not in metadata_path.read_text(encoding="utf-8")


def test_built_zip_imports_as_qgis_plugin_package(tmp_path, monkeypatch) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    archive_path = build_plugin_zip(repository_root, tmp_path / "plugin.zip")
    with ZipFile(archive_path) as archive:
        archive.extractall(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    package = importlib.import_module(PLUGIN_PACKAGE_NAME)
    instance = package.classFactory(FakeIface())

    assert instance.__class__.__name__ == "EgibAreaPlugin"
