# Audyt materiałów wejściowych

## 1. Zakres i wynik audytu

Audyt wykonano przed rozpoczęciem implementacji pluginu. Obejmował:

- pełny skrypt `legacy/pow_QGIS_v1.py`,
- `docs/legal/D20240342.pdf`,
- `docs/legal/zalacznik_nr_3_egib.png`,
- aktualny układ repozytorium i historię Git,
- wymagania zgodności QGIS 3.44.x/Qt5 oraz QGIS 4.2.x/Qt6.

Najważniejszy wniosek: skrypt zawiera poprawne stałe i zasadniczą postać
wzoru, ale nie może zostać bezpośrednio przeniesiony do pluginu. Krytycznie
zamienia osie QGIS i geodezyjne, przez co błędnie wyznacza również strefę i
argumenty wzoru. Brakuje ponadto bezpiecznego wyboru strefy, walidacji i
naprawy geometrii, jednoznacznej polityki PGK, właściwego zaokrąglania,
architektury pluginu oraz testów.

## 2. Stan repozytorium

W chwili audytu repozytorium było na gałęzi `main`, zgodnej z `origin/main`,
a drzewo robocze było czyste. Śledzone były tylko:

```text
LICENSE
README.md
docs/legal/D20240342.pdf
docs/legal/zalacznik_nr_3_egib.png
legacy/pow_QGIS_v1.py
```

Nie było jeszcze:

- `metadata.txt` ani `__init__.py` z `classFactory()`;
- klasy pluginu z `initGui()` i `unload()`;
- providera Processing;
- modułu obliczeniowego niezależnego od QGIS;
- GUI pluginu;
- konfiguracji Ruff/pytest;
- testów automatycznych i instrukcji testów ręcznych.

Repozytorium zawiera pełny tekst GNU GPL w wersji 2. Nie ma potrzeby wyboru
nowej licencji. Przed publikacją trzeba natomiast umieścić poprawne dane autora
i kontakt w metadata pluginu.

README jest obecnie tylko krótkim, dwuwierszowym opisem projektu. Jego
rozbudowa należy do późniejszego etapu, nie do niniejszego audytu.

## 3. Środowisko użyte do audytu

Lokalnie dostępne środowisko:

| Składnik | Wersja |
|---|---|
| QGIS | 3.40.15-Bratislava |
| Qt | 5.15.18 |
| PyQt | 5.15.11 |
| GEOS widziany przez QGIS | 3.14.1 |
| Python uruchomiony z powłoki | 3.14.4 |

To środowisko pozwoliło sprawdzić kształt istniejącego API, lecz nie jest
żadną z dwóch wersji docelowych. Nie wykonano i nie wolno deklarować jako
wykonanych rzeczywistych testów:

- QGIS 3.44.x z Qt5,
- QGIS 4.2.x z Qt6.

Zgodność tych gałęzi musi zostać potwierdzona później na faktycznych
instalacjach.

## 4. Materiały prawne

### 4.1. Dwa odrębne źródła

Materiały w repozytorium dotyczą dwóch odrębnych aktów i pełnią różne role.

`docs/legal/zalacznik_nr_3_egib.png` przedstawia stronę 28 Dz.U. 2024
poz. 219 — załącznik nr 3 do rozporządzenia w sprawie ewidencji gruntów i
budynków. Zawiera wzór poprawki odwzorowawczej, definicję PGK, stałe i
przekształcenie współrzędnych PL-2000 do Gaussa–Krügera.

`docs/legal/D20240342.pdf` jest tekstem dotyczącym państwowego systemu
odniesień przestrzennych. Jego § 16 ust. 3 określa, że oś północna jest
oznaczana literą x, a oś wschodnia literą y. Załącznik opisujący PL-2000
potwierdza również prefiksy stref oraz to, że praktyczne granice stref
pokrywają się z granicami jednostek administracyjnych szczebla powiatowego.

Nie należy przedstawiać PDF-u Dz.U. poz. 342 jako źródła wzoru EGiB ani
obrazu Dz.U. poz. 219 jako źródła prawnej definicji osi. Dokumentacja pluginu
powinna cytować oba akty osobno.

Źródła urzędowe do dalszej dokumentacji:

- EGiB, Dz.U. 2024 poz. 219:
  <https://eli.gov.pl/api/acts/DU/2024/219/text.html>
- państwowy system odniesień przestrzennych, Dz.U. 2024 poz. 342:
  <https://eli.gov.pl/api/acts/DU/2024/342/text.html>

Przed publikacją pluginu należy ponownie sprawdzić aktualny stan prawny oraz
akty zmieniające. Materiały repozytorium są materiałami referencyjnymi, a nie
mechanizmem automatycznej aktualizacji prawa.

### 4.2. Rozbieżność nazwy pliku

W wymaganiach pierwotnych wskazano:

```text
docs/legal/zalacznik_nr_3.png
```

Faktyczny i poprawnie umieszczony plik to:

```text
docs/legal/zalacznik_nr_3_egib.png
```

Nie jest to brak materiału prawnego, lecz błąd nazwy w opisie zadania.

### 4.3. Wzór i stałe

Skrypt zachowuje zasadniczą postać wzoru:

```text
P = Po - delta_Po
delta_Po = Po * (m^2 - 1)
m = sigma * 10^-5 + 1

sigma = sigma0 + m0 * v^2 *
        (q1 + q2*u + q3*u^2 + q4*v^2)
```

Stałe w liniach 95–97 skryptu są zgodne z materiałem:

```text
m0     = 0.999923
sigma0 = -7.7
q1     = 306.752873
q2     = -0.312616
q3     = 0.006382
q4     = 0.158591
```

Dla kontrolnego przypadku:

```text
Po = 10000 m²
XGK = 5800000 m
YGK = 0 m
sigma = -7.7 cm/km
m = 0.999923
```

otrzymano:

```text
delta_Po = -1.539940710000 m²
P        = 10001.539940710000 m²
```

Znak poprawki i kolejność `P = Po - delta_Po` są w skrypcie poprawne.
Wynik całego skryptu nadal jest jednak błędny dla rzeczywistych danych ze
względu na zamianę osi i wynikające z niej błędne `XGK`, `YGK` oraz N.

## 5. Analiza skryptu legacy

### 5.1. Forma skryptu

`legacy/pow_QGIS_v1.py` jest skryptem akcji obiektu QGIS, a nie importowalnym
modułem Python. Linie 14–15 zawierają placeholdery QGIS:

```python
feature_id = [%$id%]
layer_id = '[%@layer_id%]'
```

Plik wykonuje całą pracę na poziomie globalnym, łączy pobranie danych,
transformację, obliczenia i prezentację. Nie można go bezpośrednio testować
przez `pytest`, rejestrować jako plugin ani używać jako algorytmu Processing.

Pozytywne cechy istniejącego skryptu:

- import widgetu pochodzi z `qgis.PyQt`, a nie bezpośrednio z PyQt5;
- używany jest `QgsProject.instance().transformContext()`;
- transformacja jest wykonywana na `QgsGeometry(g)`, a nie celowo na obiekcie
  źródłowym;
- sprawdzana jest geometria pusta i ogólny typ poligonowy;
- techniczne domknięcie pierścienia jest usuwane;
- pole `Po` jest polem planarnym geometrii w PL-2000;
- stałe i ogólna kolejność wzoru są czytelne.

Te elementy można zachować jako intencję, ale nie jako gotową implementację.

### 5.2. Krytyczny błąd osi

Linie 103–104 wykonują:

```python
X2000 = sum(p.x() for p in pts) / len(pts)
Y2000 = sum(p.y() for p in pts) / len(pts)
```

W geometrii QGIS po standardowej transformacji:

```text
point.x() = easting
point.y() = northing
```

W prawnej/geodezyjnej notacji PL-2000:

```text
X2000 = northing
Y2000 = easting
```

Poprawne mapowanie jest zatem odwrotne do tego w skrypcie:

```text
legal_X2000 = point.y()
legal_Y2000 = point.x()
```

Skutek błędu nie ogranicza się do zamiany etykiet w oknie. Błędne wartości
wchodzą do obliczenia strefy, `XGK`, `YGK`, `u`, `v`, `sigma`, `m` i końcowej
powierzchni. Jest to błąd blokujący migrację metodą kopiuj–wklej.

### 5.3. Błędne i ryzykowne ustalanie strefy

Skrypt ma dwa sposoby wyznaczania strefy.

1. Dla warstwy w EPSG:2176–2179 wybiera ten sam CRS. Ten krok jest właściwym
   punktem wyjścia, lecz nie weryfikuje prefiksu współrzędnej Y.
2. Dla innego CRS wybiera strefę bez pytania użytkownika na podstawie
   długości geograficznej centroidu i orientacyjnych progów 16.5°, 19.5° i
   22.5°.

Drugi sposób nie uwzględnia rzeczywistego przebiegu granic stref wzdłuż
granic powiatów, nie wymaga potwierdzenia i nie obsługuje wiarygodnie
geometrii przy granicy stref lub poza Polską.

Następnie linia 107 oblicza N z wartości nazwanej `Y2000`, która faktycznie
pochodzi z `point.y()`, czyli northing. Dla typowych danych może to zwrócić
strefę 5 niezależnie od prawdziwego EPSG. Skrypt nie porównuje N z EPSG.

W pluginie rozstrzygnięcie z EPSG oraz walidacja prefiksu Y muszą być
oddzielnymi krokami. Centroid może być co najwyżej sugestią wymagającą
potwierdzenia.

### 5.4. PGK i punkty graniczne

Funkcja `iter_rings_points()`:

- iteruje wszystkie części i wszystkie pierścienie;
- usuwa techniczny punkt domykający;
- dodaje pozostałe punkty do jednej listy.

Nie wykonuje jednak globalnej deduplikacji ani nie raportuje:

- kolejnych identycznych punktów;
- punktów powtórzonych między pierścieniami lub częściami;
- obecności otworów i wieloczęściowości;
- ewentualnego segmentowania krzywych przez konwersję geometrii.

Powtórzenia zmieniają wagi średniej arytmetycznej, a więc położenie PGK.

Najważniejsze ograniczenie pojęciowe: wierzchołek geometrii warstwy nie musi
być autorytatywnym punktem granicznym EGiB. Skrypt nie zna identyfikatorów
punktów ani ich źródła. Pierwsza wersja pluginu może obsługiwać wierzchołki,
ale musi nazwać i dokumentować to ograniczenie oraz pozostawić interfejs dla
autorytatywnej warstwy punktowej.

### 5.5. Multipart, otwory i krzywe

Multipart i pierścienie wewnętrzne są technicznie iterowane, lecz użytkownik
nie dostaje informacji o ich obecności ani o przyjętej polityce. Dla PGK ma
to znaczenie, ponieważ punkty ze wszystkich pierścieni wpływają na średnią.

Metody `asPolygon()` i `asMultiPolygon()` nie stanowią jawnej polityki dla
geometrii krzywych. Plugin nie może cicho wytwarzać dodatkowych punktów przez
segmentację, ponieważ zmieniałoby to zbiór używany do PGK.

Planowana polityka wersji 1.0:

- uwzględnić wszystkie pierwotne części i pierścienie jako granice geometrii;
- usunąć tylko techniczne domknięcia;
- deduplikować dokładne współrzędne;
- ostrzegać o multipart i otworach;
- wykryć krzywe i nie segmentować ich bez jawnego ostrzeżenia lub odmowy.

### 5.6. Poprawność i naprawa geometrii

Skrypt sprawdza tylko pustkę oraz ogólny typ. Nie wywołuje GEOS
`isGeosValid()` i nie reaguje na samoprzecięcia, błędne pierścienie czy inne
problemy topologiczne. Pole niepoprawnej geometrii może być niewiarygodne.

Wymagana implementacja musi:

- pracować na kopii;
- sprawdzać poprawność po transformacji do PL-2000;
- pozostawiać poprawną geometrię bez zmian;
- próbować `Structure`, a następnie `Linework`;
- ponownie sprawdzać typ, pustkę i poprawność;
- raportować metodę i różnice;
- liczyć `Po` z zaakceptowanego wyniku;
- nadal liczyć PGK z pierwotnego zbioru punktów.

W trybie `STRICT` każda konieczność użycia `makeValid()` będzie konserwatywnie
blokowała wynik ustawowy. W `AUTO_REPAIR` wynik będzie wyraźnie oznaczony jako
uzyskany po naprawie.

### 5.7. Pole planarne i pomiar GRS80

Linia 85 używa `g2000.area()`, co odpowiada wymaganemu planarnemu `Po`, o ile
geometria jest we właściwym PL-2000 i jest poprawna.

Linie 87–91 wyznaczają dodatkowo `QgsDistanceArea` z elipsoidą GRS80. Taka
wartość może być przydatna diagnostycznie, ale nie zastępuje obliczenia według
załącznika nr 3. Obecny komunikat prezentuje oba wyniki obok siebie bez
wystarczającego wyjaśnienia tej różnicy.

### 5.8. Zaokrąglanie i prezentacja

Funkcja `fmt()` formatuje float do trzech miejsc w m² i czterech miejsc w ha.
Nie zachowuje oddzielnie wyniku surowego i ewidencyjnego oraz polega na
standardowym zaokrąglaniu formatowania Pythona. Nie definiuje wymaganej,
nazwanej polityki dla przypadku połówkowego.

Plugin powinien:

- przechowywać surowe wartości bez zaokrągleń pośrednich;
- użyć `Decimal` i `ROUND_HALF_UP` wyłącznie na końcu;
- formatować wartość ewidencyjną dokładnie do `0.0001 ha`;
- opisać tę politykę jako decyzję aplikacji.

### 5.9. Obsługa błędów i działanie seryjne

Brakuje kontrolowanej obsługi:

- niepoprawnego lub nieokreślonego CRS;
- błędów `QgsCoordinateTransform`;
- geometrii spoza oczekiwanego obszaru;
- niezgodności strefy i prefiksu Y;
- błędów GEOS;
- anulowania Processing;
- częściowych błędów podczas przetwarzania wielu obiektów.

Skrypt obsługuje jeden obiekt wskazany przez placeholder akcji. Nie obsługuje
zaznaczenia wielu działek ani warstwy wynikowej. W algorytmie Processing błąd
jednego obiektu powinien dać status i puste pola wyniku tego obiektu, a nie
bezwarunkowo przerywać cały poprawny wsad.

## 6. Zgodność QGIS 3.44 i QGIS 4.2

### 6.1. Qt

Wszystkie przyszłe importy Qt muszą pochodzić z:

```python
from qgis.PyQt.QtCore import ...
from qgis.PyQt.QtGui import ...
from qgis.PyQt.QtWidgets import ...
```

Bezpośrednie importy `PyQt5` i `PyQt6` są zabronione. Dialogi, enumy,
sygnały, sloty i zasoby wymagają testów w obu docelowych środowiskach.

### 6.2. `QgsGeometry.makeValid()`

Dokumentacja API QGIS 3.44 udostępnia wywołanie:

```python
geometry.makeValid(method, keepCollapsed)
```

Argument `feedback` został dodany w QGIS 4.2. Wspólny kod musi pozostać przy
dwóch argumentach, dzięki czemu nie potrzebuje osobnej gałęzi wersji dla tej
operacji.

`Qgis.MakeValidMethod.Structure` i `Linework` są dostępne od QGIS 3.28, ale
`Structure` wymaga GEOS 3.10 lub nowszego. Należy przechwycić właściwy wyjątek
braku obsługi, zapisać ostrzeżenie i spróbować `Linework`.

Dokumentacja referencyjna:

- <https://api.qgis.org/api/3.44/classQgsGeometry.html>
- <https://api.qgis.org/api/classQgsGeometry.html>

### 6.3. Metadata i deklaracja zgodności

Docelowe wartości:

```ini
qgisMinimumVersion=3.44
qgisMaximumVersion=4.99
hasProcessingProvider=yes
```

`supportsQt6=True` nie będzie używane, ponieważ flaga nie jest już
rozpoznawana. Oficjalna informacja migracyjna:

<https://plugins.qgis.org/docs/migrate-qgis4>

Istnieje pozorna sprzeczność między wymaganą docelową wartością `4.99` a
zakazem deklarowania zgodności przed testem. Bezpieczna kolejność jest
następująca:

1. podczas implementacji i przed testem QGIS 4.2 ograniczyć maksimum do
   `3.99`;
2. wykonać rzeczywisty test QGIS 4.2/Qt6;
3. po zaliczeniu testu ustawić docelowe `4.99`.

## 7. Rejestr głównych ryzyk

| Priorytet | Ryzyko | Skutek | Planowane zabezpieczenie |
|---|---|---|---|
| Krytyczny | Zamiana osi | Błędny PGK, strefa i wynik | Semantyczne nazwy i test regresyjny |
| Krytyczny | Błędna strefa | Błędne YGK i poprawka | EPSG, prefiks Y, wybór użytkownika |
| Krytyczny | Niepoprawna geometria | Niewiarygodne Po | GEOS, kopia, raport i dwa tryby |
| Wysoki | Punkty z `makeValid()` użyte do PGK | Zmiana podstawy prawnej obliczenia | PGK wyłącznie sprzed naprawy |
| Wysoki | Wierzchołki uznane za punkty EGiB | Nadmierna deklaracja wiarygodności | Jawne ograniczenie i interfejs źródła |
| Wysoki | Cicha segmentacja krzywych | Sztuczne punkty i zmieniony PGK | Wykrycie i ostrzeżenie/odmowa |
| Średni | Duplikaty punktów | Przesunięcie średniej PGK | Dokładna globalna deduplikacja |
| Średni | Niejawne zaokrąglanie float | Inny zapis granicznych wartości | `Decimal`, `ROUND_HALF_UP` |
| Średni | Deklaracja QGIS 4 bez testu | Niedziałający plugin oznaczony jako zgodny | Metadata `4.99` dopiero po teście |

## 8. Ustalenia wymagające danych spoza repozytorium

Poniższe braki nie blokują zaplanowania bezpiecznej wersji 1.0, lecz muszą
pozostać jawne:

- brak autorytatywnej warstwy punktów granicznych EGiB i zasad powiązania jej
  rekordów z działką;
- brak autorytatywnego zbioru przypisania powiat–strefa;
- brak rzeczywistych środowisk testowych QGIS 3.44 i QGIS 4.2;
- brak ustalonego zestawu danych referencyjnych z urzędowo potwierdzonymi
  wynikami poza przykładem analitycznym 1 ha;
- brak zatwierdzonych treści metadata, takich jak nazwa wyświetlana, e-mail,
  wersja początkowa i opis publikacyjny.

Do czasu uzupełnienia pierwszych dwóch elementów plugin powinien działać
konserwatywnie: wymagać potwierdzenia strefy, nazywać źródło punktów i nie
przedstawiać trybu wierzchołkowego jako równoważnego autorytatywnym punktom
EGiB.

## 9. Rekomendacja

Nie należy poprawiać skryptu legacy fragment po fragmencie. Zalecana jest
migracja jego poprawnych elementów matematycznych do nowego, czystego modułu
domenowego oraz napisanie cienkiego adaptera PyQGIS. Pierwszym etapem
implementacji powinny być modele, wzór i test regresyjny osi; dopiero po ich
ustabilizowaniu należy dodać geometrię, Processing i GUI.

Szczegółowa kolejność prac i docelowa struktura znajdują się w
[`PLAN.md`](../PLAN.md).
