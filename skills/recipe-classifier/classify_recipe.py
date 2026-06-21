"""Script de la skill `recipe-classifier`.

Orquesta (no calcula):
  1. Lee la receta indicada desde FileRepository.
  2. Carga el perfil de gustos desde preferences.json.
  3. Normaliza los campos de parámetros que faltan (heurísticas ligeras).
  4. Calcula affinity_score con core.domain.affinity.score().
  5. Guarda la receta enriquecida con classified_at y affinity_score.

Uso:
  python skills/recipe-classifier/classify_recipe.py <slug>
  python skills/recipe-classifier/classify_recipe.py --all
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Rutas relativas a la raíz del proyecto (el script se llama desde ahí).
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from adapters.file_repository import FileRepository  # noqa: E402
from core.domain.affinity import score  # noqa: E402
from core.domain.taste_profile import TasteProfile  # noqa: E402


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _normalize(recipe_dict: dict) -> dict:
    """Heurísticas deterministas para completar parámetros que la fuente no proveyó.

    Solo rellena si el campo es None/vacío; nunca sobreescribe datos ya presentes.
    """
    # main_ingredients: los primeros 5 nombres de ingredientes si está vacío.
    if not recipe_dict.get("main_ingredients"):
        recipe_dict["main_ingredients"] = [
            i["name"].split()[-1].lower()  # última palabra del nombre ("albahaca fresca" → "fresca")
            for i in recipe_dict.get("ingredients", [])[:5]
            if i.get("name")
        ]

    # meal_type: inferido del tiempo total si falta.
    if not recipe_dict.get("meal_type"):
        t = recipe_dict.get("time_total_min")
        if t is not None:
            recipe_dict["meal_type"] = "desayuno" if t <= 20 else "almuerzo" if t <= 60 else "cena"

    # difficulty: inferida del tiempo activo o total si falta.
    if not recipe_dict.get("difficulty"):
        t = recipe_dict.get("time_active_min") or recipe_dict.get("time_total_min")
        if t is not None:
            recipe_dict["difficulty"] = "baja" if t <= 20 else "media" if t <= 45 else "alta"

    return recipe_dict


def classify_slug(slug: str, repo: FileRepository, profile: TasteProfile) -> None:
    recipe = repo.get(slug)
    if recipe is None:
        print(f"[ERROR] No existe la receta con slug '{slug}'", file=sys.stderr)
        sys.exit(1)

    # Normalizar vía dict para no romper la inmutabilidad del dataclass.
    data = recipe.to_dict()
    data = _normalize(data)

    # Calcular score con los parámetros ya normalizados.
    from core.domain.recipe import Recipe as R
    enriched = R.from_dict(data)
    data["affinity_score"] = score(enriched, profile)
    data["classified_at"] = _now_iso()

    repo.save(R.from_dict(data))
    print(f"[OK] {slug} -> affinity_score={data['affinity_score']:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clasifica recetas calculando su affinity_score.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("slug", nargs="?", help="Slug de la receta a clasificar.")
    group.add_argument("--all", action="store_true", help="Clasifica todas las recetas del repositorio.")
    args = parser.parse_args()

    repo = FileRepository(ROOT / "recipes")
    prefs_path = ROOT / "preferences.json"
    profile = TasteProfile.from_dict(json.loads(prefs_path.read_text(encoding="utf-8")))

    if args.all:
        for recipe in repo.list():
            classify_slug(recipe.slug, repo, profile)
    else:
        classify_slug(args.slug, repo, profile)


if __name__ == "__main__":
    main()
