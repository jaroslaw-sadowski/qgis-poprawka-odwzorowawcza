"""Domain exceptions raised by the pure calculation module."""


class AreaCalculationError(ValueError):
    """Base class for invalid input to a cadastral area calculation."""


class NonFiniteValueError(AreaCalculationError):
    """Raised when a coordinate or calculation input is NaN or infinite."""


class InvalidAreaError(AreaCalculationError):
    """Raised when the planar area is not strictly positive."""


class EmptyBoundaryPointsError(AreaCalculationError):
    """Raised when PGK cannot be calculated because no points were supplied."""


class InvalidZoneError(AreaCalculationError):
    """Raised when a PL-2000 zone is outside the supported range 5 to 8."""


class UnsupportedPl2000CrsError(AreaCalculationError):
    """Raised when an EPSG code is not one of EPSG:2176 through EPSG:2179."""


class ZoneMismatchError(AreaCalculationError):
    """Raised when the easting prefix conflicts with the selected zone."""
