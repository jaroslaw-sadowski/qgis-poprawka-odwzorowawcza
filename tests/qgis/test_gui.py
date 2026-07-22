from decimal import Decimal

from qgis.core import QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer

import gui.dialog as dialog_module
from adapters import RepairMethod
from gui import SelectedParcelDialog


def _layer_with_geometry(wkt: str, *, crs: str = "EPSG:2178") -> QgsVectorLayer:
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


def test_dialog_calculates_selected_pl2000_parcel_without_editing_source() -> None:
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    source_wkb = bytes(next(layer.getFeatures()).geometry().asWkb())
    dialog = _dialog(layer)

    assert dialog.windowTitle() == "Poprawka odwzorowawcza — zaznaczona działka"
    assert dialog.zone_combo.isEnabled() is False
    assert "strefa 7" in dialog.zone_combo.currentText()

    dialog.calculate_button.click()

    assert dialog.last_result is not None
    assert dialog.last_result.calculation is not None
    assert dialog.last_result.calculation.legal_area_ha_rounded == Decimal("1.0002")
    text = dialog.result_text.toPlainText()
    assert "Pole ewidencyjne: 1,0002 ha" in text
    assert "PGK — prawne X (północna)" in text
    assert "PGK — prawne Y (wschodnia)" in text
    assert "Strefa PL-2000: 7 (EPSG:2178)" in text
    assert bytes(next(layer.getFeatures()).geometry().asWkb()) == source_wkb


def test_dialog_strict_mode_blocks_result_after_repair() -> None:
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((7500000 5800000,7500100 5800100,"
        "7500000 5800100,7500100 5800000,7500000 5800000)))"
    )
    source_wkb = bytes(next(layer.getFeatures()).geometry().asWkb())
    dialog = _dialog(layer)

    dialog.calculate_button.click()

    assert dialog.last_result is not None
    assert dialog.last_result.calculation is None
    assert dialog.last_result.preparation.report.repair_method is RepairMethod.STRUCTURE
    assert "Tryb STRICT zablokował wynik ustawowy" in dialog.status_label.text()
    assert "Nie wyznaczono" in dialog.result_text.toPlainText()
    assert bytes(next(layer.getFeatures()).geometry().asWkb()) == source_wkb


def test_dialog_auto_repair_marks_repaired_calculation() -> None:
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((7500000 5800000,7500100 5800100,"
        "7500000 5800100,7500100 5800000,7500000 5800000)))"
    )
    dialog = _dialog(layer)
    dialog.repair_mode_combo.setCurrentIndex(1)

    dialog.calculate_button.click()

    assert dialog.last_result is not None
    assert dialog.last_result.calculation is not None
    assert "naprawionej kopii" in dialog.status_label.text()
    assert "Naprawa zmieniła zbiór wierzchołków" in (dialog.result_text.toPlainText())


def test_dialog_requires_confirmed_zone_for_other_crs(monkeypatch) -> None:
    layer = _layer_with_geometry(
        "MULTIPOLYGON (((21 52,21.001 52,21.001 52.001,21 52.001,21 52)))",
        crs="EPSG:4326",
    )
    dialog = _dialog(layer)
    warnings = []

    class FakeMessageBox:
        @staticmethod
        def warning(parent, title, message):
            del parent, title
            warnings.append(message)

    monkeypatch.setattr(dialog_module, "QMessageBox", FakeMessageBox)

    dialog.calculate_button.click()

    assert dialog.last_result is None
    assert warnings == ["Wybierz strefę PL-2000 i potwierdź ją przed obliczeniem."]

    dialog.zone_combo.setCurrentIndex(3)
    dialog.calculate_button.click()
    assert dialog.last_result is not None
    assert dialog.last_result.preparation.target_epsg == 2178
