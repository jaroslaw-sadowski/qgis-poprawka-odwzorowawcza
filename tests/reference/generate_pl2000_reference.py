"""Reproduce synthetic Annex 3 references using exact rational arithmetic.

Run this file from the repo root and compare stdout with the checked-in
pl2000_reference.json. Tests never regenerate expected values.
No production code, QGIS, GEOS or PROJ is used. Areas use the shoelace
formula; coefficients are transcribed from Dz.U. 2024 poz. 219, p. 28.
Coordinates are (easting, northing); rings exclude the closing vertex.
"""

import json
from decimal import Decimal, localcontext
from fractions import Fraction

CASES = (
    (
        "central_square",
        2178,
        ("7500000", "5800000"),
        [[[("-50", "-50"), ("50", "-50"), ("50", "50"), ("-50", "50")]]],
    ),
    (
        "east_asymmetric",
        2178,
        ("7600000", "5800000"),
        [[[("0", "0"), ("200", "0"), ("250", "100"), ("0", "300")]]],
    ),
    (
        "west_centimetres",
        2176,
        ("5400000", "5450000"),
        [[[("0", "0"), ("123.45", "0"), ("100.12", "67.89"), ("0", "90.12")]]],
    ),
    (
        "multipart_with_hole",
        2177,
        ("6625000", "5850000"),
        [
            [
                [("0", "0"), ("400", "0"), ("400", "300"), ("0", "300")],
                [("40", "60"), ("80", "60"), ("80", "80"), ("40", "80")],
            ],
            [[("500", "400"), ("620", "400"), ("520", "450")]],
        ],
    ),
    (
        "millimetres",
        2179,
        ("8500000", "6000000"),
        [
            [
                [
                    ("0.001", "0.002"),
                    ("0.126", "0.002"),
                    ("0.130", "0.203"),
                    ("0.001", "0.200"),
                ]
            ]
        ],
    ),
    (
        "source_bow_tie",
        2178,
        ("7500000", "5800000"),
        [[[("0", "0"), ("200", "200"), ("0", "200"), ("100", "0")]]],
    ),
    (
        "repaired_bow_tie",
        2178,
        ("7500000", "5800000"),
        [
            [[("0", "0"), ("200/3", "200/3"), ("100", "0")]],
            [[("0", "200"), ("200", "200"), ("200/3", "200/3")]],
        ],
    ),
)


def decimal_text(number):
    with localcontext() as context:
        context.prec = 45
        return str(Decimal(number.numerator) / Decimal(number.denominator))


def reference_case(name, epsg, origin, offsets):
    e0, n0 = map(Fraction, origin)
    parts = [
        [
            [(e0 + Fraction(e), n0 + Fraction(n)) for e, n in ring]
            for ring in part
        ]
        for part in offsets
    ]
    area = Fraction(0)
    points = set()
    for part in parts:
        for index, ring in enumerate(part):
            points.update(ring)
            twice_area = sum(
                a[0] * b[1] - b[0] * a[1]
                for a, b in zip(ring, ring[1:] + ring[:1])
            )
            area += (1 if index == 0 else -1) * abs(twice_area) / 2
    northing = sum(n for e, n in points) / len(points)
    easting = sum(e for e, n in points) / len(points)
    zone = epsg - 2171
    m0 = Fraction("0.999923")
    x_gk = northing / m0
    y_gk = (easting - zone * 1_000_000 - 500_000) / m0
    u = (x_gk - 5_800_000) / 500_000
    v = y_gk / 500_000
    sigma = Fraction("-7.7") + m0 * v * v * (
        Fraction("306.752873")
        - Fraction("0.312616") * u
        + Fraction("0.006382") * u * u
        + Fraction("0.158591") * v * v
    )
    scale = 1 + sigma / 100_000
    correction = area * (scale * scale - 1)
    corrected = area - correction
    # Exactly round positive m² to integer: 0.0001 ha = 1 m² (half-up).
    rounded_m2 = (2 * corrected.numerator + corrected.denominator) // (
        2 * corrected.denominator
    )
    expected = {
        "po_m2": area,
        "pgk_x_northing": northing,
        "pgk_y_easting": easting,
        "x_gk_northing": x_gk,
        "y_gk_easting": y_gk,
        "u": u,
        "v": v,
        "sigma_cm_per_km": sigma,
        "scale_m": scale,
        "correction_m2": correction,
        "legal_area_m2_raw": corrected,
        "legal_area_ha_raw": corrected / 10_000,
    }
    return {
        "name": name,
        "epsg": epsg,
        "parts": [
            [
                [[decimal_text(e), decimal_text(n)] for e, n in ring]
                for ring in part
            ]
            for part in parts
        ],
        "expected": {key: decimal_text(v) for key, v in expected.items()},
        "rounded_ha": format(Decimal(rounded_m2) / 10_000, ".4f"),
    }


if __name__ == "__main__":
    print(json.dumps([reference_case(*case) for case in CASES], indent=2))
