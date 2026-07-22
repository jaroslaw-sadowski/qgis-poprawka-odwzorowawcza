"""Immutable data models used by the pure calculation module."""

from dataclasses import dataclass
from decimal import Decimal
from math import isfinite
from typing import Tuple

from .errors import NonFiniteValueError


@dataclass(frozen=True)
class Pl2000BoundaryPoint:
    """A boundary point named according to the Polish geodetic convention.

    ``northing_x`` is the legal/geodetic X coordinate and ``easting_y`` is
    the legal/geodetic Y coordinate, including the PL-2000 zone prefix.
    """

    northing_x: float
    easting_y: float

    def __post_init__(self) -> None:
        if not isfinite(self.northing_x):
            raise NonFiniteValueError("northing_x must be finite")
        if not isfinite(self.easting_y):
            raise NonFiniteValueError("easting_y must be finite")


@dataclass(frozen=True)
class AreaCalculationResult:
    """Auditable result of the statutory projection correction formula."""

    po_m2: float
    correction_m2: float
    legal_area_m2_raw: float
    legal_area_ha_raw: float
    legal_area_ha_rounded: Decimal
    zone: int
    epsg: int
    pgk_x_northing: float
    pgk_y_easting: float
    x_gk_northing: float
    y_gk_easting: float
    u: float
    v: float
    sigma_cm_per_km: float
    scale_m: float
    warnings: Tuple[str, ...]
