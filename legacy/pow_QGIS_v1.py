import math
from qgis.core import (
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsDistanceArea,
    QgsFeatureRequest,
    QgsWkbTypes,
    QgsGeometry
)
from qgis.PyQt.QtWidgets import QMessageBox

# ID klikniętego obiektu i warstwy (podstawiane przez QGIS)
feature_id = [%$id%]
layer_id = '[%@layer_id%]'

project = QgsProject.instance()
layer = project.mapLayer(layer_id)

if layer is None:
    QMessageBox.critical(None, "Błąd", "Nie mogę znaleźć warstwy (layer_id).")
else:
    feat = next(layer.getFeatures(QgsFeatureRequest().setFilterFid(feature_id)), None)
    if feat is None:
        QMessageBox.critical(None, "Błąd", f"Nie mogę pobrać obiektu o FID={feature_id}.")
    else:
        geom = feat.geometry()
        if geom is None or geom.isEmpty():
            QMessageBox.information(None, "Powierzchnie działki", "Geometria jest pusta.")
        elif QgsWkbTypes.geometryType(geom.wkbType()) != QgsWkbTypes.PolygonGeometry:
            QMessageBox.information(None, "Powierzchnie działki", "To nie jest poligon.")
        else:
            src_crs = layer.crs()
            ctx = project.transformContext()

            def pick_pl2000_crs(g: QgsGeometry, crs: QgsCoordinateReferenceSystem) -> QgsCoordinateReferenceSystem:
                # Jeśli warstwa już jest w PL-2000 (EPSG:2176-2179), użyj jej.
                auth = crs.authid()
                if auth in ("EPSG:2176", "EPSG:2177", "EPSG:2178", "EPSG:2179"):
                    return QgsCoordinateReferenceSystem(auth)

                # W przeciwnym razie dobierz strefę po długości geogr. centroidu
                ct = QgsCoordinateTransform(crs, QgsCoordinateReferenceSystem("EPSG:4326"), ctx)
                lon = ct.transform(g.centroid().asPoint()).x()

                # granice orientacyjne stref (co 3°): 15/18/21/24
                if lon < 16.5:
                    epsg = 2176  # strefa 5 (15E)
                elif lon < 19.5:
                    epsg = 2177  # strefa 6 (18E)
                elif lon < 22.5:
                    epsg = 2178  # strefa 7 (21E)
                else:
                    epsg = 2179  # strefa 8 (24E)
                return QgsCoordinateReferenceSystem(f"EPSG:{epsg}")

            def geom_to_crs(g: QgsGeometry, from_crs, to_crs) -> QgsGeometry:
                g2 = QgsGeometry(g)
                if from_crs.authid() != to_crs.authid():
                    tr = QgsCoordinateTransform(from_crs, to_crs, ctx)
                    g2.transform(tr)
                return g2

            def iter_rings_points(g2000: QgsGeometry):
                # Zbiera wierzchołki ze wszystkich pierścieni (zewn. i wewn.)
                pts = []
                if g2000.isMultipart():
                    parts = g2000.asMultiPolygon()
                else:
                    parts = [g2000.asPolygon()]

                for part in parts:
                    for ring in part:  # ring: list[QgsPointXY]
                        if not ring:
                            continue
                        # usuń domknięcie (ostatni = pierwszy)
                        if len(ring) > 1 and ring[0] == ring[-1]:
                            ring = ring[:-1]
                        pts.extend(ring)
                return pts

            # --- 1) Pole kartezjańskie (Po) w PL-2000 ---
            crs2000 = pick_pl2000_crs(geom, src_crs)
            g2000 = geom_to_crs(geom, src_crs, crs2000)
            Po = g2000.area()  # m^2

            # --- 2) Pole elipsoidalne (GRS80) ---
            da = QgsDistanceArea()
            da.setEllipsoid("GRS80")
            da.setSourceCrs(crs2000, ctx)
            Pell = da.measureArea(g2000)  # m^2

            # --- 3) Pole wg rozporządzenia (PGK + m^2) ---
            # Stałe z rozporządzenia:
            m0 = 0.999923
            sigma0 = -7.7  # cm/km
            q1, q2, q3, q4 = 306.752873, -0.312616, 0.006382, 0.158591

            pts = iter_rings_points(g2000)
            if not pts:
                QMessageBox.information(None, "Powierzchnie działki", "Brak wierzchołków do wyznaczenia PGK.")
            else:
                X2000 = sum(p.x() for p in pts) / len(pts)
                Y2000 = sum(p.y() for p in pts) / len(pts)

                # N (5..8) z miliona w Y2000:
                N = int(math.floor(Y2000 / 1_000_000))

                # Niemodyfikowane współrzędne GK:
                XGK = X2000 / m0
                YGK = (Y2000 - (N * 1_000_000 + 500_000)) / m0

                u = (XGK - 5_800_000.0) * 2.0e-6
                v = YGK * 2.0e-6

                sigma = sigma0 + m0 * (v ** 2) * (q1 + q2 * u + q3 * (u ** 2) + q4 * (v ** 2))
                m = sigma * 1.0e-5 + 1.0
                m2 = m ** 2

                dPo = Po * (m2 - 1.0)
                Proz = Po - dPo  # P = Po - ΔPo

                def fmt(m2_area):
                    return f"{m2_area:,.3f} m²   ({m2_area/10000.0:.4f} ha)"

                msg = (
                    f"CRS do Po/PGK: {crs2000.authid()}\n\n"
                    f"1) Kartezjańska (Po, PL-2000):\n   {fmt(Po)}\n\n"
                    f"2) Elipsoidalna (GRS80):\n   {fmt(Pell)}\n\n"
                    f"3) Wg rozporządzenia (PGK + m²):\n   {fmt(Proz)}\n\n"
                    f"(info) PGK: X={X2000:.3f}, Y={Y2000:.3f}\n"
                    f"(info) sigma={sigma:.4f} cm/km, m={m:.8f}"
                )

                QMessageBox.information(None, "Powierzchnie działki", msg)
