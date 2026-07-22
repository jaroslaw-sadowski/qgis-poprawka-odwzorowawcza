"""GEOS validation and non-mutating Structure/Linework geometry repair."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext,
    QgsGeometry,
    QgsNotSupportedException,
)

if "." in __package__:
    from ..core import Pl2000BoundaryPoint, validate_easting_zone
else:
    from core import Pl2000BoundaryPoint, validate_easting_zone

from .geometry import (
    GeometryInputError,
    GeometrySnapshot,
    extract_boundary_points,
    geometry_snapshot,
    transform_geometry_to_pl2000,
)


class RepairMode(str, Enum):
    """Policy controlling whether a repaired geometry may yield legal area."""

    STRICT = "strict"
    AUTO_REPAIR = "auto_repair"


class RepairMethod(str, Enum):
    """Method used to produce the accepted geometry."""

    NONE = "none"
    STRUCTURE = "structure"
    LINEWORK = "linework"
    FAILED = "failed"


@dataclass(frozen=True)
class GeometryRepairReport:
    """Required before/after geometry repair metrics."""

    validity_before: bool
    validity_after: bool
    repair_method: RepairMethod
    original_part_count: int
    repaired_part_count: int
    original_ring_count: int
    repaired_ring_count: int
    original_vertex_count: int
    repaired_vertex_count: int
    original_area_m2: float
    repaired_area_m2: float
    area_difference_m2: float
    vertices_added: int
    vertices_removed: int
    warnings: Tuple[str, ...]


@dataclass(frozen=True)
class GeometryPreparationResult:
    """A PL-2000 geometry, original points and its auditable repair report."""

    geometry_for_area: QgsGeometry
    original_boundary_points: Tuple[Pl2000BoundaryPoint, ...]
    target_crs: QgsCoordinateReferenceSystem
    target_epsg: int
    zone: int
    statutory_result_allowed: bool
    report: GeometryRepairReport


class GeometryRepairError(RuntimeError):
    """Raised when neither makeValid strategy returns an acceptable polygon."""

    def __init__(self, message: str, report: GeometryRepairReport) -> None:
        super().__init__(message)
        self.report = report


@dataclass(frozen=True)
class _RepairResult:
    geometry: QgsGeometry
    statutory_result_allowed: bool
    report: GeometryRepairReport


def prepare_geometry(
    geometry: QgsGeometry,
    source_crs: QgsCoordinateReferenceSystem,
    transform_context: QgsCoordinateTransformContext,
    *,
    selected_zone: Optional[int] = None,
    repair_mode: RepairMode = RepairMode.STRICT,
) -> GeometryPreparationResult:
    """Transform, validate and optionally accept repair of a geometry copy."""

    transformed = transform_geometry_to_pl2000(
        geometry,
        source_crs,
        transform_context,
        selected_zone=selected_zone,
    )
    original_boundary_points = extract_boundary_points(transformed.geometry)
    for point in original_boundary_points:
        validate_easting_zone(point.easting_y, transformed.zone)

    repair_result = _repair_geometry(transformed.geometry, repair_mode)
    return GeometryPreparationResult(
        geometry_for_area=repair_result.geometry,
        original_boundary_points=original_boundary_points,
        target_crs=transformed.target_crs,
        target_epsg=transformed.target_epsg,
        zone=transformed.zone,
        statutory_result_allowed=repair_result.statutory_result_allowed,
        report=repair_result.report,
    )


def _repair_geometry(geometry: QgsGeometry, repair_mode: RepairMode) -> _RepairResult:
    if not isinstance(repair_mode, RepairMode):
        raise TypeError("repair_mode must be a RepairMode value")

    original_geometry = QgsGeometry(geometry)
    original_snapshot = geometry_snapshot(original_geometry)
    input_warnings = _geometry_input_warnings(original_snapshot)
    validity_before = original_geometry.isGeosValid()
    if validity_before:
        report = _build_report(
            validity_before=True,
            validity_after=True,
            repair_method=RepairMethod.NONE,
            original=original_snapshot,
            repaired=original_snapshot,
            warnings=input_warnings,
        )
        return _RepairResult(
            geometry=QgsGeometry(original_geometry),
            statutory_result_allowed=True,
            report=report,
        )

    warnings = list(input_warnings) + ["geometry_invalid_before_repair"]
    last_candidate_snapshot: Optional[GeometrySnapshot] = None
    attempts = (
        (RepairMethod.STRUCTURE, Qgis.MakeValidMethod.Structure),
        (RepairMethod.LINEWORK, Qgis.MakeValidMethod.Linework),
    )

    for repair_method, qgis_method in attempts:
        try:
            candidate = _make_valid(original_geometry, qgis_method)
        except QgsNotSupportedException as error:
            warnings.append(f"{repair_method.value}_not_supported: {error}")
            continue

        rejection_reason = _candidate_rejection_reason(candidate)
        if rejection_reason is not None:
            warnings.append(f"{repair_method.value}_failed: {rejection_reason}")
            last_candidate_snapshot = _snapshot_if_polygon(candidate)
            continue

        repaired_snapshot = geometry_snapshot(candidate)
        warnings.extend(_geometry_change_warnings(original_snapshot, repaired_snapshot))
        if repair_mode is RepairMode.STRICT:
            warnings.append("strict_mode_blocks_statutory_result")

        report = _build_report(
            validity_before=False,
            validity_after=True,
            repair_method=repair_method,
            original=original_snapshot,
            repaired=repaired_snapshot,
            warnings=tuple(warnings),
        )
        return _RepairResult(
            geometry=QgsGeometry(candidate),
            statutory_result_allowed=repair_mode is RepairMode.AUTO_REPAIR,
            report=report,
        )

    failed_snapshot = last_candidate_snapshot or _empty_snapshot()
    report = _build_report(
        validity_before=False,
        validity_after=False,
        repair_method=RepairMethod.FAILED,
        original=original_snapshot,
        repaired=failed_snapshot,
        warnings=tuple(warnings),
    )
    raise GeometryRepairError(
        "Structure and Linework failed to produce a valid polygon",
        report,
    )


def _make_valid(geometry: QgsGeometry, method: Qgis.MakeValidMethod) -> QgsGeometry:
    """Call the QGIS 3.44-compatible two-argument makeValid overload."""

    return geometry.makeValid(method, False)


def _candidate_rejection_reason(candidate: QgsGeometry) -> Optional[str]:
    if candidate is None or candidate.isNull():
        return "makeValid returned a null geometry"
    if candidate.isEmpty():
        return "makeValid returned an empty geometry"
    if candidate.type() != Qgis.GeometryType.Polygon:
        return "makeValid returned a non-polygonal geometry"
    if not candidate.isGeosValid():
        error_detail = candidate.lastError()
        return error_detail or "makeValid result is still GEOS-invalid"
    return None


def _snapshot_if_polygon(candidate: QgsGeometry) -> Optional[GeometrySnapshot]:
    if candidate is None or candidate.isNull() or candidate.isEmpty():
        return None
    if candidate.type() != Qgis.GeometryType.Polygon:
        return None
    try:
        return geometry_snapshot(candidate)
    except GeometryInputError:
        return None


def _geometry_change_warnings(
    original: GeometrySnapshot,
    repaired: GeometrySnapshot,
) -> Tuple[str, ...]:
    warnings = ["geometry_repaired"]
    if original.vertex_coordinates != repaired.vertex_coordinates:
        warnings.append("repair_changed_boundary_vertices")
    if original.part_count != repaired.part_count:
        warnings.append("repair_changed_part_count")
    if original.ring_count != repaired.ring_count:
        warnings.append("repair_changed_ring_count")
    if original.area_m2 != repaired.area_m2:
        warnings.append("repair_changed_area")
    return tuple(warnings)


def _geometry_input_warnings(snapshot: GeometrySnapshot) -> Tuple[str, ...]:
    warnings = []
    if snapshot.part_count > 1:
        warnings.append("multipart_geometry")
    if snapshot.ring_count > snapshot.part_count:
        warnings.append("interior_rings_included")
    return tuple(warnings)


def _build_report(
    *,
    validity_before: bool,
    validity_after: bool,
    repair_method: RepairMethod,
    original: GeometrySnapshot,
    repaired: GeometrySnapshot,
    warnings: Tuple[str, ...],
) -> GeometryRepairReport:
    return GeometryRepairReport(
        validity_before=validity_before,
        validity_after=validity_after,
        repair_method=repair_method,
        original_part_count=original.part_count,
        repaired_part_count=repaired.part_count,
        original_ring_count=original.ring_count,
        repaired_ring_count=repaired.ring_count,
        original_vertex_count=original.vertex_count,
        repaired_vertex_count=repaired.vertex_count,
        original_area_m2=original.area_m2,
        repaired_area_m2=repaired.area_m2,
        area_difference_m2=repaired.area_m2 - original.area_m2,
        vertices_added=len(repaired.vertex_coordinates - original.vertex_coordinates),
        vertices_removed=len(original.vertex_coordinates - repaired.vertex_coordinates),
        warnings=warnings,
    )


def _empty_snapshot() -> GeometrySnapshot:
    return GeometrySnapshot(
        part_count=0,
        ring_count=0,
        vertex_count=0,
        area_m2=0.0,
        vertex_coordinates=frozenset(),
    )
