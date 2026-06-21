"""Entrypoint delgado de la skill `recipe-fetcher`.

Orquesta (no calcula): pega el adaptador `JsonLdSource` con el puerto `RecipeRepository`
(`FileRepository`) y encadena el clasificador (Fase 2) automáticamente.

Uso:
    python skills/recipe-fetcher/fetch_recipe.py <url> [--out-dir recipes] [--no-classify]

Imprime una línea JSON con el resultado (slug, ruta y affinity_score) para que la skill la encadene.
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
    parser.add_argument(
        "--no-classify",
        action="store_true",
        help="No encadenar el clasificador tras la descarga.",
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

    affinity_score = None
    if not args.no_classify:
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "classify_recipe",
                _REPO_ROOT / "skills" / "recipe-classifier" / "classify_recipe.py",
            )
            mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
            spec.loader.exec_module(mod)  # type: ignore[union-attr]

            prefs_path = _REPO_ROOT / "preferences.json"
            profile = mod.TasteProfile.from_dict(
                json.loads(prefs_path.read_text(encoding="utf-8"))
            )
            mod.classify_slug(recipe.slug, repo, profile)
            affinity_score = repo.get(recipe.slug).affinity_score  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] Clasificador no disponible: {exc}", file=sys.stderr)

    out_path = Path(args.out_dir) / f"{recipe.slug}.json"
    print(
        json.dumps(
            {
                "ok": True,
                "slug": recipe.slug,
                "title": recipe.title,
                "path": str(out_path),
                "affinity_score": affinity_score,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
