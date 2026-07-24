## Cel

<!-- Krótko opisz problem i rozwiązanie. -->

## Zakres i ryzyko

- [ ] Zmiana nie modyfikuje wzoru, stałych, osi, stref, PGK ani zaokrąglania.
- [ ] Warstwa wejściowa nadal nie jest modyfikowana.
- [ ] Teksty GUI nie ujawniają surowych wyjątków ani danych lokalnych.
- [ ] Nowe pliki runtime zostały świadomie dodane do manifestu ZIP.

Jeżeli zaznaczenie pierwszego pola nie jest możliwe, opisz podstawę prawną,
wektory referencyjne i sposób niezależnej weryfikacji.

## Walidacja

- [ ] `pytest -p no:cacheprovider`
- [ ] `ruff check --no-cache .`
- [ ] `ruff format --check --no-cache .`
- [ ] Flake8, Bandit i detect-secrets
- [ ] świeży ZIP porównany ze źródłami
- [ ] test ręczny GUI/Processing, jeżeli zmiana dotyczy PyQGIS

## Zrzuty ekranu

<!-- Dodaj tylko dla zmian widocznych w interfejsie. Usuń sekcję, jeśli nie dotyczy. -->
