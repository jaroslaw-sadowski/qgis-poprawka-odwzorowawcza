import os
from unittest.mock import Mock

import pytest
from qgis.core import (
    NULL,
    QgsApplication,
    QgsDataSourceUri,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsGeometry,
    QgsProcessing,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeatureSourceDefinition,
    QgsProcessingFeedback,
    QgsProcessingOutputLayerDefinition,
    QgsProcessingRegistry,
    QgsProcessingUtils,
    QgsVectorFileWriter,
    QgsVectorLayer,
)
from qgis.gui import QgsProcessingToolboxModel

import adapters.geometry as geometry_module
import processing_provider.area_algorithm as algorithm_module
from adapters import GeometryTransformError
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
    destination=QgsProcessing.TEMPORARY_OUTPUT,
    feedback=None,
):
    algorithm = CalculateEgibAreaAlgorithm()
    context = QgsProcessingContext()
    if feedback is None:
        feedback = QgsProcessingFeedback()
    parameters = {
        algorithm.INPUT: layer,
        algorithm.ZONE: zone_index,
        algorithm.REPAIR_MODE: repair_mode_index,
        algorithm.OUTPUT: destination,
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

    assert CalculateEgibAreaAlgorithm.REPAIR_OPTIONS == (
        "Sprawdź geometrię; licz bez naprawy",
        "Wykryj błędy i spróbuj naprawić geometrię "
        "(uwaga: geometria wyniku może się zmienić)",
    )

    assert registry.addProvider(provider) is True
    try:
        algorithm = registry.algorithmById("egib_area:calculate_egib_area")
        assert algorithm is not None
        assert algorithm.provider().id() == "egib_area"
        assert algorithm.displayName() == "Poprawka odwzorowawcza PL-2000"
        assert provider.name() == algorithm.displayName()
        assert provider.longName() == algorithm.displayName()
        assert algorithm.group() == ""
        assert algorithm.groupId() == ""
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
    assert not any(
        name.startswith("egib_") for name in output.fields().names()
    )
    for field_name in (
        "PO_P0_m2",
        "PO_QGIS_m2",
        "PO_dP_m2",
        "PO_P_m2",
        "PO_pole_przed_m2",
        "PO_pole_po_m2",
        "PO_zmiana_m2",
    ):
        assert output.fields().field(field_name).precision() == 2
    assert output.fields().field("PO_P_ha").precision() == 4
    assert layer.fields().names() == input_fields
    assert [
        bytes(feature.geometry().asWkb()) for feature in layer.getFeatures()
    ] == input_wkbs
    assert "PO_status" not in layer.fields().names()

    first = next(output.getFeatures())
    assert first["parcel_id"] == 1
    assert first["PO_status"] == "source_geometry"
    assert first["PO_P0_m2"] == 10_000.00
    assert first["PO_QGIS_m2"] == 10_001.54
    assert first["PO_dP_m2"] == -1.54
    assert first["PO_P_m2"] == 10_001.54
    assert first["PO_P_ha"] == pytest.approx(1.0002)
    assert first["PO_strefa"] == 7
    assert first["PO_EPSG"] == 2178
    assert first["PO_naprawa"] == "none"
    assert first.geometry().isMultipart() is True


def test_source_mode_reports_invalid_geometry_without_repair() -> None:
    layer = _polygon_layer(
        "MULTIPOLYGON (((7500000 5800000,7500200 5800200,"
        "7500000 5800200,7500100 5800000,7500000 5800000)))"
    )
    source_wkb = bytes(next(layer.getFeatures()).geometry().asWkb())

    output, _context = _run_algorithm(layer, repair_mode_index=0)
    result = next(output.getFeatures())

    assert result["PO_status"] == "invalid_source_geometry"
    assert "geometry_not_repaired" in result["PO_uwagi"]
    assert result["PO_naprawa"] == "none"
    assert result["PO_poprawna_przed"] is False
    assert result["PO_poprawna_po"] is False
    assert result["PO_P0_m2"] == 10_000.00
    assert result["PO_P_m2"] is not NULL
    assert bytes(result.geometry().asWkb()) == source_wkb


def test_auto_repair_calculates_area_in_new_layer() -> None:
    layer = _polygon_layer(
        "MULTIPOLYGON (((7500000 5800000,7500100 5800100,"
        "7500000 5800100,7500100 5800000,7500000 5800000)))"
    )
    source_wkb = bytes(next(layer.getFeatures()).geometry().asWkb())

    output, _context = _run_algorithm(layer, repair_mode_index=1)
    result = next(output.getFeatures())

    assert result["PO_status"] == "repaired"
    assert result["PO_P0_m2"] == pytest.approx(5_000.0)
    assert result["PO_P_m2"] is not None
    assert "repair_changed_boundary_vertices" in result["PO_uwagi"]
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
    assert results[1]["PO_status"] == "source_geometry"
    assert results[2]["PO_status"] == "error"
    assert results[2]["PO_strefa"] == 7
    assert results[2]["PO_EPSG"] == 2178
    assert results[2].hasGeometry() is False
    assert "Geometria wejściowa jest pusta" in results[2]["PO_uwagi"]


def test_feature_over_geometry_budget_is_reported_without_processing(
    monkeypatch,
) -> None:
    layer = _polygon_layer(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    monkeypatch.setattr(
        geometry_module,
        "MAX_BOUNDARY_COORDINATES",
        4,
    )

    output, _context = _run_algorithm(layer)
    result = next(output.getFeatures())

    assert result["PO_status"] == "error"
    assert result["PO_P_m2"] == NULL
    assert "limit liczby współrzędnych: 5 > 4" in result["PO_uwagi"]
    assert result.hasGeometry() is False


def test_processing_hides_raw_transform_error_details(monkeypatch) -> None:
    layer = _polygon_layer(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )

    def fail_preparation(*args, **kwargs):
        del args, kwargs
        raise GeometryTransformError(
            "grid missing at /home/private-user/secret-grid.gsb"
        )

    monkeypatch.setattr(
        algorithm_module,
        "prepare_geometry",
        fail_preparation,
    )

    output, _context = _run_algorithm(layer)
    result = next(output.getFeatures())

    assert result["PO_status"] == "error"
    assert "Sprawdź CRS warstwy" in result["PO_uwagi"]
    assert "/home/private-user" not in result["PO_uwagi"]
    assert "grid missing" not in result["PO_uwagi"]


@pytest.mark.parametrize("field_name", ["PO_status", "PO_STATUS"])
def test_reserved_output_field_collision_is_rejected(field_name) -> None:
    layer = _polygon_layer(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    layer.dataProvider().addAttributes(
        [QgsField(field_name, FIELD_TYPE_STRING)]
    )
    layer.updateFields()

    with pytest.raises(QgsProcessingException, match=field_name):
        _run_algorithm(layer)


@pytest.mark.parametrize("destination", ["memory:", "result.gpkg"])
def test_existing_source_attribute_with_old_prefix_is_preserved(
    tmp_path, destination
):
    layer = _polygon_layer(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    layer.dataProvider().addAttributes(
        [QgsField("egib_area_m2", FIELD_TYPE_STRING)]
    )
    layer.updateFields()
    feature = next(layer.getFeatures())
    layer.dataProvider().changeAttributeValues(
        {
            feature.id(): {
                layer.fields().indexFromName("egib_area_m2"): "źródło"
            }
        }
    )
    before = [feature.attributes() for feature in layer.getFeatures()]

    if destination != "memory:":
        destination = str(tmp_path / destination)
    output, _context = _run_algorithm(layer, destination=destination)
    if destination.endswith(".gpkg"):
        output = QgsVectorLayer(destination, "Ponownie otwarty wynik", "ogr")
        assert output.isValid()
    result = next(output.getFeatures())

    assert result["egib_area_m2"] == "źródło"
    assert result["PO_P_m2"] == 10_001.54
    assert [feature.attributes() for feature in layer.getFeatures()] == before
    assert [
        name for name in output.fields().names() if name.startswith("egib_")
    ] == ["egib_area_m2"]


@pytest.fixture
def saved_parcels(tmp_path):
    layer = _polygon_layer(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    path = tmp_path / "source.gpkg"
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = "parcels"
    result = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, str(path), QgsProcessingContext().transformContext(), options
    )
    assert result[0] == QgsVectorFileWriter.WriterError.NoError
    options.layerName = "other"
    options.actionOnExistingFile = (
        QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
    )
    result = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, str(path), QgsProcessingContext().transformContext(), options
    )
    assert result[0] == QgsVectorFileWriter.WriterError.NoError
    return path


def _geopackage_destination(path, table):
    uri = QgsDataSourceUri()
    uri.setDatabase(str(path))
    uri.setTable(table)
    uri.setGeometryColumn("geom")
    return "ogr:" + uri.uri(False)


@pytest.mark.parametrize(
    "destination_kind",
    [
        "file",
        "wrapped",
        "table",
        "other_table",
        "symlink",
        "hardlink",
        "source_definition",
        "encoded_table",
        "default_extension",
    ],
)
def test_output_cannot_overwrite_source_database(
    saved_parcels, tmp_path, destination_kind
):
    path = saved_parcels
    source = str(path)
    before = path.read_bytes()
    destination = str(path)
    if destination_kind == "wrapped":
        destination = QgsProcessingOutputLayerDefinition(destination)
    elif destination_kind == "source_definition":
        source = QgsProcessingFeatureSourceDefinition(str(path))
    elif destination_kind == "encoded_table":
        destination = QgsProcessingUtils.encodeProviderKeyAndUri(
            "ogr", f"{path}|layername=parcels"
        )
    elif destination_kind == "default_extension":
        destination = str(path.with_suffix(""))
    elif destination_kind in ("table", "other_table"):
        destination = _geopackage_destination(
            path, "PARCELS" if destination_kind == "table" else "other"
        )
    elif destination_kind in ("symlink", "hardlink"):
        link = tmp_path / "link.gpkg"
        try:
            if destination_kind == "symlink":
                link.symlink_to(path)
            else:
                os.link(path, link)
        except OSError as error:
            pytest.skip(f"System nie pozwala utworzyć dowiązania: {error}")
        destination = str(link)

    with pytest.raises(QgsProcessingException, match="nie może nadpisać"):
        _run_algorithm(source, destination=destination)

    assert path.read_bytes() == before
    for table in ("parcels", "other"):
        reopened = QgsVectorLayer(f"{path}|layername={table}", table, "ogr")
        assert reopened.isValid()
        assert reopened.featureCount() == 1
        assert "PO_P_m2" not in reopened.fields().names()


def test_output_can_add_new_table_to_source_geopackage(saved_parcels):
    path = saved_parcels
    source = QgsVectorLayer(str(path), "parcels", "ogr")
    assert source.isValid()
    source_wkb = bytes(next(source.getFeatures()).geometry().asWkb())
    output, _context = _run_algorithm(
        source, destination=_geopackage_destination(path, "result")
    )

    assert output.featureCount() == 1
    assert next(output.getFeatures())["PO_P_ha"] == pytest.approx(1.0002)
    for table in ("parcels", "other"):
        reopened = QgsVectorLayer(f"{path}|layername={table}", table, "ogr")
        assert reopened.featureCount() == 1
        assert "PO_P_m2" not in reopened.fields().names()
        assert bytes(next(reopened.getFeatures()).geometry().asWkb()) == (
            source_wkb
        )


@pytest.mark.parametrize(
    ("driver", "source_name", "output_name"),
    [
        ("ESRI Shapefile", "source.dbf.shp", "source.dbf"),
        ("GeoJSON", "source.json.geojson", "source.json"),
        ("SQLite", "source.db.sqlite", "source.db"),
        ("MapInfo File", "source.mif.tab", "source.mif"),
    ],
)
def test_writer_extension_normalization_cannot_overwrite_source(
    tmp_path, driver, source_name, output_name
):
    layer = _polygon_layer(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    path = tmp_path / source_name
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = driver
    result = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, str(path), QgsProcessingContext().transformContext(), options
    )
    assert result[0] == QgsVectorFileWriter.WriterError.NoError
    before = path.read_bytes()

    with pytest.raises(QgsProcessingException, match="nie może nadpisać"):
        _run_algorithm(str(path), destination=str(tmp_path / output_name))

    assert path.read_bytes() == before
    reopened = QgsVectorLayer(str(path), "source", "ogr")
    assert reopened.featureCount() == 1
    assert "PO_P_m2" not in reopened.fields().names()
    del reopened


def test_spatialite_destination_cannot_overwrite_source(tmp_path):
    layer = _polygon_layer(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    path = tmp_path / "source.sqlite"
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "SQLite"
    options.datasourceOptions = ["SPATIALITE=YES"]
    options.layerName = "parcels"
    result = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, str(path), QgsProcessingContext().transformContext(), options
    )
    assert result[0] == QgsVectorFileWriter.WriterError.NoError
    uri = QgsDataSourceUri()
    uri.setDatabase(str(path))
    uri.setDataSource("", "parcels", "GEOMETRY")
    source = QgsProcessingUtils.encodeProviderKeyAndUri(
        "spatialite", uri.uri(False)
    )
    before = path.read_bytes()

    with pytest.raises(QgsProcessingException, match="nie może nadpisać"):
        _run_algorithm(source, destination=source)

    assert path.read_bytes() == before


@pytest.mark.parametrize("port", ["5432", ""])
@pytest.mark.parametrize("schema", ["public", ""])
def test_postgres_destination_checks_table_without_using_credentials(
    monkeypatch, port, schema
):
    algorithm = CalculateEgibAreaAlgorithm()
    algorithm.initAlgorithm()
    source_uri = QgsDataSourceUri()
    source_uri.setConnection("host", "5432", "database", "reader", "secret")
    source_uri.setDataSource("public", "parcels", "geom")
    source = QgsVectorLayer("Polygon?crs=EPSG:2178", "mock", "memory")
    monkeypatch.setattr(source, "providerType", lambda: "postgres")
    monkeypatch.setattr(source, "source", lambda: source_uri.uri(False))
    monkeypatch.setattr(
        algorithm, "parameterAsVectorLayer", lambda *args: source
    )
    output_uri = QgsDataSourceUri(source_uri.uri(False))
    output_uri.setConnection("HOST", port, "database", "writer", "other")
    output_uri.setDataSource(schema, "parcels", "geom")
    context = QgsProcessingContext()
    parameters = {
        "INPUT": "mock",
        "OUTPUT": "postgres:" + output_uri.uri(False),
    }

    with pytest.raises(QgsProcessingException, match="nie może nadpisać"):
        algorithm._check_output_destination(parameters, context)

    output_uri.setDataSource("public", "new_table", "geom")
    parameters["OUTPUT"] = QgsProcessingUtils.encodeProviderKeyAndUri(
        "postgres", output_uri.uri(False)
    )
    assert algorithm._check_output_destination(parameters, context) == ""


def test_buffer_write_failure_is_not_reported_as_success(monkeypatch):
    layer = _polygon_layer(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    algorithm = CalculateEgibAreaAlgorithm()
    algorithm.initAlgorithm()
    sink = Mock(spec=QgsFeatureSink)
    sink.addFeature.return_value = True
    sink.flushBuffer.return_value = False
    monkeypatch.setattr(
        algorithm, "parameterAsSink", lambda *args, **kwargs: (sink, "failed")
    )
    context = QgsProcessingContext()
    with pytest.raises(QgsProcessingException, match="zakończyć zapisu"):
        algorithm.processAlgorithm(
            {"INPUT": layer, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT},
            context,
            QgsProcessingFeedback(),
        )
    sink.addFeature.assert_called_once()
    sink.flushBuffer.assert_called_once_with()
    assert sink.addFeature.call_args.args[0]["PO_P_m2"] == 10_001.54


@pytest.mark.parametrize("table_destination", [False, True])
@pytest.mark.parametrize(
    ("field_name", "field_type", "values", "existing_name"),
    [
        ("fid", FIELD_TYPE_STRING, ["parcel-A", "parcel-B"], None),
        ("FID", FIELD_TYPE_STRING, ["parcel-A", "parcel-B"], None),
        ("fid", FIELD_TYPE_INT, [1, 1], None),
        ("fid", FIELD_TYPE_STRING, ["A", "B"], "FID_ZRODLOWY"),
    ],
)
def test_geopackage_preserves_source_fid_as_ordinary_attribute(
    tmp_path, table_destination, field_name, field_type, values, existing_name
):
    layer = _polygon_layer(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))",
        "MULTIPOLYGON (((7500200 5800200,7500250 5800200,"
        "7500250 5800250,7500200 5800250,7500200 5800200)))",
    )
    fields = [QgsField(field_name, field_type)]
    if existing_name:
        fields.append(QgsField(existing_name, FIELD_TYPE_INT))
    layer.dataProvider().addAttributes(fields)
    layer.updateFields()
    changes = {}
    for feature, value in zip(layer.getFeatures(), values):
        changes[feature.id()] = {1: value}
        if existing_name:
            changes[feature.id()][2] = 123
    layer.dataProvider().changeAttributeValues(changes)
    before = [feature.attributes() for feature in layer.getFeatures()]

    path = tmp_path / "result.gpkg"
    destination = (
        _geopackage_destination(path, "result")
        if table_destination
        else str(path)
    )
    output, _context = _run_algorithm(layer, destination=destination)
    assert output.featureCount() == 2
    renamed = "fid_zrodlowy_2" if existing_name else "fid_zrodlowy"
    results = list(output.getFeatures())
    assert [feature[renamed] for feature in results] == values
    assert len({feature["fid"] for feature in results}) == 2
    if existing_name:
        assert [feature[existing_name] for feature in results] == [123, 123]
    assert [feature.attributes() for feature in layer.getFeatures()] == before


def test_shapefile_output_warns_about_truncated_schema(tmp_path, monkeypatch):
    layer = _polygon_layer(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))"
    )
    feedback = QgsProcessingFeedback()
    warnings = []
    monkeypatch.setattr(feedback, "pushWarning", warnings.append)

    output, _context = _run_algorithm(
        layer,
        destination=str(tmp_path / "result.shp"),
        feedback=feedback,
    )

    assert output.featureCount() == 1
    assert "PO_P_m2" in output.fields().names()
    assert "PO_P_ha" in output.fields().names()
    assert "PO_poprawna_przed" not in output.fields().names()
    assert any(
        "Shapefile" in warning
        and "10 znaków" in warning
        and "254 znaków" in warning
        and "GeoPackage" in warning
        for warning in warnings
    )


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
    assert result["PO_status"] == "source_geometry"
    assert result["PO_strefa"] == 7
    assert result["PO_EPSG"] == 2178
    assert result["PO_P_m2"] > 0
    assert bytes(next(layer.getFeatures()).geometry().asWkb()) == source_wkb


@pytest.mark.parametrize("repair_mode_index", [0, 1])
def test_auxiliary_failure_keeps_main_fields_status_and_next_feature(
    monkeypatch,
    repair_mode_index,
):
    layer = _polygon_layer(
        "MULTIPOLYGON (((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950)))",
        "MULTIPOLYGON (((7500000 5800000,7500200 5800200,"
        "7500000 5800200,7500100 5800000,7500000 5800000)))",
        "MULTIPOLYGON (((7500200 5800200,7500250 5800200,"
        "7500250 5800250,7500200 5800250,7500200 5800200)))",
    )
    baseline, baseline_context = _run_algorithm(
        layer, repair_mode_index=repair_mode_index
    )
    measure = algorithm_module.measure_geodesic_area_m2
    calls = []

    def fail_first_two_measurements(*args):
        calls.append(1)
        if len(calls) < 3:
            raise GeometryTransformError("private/path/grid.gsb")
        return measure(*args)

    monkeypatch.setattr(
        algorithm_module,
        "measure_geodesic_area_m2",
        fail_first_two_measurements,
    )
    output, context = _run_algorithm(
        layer, repair_mode_index=repair_mode_index
    )
    assert baseline_context is not None and context is not None
    assert len(calls) == 3
    for index, (expected, actual) in enumerate(
        zip(baseline.getFeatures(), output.getFeatures())
    ):
        assert bytes(actual.geometry().asWkb()) == bytes(
            expected.geometry().asWkb()
        )
        for field in output.fields().names():
            if field not in ("PO_QGIS_m2", "PO_uwagi"):
                assert actual[field] == expected[field], field
        if index < 2:
            assert actual["PO_QGIS_m2"] == NULL
            assert "geodesic_measurement_failed" in actual["PO_uwagi"]
            assert "private/path" not in actual["PO_uwagi"]
            if expected["PO_uwagi"] != NULL:
                assert expected["PO_uwagi"] in actual["PO_uwagi"]
        else:
            assert actual.attributes() == expected.attributes()


def test_processing_toolbox_has_no_redundant_group():
    registry = QgsProcessingRegistry()
    assert registry.addProvider(EgibAreaProvider())
    model = QgsProcessingToolboxModel(registry=registry)
    # QGIS 4 also has a built-in "Input parameters" root in this model.
    provider = model.indexForProvider("egib_area")
    assert provider.isValid()
    assert provider.data() == "Poprawka odwzorowawcza PL-2000"
    assert model.rowCount(provider) == 1
    algorithm = model.index(0, 0, provider)
    assert algorithm.data() == provider.data()
    assert model.algorithmForIndex(algorithm).id() == (
        "egib_area:calculate_egib_area"
    )
    assert model.rowCount(algorithm) == 0
