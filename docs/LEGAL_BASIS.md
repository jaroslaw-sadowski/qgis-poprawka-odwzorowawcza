# Podstawa prawna i zakres obliczenia

Wtyczka implementuje powierzchniową poprawkę odwzorowawczą dla działek
ewidencyjnych w polskim układzie PL-2000.

Podstawowe źródła:

- § 16 ust. 2 rozporządzenia w sprawie ewidencji gruntów i budynków,
  Dz.U. 2024 poz. 219 ze zm. — obowiązek obliczenia pola na podstawie
  współrzędnych punktów granicznych z uwzględnieniem poprawki
  odwzorowawczej oraz wykazania go w hektarach z precyzją do `0,0001 ha`;
- załącznik nr 3 do rozporządzenia w sprawie ewidencji gruntów i budynków,
  Dz.U. 2024 poz. 219 — wzór poprawki i definicja przybliżonego środka
  ciężkości:
  <https://eli.gov.pl/eli/DU/2024/219/ogl>;
- rozporządzenie w sprawie państwowego systemu odniesień przestrzennych,
  Dz.U. 2024 poz. 342 — układy PL-2000 i konwencja osi:
  <https://eli.gov.pl/eli/DU/2024/342/ogl>.

Aktualne stanowisko Głównego Urzędu Geodezji i Kartografii dotyczące
stosowania § 16 ust. 2 i załącznika nr 3:
<https://www.gov.pl/web/gugik/zasady-obliczania-pol-powierzchni-dzialek-ewidencyjnych>.

## Znaczenie prezentowanych pól

- `P₀` jest polem planarnym, matematycznym (kartezjańskim), obliczonym
  z prostokątnych współrzędnych płaskich PL-2000 przez
  `QgsGeometry.area()`.
- `P = P₀ − ΔP₀` jest głównym wynikiem obliczenia według załącznika nr 3.
  Przepisy definiują je jako pole obiektu ewidencyjnego będącego fragmentem
  powierzchni elipsoidy GRS 80.
- „Pole geodezyjne QGIS — GRS 80” jest dodatkowym, niezależnym pomiarem
  `QgsDistanceArea.measureArea()` bezpośrednio na elipsoidzie. Nie zastępuje
  wyniku według rozporządzenia i może się od niego nieznacznie różnić,
  ponieważ QGIS wykonuje pomiar geometrii na elipsoidzie, a wynik prawny
  korzysta z powierzchniowej poprawki odwzorowawczej wyznaczonej w punkcie
  `P_GK`.

Materiały w `docs/legal/` są zachowanymi kopiami referencyjnymi użytymi
podczas implementacji. Nie stanowią mechanizmu automatycznej aktualizacji
prawa. Przed użyciem wyniku w postępowaniu urzędowym należy sprawdzić aktualny
stan prawny, właściwy CRS, strefę PL-2000 i źródło punktów granicznych.

Moduł obliczeniowy nie wykonuje zaokrągleń pośrednich. Wartość ewidencyjna
jest prezentowana w hektarach z czterema miejscami po przecinku, zgodnie
z udokumentowaną polityką `ROUND_HALF_UP`.
