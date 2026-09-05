"""End-to-end numeric checks with fixed, independently derived references."""

import json
from decimal import Decimal
from math import fsum
from pathlib import Path

import pytest
from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsCoordinateTransformContext,
    QgsFeature,
    QgsGeometry,
    QgsNotSupportedException,
    QgsPointXY,
    QgsProcessing,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingUtils,
    QgsProject,
    QgsVectorLayer,
)

import adapters.repair as repair_module
from adapters import RepairMethod, RepairMode, prepare_geometry
from core import calculate_pgk
from gui.dialog import calculate_selected_parcel
from processing_provider import CalculateEgibAreaAlgorithm

REFERENCES = {
    case["name"]: case
    for case in json.loads(
        (
            Path(__file__).parents[1] / "reference" / "pl2000_reference.json"
        ).read_text(encoding="utf-8")
    )
}


def _geometry(case, variant="original"):
    parts = []
    for part in case["parts"]:
        rings = []
        for ring in part:
            points = [QgsPointXY(float(e), float(n)) for e, n in ring]
            if variant == "reversed":
                points.reverse()
            elif variant == "rotated":
                points = points[1:] + points[:1]
            elif variant == "repeated":
                points.insert(1, QgsPointXY(points[0]))
            rings.append(points + [QgsPointXY(points[0])])
        parts.append(rings)
    return QgsGeometry.fromMultiPolygonXY(parts)


def _run_both(
    geometry,
    source_crs,
    mode,
    zone=None,
    destination=QgsProcessing.TEMPORARY_OUTPUT,
):
    """Run the GUI calculation and real Processing entry point on a layer."""
    layer = QgsVectorLayer("MultiPolygon", "reference", "memory")
    layer.setCrs(source_crs)
    feature = QgsFeature(layer.fields())
    feature.setGeometry(geometry)
    assert layer.dataProvider().addFeature(feature)
    feature = next(layer.getFeatures())
    source_wkb = bytes(feature.geometry().asWkb())
    context = QgsProcessingContext()
    context.setInvalidGeometryCheck(Qgis.InvalidGeometryCheck.AbortOnInvalid)
    context.setTransformContext(QgsCoordinateTransformContext())
    gui = calculate_selected_parcel(
        feature,
        source_crs,
        context.transformContext(),
        selected_zone=zone,
        repair_mode=mode,
    )
    algorithm = CalculateEgibAreaAlgorithm()
    results, ok = algorithm.run(
        {
            algorithm.INPUT: layer,
            algorithm.ZONE: 0 if zone is None else zone - 4,
            algorithm.REPAIR_MODE: 0
            if mode is RepairMode.SOURCE_GEOMETRY
            else 1,
            algorithm.OUTPUT: destination,
        },
        context,
        QgsProcessingFeedback(),
        catchExceptions=False,
    )
    assert ok
    output = QgsProcessingUtils.mapLayerFromString(
        results[algorithm.OUTPUT], context
    )
    assert output.featureCount() == 1
    assert output.crs() == gui.preparation.target_crs
    assert bytes(next(layer.getFeatures()).geometry().asWkb()) == source_wkb
    assert bytes(geometry.asWkb()) == source_wkb
    assert layer.fields().isEmpty()
    return gui, next(output.getFeatures())


def _assert_reference(gui, batch, case, area_tolerance=1e-6):
    expected = case["expected"]
    result = gui.calculation
    assert result is not None
    for field in ("po_m2", "correction_m2", "legal_area_m2_raw"):
        assert getattr(result, field) == pytest.approx(
            float(expected[field]), rel=0, abs=area_tolerance
        ), field
    for field in ("pgk_x_northing", "pgk_y_easting"):
        assert getattr(result, field) == pytest.approx(
            float(expected[field]), rel=0, abs=1e-6
        ), field
    assert result.legal_area_ha_rounded == Decimal(case["rounded_ha"])
    assert batch["egib_area_ha"] == float(Decimal(case["rounded_ha"]))
    for output_field, expected_field in (
        ("egib_po_m2", "po_m2"),
        ("egib_corr_m2", "correction_m2"),
        ("egib_area_m2", "legal_area_m2_raw"),
    ):
        assert batch[output_field] == round(float(expected[expected_field]), 2)
    for output_field, result_field in (
        ("egib_pgk_x", "pgk_x_northing"),
        ("egib_pgk_y", "pgk_y_easting"),
        ("egib_sigma", "sigma_cm_per_km"),
        ("egib_scale", "scale_m"),
    ):
        assert batch[output_field] == getattr(result, result_field)
    assert batch["egib_qgis_m2"] == round(gui.qgis_geodesic_area_m2, 2)
    assert batch["egib_valid_before"] == gui.preparation.report.validity_before
    assert batch["egib_valid_after"] == gui.preparation.report.validity_after


@pytest.mark.parametrize("mode", list(RepairMode))
@pytest.mark.parametrize(
    "variant", ["original", "reversed", "rotated", "repeated"]
)
@pytest.mark.parametrize(
    "name", [n for n in REFERENCES if n != "source_bow_tie"]
)
def test_gui_and_processing_match_polygon_references(name, variant, mode):
    case = REFERENCES[name]
    geometry = _geometry(case, variant)
    before = bytes(geometry.asWkb())
    gui, batch = _run_both(
        geometry, QgsCoordinateReferenceSystem.fromEpsgId(case["epsg"]), mode
    )
    _assert_reference(gui, batch, case)
    assert gui.preparation.report.validity_before is True
    assert gui.preparation.report.repair_method is RepairMethod.NONE
    assert bytes(gui.preparation.geometry_for_area.asWkb()) == before
    assert bytes(batch.geometry().asWkb()) == before


@pytest.mark.parametrize("mode", list(RepairMode))
@pytest.mark.parametrize("source_epsg", [2180, 4326])
@pytest.mark.parametrize("zone", [5, 6, 7, 8])
def test_reprojection_before_area_and_mean_in_all_zones(
    mode, source_epsg, zone
):
    # Move the asymmetric reference by the zone prefix, then express it
    # in another CRS. The expected PL-2000 result remains fixed.
    case = json.loads(json.dumps(REFERENCES["east_asymmetric"]))
    shift = (zone - 7) * 1_000_000
    for part in case["parts"]:
        for ring in part:
            for point in ring:
                point[0] = str(Decimal(point[0]) + shift)
    case["expected"]["pgk_y_easting"] = str(
        Decimal(case["expected"]["pgk_y_easting"]) + shift
    )
    target_crs = QgsCoordinateReferenceSystem.fromEpsgId(2171 + zone)
    source_crs = QgsCoordinateReferenceSystem.fromEpsgId(source_epsg)
    source = _geometry(case)
    source.transform(
        QgsCoordinateTransform(
            target_crs, source_crs, QgsCoordinateTransformContext()
        )
    )
    gui, batch = _run_both(source, source_crs, mode, zone)
    # Includes floating-point errors in the two CRS transformations;
    # 0.0001 m² is 10 000 times smaller than the hectare output quantum.
    _assert_reference(gui, batch, case, area_tolerance=1e-4)


def test_mean_of_transformed_vertices_is_not_transformed_mean_or_centroid():
    source = QgsGeometry.fromWkt(
        "MULTIPOLYGON (((21 52,21.2 52,21.3 52.1,21 52.2,21 52)))"
    )
    crs = QgsCoordinateReferenceSystem("EPSG:4326")
    transform = QgsCoordinateTransform(
        crs,
        QgsCoordinateReferenceSystem("EPSG:2178"),
        QgsCoordinateTransformContext(),
    )
    points = source.asMultiPolygon()[0][0][:-1]
    transformed = [transform.transform(p) for p in points]
    expected_e = fsum(p.x() for p in transformed) / len(points)
    expected_n = fsum(p.y() for p in transformed) / len(points)
    wrong_mean = transform.transform(
        QgsPointXY(
            fsum(p.x() for p in points) / len(points),
            fsum(p.y() for p in points) / len(points),
        )
    )
    assert abs(wrong_mean.x() - expected_e) > 1
    assert abs(wrong_mean.y() - expected_n) > 1
    gui, batch = _run_both(source, crs, RepairMode.SOURCE_GEOMETRY, 7)
    assert gui.calculation.pgk_x_northing == pytest.approx(
        expected_n, rel=0, abs=1e-8
    )
    assert batch["egib_pgk_y"] == pytest.approx(expected_e, rel=0, abs=1e-8)
    centroid = gui.preparation.geometry_for_area.centroid().asPoint()
    assert abs(centroid.x() - expected_e) > 1


@pytest.mark.parametrize("force_linework", [False, True])
def test_repair_changes_area_and_pgk_in_both_entry_points(
    monkeypatch, force_linework
):
    if force_linework:
        real_make_valid = repair_module._make_valid

        def structure_unavailable(geometry, method):
            if method == Qgis.MakeValidMethod.Structure:
                raise QgsNotSupportedException("Structure unavailable")
            return real_make_valid(geometry, method)

        monkeypatch.setattr(
            repair_module, "_make_valid", structure_unavailable
        )
    source = _geometry(REFERENCES["source_bow_tie"])
    gui, batch = _run_both(
        source,
        QgsCoordinateReferenceSystem("EPSG:2178"),
        RepairMode.AUTO_REPAIR,
    )
    _assert_reference(gui, batch, REFERENCES["repaired_bow_tie"])
    assert batch["egib_status"] == "repaired"
    assert batch["egib_vertices_added"] == 1
    assert batch["egib_repair_method"] == (
        "linework" if force_linework else "structure"
    )
    assert batch.geometry().isGeosValid()


@pytest.mark.parametrize("name", ["source_bow_tie", "east_asymmetric"])
def test_source_mode_never_calls_make_valid_and_keeps_original_pgk(
    monkeypatch, name
):
    def unexpected_repair(*args):
        pytest.fail("source mode must never call makeValid")

    monkeypatch.setattr(repair_module, "_make_valid", unexpected_repair)
    case = REFERENCES[name]
    source = _geometry(case)
    before = bytes(source.asWkb())
    gui, batch = _run_both(
        source,
        QgsCoordinateReferenceSystem("EPSG:2178"),
        RepairMode.SOURCE_GEOMETRY,
    )
    _assert_reference(gui, batch, case)
    valid = name != "source_bow_tie"
    assert gui.preparation.report.validity_before is valid
    assert gui.preparation.report.validity_after is valid
    assert batch["egib_status"] == (
        "source_geometry" if valid else "invalid_source_geometry"
    )
    assert bytes(batch.geometry().asWkb()) == before


def test_structure_removes_collapsed_spike_vertex_from_pgk():
    source = QgsGeometry.fromWkt(
        "POLYGON ((7500000 5800000,7500100 5800000,7500150 5800000,"
        "7500100 5800000,7500100 5800100,7500000 5800100,"
        "7500000 5800000))"
    )
    before = bytes(source.asWkb())
    prepared = prepare_geometry(
        source,
        QgsCoordinateReferenceSystem("EPSG:2178"),
        QgsCoordinateTransformContext(),
        repair_mode=RepairMode.AUTO_REPAIR,
    )
    pgk = calculate_pgk(prepared.boundary_points_for_calculation)
    assert pgk.easting_y == 7_500_050
    assert pgk.northing_x == 5_800_050
    assert prepared.geometry_for_area.area() == 10_000
    assert prepared.report.vertices_removed == 1
    assert bytes(source.asWkb()) == before


@pytest.mark.parametrize("project_epsg", [4326, 3857])
def test_project_crs_and_ellipsoid_do_not_change_statutory_result(
    project_epsg,
):
    project = QgsProject.instance()
    old_crs, old_ellipsoid = project.crs(), project.ellipsoid()
    try:
        project.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(project_epsg))
        project.setEllipsoid("WGS84")
        case = REFERENCES["east_asymmetric"]
        gui, batch = _run_both(
            _geometry(case),
            QgsCoordinateReferenceSystem("EPSG:2178"),
            RepairMode.SOURCE_GEOMETRY,
        )
        _assert_reference(gui, batch, case)
    finally:
        project.setCrs(old_crs)
        project.setEllipsoid(old_ellipsoid)


@pytest.mark.parametrize("mode", list(RepairMode))
def test_geopackage_preserves_results_after_reopening(tmp_path, mode):
    case = REFERENCES["source_bow_tie"]
    expected = REFERENCES[
        "source_bow_tie"
        if mode is RepairMode.SOURCE_GEOMETRY
        else "repaired_bow_tie"
    ]
    destination = str(tmp_path / "results.gpkg")
    gui, _batch = _run_both(
        _geometry(case),
        QgsCoordinateReferenceSystem("EPSG:2178"),
        mode,
        destination=destination,
    )
    reopened = QgsVectorLayer(destination, "results", "ogr")
    assert reopened.isValid()
    assert reopened.featureCount() == 1
    assert reopened.crs().authid() == "EPSG:2178"
    _assert_reference(gui, next(reopened.getFeatures()), expected)


@pytest.mark.parametrize("mode", list(RepairMode))
def test_height_and_measure_coordinates_do_not_change_planar_result(mode):
    case = REFERENCES["east_asymmetric"]
    source = _geometry(case)
    source.get().addZValue(150)
    source.get().addMValue(42)
    gui, batch = _run_both(
        source, QgsCoordinateReferenceSystem("EPSG:2178"), mode
    )
    _assert_reference(gui, batch, case)
