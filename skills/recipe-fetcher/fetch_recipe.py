"""Entrypoint delgado de la skill `recipe-fetcher`.

Orquesta (no calcula): pega el adaptador `JsonLdSource` con el puerto `RecipeRepository`
(`FileRepository`). Toda la lógica determinista vive en los adaptadores/dominio.

Uso:
    python skills/recipe-fetcher/fetch_recipe.py <url> [--out-dir recipes]

Imprime una línea JSON con el resultado (slug y ruta) para que la skill la encadene.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Permite ejecutar el script directamente: añade la raíz del repo al sys.path.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from adapters.file_repository import FileRepository  # noqa: E402
from adapters.jsonld_source import JsonLdSource  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Descarga una receta desde una URL y la guarda.")
    parser.add_argument("url", help="URL de la receta a descargar")
    parser.add_argument(
        "--out-dir",
        default=str(_REPO_ROOT / "recipes"),
        help="Directorio destino (por defecto: recipes/)",
    )
    args = parser.parse_args(argv)

    source = JsonLdSource()
    repo = FileRepository(base_dir=Path(args.out_dir))

    try:
        recipe = source.fetch(args.url)
    except Exception as exc:  # noqa: BLE001 (queremos un mensaje legible para la skill)
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        return 1

    repo.save(recipe)
    out_path = Path(args.out_dir) / f"{recipe.slug}.json"
    print(
        json.dumps(
            {"ok": True, "slug": recipe.slug, "title": recipe.title, "path": str(out_path)},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
