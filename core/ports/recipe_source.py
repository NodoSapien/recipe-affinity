"""Puerto `RecipeSource`: contrato para obtener una receta desde una fuente externa.

Interfaz definida en la Fase 0; su adaptador `JsonLdSource` (scraping de schema.org/Recipe vía
`recipe-scrapers`) se implementa en la **Fase 1**. No implementar aquí.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from core.domain.recipe import Recipe


@runtime_checkable
class RecipeSource(Protocol):
    def fetch(self, url: str) -> Recipe:
        """Descarga y normaliza la receta apuntada por `url` al esquema `Recipe`."""
        ...
