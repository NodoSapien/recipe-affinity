"""Puerto `RecipeRepository`: contrato de persistencia de recetas.

Definido como `Protocol` (tipado estructural): los adaptadores lo cumplen por forma, sin importar
este módulo. Así las dependencias apuntan hacia adentro (el dominio define el contrato; los
adaptadores se ajustan a él). Hoy lo implementa `FileRepository`; en la Fase 4, `SupabaseRepository`,
sin que las skills cambien.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from core.domain.recipe import Recipe


@runtime_checkable
class RecipeRepository(Protocol):
    """Persistencia de recetas. La clave natural es `slug` (= nombre de archivo)."""

    def save(self, recipe: Recipe) -> None:
        """Crea o sobrescribe la receta identificada por su slug."""
        ...

    def get(self, slug: str) -> Recipe | None:
        """Devuelve la receta, o `None` si no existe."""
        ...

    def list(self) -> list[Recipe]:
        """Devuelve todas las recetas, ordenadas por slug."""
        ...

    def exists(self, slug: str) -> bool:
        """Indica si existe una receta con ese slug."""
        ...

    def delete(self, slug: str) -> None:
        """Elimina la receta. Idempotente: no falla si no existe."""
        ...
