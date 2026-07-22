"""Statutory PL-2000 projection correction without QGIS dependencies."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from math import floor, fsum, isfinite
from typing import Iterable, Sequence, Tuple, Union

from .errors import (
    EmptyBoundaryPointsError,
    InvalidAreaError,
    InvalidZoneError,
    NonFiniteValueError,
    UnsupportedPl2000CrsError,
    ZoneMismatchError,
)
from .models import AreaCalculationResult, Pl2000BoundaryPoint

M0 = 0.999923
SIGMA0_CM_PER_KM = -7.7
Q1 = 306.752873
Q2 = -0.312616
Q3 = 0.006382
Q4 = 0.158591

HECTARE_IN_M2 = 10_000.0
ZONE_PREFIX_DIVISOR = 1_000_000.0
FALSE_EASTING_WITHIN_ZONE_M = 500_000.0
HA_QUANTUM = Decimal("0.0001")

EPSG_TO_ZONE = {
    2176: 5,
    2177: 6,
    2178: 7,
    2179: 8,
}
ZONE_TO_EPSG = {zone: epsg for epsg, zone in EPSG_TO_ZONE.items()}

DecimalInput = Union[Decimal, float, int, str]


def pl2000_point_from_qgis_coordinates(
    *, qgis_easting: float, qgis_northing: float
) -> Pl2000BoundaryPoint:
    """Map QGIS working XY coordinates to explicitly named PL-2000 axes.

    QGIS geometry uses ``x`` for easting and ``y`` for northing. Polish
    geodetic notation calls northing X and easting Y. Keyword-only arguments
    make an accidental positional swap harder.
    """

    return Pl2000BoundaryPoint(
        northing_x=qgis_northing,
        easting_y=qgis_easting,
    )


def zone_for_epsg(epsg: int) -> int:
    """Return the PL-2000 zone encoded by an EPSG code."""

    try:
        return EPSG_TO_ZONE[epsg]
    except KeyError as error:
        raise UnsupportedPl2000CrsError(
            f"EPSG:{epsg} is not a supported PL-2000 CRS"
        ) from error


def epsg_for_zone(zone: int) -> int:
    """Return the EPSG code assigned to a PL-2000 zone."""

    _validate_zone(zone)
    return ZONE_TO_EPSG[zone]


def zone_prefix_from_easting(easting_y: float) -> int:
    """Extract the million-metre PL-2000 zone prefix from legal Y."""

    _require_finite(easting_y, "easting_y")
    return floor(easting_y / ZONE_PREFIX_DIVISOR)


def validate_easting_zone(easting_y: float, expected_zone: int) -> None:
    """Ensure that legal Y carries the prefix of ``expected_zone``."""

    _validate_zone(expected_zone)
    actual_zone = zone_prefix_from_easting(easting_y)
    if actual_zone != expected_zone:
        raise ZoneMismatchError(
            "PL-2000 easting prefix does not match the selected zone: "
            f"expected {expected_zone}, got {actual_zone} for Y={easting_y}"
        )


def unique_boundary_points(
    boundary_points: Iterable[Pl2000BoundaryPoint],
) -> Tuple[Pl2000BoundaryPoint, ...]:
    """Deduplicate exact coordinate pairs while preserving input order."""

    unique_points = []
    seen = set()
    for point in boundary_points:
        if not isinstance(point, Pl2000BoundaryPoint):
            raise TypeError("boundary_points must contain Pl2000BoundaryPoint")
        if point not in seen:
            seen.add(point)
            unique_points.append(point)
    return tuple(unique_points)


def calculate_pgk(
    boundary_points: Iterable[Pl2000BoundaryPoint],
) -> Pl2000BoundaryPoint:
    """Calculate PGK as the arithmetic mean of unique boundary points."""

    points = unique_boundary_points(boundary_points)
    if not points:
        raise EmptyBoundaryPointsError("at least one boundary point is required")

    point_count = len(points)
    return Pl2000BoundaryPoint(
        northing_x=fsum(point.northing_x for point in points) / point_count,
        easting_y=fsum(point.easting_y for point in points) / point_count,
    )


def round_area_ha(area_ha: DecimalInput) -> Decimal:
    """Round hectares to 0.0001 ha using the named application policy."""

    try:
        decimal_area = Decimal(str(area_ha))
    except (InvalidOperation, ValueError) as error:
        raise NonFiniteValueError("area_ha must be a finite number") from error

    if not decimal_area.is_finite():
        raise NonFiniteValueError("area_ha must be finite")
    return decimal_area.quantize(HA_QUANTUM, rounding=ROUND_HALF_UP)


def calculate_area_from_pgk(
    *,
    po_m2: float,
    pgk: Pl2000BoundaryPoint,
    epsg: int,
    warnings: Sequence[str] = (),
) -> AreaCalculationResult:
    """Apply the statutory formula to a known PGK point."""

    _validate_po(po_m2)
    zone = zone_for_epsg(epsg)
    validate_easting_zone(pgk.easting_y, zone)

    x_gk_northing = pgk.northing_x / M0
    y_gk_easting = (
        pgk.easting_y - (zone * ZONE_PREFIX_DIVISOR + FALSE_EASTING_WITHIN_ZONE_M)
    ) / M0

    u = (x_gk_northing - 5_800_000.0) * 2.0e-6
    v = y_gk_easting * 2.0e-6

    sigma_cm_per_km = SIGMA0_CM_PER_KM + M0 * v**2 * (
        Q1 + Q2 * u + Q3 * u**2 + Q4 * v**2
    )
    scale_m = sigma_cm_per_km * 1.0e-5 + 1.0

    correction_m2 = po_m2 * (scale_m**2 - 1.0)
    legal_area_m2_raw = po_m2 - correction_m2
    legal_area_ha_raw = legal_area_m2_raw / HECTARE_IN_M2

    for name, value in (
        ("x_gk_northing", x_gk_northing),
        ("y_gk_easting", y_gk_easting),
        ("u", u),
        ("v", v),
        ("sigma_cm_per_km", sigma_cm_per_km),
        ("scale_m", scale_m),
        ("correction_m2", correction_m2),
        ("legal_area_m2_raw", legal_area_m2_raw),
    ):
        _require_finite(value, name)

    return AreaCalculationResult(
        po_m2=po_m2,
        correction_m2=correction_m2,
        legal_area_m2_raw=legal_area_m2_raw,
        legal_area_ha_raw=legal_area_ha_raw,
        legal_area_ha_rounded=round_area_ha(legal_area_ha_raw),
        zone=zone,
        epsg=epsg,
        pgk_x_northing=pgk.northing_x,
        pgk_y_easting=pgk.easting_y,
        x_gk_northing=x_gk_northing,
        y_gk_easting=y_gk_easting,
        u=u,
        v=v,
        sigma_cm_per_km=sigma_cm_per_km,
        scale_m=scale_m,
        warnings=tuple(warnings),
    )


def calculate_area(
    *,
    po_m2: float,
    boundary_points: Iterable[Pl2000BoundaryPoint],
    epsg: int,
) -> AreaCalculationResult:
    """Calculate PGK, validate the zone and apply the statutory formula."""

    supplied_points = tuple(boundary_points)
    points = unique_boundary_points(supplied_points)
    if not points:
        raise EmptyBoundaryPointsError("at least one boundary point is required")

    zone = zone_for_epsg(epsg)
    for point in points:
        validate_easting_zone(point.easting_y, zone)

    warnings = ()
    if len(points) != len(supplied_points):
        warnings = ("duplicate_boundary_points_removed",)

    pgk = calculate_pgk(points)
    return calculate_area_from_pgk(
        po_m2=po_m2,
        pgk=pgk,
        epsg=epsg,
        warnings=warnings,
    )


def _validate_zone(zone: int) -> None:
    if zone not in ZONE_TO_EPSG:
        raise InvalidZoneError(f"zone must be one of 5, 6, 7 or 8, got {zone}")


def _validate_po(po_m2: float) -> None:
    _require_finite(po_m2, "po_m2")
    if po_m2 <= 0:
        raise InvalidAreaError("po_m2 must be greater than zero")


def _require_finite(value: float, name: str) -> None:
    try:
        finite = isfinite(value)
    except TypeError as error:
        raise NonFiniteValueError(f"{name} must be a finite number") from error
    if not finite:
        raise NonFiniteValueError(f"{name} must be finite")
