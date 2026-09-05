# Poprawka odwzorowawcza PL-2000 1.1.0

## Polski

Wtyczka oblicza pole działek z poprawką odwzorowawczą PL-2000 według
§ 16 ust. 2 i załącznika nr 3 rozporządzenia w sprawie ewidencji gruntów
i budynków ([Dz.U. 2024 poz. 219 ze zm.](https://eli.gov.pl/eli/DU/2024/219/ogl)).
Udostępnia to obliczenie w bezpłatnym QGIS, bez kupowania komercyjnego
pakietu geodezyjnego tylko do wyznaczenia tej poprawki. Sama wtyczka jest
bezpłatna i otwartoźródłowa, na licencji GNU GPL v2.

W tym wydaniu:

- Obsługa QGIS 4.x obok QGIS 3.40–3.x.
- Zapis raportu pojedynczej działki do Markdown.
- Kontrola geometrii w obu trybach; opcjonalna naprawa kopii. Pole
  i punkt średni pochodzą z tej samej geometrii użytej w obliczeniu.
- Pełna precyzja parametrów zapisywanych w GeoPackage.
- Bezpośredni wpis w menu **Wtyczki → Poprawka odwzorowawcza PL-2000**.
- Opisy i tagi po polsku oraz angielsku; polski interfejs.

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

- QGIS 4.x support alongside QGIS 3.40–3.x.
- Single-parcel report export to Markdown.
- Geometry validation in both modes, with optional repair of a copy.
  Area and mean boundary point use the same calculation geometry.
- Full precision for calculation parameters saved to GeoPackage.
- A direct **Plugins → Poprawka odwzorowawcza PL-2000** menu entry.
- Polish and English descriptions and tags; a Polish interface.

The plugin runs locally using QGIS libraries and standard Python. It
sends no data outside QGIS and does not modify the source layer. It was
developed through vibe coding with AI assistance. The author accepts no
responsibility for results to the extent permitted by law; verify inputs
and results before use.

Install the attached ZIP through QGIS's plugin manager. The `.zip.sha256`
file verifies the download. GitHub's “Source code” archive is not the
installable plugin package.
