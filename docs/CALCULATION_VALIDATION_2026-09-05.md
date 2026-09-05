# Walidacja obliczeń — punkt 1, 2026-09-05

Zakres: kontrola geometrii w obu trybach, spójne źródło pola P₀ i punktu
P_GK, wzór poprawki, osie, strefy, transformacje, zaokrąglanie oraz zapis
parametrów. Baza: commit `80b7994` (wersja 1.0.1). Zmiany są przygotowane
do osobnego commita; nie obejmują punktu 2 (obsługi awarii pomiaru
porównawczego i nieaktualnego raportu), nazw narzędzi, tłumaczeń ani eksportu.

## Podstawa i założenia

Źródło wzoru: [Dz.U. 2024 poz. 219, załącznik nr 3, strona 28](https://eli.gov.pl/api/acts/DU/2024/219/text.pdf).
Sprawdzono także § 16 ust. 2 oraz nowelizacje 2024/1954 i 2026/1094;
nie zmieniają badanej formuły. Pełne odnośniki i rozdzielenie wymogów
prawnych od konwencji aplikacji znajdują się w [LEGAL_BASIS.md](LEGAL_BASIS.md).

Wzór pozostaje P = P₀ − P₀(m² − 1). Nie zastępujemy go P₀/m² ani
pomiarem elipsoidalnym QGIS. Wszystkie współrzędne we wzorze są w PL-2000.
Średnia powstaje po transformacji punktów. Po naprawie zarówno pole,
jak i średnia pochodzą z poprawionej kopii.

Tryb bez naprawy zawsze sprawdza GEOS i nigdy nie uruchamia makeValid.
Jeżeli geometria jest błędna, zachowuje ją i oznacza wynik jako
diagnostyczny (`invalid_source_geometry` w Processing i wyraźny komunikat
w GUI). Nadal odrzuca przypadki uniemożliwiające obliczenie, m.in. puste
geometrie, krzywe, nieskończone współrzędne i niedodatnie pole.

## Niezależne wartości oczekiwane

`tests/reference/pl2000_reference.json` zawiera stałe dane syntetyczne
oraz wartości pośrednie. Nie są to dane produkcyjne ani urzędowe wzorce
pomiarowe. Ich generator korzysta wyłącznie z biblioteki standardowej:

- pole oblicza wzorem Gaussa (shoelace) na dokładnych ułamkach;
- współczynniki przepisano z załącznika, bez importowania stałych wtyczki;
- wszystkie działania aż do zapisu dziesiętnego wykonuje `Fraction`;
- regułę zaokrąglenia do 1 m², czyli 0,0001 ha, realizuje rachunek całkowity;
- nie importuje QGIS, GEOS, PROJ ani żadnego modułu produkcyjnego wtyczki.

Przykłady referencyjne:

| Przypadek | P₀ [m²] | P_GK X [m] | P_GK Y [m] | P [ha] |
|---|---:|---:|---:|---:|
| Kwadrat na południku osiowym | 10000 | 5800000 | 7500000 | 1.0002 |
| Niesymetryczna działka na wschód od osi | 47500 | 5800100 | 7600112.5 | 4.7496 |
| Zachód od osi, współrzędne centymetrowe | 8701.91745 | 5450039.5025 | 5400055.8925 | 0.8701 |
| Wielopoligon z otworem | 122200 | 5850193.636363… | 6625243.636363… | 12.2172 |
| Mały poligon, współrzędne milimetrowe | 0.0253335 | 6000000.10175 | 8500000.0645 | 0.0000 |
| Samoprzecięcie, wynik źródłowy diagnostyczny | 10000 | 5800100 | 7500075 | 1.0002 |
| To samo samoprzecięcie po naprawie | 50000/3 | 5800000 + 280/3 | 7500000 + 220/3 | 1.6669 |

Ostatnie dwa przykłady odróżniają stary i nowy sposób wyznaczania P_GK.
Punkt przecięcia dwóch odcinków ma lokalne współrzędne (200/3, 200/3).
Jest wspólny dla dwóch naprawionych trójkątów, ale w średniej występuje raz.
Osobny test sprawdza usunięcie wierzchołka zapadniętego fragmentu granicy.

Odtworzenie referencji, bez nadpisywania zatwierdzonego wzorca:

```bash
python tests/reference/generate_pl2000_reference.py > /tmp/reference-check.json
cmp tests/reference/pl2000_reference.json /tmp/reference-check.json
```

Testy nigdy nie generują wartości oczekiwanych przy użyciu kodu badanego.

## Zakres testów i tolerancje

- Wszystkie parametry wzoru, surowy wynik oraz wynik po zaokrągleniu.
- Wszystkie strefy 5–8; brak wpływu samego prefiksu strefy na poprawkę.
- GUI i rzeczywisty algorytm Processing, oba tryby geometrii.
- Odwrócony kierunek pierścieni, inny punkt początkowy, powtórzone punkty,
  otwory, części wielopoligonowe i współrzędne Z/M.
- Transformacje z EPSG:2180 i 4326 do każdej strefy oraz brak zmian źródła.
- Osobny niesymetryczny przykład wykazujący, że transformacja średniej
  i centroid powierzchniowy dają inne punkty niż wymagana średnia.
- Metody Structure i Linework, brak naprawy w trybie źródłowym, nieudana
  naprawa, ochrona strefy i istniejące kontrole geometrii.
- Brak wpływu CRS projektu i jego elipsoidy na wynik wzoru.
- Ponowne otwarcie GeoPackage: zgodność wyników i pełnych parametrów
  P_GK, sigma oraz m. Test wykrył i zabezpiecza przed wcześniejszym
  ograniczeniem ich precyzji przez deklarację pól Processing.
- Dwie wartości po przeciwnych stronach progu zaokrąglenia, oddalone
  od niego o około 0,00001 m²: brak zaokrąglenia pośredniego do 0,01 m².

Testy nie polegają na domyślnej tolerancji względnej pytest. Przy
współrzędnych rzędu milionów metrów byłaby ona zbyt luźna.

| Porównanie | Tolerancja bezwzględna |
|---|---:|
| Moduł wzoru vs referencja: współrzędne i powierzchnie | 1e-8 m lub m² |
| Moduł wzoru: u, v, sigma, skala | 1e-10 w jednostce parametru |
| Pole poligonu przez QGIS vs dokładny wzór Gaussa | 1e-6 m² |
| P_GK w teście całej ścieżki | 1e-6 m |
| Pole po transformacji do innego CRS i z powrotem | 1e-4 m² |
| Wynik w hektarach | dokładna zgodność zaokrąglonej wartości |
| Parametry GUI vs Processing i ponownie otwarty GeoPackage | dokładna zgodność wartości double |

Tolerancje mierzą zgodność numeryczną programu, nie dokładność terenową
ani dokładność transformacji między realizacjami układów odniesienia.
Testy transformacji korzystają z QGIS/PROJ w obu kierunkach, więc są testami
integracji, a nie niezależną certyfikacją biblioteki PROJ lub danych WGS 84.

## Wyniki wykonania

Środowisko: Linux, QGIS 3.40.15, Qt 5.15.18, Python 3.14.4.
Bazowy zestaw przed zmianami: 105 testów.
Końcowy zestaw: **194 testy przeszły** (w tym 89 dodatkowych przypadków).
Ruff, kontrola formatowania, Flake8, Bandit, detect-secrets oraz kontrola
składni zakończyły się bez ustaleń. pip-audit nie wykrył znanych podatności
w zależnościach z requirements-dev.txt. Referencje odtworzono bajt w bajt.
Dwa buildy ZIP były identyczne; 24 pliki, poprawne sumy CRC.

Sprawdzono skuteczność testów na sześciu celowo zmienionych kopiach kodu
w katalogach tymczasowych. Wszystkie regresje zostały wykryte:

| Wprowadzony błąd | Wynik wybranych testów |
|---|---|
| P_GK z punktów sprzed naprawy | 2 nieprzechodzące testy |
| Pominięcie kontroli GEOS | 1 nieprzechodzący test |
| Zamiana osi geodezyjnych | 48 nieprzechodzących testów |
| Zastąpienie wzoru przez P₀/m² | 7 nieprzechodzących testów |
| Liczenie powtórzonych punktów wielokrotnie | 18 nieprzechodzących testów |
| Zaokrąglenie m² przed obliczeniem ha | 1 nieprzechodzący test |

Zmiany mutacyjne nie trafiły do kodu roboczego. Test zapisu GeoPackage
również najpierw wykazał utratę precyzji na starej deklaracji pól, a po
usunięciu ograniczeń sprawdza dokładną zgodność zapisanych parametrów.

Nie deklarowano zgodności z QGIS 4 i nie zmieniano zakresu wersji QGIS.
Pełne testy na QGIS 3.44, Windows i macOS należą do dalszej walidacji
wydania. Testy nie potwierdzają prawidłowości dowolnych danych granicznych
ani prawnej akceptacji punktów dodanych przez GEOS.
