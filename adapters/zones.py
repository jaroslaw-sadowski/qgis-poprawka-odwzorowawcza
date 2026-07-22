"""Selection of a target PL-2000 CRS without centroid-based guessing."""

from dataclasses import dataclass
from typing import Optional

from qgis.core import QgsCoordinateReferenceSystem

if "." in __package__:
    from ..core import epsg_for_zone, zone_for_epsg
else:
    from core import epsg_for_zone, zone_for_epsg


class ZoneSelectionError(ValueError):
    """Raised when a target PL-2000 zone cannot be selected safely."""


@dataclass(frozen=True)
class TargetCrsSelection:
    """A resolved target CRS and its legal PL-2000 zone."""

    crs: QgsCoordinateReferenceSystem
    epsg: int
    zone: int
    derived_from_source_crs: bool


def resolve_target_pl2000_crs(
    source_crs: QgsCoordinateReferenceSystem,
    *,
    selected_zone: Optional[int] = None,
) -> TargetCrsSelection:
    """Resolve target PL-2000 according to the required precedence rules.

    An existing EPSG:2176--2179 source CRS is authoritative. For any other
    valid CRS, the caller must provide a user-confirmed zone.
    """

    if source_crs is None or not source_crs.isValid():
        raise ZoneSelectionError("source CRS is missing or invalid")

    source_epsg = _pl2000_epsg_from_authid(source_crs.authid())
    if source_epsg is not None:
        source_zone = zone_for_epsg(source_epsg)
        if selected_zone is not None and selected_zone != source_zone:
            raise ZoneSelectionError(
                "selected zone conflicts with the PL-2000 source CRS: "
                f"EPSG:{source_epsg} requires zone {source_zone}"
            )
        return TargetCrsSelection(
            crs=QgsCoordinateReferenceSystem.fromEpsgId(source_epsg),
            epsg=source_epsg,
            zone=source_zone,
            derived_from_source_crs=True,
        )

    if selected_zone is None:
        raise ZoneSelectionError(
            "a user-confirmed PL-2000 zone is required for a non-PL-2000 CRS"
        )

    target_epsg = epsg_for_zone(selected_zone)
    return TargetCrsSelection(
        crs=QgsCoordinateReferenceSystem.fromEpsgId(target_epsg),
        epsg=target_epsg,
        zone=selected_zone,
        derived_from_source_crs=False,
    )


def _pl2000_epsg_from_authid(authid: str) -> Optional[int]:
    normalized_authid = authid.strip().upper()
    if not normalized_authid.startswith("EPSG:"):
        return None

    try:
        epsg = int(normalized_authid.removeprefix("EPSG:"))
    except ValueError:
        return None

    return epsg if epsg in (2176, 2177, 2178, 2179) else None
