# Poprawka odwzorowawcza EGiB

Wtyczka QGIS obliczająca pole powierzchni działki ewidencyjnej z poprawką
odwzorowawczą dla układu PL-2000. Udostępnia polski dialog dla jednej
zaznaczonej działki oraz algorytm Processing do obliczeń seryjnych.

## Instalacja

1. Pobierz świeżo zbudowany plik
   `qgis_poprawka_odwzorowawcza-<wersja>.zip`.
2. W QGIS wybierz **Wtyczki → Zarządzanie wtyczkami → Instaluj z ZIP**,
   wskaż archiwum i zaakceptuj instalację.
3. Włącz wtyczkę **Poprawka odwzorowawcza EGiB**, jeżeli QGIS nie zrobił
   tego automatycznie.

Nie instaluj zawartości katalogu `dist/` bez ponownego zbudowania paczki ze
źródeł przeznaczonych do publikacji i sprawdzenia jej sumy SHA-256.

## Użycie

### Jedna zaznaczona działka

1. Aktywuj warstwę poligonową i zaznacz dokładnie jeden obiekt.
2. Uruchom **Wektor → Poprawka odwzorowawcza EGiB → Oblicz powierzchnię
   zaznaczonej działki** albo użyj przycisku wtyczki na pasku narzędzi.
3. Dla CRS innego niż EPSG:2176–2179 wskaż właściwą strefę PL-2000.
4. Wybierz tryb obsługi geometrii i uruchom obliczenie.

### Wiele działek

W **Panelu Algorytmów Processingu** wyszukaj
**Oblicz powierzchnię działek EGiB**. Wskaż warstwę poligonową, strefę
PL-2000, tryb obsługi geometrii oraz miejsce zapisu nowej warstwy wynikowej.

Najważniejsze pola wyniku to: `egib_po_m2`, `egib_corr_m2`,
`egib_area_m2`, `egib_area_ha`, `egib_zone`, `egib_epsg`, `egib_pgk_x`,
`egib_pgk_y`, `egib_sigma`, `egib_scale` i `egib_status`. Pozostałe pola
opisują stan geometrii, metodę naprawy, zmiany w kopii i ostrzeżenia.

Do zachowania pełnych nazw pól i kompletnej diagnostyki zalecany jest
GeoPackage. Shapefile ogranicza nazwy pól do 10 znaków i tekst do 254
znaków, dlatego może zmienić schemat i uciąć `egib_warnings`.

## Bezpieczeństwo danych

Wtyczka nie edytuje warstwy wejściowej. Transformacja, walidacja GEOS i
opcjonalne `makeValid()` działają na kopiach geometrii. Processing zapisuje
wyniki i diagnostykę do nowej warstwy.

Domyślna opcja pomija kontrolę GEOS i oblicza pole z geometrii obiektu
źródłowego. Druga opcja wykrywa błędy, próbuje naprawić kopię geometrii i
wyraźnie oznacza obliczony na niej wynik. Warstwa źródłowa pozostaje bez
zmian w obu trybach.

Dla warstw w EPSG:2176–2179 strefa PL-2000 jest wykrywana automatycznie.
Dla pozostałych CRS użytkownik wskazuje właściwą strefę, a kopia geometrii
jest transformowana do niej w locie na potrzeby obliczenia.

## Zakres i ograniczenia

- Wtyczka jest przeznaczona do działek w Polsce i stref PL-2000 5–8
  (EPSG:2176–2179). Nie jest uniwersalnym kalkulatorem powierzchni.
- Dla innego źródłowego CRS właściwa strefa nie jest ustalana
  automatycznie; musi ją wybrać użytkownik.
- Obsługiwane są geometrie Polygon i MultiPolygon. Pierścienie krzywe są
  odrzucane, aby nie zmieniać zbioru punktów granicznych przez cichą
  segmentację.
- Obowiązują limity bezpieczeństwa: najwyżej 10 000 części, 50 000
  pierścieni i 500 000 współrzędnych geometrii. Większy obiekt jest
  odrzucany przed transformacją i operacjami GEOS.
- Punkty używane do wyznaczenia P_GK są wierzchołkami geometrii, a nie
  niezależnie potwierdzonym rejestrem punktów granicznych EGiB.
- Tryb domyślny świadomie pomija `isGeosValid()` i `makeValid()`. Tryb
  naprawy może zmienić wyłącznie kopię geometrii używaną do obliczenia
  i wyniku Processing; raport jawnie opisuje tę zmianę.
- Obliczenie nie zastępuje kontroli właściwego CRS, strefy, źródła punktów
  granicznych ani aktualnego stanu prawnego.

## Zgodność

Kod używa wyłącznie `qgis.PyQt` i deklaruje zgodność z QGIS 3.40–3.x.
Przed publikacją wydanie wymaga rzeczywistych testów instalacji, GUI,
wyładowania wtyczki i Processing na wspieranych systemach. QGIS 4/Qt6 nie
jest deklarowany w `metadata.txt`; należy go zadeklarować dopiero po teście
na rzeczywistej instalacji QGIS 4.

## Testy lokalne

```bash
QT_QPA_PLATFORM=offscreen \
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/usr/lib/python3/dist-packages \
pytest -p no:cacheprovider

ruff check --no-cache .
ruff format --check --no-cache .

bandit -r . -x ./legacy
flake8 . --exclude=legacy,__pycache__ --jobs 1
detect-secrets scan --all-files .
```

## Pakowanie ZIP

```bash
python scripts/build_plugin_zip.py
```

Archiwum powstaje w `dist/` i zawiera pojedynczy katalog
`qgis_poprawka_odwzorowawcza/` z kompletem plików uruchomieniowych, licencją
i metadanymi. Testy, materiały prawne, skrypt legacy i pliki Git nie są
dołączane do paczki instalacyjnej.

Przed wysłaniem paczki zbuduj ją ze stanu źródeł przeznaczonego do
publikacji, porównaj pliki ZIP ze źródłami, uruchom skanery na rozpakowanej
zawartości i zapisz sumę:

```bash
sha256sum dist/qgis_poprawka_odwzorowawcza-0.1.0.zip
```
