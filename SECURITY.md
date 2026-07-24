# Polityka bezpieczeństwa

## Obsługiwane wersje

Do czasu pierwszej publikacji poprawki bezpieczeństwa są przygotowywane dla
bieżącej gałęzi `main` i kandydata wersji `0.1.x`. Po opublikowaniu kolejnej
wersji wspierane będzie najnowsze wydanie dostępne w oficjalnym repozytorium
wtyczek QGIS.

## Prywatne zgłaszanie podatności

Nie publikuj podatności, exploita, danych wrażliwych ani projektu QGIS
potrzebnego do odtworzenia problemu w zwykłym issue.

1. Użyj prywatnego formularza
   [Report a vulnerability](https://github.com/jaroslaw-sadowski/qgis-poprawka-odwzorowawcza/security/advisories/new).
2. Opisz wersję wtyczki i QGIS, system operacyjny, wpływ oraz minimalne kroki
   odtworzenia.
3. Dołącz wyłącznie zanonimizowane dane niezbędne do analizy.

Jeżeli prywatne zgłaszanie nie jest jeszcze dostępne, utwórz neutralne issue
bez szczegółów technicznych i poproś opiekuna o wskazanie prywatnego kanału.

Potwierdzenie przyjęcia zgłoszenia jest planowane w ciągu 7 dni, a pierwsza
ocena i dalszy plan w ciągu 14 dni. Termin poprawki zależy od wpływu,
złożoności oraz koordynacji publikacji.

## Zakres

Wtyczka nie łączy się z siecią, nie przechowuje poświadczeń i nie modyfikuje
warstwy wejściowej. Problemy dotyczące wzoru, doboru strefy lub interpretacji
wyniku zgłaszaj jako zwykły błąd, o ile nie prowadzą do naruszenia
poufności, integralności albo dostępności.
