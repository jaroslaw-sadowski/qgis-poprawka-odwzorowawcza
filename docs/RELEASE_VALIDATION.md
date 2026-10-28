# Walidacja wydania 1.1.0 — 2026-09-05

Stan: [wydanie GitHub v1.1.0 opublikowane](https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/releases/tag/v1.1.0)
5 września 2026 r., jako stabilne i najnowsze. Tag wskazuje commit
`6dc50de8de58bd70f35a12692354dcfb67cd2c5b`, obejmujący zatwierdzone korekty
metadanych. Użytkownik sprawdził wtyczkę w QGIS i zatwierdził publikację.
Użytkownik potwierdził wgranie paczki 1.1.0 do plugins.qgis.org.
Status zatwierdzenia przez administratorów nie był weryfikowany.

## Artefakt

- Nazwa: `Poprawka odwzorowawcza PL-2000-1.1.0.zip`.
- Rozmiar: 58 142 bajtów; 25 plików.
- Jeden katalog instalacyjny: `qgis_poprawka_odwzorowawcza`.
- SHA-256: `a690174d4feed81af8f1f07fd31d8f5df9bf2e42386f7a7c8c26800bf4da338b`.
- Obok paczki jest plik `.zip.sha256` do kontroli pobranego archiwum.
- Nazwa publiczna, wersja, oba języki opisu i pary tagów są w metadanych.
  Zakres QGIS: `3.40–4.99`, bez nieużywanej flagi `supportsQt6`.

Dwa niezależne buildy dały identyczne archiwa. Kontrola CRC przeszła.
Test manifestu potwierdza zgodność każdego pliku ze źródłami, uprawnienia
`0644` i brak symlinków, ukrytych plików, cache, testów, narzędzi
programistycznych oraz materiałów roboczych w ZIP-ie. Oba README i pełna
licencja GNU GPL v2 są dołączone.

## Obliczenia i integracja

Pełny zestaw uruchomiono ponownie na finalnych źródłach 1.1.0:

| Lokalne środowisko Linux, Python 3.14.4 | Wynik |
| --- | --- |
| QGIS 3.40.15 / Qt 5.15.18 | 225/225 testów |
| QGIS 4.2.2 / Qt 6.10.2 / PyQt 6.10.2 | 225/225 testów |

Testy obejmują niezależne referencje wzoru, strefy i transformacje,
zaokrąglenia, kontrolę bez naprawy i z naprawą, źródło punktu średniego,
niezmienność danych wejściowych, GUI, Processing, GeoPackage i raport MD.
Natywny czytnik menedżera akceptuje ZIP oraz odczytuje opisy PL/EN dla
`pl_PL`, `en_US` i `de_DE` w obu generacjach QGIS.

Przed późniejszą korektą metadanych ZIP uruchomiono przez standardowy loader w pełnym
QGIS Desktop 4.2.2, w czystym profilu i trybie `offscreen`. Potwierdzono:

- załadowanie, akcję w menu Wtyczki i provider Processing;
- działanie kalkulatora w obu trybach i niezmienność źródła;
- wynik `10001,54 m²` dla kwadratu 100 × 100 m na osi strefy 7;
- zapis MD przez rzeczywiste okno pliku i `QSaveFile`, zgodny z raportem;
- wersję 1.1.0, opisy PL/EN i licencję w oknie informacji;
- `processing.run`, zapis GeoPackage i odczyt oczekiwanego wyniku;
- wyłączenie, ponowne włączenie i wyłączenie wtyczki.

W punkcie 7 nie zmieniono kodu wzoru, przygotowania geometrii, naprawy,
Processing, eksportu raportu ani funkcji zgodności Qt5/Qt6.
[Niezależne referencje obliczeń](CALCULATION_VALIDATION_2026-09-05.md)
i [podstawa prawna](LEGAL_BASIS.md) zachowują aktualność dla tego kodu.

## Jakość i bezpieczeństwo

Bez wykrytych problemów: Ruff, kontrola formatowania, Flake8, Bandit,
detect-secrets i pip-audit. Kompilacja kodu przeszła. Bandit i kontrola
sekretów objęły także rozpakowany ZIP. Kontrola odsyłaczy względnych
w utrzymywanej dokumentacji nie wykazała brakujących celów.

Oficjalny skrypt używany przez
[pyqgis4-checker](https://github.com/qgis/pyqgis4-checker), uruchomiony
w Qt6 na kodzie rozpakowanego ZIP-a, nie zgłosił propozycji zmian.
W tym procesie PyQt5 nie był dostępny do importu. Są to kontrole lokalne
według [zaleceń QGIS](https://plugins.qgis.org/docs/security-scanning/tools),
a nie certyfikat ani wynik skanowania nowej wersji na plugins.qgis.org.

[CI bazowego commitu c19a802](https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/actions/runs/33973305815)
zakończyło się poprawnie we wszystkich trzech zadaniach: Source quality,
QGIS 3.44.11/Qt5 oraz QGIS 4.2.2/Qt6.
[CI finalnego commitu 6dc50de](https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/actions/runs/33980039690)
również zakończyło się powodzeniem.

## Porządek i zakres wydania

- Usunięto stary skrypt `legacy/pow_QGIS_v1.py`, zakończone plany
  `docs/archive/` i nieużywany `docs/images/dialog-preview.png`.
- Usunięto wyjątki lintowania dotyczące starego skryptu.
- Zastąpiono stare instrukcje publikacji i zbiorczy raport aktualnym
  opisem wydania; poprawiono nieaktualną politykę bezpieczeństwa.
- Zachowano źródła prawne, niezależny generator referencji, testy oraz
  oznaczony jako historyczny [audyt bezpieczeństwa](SECURITY_AUDIT_2026-07-24.md).
- Starszy raport i usunięte materiały są dostępne w historii Git:
  [stan przed porządkowaniem](https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/tree/c19a80249769d0f3eb418e0d429dcaaa35872f55).
- #3: gotowy eksport Markdown; ODT/DOCX nie należą do tego wydania.
  #4: ujednolicona nazwa i płaskie menu Wtyczki według decyzji autora.
  PR #5 proponuje inną etykietę wyniku; zachowano uzgodnioną nazwę.
  Aktualizacje narzędzi z PR #1 i #6 pozostają osobnymi zmianami.

Opisy PL/EN mówią o bezpłatnym obliczeniu w QGIS i otwartej licencji.
Nie deklarują pierwszeństwa na rynku ani wcześniejszej wyłączności
płatnych programów, których nie udało się potwierdzić.

## Granice weryfikacji i publikacja

Na etapie walidacji z 5 września nie wykonano testów na Windows ani macOS.
Późniejszy ręczny test Windows 11 opisano w uzupełnieniu poniżej.
Ostrzeżenia `codecs.open`
pochodzą z menedżera QGIS 3 na Pythonie 3.14; komunikaty `QThreadStorage`
i `propagateSizeHints` pochodzą z QGIS/Qt w środowisku testowym.
Testy i uruchomienie Desktop zakończyły się kodem 0.

Po poprawnym CI odbudowano identyczny ZIP i zweryfikowano pobrane
załączniki GitHub przez SHA-256 i porównanie bajtowe. GitHub zastąpił
spacje kropkami w nazwie pliku: `Poprawka.odwzorowawcza.PL-2000-1.1.0.zip`;
dołączona suma kontrolna uwzględnia tę nazwę. Tag i załączniki wydania
zweryfikowano po publikacji. Opis wydania: [RELEASE_NOTES.md](RELEASE_NOTES.md).
Użytkownik potwierdził przesłanie paczki do katalogu QGIS. Nie sprawdzano
jeszcze decyzji administratorów. Instrukcja: [PUBLISHING.md](PUBLISHING.md).

## Korekta opisów przed ponownym testem użytkownika

Opis krótki zaczyna się od PL, następnie EN, bez dopisku o bezpłatności.
Opis szczegółowy ma około 100 słów na język: funkcja i rozporządzenie,
brak potrzeby zakupu programu geodezyjnego, vibe coding, lokalność,
biblioteki QGIS, kontrole i odpowiedzialność; pozostałe informacje
wskazuje odsyłacz do GitHuba. Changelog: sekcje POLSKI i ENGLISH, po
sześć punktów w osobnych wierszach. README pozostają bez zmian.

225/225 testów ponownie przeszło na QGIS 3.40 i 4.2. Natywny czytnik
metadanych z ZIP-a sprawdza oba języki i zachowanie nowych linii
changelogu dla pl_PL, en_US i de_DE. Ruff, Flake8, Bandit i checker Qt6
przeszły; dwa buildy są identyczne i CRC jest poprawne.
Aktualny artefakt jest opisany na początku tego raportu. Po sprawdzeniu
użytkownika został opublikowany w GitHub Release 1.1.0.

## Ręczna korekta metadanych i e-mail — 2026-09-05

Uwzględniono ręcznie zmienioną treść użytkownika i nagłówki PL / EN.
Dodano wcięcie kontynuacji wiersza angielskiego description, aby nie
powstawał osobny klucz INI; poprawiono literówkę GitHun na GitHub.
Odczyt angielskiej części w oknie informacji dostosowano do nagłówka EN.

Adres w pobranej opublikowanej paczce QGIS 1.0.1 i nowym ZIP-ie:
`github.com.amenity983@passfwd.com`. To jedyny adres e-mail znaleziony
w zawartości nowego ZIP-a; występuje w metadata.txt. Weryfikacja nie
obejmowała wysyłania wiadomości ani sprawdzania dostarczalności poczty.
Ponownie: 225/225 testów na QGIS 3.40 i 4.2; Flake8, Ruff, Bandit,
checker Qt6, CRC i powtarzalność ZIP-a — poprawne. Użytkownik zaakceptował
paczkę; opublikowany GitHub Release zawiera ten finalny ZIP.

## Ostateczna kontrola nazwy i nowych linii

Pełna nazwa „Poprawka odwzorowawcza PL-2000” jest spójna w metadanych,
menu, GUI, Processing, raporcie i nazwie paczki. Krótki opis zachowuje
kolejność PL, następnie EN. Menedżer QGIS 3.44 i 4.2 renderuje go jako
HTML bez zamiany nowych linii na znaczniki podziału; Qt5 i Qt6 scalają
nową linię do spacji. Nie wymuszano podziału przez HTML, którego
[zasady metadanych QGIS](https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/plugins.html#metadata-txt)
nie dopuszczają. Opis szczegółowy i changelog mają osobne wiersze.

## Uzupełnienie po publikacji — 2026-09-06

### Porównanie powierzchni z dwoma programami geodezyjnymi

Sprawdzono działkę `100102_2.0026.477/4` na podstawie WKT przekazanego
przez użytkownika w układzie EPSG:2177. Poligon zawiera jeden otwór
i 83 unikalne punkty graniczne. QGIS potwierdził poprawność geometrii.

Test wywoływał funkcje geometrii i obliczeń wtyczki z katalogów `adapters/`
i `core/`, których zawartość była zgodna z tagiem `v1.1.0`. Uruchomiono go
lokalnie na Linuxie w QGIS 3.40.15 i 4.2.2; oba środowiska dały identyczne
wyniki. Zastosowanie `makeValid()` nie zmieniło powierzchni ani wyniku
poprawki. Niezależne obliczenie pola wzorem Gaussa z użyciem `Decimal`
dało 616 289,5481 m², zgodnie z wynikiem QGIS do pokazanych czterech
miejsc po przecinku.

Wyniki porównano ze zrzutami `1.png` i `2.png`, przekazanymi przez
użytkownika jako wyniki dwóch zewnętrznych specjalistycznych programów
geodezyjnych. Nazw i wersji tych programów nie podano.

| Wielkość | Wtyczka | Program ze zrzutu `1.png` | Program ze zrzutu `2.png` |
| --- | ---: | ---: | ---: |
| Powierzchnia przed poprawką | 616 289,5481 m² | 61,6290 ha | 616 290 m² |
| Odejmowana poprawka odwzorowawcza | 36,6371 m² | 0,0037 ha | Nie pokazano osobno |
| Powierzchnia po poprawce | 616 252,9110 m² | 61,6253 ha | 616 253 m² |

Potwierdzono zgodność powierzchni przed i po poprawce z oboma programami,
z dokładnością prezentowaną na zrzutach (1 m², czyli 0,0001 ha).
Poprawka jest również zgodna z wartością pokazaną w `1.png`.
Wniosek dotyczy tej jednej geometrii i wymienionych wartości powierzchni;
nie obejmuje obwodu, dopuszczalnych odchyłek ani identyczności algorytmów
zewnętrznych programów. Było to porównanie ze zrzutami użytkownika,
bez uruchamiania tych programów przez autora testu.

### Ręczny test paczki na Windows 11

6 września 2026 r. użytkownik potwierdził pomyślny ręczny test paczki ZIP
wydania 1.1.0 na innym komputerze z Windows 11 i QGIS
3.40.15-Bratislava. Potwierdzenie dotyczy działania paczki w tym
środowisku w zakresie ręcznego testu użytkownika. Nie przekazano
szczegółowej listy wykonanych czynności; nie jest to wynik pełnego
zestawu testów automatycznych ani CI na Windows.

## Weryfikacja lokalnego kandydata 1.1.1 — 2026-10-28

Wersja 1.1.1 jest przygotowana lokalnie. Użytkownik zlecił zapis zmian
w commicie, bez tagu, pushu ani publikacji. Wydanie 1.1.0 i jego paczka pozostają
niezmienione. Powyższe wyniki dotyczą 1.1.0.

Zmiany obejmują ochronę zapisu Processing, zachowanie źródłowego fid,
kolizje nazw, kontrolę bufora zapisu i ostrzeżenie o ograniczeniach SHP.
Wynik ma rzeczywiste nazwy wszystkich 27 dodawanych pól z prefiksem PO_,
m.in. PO_P0_m2, PO_dP_m2, PO_P_m2, PO_P_ha, PO_QGIS_m2, PO_status
i PO_uwagi. Polskie aliasy zaczynają się nazwą pola. Układ tabeli
zapisuje się w GeoPackage; dodano podsumowanie i informację o anulowaniu.
Starsze modele i wyrażenia odwołujące się do egib_* wymagają aktualizacji;
identyfikator algorytmu egib_area:calculate_egib_area pozostaje bez zmian.
Raport MD zawiera czas z offsetem, wersję i etykietę obiektu QGIS.
Transformacja zastępcza jest oznaczana również dla wcześniejszych części
wielopoligonu; po naprawie ponownie sprawdzane są limity geometrii.
Wzór, osie, P_GK i zaokrąglenia pozostają bez zmian.

| Lokalne środowisko Linux, Python 3.14.4 | Wynik |
| --- | --- |
| QGIS 3.40.15 / Qt 5.15.18 | 280/280 testów, kod 0 |
| QGIS 4.2.2 / Qt 6.10.2 | 280/280 testów, kod 0 |

Nowe przypadki sprawdzają rzeczywisty zapis i niezmienność źródeł, wybór
zaznaczonych obiektów, URI, dowiązania i rozszerzenia dopisywane przez QGIS,
nową tabelę w tej samej bazie, fid, błędy zapisu, oba tryby geometrii,
raport oraz ponowne otwarcie GeoPackage z rzeczywistymi nazwami PO_*,
aliasami i układem tabeli. Algorytm nie dodaje nowych pól egib_*;
istniejące źródłowe atrybuty egib_* są zachowywane jak pozostałe dane.
Testy nie wymagają rozluźnienia tolerancji istniejących referencji.

Ruff 0.16.0 (lint i format), Flake8 7.3.0, Bandit 1.9.4,
detect-secrets 1.5.0, pip-audit 2.10.1 i kompilacja zakończyły się poprawnie.
pip-audit nie wykrył znanych podatności w zależnościach developerskich.
Bandit, Flake8 i detect-secrets objęły również rozpakowany ZIP;
pełny skan sekretów wszystkich 25 plików nie wykrył zgłoszeń.
Workflow Quality wykonuje te kontrole także na gotowej paczce.
Oficjalny skrypt pyqgis4-checker uruchomiony w Qt6 w trybie dry_run
nie zgłosił zmian; nie zastępuje to powyższych testów rzeczywistego QGIS 4.

Paczka: `Poprawka odwzorowawcza PL-2000-1.1.1.zip`, 25 plików,
63 067 bajtów. SHA-256:
`aa35fd2b39e59b52ddf08dfb3482f29492c445bc83e1c1bbba0a315996dd5df6`.
Dwa buildy są identyczne; CRC i suma kontrolna poprawne. Do runtime
nie dodano zależności, narzędzi developerskich ani materiałów agentów.

Ostrzeżenia QGIS 3 o codecs.open i komunikaty zamykania QThreadStorage
w QGIS 4 pochodzą z bibliotek środowiska; oba procesy zakończyły się
kodem 0. QGIS 4 i jego zależności rozpakowano wyłącznie do /tmp,
bez zmiany systemowej instalacji i profilu QGIS.

Nie wykonano testów 1.1.1 na Windows/macOS ani na rzeczywistym serwerze
PostGIS. Kontrola PostGIS obejmuje porównanie URI, port domyślny i schemat;
równoważne aliasy adresu serwera mogą wymagać dodatkowej weryfikacji.
Nie wykonano CI nowego commitu ani skanowania na plugins.qgis.org.
