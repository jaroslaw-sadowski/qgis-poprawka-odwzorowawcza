import pytest

from core import NonFiniteValueError, pl2000_point_from_qgis_coordinates


def test_qgis_axes_are_mapped_to_polish_geodetic_convention() -> None:
    point = pl2000_point_from_qgis_coordinates(
        qgis_easting=7_500_125.25,
        qgis_northing=5_800_375.75,
    )

    assert point.northing_x == 5_800_375.75
    assert point.easting_y == 7_500_125.25


@pytest.mark.parametrize("invalid_value", [float("nan"), float("inf"), -float("inf")])
def test_qgis_axis_mapping_rejects_non_finite_values(invalid_value: float) -> None:
    with pytest.raises(NonFiniteValueError):
        pl2000_point_from_qgis_coordinates(
            qgis_easting=invalid_value,
            qgis_northing=5_800_000.0,
        )
