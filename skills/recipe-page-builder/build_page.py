"""Script de la skill `recipe-page-builder`.

Orquesta (no calcula):
  1. Lee la receta indicada desde FileRepository.
  2. Copia el JSON a app/src/content/recipes/ vía AstroRenderer.
  3. (Opcional) Ejecuta `astro build` para exportar el HTML estático.

Uso:
  python skills/recipe-page-builder/build_page.py <slug> [--build]
  python skills/recipe-page-builder/build_page.py --all [--build]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from adapters.astro_renderer import AstroRenderer  # noqa: E402
from adapters.file_repository import FileRepository  # noqa: E402


def build_slug(slug: str, repo: FileRepository, renderer: AstroRenderer) -> None:
    recipe = repo.get(slug)
    if recipe is None:
        print(f"[ERROR] No existe la receta '{slug}'", file=sys.stderr)
        sys.exit(1)
    path = renderer.render(recipe)
    print(f"[OK] {slug} -> {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Publica recetas en la app Astro.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("slug", nargs="?", help="Slug de la receta a publicar.")
    group.add_argument("--all", action="store_true", help="Publica todas las recetas.")
    parser.add_argument("--build", action="store_true", help="Ejecuta 'astro build' al final.")
    args = parser.parse_args()

    repo = FileRepository(ROOT / "recipes")
    renderer = AstroRenderer()

    if args.all:
        for recipe in repo.list():
            build_slug(recipe.slug, repo, renderer)
    else:
        build_slug(args.slug, repo, renderer)

    if args.build:
        app_dir = ROOT / "app"
        print("[BUILD] Ejecutando astro build...")
        npm = "npm.cmd" if sys.platform == "win32" else "npm"
        result = subprocess.run([npm, "run", "build"], cwd=app_dir, check=False)
        if result.returncode != 0:
            print("[ERROR] astro build fallo", file=sys.stderr)
            sys.exit(result.returncode)
        print("[BUILD] Completado. Salida en app/dist/")


if __name__ == "__main__":
    main()
