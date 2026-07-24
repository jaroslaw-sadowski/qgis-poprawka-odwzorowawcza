# Audyt bezpieczeństwa i jakości wtyczki QGIS

> Raport punktowy dla commitu wskazanego poniżej. Wdrożenie rekomendacji
> i aktualny stan kandydata wydania opisuje `RELEASE_VALIDATION.md`.

Data audytu: 2026-07-24  
Audytowany commit: `5310cd4` (`main`, zgodny z `origin/main`)  
Zakres: cały katalog projektu, w tym pliki śledzone, lokalne artefakty
`dist/`, testy, dokumentacja i historia 14 commitów. Kod i pozostałe pliki
projektu nie zostały zmodyfikowane.

## Podsumowanie

W kodzie uruchomieniowym nie znaleziono podatności krytycznych ani wysokich.
W szczególności nie ma wykonywania kodu lub poleceń systemowych, SQL,
komunikacji sieciowej, obsługi poświadczeń ani niebezpiecznej deserializacji.
Wtyczka nie edytuje geometrii źródłowej, poprawnie kopiuje ją przed
transformacją i naprawą, ucieka dane umieszczane w HTML oraz sprząta własną
akcję i provider Processing.

Ocena liczby ustaleń:

| Poziom | Liczba | Charakter |
|---|---:|---|
| Krytyczny | 0 | brak |
| Wysoki | 0 | brak |
| Średni | 5 | 2 bezpieczeństwo/stabilność, 3 publikacja i integralność danych |
| Niski | 2 | przenośność testów i utrzymywalność |

Najważniejsze ryzyka to brak limitu złożoności geometrii, możliwość
niezamierzonego dołączenia do ZIP pliku lub dowiązania symbolicznego,
nieaktualny lokalny ZIP wydaniowy, niezgodne z wymaganiami QGIS polskie
metadane publikacyjne oraz utrata nazw lub części diagnostyki przy eksporcie
do Shapefile.

Ocena końcowa: **gotowa po poprawkach**.

### Zakres pewności i ograniczenia

- Skanery uruchomiono z tymczasowego, izolowanego środowiska poza paczką
  wtyczki: Bandit 1.9.4, Flake8 7.3.0, detect-secrets 1.5.0,
  pip-audit 2.10.1, pytest 9.1.1 i Ruff 0.16.0. Instalacja tych narzędzi nie
  dodała zależności do projektu ani do ZIP.
- Oprócz automatyki wykonano ręczną analizę przepływu danych, parsowanie AST
  31 utrzymywanych plików Python, kontrole archiwum, skan historii i testy
  dymne. Wyników narzędzi nie traktowano jako pełnego audytu.
- Pełny zestaw 90 przypadków `pytest` przeszedł w QGIS 3.40.15 na Linuksie.
- Test dymny providera i obliczenia wykonano w QGIS 3.40.15 na Linuksie.
  Nie przeprowadzono w tym audycie testów na Windows, macOS, QGIS 3.44 ani
  QGIS 4.2.
- `detect-secrets` sprawdził wszystkie pliki bieżącego katalogu oraz osobno
  zawartość świeżego ZIP. Historia 14 commitów pozostała objęta ręcznym
  skanem wzorców wysokiej pewności, ponieważ zwykłe `detect-secrets scan`
  nie analizuje historii Git.
- `pip-audit` nie ma manifestu zależności projektu do sprawdzenia. Jego wynik
  dla współdzielonego środowiska Python opisano oddzielnie i nie przypisano
  go wtyczce, która tych pakietów nie deklaruje ani nie dystrybuuje.
- Plik `legacy/pow_QGIS_v1.py` zawiera składnię szablonu akcji QGIS
  (`[%...%]`), więc celowo nie jest poprawnym samodzielnym modułem Python.
  Nie trafia do paczki wtyczki.

## Znalezione problemy

### M-01. Brak limitu złożoności geometrii może zablokować QGIS

- **Poziom ryzyka:** średni — dostępność i stabilność aplikacji.
- **Miejsce:**
  - `plugin.py:86-93`;
  - `gui/dialog.py:606-640`;
  - `adapters/geometry.py:103-149`;
  - `adapters/repair.py:104-114`, `adapters/repair.py:132-189`;
  - `processing_provider/area_algorithm.py:222-237`,
    `processing_provider/area_algorithm.py:268-299`.
- **Opis podatności:** lista wszystkich zaznaczonych obiektów jest
  materializowana tylko po to, aby sprawdzić, czy wybrano jeden obiekt.
  Następnie wszystkie punkty graniczne są materializowane w krotce, a drugi
  pełny zbiór współrzędnych trafia do `frozenset`. W trybie naprawy GEOS
  wykonuje ponadto `isGeosValid()` i do dwóch prób `makeValid()`. Nie ma limitu
  liczby części, pierścieni, wierzchołków ani budżetu czasu/pamięci.
  Obliczenie z dialogu jest wykonywane synchronicznie w wątku GUI.
- **Przepływ niezaufanych danych:** geometria z warstwy/projektu QGIS →
  `prepare_geometry()` → transformacja → pełna ekstrakcja punktów i snapshot
  → GEOS → obliczenie i HTML. Dane przestrzenne mogą pochodzić z obcego pliku,
  usługi lub projektu.
- **Możliwy scenariusz ataku:** użytkownik otwiera otrzymany projekt lub
  warstwę z poligonem zawierającym miliony wierzchołków, zaznacza obiekt
  i uruchamia wtyczkę. Wielokrotne kopie i zbiory współrzędnych wyczerpują
  pamięć lub blokują interfejs. W Processing anulowanie jest sprawdzane tylko
  między obiektami, więc jedna skrajnie złożona geometria pozostaje
  nieprzerywalna.
- **Wpływ:** długie zamrożenie lub zakończenie QGIS, a w konsekwencji możliwa
  utrata niezapisanych zmian w projekcie. Nie stwierdzono drogi do wykonania
  kodu.
- **Rekomendacja:**
  1. użyć `selectedFeatureCount()` zamiast materializacji całej selekcji;
  2. przed transformacją i GEOS wprowadzić udokumentowany limit części,
     pierścieni i współrzędnych;
  3. zaoferować świadome potwierdzenie dla geometrii ponad próg ostrzegawczy;
  4. dla ciężkiej pracy GUI rozważyć `QgsTask`, przekazując do niego wyłącznie
     wcześniej skopiowane dane, nigdy obiekty GUI ani `QgsVectorLayer`;
  5. dodać testy graniczne i pomiar pamięci/czasu.
- **Bezpieczny przykład:**

  ```python
  MAX_BOUNDARY_COORDINATES = 500_000


  def validate_geometry_budget(geometry: QgsGeometry) -> None:
      abstract_geometry = geometry.constGet()
      coordinate_count = abstract_geometry.nCoordinates()
      if coordinate_count > MAX_BOUNDARY_COORDINATES:
          raise GeometryInputError(
              "geometry exceeds the supported coordinate limit: "
              f"{coordinate_count} > {MAX_BOUNDARY_COORDINATES}"
          )
  ```

  W `plugin.run()`:

  ```python
  if layer.selectedFeatureCount() != 1:
      self._warn("Zaznacz dokładnie jedną działkę na aktywnej warstwie.")
      return
  selected_feature = next(layer.getSelectedFeatures())
  ```

- **Podstawa oceny:** OWASP zaleca walidację zakresów, długości i rozmiaru
  wszystkich danych wejściowych. PyQGIS wskazuje `QgsTask` jako mechanizm
  utrzymania responsywności przy ciężkiej pracy i wymaga kopiowania danych
  przed przekazaniem ich do tła:
  - <https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html>
  - <https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/tasks.html>
- **Pewność:** wysoka co do braku limitów i synchronicznego GUI; czas
  potrzebny do wywołania DoS zależy od wersji GEOS, pamięci i danych.

### M-02. Budowniczy ZIP może spakować nieśledzony plik lub dereferencjonować dowiązanie

- **Poziom ryzyka:** średni — bezpieczeństwo łańcucha wydawniczego i poufność.
- **Miejsce:** `scripts/build_plugin_zip.py:42-61`,
  `scripts/build_plugin_zip.py:67-77`, `scripts/build_plugin_zip.py:90-99`.
- **Opis podatności:** `runtime_files()` dołącza każdy plik znaleziony przez
  `rglob("*")` w pięciu katalogach uruchomieniowych. Nie wymaga, aby plik był
  śledzony przez Git, nie stosuje listy dozwolonych rozszerzeń i nie odrzuca
  dowiązań symbolicznych. `Path.is_file()` podąża za dowiązaniem, a
  `read_bytes()` zapisuje zawartość celu jako zwykły plik ZIP.
- **Możliwy scenariusz ataku:** złośliwa zmiana w checkoutcie, skrypt
  przygotowujący CI albo pomyłka dewelopera tworzy
  `resources/diagnostic.txt` jako dowiązanie do pliku z kluczem lub tokenem.
  Budowniczy bez ostrzeżenia umieszcza zawartość celu w publicznej paczce.
  Prostszy wariant to przypadkowy nieśledzony plik z danymi w jednym
  z katalogów rekurencyjnych.
- **Wpływ:** publikacja sekretu lub prywatnego pliku, dołączenie
  nieprzejrzanego kodu/zasobu albo wynik blokujący skan QGIS.
- **Stan bieżący:** w audytowanym drzewie nie ma żadnych dowiązań
  symbolicznych, a zbudowana paczka zawiera wyłącznie oczekiwane 20 plików.
  Jest to podatność latentna procesu budowy, nie dowód obecnego wycieku.
- **Rekomendacja:** utrzymywać jawny manifest plików albo przynajmniej
  dozwolone rozszerzenia, odrzucać dowiązania i po `resolve(strict=True)`
  sprawdzać przynależność do `source_root`. W CI budować z czystego checkoutu
  i skanować dokładnie powstałe archiwum.
- **Bezpieczny przykład:**

  ```python
  def validated_runtime_file(source_root: Path, candidate: Path) -> Path:
      if candidate.is_symlink():
          raise ValueError(f"runtime symlink is not allowed: {candidate}")

      resolved_root = source_root.resolve(strict=True)
      resolved_candidate = candidate.resolve(strict=True)
      try:
          resolved_candidate.relative_to(resolved_root)
      except ValueError as error:
          raise ValueError(
              f"runtime file escapes source root: {candidate}"
          ) from error

      if not resolved_candidate.is_file():
          raise ValueError(f"runtime entry is not a regular file: {candidate}")
      return resolved_candidate
  ```

- **Podstawa oceny:** zasada walidacji ścieżek i allowlist OWASP oraz kontrola
  podejrzanych plików wykonywana przez QGIS:
  - <https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html>
  - <https://plugins.qgis.org/docs/security-scanning/tools>
- **Pewność:** wysoka. Potencjalny false positive dotyczy wyłącznie
  prawdopodobieństwa pojawienia się takiego pliku; zachowanie kodu jest
  jednoznaczne.

### M-03. Lokalny ZIP wydaniowy jest nieaktualny względem źródła

- **Poziom ryzyka:** średni — integralność wydania i możliwość odrzucenia
  publikacji.
- **Miejsce:** `dist/qgis_poprawka_odwzorowawcza-0.1.0.zip`
  (plik binarny, numery linii nie mają zastosowania), `.gitignore:4`,
  `scripts/build_plugin_zip.py:64-78`.
- **Opis:** istniejący ZIP jest poprawny strukturalnie, ale nie odpowiada
  bieżącemu commitowi. Ma 31 008 B i SHA-256
  `f97adf5953bb28b571982a45e08bfd4eb79eda075185a2523901be8e03183256`.
  Świeża deterministyczna kompilacja ma 40 223 B i SHA-256
  `e34b90bc0d8fede633cdf3500e4b1c1fb30322088ad5a23406b374b5a068d486`.
  Różnią się:

  | Plik | Bieżące źródło | Lokalny ZIP |
  |---|---:|---:|
  | `README.md` | 1 697 B | 1 420 B |
  | `adapters/repair.py` | 10 141 B | 9 731 B |
  | `gui/dialog.py` | 52 102 B | 12 884 B |
  | `processing_provider/area_algorithm.py` | 17 077 B | 16 401 B |
  | `resources/icon.svg` | 716 B | 524 B |

- **Możliwy scenariusz ataku/błędu:** nie jest potrzebny napastnik. Autor
  wybiera istniejący plik z `dist/` podczas publikacji i udostępnia starszy
  kod niż kod wskazany w publicznym repozytorium. W scenariuszu
  supply-chain audyt dotyczy innego źródła niż faktycznie publikowany plik.
- **Wpływ:** użytkownicy otrzymują starszą funkcjonalność, ustalenia audytu
  nie opisują dokładnie paczki, a ręczna kontrola QGIS może zakwestionować
  zgodność ZIP z repozytorium.
- **Rekomendacja:** nie publikować istniejącego ZIP. Zbudować nowy artefakt
  z czystego i oznaczonego commitu, zapisać SHA-256, porównać każdy plik
  archiwum ze źródłem i dopiero wtedy przesłać go do QGIS. W CI artefakt
  powinien być tworzony od zera, a nie ponownie używany z `dist/`.
- **Podstawa oceny:** QGIS zaleca, aby źródło przesłane w ZIP było identyczne
  ze źródłem w repozytorium:
  <https://plugins.qgis.org/docs/publish/>.
- **Pewność:** wysoka; różnice potwierdzono porównaniem bajtowym.

### M-04. Metadane publikacyjne nie zawierają wymaganego angielskiego opisu i ograniczeń

- **Poziom ryzyka:** średni — zgodność z QGIS Plugin Repository.
- **Miejsce:** `metadata.txt:3-4`, `README.md:1-26`.
- **Opis:** pola `description` i `about` są wyłącznie po polsku. Oficjalne
  zasady wymagają krótkiego angielskiego opisu. Metadane nie informują też
  wprost o istotnych ograniczeniach: zakres PL-2000/Polska, wymagany ręczny
  wybór strefy dla innych CRS, odrzucanie krzywych oraz świadome pomijanie
  GEOS w trybie domyślnym. README opisuje część zasad, ale nie podaje prostych
  instrukcji instalacji i uruchomienia z menu oraz Processing.
- **Możliwy scenariusz ataku/błędu:** brak realistycznego scenariusza ataku.
  Recenzent odrzuca wtyczkę albo użytkownik spoza polskiego kontekstu
  instaluje ją bez zrozumienia ograniczeń i interpretuje wynik jako
  uniwersalny.
- **Wpływ:** możliwa blokada ręcznego zatwierdzenia, gorsza
  interpretowalność wyników i zwiększone ryzyko błędnego użycia.
- **Rekomendacja:** dodać zwięzły angielski `description` i angielski lub
  dwujęzyczny `about` bez HTML. W `about` oraz README opisać ograniczenia,
  wejście, oba tryby geometrii, strefy, pola wynikowe i zalecany format
  zapisu. Polski interfejs może pozostać bez zmian.
- **Przykład metadanych:**

  ```ini
  description=Calculates statutory cadastral parcel area with the PL-2000 projection correction.
  about=Calculates corrected parcel areas for Poland in PL-2000 zones 5-8. For other source CRS values, the user must select the correct target zone. Curved polygon rings are rejected. Source geometry is never modified.
  ```

- **Podstawa oceny:**
  - wymaganie krótkiego angielskiego opisu i ujawniania ograniczeń:
    <https://plugins.qgis.org/docs/publish/>;
  - format i pola UTF-8 `metadata.txt`:
    <https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/plugins.html>.
- **Pewność:** wysoka dla braku angielskiego opisu. Ocena, czy obecny README
  spełnia próg „minimalnej dokumentacji”, zależy od recenzenta.

### M-05. Schemat wynikowy nie jest przenośny do Shapefile

- **Poziom ryzyka:** średni — integralność i audytowalność danych wynikowych;
  nie jest to podatność wykonania kodu.
- **Miejsce:** `processing_provider/area_algorithm.py:95-122`,
  `processing_provider/area_algorithm.py:338-397`.
- **Opis:** 19 z 26 nazw pól wynikowych ma więcej niż 10 znaków, a
  `egib_warnings` deklaruje długość 2000. Test dymny z wyjściem `.shp`
  w QGIS 3.40/GDAL potwierdził zmianę nazw, np.
  `egib_area_m2` → `egib_area_`,
  `egib_area_ha` → `egib_are_1`,
  `egib_repaired_area_m2` → `egib_rep_4`.
  Pole `egib_warnings` zostało zmienione na `egib_warni` i skrócone do
  254 znaków.
- **Możliwy scenariusz ataku/błędu:** brak potrzebnego napastnika.
  Użytkownik wybiera popularny format Shapefile. Skrypt dalszego
  przetwarzania oczekujący nazw zadeklarowanych przez algorytm przestaje
  działać, a dłuższe uzasadnienie błędu lub naprawy może zostać ucięte.
- **Wpływ:** niejednoznaczne mapowanie pól, utrata części diagnostyki i słabszy
  ślad audytowy obliczenia.
- **Rekomendacja:** wybrać i udokumentować jedną z polityk:
  1. zastosować stabilne, unikalne nazwy do 10 znaków i krótsze kody
     diagnostyczne;
  2. jawnie wymagać/rekomendować GeoPackage dla pełnego raportu, a przy
     Shapefile zgłaszać ostrzeżenie o zmianie schematu;
  3. zapisywać rozbudowany raport do osobnej tabeli/pliku i pozostawić
     w warstwie krótki kod;
  4. dodać testy integracyjne co najmniej dla pamięci, GeoPackage i Shapefile.
- **Podstawa oceny:** dokumentacja sterownika GDAL potwierdza limit 10 znaków
  nazw DBF, generowanie nazw unikalnych po skróceniu oraz obcinanie tekstu
  przekraczającego szerokość pola:
  <https://gdal.org/en/stable/drivers/vector/shapefile.html>.
- **Pewność:** wysoka; zachowanie odtworzono. Nowszy GDAL 3.13 może zapisać
  długie nazwy w dodatkowym `.shp.xml`, ale nie usuwa to problemu
  interoperacyjności ze starszym QGIS/GDAL i innym oprogramowaniem.

### L-01. Testy QGIS są związane z linuksowym prefiksem `/usr`

- **Poziom ryzyka:** niski — jakość i przenośność procesu testowego.
- **Miejsce:** `tests/qgis/conftest.py:5-19`, `README.md:22-38`,
  `metadata.txt:6-7`.
- **Opis:** fixture ustawia `QgsApplication.setPrefixPath("/usr", True)`.
  To poprawne dla audytowanego Linuksa, ale nie dla typowej instalacji
  Windows lub macOS. README deklaruje przygotowanie kodu dla Qt5/Qt6,
  jednocześnie przyznając brak rzeczywistego testu QGIS 4.2.
- **Możliwy scenariusz ataku/błędu:** brak scenariusza ataku. Testy nie
  uruchamiają się albo używają złych danych zasobów na innym systemie, przez
  co regresja platformowa pozostaje niewykryta.
- **Wpływ:** niższa pewność spełnienia wymogu QGIS dotyczącego działania na
  Windows, Linux i macOS oraz ryzyko problemu podczas losowego testu
  recenzenta.
- **Rekomendacja:** pobierać prefix z kontrolowanej zmiennej środowiskowej
  testu lub używać środowiska QGIS przygotowanego przez runner. Dodać macierz
  CI/ręczny release checklist dla wspieranych systemów i wersji. Nie
  deklarować QGIS 4 w `qgisMaximumVersion` przed rzeczywistym testem.
- **Podstawa oceny:** QGIS oczekuje wtyczek cross-platform i wykonuje losowe
  testy instalacji/uruchomienia:
  <https://plugins.qgis.org/docs/approval>.
- **Pewność:** wysoka dla hardcodowanego prefiksu; niepewne jest, czy
  występuje błąd runtime na nieprzetestowanych platformach.

### L-02. Duże funkcje GUI i drobne wyniki analizy jakościowej

- **Poziom ryzyka:** niski — utrzymywalność i ryzyko regresji.
- **Miejsce:**
  - `gui/dialog.py:111` — Ruff B009;
  - `gui/dialog.py:315-323` — Ruff N802, false positive dla nadpisania
    `QTextBrowser.viewportEvent()`;
  - `tests/qgis/test_gui.py:121` — Ruff B009 w teście;
  - `gui/dialog.py:399-555` (`_build_ui`, 157 linii);
  - `gui/dialog.py:676-909` (`_format_result_html`, 234 linie);
  - `gui/dialog.py:982-1139` (`_html_document`, 158 linii);
  - `gui/dialog.py:1360-1525` (`_dialog_stylesheet`, 166 linii);
  - `processing_provider/area_algorithm.py:250-336`
    (`_process_feature`, 87 linii);
  - `adapters/repair.py:126-220` (`_repair_geometry`, 95 linii).
- **Opis:** Ruff wskazał dwa zbędne wywołania `getattr()` ze stałą nazwą
  atrybutu. Trzecie trafienie dotyczy nazwy metody wymaganej przez API Qt,
  dlatego jest false positive. `ruff format --check` wskazał trzy pliki,
  które sformatowałby inaczej: `gui/dialog.py`,
  `processing_provider/area_algorithm.py` i `tests/qgis/test_gui.py`.
  Flake8 zakończył się bez trafień. Własny limit 79 znaków również jest
  zachowany; wcześniejsze ręczne liczenie bajtów UTF-8 błędnie traktowało
  polskie znaki jako więcej niż jeden znak. Większym problemem pozostaje
  skupienie budowy UI, CSS, HTML, treści pomocy i logiki raportu w jednym
  pliku o długości 1525 linii.
- **Możliwy scenariusz ataku/błędu:** brak bezpośredniego scenariusza ataku.
  Rozbudowa jednego z wielkich generatorów HTML może łatwiej pominąć
  `escape()` albo zepsuć mapowanie pomocy i danych.
- **Wpływ:** trudniejszy przegląd bezpieczeństwa, większe ryzyko regresji
  oraz niewielki dług jakościowy. Nie stwierdzono bezpośredniego wpływu na
  bezpieczeństwo lub działanie wtyczki.
- **Rekomendacja:** podzielić dane pomocy, renderer raportu i styl na osobne
  moduły/zasoby; rozbić `_process_feature()` na przygotowanie, obliczenie
  i mapowanie wyniku; uruchamiać `ruff check`, `ruff format --check` oraz
  `flake8` w CI. Usunąć zbędne `getattr()` i oznaczyć
  `viewportEvent()` jako świadomy wyjątek `N802`; nie zmieniać nazw
  wymaganych przez API QGIS.
- **Podstawa oceny:** PEP 8 i zalecenia QGIS dotyczące PEP 8 oraz dobrej
  organizacji kodu:
  - <https://peps.python.org/pep-0008/>
  - <https://plugins.qgis.org/docs/publish/>.
- **Pewność:** wysoka; wpływ na bezpieczeństwo jest pośredni.

## Kontrole bez stwierdzonej podatności

Poniższe wyniki są istotne, ponieważ pokazują ręczny przegląd przepływu
niezaufanych danych, a nie wyłącznie brak trafień automatu.

### Wykonywanie kodu i poleceń

- W kodzie uruchomieniowym nie ma `eval()`, wbudowanego `exec()`, `compile()`,
  `pickle`, `marshal`, `yaml.load`, `jsonpickle`, `__import__()` ani
  `importlib`.
- `compat.py:36-42` odwołuje się do metody `QDialog.exec()`/`exec_()`.
  Jest to modalne uruchomienie dialogu Qt, a nie wbudowana funkcja Python
  `exec`; ewentualne zgłoszenie tekstowego skanera byłoby false positive.
- Nie ma `os.system`, `subprocess`, `shell=True`, powłoki ani automatycznej
  instalacji pakietów.
- Dynamiczny import w `tests/qgis/test_plugin.py:121-155` używa lokalnej,
  kontrolowanej nazwy paczki w teście. Testy nie trafiają do ZIP.

### SQL i dane z warstw

- Wtyczka nie buduje i nie wykonuje SQL.
- Obiekt wejściowy musi być `QgsVectorLayer` z typem Polygon
  (`plugin.py:78-89`), a adapter ponownie odrzuca geometrię null, pustą
  i niepoligonową (`adapters/geometry.py:152-158`).
- CRS musi być poprawny; PL-2000 jest ograniczony do EPSG:2176–2179, a dla
  innego CRS użytkownik musi wybrać strefę. Po transformacji każdy punkt jest
  kontrolowany względem prefiksu strefy
  (`adapters/zones.py:28-68`, `adapters/repair.py:104-114`).
- Wartości `NaN`/`Inf`, niedodatnie pole i przepełnienie są odrzucane w
  `core/models.py:22-26` i `core/calculation.py:149-194`, `253-265`.
- Tryb bez GEOS jest świadomą funkcją, a nie pomyłką: interfejs i pomoc
  informują, że obliczenie używa kopii geometrii źródłowej bez
  `isGeosValid()`/`makeValid()`.

### Ścieżki, archiwa i formaty

- Kod runtime nie odczytuje ani nie zapisuje ścieżek podanych przez
  użytkownika. Ścieżka wyjściowa Processing jest obsługiwana przez framework
  QGIS.
- Wtyczka nie rozpakowuje archiwów. `ZipFile.extractall()` występuje wyłącznie
  w `tests/qgis/test_plugin.py:145-155` i rozpakowuje ZIP utworzony chwilę
  wcześniej przez własny builder do katalogu `tmp_path`.
- Świeżo zbudowany ZIP:
  - ma jeden katalog główny `qgis_poprawka_odwzorowawcza/`;
  - zawiera 20 plików, 40 223 B;
  - nie ma ścieżek absolutnych, `..`, separatorów `\` ani duplikatów;
  - nie ma plików wykonywalnych, ukrytych, `.pyc`, binariów natywnych,
    testów, `legacy/` ani materiałów prawnych;
  - nadaje wszystkim wpisom tryb `0644`;
  - jest deterministyczny: dwa buildy miały identyczny SHA-256;
  - odpowiadał bajt w bajt bieżącym plikom źródłowym.
- Nie ma parsera XML/JSON danych użytkownika. Lokalny `resources/icon.svg`
  zawiera tylko statyczne kształty, bez skryptów, odwołań do plików i zasobów
  sieciowych. Nie ma powierzchni XXE.

### Sieć, SSRF, TLS i uwierzytelnianie

- W repozytorium nie ma `requests`, `urllib`, `httpx`, `aiohttp`,
  `QNetworkAccessManager`, `QgsNetworkAccessManager` ani własnego TLS.
- Nie istnieje więc obecnie powierzchnia SSRF, przekierowań, timeoutów,
  limitów pobrania lub walidacji certyfikatów.
- Brak `QgsNetworkAccessManager` nie jest wadą, ponieważ wtyczka nie wykonuje
  żadnych żądań. Gdyby sieć została dodana, zasady QGIS wymagają użycia
  menedżera QGIS zamiast `requests`/`urllib`.
- Wtyczka nie pobiera i nie przechowuje haseł, tokenów ani kluczy. Nie ma
  potrzeby użycia `QgsAuthManager`. Jeżeli pojawi się uwierzytelniana sieć,
  należy przechowywać wyłącznie `authcfg`, pozostawiając rozwinięcie
  poświadczeń `QgsAuthManager`.

Źródła:

- <https://plugins.qgis.org/docs/publish/>
- <https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/authentication.html>
- <https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html>
- <https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html>
- <https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html>

### Sekrety i zależności

- `detect-secrets scan --all-files .` nie znalazł sekretów. Osobny skan
  wszystkich plików świeżej paczki ZIP również zwrócił zero wyników.
- Ręczny skan wzorców wysokiej pewności nie znalazł sekretów także
  w historii 14 commitów.
- Jedyny adres e-mail w `metadata.txt:9` jest adresem GitHub `noreply`, nie
  sekretem.
- Runtime korzysta wyłącznie z biblioteki standardowej Python oraz API
  dostarczanego z QGIS (`qgis.core`, `qgis.PyQt`). Nie ma `requirements.txt`,
  vendoringu, plików wheel, bibliotek `.so`/`.dll`/`.dylib` ani kodu
  instalującego pakiety.
- `pip-audit` nie ma manifestu zależności wtyczki do sprawdzenia. Uruchomiony
  bez pliku wymagań zbadał 149 pakietów współdzielonego środowiska
  Python/QGIS i zgłosił 66 rekordów advisory w 14 pakietach: `click`,
  `cryptography`, `gdal`, `httplib2`, `idna`, `jaraco-context`, `lxml`,
  `pillow`, `pygments`, `pyjwt`, `requests`, `setuptools`, `soupsieve`
  i `urllib3`. Nie są one deklarowane, vendoringowane ani instalowane przez
  wtyczkę, dlatego wynik nie jest podatnością w konkretnym miejscu jej kodu
  i nie został doliczony do ustaleń. Środowisko QGIS i środowisko skanerów
  należy jednak zaktualizować niezależnie od publikacji wtyczki.

### HTML i GUI

- Nazwa warstwy i opis CRS są wstawiane do HTML dopiero po `html.escape`
  (`gui/dialog.py:437-461`, `gui/dialog.py:1299-1303`).
- Ostrzeżenia i techniczne szczegóły GEOS są escapowane zarówno w raporcie,
  jak i tooltipach (`gui/dialog.py:875-885`, `gui/dialog.py:1150-1173`).
- Wartości nieescapowane w `_result_row()` i `_parameter_cells()` pochodzą
  tylko ze stałych symboli i sformatowanych wartości liczbowych, nie z warstw.
- `QTextBrowser` ma wyłączone otwieranie linków zewnętrznych
  (`gui/dialog.py:519-524`), a klucze `href` są wewnętrznymi identyfikatorami
  pomocy.

### Cykl życia QGIS

- `__init__.py:4-9` zawiera wymagane `classFactory()`.
- `plugin.py:32-56` rejestruje akcję i provider, a `plugin.py:58-73` usuwa
  menu, ikonę, połączenie sygnału i provider.
- Provider Processing jest deklarowany w `metadata.txt:15` i poprawnie
  rejestrowany/usuwany.
- Brak wątków, timerów, otwartych plików i zasobów sieciowych wymagających
  dodatkowego sprzątania.
- Dialog kopiuje `QgsFeature` (`gui/dialog.py:382-385`), a transformacja i
  naprawa działają na `QgsGeometry` utworzonej jako kopia
  (`adapters/geometry.py:72`, `adapters/repair.py:132-149`, `202-205`).

## Wyniki narzędzi i testów

| Kontrola | Wynik |
|---|---|
| `bandit -r . -x ./legacy` | 270 wyników LOW/HIGH confidence, wszystkie B101 (`assert`) wyłącznie w testach; 0 wyników w kodzie runtime |
| Bandit na świeżym ZIP | 0 wyników, 0 błędów analizy |
| `flake8 . --exclude=legacy,__pycache__ --jobs 1` | zaliczony, 0 wyników |
| Flake8 na świeżym ZIP | zaliczony, 0 wyników |
| `detect-secrets scan --all-files .` | zaliczony, 0 sekretów |
| detect-secrets na świeżym ZIP | zaliczony, 0 sekretów |
| `pip-audit` | 66 rekordów w 14 pakietach współdzielonego środowiska; brak manifestu i zależności pip wtyczki |
| `pytest -p no:cacheprovider` | zaliczony: 90/90 przypadków w 1,00 s |
| `ruff check --no-cache .` | 3 uwagi jakościowe: 2 × B009 i 1 × N802; N802 jest false positive dla Qt |
| `ruff format --check --no-cache .` | 3 pliki wymagałyby formatowania; 32 pliki zgodne |
| Parsowanie AST | 31/31 utrzymywanych plików poprawnych; `legacy/` świadomie wyłączony |
| Test wzoru | zaliczony: 10 000 m² → 10 001,53994071 m² i 1,0002 ha |
| PyQGIS provider smoke test | zaliczony w QGIS 3.40.15; rejestracja, obecność algorytmu i usunięcie |
| Świeży build ZIP | zaliczony: 20 plików, 40 223 B, SHA-256 `e34b90bc0d8fede633cdf3500e4b1c1fb30322088ad5a23406b374b5a068d486` |
| Shapefile smoke test | algorytm zakończony; potwierdzono laundering nazw i limit 254 znaków |
| Publiczne URL | repozytorium i tracker zwróciły HTTP 200; zdalny HEAD = lokalny commit |

Narzędzia uruchomiono z izolowanego środowiska audytowego, bez dodawania ich
do wtyczki. `legacy/` jawnie wyłączono z analizy Python, ponieważ jest
szablonem akcji QGIS. Banditowe B101 są oczekiwanymi użyciami `assert`
w testach, które nie trafiają do ZIP, i nie stanowią podatności runtime.
Komendy należy powtórzyć na stanie źródeł i dokładnym artefakcie
przeznaczonym do publikacji:

```bash
bandit -r . -x ./legacy
flake8 . --exclude=legacy
detect-secrets scan --all-files .
pytest -p no:cacheprovider
ruff check --no-cache .
ruff format --check --no-cache .
```

Świeżą paczkę dodatkowo rozpakowano do katalogu tymczasowego i uruchomiono
na niej Bandit, Flake8 oraz `detect-secrets`; wszystkie trzy kontrole były
czyste. Wyniki automatyczne nadal wymagają ręcznej oceny przepływów danych.

## Zgodność z QGIS Plugin Repository

### Elementy spełnione

- `metadata.txt`, `__init__.py`, `classFactory()`, `LICENSE` i README są
  obecne.
- Metadane są poprawnie kodowane w UTF-8 i zawierają wymagane podstawowe pola.
- `category=Vector` odpowiada miejscu dodania akcji.
- `hasProcessingProvider=yes` odpowiada faktycznej implementacji providera.
- Licencja to pełny tekst GNU GPL v2; jest zgodna z wymaganiami repozytorium.
- Repozytorium i tracker są dostępne publicznie, a repozytorium nie zawiera
  śledzonego ZIP wydaniowego.
- Świeża paczka jest znacznie mniejsza niż limit 25 MB, ma prawidłowy jeden
  katalog główny, nie zawiera binariów, ukrytych katalogów, cache, testów ani
  plików wykonywalnych.
- Kod używa `qgis.PyQt`, a nie bezpośredniego `PyQt5`/`PyQt6`.
- Wtyczka nie używa sieci, więc nie omija `QgsNetworkAccessManager`.
- Rejestracja i usuwanie providera są zgodne z cookbook Processing.
- Bandit, Flake8 i `detect-secrets` na dokładnej zawartości świeżego ZIP nie
  zgłosiły żadnego wyniku.

### Elementy mogące zablokować lub opóźnić publikację

1. **Prawdopodobna blokada ręczna:** brak krótkiego angielskiego opisu
   (`metadata.txt:3-4`).
2. **Ryzyko odrzucenia lub wydania złego kodu:** istniejący ZIP w `dist/` nie
   odpowiada repozytorium. Trzeba przesłać świeżo zbudowany artefakt.
3. **Możliwa uwaga recenzenta:** `about` i README nie opisują wszystkich
   ograniczeń oraz kompletnej ścieżki użycia.
4. **Testy platformowe:** nie potwierdzono Windows/macOS. Losowy test
   recenzenta może ujawnić problem, mimo że kod nie zawiera oczywistych
   zależności platformowych.
5. **Warunkowe, możliwy false positive:** `metadata.txt` nie ma pola
   `changelog`. Dla pierwszej publikacji 0.1.0 jest ono opcjonalne. Jeżeli
   wersja jest aktualizacją już opublikowanej wtyczki, QGIS wymaga changelogu
   i zwiększenia numeru wersji.
6. **Opcjonalne:** metadane nie wskazują ikony. Pole jest opcjonalne; jeśli
   zostanie dodane, dokumentacja metadata zaleca web-friendly PNG/JPEG,
   nie obecny SVG.

Oficjalne reguły skanowania są generowane dynamicznie i mogą ulec zmianie.
W dniu audytu QGIS opisywał Bandit i `detect-secrets` jako skanery blokujące,
a Flake8 i analizę plików jako nieblokujące:

- <https://plugins.qgis.org/docs/security-scanning>
- <https://plugins.qgis.org/docs/security-scanning/tools>
- <https://plugins.qgis.org/docs/security-scanning/rules>

## Zgodność z PEP 8

Najważniejsze, niekosmetyczne ustalenia:

1. Flake8 nie zgłosił błędów, a żadna utrzymywana linia nie przekracza
   skonfigurowanego limitu 79 znaków Unicode. Liczenie bajtów UTF-8 zamiast
   znaków dawałoby dla polskich treści fałszywe przekroczenia.
2. Ruff zgłosił dwa zbędne użycia `getattr()` ze stałą nazwą. Jego N802 dla
   `viewportEvent()` jest false positive, ponieważ nazwa wynika z API Qt.
   Kontrola formatowania wskazała trzy pliki odbiegające od stylu Ruff.
3. `gui/dialog.py` ma 1525 linii i łączy treści UX, mapy pomocy, widgety,
   generowanie HTML oraz CSS. Funkcje o długości 157–234 linii utrudniają
   przegląd bezpieczeństwa i testowanie.
4. `_process_feature()` oraz `_repair_geometry()` łączą po kilka etapów
   przetwarzania i raportowania. Warto rozdzielić je bez zmiany semantyki.
5. Nazwy wymagane przez QGIS, np. `classFactory`, `initGui`,
   `processAlgorithm`, są poprawnymi wyjątkami od PEP 8. Obecne wyłączenia
   `N802` w `pyproject.toml:19-23` są uzasadnione; analogicznego oznaczenia
   wymaga nadpisanie Qt w `gui/dialog.py:315`.
6. Importy są pogrupowane, nie ma wildcard imports, martwych importów
   widocznych w ręcznym przeglądzie ani pustych bloków `except`.
7. `legacy/pow_QGIS_v1.py` nie powinien być raportowany jak kod runtime.
   Zawiera placeholdery QGIS i jest wyłączony z Ruff oraz paczki. Dla Bandit
   i Flake8 potrzebne jest analogiczne jawne wyłączenie.

Źródło: <https://peps.python.org/pep-0008/>.

## Priorytety napraw

### 1. Przed publikacją

1. Nie używać istniejącego `dist/qgis_poprawka_odwzorowawcza-0.1.0.zip`;
   zbudować świeży ZIP z audytowanego commitu i zachować jego sumę SHA-256.
2. Uzupełnić `metadata.txt` o krótki angielski opis i pełniejszy opis
   ograniczeń; rozbudować minimalną instrukcję użytkownika w README.
3. Utwardzić builder ZIP: odrzucać symlinki i nieoczekiwane/nieśledzone pliki,
   sprawdzać pozostanie ścieżki w `source_root`, dodać testy negatywne.
4. Wprowadzić limity złożoności geometrii i usunąć materializowanie całej
   selekcji. Dla ciężkich obliczeń GUI dodać bezpieczne przetwarzanie w tle
   albo co najmniej próg blokujący z jasnym komunikatem.
5. Po każdej poprawce powtórzyć Bandit, `detect-secrets`, Flake8 i pełne
   `pytest` na źródłach oraz dokładnej zawartości finalnego ZIP; zachować
   raport i ręcznie sklasyfikować wyniki.
6. Wykonać test instalacji, GUI, unload i Processing na wspieranym QGIS 3.44
   w Linux, Windows i macOS. QGIS 4 deklarować dopiero po teście Qt6.

### 2. Zalecane

1. Ustalić politykę wyniku dla Shapefile albo rekomendować GeoPackage;
   dodać testy schematu i długości ostrzeżeń dla kilku providerów.
2. Dodać CI uruchamiające testy, skanery, deterministyczny build oraz
   porównanie paczki ze źródłem.
3. Podzielić `gui/dialog.py` na dane pomocy, renderer raportu, styl i dialog;
   rozbić duże funkcje Processing/repair.
4. Zastosować uzasadnione poprawki Ruff i ujednolicić format trzech
   wskazanych plików.
5. Jeżeli to aktualizacja już opublikowanej wtyczki, zwiększyć wersję i dodać
   `changelog`.

### 3. Opcjonalne ulepszenia

1. Dodać mały, anonimowy zestaw danych referencyjnych do testów ręcznych.
2. Dodać ikonę PNG/JPEG w `metadata.txt` dla widoku repozytorium QGIS.
3. Tworzyć podpisany tag wydania i publikować sumę SHA-256 artefaktu.
4. Dodać test obciążeniowy geometrii przy progu limitu i poniżej niego.

## Źródła i zasady

### QGIS i PyQGIS

- Publikacja wtyczek:
  <https://plugins.qgis.org/docs/publish/>
- Proces zatwierdzania:
  <https://plugins.qgis.org/docs/approval>
- Skanowanie bezpieczeństwa:
  <https://plugins.qgis.org/docs/security-scanning>
- Narzędzia skanowania:
  <https://plugins.qgis.org/docs/security-scanning/tools>
- Aktualne reguły skanera:
  <https://plugins.qgis.org/docs/security-scanning/rules>
- Struktura i cykl życia wtyczki:
  <https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/plugins.html>
- Provider Processing:
  <https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/processing.html>
- Authentication Infrastructure:
  <https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/authentication.html>
- Ciężka praca w tle:
  <https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/tasks.html>

### OWASP

- Input Validation:
  <https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html>
- SQL Injection Prevention:
  <https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html>
- OS Command Injection Defense:
  <https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html>
- SSRF Prevention:
  <https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html>
- XXE Prevention:
  <https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html>
- Deserialization:
  <https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html>
- Secure Code Review:
  <https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html>

### Python i formaty danych

- PEP 8: <https://peps.python.org/pep-0008/>
- GDAL Shapefile/DBF:
  <https://gdal.org/en/stable/drivers/vector/shapefile.html>

## Rekomendacja końcowa

Wtyczka nie wykazuje obecnie krytycznych lub wysokich podatności runtime,
ale nie powinna zostać opublikowana z istniejącego ZIP ani przed usunięciem
średnich ryzyk procesu budowy, odporności na złożone geometrie i metadanych.

**Rekomendacja: gotowa po poprawkach.**
