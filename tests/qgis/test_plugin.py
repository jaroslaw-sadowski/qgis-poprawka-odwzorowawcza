import configparser
import importlib
from pathlib import Path
from zipfile import ZipFile

import pytest
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsFeature,
    QgsGeometry,
    QgsVectorLayer,
)
from qgis.PyQt.QtWidgets import QMenu, QWidget

import plugin as plugin_module
from plugin import EgibAreaPlugin
from scripts.build_plugin_zip import PLUGIN_PACKAGE_NAME, build_plugin_zip


class FakeIface:
    def __init__(self) -> None:
        self.window = QWidget()
        self.layer = None
        self.menu = QMenu("Wtyczki", self.window)
        self.toolbar_actions = []
        self.removed_toolbar_actions = []

    def mainWindow(self):
        return self.window

    def activeLayer(self):
        return self.layer

    def pluginMenu(self):
        return self.menu

    def addToolBarIcon(self, action) -> None:
        self.toolbar_actions.append(action)

    def removeToolBarIcon(self, action) -> None:
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

    other_action = iface.menu.addAction("Inna wtyczka")
    plugin.initGui()
    plugin.initGui()
    try:
        assert plugin.action is not None
        assert plugin.action.objectName() == "egibSelectedParcelAction"
        assert plugin.action.icon().isNull() is False
        assert iface.menu.actions() == [other_action, plugin.action]
        assert plugin.action.menu() is None
        assert iface.toolbar_actions == [plugin.action]
        assert plugin.action.text() == "Poprawka odwzorowawcza PL-2000"
        assert (
            registry.algorithmById("egib_area:calculate_egib_area") is not None
        )

        iface.layer = _selected_layer()
        plugin.action.trigger()
        assert len(opened_dialogs) == 1
        assert (
            opened_dialogs[0]
            .windowTitle()
            .startswith("Poprawka odwzorowawcza PL-2000")
        )
        assert plugin.dialog is None
    finally:
        action = plugin.action
        plugin.unload()

    assert registry.algorithmById("egib_area:calculate_egib_area") is None
    plugin.unload()
    assert iface.menu.actions() == [other_action]
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

    assert messages == [
        "Zaznacz dokładnie jedną działkę na aktywnej warstwie."
    ]


def test_plugin_does_not_materialize_the_selected_feature_iterator(
    monkeypatch,
) -> None:
    selected_feature = QgsFeature()
    opened_dialogs = []

    class SelectionIterator:
        def __init__(self):
            self.call_count = 0

        def __iter__(self):
            return self

        def __next__(self):
            self.call_count += 1
            if self.call_count == 1:
                return selected_feature
            raise AssertionError("selection iterator was materialized")

    selection_iterator = SelectionIterator()

    class FakeSelectedLayer:
        def geometryType(self):
            return Qgis.GeometryType.Polygon

        def selectedFeatureCount(self):
            return 1

        def getSelectedFeatures(self):
            return selection_iterator

    class FakeDialog:
        def __init__(self, layer, feature, transform_context, parent):
            del layer, transform_context, parent
            assert feature is selected_feature
            opened_dialogs.append(self)

    monkeypatch.setattr(plugin_module, "QgsVectorLayer", FakeSelectedLayer)
    monkeypatch.setattr(plugin_module, "SelectedParcelDialog", FakeDialog)
    monkeypatch.setattr(plugin_module, "execute_dialog", lambda dialog: 0)
    iface = FakeIface()
    iface.layer = FakeSelectedLayer()

    EgibAreaPlugin(iface).run()

    assert len(opened_dialogs) == 1
    assert selection_iterator.call_count == 1


def test_qgis_class_factory_imports_plugin_as_a_package(monkeypatch) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    monkeypatch.syspath_prepend(str(repository_root.parent))
    package = importlib.import_module(repository_root.name)

    instance = package.classFactory(FakeIface())

    assert instance.__class__.__name__ == "EgibAreaPlugin"


def test_metadata_enables_processing_and_supports_qgis3_and_qgis4() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    metadata_path = repository_root / "metadata.txt"
    parser = configparser.ConfigParser()
    parser.read(metadata_path, encoding="utf-8")

    metadata = parser["general"]
    assert metadata["name"] == "Poprawka odwzorowawcza PL-2000"
    assert metadata["version"] == "1.1.0"
    assert metadata["qgisminimumversion"] == "3.40"
    assert metadata["qgismaximumversion"] == "4.99"
    assert metadata["hasprocessingprovider"] == "yes"
    assert metadata["email"] == "github.com.amenity983@passfwd.com"
    assert metadata["description"].startswith("PL: Oblicza pole działek")
    assert "EN: Calculates parcel areas" in metadata["description"]
    assert ";" not in metadata["description"]
    assert "\n| EN: Calculates" in metadata["description"]
    assert "| en" not in metadata
    for text in (
        "§ 16 ust. 2",
        "załącznika nr 3",
        "Dz.U. 2024 poz. 219 ze zm.",
        "Nie wysyła danych na zewnątrz",
        "vibe coding",
        "Autor nie bierze odpowiedzialności",
        "Bandit",
        "detect-secrets",
        "Flake8",
        "analiza ZIP-a",
        "lokalne testy bezpieczeństwa i jakości",
    ):
        assert text in metadata["about"]
    assert metadata["tags"] == (
        "kataster,cadastre,egib,land and building register,geodezja,geodesy,"
        "pole działki,parcel area,powierzchnia,area,odwzorowanie,projection,"
        "poprawka odwzorowawcza,projection correction,"
        "rozporządzenie egib,land and building register regulation,"
        "polska,poland,pl-2000"
    )
    assert "\nEN\n" in metadata["about"]
    assert "PL\n" in metadata["about"]
    assert "§ 16(2)" in metadata["about"]
    assert "Więcej informacji na repozytorium GitHub." in metadata["about"]
    for section in metadata["about"].split("\nEN\n"):
        assert len(section.split()) <= 150
    assert "The author accepts no responsibility" in metadata["about"]
    assert "category" not in metadata
    assert metadata["icon"] == "resources/icon.png"
    assert metadata["changelog"].startswith("1.1.0\nPOLSKI\n• ")
    assert metadata["experimental"] == "False"
    assert metadata["deprecated"] == "False"
    assert "supportsQt6" not in metadata_path.read_text(encoding="utf-8")


def test_built_zip_imports_as_qgis_plugin_package(
    tmp_path, monkeypatch
) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    archive_path = build_plugin_zip(repository_root, tmp_path / "plugin.zip")
    with ZipFile(archive_path) as archive:
        archive.extractall(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    package = importlib.import_module(PLUGIN_PACKAGE_NAME)
    iface = FakeIface()
    instance = package.classFactory(iface)
    instance.initGui()
    try:
        expected = "Poprawka odwzorowawcza PL-2000"
        assert iface.menu.actions() == [instance.action]
        assert instance.action.text() == expected
        assert instance.provider.name() == expected
        algorithm = instance.provider.algorithms()[0]
        assert algorithm.displayName() == expected
        assert algorithm.group() == ""
        assert algorithm.groupId() == ""
    finally:
        instance.unload()
    assert not iface.menu.actions()


@pytest.mark.parametrize("locale", ["pl_PL", "en_US", "de_DE"])
def test_native_qgis_installer_reads_both_languages_from_zip(
    tmp_path,
    monkeypatch,
    locale,
):
    # Use QGIS's own installed-plugin reader, without changing user settings.
    monkeypatch.syspath_prepend(
        str(Path(QgsApplication.pkgDataPath()) / "python")
    )
    installer_data = importlib.import_module(
        "pyplugin_installer.installer_data"
    )

    class LocaleSettings:
        def value(self, key, default=None, value_type=None):
            return {
                "locale/overrideFlag": True,
                "locale/userLocale": locale,
            }.get(key, default)

    monkeypatch.setattr(installer_data, "QgsSettings", LocaleSettings)
    root = Path(__file__).resolve().parents[2]
    archive_path = build_plugin_zip(root, tmp_path / "plugin.zip")
    with ZipFile(archive_path) as archive:
        archive.extractall(tmp_path)
    installed = installer_data.Plugins().getInstalledPlugin(
        PLUGIN_PACKAGE_NAME, str(tmp_path / PLUGIN_PACKAGE_NAME), False
    )
    assert installed["error"] == ""
    assert installed["installed"] is True
    assert installed["name"] == "Poprawka odwzorowawcza PL-2000"
    for expected in ("EN: Calculates", "PL: Oblicza"):
        assert expected in installed["description"]
    for expected in (
        "PL\n",
        "\nEN\n",
        "§ 16 ust. 2",
        "§ 16(2)",
        "Nie wysyła danych na zewnątrz",
        "Does not send data outside QGIS",
        "lokalne testy bezpieczeństwa i jakości",
        "local security and quality checks",
    ):
        assert expected in installed["about"]
    assert "pole działki,parcel area" in installed["tags"]
    assert "powierzchnia,area" in installed["tags"]
    assert installed["description"].startswith("PL: Oblicza")
    assert installed["changelog"].startswith("1.1.0\nPOLSKI\n• ")
    assert "\nENGLISH\n• QGIS 4 and Qt6 support." in installed["changelog"]
    assert installed["changelog"].count("\n• ") == 12
