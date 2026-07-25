from decimal import Decimal
from pathlib import Path

import pytest
from qgis.core import QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QPoint, Qt
from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtWidgets import (
    QApplication,
    QComboBox,
    QGroupBox,
    QLabel,
    QTextBrowser,
)

import adapters.geometry as geometry_module
import gui.dialog as dialog_module
from adapters import GeometryTransformError, RepairMethod
from gui import AboutDialog, SelectedParcelDialog, read_plugin_metadata


def _layer_with_geometry(
    wkt: str, *, crs: str = "EPSG:2178"
) -> QgsVectorLayer:
    layer = QgsVectorLayer(f"MultiPolygon?crs={crs}", "Działki", "memory")
    feature = QgsFeature(layer.fields())
    feature.setGeometry(QgsGeometry.fromWkt(wkt))
    layer.dataProvider().addFeature(feature)
    return layer


def _dialog(layer: QgsVectorLayer) -> SelectedParcelDialog:
    feature = next(layer.getFeatures())
    return SelectedParcelDialog(
        layer,
        feature,
        QgsProject.instance().transformContext(),
    )


def test_dialog_calculates_without_editing_source() -> None:
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    source_wkb = bytes(next(layer.getFeatures()).geometry().asWkb())
    dialog = _dialog(layer)

    assert (
        dialog.windowTitle()
        == "Poprawka odwzorowawcza PL-2000 — zaznaczona działka"
    )
    assert dialog.zone_combo.isEnabled() is False
    assert "Wykryto PL-2000" in dialog.zone_combo.currentText()
    assert "strefa 7" in dialog.zone_combo.currentText()
    assert "Automatycznie wykryto PL-2000" in dialog.zone_combo.toolTip()
    assert (
        dialog.repair_mode_combo.currentText()
        == "Nie wykrywaj błędów geometrii; licz obiekt źródłowy"
    )
    assert "Noto Sans" not in dialog.styleSheet()
    assert "Segoe UI" not in dialog.styleSheet()
    assert "DejaVu Sans Mono" in dialog.styleSheet()
    assert "DejaVu Sans Mono" in dialog.result_text.toHtml()
    expected_font_family = dialog.font().family()
    assert expected_font_family == "DejaVu Sans Mono"
    assert (
        dialog.findChild(QLabel, "dialogTitle").font().family()
        == expected_font_family
    )
    assert (
        dialog.findChild(QLabel, "dialogTitle").text()
        == "Poprawka odwzorowawcza PL-2000"
    )
    assert (
        dialog.findChild(QGroupBox, "settingsGroup").font().family()
        == expected_font_family
    )
    assert (
        dialog.findChild(QComboBox, "zoneCombo").font().family()
        == expected_font_family
    )
    assert (
        dialog.findChild(QTextBrowser, "resultText").font().family()
        == expected_font_family
    )
    assert dialog.width() == 880
    assert dialog.height() == 580
    assert dialog.calculate_button.isDefault() is True
    selection_text = " ".join(
        label.text() for label in dialog.findChildren(dialog_module.QLabel)
    )
    assert "Warstwa:" in selection_text
    assert "Wykryty EPSG:" in selection_text
    assert "Obiekt:" in selection_text
    repair_tooltip = dialog.repair_mode_combo.toolTip()
    assert "pomija kontrolę GEOS" in repair_tooltip
    assert "nie uruchamia makeValid()" in repair_tooltip
    assert "próbuje naprawić kopię" in repair_tooltip

    dialog.calculate_button.click()

    assert dialog.last_result is not None
    assert dialog.last_result.calculation is not None
    assert dialog.last_result.calculation.legal_area_ha_rounded == Decimal(
        "1.0002"
    )
    assert dialog.last_result.qgis_geodesic_area_m2 == pytest.approx(
        10_001.54017795077
    )
    text = dialog.result_text.toPlainText()
    assert "P₀" in text
    assert "P QGIS" in text
    assert "Pole matematyczne/kartezjańskie" in text
    assert "Pole geodezyjne QGIS" in text
    assert "ΔP₀" in text
    assert "P = P₀ − ΔP₀" in text
    assert "10000,00 m²" in text
    assert "-1,54 m²" in text
    assert "10001,54 m²" in text
    assert "1,0002 ha" in text
    assert "PGK — X₂₀₀₀" in text
    assert "PGK — Y₂₀₀₀" in text
    assert "7 (EPSG:2178)" in text
    assert "σ = σ₀ + m₀ · v²" in text
    assert "10001,539" not in text
    assert "param:sigma" in dialog.result_text._hover_help
    assert "result:p0" in dialog.result_text._hover_help
    assert "result:qgis-geodesic" in dialog.result_text._hover_help
    assert "QgsGeometry.area()" in dialog.result_text._hover_help["result:p0"]
    assert "area(geometry)" in dialog.result_text._hover_help["result:p0"]
    assert (
        "QgsDistanceArea.measureArea()"
        in dialog.result_text._hover_help["result:qgis-geodesic"]
    )
    assert "$area" in dialog.result_text._hover_help["result:qgis-geodesic"]
    assert "diagnostic:zone" in dialog.result_text._hover_help
    assert bytes(next(layer.getFeatures()).geometry().asWkb()) == source_wkb


def test_clicking_report_help_link_keeps_calculation_visible() -> None:
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    dialog = _dialog(layer)
    dialog.calculate_button.click()
    dialog.show()
    QApplication.processEvents()

    browser = dialog.result_text
    help_position = None
    for y_position in range(0, browser.viewport().height(), 2):
        for x_position in range(0, browser.viewport().width(), 3):
            position = QPoint(x_position, y_position)
            if browser.anchorAt(position) == "result:p0":
                help_position = position
                break
        if help_position is not None:
            break

    assert help_position is not None
    text_before_click = browser.toPlainText()
    mouse_button_enum = getattr(Qt, "MouseButton", Qt)
    QTest.mouseClick(
        browser.viewport(),
        mouse_button_enum.LeftButton,
        pos=help_position,
    )
    QApplication.processEvents()

    assert browser.toPlainText() == text_before_click
    assert dialog.last_result is not None
    assert dialog.last_result.calculation is not None


def test_dialog_source_mode_calculates_without_geometry_check() -> None:
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((7500000 5800000,7500200 5800200,"
        "7500000 5800200,7500100 5800000,7500000 5800000)))"
    )
    source_wkb = bytes(next(layer.getFeatures()).geometry().asWkb())
    dialog = _dialog(layer)

    dialog.calculate_button.click()

    assert dialog.last_result is not None
    assert dialog.last_result.calculation is not None
    assert (
        dialog.last_result.preparation.report.repair_method
        is RepairMethod.NONE
    )
    assert dialog.last_result.preparation.report.validity_before is None
    assert dialog.last_result.preparation.report.validity_after is None
    assert "bez kontroli poprawności geometrii" in dialog.status_label.text()
    assert "nie sprawdzano" in dialog.result_text.toPlainText()
    assert bytes(next(layer.getFeatures()).geometry().asWkb()) == source_wkb


def test_dialog_auto_repair_marks_repaired_calculation() -> None:
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((7500000 5800000,7500100 5800100,"
        "7500000 5800100,7500100 5800000,7500000 5800000)))"
    )
    dialog = _dialog(layer)
    dialog.repair_mode_combo.setCurrentIndex(1)

    assert (
        dialog.repair_mode_combo.currentText()
        == "Wykryj błędy i spróbuj naprawić geometrię"
    )
    assert "Naprawa może zmienić pole" in dialog.repair_mode_combo.toolTip()
    assert "warstwa źródłowa" in dialog.repair_mode_combo.toolTip()

    dialog.calculate_button.click()

    assert dialog.last_result is not None
    assert dialog.last_result.calculation is not None
    assert "naprawionej kopii" in dialog.status_label.text()
    assert "Naprawa zmieniła zbiór wierzchołków" in (
        dialog.result_text.toPlainText()
    )
    assert any(
        "Geometria na warstwie źródłowej nie została zmieniona" in tooltip
        for help_key, tooltip in dialog.result_text._hover_help.items()
        if help_key.startswith("warning:")
    )


def test_interior_ring_warning_has_extended_hover_help() -> None:
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((7499900 5799900,7500100 5799900,"
        "7500100 5800100,7499900 5800100,7499900 5799900),"
        "(7499975 5799975,7499975 5800025,7500025 5800025,"
        "7500025 5799975,7499975 5799975))))"
    )
    dialog = _dialog(layer)

    dialog.calculate_button.click()

    assert "Pierścienie wewnętrzne" in dialog.result_text.toPlainText()
    warning_help = [
        tooltip
        for help_key, tooltip in dialog.result_text._hover_help.items()
        if help_key.startswith("warning:")
    ]
    assert any("Obiekt zawiera otwory" in tooltip for tooltip in warning_help)
    assert any("P_GK" in tooltip for tooltip in warning_help)


def test_dialog_requires_confirmed_zone_for_other_crs(monkeypatch) -> None:
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((21 52,21.001 52,21.001 52.001,21 52.001,21 52)))",
        crs="EPSG:4326",
    )
    dialog = _dialog(layer)
    warnings = []

    assert "Wykryty EPSG:</b> 4326" in " ".join(
        label.text() for label in dialog.findChildren(dialog_module.QLabel)
    )
    assert dialog.zone_combo.isEnabled() is True
    assert (
        dialog.zone_combo.currentText()
        == "Wskaż strefę PL-2000, w której leży obiekt…"
    )
    assert "przeliczona w locie" in dialog.zone_combo.toolTip()
    assert "CRS nie zostaną zmienione" in dialog.zone_combo.toolTip()

    class FakeMessageBox:
        @staticmethod
        def warning(parent, title, message):
            del parent, title
            warnings.append(message)

    monkeypatch.setattr(dialog_module, "QMessageBox", FakeMessageBox)

    dialog.calculate_button.click()

    assert dialog.last_result is None
    assert warnings == [
        "Wskaż strefę PL-2000, w której leży obiekt, i potwierdź wybór "
        "przed obliczeniem."
    ]

    dialog.zone_combo.setCurrentIndex(3)
    assert "Wybrano strefę 7" in dialog.zone_combo.toolTip()
    assert "EPSG:2178" in dialog.zone_combo.toolTip()
    dialog.calculate_button.click()
    assert dialog.last_result is not None
    assert dialog.last_result.preparation.target_epsg == 2178


def test_epsg_1992_requires_explicit_pl2000_zone() -> None:
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((500000 500000,500100 500000,"
        "500100 500100,500000 500100,500000 500000)))",
        crs="EPSG:2180",
    )
    dialog = _dialog(layer)

    selection_text = " ".join(
        label.text() for label in dialog.findChildren(dialog_module.QLabel)
    )
    assert "Wykryty EPSG:</b> 2180" in selection_text
    assert dialog.zone_combo.isEnabled() is True
    assert "Wskaż strefę PL-2000" in dialog.zone_combo.currentText()
    assert "EPSG:2180" in dialog.zone_combo.toolTip()
    assert "przeliczona w locie" in dialog.zone_combo.toolTip()


def test_dialog_reports_geometry_budget_before_calculation(
    monkeypatch,
) -> None:
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    dialog = _dialog(layer)
    warnings = []
    monkeypatch.setattr(
        geometry_module,
        "MAX_BOUNDARY_COORDINATES",
        4,
    )

    class FakeMessageBox:
        @staticmethod
        def warning(parent, title, message):
            del parent, title
            warnings.append(message)

    monkeypatch.setattr(dialog_module, "QMessageBox", FakeMessageBox)

    dialog.calculate_button.click()

    assert dialog.last_result is None
    assert "Nie można obliczyć powierzchni" in warnings[0]
    assert "limit liczby współrzędnych: 5 > 4" in warnings[0]


def test_dialog_hides_raw_transform_error_details(monkeypatch) -> None:
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    dialog = _dialog(layer)
    warnings = []

    def fail_calculation(*args, **kwargs):
        del args, kwargs
        raise GeometryTransformError(
            "grid missing at /home/private-user/secret-grid.gsb"
        )

    class FakeMessageBox:
        @staticmethod
        def warning(parent, title, message):
            del parent, title
            warnings.append(message)

    monkeypatch.setattr(
        dialog_module,
        "calculate_selected_parcel",
        fail_calculation,
    )
    monkeypatch.setattr(dialog_module, "QMessageBox", FakeMessageBox)

    dialog.calculate_button.click()

    assert dialog.last_result is None
    assert "Sprawdź CRS warstwy" in warnings[0]
    assert "/home/private-user" not in warnings[0]
    assert "grid missing" not in warnings[0]


def test_about_dialog_presents_authorship_privacy_and_disclosure() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    metadata = read_plugin_metadata(repository_root)
    dialog = AboutDialog(plugin_root=repository_root)
    visible_text = " ".join(
        label.text() for label in dialog.findChildren(QLabel)
    )

    assert dialog.objectName() == "aboutDialog"
    assert dialog.windowIcon().isNull() is False
    assert metadata["name"] in dialog.windowTitle()
    assert f"Wersja {metadata['version']}" in visible_text
    assert metadata["author"] in visible_text
    assert metadata["repository"] in visible_text
    assert "Dane pozostają w QGIS" in visible_text
    assert "nie łączy się z siecią" in visible_text
    assert "vibe coding" in visible_text
    assert "DejaVu Sans Mono" in dialog.styleSheet()
    assert dialog.font().family() == "DejaVu Sans Mono"
    assert (
        dialog.findChild(QLabel, "aboutTitle").font().family()
        == dialog.font().family()
    )
    assert dialog.findChild(QLabel, "aboutIcon").width() == 18
    assert "font-size: 10.5pt" in dialog.styleSheet()
    assert dialog.height() == 440
