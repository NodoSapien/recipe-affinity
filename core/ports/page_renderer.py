"""Puerto `PageRenderer`: contrato para renderizar una receta a una página.

Interfaz definida en la Fase 0; su adaptador `AstroRenderer` (genera la entrada de la content
collection y exporta el HTML estático) se implementa en la **Fase 3**. No implementar aquí.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from core.domain.recipe import Recipe


@runtime_checkable
class PageRenderer(Protocol):
    def render(self, recipe: Recipe) -> str:
        """Renderiza la receta y devuelve la ruta del artefacto generado."""
        ...
