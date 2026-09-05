# Współtworzenie

Dziękuję za zainteresowanie projektem. Mile widziane są małe, dobrze
uzasadnione poprawki, które zachowują audytowalność obliczeń i zgodność
z QGIS.

## Zanim zaczniesz

- Błędy i propozycje opisuj najpierw w issue.
- Podatności zgłaszaj zgodnie z [SECURITY.md](SECURITY.md), nigdy publicznie.
- Nie dołączaj danych produkcyjnych, projektów zawierających dane osobowe,
  poświadczeń ani lokalnych konfiguracji.
- Zmiana wzoru, stałych, osi, strefy, PGK lub zaokrąglania wymaga wskazania
  podstawy prawnej oraz nowych testów referencyjnych.

## Praca lokalna

Sklonuj repozytorium do katalogu będącego poprawną nazwą pakietu Python:

```bash
git clone \
  https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza.git \
  qgis_poprawka_odwzorowawcza
cd qgis_poprawka_odwzorowawcza
```

Narzędzia deweloperskie są odseparowane od zależności runtime:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Testy wymagające PyQGIS uruchamiaj interpreterem środowiska QGIS. Przykład
dla typowej instalacji linuksowej:

```bash
QT_QPA_PLATFORM=offscreen \
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/usr/lib/python3/dist-packages \
pytest -p no:cacheprovider
```

Pełny zestaw uruchamiaj zarówno w QGIS 3/Qt5, jak i QGIS 4/Qt6.
Workflow Quality wykonuje go w oficjalnych obrazach QGIS 3.44.11 i 4.2.2,
przypiętych do konkretnych digestów. Obrazy zawierają już PyQGIS i pytest.
W instalacji poza `/usr` ustaw `QGIS_PREFIX_PATH` na jej katalog główny
oraz `PYTHONPATH` na jej moduły PyQGIS. Nie mieszaj bibliotek QGIS 3 i 4.

Kontrole niezależne od QGIS:

```bash
ruff check --no-cache .
ruff format --check --no-cache .
flake8 . --exclude=legacy,__pycache__ --jobs 1
bandit -r __init__.py compat.py plugin.py user_messages.py \
  adapters core gui processing_provider scripts
git ls-files -z | \
  xargs -0 detect-secrets-hook --baseline .secrets.baseline
pytest -p no:cacheprovider tests/unit
python scripts/build_plugin_zip.py
```

## Gałęzie, commity i pull requesty

- Używaj krótkotrwałych gałęzi `feature/...`, `fix/...`, `docs/...` lub
  `chore/...`.
- Stosuj angielskie komunikaty Conventional Commits w trybie rozkazującym,
  np. `fix: reject oversized geometries before transform`.
- Nie commituj ZIP, cache, środowisk wirtualnych ani wygenerowanych plików.
- Pull request powinien mieć jeden cel, testy proporcjonalne do ryzyka
  i opis wpływu na dane użytkownika.
- Nie zmieniaj `legacy/pow_QGIS_v1.py`; jest archiwalnym materiałem
  referencyjnym i nie trafia do paczki.

Przed wysłaniem zmian upewnij się, że pełny zestaw testów i skanerów
przechodzi w obsługiwanym środowisku QGIS.
