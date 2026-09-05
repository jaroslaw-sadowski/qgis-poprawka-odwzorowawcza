import pytest
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext,
    QgsGeometry,
)

import adapters.geometry as geometry_module
from adapters import (
    CurvedGeometryError,
    GeometryInputError,
    extract_boundary_points,
    geometry_snapshot,
    measure_geodesic_area_m2,
    transform_geometry_to_pl2000,
    validate_geometry_budget,
)


def test_transform_to_selected_pl2000_zone_does_not_modify_source() -> None:
    source = QgsGeometry.fromWkt(
        "POLYGON ((21 52, 21.001 52, 21.001 52.001, 21 52.001, 21 52))"
    )
    source_wkb = bytes(source.asWkb())

    result = transform_geometry_to_pl2000(
        source,
        QgsCoordinateReferenceSystem("EPSG:4326"),
        QgsCoordinateTransformContext(),
        selected_zone=7,
    )

    assert bytes(source.asWkb()) == source_wkb
    assert result.geometry is not source
    assert result.target_epsg == 2178
    assert result.zone == 7
    assert all(
        int(point.easting_y // 1_000_000) == 7
        for point in extract_boundary_points(result.geometry)
    )


def test_geometry_already_in_pl2000_is_still_copied() -> None:
    source = QgsGeometry.fromWkt(
        "POLYGON ((7500000 5800000, 7500100 5800000, "
        "7500100 5800100, 7500000 5800000))"
    )

    result = transform_geometry_to_pl2000(
        source,
        QgsCoordinateReferenceSystem("EPSG:2178"),
        QgsCoordinateTransformContext(),
    )

    assert result.geometry is not source
    assert bytes(result.geometry.asWkb()) == bytes(source.asWkb())


def test_geodesic_area_uses_qgis_engine_with_grs80() -> None:
    geometry = QgsGeometry.fromWkt(
        "POLYGON ((7499950 5799950,7500050 5799950,"
        "7500050 5800050,7499950 5800050,7499950 5799950))"
    )

    result = measure_geodesic_area_m2(
        geometry,
        QgsCoordinateReferenceSystem("EPSG:2178"),
        QgsCoordinateTransformContext(),
    )

    assert geometry.area() == 10_000.0
    assert result == pytest.approx(10_001.54017795077)


@pytest.mark.parametrize(
    "geometry",
    [
        QgsGeometry(),
        QgsGeometry.fromWkt("POLYGON EMPTY"),
        QgsGeometry.fromWkt("LINESTRING (0 0, 1 1)"),
    ],
)
def test_null_empty_and_non_polygonal_geometries_are_rejected(
    geometry,
) -> None:
    with pytest.raises(GeometryInputError):
        transform_geometry_to_pl2000(
            geometry,
            QgsCoordinateReferenceSystem("EPSG:2178"),
            QgsCoordinateTransformContext(),
        )


def test_snapshot_counts_geometry_structure() -> None:
    geometry = QgsGeometry.fromWkt(
        "MULTIPOLYGON (((0 0,10 0,10 10,0 0)),"
        "((20 20,30 20,30 30,20 20),(22 22,23 22,23 23,22 22)))"
    )

    snapshot = geometry_snapshot(geometry)

    assert snapshot.part_count == 2
    assert snapshot.ring_count == 3
    assert snapshot.vertex_count == 9
    assert len(snapshot.vertex_coordinates) == 9


def test_curved_rings_are_not_silently_segmentized() -> None:
    geometry = QgsGeometry.fromWkt(
        "CURVEPOLYGON (CIRCULARSTRING (0 0, 5 5, 10 0, 5 -5, 0 0))"
    )

    with pytest.raises(CurvedGeometryError):
        extract_boundary_points(geometry)


def test_boundary_point_extraction_preserves_legal_axis_mapping() -> None:
    geometry = QgsGeometry.fromWkt(
        "POLYGON ((7500100 5800200,7500300 5800200,7500300 5800600,"
        "7500100 5800600,7500100 5800200))"
    )

    points = extract_boundary_points(geometry)

    assert {point.northing_x for point in points} == {5_800_200.0, 5_800_600.0}
    assert {point.easting_y for point in points} == {7_500_100.0, 7_500_300.0}


def test_coordinate_budget_is_checked_before_transform(monkeypatch) -> None:
    geometry = QgsGeometry.fromWkt(
        "POLYGON ((21 52,21.001 52,21.001 52.001,21 52.001,21 52))"
    )
    source_wkb = bytes(geometry.asWkb())
    monkeypatch.setattr(
        geometry_module,
        "MAX_BOUNDARY_COORDINATES",
        4,
    )

    def unexpected_transform(*args, **kwargs):
        del args, kwargs
        pytest.fail("coordinate transform must not be created over budget")

    monkeypatch.setattr(
        geometry_module,
        "QgsCoordinateTransform",
        unexpected_transform,
    )

    with pytest.raises(GeometryInputError, match="współrzędnych: 5 > 4"):
        transform_geometry_to_pl2000(
            geometry,
            QgsCoordinateReferenceSystem("EPSG:4326"),
            QgsCoordinateTransformContext(),
            selected_zone=7,
        )

    assert bytes(geometry.asWkb()) == source_wkb


def test_part_budget_is_enforced(monkeypatch) -> None:
    geometry = QgsGeometry.fromWkt(
        "MULTIPOLYGON (((0 0,10 0,10 10,0 0)),((20 20,30 20,30 30,20 20)))"
    )
    monkeypatch.setattr(geometry_module, "MAX_POLYGON_PARTS", 1)

    with pytest.raises(GeometryInputError, match="liczby części: 2 > 1"):
        validate_geometry_budget(geometry)


def test_ring_budget_is_enforced(monkeypatch) -> None:
    geometry = QgsGeometry.fromWkt(
        "POLYGON ((0 0,10 0,10 10,0 0),(2 2,3 2,3 3,2 2))"
    )
    monkeypatch.setattr(geometry_module, "MAX_POLYGON_RINGS", 1)

    with pytest.raises(GeometryInputError, match="pierścieni: 2 > 1"):
        validate_geometry_budget(geometry)


def test_geometry_exactly_at_complexity_budget_is_accepted(
    monkeypatch,
) -> None:
    geometry = QgsGeometry.fromWkt("POLYGON ((0 0,10 0,10 10,0 10,0 0))")
    monkeypatch.setattr(geometry_module, "MAX_POLYGON_PARTS", 1)
    monkeypatch.setattr(geometry_module, "MAX_POLYGON_RINGS", 1)
    monkeypatch.setattr(geometry_module, "MAX_BOUNDARY_COORDINATES", 5)

    validate_geometry_budget(geometry)


@pytest.mark.parametrize("measurement", [float("nan"), float("inf"), -1.0])
def test_unusable_ellipsoidal_measurement_is_an_expected_error(
    monkeypatch,
    measurement,
):
    class InvalidDistanceArea(geometry_module.QgsDistanceArea):
        def measureArea(self, geometry):  # noqa: N802
            return measurement

    monkeypatch.setattr(
        geometry_module, "QgsDistanceArea", InvalidDistanceArea
    )
    with pytest.raises(geometry_module.GeometryTransformError):
        measure_geodesic_area_m2(
            QgsGeometry.fromWkt(
                "POLYGON ((7500000 5800000,7500100 5800000,"
                "7500100 5800100,7500000 5800000))"
            ),
            QgsCoordinateReferenceSystem("EPSG:2178"),
            QgsCoordinateTransformContext(),
        )
