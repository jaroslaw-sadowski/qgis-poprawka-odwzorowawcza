# Stan prac — 2026-09-05

## Punkt zatrzymania

Opublikowano stabilne, najnowsze wydanie [GitHub v1.1.0](https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/releases/tag/v1.1.0).
Tag wskazuje `6dc50de8de58bd70f35a12692354dcfb67cd2c5b`; CI tego commitu
przeszło (run `33980039690`). Użytkownik sprawdził wtyczkę w QGIS i zlecił
publikację. Pobrane załączniki przeszły kontrolę SHA-256 oraz porównanie
bajtowe z lokalnym ZIP-em. Do plugins.qgis.org nie wysłano nowej wersji.
Nie przesuwaj opublikowanego tagu; późniejsze zmiany dokumentacji nie
zmieniają paczki wydania.

GitHub zamienił spacje w nazwie załącznika na kropki:
`Poprawka.odwzorowawcza.PL-2000-1.1.0.zip`. Etykieta pobierania zachowuje
spacje, a dołączona suma kontrolna używa faktycznej nazwy pobieranego pliku.

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

CI finalnego commitu `6dc50de` przeszło także w oficjalnych obrazach
QGIS 3.44.11/Qt5 i 4.2.2/Qt6 oraz w zadaniu Source quality. Windows
ani macOS nie były testowane. Ostrzeżenia QGIS/Qt opisuje raport walidacji.

## Wznowienie

1. Sprawdź aktualne polecenie użytkownika, `git status` i HEAD.
2. GitHub 1.1.0 jest opublikowany. Następny krok użytkownika: przesłanie
   tego samego ZIP-a na plugins.qgis.org według instrukcji publikacji.
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
checker Qt6, CRC i powtarzalność ZIP-a — poprawne. Użytkownik zaakceptował
paczkę; finalny ZIP jest załącznikiem opublikowanego wydania 1.1.0.

## Ostateczna kontrola nazwy i opisu

Pełna nazwa „Poprawka odwzorowawcza PL-2000” jest spójna w metadanych,
GUI, menu, Processing, raporcie i paczce. Menedżer QGIS 3.44/4.2 scala
nowe linie krótkiego opisu; sprawdzono źródła menedżera i renderowanie
Qt5/Qt6. HTML w metadanych jest niedozwolony, więc zachowano PL przed EN
z separatorem. Opis szczegółowy i changelog zachowują osobne wiersze.
Nie dodawać obejść zmieniających działanie menedżera QGIS.
