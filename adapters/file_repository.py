"""Adaptador `FileRepository`: persistencia de recetas en archivos `recipes/<slug>.json`.

Cumple el puerto `core.ports.recipe_repository.RecipeRepository` por tipado estructural
(no necesita importarlo). Es la implementación de la fase "archivos primero"; en la Fase 4 se
sustituye por `SupabaseRepository` sin tocar el dominio ni las skills.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from core.domain.recipe import Recipe


class FileRepository:
    """Repositorio de recetas respaldado por un directorio de archivos JSON (UTF-8)."""

    def __init__(self, base_dir: Path | str = Path("recipes")) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, slug: str) -> Path:
        return self._base_dir / f"{slug}.json"

    def save(self, recipe: Recipe) -> None:
        """Escritura atómica: vuelca a un temporal en el mismo dir y luego `os.replace`."""
        payload = json.dumps(recipe.to_dict(), ensure_ascii=False, indent=2) + "\n"
        # `delete=False` + replace evita dejar archivos corruptos si el proceso muere a mitad.
        fd, tmp_name = tempfile.mkstemp(dir=self._base_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
            os.replace(tmp_name, self._path(recipe.slug))
        except BaseException:
            # Limpia el temporal si algo falló antes del replace.
            Path(tmp_name).unlink(missing_ok=True)
            raise

    def get(self, slug: str) -> Recipe | None:
        path = self._path(slug)
        if not path.exists():
            return None
        with path.open(encoding="utf-8") as fh:
            return Recipe.from_dict(json.load(fh))

    def list(self) -> list[Recipe]:
        recipes = []
        for path in sorted(self._base_dir.glob("*.json")):
            with path.open(encoding="utf-8") as fh:
                recipes.append(Recipe.from_dict(json.load(fh)))
        return recipes

    def exists(self, slug: str) -> bool:
        return self._path(slug).exists()

    def delete(self, slug: str) -> None:
        # Idempotente: no falla si el archivo no existe.
        self._path(slug).unlink(missing_ok=True)
