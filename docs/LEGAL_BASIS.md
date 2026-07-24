# Podstawa prawna i zakres obliczenia

Wtyczka implementuje powierzchniową poprawkę odwzorowawczą dla działek
ewidencyjnych w polskim układzie PL-2000.

Podstawowe źródła:

- załącznik nr 3 do rozporządzenia w sprawie ewidencji gruntów i budynków,
  Dz.U. 2024 poz. 219 — wzór poprawki i definicja przybliżonego środka
  ciężkości:
  <https://eli.gov.pl/eli/DU/2024/219/ogl>;
- rozporządzenie w sprawie państwowego systemu odniesień przestrzennych,
  Dz.U. 2024 poz. 342 — układy PL-2000 i konwencja osi:
  <https://eli.gov.pl/eli/DU/2024/342/ogl>.

Materiały w `docs/legal/` są zachowanymi kopiami referencyjnymi użytymi
podczas implementacji. Nie stanowią mechanizmu automatycznej aktualizacji
prawa. Przed użyciem wyniku w postępowaniu urzędowym należy sprawdzić aktualny
stan prawny, właściwy CRS, strefę PL-2000 i źródło punktów granicznych.

Moduł obliczeniowy nie wykonuje zaokrągleń pośrednich. Wartość ewidencyjna
jest prezentowana w hektarach z czterema miejscami po przecinku, zgodnie
z udokumentowaną polityką `ROUND_HALF_UP`.
