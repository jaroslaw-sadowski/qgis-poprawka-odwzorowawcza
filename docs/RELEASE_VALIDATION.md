# Walidacja kandydata wydania 1.0.1

- Data: 2026-07-25
- Gałąź lokalna: `main`
- Bazowy commit zgodny z `origin/main`:
  `b46abfb51ef5feff4aa2725ea1b62cffb970a1fd`
- Stan wydania: finalne zmiany `1.0.1` w drzewie przed commitem
- Środowisko lokalne: Linux, QGIS 3.40.15, Qt 5.15.18, Python 3.14.4

Raport dotyczy bazowego commitu wskazanego powyżej oraz opisanych zmian
wydaniowych. Nie zastępuje odbudowania artefaktu z oznaczonego commitu ani
testów na wszystkich wspieranych platformach.

## Zakres zmian

- Uporządkowano README, dokumentację projektu i materiały audytowe.
- Dodano politykę bezpieczeństwa, changelog, zasady współtworzenia,
  formularze zgłoszeń i szablon pull requestu.
- Dodano minimalnie uprzywilejowany workflow CI, Dependabot oraz baseline
  skanera sekretów.
- Ujednolicono motyw GUI, dodano okno „O wtyczce” i ikonę PNG dla
  repozytorium QGIS.
- Ujednolicono oficjalną nazwę do „Poprawka odwzorowawcza PL-2000”.
- Przygotowano aktualizację `1.0.1` z pełną nazwą we wszystkich elementach
  widocznych dla użytkownika i poprawką checkera Qt6/QGIS 4.
- Przygotowano pierwsze stabilne wydanie `1.0.0` i prostą instrukcję
  publikacji.
- Wszystkie widoczne opisy metadanych wydania `1.0.0` przetłumaczono na
  język polski.
- Opis publikacyjny uproszczono i ukierunkowano na potrzeby użytkownika;
  dodano tagi „powierzchnia” i „Stowarzyszenie QGIS Polska”.
- Dodano porównawczy pomiar geodezyjny QGIS na elipsoidzie GRS 80 do
  dialogu oraz warstwy Processing jako `egib_qgis_m2`.
- Opisano `P₀` jako pole matematyczne/kartezjańskie i wyjaśniono w popupach
  różnicę względem pomiaru geodezyjnego oraz głównego wyniku prawnego.
- Wymuszono techniczny krój pisma na wszystkich kontrolkach Qt i raportach
  wtyczki. Zmniejszono nagłówek okna „O wtyczce” i jego ikonę z 64 do 16 px.
- Zmniejszono ikonę PNG wyświetlaną przez Menedżer wtyczek QGIS z 256×256
  do 64×64 px i objęto jej wymiary testem paczki.
- Zmieniono adres kontaktowy metadanych na odbierający pocztę alias
  `github.com.amenity983@passfwd.com`.
- Usunięto ustalenie checkera QGIS 4 dotyczące starego zapisu
  `QgsFeatureSink.FastInsert`; używany jest zgodny zapis
  `QgsFeatureSink.Flag.FastInsert`, dostępny również w QGIS 3.40.
- Opis metadanych powiązano wprost z § 16 ust. 2 i załącznikiem nr 3
  rozporządzenia EGiB (Dz.U. z 2024 r. poz. 219 ze zm.).
- Potwierdzono, że `Vector` jest najlepiej dopasowaną z czterech kategorii
  obsługiwanych przez oficjalne repozytorium QGIS.
- Komunikaty GUI nie pokazują surowych wyjątków ani lokalnych ścieżek.
- Uzupełniono metadane, jawny manifest paczki i testy nowych elementów.
- Nie zmieniono wzoru, stałych, mapowania osi, stref, PGK, zaokrąglania ani
  kolejności obliczeń.

## Kontrole po grupach zmian

| Grupa | Pytest | Ruff/format | Flake8 | Bandit | Sekrety |
|---|---:|---:|---:|---:|---:|
| Repozytorium i dokumentacja | 101/101 | 3 ustalenia bazowe | 0 | 0 | 0 |
| Interfejs i metadane | 103/103 | 0 | 0 | 0 | 0 |
| CI, bezpieczne błędy i paczka | 104/104 | 0 | 0 | 0 | 0 |
| Stabilne wydanie 1.0.0 | 104/104 | 0 | 0 | 0 | 0 |
| Polskie metadane 1.0.0 | 104/104 | 0 | 0 | 0 | 0 |
| Opis produkcyjny i tagi | 104/104 | 0 | 0 | 0 | 0 |
| Wynik geodezyjny i finalne GUI | 105/105 | 0 | 0 | 0 | 0 |
| Nazwa PL-2000 i zgodność enumu Qt6 | 105/105 | 0 | 0 | 0 | 0 |

Trzy bazowe ustalenia Ruff z pierwszej grupy zostały naprawione w drugiej:
dwa stałe odczyty enum oraz format trzech plików. Nazwa
`viewportEvent()` zachowuje wymagany kontrakt Qt i ma minimalne, lokalne
`# noqa: N802`.

Końcowe kontrole źródeł:

| Kontrola | Wynik |
|---|---|
| `compileall` utrzymywanych plików | OK |
| Ruff 0.16.0 | 0 ustaleń, 45/45 plików sformatowanych |
| Flake8 7.3.0 | 0 ustaleń |
| Bandit 1.9.4 na runtime i builderze | 0 ustaleń |
| detect-secrets 1.5.0 | 0 sekretów |
| pip-audit 2.10.1 dla `requirements-dev.txt` | 0 znanych podatności |
| actionlint 1.7.12 | workflow poprawny |
| pełny pytest | 105/105 |

## Artefakt

Końcowy ZIP z bieżącego drzewa zbudowano dwukrotnie:

- plik kontrolny:
  `dist/qgis_poprawka_odwzorowawcza-1.0.1.zip`;
- rozmiar: 54 123 B;
- SHA-256:
  `4ef93241e79839cabaff94cb3ced509e4cfb050a76943df26d82c8f5eb5ec215`;
- zawartość: 24 pliki pod jednym katalogiem
  `qgis_poprawka_odwzorowawcza/`;
- porównanie z jawnym manifestem: wszystkie pliki zgodne bajt w bajt;
- powtarzalność: drugi build jest identyczny według `cmp`;
- test struktury ZIP: OK.

Dokładną rozpakowaną zawartość przeskanowano ponownie. Ruff, formatowanie,
Flake8, Bandit i detect-secrets zakończyły się bez ustaleń. ZIP nie zawiera
testów, dokumentacji deweloperskiej, materiałów prawnych, plików cache,
lokalnego `dist/`, konfiguracji GitHub ani zależności narzędziowych.

Starego pliku `dist/qgis_poprawka_odwzorowawcza-0.1.0.zip` nie należy
publikować. Po utworzeniu końcowego commitu i taga trzeba ponownie zbudować
paczkę `1.0.1`; jej suma musi pozostać zgodna z wartością
powyżej.

## Kontrola repozytorium i historii

- `main` i `origin/main` wskazują ten sam commit bazowy; zmiany wydania
  `1.0.1` z finalną nazwą nie są jeszcze zatwierdzone.
- Jedyna zdalna gałąź to `main`; brak zdalnych kandydatów do usunięcia.
- Istniejący lokalny i zdalny tag `v1.0.0` pozostaje bez zmian. Po
  zatwierdzeniu aktualizacji należy utworzyć nowy tag `v1.0.1`.
- Historia bazowa ma 25 commitów i jednego autora używającego adresu GitHub
  `noreply`. Starsze niespójne komunikaty pozostają bez przepisywania
  historii; dla nowych zmian udokumentowano Conventional Commits.
- Nie znaleziono sekretów, poświadczeń, prywatnych kluczy, wewnętrznych
  hostów ani danych produkcyjnych.
- Nie ma śledzonych symlinków, cache Python, środowisk wirtualnych ani ZIP.
- Pliki binarne w `docs/legal/` pozostają audytowalnym źródłem podstawy
  prawnej i nie trafiają do paczki wtyczki.

## Stan i zalecane ustawienia GitHub

Publiczne API GitHub potwierdziło: repozytorium jest publiczne, `main` jest
gałęzią domyślną, istnieje tag `v1.0.0`, a GitHub Release nie został jeszcze
utworzony. Ustawień bezpieczeństwa niewidocznych bez uwierzytelnienia nie
oznaczono jako sprawdzone.

Przed wysłaniem lokalnego `main` i publikacją opiekun powinien:

1. Ustawić topics: `qgis`, `qgis-plugin`, `pyqgis`, `cadastre`, `egib`,
   `pl-2000`, `geodesy`, `poland`.
2. Dodać ruleset dla `main`: pull request, wymagany check `Source quality`,
   rozwiązane rozmowy, liniowa historia, blokada force push i usuwania.
   Przy jednym opiekunie można zacząć od 0 wymaganych akceptacji; po dodaniu
   drugiego opiekuna ustawić 1 i unieważnianie akceptacji po nowych zmianach.
3. Ustawić Actions na read-only `GITHUB_TOKEN`, wyłączyć zatwierdzanie pull
   requestów przez workflow i wymagać pełnych SHA dla akcji.
4. Włączyć Dependabot alerts i security updates, code scanning dla Python,
   secret scanning z push protection oraz private vulnerability reporting.
5. Włączyć automatyczne usuwanie gałęzi po scaleniu i preferować squash
   merge lub rebase. Wyłączyć Wiki i Projects, jeśli nie będą używane.

## Ręczne testy finalnego ZIP-u

| Środowisko | Instalacja | GUI | Processing | unload | Stan |
|---|---:|---:|---:|---:|---|
| QGIS 3.44 / Linux | — | — | — | — | niewykonany |
| QGIS 3.44 / Windows | — | — | — | — | niewykonany |
| QGIS 3.44 / macOS | — | — | — | — | niewykonany |

## Niewykonane bramki publikacji

Nie wykonano interaktywnej instalacji finalnego ZIP ani testów na QGIS 3.44,
Windows i macOS. Przed wysłaniem do oficjalnego repozytorium QGIS pozostają:

- instalacja, GUI, unload i Processing na QGIS 3.44 / Linux;
- te same testy na QGIS 3.44 / Windows;
- te same testy na QGIS 3.44 / macOS;
- commit i push zmian wydania oraz zielony check `Source quality`;
- odbudowanie ZIP-u z commitu wydania i potwierdzenie SHA-256;
- utworzenie taga `v1.0.1`, GitHub Release i wysłanie tego samego ZIP-u do
  QGIS.

QGIS 4/Qt6 nie jest deklarowany i nie wolno rozszerzać
`qgisMaximumVersion` przed rzeczywistym testem. Do czasu zamknięcia powyższych
bramek ocena kandydata brzmi:
**AUTOMATYCZNIE ZWALIDOWANY — OCZEKUJE NA TESTY RĘCZNE**.

## Punkt 3 — 2026-09-05

Aktualizacja lokalna względem commitu `7132437`: bezpośrednie menu Wtyczki,
jednolita nazwa „Poprawka odwzorowawcza PL-2000”, usunięta podgrupa
Processing, uproszczone README i metadane oraz czytelne okno informacji.
Powyższy raport lipcowy pozostaje zapisem historycznym.

Środowisko: Linux, QGIS 3.40.15, Qt 5.15.18, Python 3.14.4.

- Pytest: **219/219**, w tym menu bez podmenu, brak duplikatów po ponownej
  rejestracji, usuwanie własnych wpisów, drzewo Processing oraz nazwy
  wtyczki zaimportowanej z wygenerowanego ZIP-a.
- Bandit i Flake8: bez ustaleń w źródłach oraz rozpakowanej paczce.
- detect-secrets: pełny skan plików rozpakowanej paczki, bez ustaleń.
- Ruff i formatowanie: bez ustaleń.
- pip-audit: brak znanych podatności zależności developerskich.
- Analiza ZIP-a: 24 pliki z jawnego manifestu, jeden katalog pakietu,
  uprawnienia `0644`, brak plików ukrytych, symlinków, cache, dodatkowych
  programów wykonywalnych i niepożądanych plików binarnych; CRC poprawne.
- Dwa niezależne zbudowania dają identyczne archiwa.
- Podgląd okna informacji: pełny tekst dostępny także przy małym rozmiarze
  okna dzięki przewijaniu; sprawdzony również testem układu.

Domyślna nazwa: `Poprawka odwzorowawcza PL-2000-1.0.1.zip`.
Nazwa wyświetlana pochodzi z `metadata.txt`; techniczny katalog importu
Pythona oraz identyfikatory algorytmu pozostają kompatybilne z istniejącymi
instalacjami i modelami.

Kontrole odpowiadają zakresom opisanym w
[zaleceniach QGIS](https://plugins.qgis.org/docs/security-scanning/tools).
Analiza plików jest lokalną kontrolą manifestu i nagłówków ZIP, nie wynikiem
serwerowego skanera plugins.qgis.org. Paczki nie wysłano do repozytorium
QGIS; nie wykonano nowych testów na Windows, macOS ani QGIS 4/Qt6.

## Punkt 4 — 2026-09-05

Zmiany względem `9581ef2`: dwujęzyczne description, about i changelog,
tagi tematyczne w parach polski–angielski bez tagu organizacji, README z pełną
wersją README.en.md oraz angielski opis w oknie informacji.
Nazwa własna i interfejs obliczeń pozostają polskie.

### Widoczność języków

- Oba języki są w standardowych polach metadanych, bez nadpisywania ich
  kluczami zależnymi od języka programu. Polski szczegółowy opis jest
  pierwszy; krótki opis zaczyna się po angielsku, zgodnie z
  [wymogiem QGIS](https://plugins.qgis.org/docs/publish).
- Parser zainstalowanego menedżera QGIS (`Plugins.getInstalledPlugin`)
  odczytał oba języki z rozpakowanego ZIP-a dla `pl_PL`, `en_US` i `de_DE`.
  Test nie zmienia ustawień użytkownika i nie pobiera danych z sieci.
- Oficjalny serwer odczytuje standardowe pola z metadata.txt, aktualizuje
  description/about z nowej wersji, a strona i katalog XML wyświetlają je
  bez wyboru języka. Sprawdzono kod QGIS-Plugins-Website, commit
  `d7ff1ffd460f9d63052954ae5ee4e1bdc58e1e65`:
  [walidator](https://github.com/qgis/QGIS-Plugins-Website/blob/d7ff1ffd460f9d63052954ae5ee4e1bdc58e1e65/qgis-app/plugins/validator.py),
  [aktualizacja wpisu](https://github.com/qgis/QGIS-Plugins-Website/blob/d7ff1ffd460f9d63052954ae5ee4e1bdc58e1e65/qgis-app/plugins/views.py),
  [szablon strony](https://github.com/qgis/QGIS-Plugins-Website/blob/d7ff1ffd460f9d63052954ae5ee4e1bdc58e1e65/qgis-app/plugins/templates/plugins/plugin_detail.html).
- Oba README są w ZIP-ie i mają wzajemne odsyłacze względne, działające
  również po rozpakowaniu. Angielski tekst okna informacji pochodzi
  bezpośrednio z angielskiej części metadanych.

### Wyniki i granice weryfikacji

223 testy przeszły na QGIS 3.40.15 / Qt 5.15.18 / Python 3.14.4.
Parser QGIS zgłasza ostrzeżenia o przestarzałym `codecs.open` w Pythonie
3.14; nie są to błędy wtyczki. Ruff, Flake8, Bandit, detect-secrets oraz
pip-audit nie wykazały problemów. Paczka zawiera 25 plików; sprawdzono
manifest, uprawnienia, CRC oraz identyczność dwóch niezależnych buildów.

Nie wykonano publikacji ani testu nowego wydania na działającym serwerze.
[Publiczny wpis](https://plugins.qgis.org/plugins/qgis_poprawka_odwzorowawcza/)
w chwili sprawdzania miał wersję 1.0.1, stare polskie opisy oraz nazwę
„Poprawka odwzorowawcza”. Przy publikacji końcowej należy:

1. Nadać aktualizacji nowy numer wersji i odbudować ZIP z zatwierdzonego kodu.
2. Uzgodnić zmianę nazwy wpisu na „Poprawka odwzorowawcza PL-2000”, jeżeli
   portal jej nie przyjmie. Serwer zmienia nazwę z metadanych wyłącznie przy
   włączonym `Allow update name`, domyślnie wyłączonym. Zwykły formularz
   edycji wtyczki nie udostępnia tego pola; może być potrzebny administrator.
3. Po publikacji sprawdzić nazwę, oba opisy i tagi na stronie oraz po
   aktualizacji przez menedżer QGIS. Poprawna nazwa i treść lokalnego ZIP-a
   nie zmieniają automatycznie istniejącego wpisu na portalu.

## Punkt 6 — 2026-09-05: QGIS 4 / Qt6

Zmiany względem `ef6c952`: zakres `qgisMinimumVersion=3.40` i
`qgisMaximumVersion=4.99`, spójne opisy PL/EN i okno informacji oraz pełne
testy PyQGIS w CI dla obu generacji QGIS. Kod obliczeń, naprawy, eksportu
oraz istniejące funkcje zgodności Qt5/Qt6 nie wymagały zmian.

### Rzeczywiste środowiska i wyniki

| Środowisko Linux, Python 3.14.4 | Pełny zestaw pytest |
| --- | --- |
| QGIS 3.40.15, Qt 5.15.18 | 225/225 |
| QGIS 4.2.2, Qt 6.10.2, PyQt 6.10.2 | 225/225 |

QGIS 4.2.2 pochodzi z oficjalnego repozytorium `qgis.org/ubuntu`, pakiety
`1:4.2.2+44resolute`. Pakiety oraz brakujące zależności rozpakowano do
osobnego katalogu testowego. Systemowy QGIS 3 i profil użytkownika nie były
podmieniane. Testy wskazywały właściwe biblioteki przez `QGIS_PREFIX_PATH`,
`PYTHONPATH` i `LD_LIBRARY_PATH`.

- Zestaw obejmuje niezależne referencje obliczeń, wszystkie strefy PL-2000,
  sprawdzanie geometrii w obu trybach, punkt średni przed/po naprawie,
  niezmienność źródła, zapis precyzji w GeoPackage oraz raport Markdown.
- Natywny czytnik menedżera wtyczek akceptuje finalny ZIP i odczytuje oba
  języki w lokalizacjach `pl_PL`, `en_US` i `de_DE`, na QGIS 3 i 4.
  Przed zmianą metadanych QGIS 4 odrzucał tę samą paczkę jako niezgodną.
- Dodano testy rzeczywistego modalnego dialogu: uruchomienie pętli zdarzeń,
  zatwierdzenie i anulowanie, bez zastępowania Qt atrapą.
- QGIS 4 dodaje do modelu Processing wbudowaną sekcję „Input parameters”.
  Test wyszukuje teraz provider przez natywne `indexForProvider`, zamiast
  zakładać, że cały model ma dokładnie jeden wiersz. Nadal sprawdza jeden
  algorytm bez pośredniej grupy i jego właściwy identyfikator.

### Uruchomienie pełnej aplikacji QGIS 4

Dodatkowy test wykonano w rzeczywistym QGIS Desktop 4.2.2, z osobnym
profilem oraz renderowaniem `offscreen`. Wykorzystano rozpakowany ZIP,
standardowy loader `qgis.utils` i rzeczywisty `iface`, bez atrapy aplikacji.
Potwierdzono:

1. Załadowanie i włączenie wtyczki, bezpośrednią akcję w menu Wtyczki oraz
   rejestrację providera Processing.
2. Otwarcie kalkulatora z akcji, obliczenie w obu trybach i wynik
   `10001,54 m²` dla kwadratu 100 × 100 m na południku osiowym strefy 7;
   geometria źródłowa pozostała identyczna bajtowo.
3. Eksport przez rzeczywiste okno zapisu pliku i `QSaveFile`; zapisany
   raport UTF-8 jest identyczny z bieżącym raportem okna.
4. Otwarcie i zamknięcie okna informacji oraz podgląd renderowania GUI.
5. Wywołanie algorytmu przez `processing.run`, zapis do GeoPackage i
   odczyt oczekiwanego wyniku `egib_area_m2`.
6. Wyłączenie, ponowne włączenie i wyłączenie; provider poprawnie znika
   z rejestru.

### Kontrole paczki i automatyzacja

- Oficjalny skrypt używany przez
  [pyqgis4-checker](https://github.com/qgis/pyqgis4-checker) uruchomiono
  w Qt6 na kodzie rozpakowanej paczki (25 plików w archiwum),
  bez importowalnego PyQt5.
  Tryb `--dry_run` nie zgłosił propozycji zmian ani błędów.
  Archiwalny plik `legacy/pow_QGIS_v1.py` nie jest częścią ZIP-a i nie był
  objęty tym skanem.
- Ruff, kontrola formatowania, Flake8, Bandit, detect-secrets i pip-audit:
  bez wykrytych problemów. Kompilacja utrzymywanego kodu przeszła.
- Testy paczki sprawdzają manifest, uprawnienia, nazwy i metadane;
  CRC jest poprawne, dwa zbudowania dały identyczne archiwa.
- Workflow Quality ma dodatkową macierz QGIS 3.44.11/Qt5 i 4.2.2/Qt6,
  w oficjalnych obrazach przypiętych digestem. Sprawdza rzeczywiste wersje
  bibliotek przed uruchomieniem wszystkich testów. PyQGIS i pytest są już
  w obrazach; wtyczka nie dostaje nowych zależności.
- Sprawdzono składnię YAML i zawartego kodu Python. Zdalne wykonanie nowego
  zadania GitHub Actions nastąpi dopiero po wysłaniu zmian do GitHuba;
  powyższe wyniki pytest pochodzą z testów lokalnych.

Zgodnie z [aktualnymi zasadami migracji QGIS](https://plugins.qgis.org/docs/migrate-qgis4)
zgodność deklaruje zakres wersji. Nie dodano usuniętej flagi `supportsQt6`.
Sprawdzono również, że czytniki metadanych wydań QGIS 4.0.0 i 4.0.3 nie
wymagają tej flagi; nie uruchamiano jednak tych wydań.

Ostrzeżenia `codecs.open` pochodzą z menedżera QGIS 3 na Pythonie 3.14.
QGIS 4 przy zamykaniu procesu testowego wypisuje komunikaty
`QThreadStorage`; pełny zestaw i test Desktop kończą się kodem 0.
Renderowanie `offscreen` zgłasza ograniczenia `propagateSizeHints`.
Nie wykonano testów na Windows ani macOS, ani publikacji w repozytorium
QGIS. Numer wydania nadal wynosi 1.0.1; przed publikacją aktualizacji trzeba
nadać nowy numer i zbudować paczkę z zatwierdzonego kodu.
