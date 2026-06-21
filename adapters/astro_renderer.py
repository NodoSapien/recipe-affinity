"""Adaptador `AstroRenderer`: sincroniza una receta al directorio de contenido de Astro.

Cumple el puerto `core.ports.page_renderer.PageRenderer` por tipado estructural.

En Astro v6 con content collections + glob loader, el "renderizado" consiste en copiar
(o sobreescribir atómicamente) el JSON de la receta en `app/src/content/recipes/`.
Astro lo recoge en el siguiente `astro build` y genera la página estática correspondiente.
No se genera HTML directamente desde Python: esa es responsabilidad de Astro.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from core.domain.recipe import Recipe

_DEFAULT_CONTENT_DIR = Path(__file__).resolve().parents[1] / "app" / "src" / "content" / "recipes"


class AstroRenderer:
    """Renderer que escribe el JSON de la receta en la content collection de Astro."""

    def __init__(self, content_dir: Path | str | None = None) -> None:
        self._content_dir = Path(content_dir) if content_dir else _DEFAULT_CONTENT_DIR
        self._content_dir.mkdir(parents=True, exist_ok=True)

    def render(self, recipe: Recipe) -> str:
        """Escribe `<slug>.json` en la content collection y devuelve la ruta generada."""
        dest = self._content_dir / f"{recipe.slug}.json"
        payload = json.dumps(recipe.to_dict(), ensure_ascii=False, indent=2) + "\n"
        fd, tmp_name = tempfile.mkstemp(dir=self._content_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
            os.replace(tmp_name, dest)
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise
        return str(dest)
