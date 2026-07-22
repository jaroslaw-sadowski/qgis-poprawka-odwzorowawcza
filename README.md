# Poprawka odwzorowawcza EGiB

Wtyczka QGIS obliczająca pole powierzchni działki ewidencyjnej z poprawką
odwzorowawczą dla układu PL-2000. Udostępnia polski dialog dla jednej
zaznaczonej działki oraz algorytm Processing do obliczeń seryjnych.

## Bezpieczeństwo danych

Wtyczka nie edytuje warstwy wejściowej. Transformacja, walidacja GEOS i
opcjonalne `makeValid()` działają na kopiach geometrii. Processing zapisuje
wyniki i diagnostykę do nowej warstwy.

Domyślny tryb `STRICT` blokuje wynik ustawowy, jeżeli geometria wymagała
naprawy. `AUTO_REPAIR` jest świadomym wyborem użytkownika i wyraźnie oznacza
wynik obliczony z naprawionej kopii.

## Zgodność

Kod jest przygotowany dla QGIS 3.44.x/Qt5 oraz QGIS 4.2.x/Qt6 i używa
wyłącznie `qgis.PyQt`. Do czasu rzeczywistego testu w QGIS 4.2 plik
`metadata.txt` celowo ogranicza deklarowaną zgodność do QGIS 3.x.

## Testy lokalne

```bash
QT_QPA_PLATFORM=offscreen \
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/usr/lib/python3/dist-packages \
pytest -p no:cacheprovider

ruff check --no-cache .
ruff format --check --no-cache .
```

## Pakowanie ZIP

```bash
python scripts/build_plugin_zip.py
```

Archiwum powstaje w `dist/` i zawiera pojedynczy katalog
`qgis_poprawka_odwzorowawcza/` z kompletem plików uruchomieniowych, licencją
i metadanymi. Testy, materiały prawne, skrypt legacy i pliki Git nie są
dołączane do paczki instalacyjnej.
