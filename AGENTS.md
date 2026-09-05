# Instrukcje dla agentów AI

## Rozpoczęcie i wznowienie pracy

- Przeczytaj [stan prac](.agents/STATE.md), następnie sprawdź `git status`
  i ostatnie commity. Stan jest migawką, a aktualne pliki mają pierwszeństwo.
- Komunikuj się z użytkownikiem po polsku, krótko i prostym językiem.
- Przed zmianami przeanalizuj istniejący kod. Najpierw sprawdź potrzebę
  funkcji, istniejące rozwiązanie, natywne API i obecne zależności.
- Wybieraj minimalne zmiany. Nie dodawaj bibliotek, warstw ani własnych
  helperów, jeśli wystarcza obecny kod lub API QGIS.
- Zachowuj niezwiązane zmiany użytkownika. Commit, push i publikację
  wykonuj zgodnie z zakresem bieżącego polecenia; samo wznowienie sesji
  nie oznacza zlecenia publikacji przygotowanego wydania.

## Zasady projektu

- Nazwa publiczna: **Poprawka odwzorowawcza PL-2000**. Menu **Wtyczki**,
  bez zbędnych podmenu; ta sama nazwa w Processing i paczce ZIP.
- Polski interfejs. Opisy PL/EN i tematyczne tagi w parach PL/EN.
  `README.md` i `README.en.md` są krótką dokumentacją dla użytkowników,
  a nie miejscem na pamięć sesji lub instrukcje dla agentów.
- Kod obliczeń: `core/`; integracja i geometria: `adapters/`; GUI: `gui/`;
  przetwarzanie seryjne: `processing_provider/`. Używaj `qgis.PyQt`.
- Zachowaj identyfikatory `egib_area:calculate_egib_area` i pola `egib_*`
  używane przez istniejące modele i dane.
- Dane źródłowe są niemodyfikowalne. Brak komunikacji sieciowej w runtime;
  wyłącznie biblioteki QGIS i standardowego Pythona.
- Zmiana wzoru, osi, stref, P_GK, doboru geometrii lub zaokrągleń wymaga
  sprawdzenia [podstawy prawnej](docs/LEGAL_BASIS.md) i niezależnych
  [referencji](docs/CALCULATION_VALIDATION_2026-09-05.md). Nie osłabiaj
  tolerancji testów, aby ukryć różnicę wyników.

## Weryfikacja i zakończenie

- Korzystaj z komend w [CONTRIBUTING.md](CONTRIBUTING.md) i istniejącego
  workflow `.github/workflows/quality.yml`. Narzędzia są przypięte w
  `requirements-dev.txt`, Ruff skonfigurowany w `pyproject.toml`.
- Sprawdzaj Flake8, Ruff lint i formatowanie. Wyjątki `N802` dotyczą
  nazw wymaganych przez QGIS/Qt, a `N999` nazwy katalogu repozytorium.
- Zmiany runtime weryfikuj w obu generacjach QGIS, odpowiednimi testami.
  Sam checker Qt6 nie zastępuje rzeczywistego uruchomienia QGIS 4.
- ZIP buduj przez `scripts/build_plugin_zip.py` z jawnego manifestu;
  materiały agentów i narzędzia developerskie nie należą do runtime.
- Przed wydaniem stosuj [PUBLISHING.md](docs/PUBLISHING.md). Nie przypisuj
  wynikom lokalnym statusu testów CI, certyfikacji ani testów Windows/macOS.
- Po istotnej sesji uaktualnij `.agents/STATE.md`: faktyczny stan, wyniki,
  decyzje i pozostałe kroki. Unikaj kopiowania całego raportu lub rozmowy.
