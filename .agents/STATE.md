# Stan prac — 2026-09-05

## Punkt zatrzymania

Punkty 1–7 zostały zatwierdzone w commicie
`404cf69675157fa4ccfb4492f5ba2c6afebfb28a`. CI tego commitu przeszło.
Użytkownik sprawdził paczkę w QGIS. Podczas przygotowywania publikacji
powstał nieopublikowany draft GitHub Release `v1.1.0`.

Użytkownik następnie wstrzymał publikację i zlecił krótsze metadane:
krótki opis PL przed EN, bez dopisku o bezpłatności; około 100 słów opisu
szczegółowego na język i changelog z punktami w nowych wierszach.
Ta korekta i testy są lokalne, jeszcze niezacommitowane. Nowy ZIP 1.1.0
czeka na ponowny test użytkownika. Dopiero potem publikacja GitHub i QGIS.

Draft na GitHubie zawiera POPRZEDNIĄ paczkę i wskazuje commit 404cf69.
Przed publikacją trzeba wymienić załączniki, sprawdzić nazwy pobieranych
plików i zgodność sumy kontrolnej oraz wskazać commit nowej korekty z CI.
Nie publikuj starego draftu bez tych zmian. Nie wysłano paczki do QGIS.

## Stan produktu i decyzje

- Oba tryby sprawdzają geometrię po transformacji kopii do PL-2000.
  Bez naprawy: bez `makeValid()`, P₀ i P_GK z niezmienionej granicy w tym
  układzie. Z naprawą: obie wartości z tej samej poprawionej kopii.
  P_GK to średnia unikalnych par XY granicy, nie centroid ważony polem.
  Wynik niepoprawnej geometrii bez naprawy ma oznaczenie diagnostyczne.
- Pełna precyzja parametrów w GeoPackage; dotychczasowa precyzja wyświetlania
  pozostaje. Pomocniczy pomiar geodezyjny QGIS jest oddzielny od wyniku
  według rozporządzenia; jego błąd nie blokuje głównego wyniku.
- Raport Markdown wystarcza na obecny etap (#3); nie dodawać teraz ODT/DOCX.
- #4 zrealizowano według decyzji użytkownika: płaskie menu Wtyczki,
  wszędzie nazwa „Poprawka odwzorowawcza PL-2000”. Propozycja innej etykiety
  w PR #5 nie zastępuje tej decyzji.
- QGIS 3.40–3.x i 4.x (`qgisMaximumVersion=4.99`), bez `supportsQt6`.
- Tagi PL/EN parami, również poprawka odwzorowawcza / projection correction
  oraz rozporządzenie egib / land and building register regulation.
  Usunięty tag organizacji nie powinien wracać do metadanych.
- README PL/EN, metadane i okno informacji wyjaśniają zastosowanie,
  przepisy i bezpłatną licencję GNU GPL v2. Nie deklarują niepotwierdzonego
  pierwszeństwa ani wcześniejszej wyłączności płatnych programów.
- Zachowano informacje o vibe codingu, odpowiedzialności, lokalnym
  działaniu i kontrolach bezpieczeństwa bez deklarowania certyfikacji.

## Wydanie i porządek

Gotowe w `dist/`: `Poprawka odwzorowawcza PL-2000-1.1.0.zip` i `.zip.sha256`.
25 plików, 58 142 bajtów. SHA-256:
`a690174d4feed81af8f1f07fd31d8f5df9bf2e42386f7a7c8c26800bf4da338b`.
`dist/` jest ignorowany przez Git. Materiały agentów nie zmieniają ZIP-a.

- [Opis release'u PL/EN](../docs/RELEASE_NOTES.md).
- [Instrukcja publikacji](../docs/PUBLISHING.md).
- [Pełny raport walidacji](../docs/RELEASE_VALIDATION.md).

Usunięto stary `legacy/pow_QGIS_v1.py`, zakończone plany `docs/archive/`
i nieużywany `docs/images/dialog-preview.png`; są w historii Git.
Zachowano dowody obliczeń, źródła prawne i historyczny audyt bezpieczeństwa.
Zaktualizowano politykę bezpieczeństwa i instrukcje wydania.

## Wyniki kontroli

Po skróceniu metadanych ponownie: 225/225 testów na QGIS 3.40 i 4.2,
Flake8, Ruff lint i formatowanie, Bandit oraz checker Qt6 — poprawne.
Czytnik menedżera potwierdza kolejność PL/EN i 12 punktów changelogu.


Finalne źródła 1.1.0: **225/225 testów** na każdym z dwóch środowisk Linux:
QGIS 3.40.15 / Qt 5.15.18 i QGIS 4.2.2 / Qt 6.10.2, Python 3.14.4.
Pełny Desktop QGIS 4: loader ZIP-a, GUI, oba tryby, MD, GeoPackage,
opisy i wersja, wyłączenie / ponowne włączenie — zaliczone.

Ruff, formatowanie, Flake8, Bandit, detect-secrets, pip-audit, kompilacja,
checker Qt6 i deterministyczne pakowanie — zaliczone. Przy zamknięciu
sesji ponowiono na rzeczywistym repo:

- Flake8 7.3.0 (pycodestyle 2.14.0): zero zgłoszeń.
- Ruff 0.16.0 `check --no-cache .`: zero zgłoszeń.
- Ruff `format --check --no-cache .`: 49 plików poprawnie sformatowanych.

To automatyczna kontrola PEP 8 w zakresie pycodestyle/Flake8 i konfiguracji
projektu. Nazwy metod API QGIS/Qt mają celowe wyjątki `N802`; nazwa katalogu
repozytorium `N999`. Nie zmieniaj wymaganych nazw API na snake_case.

CI commitu c19a802 przeszło także w oficjalnych obrazach QGIS 3.44.11/Qt5
i 4.2.2/Qt6. CI nowych zmian trzeba sprawdzić po ich wysłaniu. Windows
ani macOS nie były testowane. Ostrzeżenia QGIS/Qt opisuje raport walidacji.

## Wznowienie

1. Sprawdź aktualne polecenie użytkownika, `git status` i HEAD.
2. Jeżeli zleci wydanie: commit, CI tego commitu, odbudowanie i porównanie
   ZIP-a, tag `v1.1.0`, release według przygotowanej instrukcji.
3. Portal QGIS może zachować dawną nazwę „Poprawka odwzorowawcza”. Zmiana
   wpisu zależy od `Allow update name`; może wymagać administratora.
4. Aktualizacje developerskie PR #1 i #6 to osobne zmiany; nie zakładaj,
   że ich stan na GitHubie jest nadal taki sam jak przy tej sesji.

Lokalne repo tej sesji: `/home/jerry/VSCode/qgis-poprawka-odwzorowawcza`.
Niektóre narzędzia wskazywały usunięty katalog profilu QGIS: podawaj jawnie
`workdir`. W nowej sesji ustal aktualny katalog i uprawnienia.
Środowiska testowe były tymczasowe: `/tmp/pl2000-audit-venv` oraz QGIS 4
rozpakowany w `/tmp/pl2000-qgis4` z ustawieniami w
`/tmp/pl2000-qgis4-env.sh`. Mogą już nie istnieć. Odtwarzaj środowisko według
CONTRIBUTING i CI; nie podmieniaj aktywnej instalacji/profilu użytkownika.

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
checker Qt6, CRC i powtarzalność ZIP-a — poprawne. Paczka czeka na test
użytkownika. Draft GitHub nadal zawiera starszą paczkę; publikacja wstrzymana.
