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

## Weryfikacja i zasady wyboru geometrii — 2026-09-05

Sprawdzono tekst jednolity oraz nowelizacje:

- [Dz.U. 2024 poz. 1954](https://eli.gov.pl/eli/DU/2024/1954/ogl);
- [Dz.U. 2026 poz. 1094](https://eli.gov.pl/eli/DU/2026/1094/ogl),
  obowiązującą od 2026-08-28.

Nowelizacje te nie zmieniają § 16 ust. 2 ani wzoru i definicji P_GK
w załączniku nr 3. Nowelizacja z 2026 r. dotyczy rejestru cen nieruchomości
(§ 40 oraz załączniki nr 9 i 10). Sprawdzenie aktualności nie jest
mechanizmem automatycznej aktualizacji przyszłych przepisów.

W obu trybach kopia całego poligonu jest najpierw transformowana do
PL-2000. Kontrola GEOS obejmuje geometrię w tym układzie. W trybie bez
naprawy P₀ i P_GK pochodzą z niezmienionych granic po transformacji;
nie wykonuje się `makeValid()`. W trybie naprawy obie wartości pochodzą
z tej samej poprawionej kopii. Punkty dodane przez naprawę uczestniczą
w średniej, a usunięte nie uczestniczą.

P_GK jest średnią arytmetyczną współrzędnych, a nie centroidem ważonym
polem. W implementacji jeden punkt oznacza jedną unikalną parę XY.
Punkt zamykający pierścień i powtórzenia tej samej pary nie zwiększają
jego wagi. Uwzględniamy otwory i wszystkie części poligonu. Nie łączymy
punktów bliskich za pomocą tolerancji ani nie zaokrąglamy ich współrzędnych.
To jawna konwencja reprezentacji punktów granicznych w geometrii, a nie
odczyt identyfikatorów punktów z rejestru EGiB. Z i M nie wpływają na wzór.

Wynik dla niepoprawnej geometrii bez naprawy jest wyłącznie diagnostyczny.
Sam test GEOS potwierdza topologię; nie potwierdza pochodzenia,
dokładności ani prawnego przebiegu granic. Naprawa może wprowadzić punkty
nieobecne w dokumentacji geodezyjnej. Ich akceptacja wymaga weryfikacji
z danymi granicznymi. Właściwy CRS i strefa pozostają warunkiem obliczenia.

Przepis określa precyzję zapisu 0,0001 ha; wybór `ROUND_HALF_UP` dla
przypadku dokładnie połowy kroku jest jawną polityką aplikacji. Obliczenia
nie zaokrąglają P₀, poprawki ani współrzędnych przed wyznaczeniem P w ha.
Formatowanie raportu w m² do dwóch miejsc nie zasila obliczeń w hektarach.
Współrzędne P_GK, sigma i skala są zapisywane w GeoPackage jako liczby
zmiennoprzecinkowe bez wymuszonej liczby miejsc dziesiętnych.

Zakres i dokładności testów opisano w
[raporcie walidacji obliczeń](CALCULATION_VALIDATION_2026-09-05.md).
