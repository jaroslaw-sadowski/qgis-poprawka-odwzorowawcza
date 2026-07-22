import pytest
from qgis.core import (
    NULL,
    QgsApplication,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsProcessing,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingUtils,
    QgsVectorLayer,
)

from compat import FIELD_TYPE_INT, FIELD_TYPE_STRING
from processing_provider import CalculateEgibAreaAlgorithm, EgibAreaProvider


def _polygon_layer(*wkts: str) -> QgsVectorLayer:
    layer = QgsVectorLayer("MultiPolygon?crs=EPSG:2178", "parcels", "memory")
    layer.dataProvider().addAttributes([QgsField("parcel_id", FIELD_TYPE_INT)])
    layer.updateFields()

    features = []
    for parcel_id, wkt in enumerate(wkts, start=1):
        feature = QgsFeature(layer.fields())
        feature.setAttribute("parcel_id", parcel_id)
        feature.setGeometry(QgsGeometry.fromWkt(wkt))
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    return layer


def _run_algorithm(
    layer: QgsVectorLayer,
    *,
    zone_index: int = 0,
    repair_mode_index: int = 0,
):
    algorithm = CalculateEgibAreaAlgorithm()
    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()
    parameters = {
        algorithm.INPUT: layer,
        algorithm.ZONE: zone_index,
        algorithm.REPAIR_MODE: repair_mode_index,
        algorithm.OUTPUT: QgsProcessing.TEMPORARY_OUTPUT,
    }

    results, ok = algorithm.run(
        parameters,
        context,
        feedback,
        catchExceptions=False,
    )
    assert ok is True
    output = QgsProcessingUtils.mapLayerFromString(
        results[algorithm.OUTPUT], context
    )
    assert output is not None
    return output, context


def test_provider_registers_and_removes_algorithm() -> None:
    registry = QgsApplication.processingRegistry()
    provider = EgibAreaProvider()

    assert registry.addProvider(provider) is True
    try:
        algorithm = registry.algorithmById("egib_area:calculate_egib_area")
        assert algorithm is not None
        assert algorithm.provider().id() == "egib_area"
    finally:
        assert registry.removeProvider(provider) is True

    assert registry.algorithmById("egib_area:calculate_egib_area") is None


def test_batch_creates_new_layer_and_leaves_input_unchanged() -> None:
    layer = _polygon_layer(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))",
        "MULTIPOLYGON (((7500200 5800200,7500250 5800200,"
        "7500250 5800250,7500200 5800250,7500200 5800200)))",
    )
    input_fields = layer.fields().names()
    input_wkbs = [
        bytes(feature.geometry().asWkb()) for feature in layer.getFeatures()
    ]

    output, _context = _run_algorithm(layer)

    assert output is not layer
    assert output.featureCount() == 2
    assert set(CalculateEgibAreaAlgorithm.OUTPUT_FIELD_NAMES).issubset(
        output.fields().names()
    )
    assert output.fields().field("egib_area_m2").precision() == 10
    assert output.fields().field("egib_area_ha").precision() == 4
    assert layer.fields().names() == input_fields
    assert [
        bytes(feature.geometry().asWkb()) for feature in layer.getFeatures()
    ] == input_wkbs
    assert "egib_status" not in layer.fields().names()

    first = next(output.getFeatures())
    assert first["parcel_id"] == 1
    assert first["egib_status"] == "ok"
    assert first["egib_po_m2"] == pytest.approx(10_000.0)
    assert first["egib_area_m2"] == pytest.approx(10_001.53994071)
    assert first["egib_area_ha"] == pytest.approx(1.0002)
    assert first["egib_zone"] == 7
    assert first["egib_epsg"] == 2178
    assert first["egib_repair_method"] == "none"
    assert first.geometry().isMultipart() is True


def test_strict_mode_writes_diagnostics_but_no_statutory_result() -> None:
    layer = _polygon_layer(
        "MULTIPOLYGON (((7500000 5800000,7500100 5800100,"
        "7500000 5800100,7500100 5800000,7500000 5800000)))"
    )

    output, _context = _run_algorithm(layer, repair_mode_index=0)
    result = next(output.getFeatures())

    assert result["egib_status"] == "strict_repair_required"
    assert result["egib_repair_method"] == "structure"
    assert result["egib_valid_before"] is False
    assert result["egib_valid_after"] is True
    assert result["egib_area_m2"] == NULL
    assert result["egib_repaired_area_m2"] == pytest.approx(5_000.0)
    assert result.geometry().isGeosValid() is True


def test_auto_repair_calculates_area_in_new_layer() -> None:
    layer = _polygon_layer(
        "MULTIPOLYGON (((7500000 5800000,7500100 5800100,"
        "7500000 5800100,7500100 5800000,7500000 5800000)))"
    )
    source_wkb = bytes(next(layer.getFeatures()).geometry().asWkb())

    output, _context = _run_algorithm(layer, repair_mode_index=1)
    result = next(output.getFeatures())

    assert result["egib_status"] == "repaired"
    assert result["egib_po_m2"] == pytest.approx(5_000.0)
    assert result["egib_area_m2"] is not None
    assert "repair_changed_boundary_vertices" in result["egib_warnings"]
    assert bytes(next(layer.getFeatures()).geometry().asWkb()) == source_wkb


def test_feature_without_geometry_is_reported_and_batch_continues() -> None:
    layer = _polygon_layer(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    empty_feature = QgsFeature(layer.fields())
    empty_feature.setAttribute("parcel_id", 2)
    layer.dataProvider().addFeature(empty_feature)

    output, _context = _run_algorithm(layer)
    results = {
        feature["parcel_id"]: feature for feature in output.getFeatures()
    }

    assert output.featureCount() == 2
    assert results[1]["egib_status"] == "ok"
    assert results[2]["egib_status"] == "error"
    assert results[2]["egib_zone"] == 7
    assert results[2]["egib_epsg"] == 2178
    assert results[2].hasGeometry() is False
    assert "null" in results[2]["egib_warnings"]


def test_reserved_output_field_collision_is_rejected() -> None:
    layer = _polygon_layer(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    layer.dataProvider().addAttributes(
        [QgsField("egib_status", FIELD_TYPE_STRING)]
    )
    layer.updateFields()

    with pytest.raises(QgsProcessingException, match="egib_status"):
        _run_algorithm(layer)


def test_non_pl2000_input_requires_explicit_zone() -> None:
    layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "parcels", "memory")

    with pytest.raises(QgsProcessingException, match="zone|required|stref"):
        _run_algorithm(layer, zone_index=0)


def test_explicit_zone_transforms_non_pl2000_input_in_output_copy() -> None:
    layer = QgsVectorLayer("MultiPolygon?crs=EPSG:4326", "parcels", "memory")
    feature = QgsFeature(layer.fields())
    feature.setGeometry(
        QgsGeometry.fromWkt(
            "MULTIPOLYGON (((21 52,21.001 52,21.001 52.001,21 52.001,21 52)))"
        )
    )
    layer.dataProvider().addFeature(feature)
    source_wkb = bytes(next(layer.getFeatures()).geometry().asWkb())

    output, _context = _run_algorithm(layer, zone_index=3)
    result = next(output.getFeatures())

    assert output.crs().authid() == "EPSG:2178"
    assert result["egib_status"] == "ok"
    assert result["egib_zone"] == 7
    assert result["egib_epsg"] == 2178
    assert result["egib_area_m2"] > 0
    assert bytes(next(layer.getFeatures()).geometry().asWkb()) == source_wkb
