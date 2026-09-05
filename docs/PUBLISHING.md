# Przygotowanie i publikacja wydania

Aktualny kandydat: **1.1.0**. Nazwa publiczna: **Poprawka odwzorowawcza
PL-2000**. Wydanie obejmuje QGIS 3.40–3.x i 4.x.

## Paczka

Po zatwierdzeniu zmian odbuduj ZIP z tego samego commitu, na którym
powstanie tag wydania:

```bash
python scripts/build_plugin_zip.py
python -m zipfile -t "dist/Poprawka odwzorowawcza PL-2000-1.1.0.zip"
cd dist
sha256sum "Poprawka odwzorowawcza PL-2000-1.1.0.zip" > \
  "Poprawka odwzorowawcza PL-2000-1.1.0.zip.sha256"
sha256sum -c "Poprawka odwzorowawcza PL-2000-1.1.0.zip.sha256"
```

Do instalacji służy ten ZIP, zawierający jeden katalog Pythona
`qgis_poprawka_odwzorowawcza`. Automatyczne archiwa GitHuba „Source code”
zawierają repozytorium, a nie paczkę instalacyjną QGIS.

## Sprawdzenie

- Workflow **Quality** musi przejść dla commitu wydania: kontrola źródeł,
  bezpieczeństwa i testy QGIS 3.44/Qt5 oraz 4.2/Qt6.
- Wyniki i granice weryfikacji są w [raporcie](RELEASE_VALIDATION.md).
- W czystym profilu QGIS zainstaluj ZIP przez **Wtyczki → Zarządzanie
  i instalowanie wtyczek → Instaluj z ZIP**. Sprawdź obliczenie jednej
  działki w obu trybach, raport MD, Processing do GeoPackage oraz
  wyłączenie i ponowne włączenie wtyczki.
- Sprawdź nazwę, wersję 1.1.0, oba języki opisu i pary tagów PL/EN.
- Test na Linuxie nie potwierdza działania na Windows i macOS. Przy
  sprawdzaniu tych platform dopisz rzeczywiste wyniki do raportu.

## GitHub Release

1. Zatwierdź sprawdzone zmiany i wyślij commit do GitHuba.
2. Po poprawnym CI utwórz tag `v1.1.0` na tym commicie.
3. Utwórz release z tytułem **Poprawka odwzorowawcza PL-2000 1.1.0**.
4. Użyj przygotowanego [opisu wydania PL/EN](RELEASE_NOTES.md).
5. Dołącz `Poprawka odwzorowawcza PL-2000-1.1.0.zip` i odpowiadający mu
   plik `.zip.sha256`; sprawdź sumę odbudowanej paczki, następnie opublikuj.

## Repozytorium QGIS

Wyślij ten sam ZIP przez [Upload a plugin](https://plugins.qgis.org/).
Sprawdź w podglądzie nazwę, wersję, zakres `3.40–4.99`, oba opisy i tagi.
Zgodność QGIS 4 określa zakres wersji; flaga `supportsQt6` nie jest używana.

Publiczny wpis ma historyczną nazwę „Poprawka odwzorowawcza”. Jeżeli portal
nie przyjmie pełnej nazwy z metadanych, poproś administratora o jej zmianę;
serwer uzależnia aktualizację nazwy od ustawienia `Allow update name`.
Po zatwierdzeniu sprawdź wpis na stronie i instalację przez menedżer QGIS.

Nie zastępuj opublikowanej paczki inną zawartością pod tym samym numerem.
Każda kolejna aktualizacja wymaga nowego numeru i odbudowania ZIP-a.

Wymagania: [publikacja](https://plugins.qgis.org/docs/publish),
[zatwierdzanie](https://plugins.qgis.org/docs/approval),
[migracja QGIS 4](https://plugins.qgis.org/docs/migrate-qgis4).
