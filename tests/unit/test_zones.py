import pytest

from core import (
    Pl2000BoundaryPoint,
    UnsupportedPl2000CrsError,
    ZoneMismatchError,
    calculate_area,
    epsg_for_zone,
    validate_easting_zone,
    zone_for_epsg,
    zone_prefix_from_easting,
)


@pytest.mark.parametrize(
    ("epsg", "expected_zone"),
    [
        (2176, 5),
        (2177, 6),
        (2178, 7),
        (2179, 8),
    ],
)
def test_epsg_maps_to_expected_zone(epsg: int, expected_zone: int) -> None:
    assert zone_for_epsg(epsg) == expected_zone
    assert epsg_for_zone(expected_zone) == epsg


@pytest.mark.parametrize("epsg", [2180, 4326, 0])
def test_non_pl2000_epsg_is_rejected(epsg: int) -> None:
    with pytest.raises(UnsupportedPl2000CrsError):
        zone_for_epsg(epsg)


@pytest.mark.parametrize(
    ("easting_y", "expected_zone"),
    [
        (5_500_000.0, 5),
        (6_500_000.0, 6),
        (7_500_000.0, 7),
        (8_500_000.0, 8),
    ],
)
def test_zone_prefix_is_read_from_legal_easting(
    easting_y: float, expected_zone: int
) -> None:
    assert zone_prefix_from_easting(easting_y) == expected_zone


def test_easting_prefix_must_match_epsg_zone() -> None:
    with pytest.raises(ZoneMismatchError):
        validate_easting_zone(6_500_000.0, expected_zone=7)


def test_every_boundary_point_is_checked_not_only_pgk() -> None:
    points = [
        Pl2000BoundaryPoint(5_800_000.0, 7_400_000.0),
        Pl2000BoundaryPoint(5_800_000.0, 6_600_000.0),
    ]

    with pytest.raises(ZoneMismatchError):
        calculate_area(po_m2=10_000.0, boundary_points=points, epsg=2178)


@pytest.mark.parametrize(
    ("epsg", "zone"),
    [(2176, 5), (2177, 6), (2178, 7), (2179, 8)],
)
def test_formula_accepts_each_supported_zone(epsg: int, zone: int) -> None:
    point = Pl2000BoundaryPoint(
        northing_x=5_800_000.0,
        easting_y=zone * 1_000_000.0 + 500_000.0,
    )

    result = calculate_area(
        po_m2=10_000.0,
        boundary_points=[point],
        epsg=epsg,
    )

    assert result.zone == zone
    assert result.epsg == epsg
