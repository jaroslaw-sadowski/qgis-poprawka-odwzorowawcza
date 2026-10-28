# Poprawka odwzorowawcza PL-2000 1.1.1

Projekt opisu — wydanie nieopublikowane. / Draft — not yet published.

## Polski

Wtyczka oblicza pole działek z poprawką odwzorowawczą PL-2000 według
§ 16 ust. 2 i załącznika nr 3 rozporządzenia w sprawie ewidencji gruntów
i budynków ([Dz.U. 2024 poz. 219 ze zm.](https://eli.gov.pl/eli/DU/2024/219/ogl)).
Udostępnia to obliczenie w bezpłatnym QGIS, bez kupowania komercyjnego
pakietu geodezyjnego tylko do wyznaczenia tej poprawki. Sama wtyczka jest
bezpłatna i otwartoźródłowa, na licencji GNU GPL v2.

W tym wydaniu:

- Rzeczywiste nazwy pól wynikowych z prefiksem `PO_`: `PO_P0_m2`,
  `PO_dP_m2`, `PO_P_m2`, `PO_P_ha`, `PO_QGIS_m2`, `PO_status`,
  `PO_uwagi` i pozostałe pola diagnostyczne. Polskie nagłówki zawierają
  nazwę i opis z jednostkami, np. `PO_P_m2 — Powierzchnia po poprawce P [m²]`.
- Ochrona danych źródłowych przed nadpisaniem w Processing.
- Obsługa źródłowego `fid` w GeoPackage i ostrzeżenie o skracaniu pól SHP.
- Podsumowanie obliczeń oraz czytelniejszy układ tabeli, zapisywany w GPKG.
- Ostrzeżenie o transformacji zastępczej i kontrola limitów po naprawie.
- Data, wersja wtyczki i etykieta obiektu QGIS w raporcie Markdown.

Identyfikator algorytmu `egib_area:calculate_egib_area` pozostaje bez zmian.
Modele i wyrażenia odwołujące się do dawnych pól `egib_*` wymagają
aktualizacji do nowych nazw `PO_*`.

Zachowano obsługę QGIS 3.40–3.x i 4.x oraz dotychczasowy wzór obliczeń.

Wtyczka działa lokalnie, używa bibliotek QGIS i standardowego Pythona,
nie wysyła danych na zewnątrz i nie zmienia warstwy źródłowej. Powstała
metodą vibe coding, z pomocą AI. Autor nie bierze odpowiedzialności za
wyniki w zakresie dopuszczonym prawem; przed użyciem sprawdź dane i wynik.

Zainstaluj załączony ZIP przez menedżer wtyczek QGIS. Plik `.zip.sha256`
służy do weryfikacji pobranej paczki. Archiwum „Source code” nie jest
paczką instalacyjną wtyczki.

## English

This plugin calculates parcel areas using the PL-2000 projection
correction required by § 16(2) and Annex 3 of Poland's regulation on the
land and building register ([Journal of Laws 2024, item 219, as amended](https://eli.gov.pl/eli/DU/2024/219/ogl)).
It makes this calculation available in free QGIS without buying a
commercial surveying package just for this correction. The plugin itself
is free and open source under GNU GPL v2.

This release adds:

- Actual result field names prefixed with `PO_`: `PO_P0_m2`, `PO_dP_m2`,
  `PO_P_m2`, `PO_P_ha`, `PO_QGIS_m2`, `PO_status`, `PO_uwagi` and the
  other diagnostic fields. Polish headings include each field name
  and a description with units, e.g. `PO_P_m2 — Powierzchnia po poprawce P [m²]`.
- Protection against overwriting source data in Processing.
- Source `fid` handling in GeoPackage and warnings about SHP truncation.
- Calculation summary and a clearer table layout stored in GeoPackage.
- Fallback transformation warnings and geometry limits after repair.
- Date, plugin version and QGIS feature display label in Markdown reports.

The algorithm ID `egib_area:calculate_egib_area` remains unchanged.
Models and expressions referring to the former `egib_*` fields need
updating to the new `PO_*` names.

QGIS 3.40–3.x and 4.x support and the calculation formula are retained.

The plugin runs locally using QGIS libraries and standard Python. It
sends no data outside QGIS and does not modify the source layer. It was
developed through vibe coding with AI assistance. The author accepts no
responsibility for results to the extent permitted by law; verify inputs
and results before use.

Install the attached ZIP through QGIS's plugin manager. The `.zip.sha256`
file verifies the download. GitHub's “Source code” archive is not the
installable plugin package.
