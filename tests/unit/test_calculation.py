import math

import pytest

from core import (
    M0,
    Q1,
    Q2,
    Q3,
    Q4,
    SIGMA0_CM_PER_KM,
    EmptyBoundaryPointsError,
    InvalidAreaError,
    NonFiniteValueError,
    Pl2000BoundaryPoint,
    calculate_area,
    calculate_area_from_pgk,
    calculate_pgk,
)


def test_statutory_constants_are_exact() -> None:
    assert M0 == 0.999923
    assert SIGMA0_CM_PER_KM == -7.7
    assert Q1 == 306.752873
    assert Q2 == -0.312616
    assert Q3 == 0.006382
    assert Q4 == 0.158591


def test_one_hectare_on_central_meridian_matches_reference_result() -> None:
    pgk = Pl2000BoundaryPoint(
        northing_x=5_800_000.0,
        easting_y=7_500_000.0,
    )

    result = calculate_area_from_pgk(po_m2=10_000.0, pgk=pgk, epsg=2178)

    expected_x_gk = 5_800_000.0 / M0
    expected_u = (expected_x_gk - 5_800_000.0) * 2.0e-6

    assert result.pgk_x_northing == 5_800_000.0
    assert result.pgk_y_easting == 7_500_000.0
    assert result.x_gk_northing == pytest.approx(expected_x_gk)
    assert result.y_gk_easting == pytest.approx(0.0)
    assert result.u == pytest.approx(expected_u)
    assert result.v == pytest.approx(0.0)
    assert result.sigma_cm_per_km == pytest.approx(-7.7)
    assert result.scale_m == pytest.approx(0.999923)
    assert result.correction_m2 == pytest.approx(-1.53994071)
    assert result.legal_area_m2_raw == pytest.approx(10_001.53994071)
    assert str(result.legal_area_ha_rounded) == "1.0002"


def test_formula_intermediate_values_are_calculated_step_by_step() -> None:
    pgk = Pl2000BoundaryPoint(
        northing_x=5_850_000.0,
        easting_y=6_625_000.0,
    )
    po_m2 = 123_456.789

    expected_x_gk = pgk.northing_x / M0
    expected_y_gk = (pgk.easting_y - 6_500_000.0) / M0
    expected_u = (expected_x_gk - 5_800_000.0) * 2.0e-6
    expected_v = expected_y_gk * 2.0e-6
    expected_sigma = SIGMA0_CM_PER_KM + M0 * expected_v**2 * (
        Q1 + Q2 * expected_u + Q3 * expected_u**2 + Q4 * expected_v**2
    )
    expected_scale = expected_sigma * 1.0e-5 + 1.0
    expected_correction = po_m2 * (expected_scale**2 - 1.0)
    expected_area = po_m2 - expected_correction

    result = calculate_area_from_pgk(po_m2=po_m2, pgk=pgk, epsg=2177)

    assert result.x_gk_northing == pytest.approx(expected_x_gk)
    assert result.y_gk_easting == pytest.approx(expected_y_gk)
    assert result.u == pytest.approx(expected_u)
    assert result.v == pytest.approx(expected_v)
    assert result.sigma_cm_per_km == pytest.approx(expected_sigma)
    assert result.scale_m == pytest.approx(expected_scale)
    assert result.correction_m2 == pytest.approx(expected_correction)
    assert result.legal_area_m2_raw == pytest.approx(expected_area)


def test_formula_is_symmetric_on_both_sides_of_central_meridian() -> None:
    west = Pl2000BoundaryPoint(5_800_000.0 * M0, 7_400_000.0)
    east = Pl2000BoundaryPoint(5_800_000.0 * M0, 7_600_000.0)

    west_result = calculate_area_from_pgk(po_m2=10_000.0, pgk=west, epsg=2178)
    east_result = calculate_area_from_pgk(po_m2=10_000.0, pgk=east, epsg=2178)

    assert west_result.v == pytest.approx(-east_result.v)
    assert west_result.sigma_cm_per_km == pytest.approx(east_result.sigma_cm_per_km)
    assert west_result.legal_area_m2_raw == pytest.approx(east_result.legal_area_m2_raw)


def test_pgk_uses_unique_boundary_points() -> None:
    first = Pl2000BoundaryPoint(5_700_000.0, 7_400_000.0)
    second = Pl2000BoundaryPoint(5_900_000.0, 7_600_000.0)

    pgk = calculate_pgk([first, first, second])

    assert pgk == Pl2000BoundaryPoint(5_800_000.0, 7_500_000.0)


def test_calculation_reports_removed_duplicate_points() -> None:
    point = Pl2000BoundaryPoint(5_800_000.0 * M0, 7_500_000.0)

    result = calculate_area(
        po_m2=10_000.0,
        boundary_points=[point, point],
        epsg=2178,
    )

    assert result.warnings == ("duplicate_boundary_points_removed",)


def test_empty_boundary_points_are_rejected() -> None:
    with pytest.raises(EmptyBoundaryPointsError):
        calculate_pgk([])


@pytest.mark.parametrize("invalid_area", [0.0, -1.0])
def test_non_positive_area_is_rejected(invalid_area: float) -> None:
    pgk = Pl2000BoundaryPoint(5_800_000.0, 7_500_000.0)

    with pytest.raises(InvalidAreaError):
        calculate_area_from_pgk(po_m2=invalid_area, pgk=pgk, epsg=2178)


@pytest.mark.parametrize("invalid_area", [math.nan, math.inf, -math.inf])
def test_non_finite_area_is_rejected(invalid_area: float) -> None:
    pgk = Pl2000BoundaryPoint(5_800_000.0, 7_500_000.0)

    with pytest.raises(NonFiniteValueError):
        calculate_area_from_pgk(po_m2=invalid_area, pgk=pgk, epsg=2178)
