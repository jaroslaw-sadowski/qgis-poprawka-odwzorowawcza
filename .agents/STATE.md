# Stan prac — 2026-09-05

## Punkt zatrzymania

Punkty 1–7 zakończone lokalnie. Użytkownik poprosił o potwierdzenie
PEP 8/Ruff, zapisanie stanu i zakończenie pracy na teraz. Nie kontynuuj
publikacji bez nowego polecenia.

Przy zapisie HEAD: `c19a80249769d0f3eb418e0d429dcaaa35872f55` (punkt 6).
Zmiany punktu 7 / wersji **1.1.0** oraz niniejsze materiały nie są jeszcze
zacommitowane. Nie cofaj ich jako przypadkowego brudnego drzewa.
Proponowany commit: `chore: prepare 1.1.0 release and clean repository`.
Nie utworzono taga 1.1.0 ani GitHub Release, nie wysłano ZIP-a do QGIS.

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
25 plików, 59 440 bajtów. SHA-256:
`710ee8dfc1c0764ecc428d7928c3c1f773c0f9457f9a19f6f7b917a33a773c87`.
`dist/` jest ignorowany przez Git. Materiały agentów nie zmieniają ZIP-a.

- [Opis release'u PL/EN](../docs/RELEASE_NOTES.md).
- [Instrukcja publikacji](../docs/PUBLISHING.md).
- [Pełny raport walidacji](../docs/RELEASE_VALIDATION.md).

Usunięto stary `legacy/pow_QGIS_v1.py`, zakończone plany `docs/archive/`
i nieużywany `docs/images/dialog-preview.png`; są w historii Git.
Zachowano dowody obliczeń, źródła prawne i historyczny audyt bezpieczeństwa.
Zaktualizowano politykę bezpieczeństwa i instrukcje wydania.

## Wyniki kontroli

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
