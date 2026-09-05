# Poprawka odwzorowawcza PL-2000

**Polski** · [English](README.en.md)

Wtyczka QGIS do obliczania pola działek z uwzględnieniem poprawki
odwzorowawczej PL-2000. Pomaga sprawdzać powierzchnie działek istniejących
i projektowanych na potrzeby prac geodezyjnych i ewidencji gruntów.

Stosuje wzór z **§ 16 ust. 2 i załącznika nr 3 rozporządzenia z 27 lipca
2021 r. w sprawie ewidencji gruntów i budynków**
([Dz.U. 2024 poz. 219 ze zm.](https://eli.gov.pl/eli/DU/2024/219/ogl)).
Wynik podaje w m² i hektarach, z precyzją zapisu 0,0001 ha.

To inny sposób obliczenia niż natywne pole kartezjańskie QGIS (na
płaszczyźnie) i pomiar geodezyjny QGIS (na elipsoidzie). Wtyczka pokazuje
wszystkie trzy wartości do porównania. Wyniki mogą się nieznacznie różnić.

## Jak używać

Wymaga QGIS 3.40–3.x; instaluje się przez menedżer wtyczek, także z ZIP-a.
Interfejs jest polski. Wtyczka obejmuje Polskę, strefy PL-2000 5–8.
Opisy po polsku i angielsku są dostępne w menedżerze wtyczek i oknie
**O wtyczce…**.

- **Jedna działka:** zaznacz poligon i wybierz **Wtyczki → Poprawka
  odwzorowawcza PL-2000** lub ikonę na pasku wtyczek. Wskaż strefę, jeśli
  jest wymagana, i wybierz **Przelicz**. Raport zapiszesz przyciskiem
  **Zapisz raport MD…**.
- **Wiele działek:** wyszukaj **Poprawka odwzorowawcza PL-2000** w panelu
  Processing. Wynik zapisz do nowej warstwy, najlepiej GeoPackage.

Domyślnie sprawdza geometrię bez naprawiania. Opcjonalna naprawa działa
na kopii. Wynik dla błędnej geometrii bez naprawy jest tylko diagnostyczny.

## Prywatność i odpowiedzialność

Działa lokalnie i **nie wysyła danych na zewnątrz**. Nie zmienia warstwy
źródłowej. Korzysta tylko z bibliotek i narzędzi dostarczanych z QGIS oraz
standardowej biblioteki Pythona; nie wymaga dodatkowych instalacji.

Projekt powstał metodą **vibe coding**, z pomocą AI. **Autor nie bierze
odpowiedzialności za wyniki ani skutki ich wykorzystania**, w zakresie
dopuszczonym prawem. Przed zastosowaniem wyniku sprawdź dane, układ
współrzędnych, przebieg granic i aktualność przepisów.

## Wykonane kontrole

Lokalnie przeszedł kontrole opisane w
[zaleceniach QGIS](https://plugins.qgis.org/docs/security-scanning/tools):

- **Bandit** — bezpieczeństwo kodu Python.
- **detect-secrets** — brak wykrytych haseł, kluczy i tokenów.
- **Flake8** — błędy i jakość kodu.
- **Analiza ZIP-a** — struktura, uprawnienia oraz brak ukrytych plików,
  plików wykonywalnych i niepożądanych dodatków.

Dodatkowo wykonano kontrole Ruff, audyt zależności developerskich pip-audit,
testy obliczeń, geometrii, zapisu wyników i raportu oraz powtarzalności
budowania paczki. To kontrole lokalne, nie certyfikat QGIS ani gwarancja
poprawności każdych danych.

Autor: **Jarosław Sadowski** · Licencja: **GNU GPL v2**.
[Podstawa prawna i ograniczenia](https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/blob/main/docs/LEGAL_BASIS.md)
· [Zgłoszenia](https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/issues)
· [Dla współtwórców](https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/blob/main/CONTRIBUTING.md)
