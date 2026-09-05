<p align="center">
  <img src="resources/icon.svg" width="88" height="88" alt="">
</p>

# Poprawka odwzorowawcza PL-2000

Wtyczka QGIS do obliczania ustawowego pola działki ewidencyjnej
z powierzchniową poprawką odwzorowawczą w układzie PL-2000. Udostępnia
czytelny dialog dla jednej zaznaczonej działki oraz algorytm Processing do
obliczeń seryjnych.

> 🤖 **Transparentność rozwoju:** projekt powstaje z wykorzystaniem podejścia
> vibe coding. Kod, wzór, zachowanie na danych brzegowych i paczka wydaniowa
> są weryfikowane testami automatycznymi, skanerami oraz ręcznym przeglądem.

**Status:** kandydat stabilnego wydania `1.0.1`. Automatyczne testy wykonano
w QGIS 3.40.15 / Qt 5.15 na Linuksie. `metadata.txt` deklaruje QGIS
3.40–3.x; QGIS 4 nie jest jeszcze deklarowany. Przed publikacją pozostaje
ręczny test finalnego ZIP-u zgodnie z
[checklistą wydania](docs/PUBLISHING.md).

![Okno obliczenia powierzchni zaznaczonej działki w QGIS](docs/images/dialog-preview.png)

## Najważniejsze możliwości

- obliczenie `P = P₀ − ΔP₀` bez zaokrąglania wartości pośrednich;
- porównanie kartezjańskiego `P₀`, głównego wyniku prawnego `P` oraz
  niezależnego pomiaru geodezyjnego QGIS na elipsoidzie GRS 80;
- automatyczne rozpoznanie strefy dla EPSG:2176–2179;
- ręczny, jawny wybór strefy PL-2000 dla innych CRS;
- dwa tryby geometrii: kontrola GEOS bez naprawy oraz kontrola z opcjonalną
  naprawą kopii;
- pełna diagnostyka w nowej warstwie wynikowej Processing;
- brak modyfikacji warstwy wejściowej, komunikacji sieciowej i zależności
  instalowanych przez pip.

## Instalacja

### Oficjalne repozytorium QGIS

Po zatwierdzeniu wydania otwórz w QGIS **Wtyczki → Zarządzanie i instalowanie
wtyczek**, wyszukaj „Poprawka odwzorowawcza PL-2000” i wybierz
**Zainstaluj wtyczkę**.

### Kandydat wydania z ZIP

1. Pobierz ZIP dołączony do oznaczonego wydania GitHub.
2. W QGIS wybierz **Wtyczki → Zarządzanie i instalowanie wtyczek →
   Instaluj z ZIP**.
3. Wskaż archiwum i zaakceptuj instalację.

Nie instaluj przypadkowego pliku z lokalnego `dist/`. Paczka przeznaczona do
publikacji musi odpowiadać oznaczonemu commitowi i opublikowanej sumie
SHA-256.

## Użycie

### Jedna działka

1. Aktywuj warstwę Polygon lub MultiPolygon i zaznacz dokładnie jeden obiekt.
2. Uruchom **Wektor → Poprawka odwzorowawcza PL-2000 → Oblicz powierzchnię
   zaznaczonej działki** albo użyj przycisku na pasku narzędzi.
3. Dla CRS innego niż EPSG:2176–2179 wskaż właściwą strefę PL-2000.
4. Wybierz sposób obsługi geometrii i uruchom obliczenie.
5. Aby zachować raport, wybierz **Zapisz raport MD…** i wskaż plik Markdown.
   Raport zawiera wyniki, parametry wzoru, diagnostykę i ostrzeżenia oraz
   nazwę warstwy, identyfikator obiektu, CRS i wybrany tryb geometrii.
   Liczby mają taką samą liczbę miejsc po przecinku jak w oknie.

Zmiana strefy lub trybu geometrii usuwa poprzedni raport i wyłącza eksport
do ponownego obliczenia. Tak samo działa nieudane obliczenie.
Raport diagnostyczny dla błędnej geometrii można zapisać, lecz jego
ostrzeżenia pozostają widoczne w pliku. Anulowanie lub błąd zapisu nie
usuwa bieżącego wyniku; nieudany zapis nie nadpisuje istniejącego pliku.

### Wiele działek

W **Panelu Algorytmów Processingu** wyszukaj **Oblicz powierzchnię działek
EGiB**. Wskaż warstwę, strefę, sposób obsługi geometrii i docelową warstwę
wynikową.

Do zachowania pełnych nazw pól i diagnostyki używaj GeoPackage. Shapefile
ogranicza nazwy pól do 10 znaków i tekst do 254 znaków, dlatego może zmienić
schemat oraz uciąć pole `egib_warnings`.

## Tryby i ograniczenia

| Obszar | Zachowanie |
|---|---|
| Zasięg | Polska, strefy PL-2000 5–8 |
| CRS | automatycznie EPSG:2176–2179; pozostałe wymagają wyboru strefy |
| Geometria | Polygon/MultiPolygon; pierścienie krzywe są odrzucane |
| Punkty PGK | wierzchołki geometrii, nie niezależny rejestr punktów EGiB |
| Tryb domyślny | sprawdza GEOS; liczy z kopii bez naprawy; błędna geometria daje wynik diagnostyczny |
| Tryb naprawy | sprawdza GEOS i może naprawić kopię; pole i PGK pochodzą z poprawionej kopii |
| Limity | 10 000 części, 50 000 pierścieni, 500 000 współrzędnych |
| Wynik seryjny | nowa warstwa; źródło pozostaje bez zmian |

W obu trybach najpierw transformowana jest kopia całego poligonu do
PL-2000, następnie sprawdzana jest jej poprawność. W trybie bez naprawy
`P₀` i `P_GK` pochodzą z tych samych niezmienionych granic po transformacji.
W trybie naprawy obie wartości pochodzą z poprawionej kopii, łącznie
z dodanymi i usuniętymi wierzchołkami. Średnia obejmuje unikalne pary XY
ze wszystkich pierścieni i części; techniczne zamknięcie pierścienia nie
jest dodatkowym punktem. Nie używamy centroidu powierzchniowego ani
transformacji średniej obliczonej w źródłowym CRS.

Wynik dla niepoprawnej geometrii bez naprawy ma wyraźne ostrzeżenie
w raporcie i status `invalid_source_geometry` w Processing. Jest wyłącznie
diagnostyczny. Geometrie puste, krzywe, nieskończone współrzędne i wyniki
niedodatnie nadal są odrzucane. Naprawa GEOS nie potwierdza zgodności
wygenerowanych punktów z dokumentacją granic działki.

`P₀` jest polem matematycznym (kartezjańskim), które QGIS oblicza metodą
`QgsGeometry.area()` w płaskim układzie PL-2000. Nie uwzględnia ono
krzywizny Ziemi; funkcja wyrażeniowa `area(geometry)` również zawsze liczy
planarnie. Głównym wynikiem wtyczki pozostaje `P = P₀ − ΔP₀` oraz `P`
w hektarach, obliczone według przepisów EGiB.

Dodatkowe pole geodezyjne QGIS jest mierzone przez
`QgsDistanceArea.measureArea()` bezpośrednio na elipsoidzie GRS 80. Stanowi
wartość porównawczą, a nie zamiennik wyniku według rozporządzenia. Może
nieznacznie różnić się od `P`, ponieważ oba wyniki powstają innymi metodami.
Odpowiada rodzajowi pomiaru wyrażenia `$area` przy ustawionej elipsoidzie,
lecz wtyczka jawnie ustawia GRS 80 niezależnie od ustawień projektu.
W algorytmie Processing wartości te zapisują odpowiednio pola
`egib_po_m2`, `egib_area_m2` i `egib_qgis_m2`.

Jeśli pomocniczy pomiar QGIS jest niedostępny, wynik według wzoru PL-2000
pozostaje dostępny. Raport pokazuje „Niedostępne” i ostrzeżenie. Processing
zachowuje wynik oraz status geometrii, zapisuje `NULL` w `egib_qgis_m2`
i dodaje `geodesic_measurement_failed` do `egib_warnings`; przetwarza
również kolejne obiekty.

Wynik nie zastępuje kontroli właściwego CRS, strefy, pochodzenia punktów
granicznych ani aktualnego stanu prawnego. Szczegóły opisuje
[podstawa prawna](docs/LEGAL_BASIS.md).

## Prywatność i bezpieczeństwo

Wtyczka przetwarza geometrię lokalnie w pamięci QGIS. Nie wykonuje zapytań
sieciowych, nie wymaga konta ani usług zewnętrznych i nie przechowuje
poświadczeń. Transformacja oraz naprawa działają na kopiach geometrii.

Błędy funkcjonalne zgłaszaj przez
[Issues](https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/issues).
Podatności zgłaszaj prywatnie zgodnie z [SECURITY.md](SECURITY.md).

## Rozwój i walidacja

Instrukcje przygotowania środowiska, konwencję gałęzi i wymagania pull
requestów opisuje [CONTRIBUTING.md](CONTRIBUTING.md). Minimalny zestaw
kontroli:

```bash
ruff check --no-cache .
ruff format --check --no-cache .
flake8 . --exclude=legacy,__pycache__ --jobs 1
bandit -r __init__.py compat.py plugin.py user_messages.py \
  adapters core gui processing_provider scripts
pytest -p no:cacheprovider
python scripts/build_plugin_zip.py
```

Kod runtime korzysta wyłącznie z biblioteki standardowej Python i API QGIS.
Plik `requirements-dev.txt` zawiera tylko narzędzia deweloperskie.

## Projekt

- [Changelog](CHANGELOG.md)
- [Publikacja wydania krok po kroku](docs/PUBLISHING.md)
- [Polityka bezpieczeństwa](SECURITY.md)
- [Raport walidacji wydania](docs/RELEASE_VALIDATION.md)
- [Audyt bezpieczeństwa i jakości](docs/SECURITY_AUDIT_2026-07-24.md)
- [Licencja GNU GPL v2](LICENSE)

Autor i opiekun: [Jarosław Sadowski](https://github.com/jaroslaw-sadowski).
Projekt jest aktywnie utrzymywany.
