import pytest
from qgis.core import QgsCoordinateReferenceSystem

from adapters import ZoneSelectionError, resolve_target_pl2000_crs


@pytest.mark.parametrize(
    ("epsg", "expected_zone"),
    [(2176, 5), (2177, 6), (2178, 7), (2179, 8)],
)
def test_pl2000_source_crs_has_priority(epsg: int, expected_zone: int) -> None:
    result = resolve_target_pl2000_crs(
        QgsCoordinateReferenceSystem(f"EPSG:{epsg}")
    )

    assert result.epsg == epsg
    assert result.zone == expected_zone
    assert result.derived_from_source_crs is True


def test_other_crs_requires_user_confirmed_zone() -> None:
    with pytest.raises(ZoneSelectionError):
        resolve_target_pl2000_crs(QgsCoordinateReferenceSystem("EPSG:4326"))


def test_other_crs_uses_explicit_zone() -> None:
    result = resolve_target_pl2000_crs(
        QgsCoordinateReferenceSystem("EPSG:4326"),
        selected_zone=8,
    )

    assert result.epsg == 2179
    assert result.zone == 8
    assert result.derived_from_source_crs is False


def test_manual_zone_cannot_override_pl2000_source_crs() -> None:
    with pytest.raises(ZoneSelectionError):
        resolve_target_pl2000_crs(
            QgsCoordinateReferenceSystem("EPSG:2177"),
            selected_zone=7,
        )


def test_invalid_source_crs_is_rejected() -> None:
    with pytest.raises(ZoneSelectionError):
        resolve_target_pl2000_crs(QgsCoordinateReferenceSystem())
