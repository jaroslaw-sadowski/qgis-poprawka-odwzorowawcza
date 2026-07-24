"""Safe Polish messages for expected calculation and geometry failures."""

if __package__:
    from .adapters import (
        GeometryInputError,
        GeometryRepairError,
        GeometryTransformError,
        ZoneSelectionError,
    )
    from .core import AreaCalculationError
else:
    from adapters import (
        GeometryInputError,
        GeometryRepairError,
        GeometryTransformError,
        ZoneSelectionError,
    )
    from core import AreaCalculationError


def safe_calculation_error_message(error: Exception) -> str:
    """Translate expected failures without exposing implementation details."""

    if isinstance(error, GeometryInputError):
        details = str(error)
        if details.startswith("Geometria przekracza limit liczby "):
            return details
        if "curved polygon rings" in details:
            return (
                "Geometria zawiera krzywe. Przed obliczeniem jawnie "
                "segmentyzuj pierścienie na kopii danych."
            )
        return (
            "Geometria wejściowa jest pusta, nie jest poligonem albo nie "
            "spełnia wymagań technicznych."
        )
    if isinstance(error, GeometryTransformError):
        return (
            "Nie udało się przeliczyć kopii geometrii do wybranej strefy "
            "PL-2000. Sprawdź CRS warstwy i dostępną transformację."
        )
    if isinstance(error, GeometryRepairError):
        return (
            "Nie udało się uzyskać poprawnej kopii geometrii. Popraw dane "
            "źródłowe albo wybierz tryb bez naprawy."
        )
    if isinstance(error, ZoneSelectionError):
        return (
            "Nie można potwierdzić strefy PL-2000. Sprawdź CRS warstwy "
            "i wybraną strefę."
        )
    if isinstance(error, AreaCalculationError):
        return (
            "Dane nie pozwalają wyznaczyć poprawnego wyniku. Sprawdź "
            "geometrię, CRS oraz strefę PL-2000."
        )
    return "Nie udało się wykonać operacji z powodu nieoczekiwanego błędu."


__all__ = ["safe_calculation_error_message"]
