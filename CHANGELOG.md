# Changelog

Wszystkie istotne zmiany projektu są dokumentowane w tym pliku. Projekt
stosuje [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-09-05

### Changed

- Skrócono opisy menedżera QGIS, ustawiono PL przed EN i zapisano
  dziennik zmian w czytelnych punktach dla obu języków.

- Opisy PL/EN wyjaśniają, jaki problem rozwiązuje wtyczka: obliczenie
  wymaganej poprawki w bezpłatnym QGIS, bez zakupu komercyjnego pakietu
  geodezyjnego; bezpłatny kod na licencji GNU GPL v2.
- Usunięto stary skrypt, zakończone plany wdrożenia i nieużywany podgląd
  okna. Uaktualniono instrukcję publikacji i politykę bezpieczeństwa.

- Obsługa QGIS 4.x obok QGIS 3.40–3.x, potwierdzona na QGIS 4.2.2/Qt6.
  Metadane dopuszczają instalację do wersji 4.99; opisy PL/EN i okno
  informacji pokazują ten sam zakres obsługi.

- Standardowe pola description, about i changelog zawierają polski
  i angielski tekst, widoczny niezależnie od języka menedżera QGIS.
- Tagi tematyczne są w parach polski–angielski; PL-2000 jest wspólny
  dla obu języków. Usunięto tag organizacji.

- Bezpośredni wpis w menu Wtyczki i ikona na pasku wtyczek; informacje
  „O wtyczce” dostępne w oknie obliczenia, bez dodatkowych podmenu.
- Ujednolicono nazwę widoczną w menu, Processing, oknach, raporcie i nazwie
  ZIP-a: „Poprawka odwzorowawcza PL-2000”. Usunięto podgrupę Processing.
- Skrócono README i opis w menedżerze QGIS: zastosowanie, przepisy,
  prywatność, vibe coding, odpowiedzialność oraz wykonane kontrole.

- Nieudany pomocniczy pomiar QGIS na GRS 80 nie blokuje wyniku według
  wzoru PL-2000; GUI i Processing zgłaszają osobne ostrzeżenie.
- Zmiana ustawień oraz nieudane obliczenie usuwają stary raport i wyłączają
  jego eksport.

- Oba tryby sprawdzają poprawność geometrii GEOS. Tryb bez naprawy zachowuje
  granice źródłowe po transformacji do PL-2000, a wynik dla niepoprawnej
  geometrii oznacza jako diagnostyczny (`invalid_source_geometry`).
- W trybie naprawy pole P₀ i punkt średni P_GK pochodzą z tej samej
  poprawionej kopii, z uwzględnieniem dodanych i usuniętych wierzchołków.
- Usunięto ograniczenie liczby miejsc dziesiętnych w polach P_GK, sigma
  i skali, aby GeoPackage zachowywał pełne parametry obliczenia.
- Zaktualizowano opisy trybów i wyjaśnienia diagnostyki w GUI i Processing.

### Added

- Pełne testy PyQGIS w CI dla QGIS 3.44.11/Qt5 i 4.2.2/Qt6.
  Testy korzystają z właściwego prefiksu instalacji i sprawdzają natywne
  otwieranie oraz zamykanie dialogu. Kontrola płaskiego układu Processing
  uwzględnia wbudowaną sekcję parametrów wejściowych w QGIS 4.

- Angielskie README dołączone także do ZIP-a, z odsyłaczami między językami.
- Angielski opis w oknie „O wtyczce”, pobierany z metadanych; polski opis
  i interfejs pozostają domyślne.

- Eksport bieżącego raportu pojedynczej działki do Markdown (UTF-8),
  z zachowaniem prezentowanej precyzji, diagnostyki i ostrzeżeń; realizacja
  części Markdown zgłoszenia #3. Zapis chroni istniejący plik przy błędzie.
- Testy awarii pomiaru porównawczego, aktualności raportu i eksportu,
  w tym anulowania oraz błędów otwarcia, zapisu i zatwierdzenia pliku.

- Niezależne referencje wzoru obliczone dokładnie na ułamkach, wraz
  z odtwarzalnym generatorem i opisem podstawy prawnej.
- Testy zgodności GUI, Processing i GeoPackage, transformacji do czterech
  stref, źródła punktu P_GK, otworów, wielopoligonów i zaokrągleń.

## 1.0.1 - 2026-07-25

### Changed

- Rozszerzono nazwę wyświetlaną w metadanych, menu, oknach i dokumentacji
  do „Poprawka odwzorowawcza PL-2000”.
- Zapis flagi `QgsFeatureSink.Flag.FastInsert` dostosowano do checkera
  zgodności Qt6/QGIS 4 przy zachowaniu wsparcia QGIS 3.40.

## [1.0.0] - 2026-07-25

### Added

- Pierwsze stabilne publiczne wydanie.
- Dialog obliczenia dla jednej zaznaczonej działki.
- Algorytm Processing do bezpiecznego przetwarzania wielu obiektów.
- Diagnostyka geometrii i opcjonalna naprawa kopii metodami GEOS.
- Deterministyczny, walidowany builder paczki QGIS.
- Testy modułu obliczeniowego, integracji PyQGIS, GUI i paczkowania.
- Spójny motyw wizualny, okno „O wtyczce” i ikona repozytorium QGIS.
- Dokumentacja użytkowa i społecznościowa oraz formularze zgłoszeń.
- Workflow CI dla jakości źródeł, skanerów i powtarzalności paczki.
- Porównawczy pomiar geodezyjny QGIS na elipsoidzie GRS 80 w dialogu
  i polu `egib_qgis_m2` warstwy Processing.

### Changed

- Wszystkie opisy metadanych wtyczki przetłumaczono na język polski.
- Opis publikacyjny uproszczono i ukierunkowano na potrzeby użytkownika.
- Do tagów dodano „powierzchnia” i „Stowarzyszenie QGIS Polska”.
- Jednoznacznie opisano `P₀` jako pole matematyczne/kartezjańskie, a wynik
  geodezyjny QGIS jako wartość porównawczą wobec głównego wyniku prawnego.
- Techniczny krój pisma wymuszono na wszystkich kontrolkach Qt i raportach
  wtyczki, a nagłówek i piktogram okna „O wtyczce” zmniejszono zgodnie
  z charakterem dialogu.
- Ikonę PNG wyświetlaną przez Menedżer wtyczek QGIS zmniejszono z 256×256
  do 64×64 px.
- Adres kontaktowy wydania zmieniono na
  `github.com.amenity983@passfwd.com`.
- Opis w Menedżerze wtyczek uzupełniono o § 16 ust. 2 i załącznik nr 3
  rozporządzenia EGiB.

### Security

- Limity złożoności geometrii wykonywane przed transformacją i GEOS.
- Jawny manifest plików paczki oraz odrzucanie symlinków i plików
  nieoczekiwanych.
- Brak komunikacji sieciowej, zależności pip i modyfikacji danych
  źródłowych.
- Bezpieczne komunikaty GUI, minimalne uprawnienia CI i akcje GitHub
  przypięte do pełnych identyfikatorów commitów.

[1.1.0]: https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/releases/tag/v1.0.0
