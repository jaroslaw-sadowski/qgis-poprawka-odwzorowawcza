# Changelog

Wszystkie istotne zmiany projektu są dokumentowane w tym pliku. Projekt
stosuje [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0] - 2026-07-24

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

### Changed

- Oficjalną nazwę skrócono do „Poprawka odwzorowawcza”; zakres EGiB
  pozostaje jednoznacznie opisany w funkcjach i dokumentacji.
- Wszystkie opisy metadanych wtyczki przetłumaczono na język polski.
- Opis publikacyjny uproszczono i ukierunkowano na potrzeby użytkownika.
- Do tagów dodano „Stowarzyszenie QGIS Polska”.
- Nie zmieniono logiki obliczeń ani zachowania wtyczki.

### Security

- Limity złożoności geometrii wykonywane przed transformacją i GEOS.
- Jawny manifest plików paczki oraz odrzucanie symlinków i plików
  nieoczekiwanych.
- Brak komunikacji sieciowej, zależności pip i modyfikacji danych
  źródłowych.
- Bezpieczne komunikaty GUI, minimalne uprawnienia CI i akcje GitHub
  przypięte do pełnych identyfikatorów commitów.

[Unreleased]: https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/releases/tag/v1.0.0
