"""Processing provider for batch cadastral area calculations."""

from .area_algorithm import CalculateEgibAreaAlgorithm
from .provider import EgibAreaProvider

__all__ = ["CalculateEgibAreaAlgorithm", "EgibAreaProvider"]
