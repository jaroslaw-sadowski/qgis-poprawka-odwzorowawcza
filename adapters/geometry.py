"""Non-mutating PyQGIS geometry validation, traversal and transformation."""

from dataclasses import dataclass
from typing import FrozenSet, List, Optional, Tuple

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsCoordinateTransformContext,
    QgsCsException,
    QgsCurve,
    QgsCurvePolygon,
    QgsDistanceArea,
    QgsGeometry,
)

if "." in __package__:
    from ..core import Pl2000BoundaryPoint, pl2000_point_from_qgis_coordinates
else:
    from core import Pl2000BoundaryPoint, pl2000_point_from_qgis_coordinates

from .zones import resolve_target_pl2000_crs

MAX_POLYGON_PARTS = 10_000
MAX_POLYGON_RINGS = 50_000
MAX_BOUNDARY_COORDINATES = 500_000


class GeometryInputError(ValueError):
    """Raised when an input geometry cannot represent a cadastral parcel."""


class CurvedGeometryError(GeometryInputError):
    """Raised to prevent silent curve segmentization in boundary points."""


class GeometryTransformError(RuntimeError):
    """Raised when a geometry cannot be transformed to the selected CRS."""


@dataclass(frozen=True)
class GeometrySnapshot:
    """Structural and numeric metrics for a polygon geometry."""

    part_count: int
    ring_count: int
    vertex_count: int
    area_m2: float
    vertex_coordinates: FrozenSet[Tuple[float, float]]


@dataclass(frozen=True)
class TransformedGeometry:
    """A copied geometry transformed to a resolved PL-2000 CRS."""

    geometry: QgsGeometry
    target_crs: QgsCoordinateReferenceSystem
    target_epsg: int
    zone: int


def measure_geodesic_area_m2(
    geometry: QgsGeometry,
    source_crs: QgsCoordinateReferenceSystem,
    transform_context: QgsCoordinateTransformContext,
) -> float:
    """Measure an ellipsoidal area on GRS 80 using the QGIS engine."""

    _validate_polygon_geometry(geometry)
    calculator = QgsDistanceArea()
    calculator.setSourceCrs(source_crs, transform_context)
    if not calculator.setEllipsoid("GRS80"):
        raise GeometryTransformError(
            "QGIS could not configure the GRS 80 ellipsoid"
        )
    try:
        return calculator.measureArea(geometry)
    except QgsCsException as error:
        raise GeometryTransformError(
            f"failed to measure ellipsoidal area on GRS 80: {error}"
        ) from error


def transform_geometry_to_pl2000(
    geometry: QgsGeometry,
    source_crs: QgsCoordinateReferenceSystem,
    transform_context: QgsCoordinateTransformContext,
    *,
    selected_zone: Optional[int] = None,
) -> TransformedGeometry:
    """Copy and transform a polygon to PL-2000 without touching the source."""

    _validate_polygon_geometry(geometry)
    validate_geometry_budget(geometry)
    selection = resolve_target_pl2000_crs(
        source_crs,
        selected_zone=selected_zone,
    )
    transformed = QgsGeometry(geometry)

    if source_crs != selection.crs:
        coordinate_transform = QgsCoordinateTransform(
            source_crs,
            selection.crs,
            transform_context,
        )
        try:
            operation_result = transformed.transform(coordinate_transform)
        except QgsCsException as error:
            raise GeometryTransformError(
                "failed to transform geometry to "
                f"EPSG:{selection.epsg}: {error}"
            ) from error

        if operation_result != Qgis.GeometryOperationResult.Success:
            raise GeometryTransformError(
                "geometry transform returned a non-success result: "
                f"{operation_result}"
            )

    _validate_polygon_geometry(transformed)
    return TransformedGeometry(
        geometry=transformed,
        target_crs=selection.crs,
        target_epsg=selection.epsg,
        zone=selection.zone,
    )


def validate_geometry_budget(geometry: QgsGeometry) -> None:
    """Reject a polygon that exceeds the synchronous processing budget."""

    _validate_polygon_geometry(geometry)
    coordinate_count = geometry.constGet().nCoordinates()
    if coordinate_count > MAX_BOUNDARY_COORDINATES:
        raise GeometryInputError(
            "Geometria przekracza limit liczby współrzędnych: "
            f"{coordinate_count} > {MAX_BOUNDARY_COORDINATES}. "
            "Uprość lub podziel obiekt przed obliczeniem."
        )

    part_count = 0
    ring_count = 0
    for part in geometry.constParts():
        if not isinstance(part, QgsCurvePolygon):
            raise GeometryInputError("polygon contains a non-polygon part")

        part_count += 1
        if part_count > MAX_POLYGON_PARTS:
            raise GeometryInputError(
                "Geometria przekracza limit liczby części: "
                f"{part_count} > {MAX_POLYGON_PARTS}. "
                "Podziel obiekt przed obliczeniem."
            )

        ring_count += 1 + part.numInteriorRings()
        if ring_count > MAX_POLYGON_RINGS:
            raise GeometryInputError(
                "Geometria przekracza limit liczby pierścieni: "
                f"{ring_count} > {MAX_POLYGON_RINGS}. "
                "Podziel obiekt przed obliczeniem."
            )


def extract_boundary_points(
    geometry: QgsGeometry,
) -> Tuple[Pl2000BoundaryPoint, ...]:
    """Extract effective ring vertices without segmentizing curved rings."""

    _validate_polygon_geometry(geometry)
    boundary_points = []
    for ring in _polygon_rings(geometry):
        for point in _effective_ring_points(ring):
            boundary_points.append(
                pl2000_point_from_qgis_coordinates(
                    qgis_easting=point.x(),
                    qgis_northing=point.y(),
                )
            )
    return tuple(boundary_points)


def geometry_snapshot(geometry: QgsGeometry) -> GeometrySnapshot:
    """Collect report metrics, excluding technical closing vertices."""

    _validate_polygon_geometry(geometry)
    part_count = 0
    ring_count = 0
    vertex_count = 0
    vertex_coordinates = set()

    for part in geometry.constParts():
        if not isinstance(part, QgsCurvePolygon):
            raise GeometryInputError("polygon contains a non-polygon part")
        part_count += 1
        rings = _rings_for_part(part)
        ring_count += len(rings)
        for ring in rings:
            points = _effective_ring_points(ring)
            vertex_count += len(points)
            vertex_coordinates.update(
                (point.x(), point.y()) for point in points
            )

    return GeometrySnapshot(
        part_count=part_count,
        ring_count=ring_count,
        vertex_count=vertex_count,
        area_m2=geometry.area(),
        vertex_coordinates=frozenset(vertex_coordinates),
    )


def _validate_polygon_geometry(geometry: QgsGeometry) -> None:
    if geometry is None or geometry.isNull():
        raise GeometryInputError("geometry is null")
    if geometry.isEmpty():
        raise GeometryInputError("geometry is empty")
    if geometry.type() != Qgis.GeometryType.Polygon:
        raise GeometryInputError("geometry must be polygonal")


def _polygon_rings(geometry: QgsGeometry) -> Tuple[QgsCurve, ...]:
    rings: List[QgsCurve] = []
    for part in geometry.constParts():
        if not isinstance(part, QgsCurvePolygon):
            raise GeometryInputError("polygon contains a non-polygon part")
        rings.extend(_rings_for_part(part))
    return tuple(rings)


def _rings_for_part(part: QgsCurvePolygon) -> Tuple[QgsCurve, ...]:
    exterior_ring = part.exteriorRing()
    if exterior_ring is None:
        raise GeometryInputError("polygon part has no exterior ring")

    rings = [exterior_ring]
    rings.extend(
        part.interiorRing(interior_index)
        for interior_index in range(part.numInteriorRings())
    )
    return tuple(rings)


def _effective_ring_points(ring: QgsCurve) -> tuple:
    if ring.hasCurvedSegments():
        raise CurvedGeometryError(
            "curved polygon rings require an explicit segmentization policy"
        )

    points = tuple(ring.pointN(index) for index in range(ring.numPoints()))
    if len(points) > 1 and _same_xy(points[0], points[-1]):
        return points[:-1]
    return points


def _same_xy(first: object, second: object) -> bool:
    return first.x() == second.x() and first.y() == second.y()
