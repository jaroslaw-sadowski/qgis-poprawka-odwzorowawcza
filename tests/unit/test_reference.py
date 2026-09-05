"""Fixed, independently computed rational references for Annex 3."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from core import (
    Pl2000BoundaryPoint,
    calculate_area,
    calculate_area_from_pgk,
)

REFERENCES = json.loads(
    (
        Path(__file__).parents[1] / "reference" / "pl2000_reference.json"
    ).read_text(encoding="utf-8")
)


@pytest.mark.parametrize("case", REFERENCES, ids=lambda c: c["name"])
def test_formula_matches_exact_rational_reference(case):
    points = [
        Pl2000BoundaryPoint(float(n), float(e))
        for part in case["parts"]
        for ring in part
        for e, n in ring
    ]
    result = calculate_area(
        po_m2=float(case["expected"]["po_m2"]),
        boundary_points=points,
        epsg=case["epsg"],
    )
    for field, value in case["expected"].items():
        # Absolute tolerances, avoiding metre-scale default relative
        # tolerances at million-metre coordinates.
        tolerance = (
            1e-10
            if field in ("u", "v", "sigma_cm_per_km", "scale_m")
            else 1e-8
        )
        assert getattr(result, field) == pytest.approx(
            float(value), rel=0, abs=tolerance
        ), field
    assert result.legal_area_ha_rounded == Decimal(case["rounded_ha"])


@pytest.mark.parametrize("zone", [5, 6, 7, 8])
def test_identical_local_coordinates_give_same_correction_in_each_zone(zone):
    case = next(c for c in REFERENCES if c["name"] == "east_asymmetric")
    expected = case["expected"]
    result = calculate_area_from_pgk(
        po_m2=float(expected["po_m2"]),
        pgk=Pl2000BoundaryPoint(
            float(expected["pgk_x_northing"]),
            float(expected["pgk_y_easting"]) + (zone - 7) * 1_000_000,
        ),
        epsg=2171 + zone,
    )
    assert result.correction_m2 == pytest.approx(
        float(expected["correction_m2"]), rel=0, abs=1e-8
    )
    assert result.legal_area_ha_rounded == Decimal(case["rounded_ha"])


@pytest.mark.parametrize(
    ("po_m2", "expected_ha"),
    [(10000.95990, "1.0002"), (10000.95992, "1.0003")],
)
def test_final_rounding_does_not_round_square_metres_first(po_m2, expected_ha):
    # P = P0 * 1.000153994071 exactly at the central meridian.
    # These straddle 10002.5 m² by about 0.00001 m². Rounding to 0.01 m²
    # first would incorrectly make both hectare results round upward.
    exact_m2 = Decimal(str(po_m2)) * Decimal("1.000153994071")
    exact_ha = (exact_m2 / 10000).quantize(
        Decimal("0.0001"), rounding="ROUND_HALF_UP"
    )
    assert exact_ha == Decimal(expected_ha)
    result = calculate_area_from_pgk(
        po_m2=po_m2,
        pgk=Pl2000BoundaryPoint(5_800_000, 7_500_000),
        epsg=2178,
    )
    assert result.legal_area_ha_rounded == exact_ha
