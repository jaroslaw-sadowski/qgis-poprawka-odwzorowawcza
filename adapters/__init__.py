"""PyQGIS adapters for geometry preparation and PL-2000 transforms."""

from .geometry import (
    CurvedGeometryError,
    GeometryInputError,
    GeometrySnapshot,
    GeometryTransformError,
    TransformedGeometry,
    extract_boundary_points,
    geometry_snapshot,
    transform_geometry_to_pl2000,
)
from .repair import (
    GeometryPreparationResult,
    GeometryRepairError,
    GeometryRepairReport,
    RepairMethod,
    RepairMode,
    prepare_geometry,
)
from .zones import (
    TargetCrsSelection,
    ZoneSelectionError,
    resolve_target_pl2000_crs,
)

__all__ = [
    "CurvedGeometryError",
    "GeometryInputError",
    "GeometryPreparationResult",
    "GeometryRepairError",
    "GeometryRepairReport",
    "GeometrySnapshot",
    "GeometryTransformError",
    "RepairMethod",
    "RepairMode",
    "TargetCrsSelection",
    "TransformedGeometry",
    "ZoneSelectionError",
    "extract_boundary_points",
    "geometry_snapshot",
    "prepare_geometry",
    "resolve_target_pl2000_crs",
    "transform_geometry_to_pl2000",
]
