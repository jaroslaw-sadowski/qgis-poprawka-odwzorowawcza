# Walidacja kandydata wydania 0.1.0

Data: 2026-07-24  
Bazowy HEAD: `6efb73a2f7a566341d510c3e447b315127430ceb`  
Środowisko lokalne: Linux, QGIS 3.40.15, Qt 5.15.18, Python 3.14.4

Raport dotyczy bieżącego drzewa roboczego z poprawkami po audycie. Nie
zastępuje testów wydania na wspieranych systemach ani odbudowania artefaktu
z końcowego, oznaczonego commitu.

## Artefakt

- plik:
  `dist/qgis_poprawka_odwzorowawcza-0.1.0.zip`;
- rozmiar: 42 189 B;
- SHA-256:
  `6328bcea0acce12d7e318a579330d7f217e6a10d221961caf7cb8040a2590943`;
- zawartość: 20 plików pod jednym katalogiem
  `qgis_poprawka_odwzorowawcza/`;
- porównanie z jawnym manifestem: 20/20 plików zgodnych bajt w bajt;
- powtarzalność: drugi build miał identyczną sumę i wynik `cmp`.

## Kontrole po grupach zmian

| Grupa | Pytest | Bandit M/H | Flake8 | detect-secrets |
|---|---:|---:|---:|---:|
| Metadane i README | 90/90 | 0 | 0 | 0 |
| Builder ZIP i testy negatywne | 94/94 | 0 | 0 | 0 |
| Limity geometrii i selekcja | 101/101 | 0 | 0 | 0 |

Pełny końcowy Bandit na źródłach zgłosił 290 trafień. Wszystkie są
`B101`, mają poziom LOW i wysoką pewność, występują wyłącznie w testach oraz
odpowiadają użyciu instrukcji `assert`. Kod runtime ma 0 trafień.

Ruff odtwarza ustalenia jakościowe opisane już w audycie:

- dwa `B009` dla stałego `getattr()` — jeden w GUI i jeden w teście;
- `N802` dla `viewportEvent()`, którego nazwa wynika z API Qt;
- formatowanie trzech plików źródłowych odbiega od Ruff.

Nowe pliki i nowo dodane fragmenty nie zwiększają liczby tych trafień.
Ustalenia Ruff należą do sekcji „Zalecane”, nie do grupy blokującej
„Przed publikacją”.

## Kontrole dokładnej zawartości ZIP

| Kontrola | Wynik |
|---|---|
| `unzip -t` | 20/20 wpisów OK |
| Bandit | 0 trafień |
| Flake8 | 0 trafień |
| detect-secrets | 0 sekretów |
| porównanie ZIP–źródła | 20/20 plików zgodnych |
| deterministyczny rebuild | identyczny bajt w bajt |

Ruff uruchomiony na paczce z konfiguracją projektu odtwarza dwa dotyczące
runtime ustalenia bazowe: `B009` i świadomy wyjątek `N802`. Kontrola
formatowania wskazuje dwa bazowe pliki runtime.

## Klasyfikacja ręczna

- Nie znaleziono sekretów, wykonania poleceń, dostępu do sieci ani nowych
  zależności runtime.
- Builder przyjmuje tylko jawny manifest, odrzuca symlinki, pliki specjalne,
  wyjście poza katalog źródłowy i nieoczekiwane pliki w katalogach runtime.
- Geometria jest odrzucana przed transformacją, materializacją punktów
  i GEOS po przekroczeniu 10 000 części, 50 000 pierścieni lub 500 000
  współrzędnych.
- Zmiany nie modyfikują wzoru, stałych, mapowania osi, stref, PGK,
  zaokrąglania ani schematu obliczenia.

## Niewykonane bramki publikacji

W lokalnym środowisku nie ma QGIS 3.44 ani systemów Windows i macOS.
Przed publikacją nadal trzeba wykonać instalację z dokładnego ZIP oraz test
GUI, unload i Processing co najmniej na:

- QGIS 3.44 / Linux;
- QGIS 3.44 / Windows;
- QGIS 3.44 / macOS.

QGIS 4/Qt6 nie jest deklarowany w `metadata.txt` i nie wolno rozszerzać
`qgisMaximumVersion` przed rzeczywistym testem QGIS 4.

Po wykonaniu testów platformowych należy zaktualizować ten raport, utworzyć
końcowy commit lub tag, odbudować ZIP z tego stanu i ponownie zapisać jego
sumę SHA-256.
