# Plan przekształcenia skryptu w plugin QGIS

## 1. Cel i zakres

Celem projektu jest utworzenie czytelnego, testowalnego pluginu QGIS do
obliczania pola powierzchni działki ewidencyjnej z uwzględnieniem
powierzchniowej poprawki odwzorowawczej. Implementacja ma być zgodna z:

- QGIS 3.44.x i Qt5,
- QGIS 4.2.x i Qt6,
- wzorem z załącznika nr 3 do rozporządzenia w sprawie ewidencji gruntów
  i budynków,
- prawną konwencją osi płaskich układów współrzędnych.

Niniejszy etap obejmuje wyłącznie audyt i plan. Nie obejmuje tworzenia kodu
pluginu ani zmian w `legacy/pow_QGIS_v1.py`.

## 2. Zasady prowadzenia repozytorium

- Prace będą prowadzone bezpośrednio na gałęzi `main`; dodatkowe gałęzie nie
  są potrzebne na obecnym etapie.
- Zmiany będą małe, logiczne i łatwe do przejrzenia.
- Pliki będą dodawane dopiero wtedy, gdy będą faktycznie używane. Nie będą
  tworzone puste katalogi ani wygenerowane pliki „na zapas”.
- Skrypt pierwotny pozostanie bez zmian w katalogu `legacy/` jako materiał
  referencyjny.
- Dane wejściowe użytkownika nie będą domyślnie modyfikowane.
- Wysłanie zmian do GitHub nastąpi wyłącznie na osobne polecenie.

## 3. Najważniejsze decyzje domenowe

### 3.1. Konwencja osi

Geometria QGIS używa roboczego porządku XY, natomiast polska konwencja
geodezyjna oznacza oś północną jako X, a wschodnią jako Y. Adapter QGIS musi
więc zawsze wykonywać jawne mapowanie:

```text
qgis_easting  = point.x()
qgis_northing = point.y()

legal_X2000 = qgis_northing
legal_Y2000 = qgis_easting
```

W kodzie domenowym nie będą używane samodzielne nazwy `x` i `y`. Nie będzie
wykonywana dodatkowa zamiana na podstawie `crs.axisOrdering()`.

### 3.2. Dobór strefy PL-2000

Kolejność rozstrzygania strefy:

1. Dla EPSG:2176–2179 użyć strefy wynikającej z CRS warstwy.
2. Po transformacji zweryfikować prefiks prawnej współrzędnej wschodniej Y
   wszystkich efektywnych punktów granicznych.
3. Rozbieżność EPSG i prefiksu Y traktować jako błąd blokujący, a nie jako
   podstawę do cichej zmiany strefy.
4. Dla innego CRS wymagać od użytkownika wyboru strefy 5–8.
5. W GUI można pokazać sugestię wyznaczoną orientacyjnie, ale użytkownik musi
   ją potwierdzić. Algorytm Processing nie będzie podejmował interaktywnej
   decyzji i dla innego CRS otrzyma obowiązkowy parametr strefy.

Mapowanie stref pozostaje stałe:

| EPSG | Strefa | Południk osiowy |
|---:|---:|---:|
| 2176 | 5 | 15°E |
| 2177 | 6 | 18°E |
| 2178 | 7 | 21°E |
| 2179 | 8 | 24°E |

Warstwa wyboru strefy otrzyma interfejs pozwalający później podłączyć
autorytatywne przypisanie powiat–strefa bez zmiany modułu obliczeniowego.

### 3.3. Punkty graniczne i PGK

- PGK będzie średnią arytmetyczną współrzędnych punktów granicznych, a nie
  centroidem geometrii.
- W trybie opartym na geometrii punkty zostaną pobrane z pierwotnej kopii
  geometrii po transformacji do właściwego PL-2000, ale przed `makeValid()`.
- Z każdego pierścienia zostanie usunięty wyłącznie techniczny punkt
  domykający.
- Dokładnie równe pary `(northing_x, easting_y)` zostaną globalnie
  zdeduplikowane bez tolerancji, snapowania lub densyfikacji.
- Kolejne duplikaty, geometrie multipart, pierścienie wewnętrzne i krzywe
  spowodują ostrzeżenia diagnostyczne.
- Wierzchołek geometrii nie będzie przedstawiany jako autorytatywny punkt
  graniczny EGiB. Powstanie abstrakcja źródła punktów umożliwiająca późniejsze
  użycie warstwy punktowej EGiB i identyfikatorów punktów.

### 3.4. Walidacja i naprawa geometrii

Proces dla każdego obiektu:

1. Odrzucić geometrię null, pustą lub niepoligonową.
2. Utworzyć kopię geometrii; nigdy nie zmieniać geometrii źródłowej.
3. Przetransformować kopię do wybranego PL-2000.
4. Zapisać metryki i zbiór punktów sprzed naprawy.
5. Sprawdzić poprawność za pomocą GEOS.
6. Poprawną geometrię pozostawić bez zmian.
7. Dla niepoprawnej geometrii spróbować kolejno:

   ```python
   geometry.makeValid(Qgis.MakeValidMethod.Structure, False)
   geometry.makeValid(Qgis.MakeValidMethod.Linework, False)
   ```

8. `Linework` jest wariantem awaryjnym, gdy `Structure` nie jest obsługiwane,
   zwróci błąd albo nie da akceptowalnego wyniku.
9. Odrzucić wynik null, pusty, niepoligonowy lub nadal niepoprawny.
10. Pole `Po` obliczyć z zaakceptowanej geometrii wynikowej, a PGK z
    pierwotnego zbioru punktów.

Do `makeValid()` nie będzie przekazywany argument `feedback`, ponieważ wspólny
kod ma używać API dostępnego w QGIS 3.44.

Tryby pracy:

- `STRICT` — tryb domyślny; jeżeli geometria wymaga `makeValid()`, nie zwraca
  ustawowego wyniku, lecz komplet diagnostyki;
- `AUTO_REPAIR` — naprawia kopię, oblicza wynik i wyraźnie oznacza go jako
  oparty na naprawionej geometrii.

Raport naprawy będzie zawierał:

```text
validity_before
validity_after
repair_method
original_part_count
repaired_part_count
original_ring_count
repaired_ring_count
original_vertex_count
repaired_vertex_count
original_area_m2
repaired_area_m2
area_difference_m2
vertices_added
vertices_removed
warnings
```

Liczby wierzchołków pominą techniczne domknięcia. `vertices_added` i
`vertices_removed` będą licznościami różnic dokładnych zbiorów współrzędnych.
Pole geometrii niepoprawnej sprzed naprawy będzie oznaczone jako informacja
diagnostyczna, a nie wynik ustawowy.

### 3.5. Wzór i zaokrąglanie

Moduł obliczeniowy zachowa kolejność działań z aktu prawnego i nie będzie
zaokrąglać wartości pośrednich. Wynik surowy pozostanie liczbą o pełnej
dostępnej precyzji. Wartość ewidencyjna zostanie obliczona przez `Decimal`
i `ROUND_HALF_UP`, a następnie zapisana dokładnie z czterema miejscami po
przecinku w hektarach.

Pomiar `QgsDistanceArea` na GRS80 może istnieć jedynie jako wartość
diagnostyczna. Nie zastąpi wzoru ustawowego ani nie będzie jego testem
referencyjnym.

## 4. Architektura

### 4.1. Warstwy odpowiedzialności

- `core` — modele domenowe, stałe, PGK, wzór, walidacja liczb i zaokrąglanie;
  bez importów QGIS i Qt.
- `adapters` — mapowanie osi, transformacje, strefy, geometria i raport
  naprawy.
- `processing_provider` — przetwarzanie wielu obiektów i zapis nowej warstwy
  lub tabeli wynikowej.
- `gui` — polski interfejs dla aktywnej warstwy i wybranych działek.
- `compat.py` — jedyne miejsce na nieuniknione różnice QGIS 3/4 lub Qt5/Qt6.

Planowane modele i interfejsy publiczne:

- `Pl2000BoundaryPoint`,
- `AreaCalculationResult`,
- `GeometryRepairReport`,
- `ZoneResolution`,
- `RepairMode`,
- `RepairMethod`,
- `BoundaryPointSource`,
- `ZoneResolver`.

### 4.2. Proponowana struktura repozytorium

Struktura jest propozycją docelową. Elementy będą tworzone dopiero w etapie,
w którym staną się potrzebne.

```text
qgis-poprawka-odwzorowawcza/
├── __init__.py
├── metadata.txt
├── plugin.py
├── compat.py
├── core/
│   ├── __init__.py
│   ├── models.py
│   ├── calculation.py
│   └── errors.py
├── adapters/
│   ├── __init__.py
│   ├── geometry.py
│   ├── zones.py
│   └── repair.py
├── processing_provider/
│   ├── __init__.py
│   ├── provider.py
│   └── area_algorithm.py
├── gui/
│   ├── __init__.py
│   └── dialog.py
├── resources/
│   └── icon.svg
├── tests/
│   ├── unit/
│   ├── qgis/
│   └── fixtures/
├── docs/
│   ├── AUDIT.md
│   ├── CALCULATION.md
│   ├── LEGAL_BASIS.md
│   ├── VALIDATION.md
│   ├── TESTING.md
│   └── legal/
├── legacy/
│   └── pow_QGIS_v1.py
├── PLAN.md
├── README.md
├── CHANGELOG.md
├── AGENTS.md
├── pyproject.toml
└── LICENSE
```

## 5. Etapy przyszłej implementacji

1. **Moduł domenowy** — modele, stałe, wzór, PGK, walidacja wartości
   skończonych i zaokrąglanie.
2. **Testy domenowe** — przykład 1 ha, regresja osi, wszystkie strefy i
   przypadki błędne.
3. **Adapter PyQGIS** — transformacje, wybór strefy, ekstrakcja punktów,
   naprawa geometrii i raport.
4. **Processing** — provider i algorytm seryjny używający tych samych usług.
5. **GUI** — prosty dialog dla aktywnej warstwy i czytelna prezentacja
   wyników oraz ostrzeżeń.
6. **Dokumentacja i pakowanie** — README, dokumentacja obliczeń, walidacji,
   podstaw prawnych, testów ręcznych i ZIP pluginu.
7. **Weryfikacja zgodności** — rzeczywiste testy QGIS 3.44.x/Qt5 i
   QGIS 4.2.x/Qt6.
8. **Deklaracja QGIS 4** — dopiero po zaliczeniu testów QGIS 4.2 ustawić
   `qgisMaximumVersion=4.99`.

Docelowe `metadata.txt` będzie zawierało co najmniej:

```ini
qgisMinimumVersion=3.44
qgisMaximumVersion=4.99
hasProcessingProvider=yes
```

Pole `supportsQt6` nie będzie używane. W okresie przed rzeczywistym testem
QGIS 4.2 maksymalna wersja pozostanie ograniczona do `3.99`.

## 6. Plan testów

### 6.1. Czysty moduł Python

- dokładność wszystkich stałych;
- wzór sprawdzany krok po kroku;
- regresja mapowania osi QGIS/geodezja;
- strefy 5, 6, 7 i 8;
- niezgodność EPSG i prefiksu Y;
- prostokąt 10 000 m² na południku osiowym, z oczekiwanym wynikiem
  `10001.53994071 m²`;
- punkty po obu stronach południka osiowego;
- usuwanie domknięcia i wykrywanie duplikatów;
- pusta lista punktów, NaN i nieskończoności;
- `ROUND_HALF_UP` do `0.0001 ha`;
- wynik diagnostyczny GRS80 nie zastępuje wyniku ustawowego.

### 6.2. Adapter geometrii

- null, empty i geometria niepoligonowa;
- geometrie pojedyncze, multipart i z otworami;
- krzywe bez cichej segmentacji;
- poprawna geometria pozostaje niezmieniona;
- `Structure`, awaryjne `Linework` i całkowite niepowodzenie naprawy;
- odrzucenie wyniku pustego, niepoligonowego lub nadal niepoprawnego;
- kompletność raportu naprawy;
- PGK pochodzi z punktów sprzed naprawy;
- ostrzeżenie o dodanych lub usuniętych wierzchołkach;
- geometria źródłowa nie zostaje zmieniona;
- osobna warstwa diagnostyczna nie zastępuje źródła.

### 6.3. Testy integracyjne QGIS

Macierz należy wykonać na rzeczywistych instalacjach:

- QGIS 3.44.x z Qt5,
- QGIS 4.2.x z Qt6.

W obu środowiskach sprawdzić:

- import, `classFactory()`, `initGui()` i `unload()`;
- rejestrację i usunięcie providera Processing;
- dialogi, enumy Qt, sygnały i sloty;
- zasoby i ikonę;
- oba warianty `makeValid()`;
- pojedyncze i seryjne przetwarzanie;
- brak zmian warstwy źródłowej;
- zawartość i interpretację `metadata.txt`.

## 7. Kryteria zakończenia projektu

- wszystkie testy przechodzą w obsługiwanych środowiskach;
- Ruff nie zgłasza błędów;
- plugin można wielokrotnie załadować i wyładować bez pozostawionych akcji
  lub providerów;
- regresja osi wykrywa każdą zamianę easting/northing;
- przykład 1 ha daje oczekiwany wynik;
- Processing obsługuje wiele obiektów i raportuje błędy per obiekt;
- geometria wejściowa nie jest modyfikowana;
- dokumentacja opisuje wzór, ograniczenia i ręczne testy obu wersji QGIS;
- zgodność z QGIS 4 jest deklarowana dopiero po rzeczywistym teście QGIS 4.2.

## 8. Założenia i ograniczenia

- Brak autorytatywnej warstwy punktów EGiB; wersja 1.0 będzie jawnie opisana
  jako tryb oparty na wierzchołkach geometrii.
- Brak autorytatywnego zbioru przypisania powiat–strefa; architektura ma
  umożliwiać późniejsze jego dodanie.
- Pierścienie wewnętrzne są traktowane jako granice geometrii i wchodzą do
  zbioru punktów, ale powodują ostrzeżenie.
- `STRICT` konserwatywnie blokuje wynik dla każdej geometrii, która wymagała
  naprawy.
- Repozytorium zachowuje istniejącą licencję GPL v2.

