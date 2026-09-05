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
    QScrollArea,
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

    assert dialog.windowTitle() == "Poprawka odwzorowawcza PL-2000"
    assert dialog.zone_combo.isEnabled() is False
    assert "Wykryto PL-2000" in dialog.zone_combo.currentText()
    assert "strefa 7" in dialog.zone_combo.currentText()
    assert "Automatycznie wykryto PL-2000" in dialog.zone_combo.toolTip()
    assert (
        dialog.repair_mode_combo.currentText()
        == "Sprawdź geometrię; licz bez naprawy"
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
    assert "wykonuje kontrolę GEOS" in repair_tooltip
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


def test_dialog_source_mode_reports_invalid_geometry_without_repair() -> None:
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
    assert dialog.last_result.preparation.report.validity_before is False
    assert dialog.last_result.preparation.report.validity_after is False
    assert "Wynik diagnostyczny" in dialog.status_label.text()
    assert "WYNIK DIAGNOSTYCZNY" in dialog.result_text.toPlainText()
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
    assert dialog.height() == 600


@pytest.fixture
def calculated_dialog():
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    dialog = _dialog(layer)
    assert not dialog.export_button.isEnabled()
    dialog.calculate()
    yield dialog
    dialog.close()


@pytest.mark.parametrize("repair_index", [0, 1])
def test_auxiliary_failure_preserves_main_gui_result(
    calculated_dialog, monkeypatch, repair_index
):
    dialog = calculated_dialog
    expected = dialog.last_result.calculation

    def fail_measurement(*args):
        raise GeometryTransformError("private/path/grid.gsb")

    monkeypatch.setattr(
        dialog_module, "measure_geodesic_area_m2", fail_measurement
    )
    dialog.repair_mode_combo.setCurrentIndex(repair_index)
    dialog.calculate()

    assert dialog.last_result.calculation == expected
    assert dialog.last_result.qgis_geodesic_area_m2 is None
    assert "geodesic_measurement_failed" in dialog.last_result.warnings
    assert dialog.status_card.property("state") == "warning"
    assert "Niedostępne" in dialog.result_text.toPlainText()
    assert "Nie wpływa to na wynik" in dialog.result_text.toPlainText()
    assert "private/path" not in dialog.result_text.toPlainText()
    assert "10001,54 m²" in dialog.result_text.toPlainText()
    assert dialog.export_button.isEnabled()
    assert "Niedostępne" in dialog._report_markdown
    assert "Nie wpływa to na wynik" in " ".join(
        dialog._report_markdown.split()
    )


def test_failed_recalculation_clears_display_and_export(
    calculated_dialog, monkeypatch
):
    dialog = calculated_dialog

    def fail_calculation(*args, **kwargs):
        raise GeometryTransformError("missing grid")

    monkeypatch.setattr(
        dialog_module, "calculate_selected_parcel", fail_calculation
    )
    messages = []
    monkeypatch.setattr(
        dialog_module.QMessageBox,
        "warning",
        lambda *args: messages.append(args[-1]),
    )
    dialog.calculate()

    assert len(messages) == 1
    assert dialog.last_result is None
    assert dialog._report_markdown == ""
    assert not dialog.export_button.isEnabled()
    assert "10001,54" not in dialog.result_text.toPlainText()
    assert dialog.result_text._hover_help == {}
    assert dialog.status_card.property("state") == "error"


def test_repair_setting_invalidates_report_until_recalculation(
    calculated_dialog,
):
    dialog = calculated_dialog
    dialog.repair_mode_combo.setCurrentIndex(1)

    assert dialog.last_result is None
    assert dialog._report_markdown == ""
    assert not dialog.export_button.isEnabled()
    assert "10001,54" not in dialog.result_text.toPlainText()
    assert dialog.result_text._hover_help == {}
    assert dialog.status_card.property("state") == "ready"

    dialog.calculate()
    assert dialog.last_result is not None
    assert dialog.export_button.isEnabled()
    assert "Wykryj błędy" in dialog._report_markdown


def test_zone_setting_invalidates_report_and_missing_zone_stays_empty(
    monkeypatch,
):
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((21 52,21.001 52,21.001 52.001,21 52.001,21 52)))",
        crs="EPSG:4326",
    )
    dialog = _dialog(layer)
    dialog.zone_combo.setCurrentIndex(dialog.zone_combo.findData(7))
    dialog.calculate()
    assert dialog.last_result is not None
    assert dialog.export_button.isEnabled()

    dialog.zone_combo.setCurrentIndex(dialog.zone_combo.findData(6))
    assert dialog.last_result is None
    assert not dialog.export_button.isEnabled()
    assert "Raport obliczenia pojawi się tutaj" in (
        dialog.result_text.toPlainText()
    )
    dialog.zone_combo.setCurrentIndex(0)
    monkeypatch.setattr(dialog_module.QMessageBox, "warning", lambda *a: None)
    dialog.calculate()
    assert dialog.last_result is None
    assert dialog._report_markdown == ""
    assert dialog.status_card.property("state") == "error"


@pytest.mark.parametrize("filename", ["raport", "raport.md", "raport.MD"])
def test_markdown_export_saves_current_report_utf8_with_default_suffix(
    calculated_dialog, monkeypatch, tmp_path, filename
):
    dialog = calculated_dialog
    before = dialog.result_text.toHtml()
    result = dialog.last_result

    def choose_destination(file_dialog):
        assert file_dialog.defaultSuffix() == "md"
        assert not file_dialog.testOption(
            dialog_module.QFileDialog.Option.DontConfirmOverwrite
        )
        file_dialog.selectFile(str(tmp_path / filename))
        return 1

    def unexpected_recalculation(*args, **kwargs):
        pytest.fail("Export must not recalculate the result")

    monkeypatch.setattr(dialog_module, "execute_dialog", choose_destination)
    monkeypatch.setattr(
        dialog_module, "calculate_selected_parcel", unexpected_recalculation
    )
    dialog.export_button.click()

    destination = tmp_path / (
        filename if "." in filename else filename + ".md"
    )
    text = destination.read_text(encoding="utf-8")
    assert text == dialog._report_markdown
    assert "# Poprawka odwzorowawcza PL-2000" in text
    document = dialog_module.QTextDocument()
    document.setMarkdown(text)
    rendered = document.toPlainText()
    for expected in (
        "Warstwa: Działki",
        "Obiekt (FID):",
        "EPSG:2178",
        "Sprawdź geometrię; licz bez naprawy",
        "10000,00 m²",
        "10001,54 m²",
        "1,0002 ha",
        "5800000,000 m",
        "7500000,000 m",
        "0,9999230000",
        "PARAMETRY WZORU",
        "STREFA I GEOMETRIA",
        "UWAGI",
        "Brak uwag",
    ):
        assert expected in rendered
    for absent in ("param:", "result:", "diagnostic:", "warning:", "Najedź"):
        assert absent not in text
    assert "10001,539" not in text
    assert dialog.result_text.toHtml() == before
    assert dialog.last_result is result


def test_cancelled_export_preserves_report_and_existing_file(
    calculated_dialog,
    monkeypatch,
    tmp_path,
):
    destination = tmp_path / "existing.md"
    destination.write_text("existing report", encoding="utf-8")
    dialog = calculated_dialog
    before = dialog._report_markdown

    def cancel(file_dialog):
        file_dialog.selectFile(str(destination))
        return 0

    monkeypatch.setattr(dialog_module, "execute_dialog", cancel)
    dialog.export_report()
    assert destination.read_text(encoding="utf-8") == "existing report"
    assert dialog._report_markdown == before
    assert dialog.export_button.isEnabled()


@pytest.mark.parametrize("failure", ["open", "write", "commit"])
def test_export_failure_does_not_destroy_existing_file_or_result(
    calculated_dialog,
    monkeypatch,
    tmp_path,
    failure,
):
    destination = tmp_path / "existing.md"
    destination.write_text("existing report", encoding="utf-8")
    dialog = calculated_dialog
    before = dialog.last_result
    warnings = []

    def choose(file_dialog):
        file_dialog.selectFile(str(destination))
        return 1

    class FailingSaveFile(dialog_module.QSaveFile):
        def open(self, flags):
            if failure == "open":
                return False
            return super().open(flags)

        def write(self, content):
            if failure == "write":
                return super().write(content[:10])
            return super().write(content)

        def commit(self):
            if failure == "commit":
                self.cancelWriting()
            return super().commit()

    monkeypatch.setattr(dialog_module, "execute_dialog", choose)
    monkeypatch.setattr(dialog_module, "QSaveFile", FailingSaveFile)
    monkeypatch.setattr(
        dialog_module.QMessageBox, "warning", lambda *a: warnings.append(a[-1])
    )
    dialog.export_report()
    assert len(warnings) == 1
    assert "Nie udało się zapisać" in warnings[0]
    assert destination.read_text(encoding="utf-8") == "existing report"
    assert dialog.last_result is before
    assert dialog.export_button.isEnabled()
    assert dialog._report_markdown


@pytest.mark.parametrize("repair_index", [0, 1])
def test_markdown_keeps_geometry_warnings_and_diagnostic_banner(repair_index):
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((7500000 5800000,7500200 5800200,"
        "7500000 5800200,7500100 5800000,7500000 5800000)))"
    )
    dialog = _dialog(layer)
    dialog.repair_mode_combo.setCurrentIndex(repair_index)
    dialog.calculate()
    assert dialog.export_button.isEnabled()
    for warning in dialog.last_result.warnings:
        # Qt wraps long paragraphs, so compare words independently of layout.
        expected = " ".join(dialog_module._warning_label(warning).split())
        assert expected in " ".join(dialog._report_markdown.split())
    assert ("WYNIK DIAGNOSTYCZNY" in dialog._report_markdown) == (
        repair_index == 0
    )
    assert "warning:" not in dialog._report_markdown


def test_export_without_current_report_does_not_open_file_dialog(
    calculated_dialog,
    monkeypatch,
):
    dialog = calculated_dialog
    dialog.repair_mode_combo.setCurrentIndex(1)

    def unexpected_dialog(*args):
        pytest.fail("A stale report must not be offered for export")

    monkeypatch.setattr(dialog_module, "execute_dialog", unexpected_dialog)
    dialog.export_report()


@pytest.mark.parametrize(
    "layer_name",
    [
        "Działki <b>źródło</b> & [opis](https://example.invalid)",
        "działki `nazwa` **2026** _archiwum_",
    ],
)
def test_markdown_escapes_layer_name_and_keeps_calculation_context(layer_name):
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    layer.setName(layer_name)
    dialog = _dialog(layer)
    dialog.calculate()
    before = dialog._report_markdown
    document = dialog_module.QTextDocument()
    document.setMarkdown(before)
    assert layer.name() in " ".join(document.toPlainText().split())
    layer.setName("Nowa nazwa")
    assert dialog._report_markdown == before


def test_about_information_opens_from_calculator(
    calculated_dialog, monkeypatch
):
    opened = []
    monkeypatch.setattr(
        dialog_module, "execute_dialog", lambda dialog: opened.append(dialog)
    )
    calculated_dialog.about_button.click()
    assert len(opened) == 1
    assert opened[0].windowTitle() == "Poprawka odwzorowawcza PL-2000"
    assert opened[0].objectName() == "aboutDialog"
    assert "Bandit" in opened[0].findChild(QLabel, "aboutChecks").text()
    assert (
        "Autor nie bierze odpowiedzialności"
        in opened[0].findChild(QLabel, "aboutDisclosure").text()
    )
    assert calculated_dialog.last_result is not None


def test_about_text_is_readable_in_a_small_window():
    dialog = AboutDialog()
    dialog.resize(560, 400)
    dialog.show()
    QApplication.processEvents()
    scroll = dialog.findChild(QScrollArea, "aboutScroll")
    assert scroll.verticalScrollBar().maximum() > 0
    for label in dialog.findChildren(QLabel):
        if label.wordWrap():
            assert label.height() >= label.heightForWidth(label.width())
    dialog.close()


def test_about_english_description_matches_published_metadata():
    root = Path(__file__).resolve().parents[2]
    metadata = read_plugin_metadata(root)
    dialog = AboutDialog(plugin_root=root)
    english = dialog.findChild(QLabel, "aboutEnglish").text()
    assert english == ("EN\n\n" + metadata["about"].partition("\nEN\n")[2])
    assert "The author accepts no responsibility" in english
    assert "Does not send data outside QGIS" in english
    assert "§ 16(2)" in english
    assert "More info at GitHub repo." in english
    assert (
        dialog.findChild(QLabel, "aboutSummary")
        .text()
        .startswith("Oblicza pole działki")
    )
