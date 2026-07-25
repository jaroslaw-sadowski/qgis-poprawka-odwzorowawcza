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
