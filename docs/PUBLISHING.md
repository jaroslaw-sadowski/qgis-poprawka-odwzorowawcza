# Publikacja wersji 1.0.0

Ta instrukcja prowadzi od gotowego kodu do publikacji w oficjalnym
repozytorium wtyczek QGIS. Do wysyłki służy wyłącznie paczka
`qgis_poprawka_odwzorowawcza-1.0.0.zip` zbudowana przez skrypt projektu.
Nie używaj automatycznego archiwum „Source code” tworzonego przez GitHub.

## 1. Przetestuj finalny ZIP

Zbuduj paczkę:

```bash
python scripts/build_plugin_zip.py
python -m zipfile -t \
  dist/qgis_poprawka_odwzorowawcza-1.0.0.zip
sha256sum dist/qgis_poprawka_odwzorowawcza-1.0.0.zip
```

W QGIS utwórz czysty profil testowy, a następnie:

1. Otwórz **Wtyczki → Zarządzanie i instalowanie wtyczek → Instaluj z ZIP**.
2. Wskaż `qgis_poprawka_odwzorowawcza-1.0.0.zip`.
3. Włącz wtyczkę i sprawdź, czy QGIS nie pokazuje błędu.
4. Oblicz wynik dla jednej zaznaczonej działki.
5. Uruchom algorytm seryjny z panelu Processing.
6. Wyłącz, ponownie włącz i odinstaluj wtyczkę.

Powtórz ten test w QGIS 3.44 na Windows, Linux i macOS. Wyniki wpisz do
`docs/RELEASE_VALIDATION.md`. Jeżeli którykolwiek test nie przejdzie, nie
twórz taga i nie wysyłaj paczki.

## 2. Zatwierdź wydanie na GitHubie

Sprawdź zmiany, utwórz commit i wyślij `main`:

```bash
git status --short
git add .github/ISSUE_TEMPLATE/bug_report.yml CHANGELOG.md README.md \
  docs/PUBLISHING.md docs/RELEASE_VALIDATION.md metadata.txt \
  tests/qgis/test_plugin.py tests/unit/test_packaging.py
git commit -m "chore: release 1.0.0"
git push origin main
```

Poczekaj, aż GitHub Actions zakończy kontrolę **Quality** na zielono.
Następnie odbuduj ZIP z zatwierdzonego commitu i ponownie sprawdź jego sumę:

```bash
python scripts/build_plugin_zip.py
python -m zipfile -t \
  dist/qgis_poprawka_odwzorowawcza-1.0.0.zip
sha256sum dist/qgis_poprawka_odwzorowawcza-1.0.0.zip
```

Suma musi być zgodna z sumą zapisaną w raporcie walidacji.

## 3. Utwórz tag i GitHub Release

Tag `v1.0.0` został utworzony przed finalną korektą metadanych, ale nie
powstał jeszcze GitHub Release ani wydanie QGIS. Po zaliczeniu testów
ręcznych i GitHub Actions odtwórz tag na finalnym commicie:

```bash
git tag -d v1.0.0
git push origin --delete v1.0.0
git tag -a v1.0.0 -m "Poprawka odwzorowawcza 1.0.0"
git push origin v1.0.0
```

Na GitHubie:

1. Otwórz **Releases → Draft a new release**.
2. Wybierz tag `v1.0.0`.
3. Ustaw tytuł `Poprawka odwzorowawcza 1.0.0`.
4. Skopiuj opis wersji `1.0.0` z `CHANGELOG.md`.
5. Dołącz dokładnie plik
   `dist/qgis_poprawka_odwzorowawcza-1.0.0.zip`.
6. Opublikuj wydanie.

## 4. Wyślij ZIP do QGIS

Do publikacji potrzebny jest bezpłatny identyfikator OSGeo.

1. Zaloguj się na [plugins.qgis.org](https://plugins.qgis.org/).
2. Wybierz **Upload a plugin**.
3. Wskaż ten sam plik ZIP, który został dołączony do GitHub Release.
4. Sprawdź podgląd: nazwa „Poprawka odwzorowawcza”, wersja `1.0.0`,
   QGIS `3.40–3.99` i wydanie stabilne.
5. Wyślij formularz i poczekaj na zatwierdzenie przez opiekuna repozytorium.

Oficjalne wymagania i przebieg zatwierdzania opisują strony
[Publishing a plugin](https://plugins.qgis.org/publish/) oraz
[Plugin approval process](https://plugins.qgis.org/publish/#plugin-approval-process).

## 5. Sprawdź publikację

Po zatwierdzeniu:

1. Otwórz czysty profil QGIS.
2. Odśwież oficjalne repozytorium w Menedżerze wtyczek.
3. Wyszukaj „Poprawka odwzorowawcza”.
4. Zainstaluj ją z repozytorium i powtórz krótki test jednej działki.

Jeżeli po publikacji trzeba coś poprawić, zwiększ numer do `1.0.1`. Nie
wysyłaj ponownie innej paczki z tym samym numerem wersji.
