import pytest
from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext,
    QgsGeometry,
    QgsNotSupportedException,
)

import adapters.repair as repair_module
from adapters import (
    GeometryRepairError,
    RepairMethod,
    RepairMode,
    prepare_geometry,
)
from core import ZoneMismatchError


def _bow_tie() -> QgsGeometry:
    return QgsGeometry.fromWkt(
        "POLYGON ((7500000 5800000, 7500100 5800100, "
        "7500000 5800100, 7500100 5800000, 7500000 5800000))"
    )


def _asymmetric_bow_tie() -> QgsGeometry:
    return QgsGeometry.fromWkt(
        "POLYGON ((7500000 5800000, 7500200 5800200, "
        "7500000 5800200, 7500100 5800000, 7500000 5800000))"
    )


def test_source_geometry_mode_does_not_validate_or_repair() -> None:
    source = QgsGeometry.fromWkt(
        "POLYGON ((7500000 5800000, 7500100 5800000, "
        "7500100 5800100, 7500000 5800000))"
    )
    source_wkb = bytes(source.asWkb())

    result = prepare_geometry(
        source,
        QgsCoordinateReferenceSystem("EPSG:2178"),
        QgsCoordinateTransformContext(),
    )

    assert bytes(source.asWkb()) == source_wkb
    assert bytes(result.geometry_for_area.asWkb()) == source_wkb
    assert result.statutory_result_allowed is True
    assert result.report.validity_before is None
    assert result.report.validity_after is None
    assert result.report.repair_method is RepairMethod.NONE
    assert result.report.area_difference_m2 == 0.0
    assert result.report.vertices_added == 0
    assert result.report.vertices_removed == 0
    assert result.report.warnings == ()


def test_structure_repairs_copy_and_populates_full_report() -> None:
    source = _bow_tie()
    source_wkb = bytes(source.asWkb())

    result = prepare_geometry(
        source,
        QgsCoordinateReferenceSystem("EPSG:2178"),
        QgsCoordinateTransformContext(),
        repair_mode=RepairMode.AUTO_REPAIR,
    )

    report = result.report
    assert bytes(source.asWkb()) == source_wkb
    assert source.isGeosValid() is False
    assert result.geometry_for_area.isGeosValid() is True
    assert result.statutory_result_allowed is True
    assert report.validity_before is False
    assert report.validity_after is True
    assert report.repair_method is RepairMethod.STRUCTURE
    assert report.original_part_count == 1
    assert report.repaired_part_count == 2
    assert report.original_ring_count == 1
    assert report.repaired_ring_count == 2
    assert report.original_vertex_count == 4
    assert report.repaired_vertex_count == 6
    assert report.original_area_m2 == pytest.approx(0.0)
    assert report.repaired_area_m2 == pytest.approx(5_000.0)
    assert report.area_difference_m2 == pytest.approx(5_000.0)
    assert report.vertices_added == 1
    assert report.vertices_removed == 0
    assert "repair_changed_boundary_vertices" in report.warnings


def test_source_geometry_mode_keeps_invalid_geometry_unchecked() -> None:
    source = _asymmetric_bow_tie()
    source_wkb = bytes(source.asWkb())

    result = prepare_geometry(
        source,
        QgsCoordinateReferenceSystem("EPSG:2178"),
        QgsCoordinateTransformContext(),
        repair_mode=RepairMode.SOURCE_GEOMETRY,
    )

    assert bytes(source.asWkb()) == source_wkb
    assert bytes(result.geometry_for_area.asWkb()) == source_wkb
    assert result.statutory_result_allowed is True
    assert result.report.validity_before is None
    assert result.report.validity_after is None
    assert result.report.repair_method is RepairMethod.NONE
    assert result.report.warnings == ()


def test_linework_is_used_when_structure_is_not_supported(monkeypatch) -> None:
    real_make_valid = repair_module._make_valid

    def structure_not_supported(geometry, method):
        if method is Qgis.MakeValidMethod.Structure:
            raise QgsNotSupportedException("Structure unavailable")
        return real_make_valid(geometry, method)

    monkeypatch.setattr(repair_module, "_make_valid", structure_not_supported)

    result = prepare_geometry(
        _bow_tie(),
        QgsCoordinateReferenceSystem("EPSG:2178"),
        QgsCoordinateTransformContext(),
        repair_mode=RepairMode.AUTO_REPAIR,
    )

    assert result.report.repair_method is RepairMethod.LINEWORK
    assert any(
        warning.startswith("structure_not_supported")
        for warning in result.report.warnings
    )


def test_failure_of_both_methods_raises_error_with_report(monkeypatch) -> None:
    monkeypatch.setattr(
        repair_module,
        "_make_valid",
        lambda geometry, method: QgsGeometry(),
    )

    with pytest.raises(GeometryRepairError) as raised:
        prepare_geometry(
            _bow_tie(),
            QgsCoordinateReferenceSystem("EPSG:2178"),
            QgsCoordinateTransformContext(),
            repair_mode=RepairMode.AUTO_REPAIR,
        )

    report = raised.value.report
    assert report.validity_before is False
    assert report.validity_after is False
    assert report.repair_method is RepairMethod.FAILED
    assert report.repaired_part_count == 0
    assert report.repaired_ring_count == 0
    assert report.repaired_vertex_count == 0
    assert len(report.warnings) == 3


def test_zone_prefix_is_validated_after_transform() -> None:
    wrong_prefix = QgsGeometry.fromWkt(
        "POLYGON ((6500000 5800000, 6500100 5800000, "
        "6500100 5800100, 6500000 5800000))"
    )

    with pytest.raises(ZoneMismatchError):
        prepare_geometry(
            wrong_prefix,
            QgsCoordinateReferenceSystem("EPSG:2178"),
            QgsCoordinateTransformContext(),
        )


def test_multipart_and_interior_rings_are_reported() -> None:
    source = QgsGeometry.fromWkt(
        "MULTIPOLYGON (((7500000 5800000,7500200 5800000,"
        "7500200 5800200,7500000 5800200,7500000 5800000),"
        "(7500050 5800050,7500050 5800100,7500100 5800100,"
        "7500100 5800050,7500050 5800050)),"
        "((7500300 5800300,7500400 5800300,7500400 5800400,"
        "7500300 5800400,7500300 5800300)))"
    )

    result = prepare_geometry(
        source,
        QgsCoordinateReferenceSystem("EPSG:2178"),
        QgsCoordinateTransformContext(),
    )

    assert result.report.validity_before is None
    assert "multipart_geometry" in result.report.warnings
    assert "interior_rings_included" in result.report.warnings
