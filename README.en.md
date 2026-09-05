# Poprawka odwzorowawcza PL-2000

[Polski](README.md) · **English**

A QGIS plugin that calculates parcel areas using the PL-2000 projection
correction required by Polish regulations. It helps check the areas of
existing and proposed parcels for surveying and cadastral work.

It implements **§ 16(2) and Annex 3 of the Regulation of 27 July 2021 on
the land and building register**
([Journal of Laws 2024, item 219, as amended](https://eli.gov.pl/eli/DU/2024/219/ogl)).
Results are shown in m² and hectares, with a reporting precision of 0.0001 ha.

This calculation differs from QGIS's native Cartesian area (on a plane)
and geodesic measurement (on an ellipsoid). The plugin shows all three
values for comparison. The results may differ slightly.

## How to use

Requires QGIS 3.40–3.x. Install through the plugin manager, including from ZIP.
The interface is in Polish. The plugin covers Poland, PL-2000 zones 5–8.
Descriptions in Polish and English are available in the plugin manager
and the plugin's **O wtyczce…** (About) window.

- **One parcel:** select a polygon and choose **Plugins → Poprawka
  odwzorowawcza PL-2000**, or its icon on the Plugins toolbar. Select the
  zone if requested and click **Przelicz** (Calculate). Use **Zapisz raport
  MD…** (Save MD report) to export the report.
- **Multiple parcels:** search for **Poprawka odwzorowawcza PL-2000** in
  the Processing toolbox. Save the result to a new layer, preferably
  GeoPackage.

By default, geometry is checked without repair. Optional repair works
on a copy. Results for invalid geometry without repair are diagnostic only.

## Privacy and responsibility

The plugin works locally and **does not send data outside QGIS**. It does
not modify the source layer. It uses only libraries and tools supplied
with QGIS and the Python standard library; no additional installation is
required.

This project was developed through **vibe coding**, with AI assistance.
**The author accepts no responsibility for results or consequences of
their use**, to the extent permitted by law. Before using a result, verify
the data, coordinate reference system, parcel boundaries and current
regulations.

## Checks performed

The plugin passed local checks described in the
[QGIS guidelines](https://plugins.qgis.org/docs/security-scanning/tools):

- **Bandit** — Python code security.
- **detect-secrets** — no passwords, keys or tokens detected.
- **Flake8** — code errors and quality.
- **ZIP analysis** — structure, permissions, and absence of hidden files,
  executable files and unwanted additions.

Additional checks covered Ruff, development dependency auditing with
pip-audit, calculations, geometry, result and report saving, and reproducible
packaging. These are local checks, not QGIS certification or a guarantee
of correctness for every input dataset.

Author: **Jarosław Sadowski** · License: **GNU GPL v2**.
[Legal basis and limitations (Polish)](https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/blob/main/docs/LEGAL_BASIS.md)
· [Issues](https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/issues)
· [Contributing (Polish)](https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/blob/main/CONTRIBUTING.md)
