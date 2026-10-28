import pytest
from qgis.core import (
    QgsFeature,
    QgsGeometry,
    QgsProcessing,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingUtils,
    QgsVectorLayer,
)

from processing_provider import CalculateEgibAreaAlgorithm


@pytest.fixture
def parcels():
    layer = QgsVectorLayer(
        "MultiPolygon?crs=EPSG:2178&field=numer:string", "Działki", "memory"
    )
    for number, wkt in enumerate(
        (
            "POLYGON ((7499950 5799950,7500050 5799950,"
            "7500050 5800050,7499950 5800050,7499950 5799950))",
            "POLYGON ((7500000 5800000,7500200 5800200,"
            "7500000 5800200,7500100 5800000,7500000 5800000))",
            None,
        ),
        start=1,
    ):
        feature = QgsFeature(layer.fields())
        feature.setAttributes([str(number)])
        if wkt:
            feature.setGeometry(QgsGeometry.fromWkt(wkt))
        assert layer.dataProvider().addFeature(feature)
    yield layer


@pytest.mark.parametrize("destination", ["memory:", "results.gpkg"])
def test_po_field_names_and_polish_headings_persist_with_table_layout(
    parcels, tmp_path, destination
):
    algorithm = CalculateEgibAreaAlgorithm()
    context = QgsProcessingContext()
    destination = (
        destination
        if destination == "memory:"
        else str(tmp_path / destination)
    )
    results, ok = algorithm.run(
        {algorithm.INPUT: parcels, algorithm.OUTPUT: destination},
        context,
        QgsProcessingFeedback(),
        catchExceptions=False,
    )
    assert ok
    output = QgsProcessingUtils.mapLayerFromString(
        results[algorithm.OUTPUT], context
    )
    if destination.endswith(".gpkg"):
        # Reopening the file must retain the same view without the project.
        output = QgsVectorLayer(destination, "Ponownie otwarty wynik", "ogr")
        assert output.isValid()
        assert not list(tmp_path.glob("*.qml"))

    assert set(algorithm.OUTPUT_FIELD_NAMES).issubset(output.fields().names())
    assert {
        "PO_P0_m2",
        "PO_QGIS_m2",
        "PO_dP_m2",
        "PO_P_m2",
        "PO_P_ha",
    }.issubset(output.fields().names())
    assert not any(
        name.startswith("egib_") for name in output.fields().names()
    )
    assert next(output.getFeatures())["numer"] == "1"
    assert output.fields().field("PO_P_m2").alias() == (
        "PO_P_m2 — Powierzchnia po poprawce P [m²]"
    )
    assert output.fields().field("PO_P_ha").alias() == (
        "PO_P_ha — Powierzchnia po poprawce P [ha]"
    )
    assert output.fields().field("PO_uwagi").alias() == (
        "PO_uwagi — Uwagi i ostrzeżenia"
    )
    for field_name in algorithm.OUTPUT_FIELD_NAMES:
        assert (
            output.fields()
            .field(field_name)
            .alias()
            .startswith(field_name + " — ")
        )
    columns = {
        column.name: column.hidden
        for column in output.attributeTableConfig().columns()
        if column.name
    }
    assert not columns["numer"]
    assert not columns["PO_P_ha"]
    assert not columns["PO_status"]
    assert not columns["PO_uwagi"]
    assert columns["PO_wierz_po"]
    assert columns["PO_PGK_X"]
    assert parcels.fields().names() == ["numer"]


@pytest.mark.parametrize(
    ("repair_mode", "expected_summary"),
    [
        (0, "po naprawie: 0; diagnostyczne: 1; błędy: 1"),
        (1, "po naprawie: 1; diagnostyczne: 0; błędy: 1"),
    ],
)
def test_batch_summary_matches_saved_results(
    parcels, repair_mode, expected_summary
):
    algorithm = CalculateEgibAreaAlgorithm()
    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()
    result, ok = algorithm.run(
        {
            algorithm.INPUT: parcels,
            algorithm.REPAIR_MODE: repair_mode,
            algorithm.OUTPUT: QgsProcessing.TEMPORARY_OUTPUT,
        },
        context,
        feedback,
        catchExceptions=False,
    )
    assert ok
    output = QgsProcessingUtils.mapLayerFromString(
        result[algorithm.OUTPUT], context
    )
    assert output.featureCount() == 3
    assert "Przetworzono: 3; poprawne bez naprawy: 1;" in feedback.textLog()
    assert expected_summary in feedback.textLog()


def test_cancelled_batch_identifies_partial_result(parcels):
    algorithm = CalculateEgibAreaAlgorithm()
    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()
    feedback.progressChanged.connect(lambda progress: feedback.cancel())
    result, ok = algorithm.run(
        {
            algorithm.INPUT: parcels,
            algorithm.OUTPUT: QgsProcessing.TEMPORARY_OUTPUT,
        },
        context,
        feedback,
        catchExceptions=False,
    )
    assert ok
    output = QgsProcessingUtils.mapLayerFromString(
        result[algorithm.OUTPUT], context
    )
    assert feedback.isCanceled()
    assert output.featureCount() == 1
    assert "Przetworzono: 1;" in feedback.textLog()
    assert "Wynik jest niepełny" in feedback.textLog()
